#!/usr/bin/env python3
"""net_setup.py
Create an isolated Attacker-Victim-Reflector topology using Linux network namespaces.
Run as root: sudo python3 net_setup.py
"""
import subprocess, sys, shlex, os

NS = ["ns_attacker", "ns_victim", "ns_reflector"]

def run(cmd):
    print("+", cmd)
    subprocess.check_call(shlex.split(cmd))

def ns_exists(ns):
    out = subprocess.check_output(["ip", "netns", "list"]).decode()
    return ns in out

def main():
    if os.geteuid() != 0:
        print("ERROR: must run as root (sudo). Aborting.")
        sys.exit(1)

    # Clean up any previous namespaces we created (idempotent)
    for ns in NS:
        try:
            if ns_exists(ns):
                run(f"ip netns delete {ns}")
        except Exception:
            pass

    # Create namespaces
    for ns in NS:
        run(f"ip netns add {ns}")

    # Create veth pairs connecting them: attacker <-> victim and victim <-> reflector
    run("ip link add att_v type veth peer name v_att")
    run("ip link add vic_r type veth peer name v_vic")

    # Move ends into namespaces
    run("ip link set att_v netns ns_attacker")
    run("ip link set v_att netns ns_victim")
    run("ip link set vic_r netns ns_victim")
    run("ip link set v_vic netns ns_reflector")

    # Assign addresses and bring up loopbacks & links
    run("ip -n ns_attacker addr add 10.200.1.1/24 dev att_v")
    run("ip -n ns_victim addr add 10.200.1.2/24 dev v_att")
    run("ip -n ns_victim addr add 10.200.2.1/24 dev vic_r")
    run("ip -n ns_reflector addr add 10.200.2.2/24 dev v_vic")

    for ns in NS:
        run(f"ip -n {ns} link set lo up")

    run("ip -n ns_attacker link set att_v up")
    run("ip -n ns_victim link set v_att up")
    run("ip -n ns_victim link set vic_r up")
    run("ip -n ns_reflector link set v_vic up")

    # Enable IP forwarding in victim namespace (optional)
    run("ip netns exec ns_victim sysctl -w net.ipv4.ip_forward=1")

    print('\nSetup complete. To enter a namespace:')
    print("  sudo ip netns exec ns_attacker bash")
    print("  sudo ip netns exec ns_victim bash")
    print("  sudo ip netns exec ns_reflector bash")
    print('\nVerify with: ip -n ns_attacker addr show && ip -n ns_victim addr show && ip -n ns_reflector addr show')

if __name__ == '__main__':
    main()
