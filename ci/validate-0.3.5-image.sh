#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then exec sudo bash "$0" "$@"; fi
IMAGE="${1:?image required}"
VERSION="${2:-0.3.5-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate.img"
ROOT="/mnt/pu2pny-os-035"
LOOP=""; PID=""
cleanup(){
  set +e
  test -n "$PID" && kill "$PID" 2>/dev/null || true
  umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$RAW" /tmp/pu2pnyd-035.log
}
trap cleanup EXIT
trap 'echo "Validation failed at line $LINENO: $BASH_COMMAND" >&2' ERR

echo '[1/14] image integrity'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"; ACTUAL="$(sha256sum "$IMAGE"|awk '{print $1}')"
test "$EXPECTED" = "$ACTUAL"
xz -dc "$IMAGE" >"$RAW"
LOOP="$(losetup --find --partscan --show "$RAW")"
for _ in {1..60}; do test -b "${LOOP}p2" && break; sleep .25; done
mkdir -p "$ROOT"; mount "${LOOP}p2" "$ROOT"; mkdir -p "$ROOT/boot/firmware"; mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[2/14] identity'
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

echo '[3/14] runtime syntax'
for x in 2pny-network-core 2pny-network-switch 2pny-wifi-profiles 2pny-auto-maintenance 2pny-hostfiles-update 2pny-rf-apply 2pny-mode-apply 2pny-mdns-guard; do
  test -x "$ROOT/usr/local/sbin/$x"; bash -n "$ROOT/usr/local/sbin/$x"
done
test -x "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns"
bash -n "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns"
for x in 2pny-station-worker 2pny-hardware-probe 2pny-display-core 2pny-display-status 2pny-display-apply 2pny-server-catalog 2pny-protocol-network-apply 2pny-mqtt-preflight 2pny-aprs 2pny-netdiag 2pny-nextion-autodetect; do
  test -x "$ROOT/usr/local/sbin/$x"; python3 -m py_compile "$ROOT/usr/local/sbin/$x"
done
python3 -m py_compile "$ROOT/usr/local/lib/2pny-live-core.py" "$ROOT/usr/local/libexec/2pny-dmr-apply"
rm -rf "$ROOT/usr/local/sbin/__pycache__" "$ROOT/usr/local/lib/__pycache__" "$ROOT/usr/local/libexec/__pycache__"

echo '[4/14] 0.2.9 feature parity preserved'
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

echo '[5/14] Wi-Fi handoff and mDNS'
SW="$ROOT/usr/local/sbin/2pny-network-switch"; WIZ="$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'create_candidate' "$SW"
grep -Fq 'stage_wifi' "$SW"
grep -Fq 'wifi-pending' "$SW"
grep -Fq 'try_profile' "$SW"
grep -Fq 'restore_on_error' "$SW"
grep -Fq 'wpa-psk' "$SW"; grep -Fq 'sae' "$SW"
grep -Fq 'connection.autoconnect-retries 0' "$SW"
grep -Fq 'Aguardando o PU2PNY reaparecer automaticamente' "$WIZ"
grep -Fq 'O perfil será salvo antes do reinício' "$WIZ"
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

echo '[6/14] Nextion / Display Core'
grep -Fq 'nextion_mmdvm' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'SSD1306' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'class LCD' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'b"connect\xff\xff\xff"' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -Fq 'PU2PNY Display Core is authoritative' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'input=b"connect\xff\xff\xff"' "$ROOT/usr/local/sbin/2pny-nextion-autodetect"
grep -Fq 'disable","--now",LEGACY' "$ROOT/usr/local/sbin/2pny-display-apply"

echo '[7/14] live-state regression fixed'
grep -Fq 'source-less END' "$ROOT/usr/local/lib/2pny-live-core.py"
grep -Fq 'action in ("end","lost","timeout")' "$ROOT/usr/local/lib/2pny-live-core.py"
grep -Fq 'currentActive' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Rastreando sinais' "$ROOT/usr/share/2pny/dashboard.html"
! grep -Fq 'Operador não identificado' "$ROOT/usr/share/2pny/dashboard.html"

echo '[8/14] preloaded protocol catalogs'
HOSTS="$ROOT/var/lib/2pny/hosts"
for x in DStar_Hosts.json DPlus_Hosts.txt DExtra_Hosts.txt DCS_Hosts.txt XLXHosts.txt YSFHosts.txt YSFHosts.json FCSRooms.txt P25Hosts.txt NXDNHosts.txt; do
  test -s "$HOSTS/$x"
done
test "$(wc -c <"$HOSTS/DStar_Hosts.json")" -gt 1000
test "$(wc -c <"$HOSTS/YSFHosts.txt")" -gt 100

echo '[9/14] protocol UI and gateways'
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

echo '[10/14] RadioID, flags and activity'
test -f "$ROOT/usr/share/2pny/flags/LICENSE-MIT"
COUNT="$(find "$ROOT/usr/share/2pny/flags/4x3" -maxdepth 1 -type f -name '*.svg' | wc -l)"
test "$COUNT" -ge 240
for cc in br us pt gb ar jp au za; do test -s "$ROOT/usr/share/2pny/flags/4x3/$cc.svg"; done
grep -Fq 'renderActivity' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'id="activityGroups"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'class="btn plus"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'history-summary.json' "$ROOT/usr/local/sbin/2pny-station-worker"

echo '[11/14] dedicated pages and APRS'
for page in internet hotspot protocols history aprs display system expert; do test -s "$ROOT/usr/share/2pny/$page.html"; done
grep -Fq 'traceroute' "$ROOT/usr/local/sbin/2pny-netdiag"
grep -Fq 'APRS-IS' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'brazil.aprs2.net' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'Google Time' "$ROOT/usr/share/2pny/system.html"

echo '[12/14] no leaked user/runtime state'
for p in \
 "$ROOT/var/lib/2pny/provisioned" "$ROOT/var/lib/2pny/rf-configured" \
 "$ROOT/var/lib/2pny/network-radio.json" "$ROOT/var/lib/2pny/network-connect.json" \
 "$ROOT/var/lib/2pny/wifi-country" "$ROOT/var/lib/2pny/display-runtime.json" \
 "$ROOT/var/lib/2pny/station/operators.sqlite"; do test ! -e "$p"; done

echo '[13/14] backend boot and APIs'
mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
mount -t proc proc "$ROOT/proc"; mount --bind /dev "$ROOT/dev"; mount --bind /sys "$ROOT/sys"
chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-035.log 2>&1 & PID=$!
OK=0
for _ in {1..100}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-035.log; exit 1; }
curl -fsS http://127.0.0.1/api/status | grep -Fq '"version":"0.3.5-alpha"'
# Fresh images are intentionally unprovisioned, so /dashboard must redirect
# to the wizard until onboarding is complete.
CODE="$(curl -sS -o /tmp/pu2pny-dashboard-unprovisioned -w '%{http_code}' http://127.0.0.1/dashboard)"
test "$CODE" = "302"
# Then simulate completed onboarding only for route validation.
touch "$ROOT/var/lib/2pny/provisioned"
curl -fsS http://127.0.0.1/dashboard | grep -Fq 'id="liveBox"'
curl -fsS http://127.0.0.1/hotspot | grep -Fq '<h1>Hotspot</h1>'
curl -fsS http://127.0.0.1/display | grep -Fq '<h1>Display</h1>'
rm -f "$ROOT/var/lib/2pny/provisioned" /tmp/pu2pny-dashboard-unprovisioned
curl -fsS http://127.0.0.1/ui-common-0.3.0.js | grep -Fq "['/hotspot','Hotspot','hotspot']"
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq 'will_reboot'
curl -fsS http://127.0.0.1/api/network/country | grep -Fq '"country":"BR"'
curl -fsS http://127.0.0.1/flags/4x3/br.svg | grep -Eq '<svg|<SVG'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/protocol/apply'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/aprs/message'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '2pny-nextion-autodetect'
kill "$PID"; PID=""

echo '[13b/14] 0.3.3 regressions preserved + 0.3.4 corrections'
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
grep -Fq 'Requires=mosquitto.service' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
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

echo '[13c/14] 0.3.5 corrective feature gates'
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
grep -Fq 'PU2PNY Moderno' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Iniciando / Starting' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'TOT: corte em' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'Em andamento / Working' "$ROOT/usr/local/sbin/2pny-display-status"
grep -Fq 'pnyAprsToast' "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'Atualizado às' "$ROOT/usr/share/2pny/aprs.html"
grep -Fq 'next_eligible' "$ROOT/usr/local/sbin/2pny-auto-maintenance"

echo '[14/14] final result'
echo "PU2PNY-OS $VERSION ARM64 image: SW/structural OK — hardware validation still required"