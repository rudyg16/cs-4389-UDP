#!/usr/bin/env python3
"""
Simple UDP Backend Service
Receives and logs forwarded packets from the gateway
"""

import socket
import argparse
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Simple UDP Backend Service')
    parser.add_argument('--port', type=int, default=9998,
                        help='Port to listen on (default: 9998)')
    parser.add_argument('--log-file', type=str,
                        help='File to log received packets')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', args.port))
    
    print(f"[+] Backend service listening on port {args.port}")
    if args.log_file:
        print(f"[+] Logging to: {args.log_file}")
    
    packet_count = 0
    
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            packet_count += 1
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            if args.verbose:
                print(f"[{timestamp}] Packet #{packet_count} from {addr[0]}:{addr[1]}")
                print(f"  Length: {len(data)} bytes")
                print(f"  Data: {data[:100]}")  # First 100 bytes
            else:
                print(f"[{timestamp}] Received {len(data)} bytes from {addr[0]}:{addr[1]}")
            
            # Log to file
            if args.log_file:
                with open(args.log_file, 'ab') as f:
                    f.write(data)
                    
    except KeyboardInterrupt:
        print(f"\n[*] Shutting down. Total packets: {packet_count}")
        sock.close()
        sys.exit(0)


if __name__ == '__main__':
    main()
