#!/bin/bash
set -euxo pipefail
ROOT="${1:?root mount required}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
install -m 0755 "$REPO/src/2pny-profile-autostart-0.3.31.py" "$ROOT/usr/local/sbin/2pny-profile-autostart"
install -m 0755 "$REPO/src/2pny-profile-proven-0.3.31.py" "$ROOT/usr/local/sbin/2pny-profile-proven"
install -m 0644 "$REPO/src/2pny-profile-proven-0.3.31.service" "$ROOT/etc/systemd/system/2pny-profile-proven.service"
install -m 0644 "$REPO/src/2pny-profile-proven-0.3.31.path" "$ROOT/etc/systemd/system/2pny-profile-proven.path"
mkdir -p "$ROOT/etc/systemd/system/multi-user.target.wants"
ln -sfn ../2pny-profile-proven.path "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-profile-proven.path"
ROOT="$ROOT" python3 - <<'PY'
import os,re
from pathlib import Path
root=Path(os.environ['ROOT'])
def one(path,old,new,label,binary=False):
    p=root/path
    if binary:
        b=p.read_bytes();a=old.encode();n=new.encode()
        c=b.count(a)
        if c<1: raise SystemExit(f'{label}: binary anchor missing')
        if len(a)!=len(n): raise SystemExit(f'{label}: binary replacement length differs')
        p.write_bytes(b.replace(a,n))
        return c
    s=p.read_text();c=s.count(old)
    if c!=1:raise SystemExit(f'{label}: anchor count={c}')
    p.write_text(s.replace(old,new,1));return c
# YSF upstream native reconnection. Manual Wires-X DISCONNECT clears m_current upstream.
one(Path('usr/local/sbin/2pny-protocol-network-apply'),'InactivityTimeout=10\nReconnect=0\nRevert=0\nDebug=0','InactivityTimeout=10\nReconnect=1\nRevert=0\nDebug=0','ysf-reconnect')
# Physical displays default to MMDVMHost native. PU2PNY Moderno remains explicit opt-in.
one(Path('usr/local/sbin/2pny-display-apply'),'requested=int(ov.get("layout") or 9)','requested=int(ov.get("layout") if ov.get("layout") is not None else 2)','display-layout-default')
one(Path('usr/local/sbin/2pny-display-apply'),'if requested not in (9,0,2,3):requested=9','if requested not in (9,0,2,3):requested=2','display-invalid-default')
one(Path('usr/local/sbin/2pny-display-apply'),'renderer=str(ov.get("renderer") or ("pu2pny-modern-v2" if requested==9 else "mmdvmhost-native")).strip().lower()','renderer=str(ov.get("renderer") or "mmdvmhost-native").strip().lower()','display-renderer-default')
one(Path('usr/local/sbin/2pny-display-apply'),'if renderer not in ("pu2pny-modern-v2","mmdvmhost-native"):renderer="pu2pny-modern-v2"','if renderer not in ("pu2pny-modern-v2","mmdvmhost-native"):renderer="mmdvmhost-native"','display-renderer-fallback')
# Protocol UI: editing profile != active RF protocol, plus contextual real radio guidance.
p=root/'usr/share/2pny/hotspot.html';s=p.read_text()
a='<div class="heroState"><small>Protocolo ativo</small><b id="currentProto">—</b><span class="muted" id="heroStateText">Carregando estado…</span></div>'
b='<div class="heroState"><small>EDITANDO PERFIL</small><b id="editingProto">—</b><small style="margin-top:8px">ATIVO NO RÁDIO</small><b id="currentProto">—</b><span class="muted" id="heroStateText">Carregando estado…</span></div>'
if s.count(a)!=1:raise SystemExit('hotspot hero anchor missing');s=s.replace(a,b,1)
a='<h3>Estado atual</h3><div class="big" id="state">—</div>'
b='''<h3>Estado atual</h3><div class="big" id="state">—</div><div class="notice" id="radioGuide" style="margin:12px 0"><b>COMO USAR PELO RÁDIO</b><div id="radioGuideBody" class="muted" style="line-height:1.7;margin-top:6px"></div></div>'''
if s.count(a)!=1:raise SystemExit('hotspot state anchor missing');s=s.replace(a,b,1)
a='function renderFamilies(){'
b='''function updateRadioGuide(){var ep=PNY.q('editingProto');if(ep)ep.textContent=(definitions[selected]||{}).label||selected||'—';var b=PNY.q('radioGuideBody');if(!b)return;var lang=(document.documentElement.lang||'pt').toLowerCase();var map={pt:{DMR:'DMR XLX: TG4000 desconecta; TG4001–TG4026 selecionam módulos A–Z; TG6 conforme a rede. Confira Group Call/Private Call e Time Slot.',DSTAR:'D-Star: CQCQCQ para conversar; Link/Unlink para REF, XRF, DCS ou XLX usando o módulo correto.',YSF:'YSF/C4FM: use o Wires-X nativo do rádio para listar, conectar e desconectar salas. Não use comandos 70xxxxx de DMR2YSF.'},en:{DMR:'DMR XLX: TG4000 disconnects; TG4001–TG4026 select modules A–Z; TG6 as required by the network. Check Group/Private Call and Time Slot.',DSTAR:'D-Star: CQCQCQ for normal calls; Link/Unlink REF, XRF, DCS or XLX using the correct module.',YSF:'YSF/C4FM: use native Wires-X on the radio to list, connect and disconnect rooms. Do not use DMR2YSF 70xxxxx commands.'},es:{DMR:'DMR XLX: TG4000 desconecta; TG4001–TG4026 seleccionan módulos A–Z; TG6 según la red. Verifique Group/Private Call y Time Slot.',DSTAR:'D-Star: CQCQCQ para hablar; Link/Unlink REF, XRF, DCS o XLX usando el módulo correcto.',YSF:'YSF/C4FM: use Wires-X nativo de la radio para listar, conectar y desconectar salas. No use comandos 70xxxxx de DMR2YSF.'}};var k=lang.startsWith('en')?'en':lang.startsWith('es')?'es':'pt';b.textContent=map[k][selected]||'—';}\nfunction renderFamilies(){updateRadioGuide();'''
if s.count(a)!=1:raise SystemExit('hotspot renderFamilies anchor missing');s=s.replace(a,b,1);p.write_text(s)
# Version file plus same-length Go binary constant patch; no code/control-flow changes.
(root/'etc/2pny/version').write_text('0.3.31-alpha\n')
bin_candidates=[root/'usr/local/bin/2pnyd',root/'usr/bin/2pnyd']
patched=0
for x in bin_candidates:
    if x.exists():patched+=one(x,'0.3.30-alpha','0.3.31-alpha','2pnyd-version',True)
if patched<1:raise SystemExit('2pnyd binary not found/version anchor absent')
PY
# Static gates before unmounting.
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-profile-autostart" "$ROOT/usr/local/sbin/2pny-profile-proven" "$ROOT/usr/local/sbin/2pny-protocol-network-apply" "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'Type=HB' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'HBPort=20010' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Port=20011' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'wait_bridge(proto,20010,unit,12.0)' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Reconnect=1' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'mmdvmhost-native' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'EDITANDO PERFIL' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'ATIVO NO RÁDIO' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'COMO USAR PELO RÁDIO' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'Perfil salvo sem reiniciar o rádio.' "$ROOT/usr/share/2pny/hotspot.html"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-profile-proven.path"
# Ensure we did not accidentally introduce an automatic TFT writer.
! grep -RqiE '(^|[;&|[:space:]])(upload|flash).*\.tft|\.tft.*(upload|flash)' "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/etc/systemd/system" || exit 1
sync
echo PATCH_IMAGE_0331_OK
