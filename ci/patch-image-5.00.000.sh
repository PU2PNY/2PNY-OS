#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-}"
[[ -n "$ROOT" && "$ROOT" == /* && -d "$ROOT" ]] || { echo "usage: $0 <mounted-root>" >&2; exit 2; }
[[ -f "$ROOT/etc/2pny/version" ]] || { echo "PU2PNY root marker missing" >&2; exit 2; }
[[ "$(cat "$ROOT/etc/2pny/version")" == "4.00.001" ]] || { echo "expected immutable 4.00.001 base" >&2; exit 2; }
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO/runtime/5x"
for f in 2pny-eventd.py 2pny-hardware-manager.py 2pny-network-manager.py 2pny-wifi-apply.py 2pny-protocol-manager.py; do
  [[ -s "$SRC/$f" ]] || { echo "missing $SRC/$f" >&2; exit 2; }
done
python3 -m py_compile "$SRC"/*.py
install -d -m 0755 "$ROOT/usr/local/libexec/pu2pny" "$ROOT/usr/local/sbin" "$ROOT/etc/systemd/system" "$ROOT/var/lib/2pny/protocol"
install -m 0755 "$SRC/2pny-eventd.py" "$ROOT/usr/local/libexec/pu2pny/2pny-eventd"
install -m 0755 "$SRC/2pny-hardware-manager.py" "$ROOT/usr/local/libexec/pu2pny/2pny-hardware-manager"
install -m 0755 "$SRC/2pny-network-manager.py" "$ROOT/usr/local/libexec/pu2pny/2pny-network-manager"
install -m 0755 "$SRC/2pny-wifi-apply.py" "$ROOT/usr/local/sbin/2pny-wifi-apply"
install -m 0755 "$SRC/2pny-protocol-manager.py" "$ROOT/usr/local/sbin/2pny-protocol-manager"

cat >"$ROOT/etc/systemd/system/2pny-eventd.service" <<'EOF'
[Unit]
Description=PU2PNY-OS 5.x local event bus
After=local-fs.target
Before=2pny-network-manager.service

[Service]
Type=simple
ExecStart=/usr/local/libexec/pu2pny/2pny-eventd
Restart=on-failure
RestartSec=2
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictAddressFamilies=AF_UNIX
ReadWritePaths=/run/pu2pny
RuntimeDirectory=pu2pny
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF
cat >"$ROOT/etc/systemd/system/2pny-hardware-manager.service" <<'EOF'
[Unit]
Description=PU2PNY-OS 5.x conservative hardware inventory
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/local/libexec/pu2pny/2pny-hardware-manager
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictAddressFamilies=AF_UNIX
ReadOnlyPaths=/proc /sys /dev /var/lib/2pny
ReadWritePaths=/run/pu2pny
RuntimeDirectory=pu2pny

[Install]
WantedBy=multi-user.target
EOF
cat >"$ROOT/etc/systemd/system/2pny-network-manager.service" <<'EOF'
[Unit]
Description=PU2PNY-OS 5.x event-driven network state
After=NetworkManager.service 2pny-eventd.service
Wants=NetworkManager.service 2pny-eventd.service

[Service]
Type=simple
ExecStart=/usr/local/libexec/pu2pny/2pny-network-manager
Restart=on-failure
RestartSec=3
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictAddressFamilies=AF_UNIX AF_NETLINK
ReadOnlyPaths=/proc /sys /dev
ReadWritePaths=/run/pu2pny
RuntimeDirectory=pu2pny

[Install]
WantedBy=multi-user.target
EOF

# mDNS contract: pu2pny.local on every interface Avahi can publish.
if [[ -f "$ROOT/etc/avahi/avahi-daemon.conf" ]]; then
  python3 - "$ROOT/etc/avahi/avahi-daemon.conf" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); text=p.read_text()
lines=text.splitlines(); out=[]; in_server=False; done=False
for line in lines:
    stripped=line.strip()
    if stripped.startswith('['): in_server=(stripped=='[server]')
    if in_server and (stripped.startswith('host-name=') or stripped.startswith('#host-name=')) and not done:
        out.append('host-name=pu2pny'); done=True
    else: out.append(line)
if not done:
    try: i=out.index('[server]')+1; out.insert(i,'host-name=pu2pny')
    except ValueError: out=['[server]','host-name=pu2pny','']+out
p.write_text('\n'.join(out)+'\n')
PY
fi

# Compatibility name is an alias only; never create a second MMDVM engine.
if [[ -f "$ROOT/etc/systemd/system/2pny-mmdvmhost.service" && ! -e "$ROOT/etc/systemd/system/mmdvmhost.service" ]]; then
  ln -s 2pny-mmdvmhost.service "$ROOT/etc/systemd/system/mmdvmhost.service"
fi

systemctl --root="$ROOT" enable 2pny-eventd.service 2pny-hardware-manager.service 2pny-network-manager.service >/dev/null
if [[ -f "$ROOT/etc/systemd/system/2pny-mmdvmhost.service" ]]; then systemctl --root="$ROOT" enable 2pny-mmdvmhost.service >/dev/null; fi
if [[ -f "$ROOT/lib/systemd/system/avahi-daemon.service" || -f "$ROOT/usr/lib/systemd/system/avahi-daemon.service" ]]; then systemctl --root="$ROOT" enable avahi-daemon.service >/dev/null || true; fi
printf '5.00.000\n' >"$ROOT/etc/2pny/version"

# Offline gates. No RF/display operation is performed here.
[[ "$(cat "$ROOT/etc/2pny/version")" == '5.00.000' ]]
test -x "$ROOT/usr/local/sbin/2pny-wifi-apply"
test -x "$ROOT/usr/local/sbin/2pny-protocol-manager"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-eventd.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-network-manager.service"
grep -Fq 'host-name=pu2pny' "$ROOT/etc/avahi/avahi-daemon.conf"
grep -Fq 'RestrictAddressFamilies=AF_UNIX AF_NETLINK' "$ROOT/etc/systemd/system/2pny-network-manager.service"
if [[ -L "$ROOT/etc/systemd/system/mmdvmhost.service" ]]; then [[ "$(readlink "$ROOT/etc/systemd/system/mmdvmhost.service")" == '2pny-mmdvmhost.service' ]]; fi

echo PATCH_IMAGE_500000_OK
