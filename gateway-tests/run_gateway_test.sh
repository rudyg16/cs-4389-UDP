#!/bin/bash
# Automated test runner for Simple Gateway v1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

LOG_FILE="/tmp/test_recv.log"
GATEWAY_LOG="/tmp/gateway.log"
BACKEND_LOG="/tmp/backend.log"

# Cleanup function
cleanup() {
    echo ""
    echo "[*] Cleaning up..."
    
    if [ ! -z "$GATEWAY_PID" ]; then
        kill $GATEWAY_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    rm -f "$LOG_FILE"
}

trap cleanup EXIT INT TERM

echo "=========================================="
echo "  Simple Gateway v1 - Test Runner"
echo "=========================================="
echo ""

# Clean up old files
rm -f "$LOG_FILE" "$GATEWAY_LOG" "$BACKEND_LOG"

# Start backend
echo "[*] Starting backend service..."
python3 "$PROJECT_DIR/gateway-modules/backend_service.py" \
    --port 9998 \
    --log-file "$LOG_FILE" \
    > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "    Backend PID: $BACKEND_PID"

sleep 1

# Start gateway
echo "[*] Starting gateway daemon..."
python3 "$PROJECT_DIR/gateway-modules/simple_gateway.py" \
    --cookie-port 40000 \
    --protected-port 9999 \
    --backend-host localhost \
    --backend-port 9998 \
    --verbose \
    > "$GATEWAY_LOG" 2>&1 &
GATEWAY_PID=$!
echo "    Gateway PID: $GATEWAY_PID"

sleep 2

# Check if processes are running
if ! kill -0 $GATEWAY_PID 2>/dev/null; then
    echo "[ERROR] Gateway failed to start"
    cat "$GATEWAY_LOG"
    exit 1
fi

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "[ERROR] Backend failed to start"
    cat "$BACKEND_LOG"
    exit 1
fi

echo ""

# Run tests
python3 "$SCRIPT_DIR/test_gateway.py"
TEST_RESULT=$?

echo ""
echo "=========================================="

if [ $TEST_RESULT -eq 0 ]; then
    echo "[SUCCESS] All tests passed!"
else
    echo "[FAILURE] Some tests failed"
    echo ""
    echo "Gateway log (last 20 lines):"
    tail -20 "$GATEWAY_LOG" 2>/dev/null || echo "  (no log)"
    echo ""
    echo "Backend log (last 20 lines):"
    tail -20 "$BACKEND_LOG" 2>/dev/null || echo "  (no log)"
fi

echo "=========================================="

exit $TEST_RESULT
