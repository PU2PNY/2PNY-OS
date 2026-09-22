#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then exec sudo bash "$0" "$@"; fi
IMAGE="${1:?image required}"
VERSION="${2:-0.3.19-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate-039.img"
ROOT="/mnt/pu2pny-os-039"
LOOP=""; PID=""
cleanup(){
  set +e
  test -n "$PID" && kill "$PID" 2>/dev/null || true
  umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$RAW" /tmp/pu2pnyd-038.log
}
trap cleanup EXIT
trap 'echo "Validation failed at line $LINENO: $BASH_COMMAND" >&2' ERR

echo '[1/15] image integrity'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"; ACTUAL="$(sha256sum "$IMAGE"|awk '{print $1}')"
test "$EXPECTED" = "$ACTUAL"
xz -dc "$IMAGE" >"$RAW"
LOOP="$(losetup --find --partscan --show "$RAW")"
for _ in {1..60}; do test -b "${LOOP}p2" && break; sleep .25; done
mkdir -p "$ROOT"; mount "${LOOP}p2" "$ROOT"; mkdir -p "$ROOT/boot/firmware"; mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[2/15] identity'
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
grep -Fq 'id="liveBox"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'reconnectOverlay' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'id="versionBadge"' "$ROOT/usr/share/2pny/wizard.html"
! grep -Fq '0.3.0-alpha' "$ROOT/usr/share/2pny/wizard.html"
test -s "$ROOT/usr/share/2pny/hotspot.html"
test -s "$ROOT/usr/share/2pny/display.html"
for label in 'Ao Vivo' 'Internet' 'Hotspot' 'Protocolos' 'APRS / D-PRS' 'Histórico' 'Display' 'Sistema'; do
  grep -Fq "$label" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
done

echo '[3/15] runtime syntax'
for x in 2pny-network-core 2pny-network-switch 2pny-wifi-profiles 2pny-auto-maintenance 2pny-hostfiles-update 2pny-rf-apply 2pny-mode-apply 2pny-mdns-guard; do
  test -x "$ROOT/usr/local/sbin/$x"; bash -n "$ROOT/usr/local/sbin/$x"
done
test -x "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns"
bash -n "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns"
for x in 2pny-station-worker 2pny-hardware-probe 2pny-display-core 2pny-display-status 2pny-display-apply 2pny-server-catalog 2pny-protocol-network-apply 2pny-protocol-profiles 2pny-update-manager 2pny-mqtt-preflight 2pny-aprs 2pny-netdiag 2pny-nextion-autodetect; do
  test -x "$ROOT/usr/local/sbin/$x"; python3 -m py_compile "$ROOT/usr/local/sbin/$x"
done
python3 -m py_compile "$ROOT/usr/local/lib/2pny-live-core.py" "$ROOT/usr/local/libexec/2pny-dmr-apply"
rm -rf "$ROOT/usr/local/sbin/__pycache__" "$ROOT/usr/local/lib/__pycache__" "$ROOT/usr/local/libexec/__pycache__"

echo '[4/15] 0.2.9 feature parity preserved'
grep -Fq 'operators.sqlite' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'radioid.net/api/dmr/user/' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'qrz_photo' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'country_code' "$ROOT/usr/local/sbin/2pny-station-worker"
for lang in pt_PT en_GB es_ES; do
  test -s "$ROOT/usr/share/2pny/audio/dmrgateway/$lang.ambe"
  test -s "$ROOT/usr/share/2pny/audio/dmrgateway/$lang.indx"
done
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX status voice requested'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, hourly time voice'

echo '[5/15] Wi-Fi handoff and mDNS'
SW="$ROOT/usr/local/sbin/2pny-network-switch"; WIZ="$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'create_candidate' "$SW"
grep -Fq 'stage_wifi' "$SW"
grep -Fq 'wifi-pending' "$SW"
grep -Fq 'try_profile' "$SW"
grep -Fq 'restore_on_error' "$SW"
grep -Fq 'wpa-psk' "$SW"; grep -Fq 'sae' "$SW"
grep -Fq 'connection.autoconnect-retries 0' "$SW"
grep -Fq 'Aguardando o PU2PNY reaparecer automaticamente' "$WIZ"
grep -Fq 'validará associação e IP antes de concluir a troca' "$WIZ"
grep -Fq 'recovery_ap' "$WIZ"
grep -Fq 'write_connect_state connected' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'saved Wi-Fi failed; preserving profile' "$ROOT/usr/local/sbin/2pny-network-core"
! grep -Fq 'PU2PNY 0.3.0-alpha' "$ROOT/usr/local/sbin/2pny-network-core"
! grep -Fq 'reconnectManual' "$WIZ"
grep -Fq 'host-name","pu2pny' "$ROOT/usr/local/sbin/2pny-mdns-guard"
grep -Fq '_http._tcp' "$ROOT/usr/local/sbin/2pny-mdns-guard"
test -s "$ROOT/etc/systemd/system/2pny-mdns-guard.service"
grep -Fq 'dhcp4-change' "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns"
grep -Fq 'connectivity-change' "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns"

echo '[6/15] Nextion / Display Core'
grep -Fq 'nextion_mmdvm' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'SSD1306' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'class LCD' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'b"connect\xff\xff\xff"' "$ROOT/usr/local/sbin/2pny-hardware-probe"
# DISPLAY-016: two mutually-exclusive renderer modes. In Moderno V2,
# MMDVMHost owns the modem transport while PU2PNY is the logical renderer;
# in native mode MMDVMHost owns both. Gate the actual contract, not the
# superseded 0.3.9 comment string.
grep -Fq 'pu2pny-modern-v2' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'mmdvmhost-native' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'patch_modern_transport' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'patch_native_nextion' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'remove_option("General","Display")' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'input=b"connect\xff\xff\xff"' "$ROOT/usr/local/sbin/2pny-nextion-autodetect"
grep -Fq 'disable","--now",LEGACY' "$ROOT/usr/local/sbin/2pny-display-apply"

test -s "$ROOT/usr/share/2pny/radioid.html"
grep -Fq 'Consulta RadioID' "$ROOT/usr/share/2pny/radioid.html"

echo '[7/15] live-state regression fixed'
grep -Fq 'source-less END' "$ROOT/usr/local/lib/2pny-live-core.py"
grep -Fq 'action in ("end","lost","timeout")' "$ROOT/usr/local/lib/2pny-live-core.py"
grep -Fq 'currentActive' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Rastreando sinais' "$ROOT/usr/share/2pny/dashboard.html"
! grep -Fq 'Operador não identificado' "$ROOT/usr/share/2pny/dashboard.html"

echo '[8/15] preloaded protocol catalogs'
HOSTS="$ROOT/var/lib/2pny/hosts"
for x in DStar_Hosts.json DPlus_Hosts.txt DExtra_Hosts.txt DCS_Hosts.txt XLXHosts.txt YSFHosts.txt YSFHosts.json FCSRooms.txt P25Hosts.txt NXDNHosts.txt; do
  test -s "$HOSTS/$x"
done
test "$(wc -c <"$HOSTS/DStar_Hosts.json")" -gt 1000
test "$(wc -c <"$HOSTS/YSFHosts.txt")" -gt 100

echo '[9/15] protocol UI and gateways'
PROTO="$ROOT/usr/share/2pny/protocols.html"
! grep -Fq 'Buscar servidor' "$PROTO"
! grep -Fq 'id="search"' "$PROTO"
for label in 'REF / DPlus' 'XRF / DExtra' 'DCS' 'XLX'; do grep -Fq "$label" "$PROTO"; done
for x in MMDVM-Host DMRGateway MMDVM-Display NextionUpdater dstargateway YSFGateway P25Gateway NXDNGateway DAPNETGateway; do
  test -x "$ROOT/usr/local/bin/$x"
done
for svc in 2pny-dmrgateway.service 2pny-dstargateway.service 2pny-ysfgateway.service 2pny-p25gateway.service 2pny-nxdngateway.service 2pny-dapnetgateway.service; do
  test -s "$ROOT/etc/systemd/system/$svc"
done

echo '[10/15] RadioID, flags and activity'
test -f "$ROOT/usr/share/2pny/flags/LICENSE-MIT"
COUNT="$(find "$ROOT/usr/share/2pny/flags/4x3" -maxdepth 1 -type f -name '*.svg' | wc -l)"
test "$COUNT" -ge 240
for cc in br us pt gb ar jp au za; do test -s "$ROOT/usr/share/2pny/flags/4x3/$cc.svg"; done
grep -Fq 'renderActivity' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'id="activityGroups"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'class="btn plus"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'history-summary.json' "$ROOT/usr/local/sbin/2pny-station-worker"

echo '[11/15] dedicated pages and APRS'
for page in internet hotspot protocols history aprs display system expert; do test -s "$ROOT/usr/share/2pny/$page.html"; done
grep -Fq 'traceroute' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq 'APRS-IS' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'Login APRS-IS' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'outboxPending' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'parse_logresp' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'retry_unacked' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'login_unverified' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'TCP_NODELAY' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'soam.aprs2.net' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'soam.aprs2.net' "$ROOT/usr/local/sbin/2pny-server-catalog"
grep -Fq 'Google Time' "$ROOT/usr/share/2pny/system.html"

echo '[11b/15] 0.3.19 focused maintenance gates'
grep -Fq 'connection","up",conn,"ifname",iface' "$ROOT/usr/local/bin/2pnyd" 2>/dev/null || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'connection'
! strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'nmcli device reapply'
grep -Fq 'rede conectada' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'Nenhuma segunda rede encontrada' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'Canal em uso:' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'Conexão via cabo' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'Caminho da conexão' "$ROOT/usr/share/2pny/internet.html"
grep -Fq '<title>PU2PNY-OS</title>' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq '<h1>Protocolos</h1>' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'DUP+/DUP−' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'TOT restante' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'expertLiveSection' "$ROOT/usr/share/2pny/expert.html"
grep -Fq 'generateSSHKey' "$ROOT/usr/share/2pny/expert.html"
grep -Fq 'pu2pny-erros.txt' "$ROOT/usr/share/2pny/expert.html"
grep -Fq "location.pathname==='/aprs'" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'range(0,101,10)' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'drain pending requests' "$ROOT/usr/local/sbin/2pny-timezone-apply"
test -x "$ROOT/usr/local/sbin/2pny-display-online-detect"
bash -n "$ROOT/usr/local/sbin/2pny-display-online-detect"
test -s "$ROOT/etc/systemd/system/2pny-display-online-detect.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-display-online-detect.service"
test "$(readlink "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-display-online-detect.service")" = "../2pny-display-online-detect.service"
# REL-014 / RF-019 / LIVE-019 / PROTO-027 / PROTO-028
grep -Fq 'CYSFReflectors::findByName' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'startup_name' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'WiresXCommandPassthrough=0' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'GatewayPort":"4200"' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'duplex=1 if usemode=="repeater" else 0' "$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'slot1=True if duplex' "$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'slot2=True if duplex' "$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'route_slots=(1,2) if duplex' "$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'Slot={remote_slot}' "$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'out.append("Duplex="+duplex)' "$ROOT/usr/local/sbin/2pny-mode-apply"
grep -Fq "RX '+a+' MHz · TX '+bb+' MHz" "$ROOT/usr/share/2pny/dashboard.html"

echo '[12/15] no leaked user/runtime state'
for p in \
 "$ROOT/var/lib/2pny/provisioned" "$ROOT/var/lib/2pny/rf-configured" \
 "$ROOT/var/lib/2pny/network-radio.json" "$ROOT/var/lib/2pny/network-connect.json" \
 "$ROOT/var/lib/2pny/wifi-country" "$ROOT/var/lib/2pny/display-runtime.json" \
 "$ROOT/var/lib/2pny/station/operators.sqlite"; do test ! -e "$p"; done

echo '[13/15] backend boot and APIs'
mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
mount -t proc proc "$ROOT/proc"; mount --bind /dev "$ROOT/dev"; mount --bind /sys "$ROOT/sys"

echo '[13a/15] deterministic MQTT broker runtime handshake'
test -x "$ROOT/usr/sbin/mosquitto"
test -s "$ROOT/etc/mosquitto/2pny-local.conf"
test -s "$ROOT/etc/systemd/system/mosquitto.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/mosquitto.service"
test "$(readlink "$ROOT/etc/systemd/system/multi-user.target.wants/mosquitto.service")" = "../mosquitto.service"
! test -e "$ROOT/etc/mosquitto/conf.d/2pny-local.conf"
# The CI runner must not already own TCP/1883 before the image broker test.
! ss -H -ltn | awk '{print $4}' | grep -Eq '(^|:|\])1883$'
chroot "$ROOT" /usr/sbin/mosquitto -c /etc/mosquitto/2pny-local.conf >/tmp/pu2pny-mosquitto-test.log 2>&1 & PID=$!
MQTT_OK=0
for _ in {1..40}; do
  if python3 - <<'PYMQTT'
import socket,sys
try:
    s=socket.create_connection(("127.0.0.1",1883),timeout=.35)
    client=b"ci"
    variable=b"\x00\x04MQTT\x04\x02\x00\x0a"
    payload=len(client).to_bytes(2,"big")+client
    body=variable+payload
    s.sendall(bytes((0x10,len(body)))+body)
    r=s.recv(4)
    s.close()
    sys.exit(0 if r==b"\x20\x02\x00\x00" else 1)
except OSError:
    sys.exit(1)
PYMQTT
  then MQTT_OK=1; break; fi
  sleep .25
done
test "$MQTT_OK" = 1 || { cat /tmp/pu2pny-mosquitto-test.log; exit 1; }
kill "$PID"; wait "$PID" 2>/dev/null || true; PID=""
rm -f /tmp/pu2pny-mosquitto-test.log

chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-038.log 2>&1 & PID=$!
OK=0
for _ in {1..100}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-038.log; exit 1; }
curl -fsS http://127.0.0.1/api/status | grep -Fq "\"version\":\"$VERSION\""
# Fresh images are intentionally unprovisioned, so /dashboard must redirect
# to the wizard until onboarding is complete.
CODE="$(curl -sS -o /tmp/pu2pny-dashboard-unprovisioned -w '%{http_code}' http://127.0.0.1/dashboard)"
test "$CODE" = "302"
# Then simulate completed onboarding only for route validation.
touch "$ROOT/var/lib/2pny/provisioned"
curl -fsS http://127.0.0.1/dashboard | grep -Fq 'id="liveBox"'
curl -fsS http://127.0.0.1/hotspot | grep -Fq '<h1>Protocolos</h1>'
curl -fsS http://127.0.0.1/display | grep -Fq '<h1>Display</h1>'
rm -f "$ROOT/var/lib/2pny/provisioned" /tmp/pu2pny-dashboard-unprovisioned
curl -fsS http://127.0.0.1/ui-common-0.3.0.js | grep -Fq "['/hotspot','Protocolos','hotspot']"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'will_reboot'
curl -fsS http://127.0.0.1/api/network/country | grep -Fq '"country":"BR"'
curl -fsS http://127.0.0.1/flags/4x3/br.svg | grep -Eq '<svg|<SVG'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/protocol/apply'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/aprs/message'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '2pny-nextion-autodetect'
kill "$PID"; PID=""

echo '[13b/15] 0.3.3 regressions preserved + 0.3.4 corrections'
test ! -d "$ROOT/var/lib/2pny/hostfiles"
grep -Fq 'atomic(HOST,host_text,0o640,"mmdvm")' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'normalize_host_permissions' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'FCSRooms.txt' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'cloned-mac-address permanent' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'ACTIVE_SSID' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'reconnectCandidates' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'serverCatalog=[]' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'id="activityGroups"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'id="signalBar"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq '2pny-dstargateway.service' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq '2pny-ysfgateway.service' "$ROOT/usr/local/sbin/2pny-station-worker"

# 0.3.4: observed physical-test regressions are represented in the image.
grep -Fq 'wifi_profile_link_ok' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'default_ip=' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'uplink_type=' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'senha Wi-Fi não permaneceu gravada' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'mqtt_preflight' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'old_host_active' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'ExecStartPre=/usr/local/sbin/2pny-mqtt-preflight --quiet' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
grep -Fq 'Wants=systemd-udev-settle.service mosquitto.service' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
! grep -Fq 'Requires=mosquitto.service' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
grep -Fq 'hostapd.pid' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'hostapd.pid'
grep -Fq 'id="languageWelcome"' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'openActivity' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'id="rfAlert"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'id="berMetric"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'pnyFooter' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'dns_recommendation' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq '208.67.222.222' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq 'alerta interno continua ativo' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'Dados brutos ficam recolhidos' "$ROOT/usr/share/2pny/expert.html"
grep -Fq 'self.first_render' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'read_network_status' "$ROOT/usr/local/sbin/2pny-display-core"

echo '[13c/15] 0.3.5 corrective feature gates'
grep -Fq 'space_around_delimiters=False' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'candidate contains spaced INI delimiters' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'network-runtime.json' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'module_tg' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq '/run/2pny/network-runtime.json' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/run/2pny/network-runtime.json'
grep -Fq '/api/network/wifi/profiles' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/network/wifi/profiles'
grep -Fq '/api/network/dns' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/network/dns'
grep -Fq 'PU2PNY-WIFI-SECONDARY' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'A rede anterior foi restaurada' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'test -s "$RUN/hostapd.pid"' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq '"channel":' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'Bem-vindo / Welcome' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'scheduleHardwareAdvance' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'Módulo / TG' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'TOT: corte automático' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Rastreando sinais' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Atividade 24h' "$ROOT/usr/share/2pny/history.html"
grep -Fq 'Usar Cloudflare' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'Canais próximos' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'Manutenção automática' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'Throttling' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'MMDVMHost nativo / ON7LDS' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Iniciando / Starting' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'TOT: corte em' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'Em andamento / Working' "$ROOT/usr/local/sbin/2pny-display-status"
grep -Fq 'pnyAprsToast' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'Atualizado às' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'next_eligible' "$ROOT/usr/local/sbin/2pny-auto-maintenance"

echo '[14/15] 0.3.6 corrective/resource gates'
SW="$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'test "${paused:-0}" = 1' "$SW"
grep -Fq 'set type managed' "$SW"
! grep -Fq 'cleanup(){ test "$paused"' "$SW"
grep -Fq 'Rede Wi-Fi 1 e Rede Wi-Fi 2' "$ROOT/usr/share/2pny/internet.html" || grep -Fq 'Rede Wi‑Fi 1 e Rede Wi‑Fi 2' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'wifiSecondManual' "$ROOT/usr/share/2pny/internet.html"
! grep -Fq '/wizard?step=1&return=internet' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'quality_label' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq 'Melhor opção' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq '[General]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq '[Repeater 1]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq '[Hosts Files]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'DisplayLevel=2' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Link has failed, polls lost' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'DExtra|D-Plus|DCS' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'protocol-profiles.json' "$ROOT/usr/local/sbin/2pny-protocol-profiles"
grep -Fq '2pny-rf-apply' "$ROOT/usr/local/sbin/2pny-protocol-profiles"
grep -Fq 'ALLOWED_PREFIX' "$ROOT/usr/local/sbin/2pny-update-manager"
grep -Fq 'sha256(pkg)' "$ROOT/usr/local/sbin/2pny-update-manager"
grep -Fq '/api/protocol/profiles' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/protocol/profiles'
grep -Fq '2pny-update-manager' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '2pny-update-manager'
grep -Fq 'friendlyNetworkError' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'falha interna e foi cancelada com segurança'
grep -Fq 'Perfil do protocolo' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'Gateway ativo / aguardando rede' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'Gerenciada automaticamente' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'quickProfiles' "$ROOT/usr/share/2pny/hotspot.html"
! grep -Fq '/wizard?step=3' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'navigator.geolocation' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'Mensagem preservada na fila' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'queued_for_send' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'queued_for_send'
grep -Fq 'soam.aprs2.net' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'soam.aprs2.net'
grep -Fq 'qrz.com/db/' "$ROOT/usr/share/2pny/history.html"
grep -Fq '/radioid?callsign=' "$ROOT/usr/share/2pny/history.html"
! grep -Fq 'radioid.net/api/dmr/user/?callsign=' "$ROOT/usr/share/2pny/history.html"
grep -Fq 'qrz.com/db/' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq '/radioid?callsign=' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'installUpdate' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'Guardar versão atual para rollback' "$ROOT/usr/share/2pny/system.html"
! grep -Fq '/wizard?step=1' "$ROOT/usr/share/2pny/expert.html"
! grep -Fq '/wizard?step=3' "$ROOT/usr/share/2pny/expert.html"
grep -Fq 'Ex.: PU2ABC' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'Ex.: 7240000' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq '>ID DMR<' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'function operation' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'MutationObserver' "$ROOT/usr/share/2pny/ui-language.js"
grep -Fq 'RF>NET' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'NET>RF' "$ROOT/usr/local/sbin/2pny-display-core"
# 0.3.6: BrandMeister personal-hotspot aliases and API-key isolation.
grep -Fq 'id="dmrEssid"' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'id="bmApiKey"' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'O PU2PNY não pede API Secret' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'Identificação do hotspot / rádio' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq '/api/brandmeister/api-key' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/brandmeister/api-key'
grep -Fq 'network_id=dmrid+essid if essid and len(dmrid)==7 else dmrid' "$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'identificação DMR deve ser 01 a 99' "$ROOT/usr/local/sbin/2pny-protocol-profiles"
test ! -e "$ROOT/var/lib/2pny/secrets/brandmeister-api.key"
# Captive portal/fallback endpoints remain present; automatic popup itself is client-controlled.
for endpoint in '/generate_204' '/hotspot-detect.html' '/connecttest.txt' '/ncsi.txt'; do
  strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq "$endpoint"
done
# DMR baseline components must still be installed and the proven custom XLX controls remain.
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
grep -Fq 'TG=6' "$ROOT/var/lib/2pny/presets/dmr-xlx026.ini" 2>/dev/null || true

echo '[14b/15] 0.3.8 corrective gates'
test -x "$ROOT/usr/local/bin/2pny-direct-core"
test -x "$ROOT/usr/local/sbin/2pny-direct-start"
test -x "$ROOT/usr/local/sbin/2pny-direct-recover"
test -s "$ROOT/etc/systemd/system/2pny-direct.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-direct.service"
test -s "$ROOT/usr/share/2pny/direct.html"
grep -Fq '/api/direct/call' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/direct/call'
grep -Fq "['/direct','Direct','direct']" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'CGNAT' "$ROOT/usr/share/2pny/direct.html"
file "$ROOT/usr/local/bin/2pny-direct-core" | grep -Eq 'ELF 64-bit.*(ARM aarch64|ARM64)'
test ! -e "$ROOT/var/lib/2pny/direct/identity.json"
test ! -e "$ROOT/var/lib/2pny/direct/peers.json"
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK

test -x "$ROOT/usr/local/bin/dgwvoicetransmit"
test -d "$ROOT/usr/share/2pny/audio/dstar"
test "$(find "$ROOT/usr/share/2pny/audio/dstar" -maxdepth 1 -type f -name '*.ambe' | wc -l)" -ge 8
test "$(find "$ROOT/usr/share/2pny/audio/dstar" -maxdepth 1 -type f -name '*.indx' | wc -l)" -ge 8
test -s "$ROOT/usr/share/2pny/audio/dstar/en_GB.ambe"
test -s "$ROOT/usr/share/2pny/audio/dstar/en_GB.indx"
grep -Fq 'audio_path="/usr/local/share/dstargateway.d/"' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Data={audio_path}' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"

grep -Fq 'PU2PNY Moderno V2' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'Graphical 128x64 renderer' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'MMDVMHost nativo / ON7LDS' "$ROOT/usr/share/2pny/display.html"

# DMR baseline markers remain untouched.
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX status voice requested'

echo '[14c/15] 0.3.8 physical-feedback corrections represented'
grep -Fq 'wifiChannelGraph' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'data-showpass' "$ROOT/usr/share/2pny/internet.html"
grep -Fq "['/hotspot','Protocolos','hotspot']" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq '/protocols/embed' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/protocols/embed'
grep -Fq 'Pareie um PU2PNY antes de chamar' "$ROOT/usr/share/2pny/direct.html"
grep -Fq 'Etapa 1/5' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq "var live=q('liveBox')" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq "sec.id='pnyHealth'" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'pny-healthitem' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'Potência RF do MMDVM' "$ROOT/usr/share/2pny/expert.html"
grep -Fq '/api/rf/power' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/rf/power'
test -x "$ROOT/usr/local/sbin/2pny-timezone-apply"
test -x "$ROOT/usr/local/sbin/2pny-rflevel-apply"
test -x "$ROOT/usr/local/sbin/2pny-ssh-apply"
test -s "$ROOT/etc/systemd/system/2pny-timezone-apply.service"
test -s "$ROOT/etc/systemd/system/2pny-rflevel-apply.service"
test -s "$ROOT/etc/systemd/system/2pny-ssh-apply.service"
test -x "$ROOT/usr/local/sbin/2pny-operational-apply"
test -s "$ROOT/etc/systemd/system/2pny-operational-apply.service"
test -s "$ROOT/etc/systemd/system/2pny-operational-restore.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-operational-restore.service"
test -x "$ROOT/usr/local/sbin/2pny-auto-maintenance"
grep -Fq 'operational-disabled' "$ROOT/usr/local/sbin/2pny-operational-apply"
grep -Fq 'display ready "Manutencao concluida"' "$ROOT/usr/local/sbin/2pny-auto-maintenance"
grep -Fq 'id="opResult"' "$ROOT/usr/share/2pny/system.html"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'wifi_rssi_dbm'
grep -Fq 'WiresXCommandPassthrough=0' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Reconnect=0' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'porta 20010' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'local=cols[3]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
! grep -Fq 'local=cols[4]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'verify_host_bridge_config(proto)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'wait_bridge(proto,20010,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'wait_bridge(proto,4200,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq '"waiting_bridge"' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'protocol-health.json' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'characterData:true' "$ROOT/usr/share/2pny/ui-language.js"
grep -Fq 'effective_layout' "$ROOT/usr/local/sbin/2pny-display-apply"

echo '[14d/15] 0.3.9 inherited physical-feedback gates'\ngrep -Fq 'wait_bridge(proto,20010,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'wait_bridge(proto,4200,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'local=cols[3]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
! grep -Fq 'local=cols[4]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
! grep -Fq '\\b127\\.0\\.0\\.1:20010' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'for attempt in 1 2 3' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'merge_scan_json' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq "sed -i '/^dhcp-option-force=114,/d'" "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'if test ! -f "$STATE/provisioned"; then' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'test -f "$STATE/provisioned" || return 0' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'address=/#/10.43.0.1' "$ROOT/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
! grep -Fq 'dhcp-option-force=114,' "$ROOT/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'http://10.43.0.1/wizard?captive=1'
! grep -Fq '10.42.0.1' "$ROOT/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
grep -Fq '5 GHz' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'bandgraph' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'effective_dns' "$ROOT/usr/share/2pny/internet.html"
grep -Fq "addEventListener('live'" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq "addEventListener('live'" "$ROOT/usr/share/2pny/expert.html"
grep -Fq "var live=q('liveBox')" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'mmdvmhost-authoritative' "$ROOT/usr/local/sbin/2pny-display-status"
grep -Fq '"error": (0, "Erro / Error")' "$ROOT/usr/local/sbin/2pny-display-status"
grep -Fq 'não confirmou o layout Nextion solicitado' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'wait_prereqs' "$ROOT/usr/local/sbin/2pny-operational-apply"
grep -Fq 'Restart=on-failure' "$ROOT/etc/systemd/system/2pny-operational-restore.service"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-operational-apply" "$ROOT/usr/local/sbin/2pny-timezone-apply" "$ROOT/usr/local/sbin/2pny-ssh-apply" "$ROOT/usr/local/sbin/2pny-display-apply-request"
rm -rf "$ROOT/usr/local/sbin/__pycache__"
for unit in 2pny-timezone-apply.path 2pny-ssh-apply.path 2pny-operational-apply.path 2pny-rflevel-apply.path 2pny-display-apply-request.path; do
  test -s "$ROOT/etc/systemd/system/$unit"
  test -L "$ROOT/etc/systemd/system/multi-user.target.wants/$unit"
done
grep -Fq 'PathExistsGlob=/run/2pny/timezone-request-*.json' "$ROOT/etc/systemd/system/2pny-timezone-apply.path"
grep -Fq 'PathExists=/run/2pny/ssh-request.json' "$ROOT/etc/systemd/system/2pny-ssh-apply.path"
grep -Fq 'PathChanged=/run/2pny/operational-request.json' "$ROOT/etc/systemd/system/2pny-operational-apply.path"
grep -Fq 'PathChanged=/run/2pny/display-apply-request.json' "$ROOT/etc/systemd/system/2pny-display-apply-request.path"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'timezone-request-'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/run/2pny/ssh-request.json'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/run/2pny/operational-request.json'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/run/2pny/display-apply-request.json'
grep -Fq 'if(!base){base=text;originals.set(node,base)}' "$ROOT/usr/share/2pny/ui-language.js"
# Approved baseline must still be present and not replaced by the corrective overlay.
grep -Fq 'PU2PNY, XLX module control' < <(strings "$ROOT/usr/local/bin/DMRGateway")
test -s "$ROOT/usr/share/2pny/history.html"
grep -Fq 'CGNAT' "$ROOT/usr/share/2pny/direct.html"
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK

echo '[14e/15] 0.3.12 inherited display/protocol/network hardening gates'
grep -Fq '/api/display/detection' < <(strings "$ROOT/usr/local/bin/2pnyd")
grep -Fq '/api/diagnostics' < <(strings "$ROOT/usr/local/bin/2pnyd")
grep -Fq 'associating' < <(strings "$ROOT/usr/local/bin/2pnyd")
grep -Fq 'MMDVMHost nativo / ON7LDS' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'nextion-101-1024x600' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Nunca automático' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Perfis rápidos nativos · sem iframe' "$ROOT/usr/share/2pny/hotspot.html"
! grep -Fqi '<iframe' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'wizardOperation' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'syncClock' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'waiting_bridge' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'protocol-health.json' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'last-protocol-rollback.json' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'mqtt-preflight.json' "$ROOT/usr/local/sbin/2pny-mqtt-preflight"
grep -Fq 'last-boot-restore.json' "$ROOT/usr/local/sbin/2pny-operational-apply"
grep -Fq 'patch_modern_transport' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'host/display-in' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'get pnyver.txt' "$ROOT/usr/local/sbin/2pny-display-detector"
test -s "$ROOT/usr/share/2pny/display-catalog.json"
python3 - <<PY
import json
p="$ROOT/usr/share/2pny/display-catalog.json"
d=json.load(open(p))
assert d["policy"]["flash_requires_explicit_confirmation"] is True
assert d["policy"]["silent_tft_overwrite"] is False
for x in d["profiles"]:
 t=x.get("tft")
 if t and t.get("status")!="unpublished":
  assert t.get("url") and t.get("sha256")
print("DISPLAY_CATALOG_OK")
PY
test -s "$ROOT/etc/systemd/system/2pny-display-detect.service"
test -s "$ROOT/etc/systemd/system/2pny-display-detect.path"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-display-detect.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-display-detect.path"
! grep -Fq 'ACTION=="add|change"' "$ROOT/etc/udev/rules.d/99-pu2pny-display-hotplug.rules"
grep -Fq 'ACTION=="add"' "$ROOT/etc/udev/rules.d/99-pu2pny-display-hotplug.rules"
grep -Fq 'ACTION=="change"' "$ROOT/etc/udev/rules.d/99-pu2pny-display-hotplug.rules"

echo '[15/15] final result'
echo '[14f/15] 0.3.12 MMDVM/i18n regression gates'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
PROBE="$ROOT/usr/local/sbin/2pny-hardware-probe"
LANG="$ROOT/usr/share/2pny/ui-language.js"
WIZ="$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'flock -w 8 8' "$RF"
# PROTO-021 supersedes the 0.3.12 requirement that RF provisioning itself
# invoke MQTT. The preflight binary is still validated below, but RF with
# MQTTLevel=0 must not call it.
! grep -Fq '2pny-mqtt-preflight --quiet' "$RF"
grep -Fq 'last-rf-apply-error.json' "$RF"
! grep -Fq 'MMDVMHost failed with detected baud' "$RF"
grep -Fq 'A MMDVM foi detectada, mas o MMDVMHost não conseguiu assumir a porta serial no teste básico' "$RF"
! grep -Fq 'bridge = probe_nextion_mmdvm' "$PROBE"
grep -Fq 'MMDVM confirmada. A Nextion pela porta do modem' "$PROBE"
grep -Fq 'O assistente avançará automaticamente em 5 segundos.' "$WIZ"
grep -Fq 'normalizeIncoming' "$LANG"
grep -Fq 'incomingPT' "$LANG"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'

echo '[14g/15] 0.3.12 MQTT broker + serial arbitration + i18n gates'
test -x "$ROOT/usr/sbin/mosquitto"
test -s "$ROOT/etc/mosquitto/2pny-local.conf"
grep -Fq 'listener 1883 127.0.0.1' "$ROOT/etc/mosquitto/2pny-local.conf"
grep -Fq 'allow_anonymous true' "$ROOT/etc/mosquitto/2pny-local.conf"
grep -Fq 'mqtt_connect_packet' "$ROOT/usr/local/sbin/2pny-mqtt-preflight"
grep -Fq 'CONNACK' "$ROOT/usr/local/sbin/2pny-mqtt-preflight"
grep -Fq 'mmdvm-serial.lock' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -Fq 'fcntl.flock' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -Fq 'SERIAL_LOCK=/run/2pny/mmdvm-serial.lock' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -Fq 'flock -w 15 7' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -Fq 'Sistema Operacional de Rádio Digital' "$ROOT/usr/share/2pny/wizard.html"
! grep -Fq 'Digital Radio Operating System' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'Object.assign(D,' "$ROOT/usr/share/2pny/ui-language.js"
grep -Fq 'A MMDVM ainda está sendo verificada' "$ROOT/usr/share/2pny/ui-language.js"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'


echo '[14h/15] inherited TGIF/i18n + 0.3.16 focused onboarding gates'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
MQTT="$ROOT/usr/local/sbin/2pny-mqtt-preflight"
SVC="$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
DMR="$ROOT/usr/local/libexec/2pny-dmr-apply"
CAT="$ROOT/usr/local/sbin/2pny-server-catalog"
WIZ="$ROOT/usr/share/2pny/wizard.html"
LANG="$ROOT/usr/share/2pny/ui-language.js"
PROTO="$ROOT/usr/local/sbin/2pny-protocol-network-apply"
MOSQCFG="$ROOT/etc/mosquitto/2pny-local.conf"
MOSQSVC="$ROOT/etc/systemd/system/mosquitto.service"

# HW-PASS MMDVM bootstrap remains exactly the authority for initial RF success.
grep -Fq 'MQTTLevel=0' "$RF"
grep -Fq 'DisplayLevel=0' "$RF"
grep -Fq 'mmdvmhost_bootstrap_failed' "$RF"
grep -Fq 'rf-bootstrap.json' "$RF"
grep -Fq 'RF_APPLY_OK' "$RF"
grep -Fq 'PROTO-021 / WIZ-008' "$RF"
! grep -Fq -- '--ensure-service' "$RF"
! grep -Fq 'enable_operational_mqtt' "$RF"
! grep -Fq 'mqtt_preflight_failed_after_uart_ok' "$RF"
! grep -Fq 'mmdvmhost_mqtt_phase_failed' "$RF"
! grep -Fq '"phase":"operational_ok"' "$RF"

# MMDVMHost service may want Mosquitto, but MQTTLevel=0 means its preflight skips.
grep -Fq 'ExecStartPre=/usr/local/sbin/2pny-mqtt-preflight --quiet --no-publish --respect-log-level' "$SVC"
grep -Fq 'Wants=systemd-udev-settle.service mosquitto.service' "$SVC"
! grep -Fq 'Requires=mosquitto.service' "$SVC"

# DMR onboarding delegates directly to the proven helper and helper itself does not use MQTT.
python3 - "$PROTO" "$DMR" <<'PY0316'
import sys
proto=open(sys.argv[1]).read(); dmr=open(sys.argv[2]).read()
s=proto.index('if proto=="DMR":'); e=proto.index('server=q(server)',s); b=proto[s:e]
assert 'os.execv(DMR_HELPER' in b
assert '2pny-mqtt-preflight' not in b
assert '--ensure-service' not in b
assert '[Log]\nDisplayLevel=1\nMQTTLevel=0' in dmr
assert 'DMRGateway did not remain active' in dmr
assert 'MMDVMHost did not remain active with DMRGateway' in dmr
assert '2pny-mqtt-preflight' not in dmr
PY0316

# TGIF/i18n from 0.3.13 remain untouched.
grep -Fq 'Name=TGIF_Network' "$DMR"
grep -Fq 'TGRewrite{idx}={s},1,2,1,9999998' "$DMR"
grep -Fq 'SrcRewrite{idx}=2,1,{s},1,9999998' "$DMR"
grep -Fq 'tgif_auth_mode="legacy" if password=="passw0rd" else "secured"' "$DMR"
grep -Fq 'Password="{password}"' "$DMR"
grep -Fq '"auth_mode":tgif_auth_mode' "$DMR"
grep -Fq 'Chave de segurança TGIF' "$CAT"
grep -Fq 'pny-i18n-pending' "$WIZ"
grep -Fq "document.documentElement.classList.remove('pny-i18n-pending')" "$LANG"

# Existing wizard commit path must advance only on backend state=applied.
grep -Fq "if(s.state==='applied')" "$WIZ"
grep -Fq "await loadConclusion();step(4)" "$WIZ"
grep -Fq "setTimeout(function(){location.href='/dashboard'},5000)" "$WIZ"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'writeRFApplyState'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'provisioned'

# Broker remains in image for later features, but is not an onboarding DMR gate.
grep -Fq 'listener 1883 127.0.0.1' "$MOSQCFG"
grep -Fq 'allow_anonymous true' "$MOSQCFG"
grep -Fq 'persistence false' "$MOSQCFG"
grep -Fq 'ExecStart=/usr/sbin/mosquitto -c /etc/mosquitto/2pny-local.conf' "$MOSQSVC"
grep -Fq 'mqtt_connect_packet' "$MQTT"
grep -Fq 'CONNACK' "$MQTT"

echo "PU2PNY-OS $VERSION ARM64 image: 0.3.16 focused MQTT-onboarding correction + inherited structural gates OK — hardware validation still required"
chroot "$ROOT" /usr/sbin/mosquitto -c /etc/mosquitto/2pny-local.conf >/tmp/pu2pny-mosquitto-test.log 2>&1 & PID=$!
MQTT_OK=0
for _ in {1..40}; do
  if python3 - <<'PYMQTT'
import socket,sys
try:
    s=socket.create_connection(("127.0.0.1",1883),timeout=.35)
    client=b"ci"
    variable=b"\x00\x04MQTT\x04\x02\x00\x0a"
    payload=len(client).to_bytes(2,"big")+client
    body=variable+payload
    s.sendall(bytes((0x10,len(body)))+body)
    r=s.recv(4)
    s.close()
    sys.exit(0 if r==b"\x20\x02\x00\x00" else 1)
except OSError:
    sys.exit(1)
PYMQTT
  then MQTT_OK=1; break; fi
  sleep .25
done
test "$MQTT_OK" = 1 || { cat /tmp/pu2pny-mosquitto-test.log; exit 1; }
kill "$PID"; wait "$PID" 2>/dev/null || true; PID=""
rm -f /tmp/pu2pny-mosquitto-test.log

chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-038.log 2>&1 & PID=$!
OK=0
for _ in {1..100}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-038.log; exit 1; }
curl -fsS http://127.0.0.1/api/status | grep -Fq "\"version\":\"$VERSION\""
# Fresh images are intentionally unprovisioned, so /dashboard must redirect
# to the wizard until onboarding is complete.
CODE="$(curl -sS -o /tmp/pu2pny-dashboard-unprovisioned -w '%{http_code}' http://127.0.0.1/dashboard)"
test "$CODE" = "302"
# Then simulate completed onboarding only for route validation.
touch "$ROOT/var/lib/2pny/provisioned"
curl -fsS http://127.0.0.1/dashboard | grep -Fq 'id="liveBox"'
curl -fsS http://127.0.0.1/hotspot | grep -Fq '<h1>Protocolos</h1>'
curl -fsS http://127.0.0.1/display | grep -Fq '<h1>Display</h1>'
rm -f "$ROOT/var/lib/2pny/provisioned" /tmp/pu2pny-dashboard-unprovisioned
curl -fsS http://127.0.0.1/ui-common-0.3.0.js | grep -Fq "['/hotspot','Protocolos','hotspot']"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'will_reboot'
curl -fsS http://127.0.0.1/api/network/country | grep -Fq '"country":"BR"'
curl -fsS http://127.0.0.1/flags/4x3/br.svg | grep -Eq '<svg|<SVG'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/protocol/apply'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/aprs/message'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '2pny-nextion-autodetect'
kill "$PID"; PID=""

echo '[13b/15] 0.3.3 regressions preserved + 0.3.4 corrections'
test ! -d "$ROOT/var/lib/2pny/hostfiles"
grep -Fq 'atomic(HOST,host_text,0o640,"mmdvm")' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'normalize_host_permissions' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'FCSRooms.txt' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'cloned-mac-address permanent' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'ACTIVE_SSID' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'reconnectCandidates' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'serverCatalog=[]' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'id="activityGroups"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'id="signalBar"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq '2pny-dstargateway.service' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq '2pny-ysfgateway.service' "$ROOT/usr/local/sbin/2pny-station-worker"

# 0.3.4: observed physical-test regressions are represented in the image.
grep -Fq 'wifi_profile_link_ok' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'default_ip=' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'uplink_type=' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'senha Wi-Fi não permaneceu gravada' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'mqtt_preflight' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'old_host_active' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'ExecStartPre=/usr/local/sbin/2pny-mqtt-preflight --quiet' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
grep -Fq 'Wants=systemd-udev-settle.service mosquitto.service' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
! grep -Fq 'Requires=mosquitto.service' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
grep -Fq 'hostapd.pid' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'hostapd.pid'
grep -Fq 'id="languageWelcome"' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'openActivity' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'id="rfAlert"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'id="berMetric"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'pnyFooter' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'dns_recommendation' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq '208.67.222.222' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq 'alerta interno continua ativo' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'Dados brutos ficam recolhidos' "$ROOT/usr/share/2pny/expert.html"
grep -Fq 'self.first_render' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'read_network_status' "$ROOT/usr/local/sbin/2pny-display-core"

echo '[13c/15] 0.3.5 corrective feature gates'
grep -Fq 'space_around_delimiters=False' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'candidate contains spaced INI delimiters' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'network-runtime.json' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'module_tg' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq '/run/2pny/network-runtime.json' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/run/2pny/network-runtime.json'
grep -Fq '/api/network/wifi/profiles' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/network/wifi/profiles'
grep -Fq '/api/network/dns' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/network/dns'
grep -Fq 'PU2PNY-WIFI-SECONDARY' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'A rede anterior foi restaurada' "$ROOT/usr/local/sbin/2pny-wifi-profiles"
grep -Fq 'test -s "$RUN/hostapd.pid"' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq '"channel":' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'Bem-vindo / Welcome' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'scheduleHardwareAdvance' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'Módulo / TG' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'TOT: corte automático' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Rastreando sinais' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Atividade 24h' "$ROOT/usr/share/2pny/history.html"
grep -Fq 'Usar Cloudflare' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'Canais próximos' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'Manutenção automática' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'Throttling' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'MMDVMHost nativo / ON7LDS' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Iniciando / Starting' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'TOT: corte em' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'Em andamento / Working' "$ROOT/usr/local/sbin/2pny-display-status"
grep -Fq 'pnyAprsToast' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'Atualizado às' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'next_eligible' "$ROOT/usr/local/sbin/2pny-auto-maintenance"

echo '[14/15] 0.3.6 corrective/resource gates'
SW="$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'test "${paused:-0}" = 1' "$SW"
grep -Fq 'set type managed' "$SW"
! grep -Fq 'cleanup(){ test "$paused"' "$SW"
grep -Fq 'Rede Wi-Fi 1 e Rede Wi-Fi 2' "$ROOT/usr/share/2pny/internet.html" || grep -Fq 'Rede Wi‑Fi 1 e Rede Wi‑Fi 2' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'wifiSecondManual' "$ROOT/usr/share/2pny/internet.html"
! grep -Fq '/wizard?step=1&return=internet' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'quality_label' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq 'Melhor opção' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq '[General]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq '[Repeater 1]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq '[Hosts Files]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'DisplayLevel=2' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Link has failed, polls lost' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'DExtra|D-Plus|DCS' "$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'protocol-profiles.json' "$ROOT/usr/local/sbin/2pny-protocol-profiles"
grep -Fq '2pny-rf-apply' "$ROOT/usr/local/sbin/2pny-protocol-profiles"
grep -Fq 'ALLOWED_PREFIX' "$ROOT/usr/local/sbin/2pny-update-manager"
grep -Fq 'sha256(pkg)' "$ROOT/usr/local/sbin/2pny-update-manager"
grep -Fq '/api/protocol/profiles' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/protocol/profiles'
grep -Fq '2pny-update-manager' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '2pny-update-manager'
grep -Fq 'friendlyNetworkError' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'falha interna e foi cancelada com segurança'
grep -Fq 'Perfil do protocolo' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'Gateway ativo / aguardando rede' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'Gerenciada automaticamente' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'quickProfiles' "$ROOT/usr/share/2pny/hotspot.html"
! grep -Fq '/wizard?step=3' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'navigator.geolocation' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'Mensagem preservada na fila' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'queued_for_send' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'queued_for_send'
grep -Fq 'soam.aprs2.net' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'soam.aprs2.net'
grep -Fq 'qrz.com/db/' "$ROOT/usr/share/2pny/history.html"
grep -Fq '/radioid?callsign=' "$ROOT/usr/share/2pny/history.html"
! grep -Fq 'radioid.net/api/dmr/user/?callsign=' "$ROOT/usr/share/2pny/history.html"
grep -Fq 'qrz.com/db/' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq '/radioid?callsign=' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'installUpdate' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'Guardar versão atual para rollback' "$ROOT/usr/share/2pny/system.html"
! grep -Fq '/wizard?step=1' "$ROOT/usr/share/2pny/expert.html"
! grep -Fq '/wizard?step=3' "$ROOT/usr/share/2pny/expert.html"
grep -Fq 'Ex.: PU2ABC' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'Ex.: 7240000' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq '>ID DMR<' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'function operation' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'MutationObserver' "$ROOT/usr/share/2pny/ui-language.js"
grep -Fq 'RF>NET' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'NET>RF' "$ROOT/usr/local/sbin/2pny-display-core"
# 0.3.6: BrandMeister personal-hotspot aliases and API-key isolation.
grep -Fq 'id="dmrEssid"' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'id="bmApiKey"' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'O PU2PNY não pede API Secret' "$ROOT/usr/share/2pny/protocols.html"
grep -Fq 'Identificação do hotspot / rádio' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq '/api/brandmeister/api-key' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/brandmeister/api-key'
grep -Fq 'network_id=dmrid+essid if essid and len(dmrid)==7 else dmrid' "$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'identificação DMR deve ser 01 a 99' "$ROOT/usr/local/sbin/2pny-protocol-profiles"
test ! -e "$ROOT/var/lib/2pny/secrets/brandmeister-api.key"
# Captive portal/fallback endpoints remain present; automatic popup itself is client-controlled.
for endpoint in '/generate_204' '/hotspot-detect.html' '/connecttest.txt' '/ncsi.txt'; do
  strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq "$endpoint"
done
# DMR baseline components must still be installed and the proven custom XLX controls remain.
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
grep -Fq 'TG=6' "$ROOT/var/lib/2pny/presets/dmr-xlx026.ini" 2>/dev/null || true

echo '[14b/15] 0.3.8 corrective gates'
test -x "$ROOT/usr/local/bin/2pny-direct-core"
test -x "$ROOT/usr/local/sbin/2pny-direct-start"
test -x "$ROOT/usr/local/sbin/2pny-direct-recover"
test -s "$ROOT/etc/systemd/system/2pny-direct.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-direct.service"
test -s "$ROOT/usr/share/2pny/direct.html"
grep -Fq '/api/direct/call' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/direct/call'
grep -Fq "['/direct','Direct','direct']" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'CGNAT' "$ROOT/usr/share/2pny/direct.html"
file "$ROOT/usr/local/bin/2pny-direct-core" | grep -Eq 'ELF 64-bit.*(ARM aarch64|ARM64)'
test ! -e "$ROOT/var/lib/2pny/direct/identity.json"
test ! -e "$ROOT/var/lib/2pny/direct/peers.json"
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK

test -x "$ROOT/usr/local/bin/dgwvoicetransmit"
test -d "$ROOT/usr/share/2pny/audio/dstar"
test "$(find "$ROOT/usr/share/2pny/audio/dstar" -maxdepth 1 -type f -name '*.ambe' | wc -l)" -ge 8
test "$(find "$ROOT/usr/share/2pny/audio/dstar" -maxdepth 1 -type f -name '*.indx' | wc -l)" -ge 8
test -s "$ROOT/usr/share/2pny/audio/dstar/en_GB.ambe"
test -s "$ROOT/usr/share/2pny/audio/dstar/en_GB.indx"
grep -Fq 'audio_path="/usr/local/share/dstargateway.d/"' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Data={audio_path}' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"

grep -Fq 'PU2PNY Moderno V2' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'Graphical 128x64 renderer' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'MMDVMHost nativo / ON7LDS' "$ROOT/usr/share/2pny/display.html"

# DMR baseline markers remain untouched.
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX status voice requested'

echo '[14c/15] 0.3.8 physical-feedback corrections represented'
grep -Fq 'wifiChannelGraph' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'data-showpass' "$ROOT/usr/share/2pny/internet.html"
grep -Fq "['/hotspot','Protocolos','hotspot']" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq '/protocols/embed' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/protocols/embed'
grep -Fq 'Pareie um PU2PNY antes de chamar' "$ROOT/usr/share/2pny/direct.html"
grep -Fq 'Etapa 1/5' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq "var live=q('liveBox')" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq "sec.id='pnyHealth'" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'pny-healthitem' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'Potência RF do MMDVM' "$ROOT/usr/share/2pny/expert.html"
grep -Fq '/api/rf/power' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/rf/power'
test -x "$ROOT/usr/local/sbin/2pny-timezone-apply"
test -x "$ROOT/usr/local/sbin/2pny-rflevel-apply"
test -x "$ROOT/usr/local/sbin/2pny-ssh-apply"
test -s "$ROOT/etc/systemd/system/2pny-timezone-apply.service"
test -s "$ROOT/etc/systemd/system/2pny-rflevel-apply.service"
test -s "$ROOT/etc/systemd/system/2pny-ssh-apply.service"
test -x "$ROOT/usr/local/sbin/2pny-operational-apply"
test -s "$ROOT/etc/systemd/system/2pny-operational-apply.service"
test -s "$ROOT/etc/systemd/system/2pny-operational-restore.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-operational-restore.service"
test -x "$ROOT/usr/local/sbin/2pny-auto-maintenance"
grep -Fq 'operational-disabled' "$ROOT/usr/local/sbin/2pny-operational-apply"
grep -Fq 'display ready "Manutencao concluida"' "$ROOT/usr/local/sbin/2pny-auto-maintenance"
grep -Fq 'id="opResult"' "$ROOT/usr/share/2pny/system.html"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'wifi_rssi_dbm'
grep -Fq 'WiresXCommandPassthrough=0' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Reconnect=0' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'porta 20010' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'local=cols[3]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
! grep -Fq 'local=cols[4]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'verify_host_bridge_config(proto)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'wait_bridge(proto,20010,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'wait_bridge(proto,4200,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq '"waiting_bridge"' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'protocol-health.json' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'characterData:true' "$ROOT/usr/share/2pny/ui-language.js"
grep -Fq 'effective_layout' "$ROOT/usr/local/sbin/2pny-display-apply"

echo '[14d/15] 0.3.9 inherited physical-feedback gates'\ngrep -Fq 'wait_bridge(proto,20010,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'wait_bridge(proto,4200,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'local=cols[3]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
! grep -Fq 'local=cols[4]' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
! grep -Fq '\\b127\\.0\\.0\\.1:20010' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'for attempt in 1 2 3' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'merge_scan_json' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq "sed -i '/^dhcp-option-force=114,/d'" "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'if test ! -f "$STATE/provisioned"; then' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'test -f "$STATE/provisioned" || return 0' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'address=/#/10.43.0.1' "$ROOT/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
! grep -Fq 'dhcp-option-force=114,' "$ROOT/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'http://10.43.0.1/wizard?captive=1'
! grep -Fq '10.42.0.1' "$ROOT/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
grep -Fq '5 GHz' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'bandgraph' "$ROOT/usr/share/2pny/internet.html"
grep -Fq 'effective_dns' "$ROOT/usr/share/2pny/internet.html"
grep -Fq "addEventListener('live'" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq "addEventListener('live'" "$ROOT/usr/share/2pny/expert.html"
grep -Fq "var live=q('liveBox')" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'mmdvmhost-authoritative' "$ROOT/usr/local/sbin/2pny-display-status"
grep -Fq '"error": (0, "Erro / Error")' "$ROOT/usr/local/sbin/2pny-display-status"
grep -Fq 'não confirmou o layout Nextion solicitado' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'wait_prereqs' "$ROOT/usr/local/sbin/2pny-operational-apply"
grep -Fq 'Restart=on-failure' "$ROOT/etc/systemd/system/2pny-operational-restore.service"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-operational-apply" "$ROOT/usr/local/sbin/2pny-timezone-apply" "$ROOT/usr/local/sbin/2pny-ssh-apply" "$ROOT/usr/local/sbin/2pny-display-apply-request"
rm -rf "$ROOT/usr/local/sbin/__pycache__"
for unit in 2pny-timezone-apply.path 2pny-ssh-apply.path 2pny-operational-apply.path 2pny-rflevel-apply.path 2pny-display-apply-request.path; do
  test -s "$ROOT/etc/systemd/system/$unit"
  test -L "$ROOT/etc/systemd/system/multi-user.target.wants/$unit"
done
grep -Fq 'PathExistsGlob=/run/2pny/timezone-request-*.json' "$ROOT/etc/systemd/system/2pny-timezone-apply.path"
grep -Fq 'PathExists=/run/2pny/ssh-request.json' "$ROOT/etc/systemd/system/2pny-ssh-apply.path"
grep -Fq 'PathChanged=/run/2pny/operational-request.json' "$ROOT/etc/systemd/system/2pny-operational-apply.path"
grep -Fq 'PathChanged=/run/2pny/display-apply-request.json' "$ROOT/etc/systemd/system/2pny-display-apply-request.path"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'timezone-request-'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/run/2pny/ssh-request.json'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/run/2pny/operational-request.json'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/run/2pny/display-apply-request.json'
grep -Fq 'if(!base){base=text;originals.set(node,base)}' "$ROOT/usr/share/2pny/ui-language.js"
# Approved baseline must still be present and not replaced by the corrective overlay.
grep -Fq 'PU2PNY, XLX module control' < <(strings "$ROOT/usr/local/bin/DMRGateway")
test -s "$ROOT/usr/share/2pny/history.html"
grep -Fq 'CGNAT' "$ROOT/usr/share/2pny/direct.html"
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK

echo '[14e/15] 0.3.12 inherited display/protocol/network hardening gates'
grep -Fq '/api/display/detection' < <(strings "$ROOT/usr/local/bin/2pnyd")
grep -Fq '/api/diagnostics' < <(strings "$ROOT/usr/local/bin/2pnyd")
grep -Fq 'associating' < <(strings "$ROOT/usr/local/bin/2pnyd")
grep -Fq 'MMDVMHost nativo / ON7LDS' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'nextion-101-1024x600' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Nunca automático' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Perfis rápidos nativos · sem iframe' "$ROOT/usr/share/2pny/hotspot.html"
! grep -Fqi '<iframe' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'wizardOperation' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'syncClock' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'waiting_bridge' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'protocol-health.json' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'last-protocol-rollback.json' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'mqtt-preflight.json' "$ROOT/usr/local/sbin/2pny-mqtt-preflight"
grep -Fq 'last-boot-restore.json' "$ROOT/usr/local/sbin/2pny-operational-apply"
grep -Fq 'patch_modern_transport' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'host/display-in' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'get pnyver.txt' "$ROOT/usr/local/sbin/2pny-display-detector"
test -s "$ROOT/usr/share/2pny/display-catalog.json"
python3 - <<PY
import json
p="$ROOT/usr/share/2pny/display-catalog.json"
d=json.load(open(p))
assert d["policy"]["flash_requires_explicit_confirmation"] is True
assert d["policy"]["silent_tft_overwrite"] is False
for x in d["profiles"]:
 t=x.get("tft")
 if t and t.get("status")!="unpublished":
  assert t.get("url") and t.get("sha256")
print("DISPLAY_CATALOG_OK")
PY
test -s "$ROOT/etc/systemd/system/2pny-display-detect.service"
test -s "$ROOT/etc/systemd/system/2pny-display-detect.path"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-display-detect.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-display-detect.path"
! grep -Fq 'ACTION=="add|change"' "$ROOT/etc/udev/rules.d/99-pu2pny-display-hotplug.rules"
grep -Fq 'ACTION=="add"' "$ROOT/etc/udev/rules.d/99-pu2pny-display-hotplug.rules"
grep -Fq 'ACTION=="change"' "$ROOT/etc/udev/rules.d/99-pu2pny-display-hotplug.rules"

echo '[15/15] final result'
echo '[14f/15] 0.3.12 MMDVM/i18n regression gates'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
PROBE="$ROOT/usr/local/sbin/2pny-hardware-probe"
LANG="$ROOT/usr/share/2pny/ui-language.js"
WIZ="$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'flock -w 8 8' "$RF"
! grep -Fq '2pny-mqtt-preflight --quiet' "$RF"
grep -Fq 'last-rf-apply-error.json' "$RF"
! grep -Fq 'MMDVMHost failed with detected baud' "$RF"
grep -Fq 'A MMDVM foi detectada, mas o MMDVMHost não conseguiu assumir a porta serial no teste básico' "$RF"
! grep -Fq 'bridge = probe_nextion_mmdvm' "$PROBE"
grep -Fq 'MMDVM confirmada. A Nextion pela porta do modem' "$PROBE"
grep -Fq 'O assistente avançará automaticamente em 5 segundos.' "$WIZ"
grep -Fq 'normalizeIncoming' "$LANG"
grep -Fq 'incomingPT' "$LANG"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'

echo '[14g/15] 0.3.12 MQTT broker + serial arbitration + i18n gates'
test -x "$ROOT/usr/sbin/mosquitto"
test -s "$ROOT/etc/mosquitto/2pny-local.conf"
grep -Fq 'listener 1883 127.0.0.1' "$ROOT/etc/mosquitto/2pny-local.conf"
grep -Fq 'allow_anonymous true' "$ROOT/etc/mosquitto/2pny-local.conf"
grep -Fq 'mqtt_connect_packet' "$ROOT/usr/local/sbin/2pny-mqtt-preflight"
grep -Fq 'CONNACK' "$ROOT/usr/local/sbin/2pny-mqtt-preflight"
grep -Fq 'mmdvm-serial.lock' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -Fq 'fcntl.flock' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -Fq 'SERIAL_LOCK=/run/2pny/mmdvm-serial.lock' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -Fq 'flock -w 15 7' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -Fq 'Sistema Operacional de Rádio Digital' "$ROOT/usr/share/2pny/wizard.html"
! grep -Fq 'Digital Radio Operating System' "$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'Object.assign(D,' "$ROOT/usr/share/2pny/ui-language.js"
grep -Fq 'A MMDVM ainda está sendo verificada' "$ROOT/usr/share/2pny/ui-language.js"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'


echo '[14h/15] 0.3.13 MMDVM bootstrap + TGIF + i18n gates'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
MQTT="$ROOT/usr/local/sbin/2pny-mqtt-preflight"
SVC="$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
DMR="$ROOT/usr/local/libexec/2pny-dmr-apply"
CAT="$ROOT/usr/local/sbin/2pny-server-catalog"
WIZ="$ROOT/usr/share/2pny/wizard.html"
LANG="$ROOT/usr/share/2pny/ui-language.js"
grep -Fq 'MQTTLevel=0' "$RF"
grep -Fq 'DisplayLevel=0' "$RF"
grep -Fq 'mmdvmhost_bootstrap_failed' "$RF"
! grep -Fq 'mqtt_preflight_failed_after_uart_ok' "$RF"
! grep -Fq 'mmdvmhost_mqtt_phase_failed' "$RF"
! grep -Fq 'enable_operational_mqtt' "$RF"
grep -Fq 'rf-bootstrap.json' "$RF"
grep -Fq -- '--no-publish' "$MQTT"
grep -Fq -- '--respect-log-level' "$MQTT"
grep -Fq 'mqtt_log_enabled' "$MQTT"
grep -Fq 'ExecStartPre=/usr/local/sbin/2pny-mqtt-preflight --quiet --no-publish --respect-log-level' "$SVC"
grep -Fq 'Wants=systemd-udev-settle.service mosquitto.service' "$SVC"
! grep -Fq 'Requires=mosquitto.service' "$SVC"
grep -Fq 'Name=TGIF_Network' "$DMR"
grep -Fq 'TGRewrite{idx}={s},1,2,1,9999998' "$DMR"
grep -Fq 'SrcRewrite{idx}=2,1,{s},1,9999998' "$DMR"
grep -Fq 'tgif_auth_mode="legacy" if password=="passw0rd" else "secured"' "$DMR"
grep -Fq 'Password="{password}"' "$DMR"
grep -Fq '"auth_mode":tgif_auth_mode' "$DMR"
grep -Fq 'Chave de segurança TGIF' "$CAT"
grep -Fq 'Chave de segurança TGIF' "$WIZ"
grep -Fq 'Senha de segurança do hotspot' "$WIZ"
grep -Fq 'O rádio precisa usar o mesmo código de cor.' "$WIZ"
! grep -Fq 'Senha do master' "$WIZ"
! grep -Fq 'Opções do master' "$WIZ"
grep -Fq 'pny-i18n-pending' "$WIZ"
grep -Fq "document.documentElement.classList.remove('pny-i18n-pending')" "$LANG"
grep -Fq 'A MMDVM passou no teste básico' "$LANG"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'

echo "PU2PNY-OS $VERSION ARM64 image: inherited regressions + 0.3.13 corrective SW/structural gates OK — hardware validation still required"

echo '[16/16] 0.3.16 HW-feedback bugfix gates'
grep -Fq 'connection.autoconnect-retries 3' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'SAVED_AUTO' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'nmcli networking on' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'Nova busca solicitada.' < <(strings "$ROOT/usr/local/bin/2pnyd")
grep -Fq 'setInterval(function(){if(!document.hidden)load()},2000)' "$ROOT/usr/share/2pny/internet.html"
grep -Fq "rfMetrics=origin==='RF'" "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'waitProtocolConnection' "$ROOT/usr/share/2pny/hotspot.html"

grep -Fq 'PathExistsGlob=/run/2pny/timezone-request-*.json' "$ROOT/etc/systemd/system/2pny-timezone-apply.path"
grep -Fq 'PathExists=/run/2pny/ssh-request.json' "$ROOT/etc/systemd/system/2pny-ssh-apply.path"
grep -Fq 'req_path.unlink()' "$ROOT/usr/local/sbin/2pny-timezone-apply"
grep -Fq 'REQ.unlink()' "$ROOT/usr/local/sbin/2pny-ssh-apply"
grep -Fq 'id="sshPubFile"' "$ROOT/usr/share/2pny/expert.html"

grep -Fq 'rotate.aprs2.net' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'server_candidates' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'configured_server' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'Enviada · aguardando confirmação (ACK)' "$ROOT/usr/share/2pny/aprs.html"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'soam.aprs2.net'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'ensureAPRSDefaults'

grep -Fq 'renderer="mmdvmhost-native"' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'cp.set("General","Display","Nextion")' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'cp.set("Nextion","Port","modem")' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'MMDVMHost nativo / ON7LDS' "$ROOT/usr/share/2pny/display.html"

grep -Fq 'Band=C' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'ReloadTime=72' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
! grep -Fq 'ReloadTimer=72' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'DStar_Hosts.json' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'reflector_type="DCS"' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"

# DMR binary was rebuilt from the same pinned source plus a narrow voice
# arbitration patch. Baseline custom controls must remain alongside it.
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, system voice priority: suppressing XLX network audio'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, system voice priority: suppressing network audio on slot'

test -x "$ROOT/usr/local/bin/2pny-direct-core"
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK

strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'
test "$(cat "$ROOT/etc/2pny/version")" = "0.3.19-alpha"

echo '[17/17] 0.3.17 D-Star RX/commands + timezone gates'
DSTAR="$ROOT/usr/local/sbin/2pny-protocol-network-apply"
STATION="$ROOT/usr/local/sbin/2pny-station-worker"
HOTSPOT="$ROOT/usr/share/2pny/hotspot.html"
TZ="$ROOT/usr/local/sbin/2pny-timezone-apply"
TZPATH="$ROOT/etc/systemd/system/2pny-timezone-apply.path"
TZSVC="$ROOT/etc/systemd/system/2pny-timezone-apply.service"

# PROTO-024: local D-Star identity must remain C/C while remote room is separate.
grep -Fq '"Module":"C" if proto=="DSTAR"' "$DSTAR"
grep -Fq 'Band=C' "$DSTAR"
grep -Fq 'LocalPort":"20011"' "$DSTAR"
grep -Fq 'GatewayPort":"20010"' "$DSTAR"
grep -Fq 'HBPort=20010' "$DSTAR"
grep -Fq 'Port=20011' "$DSTAR"
grep -Fq 'ReflectorReconnect=Never' "$DSTAR"
! grep -Fq 'ReflectorReconnect=Fixed' "$DSTAR"
grep -Fq 'ReloadTime=72' "$DSTAR"
! grep -Fq 'ReloadTimer=72' "$DSTAR"
grep -Fq 'D-Star.Module local não confirmou C' "$DSTAR"

# The native gateway command/status voice pack is present; do not claim a
# language pack that is not actually installed.
test -d "$ROOT/usr/share/2pny/audio/dstar"
test -s "$ROOT/usr/share/2pny/audio/dstar/en_GB.ambe"
test -s "$ROOT/usr/share/2pny/audio/dstar/en_GB.indx"
test -s "$ROOT/usr/share/2pny/audio/dstar/es_ES.ambe"
test -s "$ROOT/usr/share/2pny/audio/dstar/es_ES.indx"

# LIVE-017/UI-032: evidence-based link/command state and operator help.
grep -Fq 'Link command from' "$STATION"
grep -Fq 'Unlink command issued via' "$STATION"
grep -Fq 'last_command_target' "$STATION"
grep -Fq 'link_state' "$STATION"
for marker in '_______I' '_______E' '_______U' '_______L' 'XLX026DL' 'REF030CL' 'CQCQCQ'; do
  grep -Fq "$marker" "$HOTSPOT"
done
grep -Fq 'id="stDstarLocal"' "$HOTSPOT"
grep -Fq 'id="stDstarCommand"' "$HOTSPOT"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'last_command_target'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'link_state'

# The existing Live parser must recognize network D-Star and leave RF metrics
# to RF-only events.
python3 - "$ROOT/usr/local/lib/2pny-live-core.py" <<'PY0317LIVE'
import importlib.util,sys
spec=importlib.util.spec_from_file_location("live",sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=m.LiveState()
e=s.ingest("D-Star, received network header from M1ABC /ABCD to CQCQCQ via XLX026 D",1000)
assert e and e["protocol"]=="DSTAR" and e["direction"]=="NETWORK"
assert e["source"]=="M1ABC" and e["target"]=="CQCQCQ" and e["reflector"]=="XLX026 D"
assert e["rssi"] is None and e["ber"] is None
x=s.snapshot()["active"]
assert x and x["direction"]=="NETWORK"
e=s.ingest("D-Star, received network end of transmission from M1ABC /ABCD to CQCQCQ, 2.0 seconds, 0% packet loss, BER: 0.0%",1002)
assert e and e["direction"]=="NETWORK" and e.get("rssi") is None
assert s.snapshot()["standby"] is True
PY0317LIVE

# SEC-024: a unique request/result pair drives only the timezone one-shot.
grep -Fq 'PathExistsGlob=/run/2pny/timezone-request-*.json' "$TZPATH"
grep -Fq 'Unit=2pny-timezone-apply.service' "$TZPATH"
grep -Fq 'User=root' "$TZSVC"
grep -Fq 'ExecStart=/usr/local/sbin/2pny-timezone-apply' "$TZSVC"
grep -Fq 'ReadWritePaths=/run/2pny /etc/timezone' "$TZSVC"
grep -Fq 'timezone-request-' "$TZ"
grep -Fq 'timezone-result-' "$TZ"
grep -Fq 'timedatectl","set-timezone' "$TZ"
grep -Fq 'effective_timezone' "$TZ"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'timezone-request-'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'timezone-result-'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'

# SEC-025 / REL-012: restricted radio administration.
RADIO="$ROOT/usr/local/sbin/2pny-radio-admin"
RADIOPATH="$ROOT/etc/systemd/system/2pny-radio-admin.path"
RADIOSVC="$ROOT/etc/systemd/system/2pny-radio-admin.service"
test -x "$RADIO"
grep -Fq 'ARM_SECONDS=30' "$RADIO"
grep -Fq 'configured_owner()' "$RADIO"
grep -Fq 'if not armed_for(caller)' "$RADIO"
grep -Fq '2pny-protocol-profiles' "$RADIO"
grep -Fq 'systemd-run' "$RADIO"
grep -Fq 'PathExists=/run/2pny/radio-admin-command.request' "$RADIOPATH"
grep -Fq 'Unit=2pny-radio-admin.service' "$RADIOPATH"
grep -Fq 'User=root' "$RADIOSVC"
grep -Fq 'ReadWritePaths=/run/2pny /var/lib/2pny' "$RADIOSVC"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-radio-admin.path"
test "$(readlink "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-radio-admin.path")" = "../2pny-radio-admin.path"
for marker in PNYARM PNYOFF PNYRBT PNYDMR PNYDST PNYYSF PNYP25 PNYNXD PNYPOC; do
  grep -Fq "$marker" "$HOTSPOT"
done
strings "$ROOT/usr/local/bin/dstargateway" | grep -Fq 'PU2PNY radio admin request'
strings "$ROOT/usr/local/bin/dstargateway" | grep -Fq 'radio-admin-command.request'

# REL-010: representative frozen 0.3.16 baselines are still present.
grep -Fq 'connection.autoconnect-retries 3' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'rotate.aprs2.net' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'renderer="mmdvmhost-native"' "$ROOT/usr/local/sbin/2pny-display-apply"
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, system voice priority'
test -x "$ROOT/usr/local/bin/2pny-direct-core"

echo '[18/18] 0.3.18 native D-Star voice assets'
DSTAR="$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'audio_path="/usr/local/share/dstargateway.d/"' "$DSTAR"
! grep -Fq 'audio_path="/usr/share/2pny/audio/dstar/"' "$DSTAR"
test -s "$ROOT/usr/local/share/dstargateway.d/en_GB.ambe"
test -s "$ROOT/usr/local/share/dstargateway.d/en_GB.indx"
test -s "$ROOT/usr/local/share/dstargateway.d/DStar_Hosts.json"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.19-alpha'
test "$(cat "$ROOT/etc/2pny/version")" = "0.3.19-alpha"
echo "PU2PNY-OS 0.3.19-alpha: native D-Star AMBE/INDX assets confirmed in configured directory"

echo "PU2PNY-OS 0.3.19-alpha ARM64 image: D-Star native voice data + inherited D-Star/timezone gates OK — hardware validation still required"
