NET_INTERFACE = ens33 # change Network interface to match VM

build:
	clang -O2 -g -target bpf -c xdp_packet_tracer.c -o xdp_packet_tracer.o

link:
	sudo ip link set dev $(NET_INTERFACE) xdp obj xdp_packet_tracer.o sec xdp

unlink:
	sudo ip link set dev $(NET_INTERFACE) xdp off

clean:
	rm -f test.o
