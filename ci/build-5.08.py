#!/usr/bin/env python3
"""Serial VPS image build of 5.08 from the checksum-verified published 5.07 images; root required.

Scope: CLOCK-058, DISPLAY-058, SPEED-058, UI-058, BOOT-058, EXPERT-058; RF, modem, gateways, Nextion remain byte-identical.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
work = Path(sys.argv[1]).resolve()
arch = sys.argv[2]
source_tree = sys.argv[3]
assert os.geteuid() == 0 and arch in ('arm32', 'arm64') and re.fullmatch('[a-f0-9]{40}', source_tree)
assert work != Path('/')
BASE = {'arm32': '6abc9e29e226f445c25246ad15dd8920d0acb8eaf02d777d98e123774a9e8667',
        'arm64': 'c8f51e5be1b652ced4f4c7323811b1e8c6b387552691bf7af8da93b953e5ea07'}
BASE_NAME = {'arm32': 'pu2pny-32-5.07.img.xz', 'arm64': 'pu2pny-64-5.07.img.xz'}
MODIFIED = {
    'usr/local/bin/2pnyd', 'usr/local/sbin/2pny-timezone-apply', 'usr/local/sbin/2pny-timezone-restore',
    'usr/local/libexec/pu2pny/expert-cmd-504.py', 'usr/local/libexec/pu2pny/i2c-505.py',
    'usr/local/sbin/2pny-display-apply', 'usr/local/sbin/2pny-display-apply-request',
    'usr/local/sbin/2pny-station-worker', 'usr/share/2pny/ui-common-0.3.0.js', 'usr/share/2pny/ui-language.js',
}
MASKED = {
    'etc/systemd/system/userconfig.service': 'etc/systemd/system/multi-user.target.wants/userconfig.service',
    'etc/systemd/system/apt-daily.timer': 'etc/systemd/system/timers.target.wants/apt-daily.timer',
    'etc/systemd/system/apt-daily-upgrade.timer': 'etc/systemd/system/timers.target.wants/apt-daily-upgrade.timer',
    'etc/systemd/system/man-db.timer': 'etc/systemd/system/timers.target.wants/man-db.timer',
    'etc/systemd/system/e2scrub_all.timer': 'etc/systemd/system/timers.target.wants/e2scrub_all.timer',
    'etc/systemd/system/dpkg-db-backup.timer': 'etc/systemd/system/timers.target.wants/dpkg-db-backup.timer',
    'etc/systemd/system/ModemManager.service': 'etc/systemd/system/multi-user.target.wants/ModemManager.service',
    'etc/systemd/system/triggerhappy.service': 'etc/systemd/system/multi-user.target.wants/triggerhappy.service',
    'etc/systemd/system/udisks2.service': 'etc/systemd/system/graphical.target.wants/udisks2.service',
}
ALLOWED = (MODIFIED | {p + '.pre-5.08' for p in MODIFIED} | set(MASKED) | set(MASKED.values()) | {
    'etc/modules-load.d/2pny-i2c.conf', 'etc/systemd/system/2pny-display-core.service.d/58-i2c.conf',
    'usr/share/2pny/brand/logo.png', 'usr/share/2pny/brand/favicon.png', 'usr/share/2pny/brand/favicon-192.png',
    'usr/share/2pny/brand/apple-touch-icon.png', 'etc/2pny/version',
})
PROTECTED = ('usr/local/bin/MMDVM-Host', 'usr/local/bin/DMRGateway', 'usr/local/bin/NextionDriver-pu2pny',
             'usr/local/bin/MMDVM-Display', 'usr/local/sbin/2pny-profile-autostart',
             'usr/local/sbin/2pny-profile-autostart-safe', 'usr/local/sbin/2pny-hardware-probe',
             'usr/local/sbin/2pny-identity-apply', 'usr/share/2pny/protocols.html',
             'usr/local/sbin/2pny-rf-apply',
             'usr/local/sbin/2pny-protocol-network-apply', 'usr/local/sbin/2pny-wifi-apply', 'usr/local/sbin/2pny-protocol-profiles',
             'usr/local/libexec/pu2pny/display/adapter.py',
             'var/lib/2pny/mmdvm/MMDVM-Host.ini')


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def manifest(root):
    result = {}
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != 'lost+found')
        for name in sorted(files + dirs):
            p = Path(directory) / name
            if p.is_symlink():
                result[str(p.relative_to(root))] = {'link': os.readlink(p)}
            elif p.is_file():
                result[str(p.relative_to(root))] = {'sha256': sha(p), 'mode': p.stat().st_mode & 0o7777}
    return result


base = work / f'base-{arch}.img.xz'
assert sha(base) == BASE[arch], 'published 5.07 base checksum mismatch'
print('BASE_SHA_PASS', arch, flush=True)
image = work / f'{arch}.img'
root = work / ('root32' if arch == 'arm32' else 'root64')
loop = ''
mounted = False
try:
    assert not image.exists()
    with image.open('wb') as out:
        run(['xz', '-dc', str(base)], stdout=out)
    root.mkdir(exist_ok=True)
    loop = subprocess.check_output(['losetup', '--find', '--show', '--partscan', str(image)], text=True).strip()
    run(['mount', loop + 'p2', str(root)])
    mounted = True
    assert (root / 'etc/2pny/version').read_text().strip() == '5.07.000'
    print('BASE_MANIFEST_SCAN', arch, flush=True)
    before = manifest(root)
    daemon = work / ('2pnyd-arm' if arch == 'arm32' else '2pnyd-arm64')
    run(['python3', str(repo / 'ci/patch-image-5.08.py'), str(root), arch, str(daemon)])
    print('OVERLAY_MANIFEST_SCAN', arch, flush=True)
    after = manifest(root)
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    assert changed <= ALLOWED, sorted(changed - ALLOWED)
    assert ALLOWED <= changed, sorted(ALLOWED - changed)
    for filename in PROTECTED:
        if filename not in before:
            assert filename not in after, f'{filename} must not appear'
            continue
        assert before[filename] == after[filename], filename
    assert (root / 'etc/2pny/version').read_text().strip() == '5.08.000'
    print('FULL_SCOPE_AND_PROTECTED_FILES_PASS', arch, len(changed), flush=True)
    run(['sync'])
    run(['umount', str(root)])
    mounted = False
    run(['e2fsck', '-fn', loop + 'p2'])
    run(['mount', '-o', 'ro', loop + 'p2', str(root)])
    mounted = True
    print('READONLY_MANIFEST_SCAN', arch, flush=True)
    assert manifest(root) == after, 'readonly_manifest_mismatch'
    run(['umount', str(root)])
    mounted = False
    run(['losetup', '-d', loop])
    loop = ''
    output = work / 'output'
    output.mkdir(exist_ok=True)
    name = 'pu2pny-' + arch[3:] + '-5.08.img.xz'
    dest = output / name
    assert not dest.exists()
    print('COMPRESSING_IMAGE', arch, flush=True)
    with dest.open('wb') as out:
        run(['nice', '-n', '10', 'xz', '-T1', '-6', '-c', str(image)], stdout=out)
    run(['xz', '-t', str(dest)])
    digest = sha(dest)
    (output / (name + '.sha256')).write_text(digest + ' ' + name + '\n')
    info = {'version': '5.08.000', 'classification': 'ALPHA_HW_TEST_CANDIDATE', 'architecture': arch,
            'base_version': '5.07.000', 'base_asset': BASE_NAME[arch], 'base_sha256': BASE[arch],
            'source_tree_sha': source_tree, 'image_sha256': digest, 'bytes': dest.stat().st_size,
            'requirements': ['CLOCK-058', 'DISPLAY-058', 'SPEED-058', 'UI-058', 'BOOT-058', 'EXPERT-058'],
            'validation': {'xz': 'PASS', 'sha256': 'PASS', 'filesystem': 'PASS', 'full_scope_manifest': 'PASS',
                           'rf_binary_preservation': 'PASS', 'HW': 'NOT_VERIFIED', 'PROD': 'NOT_APPROVED'},
            'scope': sorted(changed)}
    (output / f'BUILD-INFO-{arch}.json').write_text(json.dumps(info, indent=2) + '\n')
    print('IMAGE_507_VERIFIED', arch, digest, dest.stat().st_size, flush=True)
finally:
    if mounted:
        subprocess.run(['umount', str(root)], check=False)
    if loop:
        subprocess.run(['losetup', '-d', loop], check=False)
