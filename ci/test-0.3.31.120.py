#!/usr/bin/env python3
"""0.3.31.120 Nextion reapply + mDNS-only regression gates."""
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
base = '274cf740dbea0a21e1431896c0ca3ccd775281a0'

patch = (repo/'ci/patch-image-0.3.31.120.sh').read_text()
for token in (
    'if (not ctl("enable",NEXTIONDRIVER)) or (not ctl("restart",NEXTIONDRIVER)):',
    'host-name=pu2pny',
    'use-ipv4=yes',
    '90-pu2pny-mdns',
    'try-restart avahi-daemon.service',
    '0.3.31.120',
):
    assert token in patch, token
assert 'NetworkManager/dispatcher.d' in patch
assert 'MMDVM-Host' not in patch
assert 'DMRGateway' not in patch
assert 'DStarGateway' not in patch
assert 'YSFGateway' not in patch

backend = repo/'ci/patch-backend-0.3.31.120.py'
with tempfile.TemporaryDirectory(prefix='pu2pny-0331120-') as td:
    out = Path(td)/'2pnyd.go'
    subprocess.run([sys.executable, str(backend), str(repo/'src/2pnyd-main-0.3.27.go'), str(out)], check=True)
    text = out.read_text()
    assert '0.3.31.120' in text
    assert 'mmdvmhost-native' in text
    assert 'on7lds-compatible' in text
    assert 'pu2pny-modern-v2' not in text

changed = subprocess.check_output(['git','diff','--name-only',base,'HEAD'], cwd=repo, text=True).splitlines()
allowed = {
    '.github/workflows/0.3.31.120-build-release.yml',
    'ci/patch-image-0.3.31.120.sh',
    'ci/patch-backend-0.3.31.120.py',
    'ci/test-0.3.31.120.py',
    'ci/sync-canonical-0.3.31.120.py',
    'PU2PNY-OS_MASTER_SPEC.md','PU2PNY-OS_RELEASE_STATUS.md','PU2PNY-OS_TEST_MATRIX.md','PU2PNY-OS_CHANGELOG.md',
}
bad = sorted(set(changed)-allowed)
if bad:
    raise SystemExit('0.3.31.120 scope violation: '+', '.join(bad))
protected = [x for x in changed if x.startswith('src/')]
if protected:
    raise SystemExit('protected runtime source changed: '+', '.join(protected))
print('DISPLAY_028_NEXTION_RESTART_GATE_OK')
print('NET_038_MDNS_REANNOUNCE_GATE_OK')
print('REL_030_SCOPE_OK', len(changed))
