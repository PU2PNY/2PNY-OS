#!/usr/bin/env python3
"""DISPLAY-053: validate new values and preserve the 5.02 OLED rows."""
import importlib.util,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('runtime/5.02/oled.py','old502');new=load('runtime/5.03/oled.py','new503')
cfg={'callsign':'PU2PNY','dmr_id':'7240000','protocol':'DMR'}
net={'default_ip':'192.0.2.10','uplink_type':'wifi'}
for live in ({}, {'active':{'source':'PU2ABC','target':'TG724','protocol':'DMR','slot':2,'ber':0.3}}):
    a=old.rows(live,cfg,net,now=1700000000)
    b=new.rows(live,cfg,net,now=1700000000)
    assert b[:len(a)]==a,(a,b)
    assert any('pu2pny.local' in item for item in b)
    assert any(item.startswith('CPU:') for item in b)
    assert any(item.startswith('Uptime:') for item in b)
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'metric'
    assert new.cpu_temperature(p)=='-' and new.system_uptime(p)=='-'
    p.write_text('42500\n');assert new.cpu_temperature(p)=='42.5 C'
    p.write_text('3661.1 0.0\n');assert new.system_uptime(p)=='1h 1m'
print('TEST_DISPLAY_053_OLED_FIELDS_OK')
