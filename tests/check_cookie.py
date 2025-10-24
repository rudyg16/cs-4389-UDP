#!/usr/bin/env python3
# tests/check_cookie.py
# Request a cookie from gateway, send protected packet to target,
# and verify the victim-side recv log contains the cookie+payload.
import argparse
import socket
import time
import sys
import binascii
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--gateway", required=True)
parser.add_argument("--gateway-port", type=int, default=40000)
parser.add_argument("--target", required=True)
parser.add_argument("--target-port", type=int, default=9999)
parser.add_argument("--payload", default="TEST_PAYLOAD")
parser.add_argument("--timeout", type=float, default=2.0)
parser.add_argument("--recv-log", required=True, help="Path to victim's receive log to check for delivered packet")
args = parser.parse_args()

RECV_LOG = Path(args.recv_log)

def request_cookie(gateway, port, timeout=2.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    s.sendto(b"COOKIE-REQ", (gateway, port))
    try:
        data, _ = s.recvfrom(4096)
    except Exception as e:
        print("ERROR: no reply from gateway:", e)
        return None
    return data

def send_protected(target, port, cookie, payload):
    t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    t.sendto(cookie + payload.encode(), (target, port))
    t.close()

def wait_for_log_contains(path: Path, substring: bytes, timeout=3.0):
    """Poll for substring appearing in file within timeout seconds."""
    end = time.time() + timeout
    while time.time() < end:
        if path.exists():
            try:
                data = path.read_bytes()
                if substring in data:
                    return True
            except Exception:
                pass
        time.sleep(0.2)
    return False

def main():
    print(f"[*] Requesting cookie from {args.gateway}:{args.gateway_port}")
    data = request_cookie(args.gateway, args.gateway_port, args.timeout)
    if not data:
        print("[!] Failed to obtain cookie")
        sys.exit(2)
    if not data.startswith(b"COOKIE:"):
        print("[!] Unexpected reply from gateway:", data)
        sys.exit(3)
    cookie = data[len(b"COOKIE:"):]
    print("[*] Received cookie (hex):", binascii.hexlify(cookie).decode())
    if len(cookie) != 16:
        print("[!] Cookie length != 16 bytes:", len(cookie))
        sys.exit(4)

    # Send protected packet to target
    print(f"[*] Sending protected packet to {args.target}:{args.target_port}")
    send_protected(args.target, args.target_port, cookie, args.payload)

    # Wait and check recv log
    expected = cookie + args.payload.encode()
    print(f"[*] Waiting for victim to record payload in {args.recv_log} (timeout 4s)")
    ok = wait_for_log_contains(RECV_LOG, expected, timeout=4.0)
    if not ok:
        # Try a bit longer (timing/environment differences)
        ok = wait_for_log_contains(RECV_LOG, expected, timeout=2.0)
    if ok:
        print("[+] Protected packet observed in victim log.")
        sys.exit(0)
    else:
        print("[!] Protected packet NOT observed in victim log. Check listener and nets.")
        sys.exit(5)

if __name__ == "__main__":
    main()
