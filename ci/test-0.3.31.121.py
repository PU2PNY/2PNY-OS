#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
base='b1c46164743d3893662d7fb6641be84d73b1b8b6'
base_branch='pu2pny-os-0.3.31.120-nextion-mdns-fix'
patch=(repo/'ci/patch-image-0.3.31.121.sh').read_text()
for token in (
    'ExecStartPre=/usr/bin/rm -f /run/2pny-nextiondriver/ttyNextionDriver',
    'NextionDriver-pu2pny -d -i -vv -c /var/lib/2pny/mmdvm/MMDVM-Host.ini',
    'ctl("start",NEXTIONDRIVER)',
    'active("2pny-mmdvmhost.service")',
    '0.3.31.121',
): assert token in patch, token
assert 'pu2pny-modern-v2' not in patch

backend=repo/'ci/patch-backend-0.3.31.121.py'
with tempfile.TemporaryDirectory(prefix='pu2pny-0331121-') as td:
    out=Path(td)/'2pnyd.go'
    subprocess.run([sys.executable,str(backend),str(repo/'src/2pnyd-main-0.3.27.go'),str(out)],check=True)
    text=out.read_text()
    assert '0.3.31.121' in text
    assert 'mmdvmhost-native' in text
    assert 'on7lds-compatible' in text

if subprocess.run(['git','cat-file','-e',base+'^{commit}'],cwd=repo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
    subprocess.run(['git','fetch','--no-tags','origin',base_branch+':refs/remotes/origin/'+base_branch],cwd=repo,check=True)
    got=subprocess.check_output(['git','rev-parse','refs/remotes/origin/'+base_branch],cwd=repo,text=True).strip()
    if got!=base: raise SystemExit(f'0.3.31.120 base moved: expected {base}, got {got}')
changed=subprocess.check_output(['git','diff','--name-only',base,'HEAD'],cwd=repo,text=True).splitlines()
allowed={
 '.github/workflows/0.3.31.121-build-release.yml',
 'ci/patch-image-0.3.31.121.sh','ci/patch-backend-0.3.31.121.py',
 'ci/test-0.3.31.121.py','ci/sync-canonical-0.3.31.121.py',
 'PU2PNY-OS_MASTER_SPEC.md','PU2PNY-OS_RELEASE_STATUS.md','PU2PNY-OS_TEST_MATRIX.md','PU2PNY-OS_CHANGELOG.md',
}
bad=sorted(set(changed)-allowed)
if bad: raise SystemExit('0.3.31.121 scope violation: '+', '.join(bad))
if [x for x in changed if x.startswith('src/')]: raise SystemExit('protected runtime source changed')
print('DISPLAY_029_RUNTIME_HANDOFF_OK')
print('DISPLAY_029_SCOPE_OK',len(changed))
