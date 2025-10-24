# UDP Shield — Testbed & Emulation Tools

This repository contains safe, isolated testbed scripts for evaluating UDP Shield prototypes.

What it does:
- Creates an attacker → victim → reflector topology using Linux network namespaces.
- Runs a local UDP reflector (safe, rate-limited).
- Generates controlled client traffic from attacker namespace.
- Captures and analyzes victim-side traffic (pcap + simple metrics).

Quick start:
See `docs/quick_start.md` for step-by-step setup and experiment recipes.

License:
This repository includes an MIT license by default. Change as appropriate for your project.
