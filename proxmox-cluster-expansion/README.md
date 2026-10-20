# Expand a Proxmox Homelab to Two Nodes

This project added a second Proxmox host, `buzz`, to the existing `hornetsnest` environment
and formed the cluster `the-hive`.

## Result

| Node | CPU threads | RAM | Role |
|---|---:|---:|---|
| `hornetsnest` | 24 | 58.5 GiB | Existing labs and shared infrastructure |
| `buzz` | 16 | 62.4 GiB | New capacity for Cisco CML and future workloads |

The cluster now has 40 CPU threads and about 121 GiB RAM. Both nodes are online and the
cluster reports quorate.

## Completed work

- [x] Installed Proxmox on the new mini PC and removed the previous Windows installation.
- [x] Assigned a stable hostname and LAN address to the new host.
- [x] Matched Proxmox versions before joining the nodes.
- [x] Joined `buzz` to `hornetsnest` as cluster `the-hive`.
- [x] Verified membership, secure Corosync transport, storage visibility, and quorum.

## Important two-node limitation

A two-node cluster needs both votes for quorum. Losing either node can block cluster-wide
configuration changes. Add a small third vote with `corosync-qdevice` before calling this a
high-availability design. Do not use a production VM inside the same two-node cluster as the
only QDevice.

## Validation

```bash
pvecm status
pvesh get /cluster/resources --type node
pvesh get /cluster/resources --type storage
```

## Rollback

Removing a node is a deliberate cluster operation, not a normal uninstall. Back up all VMs
and `/etc/pve` before changing membership. Follow the Proxmox node-removal procedure from a
remaining quorate node.
