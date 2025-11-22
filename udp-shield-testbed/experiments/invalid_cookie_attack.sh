#!/usr/bin/env bash
# Wrapper to run the invalid-cookie reflector-style attack from the attacker namespace.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS_ATTACKER="${NS_ATTACKER:-ns_attacker}"
TARGET_IP="${1:-10.200.2.2}"
TARGET_PORT="${2:-12345}"
PPS="${3:-5000}"
DURATION="${4:-10}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo) so namespace exec works."
  exit 2
fi

if ! ip netns list | grep -q "$NS_ATTACKER"; then
  echo "Namespace $NS_ATTACKER not found. Run udp-shield-testbed/net_setup.py first."
  exit 1
fi

echo "[*] Launching invalid-cookie attack from $NS_ATTACKER -> $TARGET_IP:$TARGET_PORT (pps=$PPS duration=${DURATION}s)"
ip netns exec "$NS_ATTACKER" python3 "$REPO_ROOT/udp-shield-testbed/invalid_cookie_attack.py" \
  --target "$TARGET_IP" --port "$TARGET_PORT" --pps "$PPS" --duration "$DURATION"
