#!/usr/bin/env python3
"""5.12.002 P2: targeted repairs based on 5.12.001 HW failures.

No changes to MMDVMHost/DMRGateway binaries, RF managers, NextionDriver,
network-core, device tree, UART, display or bootloader. Fail closed.
"""
from pathlib import Path
import shutil
import stat
import sys

REPO=Path(__file__).resolve().parents[1]
BACKUP='.pre-5.12.2'

def apply(root,board):
    root=Path(root).resolve()
    assert board in ('32','64','opizero','nanopineo')
    assert root!=Path('/') and root.is_dir()
    version=root/'etc/2pny/version'
    assert version.is_file() and version.read_text().strip()=='5.12.001', 'requires published P1'
    changes=[]
    def backup(file):
        assert file.is_file() and not file.is_symlink() and not file.with_name(file.name+BACKUP).exists(),file
        b=file.with_name(file.name+BACKUP);shutil.copy2(file,b)
        changes.append(str(b.relative_to(root)))
    def create(relative,contents,mode=0o644):
        p=root/relative
        assert not p.exists() and not p.is_symlink(),p
        # One known configuration owner per unit; no duplicate dropin names.
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(contents,encoding='utf-8')
        p.chmod(mode)
        changes.append(relative)
    def replace(relative,old,new,expected=None,mode=None):
        p=root/relative
        assert p.is_file() and not p.is_symlink(),relative
        raw=p.read_bytes()
        if expected is not None:
            assert raw==expected, 'changed baseline: '+relative
        backup(p)
        p.write_bytes(new if old is None else raw.replace(old,new))
        if old is not None:
            assert raw.count(old)==1,('missing/duplicate anchor',relative)
        if mode is not None:p.chmod(mode)
        changes.append(relative)

    # Original and its prior rollback have matching bytes in both board families.
    original=(REPO/'runtime/5.11/voice-apply.py').read_bytes()
    fixed=(REPO/'runtime/5.12.2/voice-apply.py').read_bytes()
    assert original!=fixed
    replace('usr/local/sbin/2pny-voice-apply',None,fixed,original,0o755)

    # Conditional maintenance postpones *background jobs only* on Pi Zero/W.
    create('usr/local/libexec/pu2pny/lowload-gate-5122.py',
           (REPO/'runtime/5.12.2/lowload-gate.py').read_text(),0o755)
    for unit in ('2pny-auto-maintenance','2pny-hostfiles-update'):
        src=root/f'etc/systemd/system/{unit}.service'
        assert src.is_file() and 'ExecStart=' in src.read_text(),unit
        create(f'etc/systemd/system/{unit}.service.d/62-pizero-lowload.conf',
               '[Service]\nExecCondition=/usr/local/libexec/pu2pny/lowload-gate-5122.py\n')

    if board=='32':
        # The HW Zero W log showed operational-restore retrying while systemd
        # is already saturated. This bounds *failures* without disabling recovery.
        src=root/'etc/systemd/system/2pny-operational-restore.service'
        assert src.is_file() and 'RestartSec=8' in src.read_text()
        create('etc/systemd/system/2pny-operational-restore.service.d/62-pizero-retry-budget.conf',
               '[Unit]\nStartLimitIntervalSec=600\nStartLimitBurst=3\n'
               '[Service]\nRestartSec=60\n')
    if board in ('opizero','nanopineo'):
        # The PU2PNY network-core is already the sole manual hostapd owner.
        # Masking the distribution's *separate* systemd hostapd.service
        # prevents a second daemon from seizing AP Wi-Fi.
        p=root/'etc/systemd/system/hostapd.service'
        assert not p.exists() and not p.is_symlink(), 'stock hostapd already overridden'
        p.symlink_to('/dev/null')
        changes.append(str(p.relative_to(root)))
        panel=root/'etc/systemd/system/2pnyd.service'
        assert panel.is_file() and 'ExecStart=/usr/local/bin/2pnyd' in panel.read_text()
        assert (root/'etc/systemd/system/multi-user.target.wants/2pnyd.service').is_symlink(), 'panel disabled'
        # 64MB hard limit may kill the Go server on Armbian boards. Maximum
        # memory is not allocated; only the permitted cap changes.
        create('etc/systemd/system/2pnyd.service.d/62-board-portal.conf',
               '[Unit]\nStartLimitIntervalSec=300\nStartLimitBurst=8\n'
               '[Service]\nMemoryMax=128M\nRestartSec=4\n')
        # Do not modify AP/DHCP config or claim it is verified in HW.
        assert '10.43.0.1' in (root/'usr/local/sbin/2pny-network-core').read_text(), 'unexpected AP owner'
        assert (root/'usr/share/2pny/network/dnsmasq-ap.template').is_file()

    backup(version)
    version.write_text('5.12.002\n')
    version.chmod(0o644)
    changes.append('etc/2pny/version')
    assert len(set(changes))==len(changes)
    print('PATCH_5122_BOUNDED_HW_REPAIR',board,len(changes),flush=True)
    return set(changes)

if __name__=='__main__':
    assert len(sys.argv)==3
    apply(Path(sys.argv[1]),sys.argv[2])
