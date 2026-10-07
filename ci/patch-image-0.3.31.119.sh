#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"

test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.118'
test -f "$ROOT/usr/share/2pny/display.html"
test -f "$ROOT/usr/local/sbin/2pny-display-apply"
test -x "$ROOT/usr/local/bin/NextionDriver-pu2pny"
test -f "$ROOT/etc/systemd/system/2pny-nextiondriver.service"

grep -Fq '/run/2pny-nextiondriver/ttyNextionDriver' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'User=mmdvm' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"

ROOT="$ROOT" python3 - <<'PY'
import os,re
from pathlib import Path
root=Path(os.environ['ROOT'])

def load(rel):
    p=root/rel
    if not p.is_file(): raise SystemExit(f'missing image file: {rel}')
    return p,p.read_text()

def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: anchor count={n}')
    return s.replace(old,new,1)

def subone(s,pattern,repl,label,flags=re.M):
    out,n=re.subn(pattern,repl,s,count=1,flags=flags)
    if n!=1: raise SystemExit(f'{label}: anchor count={n}')
    return out

# DISPLAY-027 UI: the Renderer field itself contains only the standard modem
# and Nextion/ON7LDS profiles. Hardware/model detection remains automatic, but
# no physical model is used to guess which HMI was flashed into the screen.
p,s=load('usr/share/2pny/display.html')
old='<label>Renderer</label><select id="rendererSelect"><option value="pu2pny-modern-v2">PU2PNY Moderno V2</option><option value="mmdvmhost-native">Compatível Pi-Star/WPSD (MMDVMHost nativo)</option><option value="on7lds-compatible">Pi-Star/WPSD avançado · ON7LDS NextionDriver</option></select>'
new='<label>Renderer</label><select id="rendererSelect"><option value="mmdvmhost-native|0">Modem · G4KLX padrão · ScreenLayout 0</option><option value="mmdvmhost-native|2">Nextion · ON7LDS L2 · ScreenLayout 2</option><option value="on7lds-compatible|3">Nextion · ON7LDS L3 · NextionDriver</option><option value="on7lds-compatible|4">Nextion · ON7LDS L3 HS · NextionDriver</option></select>'
s=one(s,old,new,'renderer choices')
old='<div id="nativeWrap" class="hidden"><label>Layout compatível</label><select id="nativeLayout"><option value="0">G4KLX · ScreenLayout 0</option><option value="2">ON7LDS L2 · ScreenLayout 2</option><option value="3">ON7LDS L3 · ScreenLayout 3</option><option value="4">ON7LDS L3 HS · ScreenLayout 4</option></select></div>'
new='<div><label>Detecção</label><div class="notice">Modelo/resolução: automático por <code>connect/comok</code> quando o modem permite retorno. HMI/layout: seleção manual quando não houver evidência específica.</div></div>'
s=one(s,old,new,'remove separate layout chooser')
s,n=re.subn(r'<article class="card"><h2>Prévia do Moderno V2</h2>.*?</article>',
'''<article class="card"><h2>Compatibilidade MMDVM / Nextion</h2><div class="displaypreview"><div class="screen"><small>MMDVMHost · Nextion</small><br><b id="previewProto">DMR</b><p id="previewText">Renderer padrão compatível com os layouts G4KLX/ON7LDS usados no ecossistema MMDVM. O HMI/TFT existente é preservado.</p></div></div><p class="muted">A detecção confirma hardware quando há resposta real; o perfil HMI não é inferido apenas pelo modelo físico.</p></article>''',s,count=1,flags=re.S)
if n!=1: raise SystemExit('preview removal anchor missing/ambiguous')
old='<div class="notice" style="margin-top:10px"><b>Nextion via modem:</b> o MMDVMHost continua sendo o único dono da UART. No modo PU2PNY, o Display Core envia atualizações incrementais pela bridge MQTT; no modo compatível, o renderer nativo do MMDVMHost assume sozinho a tela. O hardware só é confirmado após <code>comok</code>. <b>Modelo físico não identifica o HMI/layout instalado.</b> Nenhum TFT/HMI é gravado automaticamente. NextionDriver/L3 HS usa o driver endurecido e fixado desta imagem quando selecionado; TFT/HMI permanece preservado e a validação física continua obrigatória.</div>'
new='<div class="notice" style="margin-top:10px"><b>Nextion via modem:</b> a UART física continua sob controle do MMDVMHost. G4KLX/L2 usam o renderer nativo; L3/L3 HS usam o NextionDriver endurecido pela rota Transparent Data. <b>Modelo físico não identifica o HMI/layout instalado.</b> Nenhum TFT/HMI é gravado automaticamente. Se o HMI não puder ser identificado com evidência, escolha o Renderer manualmente.</div>'
s=one(s,old,new,'compatibility notice')
s=one(s,"['enabled','rendererSelect','modelSelect','nativeLayout'].forEach(function(id){q(id).onchange=function(){displayDirty=true;syncRenderer()}});","['enabled','rendererSelect','modelSelect'].forEach(function(id){q(id).onchange=function(){displayDirty=true}});",'ui change listeners')
s=one(s,"function syncRenderer(){var r=q('rendererSelect').value,native=r==='mmdvmhost-native'||r==='on7lds-compatible';q('nativeWrap').classList.toggle('hidden',!native)}","function syncRenderer(){}",'renderer sync')
old="q('enabled').checked=o.enabled!==false;q('rendererSelect').value=o.renderer==='on7lds-compatible'?'on7lds-compatible':(o.renderer==='mmdvmhost-native'?'mmdvmhost-native':'pu2pny-modern-v2');"
new="q('enabled').checked=o.enabled!==false;var ol=Number(o.layout),or=o.renderer==='on7lds-compatible'?'on7lds-compatible':'mmdvmhost-native';if(or==='on7lds-compatible'&&![3,4].includes(ol))ol=3;if(or==='mmdvmhost-native'&&![0,2].includes(ol))ol=0;var rk=or+'|'+ol;q('rendererSelect').value=Array.from(q('rendererSelect').options).some(function(x){return x.value===rk})?rk:'mmdvmhost-native|0';"
s=one(s,old,new,'renderer load')
old="q('nativeLayout').value=String([0,2,3,4].includes(Number(o.layout))?Number(o.layout):2);syncRenderer()"
s=one(s,old,"syncRenderer()",'remove layout load')
old="var renderer=q('rendererSelect').value,parts=q('modelSelect').value.split('|'),layout=renderer==='pu2pny-modern-v2'?9:Number(q('nativeLayout').value);var detail=renderer==='on7lds-compatible'?'Ativando compatibilidade ON7LDS por Transparent Data com writer exclusivo…':(renderer==='mmdvmhost-native'?'Ativando renderer compatível do MMDVMHost com writer exclusivo…':'Ativando PU2PNY Moderno V2 com atualizações incrementais…');"
new="var choice=q('rendererSelect').value.split('|'),renderer=choice[0],layout=Number(choice[1]),parts=q('modelSelect').value.split('|');var detail=renderer==='on7lds-compatible'?'Ativando Nextion ON7LDS por Transparent Data com writer exclusivo…':'Ativando renderer nativo do MMDVMHost com writer exclusivo…';"
s=one(s,old,new,'renderer save')
s=s.replace("q('driver').textContent=dr.driver||(active?'PU2PNY Display Core':'—');","q('driver').textContent=dr.driver||(active?'MMDVMHost / NextionDriver':'—');")
s=s.replace('<p><b>OLED 0x3C/0x3D:</b> SSD1306/SH1106 em Moderno V2 compacto. O controlador exato só é afirmado quando o kernel/Device Tree fornece evidência.</p>','<p><b>OLED 0x3C/0x3D:</b> SSD1306/SH1106 preservado. O controlador exato só é afirmado quando o kernel/Device Tree fornece evidência.</p>')
if 'PU2PNY Moderno' in s or 'pu2pny-modern-v2' in s: raise SystemExit('project-specific Nextion renderer remains in active display UI')
p.write_text(s)

p,s=load('usr/local/sbin/2pny-display-apply')
# Temporary source-shape diagnostic for the immutable 0.3.31.118 image.
for ln,line in enumerate(s.splitlines(),1):
    if any(k in line for k in ('requested','renderer','effective','DISPLAY-021','patch_modern_transport','layout')):
        print(f'DISPLAY_HELPER_DIAG {ln}: {line}')
s=s.replace('Two mutually-exclusive Nextion renderer modes are supported:', 'Two mutually-exclusive standard Nextion renderer modes are supported:')
s=s.replace('- pu2pny-modern-v2: MMDVMHost owns the modem serial transport while the\n  PU2PNY Display Core sends vector commands through MQTT host/display-in.\n- mmdvmhost-native: MMDVMHost owns both transport and native Nextion rendering.','- mmdvmhost-native: MMDVMHost owns transport and native G4KLX/ON7LDS L2 rendering.\n- on7lds-compatible: hardened NextionDriver sits between MMDVMHost and ON7LDS L3/L3 HS through Transparent Data.')
s=subone(s,r'^(?P<i>\s*)requested\s*=\s*int\(ov\.get\("layout"\)\s*or\s*[0-9]+\)\s*$',r'\g<i>raw_layout=ov.get("layout")\n\g<i>try:requested=int(raw_layout if raw_layout is not None else 0)\n\g<i>except Exception:requested=0','layout parser')
s=subone(s,r'^(?P<i>\s*)if\s+requested\s+not\s+in\s*\(9\s*,\s*0\s*,\s*2\s*,\s*3\s*,\s*4\)\s*:\s*requested\s*=\s*[29]\s*$',r'\g<i>if requested not in (0,2,3,4):requested=0','layout allowlist')
s=subone(s,r'^(?P<i>\s*)renderer\s*=\s*str\(ov\.get\("renderer"\)\s*or\s*.*\)\.strip\(\)\.lower\(\)\s*$',r'\g<i>renderer=str(ov.get("renderer") or ("on7lds-compatible" if requested in (3,4) else "mmdvmhost-native")).strip().lower()','renderer default')
s=subone(s,r'^(?P<i>\s*)if\s+renderer\s+not\s+in\s*\([^\n]+\)\s*:\s*renderer\s*=\s*"[^"]+"\s*$',r'\g<i>if renderer not in ("mmdvmhost-native","on7lds-compatible"):renderer=("on7lds-compatible" if requested in (3,4) else "mmdvmhost-native")','renderer allowlist')
policy_marker='# DISPLAY-021: MMDVM-connected Nextion may have a valid host->display path even\n'
s=one(s,policy_marker,'if requested in (3,4):renderer="on7lds-compatible"\nelse:renderer="mmdvmhost-native"\n'+policy_marker,'final renderer normalization')
s,n=re.subn(r'^\s*if\s+requested\s*==\s*9\s*:\s*renderer\s*=\s*"pu2pny-modern-v2"\s*$', '', s, count=1, flags=re.M)
if n!=1: raise SystemExit(f'remove Moderno fallback: anchor count={n}')
s=s.replace('    # Preserve an explicit native layout selection. Moderno V2 remains the\n    # default when the user has not selected ON7LDS 2/3.\n','')
s=subone(s,r'^(?P<i>\s*)effective\s*=\s*requested\s+if\s+requested\s+in\s*\(0\s*,\s*2\s*,\s*3\s*\)\s+else\s+2\s*$',r'\g<i>effective=requested if requested in (0,2) else 0','native layouts')
s=one(s,'if ov.get("enabled") is False:\n    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)','if ov.get("enabled") is False:\n    ctl("disable","--now",NEXTIONDRIVER);ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)','disable compatibility writer')
s=one(s,'if not kind:\n    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)','if not kind:\n    ctl("disable","--now",NEXTIONDRIVER);ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)','not configured compatibility writer')
s,n=re.subn(r'\ndef patch_modern_transport\(\):.*?\n    return backup\n', '\n', s, count=1, flags=re.S)
if n!=1: raise SystemExit('old Moderno transport helper missing/ambiguous')
marker='# PU2PNY renderer: direct displays use their bus; Nextion/MMDVM uses MQTT.\nstop_on7lds()\nctl("disable","--now",LEGACY)\nif kind=="nextion_mmdvm":\n    patch_modern_transport()'
replacement='# Non-Nextion direct displays keep their existing bus driver. Nextion can never enter this tail.\nif kind=="nextion_mmdvm":\n    raise RuntimeError("Renderer Nextion inválido; escolha Modem/G4KLX, ON7LDS L2, L3 ou L3 HS")\nstop_on7lds()\nctl("disable","--now",LEGACY)'
s=one(s,marker,replacement,'direct-display tail')
s=s.replace('"renderer":"pu2pny-modern-v2"','"renderer":"direct-display-core"')
s=s.replace('PU2PNY Moderno V2 configurado; iniciará junto com o rádio.','Display direto configurado; iniciará junto com o rádio.')
s=s.replace('PU2PNY Moderno V2 ativo.','Display direto ativo.')
if 'pu2pny-modern-v2' in s or 'PU2PNY Moderno' in s or 'patch_modern_transport' in s: raise SystemExit('old Moderno Nextion path remains in runtime helper')
p.write_text(s)
(root/'etc/2pny/version').write_text('0.3.31.119\n')
PY

python3 -m py_compile "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'Modem · G4KLX padrão · ScreenLayout 0' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Nextion · ON7LDS L2 · ScreenLayout 2' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Nextion · ON7LDS L3 · NextionDriver' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Nextion · ON7LDS L3 HS · NextionDriver' "$ROOT/usr/share/2pny/display.html"
! grep -Fqi 'PU2PNY Moderno' "$ROOT/usr/share/2pny/display.html"
! grep -Fq 'pu2pny-modern-v2' "$ROOT/usr/share/2pny/display.html"
! grep -Fq 'pu2pny-modern-v2' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'raw_layout=ov.get("layout")' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'requested not in (0,2,3,4)' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq '/run/2pny-nextiondriver/ttyNextionDriver' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'SendFrameType","1"' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'User=mmdvm' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.119'
echo PATCH_IMAGE_0331119_OK