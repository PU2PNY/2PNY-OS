#!/usr/bin/env python3
"""Regression gates for PU2PNY-OS 0.3.18-alpha.

The source delta from 0.3.17 is deliberately constrained to:
1) app version;
2) native DStarGateway AMBE data directory.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def text(p): return (ROOT/p).read_text()

p17=text("src/2pny-protocol-network-apply-all-0.3.17.py")
p18=text("src/2pny-protocol-network-apply-all-0.3.18.py")
m17=text("src/2pnyd-main-0.3.17.go")
m18=text("src/2pnyd-main-0.3.18.go")

old_audio='audio_path="/usr/share/2pny/audio/dstar/"'
new_audio='audio_path="/usr/local/share/dstargateway.d/"'
assert old_audio in p17
assert new_audio in p18 and old_audio not in p18
assert p18 == p17.replace(old_audio,new_audio,1)

assert 'appVersion            = "0.3.17-alpha"' in m17
assert 'appVersion            = "0.3.18-alpha"' in m18
assert m18 == m17.replace('appVersion            = "0.3.17-alpha"',
                          'appVersion            = "0.3.18-alpha"',1)

# Preserve all focal D-Star behavior already implemented in 0.3.17.
for marker in (
    '"Module":"C" if proto=="DSTAR"',
    'Band=C',
    'ReflectorReconnect=Never',
    'ReloadTime=72',
    'LocalPort":"20011"',
    'GatewayPort":"20010"',
    'HBPort=20010',
    'Port=20011',
    'D-Star.Module local não confirmou C',
):
    assert marker in p18, marker
assert 'ReloadTimer=72' not in p18
assert 'ReflectorReconnect=Fixed' not in p18

# Preserve unique timezone request design unchanged from 0.3.17.
for marker in (
    '"timezone-request-"+requestID+".json"',
    '"timezone-result-"+requestID+".json"',
    'runTimezoneRequest(tz)',
):
    assert marker in m18, marker
tz=text("src/2pny-timezone-apply-0.3.17.py")
assert '["timedatectl","set-timezone",tz]' in tz
assert 'effective_timezone()' in tz
assert 'PathExistsGlob=/run/2pny/timezone-request-*.json' in text("src/2pny-timezone-apply-0.3.17.path")

# Preserve D-Star NETWORK->RF parser and runtime visibility code.
live=text("src/2pny-live-core-0.3.17.py")
station=text("src/2pny-station-worker-0.3.17.py")
hotspot=text("src/hotspot-0.3.17.html")
assert 'DSTAR_START_RE' in live and 'received (RF|network)' in live
assert 'last_command' in station
assert 'Comandos pelo rádio' in hotspot or 'I' in hotspot

print("TEST_0318_REGRESSIONS_OK")
