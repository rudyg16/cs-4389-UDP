# Instructions
Install python3.<br/>
```sh
sudo apt instal python3-pip
```

Install clang, llvm, libbpf and make
```sh
sudo apt-get install clang llvm libbpf-dev make -y
```

Install bpftool
```sh
git clone --recurse-submodules https://github.com/libbpf/bpftool.git
```
Then
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
make install
```
<br/>
<br/>
If you try to run bpftool but it says there is no bpftool for version 6.14 then do the following steps, otherwise try to run bpftool first<br/>
Then move bpftool to a directory in your PATH:

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
Your network interface should be the second interface. The one that does not have `127.0.0.1` as its IP address.

To the run the program first run:
```sh
make build
```

then run:
```sh
make link
```
This links the XDP to the network interface.
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
