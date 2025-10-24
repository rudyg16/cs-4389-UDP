#!/usr/bin/env python3
"""reflector_server.py - simple UDP reflector (run in ns_reflector)
"""
import socket, argparse, time

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", type=int, default=12345)
parser.add_argument("--max-responses-per-sec", type=float, default=500.0)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((args.host, args.port))
print(f"Reflector listening on {args.host}:{args.port}")

last_ts = time.time()
resp_count = 0

try:
    while True:
        data, addr = sock.recvfrom(4096)
        now = time.time()
        if now - last_ts >= 1.0:
            last_ts = now
            resp_count = 0
        if resp_count >= args.max_responses_per_sec:
            continue
        payload = data[:64]
        resp = b"ACK:" + payload[:200]
        sock.sendto(resp, addr)
        resp_count += 1
except KeyboardInterrupt:
    print("Shutting down reflector")
finally:
    sock.close()
