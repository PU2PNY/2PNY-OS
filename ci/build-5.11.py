#!/usr/bin/env python3
"""Build 5.11 sobre imagens 5.10 verificadas; escopo, donos e RF protegidos."""
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
BASE={'arm32':'f9f53055f0685281a68cefbb94511d79a7f977c1a09f46eb4296f0599d63654c','arm64':'b4e07dd717d62c6d5aa6816bf63051d946516e4759b5d3d96cf9b9cbaf4d4fa3'}
PROTECTED=('usr/local/bin/MMDVM-Host','usr/local/bin/DMRGateway','usr/local/bin/NextionDriver-pu2pny','usr/local/bin/MMDVM-Display','usr/local/bin/2pny-direct-core',
 'usr/local/sbin/2pny-profile-autostart','usr/local/sbin/2pny-profile-autostart-safe','usr/local/sbin/2pny-hardware-probe','usr/local/sbin/2pny-identity-apply','usr/local/sbin/2pny-direct-start','usr/local/sbin/2pny-direct-recover',
 'usr/local/sbin/2pny-rf-apply','usr/local/sbin/2pny-protocol-network-apply','usr/local/sbin/2pny-wifi-apply','usr/local/libexec/pu2pny/display/adapter.py','var/lib/2pny/mmdvm/MMDVM-Host.ini')
# PROTO-511: protocol-profiles deixa a lista apenas para chamar rollback antes da troca.
MODIFIED={'usr/local/bin/2pnyd','usr/local/sbin/2pny-station-worker','usr/local/sbin/2pny-network-core','usr/local/sbin/2pny-mdns-guard','usr/local/sbin/2pny-display-core','usr/local/sbin/2pny-fast-resume','usr/local/sbin/2pny-protocol-profiles',
 'usr/local/sbin/2pny-network-switch','usr/local/sbin/2pny-firstboot','usr/local/sbin/2pny-wifi-profiles','usr/local/libexec/pu2pny/oled-502.py','etc/2pny/version','etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice',
 'usr/share/2pny/display.html','usr/share/2pny/wizard.html','usr/share/2pny/expert.html','usr/share/2pny/system.html','usr/share/2pny/protocols.html','usr/share/2pny/direct.html',
 'usr/share/2pny/ui-language.js','usr/share/2pny/ui-common-0.3.0.js'}
HOST64={'usr/share/2pny/internet.html','usr/share/2pny/network/dnsmasq-ap.template','etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf','etc/NetworkManager/dispatcher.d/90-pu2pny-mdns','usr/local/libexec/pu2pny/lcd-504.py','usr/local/sbin/2pny-mdns-alias','etc/hostname','etc/hosts','etc/avahi/avahi-daemon.conf'}
NEW={'usr/local/libexec/pu2pny/followers-511.py','usr/local/sbin/2pny-voice-apply','usr/local/sbin/2pny-crossmode','usr/local/sbin/2pny-direct-group','usr/local/sbin/2pny-cm-run','etc/tmpfiles.d/2pny-cpu-511.conf','usr/share/2pny/panel-511.js',
 'etc/systemd/system/2pny-hostfiles-update.service.d/511-priority.conf','etc/systemd/system/2pny-auto-maintenance.service.d/511-priority.conf','etc/systemd/system/2pny-voice-apply.service','etc/systemd/system/2pny-mode-apply.service','etc/systemd/system/2pny-cm@.service','etc/systemd/system/2pny-cm-gateway@.service','etc/systemd/system/2pny-direct-group.service','etc/systemd/system/2pny-wifi-autoselect.service','etc/systemd/system/2pny-direct.service.d/511-enabled.conf',
 'etc/systemd/system/2pny-profile-autostart.service.d/511-mode.conf','etc/systemd/system/2pny-profile-autostart-retry.service.d/511-mode.conf','etc/systemd/system/2pny-special-mode-reset.service','etc/systemd/system/multi-user.target.wants/2pny-special-mode-reset.service'}
CONVERTERS=('DMR2YSF','YSF2DMR','DMR2NXDN','YSF2NXDN','YSF2P25')
NEW|={f'usr/local/bin/{n}' for n in CONVERTERS}
NEW|={f'usr/local/libexec/pu2pny/cm-templates/{n}.ini' for n in CONVERTERS}|{'usr/local/libexec/pu2pny/cm-templates/LICENCE'}
NEW|={f'etc/systemd/system/2pny-{p}gateway.service.d/511-voice.conf' for p in ('dmr','dstar','p25','nxdn')}


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def manifest(root):
    result={}
    for directory,dirs,files in os.walk(root):
        dirs[:]=sorted(d for d in dirs if d!='lost+found')
        for n in sorted(dirs+files):
            p=Path(directory)/n;s=p.lstat()
            row={'uid':s.st_uid,'gid':s.st_gid,'mode':stat.S_IMODE(s.st_mode)}
            if p.is_symlink():row['link']=os.readlink(p)
            elif p.is_file():row['sha256']=sha(p)
            elif p.is_dir():row['dir']=True
            else:continue
            result[str(p.relative_to(root))]=row
    return result


def gate(before,after,arch):
    allowed=MODIFIED|(HOST64 if arch=='arm64' else set());allowed|={p+'.pre-5.11' for p in allowed};allowed|=NEW
    for p in set(before)|set(after):
        old,new=before.get(p),after.get(p)
        if old==new:continue
        if old is None and new and new.get('dir'):
            assert any(a.startswith(p+'/') for a in allowed) or p in ('usr/share/2pny/audio/dstar-off','var/lib/2pny/crossmode'),p
            continue
        if old is not None and new is not None:
            expected=dict(old)
            for k in ('uid','gid'):
                if expected[k]==1001:expected[k]=0
            if p=='var/lib/2pny':expected.update(uid=0,gid=0,mode=0o755)
            if expected==new:continue
        assert p in allowed,('fora do escopo',p)
    for p,row in after.items():assert row['uid']!=1001 and row['gid']!=1001,('dono CI',p)
    for p in PROTECTED:
        a,b=before.get(p),after.get(p)
        assert (a is None)==(b is None),p
        if a:
            assert {k:v for k,v in a.items() if k not in ('uid','gid')}=={k:v for k,v in b.items() if k not in ('uid','gid')},p
    for p in (MODIFIED|(HOST64 if arch=='arm64' else set())):
        if before.get(p)!=after.get(p) and p in before and not before[p].get('dir'):
            # Mudança somente de dono não precisa backup de conteúdo.
            if before[p].get('sha256')!=after.get(p,{}).get('sha256'):
                assert after.get(p+'.pre-5.11',{}).get('sha256')==before[p].get('sha256'),('backup',p)


def run(args,**kw):return subprocess.run(args,check=True,**kw)


def compile_cm(root,work,arch):
    copy=work/'cm-root'
    assert not copy.exists()
    try:
        run(['cp','-a','--reflink=auto',str(root),str(copy)])
        policy=copy/'usr/sbin/policy-rc.d';policy.write_text('#!/bin/sh\nexit 101\n');policy.chmod(0o755)
        resolver=copy/'etc/resolv.conf'
        if resolver.is_symlink():resolver.unlink()
        shutil.copyfile('/etc/resolv.conf',resolver)
        run(['git','clone','--quiet','https://github.com/juribeparada/MMDVM_CM.git',str(copy/'build-cm')])
        run(['git','-C',str(copy/'build-cm'),'checkout','--quiet','7328c9e9532d29cf4d9d7d24541d57f825207be4'])
        run(['chroot',str(copy),'/bin/sh','-c','apt-get update -qq && apt-get install -y --no-install-recommends build-essential'])
        output=work/'cm-output';output.mkdir(exist_ok=True)
        for name in CONVERTERS:
            run(['chroot',str(copy),'/bin/sh','-c',f'cd /build-cm/{name} && make -j2 CFLAGS="-O2 -Wall -std=c++0x -pthread"'])
            binary=copy/'build-cm'/name/name
            header=binary.read_bytes()[:20]
            assert (header[4],struct.unpack('<H',header[18:20])[0])==((1,40) if arch=='arm32' else (2,183))
            if arch=='arm32':
                attrs=subprocess.check_output(['readelf','-A',str(binary)],text=True)
                assert 'Tag_CPU_arch: v6' in attrs and 'Tag_CPU_arch: v7' not in attrs,attrs
            shutil.copy2(binary,output/name)
        return output
    finally:
        if copy.exists():shutil.rmtree(copy)


def main():
    work=Path(sys.argv[1]).resolve();arch=sys.argv[2];commit=sys.argv[3]
    assert os.geteuid()==0 and arch in BASE and re.fullmatch('[a-f0-9]{40}',commit)
    base=work/f'base-{arch}.img.xz';assert sha(base)==BASE[arch],'SHA da base 5.10 divergente'
    run(['xz','-t',str(base)])
    image=work/f'{arch}.img';assert not image.exists()
    with image.open('wb') as out:run(['xz','-dc',str(base)],stdout=out)
    loop='';root=work/'root';mounted=False
    try:
        loop=subprocess.check_output(['losetup','--find','--show','--partscan',str(image)],text=True).strip()
        root.mkdir(exist_ok=True);run(['mount',loop+'p2',str(root)]);mounted=True
        assert (root/'etc/2pny/version').read_text().strip()=='5.10.000'
        before=manifest(root)
        # A cópia descartável recebe compilador; a imagem final recebe só os cinco binários.
        cm=compile_cm(root,work,arch)
        binary=work/('2pnyd-arm' if arch=='arm32' else '2pnyd-arm64')
        run(['python3',str(repo/'ci/patch-image-5.11.py'),str(root),arch,str(binary)])
        for name in CONVERTERS:
            shutil.copy2(cm/name,root/'usr/local/bin'/name);os.chown(root/'usr/local/bin'/name,0,0)
        after=manifest(root);gate(before,after,arch)
        # Arquitetura dos binários operacionais, inclusive o Direct corrigido na 5.10.
        for name in ('MMDVM-Host','DMRGateway','NextionDriver-pu2pny','MMDVM-Display','2pny-direct-core','2pnyd',*CONVERTERS):
            b=(root/'usr/local/bin'/name).read_bytes()[:20]
            assert b[:4]==b'\x7fELF' and (b[4],struct.unpack('<H',b[18:20])[0])==((1,40) if arch=='arm32' else (2,183)),name
        # Sem nomes de outros painéis nos textos visíveis. URLs de dados ficam fora deste scan.
        for p in (root/'usr/share/2pny').iterdir():
            if p.suffix in ('.html','.js'):assert not re.search(r'Pi-Star|WPSD',p.read_text()),p
        run(['sync']);run(['umount',str(root)]);mounted=False
        run(['e2fsck','-fn',loop+'p2'])
        run(['mount','-o','ro',loop+'p2',str(root)]);mounted=True
        assert manifest(root)==after,'manifesto RO divergente'
        run(['umount',str(root)]);mounted=False;run(['losetup','-d',loop]);loop=''
        output=work/'output';output.mkdir(exist_ok=True)
        name=f'pu2pny-{arch[3:]}-5.11.img.xz';dest=output/name
        assert not dest.exists()
        with dest.open('wb') as out:run(['xz','-T2','-6','-c',str(image)],stdout=out)
        run(['xz','-t',str(dest)]);digest=sha(dest)
        (output/(name+'.sha256')).write_text(digest+'  '+name+'\n')
        info={'version':'5.11.000','classification':'ALPHA_HW_TEST_CANDIDATE','architecture':arch,
              'base_version':'5.10.000','base_sha256':BASE[arch],'source_commit':commit,'source_tree_sha':commit,
              'image_sha256':digest,'bytes':dest.stat().st_size,'cm_commit':'7328c9e9532d29cf4d9d7d24541d57f825207be4',
              'validation':{'filesystem':'PASS','xz':'PASS','sha256':'PASS','full_scope_manifest':'PASS','rf_binary_preservation':'PASS','uid_gid_1001':'ABSENT','HW':'NOT_VERIFIED','PROD':'NOT_APPROVED'}}
        (output/f'BUILD-INFO-{arch}.json').write_text(json.dumps(info,indent=2)+'\n')
        (output/f'MANIFEST-{arch}.json').write_text(json.dumps({'before':before,'after':after},sort_keys=True))
        print('IMAGE_511_VERIFIED',arch,digest,flush=True)
    finally:
        if mounted:subprocess.run(['umount',str(root)],check=False)
        if loop:subprocess.run(['losetup','-d',loop],check=False)

if __name__=='__main__':main()
