#!/usr/bin/env python3
"""0.3.30 display-only regression tests. No RF/HW claims are made."""
import importlib.util, unittest.mock as mock
from pathlib import Path

repo=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,repo/path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

core=load("pny_display_0330","src/2pny-display-core-0.3.30.py")
det=load("pny_detector_0330","src/2pny-display-detector-0.3.30.py")
chunks=[]
def publish(*args,**kwargs):
    if "input" in kwargs: chunks.append(kwargs["input"])
    return mock.Mock(returncode=0)

driver=core.Nextion("nextion_mmdvm",width=320,height=240)
cfg={"protocol":"DMR","callsign":"PU2PNY"}
with mock.patch.object(core.subprocess,"run",side_effect=publish), \
     mock.patch.object(core.time,"sleep"), \
     mock.patch.object(core,"read_network_status",return_value={}):
    with mock.patch.object(core,"display_hm",return_value="12:00"), mock.patch.object(core.time,"time",return_value=1000):
        driver.render({"active":{},"internet":{}},cfg,{})
    first=b"".join(chunks); assert first.count(b"cls 0"+core.END)==1
    chunks.clear()
    with mock.patch.object(core,"display_hm",return_value="12:00"), mock.patch.object(core.time,"time",return_value=1000):
        driver.render({"active":{},"internet":{}},cfg,{})
    assert chunks==[], "unchanged standby must not be rewritten"
    with mock.patch.object(core,"display_hm",return_value="12:01"), mock.patch.object(core.time,"time",return_value=1000):
        driver.render({"active":{},"internet":{}},cfg,{})
    changed=b"".join(chunks); assert b"cls 0" not in changed and b"12:01" in changed
    chunks.clear()
    rx={"active":{"mode":"rx","protocol":"DMR","source":"TEST","target":"TG 6","direction":"RF","started_unix_ms":999000},"internet":{}}
    with mock.patch.object(core,"display_hm",return_value="12:01"), mock.patch.object(core.time,"time",return_value=1000):
        driver.render(rx,cfg,{})
    transition=b"".join(chunks); assert transition.count(b"cls 0"+core.END)==1
    chunks.clear()
    with mock.patch.object(core,"display_hm",return_value="12:01"), mock.patch.object(core.time,"time",return_value=1001):
        driver.render(rx,cfg,{})
    incremental=b"".join(chunks); assert b"cls 0" not in incremental and b"00:02" in incremental
    chunks.clear()
    tx={"active":{"mode":"tx","protocol":"DMR","source":"PU2PNY","target":"TG 6","direction":"RF","started_unix_ms":829000},"internet":{}}
    with mock.patch.object(core,"display_hm",return_value="12:01"), mock.patch.object(core.time,"time",return_value=1000):
        driver.render(tx,cfg,{})
    assert b"cls 0"+core.END in b"".join(chunks)
    chunks.clear()
    with mock.patch.object(core,"display_hm",return_value="12:01"), mock.patch.object(core.time,"time",return_value=1001):
        driver.render(tx,cfg,{})
    assert b"cls 0" not in b"".join(chunks)
    assert chunks and max(map(len,chunks))<=240

sample=b"comok,1,NX4832K035_011R,99,61488,123456,33554432\xff\xff\xff"
info=det.parse_connect(sample)
assert info and info["model"]=="NX4832K035_011R"
assert info["resolution"]=="480x320" and info["size_inch"]=="3.5"
assert info["firmware_version"]=="99" and info["mcu_code"]=="61488"
assert info["serial_number"]=="123456" and info["flash_size_bytes"]==33554432
assert info["hmi_layout"]=="unknown" and info["hardware_identified"] is True

apply=(repo/"src/2pny-display-apply-0.3.30.py").read_text()
assert "if requested not in (9,0,2,3)" in apply
assert "Conflito de writer" in apply
html=(repo/"src/display-0.3.30.html").read_text()
for token in ('value="pu2pny-modern-v2"','value="mmdvmhost-native"','ScreenLayout 0','ScreenLayout 2','ScreenLayout 3','Modelo físico não identifica o HMI/layout'):
    assert token in html
assert "NextionDriver/L3 HS" in html
print("DISPLAY_0330_INCREMENTAL_OK")
print("DISPLAY_0330_COMOK_METADATA_OK")
print("DISPLAY_0330_FALLBACK_OK")
