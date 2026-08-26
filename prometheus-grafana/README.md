# Prometheus + Node Exporter + Grafana on a Homelab Cluster

Companion repo for the video: **[Monitor Your Proxmox Homelab with Prometheus + Grafana](https://www.youtube.com/watch?v=FK3gSoV4Ftg)**

Monitors six machines: one metrics server, a Warewulf head node, two RHEL servers, and two
stateless compute nodes.

## How it works

Prometheus pulls. Clients do not push. The server holds the whole target list.

```
workstation ──▶ :3000 Grafana        dashboards
                :9090 Prometheus     storage + query
                          │ scrapes every 15s
                          ▼
                    :9100 on every machine   node_exporter
```

## Tested on

- AlmaLinux 10.2 (metrics server), Rocky Linux 9.6 (clients)
- Prometheus 3.13.1, node_exporter 1.12.1, Grafana 10.2.6
- Warewulf 4.7.0 with a `rockylinux-9.6` image
- SELinux enforcing

## Files

- `install-node-exporter.sh` — installs node_exporter on a running machine, offline
- `install-node-exporter-image.sh` — same, for a Warewulf image chroot
- `nodes.json.example` — target list for `file_sd`

## Video chapters

```
0:00  Why monitor
0:53  Networking
4:39  Installing Prometheus
5:42  It failed. Reading the journal
6:36  Port conflict: moving Cockpit
8:28  Node exporter, offline install
10:03 Baking it into the Warewulf image
11:35 Installing Grafana
12:16 Importing dashboard 1860
13:49 SELinux blocking Grafana
15:11 Every machine reporting
15:37 What's next
```

---

## 1. Check port 9090 first

Cockpit usually already has it on RHEL-family systems.

```bash
ss -tlnp | grep :9090
```

If Cockpit answers, move it to 8090:

```bash
mkdir -p /etc/systemd/system/cockpit.socket.d
cat > /etc/systemd/system/cockpit.socket.d/listen.conf <<'EOF'
[Socket]
ListenStream=
ListenStream=8090
EOF

semanage port -a -t websm_port_t -p tcp 8090
firewall-cmd --add-port=8090/tcp
firewall-cmd --permanent --add-port=8090/tcp

systemctl daemon-reload
systemctl restart cockpit.socket
systemctl status cockpit.socket
```

`Listen:` should now read 8090.

The empty `ListenStream=` is required. It clears the inherited 9090. Without it Cockpit
listens on both.

Do not use 9091. Ports 9090-9999 are used by Prometheus exporters and 9091 is Pushgateway.

## 2. Note your IP addresses

```bash
ip -brief addr show
```

If the server has more than one NIC, you need the address that faces the nodes you will
scrape. Traffic to a `10.x` node leaves the `10.x` interface and arrives with that source
address. A client firewall rule naming the wrong address blocks every scrape and produces
no error.

## 3. Install Prometheus

```bash
dnf install -y epel-release
dnf install -y prometheus
systemctl enable --now prometheus

sleep 10
systemctl is-active prometheus
ss -tlnp | grep :9090
```

Wait the 10 seconds. A status check immediately after start will say `active` for a
service that dies at 116 ms.

Firewall. Prometheus has no authentication, so do not open it to everything.

```bash
firewall-cmd --permanent --remove-service=cockpit
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="9090" protocol="tcp" accept'
firewall-cmd --reload
```

Replace `192.168.1.0/24` with the subnet you browse from.

## 4. Install node_exporter

### Machines with repo access

```bash
dnf install -y node-exporter
systemctl enable --now prometheus-node-exporter
ss -tlnp | grep :9100
```

Package is `node-exporter`. Unit is `prometheus-node-exporter.service`. They do not match.

### Offline machines

Build the bundle on a machine with internet:

```bash
cd /root
VER=1.12.1
curl -LO https://github.com/prometheus/node_exporter/releases/download/v${VER}/node_exporter-${VER}.linux-amd64.tar.gz
curl -LO https://github.com/prometheus/node_exporter/releases/download/v${VER}/sha256sums.txt
sha256sum -c sha256sums.txt --ignore-missing

chmod +x install-node-exporter.sh
tar czf node-exporter-bundle.tar.gz node_exporter-${VER}.linux-amd64.tar.gz install-node-exporter.sh
```

`sha256sum -c` must print OK.

Push to each node:

```bash
PROM_IP=10.0.0.121

for n in 10.0.0.2 10.0.0.3; do
  echo "=== $n ==="
  scp -o StrictHostKeyChecking=accept-new node-exporter-bundle.tar.gz admin@$n:/tmp/ \
    && ssh -t admin@$n "cd /tmp && tar xzf node-exporter-bundle.tar.gz && sudo ./install-node-exporter.sh $PROM_IP" \
    || echo "!!! FAILED: $n"
done
```

`PROM_IP` is the server address on the network these nodes use. `ssh -t` is required or
sudo cannot prompt.

The script creates the service user, writes the unit, opens 9100 to `PROM_IP` only,
starts it, and exits non-zero if `/metrics` does not answer.

### Warewulf stateless nodes

Installs on a running stateless node are lost at the next boot. Put it in the image.

```bash
wwctl image list

IMG=rockylinux-9.6
ROOT=/var/lib/warewulf/chroots/$IMG/rootfs

sudo cp install-node-exporter-image.sh node_exporter-1.12.1.linux-amd64.tar.gz $ROOT/tmp/
sudo wwctl image exec $IMG -- /bin/bash /tmp/install-node-exporter-image.sh 10.0.0.121
sudo wwctl image build $IMG
```

`wwctl` needs root. Reboot a node, then check from the Prometheus server:

```bash
curl -sf -o /dev/null --max-time 5 http://10.0.0.10:9100/metrics && echo OK
```

Test from the Prometheus server, not the head node. The image firewall rule only allows
that one address.

## 5. Add targets with file_sd

Put the target list in a JSON file Prometheus watches. Adding a node is then one line with
no reload.

Replace the `node` job's `static_configs` in `/etc/prometheus/prometheus.yml`:

```yaml
  - job_name: node
    file_sd_configs:
      - files:
          - /etc/prometheus/targets/*.json
```

```bash
mkdir -p /etc/prometheus/targets
cat > /etc/prometheus/targets/nodes.json <<'EOF'
[
  {
    "targets": [
      "localhost:9100",
      "10.0.0.1:9100",
      "10.0.0.2:9100",
      "10.0.0.3:9100",
      "10.0.0.10:9100",
      "10.0.0.11:9100"
    ],
    "labels": {}
  }
]
EOF

promtool check config /etc/prometheus/prometheus.yml
systemctl reload prometheus
```

`promtool` must print SUCCESS before the reload.

Check:

```bash
promtool query instant http://localhost:9090 up
```

Every target should read `=> 1`.

`up` is generated by Prometheus, one per target. `1` means the last scrape succeeded. `0`
means the target is configured and was tried but did not answer. Removed targets stay in
query results for about 5 minutes, so wait before trusting the output after a change.

## 6. Install Grafana

```bash
ss -tlnp | grep :3000 || echo "3000 free"
dnf install -y grafana

mkdir -p /etc/grafana/provisioning/datasources
cat > /etc/grafana/provisioning/datasources/prometheus.yml <<'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
EOF

setsebool -P grafana_can_tcp_connect_prometheus_port on

systemctl enable --now grafana-server
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="3000" protocol="tcp" accept'
firewall-cmd --reload

systemctl is-active grafana-server
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/login
```

Expect `200`.

The `setsebool` line is required on SELinux enforcing systems. Without it Grafana starts
fine and every dashboard shows N/A.

Browse to `http://<server>:3000`. Log in with `admin` / `admin`. It forces a password
change. To reset later: `grafana-cli admin reset-admin-password <newpassword>`

## 7. Import a dashboard

Dashboards → New → Import → `1860` → Load → select Prometheus → Import.

[1860 Node Exporter Full](https://grafana.com/grafana/dashboards/1860-node-exporter-full/)
works on Grafana 10.x. The `instance` dropdown lists every node.

Others:

- [13702](https://grafana.com/grafana/dashboards/13702-node-exporter-resources-overview/) Resources Overview, lighter than 1860
- [11074](https://grafana.com/grafana/dashboards/11074-node-exporter-for-prometheus-dashboard-en-v20201010/) more gauges
- [18648](https://grafana.com/grafana/dashboards/18648-node-exporter/) minimal

Dashboards built for Grafana 11 or 12 may show blank panels on 10.x.

---

# Fixes

**Prometheus dies immediately.** `systemctl status` says it failed but not why. Read the
journal:

```bash
journalctl -u prometheus -n 30 --no-pager
```

`bind: address already in use` means something else has 9090. Find it with
`ss -tlnp | grep :9090`.

**Cockpit is on `[::]:9090` and Prometheus wants `0.0.0.0:9090`, and they still collide.**
`net.ipv6.bindv6only` is 0 by default on Linux, so an IPv6 wildcard socket also takes IPv4.
Check with `sysctl net.ipv6.bindv6only`.

**"Start request repeated too quickly."** systemd latched the unit failed after too many
restarts. Clear it:

```bash
systemctl reset-failed prometheus
systemctl start prometheus
```

**Grafana dashboards show N/A and the variable dropdowns are empty.** Check whether the
data exists:

```bash
promtool query instant http://localhost:9090 node_uname_info
```

If rows come back but Grafana is empty, Grafana cannot reach Prometheus. On SELinux:

```bash
ausearch -m avc -ts today | grep -i grafana | tail
```

Look for `denied { name_connect } dest=9090`. Fix:

```bash
setsebool -P grafana_can_tcp_connect_prometheus_port on
systemctl restart grafana-server
```

Do not relabel the port. 9090 is `websm_port_t` in RHEL policy and the boolean is named
for the use case, not the label. `prometheus_port_t` does not exist.

To see what a domain is allowed to connect to:

```bash
dnf install -y setools-console
sesearch -A -s grafana_t -c tcp_socket -p name_connect
```

---

# Next

- DHCP reservations so target IPs stop moving. Prometheus cannot target a MAC address, so
  pin MAC to IP at the DHCP server instead.
- Relabel `instance` to hostnames so dashboards do not key on IPs.
- Reverse proxy with auth in front of Prometheus and Grafana.
- More exporters: IPMI, smartctl, DCGM for NVIDIA GPUs.
