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
        if arch=='arm32':network_source=(root/'usr/local/sbin/2pny-network-core').read_text()
        for file in ('usr/local/sbin/2pny-network-core','usr/local/sbin/2pny-mdns-guard'):
            assert subprocess.run(['bash','-n',str(root/file)]).returncode==0,file
        for file in ('usr/local/sbin/2pny-station-worker','usr/local/sbin/2pny-display-core'):
            compile((root/file).read_bytes(),file,'exec')
        assert b'pu2pny64.local' in (root/'usr/share/2pny/wizard.html').read_bytes() if arch=='arm64' else b'pu2pny32.local' in (root/'usr/share/2pny/wizard.html').read_bytes()
print('TEST_511_OK')

# Planejamento dos cinco modos e rollback sem modificar o INI do MMDVMHost.
modes=module('mode511',ROOT/'runtime/5.11/mode.py')
with tempfile.TemporaryDirectory() as td:
    state=Path(td)/'state';state.mkdir();run=Path(td)/'run';run.mkdir();bins=Path(td)/'bin';bins.mkdir()
    modes.BASE,modes.RUN,modes.LIB,modes.BIN=state,run,ROOT/'runtime/5.11',bins
    (state/'mmdvm').mkdir();rf=state/'mmdvm/MMDVM-Host.ini'
    rf.write_text('[DMR Network]\nGatewayPort=62031\nLocalPort=62032\n[System Fusion Network]\nGatewayPort=4200\nLocalPort=3200\n')
    before=rf.read_bytes()
    (state/'hosts').mkdir();(state/'protocol-secrets').mkdir()
    for proto in ('YSF','NXDN','P25'):(state/'hosts'/(proto+'Hosts.json')).write_text(json.dumps({'reflectors':[{'designator':'9999','name':'fixture','ipv4':'192.0.2.1','port':42000}]}))
    (state/'protocol-profiles.json').write_text(json.dumps({'profiles':{'DMR':{'server_address':'example.invalid','server_port':62031,'network_kind':'BM'}}}))
    (state/'protocol-secrets/dmr.secret').write_text('fixture-secret')
    for mode,binary in modes.MODES.items():
        (state/'config.json').write_text(json.dumps({'protocol':'DMR' if mode.startswith('dmr') else 'YSF','callsign':'TEST123','dmr_id':'1234567'}))
        plan=modes.plan(mode,'9999');assert b'fixture-secret' not in plan['ini'] or mode=='ysf2dmr'
        assert b'Password=fixture-secret' in plan['ini'] if mode=='ysf2dmr' else True
        (bins/binary).write_bytes(b'fixture')
        if plan['gateway']:(bins/plan['gateway'][0]).write_bytes(b'fixture')
        calls=[]
        def control(*args):
            calls.append(args)
            return not (args[0]=='start' and args[1]=='2pny-cm@'+mode+'.service')
        try:modes.activate(mode,'9999',control=control,wait=lambda _:None)
        except RuntimeError:pass
        else:raise AssertionError('conversor que falha exige rollback')
        assert ('start',plan['original']) in calls
        assert not modes.readj(state/'special-mode.json')
        assert rf.read_bytes()==before

# Driver I2C incremental: empacotamento deve equivaler à implementação antiga bit a bit.
fixture_source=(ROOT/'ci/fixtures/5.03/2pny-display-core').read_text()
start=fixture_source.index('class I2CBase:');end=fixture_source.index('    def label(',start)
# Obter a função nova da própria aplicação do overlay em fixture, já validada acima.
ns2={'__file__':str(ROOT/'ci/test-5.10.py')};exec((ROOT/'ci/test-5.10.py').read_text().split('with tempfile.TemporaryDirectory() as td:')[0],ns2)
with tempfile.TemporaryDirectory() as td:
    root,binary=ns2['build_root'](td,'i2c','arm64');cp=ns2['patch510'](root,'arm64',binary);assert cp.returncode==0
    # O teste unitário extrai show_image do overlay a partir de uma fixture comum.
    patch=(ROOT/'ci/patch-image-5.11.py').read_text()
    marker="replace(core,s[start:end],";a=patch.index(marker)+len(marker);b=patch.index("\nreplace(core,",a)
    import ast
    expression=patch[a:b].strip();assert expression.endswith(')')
    body=ast.literal_eval('('+expression[:-1].strip()+')')
    space={};exec('def show_image(self,img):\n'+body,space)
    class Bus:
        calls=[]
        def write_i2c_block_data(self,addr,reg,data):self.calls.append((addr,reg,tuple(data)))
    class OLED:
        h=64;sh1106=False;Image=Image;addr=0x3c
        def __init__(self):self.bus=Bus();self.bus.calls=[];self.commands=[]
        def cmd(self,*args):self.commands.append(args)
    d=OLED();img=Image.new('1',(128,64));draw=ImageDraw.Draw(img);draw.rectangle((2,3,19,27),fill=1)
    space['show_image'](d,img);assert len(d.bus.calls)==64
    expected=[];pix=img.load()
    for page in range(8):
        data=[sum((1<<bit) if pix[x,page*8+bit] else 0 for bit in range(8)) for x in range(128)]
        for off in range(0,128,16):expected.append((0x3c,0x40,tuple(data[off:off+16])))
    assert d.bus.calls==expected
    d.bus.calls=[];space['show_image'](d,img);assert not d.bus.calls
    img.putpixel((127,63),1);space['show_image'](d,img);assert len(d.bus.calls)==8
print('TEST_511_MODE_I2C_OK')

nettest=module('netsim511',ROOT/'ci/network-simulation-5.11.py')
nettest.simulate(network_source)
