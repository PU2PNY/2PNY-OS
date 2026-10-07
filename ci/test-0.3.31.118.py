#!/usr/bin/env python3
"""0.3.31.118 surgical regression gates for the ON7LDS virtual-port HW fix."""
from pathlib import Path
import subprocess

repo=Path(__file__).resolve().parents[1]
base='088ba5901bfc918503430df658f1a7b5728ef64e'
base_branch='pu2pny-os-0.3.31.117-network-nextion'

hard=(repo/'ci/harden-nextiondriver-0.3.31.118.py').read_text()
for token in ('/run/2pny-nextiondriver/ttyNextionDriver','/dev/ttyNextionDriver','harden-nextiondriver-0.3.31.117.py'):
    assert token in hard, token
assert 're.subn' in hard

patch=(repo/'ci/patch-image-0.3.31.118.sh').read_text()
for token in ('User=mmdvm','RuntimeDirectory=2pny-nextiondriver','/run/2pny-nextiondriver/ttyNextionDriver','0.3.31.118'):
    assert token in patch, token
assert 'systemctl' not in patch
assert 'MMDVM-Host.ini' not in patch

backend=(repo/'ci/patch-backend-0.3.31.118.py').read_text()
assert 'patch-backend-0.3.31.117.py' in backend
assert '0.3.31.118' in backend

hotfix=(repo/'docs/HOTFIX-0.3.31.118.md').read_text()
for token in ('DISPLAY-026','/dev/ttyNextionDriver','/run/2pny-nextiondriver/ttyNextionDriver','HW FAIL'):
    assert token in hotfix, token

if subprocess.run(['git','cat-file','-e',base+'^{commit}'],cwd=repo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
    subprocess.run(['git','fetch','--no-tags','origin',base_branch+':refs/remotes/origin/'+base_branch],cwd=repo,check=True)
    got=subprocess.check_output(['git','rev-parse','refs/remotes/origin/'+base_branch],cwd=repo,text=True).strip()
    if got!=base:
        raise SystemExit(f'0.3.31.117 base moved: expected {base}, got {got}')
changed=subprocess.check_output(['git','diff','--name-only',base,'HEAD'],cwd=repo,text=True).splitlines()
allowed={
    '.github/workflows/0.3.31.118-build-release.yml',
    'ci/harden-nextiondriver-0.3.31.118.py',
    'ci/patch-backend-0.3.31.118.py',
    'ci/patch-image-0.3.31.118.sh',
    'ci/sync-canonical-0.3.31.118.py',
    'ci/test-0.3.31.118.py',
    'docs/HOTFIX-0.3.31.118.md',
    'PU2PNY-OS_MASTER_SPEC.md','PU2PNY-OS_RELEASE_STATUS.md','PU2PNY-OS_TEST_MATRIX.md','PU2PNY-OS_CHANGELOG.md',
}
bad=sorted(set(changed)-allowed)
if bad:
    raise SystemExit('0.3.31.118 scope violation: '+', '.join(bad))
protected=[x for x in changed if x.startswith('src/')]
if protected:
    raise SystemExit('runtime source changed in display-only hotfix: '+', '.join(protected))

print('DISPLAY_026_ROOT_CAUSE_GATE_OK')
print('DISPLAY_026_NONROOT_RUNTIME_LINK_POLICY_OK')
print('SCOPE_0331118_OK',len(changed))
