#!/usr/bin/env python3
"""Offline 5.02 overlay. Never runs target binaries or changes RF configuration."""
import hashlib
import shutil
import sys
from pathlib import Path

root, binary, arch = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
repo = Path(__file__).resolve().parents[1]
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.01.002'
assert binary.is_file() and binary.stat().st_size > 1000000
assert ('ssid=pu2pny-'+arch[3:]) in (root/'usr/share/2pny/network/hostapd.template').read_text()

def replace(path, old, new):
    p = root/path
    text = p.read_text()
    assert text.count(old) == 1, (str(path), old[:70], text.count(old))
    p.write_text(text.replace(old, new, 1))

def install(source, destination, mode=0o755):
    p = root/destination
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo/source, p)
    p.chmod(mode)

shutil.copy2(root/'usr/local/bin/2pnyd', root/'usr/local/bin/2pnyd.pre-5.02')
shutil.copyfile(binary, root/'usr/local/bin/2pnyd')
(root/'usr/local/bin/2pnyd').chmod(0o755)
install('runtime/5.02/diagnostics.py', 'usr/local/libexec/pu2pny/diagnostics-502.py')
install('runtime/5.02/reset.py', 'usr/local/libexec/pu2pny/reset-mmdvm-502.py')
install('runtime/display/adapter.py', 'usr/local/libexec/pu2pny/display/adapter.py')
install('runtime/5.02/oled.py', 'usr/local/libexec/pu2pny/oled-502.py')
replace('usr/local/sbin/2pny-display-core',
        'cadence=int(now) if active else int(now//60)',
        'cadence=int(now) if active else (int(now//4) if kind=="oled" else int(now//60))')
replace('usr/local/sbin/2pny-display-core', 'if __name__=="__main__":main()',
        'if __name__=="__main__":\n'
        '    import importlib.util\n'
        '    _spec=importlib.util.spec_from_file_location("oled502","/usr/local/libexec/pu2pny/oled-502.py")\n'
        '    _oled=importlib.util.module_from_spec(_spec)\n'
        '    _spec.loader.exec_module(_oled)\n'
        '    OLED.render=_oled.render\n'
        '    main()')

service = root/'etc/systemd/system/2pny-reset-mmdvm.service'
service.write_text('''[Unit]
Description=PU2PNY explicit MMDVM software reset without erasing configuration
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /usr/local/libexec/pu2pny/reset-mmdvm-502.py
TimeoutStartSec=18
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/run/2pny
''')
watch = root/'etc/systemd/system/2pny-reset-mmdvm.path'
watch.write_text('''[Unit]
Description=PU2PNY explicit Expert reset request
[Path]
PathChanged=/run/2pny/reset-mmdvm-request.json
Unit=2pny-reset-mmdvm.service
[Install]
WantedBy=multi-user.target
''')
link = root/'etc/systemd/system/multi-user.target.wants/2pny-reset-mmdvm.path'
assert not link.exists()
link.symlink_to('../2pny-reset-mmdvm.path')

# Correct the proven legacy OLED misclassification without touching the approved Nextion path.
legacy = 'usr/local/sbin/2pny-display-apply.pre-5.00.002'
replace(legacy,
        'if d.get("class")=="nextion":kind="nextion"',
        'if d.get("class")=="oled" or str(d.get("address") or "").lower() in ("0x3c","0x3d"):kind="oled"\n'
        'elif d.get("class")=="lcd" or str(d.get("address") or "").lower() in ("0x27","0x3f"):kind="lcd"\n'
        'elif d.get("class")=="nextion":kind="nextion"')

identity = '<div class="notice" id="identity502"><span>Indicativo</span>: <b id="callsign502">—</b> · Radio ID: <b id="radioid502">—</b></div>'
replace('usr/share/2pny/hotspot.html', '<section class="section" id="protocols">', '<section class="section" id="protocols">'+identity)
replace('usr/share/2pny/hotspot.html', "cfg=await PNY.getj('/api/config').catch(function(){return{}});",
        "cfg=await PNY.getj('/api/config').catch(function(){return{}});\n"
        "PNY.q('callsign502').textContent=cfg.callsign||'—';PNY.q('radioid502').textContent=cfg.dmr_id||'—';")

expert = '''<section class="section"><article class="card"><h2>Reset MMDVM</h2>
<p id="resetHelp502"></p><button class="btn danger" id="reset502">Reset MMDVM</button>
<a class="btn" id="fullReport502" href="/api/diagnostics/full">Relatório completo</a><p id="resetResult502"></p></article></section>'''
replace('usr/share/2pny/expert.html', '</main>', expert+'</main>')
script = '''<script>
(function(){
var lang=String(document.documentElement.lang||'pt').slice(0,2),en=lang==='en',es=lang==='es';
document.getElementById('resetHelp502').textContent=en?'Restarts MMDVM software in standby; preserves configuration.':es?'Reinicia MMDVM en espera; conserva la configuración.':'Reinicia o software MMDVM em standby; preserva as configurações.';
document.getElementById('fullReport502').textContent=en?'Full diagnostic report':es?'Informe completo':'Relatório completo';
document.getElementById('reset502').onclick=async function(){
 if(!confirm(en?'Restart MMDVM now?':es?'¿Reiniciar MMDVM ahora?':'Reiniciar o MMDVM agora?'))return;
 this.disabled=true;var status=document.getElementById('resetResult502');status.textContent=en?'Please wait…':es?'Espere…':'Aguarde…';
 try{await PNY.getj('/api/expert/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmation:'RESET MMDVM'})},25000);status.textContent=en?'Software restarted. Verify the radio.':es?'Software reiniciado. Verifique el radio.':'Software reiniciado. Verifique o rádio.'}
 catch(e){status.textContent=e.message}finally{this.disabled=false}
};
document.getElementById('errorDownload').onclick=function(){location.href='/api/diagnostics/full'};
})();
</script>'''
replace('usr/share/2pny/expert.html', '</body>', script+'</body>')

internet = root/'usr/share/2pny/internet.html'
text = internet.read_text()
assert text.count("op.done(st.message||'Rede Wi‑Fi 1 conectada.');") == 1
text = text.replace("PNY.q('wifiPrimaryManual').value='';load();return", "PNY.q('wifiPrimaryManual').value='';location.replace('http://pu2pny.local/internet');return", 1)
text = text.replace("location.replace('/dashboard')", "location.replace('http://pu2pny.local/internet')")
internet.write_text(text)

# Slow only background summary refreshes; live SSE and control/health checks are untouched.
for name in ('expert.html', 'internet.html', 'hotspot.html', 'system.html'):
    p = root/'usr/share/2pny'/name
    text = p.read_text().replace('if(!document.hidden)load()},5000)', 'if(!document.hidden)load()},15000)')
    p.write_text(text)
(root/'etc/2pny/version').write_text('5.02.000\n')
print('PATCH_502_OFFLINE_OK', arch)
