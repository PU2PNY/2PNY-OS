#!/usr/bin/env python3
"""Reconstruct the 5.07 backend; read the clock from files, derive Wi-Fi % from dBm, serve /brand/ (CLOCK-058, UI-058).
Second argument `arm32` is passed through to the 5.07 step (pu2pny32.local)."""
from pathlib import Path
import re
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2] if len(sys.argv) > 2 else 'arm64'
assert arch in ('arm32', 'arm64')
subprocess.run([sys.executable, str(repo/'ci/prepare-5.07-backend.py'), str(out), arch], check=True)
main = out/'main.go'
text = main.read_text()
if text.count('appVersion            = "5.07.000"') != 1:
    raise SystemExit('unexpected baseline anchor: version')
text = text.replace('appVersion            = "5.07.000"', 'appVersion            = "5.08.000"', 1)

TZ = re.compile(r'exec\.Command\("timedatectl",\s*"show",\s*"-p",\s*"Timezone",\s*"--value"\)\.Output\(\)')
NTP = re.compile(r'exec\.Command\("timedatectl",\s*"show",\s*"-p",\s*"NTPSynchronized",\s*"--value"\)\.Output\(\)')

def swap(source, name, expected_tz, expected_ntp):
    tz_hits = len(TZ.findall(source))
    ntp_hits = len(NTP.findall(source))
    if tz_hits != expected_tz or ntp_hits != expected_ntp:
        raise SystemExit(f'unexpected timedatectl calls in {name}: tz={tz_hits} ntp={ntp_hits}')
    return NTP.sub('ntpSyncOutput()', TZ.sub('tzFileOutput()', source))

text = swap(text, 'main.go', 2, 1)
anchor = '\tquality := ""\n\tif signal > 0 {'
if text.count(anchor) != 1:
    raise SystemExit('unexpected Wi-Fi quality anchor')
text = text.replace(anchor, '\tif signal == 0 && rssi != 0 {\n\t\tsignal = wifiSignalFromRSSI(rssi)\n\t}\n' + anchor, 1)
main.write_text(text)
w506 = out/'web506.go'
w506.write_text(swap(w506.read_text(), 'web506.go', 1, 1))
(out/'web508.go').write_bytes((repo/'runtime/5.08/web.go').read_bytes())
print('PREPARE_508_BACKEND_OK', arch)
