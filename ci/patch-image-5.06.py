#!/usr/bin/env python3
"""Offline 5.06 overlay on the published 5.05 image.

CLOCK-056 (zone applied for real + browser time when NTP is not synchronized), VOICE-056 (spoken hour on
D-Star, missing "linkedto" word alias), BOOT-056 (quick resume of the proven profile), PROTO-056
(honest crossmode status). Never touches RF configuration, MMDVMHost, DMRGateway, NextionDriver, the
probe, the profile autostart or the profile/protocol apply helpers. Edits must match exactly once.
"""
import shutil
import sys
from pathlib import Path

root, arch, binary = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
repo = Path(__file__).resolve().parents[1]
fix = repo/'ci/fixtures/5.03'
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.05.000'
assert binary.is_file() and binary.stat().st_size > 1000000


def backup(path):
    src, dst = root/path, root/(path + '.pre-5.06')
    assert src.is_file() and not dst.exists()
    shutil.copy2(src, dst)


def replace(path, old, new):
    p = root/path
    text = p.read_text()
    assert text.count(old) == 1, (path, old[:70], text.count(old))
    p.write_text(text.replace(old, new, 1))


def upgrade(target, source, expected, mode):
    """Replace an installed file only if it is exactly what the previous release shipped."""
    installed = root/target
    assert installed.read_bytes() == expected.read_bytes(), 'unexpected baseline: ' + target
    backup(target)
    shutil.copyfile(source, installed)
    installed.chmod(mode)


def create(target, content, mode):
    path = root/target
    assert not path.exists(), target
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, Path):
        shutil.copyfile(content, path)
    else:
        path.write_text(content)
    path.chmod(mode)


backup('usr/local/bin/2pnyd')
shutil.copyfile(binary, root/'usr/local/bin/2pnyd')
(root/'usr/local/bin/2pnyd').chmod(0o755)

# CLOCK-056
upgrade('usr/local/sbin/2pny-timezone-apply', repo/'runtime/5.06/tz-apply.py', fix/'2pny-timezone-apply', 0o755)
create('etc/systemd/system/2pny-timezone-apply.service.d/56-etc.conf', '[Service]\nReadWritePaths=/etc\n', 0o644)
system = 'usr/share/2pny/system.html'
assert (root/system).read_bytes() == (fix/'system.html').read_bytes(), 'unexpected baseline: ' + system
backup(system)
replace(system, '</body>', '<script>' + (repo/'runtime/5.06/clock.js').read_text() + '</script></body>')

# VOICE-056
create('usr/local/sbin/2pny-hourly-voice', repo/'runtime/5.06/hourly-voice.py', 0o755)
create('etc/systemd/system/2pny-hourly-voice.service', repo/'runtime/5.06/2pny-hourly-voice.service', 0o644)
create('etc/systemd/system/2pny-hourly-voice.timer', repo/'runtime/5.06/2pny-hourly-voice.timer', 0o644)
link = root/'etc/systemd/system/timers.target.wants/2pny-hourly-voice.timer'
assert not link.exists() and not link.is_symlink()
link.symlink_to('../2pny-hourly-voice.timer')
indx = 'usr/local/share/dstargateway.d/en_GB.indx'
assert (root/indx).read_bytes() == (fix/'en_GB.indx').read_bytes(), 'unexpected baseline: ' + indx
assert (root/'usr/local/share/dstargateway.d/TIME_en_GB.ambe').read_bytes() == (fix/'TIME_en_GB.ambe').read_bytes()
backup(indx)
text = (root/indx).read_text()
assert text.endswith('\n') and '\nlinked\t2124\t19\n' in text and 'linkedto' not in text
(root/indx).write_text(text + 'linkedto\t2124\t19\n')

# BOOT-056
create('usr/local/sbin/2pny-fast-resume', repo/'runtime/5.06/fast-resume.py', 0o755)
create('etc/systemd/system/2pny-profile-autostart.service.d/56-fast-resume.conf',
       '[Service]\nExecStartPre=-/usr/local/sbin/2pny-fast-resume\n', 0o644)

# EXPERT-056 + PROTO-056
upgrade('usr/local/libexec/pu2pny/expert-cmd-504.py', repo/'runtime/5.06/expert-cmd.py', repo/'runtime/5.05/expert-cmd.py', 0o755)
expert = 'usr/share/2pny/expert.html'
backup(expert)
replace(expert, '</main>', (repo/'runtime/5.06/expert-crossmode-card.html').read_text() + '</main>')

for filename in ('usr/local/sbin/2pny-timezone-apply', 'usr/local/sbin/2pny-hourly-voice',
                 'usr/local/sbin/2pny-fast-resume', 'usr/local/libexec/pu2pny/expert-cmd-504.py'):
    compile((root/filename).read_bytes(), filename, 'exec')
(root/'etc/2pny/version').write_text('5.06.000\n')
print('PATCH_506_OFFLINE_OK', arch)
