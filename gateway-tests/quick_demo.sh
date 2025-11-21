#!/bin/bash
# Quick demo of the Simple Gateway v1
# This script shows the gateway in action


echo "This demo will:"
echo "  1. Start a backend service"
echo "  2. Start the gateway daemon"
echo "  3. Send a test packet using the existing client"
echo "  4. Show the results"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "[*] Cleaning up..."
    [ ! -z "$GATEWAY_PID" ] && kill $GATEWAY_PID 2>/dev/null || true
    [ ! -z "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
    #rm -f /tmp/demo_recv.log
    echo "[+] Done"
}

trap cleanup EXIT INT TERM

# Start backend
echo "[1] Starting backend service on port 9998..."
python3 gateway-modules/backend_service.py \
    --port 9998 \
    --log-file /tmp/demo_recv.log \
    > /tmp/demo_backend.log 2>&1 &
BACKEND_PID=$!
sleep 1

# Start gateway
echo "[2] Starting gateway daemon..."
python3 gateway-modules/simple_gateway.py \
    --verbose \
    > /tmp/demo_gateway.log 2>&1 &
GATEWAY_PID=$!
sleep 2

echo "[3] Sending test packet..."
echo ""

# Send packet using existing client
python3 cookie-handshake/send_with_cookie.py \
    --gateway 127.0.0.1 \
    --gateway-port 40000 \
    --target 127.0.0.1 \
    --target-port 9999 \
    --payload "Hello from Simple Gateway v1!"

sleep 1

echo ""
echo "[4] Results:"
echo ""
echo "--- Gateway Log ---"
tail -15 /tmp/demo_gateway.log
echo ""
echo "--- Backend Received ---"
if [ -f /tmp/demo_recv.log ]; then
    echo "Data: $(cat /tmp/demo_recv.log)"
    echo "Success! Backend received the payload."
else
    echo "No data received (check logs)"
fi

echo ""
echo "========================================"
echo "Demo complete! The gateway is working."
echo "========================================"
