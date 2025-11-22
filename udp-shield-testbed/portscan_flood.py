#!/usr/bin/env python3
"""
portscan_flood.py
Rapid UDP spray across random destination ports (avoids the allowlist ports).

Usage (inside ns_attacker):
  sudo ip netns exec ns_attacker python3 portscan_flood.py \
      --target 10.200.1.2 --pps 20000 --duration 8
"""

import argparse
import os
import random
import socket
import time

parser = argparse.ArgumentParser()
parser.add_argument("--target", required=True, help="Target IP (victim/gateway)")
parser.add_argument("--pps", type=int, default=20000, help="Packets per second")
parser.add_argument("--duration", type=int, default=8, help="Attack duration in seconds")
parser.add_argument("--min-port", type=int, default=1025, help="Lowest random dest port (default 1025)")
parser.add_argument("--max-port", type=int, default=65535, help="Highest random dest port (default 65535)")
args = parser.parse_args()

ALLOWLIST = {40000, 9999}

def random_port():
    while True:
        port = random.randint(args.min_port, args.max_port)
        if port not in ALLOWLIST:
            return port

def build_payload(seq_num: int) -> bytes:
    return f"SCAN{seq_num}".encode()

def main():
    if os.geteuid() != 0:
        print("ERROR: must run as root (sudo)")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    interval = 1.0 / max(args.pps, 1)
    end_time = time.time() + args.duration
    sent = 0

    try:
        while time.time() < end_time:
            dport = random_port()
            payload = build_payload(sent)
            sock.sendto(payload, (args.target, dport))
            sent += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        print("Sent port-scan packets:", sent)
        sock.close()

if __name__ == "__main__":
    main()
