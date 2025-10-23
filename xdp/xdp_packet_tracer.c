#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <linux/in.h>  // for IPPROTO_UDP

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

SEC("xdp")
int xdp_pkt_tracker(struct xdp_md *ctx) {
    // point to the start of the packet
    void *data = (void *)(long)ctx->data;

    // point to the end of the packet
    void *data_end = (void *)(long)ctx->data_end; 

    // interpret beginning of packet as an Ethernet header
    struct ethhdr *eth = data; 
    if ((void*)(eth + 1) > data_end) 
        return XDP_PASS;

    // check if Ethernet protocol type is IPv4
    if (eth->h_proto != __constant_htons(ETH_P_IP)) 
        return XDP_PASS;

    // IP header after Ethernet header
    struct iphdr *iph = (void*)(eth + 1);
    if ((void*)(iph + 1) > data_end) 
        return XDP_PASS;

    // check if protocol field is UDP
    if (iph->protocol != IPPROTO_UDP) 
        return XDP_PASS;

    // calculate IP header length
    __u32 ihl = iph->ihl * 4;
    struct udphdr *udph = (void*)iph + ihl;

    if ((void*)(udph + 1) > data_end) 
        return XDP_PASS;

    // Count per source IP
    // extract source IP addr
    __u32 saddr = iph->saddr;
    __u64 one = 1;

    // do a lookup if this IP address already exists, if so increment 1
    __u64 *val = bpf_map_lookup_elem(&pkt_cnt_by_saddr, &saddr);
    if (val)
        __sync_fetch_and_add(val, 1);
    else
        bpf_map_update_elem(&pkt_cnt_by_saddr, &saddr, &one, BPF_ANY);

    // Count per destination port
    struct port_key_t pkey = {};
    pkey.port = udph->dest; // store destination UDP port
    __u64 *pval = bpf_map_lookup_elem(&pkt_cnt_by_dport, &pkey);
    if (pval)
        __sync_fetch_and_add(pval, 1);
    else
        bpf_map_update_elem(&pkt_cnt_by_dport, &pkey, &one, BPF_ANY);

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
