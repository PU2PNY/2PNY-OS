#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re

root = Path('.')

# Patch release: captive/open setup AP, deterministic panel listener and responsive UI.
for rel in ['builder/build-image.sh', 'rootfs-overlay/usr/local/sbin/2pny-firstboot', 'src/2pnyd/main.go']:
    p = root / rel
    s = p.read_text()
    s = s.replace('0.1.7-hotfix1', '0.1.7-hotfix2').replace('Alpha 0.1.7 hotfix1', 'Alpha 0.1.7 hotfix2')
    p.write_text(s)
(root / 'rootfs-overlay/etc/2pny/version').write_text('0.1.7-hotfix2\n')

# Setup AP is intentionally open. It is only a provisioning transport and is
# automatically replaced by the configured network after provisioning.
ap = root / 'rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection'
s = ap.read_text()
s = re.sub(r'\n\[wifi-security\]\n.*?(?=\n\[ipv4\])', '\n', s, flags=re.S)
s = s.replace('autoconnect=false\nmdns=2', 'autoconnect=false\nautoconnect-priority=100\nmdns=2', 1)
ap.write_text(s)

# NetworkManager shared-mode dnsmasq: hijack DNS only while a shared setup
# transport is active. This lets Windows/Android/iOS captive checks reach 2PNY.
dnsdir = root / 'rootfs-overlay/etc/NetworkManager/dnsmasq-shared.d'
dnsdir.mkdir(parents=True, exist_ok=True)
(dnsdir / '2pny-captive.conf').write_text('''# 2PNY captive setup only\naddress=/#/10.42.0.1\naddress=/2pny.local/10.42.0.1\nlocal=/2pny.local/\n''')

# Small privileged helper used by the local panel API.
apctl = root / 'rootfs-overlay/usr/local/sbin/2pny-ap-control'
apctl.write_text(r'''#!/bin/bash
set -euo pipefail
ACTION="${1:-status}"
PROFILE=2PNY-SETUP
wifi_if(){ nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}'; }
active(){ nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq "$1"; }
ensure_profile(){
  if ! nmcli -t -f NAME connection show 2>/dev/null | grep -Fxq "$PROFILE"; then
    nmcli connection add type wifi ifname '*' con-name "$PROFILE" ssid 2PNY-SETUP >/dev/null
    nmcli connection modify "$PROFILE" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared ipv4.addresses 10.42.0.1/24 ipv6.method disabled connection.autoconnect no connection.mdns yes >/dev/null
  fi
}
case "$ACTION" in
  status)
    active "$PROFILE" && echo active || echo inactive
    ;;
  on)
    WIFI="$(wifi_if)"; [[ -n "$WIFI" ]] || { echo 'Wi-Fi não detectado' >&2; exit 2; }
    ensure_profile
    rfkill unblock wifi >/dev/null 2>&1 || true
    nmcli radio wifi on >/dev/null 2>&1 || true
    # Avoid two setup interfaces owning 10.42.0.1 simultaneously.
    nmcli connection down 2PNY-Ethernet-Setup >/dev/null 2>&1 || true
    nmcli --wait 12 connection up "$PROFILE" ifname "$WIFI" >/dev/null
    echo 'AP 2PNY-SETUP ativo e aberto'
    ;;
  off)
    nmcli connection down "$PROFILE" >/dev/null 2>&1 || true
    echo 'AP 2PNY-SETUP desativado'
    ;;
  *) echo 'uso: 2pny-ap-control status|on|off' >&2; exit 2;;
esac
''')

# If the static profile ever becomes corrupted, recreate an OPEN profile rather
# than falling back to NetworkManager's WPA hotspot helper.
fb = root / 'rootfs-overlay/usr/local/sbin/2pny-firstboot'
s = fb.read_text()
legacy = '''  nmcli connection delete 2PNY-SETUP >/dev/null 2>&1 || true\n  if nmcli --wait 8 device wifi hotspot ifname "$WIFI_IF" con-name 2PNY-SETUP ssid 2PNY-SETUP band bg channel 6 password 2pnysetup >/dev/null 2>&1; then\n    nmcli connection modify 2PNY-SETUP ipv4.method shared ipv4.addresses 10.42.0.1/24 ipv6.method disabled connection.autoconnect no connection.mdns yes >/dev/null 2>&1 || true\n    status_write ready-wifi-recovered; echo '2PNY-SETUP recovered: http://10.42.0.1'; exit 0\n  fi'''
open_recovery = '''  nmcli connection delete 2PNY-SETUP >/dev/null 2>&1 || true\n  if nmcli connection add type wifi ifname "$WIFI_IF" con-name 2PNY-SETUP ssid 2PNY-SETUP >/dev/null 2>&1; then\n    nmcli connection modify 2PNY-SETUP 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared ipv4.addresses 10.42.0.1/24 ipv6.method disabled connection.autoconnect no connection.mdns yes >/dev/null 2>&1 || true\n    if nmcli --wait 10 connection up 2PNY-SETUP ifname "$WIFI_IF" >/dev/null 2>&1; then\n      status_write ready-wifi-recovered; echo '2PNY-SETUP aberto recuperado: http://10.42.0.1'; exit 0\n    fi\n  fi'''
if legacy in s:
    s = s.replace(legacy, open_recovery, 1)
else:
    # Refuse to silently ship the old password fallback if its text changed.
    if 'device wifi hotspot' in s or 'password 2pnysetup' in s:
        raise SystemExit('unexpected legacy secured hotspot fallback')
fb.write_text(s)

# Make state directory explicit before the hardened service namespace starts.
svc = root / 'rootfs-overlay/etc/systemd/system/2pnyd.service'
s = svc.read_text()
if 'StateDirectory=2pny' not in s:
    s = s.replace('[Service]\nType=simple', '[Service]\nType=simple\nStateDirectory=2pny', 1)
svc.write_text(s)

# Add panel health, captive endpoints and AP control to the existing local daemon.
p = root / 'src/2pnyd/main.go'
s = p.read_text()

# Normalize every known port-80 listener form to all interfaces.
s, n1 = re.subn(r'http\.ListenAndServe\(\s*"(?:127\.0\.0\.1|localhost|0\.0\.0\.0)?:80"\s*,', 'http.ListenAndServe("0.0.0.0:80",', s, count=1)
if n1 == 0:
    s, n1 = re.subn(r'http\.ListenAndServe\(\s*":80"\s*,', 'http.ListenAndServe("0.0.0.0:80",', s, count=1)
s, n2 = re.subn(r'Addr:\s*"(?:127\.0\.0\.1|localhost|0\.0\.0\.0)?:80"', 'Addr: "0.0.0.0:80"', s, count=1)
if n1 == 0 and n2 == 0 and '0.0.0.0:80' not in s:
    candidates = [line.strip() for line in s.splitlines() if 'ListenAndServe' in line or 'Addr:' in line]
    raise SystemExit('could not prove port-80 listener: ' + ' | '.join(candidates[:8]))

marker = '// 2PNY_CAPTIVE_AP_API_V1'
if marker not in s:
    anchor = '// 2PNY_MODULE_STATUS_API_V1'
    if anchor not in s:
        raise SystemExit('module API anchor not found')
    code = r'''
// 2PNY_CAPTIVE_AP_API_V1
func healthzHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("2PNY OK\n"))
}

func captivePortalHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store, no-cache, must-revalidate")
	http.Redirect(w, r, "/wizard", http.StatusFound)
}

func apActive() bool {
	out, err := exec.Command("nmcli", "-t", "-f", "NAME", "connection", "show", "--active").Output()
	if err != nil {
		return false
	}
	for _, line := range strings.Split(string(out), "\n") {
		if strings.TrimSpace(line) == "2PNY-SETUP" {
			return true
		}
	}
	return false
}

func apControlHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	if r.Method == http.MethodGet {
		writeJSON(w, http.StatusOK, map[string]any{"active": apActive(), "ssid": "2PNY-SETUP", "open": true})
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
		return
	}
	if err := r.ParseForm(); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "pedido inválido"})
		return
	}
	action := strings.TrimSpace(r.FormValue("action"))
	if action != "on" && action != "off" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "action deve ser on ou off"})
		return
	}
	out, err := exec.Command("/usr/local/sbin/2pny-ap-control", action).CombinedOutput()
	msg := strings.TrimSpace(string(out))
	if err != nil {
		if msg == "" { msg = err.Error() }
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok": false, "error": msg, "active": apActive()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "message": msg, "active": apActive(), "ssid": "2PNY-SETUP", "open": true})
}

'''
    s = s.replace(anchor, code + anchor, 1)

route_anchor = '\thttp.HandleFunc("/api/modules", moduleStatusHandler)'
if '/healthz' not in s:
    if route_anchor not in s:
        raise SystemExit('module route anchor not found')
    routes = route_anchor + '''\n\thttp.HandleFunc("/healthz", healthzHandler)\n\thttp.HandleFunc("/api/ap", apControlHandler)\n\thttp.HandleFunc("/generate_204", captivePortalHandler)\n\thttp.HandleFunc("/gen_204", captivePortalHandler)\n\thttp.HandleFunc("/hotspot-detect.html", captivePortalHandler)\n\thttp.HandleFunc("/library/test/success.html", captivePortalHandler)\n\thttp.HandleFunc("/connecttest.txt", captivePortalHandler)\n\thttp.HandleFunc("/ncsi.txt", captivePortalHandler)\n\thttp.HandleFunc("/redirect", captivePortalHandler)'''
    s = s.replace(route_anchor, routes, 1)

# Responsive contract is injected in every embedded page without external assets.
if '2pny-responsive-hotfix2' not in s:
    responsive = r'''<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style id="2pny-responsive-hotfix2">html,body{max-width:100%;overflow-x:hidden}img,svg,video,canvas{max-width:100%;height:auto}pre,code{max-width:100%;white-space:pre-wrap;overflow-wrap:anywhere}table{max-width:100%;display:block;overflow-x:auto;-webkit-overflow-scrolling:touch}.container,main,.card,.panel,section{max-width:100%}.grid,.cards,.formgrid{grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr))!important}@media(max-width:640px){body{font-size:16px}.container,main{width:100%!important;padding-left:12px!important;padding-right:12px!important}.card,.panel,section{width:100%!important;margin-left:0!important;margin-right:0!important}button,.btn,input,select,textarea{min-height:44px;max-width:100%}.actions{display:flex!important;flex-wrap:wrap!important;gap:8px!important}.actions .btn,.actions button{flex:1 1 160px}}</style>'''
    s = s.replace('</head>', responsive + '</head>')

if '2pny-ap-runtime-v1' not in s:
    ui = r'''<script id="2pny-ap-runtime-v1">(function(){async function state(){try{var r=await fetch('/api/ap',{cache:'no-store'});if(!r.ok)return;var x=await r.json();var b=document.getElementById('pny-ap-toggle');if(!b)return;b.textContent=x.active?'AP: ligado':'AP: desligado';b.dataset.active=x.active?'1':'0';b.title=x.active?'Desativar 2PNY-SETUP':'Ativar 2PNY-SETUP aberto'}catch(e){}}async function toggle(){var b=document.getElementById('pny-ap-toggle');if(!b)return;var on=b.dataset.active==='1';if(on&&!confirm('Desativar o modo AP? Se você estiver conectado ao 2PNY-SETUP, esta conexão será encerrada.'))return;b.disabled=true;try{var q=new URLSearchParams({action:on?'off':'on'});var r=await fetch('/api/ap',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:q});var x=await r.json();if(!r.ok)alert(x.error||'Não foi possível alterar o AP.');else if(!on)alert('AP 2PNY-SETUP ativado sem senha. Se esta tela desconectar, conecte-se ao AP novamente.')}catch(e){alert('Falha ao alterar o modo AP.')}b.disabled=false;setTimeout(state,700)}function boot(){if(document.getElementById('pny-ap-toggle')){state();return}var b=document.createElement('button');b.id='pny-ap-toggle';b.type='button';b.className='btn';b.style.cssText='position:fixed;left:12px;bottom:12px;z-index:9999;padding:9px 12px;border-radius:10px';b.textContent='AP: ...';b.onclick=toggle;document.body.appendChild(b);state()}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot()})();</script>'''
    s = s.replace('</body>', ui + '</body>')

p.write_text(s)

# Extend display discovery conservatively: only report evidence we can see.
hp = root / 'rootfs-overlay/usr/local/sbin/2pny-hardware-probe'
hs = hp.read_text()
if 'def probe_configured_display(' not in hs:
    anchor = '\nstate = {'
    if anchor not in hs:
        raise SystemExit('hardware display state anchor not found')
    helper = r'''

def probe_configured_display(i2c, hat):
    addresses = {str(item.get("address", "")).lower() for item in i2c}
    if "0x3c" in addresses or "0x3d" in addresses:
        addr = "0x3c" if "0x3c" in addresses else "0x3d"
        return {"detected": True, "state": "i2c_configured", "class": "oled", "model": "OLED I2C compatível", "address": addr, "confidence": "configured"}
    if "0x27" in addresses or "0x3f" in addresses:
        addr = "0x27" if "0x27" in addresses else "0x3f"
        return {"detected": True, "state": "i2c_configured", "class": "character_lcd", "model": "HD44780/PCF8574 compatível", "address": addr, "confidence": "configured"}
    h = " ".join(str(hat.get(k, "")) for k in ("product", "vendor")).lower()
    if any(word in h for word in ("display", "screen", "lcd", "oled", "tft")):
        return {"detected": True, "state": "hat_metadata", "class": "hat_display", "model": hat.get("product") or "Display HAT", "confidence": "hat_metadata"}
    for fb in sorted(glob.glob("/sys/class/graphics/fb*")):
        name = read_text(Path(fb) / "name")
        low = name.lower()
        if name and any(word in low for word in ("tft", "lcd", "ili", "st77", "fb_", "waveshare")):
            return {"detected": True, "state": "framebuffer", "class": "framebuffer", "model": name, "device": fb, "confidence": "kernel"}
    return None
'''
    hs = hs.replace(anchor, helper + anchor, 1)

    pending = 'if not state["display"].get("detected") and state["mmdvm"].get("detected"):'
    if pending not in hs:
        pending = "if not state['display'].get('detected') and state['mmdvm'].get('detected'):"
    if pending not in hs:
        raise SystemExit('hardware pending-display anchor not found')
    inject = '''configured_display = probe_configured_display(state["i2c"], state["hat"])\nif not state["display"].get("detected") and configured_display:\n    state["display"] = configured_display\n\n'''
    hs = hs.replace(pending, inject + pending, 1)
hp.write_text(hs)

# Source validation: make the new behavior a build contract.
v = root / 'builder/validate-source.sh'
vs = v.read_text().replace("grep -q '0.1.7-hotfix1' src/2pnyd/main.go", "grep -q '0.1.7-hotfix2' src/2pnyd/main.go")
if '# 2PNY_0_1_7_HOTFIX2_CAPTIVE' not in vs:
    vs += '''\n# 2PNY_0_1_7_HOTFIX2_CAPTIVE\necho "[2PNY] Validate open captive AP and responsive panel"\nbash -n rootfs-overlay/usr/local/sbin/2pny-ap-control\npython3 -c 'p="rootfs-overlay/usr/local/sbin/2pny-hardware-probe"; compile(open(p, encoding="utf-8").read(), p, "exec")'\n! grep -q '\\[wifi-security\\]' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\ngrep -q 'address=/#/10.42.0.1' rootfs-overlay/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf\ngrep -q 'StateDirectory=2pny' rootfs-overlay/etc/systemd/system/2pnyd.service\ngrep -q '2PNY_CAPTIVE_AP_API_V1' src/2pnyd/main.go\ngrep -q '/healthz' src/2pnyd/main.go\ngrep -q '/api/ap' src/2pnyd/main.go\ngrep -q '/generate_204' src/2pnyd/main.go\ngrep -q '/hotspot-detect.html' src/2pnyd/main.go\ngrep -q '2pny-responsive-hotfix2' src/2pnyd/main.go\ngrep -q '2pny-ap-runtime-v1' src/2pnyd/main.go\ngrep -q 'probe_configured_display' rootfs-overlay/usr/local/sbin/2pny-hardware-probe\ngrep -q '0.1.7-hotfix2' src/2pnyd/main.go\n'''
v.write_text(vs)
PY

chmod 0755 rootfs-overlay/usr/local/sbin/2pny-ap-control rootfs-overlay/usr/local/sbin/2pny-firstboot rootfs-overlay/usr/local/sbin/2pny-hardware-probe
chmod 0600 rootfs-overlay/etc/NetworkManager/system-connections/*.nmconnection
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-hardware-probe
rm -rf rootfs-overlay/usr/local/sbin/__pycache__
gofmt -w src/2pnyd/main.go

echo '2PNY 0.1.7 hotfix2 captive/open AP, panel health, display discovery and responsive UI applied'
