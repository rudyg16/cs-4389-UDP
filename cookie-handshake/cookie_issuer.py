# Simple UDP cookie issuer
# ./cookie_issuer.py --bind 0.0.0.0 --port 40000

import socket, secrets, argparse, sys

parser = argparse.ArgumentParser()
parser.add_argument('--bind', default='0.0.0.0', help='IP to bind (default 0.0.0.0)')
parser.add_argument('--port', type=int, default=40000, help='Port to listen for requests')
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((args.bind, args.port))
print(f"cookie_issuer listening on {args.bind}:{args.port}")

try:
    while True:
        data, addr = sock.recvfrom(4096)
        if data.startswith(b"COOKIE-REQ"):
            cookie = secrets.token_bytes(16)
            sock.sendto(b"COOKIE:" + cookie, addr)
            if args.verbose:
                print(f"Issued cookie to {addr[0]}:{addr[1]} -> {cookie.hex()}")
        else:
            sock.sendto(b"ERR", addr)
except KeyboardInterrupt:
    print("\n[+] shutting down")
    sock.close()
    sys.exit(0)
