#!/usr/bin/env bash
# Wrapper to run the random-port UDP spray from the attacker namespace.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS_ATTACKER="${NS_ATTACKER:-ns_attacker}"
TARGET_IP="${1:-10.200.1.2}"
PPS="${2:-20000}"
DURATION="${3:-8}"
MIN_PORT="${4:-1025}"
MAX_PORT="${5:-65535}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo) so namespace exec works."
  exit 2
fi

if ! ip netns list | grep -q "$NS_ATTACKER"; then
  echo "Namespace $NS_ATTACKER not found. Run udp-shield-testbed/net_setup.py first."
  exit 1
fi

echo "[*] Launching port-scan flood from $NS_ATTACKER -> $TARGET_IP (pps=$PPS duration=${DURATION}s ports=${MIN_PORT}-${MAX_PORT}, excluding 40000/9999)"
ip netns exec "$NS_ATTACKER" python3 "$REPO_ROOT/udp-shield-testbed/portscan_flood.py" \
  --target "$TARGET_IP" --pps "$PPS" --duration "$DURATION" --min-port "$MIN_PORT" --max-port "$MAX_PORT"
