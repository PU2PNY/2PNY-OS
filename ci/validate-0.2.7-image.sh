#!/usr/bin/env bash
set -euo pipefail
# Image tests read root:mmdvm 0640 files; keep production permissions intact.
if (( EUID != 0 )); then exec sudo bash "$0" "$@"; fi

IMAGE="${1:?image required}"
VERSION="${2:-0.2.7-alpha}"
RAW="/tmp/PU2PNY-OS-${VERSION}-validate.img"
ROOT="/mnt/pu2pny-os-026"
PID=""
LOOP=""
DG_COMMIT="2a3306de313cf4c094c2031c9ced5a6858bbbfcc"
DISP_COMMIT="96a0705d818c4234960a61dd2837e32f9450f811"

cleanup(){
  set +e
  test -n "$PID" && sudo kill "$PID" 2>/dev/null || true
  sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true
  sudo rm -f "$RAW" /tmp/pu2pnyd-026.log
}
trap cleanup EXIT
trap 'echo "Validation failed at line $LINENO: $BASH_COMMAND" >&2' ERR

echo '[1/20] Validator syntax'
bash -n "$0"

echo '[2/20] Integrity and partitions'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"
ACTUAL="$(sha256sum "$IMAGE" | awk '{print $1}')"
test -n "$EXPECTED" && test "$EXPECTED" = "$ACTUAL"
sudo sh -c "xz -dc '$IMAGE' > '$RAW'"
LOOP="$(sudo losetup --find --partscan --show "$RAW")"
for _ in {1..40}; do test -b "${LOOP}p2" && break; sleep .25; done
test -b "${LOOP}p1" && test -b "${LOOP}p2"
sudo mkdir -p "$ROOT"
sudo mount "${LOOP}p2" "$ROOT"
sudo mkdir -p "$ROOT/boot/firmware"
sudo mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[3/20] OS identity and public naming'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
grep -Fq 'PU2PNY-OS' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'PU2PNY-OS' "$ROOT/usr/share/2pny/dashboard.html"

echo '[4/20] Runtime script syntax'
for x in 2pny-network-core 2pny-network-switch 2pny-hostfiles-update 2pny-auto-maintenance 2pny-rf-apply 2pny-mode-apply; do
  test -x "$ROOT/usr/local/sbin/$x"
  bash -n "$ROOT/usr/local/sbin/$x"
done
for x in 2pny-protocol-network-apply 2pny-server-catalog 2pny-live-status 2pny-display-apply 2pny-display-status 2pny-hardware-probe; do
  test -x "$ROOT/usr/local/sbin/$x"
  python3 -m py_compile "$ROOT/usr/local/sbin/$x"
done
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"

echo '[5/20] Pinned radio binaries'
for x in MMDVM-Host DMRGateway MMDVM-Display NextionUpdater; do test -x "$ROOT/usr/local/bin/$x"; done
grep -Fxq "$DG_COMMIT" "$ROOT/usr/share/2pny/upstream/DMRGateway.commit"
grep -Fxq "$DISP_COMMIT" "$ROOT/usr/share/2pny/upstream/MMDVMDisplay.commit"
test -s "$ROOT/usr/share/2pny/upstream/MMDVMHost.commit"

echo '[6/20] Wi-Fi recovery contract'
SW="$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'BSSID,SIGNAL,FREQ,SECURITY' "$SW"
grep -Fq 'for attempt in 1 2' "$SW"
grep -Fq 'restore_on_error' "$SW"
grep -Fq 'AP pu2pny foi restaurado' "$SW"
grep -Fq 'scope global' "$SW"
! grep -Fq 'systemctl stop 2pny-network-core.service' "$SW"

echo '[7/20] Local MQTT is loopback-only'
MOSQ="$ROOT/etc/mosquitto/conf.d/pu2pny-local.conf"
grep -Fxq 'listener 1883 127.0.0.1' "$MOSQ"
! grep -Eq 'listener[[:space:]]+1883[[:space:]]+(0\.0\.0\.0|::)' "$MOSQ"
grep -Fxq 'persistence false' "$MOSQ"

echo '[8/20] Service contracts'
for s in 2pny-mmdvmhost.service 2pny-dmrgateway.service 2pny-display.service; do test -s "$ROOT/etc/systemd/system/$s"; done
grep -Fq '/usr/local/bin/DMRGateway /var/lib/2pny/dmr/DMRGateway.ini' "$ROOT/etc/systemd/system/2pny-dmrgateway.service"
grep -Fq '/usr/local/bin/MMDVM-Display /var/lib/2pny/display/MMDVM-Display.ini' "$ROOT/etc/systemd/system/2pny-display.service"
grep -Fq 'After=systemd-udev-settle.service mosquitto.service' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"

echo '[9/20] RF uses detected modem baud and local gateway'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
grep -Fq 'MODEM_BAUD=' "$RF"
grep -Fq 'UARTSpeed=$MODEM_BAUD' "$RF"
grep -Fq 'GatewayAddress=127.0.0.1' "$RF"
grep -Fq 'GatewayPort=62031' "$RF"
grep -Fq 'LocalPort=62032' "$RF"
grep -Fq 'Name=host' "$RF"
! grep -Fq 'UARTSpeed=115200' "$RF"

echo '[10/20] DMR network applier routes through DMRGateway'
NET="$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'DMRGateway.ini' "$NET"
grep -Fq '[XLX Network]' "$NET"
grep -Fq '"GatewayAddress":"127.0.0.1"' "$NET"
grep -Fq '"GatewayPort":"62031"' "$NET"
grep -Fq 'BrandMeister requires the Hotspot Security password' "$NET"
grep -Fq '"state":"configured"' "$NET"

echo '[11/20] Clean first boot before synthetic tests'
for p in   "$ROOT/var/lib/2pny/provisioned"   "$ROOT/var/lib/2pny/rf-configured"   "$ROOT/var/lib/2pny/network-radio.json"   "$ROOT/var/lib/2pny/display-runtime.json"   "$ROOT/var/lib/2pny/display-override.json"   "$ROOT/var/lib/2pny/dmr/DMRGateway.ini"   "$ROOT/var/lib/2pny/display/MMDVM-Display.ini"   "$ROOT/var/lib/2pny/secrets/brandmeister-api.key"; do
  test ! -e "$p"
done

echo '[12/20] Synthetic XLX and BrandMeister rendering'
sudo mkdir -p "$ROOT/var/lib/2pny/mmdvm" "$ROOT/var/lib/2pny/backups/network-radio" "$ROOT/var/lib/2pny/dmr" "$ROOT/run/2pny" "$ROOT/tmp/testbin"
write_base_ini(){
sudo tee "$ROOT/var/lib/2pny/mmdvm/MMDVM-Host.ini" >/dev/null <<'EOF'
[General]
Callsign=PU2PNY
Id=7241465
Duplex=0

[Modem]
RXFrequency=439125000
TXFrequency=439125000

[DMR]
Enable=1
ColorCode=1
DumpTAData=1

[DMR Network]
Enable=0
GatewayAddress=127.0.0.1
GatewayPort=62031
LocalAddress=127.0.0.1
LocalPort=62032
EOF
}
sudo tee "$ROOT/tmp/testbin/systemctl" >/dev/null <<'EOF'
#!/bin/sh
exit 0
EOF
sudo chmod 0755 "$ROOT/tmp/testbin/systemctl"
write_base_ini
sudo chroot "$ROOT" /usr/bin/env PATH=/tmp/testbin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin   /usr/local/sbin/2pny-protocol-network-apply DMR XLX_026 82.152.175.30 62030 passw0rd hotspot 1 2 C '' XLX ''
HOST="$ROOT/var/lib/2pny/mmdvm/MMDVM-Host.ini"
DG="$ROOT/var/lib/2pny/dmr/DMRGateway.ini"
sudo chroot "$ROOT" runuser -u mmdvm -- test -r /var/lib/2pny/mmdvm/MMDVM-Host.ini
sudo chroot "$ROOT" runuser -u mmdvm -- test -r /var/lib/2pny/dmr/DMRGateway.ini
grep -A15 '^\[DMR Network\]$' "$HOST" | grep -Fxq 'GatewayAddress=127.0.0.1'
! grep -A15 '^\[DMR Network\]$' "$HOST" | grep -Fq '82.152.175.30'
grep -A20 '^\[XLX Network\]$' "$DG" | grep -Fxq 'Enabled=1'
grep -A20 '^\[XLX Network\]$' "$DG" | grep -Fxq 'Startup=026'
grep -A20 '^\[XLX Network\]$' "$DG" | grep -Fxq 'Module=C'
grep -A20 '^\[XLX Network\]$' "$DG" | grep -Fxq 'TG=6'
grep -A20 '^\[XLX Network\]$' "$DG" | grep -Fxq 'Slot=2'
write_base_ini
sudo rm -f "$ROOT/var/lib/2pny/network-radio.json"
sudo chroot "$ROOT" /usr/bin/env PATH=/tmp/testbin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin   /usr/local/sbin/2pny-protocol-network-apply DMR BM_7242_Brazil 7242.master.brandmeister.network 62031 bmsecret hotspot 1 2 '' 01 BrandMeister ''
grep -A24 '^\[DMR Network 1\]$' "$DG" | grep -Fxq 'Name=BM'
grep -A24 '^\[DMR Network 1\]$' "$DG" | grep -Fxq 'Id=724146501'
grep -A24 '^\[DMR Network 1\]$' "$DG" | grep -Fxq 'Address=7242.master.brandmeister.network'
grep -A24 '^\[DMR Network 1\]$' "$DG" | grep -Fxq 'Password=bmsecret'
grep -A24 '^\[DMR Network 1\]$' "$DG" | grep -Fxq 'PassAllTG=2'
grep -A24 '^\[DMR Network 1\]$' "$DG" | grep -Fxq 'PassAllPC=2'
! grep -Fq 'bmsecret' "$ROOT/var/lib/2pny/network-radio.json"

echo '[13/20] Display renderer uses MMDVM-Display without HMI flashing'
sudo tee "$ROOT/var/lib/2pny/hardware-probe.json" >/dev/null <<'EOF'
{"state":"complete","mmdvm":{"detected":true,"port":"/dev/ttyACM0","baud":460800},"display":{"detected":false,"state":"mmdvm_display_candidate"}}
EOF
sudo tee "$ROOT/var/lib/2pny/display-override.json" >/dev/null <<'EOF'
{"enabled":true,"type":"nextion_mmdvm","layout":2}
EOF
sudo chroot "$ROOT" /usr/local/sbin/2pny-display-apply
DISPCONF="$ROOT/var/lib/2pny/display/MMDVM-Display.ini"
sudo chroot "$ROOT" runuser -u mmdvm -- test -r /var/lib/2pny/display/MMDVM-Display.ini
grep -Fxq 'Display=Nextion' "$DISPCONF"
grep -Fxq 'Port=modem' "$DISPCONF"
grep -Fxq 'ScreenLayout=2' "$DISPCONF"
! grep -Fq 'NextionUpdater' "$ROOT/usr/local/sbin/2pny-display-apply"

echo '[14/20] Wizard exposes network-specific DMR controls'
WIZ="$ROOT/usr/share/2pny/wizard.html"
for needle in '0.2.7-alpha' 'Time Slot' 'Hotspot Security' 'BrandMeister API Key' 'Módulo XLX' 'ON7LDS / Pi-Star' 'dataset.bssid'; do grep -Fq "$needle" "$WIZ"; done

echo '[15/20] Responsive live dashboard exposes RX TX and quality'
DASH="$ROOT/usr/share/2pny/dashboard.html"
for needle in 'TX · Seu rádio → Internet' 'RX · Internet → seu rádio' 'MTR / qualidade' 'Internet e rede local' 'DMRGateway' 'MMDVM-Display' '@media(max-width:760px)'; do grep -Fq "$needle" "$DASH"; done

echo '[16/20] Live parser returns split RX TX state'
LIVE="$(sudo chroot "$ROOT" /usr/local/sbin/2pny-live-status)"
echo "$LIVE" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert all(k in d for k in ("network","rx","tx","events"))'

echo '[17/20] Cleanup synthetic state and verify no static secret exposure'
sudo rm -rf "$ROOT/tmp/testbin" "$ROOT/var/lib/2pny/mmdvm/MMDVM-Host.ini"   "$ROOT/var/lib/2pny/network-radio.json" "$ROOT/var/lib/2pny/dmr/DMRGateway.ini"   "$ROOT/var/lib/2pny/dmr/XLXHosts.txt" "$ROOT/var/lib/2pny/display/MMDVM-Display.ini"   "$ROOT/var/lib/2pny/display-runtime.json" "$ROOT/var/lib/2pny/display-override.json"   "$ROOT/var/lib/2pny/hardware-probe.json" "$ROOT/var/lib/2pny/backups/network-radio"
! grep -Fq 'bmsecret' "$ROOT/usr/share/2pny/dashboard.html"
! grep -Fq 'bmsecret' "$ROOT/usr/share/2pny/wizard.html"
! grep -Fq 'BMAPIKey' "$ROOT/usr/share/2pny/dashboard.html"

echo '[18/20] Run web panel inside final image'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-026.log 2>&1 & PID=$!
OK=0
for _ in {1..70}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-026.log; exit 1; }
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq '"version":"0.2.7-alpha"'
curl -fsS 'http://127.0.0.1/api/servers?protocol=DMR' | python3 -c 'import json,sys; d=json.load(sys.stdin); bm=next(x for x in d["servers"] if x.get("kind")=="BrandMeister"); assert bm.get("password_required") is True and bm.get("api_supported") is True'
curl -fsS 'http://127.0.0.1/api/live' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert "rx" in d and "tx" in d'

echo '[19/20] Routing before and after provisioning'
LOC="$(curl -sSI http://127.0.0.1/ | awk 'BEGIN{IGNORECASE=1}/^Location:/{gsub("\r","");print $2}')"
test "$LOC" = /wizard
sudo touch "$ROOT/var/lib/2pny/provisioned"
LOC="$(curl -sSI http://127.0.0.1/ | awk 'BEGIN{IGNORECASE=1}/^Location:/{gsub("\r","");print $2}')"
test "$LOC" = /dashboard
DASH_HTML="$(curl -fsS http://127.0.0.1/dashboard)"
grep -Fq 'TX · Seu rádio → Internet' <<<"$DASH_HTML"
sudo rm -f "$ROOT/var/lib/2pny/provisioned"

# New services and optional expert integrations must be present in the final image.
test -x "$ROOT/usr/local/sbin/2pny-station-worker"
test -x "$ROOT/usr/bin/mosquitto_pub"
test -x "$ROOT/usr/sbin/sshd"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'host-name=pu2pny' "$ROOT/etc/avahi/avahi-daemon.conf"
grep -Fq 'wifi-operation.lock' "$ROOT/usr/local/sbin/2pny-network-core"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-station.service"
curl -fsS http://127.0.0.1/api/contacts | python3 -c 'import json,sys; assert isinstance(json.load(sys.stdin),dict)'
curl -fsS http://127.0.0.1/api/station/settings | python3 -c 'import json,sys; assert json.load(sys.stdin)["qrz_configured"] is False'

echo '[20/20] Final result' 
echo "PU2PNY-OS $VERSION ARM64 image: OK"

