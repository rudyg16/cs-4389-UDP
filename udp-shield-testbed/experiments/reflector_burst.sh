#!/usr/bin/env bash
# Send a short burst to the reflector from the attacker namespace (non-spoofed).
set -euo pipefail

NS_ATTACKER="${NS_ATTACKER:-ns_attacker}"
REFLECTOR_IP="${1:-10.200.2.2}"
REFLECTOR_PORT="${2:-12345}"
COUNT="${3:-200}"
SLEEP="${4:-0.01}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo) so namespace exec works."
  exit 2
fi

if ! ip netns list | grep -q "$NS_ATTACKER"; then
  echo "Namespace $NS_ATTACKER not found. Run udp-shield-testbed/net_setup.py first."
  exit 1
fi

echo "[*] Sending $COUNT packets to reflector $REFLECTOR_IP:$REFLECTOR_PORT from $NS_ATTACKER"
ip netns exec "$NS_ATTACKER" python3 - "$REFLECTOR_IP" "$REFLECTOR_PORT" "$COUNT" "$SLEEP" <<'PY'
import socket, sys, time
ref_ip, ref_port = sys.argv[1], int(sys.argv[2])
count, pause = int(sys.argv[3]), float(sys.argv[4])
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for i in range(count):
    s.sendto(b"REFLECT"+bytes([i % 256]), (ref_ip, ref_port))
    time.sleep(pause)
s.close()
print("Sent", count, "packets")
PY
