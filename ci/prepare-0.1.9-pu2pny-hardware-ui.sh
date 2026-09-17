#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re

root = Path('.')

# ---------------------------------------------------------------------------
# Version + public identity. Internal 2pny service/file names remain unchanged
# for compatibility and rollback safety.
# ---------------------------------------------------------------------------
for rel in [
    'builder/build-image.sh',
    'rootfs-overlay/usr/local/sbin/2pny-firstboot',
    'rootfs-overlay/usr/local/sbin/2pny-network-core',
    'src/2pnyd/main.go',
]:
    p = root / rel
    s = p.read_text()
    s = s.replace('0.1.8-alpha', '0.1.9-alpha')
    p.write_text(s)
(root / 'rootfs-overlay/etc/2pny/version').write_text('0.1.9-alpha\n')

# Raspberry hostname becomes pu2pny. Keep legacy internal paths/services.
b = root / 'builder/build-image.sh'
s = b.read_text()
s = s.replace("printf '2pny\\n' > \"${ROOT_MNT}/etc/hostname\"", "printf 'pu2pny\\n' > \"${ROOT_MNT}/etc/hostname\"")
s = s.replace("\\1\\t2pny/' \"${ROOT_MNT}/etc/hosts\"", "\\1\\tpu2pny/' \"${ROOT_MNT}/etc/hosts\"")
if 'usbutils kmod python3' not in s:
    s = s.replace('usbutils python3', 'usbutils kmod python3')
if 'avahi-utils' not in s:
    s = s.replace('network-manager avahi-daemon', 'network-manager avahi-daemon avahi-utils')
if '2pny-mdns-alias.service' not in s:
    s = s.replace(
        'systemctl enable NetworkManager.service avahi-daemon.service 2pnyd.service 2pny-network-core.service 2pny-hardware-detect.service',
        'systemctl enable NetworkManager.service avahi-daemon.service 2pnyd.service 2pny-network-core.service 2pny-hardware-detect.service 2pny-mdns-alias.service'
    )
s = s.replace('Primary URL: http://2pny.local', 'Primary URL: http://pu2pny.local')
b.write_text(s)

fb = root / 'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fs = fb.read_text().replace('hostnamectl set-hostname 2pny', 'hostnamectl set-hostname pu2pny')
fb.write_text(fs)

# Friendly Avahi service name.
av = root / 'rootfs-overlay/etc/avahi/services/2pny-http.service'
if av.exists():
    a = av.read_text().replace('2PNY on %h', 'PU2PNY OS on %h')
    av.write_text(a)

# ---------------------------------------------------------------------------
# Legacy mDNS alias: primary hostname is pu2pny.local. On a normal LAN,
# publish 2pny.local against the current default-route IPv4 for compatibility.
# During captive setup both names are resolved by dnsmasq directly.
# ---------------------------------------------------------------------------
sbin = root / 'rootfs-overlay/usr/local/sbin'
sbin.mkdir(parents=True, exist_ok=True)
(sbin / '2pny-mdns-alias').write_text(r'''#!/bin/bash
set -u
child=""
last=""
cleanup(){ [[ -n "$child" ]] && kill "$child" 2>/dev/null || true; }
trap cleanup EXIT TERM INT
while true; do
  ip="$(ip -4 route get 1.1.1.1 2>/dev/null | sed -n 's/.* src \([0-9.]*\).*/\1/p' | head -1)"
  if [[ -n "$ip" && "$ip" != "$last" ]]; then
    [[ -n "$child" ]] && kill "$child" 2>/dev/null || true
    avahi-publish -a -f 2pny.local "$ip" >/dev/null 2>&1 &
    child=$!
    last="$ip"
  fi
  sleep 5
done
''')

svc = root / 'rootfs-overlay/etc/systemd/system'
svc.mkdir(parents=True, exist_ok=True)
(svc / '2pny-mdns-alias.service').write_text('''[Unit]\nDescription=PU2PNY legacy mDNS alias\nAfter=avahi-daemon.service NetworkManager.service\nWants=avahi-daemon.service\n\n[Service]\nType=simple\nExecStart=/usr/local/sbin/2pny-mdns-alias\nRestart=always\nRestartSec=3\nMemoryMax=16M\nTasksMax=24\n\n[Install]\nWantedBy=multi-user.target\n''')

# ---------------------------------------------------------------------------
# Fast local driver preparation. Do NOT download arbitrary drivers at runtime:
# load the known kernel modules already shipped in the image.
# ---------------------------------------------------------------------------
(sbin / '2pny-hardware-drivers').write_text(r'''#!/bin/bash
set -u
mods=(cdc_acm ch341 cp210x ftdi_sio i2c_dev)
loaded=0
for mod in "${mods[@]}"; do
  if modprobe "$mod" >/dev/null 2>&1; then
    echo "$mod=ready"
    loaded=$((loaded+1))
  else
    echo "$mod=unavailable"
  fi
done
echo "ready=$loaded"
exit 0
''')

# Improve AP state/control now that 0.1.8 uses hostapd directly instead of an
# active NetworkManager AP profile.
apctl = sbin / '2pny-ap-control'
aps = apctl.read_text()
aps = re.sub(
    r'''case "\$\{1:-status\}" in.*?esac''',
    r'''case "${1:-status}" in
  on)
    rm -f "$STATE/ap-disabled"
    systemctl restart 2pny-network-core.service >/dev/null 2>&1 || true
    echo 'AP habilitado'
    ;;
  off)
    touch "$STATE/ap-disabled"
    systemctl restart 2pny-network-core.service >/dev/null 2>&1 || true
    echo 'AP desabilitado'
    ;;
  status)
    if [[ -f "$STATE/ap-disabled" ]]; then
      echo inactive
    elif [[ -r /run/2pny/hostapd.pid ]] && kill -0 "$(cat /run/2pny/hostapd.pid 2>/dev/null)" 2>/dev/null; then
      echo active
    else
      echo inactive
    fi
    ;;
  *) echo 'uso: 2pny-ap-control on|off|status' >&2; exit 2;;
esac''',
    aps,
    count=1,
    flags=re.S,
)
apctl.write_text(aps)

# Captive DNS names: primary pu2pny.local + legacy 2pny.local.
for name, ip in [('dnsmasq-ap.template', '10.42.0.1'), ('dnsmasq-eth.template', '10.43.0.1')]:
    p = root / 'rootfs-overlay/usr/share/2pny/network' / name
    t = p.read_text()
    marker = f'address=/#/{ip}'
    aliases = f'address=/pu2pny.local/{ip}\naddress=/2pny.local/{ip}\n'
    if 'address=/pu2pny.local/' not in t:
        t = t.replace(marker, aliases + marker)
    p.write_text(t)

# ---------------------------------------------------------------------------
# Hardware probe 0.1.9: load local drivers, identify serial driver/USB IDs,
# try both common MMDVM baud rates, detect direct Nextion and kernel displays.
# ---------------------------------------------------------------------------
hp = sbin / '2pny-hardware-probe'
hs = hp.read_text()

hs = hs.replace(
    'speed = {9600: termios.B9600, 115200: termios.B115200}[baud]',
    '''speed_map = {9600: termios.B9600, 115200: termios.B115200}\n    if hasattr(termios, "B460800"):\n        speed_map[460800] = termios.B460800\n    speed = speed_map[baud]'''
)

# Add serial kernel-driver metadata.
old = 'out.append({"path": dev, "realpath": real})'
new = '''driver = ""\n            try:\n                driver = (Path("/sys/class/tty") / Path(real).name / "device/driver").resolve().name\n            except Exception:\n                pass\n            out.append({"path": dev, "realpath": real, "driver": driver})'''
if old in hs:
    hs = hs.replace(old, new, 1)

# Replace MMDVM probe with bounded dual-baud discovery.
hs = re.sub(
    r'def probe_mmdvm\(dev\):.*?\n\ndef probe_nextion',
    '''def probe_mmdvm(dev):\n    errors = []\n    for baud in (115200, 460800):\n        if baud == 460800 and not hasattr(termios, "B460800"):\n            continue\n        try:\n            fd = open_port(dev, baud)\n        except Exception as exc:\n            errors.append(str(exc))\n            continue\n        try:\n            request = bytes((0xE0, 0x03, 0x00))\n            os.write(fd, request)\n            result = parse_mmdvm(read_for(fd, 0.45))\n            if result:\n                result["baud"] = baud\n                return result, None\n        except Exception as exc:\n            errors.append(str(exc))\n        finally:\n            try:\n                os.close(fd)\n            except Exception:\n                pass\n    return None, (errors[-1] if errors else None)\n\n\ndef probe_nextion''',
    hs,
    count=1,
    flags=re.S,
)

# Make Nextion probing faster while retaining both common rates.
hs = hs.replace('raw = read_for(fd, 0.7)', 'raw = read_for(fd, 0.35)')

# Add generic USB + DRM/HDMI/DSI discovery before display classification.
anchor = '\ndef probe_configured_display(i2c, hat):\n'
extra = r'''
def usb_devices():
    found = []
    for base in sorted(Path("/sys/bus/usb/devices").glob("*")):
        vid = read_text(base / "idVendor")
        pid = read_text(base / "idProduct")
        if not vid or not pid:
            continue
        found.append({
            "vendor_id": vid,
            "product_id": pid,
            "manufacturer": read_text(base / "manufacturer"),
            "product": read_text(base / "product"),
            "serial": read_text(base / "serial"),
        })
    return found


def display_outputs():
    found = []
    for status in sorted(Path("/sys/class/drm").glob("card*-*/status")):
        if read_text(status).lower() != "connected":
            continue
        found.append({"connector": status.parent.name, "state": "connected"})
    return found

'''
if 'def usb_devices():' not in hs:
    if anchor not in hs:
        raise SystemExit('hardware display helper anchor not found')
    hs = hs.replace(anchor, '\n' + extra + anchor.lstrip('\n'), 1)

hs = hs.replace(
    '"i2c": i2c_devices(),\n    "mmdvm":',
    '"i2c": i2c_devices(),\n    "usb": usb_devices(),\n    "display_outputs": display_outputs(),\n    "mmdvm":',
    1,
)

pending = 'if not state["display"].get("detected") and state["mmdvm"].get("detected"):'
if 'kernel_display = state.get("display_outputs")' not in hs:
    if pending not in hs:
        raise SystemExit('hardware display fallback anchor not found')
    hs = hs.replace(
        pending,
        '''kernel_display = state.get("display_outputs") or []\nif not state["display"].get("detected") and kernel_display:\n    connector = kernel_display[0].get("connector", "display")\n    state["display"] = {"detected": True, "state": "kernel_connector", "class": "video_output", "model": connector, "confidence": "kernel"}\n\n''' + pending,
        1,
    )
hp.write_text(hs)

# ---------------------------------------------------------------------------
# Panel: PU2PNY branding, mobile hardening, non-blocking hardware wizard.
# ---------------------------------------------------------------------------
go = root / 'src/2pnyd/main.go'
gs = go.read_text()

# Visible/public brand only. Keep API/service paths and SSID compatibility.
for old, new in [
    ('2PNY OS', 'PU2PNY OS'),
    ('2PNY online', 'PU2PNY online'),
    ('2PNY local', 'PU2PNY local'),
    ('O 2PNY ', 'O PU2PNY '),
    ('o 2PNY ', 'o PU2PNY '),
    ('painel 2PNY', 'painel PU2PNY'),
    ('assistente 2PNY', 'assistente PU2PNY'),
]:
    gs = gs.replace(old, new)

gs = gs.replace('http://2pny.local', 'http://pu2pny.local')
gs = gs.replace('http://169.254.2.1', 'http://10.43.0.1')

# Remove duplicate square logo while keeping the clean wordmark.
gs = gs.replace('<div class="logo">2PNY</div>', '')
gs = gs.replace('<div class="logo">PU2PNY</div>', '')

# Hardware driver stage before probe.
probe_cmd = 'cmd := exec.Command("/usr/local/sbin/2pny-hardware-probe")'
if '2pny-hardware-drivers' not in gs:
    if probe_cmd not in gs:
        raise SystemExit('hardware scan command anchor not found')
    gs = gs.replace(
        probe_cmd,
        '_ = exec.Command("/usr/local/sbin/2pny-hardware-drivers").Run()\n\t\t' + probe_cmd,
        1,
    )

# AP state must reflect hostapd runtime, not the retired NetworkManager AP.
start = gs.find('func apActive() bool {')
end = gs.find('\nfunc apControlHandler', start)
if start < 0 or end < 0:
    raise SystemExit('apActive function anchor not found')
new_ap = '''func apActive() bool {\n\tout, err := exec.Command("/usr/local/sbin/2pny-ap-control", "status").Output()\n\treturn err == nil && strings.TrimSpace(string(out)) == "active"\n}\n'''
gs = gs[:start] + new_ap + gs[end:]

# RF port becomes editable for unsupported/new hardware.
gs = gs.replace('<input id="rf-port" readonly>', '<input id="rf-port" placeholder="Ex.: /dev/serial0">')

# The scan must never trap the user on the hardware page.
gs = gs.replace('id="continue" disabled onclick="showRF()"', 'id="continue" onclick="showRF()"')
gs = gs.replace("$('continue').disabled=true;try{await fetch('/api/hardware/scan'", "$('continue').disabled=false;try{await fetch('/api/hardware/scan'")
gs = gs.replace(
    "stateBox('warn','A detecção encontrou um erro',s.message||'Tente novamente.');return",
    "$('continue').disabled=false;stateBox('warn','A detecção encontrou um erro',(s.message||'Tente novamente.')+' Você pode continuar manualmente para RF.');return"
)
gs = gs.replace(
    "stateBox('warn','A detecção está demorando','Tente Detectar novamente. O painel continua operacional.')",
    "$('continue').disabled=false;stateBox('warn','Detecção encerrada por tempo','Você pode detectar novamente ou continuar manualmente para RF.')"
)
# Shorter UI timeout; probe itself is bounded/faster in 0.1.9.
gs = gs.replace('let end=Date.now()+25000', 'let end=Date.now()+12000')

# Always allow progression once a scan returns, even if MMDVM did not answer.
render_anchor = "function render(s){$('pi-model')"
if render_anchor in gs and "function render(s){$('continue').disabled=false;$('pi-model')" not in gs:
    gs = gs.replace(render_anchor, "function render(s){$('continue').disabled=false;$('pi-model')", 1)

gs = gs.replace(
    "$('ports').textContent=(s.serial_ports||[]).map(x=>x.path).join(', ')||'nenhuma';",
    "$('ports').textContent=(s.serial_ports||[]).map(x=>x.path+(x.driver?' ['+x.driver+']':'')).join(', ')||'nenhuma';"
)
gs = gs.replace(
    "stateBox('warn','MMDVM ainda não identificada','Confira o encaixe do HAT. Nesta imagem o UART do GPIO já é reservado para a MMDVM.')",
    "stateBox('warn','MMDVM não respondeu automaticamente','Os drivers locais foram preparados. Você pode detectar novamente ou informar a porta manualmente na etapa RF.')"
)
gs = gs.replace(
    "if(d.detected){$('d-state').textContent='✓ Nextion identificada';$('d-model').textContent=d.model||'Nextion';",
    "if(d.detected){$('d-state').textContent=d.state==='direct_serial'?'✓ Nextion identificada':'✓ Display identificado';$('d-model').textContent=d.model||'Display';"
)

# Strong mobile/responsive override. Keeps desktop appearance intact.
mobile_css = r'''<style id="pu2pny-responsive-019">html,body{width:100%;max-width:100%;overflow-x:hidden}.app,.main,.side,.card,.grid,.formgrid{min-width:0}.main{max-width:100%!important}.brand{gap:0}.brand>div{min-width:0}.brand b{font-size:20px}.actions{flex-wrap:wrap}.actions .btn{min-width:150px}.kv dd{min-width:0;word-break:break-word}@media(max-width:900px){.app{display:block}.side{padding:14px 14px 10px;border-right:0;border-bottom:1px solid var(--line)}.brand{margin:0 2px 10px}.steps{display:flex;gap:6px;overflow-x:auto;overscroll-behavior-x:contain;padding-bottom:5px;scrollbar-width:thin}.step{flex:0 0 auto;min-width:max-content;padding:8px 10px}.main{padding:18px 12px 56px}.top{align-items:flex-start;flex-wrap:wrap}.top>div{min-width:0;flex:1 1 240px}.theme{flex:0 0 auto}.grid,.formgrid{grid-template-columns:1fr!important}}@media(max-width:520px){body{font-size:15px}.side{padding:10px}.brand small{display:none}.main{padding:14px 10px 64px}.top{gap:10px;margin-bottom:14px}.top h1{font-size:22px;line-height:1.15}.statusbar{gap:6px}.pill{font-size:11px;padding:6px 8px}.card{padding:15px;border-radius:14px}.kv{grid-template-columns:1fr;gap:2px}.kv dt{margin-top:8px}.actions{display:grid!important;grid-template-columns:1fr!important}.actions .btn,.actions button{width:100%;min-width:0}.theme{padding:9px 11px}.step{font-size:13px}.step .n{width:22px;height:22px}}</style>'''
if 'pu2pny-responsive-019' not in gs:
    if '</head>' not in gs:
        raise SystemExit('panel head anchor not found')
    gs = gs.replace('</head>', mobile_css + '</head>')

go.write_text(gs)
PY

chmod 0755 \
  rootfs-overlay/usr/local/sbin/2pny-mdns-alias \
  rootfs-overlay/usr/local/sbin/2pny-hardware-drivers \
  rootfs-overlay/usr/local/sbin/2pny-hardware-probe \
  rootfs-overlay/usr/local/sbin/2pny-ap-control

bash -n rootfs-overlay/usr/local/sbin/2pny-mdns-alias
bash -n rootfs-overlay/usr/local/sbin/2pny-hardware-drivers
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-hardware-probe
rm -rf rootfs-overlay/usr/local/sbin/__pycache__
gofmt -w src/2pnyd/main.go

echo 'PU2PNY OS 0.1.9 hardware discovery, hostname, AP status and responsive UI applied'
