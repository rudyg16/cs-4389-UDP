#!/usr/bin/env bash
# Wrapper to run the sub-16-byte payload spray against the protected port from the attacker namespace.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS_ATTACKER="${NS_ATTACKER:-ns_attacker}"
TARGET_IP="${1:-10.200.1.2}"
TARGET_PORT="${2:-9999}"
PPS="${3:-5000}"
DURATION="${4:-10}"
PAYLOAD_BYTES="${5:-4}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo) so namespace exec works."
  exit 2
fi

if ! ip netns list | grep -q "$NS_ATTACKER"; then
  echo "Namespace $NS_ATTACKER not found. Run udp-shield-testbed/net_setup.py first."
  exit 1
fi

echo "[*] Launching short-payload attack from $NS_ATTACKER -> $TARGET_IP:$TARGET_PORT (pps=$PPS duration=${DURATION}s payload_bytes=$PAYLOAD_BYTES)"
ip netns exec "$NS_ATTACKER" python3 "$REPO_ROOT/udp-shield-testbed/short_payload_attack.py" \
  --target "$TARGET_IP" --port "$TARGET_PORT" --pps "$PPS" --duration "$DURATION" --payload-bytes "$PAYLOAD_BYTES"
