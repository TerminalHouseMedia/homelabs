# Migrate a Vendor-Specific AI VM to `ai01`

The management desktop started as a vendor-specific AI workstation. It was converted into a
general-purpose local AI operations VM while preserving every project, runbook, and access key.

## Completed work

- [x] Inventoried the desktop client, CLI, caches, configuration, and project data before removal.
- [x] Archived user configuration and session data in a dated, recoverable directory.
- [x] Removed the unused desktop client, CLI, autostart entry, cache, and browser integration.
- [x] Renamed the Linux hostname and Proxmox VM from the old vendor name to `ai01`.
- [x] Updated homelab reports and access documentation to use the new hostname.

## Result

Removing the unused client reduced active memory consumption by several GiB and recovered disk
space without deleting runbooks, keys, documents, or project files. The Linux username was left
unchanged to avoid breaking home-directory paths and permissions.

## Safe migration pattern

1. Inventory package and per-user data locations.
2. Archive irreplaceable configuration before uninstalling anything.
3. Remove applications and generated caches separately from user-created files.
4. Rename the OS and hypervisor object together.
5. Search documentation and automation for stale hostname references.
6. Reboot and verify SSH, DNS, monitoring, and application startup.
