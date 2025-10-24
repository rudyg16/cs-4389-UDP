# Quick Start

1. Install prerequisites:
   ```
   sudo apt update
   sudo apt install -y python3 python3-pip tcpdump iproute2 netcat
   sudo pip3 install scapy
   ```

2. Run topology setup:
   ```
   sudo python3 ./net_setup.py
   ```

3. Start reflector (in a separate terminal or background):
   ```
   sudo ip netns exec ns_reflector python3 reflector_server.py --port 12345
   ```

4. Capture on victim (in another terminal):
   ```
   sudo ip netns exec ns_victim python3 capture_and_measure.py --iface v_att --duration 20 --out victim_capture.pcap
   ```

5. Generate traffic from attacker (in another terminal):
   ```
   sudo ip netns exec ns_attacker python3 legit_sender.py --target 10.200.1.2 --port 54321 --pps 10 --duration 20
   ```

6. Inspect results:
   ```
   sudo ip netns exec ns_victim tcpdump -nn -r victim_capture.pcap -c 20
   ```

7. Cleanup:
   ```
   sudo ip netns delete ns_attacker || true
   sudo ip netns delete ns_victim || true
   sudo ip netns delete ns_reflector || true
   ```
