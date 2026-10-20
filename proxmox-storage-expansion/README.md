# Recover and Register Proxmox Storage Capacity

The hosts had usable storage that was not available for VM disks. This project registered the
unused thin pool and verified thin allocation after guest cleanup and TRIM.

## Result

| Storage | Node | Approximate capacity | Current use |
|---|---|---:|---:|
| `local-lvm` | `buzz` | 794 GiB | Empty |
| `local-lvm` | `hornetsnest` | 794 GiB | About 166 GiB |
| `local-lvm2` | `hornetsnest` | 920 GiB | Empty |

Total thin capacity is about 2.45 TiB, with about 2.29 TiB currently free.

## Completed work

- [x] Inventoried disks, volume groups, thin pools, and existing Proxmox storage definitions.
- [x] Registered the unused 920 GiB thin pool as `local-lvm2` without formatting it.
- [x] Enabled guest discard and SSD hints on the optimized VM disks.
- [x] Ran filesystem TRIM and confirmed lower thin-pool allocation from the Proxmox host.

## Notes

`local-lvm2` is local storage. It is additional capacity, not shared storage and not automatic
replication. A VM using it cannot live-migrate without moving its disk or adding replication.

## Validation

```bash
pvesm status
lvs -o lv_name,lv_size,data_percent,metadata_percent
```

Inside a Linux guest with discard enabled:

```bash
systemctl enable --now fstrim.timer
fstrim -av
```
