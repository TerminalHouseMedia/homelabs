Failed to create stream fd: Operation not permitted
Failed to create stream fd: Operation not permitted
Failed to create stream fd: Operation not permitted
# Optimize an AlmaLinux Infrastructure VM

This project right-sized a multi-purpose AlmaLinux infrastructure VM while retaining its desktop
environment and required lab services. The public version intentionally omits access paths,
interface assignments, and internal addresses.

## Before and after

| Setting | Before | After |
|---|---:|---:|
| Assigned RAM | 16 GiB | 8 GiB |
| CPU topology | 2 sockets × 2 cores | 1 socket × 4 cores |
| Idle memory used | About 1.2 GiB | About 1.2 GiB |
| Thin-disk allocation | 22.1% | 19.2% |

GNOME remains installed, enabled, and active. The attached AlmaLinux DVD ISO also remains mounted
because it supplies the offline BaseOS and AppStream repository to private lab machines.

## Completed work

- [x] Backed up Proxmox and guest configuration before making changes.
- [x] Reduced RAM to 8 GiB and corrected the virtual CPU topology without reducing total cores.
- [x] Enabled the guest agent, SSD discard, scheduled TRIM, and a disk-first boot order.
- [x] Preserved GNOME while disabling irrelevant virtual hardware services and masking unsupported `mcelog`.
- [x] Updated 332 non-kernel packages, preserved the intentional kernel pin, and validated every infrastructure service after reboot.

## Validation scope

- Core networking and host firewall
- Local package repository availability
- Monitoring and management services
- Required interfaces and routes
- GNOME Display Manager and graphical boot target

## Kernel pin lesson

The original DNF exclusion named individual kernel packages but omitted
`kernel-modules-extra`. That produced an unsatisfiable mixed-version update. The rule was changed
to `excludepkgs=kernel*`, preserving the pin consistently while allowing userspace updates.

## Validation

```bash
free -h
lscpu | grep -E 'CPU\(s\)|Socket|Core'
systemctl --failed
systemctl is-active gdm sshd firewalld tailscaled httpd prometheus grafana-server
curl -fsS http://localhost:9090/-/healthy
curl -fsS http://localhost:3000/api/health
```
