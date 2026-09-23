#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then exec sudo bash "$0" "$@"; fi
IMAGE="${1:?image required}"
VERSION="${2:-0.3.23-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate-0321.img"
ROOT="/mnt/pu2pny-os-0321"
LOOP=""; PID=""
cleanup(){
  set +e
  test -n "$PID" && kill "$PID" 2>/dev/null || true
  umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$RAW" /tmp/pu2pnyd-0321.log
}
trap cleanup EXIT
trap 'echo "Validation failed at line $LINENO: $BASH_COMMAND" >&2' ERR

echo '[1/10] integrity'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"; ACTUAL="$(sha256sum "$IMAGE"|awk '{print $1}')"
test "$EXPECTED" = "$ACTUAL"
xz -dc "$IMAGE" >"$RAW"
LOOP="$(losetup --find --partscan --show "$RAW")"
for _ in {1..60}; do test -b "${LOOP}p2" && break; sleep .25; done
mkdir -p "$ROOT"; mount "${LOOP}p2" "$ROOT"; mkdir -p "$ROOT/boot/firmware"; mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[2/10] identity and protected baseline'
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
test -x "$ROOT/usr/local/bin/MMDVM-Host"
test -x "$ROOT/usr/local/bin/DMRGateway"
test -x "$ROOT/usr/local/bin/dstargateway"
test -x "$ROOT/usr/local/bin/YSFGateway"
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, system voice priority'
test -s "$ROOT/usr/local/share/dstargateway.d/en_GB.ambe"
test -s "$ROOT/usr/local/share/dstargateway.d/en_GB.indx"

echo '[3/10] runtime syntax'
for x in 2pny-network-core 2pny-network-switch 2pny-wifi-profiles 2pny-auto-maintenance 2pny-hostfiles-update 2pny-rf-apply 2pny-mode-apply 2pny-display-online-detect; do
  test -x "$ROOT/usr/local/sbin/$x"; bash -n "$ROOT/usr/local/sbin/$x"
done
bash -n "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice"
for x in 2pny-station-worker 2pny-hardware-probe 2pny-display-core 2pny-display-status 2pny-display-apply 2pny-display-detector 2pny-server-catalog 2pny-protocol-network-apply 2pny-protocol-profiles 2pny-update-manager 2pny-mqtt-preflight 2pny-aprs 2pny-netdiag 2pny-timezone-apply 2pny-dmr-duplex-diagnostics 2pny-rxoffset-apply; do
  test -x "$ROOT/usr/local/sbin/$x"; python3 -m py_compile "$ROOT/usr/local/sbin/$x"
done
python3 -m py_compile "$ROOT/usr/local/lib/2pny-live-core.py" "$ROOT/usr/local/libexec/2pny-dmr-apply"
rm -rf "$ROOT/usr/local/sbin/__pycache__" "$ROOT/usr/local/lib/__pycache__" "$ROOT/usr/local/libexec/__pycache__"

echo '[4/10] DMR simplex protection and duplex contract'
DMR="$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'PROTO-036' "$DMR"
grep -Fq 'local_transport":"gateway-explicit" if duplex else "simplex-protected"' "$DMR"
grep -Fq 'duplex=1 if usemode=="repeater" else 0' "$DMR"
grep -Fq 'slot1=True if duplex' "$DMR"; grep -Fq 'slot2=True if duplex' "$DMR"
grep -Fq 'route_slots=(1,2) if duplex' "$DMR"
! grep -Fq 'DMRDelay=' "$DMR"
python3 "$ROOT/usr/local/sbin/2pny-dmr-duplex-diagnostics" --selftest | grep -Fq DMR_DUPLEX_DIAGNOSTICS_OK

echo '[5/10] DMR TG and protocol UI truth'
DASH="$ROOT/usr/share/2pny/dashboard.html"; HOT="$ROOT/usr/share/2pny/hotspot.html"; ST="$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'connected_tg' "$ST"; grep -Fq 'requested_tg' "$ST"
grep -Fq 'id="rxFrequencyMetric"' "$DASH"; grep -Fq 'id="txFrequencyMetric"' "$DASH"
grep -Fq 'Módulo / TG' "$DASH"; grep -Fq "TG '+dmrTG" "$DASH"
grep -Fq 'TG conectado' "$HOT"; grep -Fq 'TG4099' "$HOT"
grep -Fq 'Aguardando confirmação real do gateway/rede' "$HOT"

echo '[6/10] network, wizard, language and time'
INT="$ROOT/usr/share/2pny/internet.html"; WIZ="$ROOT/usr/share/2pny/wizard.html"; SYS="$ROOT/usr/share/2pny/system.html"
grep -Fq 'r.pending' "$INT"; grep -Fq 'Salvar rede de backup' "$INT"
grep -Fq 'auto-select' "$INT"; grep -Fq '12-point hysteresis' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq '/api/language' "$WIZ"; grep -Fq 'lastConnectivity&&lastConnectivity.internet' "$WIZ"
grep -Fq '<title>PU2PNY-OS</title>' "$WIZ"
grep -Fq 'Horário de verão manual' "$SYS"; grep -Fq 'UTC, logs e protocolos' "$SYS"
test -s "$ROOT/etc/systemd/journald.conf.d/20-pu2pny.conf"
grep -Fq 'SystemMaxUse=64M' "$ROOT/etc/systemd/journald.conf.d/20-pu2pny.conf"
grep -Fq 'MaxRetentionSec=7day' "$ROOT/etc/systemd/journald.conf.d/20-pu2pny.conf"

echo '[7/10] Nextion and BER'
DAP="$ROOT/usr/local/sbin/2pny-display-apply"; DCORE="$ROOT/usr/local/sbin/2pny-display-core"; DISP="$ROOT/usr/share/2pny/display.html"
grep -Eq 'tx_only_unconfirmed|candidate_native_fallback' "$DAP"
grep -Fq '"physical_confirmed":bool(d.get("physical_confirmed"))' "$DAP"
! grep -Fq '"physical_confirmed":True' "$DAP"
grep -Fq 'Saída ativa · retorno COMOK ainda não confirmado' "$DISP"
grep -Fq 'display_hm' "$DCORE"
test -x "$ROOT/usr/local/sbin/2pny-rxoffset-apply"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-rxoffset-apply.path"
grep -Fq '/api/rf/ber-calibration' "$ROOT/usr/share/2pny/hotspot.html" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/rf/ber-calibration'
grep -Fq 'Salvar melhor ajuste' "$HOT"

echo '[8/10] APRS ACK and Direct-only'
APRS="$ROOT/usr/local/sbin/2pny-aprs"; APRSUI="$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'ACKDIAG' "$APRS"; grep -Fq 'item.get("station")==source' "$APRS"
grep -Fq 'M-SMS' "$APRSUI"; grep -Fq 'H-SMS' "$APRSUI"; grep -Fq 'latitude' "$APRSUI"
test -x "$ROOT/usr/local/bin/2pny-direct-core"
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK
strings "$ROOT/usr/local/bin/2pny-direct-core" | grep -Fq 'relay desativado'
grep -Fq 'CGNAT/NAT restritivo' "$ROOT/usr/share/2pny/direct.html"
grep -Fq 'Bloqueado' "$ROOT/usr/share/2pny/direct.html"
grep -Fq 'ID digital' "$ROOT/usr/share/2pny/direct.html"
! grep -Fq 'Direct/Relay' "$ROOT/usr/share/2pny/direct.html"

echo '[9/10] backend boot/API'
mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
mount -t proc proc "$ROOT/proc"; mount --bind /dev "$ROOT/dev"; mount --bind /sys "$ROOT/sys"
chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-0321.log 2>&1 & PID=$!
OK=0
for _ in {1..100}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-0321.log; exit 1; }
curl -fsS http://127.0.0.1/api/status | grep -Fq "\"version\":\"$VERSION\""
curl -fsS http://127.0.0.1/api/language | grep -Fq '"selected":false'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.23-alpha'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/rf/ber-calibration'
kill "$PID"; wait "$PID" 2>/dev/null || true; PID=""

echo '[10/10] no leaked runtime state'
for p in "$ROOT/var/lib/2pny/provisioned" "$ROOT/var/lib/2pny/rf-configured" "$ROOT/var/lib/2pny/network-radio.json" "$ROOT/var/lib/2pny/wifi-country"; do test ! -e "$p"; done
echo "PU2PNY-OS $VERSION ARM64 image: SW/structural gates PASS; reported RF/Nextion/Direct corrections remain HW PENDING"
