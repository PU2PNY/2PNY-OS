#!/usr/bin/env python3
"""Testes 5.11: EOF/CPU, OLED/I2C, voz/rollback, Direct autenticado e overlay."""
import importlib.util
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

f=module('followers511',ROOT/'runtime/5.11/followers.py')
follower=f.Followers({'journal':[sys.executable,'-c','print("line")']})
try:
    assert follower.select(1)[0][0].fileobj.readline()=='line'
    follower.select(1)  # EOF: descritor removido
    assert not follower.selector.get_map()
    start=time.monotonic();cpu=time.process_time()
    for _ in range(4):assert follower.select(.05)==[]
    assert time.monotonic()-start>=.18
    assert time.process_time()-cpu<.05, 'EOF não pode ocupar CPU'
    assert follower.items['journal']['delay']==10
finally:follower.close()

from PIL import Image,ImageDraw,ImageFont
m=module('oled511',ROOT/'runtime/5.11/oled.py')
OUT=ROOT/'test-output/5.11';OUT.mkdir(parents=True,exist_ok=True)
for height in (32,64):
    class Display:
        h=height
        Image=Image
        ImageDraw=ImageDraw
        shown=[]
        def show_image(self,img):self.shown.append(img)
    d=Display();live={'active':{'source':'TEST123','protocol':'DMR','mode':'rx','slot':2,'target':'TG 9','started_unix_ms':time.time()*1000,'ber':0.4}}
    cfg={'protocol':'DMR','callsign':'TEST456','server_name':'servidor de teste'}
    m.render(d,live,cfg,{})
    assert d.shown[-1].size==(128,height)
    d.shown[-1].save(OUT/f'oled-{height}-rx.png')
    m.render(d,{},cfg,{})
    d.shown[-1].save(OUT/f'oled-{height}-idle.png')
    count=len(d.shown);m.render(d,{},cfg,{})
    assert len(d.shown)==count,'repouso não pode redesenhar'

v=module('voice511',ROOT/'runtime/5.11/voice-apply.py')
with tempfile.TemporaryDirectory() as td:
    state=Path(td)
    for proto,path in v.FILES.items():
        p=state/path;p.parent.mkdir(parents=True)
        p.write_text('[Paths]\nData=/usr/local/share/dstargateway.d/\n[Other]\nPassword=fixture\n' if proto=='dstar' else '[Voice]\nEnabled=1\nLanguage=English_UK\n[Other]\nPassword=fixture\n')
    originals={p:(state/path).read_bytes() for p,path in v.FILES.items()}
    settings={p:False for p in v.FILES};settings['language']='pt'
    assert len(v.apply(state,settings,restart=False))==4
    assert b'dstar-off/' in (state/v.FILES['dstar']).read_bytes()
    assert b'Language=Portugues' in (state/v.FILES['dmr']).read_bytes()
    assert all(b'Password=fixture' in (state/path).read_bytes() for path in v.FILES.values())
    v.apply(state,{p:True for p in v.FILES},restart=False)
    before={p:(state/path).read_bytes() for p,path in v.FILES.items()}
    try:v.apply(state,settings,ctl=lambda *args: args[0]!='restart')
    except RuntimeError:pass
    else:raise AssertionError('falha de restart deveria causar rollback')
    assert before=={p:(state/path).read_bytes() for p,path in v.FILES.items()}

g=module('group511',ROOT/'runtime/5.11/direct-group.py')
code=secrets.token_urlsafe(24)
a,b=g.Channel(code),g.Channel(code)
raw=a.pack(b'hello');assert b.unpack(raw)==b'hello'
for bad in (raw,raw[:-1]+bytes([raw[-1]^1])):
    try:b.unpack(bad)
    except Exception:pass
    else:raise AssertionError('replay/adulteração aceito')
assert g.decode(g.encode({b'q':b'get_peers',b'a':{b'x':1}}))=={b'q':b'get_peers',b'a':{b'x':1}}
radioa=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);radioa.bind(('127.0.0.1',0));radioa.settimeout(1)
radiob=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);radiob.bind(('127.0.0.1',0));radiob.settimeout(1)
a=g.Group(code,('127.0.0.1',0),('127.0.0.1',0),radioa.getsockname(),[])
b=g.Group(code,('127.0.0.1',0),('127.0.0.1',0),radiob.getsockname(),[])
try:
    a.add_peer(b.sock.getsockname(),public=False)
    assert a.status()['peers'][0]['state']=='procurando'
    for _ in range(6):a.step(.01);b.step(.01)
    assert a.status()['peers'][0]['state']=='conectado P2P'
    frame=b'DMRD'+bytes(range(51))
    radioa.sendto(frame,a.radio.getsockname())
    for _ in range(4):a.step(.01);b.step(.01)
    assert radiob.recvfrom(256)[0]==frame
    radiob.sendto(b'DMRP',b.radio.getsockname());b.step(.01)
    assert radiob.recvfrom(256)[0]==b'DMRP'
finally:a.close();b.close();radioa.close();radiob.close()

# Reprodução da cadeia publicada. Fixtures isoladas; sem tocar o hardware do host.
ns={'__file__':str(ROOT/'ci/test-5.10.py')}
src=(ROOT/'ci/test-5.10.py').read_text().split('with tempfile.TemporaryDirectory() as td:')[0]
exec(compile(src,'fixtures509','exec'),ns)
for arch in ('arm32','arm64'):
    with tempfile.TemporaryDirectory() as td:
        binary=Path(td)/'binary';binary.write_bytes(b'0'*1_200_000)
        root,binary=ns['build_root'](td,'r',arch)
        core=Path(td)/'core';core.write_bytes(ns['fake_elf'](1,40))
        cp=ns['patch510'](root,arch,binary,*([core] if arch=='arm32' else []))
        assert cp.returncode==0,cp.stderr
        for src,dst in [('wifi-choice','etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice'),('direct.html','usr/share/2pny/direct.html'),('network-switch','usr/local/sbin/2pny-network-switch'),('firstboot','usr/local/sbin/2pny-firstboot'),('wifi-profiles','usr/local/sbin/2pny-wifi-profiles')]:
            path=root/dst;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/'ci/fixtures/5.11'/src).read_bytes())
        if arch=='arm64':
            wiz=root/'usr/share/2pny/wizard.html';wiz.write_text(wiz.read_text().replace('pu2pny32.local','pu2pny.local'))
        (root/'var/lib/2pny').mkdir(parents=True,exist_ok=True)
        timer=root/'etc/systemd/system/2pny-hostfiles-update.timer'
        timer.write_text('[Timer]\nOnBootSec=5min\nPersistent=true\n')
        cp=subprocess.run([sys.executable,str(ROOT/'ci/patch-image-5.11.py'),str(root),arch,str(binary)],capture_output=True,text=True)
        assert cp.returncode==0,(arch,cp.stderr)
        assert (root/'etc/2pny/version').read_text().strip()=='5.11.000'
        for file in ('usr/local/sbin/2pny-network-core','usr/local/sbin/2pny-mdns-guard'):
            assert subprocess.run(['bash','-n',str(root/file)]).returncode==0,file
        for file in ('usr/local/sbin/2pny-station-worker','usr/local/sbin/2pny-display-core'):
            compile((root/file).read_bytes(),file,'exec')
        assert b'pu2pny64.local' in (root/'usr/share/2pny/wizard.html').read_bytes() if arch=='arm64' else b'pu2pny32.local' in (root/'usr/share/2pny/wizard.html').read_bytes()
print('TEST_511_OK')
