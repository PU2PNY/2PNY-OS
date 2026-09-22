#!/usr/bin/env python3
"""Focused regression gates for PU2PNY-OS 0.3.17-alpha."""
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]

def text(p): return (ROOT/p).read_text()

proto=text("src/2pny-protocol-network-apply-all-0.3.17.py")
station=text("src/2pny-station-worker-0.3.17.py")
hotspot=text("src/hotspot-0.3.17.html")
main=text("src/2pnyd-main-0.3.17.go")
tz=text("src/2pny-timezone-apply-0.3.17.py")
tzpath=text("src/2pny-timezone-apply-0.3.17.path")
tzsvc=text("src/2pny-timezone-apply-0.3.17.service")
prepare=text("ci/prepare-0.3.17-alpha.py")

# PROTO-024: local RF identity is C/C and the remote room stays independent.
assert '"Module":"C" if proto=="DSTAR"' in proto
assert 'Band=C' in proto
assert 'Reflector={reflector}' in proto
assert 'ReflectorReconnect=Never' in proto
assert 'ReflectorReconnect=Fixed' not in proto
assert 'LocalPort":"20011"' in proto
assert 'GatewayPort":"20010"' in proto
assert 'HBPort=20010' in proto
assert 'Port=20011' in proto
assert 'ReloadTime=72' in proto
assert 'ReloadTimer=72' not in proto
assert 'D-Star.Module local não confirmou C' in proto
# Selected remote module must still form the reflector target.
assert 'reflector=normalized[:6]+" "+module' in proto

# LIVE-017: feed the actual MMDVMHost D-Star network log form to the parser.
spec=importlib.util.spec_from_file_location("live0317",ROOT/"src/2pny-live-core-0.3.17.py")
live=importlib.util.module_from_spec(spec);spec.loader.exec_module(live)
s=live.LiveState()
ev=s.ingest("D-Star, received network header from M1ABC /ABCD to CQCQCQ via XLX026 D",ts=1000)
assert ev is not None
assert ev["protocol"]=="DSTAR"
assert ev["direction"]=="NETWORK"
assert ev["source"]=="M1ABC"
assert ev["target"]=="CQCQCQ"
assert ev["reflector"]=="XLX026 D"
assert ev["rssi"] is None and ev["ber"] is None
snap=s.snapshot()
assert snap["active"]["direction"]=="NETWORK"
assert snap["active"]["protocol"]=="DSTAR"

# End event closes the same NETWORK event; no RSSI is manufactured.
end=s.ingest("D-Star, received network end of transmission from M1ABC /ABCD to CQCQCQ, 2.0 seconds, 0% packet loss, BER: 0.0%",ts=1002)
assert end is not None and end["direction"]=="NETWORK"
assert end.get("rssi") is None
assert s.snapshot()["standby"] is True

# UI-032 and gateway evidence state.
for marker in ("Link command from","Unlink command issued via","last_command","last_command_target","link_state"):
    assert marker in station, marker
for marker in ("_______I","_______E","_______U","_______L","XLX026DL","REF030CL","CQCQCQ","stDstarLocal","stDstarCommand"):
    assert marker in hotspot, marker
for marker in ('"link_state": nr["link_state"]','"last_command": nr["last_command"]','"last_command_target": nr["last_command_target"]'):
    assert marker in main, marker

# The pinned gateway itself has Info/Echo/DTMF enabled in its application code;
# 0.3.17 relies on those native commands rather than a parallel implementation.
assert 'audio_path="/usr/share/2pny/audio/dstar/"' in proto

# SEC-024: unique request/result pair and effective timezone verification.
assert 'runTimezoneRequest' in main
assert '"timezone-request-"+requestID+".json"' in main
assert '"timezone-result-"+requestID+".json"' in main
assert 'res["request_id"]' in main
assert 'PathExistsGlob=/run/2pny/timezone-request-*.json' in tzpath
assert 'timezone-request-' in tz and 'timezone-result-' in tz
assert '["timedatectl","set-timezone",tz]' in tz
assert '["timedatectl","show","-p","Timezone","--value"]' in tz
assert 'if effective!=tz:' in tz
assert 'request_id=request_id' in tz
assert 'User=root' in tzsvc
assert 'ExecStart=/usr/local/sbin/2pny-timezone-apply' in tzsvc
assert 'ReadWritePaths=/run/2pny /etc/timezone' in tzsvc

# REL-010: 0.3.17 overlay is intentionally narrow.
for forbidden in (
    'src/2pny-network-switch-0.3.17',
    'src/2pny-aprs-0.3.17',
    'src/2pny-display-apply-0.3.17',
    'src/2pny-dmr',
    'src/direct-core',
):
    assert forbidden not in prepare, forbidden

# Representative frozen 0.3.16 baselines remain untouched in source.
dmr=text("src/2pny-protocol-network-apply-0.3.13.py")
rf=text("src/2pny-rf-apply-0.3.15")
net=text("src/2pny-network-switch-0.3.16")
aprs=text("src/2pny-aprs-0.3.16.py")
display=text("src/2pny-display-apply-0.3.16.py")
assert '[Log]\nDisplayLevel=1\nMQTTLevel=0' in dmr
assert 'Name=TGIF_Network' in dmr
assert 'RF_APPLY_OK' in rf
assert 'connection.autoconnect-retries 3' in net
assert 'rotate.aprs2.net' in aprs
assert 'if kind=="nextion_mmdvm":' in display

assert 'appVersion            = "0.3.17-alpha"' in main

print("TEST_0317_REGRESSIONS_OK")
