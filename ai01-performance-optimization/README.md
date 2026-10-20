# Optimize an Ubuntu Desktop VM for Local AI Administration

`ai01` runs the local AI desktop and administers the homelab. The goal was to return resources
to Proxmox without making the interactive desktop feel constrained.

## Before and after

| Metric | Before | After |
|---|---:|---:|
| Assigned RAM | 16 GiB | 10 GiB |
| Guest disk use | About 84% | About 58% |
| Proxmox thin allocation | 95.9% | 54.9% |
| Boot time | — | About 6 seconds |

Normal post-cleanup use leaves roughly 5-6 GiB available and swap unused.

## Completed work

- [x] Reduced RAM from 16 GiB to 10 GiB after measuring the real desktop workload.
- [x] Installed and enabled `qemu-guest-agent` for shutdown, address, and backup integration.
- [x] Detached the installer ISO and disabled the irrelevant failed OpenIPMI service.
- [x] Enabled SSD discard, scheduled TRIM, and reclaimed thin-pool blocks.
- [x] Capped journals, removed obsolete Snap revisions and unused local virtualization packages, cleared disposable caches, and installed updates.

## Why not reduce it to 8 GiB?

Chromium and the AI desktop can consume several GiB together. Ten GiB retains enough headroom for
interactive work while returning 6 GiB to the hypervisor.

## Validation

```bash
free -h
systemctl --failed
systemctl is-active qemu-guest-agent fstrim.timer
systemd-analyze
```

On Proxmox:

```bash
qm config <vmid>
qm status <vmid> --verbose
lvs -o lv_name,lv_size,data_percent
```
