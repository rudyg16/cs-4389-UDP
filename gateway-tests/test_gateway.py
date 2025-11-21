#!/usr/bin/env python3
"""
Basic integration tests for Simple Gateway v1
"""

import socket
import time
import sys
from pathlib import Path


def test_cookie_request(host='127.0.0.1', port=40000):
    """Test 1: Request a cookie"""
    print("\n[TEST 1] Requesting cookie...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    
    try:
        sock.sendto(b"COOKIE-REQ", (host, port))
        data, _ = sock.recvfrom(4096)
        
        if not data.startswith(b"COOKIE:"):
            print(f"  [FAIL] Unexpected response: {data}")
            sock.close()
            return None, None
        
        cookie = data[7:]  # Skip "COOKIE:" prefix
        
        if len(cookie) != 16:
            print(f"  [FAIL] Invalid cookie length: {len(cookie)}")
            sock.close()
            return None, None
        
        print(f"  [PASS] Received 16-byte cookie: {cookie.hex()}")
        # IMPORTANT: do NOT close sock here – we reuse it in Test 2
        return sock, cookie
        
    except socket.timeout:
        print("  [FAIL] Timeout - is gateway running?")
        sock.close()
        return None, None



def test_valid_packet(sock, cookie, host='127.0.0.1', port=9999):
    """Test 2: Send valid packet with cookie"""
    print("\n[TEST 2] Sending packet with valid cookie...")

    try:
        payload = b"TEST_PAYLOAD_VALID"
        packet = cookie + payload
        sock.sendto(packet, (host, port))

        print(f"  [PASS] Sent packet with cookie ({len(payload)} bytes payload)")
        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False
    finally:
        sock.close()


def test_invalid_packet(host='127.0.0.1', port=9999):
    """Test 3: Send packet with fake cookie (should be dropped)"""
    print("\n[TEST 3] Sending packet with invalid cookie...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        fake_cookie = b'\x00' * 16
        payload = b"SHOULD_BE_DROPPED"
        packet = fake_cookie + payload
        sock.sendto(packet, (host, port))
        print(f"  [PASS] Sent packet with fake cookie (gateway should drop it)")
        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False
    finally:
        sock.close()


def verify_backend_log(log_file, expected, should_exist=True):
    """Verify backend received (or didn't receive) expected data"""
    time.sleep(1)  # Give time for packet to be processed
    
    log_path = Path(log_file)
    
    if not log_path.exists():
        if should_exist:
            print(f"  [FAIL] Log file doesn't exist: {log_file}")
            return False
        else:
            print(f"  [PASS] Log file doesn't exist (as expected)")
            return True
    
    data = log_path.read_bytes()
    
    if should_exist:
        if expected in data:
            print(f"  [PASS] Backend received expected payload")
            return True
        else:
            print(f"  [FAIL] Backend did NOT receive expected payload")
            return False
    else:
        if expected not in data:
            print(f"  [PASS] Backend correctly did NOT receive payload")
            return True
        else:
            print(f"  [FAIL] Backend received payload that should have been dropped")
            return False


def run_tests():
    """Run all tests"""
    print("="*60)
    print("Simple Gateway v1 - Integration Tests")
    print("="*60)
    
    print("\nPrerequisites:")
    print("  1. Gateway running: python3 gateway-modules/simple_gateway.py -v")
    print("  2. Backend running: python3 gateway-modules/backend_service.py --log-file /tmp/test_recv.log")
    
    LOG_FILE = '/tmp/test_recv.log'
    
    # Clean up old log
    log_path = Path(LOG_FILE)
    if log_path.exists():
        log_path.unlink()
    
    passed = 0
    total = 5
    
    # Test 1: Get cookie
    sock, cookie = test_cookie_request()
    if cookie:
        passed += 1
    else:
        print("\n[ABORT] Cannot continue without cookie")
        return 1
    
    # Test 2: Send valid packet
    if test_valid_packet(sock, cookie):
        passed += 1
    
    # Test 3: Verify backend received it
    print("\n[TEST 4] Verifying backend received valid packet...")
    if verify_backend_log(LOG_FILE, b"TEST_PAYLOAD_VALID", should_exist=True):
        passed += 1
    
    # Test 4: Send invalid packet
    if test_invalid_packet():
        passed += 1
    
    # Test 5: Verify backend did NOT receive invalid packet
    print("\n[TEST 5] Verifying backend did NOT receive invalid packet...")
    if verify_backend_log(LOG_FILE, b"SHOULD_BE_DROPPED", should_exist=False):
        passed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("[SUCCESS] All tests passed! ✓\n")
        return 0
    else:
        print(f"[FAILURE] {total - passed} test(s) failed\n")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
