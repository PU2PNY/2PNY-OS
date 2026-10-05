#!/usr/bin/env python3
"""Display-only candidate contract for 0.3.31.114.

This intentionally revalidates the 0.3.30 display implementation instead of
rewriting working code. It makes no HW claim.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
core=(ROOT/'src/2pny-display-core-0.3.30.py').read_text()
det=(ROOT/'src/2pny-display-detector-0.3.30.py').read_text()
apply=(ROOT/'src/2pny-display-apply-0.3.30.py').read_text()
html=(ROOT/'src/display-0.3.30.html').read_text()

# DISPLAY-024/020: real Nextion identity comes from connect/comok; HMI remains
# a separate unknown state unless a real marker is read.
for token in ('nextion_command(fd,"connect"', 'find("comok")', '"hmi_layout":"unknown"', '"physical_confirmed":True'):
    assert token in det, token
assert 'if modem and item["realpath"]==modem:continue' in det
assert 'host/display-in' in det and 'host/display-out' in det

# One writer only. Native MMDVMHost and PU2PNY Display Core are mutually exclusive.
for token in ('pu2pny-modern-v2','mmdvmhost-native','Conflito de writer','ctl("disable","--now",CORE)','patch_modern_transport()'):
    assert token in apply, token

# Incremental rendering: clear only on page transition and suppress identical fields.
assert 'transition=page!=self.last_page' in core
assert 'if transition:' in core and 'out.append("cls 0")' in core
assert 'self.command_cache.get(key)==c' in core
assert 'if len(frame)>240' in core

# Fallbacks exposed without silently identifying HMI by physical model.
for token in ('ScreenLayout 0','ScreenLayout 2','ScreenLayout 3','Modelo físico não identifica o HMI/layout'):
    assert token in html, token

# No automatic TFT/HMI flashing is introduced by these runtime components.
for text,name in ((det,'detector'),(core,'core'),(apply,'apply')):
    lowered=text.lower()
    assert 'nextion_upload' not in lowered, name
    assert 'flash_tft' not in lowered, name
    assert not re.search(r'\b(?:upload|flash)\s*\([^\n]*\.tft', lowered), name

print('PASS: COMOK physical detection is explicit')
print('PASS: physical model and HMI identity are separated')
print('PASS: exactly one logical Nextion writer is selected')
print('PASS: Nextion rendering is incremental')
print('PASS: G4KLX/ON7LDS native fallbacks remain available')
print('PASS: no automatic TFT/HMI flashing path in candidate runtime')
