#!/usr/bin/env python3
"""capture_and_measure.py

Capture with tcpdump then analyze pcap with scapy.
Usage:
  sudo python3 capture_and_measure.py --iface <iface> --duration 10 --out out.pcap
"""
import argparse, subprocess, time, os
from collections import Counter

parser = argparse.ArgumentParser()
parser.add_argument("--iface", required=True)
parser.add_argument("--duration", type=int, default=10)
parser.add_argument("--out", default="capture.pcap")
args = parser.parse_args()

def run_tcpdump(iface, out, duration):
    print(f"Capturing on {iface} for {duration}s -> {out}")
    cmd = ["tcpdump", "-i", iface, "-w", out]
    proc = subprocess.Popen(cmd)
    time.sleep(duration)
    proc.terminate()
    proc.wait()
    print("tcpdump finished")

def analyze_pcap(path):
    try:
        from scapy.all import rdpcap, IP, UDP, TCP
    except Exception as e:
        print("scapy import failed:", e)
        return
    pkts = rdpcap(path)
    total_packets = len(pkts)
    total_bytes = sum(len(p) for p in pkts)
    srcs = []
    dst_ports = []
    for p in pkts:
        if IP in p:
            srcs.append(p[IP].src)
            if UDP in p or TCP in p:
                l4 = p[UDP] if UDP in p else p[TCP]
                dst_ports.append(l4.dport)
    src_counts = Counter(srcs)
    port_counts = Counter(dst_ports)
    print("Total packets:", total_packets)
    print("Total bytes:", total_bytes)
    print("Unique source IPs:", len(src_counts))
    print("Top 5 source IPs:", src_counts.most_common(5))
    print("Top 5 destination ports:", port_counts.most_common(5))

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Run as root (sudo). Aborting.")
        exit(1)
    run_tcpdump(args.iface, args.out, args.duration)
    analyze_pcap(args.out)
