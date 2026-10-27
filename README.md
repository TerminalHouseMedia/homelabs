# homelabs

Build notes and scripts from my homelab. Each folder is a self-contained project. Some projects
also have a companion video.

| Project | What it covers | Video |
|---|---|---|
| [gods-eye-view](gods-eye-view/) | Source-linked global events, stream panel integration, and regression checks. | — |
| [gpu-worker-monitoring](gpu-worker-monitoring/) | Windows GPU metrics, collector freshness, and Prometheus scrape examples. | — |
| [prometheus-grafana](prometheus-grafana/) | Monitoring infrastructure and lab nodes with Prometheus, node_exporter, and Grafana. Includes stateless Warewulf compute nodes. | [Watch](https://www.youtube.com/watch?v=FK3gSoV4Ftg) |
| [tailscale-remote-access](tailscale-remote-access/) | Reaching both homelab networks remotely through an AlmaLinux subnet router. | [Watch](https://www.youtube.com/watch?v=VumPIXVq9lg) |
| [proxmox-cluster-expansion](proxmox-cluster-expansion/) | Two-node Proxmox expansion, historical validation, and quorum limitations. | — |
| [proxmox-storage-expansion](proxmox-storage-expansion/) | LVM-thin storage recovery, historical capacity evidence, and discard validation. | — |
| [homelab-ssh-access](homelab-ssh-access/) | A key-based access pattern for LAN, jump-host, private-lab, and Windows systems. | — |
| [windows-rtx4090-access](windows-rtx4090-access/) | Adding a Windows RTX 4090 workstation as reachable homelab compute. | — |
| [ai-management-vm-migration](ai-management-vm-migration/) | Removing a vendor-specific AI client while preserving data and renaming the management VM. | — |
| [ai01-performance-optimization](ai01-performance-optimization/) | Right-sizing the Ubuntu AI workstation and reclaiming RAM and thin storage. | — |
| [almabrain-optimization](almabrain-optimization/) | Right-sizing the jump host and monitoring server while preserving its GNOME desktop. | — |

Project READMEs distinguish historical deployment evidence, publication checks, and remaining
validation. Where something broke, the recovery is documented.

## Current lab capability

- Two-node Proxmox cluster: 40 CPU threads and about 121 GiB host RAM
- About 2.45 TiB of thin-provisioned VM storage, with roughly 2.29 TiB free after cleanup
- Isolated Warewulf and RHCSA lab behind a dual-homed jump host
- Prometheus and Grafana monitoring across infrastructure and lab nodes
- Remote access through Tailscale without exposing management ports to the internet
- Key-authenticated access to a Windows workstation with an RTX 4090 and 24 GB VRAM

The two-node cluster is quorate while both nodes are online. It is not full high availability:
a third vote, such as a lightweight QDevice, is still recommended before treating it as HA.

---

Terminal House Media
