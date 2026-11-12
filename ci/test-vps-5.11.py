#!/usr/bin/env python3
"""Integração Linux de watchers reais e API, com diretórios e gateways simulados.

Requer root e systemd na VPS de teste. Nunca instala unidades 2pny reais nem
chama gateways/RF; todo systemctl do aplicativo é simulado no PATH privado.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
GO=Path(sys.argv[1]).resolve()
assert os.geteuid()==0 and GO.is_file()
PREFIX='pu2pny511-lab-'
UNITS=[PREFIX+k+'.'+ext for k in ('voice','mode') for ext in ('path','service')]
assert not any((Path('/run/systemd/system')/u).exists() for u in UNITS),'unidades de teste já presentes'

def ctl(*args):return subprocess.run(['systemctl',*args],check=True,capture_output=True,text=True)

with tempfile.TemporaryDirectory(prefix='pu2pny511-vps-') as td:
    root=Path(td);state=root/'state';run=root/'run';mock=root/'bin';backend=root/'backend'
    for p in (state,run,mock):p.mkdir()
    (state/'provisioned').touch();(state/'config.json').write_text(json.dumps({'protocol':'YSF','callsign':'TEST123','dmr_id':'1234567'}))
    for proto,file in (('dmr','DMRGateway'),('p25','P25Gateway'),('nxdn','NXDNGateway')):
        p=state/proto;p.mkdir();(p/(file+'.ini')).write_text('[Voice]\nEnabled=1\nLanguage=English_UK\n')
    (state/'dstar').mkdir();(state/'dstar/DStarGateway.ini').write_text('[Paths]\nData=/usr/local/share/dstargateway.d/\n')
    (state/'mmdvm').mkdir();(state/'mmdvm/MMDVM-Host.ini').write_text('[System Fusion Network]\nGatewayPort=4200\nLocalPort=3200\n')
    (state/'protocol-secrets').mkdir();(state/'protocol-secrets/dmr.secret').write_text('fixture-secret')
    (state/'protocol-profiles.json').write_text(json.dumps({'profiles':{'DMR':{'server_address':'example.invalid','server_port':62031,'network_kind':'BM'}}}))
    (mock/'YSF2DMR').touch()
    subprocess.run([sys.executable,str(REPO/'ci/prepare-5.11-backend.py'),str(backend),'arm64'],check=True,stdout=subprocess.DEVNULL)
    port_socket=socket.socket();port_socket.bind(('127.0.0.1',0));port=port_socket.getsockname()[1];port_socket.close()
    # Alterar apenas caminhos e nomes de unidades na cópia descartável de teste.
    for p in backend.glob('*.go'):
        text=p.read_text().replace('/var/lib/2pny',str(state)).replace('/run/2pny',str(run)).replace('0.0.0.0:80',f'127.0.0.1:{port}')
        text=text.replace('2pny-voice-apply.service',PREFIX+'voice.service').replace('2pny-mode-apply.service',PREFIX+'mode.service')
        p.write_text(text)
    env=dict(os.environ,GO111MODULE='off')
    subprocess.run([str(GO),'build','-o',str(root/'backend-native'),'.'],cwd=backend,env=env,check=True)
    script=mock/'systemctl'
    script.write_text('''#!/usr/bin/env python3
import os,subprocess,sys
from pathlib import Path
r=Path(os.environ['PNY_RUN']);args=sys.argv[1:]
with (r/'calls').open('a') as f:f.write(' '.join(args)+'\\n')
if args[0]=='is-active':sys.exit(0 if args[-1].endswith('.path') or args[-1]=='2pny-dmrgateway.service' or args[-1]=='2pny-mmdvmhost.service' else 1)
if args[0]=='restart' and args[-1]=='2pny-dmrgateway.service':
 if (r/'fail-voice').exists():sys.exit(1)
 sys.exit(subprocess.run([sys.executable,os.environ['VOICE_HELPER'],'--only','dmr','--no-restart']).returncode)
if args[0]=='start' and args[-1]=='2pny-cm@ysf2dmr.service':sys.exit(1)
sys.exit(0)
''');script.chmod(0o755)
    env=dict(os.environ,PATH=str(mock)+':'+os.environ['PATH'],PNY_STATE=str(state),PNY_RUN=str(run),PNY_LIB=str(REPO/'runtime/5.11'),PNY_BIN=str(mock),VOICE_HELPER=str(REPO/'runtime/5.11/voice-apply.py'),PYTHONDONTWRITEBYTECODE='1')
    proc=None
    try:
        for kind,helper in (('voice','voice-apply.py'),('mode','mode.py')):
            service=Path('/run/systemd/system')/(PREFIX+kind+'.service')
            settings='\n'.join('Environment='+k+'='+env[k] for k in ('PATH','PNY_STATE','PNY_RUN','PNY_LIB','PNY_BIN','VOICE_HELPER','PYTHONDONTWRITEBYTECODE'))
            service.write_text(f'[Unit]\nDescription=Teste isolado PU2PNY 5.11\n[Service]\nType=oneshot\n{settings}\nExecStart=/usr/bin/python3 {REPO}/runtime/5.11/{helper} --request\nTimeoutStartSec=120\n')
            path=Path('/run/systemd/system')/(PREFIX+kind+'.path')
            path.write_text(f'[Unit]\nDescription=Watcher isolado PU2PNY 5.11\n[Path]\nPathExists={run}/{kind}-request.json\nUnit={PREFIX}{kind}.service\n')
        ctl('daemon-reload')
        for kind in ('voice','mode'):ctl('start',PREFIX+kind+'.path')
        log=(root/'backend.log').open('w');proc=subprocess.Popen([str(root/'backend-native')],env=env,stdout=log,stderr=log)
        base=f'http://127.0.0.1:{port}'
        for _ in range(100):
            try:urllib.request.urlopen(base+'/api/voice/settings',timeout=.3).read();break
            except (OSError,urllib.error.URLError):time.sleep(.05)
        def post(path,payload):
            request=urllib.request.Request(base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Origin':base})
            try:
                with urllib.request.urlopen(request,timeout=100) as r:return r.status,json.load(r)
            except urllib.error.HTTPError as exc:return exc.code,json.load(exc)
        settings={'dmr':False,'dstar':False,'p25':False,'nxdn':False,'hourly':False,'language':'pt'}
        code,out=post('/api/voice/settings',settings);assert code==200 and out.get('ok'),(code,out)
        assert 'Enabled=0' in (state/'dmr/DMRGateway.ini').read_text()
        prior=(state/'dmr/DMRGateway.ini').read_bytes();prior_settings=(state/'voice-settings.json').read_bytes()
        (run/'fail-voice').touch();settings['dmr']=True
        code,out=post('/api/voice/settings',settings);assert code==503 and out.get('ok') is False,(code,out)
        assert (state/'dmr/DMRGateway.ini').read_bytes()==prior
        assert (state/'voice-settings.json').read_bytes()==prior_settings
        rf=(state/'mmdvm/MMDVM-Host.ini').read_bytes()
        code,out=post('/api/mode/settings',{'mode':'ysf2dmr','destination':'9999'})
        assert code==503 and out.get('ok') is False,(code,out)
        assert json.loads((state/'special-mode.json').read_text())=={}
        assert 'start 2pny-ysfgateway.service' in (run/'calls').read_text()
        assert rf==(state/'mmdvm/MMDVM-Host.ini').read_bytes()
        print('VPS_511_REAL_PATH_API_VOICE_ROLLBACK_MODE_ROLLBACK_PASS')
    finally:
        if proc:proc.terminate();proc.wait(timeout=5)
        for u in UNITS:subprocess.run(['systemctl','stop',u],check=False,capture_output=True)
        for u in UNITS:(Path('/run/systemd/system')/u).unlink(missing_ok=True)
        ctl('daemon-reload')
