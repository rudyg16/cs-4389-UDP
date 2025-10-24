# Prerequisites
VM Victim Hardware Minimum:
- Ubuntu 24.04.3
- Processor: 2
- Memory: 4 GB
- Hard Disk: 20 GB
- Network Adapter: NAT

VM Attacker Hardware Minimum:
- Ubuntu 24.04.3
- Processor: 2
- Memory: 4 GB
- Hard Disk: 20 GB
- Network Adapter: NAT

# Instructions
Install python3.<br/>
```sh
sudo apt instal python3-pip
```

Install clang, llvm, libbpf and make.
```sh
sudo apt-get install clang llvm libbpf-dev make -y
```

Install git.
```sh
sudo apt install git
```

Install openssl.
```sh
sudo apt-get install libssl-dev
```

Install gcc-multilib.
```sh
sudo apt-get install gcc-multilib
```

Install bpftool. (Recommend installing this in home directory)
```sh
git clone --recurse-submodules https://github.com/libbpf/bpftool.git
```
Then, cd into bpftool and run:
```sh
git submodule update --init
```
Build bpftool:
```sh
cd src
make
```
Then install bpftool:
```sh
cd src
sudo make install
```
Note: only run `cd src` if that is not the current working directory.

<br/>
<br/>
NOTE: ONLY PERFORM THIS IF NECESSARY. READ BELOW. 
If you try to run bpftool but it says there is no bpftool for version 6.14 then do the following steps.<br/>
Move bpftool to a directory in your PATH:

```sh
sudo mv ~/bpftool/src/bpftool /usr/local/bin/
```

Verify
```sh
which bpftool
bpftool version
```

---

# How to Run
IMPORTANT STEP: Before you run the commands below, first check what your network interface is.
Run this command to check:
```sh
ip addr
```
Your network interface should be the second interface. The one that does not have `127.0.0.1` as its IP address.<br/>
Then edit the Makefile and change the `NET_INTERFACE` to your network interface.<br/>

To the run the program first run:
```sh
make build
```

then run:
```sh
make link
```
This attaches the XDP to the network interface.
<br/>

Run this command to check your current UDP traffic:
```sh
sudo bpftool map dump name pkt_cnt_by_sadd
```
<br/>

Now on another VM, spin it up and ensure you can communicate to the first VM.<br/>
Once you confirm that the two VMs are able to communicate, on the second VM run this command:
```sh
echo "hello" | nc -u <first-VM-IP-address> 9999
```
Then go back to the first VM and run this command again and notice the difference.
```sh
sudo bpftool map dump name pkt_cnt_by_sadd
```
They `key` is your IP address in 32-bit integer. You can convert it to dotted notation to verify it came from the second VM.<br/>
There will be 2 IP addresses: one is the gateway, one is the VM.
<br/>

When you are done with testing, run the command to unlink XDP from the NIC:
```sh
make unlink
```

Additionally, you can run this command to clean up:
```sh
make clean
```
