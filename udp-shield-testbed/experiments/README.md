## UDP Shield Experiments

These scripts layer simple traffic/attack scenarios on top of the existing namespace testbed. Run them after the namespaces are up (`sudo python3 udp-shield-testbed/net_setup.py` or via `tests/run_tests.sh`), and execute as root so namespace exec and raw sockets work.

**Assumptions / prerequisites**
- Namespaces `ns_attacker/ns_victim/ns_reflector` exist.
- Cookie issuer running in ns_victim on IP:port, e.g.:
  `sudo ip netns exec ns_victim python3 cookie-handshake/cookie_issuer.py --bind 10.200.1.2 --port 40000 --verbose &`
- Reflector running in ns_reflector (only needed for reflector scenarios):
  `sudo ip netns exec ns_reflector python3 udp-shield-testbed/reflector_server.py --port 12345 &`
- Run these scripts with sudo.

**Scenarios**
- `legit_cookie_baseline.sh` — from ns_attacker, request a cookie and send one protected packet to the victim’s protected port.
- `spoofed_flood.sh` — from ns_attacker, generate a spoofed-source UDP flood at configurable pps/duration/port using the raw-packet spoofer.
- `reflector_burst.sh` — from ns_attacker, send a short burst to the reflector (defaults 10.200.2.2:12345) to exercise reflection-style traffic.
- `low_and_slow.sh` — from ns_attacker, send low-rate jittered UDP traffic to a chosen port (defaults 10.200.1.2:54321) to mimic low-and-slow behavior.
- `invalid_cookie_attack.sh` — from ns_attacker, send fabricated “invalid cookie” style payloads to the reflector (defaults 10.200.2.2:12345).
- `short_payload_attack.sh` — from ns_attacker, spray sub-16-byte payloads at the protected port (defaults 10.200.1.2:9999) to trigger cookie-length drops.
- `portscan_flood.sh` — from ns_attacker, high-rate UDP spray across random destination ports (excluding 40000/9999) to exercise the port allowlist.
- `mixed_attack_demo.sh` — runs the original three (legit baseline + spoofed flood + reflector burst) sequentially with defaults; check `/tmp/test_results` or your capture logs for effects.

**Outputs**
- Listener/issuer/reflector logs land in `/tmp/test_results` when started with the provided commands or via `tests/run_tests.sh`.
- If you capture traffic, point outputs to `/tmp/test_results` (or another path) and inspect with tcpdump/scapy as needed.

Usage examples:
```bash
sudo bash udp-shield-testbed/experiments/legit_cookie_baseline.sh 10.200.1.2 9999 "YOUR-PAYLOAD"
sudo bash udp-shield-testbed/experiments/spoofed_flood.sh 10.200.1.2 54321 20000 6
sudo bash udp-shield-testbed/experiments/reflector_burst.sh 10.200.2.2 12345 200 0.01
sudo bash udp-shield-testbed/experiments/low_and_slow.sh 10.200.1.2 54321 2 60
sudo bash udp-shield-testbed/experiments/invalid_cookie_attack.sh 10.200.2.2 12345 5000 10
sudo bash udp-shield-testbed/experiments/short_payload_attack.sh 10.200.1.2 9999 5000 10 4
sudo bash udp-shield-testbed/experiments/portscan_flood.sh 10.200.1.2 20000 8 1025 65535
sudo bash udp-shield-testbed/experiments/mixed_attack_demo.sh
```

All commands assume namespaces `ns_attacker/ns_victim/ns_reflector` exist and the cookie issuer is reachable on 10.200.1.2:40000. Adjust IPs/ports if you deviated from the default topology. Logs/captures still live in `/tmp/test_results` when using the main test runner.***
