#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

test -d "$ROOT/etc"
test "$(cat "$ROOT/etc/2pny/version")" = '4.00.000'
test -f "$REPO/runtime/pu2pny-capability-scan.py"

install -D -m 0755 "$REPO/runtime/pu2pny-capability-scan.py" "$ROOT/usr/local/sbin/pu2pny-capability-scan"

cat >"$ROOT/etc/systemd/system/pu2pny-capabilities.service" <<'EOF'
[Unit]
Description=PU2PNY-OS capability inventory
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/pu2pny-capability-scan
User=root
Group=root
UMask=0022
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX
ReadWritePaths=/run/2pny

[Install]
WantedBy=multi-user.target
EOF

cat >"$ROOT/etc/systemd/system/pu2pny-capabilities.path" <<'EOF'
[Unit]
Description=Refresh PU2PNY-OS capabilities after local hardware/config changes

[Path]
PathChanged=/var/lib/2pny/hardware.json
PathChanged=/var/lib/2pny/display-detection.json
PathChanged=/var/lib/2pny/config.json
Unit=pu2pny-capabilities.service

[Install]
WantedBy=multi-user.target
EOF

cat >"$ROOT/etc/systemd/system/pu2pny-capabilities.timer" <<'EOF'
[Unit]
Description=Low-frequency PU2PNY-OS capability refresh

[Timer]
OnBootSec=20s
OnUnitInactiveSec=15min
AccuracySec=1min
Unit=pu2pny-capabilities.service

[Install]
WantedBy=timers.target
EOF

mkdir -p "$ROOT/etc/systemd/system/multi-user.target.wants" "$ROOT/etc/systemd/system/timers.target.wants"
ln -sfn ../pu2pny-capabilities.path "$ROOT/etc/systemd/system/multi-user.target.wants/pu2pny-capabilities.path"
ln -sfn ../pu2pny-capabilities.timer "$ROOT/etc/systemd/system/timers.target.wants/pu2pny-capabilities.timer"

python3 -m py_compile "$REPO/runtime/pu2pny-capability-scan.py"
grep -Fq 'NoNewPrivileges=true' "$ROOT/etc/systemd/system/pu2pny-capabilities.service"
grep -Fq 'RestrictAddressFamilies=AF_UNIX' "$ROOT/etc/systemd/system/pu2pny-capabilities.service"
grep -Fq 'OnUnitInactiveSec=15min' "$ROOT/etc/systemd/system/pu2pny-capabilities.timer"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/pu2pny-capabilities.path"
test -L "$ROOT/etc/systemd/system/timers.target.wants/pu2pny-capabilities.timer"
test -x "$ROOT/usr/local/sbin/pu2pny-capability-scan"
echo PATCH_IMAGE_400000_CAPABILITIES_OK
