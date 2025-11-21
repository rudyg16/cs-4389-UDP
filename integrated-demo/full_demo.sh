#!/usr/bin/env bash
# integrated-demo/full_demo.sh
# Single entrypoint to demo and exercise all major UDP Shield components
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="${1:-/tmp/udp_shield_demo}"

mkdir -p "$LOG_DIR"
cd "$REPO_ROOT"

echo "========================================"
echo " UDP Shield Integrated Demo / Test Run"
echo " Logs: $LOG_DIR"
echo "========================================"
echo ""

step() {
  echo ""
  echo "[$1] $2"
  echo "----------------------------------------"
}

# 0) Quick environment notes
step "0/3" "Prereqs"
echo "- Expect WSL/Ubuntu with python3, clang/llvm, bpftool, scapy"
echo "- Root required for namespace+XDP portion (tests/run_tests.sh)"
echo ""

# 1) Gateway quick demo (backend + gateway + cookie client)
step "1/3" "Gateway quick demo"
bash "$REPO_ROOT/gateway-tests/quick_demo.sh" | tee "$LOG_DIR/gateway_quick_demo.log"

# 2) Gateway automated tests
step "2/3" "Gateway test suite"
bash "$REPO_ROOT/gateway-tests/run_gateway_test.sh" | tee "$LOG_DIR/gateway_tests.log"

# 3) Full namespace + XDP test suite (requires root)
if [ "$(id -u)" -ne 0 ]; then
  echo "[!] Skipping tests/run_tests.sh because this script is not running as root."
  echo "    Re-run with sudo to include namespace and XDP coverage."
else
  step "3/3" "Namespace + XDP integration tests"
  bash "$REPO_ROOT/tests/run_tests.sh" | tee "$LOG_DIR/full_stack_tests.log"
fi

echo ""
echo "========================================"
echo " Done. Key artifacts:"
echo " - $LOG_DIR/gateway_quick_demo.log"
echo " - $LOG_DIR/gateway_tests.log"
echo " - $LOG_DIR/full_stack_tests.log (if run as root)"
echo " - /tmp/test_results/* from tests/run_tests.sh"
echo "========================================"
