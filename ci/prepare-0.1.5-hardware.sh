#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re
root = Path('.')

# Version 0.1.5-alpha.
for rel in ['builder/build-image.sh','rootfs-overlay/usr/local/sbin/2pny-firstboot','src/2pnyd/main.go']:
    p = root/rel
    s = p.read_text()
    s = s.replace('0.1.4-alpha','0.1.5-alpha').replace('Alpha 0.1.4','Alpha 0.1.5')
    p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.5-alpha\n')

# Prepare the Raspberry Pi GPIO UART for an MMDVM HAT at image-build time.
p = root/'builder/build-image.sh'
s = p.read_text()
marker = '# 2PNY_MMDVM_UART_PREPARED'
if marker not in s:
    anchor = 'chmod 0600 "${ROOT_MNT}/etc/NetworkManager/system-connections/"*.nmconnection\n'
    if anchor not in s:
        raise SystemExit('UART build patch anchor not found')
    uart = r'''chmod 0600 "${ROOT_MNT}/etc/NetworkManager/system-connections/"*.nmconnection
# 2PNY_MMDVM_UART_PREPARED
BOOTCFG="${ROOT_MNT}/boot/firmware/config.txt"
CMDLINE="${ROOT_MNT}/boot/firmware/cmdline.txt"
grep -qxF 'enable_uart=1' "$BOOTCFG" || printf '\nenable_uart=1\n' >> "$BOOTCFG"
grep -qxF 'dtoverlay=disable-bt' "$BOOTCFG" || printf 'dtoverlay=disable-bt\n' >> "$BOOTCFG"
grep -qxF 'dtparam=i2c_arm=on' "$BOOTCFG" || printf 'dtparam=i2c_arm=on\n' >> "$BOOTCFG"
# The GPIO UART belongs to the radio modem, not to a Linux login console.
sed -E -i 's/(^| )console=(serial0|ttyAMA0|ttyS0),[0-9]+( |$)/ /g; s/  +/ /g; s/^ //; s/ $//' "$CMDLINE"
chroot "$ROOT_MNT" systemctl disable hciuart.service 2>/dev/null || true
chroot "$ROOT_MNT" systemctl disable serial-getty@ttyAMA0.service 2>/dev/null || true
chroot "$ROOT_MNT" systemctl disable serial-getty@ttyS0.service 2>/dev/null || true
'''
    s = s.replace(anchor, uart, 1)
p.write_text(s)

# Active, read-only-by-default hardware probe. It sends only identification queries.
probe = root/'rootfs-overlay/usr/local/sbin/2pny-hardware-probe'
probe.write_text(r'''#!/usr/bin/env python3
import glob
import json
import os
import re
import select
import termios
import time
from pathlib import Path

OUT = Path('/var/lib/2pny/hardware-probe.json')
OUT.parent.mkdir(parents=True, exist_ok=True)


def read_text(path):
    try:
        return Path(path).read_bytes().replace(b'\x00', b'').decode('utf-8', 'replace').strip()
    except Exception:
        return ''


def save(obj):
    obj['updated'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    tmp = OUT.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    os.chmod(tmp, 0o600)
    os.replace(tmp, OUT)


def serial_candidates():
    patterns = [
        '/dev/serial0', '/dev/ttyAMA0', '/dev/ttyS0',
        '/dev/ttyACM*', '/dev/ttyUSB*', '/dev/serial/by-id/*'
    ]
    out, seen = [], set()
    for pat in patterns:
        for dev in glob.glob(pat):
            try:
                real = os.path.realpath(dev)
                st = os.stat(real)
                key = (st.st_rdev, real)
            except Exception:
                continue
            if key in seen:
                continue
            seen.add(key)
            out.append({'path': dev, 'realpath': real})
    return out


def set_serial(fd, baud):
    attrs = termios.tcgetattr(fd)
    attrs[0] = 0
    attrs[1] = 0
    attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[3] = 0
    speed = {9600: termios.B9600, 115200: termios.B115200}[baud]
    attrs[4] = speed
    attrs[5] = speed
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 2
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)


def read_for(fd, seconds=0.8, limit=1024):
    end = time.monotonic() + seconds
    data = bytearray()
    while time.monotonic() < end and len(data) < limit:
        wait = max(0.0, min(0.12, end - time.monotonic()))
        r, _, _ = select.select([fd], [], [], wait)
        if not r:
            continue
        try:
            chunk = os.read(fd, min(256, limit - len(data)))
        except BlockingIOError:
            continue
        if chunk:
            data.extend(chunk)
    return bytes(data)


def open_port(path, baud):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    set_serial(fd, baud)
    return fd


def parse_mmdvm(raw):
    for pos, b in enumerate(raw):
        if b != 0xE0 or pos + 4 > len(raw):
            continue
        length = raw[pos + 1]
        if length < 4 or pos + length > len(raw):
            continue
        frame = raw[pos:pos + length]
        if frame[2] != 0x00:
            continue
        proto = frame[3]
        cap1 = cap2 = 0
        cpu = 'Não informado'
        udid = ''
        desc = ''
        if proto == 1:
            cap1, cap2 = 0x1F, 0x01
            desc = frame[4:].decode('utf-8', 'replace').strip('\x00 \r\n')
        elif proto == 2 and len(frame) >= 23:
            cap1, cap2 = frame[4], frame[5]
            cpu = {0: 'Atmel ARM', 1: 'NXP ARM', 2: 'ST-Micro ARM'}.get(frame[6], 'Tipo %d' % frame[6])
            udid = ''.join('%02X' % x for x in frame[7:23]).rstrip('0')
            desc = frame[23:].decode('utf-8', 'replace').strip('\x00 \r\n')
        else:
            desc = frame[4:].decode('utf-8', 'replace').strip('\x00 \r\n')
        modes = []
        for bit, name in [(0x01,'D-Star'),(0x02,'DMR'),(0x04,'YSF'),(0x08,'P25'),(0x10,'NXDN'),(0x40,'FM')]:
            if cap1 & bit:
                modes.append(name)
        if cap2 & 0x01:
            modes.append('POCSAG')
        profile = 'MMDVM compatível'
        low = desc.lower()
        if 'mmdvm_hs' in low or 'mmdvm hs' in low:
            profile = 'MMDVM_HS compatível'
        elif 'zumspot' in low:
            profile = 'ZUMspot (identificação do firmware)'
        return {
            'detected': True,
            'protocol_version': proto,
            'description': desc or 'Firmware MMDVM sem descrição',
            'profile': profile,
            'cpu': cpu,
            'udid': udid,
            'capabilities': modes,
            'duplex': 'unknown'
        }
    return None


def probe_mmdvm(dev):
    try:
        fd = open_port(dev, 115200)
    except Exception as e:
        return None, str(e)
    try:
        # Official MMDVM framing: E0, length=3, command GET_VERSION=00.
        os.write(fd, bytes((0xE0, 0x03, 0x00)))
        raw = read_for(fd, 1.0)
        return parse_mmdvm(raw), None
    except Exception as e:
        return None, str(e)
    finally:
        try: os.close(fd)
        except Exception: pass


def probe_nextion(dev):
    # Standard Nextion identification query. Never flash or change HMI data here.
    for baud in (9600, 115200):
        try:
            fd = open_port(dev, baud)
        except Exception:
            continue
        try:
            os.write(fd, b'connect\xff\xff\xff')
            raw = read_for(fd, 0.7)
            text = raw.replace(b'\xff', b'').decode('ascii', 'replace').strip('\x00\r\n ')
            if 'comok' in text.lower():
                model = ''
                parts = [x.strip() for x in text.split(',')]
                if len(parts) >= 3:
                    model = parts[2]
                return {'detected': True, 'port': dev, 'baud': baud, 'response': text, 'model': model or 'Nextion'}
        except Exception:
            pass
        finally:
            try: os.close(fd)
            except Exception: pass
    return None


def hat_info():
    base = Path('/proc/device-tree/hat')
    if not base.exists():
        return {'detected': False}
    return {
        'detected': True,
        'product': read_text(base/'product'),
        'vendor': read_text(base/'vendor'),
        'uuid': read_text(base/'uuid')
    }


def i2c_devices():
    out = []
    for p in glob.glob('/sys/bus/i2c/devices/*-*'):
        name = os.path.basename(p)
        m = re.match(r'^(\d+)-([0-9a-fA-F]{4})$', name)
        if not m:
            continue
        out.append({'bus': int(m.group(1)), 'address': '0x' + m.group(2)[-2:].lower(), 'name': read_text(Path(p)/'name')})
    return out


state = {
    'state': 'scanning',
    'raspberry': {
        'model': read_text('/proc/device-tree/model'),
        'serial': ''
    },
    'hat': hat_info(),
    'serial_ports': serial_candidates(),
    'i2c': i2c_devices(),
    'mmdvm': {'detected': False, 'duplex': 'unknown', 'capabilities': []},
    'display': {'detected': False, 'state': 'not_found'}
}
for line in read_text('/proc/cpuinfo').splitlines():
    if line.lower().startswith('serial') and ':' in line:
        state['raspberry']['serial'] = line.split(':',1)[1].strip()
        break
save(state)

mmdvm_real = None
for item in state['serial_ports']:
    result, err = probe_mmdvm(item['path'])
    item['mmdvm_probe'] = 'ok' if result else ('error' if err else 'no_response')
    if result:
        result['port'] = item['path']
        result['realpath'] = item['realpath']
        state['mmdvm'] = result
        mmdvm_real = item['realpath']
        break

for item in state['serial_ports']:
    if item['realpath'] == mmdvm_real:
        continue
    nxt = probe_nextion(item['path'])
    if nxt:
        state['display'] = dict(nxt, state='direct_serial')
        break

if not state['display'].get('detected') and state['mmdvm'].get('detected'):
    state['display'] = {
        'detected': False,
        'state': 'via_mmdvm_pending',
        'message': 'MMDVM detectada. A Nextion ligada ao conector do modem será confirmada pela camada Display/MMDVM.'
    }

state['state'] = 'complete'
save(state)
print(json.dumps(state, ensure_ascii=False))
''')

# Add HTTP API + a self-contained professional wizard. This page does not depend on the legacy dashboard CSS.
p = root/'src/2pnyd/main.go'
s = p.read_text()
marker = '2PNY_HARDWARE_WIZARD_V1'
if marker not in s:
    code = r'''
// 2PNY_HARDWARE_WIZARD_V1
const hardwareProbeFile = "/var/lib/2pny/hardware-probe.json"

func hardwareStatusHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	b, err := os.ReadFile(hardwareProbeFile)
	if err != nil {
		writeJSON(w, http.StatusOK, map[string]any{"state": "not_scanned"})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_, _ = w.Write(b)
}

func hardwareScanHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	_ = os.WriteFile(hardwareProbeFile, []byte("{\"state\":\"scanning\"}\n"), 0600)
	go func() {
		cmd := exec.Command("/usr/local/sbin/2pny-hardware-probe")
		if b, err := cmd.CombinedOutput(); err != nil {
			msg := strings.TrimSpace(string(b))
			if msg == "" { msg = err.Error() }
			_ = os.WriteFile(hardwareProbeFile, []byte(fmt.Sprintf("{\"state\":\"error\",\"message\":%q}\n", msg)), 0600)
			log.Printf("hardware probe failed: %v: %s", err, msg)
		}
	}()
	writeJSON(w, http.StatusAccepted, map[string]any{"ok": true, "state": "scanning"})
}

func wizardHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = fmt.Fprint(w, hardwareWizardHTML)
}

const hardwareWizardHTML = `<!doctype html>
<html lang="pt-BR" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light"><title>2PNY OS — Configuração</title>
<script>(function(){var t=localStorage.getItem('2pny-theme')||'dark';document.documentElement.setAttribute('data-theme',t)})();</script>
<style>
:root{color-scheme:dark;--bg:#080d13;--panel:#0f1722;--panel2:#151f2c;--line:#263447;--txt:#f4f7fb;--muted:#91a2b8;--blue:#4bb3fd;--green:#37d391;--yellow:#f6c85f;--red:#ff6475;--shadow:0 18px 55px #0007}html[data-theme=light]{color-scheme:light;--bg:#f1f5f9;--panel:#fff;--panel2:#eef3f8;--line:#d6e0eb;--txt:#111827;--muted:#5e6d80;--blue:#0879c9;--green:#087f5b;--yellow:#986801;--red:#c92a2a;--shadow:0 16px 42px #23364a17}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.45 Inter,system-ui,-apple-system,"Segoe UI",sans-serif}.app{min-height:100vh;display:grid;grid-template-columns:250px 1fr}.side{border-right:1px solid var(--line);padding:24px 18px;background:var(--panel)}.brand{display:flex;gap:12px;align-items:center;margin:0 4px 28px}.logo{width:48px;height:48px;border-radius:14px;background:#050505;color:#fff;display:grid;place-items:center;font-size:20px;font-weight:900}.brand b{font-size:20px}.brand small{display:block;color:var(--muted)}.steps{display:grid;gap:7px}.step{display:flex;gap:10px;align-items:center;padding:11px 12px;border:1px solid transparent;border-radius:12px;color:var(--muted)}.step .n{width:25px;height:25px;border-radius:50%;display:grid;place-items:center;background:var(--panel2);font-size:12px;font-weight:800}.step.done{color:var(--txt)}.step.done .n{background:#123d30;color:#7ff0bd}.step.active{background:var(--panel2);border-color:var(--line);color:var(--txt)}.step.active .n{background:var(--blue);color:#06131d}.main{padding:26px 32px 60px;max-width:1250px;width:100%;margin:auto}.top{display:flex;justify-content:space-between;align-items:center;gap:18px;margin-bottom:22px}.top h1{margin:0;font-size:28px}.top p{margin:4px 0 0;color:var(--muted)}button{font:inherit}.theme,.btn{border:1px solid var(--line);background:var(--panel2);color:var(--txt);border-radius:11px;padding:10px 14px;font-weight:750;cursor:pointer}.btn.primary{background:var(--blue);border-color:var(--blue);color:#05131d}.btn:disabled{opacity:.45;cursor:not-allowed}.statusbar{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:18px}.pill{display:inline-flex;gap:7px;align-items:center;background:var(--panel);border:1px solid var(--line);padding:7px 10px;border-radius:999px;color:var(--muted);font-size:12px}.dot{width:8px;height:8px;border-radius:50%;background:var(--green)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.card{background:var(--panel);border:1px solid var(--line);border-radius:17px;padding:20px;box-shadow:var(--shadow)}.card.wide{grid-column:1/-1}.card h2{font-size:17px;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 17px}.kv{display:grid;grid-template-columns:160px 1fr;gap:10px 15px}.kv dt{color:var(--muted)}.kv dd{margin:0;font-weight:650;overflow-wrap:anywhere}.chips{display:flex;gap:7px;flex-wrap:wrap}.chip{padding:6px 9px;border-radius:999px;background:var(--panel2);border:1px solid var(--line);font-size:12px}.state{display:flex;gap:13px;align-items:center;padding:15px;border:1px solid var(--line);border-radius:14px;background:var(--panel2);margin-bottom:16px}.spinner{width:20px;height:20px;border:3px solid var(--line);border-top-color:var(--blue);border-radius:50%;animation:spin .8s linear infinite}.okicon{width:22px;height:22px;border-radius:50%;background:var(--green);color:#06291d;display:grid;place-items:center;font-weight:900}.warnicon{width:22px;height:22px;border-radius:50%;background:var(--yellow);color:#332400;display:grid;place-items:center;font-weight:900}@keyframes spin{to{transform:rotate(360deg)}}.actions{display:flex;gap:10px;justify-content:flex-end;margin-top:18px}.hidden{display:none!important}.rfbox{border:1px dashed var(--line);border-radius:15px;padding:20px;background:var(--panel2)}.rfbox h2{margin-top:0}.notice{color:var(--muted)}
@media(max-width:820px){.app{display:block}.side{border-right:0;border-bottom:1px solid var(--line);padding:14px}.brand{margin-bottom:12px}.steps{display:flex;overflow:auto}.step{min-width:max-content}.main{padding:20px 14px 50px}.grid{grid-template-columns:1fr}.kv{grid-template-columns:125px 1fr}.top h1{font-size:23px}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style></head><body><div class="app"><aside class="side"><div class="brand"><div class="logo">2PNY</div><div><b>2PNY OS</b><small>Digital Radio Operating System</small></div></div><nav class="steps"><div class="step done"><span class="n">✓</span>Identidade</div><div class="step done"><span class="n">✓</span>Rede</div><div class="step active" id="step-hw"><span class="n">3</span>Hardware</div><div class="step" id="step-rf"><span class="n">4</span>RF</div><div class="step"><span class="n">5</span>Protocolos</div><div class="step"><span class="n">6</span>Redes</div><div class="step"><span class="n">7</span>Display</div><div class="step"><span class="n">8</span>Finalizar</div></nav></aside><main class="main"><div class="top"><div><h1 id="title">Detectando hardware</h1><p id="subtitle">O 2PNY identifica a Raspberry Pi, o modem MMDVM e interfaces de display sem adivinhar o modelo.</p></div><button class="theme" id="theme">☀ Claro</button></div><div class="statusbar"><span class="pill"><i class="dot"></i>2PNY online</span><span class="pill">Wi‑Fi conectado</span><span class="pill">0.1.5-alpha</span></div><section id="hardware"><div class="state" id="scanstate"><span class="spinner"></span><div><b>Preparando a detecção...</b><div class="notice">Somente consultas de identificação. Nenhuma frequência ou nível RF será alterado.</div></div></div><div class="grid"><article class="card"><h2>Raspberry Pi</h2><p class="sub">Plataforma e interfaces locais.</p><dl class="kv"><dt>Modelo</dt><dd id="pi-model">—</dd><dt>HAT EEPROM</dt><dd id="hat">—</dd><dt>Portas seriais</dt><dd id="ports">—</dd><dt>I²C</dt><dd id="i2c">—</dd></dl></article><article class="card"><h2>MMDVM</h2><p class="sub">Sondagem pelo protocolo oficial GET_VERSION.</p><dl class="kv"><dt>Estado</dt><dd id="m-state">Detectando...</dd><dt>Porta</dt><dd id="m-port">—</dd><dt>Firmware</dt><dd id="m-desc">—</dd><dt>Protocolo</dt><dd id="m-proto">—</dd><dt>CPU</dt><dd id="m-cpu">—</dd><dt>Simplex/Duplex</dt><dd id="m-duplex">Não confirmado</dd></dl><div class="chips" id="m-modes"></div></article><article class="card wide"><h2>Display / Nextion</h2><p class="sub">Primeiro procura display serial direto. Se estiver ligado ao conector da MMDVM, a confirmação será feita pela camada Display/MMDVM.</p><dl class="kv"><dt>Estado</dt><dd id="d-state">Detectando...</dd><dt>Modelo</dt><dd id="d-model">—</dd><dt>Porta</dt><dd id="d-port">—</dd></dl></article></div><div class="actions"><button class="btn" onclick="scan()">Detectar novamente</button><button class="btn primary" id="continue" disabled onclick="showRF()">Continuar para RF →</button></div></section><section id="rf" class="hidden"><div class="card"><h2>Etapa 4 — Configuração RF</h2><p class="sub">A MMDVM foi identificada. Esta tela prepara frequência, modo simplex/duplex e offsets; a aplicação segura desses parâmetros entra junto com MMDVMHost/MMDVMCal.</p><div class="rfbox"><b>Próximo módulo técnico</b><p class="notice">RX/TX Frequency • RX/TX Offset • BER • níveis • calibração assistida. Nenhum valor será aplicado até a rotina de validação e rollback estar pronta.</p></div><div class="actions"><button class="btn" onclick="showHW()">← Hardware</button><button class="btn primary" disabled>Salvar RF e continuar</button></div></div></section></main></div><script>
const $=id=>document.getElementById(id);function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.setItem('2pny-theme',t);$('theme').textContent=t==='dark'?'☀ Claro':'☾ Escuro'}$('theme').onclick=()=>setTheme((document.documentElement.getAttribute('data-theme')||'dark')==='dark'?'light':'dark');setTheme(localStorage.getItem('2pny-theme')||'dark');function esc(x){return String(x??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function stateBox(kind,title,text){let icon=kind==='scan'?'<span class="spinner"></span>':kind==='ok'?'<span class="okicon">✓</span>':'<span class="warnicon">!</span>';$('scanstate').innerHTML=icon+'<div><b>'+esc(title)+'</b><div class="notice">'+esc(text)+'</div></div>'}async function getStatus(){try{let r=await fetch('/api/hardware',{cache:'no-store'});return r.ok?await r.json():null}catch(e){return null}}async function scan(){stateBox('scan','Detectando hardware...','Consultando GPIO/UART, MMDVM, HAT, I²C e display.');$('continue').disabled=true;try{await fetch('/api/hardware/scan',{method:'POST'})}catch(e){}poll()}async function poll(){let end=Date.now()+25000;while(Date.now()<end){let s=await getStatus();if(s&&s.state==='complete'){render(s);return}if(s&&s.state==='error'){stateBox('warn','A detecção encontrou um erro',s.message||'Tente novamente.');return}await new Promise(r=>setTimeout(r,700))}stateBox('warn','A detecção está demorando','Tente Detectar novamente. O painel continua operacional.')}function render(s){$('pi-model').textContent=s.raspberry?.model||'Não informado';let h=s.hat||{};$('hat').textContent=h.detected?[h.product,h.vendor].filter(Boolean).join(' — ')||'EEPROM presente':'Não identificado';$('ports').textContent=(s.serial_ports||[]).map(x=>x.path).join(', ')||'nenhuma';$('i2c').textContent=(s.i2c||[]).map(x=>x.address).join(', ')||'nenhum';let m=s.mmdvm||{};if(m.detected){$('m-state').textContent='✓ MMDVM identificada';$('m-port').textContent=m.port||'—';$('m-desc').textContent=m.description||m.profile||'MMDVM';$('m-proto').textContent=m.protocol_version||'—';$('m-cpu').textContent=m.cpu||'—';$('m-duplex').textContent=m.duplex==='unknown'?'Não confirmado':m.duplex;$('m-modes').innerHTML=(m.capabilities||[]).map(x=>'<span class="chip">'+esc(x)+'</span>').join('');$('continue').disabled=false;stateBox('ok','Hardware principal identificado','A MMDVM respondeu ao protocolo de identificação. Você já pode avançar para a etapa RF.')}else{$('m-state').textContent='MMDVM não respondeu';$('m-port').textContent='—';$('m-desc').textContent=h.detected&&/mmdvm/i.test(h.product||'')?'HAT parece relacionado a MMDVM, mas o UART não respondeu':'Não identificada';$('m-proto').textContent='—';$('m-cpu').textContent='—';$('m-modes').innerHTML='';stateBox('warn','MMDVM ainda não identificada','Confira o encaixe do HAT. Nesta imagem o UART do GPIO já é reservado para a MMDVM.')}let d=s.display||{};if(d.detected){$('d-state').textContent='✓ Nextion identificada';$('d-model').textContent=d.model||'Nextion';$('d-port').textContent=d.port||'—'}else if(d.state==='via_mmdvm_pending'){$('d-state').textContent='Aguardando confirmação via MMDVM';$('d-model').textContent='Nextion atrás do modem: ainda não confirmada';$('d-port').textContent='Conector da MMDVM (a confirmar)'}else{$('d-state').textContent='Display serial direto não identificado';$('d-model').textContent='—';$('d-port').textContent='—'}}function showRF(){$('hardware').classList.add('hidden');$('rf').classList.remove('hidden');$('step-hw').classList.remove('active');$('step-hw').classList.add('done');$('step-rf').classList.add('active');$('title').textContent='Configuração RF';$('subtitle').textContent='Próxima etapa do assistente 2PNY.'}function showHW(){$('rf').classList.add('hidden');$('hardware').classList.remove('hidden');$('step-rf').classList.remove('active');$('step-hw').classList.add('active');$('title').textContent='Hardware';$('subtitle').textContent='Raspberry Pi, MMDVM e display.'}scan();
</script></body></html>`
'''
    route_marker = 'func setupHandler(w http.ResponseWriter, r *http.Request) {'
    if route_marker not in s:
        raise SystemExit('Go hardware insertion anchor not found')
    s = s.replace(route_marker, code + '\n' + route_marker, 1)

    route = 'http.HandleFunc("/api/setup", setupHandler)'
    if route not in s:
        raise SystemExit('Go route anchor not found')
    extra = route + '\n\thttp.HandleFunc("/wizard", wizardHandler)\n\thttp.HandleFunc("/api/hardware", hardwareStatusHandler)\n\thttp.HandleFunc("/api/hardware/scan", hardwareScanHandler)'
    s = s.replace(route, extra, 1)

    # Successful provisioning now goes directly to the next real wizard stage.
    s = s.replace('http://2pny.local/', 'http://2pny.local/wizard')
    s = s.replace('"next":"http://2pny.local"', '"next":"http://2pny.local/wizard"')
    s = s.replace('"next": "http://2pny.local"', '"next": "http://2pny.local/wizard"')

    old = 'A sondagem ativa do MMDVM e os gateways DMR/D-Star/YSF entram na próxima etapa após o primeiro teste físico.'
    new = 'A configuração por módulos já está disponível. <a href="/wizard"><b>Continuar configuração → detectar MMDVM e display</b></a>.'
    s = s.replace(old, new)

p.write_text(s)

# Run a first hardware scan after boot; the wizard can always rescan on demand.
fb = root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fs = fb.read_text()
if '2pny-hardware-probe' not in fs:
    anchor = 'systemctl restart 2pnyd.service || true\n'
    if anchor in fs:
        fs = fs.replace(anchor, anchor + '/usr/local/sbin/2pny-hardware-probe >/dev/null 2>&1 || true\n', 1)
fb.write_text(fs)

# Remove the experimental 0.1.4 theme greps; 0.1.5 validates its independent wizard instead.
v = root/'builder/validate-source.sh'
vs = v.read_text()
for line in [
    "grep -q '2pny-theme-bootstrap' src/2pnyd/main.go\n",
    "grep -q 'pny-theme-toggle' src/2pnyd/main.go\n",
    "grep -q 'localStorage.getItem' src/2pnyd/main.go\n",
    "grep -q '0.1.4-alpha' src/2pnyd/main.go\n",
]:
    vs = vs.replace(line, '')
checks = r'''
echo "[2PNY] Validate hardware/wizard module"
test -x rootfs-overlay/usr/local/sbin/2pny-hardware-probe
grep -q '2PNY_HARDWARE_WIZARD_V1' src/2pnyd/main.go
grep -q '/api/hardware/scan' src/2pnyd/main.go
grep -q 'MMDVM_GET_VERSION' rootfs-overlay/usr/local/sbin/2pny-hardware-probe || grep -q '0xE0, 0x03, 0x00' rootfs-overlay/usr/local/sbin/2pny-hardware-probe
grep -q '0.1.5-alpha' src/2pnyd/main.go
grep -q '2PNY_MMDVM_UART_PREPARED' builder/build-image.sh
'''
if '[2PNY] Validate hardware/wizard module' not in vs:
    vs += checks
v.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-hardware-probe
rm -rf rootfs-overlay/usr/local/sbin/__pycache__
chmod +x builder/build-image.sh builder/validate-source.sh rootfs-overlay/usr/local/sbin/2pny-firstboot rootfs-overlay/usr/local/sbin/2pny-hardware-probe

echo "2PNY 0.1.5 hardware/MMDVM/Nextion wizard module applied"
