#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:?image required}"
VERSION="${2:-0.2.5-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate.img"
ROOT="/mnt/pu2pny-025"
PID=""
LOOP=""

cleanup(){
  set +e
  test -n "$PID" && sudo kill "$PID" 2>/dev/null || true
  sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true
  sudo rm -f "$RAW" /tmp/pu2pnyd-025.log
}
trap cleanup EXIT

echo '[1/15] Integrity and partitions'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"
ACTUAL="$(sha256sum "$IMAGE" | awk '{print $1}')"
test -n "$EXPECTED" && test "$EXPECTED" = "$ACTUAL"
sudo sh -c "xz -dc '$IMAGE' > '$RAW'"
LOOP="$(sudo losetup --find --partscan --show "$RAW")"
for _ in {1..30}; do test -b "${LOOP}p2" && break; sleep .25; done
test -b "${LOOP}p1" && test -b "${LOOP}p2"
sudo mkdir -p "$ROOT"
sudo mount "${LOOP}p2" "$ROOT"
sudo mkdir -p "$ROOT/boot/firmware"
sudo mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[2/15] OS identity'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"

echo '[3/15] Executables and syntax'
for x in \
  2pny-network-core 2pny-network-switch 2pny-hostfiles-update \
  2pny-protocol-network-apply 2pny-auto-maintenance; do
  test -x "$ROOT/usr/local/sbin/$x"
  bash -n "$ROOT/usr/local/sbin/$x"
done
for x in 2pny-server-catalog 2pny-live-status 2pny-hardware-probe 2pny-display-status; do
  test -x "$ROOT/usr/local/sbin/$x"
  python3 -m py_compile "$ROOT/usr/local/sbin/$x"
done
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"

echo '[4/15] Wi-Fi scan does not drop Ethernet core'
SW="$ROOT/usr/local/sbin/2pny-network-switch"
CORE="$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'SCAN_HOLD=' "$SW"
grep -Fq 'ap-scan-hold' "$CORE"
! grep -Fq 'systemctl stop 2pny-network-core.service' "$SW"
grep -Fq 'PU2PNY-WIFI-CANDIDATE' "$SW"
grep -Fq 'A configuração anterior foi preservada' "$SW"
grep -Fq 'scope global' "$SW"
OUT="$(sudo chroot "$ROOT" /usr/local/sbin/2pny-network-switch scan-json)"
test "$OUT" = '[]'

echo '[5/15] Public server catalog works offline'
CAT="$(sudo chroot "$ROOT" /usr/local/sbin/2pny-server-catalog DMR)"
echo "$CAT" | python3 -c 'import json,sys; d=json.load(sys.stdin); n={x["name"] for x in d["servers"]}; assert "XLX_026" in n; assert "BM_7242_Brazil" in n; assert "TGIF_Network" in n'
YSF="$(sudo chroot "$ROOT" /usr/local/sbin/2pny-server-catalog YSF)"
echo "$YSF" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert any(x.get("id")=="72426" for x in d["servers"])'
grep -Fq 'DMR_Hosts.txt' "$ROOT/usr/local/sbin/2pny-hostfiles-update"
grep -Fq 'YSFHosts.txt' "$ROOT/usr/local/sbin/2pny-hostfiles-update"

echo '[6/15] Real DMR master renderer/applier'
sudo mkdir -p "$ROOT/var/lib/2pny/mmdvm" "$ROOT/var/lib/2pny/backups/network-radio" "$ROOT/run/2pny" "$ROOT/tmp/testbin"
sudo tee "$ROOT/var/lib/2pny/mmdvm/MMDVM-Host.ini" >/dev/null <<'EOF'
[General]
Callsign=PU2PNY
Id=7241465
Duplex=0

[DMR]
Enable=1
ColorCode=1
DumpTAData=1

[DMR Network]
Enable=0

[D-Star Network]
Enable=0

[System Fusion Network]
Enable=0

[P25 Network]
Enable=0

[NXDN Network]
Enable=0
EOF
sudo tee "$ROOT/tmp/testbin/systemctl" >/dev/null <<'EOF'
#!/bin/sh
exit 0
EOF
sudo chmod 0755 "$ROOT/tmp/testbin/systemctl"
sudo chroot "$ROOT" /usr/bin/env PATH=/tmp/testbin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  /usr/local/sbin/2pny-protocol-network-apply DMR TEST_MASTER 192.0.2.10 62031 testpass hotspot 1 ''
CONF="$ROOT/var/lib/2pny/mmdvm/MMDVM-Host.ini"
grep -A12 '^\[DMR Network\]$' "$CONF" | grep -q '^Enable=1$'
grep -A12 '^\[DMR Network\]$' "$CONF" | grep -q '^Type=Direct$'
grep -A12 '^\[DMR Network\]$' "$CONF" | grep -q '^Address=192.0.2.10$'
grep -A12 '^\[DMR Network\]$' "$CONF" | grep -q '^Port=62031$'
grep -A12 '^\[DMR Network\]$' "$CONF" | grep -q '^Slot1=0$'
grep -A12 '^\[DMR Network\]$' "$CONF" | grep -q '^Slot2=1$'
test -s "$ROOT/var/lib/2pny/network-radio.json"
sudo rm -rf "$ROOT/tmp/testbin" "$ROOT/var/lib/2pny/mmdvm/MMDVM-Host.ini" "$ROOT/var/lib/2pny/network-radio.json" "$ROOT/var/lib/2pny/backups/network-radio"

echo '[7/15] Wizard includes mandatory server flow'
WIZ="$ROOT/usr/share/2pny/wizard.html"
grep -Fq '0.2.5-alpha' "$WIZ"
grep -Fq 'Servidor DMR' "$WIZ"
grep -Fq '/api/servers' "$WIZ"
grep -Fq 'server_password' "$WIZ"
grep -Fq 'Color Code' "$WIZ"
grep -Fq 'singleWifiNote' "$WIZ"
grep -Fq 'O cabo Ethernet permanece funcionando' "$WIZ"
grep -Fq 'RF, MMDVMHost e servidor DMR' "$WIZ"

echo '[8/15] Dashboard live view preserved and extended'
DASH="$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Painel principal' "$DASH"
grep -Fq 'Servidor digital' "$DASH"
grep -Fq 'Estado da rede digital' "$DASH"
grep -Fq 'Ao vivo' "$DASH"
grep -Fq '/api/live' "$DASH"
grep -Fq 'liveBer' "$DASH"
grep -Fq 'liveRssi' "$DASH"
grep -Fq 'Atividade recente' "$DASH"

echo '[9/15] Live parser returns valid light JSON'
LIVE="$(sudo chroot "$ROOT" /usr/local/sbin/2pny-live-status)"
echo "$LIVE" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert "network" in d and "events" in d and "live" in d'

echo '[10/15] Base RF safety preserved'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
grep -Fq 'CONFIG=/var/lib/2pny/mmdvm/MMDVM-Host.ini' "$RF"
grep -Fq 'ScreenLayout=2' "$RF"
grep -Fq 'DumpTAData=1' "$RF"
grep -Fq 'RXOffset=$RXOFF' "$RF"
grep -Fq 'TXOffset=$TXOFF' "$RF"

echo '[11/15] Clean first boot'
test ! -e "$ROOT/var/lib/2pny/provisioned"
test ! -e "$ROOT/var/lib/2pny/network-radio.json"
test ! -e "$ROOT/var/lib/2pny/network-connect.json"
test ! -e "$ROOT/var/lib/2pny/wifi-scan.json"
test -s "$ROOT/var/lib/2pny/hosts/DMR_Hosts.txt"

echo '[12/15] Run web panel inside final image'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-025.log 2>&1 & PID=$!
OK=0
for _ in {1..60}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-025.log; exit 1; }
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq '"version":"0.2.5-alpha"'
curl -fsS 'http://127.0.0.1/api/servers?protocol=DMR' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert any(x.get("name")=="BM_7242_Brazil" for x in d["servers"])'
curl -fsS 'http://127.0.0.1/api/live' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert "network" in d and "events" in d'

echo '[13/15] Routing before/after provisioning'
LOC="$(curl -sSI http://127.0.0.1/ | awk 'BEGIN{IGNORECASE=1}/^Location:/{gsub("\r","");print $2}')"
test "$LOC" = /wizard
sudo touch "$ROOT/var/lib/2pny/provisioned"
LOC="$(curl -sSI http://127.0.0.1/ | awk 'BEGIN{IGNORECASE=1}/^Location:/{gsub("\r","");print $2}')"
test "$LOC" = /dashboard
curl -fsS http://127.0.0.1/dashboard | grep -Fq 'Painel principal'
sudo rm -f "$ROOT/var/lib/2pny/provisioned"

echo '[14/15] No password is exposed in public config files'
! grep -Rqs 'testpass' "$ROOT/var/lib/2pny" || { echo 'test password leaked'; exit 1; }
! grep -Fq 'ServerPassword' "$ROOT/usr/share/2pny/dashboard.html"

echo '[15/15] Final result'
echo "PU2PNY $VERSION ARM64 image: OK"
