#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?mounted image root required}"
[[ "$ROOT" == /* && -d "$ROOT" && "$(cat "$ROOT/etc/2pny/version")" == '5.00.001' ]] || exit 2
REPO="$(cd "$(dirname "$0")/.." && pwd)"
for p in usr/local/bin/MMDVM-Display usr/local/bin/NextionDriver-pu2pny usr/local/sbin/2pny-display-apply; do
  test -s "$ROOT/$p"
done
install -d -m 0755 "$ROOT/usr/local/libexec/pu2pny/display"
install -m 0644 "$REPO/runtime/display/mqtt_link.py" "$ROOT/usr/local/libexec/pu2pny/display/mqtt_link.py"
install -m 0755 "$REPO/runtime/display/adapter.py" "$ROOT/usr/local/libexec/pu2pny/display/adapter.py"
cp -a "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/usr/local/sbin/2pny-display-apply.pre-5.00.002"
install -m 0755 "$REPO/runtime/display/apply.py" "$ROOT/usr/local/sbin/2pny-display-apply"
cat >"$ROOT/etc/systemd/system/2pny-display-adapter.service" <<'EOF'
[Unit]
Description=PU2PNY official display metadata and ON7LDS MQTT transport
After=mosquitto.service
Requires=mosquitto.service
ConditionPathExists=/var/lib/2pny/display-settings.json
[Service]
Type=simple
User=mmdvm
Group=mmdvm
ExecStart=/usr/bin/python3 /usr/local/libexec/pu2pny/display/adapter.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
IPAddressDeny=any
IPAddressAllow=localhost
[Install]
WantedBy=multi-user.target
EOF
# Display depends on the adapter, never the reverse dependency from the RF host.
install -d -m 0755 "$ROOT/etc/systemd/system/2pny-display.service.d"
cat >"$ROOT/etc/systemd/system/2pny-display.service.d/official-renderer.conf" <<'EOF'
[Unit]
After=2pny-display-adapter.service 2pny-nextiondriver.service
Wants=2pny-display-adapter.service
EOF
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'etc/systemd/system/2pny-nextiondriver.service'
s=p.read_text()
assert s.count('Before=2pny-mmdvmhost.service')==1
s=s.replace('Before=2pny-mmdvmhost.service','Before=2pny-display.service')
s=s.replace('-c /var/lib/2pny/mmdvm/MMDVM-Host.ini','-c /var/lib/2pny/display/NextionDriver.ini')
s=s.replace('RequiredBy=2pny-mmdvmhost.service','WantedBy=multi-user.target')
p.write_text(s)
# Remove only the legacy display->RF requirement, not any RF unit or config.
p=root/'etc/systemd/system/2pny-mmdvmhost.service.requires/2pny-nextiondriver.service'
p.unlink(missing_ok=True)
p=root/'usr/share/2pny/display.html'
s=p.read_text()
s=s.replace('Ativando renderer nativo do MMDVMHost com writer exclusivo…','Ativando MMDVM-Display oficial com writer exclusivo…')
s=s.replace('Ativando Nextion ON7LDS por Transparent Data com writer exclusivo…','Ativando MMDVM-Display oficial + NextionDriver ON7LDS…')
s=s.replace('a UART física continua sob controle do MMDVMHost.', 'a UART física continua sob controle do MMDVMHost. O MMDVM-Display oficial recebe os eventos MQTT e desenha a tela.')
s=s.replace('G4KLX/L2 usam o renderer nativo;', 'G4KLX/L2 usam MMDVM-Display;')
s=s.replace('L3/L3 HS usam o NextionDriver endurecido pela rota Transparent Data.', 'L3/L3 HS usam MMDVM-Display + NextionDriver pela bridge MQTT de display.')
p.write_text(s)
# Same-size version identity update; no executable instructions or backend logic change.
p=root/'usr/local/bin/2pnyd'
s=p.read_bytes()
assert b'5.00.001' in s
p.write_bytes(s.replace(b'5.00.001',b'5.00.002'))
(root/'etc/2pny/version').write_text('5.00.002\n')
PY
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/usr/local/libexec/pu2pny/display/adapter.py" "$ROOT/usr/local/libexec/pu2pny/display/mqtt_link.py"
echo DISPLAY_500002_OVERLAY_OK
