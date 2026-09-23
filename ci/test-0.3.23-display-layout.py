#!/usr/bin/env python3
"""Verify bounded Nextion commands and geometry without claiming RF/HMI tests."""
import importlib.util
import unittest.mock as mock
from pathlib import Path

source=Path(__file__).resolve().parents[1]/"src/2pny-display-core-0.3.21.py"
spec=importlib.util.spec_from_file_location("pny_display_layout",source)
display=importlib.util.module_from_spec(spec)
spec.loader.exec_module(display)

for width,height in ((320,240),(480,320),(800,480)):
    driver=display.Nextion("nextion_mmdvm",width=width,height=height)
    chunks=[]
    def publish(*args,**kwargs):
        chunks.append(kwargs["input"])
        return mock.Mock(returncode=0)
    with mock.patch.object(display.subprocess,"run",side_effect=publish), \
         mock.patch.object(display.time,"sleep"), \
         mock.patch.object(display,"read_network_status",return_value={}):
        cfg={"protocol":"DMR","callsign":"PU2PNY"}
        driver.render({"active":{},"internet":{}},cfg,{})
        driver.render({"active":{"mode":"rx","protocol":"DMR","source":"TEST","target":"TG 6","direction":"RF"},"internet":{}},cfg,{})
    assert chunks and max(map(len,chunks))<=240
    commands=b"".join(chunks).split(display.END)
    assert commands.count(b"cls 0")==2
    assert b"AGUARDANDO RF" in b"".join(commands)
    assert b"REDE ?" not in b"".join(commands)
    for command in commands:
        if not command.startswith(b"xstr "):continue
        x,y,w,h=(int(v) for v in command[5:].split(b",",4)[:4])
        assert 0<=x<width and 0<=y<height and x+w<=width and y+h<=height,(width,height,command)

print("DISPLAY_0323_LAYOUT_OK")
