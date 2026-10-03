#!/usr/bin/env python3
from pathlib import Path
import json, os, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
BASE=(ROOT/'src/2pny-profile-autostart-0.3.28.py').read_text()
REGRESSED=(ROOT/'src/2pny-profile-autostart-0.3.31.py').read_text()

def run(source, with_proven=False):
    with tempfile.TemporaryDirectory(prefix='pu2pny-031110-') as td:
        t=Path(td); state=t/'state'; run=t/'run'; bindir=t/'bin'; state.mkdir(); run.mkdir(); bindir.mkdir()
        (state/'provisioned').write_text('1')
        cfg={'protocol':'DMR','callsign':'PU2PNY'}
        (state/'config.json').write_text(json.dumps(cfg))
        (state/'hardware-probe.json').write_text(json.dumps({'mmdvm':{'detected':True}}))
        if with_proven:
            (state/'last-active-profile.json').write_text(json.dumps({'schema':1,'protocol':'DMR','profile':cfg}))
        calls=t/'calls.log'
        scripts={
          'systemctl':'#!/bin/sh\necho systemctl "$@" >> "$CALLS"\nexit 3\n',
          'ip':'#!/bin/sh\necho ip "$@" >> "$CALLS"\necho "default via 192.0.2.1 dev eth0"\nexit 0\n',
          'logger':'#!/bin/sh\necho logger "$@" >> "$CALLS"\nexit 0\n',
          'timeout':'#!/bin/sh\necho timeout "$@" >> "$CALLS"\nexit 0\n',
        }
        for name,body in scripts.items():
            f=bindir/name;f.write_text(body);f.chmod(0o755)
        source=source.replace("STATE=Path('/var/lib/2pny');RUN=Path('/run/2pny')",f"STATE=Path({str(state)!r});RUN=Path({str(run)!r})")
        source=source.replace('STATE=Path("/var/lib/2pny")',f'STATE=Path({str(state)!r})').replace('RUN=Path("/run/2pny")',f'RUN=Path({str(run)!r})')
        script=t/'autostart.py';script.write_text(source)
        env=os.environ.copy();env['PATH']=str(bindir)+os.pathsep+env['PATH'];env['CALLS']=str(calls)
        cp=subprocess.run(['python3',str(script)],env=env,text=True,capture_output=True)
        if cp.returncode != 0: raise AssertionError(cp.stderr)
        text=calls.read_text() if calls.exists() else ''
        return 'timeout -k 5 80 /usr/local/sbin/2pny-protocol-profiles activate DMR' in text

assert run(BASE) is True, '0.3.30 autostart baseline must activate saved DMR profile'
assert run(REGRESSED) is False, '0.3.31 regression reproduction changed unexpectedly'
assert run(REGRESSED,with_proven=True) is True, '0.3.31 proven-profile path must remain understood'
patch=(ROOT/'ci/patch-image-0.3.31.110.sh').read_text()
assert '2pny-profile-autostart-0.3.28.py' in patch
print('TEST_031110_MMDVM_AUTOSTART_OK')
