#!/usr/bin/env python3
"""Offline 5.07 overlay on the published 5.06 image.

SPEED-057 (cached dashboard states, retry gate and back-off, background CPU weight, longer activation
limits), BOOT-057 (quick resume for D-Star, DMR and YSF, also before the retry), EXPERT-057 (load, boot
and apply evidence), HOST-057 (arm32 only: pu2pny32.local). Edits must match exactly once unless noted.
Never touches MMDVMHost, DMRGateway, NextionDriver, the probe, the autostart scripts or the RF apply scripts.
"""
import shutil
import sys
from pathlib import Path

root, arch, binary = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
repo = Path(__file__).resolve().parents[1]
fix = repo/'ci/fixtures/5.03'
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.06.000'
assert binary.is_file() and binary.stat().st_size > 1000000
backed = set()


def backup(path):
    src, dst = root/path, root/(path + '.pre-5.07')
    if path in backed:
        return
    assert src.is_file() and not dst.exists()
    shutil.copy2(src, dst)
    backed.add(path)


def replace(path, old, new, count=1):
    p = root/path
    text = p.read_text()
    assert text.count(old) == count, (path, old[:70], text.count(old))
    p.write_text(text.replace(old, new))


def upgrade(target, source, expected, mode):
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


def baseline(path, name):
    assert (root/path).read_bytes() == (fix/name).read_bytes(), 'unexpected baseline: ' + path


backup('usr/local/bin/2pnyd')
shutil.copyfile(binary, root/'usr/local/bin/2pnyd')
(root/'usr/local/bin/2pnyd').chmod(0o755)

# SPEED-057: retry gate and back-off; lower priority for background work; longer activation limits
create('usr/local/sbin/2pny-retry-gate', repo/'runtime/5.07/retry-gate.sh', 0o755)
create('etc/systemd/system/2pny-profile-autostart-retry.service.d/57-gate.conf',
       '[Service]\nExecCondition=/usr/local/sbin/2pny-retry-gate\nExecStartPre=-/usr/local/sbin/2pny-fast-resume\nNice=15\nCPUWeight=20\n', 0o644)
for unit, weight in (('2pny-netdiag', 20), ('2pny-aprs', 20), ('2pny-station', 20), ('2pny-display-core', 30)):
    create(f'etc/systemd/system/{unit}.service.d/57-cpu.conf', f'[Service]\nCPUWeight={weight}\n', 0o644)
profiles = 'usr/local/sbin/2pny-protocol-profiles'
baseline(profiles, '2pny-protocol-profiles')
backup(profiles)
replace(profiles, 'text=True,capture_output=True,timeout=45)', 'text=True,capture_output=True,timeout=150)')
replace(profiles, 'text=True,capture_output=True,timeout=55)', 'text=True,capture_output=True,timeout=150)')
wizard = 'usr/share/2pny/wizard.html'
baseline(wizard, 'wizard.html')
backup(wizard)
replace(wizard, 'let deadline=Date.now()+90000;', 'let deadline=Date.now()+240000;')

# BOOT-057 / EXPERT-057
upgrade('usr/local/sbin/2pny-fast-resume', repo/'runtime/5.07/fast-resume.py', repo/'runtime/5.06/fast-resume.py', 0o755)
upgrade('usr/local/libexec/pu2pny/expert-cmd-504.py', repo/'runtime/5.07/expert-cmd.py', repo/'runtime/5.06/expert-cmd.py', 0o755)

# HOST-057: the 32-bit image answers on pu2pny32.local so it never collides with a 64-bit hotspot
if arch == 'arm32':
    for name, path in (('wizard.html', wizard), ('internet.html', 'usr/share/2pny/internet.html'),
                       ('dnsmasq-ap.template', 'usr/share/2pny/network/dnsmasq-ap.template'),
                       ('2pny-captive.conf', 'etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf'),
                       ('90-pu2pny-mdns', 'etc/NetworkManager/dispatcher.d/90-pu2pny-mdns'),
                       ('2pny-network-core', 'usr/local/sbin/2pny-network-core'),
                       ('2pny-mdns-guard', 'usr/local/sbin/2pny-mdns-guard')):
        if path != wizard:
            baseline(path, name)
        backup(path)
        text = (root/path).read_text()
        assert text.count('pu2pny.local') >= 1, path
        (root/path).write_text(text.replace('pu2pny.local', 'pu2pny32.local'))
    guard = 'usr/local/sbin/2pny-mdns-guard'
    replace(guard, 'hostnamectl set-hostname pu2pny >/dev/null', 'hostnamectl set-hostname pu2pny32 >/dev/null')
    replace(guard, "printf 'pu2pny\\n' >/etc/hostname", "printf 'pu2pny32\\n' >/etc/hostname")
    replace(guard, '("host-name","pu2pny")', '("host-name","pu2pny32")')
    alias = 'usr/local/sbin/2pny-mdns-alias'
    baseline(alias, '2pny-mdns-alias')
    backup(alias)
    replace(alias, '-f 2pny.local "$ip"', '-f 2pny32.local "$ip"')
    baseline('etc/hostname', 'hostname'); backup('etc/hostname'); (root/'etc/hostname').write_text('pu2pny32\n')
    baseline('etc/hosts', 'hosts'); backup('etc/hosts'); replace('etc/hosts', '127.0.1.1\tpu2pny\n', '127.0.1.1\tpu2pny32\n')
    baseline('etc/avahi/avahi-daemon.conf', 'avahi-daemon.conf'); backup('etc/avahi/avahi-daemon.conf')
    replace('etc/avahi/avahi-daemon.conf', 'host-name=pu2pny\n', 'host-name=pu2pny32\n')
    for path in ('usr/local/libexec/pu2pny/oled-502.py', 'usr/local/libexec/pu2pny/lcd-504.py'):
        backup(path)
        text = (root/path).read_text()
        assert text.count("'pu2pny.local'") >= 1, path
        (root/path).write_text(text.replace("'pu2pny.local'", "'pu2pny32.local'"))

for filename in ('usr/local/sbin/2pny-protocol-profiles', 'usr/local/sbin/2pny-fast-resume',
                 'usr/local/libexec/pu2pny/expert-cmd-504.py'):
    compile((root/filename).read_bytes(), filename, 'exec')
(root/'etc/2pny/version').write_text('5.07.000\n')
print('PATCH_507_OFFLINE_OK', arch)
