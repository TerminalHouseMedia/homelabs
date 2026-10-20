Failed to create stream fd: Operation not permitted
Failed to create stream fd: Operation not permitted
Failed to create stream fd: Operation not permitted
# Key-Based SSH Access Across a Segmented Homelab

The management workstation can administer approved systems with dedicated SSH keys. Separate
credentials are used for the Linux lab and Windows.

The public documentation intentionally omits real addresses, privileged usernames, host-key
fingerprints, and routing details. Private keys stay on their originating machine and are never
copied into documentation or chat.

## Completed work

- [x] Created a dedicated Ed25519 key for the Windows workstation without overwriting keys.
- [x] Installed the public key in Windows OpenSSH with administrator-authorized-key ACLs.
- [x] Verified Windows host fingerprints and passwordless login as the normal Windows user.
- [x] Verified key authentication through the authorized management path.
- [x] Documented the access chain, key roles, fingerprints workflow, and recovery boundaries.

## Example client configuration

Use placeholders in public configuration examples:

```sshconfig
Host lab-jump
    HostName 192.0.2.10
    User admin-user
    IdentityFile ~/.ssh/lab_ed25519
    IdentitiesOnly yes

Host private-lab-*
    ProxyJump lab-jump

Host gpu-workstation
    HostName 192.0.2.20
    User windows-user
    IdentityFile ~/.ssh/windows_ed25519
    IdentitiesOnly yes
```

Verify a host key out of band before accepting it. Never publish private keys, account tokens,
`known_hosts`, or a real `authorized_keys` file.
