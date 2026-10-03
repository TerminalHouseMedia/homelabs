# Remote Lab Access with Tailscale

Companion repo for the video: [Turn Your Home Lab Into a Secure Remote Network with Tailscale](https://www.youtube.com/watch?v=VumPIXVq9lg)

Reach the Proxmox web UI and SSH into every lab VM from anywhere — a coffee shop, a phone on cellular — with no port forwarding and no static IP.

## How it works

Tailscale runs on one Linux host that already sits on the network and advertises its subnets into your tailnet. That host is a **subnet router**. Every other device you add to the tailnet reaches the lab through it.

```
laptop (anywhere) ──tailnet (WireGuard)──▶ almabrain  ──▶ 192.168.1.0/24  Proxmox UI, servers
                                            (subnet       └▶ 10.0.0.0/24     private lab VMs
                                             router)
```

Nothing is exposed to the internet. The only reachable thing from outside is the encrypted tunnel; `:8006` and `:22` stay private.

A dual-homed router host is the trick. `almabrain` sits on both `192.168.1.0/24` (where Proxmox lives) and `10.0.0.0/24` (the private VMs), so one install advertises both networks. Replace these two subnets with yours.

Tailscale SNATs subnet-routed traffic by default, so the Proxmox host and the `10.0.0.x` VMs see connections coming *from* the router and reply normally. You do not add return routes on every machine.

## Tested on

- Router host: AlmaLinux 10, Tailscale 1.102.4
- Client: macOS, Tailscale 1.102.4
- Free Tailscale plan, one user

## 1. Install Tailscale on the router host

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

The script detects the distro and adds the right repo. On AlmaLinux it's the dnf repo, not apt.

## 2. Enable IP forwarding

A subnet router forwards packets, which the kernel blocks by default.

```bash
echo 'net.ipv4.ip_forward = 1'          | tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | tee -a /etc/sysctl.d/99-tailscale.conf
sysctl -p /etc/sysctl.d/99-tailscale.conf
```

Give `sysctl -p` the full file path. A bare `sysctl -p` reads `/etc/sysctl.conf`, not the file you just wrote, and prints nothing — which looks like success and is not. With the path it echoes both lines back with `= 1`.

Confirm the live value:

```bash
sysctl net.ipv4.ip_forward
```

Must read `net.ipv4.ip_forward = 1`.

## 3. Bring it up and advertise the subnets

```bash
tailscale up --advertise-routes=192.168.1.0/24,10.0.0.0/24
```

Replace the two subnets with yours. One subnet? List one. This prints a login URL and pauses — open it, authenticate, and the host joins. The command returns once you've logged in.

## 4. Approve the routes in the admin console

Advertised routes do nothing until approved.

Admin console → Machines → the router host → Edit route settings → check each subnet → Save. Same menu → Disable key expiry, so an always-on router does not drop off the tailnet in 90 days.

A route checked here but not advertised in step 3, or advertised but not checked here, both fail silently. Both sides must agree.

## 5. Connect a client

```bash
tailscale up --accept-routes
```

On the macOS/Windows/mobile app this is a toggle: "Use Tailscale subnet routes." It is separate from the OS network-extension permission the app asks for on install — granting that permission does not accept routes.

From anywhere, use the same addresses you use at home:

```
https://192.168.1.42:8006      # Proxmox UI
ssh admin@10.0.0.3             # a lab VM
```

## Verify

```bash
tailscale status
```

Shows the router online, and the admin console shows the subnets as Approved.

Then test from a phone on cellular, not home Wi-Fi. On-LAN everything works whether or not the tunnel does; cellular is what proves remote access.

## Fixes

`sysctl -p` printed nothing. You ran it without the file path. Re-run with the full path (step 2).

Client is on the tailnet but the Proxmox UI will not load. Routes not approved, or the client is not accepting routes. Approve in the admin console (step 4) and `tailscale up --accept-routes` on the client (step 5). Both are required.

`tailscale up` warned about IP forwarding. Step 2 was skipped or did not take. Enable forwarding, then re-run.

Works at home, not on cellular. You are testing on-LAN. The tunnel is not in the path until you leave your own network.

## Rollback

```bash
tailscale down            # stop advertising
tailscale logout          # leave the tailnet
dnf remove tailscale      # AlmaLinux / Rocky / Fedora  (apt remove on Debian / Ubuntu)
```

If the router host is a VM, a pre-change snapshot is the fastest reset.

## Next

- Tailscale ACLs to limit which devices can reach the lab.
- Tailscale SSH for key-free, audited SSH.
- A real HTTPS cert for the Proxmox node over the tailnet (`tailscale cert` + `pvenode cert set`) to kill the browser warning.
