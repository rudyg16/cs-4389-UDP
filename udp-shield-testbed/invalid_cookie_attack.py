#!/usr/bin/env python3
"""
invalid_cookie_attack.py
Send UDP packets with 'invalid cookie' style payloads to simulate
reflection-pattern attack traffic.

Usage (inside ns_attacker, targeting the reflector):
  sudo ip netns exec ns_attacker python3 invalid_cookie_attack.py \
      --target 10.200.2.2 --port 12345 --pps 20000 --duration 10
"""

import argparse
import socket
import time
import random
import string
import os

parser = argparse.ArgumentParser()
parser.add_argument("--target", required=True, help="Target IP (e.g., reflector)")
parser.add_argument("--port", type=int, required=True, help="Target UDP port")
parser.add_argument("--pps", type=int, default=5000, help="Packets per second")
parser.add_argument("--duration", type=int, default=10, help="Attack duration in seconds")
args = parser.parse_args()

def random_cookie(length=16):
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))

def build_invalid_cookie_payload(seq_num: int) -> bytes:
    # Simple fake "protocol" with a cookie field and a request ID.
    cookie = random_cookie()
    payload_str = (
        f"COOKIE={cookie};VALID=0;REQ_ID={seq_num};TYPE=REFLECT_REQ;DATA=TESTDATA"
    )
    return payload_str.encode()

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
            payload = build_invalid_cookie_payload(sent)
            sock.sendto(payload, (args.target, args.port))
            sent += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        print("Sent invalid-cookie packets:", sent)
        sock.close()

if __name__ == "__main__":
    main()
