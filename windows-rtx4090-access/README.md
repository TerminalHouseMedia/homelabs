# Add a Windows RTX 4090 Workstation to the Homelab

This project made a Windows gaming and music workstation available as optional GPU compute
without turning it into an always-on server.

## Hardware verified

- Windows workstation reachable over the home LAN
- NVIDIA GeForce RTX 4090
- 24,564 MiB reported VRAM
- OpenSSH Server on TCP 22
- Key authentication using a dedicated Ed25519 key

## Completed work

- [x] Verified the Windows hostname, LAN address, OpenSSH service, and firewall path.
- [x] Created and installed a dedicated public key using Windows administrator ACLs.
- [x] Confirmed passwordless SSH and command execution from the Linux management VM.
- [x] Queried `nvidia-smi` remotely and confirmed the RTX 4090 is available.

## What this enables

The working SSH path is the foundation for remote Ollama, llama.cpp, ComfyUI, CUDA jobs, or a
small queued worker. Those runtimes are not deployed by this project; the GPU remains available
for gaming and music whenever the workstation is in use locally.

## Validation

```bash
ssh gpu-workstation hostname
ssh gpu-workstation 'nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv'
```

Windows OpenSSH may lag Linux OpenSSH in key-exchange features. Keep Windows updated and restrict
the firewall rule to trusted LAN or VPN source ranges.
