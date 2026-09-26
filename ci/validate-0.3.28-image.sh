#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then exec sudo bash "$0" "$@"; fi
IMAGE="${1:?image required}"
VERSION="${2:-0.3.28-alpha}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
RAW="/tmp/PU2PNY-${VERSION}-validate-0328.img"
ROOT="/mnt/pu2pny-os-0328"
LOOP=""; PID=""
cleanup(){
  set +e
  test -n "$PID" && kill "$PID" 2>/dev/null || true
  umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$RAW" /tmp/pu2pnyd-0328.log
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
cmp -s "$ROOT/usr/local/sbin/2pny-protocol-network-apply" "$REPO/src/2pny-protocol-network-apply-all-0.3.20.py"
cmp -s "$ROOT/usr/local/libexec/2pny-dmr-apply" "$REPO/src/2pny-protocol-network-apply-0.3.21.py"

echo '[3/10] runtime syntax'
for x in 2pny-network-core 2pny-network-switch 2pny-wifi-profiles 2pny-auto-maintenance 2pny-hostfiles-update 2pny-rf-apply 2pny-mode-apply 2pny-display-online-detect 2pny-mdns-guard; do
  test -x "$ROOT/usr/local/sbin/$x"; bash -n "$ROOT/usr/local/sbin/$x"
done
bash -n "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice"
for x in 2pny-station-worker 2pny-hardware-probe 2pny-display-core 2pny-display-status 2pny-display-apply 2pny-display-detector 2pny-server-catalog 2pny-protocol-network-apply 2pny-protocol-profiles 2pny-update-manager 2pny-mqtt-preflight 2pny-aprs 2pny-netdiag 2pny-timezone-apply 2pny-dmr-duplex-diagnostics 2pny-rxoffset-apply; do
  test -x "$ROOT/usr/local/sbin/$x"; python3 -m py_compile "$ROOT/usr/local/sbin/$x"
done
python3 -m py_compile "$ROOT/usr/local/lib/2pny-live-core.py" "$ROOT/usr/local/libexec/2pny-dmr-apply"
rm -rf "$ROOT/usr/local/sbin/__pycache__" "$ROOT/usr/local/lib/__pycache__" "$ROOT/usr/local/libexec/__pycache__"

echo '[3b/10] MMDVM discovery coverage'
PROBE="$ROOT/usr/local/sbin/2pny-hardware-probe"
for token in '/dev/serial/by-id/*' '/dev/serial/by-path/*' '/dev/ttyAMA*' '/dev/ttyS*' '/dev/ttyACM*' '/dev/ttyUSB*' '/dev/ttyXRUSB*' '/dev/ttyGS*'; do grep -Fq "$token" "$PROBE"; done
for baud in 1200 2400 4800 9600 19200 38400 57600 115200 230400 460800 500000; do grep -Fq "B$baud" "$PROBE"; done
grep -Fq 'bytes((0xE0, 0x03, 0x00))' "$PROBE"
grep -Fq 'usb_reset_prone' "$PROBE"
grep -Fq 'radio_service_active()' "$PROBE"

echo '[4/10] DMR simplex protection and duplex contract'
DMR="$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'PROTO-036' "$DMR"
grep -Fq 'local_transport":"gateway-explicit" if duplex else "simplex-protected"' "$DMR"
grep -Fq 'duplex=1 if usemode=="repeater" else 0' "$DMR"
grep -Fq 'slot1=True if duplex' "$DMR"; grep -Fq 'slot2=True if duplex' "$DMR"
grep -Fq 'route_slots=(1,2) if duplex' "$DMR"
! grep -Fq 'DMRDelay=' "$DMR"
python3 "$ROOT/usr/local/sbin/2pny-dmr-duplex-diagnostics" --selftest | grep -Fq DMR_DUPLEX_DIAGNOSTICS_OK

echo '[4b/10] YSF/Wires-X and D-Star protected gateway contracts'
PROTO="$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'WiresXCommandPassthrough=0' "$PROTO"
grep -Fq 'RptPort=3200' "$PROTO"; grep -Fq 'LocalPort=4200' "$PROTO"
grep -Fq 'Reconnect=0' "$PROTO"; grep -Fq 'Revert=0' "$PROTO"
grep -Fq 'Startup={startup}' "$PROTO"
grep -Fq 'LocalPort":"3200","GatewayAddress":"127.0.0.1","GatewayPort":"4200' "$PROTO"
grep -Fq 'HBPort=20010' "$PROTO"; grep -Fq 'Port=20011' "$PROTO"
grep -Fq 'ReflectorAtStartup=1' "$PROTO"; grep -Fq 'ReflectorReconnect=Never' "$PROTO"
grep -Fq '[D-Plus]' "$PROTO"; grep -Fq '[Dextra]' "$PROTO"; grep -Fq '[DCS]' "$PROTO"; grep -Fq '[XLX]' "$PROTO"

echo '[5/10] DMR TG and protocol UI truth'
DASH="$ROOT/usr/share/2pny/dashboard.html"; HOT="$ROOT/usr/share/2pny/hotspot.html"; ST="$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'connected_tg' "$ST"; grep -Fq 'requested_tg' "$ST"
grep -Fq 'id="rxFrequencyMetric"' "$DASH"; grep -Fq 'id="txFrequencyMetric"' "$DASH"
grep -Fq 'Módulo / TG' "$DASH"; grep -Fq "TG '+dmrTG" "$DASH"
grep -Fq 'TG conectado' "$HOT"; grep -Fq 'TG4099' "$HOT"
grep -Fq 'Aguardando confirmação real do gateway/rede' "$HOT"
grep -Fq 'id="bmSecurityPassword"' "$HOT"
grep -Fq 'BrandMeister Hotspot Security Password' "$HOT"
grep -Fq 'type="password"' "$HOT"
grep -Fq 'Hotspot Security configurada' "$HOT"

echo '[6/10] network, wizard, language and time'
INT="$ROOT/usr/share/2pny/internet.html"; WIZ="$ROOT/usr/share/2pny/wizard.html"; SYS="$ROOT/usr/share/2pny/system.html"
grep -Fq 'r.pending' "$INT"; grep -Fq 'Salvar rede de backup' "$INT"
grep -Fq 'auto-select' "$INT"; grep -Fq '12-point hysteresis' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq '/api/language' "$WIZ"; grep -Fq 'lastConnectivity&&lastConnectivity.internet' "$WIZ"
grep -Fq 'ethernetAutoAdvanced' "$WIZ"
grep -Fq 'c.internet&&c.ethernet' "$WIZ"
grep -Fq "get('step')!=='1'" "$WIZ"
grep -Fq 'nmcli --wait 45 connection up PU2PNY-WIFI-CANDIDATE' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'ipv4.dhcp-timeout 30' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'test "${count:-0}" -lt 2' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq '12-point hysteresis' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'connection.autoconnect-priority 200' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'connection.autoconnect-priority 150' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'nm --wait 18 connection up "$chosen"' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'sleep 0.15' "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice"
grep -Fq 'id="wifiSearchSecond"' "$INT"
grep -Fq "PNY.q('wifiSearchSecond').onclick=wifiScan" "$INT"
test -x "$ROOT/usr/local/sbin/2pny-mdns-guard"
grep -Fq 'host-name","pu2pny' "$ROOT/usr/local/sbin/2pny-mdns-guard"
grep -Fq 'domain-name","local' "$ROOT/usr/local/sbin/2pny-mdns-guard"
grep -Fq '5353' "$ROOT/usr/local/sbin/2pny-mdns-guard"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-mdns-guard.service"
grep -Fq 'network-online.target' "$ROOT/etc/systemd/system/2pny-mdns-guard.service"
test -x "$ROOT/usr/sbin/avahi-daemon"
test -s "$ROOT/lib/systemd/system/avahi-daemon.service"
grep -Fq 'Aplicar fuso manual' "$SYS"
grep -Fq 'Aplicar data/hora manual' "$SYS"
grep -Fq 'timezone_source' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'STRICT_I18N_FALLBACK' "$ROOT/usr/share/2pny/ui-language.js"
grep -Fq 'PNYSetLanguage' "$ROOT/usr/share/2pny/ui-language.js"
grep -Fq '<title>PU2PNY-OS</title>' "$WIZ"
grep -Fq 'Horário de verão manual' "$SYS"; grep -Fq 'UTC, logs e protocolos' "$SYS"
grep -Fq "PNY.operation(rt,rt" "$SYS"
grep -Fq 'requestAnimationFrame(function(){requestAnimationFrame(r)})' "$SYS"
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

echo '[8/10] APRS ACK, Direct/Relay and radio acceptance'
APRS="$ROOT/usr/local/sbin/2pny-aprs"; APRSUI="$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'ACKDIAG' "$APRS"; grep -Fq 'item.get("station")==source' "$APRS"
grep -Fq 'def msg_packet' "$APRS"; grep -Fq 'retry_unacked' "$APRS"; grep -Fq 'consume_outbox' "$APRS"
! grep -Fq 'cfg.get("latitude")' "$APRS"
! grep -Fq 'cfg.get("longitude")' "$APRS"
! grep -Fq 'beacon(cfg' "$APRS"
grep -Fq 'Modo mensagens' "$APRSUI"
grep -Fq 'Enviar mensagem' "$APRSUI"
! grep -Fqi 'id="lat"' "$APRSUI"; ! grep -Fqi 'id="lon"' "$APRSUI"
! grep -Fqi 'useLocation' "$APRSUI"; ! grep -Fqi 'aprs.fi' "$APRSUI"
! grep -Fqi 'mapstub' "$APRSUI"; ! grep -Fqi 'radarcore' "$APRSUI"
test -x "$ROOT/usr/local/bin/2pny-direct-core"
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK
strings "$ROOT/usr/local/bin/2pny-direct-core" | grep -Fq 'Encrypted relay fallback'
strings "$ROOT/usr/local/bin/2pny-direct-core" | grep -Fq 'accepted-by-radio'
grep -Fq 'Direct primeiro · Relay automático' "$ROOT/usr/share/2pny/direct.html"
grep -Fq 'fallback criptografado' "$ROOT/usr/share/2pny/direct.html"
grep -Fq 'aceitar uma chamada pendente' "$ROOT/usr/share/2pny/direct.html"
grep -Fq 'ID digital' "$ROOT/usr/share/2pny/direct.html"

echo '[9/10] backend boot/API'
mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
mount -t proc proc "$ROOT/proc"; mount --bind /dev "$ROOT/dev"; mount --bind /sys "$ROOT/sys"
chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-0328.log 2>&1 & PID=$!
OK=0
for _ in {1..100}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-0328.log; exit 1; }
curl -fsS http://127.0.0.1/api/status | grep -Fq "\"version\":\"$VERSION\""
curl -fsS http://127.0.0.1/api/language | grep -Fq '"selected":false'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.28-alpha'
! strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'fileExists(filepath.Join(dataDir, "uplink-ssid")) && cachedConnectivitySnapshot().Internet'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/rf/ber-calibration'
mkdir -p "$ROOT/var/lib/2pny/protocol-secrets"
printf '%s\n' 'NEVERRETURNME-0328' > "$ROOT/var/lib/2pny/protocol-secrets/dmr.secret"
chmod 600 "$ROOT/var/lib/2pny/protocol-secrets/dmr.secret"
BMJSON="$(curl -fsS http://127.0.0.1/api/brandmeister/api-key)"
echo "$BMJSON" | grep -Fq '"hotspot_security_configured":true'
! echo "$BMJSON" | grep -Fq 'NEVERRETURNME-0328'
curl -fsS http://127.0.0.1/api/config | grep -vq 'NEVERRETURNME-0328'
rm -rf "$ROOT/var/lib/2pny/protocol-secrets"
kill "$PID"; wait "$PID" 2>/dev/null || true; PID=""

echo '[9b/10] 0.3.28 network recovery, scheduled hostfiles and Live state'
NET="$ROOT/usr/local/sbin/2pny-network-switch"
WIFI="$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'nmcli --wait 45 connection up PU2PNY-WIFI-CANDIDATE' "$NET"
grep -Fq 'ipv4.dhcp-timeout 30' "$NET"
grep -Fq 'connection.autoconnect-priority 200 connection.autoconnect-retries 3' "$NET"
grep -Fq 'nm --wait 18 connection up "$chosen"' "$WIFI"
grep -Fq 'nm --wait 22 connection up "$SECONDARY"' "$WIFI"
grep -Fq 'connection.autoconnect-priority 150 connection.autoconnect-retries 3' "$WIFI"
grep -Fq 'OnUnitActiveSec=8h' "$ROOT/etc/systemd/system/2pny-hostfiles-update.timer"
grep -Fq 'Persistent=true' "$ROOT/etc/systemd/system/2pny-hostfiles-update.timer"
test -L "$ROOT/etc/systemd/system/timers.target.wants/2pny-hostfiles-update.timer"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-network-online.service"
grep -Fq 'hostfiles-update.lock' "$ROOT/usr/local/sbin/2pny-hostfiles-update"
grep -Fq '2pny-mdns-guard' "$ROOT/usr/local/sbin/2pny-network-online"
grep -Fq '2pny-hostfiles-update.service' "$ROOT/usr/local/sbin/2pny-network-online"
grep -Fq '2pny-profile-autostart.service' "$ROOT/usr/local/sbin/2pny-network-online"
grep -Fq 'systemctl start --no-block 2pny-network-online.service' "$ROOT/etc/NetworkManager/dispatcher.d/91-pu2pny-online-actions"
grep -Fq '2pny-protocol-profiles","activate",proto' "$ROOT/usr/local/sbin/2pny-profile-autostart"
! grep -Fqi 'restart' "$ROOT/usr/local/sbin/2pny-profile-autostart"
grep -Fq 'Perfil selecionado não está ativo.' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Não conectado ao servidor.' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Ativar perfil selecionado' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'pu2pny-wifi2-target' "$ROOT/usr/share/2pny/internet.html"
grep -Fq "location.replace('/dashboard')" "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'handoffEthernetToLAN' "$ROOT/usr/share/2pny/wizard.html"

echo '[10/10] no leaked runtime state'
for p in "$ROOT/var/lib/2pny/provisioned" "$ROOT/var/lib/2pny/rf-configured" "$ROOT/var/lib/2pny/network-radio.json" "$ROOT/var/lib/2pny/wifi-country"; do test ! -e "$p"; done
echo "PU2PNY-OS $VERSION ARM64 image: protocol-baseline/APRS/BM-security SW/structural gates PASS; RF/Wires-X/DMR-duplex/APRS-external remain HW PENDING"
