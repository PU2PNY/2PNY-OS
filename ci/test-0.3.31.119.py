#!/usr/bin/env python3
"""0.3.31.119 display-only regression gates."""
from pathlib import Path
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
base='a31701ed2cfce1874a1d97145601af94f4380ae2'
base_branch='pu2pny-os-0.3.31.118-nextion-hotfix'

patch=(repo/'ci/patch-image-0.3.31.119.sh').read_text()
for token in (
    'Modem · G4KLX padrão · ScreenLayout 0',
    'Nextion · ON7LDS L2 · ScreenLayout 2',
    'Nextion · ON7LDS L3 · NextionDriver',
    'Nextion · ON7LDS L3 HS · NextionDriver',
    'raw_layout=ov.get("layout")',
    '/run/2pny-nextiondriver/ttyNextionDriver',
    'SendFrameType","1"',
    '0.3.31.119',
):
    assert token in patch, token
assert 'requested not in (0,2,3,4)' in patch
assert 'NoNewPrivileges' not in patch  # unit is protected, not rewritten here

backend=repo/'ci/patch-backend-0.3.31.119.py'
with tempfile.TemporaryDirectory(prefix='pu2pny-0331119-') as td:
    out=Path(td)/'2pnyd.go'
    subprocess.run([sys.executable,str(backend),str(repo/'src/2pnyd-main-0.3.27.go'),str(out)],check=True)
    text=out.read_text()
    assert '0.3.31.119' in text
    assert 'mmdvmhost-native' in text
    assert 'on7lds-compatible' in text
    assert 'pu2pny-modern-v2' not in text

if subprocess.run(['git','cat-file','-e',base+'^{commit}'],cwd=repo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
    subprocess.run(['git','fetch','--no-tags','origin',base_branch+':refs/remotes/origin/'+base_branch],cwd=repo,check=True)
    got=subprocess.check_output(['git','rev-parse','refs/remotes/origin/'+base_branch],cwd=repo,text=True).strip()
    if got!=base:
        raise SystemExit(f'0.3.31.118 base moved: expected {base}, got {got}')

changed=subprocess.check_output(['git','diff','--name-only',base,'HEAD'],cwd=repo,text=True).splitlines()
allowed={
    '.github/workflows/0.3.31.119-build-release.yml',
    'ci/patch-image-0.3.31.119.sh',
    'ci/patch-backend-0.3.31.119.py',
    'ci/test-0.3.31.119.py',
    'ci/sync-canonical-0.3.31.119.py',
    'PU2PNY-OS_MASTER_SPEC.md','PU2PNY-OS_RELEASE_STATUS.md','PU2PNY-OS_TEST_MATRIX.md','PU2PNY-OS_CHANGELOG.md',
}
bad=sorted(set(changed)-allowed)
if bad:
    raise SystemExit('0.3.31.119 scope violation: '+', '.join(bad))
protected=[x for x in changed if x.startswith('src/')]
if protected:
    raise SystemExit('protected runtime source changed: '+', '.join(protected))

print('DISPLAY_027_STANDARD_RENDERERS_OK')
print('DISPLAY_027_LAYOUT0_ZERO_VALUE_OK')
print('DISPLAY_027_SCOPE_OK',len(changed))
