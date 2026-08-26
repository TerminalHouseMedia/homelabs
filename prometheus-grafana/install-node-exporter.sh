#!/usr/bin/env bash
#
# install-node-exporter.sh — offline installer for Prometheus node_exporter
#
# Usage:  ./install-node-exporter.sh [PROMETHEUS_SERVER_IP]
#         Default server IP is 192.168.1.21 (almabrain)
#
# Expects node_exporter-*.linux-*.tar.gz in the SAME DIRECTORY as this script.
# No internet required. Run as root.
#
set -euo pipefail

PROM_SERVER="${1:-192.168.1.21}"
PORT=9100
BIN_DEST=/usr/local/bin/node_exporter
SVC_USER=node_exporter
UNIT=/etc/systemd/system/node_exporter.service

# --- sanity checks -----------------------------------------------------------
[[ $EUID -eq 0 ]] || { echo "ERROR: run as root." >&2; exit 1; }

cd "$(dirname "$(readlink -f "$0")")"

TARBALL=$(ls node_exporter-*.linux-*.tar.gz 2>/dev/null | head -1) || true
[[ -n "${TARBALL:-}" ]] || { echo "ERROR: no node_exporter-*.linux-*.tar.gz found here." >&2; exit 1; }
echo "==> Using tarball: $TARBALL"

# --- extract and place the binary --------------------------------------------
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
tar xzf "$TARBALL" -C "$TMP"
SRC=$(find "$TMP" -type f -name node_exporter | head -1)
[[ -n "$SRC" ]] || { echo "ERROR: node_exporter binary not found inside tarball." >&2; exit 1; }

install -o root -g root -m 0755 "$SRC" "$BIN_DEST"
echo "==> Installed $("$BIN_DEST" --version 2>&1 | head -1)"

# SELinux: give the binary a sane executable context if the system enforces it.
if command -v restorecon >/dev/null 2>&1; then
    restorecon -v "$BIN_DEST" || true
fi

# --- service account (no login, no home) -------------------------------------
if ! id -u "$SVC_USER" >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$SVC_USER" 2>/dev/null \
        || useradd --system --no-create-home --shell /sbin/nologin "$SVC_USER"
    echo "==> Created system user: $SVC_USER"
else
    echo "==> System user $SVC_USER already exists"
fi

# --- systemd unit -------------------------------------------------------------
cat > "$UNIT" <<EOF
[Unit]
Description=Prometheus Node Exporter
Documentation=https://github.com/prometheus/node_exporter
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SVC_USER
Group=$SVC_USER
ExecStart=$BIN_DEST --web.listen-address=:$PORT
Restart=on-failure
RestartSec=5s

# Modest hardening. node_exporter only needs to read /proc and /sys,
# neither of which these settings block.
NoNewPrivileges=true
ProtectHome=true
ProtectSystem=strict
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
echo "==> Wrote $UNIT"

# --- firewall: allow ONLY the Prometheus server to reach 9100 -----------------
if command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state >/dev/null 2>&1; then
    RULE="rule family=\"ipv4\" source address=\"$PROM_SERVER/32\" port port=\"$PORT\" protocol=\"tcp\" accept"
    firewall-cmd --permanent --add-rich-rule="$RULE" >/dev/null
    firewall-cmd --reload >/dev/null
    echo "==> firewalld: $PORT/tcp opened to $PROM_SERVER only"
elif command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "^Status: active"; then
    ufw allow from "$PROM_SERVER" to any port "$PORT" proto tcp >/dev/null
    echo "==> ufw: $PORT/tcp opened to $PROM_SERVER only"
else
    echo "==> WARNING: no active firewalld or ufw detected."
    echo "    Port $PORT is NOT firewall-restricted on this host. Verify manually."
fi

# --- start it -----------------------------------------------------------------
systemctl daemon-reload
systemctl enable --now node_exporter

# --- verify (this is the part that actually proves anything) ------------------
sleep 3
echo
echo "==> Verification"
systemctl is-active node_exporter
ss -tlnp 2>/dev/null | grep ":$PORT " || echo "WARNING: nothing listening on $PORT"
echo -n "==> /metrics responds: "
if curl -sf "http://localhost:$PORT/metrics" | head -1 >/dev/null; then
    echo "yes"
else
    echo "NO — check: journalctl -u node_exporter -n 30 --no-pager"
    exit 1
fi

echo
echo "Done. Add this host to Prometheus on $PROM_SERVER as: $(hostname -f 2>/dev/null || hostname):$PORT"
