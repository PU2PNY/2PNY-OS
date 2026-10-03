#!/usr/bin/env python3
from pathlib import Path
import json, os, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
REGRESSED=(ROOT/'src/2pny-profile-autostart-0.3.31.py').read_text()
FIXED=(ROOT/'src/2pny-profile-autostart-0.3.31.110.py').read_text()
PROVEN_OLD=(ROOT/'src/2pny-profile-proven-0.3.31.py').read_text()
PROVEN_NEW=(ROOT/'src/2pny-profile-proven-0.3.31.110.py').read_text()

def run_autostart(source, runtime, proof=None, cfg=None):
    with tempfile.TemporaryDirectory(prefix='pu2pny-031110-auto-') as td:
        t=Path(td); state=t/'state'; run=t/'run'; bindir=t/'bin'; state.mkdir(); run.mkdir(); bindir.mkdir()
        (state/'provisioned').write_text('1')
        cfg=cfg or {'protocol':'DMR','server_name':'XLX026','server_address':'192.0.2.26','server_port':62031,'network_kind':'XLX'}
        (state/'config.json').write_text(json.dumps(cfg))
        (state/'hardware-probe.json').write_text(json.dumps({'mmdvm':{'detected':True}}))
        (state/'network-radio.json').write_text(json.dumps(runtime))
        if proof is not None:(state/'last-active-profile.json').write_text(json.dumps(proof))
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
        script=t/'autostart.py';script.write_text(source)
        env=os.environ.copy();env['PATH']=str(bindir)+os.pathsep+env['PATH'];env['CALLS']=str(calls)
        cp=subprocess.run(['python3',str(script)],env=env,text=True,capture_output=True)
        if cp.returncode != 0:raise AssertionError(cp.stderr)
        text=calls.read_text() if calls.exists() else ''
        activated='timeout -k 5 80 /usr/local/sbin/2pny-protocol-profiles activate DMR' in text
        saved=json.loads((state/'config.json').read_text())
        return activated,saved,text

def run_proven(source, runtime, cfg=None):
    with tempfile.TemporaryDirectory(prefix='pu2pny-031110-proof-') as td:
        state=Path(td)/'state';state.mkdir()
        cfg=cfg or {'protocol':'DMR','server_name':'XLX026'}
        (state/'config.json').write_text(json.dumps(cfg))
        (state/'network-radio.json').write_text(json.dumps(runtime))
        source=source.replace("STATE=Path('/var/lib/2pny')",f"STATE=Path({str(state)!r})")
        script=state/'proof.py';script.write_text(source)
        cp=subprocess.run(['python3',str(script)],text=True,capture_output=True)
        if cp.returncode != 0:raise AssertionError(cp.stderr)
        out=state/'last-active-profile.json'
        return json.loads(out.read_text()) if out.exists() else None

DMR_OK={'protocol':'DMR','server_name':'XLX026','address':'192.0.2.26','port':62031,'kind':'XLX','state':'configured'}
# Confirm the concrete 0.3.31 regression.
a,_,_=run_autostart(REGRESSED,DMR_OK)
assert a is False,'0.3.31 regression reproduction changed unexpectedly'
assert run_proven(PROVEN_OLD,DMR_OK) is None,'0.3.31 proof bug reproduction changed unexpectedly'
# Fix: DMR configured is a proven state because the protected helper writes it only after both services are active.
p=run_proven(PROVEN_NEW,DMR_OK)
assert p and p['protocol']=='DMR' and p['runtime']['state']=='configured'
# Fix: migration/missed-event fallback may reactivate only when saved config matches a previously successful runtime.
a,saved,_=run_autostart(FIXED,DMR_OK)
assert a is True and saved['protocol']=='DMR'
# Safety: a draft that does not match the proven runtime must never be auto-activated.
mismatch={'protocol':'DMR','server_name':'OTHER','server_address':'198.51.100.9','server_port':62031,'network_kind':'XLX'}
a,_,_=run_autostart(FIXED,DMR_OK,cfg=mismatch)
assert a is False
# Existing 0.3.31 proven-profile behavior remains valid.
proof={'schema':1,'protocol':'DMR','profile':{'protocol':'DMR','server_name':'XLX026','server_address':'192.0.2.26','server_port':62031,'network_kind':'XLX'}}
a,_,_=run_autostart(FIXED,DMR_OK,proof=proof)
assert a is True
# Other protocols keep their original proof gate.
dstar={'protocol':'DSTAR','server_name':'XLX026','address':'192.0.2.26','port':20010,'kind':'XLX','state':'gateway_active'}
p=run_proven(PROVEN_NEW,dstar,cfg={'protocol':'DSTAR','server_name':'XLX026'})
assert p and p['protocol']=='DSTAR'
invalid=dict(DMR_OK,state='connecting')
assert run_proven(PROVEN_NEW,invalid) is None

patch=(ROOT/'ci/patch-image-0.3.31.110.sh').read_text()
assert '2pny-profile-autostart-0.3.31.110.py' in patch
assert '2pny-profile-proven-0.3.31.110.py' in patch
print('TEST_031110_MMDVM_AUTOSTART_OK')
