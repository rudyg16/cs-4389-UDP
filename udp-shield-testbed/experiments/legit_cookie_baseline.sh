#!/usr/bin/env bash
# Send one cookie-protected packet from the attacker namespace to the victim protected port.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS_ATTACKER="${NS_ATTACKER:-ns_attacker}"
GATEWAY_IP="${1:-10.200.1.2}"
PROTECTED_PORT="${2:-9999}"
PAYLOAD="${3:-LEGIT-BASELINE}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo) so namespace exec works."
  exit 2
fi

if ! ip netns list | grep -q "$NS_ATTACKER"; then
  echo "Namespace $NS_ATTACKER not found. Run udp-shield-testbed/net_setup.py first."
  exit 1
fi

echo "[*] Sending cookie-protected packet from $NS_ATTACKER to $GATEWAY_IP:$PROTECTED_PORT"
ip netns exec "$NS_ATTACKER" python3 "$REPO_ROOT/cookie-handshake/send_with_cookie.py" \
  --gateway "$GATEWAY_IP" --gateway-port 40000 \
  --target "$GATEWAY_IP" --target-port "$PROTECTED_PORT" \
  --payload "$PAYLOAD"
