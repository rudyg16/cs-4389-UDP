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
