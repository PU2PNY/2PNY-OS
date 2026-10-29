#!/usr/bin/env python3
"""Serial VPS image build from checksum-verified published bases; root required."""
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
BASE = {'arm32':'2145cdf81fffa8c3821289a68b2d35c99504f8387eed575d5f4f9ee7adf35533',
        'arm64':'a3ae728d8cc21d894f29c934363a5da97a4898219c25c6b97ba69843aaeafef0'}

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def manifest(root):
    result = {}
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != 'lost+found')
        for name in sorted(files+dirs):
            p = Path(directory)/name
            if p.is_symlink():
                result[str(p.relative_to(root))] = {'link':os.readlink(p)}
            elif p.is_file():
                result[str(p.relative_to(root))] = {'sha256':sha(p),'mode':p.stat().st_mode&0o7777}
    return result

base = work/f'base-{arch}.img.xz'
assert sha(base) == BASE[arch]
print('BASE_SHA_PASS', arch, flush=True)
# xz -dc below verifies the base stream while extracting; do not decode twice.
image = work/f'{arch}.img'
root = work/('root32' if arch=='arm32' else 'root64')
loop_file = work/('loop32' if arch=='arm32' else 'loop64')
loop = ''
mounted = False
try:
    if loop_file.exists():
        loop = loop_file.read_text().strip()
        source = subprocess.check_output(['findmnt','-n','-o','SOURCE','--target',str(root)],text=True).strip()
        assert source == loop+'p2'
        mounted = True
    else:
        assert not image.exists()
        with image.open('wb') as out:
            run(['xz','-dc',str(base)],stdout=out)
        root.mkdir(exist_ok=True)
        loop = subprocess.check_output(['losetup','--find','--show','--partscan',str(image)],text=True).strip()
        loop_file.write_text(loop)
        run(['mount',loop+'p2',str(root)])
        mounted = True
    assert (root/'etc/2pny/version').read_text().strip()=='5.01.002'
    print('BASE_MANIFEST_SCAN', arch, flush=True)
    before = manifest(root)
    binary = work/('2pnyd-arm' if arch=='arm32' else '2pnyd-arm64')
    elf = subprocess.check_output(['file',str(binary)],text=True)
    assert ('32-bit' in elf and 'ARM' in elf) if arch=='arm32' else 'aarch64' in elf
    run(['python3',str(repo/'ci/patch-image-5.02.py'),str(root),str(binary),arch])
    print('OVERLAY_MANIFEST_SCAN', arch, flush=True)
    after = manifest(root)
    changed = {p for p in set(before)|set(after) if before.get(p)!=after.get(p)}
    allowed = {'usr/local/bin/2pnyd','usr/local/bin/2pnyd.pre-5.02',
        'usr/local/libexec/pu2pny/diagnostics-502.py','usr/local/libexec/pu2pny/reset-mmdvm-502.py',
        'usr/local/libexec/pu2pny/display/adapter.py','usr/local/sbin/2pny-display-apply.pre-5.00.002',
        'usr/local/libexec/pu2pny/oled-502.py','usr/local/sbin/2pny-display-core',
        'etc/systemd/system/2pny-reset-mmdvm.service','etc/systemd/system/2pny-reset-mmdvm.path',
        'etc/systemd/system/multi-user.target.wants/2pny-reset-mmdvm.path',
        'usr/share/2pny/hotspot.html','usr/share/2pny/expert.html','usr/share/2pny/internet.html',
        'usr/share/2pny/system.html','etc/2pny/version'}
    assert changed <= allowed, sorted(changed-allowed)
    for filename in ('usr/local/libexec/pu2pny/diagnostics-502.py','usr/local/libexec/pu2pny/reset-mmdvm-502.py',
                     'usr/local/libexec/pu2pny/display/adapter.py','usr/local/sbin/2pny-display-apply.pre-5.00.002',
                     'usr/local/libexec/pu2pny/oled-502.py','usr/local/sbin/2pny-display-core'):
        compile((root/filename).read_bytes(),filename,'exec')
    assert (root/'etc/2pny/version').read_text().strip()=='5.02.000'
    for filename in ('usr/local/bin/MMDVM-Host','usr/local/bin/DMRGateway','usr/local/bin/NextionDriver-pu2pny',
                     'usr/local/bin/MMDVM-Display','var/lib/2pny/mmdvm/MMDVM-Host.ini'):
        if filename == 'var/lib/2pny/mmdvm/MMDVM-Host.ini' and filename not in before:
            assert filename not in after, 'unprovisioned RF configuration must remain absent'
            continue
        assert before[filename]==after[filename], filename
    print('FULL_SCOPE_AND_PROTECTED_FILES_PASS', arch, len(changed), flush=True)
    run(['systemd-analyze','--root='+str(root),'verify','2pny-reset-mmdvm.service','2pny-reset-mmdvm.path'])
    run(['sync'])
    run(['umount',str(root)])
    mounted = False
    run(['e2fsck','-fn',loop+'p2'])
    run(['mount','-o','ro',loop+'p2',str(root)])
    mounted = True
    print('READONLY_MANIFEST_SCAN', arch, flush=True)
    assert manifest(root)==after, 'readonly_manifest_mismatch'
    run(['umount',str(root)])
    mounted = False
    run(['losetup','-d',loop])
    loop = ''
    loop_file.unlink()
    output = work/'output'
    output.mkdir(exist_ok=True)
    name = 'pu2pny-'+arch[3:]+'-5.02.img.xz'
    dest = output/name
    assert not dest.exists()
    print('COMPRESSING_IMAGE', arch, flush=True)
    with dest.open('wb') as out:
        run(['nice','-n','10','xz','-T1','-6','-c',str(image)],stdout=out)
    run(['xz','-t',str(dest)])
    digest = sha(dest)
    (output/(name+'.sha256')).write_text(digest+'  '+name+'\n')
    info = {'version':'5.02.000','classification':'ALPHA_HW_TEST_CANDIDATE','architecture':arch,
        'base_version':'5.01.002','base_sha256':BASE[arch],'source_tree_sha':source_tree,
        'image_sha256':digest,'bytes':dest.stat().st_size,
        'validation':{'xz':'PASS','sha256':'PASS','filesystem':'PASS','full_scope_manifest':'PASS',
                      'rf_binary_preservation':'PASS','HW':'NOT_VERIFIED','PROD':'NOT_APPROVED'},
        'scope':sorted(changed)}
    (output/f'BUILD-INFO-{arch}.json').write_text(json.dumps(info,indent=2)+'\n')
    (work/f'BASELINE-MANIFEST-{arch}.json').write_text(json.dumps(before,sort_keys=True))
    (work/f'IMAGE-MANIFEST-{arch}.json').write_text(json.dumps(after,sort_keys=True))
    print('IMAGE_502_VERIFIED',arch,digest,dest.stat().st_size,flush=True)
finally:
    if mounted:
        subprocess.run(['umount',str(root)],check=False)
    if loop:
        subprocess.run(['losetup','-d',loop],check=False)
