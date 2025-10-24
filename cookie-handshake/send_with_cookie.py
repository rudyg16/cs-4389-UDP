# Requests a cookie from the gateway then sends a UDP packet to the protected service
# python3 send_with_cookie.py --gateway <VICTIM_IP> --gateway-port 40000 --target <VICTIM_IP> --target-port 9999

import socket, argparse, sys, time

parser = argparse.ArgumentParser()
parser.add_argument('--gateway', required=True, help='IP of cookie issuer')
parser.add_argument('--gateway-port', type=int, default=40000)
parser.add_argument('--target', required=True, help='Target IP to send protected packet')
parser.add_argument('--target-port', type=int, default=9999)
parser.add_argument('--payload', default='HELLO', help='extra payload after cookie')
parser.add_argument('--timeout', type=float, default=2.0)
args = parser.parse_args()

g = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
g.settimeout(args.timeout)
g.sendto(b"COOKIE-REQ", (args.gateway, args.gateway_port))
try:
    data, _ = g.recvfrom(4096)
except Exception as e:
    print("No reply from gateway:", e); sys.exit(1)

if not data.startswith(b"COOKIE:"):
    print("Unexpected reply:", data); sys.exit(1)

cookie = data[len(b"COOKIE:"):]
print("Received cookie:", cookie.hex())

t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
t.sendto(cookie + args.payload.encode(), (args.target, args.target_port))
print(f"Sent protected packet to {args.target}:{args.target_port}")

