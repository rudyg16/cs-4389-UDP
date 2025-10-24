#!/usr/bin/env bash
# tests/run_tests.sh
# Orchestrates the test environment and runs the smaller checks.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTDIR="/tmp/test_results"
NETSETUP="$REPO_ROOT/net_setup.py"
COOKIE_ISSUER="$REPO_ROOT/cookie_issuer.py"
REFLECTOR="$REPO_ROOT/reflector_server.py"
LEGIT_SENDER="$REPO_ROOT/legit_sender.py"
CAPTURE="$REPO_ROOT/capture_and_measure.py"
PKT_C="$REPO_ROOT/pkt_tracker.c"

NS_ATTACKER="ns_attacker"
NS_VICTIM="ns_victim"
NS_REFLECTOR="ns_reflector"

# Ensure root
if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root (sudo). Aborting."
  exit 2
fi

mkdir -p "$TESTDIR"
echo "[*] test output dir: $TESTDIR"

cleanup() {
  echo "[*] cleaning up..."
  pkill -f cookie_issuer.py || true
  pkill -f reflector_server.py || true
  pkill -f socat || true
  pkill -f tcpdump || true
  # Delete namespaces created by net_setup.py (idempotent)
  for ns in $NS_ATTACKER $NS_VICTIM $NS_REFLECTOR; do
    ip netns delete "$ns" 2>/dev/null || true
  done
}
trap cleanup EXIT

# 0. Create network namespaces and verify
echo "[*] Creating network namespaces using $NETSETUP"
python3 "$NETSETUP"

echo "[*] Starting services in namespaces..."

# Start reflector (ns_reflector)
ip netns exec $NS_REFLECTOR python3 "$REFLECTOR" --port 12345 --max-responses-per-sec 200 \
  > "$TESTDIR/reflector.log" 2>&1 &
sleep 0.5
echo "[*] reflector started (ns_reflector) -> $TESTDIR/reflector.log"

# Start cookie issuer in ns_victim
ip netns exec $NS_VICTIM python3 "$COOKIE_ISSUER" --bind 10.200.1.2 --port 40000 --verbose \
  > "$TESTDIR/cookie_issuer.log" 2>&1 &
sleep 0.5
echo "[*] cookie_issuer started (ns_victim) -> $TESTDIR/cookie_issuer.log"

# Start simple listener on victim port 9999 to capture protected packets
# Using socat if available; otherwise fallback to nc -u -l
RECV_LOG="$TESTDIR/recv.log"
if command -v socat >/dev/null 2>&1; then
  ip netns exec $NS_VICTIM socat -u UDP-RECV:9999 SYSTEM:'tee -a $RECV_LOG' &
else
  # busybox/nc style
  ip netns exec $NS_VICTIM bash -c "nc -u -l 9999 >> $RECV_LOG" &
fi
sleep 0.5
echo "[*] victim UDP listener running -> $RECV_LOG"

# Run basic cookie check
echo "[*] Running tests/check_cookie.py (from attacker namespace)..."
ip netns exec $NS_ATTACKER python3 "$REPO_ROOT/tests/check_cookie.py" \
  --gateway 10.200.1.2 --gateway-port 40000 \
  --target 10.200.1.2 --target-port 9999 \
  --recv-log "$RECV_LOG" \
  > "$TESTDIR/check_cookie.out" 2>&1 || {
    echo "[!] check_cookie failed, see $TESTDIR/check_cookie.out"
    exit 1
  }
echo "[+] check_cookie passed."

# Run BPF check (compile/attach + basic map inspection)
echo "[*] Running tests/check_bpfs.py (will compile pkt_tracker.c and attach in victim ns)..."
ip netns exec $NS_VICTIM python3 "$REPO_ROOT/tests/check_bpfs.py" \
  --c-file "$PKT_C" \
  --iface v_att \
  --probe-src 10.200.1.1 \
  --probe-port 54321 \
  > "$TESTDIR/check_bpf.out" 2>&1 || {
    echo "[!] check_bpfs failed, see $TESTDIR/check_bpf.out"
    exit 1
  }
echo "[+] check_bpfs passed."

# Run integration scenario (longer, creates pcap)
echo "[*] Running integration scenario (this takes ~10s)..."
ip netns exec $NS_VICTIM python3 "$REPO_ROOT/tests/integration_scenario.sh" \
  --duration 8 --out "$TESTDIR/integration.pcap" \
  > "$TESTDIR/integration.out" 2>&1 || {
    echo "[!] integration scenario failed, see $TESTDIR/integration.out"
    exit 1
  }
echo "[+] integration scenario completed. pcap: $TESTDIR/integration.pcap"

echo "[*] All tests passed. Inspect $TESTDIR for logs and outputs."
