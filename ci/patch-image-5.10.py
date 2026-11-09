#!/usr/bin/env python3
"""Offline 5.10 overlay on the published 5.09 image.

CLOCK-060: 2pny-timezone-apply.service runs with ProtectSystem=full and only /etc/timezone writable, so the helper could
never replace the /etc/localtime link (the zone stayed Europe/London); /etc becomes writable for that one-shot unit.
DIRECT-060: the 32-bit image shipped an AArch64 2pny-direct-core (cannot execute on a Pi Zero): the unit restarted every
8 s forever (load 5, CPU at 86%). An ARMv6 build of the project's own source replaces it, and the unit gets a restart limit.
BOOT-060: auto-maintenance and the host-list refresh wait 5 minutes after boot (CPU-free sleep).
UI-060: logo without the small tagline, bigger; Protocolos gets a visible button to the existing identity card.
EXPERT-060: NetworkManager keyfile owners and the clock request/result files.
Never touches RF, MMDVMHost, DMRGateway, NextionDriver, the probe, autostart or the apply scripts.
"""
import shutil
import struct
import sys
from pathlib import Path

root, arch, binary = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
direct_core = Path(sys.argv[4]).resolve() if len(sys.argv) > 4 else None
repo = Path(__file__).resolve().parents[1]
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.09.000'
assert binary.is_file() and binary.stat().st_size > 1000000
SUFFIX = '.pre-5.10'
backed = set()


def backup(path):
    if path in backed:
        return
    src, dst = root/path, root/(path + SUFFIX)
    assert src.is_file() and not dst.exists()
    shutil.copy2(src, dst)
    backed.add(path)


def replace(path, old, new, count=1):
    p = root/path
    text = p.read_text()
    assert text.count(old) == count, (path, old[:70], text.count(old))
    p.write_text(text.replace(old, new))


def create(path, content, mode=0o644):
    target = root/path
    assert not target.exists(), path
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, Path):
        shutil.copyfile(content, target)
    else:
        target.write_text(content)
    target.chmod(mode)


def elf(path):
    head = Path(path).read_bytes()[:20]
    assert head[:4] == b'\x7fELF', path
    return head[4], struct.unpack('<H', head[18:20])[0]       # (class 1=32 2=64, machine 40=ARM 183=AArch64)


backup('usr/local/bin/2pnyd')
shutil.copyfile(binary, root/'usr/local/bin/2pnyd')
(root/'usr/local/bin/2pnyd').chmod(0o755)

# CLOCK-060
create('etc/systemd/system/2pny-timezone-apply.service.d/60-etc.conf',
       '# CLOCK-060: the helper replaces the /etc/localtime link; ProtectSystem=full had made /etc read-only.\n[Service]\nReadWritePaths=/etc\n')

# DIRECT-060
create('etc/systemd/system/2pny-direct.service.d/60-restart.conf',
       '# DIRECT-060: never restart forever.\n[Unit]\nStartLimitIntervalSec=900\nStartLimitBurst=4\n\n[Service]\nRestartSec=30\n')
if arch == 'arm32':
    assert direct_core is not None and direct_core.is_file(), 'arm32 needs the ARMv6 2pny-direct-core build'
    assert elf(direct_core) == (1, 40), 'the replacement must be a 32-bit ARM ELF'
    target = 'usr/local/bin/2pny-direct-core'
    assert elf(root/target) == (2, 183), 'unexpected baseline: the shipped core is not the AArch64 build'
    backup(target)
    shutil.copyfile(direct_core, root/target)
    (root/target).chmod(0o755)
else:
    assert elf(root/'usr/local/bin/2pny-direct-core') == (2, 183), 'the 64-bit core stays as shipped'

# BOOT-060
for unit, limit in (('2pny-auto-maintenance', '30min'), ('2pny-hostfiles-update', '20min')):
    create(f'etc/systemd/system/{unit}.service.d/60-delay.conf',
           f'# BOOT-060: wait 5 minutes after boot so the first-boot CPU belongs to the radio and the wizard.\n[Service]\nExecStartPre=/bin/sleep 300\nTimeoutStartSec={limit}\n')

# EXPERT-060
expert = 'usr/local/libexec/pu2pny/expert-cmd-504.py'
assert (root/expert).read_bytes() == (repo/'runtime/5.08/expert-cmd.py').read_bytes(), 'unexpected baseline: ' + expert
backup(expert)
shutil.copyfile(repo/'runtime/5.10/expert-cmd.py', root/expert)
(root/expert).chmod(0o755)
compile((root/expert).read_bytes(), expert, 'exec')

# UI-060
create('usr/share/2pny/brand/logo-mark.png', repo/'assets/brand/web/logo-mark.png')
ui = 'usr/share/2pny/ui-language.js'
backup(ui)
replace(ui, "img.src='/brand/logo.png';", "img.src='/brand/logo-mark.png';")
replace(ui, "[[d.querySelector('.topnav .brand'),26],[d.querySelector('.brand strong'),34]]", "[[d.querySelector('.topnav .brand'),30],[d.querySelector('.brand strong'),38]]")
page = 'usr/share/2pny/protocols.html'
backup(page)
replace(page, '<span class="badge">Atual: <b id="currentProto">—</b></span></div>',
        '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><a class="badge" href="#identity504" style="text-decoration:none;cursor:pointer">✎ Editar indicativo e ID</a>'
        '<span class="badge">Atual: <b id="currentProto">—</b></span></div></div>')

(root/'etc/2pny/version').write_text('5.10.000\n')
print('PATCH_510_OFFLINE_OK', arch)
