#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <linux/in.h>  // for IPPROTO_UDP

#define UDP_PORT_COOKIE 40000
#define UDP_PORT_PROTECTED 9999
#define RATE_LIMIT_PPS 20000

// count packets by source IP
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 10240);
    __type(key, __u32); // source IP address (IPv4)
    __type(value, __u64); // packet count
} pkt_cnt_by_saddr SEC(".maps");

// Key structure for destination ports
struct port_key_t {
    __u16 port;
    __u8 pad[2];
};

// count packets by destination UDP port
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_HASH);
    __uint(max_entries, 4096);
    __type(key, struct port_key_t);
    __type(value, __u64);
} pkt_cnt_by_dport SEC(".maps");

// Per source rate limiting state: simple 1 second buckets
struct rate_val {
    __u64 last_ts;   // seconds since boot
    __u64 count;     // packets seen in that second
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 10240);
    __type(key, __u32);           // source IP
    __type(value, struct rate_val);
} rate_limit_by_saddr SEC(".maps");

// Cookie key (16 bytes) for fast-path cookie pre check
struct cookie_key {
    __u8 bytes[16];
};

// Map of valid cookies. User space gateway should insert a key when it
// issues a cookie, and optionally remove it when expired.
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 65536);
    __type(key, struct cookie_key);
    __type(value, __u8);      // dummy value, 1 = valid
} valid_cookies SEC(".maps");

// Helper function: simple per source rate limiting
static __always_inline int check_rate_limit(__u32 saddr)
{
    __u64 now_ns = bpf_ktime_get_ns();
    __u64 now_s = now_ns / 1000000000ULL; // convert to seconds

    struct rate_val *rv = bpf_map_lookup_elem(&rate_limit_by_saddr, &saddr);
    if (!rv) {
        struct rate_val init = {
            .last_ts = now_s,
            .count = 1,
        };
        bpf_map_update_elem(&rate_limit_by_saddr, &saddr, &init, BPF_ANY);
        return 0; // allow
    }

    if (rv->last_ts == now_s) {
        rv->count += 1;
    } else {
        rv->last_ts = now_s;
        rv->count = 1;
    }

    if (rv->count > RATE_LIMIT_PPS) {
        // Too many packets from this source in current second: drop
        return -1;
    }

    return 0;
}

// Helper: check if destination UDP port is in allowlist
static __always_inline bool port_allowed(__u16 dport_host)
{
    if (dport_host == UDP_PORT_COOKIE)
        return true;
    if (dport_host == UDP_PORT_PROTECTED)
        return true;

    // Add more allowed ports here if needed

    return false;
}

// Helper: cookie pre check for packets to protected port
static __always_inline int cookie_precheck(void *data_end,
                                           struct udphdr *udph,
                                           __u16 dport_host)
{
    // Only enforce cookie pre check on protected port
    if (dport_host != UDP_PORT_PROTECTED)
        return 0; // not protected port, allow

    __u16 udp_len = bpf_ntohs(udph->len);
    if (udp_len <= sizeof(struct udphdr))
        return -1;  // no payload, drop

    __u16 payload_len = udp_len - sizeof(struct udphdr);
    if (payload_len < 16)
        return -1;  // requires at least 16 bytes cookie in payload

    void *payload = (void *)(udph + 1);
    if (payload + 16 > data_end)
        return -1;  // out of bounds

    struct cookie_key ckey = {};
#pragma unroll
    for (int i = 0; i < 16; i++) {
        ckey.bytes[i] = ((unsigned char *)payload)[i];
    }

    __u8 *ok = bpf_map_lookup_elem(&valid_cookies, &ckey);
    if (!ok || *ok == 0) {
        // Cookie not known in fast path, drop
        return -1;
    }

    // Cookie is known and valid according to map
    return 0;
}

SEC("xdp")
int xdp_pkt_tracker(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    // Ethernet header
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP; // garbage, drop

    // Only handle IPv4, drop all other Ethertypes as garbage traffic
    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_DROP;

    // IP header
    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_DROP;

    // Basic IP header sanity: header length and protocol
    __u32 ihl = iph->ihl * 4;
    if (ihl < sizeof(struct iphdr))
        return XDP_DROP;

    if ((void *)iph + ihl > data_end)
        return XDP_DROP;

    if (iph->protocol != IPPROTO_UDP)
        return XDP_DROP; // non UDP, drop according to spec

    // UDP header
    struct udphdr *udph = (void *)iph + ihl;
    if ((void *)(udph + 1) > data_end)
        return XDP_DROP;

    // IP total length and UDP length checks, drop "garbage traffic"
    __u16 ip_tot_len = bpf_ntohs(iph->tot_len);
    __u16 udp_len = bpf_ntohs(udph->len);

    // IP total length must be at least IP header + UDP header
    if (ip_tot_len < ihl + sizeof(struct udphdr))
        return XDP_DROP;

    // UDP length must be at least UDP header
    if (udp_len < sizeof(struct udphdr))
        return XDP_DROP;

    // Make sure UDP payload is inside packet bounds
    void *udp_payload_end = (void *)(udph + 1) + (udp_len - sizeof(struct udphdr));
    if (udp_payload_end > data_end)
        return XDP_DROP;

    // Extract fields used for filtering and accounting
    __u32 saddr = iph->saddr;
    __u16 dport_host = bpf_ntohs(udph->dest);

    // Rate limiting per source
    if (check_rate_limit(saddr) < 0)
        return XDP_DROP;

    // Destination port allowlist
    if (!port_allowed(dport_host))
        return XDP_DROP;

    // Cookie pre check for protected port
    if (cookie_precheck(data_end, udph, dport_host) < 0)
        return XDP_DROP;

    // At this point the packet is considered valid. Update counters.

    __u64 one = 1;

    // Count per source IP
    __u64 *val = bpf_map_lookup_elem(&pkt_cnt_by_saddr, &saddr);
    if (val)
        __sync_fetch_and_add(val, 1);
    else
        bpf_map_update_elem(&pkt_cnt_by_saddr, &saddr, &one, BPF_ANY);

    // Count per destination port
    struct port_key_t pkey = {};
    pkey.port = udph->dest; // still in network order, but used consistently as key
    __u64 *pval = bpf_map_lookup_elem(&pkt_cnt_by_dport, &pkey);
    if (pval)
        __sync_fetch_and_add(pval, 1);
    else
        bpf_map_update_elem(&pkt_cnt_by_dport, &pkey, &one, BPF_ANY);

    // Pass packet up the stack
    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
