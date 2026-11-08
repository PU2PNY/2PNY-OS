#!/usr/bin/env python3
"""BOOT-053: reproduce the old failure before testing the surgical fix."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
legacy = (ROOT / 'ci/patch-image-5.00.003.sh').read_text()
anchor = 'cat >"$ROOT/usr/local/sbin/2pny-profile-autostart-safe" <<\'EOF\'\n'
assert legacy.count(anchor) == 1
original = legacy.split(anchor, 1)[1].split('\nEOF\n', 1)[0]
fixed = (ROOT / 'runtime/5.03/profile-autostart-safe.py').read_text()

def run(source, states):
    with tempfile.TemporaryDirectory(prefix='pu2pny-boot053-') as directory:
        root=Path(directory); bindir=root/'bin'; bindir.mkdir()
        ctl=bindir/'systemctl'
        ctl.write_text('#!/usr/bin/env python3\nimport os,sys,json\n'
                       's=json.loads(os.environ["SERVICE_STATES"])\n'
                       'sys.exit(0 if s.get(sys.argv[-1],False) else 3)\n')
        ctl.chmod(0o755)
        hit=root/'called'
        app=bindir/'autostart'
        app.write_text('#!/usr/bin/env python3\nimport os,pathlib\n'
                       'pathlib.Path(os.environ["CALLS"]).write_text("called")\n')
        app.chmod(0o755)
        src=root/'safe.py'
        src.write_text(source.replace('/usr/local/sbin/2pny-profile-autostart',str(app)))
        env=dict(os.environ,PATH=str(bindir)+os.pathsep+os.environ.get('PATH',''),
                 CALLS=str(hit),SERVICE_STATES=json.dumps(states))
        result=subprocess.run([sys.executable,str(src)],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        return hit.exists()

gateway={'2pny-dmrgateway.service':True}
both={**gateway,'2pny-mmdvmhost.service':True}
assert run(original,gateway) is False  # red on the existing version
assert run(fixed,gateway) is True       # correct gateway-only false healthy state
assert run(original,both) is False
assert run(fixed,both) is False         # preserve a healthy active profile
assert run(fixed,{}) is True
u=(ROOT/'runtime/5.03/2pny-profile-autostart-retry.path').read_text()
assert 'PathChanged=/var/lib/2pny/hardware-probe.json' in u
assert 'Unit=2pny-profile-autostart-retry.service' in u
print('TEST_BOOT_053_PROFILE_RETRY_OK')
