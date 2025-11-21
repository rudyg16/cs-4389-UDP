#!/usr/bin/env bash
# tests/integration_scenario.sh
# Run a short integration scenario:
#  - start capture on victim namespace
#  - send a legit cookie-protected packet
#  - send a short flood to the reflector
#  - stop capture and analyze pcap with capture_and_measure.py
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Defaults (can be overridden)
DURATION=${1:-8}
OUT=${2:-/tmp/integration.pcap}

# allow CLI flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --duration) DURATION="$2"; shift 2;;
    --out) OUT="$2"; shift 2;;
    *) break;;
  esac
done

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo). Aborting."
  exit 2
fi

NS_ATTACKER="ns_attacker"
NS_VICTIM="ns_victim"
NS_REFLECTOR="ns_reflector"

REFLECTOR="$REPO_ROOT/udp-shield-testbed/reflector_server.py"
COOKIE_ISSUER="$REPO_ROOT/cookie-handshake/cookie_issuer.py"
SEND_WITH_COOKIE="$REPO_ROOT/cookie-handshake/send_with_cookie.py"
CAPTURE="$REPO_ROOT/udp-shield-testbed/capture_and_measure.py"


# start capture inside victim namespace
echo "[*] Starting tcpdump capture inside $NS_VICTIM (duration ${DURATION}s) -> $OUT"
ip netns exec $NS_VICTIM python3 "$CAPTURE" --iface v_att --duration "$DURATION" --out "$OUT" &
CAP_PID=$!
sleep 0.5

# ensure cookie issuer running
ip netns exec $NS_VICTIM pgrep -f cookie_issuer.py >/dev/null || \
  ip netns exec $NS_VICTIM python3 "$COOKIE_ISSUER" --bind 10.200.1.2 --port 40000 --verbose > /dev/null 2>&1 &
sleep 0.5

# Trigger a legit cookie-protected packet from attacker
echo "[*] Attacker requesting cookie and sending protected packet"
ip netns exec $NS_ATTACKER python3 "$SEND_WITH_COOKIE" --gateway 10.200.1.2 --gateway-port 40000 --target 10.200.1.2 --target-port 9999 --payload "LEGIT" || true

# Short pause then flood reflector from attacker
echo "[*] Sending short flood to reflector from attacker (50 packets)"
ip netns exec $NS_ATTACKER python3 - <<'PY'
import socket, time
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for i in range(50):
    s.sendto(b'FLOOD'+bytes([i%256]), ("10.200.2.2", 12345))
    time.sleep(0.01)
s.close()
PY

# Wait for capture to finish
wait $CAP_PID || true

# Analyze pcap (run the analyzer; capture_and_measure will print outputs)
echo "[*] Analyzing pcap with capture_and_measure.py"
ip netns exec $NS_VICTIM python3 "$CAPTURE" --iface v_att --duration 0 --out "$OUT" || true

echo "[*] Integration scenario finished. pcap -> $OUT"
