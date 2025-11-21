## Integrated Demo Runner

### What it does
- Runs the gateway quick demo.
- Runs the gateway automated tests.
- If executed as root, runs the full namespace + XDP test suite (`tests/run_tests.sh`), which sets up namespaces, cookie issuer, reflector, XDP attach, and the integration pcap capture. When not root, it skips this step with a notice.

### Usage
```
# From repo root
bash integrated-demo/full_demo.sh              # logs to /tmp/udp_shield_demo
bash integrated-demo/full_demo.sh /custom/dir  # optional log directory
```
Run with sudo if you want the namespace/XDP portion included:
```
sudo bash integrated-demo/full_demo.sh
```

### Outputs
- Logs from each stage are written to the chosen log directory.
- The namespace/XDP suite writes detailed artifacts to `/tmp/test_results` (pcap, per-test logs).

### Notes
- Requires the prerequisites listed in the top-level README (python3, clang/llvm, bpftool, scapy, etc.).
