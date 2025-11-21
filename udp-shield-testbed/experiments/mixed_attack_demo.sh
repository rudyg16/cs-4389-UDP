#!/usr/bin/env bash
# Run a quick sequence: legit cookie packet, spoofed flood, reflector burst.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/3] Legit cookie baseline"
"$DIR/legit_cookie_baseline.sh" 10.200.1.2 9999 "LEGIT-DEMO"

echo "[2/3] Spoofed flood"
"$DIR/spoofed_flood.sh" 10.200.1.2 54321 20000 6

echo "[3/3] Reflector burst"
"$DIR/reflector_burst.sh" 10.200.2.2 12345 200 0.01

echo "[*] Mixed attack demo completed. Check /tmp/test_results and/or captures for effects."
