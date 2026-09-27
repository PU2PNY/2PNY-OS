#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch-0.3.29-surgical.py <staged-root>")
root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
share=root/"rootfs-overlay/usr/share/2pny"
main=root/"src/2pnyd/main.go"
hostapd=share/"network/hostapd.template"
netcore=root/"rootfs-overlay/usr/local/sbin/2pny-network-core"
wizard=share/"wizard.html"
expert=share/"expert.html"
lang=share/"ui-language.js"
version=root/"rootfs-overlay/etc/2pny/version"

for p in (main,hostapd,netcore,wizard,expert,lang,version):
    if not p.exists(): raise SystemExit(f"missing staged file: {p}")

def replace_exact(path, old, new, count=None):
    s=path.read_text()
    n=s.count(old)
    if count is not None and n != count:
        raise SystemExit(f"{path}: expected {count} occurrences of {old!r}, found {n}")
    if n == 0:
        raise SystemExit(f"{path}: anchor not found: {old!r}")
    path.write_text(s.replace(old,new))

# Release identity only. No RF/gateway logic is changed here.
replace_exact(main, 'appVersion            = "0.3.28-alpha"', 'appVersion            = "0.3.29-alpha"', 1)
replace_exact(main, 'APSSID:            "pu2pny",', 'APSSID:            "PU2PNY-OS",', 1)
replace_exact(main, '"ssid": "pu2pny"', '"ssid": "PU2PNY-OS"', 2)
main.write_text(main.read_text().replace('<TITLE>Success</TITLE>','<TITLE>PU2PNY-OS</TITLE>'))

# Canonical setup SSID. Hostname remains pu2pny.local by design.
hs=hostapd.read_text()
hs2,n=re.subn(r'(?m)^ssid=pu2pny$', 'ssid=PU2PNY-OS', hs)
if n != 1: raise SystemExit(f"hostapd SSID anchor count={n}")
hostapd.write_text(hs2)
netcore.write_text(netcore.read_text().replace('AP pu2pny','AP PU2PNY-OS').replace('Setup AP pu2pny','Setup AP PU2PNY-OS'))
w=wizard.read_text()
for a,b in (
    ('AP <b>pu2pny</b>','AP <b>PU2PNY-OS</b>'),
    ('Manter AP pu2pny ativo','Manter AP PU2PNY-OS ativo'),
    ('AP pu2pny voltou','AP PU2PNY-OS voltou'),
    ('AP pu2pny será restaurado','AP PU2PNY-OS será restaurado'),
    ('AP pu2pny estiver ativo','AP PU2PNY-OS estiver ativo'),
):
    w=w.replace(a,b)
wizard.write_text(w)

# Browser title is canonical on every user-facing HTML page.
for page in share.glob("*.html"):
    s=page.read_text()
    s,n=re.subn(r'<title>[^<]*</title>','<title>PU2PNY-OS</title>',s,flags=re.I)
    if n:
        page.write_text(s)

support_html = r'''
<section class="section"><div class="expertgrid">
<article class="card"><h2>Suporte PU2PNY-OS</h2>
<p class="muted">Gere uma prévia sanitizada antes de compartilhar. Nada é enviado automaticamente e nenhuma senha, token, API key ou segredo é incluído.</p>
<div class="row"><a class="btn" target="_blank" rel="noopener noreferrer" href="https://chat.whatsapp.com/IEtpCZ1t8IoEgktJs2aNZq?s=cl&p=a&mlu=4&iam=0">Grupo de suporte PU2PNY-OS</a><button class="btn primary" id="diagGenerate" type="button">Gerar prévia do relatório</button></div>
<textarea id="diagPreview" rows="13" readonly placeholder="A prévia aparecerá aqui depois da sua solicitação."></textarea>
<div class="row"><button class="btn" id="diagCopy" type="button" disabled>Copiar relatório</button><button class="btn" id="diagDownload" type="button" disabled>Baixar .txt</button></div>
<p class="statusmsg" id="diagState">Relatório ainda não gerado.</p></article>
<article class="card"><h2>Cross-mode</h2>
<p><b>Estado nesta Alpha:</b> não habilitado automaticamente.</p>
<div class="rows">
<div class="row"><span>DMR ↔ YSF DN</span><b>Transcoder necessário</b></div>
<div class="row"><span>DMR ↔ D-Star</span><b>Transcoder necessário</b></div>
<div class="row"><span>YSF DN ↔ D-Star</span><b>Transcoder necessário</b></div>
<div class="row"><span>NXDN / P25</span><b>Não habilitado</b></div>
</div>
<p class="muted">O MMDVM-CrossMode atual usa MMDVM-Transcoder. Sem o hardware/vocoder correspondente, o PU2PNY-OS não anuncia conversão de áudio como funcional.</p>
</article>
</div></section>
'''
e=expert.read_text()
marker='<section class="section"><div class="card"><h2>Detalhes técnicos</h2>'
if marker not in e: raise SystemExit("expert insertion marker not found")
e=e.replace(marker,support_html+"\n"+marker,1)
js = r'''
var diagText='',diagId='';
function diagScalar(v){return v==null||v===''?'—':String(v)}
async function buildSupportDiagnostic(){
  q('diagState').textContent='Gerando prévia local e sanitizada...';
  try{
    var dash=await PNY.getj('/api/dashboard',null,6000), dg=await PNY.getj('/api/diagnostics',null,6000);
    var err='';try{var rr=await fetch('/api/diagnostics/errors/download',{cache:'no-store'});if(rr.ok)err=await rr.text()}catch(_){}
    var now=new Date(),cfg=dash.config||{},hw=dash.hardware||{},m=hw.mmdvm||{},cn=dash.connectivity||{},dr=dash.display_runtime||{};
    diagId='PU2PNY-DIAG-'+now.toISOString().slice(0,10).replaceAll('-','')+'-'+now.toISOString().slice(11,19).replaceAll(':','');
    var lines=[
      diagId,'generated_utc: '+now.toISOString(),'version: '+diagScalar(dash.version),
      'callsign: '+diagScalar(cfg.callsign),'protocol: '+diagScalar(cfg.protocol),'use_mode: '+diagScalar(cfg.use_mode),
      'rx_hz: '+diagScalar(cfg.rx_hz),'tx_hz: '+diagScalar(cfg.tx_hz),
      'raspberry: '+diagScalar(hw.raspberry_model||hw.model),'mmdvm_model: '+diagScalar(m.model||m.firmware),
      'mmdvm_port: '+diagScalar(m.port),'mmdvm_baud: '+diagScalar(dash.mmdvm_baud),
      'display: '+diagScalar(dr.type)+' / '+diagScalar(dr.state),
      'uplink_interface: '+diagScalar(cn.default_interface||cn.client_interface),
      'local_ipv4: '+diagScalar((cn.ipv4||[]).join(',')),
      'mmdvmhost_active: '+diagScalar(dg.mmdvmhost_active),'gateway: '+diagScalar(dg.gateway),
      'gateway_active: '+diagScalar(dg.gateway_active),'',
      '[ERROS SANITIZADOS]',err||'—'
    ];
    diagText=lines.join('\n');
    q('diagPreview').value=diagText;q('diagCopy').disabled=false;q('diagDownload').disabled=false;
    q('diagState').textContent='Prévia pronta. Revise antes de copiar ou baixar.';
  }catch(x){q('diagState').textContent='Não foi possível gerar a prévia: '+x.message}
}
q('diagGenerate').onclick=buildSupportDiagnostic;
q('diagCopy').onclick=async function(){if(!diagText)return;try{await navigator.clipboard.writeText(diagText);q('diagState').textContent='Relatório copiado.'}catch(_){q('diagPreview').focus();q('diagPreview').select();document.execCommand('copy');q('diagState').textContent='Relatório copiado.'}};
q('diagDownload').onclick=function(){if(!diagText)return;var b=new Blob([diagText],{type:'text/plain;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=(diagId||'PU2PNY-DIAG')+'.txt';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},0)};
'''
anchor="q('refresh').onclick=load;"
if anchor not in e: raise SystemExit("expert JS anchor not found")
e=e.replace(anchor,js+"\n"+anchor,1)
expert.write_text(e)

# Translate every new UI string; no mixed-language fallback for the new surface.
l=lang.read_text()
lang_anchor="let language=localStorage.getItem('pu2pny-language')||'pt'"
if lang_anchor not in l: raise SystemExit("language insertion anchor not found")
extra = r'''Object.assign(D,{
"Suporte PU2PNY-OS":["PU2PNY-OS Support","Soporte PU2PNY-OS"],
"Gere uma prévia sanitizada antes de compartilhar. Nada é enviado automaticamente e nenhuma senha, token, API key ou segredo é incluído.":["Generate a sanitized preview before sharing. Nothing is sent automatically and no password, token, API key or secret is included.","Genere una vista previa sanitizada antes de compartir. Nada se envía automáticamente y no se incluye ninguna contraseña, token, clave API ni secreto."],
"Grupo de suporte PU2PNY-OS":["PU2PNY-OS support group","Grupo de soporte PU2PNY-OS"],
"Gerar prévia do relatório":["Generate report preview","Generar vista previa del informe"],
"A prévia aparecerá aqui depois da sua solicitação.":["The preview will appear here after you request it.","La vista previa aparecerá aquí después de solicitarla."],
"Copiar relatório":["Copy report","Copiar informe"],"Baixar .txt":["Download .txt","Descargar .txt"],
"Relatório ainda não gerado.":["Report not generated yet.","Informe aún no generado."],
"Cross-mode":["Cross-mode","Cross-mode"],"Estado nesta Alpha:":["Status in this Alpha:","Estado en esta Alpha:"],
"não habilitado automaticamente.":["not enabled automatically.","no habilitado automáticamente."],
"Transcoder necessário":["Transcoder required","Transcoder necesario"],"Não habilitado":["Not enabled","No habilitado"],
"O MMDVM-CrossMode atual usa MMDVM-Transcoder. Sem o hardware/vocoder correspondente, o PU2PNY-OS não anuncia conversão de áudio como funcional.":["The current MMDVM-CrossMode uses MMDVM-Transcoder. Without the corresponding hardware/vocoder, PU2PNY-OS does not claim audio conversion is functional.","El MMDVM-CrossMode actual usa MMDVM-Transcoder. Sin el hardware/vocoder correspondiente, PU2PNY-OS no anuncia la conversión de audio como funcional."],
"Gerando prévia local e sanitizada...":["Generating local sanitized preview...","Generando vista previa local y sanitizada..."],
"Prévia pronta. Revise antes de copiar ou baixar.":["Preview ready. Review it before copying or downloading.","Vista previa lista. Revísela antes de copiar o descargar."],
"Relatório copiado.":["Report copied.","Informe copiado."]
});
'''
l=l.replace(lang_anchor,extra+lang_anchor,1)
lang.write_text(l)

version.write_text("0.3.29-alpha\n")

# No cross-mode executable/service is introduced. This preserves the native protocol path.
for p in (
    root/"rootfs-overlay/usr/local/bin/MMDVM-CrossMode",
    root/"rootfs-overlay/etc/systemd/system/2pny-crossmode.service",
):
    if p.exists(): raise SystemExit(f"unexpected cross-mode runtime introduced: {p}")

# Protected protocol helpers must still be byte-identical to the approved source files.
pairs=[
 ("rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply","src/2pny-protocol-network-apply-all-0.3.20.py"),
 ("rootfs-overlay/usr/local/libexec/2pny-dmr-apply","src/2pny-protocol-network-apply-0.3.21.py"),
]
for staged,src in pairs:
    if (root/staged).read_bytes() != (repo/src).read_bytes():
        raise SystemExit(f"protected protocol file changed: {staged}")

subprocess.run(["gofmt","-w",str(main)],check=True)
print("PATCH_0329_OK")
