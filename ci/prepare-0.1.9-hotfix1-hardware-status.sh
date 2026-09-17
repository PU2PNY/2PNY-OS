#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path

# Version hotfix identity.
for rel in [
    'builder/build-image.sh',
    'rootfs-overlay/usr/local/sbin/2pny-firstboot',
    'rootfs-overlay/usr/local/sbin/2pny-network-core',
    'src/2pnyd/main.go',
]:
    p = Path(rel)
    s = p.read_text()
    s = s.replace('0.1.9-alpha', '0.1.9-hotfix1-alpha')
    p.write_text(s)
Path('rootfs-overlay/etc/2pny/version').write_text('0.1.9-hotfix1-alpha\n')

p = Path('src/2pnyd/main.go')
s = p.read_text()

# Critical fix: the wizard was polling the legacy /api/hardware payload.
# Keep that endpoint untouched for backward compatibility and give the new
# wizard its dedicated state-machine endpoint.
s = s.replace(
    "async function getStatus(){try{let r=await fetch('/api/hardware',{cache:'no-store'});return r.ok?await r.json():null}catch(e){return null}}",
    "async function getStatus(){try{let r=await fetch('/api/hardware/status',{cache:'no-store'});return r.ok?await r.json():null}catch(e){return null}}",
)

main_anchor = 'http.HandleFunc("/api/hardware/scan", hardwareScanHandler)'
if 'http.HandleFunc("/api/hardware/status", hardwareStatusHandler)' not in s:
    if main_anchor not in s:
        raise SystemExit('hardware route anchor not found')
    s = s.replace(
        main_anchor,
        'http.HandleFunc("/api/hardware/status", hardwareStatusHandler)\n\t' + main_anchor,
        1,
    )

# While the serial probe is still running, show the Raspberry/local buses
# immediately instead of leaving the cards blank until all serial attempts end.
old_poll = "let s=await getStatus();if(s&&s.state==='complete'){render(s);return}if(s&&s.state==='error')"
new_poll = "let s=await getStatus();if(s&&s.raspberry){$('pi-model').textContent=s.raspberry?.model||'Não informado';let ph=s.hat||{};$('hat').textContent=ph.detected?[ph.product,ph.vendor].filter(Boolean).join(' — ')||'EEPROM presente':'Não identificado';$('ports').textContent=(s.serial_ports||[]).map(x=>x.path+(x.driver?' ['+x.driver+']':'')).join(', ')||'nenhuma';$('i2c').textContent=(s.i2c||[]).map(x=>x.address).join(', ')||'nenhum'}if(s&&s.state==='complete'){render(s);return}if(s&&s.state==='error')"
if old_poll not in s:
    raise SystemExit('wizard polling anchor not found')
s = s.replace(old_poll, new_poll, 1)

# Make the timeout text precise: the basic Raspberry data may already be shown.
s = s.replace(
    "stateBox('warn','Detecção encerrada por tempo','Você pode detectar novamente ou continuar manualmente para RF.')",
    "stateBox('warn','Sondagem serial excedeu o tempo','Os dados locais acima continuam válidos. Detecte novamente ou avance para RF manualmente.')",
)

# If GET_VERSION does not answer but /dev/serial0 exists, expose it only as a
# candidate. Do not claim that a MMDVM was positively identified.
probe = Path('rootfs-overlay/usr/local/sbin/2pny-hardware-probe')
ps = probe.read_text()
anchor = 'for item in state["serial_ports"]:\n    if item["realpath"] == mmdvm_real:'
insert = '''if not state["mmdvm"].get("detected"):\n    for item in state["serial_ports"]:\n        if item.get("path") == "/dev/serial0":\n            state["mmdvm"]["candidate_port"] = item["path"]\n            state["mmdvm"]["candidate_realpath"] = item["realpath"]\n            state["mmdvm"]["candidate_reason"] = "primary_uart"\n            break\n\n'''
if 'candidate_reason' not in ps:
    if anchor not in ps:
        raise SystemExit('probe candidate anchor not found')
    ps = ps.replace(anchor, insert + anchor, 1)
probe.write_text(ps)

# Reflect a candidate UART in the UI without falsely marking detection success.
old_else = "else{$('m-state').textContent='MMDVM não respondeu';$('m-port').textContent='—';$('m-desc').textContent=h.detected&&/mmdvm/i.test(h.product||'')?'HAT parece relacionado a MMDVM, mas o UART não respondeu':'Não identificada';"
new_else = "else{let cp=m.candidate_port||'';$('m-state').textContent=cp?'UART encontrado; MMDVM não confirmou':'MMDVM não respondeu';$('m-port').textContent=cp||'—';if(cp&&!$('rf-port').value)$('rf-port').value=cp;$('m-desc').textContent=h.detected&&/mmdvm/i.test(h.product||'')?'HAT parece relacionado a MMDVM, mas o protocolo não respondeu':(cp?'Porta serial candidata; identificação ainda não confirmada':'Não identificada');"
if old_else not in s:
    raise SystemExit('MMDVM fallback UI anchor not found')
s = s.replace(old_else, new_else, 1)

p.write_text(s)
PY

gofmt -w src/2pnyd/main.go
python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-hardware-probe
rm -rf rootfs-overlay/usr/local/sbin/__pycache__

grep -Fq "fetch('/api/hardware/status'" src/2pnyd/main.go
grep -Fq 'http.HandleFunc("/api/hardware/status", hardwareStatusHandler)' src/2pnyd/main.go
grep -Fq 'candidate_reason' rootfs-overlay/usr/local/sbin/2pny-hardware-probe
grep -Fq '0.1.9-hotfix1-alpha' src/2pnyd/main.go

echo 'PU2PNY OS 0.1.9 hotfix1 hardware status route applied'
