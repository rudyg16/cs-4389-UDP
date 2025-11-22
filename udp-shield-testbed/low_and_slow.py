#!/usr/bin/env python3
"""
low_and_slow.py
Generate low-rate, slowly varying UDP traffic to mimic 'low-and-slow' attacks.

Usage (inside ns_attacker, targeting the victim):
  sudo ip netns exec ns_attacker python3 low_and_slow.py \
      --target 10.200.1.2 --port 54321 --pps 2 --duration 60
"""

import argparse
import socket
import time
import random
import os

parser = argparse.ArgumentParser()
parser.add_argument("--target", required=True, help="Target IP (e.g., victim)")
parser.add_argument("--port", type=int, required=True, help="Target UDP port")
parser.add_argument("--pps", type=float, default=1.0, help="Average packets per second (low)")
parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
args = parser.parse_args()

def build_payload(seq_num: int) -> bytes:
    # Vary the size and content slightly over time
    base = f"slow_req_{seq_num}"
    extra_len = random.randint(0, 64)  # small variation
    payload = (base + ("." * extra_len)).encode()
    return payload

def main():
    if os.geteuid() != 0:
        print("ERROR: must run as root (sudo)")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    avg_interval = 1.0 / max(args.pps, 0.1)
    end_time = time.time() + args.duration
    sent = 0

    try:
        while time.time() < end_time:
            payload = build_payload(sent)
            sock.sendto(payload, (args.target, args.port))
            sent += 1

            # Add a bit of randomness to timing to avoid a perfect pattern
            jitter = random.uniform(-0.3, 0.3) * avg_interval
            sleep_time = max(0.01, avg_interval + jitter)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        pass
    finally:
        print("Sent low-and-slow packets:", sent)
        sock.close()

if __name__ == "__main__":
    main()