#!/usr/bin/env python3
"""
Simple UDP Gateway Daemon v1 - Basic Implementation
Provides cookie-based DDoS protection for UDP services
"""

import socket
import hmac
import hashlib
import time
import argparse
import sys
import threading
import secrets


class SimpleGateway:
    def __init__(self, cookie_port=40000, protected_port=9999, 
                 backend_host='localhost', backend_port=9998, verbose=False):
        self.cookie_port = cookie_port
        self.protected_port = protected_port
        self.backend_host = backend_host
        self.backend_port = backend_port
        self.verbose = verbose
        
        # HMAC secret for cookies
        self.secret = secrets.token_bytes(32)
        
        # Statistics
        self.cookies_issued = 0
        self.packets_forwarded = 0
        self.packets_dropped = 0
        
        self.running = False
    
    def generate_cookie(self, client_ip, client_port):
        """Generate a 16-byte HMAC-based cookie for a client"""
        timestamp = int(time.time())
        message = f"{client_ip}:{client_port}:{timestamp}".encode()
        h = hmac.new(self.secret, message, hashlib.sha256)
        return h.digest()[:16]
    
    def verify_cookie(self, cookie, client_ip, client_port, max_age=60):
        """Verify a cookie is valid and not expired"""
        if len(cookie) != 16:
            return False
        
        current_time = int(time.time())
        
        # Try timestamps within max_age window
        for offset in range(max_age + 1):
            timestamp = current_time - offset
            message = f"{client_ip}:{client_port}:{timestamp}".encode()
            h = hmac.new(self.secret, message, hashlib.sha256)
            expected = h.digest()[:16]
            
            if hmac.compare_digest(cookie, expected):
                return True
        
        return False
    
    def handle_cookie_requests(self):
        """Handle cookie issuance requests"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', self.cookie_port))
        
        print(f"[+] Cookie issuer listening on port {self.cookie_port}")
        
        while self.running:
            try:
                sock.settimeout(1.0)
                try:
                    data, addr = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                
                if data.startswith(b"COOKIE-REQ"):
                    cookie = self.generate_cookie(addr[0], addr[1])
                    sock.sendto(b"COOKIE:" + cookie, addr)
                    self.cookies_issued += 1
                    
                    if self.verbose:
                        print(f"[*] Issued cookie to {addr[0]}:{addr[1]} -> {cookie.hex()}")
                        
            except Exception as e:
                if self.running:
                    print(f"[!] Cookie handler error: {e}")
        
        sock.close()
    
    def handle_protected_traffic(self):
        """Handle protected traffic (verify cookies and forward)"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', self.protected_port))
        
        backend_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        print(f"[+] Protected port listening on port {self.protected_port}")
        
        while self.running:
            try:
                sock.settimeout(1.0)
                try:
                    data, addr = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                
                # Must have at least 16 bytes for cookie
                if len(data) < 16:
                    self.packets_dropped += 1
                    if self.verbose:
                        print(f"[!] Dropped short packet from {addr[0]}:{addr[1]}")
                    continue
                
                # Extract cookie and payload
                cookie = data[:16]
                payload = data[16:]
                
                # Verify cookie
                if self.verify_cookie(cookie, addr[0], addr[1]):
                    # Forward to backend
                    backend_sock.sendto(payload, (self.backend_host, self.backend_port))
                    self.packets_forwarded += 1
                    
                    if self.verbose:
                        print(f"[+] Forwarded packet from {addr[0]}:{addr[1]} ({len(payload)} bytes)")
                else:
                    self.packets_dropped += 1
                    if self.verbose:
                        print(f"[!] Dropped invalid cookie from {addr[0]}:{addr[1]}")
                        
            except Exception as e:
                if self.running:
                    print(f"[!] Protected traffic handler error: {e}")
        
        sock.close()
        backend_sock.close()
    
    def start(self):
        """Start the gateway daemon"""
        print("[*] Starting Simple UDP Gateway v1")
        print(f"    Cookie port: {self.cookie_port}")
        print(f"    Protected port: {self.protected_port}")
        print(f"    Backend: {self.backend_host}:{self.backend_port}")
        
        self.running = True
        
        # Start handler threads
        cookie_thread = threading.Thread(target=self.handle_cookie_requests, daemon=True)
        protected_thread = threading.Thread(target=self.handle_protected_traffic, daemon=True)
        
        cookie_thread.start()
        protected_thread.start()
        
        print("[+] Gateway running. Press Ctrl+C to stop.\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Shutting down...")
            self.stop()
    
    def stop(self):
        """Stop the gateway daemon"""
        self.running = False
        time.sleep(1)  # Give threads time to finish
        
        print("\n=== Statistics ===")
        print(f"Cookies issued: {self.cookies_issued}")
        print(f"Packets forwarded: {self.packets_forwarded}")
        print(f"Packets dropped: {self.packets_dropped}")
        print("==================")
        print("[+] Gateway stopped")


def main():
    parser = argparse.ArgumentParser(description='Simple UDP Gateway Daemon v1')
    parser.add_argument('--cookie-port', type=int, default=40000,
                        help='Port for cookie issuance (default: 40000)')
    parser.add_argument('--protected-port', type=int, default=9999,
                        help='Port for protected traffic (default: 9999)')
    parser.add_argument('--backend-host', default='localhost',
                        help='Backend service host (default: localhost)')
    parser.add_argument('--backend-port', type=int, default=9998,
                        help='Backend service port (default: 9998)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    gateway = SimpleGateway(
        cookie_port=args.cookie_port,
        protected_port=args.protected_port,
        backend_host=args.backend_host,
        backend_port=args.backend_port,
        verbose=args.verbose
    )
    
    gateway.start()


if __name__ == '__main__':
    main()
