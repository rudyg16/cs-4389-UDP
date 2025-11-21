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

def parse_args():
    p = argparse.ArgumentParser(
        description="Cookie end-to-end check: gateway -> protected port -> backend log"
    )
    p.add_argument("--gateway", required=True,
                   help="IP/host of gateway (ns_victim side, e.g. 10.200.1.2)")
    p.add_argument("--gateway-port", type=int, default=40000,
                   help="UDP port for cookie requests (default 40000)")
    p.add_argument("--target", required=True,
                   help="Target IP for protected packet (usually same as gateway)")
    p.add_argument("--target-port", type=int, default=9999,
                   help="Protected UDP port (default 9999)")
    p.add_argument("--recv-log", required=True,
                   help="Path to backend log file in victim namespace, e.g. /tmp/backend.log")
    p.add_argument("--payload", default="HELLO",
                   help="Application payload to append after cookie (default HELLO)")
    p.add_argument("--timeout", type=float, default=2.0,
                   help="Socket timeout in seconds for cookie reply (default 2.0)")
    return p.parse_args()


def request_cookie_and_send(args):
    """
    Use a single UDP socket so the source port used for COOKIE-REQ
    is the same source port used for the protected packet.
    This matches SimpleGateway.generate_cookie/verify_cookie,
    which binds the cookie to (client_ip, client_port, timestamp).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(args.timeout)

    # 1) Request cookie
    print(f"[*] Requesting cookie from {args.gateway}:{args.gateway_port}")
    s.sendto(b"COOKIE-REQ", (args.gateway, args.gateway_port))

    try:
        data, addr = s.recvfrom(4096)
    except socket.timeout:
        print("[!] Timed out waiting for cookie reply")
        sys.exit(2)

    if not data.startswith(b"COOKIE:"):
        print(f"[!] Unexpected cookie reply from {addr}: {data!r}")
        sys.exit(3)

    cookie = data[len(b"COOKIE:"):]
    if len(cookie) != 16:
        print(f"[!] Cookie length {len(cookie)} != 16")
        sys.exit(4)

    print("[*] Received cookie (hex):", binascii.hexlify(cookie).decode())

    # 2) Send protected packet using the SAME socket (same local port)
    payload_bytes = args.payload.encode()
    protected = cookie + payload_bytes

    print(f"[*] Sending protected packet to {args.target}:{args.target_port}")
    s.sendto(protected, (args.target, args.target_port))
    s.close()

    return cookie, payload_bytes


def wait_for_log_contains(path: Path, needle: bytes, timeout: float = 4.0) -> bool:
    """
    Poll the backend log file until 'needle' (cookie+payload) appears
    or timeout expires.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            try:
                data = path.read_bytes()
            except Exception:
                data = b""
            if needle in data:
                return True
        time.sleep(0.25)
    return False


def main():
    args = parse_args()
    recv_log = Path(args.recv_log)

    cookie, payload_bytes = request_cookie_and_send(args)
    expected = cookie + payload_bytes

    print(f"[*] Waiting for victim to record payload in {recv_log} (timeout 4s)")
    ok = wait_for_log_contains(recv_log, expected, timeout=4.0)
    if not ok:
        # a little extra slack in case of scheduling delays
        ok = wait_for_log_contains(recv_log, expected, timeout=2.0)

    if ok:
        print("[+] Protected packet observed in victim log.")
        sys.exit(0)
    else:
        print("[!] Protected packet NOT observed in victim log. Check listener and nets.")
        sys.exit(5)


if __name__ == "__main__":
    main()
