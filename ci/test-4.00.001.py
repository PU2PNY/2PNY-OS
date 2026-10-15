#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
backend=repo/'ci/patch-backend-4.00.001.py'
image=repo/'ci/patch-image-4.00.001.sh'

for p in (backend,image):
    if not p.is_file(): raise SystemExit(f'missing {p}')

subprocess.run(['bash','-n',str(image)],check=True)
with tempfile.TemporaryDirectory(prefix='pu2pny-400001-test-') as td:
    out=Path(td)/'main.go'
    subprocess.run([sys.executable,str(backend),str(repo/'src/2pnyd-main-0.3.27.go'),str(out)],check=True)
    text=out.read_text()
    assert 'appVersion            = "4.00.001"' in text
    assert 'time.Sleep(160 * time.Millisecond)' in text
    assert 'time.Sleep(80 * time.Millisecond)' not in text
    # Protected RF/gateway literals are inherited from the 4.00.000 chain;
    # this overlay must not introduce edits in those subsystems.
    for forbidden in ('DMRGateway.ini','YSFGateway.ini','DStarGateway','RXFrequency','TXFrequency','ColorCode'):
        assert forbidden not in backend.read_text(), forbidden

patch=image.read_text()
required=(
 'new=\'ExecStart=/usr/local/bin/NextionDriver-pu2pny -i -vv -c /var/lib/2pny/mmdvm/MMDVM-Host.ini\'',
 "! grep -Fq 'NextionDriver-pu2pny -d '",
 'RemotePort\\\",\\\"40094', 'LocalPort\\\",\\\"40095', 'SendFrameType\\\",\\\"1',
 '2pny-timezone-restore.service','timedatectl set-timezone','4.00.001',
)
for token in required:
    assert token in patch, token
assert 'curl | bash' not in patch
print('SW_400001_SURGICAL_GATES_OK')
