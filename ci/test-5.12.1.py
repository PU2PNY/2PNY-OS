#!/usr/bin/env python3
"""5.12.001 software gates: protected Nextion/RF bytes, UI, OLED/LCD and Expert."""
import importlib.util
import json
import shutil
import tempfile
import time
from pathlib import Path
from PIL import Image,ImageDraw

REPO=Path(__file__).resolve().parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,REPO/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

patch=module('overlay5121','ci/patch-image-5.12.1.py')
oled=module('oled5121','runtime/5.12.1/oled.py')
lcd=module('lcd5121','runtime/5.12.1/lcd.py')
expert=module('expert5121','runtime/5.12.1/expert-cmd.py')

cfg={'callsign':'TEST123','dmr_id':'1234567','rx_hz':439500000,'protocol':'DMR','server_name':'XLX026'}
tx={'active':{'source':'N0CALL','protocol':'DMR','slot':2,'direction':'RF','mode':'RX',
              'started_unix_ms':(time.time()-21)*1000,'target':'TG 6','ber':0.4,'rssi':-85}}
n={'default_ip':'192.0.2.33','uplink_type':'wifi'}
idle64=oled.pages({},cfg,{'temperature':48},network=n,height=64)
tx64=oled.pages(tx,cfg,{'temperature':48},network=n,height=64)
assert 'PU2PNY-OS' in idle64[0][0] and any('TEST123' in x[0] for x in idle64)
assert any('192.0.2.33' in x[0] for x in idle64)
assert any('N0CALL' in x[0] for x in tx64)
assert any('00:21' in x[0] for x in tx64)
assert any('BER' in x[0] and 'RSSI' in x[0] for x in tx64)
oled32=oled.pages(tx,cfg,{},network=n,height=32,monotonic=0)
assert len(oled32)==2 and 'N0CALL' in oled32[1][0]
assert oled.pages({},cfg,{},network=n,height=32,monotonic=0)[0][0]=='PU2PNY-OS'
frames=lcd.rows_for({},cfg,{'temperature':42},20,4,network=n)
assert frames[0][0]=='PU2PNY-OS' and any('192.0.2.33' in x for x in frames[1])
frames=lcd.rows_for(tx,cfg,{},20,4,network=n,now=time.time())
assert any('N0CALL' in line for line in frames[0])
assert any('BER' in line for line in frames[0])
assert all(len(line)<=20 for page in frames for line in page)

# Screen rendering is a separate read-only path; no original Nextion writer is touched.
for h in (32,64):
    class MockDisplay:
        Image=Image
        ImageDraw=ImageDraw
        def __init__(self):self.h=h;self.frames=[]
        def show_image(self,im):self.frames.append(im.copy())
    d=MockDisplay()
    assert oled.render(d,tx,cfg,{'temperature':48})==(0,1)
    assert d.frames[-1].size==(128,h)
    before=len(d.frames)
    oled.render(d,tx,cfg,{'temperature':48})
    assert len(d.frames)==before, 'unchanged OLED frames must not generate I2C writes'
    oled.render(d,{},cfg,{'temperature':48})
    assert len(d.frames)==before+1

assert expert.LIMIT>=100000
assert 'panel' in expert.COMMANDS and 'gateways' in expert.COMMANDS
assert expert.run('bash -c id')['ok'] is False
sample='{"Password":"supersecret","psk":"abc123","server":"example"}'
red=expert.redact(sample)
assert 'supersecret' not in red and 'abc123' not in red
assert 'example' in red

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'etc/2pny').mkdir(parents=True)
    (root/'etc/2pny/version').write_text('5.12.000\n')
    for rel,baseline in {
        'usr/local/libexec/pu2pny/oled-502.py':'runtime/5.11/oled.py',
        'usr/local/libexec/pu2pny/lcd-504.py':'runtime/5.05/lcd.py',
        'usr/local/libexec/pu2pny/expert-cmd-504.py':'runtime/5.10/expert-cmd.py'
    }.items():
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/baseline,p)
    public=root/'usr/share/2pny';public.mkdir(parents=True)
    html='<html><header><nav class="nav" id="mainNav"></nav></header><main></main></html>'
    for name in ('dashboard','expert','system','hotspot','internet'):
        p=public/(name+'.html')
        text=html
        if name=='system':text=text.replace('<main>','<main><h2>Relógio</h2><style>article:has(#localClock),#clockLocal,#clockUTC,#pnyClock,.top .clock{display:none!important}</style>Operação do rádio, voz, energia e estado do sistema.')
        p.write_text(text)
    sentinel=root/'usr/local/bin/NextionDriver-pu2pny'
    sentinel.parent.mkdir(parents=True,exist_ok=True)
    sentinel.write_bytes(b'ON7LDS_APPROVED_BYTE_IDENTICAL')
    changes=patch.apply(root)
    assert sentinel.read_bytes()==b'ON7LDS_APPROVED_BYTE_IDENTICAL'
    assert (root/'etc/2pny/version').read_text().strip()=='5.12.001'
    assert 'PU2PNY-OS' not in (public/'dashboard.html').read_text() or '/expert' in (public/'dashboard.html').read_text()
    assert '/expert' in (public/'dashboard.html').read_text()
    assert '/dashboard' in (public/'expert.html').read_text()
    assert 'display:none!important' not in (public/'system.html').read_text()
    for change in changes:
        assert (root/change).is_file()
    assert changes==set(changes)
    try:patch.apply(root)
    except AssertionError:pass
    else:raise AssertionError('double-apply was accepted')

print('TEST_5121_UI_EXPERT_OLED_LCD_BASELINE_PASS')
