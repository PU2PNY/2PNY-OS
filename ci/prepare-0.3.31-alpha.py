#!/usr/bin/env python3
from pathlib import Path
import hashlib,os,shutil,subprocess,sys,re,tempfile
root=Path(sys.argv[1]).resolve(); repo=Path(__file__).resolve().parents[1]; version='0.3.31-alpha'
def sha(p):
 p=Path(p);return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None
def install(src,dst,mode=0o644):
 t=root/dst;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/src,t);os.chmod(t,mode)
# DMR simplex/RF helper is protected byte-for-byte.
dmr=root/'rootfs-overlay/usr/local/libexec/2pny-dmr-apply'; dmr_before=sha(dmr)
# Last proven active profile: event-driven snapshot only after network-radio success.
for src,dst,mode in [
 ('src/2pny-profile-autostart-0.3.31.py','rootfs-overlay/usr/local/sbin/2pny-profile-autostart',0o755),
 ('src/2pny-profile-proven-0.3.31.py','rootfs-overlay/usr/local/sbin/2pny-profile-proven',0o755),
 ('src/2pny-profile-proven-0.3.31.service','rootfs-overlay/etc/systemd/system/2pny-profile-proven.service',0o644),
 ('src/2pny-profile-proven-0.3.31.path','rootfs-overlay/etc/systemd/system/2pny-profile-proven.path',0o644),
]: install(src,dst,mode)
wants=root/'rootfs-overlay/etc/systemd/system/multi-user.target.wants';wants.mkdir(parents=True,exist_ok=True)
link=wants/'2pny-profile-proven.path'
if link.exists() or link.is_symlink():link.unlink()
link.symlink_to('../2pny-profile-proven.path')
# YSF: use upstream native reconnect. Upstream retains m_current after link-loss,
# but Wires-X manual DISCONNECT clears it, so Reconnect=1 recovers transient loss
# without forcing a manually unlinked room and without restarting MMDVMHost.
net=root/'rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply'
s=net.read_text();anchor='InactivityTimeout=10\nReconnect=0\nRevert=0\nDebug=0'
if s.count(anchor)!=1:raise SystemExit('0.3.31 YSF reconnect anchor missing/ambiguous')
s=s.replace(anchor,'InactivityTimeout=10\nReconnect=1\nRevert=0\nDebug=0',1);net.write_text(s)
# Display native-first: keep Moderno V2 available only when explicitly selected.
display=root/'rootfs-overlay/usr/local/sbin/2pny-display-apply'
d=display.read_text()
for old,new in [
 ('requested=int(ov.get("layout") or 9)','requested=int(ov.get("layout") if ov.get("layout") is not None else 2)'),
 ('if requested not in (9,0,2,3):requested=9','if requested not in (9,0,2,3):requested=2'),
 ('renderer=str(ov.get("renderer") or ("pu2pny-modern-v2" if requested==9 else "mmdvmhost-native")).strip().lower()','renderer=str(ov.get("renderer") or "mmdvmhost-native").strip().lower()'),
 ('if renderer not in ("pu2pny-modern-v2","mmdvmhost-native"):renderer="pu2pny-modern-v2"','if renderer not in ("pu2pny-modern-v2","mmdvmhost-native"):renderer="mmdvmhost-native"'),
]:
 if old not in d:raise SystemExit('0.3.31 display native-first anchor missing: '+old[:36])
 d=d.replace(old,new,1)
display.write_text(d)
# Release identity only; no RF fields are changed here.
main=root/'src/2pnyd/main.go';m=main.read_text();old='appVersion            = "0.3.30-alpha"'
if m.count(old)!=1:raise SystemExit('0.3.31 version anchor missing/ambiguous')
main.write_text(m.replace(old,'appVersion            = "0.3.31-alpha"',1))
(root/'rootfs-overlay/etc/2pny/version').write_text(version+'\n')
# UI: expose edited profile vs actually active protocol and contextual radio guide.
h=root/'rootfs-overlay/usr/share/2pny/hotspot.html';html=h.read_text()
oldhero='<div class="heroState"><small>Protocolo ativo</small><b id="currentProto">—</b><span class="muted" id="heroStateText">Carregando estado…</span></div>'
newhero='<div class="heroState"><small>EDITANDO PERFIL</small><b id="editingProto">—</b><small style="margin-top:8px">ATIVO NO RÁDIO</small><b id="currentProto">—</b><span class="muted" id="heroStateText">Carregando estado…</span></div>'
if oldhero not in html:raise SystemExit('0.3.31 hotspot hero anchor missing')
html=html.replace(oldhero,newhero,1)
oldstate='<h3>Estado atual</h3><div class="big" id="state">—</div>'
guide='''<h3>Estado atual</h3><div class="big" id="state">—</div>\n<div class="notice" id="radioGuide" style="margin:12px 0"><b>COMO USAR PELO RÁDIO</b><div id="radioGuideBody" class="muted" style="line-height:1.7;margin-top:6px"></div></div>'''
if oldstate not in html:raise SystemExit('0.3.31 hotspot state anchor missing')
html=html.replace(oldstate,guide,1)
# Reuse existing selected state and language infrastructure; update labels whenever render() runs.
marker='function render(){'
if marker not in html:raise SystemExit('0.3.31 hotspot render anchor missing')
inject='''function updateRadioGuide(){\n var ep=PNY.q('editingProto');if(ep)ep.textContent=(definitions[selected]||{}).label||selected||'—';\n var b=PNY.q('radioGuideBody');if(!b)return;\n var lang=(document.documentElement.lang||'pt').toLowerCase();\n var map={\n  pt:{DMR:'DMR XLX: TG4000 desconecta; TG4001–TG4026 selecionam módulos A–Z; TG6 conforme a rede. Confira Group Call/Private Call e o Time Slot.',DSTAR:'D-Star: use CQCQCQ para conversar. Link/Unlink para REF, XRF, DCS ou XLX deve usar o módulo correto.',YSF:'YSF/C4FM: use o Wires-X nativo do rádio para listar, conectar e desconectar salas. Não use comandos 70xxxxx de DMR2YSF.'},\n  en:{DMR:'DMR XLX: TG4000 disconnects; TG4001–TG4026 select modules A–Z; TG6 as required by the network. Check Group/Private Call and Time Slot.',DSTAR:'D-Star: use CQCQCQ for normal calls. Link/Unlink REF, XRF, DCS or XLX using the correct module.',YSF:'YSF/C4FM: use native Wires-X on the radio to list, connect and disconnect rooms. Do not use DMR2YSF 70xxxxx commands.'},\n  es:{DMR:'DMR XLX: TG4000 desconecta; TG4001–TG4026 seleccionan módulos A–Z; TG6 según la red. Verifique Group/Private Call y Time Slot.',DSTAR:'D-Star: use CQCQCQ para hablar. Link/Unlink REF, XRF, DCS o XLX usando el módulo correcto.',YSF:'YSF/C4FM: use Wires-X nativo de la radio para listar, conectar y desconectar salas. No use comandos 70xxxxx de DMR2YSF.'}\n };var k=lang.startsWith('en')?'en':lang.startsWith('es')?'es':'pt';b.textContent=(map[k][selected]||'—');\n}\nfunction render(){updateRadioGuide();'''
html=html.replace(marker,inject,1);h.write_text(html)
# Validation
subprocess.run(['gofmt','-w',str(main)],check=True);subprocess.run(['go','test',str(main)],check=True)
for p in [net,display,root/'rootfs-overlay/usr/local/sbin/2pny-profile-autostart',root/'rootfs-overlay/usr/local/sbin/2pny-profile-proven']:
 subprocess.run(['python3','-m','py_compile',str(p)],check=True)
for c in root.rglob('__pycache__'):shutil.rmtree(c,ignore_errors=True)
for body in re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',h.read_text(),re.I|re.S):
 if body.strip():
  with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False) as tf:tf.write(body);tmp=tf.name
  try:subprocess.run(['node','--check',tmp],check=True)
  finally:os.unlink(tmp)
assert sha(dmr)==dmr_before,'DMR protected helper changed'
assert 'Type=HB' in net.read_text() and 'HBPort=20010' in net.read_text() and 'Port=20011' in net.read_text()
assert 'wait_bridge(proto,20010,unit,12.0)' in net.read_text()
assert 'Reconnect=1' in net.read_text()
assert 'mmdvmhost-native' in display.read_text()
print('PREPARE_0331_OK');print('DMR_PROTECTED_IDENTICAL')
