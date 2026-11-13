#!/usr/bin/env python3
"""REL-512: overlay P0 sobre a imagem 5.11 imutável, sem recompilar RF ou alterar rede."""
import hashlib
import importlib.util
import json
import os
import re
import stat
import struct
import subprocess
import sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
BASE={
  'arm32':'6a90ac0080fd72c28d3df8d52b44d076bb7764bd530b5673798180987a1262d9',
  'arm64':'b8b6d844230c0611566625ab050e30dfbf89ca7adb367412e4f14a4bcf0bb103',
}
ALLOWED={
    'etc/2pny/version',
    'etc/2pny/version.pre-5.12',
    'etc/systemd/system/2pny-auto-maintenance.timer',
    'etc/systemd/system/timers.target.wants/2pny-auto-maintenance.timer',
}
for name in ('2pny-auto-maintenance','2pny-hostfiles-update'):
    ALLOWED.add(f'etc/systemd/system/{name}.service.d/60-delay.conf')
    ALLOWED.add(f'etc/systemd/system/{name}.service.d/60-delay.conf.pre-5.12')
    ALLOWED.add(f'etc/systemd/system/multi-user.target.wants/{name}.service')

def run(command, **kw):
    return subprocess.run(command, check=True, **kw)

def sha(path):
    with Path(path).open('rb') as fh:return hashlib.file_digest(fh,'sha256').hexdigest()

def module(filename, name):
    spec=importlib.util.spec_from_file_location(name,REPO/'ci'/filename)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

COMMON=module('build-5.11.py','builder511_manifest')
manifest=COMMON.manifest
PROTECTED=COMMON.PROTECTED

def gate(before, after, protected):
    changes={p for p in set(before)|set(after) if before.get(p)!=after.get(p)}
    unexpected=changes-ALLOWED
    assert not unexpected, 'alterações fora do escopo: '+repr(sorted(unexpected)[:20])
    for p in protected:
        assert before.get(p)==after.get(p), 'baseline protegida: '+p
    for name in ('2pny-auto-maintenance','2pny-hostfiles-update'):
        delay=f'etc/systemd/system/{name}.service.d/60-delay.conf'
        backup=delay+'.pre-5.12'
        assert delay in before and delay not in after
        assert after[backup]['sha256']==before[delay]['sha256']
        assert f'etc/systemd/system/multi-user.target.wants/{name}.service' not in after
    assert after['etc/2pny/version.pre-5.12']['sha256']==before['etc/2pny/version']['sha256']
    assert 'etc/systemd/system/2pny-auto-maintenance.timer' in after
    assert 'etc/systemd/system/timers.target.wants/2pny-auto-maintenance.timer' in after
    for p, metadata in after.items():
        assert metadata['uid']!=1001 and metadata['gid']!=1001, 'dono CI: '+p

def main():
    assert len(sys.argv)==4, 'uso: build-5.12.py WORKDIR ARM32|ARM64 COMMIT'
    work=Path(sys.argv[1]).resolve();arch=sys.argv[2];commit=sys.argv[3]
    assert os.geteuid()==0 and arch in BASE and re.fullmatch(r'[a-f0-9]{40}',commit)
    base=work/f'base-{arch}.img.xz'
    assert base.is_file() and sha(base)==BASE[arch], 'SHA-256 da base 5.11 divergente'
    run(['xz','-t',str(base)])
    image=work/f'{arch}.img'
    assert not image.exists(), 'imagem de saída já existe'
    with image.open('wb') as dst:run(['xz','-dc',str(base)],stdout=dst)
    original=module('build-5.11.py','builder511')
    patch=module('patch-image-5.12.py','patch512')
    loop=''
    root=work/f'root-{arch}'
    mounted=False
    try:
        loop=subprocess.check_output(['losetup','--find','--show','--partscan',str(image)],text=True).strip()
        root.mkdir(exist_ok=False)
        run(['mount',loop+'p2',str(root)])
        mounted=True
        assert (root/'etc/2pny/version').read_text().strip()=='5.11.000'
        before=original.manifest(root)
        patch.apply(root)
        after=original.manifest(root)
        gate(before,after,original.PROTECTED)
        for executable in ('MMDVM-Host','DMRGateway','NextionDriver-pu2pny','MMDVM-Display','2pny-direct-core','2pnyd'):
            header=(root/'usr/local/bin'/executable).read_bytes()[:20]
            assert header[:4]==b'\x7fELF'
            assert (header[4],struct.unpack('<H',header[18:20])[0])==((1,40) if arch=='arm32' else (2,183)),executable
        run(['sync'])
        run(['umount',str(root)]);mounted=False
        result=subprocess.run(['e2fsck','-fn',loop+'p2'],check=False)
        assert result.returncode==0,'filesystem com inconsistência após alteração'
        run(['mount','-o','ro',loop+'p2',str(root)]);mounted=True
        assert original.manifest(root)==after, 'imagem remontada RO divergente'
        assert (root/'etc/2pny/version').read_text().strip()=='5.12.000'
        run(['umount',str(root)]);mounted=False
        run(['losetup','-d',loop]);loop=''
        output=work/'output';output.mkdir(exist_ok=True)
        name=f'pu2pny-{arch[3:]}-5.12.img.xz'
        dest=output/name
        assert not dest.exists()
        with dest.open('wb') as dst:run(['xz','-T2','-6','-c',str(image)],stdout=dst)
        run(['xz','-t',str(dest)])
        digest=sha(dest)
        (output/(name+'.sha256')).write_text(digest+'  '+name+'\n')
        info={'version':'5.12.000','scope':'BOOT-512_NET-512_P0_ONLY',
              'classification':'ALPHA_HW_TEST_CANDIDATE','architecture':arch,
              'source_commit':commit,'source_tree_sha':subprocess.check_output(
                  ['git','rev-parse',commit+'^{tree}'],cwd=REPO,text=True).strip(),
              'base_sha256':BASE[arch],'image_sha256':digest,'bytes':dest.stat().st_size,
              'validation':{'filesystem':'PASS','xz':'PASS','sha256':'PASS',
                  'scope_manifest':'PASS','protected_rf':'PASS','HW':'NOT_VERIFIED',
                  'PROD':'NOT_APPROVED'}}
        (output/f'BUILD-INFO-{arch}.json').write_text(json.dumps(info,indent=2)+'\n')
        (output/f'MANIFEST-{arch}.json').write_text(json.dumps(
            {'before':before,'after':after},sort_keys=True))
        print('IMAGE_512_P0_VERIFIED',arch,digest,flush=True)
    finally:
        if mounted:subprocess.run(['umount',str(root)],check=False)
        if loop:subprocess.run(['losetup','-d',loop],check=False)

if __name__=='__main__':main()
