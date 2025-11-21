#!/usr/bin/env bash
# Wrapper to launch the raw spoofed flood from the attacker namespace.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS_ATTACKER="${NS_ATTACKER:-ns_attacker}"
TARGET_IP="${1:-10.200.1.2}"
TARGET_PORT="${2:-54321}"
PPS="${3:-20000}"
DURATION="${4:-6}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo) so namespace exec and raw sockets work."
  exit 2
fi

if ! ip netns list | grep -q "$NS_ATTACKER"; then
  echo "Namespace $NS_ATTACKER not found. Run udp-shield-testbed/net_setup.py first."
  exit 1
fi

echo "[*] Launching spoofed flood from $NS_ATTACKER -> $TARGET_IP:$TARGET_PORT (pps=$PPS duration=${DURATION}s)"
ip netns exec "$NS_ATTACKER" python3 "$REPO_ROOT/udp-shield-testbed/spoofed_flood.py" \
  --target "$TARGET_IP" --port "$TARGET_PORT" --pps "$PPS" --duration "$DURATION"
