#!/usr/bin/env python3
"""legit_sender.py
A very simple UDP sender to act as a 'legitimate client' for experiments.
Usage (inside ns_attacker):
  sudo ip netns exec ns_attacker python3 legit_sender.py --target 10.200.1.2 --port 54321 --pps 10 --duration 20
"""
import socket, argparse, time

parser = argparse.ArgumentParser()
parser.add_argument("--target", required=True)
parser.add_argument("--port", type=int, required=True)
parser.add_argument("--pps", type=float, default=10.0)
parser.add_argument("--duration", type=int, default=20)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
interval = 1.0 / max(args.pps, 1.0)
end = time.time() + args.duration
count = 0
try:
    while time.time() < end:
        msg = f"hello {count}".encode()
        sock.sendto(msg, (args.target, args.port))
        count += 1
        time.sleep(interval)
except KeyboardInterrupt:
    pass
finally:
    print("Sent", count, "packets")
    sock.close()
