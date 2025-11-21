# UDP SHIELD — TESTING & VALIDATION GUIDE (WSL)

## Overview
This guide provides complete instructions for installing dependencies, running tests, and validating the UDP Shield project inside **WSL (Ubuntu)**.

---

# 1. SYSTEM REQUIREMENTS

## 1.1 WSL Version
- WSL2 recommended  
- Ubuntu 22.04 or newer  

## 1.2 Required Tools
- Python 3.10+  
- pip  
- net-tools  
- clang / llvm  
- build-essential  
- tcpdump  
- bpftool  
- scapy (Python library)

---

# 2. INSTALLATION STEPS

## 2.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

## 2.2 Install Required Packages
```bash
sudo apt install -y python3 python3-pip tcpdump clang llvm make gcc bpftool net-tools
```

## 2.3 Install Python Dependencies
```bash
pip install scapy
```

---

# 3. REPOSITORY SETUP

## 3.1 Clone or Copy the Project
If cloning:
```bash
git clone <repo-url>
cd cs-4389-UDP
```

If copied into Downloads/etc:
```bash
cd ~/Downloads/code/cs-4389-UDP
```

---

# 4. BASIC FUNCTIONALITY TESTING

## 4.1 Run Gateway Quick Demo
```bash
bash gateway-tests/quick_demo.sh
```

This verifies:
- Cookie issuance  
- Gateway forwarding  
- Protected packet handling  

---

# 5. INTEGRATION TEST SUITE

The main test runner configures namespaces, starts services, runs BPF tests, and performs a full simulation.

## 5.1 Run Full Test Suite
```bash
sudo bash tests/run_tests.sh
```

This executes:
- Namespace setup  
- Cookie issuer test (`check_cookie.py`)  
- BPF/XDP compile + attach test (`check_bpfs.py`)  
- Full integration scenario (`integration_scenario.sh`)

---

# 6. VIEWING TEST OUTPUTS

## 6.1 List Test Results Directory
```bash
ls /tmp/test_results
```

## 6.2 View Logs Individually

### Cookie Test Output
```bash
sudo cat /tmp/test_results/check_cookie.out
```

### BPF/XDP Test Output
```bash
sudo cat /tmp/test_results/check_bpf.out
```

### Integration Scenario Output
```bash
sudo cat /tmp/test_results/integration.out
```

### Packet Capture (PCAP)
```bash
sudo tcpdump -r /tmp/test_results/integration.pcap
```

---

# 7. COMMON FIXES

## 7.1 Missing tcpdump
```bash
sudo apt install tcpdump
```

## 7.2 Missing kernel headers (BPF compilation errors)
```bash
sudo apt install linux-headers-$(uname -r)
```

## 7.3 Missing scapy
```bash
pip install scapy
```

---

# 8. CLEANUP AFTER TESTING

Delete namespaces:
```bash
sudo ip netns delete ns_attacker
sudo ip netns delete ns_victim
sudo ip netns delete ns_reflector
```

Stop background processes:
```bash
sudo pkill -f cookie_issuer.py
sudo pkill -f reflector_server.py
sudo pkill -f tcpdump
sudo pkill -f socat
```

---

# 9. CONTACT & SUPPORT
For questions, debugging help, or validation checks, refer to the course project instructions or contact your project teammate(s).
