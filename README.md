# UDP Shield — Master Runbook

Single-source instructions to install dependencies, bring up the full stack, run gateway/XDP/end-to-end tests, and replay experiments. All commands assume Ubuntu/WSL with root available for namespace/XDP steps.

## 1) Prerequisites
- Ubuntu 22.04+ (WSL2 recommended)
- Root/sudo for namespaces, tcpdump, XDP attach
- Git to clone this repo
- Required packages (incorporating the XDP README install tutorial): `python3` `python3-pip` `gcc` `make` `clang` `llvm` `bpftool` `net-tools` `iproute2` `tcpdump` `libbpf-dev` `libssl-dev` `gcc-multilib`
- Python deps: `pip install scapy`
- Optional: `socat` (nicer UDP listener)

Clone the repo:
```bash
git clone https://github.com/rudyg16/cs-4389-UDP.git
cd cs-4389-UDP
```

Install essentials:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip gcc make clang llvm bpftool tcpdump iproute2 net-tools libbpf-dev libssl-dev gcc-multilib socat
sudo pip3 install scapy
```

If `bpftool` is missing or kernel headers are unavailable, either build from bundled `bpftool/` (see `xdp/README.md` for the manual steps) or install headers:
```bash
sudo apt install linux-headers-$(uname -r)
```

## 2) Repo layout
- Gateway: `gateway-modules/` (simple gateway + backend), `cookie-handshake/` (issuer/client)
- XDP fast path: `xdp/xdp_packet_tracer.c` (+ `xdp/Makefile`)
- Namespace testbed + traffic/attacks: `udp-shield-testbed/` and `udp-shield-testbed/experiments/`
- Automated runs: `gateway-tests/`, `tests/` (rooted full suite), `integrated-demo/`
- Docs artifacts land in `/tmp/test_results` or a chosen log dir

For deeper, task-specific instructions:
- Detailed XDP build/attach guidance: `xdp/README.md` (includes bpftool build steps and interface selection)
- Standalone testbed quick start: `udp-shield-testbed/docs/quick_start.md`
- Experiment scenarios and usage: `udp-shield-testbed/experiments/README.md`
- Integrated demo overview: `integrated-demo/README.md`

## 3) Quick health checks (no root)
1) Gateway quick demo:
```bash
bash gateway-tests/quick_demo.sh
```
Shows cookie issuance, gateway forwarding, backend receive.

2) Gateway test suite:
```bash
bash gateway-tests/run_gateway_test.sh
```
Runs integration tests in-process; logs go to `/tmp`.

## 4) Full-stack test harness (root)
Runs namespaces, cookie issuer, reflector, BPF compile/attach, and integration capture.
```bash
sudo bash tests/run_tests.sh
```
Artifacts: `/tmp/test_results/{check_cookie.out,check_bpf.out,integration.out,integration.pcap,recv.log,...}` plus service logs.

## 5) Integrated one-button demo
Chains gateway demos and (when root) the full stack. Optional arg sets log dir.
```bash
# without root: gateway-only parts
bash integrated-demo/full_demo.sh /tmp/udp_shield_demo

# with root: includes namespace+XDP suite
sudo bash integrated-demo/full_demo.sh /tmp/udp_shield_demo
```
Key logs: `gateway_quick_demo.log`, `gateway_tests.log`, optional `full_stack_tests.log`; see `/tmp/test_results` for pcaps/logs from the full suite.

## 6) Manual namespace testbed workflow (root)
Bring up topology, run services, send traffic, capture, and tear down.
```bash
sudo python3 udp-shield-testbed/net_setup.py            # create ns_attacker/ns_victim/ns_reflector

# Start reflector (ns_reflector)
sudo ip netns exec ns_reflector python3 udp-shield-testbed/reflector_server.py --port 12345 --max-responses-per-sec 200 &

# Start cookie issuer (ns_victim)
sudo ip netns exec ns_victim python3 cookie-handshake/cookie_issuer.py --bind 10.200.1.2 --port 40000 --verbose &

# Optional listener on protected port (ns_victim)
sudo ip netns exec ns_victim socat -u UDP-RECV:9999 SYSTEM:'tee -a /tmp/test_results/recv.log' &

# Legit cookie-protected packet from attacker
sudo ip netns exec ns_attacker python3 cookie-handshake/send_with_cookie.py --gateway 10.200.1.2 --gateway-port 40000 --target 10.200.1.2 --target-port 9999 --payload HELLO

# Capture + summarize
sudo ip netns exec ns_victim python3 udp-shield-testbed/capture_and_measure.py --iface v_att --duration 10 --out /tmp/test_results/manual_capture.pcap
```

Cleanup:
```bash
sudo ip netns delete ns_attacker ns_victim ns_reflector || true
sudo pkill -f 'cookie_issuer.py|reflector_server.py|tcpdump|socat' || true
```

## 7) XDP fast-path only (manual)
Adjust `NET_INTERFACE` in `xdp/Makefile` to your NIC, then:
```bash
cd xdp
make build
sudo make link            # attach XDP
# send UDP traffic toward the host (port 9999 protected, 40000 cookie)
sudo bpftool map dump name pkt_cnt_by_saddr
sudo bpftool map dump name pkt_cnt_by_dport
sudo make unlink          # detach when done
```
Note: fast-path cookie precheck expects `valid_cookies` map populated by a user-space agent (not yet wired here).

## 8) Experiment scripts (on top of testbed, root)
Assumes namespaces up and cookie issuer running on 10.200.1.2:40000.
```bash
# Legit single packet
sudo bash udp-shield-testbed/experiments/legit_cookie_baseline.sh 10.200.1.2 9999 "PAYLOAD"

# Spoofed flood (raw packets)
sudo bash udp-shield-testbed/experiments/spoofed_flood.sh 10.200.1.2 54321 20000 6

# Reflector burst
sudo bash udp-shield-testbed/experiments/reflector_burst.sh 10.200.2.2 12345 200 0.01

# Mixed sequence (baseline + flood + reflector)
sudo bash udp-shield-testbed/experiments/mixed_attack_demo.sh
```
Inspect effects via `/tmp/test_results/` logs or captures.
