#!/usr/bin/env bash
#
# install-node-exporter-image.sh
#
# Installs node_exporter INSIDE a Warewulf node image (a chroot).
# Differs from the running-node installer in three ways:
#   - no `systemctl` (no PID 1 / D-Bus inside a chroot)
#   - enables the service by creating the wants symlink by hand
#   - firewall handled with firewall-offline-cmd, since firewalld isn't running
#
# Run this from INSIDE the image, e.g.:
#   wwctl image exec rockylinux-9.6 -- /bin/bash /tmp/install-node-exporter-image.sh 10.0.0.121
#
set -euo pipefail

PROM_SERVER="${1:-10.0.0.121}"
PORT=9100
BIN_DEST=/usr/local/bin/node_exporter
SVC_USER=node_exporter
UNIT=/etc/systemd/system/node_exporter.service
WANTS=/etc/systemd/system/multi-user.target.wants

[[ $EUID -eq 0 ]] || { echo "ERROR: run as root (inside the image)." >&2; exit 1; }

cd /tmp
TARBALL=$(ls node_exporter-*.linux-*.tar.gz 2>/dev/null | head -1) || true
[[ -n "${TARBALL:-}" ]] || { echo "ERROR: no node_exporter tarball in /tmp inside the image." >&2; exit 1; }
echo "==> Using tarball: $TARBALL"

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
tar xzf "$TARBALL" -C "$TMP"
SRC=$(find "$TMP" -type f -name node_exporter | head -1)
[[ -n "$SRC" ]] || { echo "ERROR: binary not found inside tarball." >&2; exit 1; }

install -o root -g root -m 0755 "$SRC" "$BIN_DEST"
echo "==> Installed binary: $BIN_DEST"

# --- service account ----------------------------------------------------------
if ! id -u "$SVC_USER" >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /sbin/nologin "$SVC_USER"
    echo "==> Created system user: $SVC_USER"
else
    echo "==> System user $SVC_USER already present"
fi

# --- unit file ----------------------------------------------------------------
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
NoNewPrivileges=true
ProtectHome=true
ProtectSystem=strict
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
echo "==> Wrote $UNIT"

# --- enable by hand -----------------------------------------------------------
# `systemctl enable` needs a live systemd. Inside a chroot it fails or no-ops.
# The symlink below is precisely what `enable` would have created.
mkdir -p "$WANTS"
ln -sf "$UNIT" "$WANTS/node_exporter.service"
echo "==> Enabled via symlink: $WANTS/node_exporter.service"

# --- firewall (offline) --------------------------------------------------------
if command -v firewall-offline-cmd >/dev/null 2>&1; then
    firewall-offline-cmd \
        --add-rich-rule="rule family=\"ipv4\" source address=\"$PROM_SERVER/32\" port port=\"$PORT\" protocol=\"tcp\" accept" \
        >/dev/null 2>&1 && echo "==> firewalld (offline): $PORT/tcp allowed from $PROM_SERVER" \
        || echo "==> NOTE: firewall-offline-cmd present but rule not added; check manually."
else
    echo "==> No firewalld in this image — nothing to open. Port $PORT will be reachable."
fi

# --- verification (static only — nothing runs inside a chroot) -----------------
echo
echo "==> Verification (static)"
[[ -x "$BIN_DEST" ]]            && echo "  binary present and executable: OK"
[[ -f "$UNIT" ]]                && echo "  unit file written:            OK"
[[ -L "$WANTS/node_exporter.service" ]] && echo "  enabled for multi-user:       OK"
id "$SVC_USER" >/dev/null       && echo "  service user exists:          OK"
echo
echo "Image side done. Rebuild the image, then reboot a node."
echo "Real verification happens after boot: up{instance=\"<node-ip>:9100\"} == 1"
