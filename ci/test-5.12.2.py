#!/usr/bin/env python3
"""SW gates 5.12.002: voice INI mmdvm access, bounded Pi Zero tasks, board AP owner."""
import importlib.util
import os
import grp
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

p=module('patch5122','ci/patch-image-5.12.2.py')
v=module('voice5122','runtime/5.12.2/voice-apply.py')
g=module('lowload5122','runtime/5.12.2/lowload-gate.py')
assert g.should_run('Raspberry Pi Zero W Rev 1.1',1,'armv6l',1200,7.75) is False
assert g.should_run('Raspberry Pi Zero W Rev 1.1',1,'armv6l',3000,.21) is True
assert g.should_run('Raspberry Pi Zero W Rev 1.1',1,'armv6l',4000,2.2) is False
assert g.should_run('Raspberry Pi 4 Model B',4,'aarch64',100,8.0) is True
assert g.should_run('Orange Pi Zero',4,'armv7l',60,3.0) is True

assert os.geteuid()==0,'gateway permission tests need root'
grp.getgrnam('mmdvm')
with tempfile.TemporaryDirectory() as td:
    # runuser must traverse all components, so make test dir searchable.
    root=Path(td);root.chmod(0o755)
    state=root/'state';state.mkdir()
    dmr=state/'dmr';dmr.mkdir()
    for d in (state,dmr):
        os.chown(d,0,grp.getgrnam('mmdvm').gr_gid);d.chmod(0o750)
    ini=dmr/'DMRGateway.ini'
    baseline=( '[General]\nId=7240000\n'
               '[Voice]\nEnabled=1\nLanguage=Portugues\nDirectory=/x\n'
               '[Info]\nCallsign=TEST123\n' ).encode()
    ini.write_bytes(baseline)
    ini.chmod(0o600)
    os.chown(ini,0,0)
    # Same config, but service cannot read it: repair *even if content unchanged*.
    assert v.apply(state,{'enabled':True,'language':'pt'},only='dmr',restart=False)==[]
    assert ini.read_bytes()==baseline,'no rewrite without a content change'
    st=ini.stat()
    assert stat.S_IMODE(st.st_mode)==0o640 and st.st_gid==grp.getgrnam('mmdvm').gr_gid
    r=subprocess.run(['runuser','-u','mmdvm','--','test','-r',str(ini)],check=False)
    assert r.returncode==0,'DMRGateway service mmdvm cannot read INI'
    # A new voice configuration must retain service permissions.
    assert v.apply(state,{'enabled':False,'language':'pt'},only='dmr',restart=False)==['dmr']
    assert b'Enabled=0' in ini.read_bytes()
    assert subprocess.run(['runuser','-u','mmdvm','--','test','-r',str(ini)]).returncode==0
    before=ini.read_bytes()
    def failure(*args):
        return args[0]=='is-active'
    try:
        v.apply(state,{'enabled':True,'language':'pt'},only='dmr',restart=True,ctl=failure)
    except RuntimeError:
        pass
    else:
        raise AssertionError('rollback failure not triggered')
    assert ini.read_bytes()==before,'rollback changed the saved configuration'
    assert subprocess.run(['runuser','-u','mmdvm','--','test','-r',str(ini)]).returncode==0
    secret=state/'voice-settings.json'
    v.atomic(secret,b'private')
    assert stat.S_IMODE(secret.stat().st_mode)==0o600,'private config exposed'

with tempfile.TemporaryDirectory() as td:
    root=Path(td);(root/'etc/2pny').mkdir(parents=True)
    (root/'etc/2pny/version').write_text('5.12.001\n')
    voice=root/'usr/local/sbin/2pny-voice-apply'
    voice.parent.mkdir(parents=True)
    voice.write_bytes((ROOT/'runtime/5.11/voice-apply.py').read_bytes())
    for unit in ('2pny-auto-maintenance','2pny-hostfiles-update','2pny-operational-restore'):
        file=root/f'etc/systemd/system/{unit}.service'
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text('[Unit]\nDescription=x\n[Service]\nExecStart=/bin/true\nRestartSec=8\n')
    panel=root/'etc/systemd/system/2pnyd.service'
    panel.write_text('[Service]\nExecStart=/usr/local/bin/2pnyd\n')
    wants=root/'etc/systemd/system/multi-user.target.wants/2pnyd.service'
    wants.parent.mkdir(parents=True)
    wants.symlink_to('/etc/systemd/system/2pnyd.service')
    net=root/'usr/local/sbin/2pny-network-core'
    net.parent.mkdir(parents=True,exist_ok=True)
    net.write_text('SETUP_IP=10.43.0.1\n')
    dns=root/'usr/share/2pny/network/dnsmasq-ap.template'
    dns.parent.mkdir(parents=True);dns.write_text('listen-address=10.43.0.1\n')
    mmdvm=root/'usr/local/bin/MMDVM-Host'
    mmdvm.parent.mkdir(parents=True);mmdvm.write_bytes(b'BASELINE_PROTECTED')
    for board in ('32','64','opizero','nanopineo'):
        clone=root.parent/(root.name+'-'+board)
        shutil.copytree(root,clone,symlinks=True)
        try:
            changed=p.apply(clone,board)
            assert (clone/'etc/2pny/version').read_text()=='5.12.002\n'
            assert (clone/'usr/local/bin/MMDVM-Host').read_bytes()==b'BASELINE_PROTECTED'
            assert 'usr/local/sbin/2pny-voice-apply' in changed
            assert (clone/'usr/local/sbin/2pny-voice-apply.pre-5.12.2').read_bytes()==voice.read_bytes()
            assert (clone/'etc/systemd/system/2pny-auto-maintenance.service.d/62-pizero-lowload.conf').exists()
            if board in ('opizero','nanopineo'):
                assert (clone/'etc/systemd/system/hostapd.service').is_symlink()
                assert (clone/'etc/systemd/system/hostapd.service').readlink()==Path('/dev/null')
                assert 'MemoryMax=128M' in (clone/'etc/systemd/system/2pnyd.service.d/62-board-portal.conf').read_text()
            else:
                assert not (clone/'etc/systemd/system/hostapd.service').exists()
            if board=='32':
                assert 'RestartSec=60' in (clone/'etc/systemd/system/2pny-operational-restore.service.d/62-pizero-retry-budget.conf').read_text()
            try:
                p.apply(clone,board)
            except AssertionError:
                pass
            else:
                raise AssertionError('P2 allowed double application')
        finally:
            shutil.rmtree(clone)
print('TEST_5122_VOICE_READABLE_ARMV6_CPU_BOARD_AP_GATES_PASS')
