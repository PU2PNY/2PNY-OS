#!/usr/bin/env python3
"""BOARD-512: transplantar userland sem substituir kernel/bootloader da placa."""
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]

def run(args,**kw):return subprocess.run(args,check=True,**kw)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def copy(src,dst):
    # Overlay arquivo a arquivo: copytree(dirs_exist_ok=True) falha se
    # usr/local/man já for um symlink do Armbian. Nunca seguir symlinks.
    if src.is_dir() and not src.is_symlink():
        if dst.is_symlink() or (dst.exists() and not dst.is_dir()):
            raise ValueError(f'destino inseguro para diretório: {dst}')
        dst.mkdir(parents=True,exist_ok=True)
        for item in sorted(src.iterdir()):
            copy(item,dst/item.name)
    else:
        dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.is_dir() and not dst.is_symlink():
            raise ValueError(f'destino inesperado para arquivo: {dst}')
        if dst.is_symlink() or dst.exists():dst.unlink()
        if src.is_symlink():dst.symlink_to(os.readlink(src))
        else:shutil.copy2(src,dst)

def configure_boot_services(root):
    # BOARD-512: NetworkManager é o único dono da rede. As bases minimal
    # podem habilitar networkd; a NanoPi 23.8.1 habilita firstrun-config.
    units=root/'etc/systemd/system';units.mkdir(parents=True,exist_ok=True)
    for unit in ('armbian-firstrun.service','armbian-firstrun-config.service',
                 'armbian-firstlogin.service','unattended-upgrades.service',
                 'apt-daily.timer','apt-daily-upgrade.timer','ssh.service',
                 'systemd-networkd.service','systemd-networkd.socket',
                 'systemd-networkd-wait-online.service'):
        p=units/unit
        if p.exists() or p.is_symlink():
            if p.is_dir():raise ValueError('unidade inesperada')
            p.unlink()
        p.symlink_to('/dev/null')
    wants=units/'multi-user.target.wants';wants.mkdir(parents=True,exist_ok=True)
    nm=wants/'NetworkManager.service'
    if nm.exists() or nm.is_symlink():nm.unlink()
    nm.symlink_to('/lib/systemd/system/NetworkManager.service')
    (root/'root/.not_logged_in_yet').unlink(missing_ok=True)


def prepare_chroot_devices(root):
    """As bases minimal Armbian podem trazer /dev/null não gravável.
    Corrigir somente nós Linux padrão, sem bind-mount do /dev do runner."""
    device=root/'dev'
    assert device.is_dir() and not device.is_symlink(), 'dev inválido'
    for name,major,minor in (('null',1,3),('zero',1,5),('random',1,8),
                             ('urandom',1,9),('tty',5,0)):
        node=device/name
        assert not node.is_symlink(), ('dispositivo inesperado',name)
        if node.exists():
            st=node.stat()
            if not (stat.S_ISCHR(st.st_mode) and
                    (os.major(st.st_rdev),os.minor(st.st_rdev))==(major,minor)):
                raise ValueError('dispositivo inválido: '+name)
        else:
            os.mknod(node,stat.S_IFCHR|0o666,os.makedev(major,minor))
        os.chown(node,0,0)
        os.chmod(node,0o666)

def configure(root,source):
    prepare_chroot_devices(root)
    for name in ('usr/local','usr/share/2pny','etc/2pny','var/lib/2pny','etc/avahi'):
        copy(source/name,root/name)
    for part in ('conf.d','dispatcher.d','dnsmasq-shared.d','system-connections'):
        p=source/'etc/NetworkManager'/part
        if p.exists():copy(p,root/'etc/NetworkManager'/part)
    for part in ('mosquitto/conf.d','udev/rules.d','systemd/journald.conf.d','tmpfiles.d'):
        p=source/'etc'/part
        if p.exists():copy(p,root/'etc'/part)
    units=root/'etc/systemd/system';units.mkdir(parents=True,exist_ok=True)
    for p in (source/'etc/systemd/system').glob('2pny-*'):copy(p,units/p.name)
    # NET-512: 2pnyd (sem hífen) era excluído por 2pny-* na 5.11.
    # Sem a unit e seu vínculo, o AP pode funcionar sem painel HTTP.
    panel=source/'etc/systemd/system/2pnyd.service'
    assert panel.is_file() and not panel.is_symlink(), 'NET-512: unit 2pnyd ausente na origem'
    copy(panel,units/panel.name)
    for name in ('pu2pny-capabilities.service','pu2pny-capabilities.timer'):
        optional=source/'etc/systemd/system'/name
        if optional.is_file() and not optional.is_symlink():copy(optional,units/name)
    for wants in ('multi-user.target.wants','timers.target.wants','paths.target.wants'):
        p=source/'etc/systemd/system'/wants
        if p.exists():
            for item in p.glob('2pny-*'):copy(item,units/wants/item.name)
            # O vínculo do painel não começa com 2pny-.
            extras=('2pnyd.service','pu2pny-capabilities.service','pu2pny-capabilities.timer')
            for name in extras:
                item=p/name
                if item.is_symlink():copy(item,units/wants/item.name)
    enabled=units/'multi-user.target.wants/2pnyd.service'
    assert enabled.is_symlink(), 'NET-512: painel não habilitado em multi-user.target'
    assert os.path.basename(os.readlink(enabled))=='2pnyd.service', 'NET-512: symlink de painel incorreto'
    # Proibir a execução de serviços durante apt na imagem offline.
    policy=root/'usr/sbin/policy-rc.d';prior=policy.read_bytes() if policy.exists() else None
    policy.write_text('#!/bin/sh\nexit 101\n');policy.chmod(0o755)
    resolver=root/'etc/resolv.conf'
    resolver_link=os.readlink(resolver) if resolver.is_symlink() else None
    resolver_data=resolver.read_bytes() if resolver.exists() and not resolver.is_symlink() else None
    resolver_mode=stat.S_IMODE(resolver.stat().st_mode) if resolver_data is not None else None
    if resolver.exists() or resolver.is_symlink():resolver.unlink()
    shutil.copyfile('/etc/resolv.conf',resolver)
    deps=['python3','python3-pil','python3-smbus','i2c-tools','fonts-dejavu-core','mosquitto','mosquitto-clients','network-manager','avahi-daemon','dnsmasq-base','hostapd','iw','rfkill','iptables','libstdc++6','libgcc-s1','libc6','libmosquitto1','libgpiod2','libasound2','libusb-1.0-0','libcurl4','libssl3']
    # apt/dpkg em um filesystem offline precisam de /proc temporário.
    # Preservar o conffile Avahi do PU2PNY, sem prompt interativo.
    proc=root/'proc'
    assert proc.is_dir() and not proc.is_symlink(), 'proc inválido'
    run(['mount','-t','proc','proc',str(proc)])
    try:
        run(['chroot',str(root),'apt-get','update','-qq'])
        run(['chroot',str(root),'env','DEBIAN_FRONTEND=noninteractive',
             'APT_LISTCHANGES_FRONTEND=none','apt-get','install','-y',
             '-o','Dpkg::Options::=--force-confdef',
             '-o','Dpkg::Options::=--force-confold',
             '--no-install-recommends',*deps])
        audit=subprocess.run(['chroot',str(root),'dpkg','--audit'],
                             capture_output=True,text=True,check=True)
        assert not audit.stdout.strip(),('pacotes não configurados',audit.stdout)
    finally:
        run(['umount',str(proc)])
        resolver.unlink(missing_ok=True)
        if resolver_link is not None:resolver.symlink_to(resolver_link)
        elif resolver_data is not None:
            resolver.write_bytes(resolver_data)
            resolver.chmod(resolver_mode)
    # Bibliotecas ausentes impedem a entrega. Não copiar ld-linux/libc da Raspberry sobre Armbian.
    for p in sorted((root/'usr/local/bin').iterdir()):
        if not p.is_file() or '.pre-' in p.name or p.read_bytes()[:4]!=b'\x7fELF':continue
        head=p.read_bytes()[:20]
        assert (head[4],struct.unpack('<H',head[18:20])[0])==(1,40),p
        cp=subprocess.run(['chroot',str(root),'ldd','/usr/local/bin/'+p.name],capture_output=True,text=True)
        assert 'not found' not in cp.stdout+cp.stderr,('dependência ausente',p.name,cp.stdout+cp.stderr)
        # Namespace de rede isolado e INI inexistente: nunca abrir RF ou portas do host de build.
        cp=subprocess.run(['unshare','--net','--fork','chroot',str(root),'/usr/bin/timeout','3','/usr/local/bin/'+p.name,'--version'],capture_output=True,text=True)
        assert cp.returncode not in (126,127) and 'unshare failed' not in cp.stderr,('execução ARM falhou',p.name,cp.stderr[-300:])
    if prior is None:policy.unlink()
    else:policy.write_bytes(prior);policy.chmod(0o755)
    run(['chroot',str(root),'/bin/sh','-c','getent group mmdvm >/dev/null || groupadd --system mmdvm; id mmdvm >/dev/null 2>&1 || useradd --system --gid mmdvm --no-create-home --shell /usr/sbin/nologin mmdvm; usermod -aG dialout mmdvm'])
    configure_boot_services(root)
    # Gate antes de concluir a imagem. A presença do binário sozinha não basta.
    assert (root/'etc/systemd/system/2pnyd.service').is_file()
    assert (root/'etc/systemd/system/multi-user.target.wants/2pnyd.service').is_symlink()
    assert (root/'usr/local/bin/2pnyd').is_file()
    (root/'etc/hostname').write_text('pu2pny32\n')
    hosts=root/'etc/hosts';lines=hosts.read_text().splitlines()
    lines=[l for l in lines if not l.startswith('127.0.1.1')];lines.append('127.0.1.1\tpu2pny32');hosts.write_text('\n'.join(lines)+'\n')
    env=root/'boot/armbianEnv.txt';text=env.read_text();lines=text.splitlines();found=False
    for i,line in enumerate(lines):
        if line.startswith('overlays='):
            assert not found,'overlays duplicados';found=True
            values=line.partition('=')[2].split();values+=['uart1','i2c0'];lines[i]='overlays='+' '.join(dict.fromkeys(values))
    if not found:lines.append('overlays=uart1 i2c0')
    env.write_text('\n'.join(lines)+'\n')
    rule=root/'etc/udev/rules.d/60-pu2pny-serial.rules'
    rule.write_text('SUBSYSTEM=="tty", KERNEL=="ttyS1", SYMLINK+="serial0", GROUP="dialout", MODE="0660"\n')
    for d,dirs,files in os.walk(root):
        for n in dirs+files:
            p=Path(d)/n
            # Todo conteúdo transplantado deve ser root; dados de pacotes preservam donos próprios.
            if any(str(p.relative_to(root)).startswith(prefix) for prefix in ('usr/local/','usr/share/2pny/','etc/2pny/','var/lib/2pny/','etc/NetworkManager/','etc/avahi/')):
                os.chown(p,0,0,follow_symlinks=False)
            elif p.lstat().st_uid==1001 or p.lstat().st_gid==1001:os.chown(p,0,0,follow_symlinks=False)
    os.chown(root/'var/lib/2pny',0,0);(root/'var/lib/2pny').chmod(0o755)
    run(['chroot',str(root),'systemctl','list-unit-files','--no-pager'])
    run(['chroot',str(root),'/bin/true'])
    run(['chroot',str(root),'apt-get','clean'])


def main():
    work=Path(sys.argv[1]).resolve();board=sys.argv[2];commit=sys.argv[3]
    assert os.geteuid()==0 and board in ('opizero','nanopineo') and re.fullmatch('[a-f0-9]{40}',commit)
    lock=json.loads((REPO/'ci/board-bases-5.11.json').read_text())[board]
    if not lock.get('url') or not re.fullmatch('[a-f0-9]{64}',lock.get('sha256') or ''):raise SystemExit('BOARD-512 BLOQUEADO: '+lock['blocked'])
    source_image=work/'pu2pny-32-5.12.img.xz';info=json.loads((work/'BUILD-INFO-arm32.json').read_text())
    assert sha(source_image)==info['image_sha256'] and info['version']=='5.12.000' and info['source_commit']==commit
    base=work/f'{board}-base.img.xz'
    # A origem primária do arquivo Armbian pode retornar 502. Espelhos
    # somente são aceitos com o SHA-256 imutável já validado; nunca mudar
    # a distribuição, placa, kernel ou versão da imagem para contornar 502.
    mirrors=[lock['url'],*lock.get('mirrors',[])]
    for url in mirrors:
        base.unlink(missing_ok=True)
        status=subprocess.run(['curl','-fL','--retry','2','--retry-all-errors',
                               '--connect-timeout','20','--max-time','360',
                               url,'-o',str(base)],check=False).returncode
        if status:
            continue
        if sha(base)!=lock['sha256']:
            raise ValueError('SHA Armbian divergente em '+url)
        print('BOARD_512_BASE_VERIFIED',board,url,flush=True)
        break
    else:
        raise RuntimeError('BOARD-512: nenhuma origem do arquivo pinado respondeu com sucesso')
    run(['xz','-t',str(base)])
    image=work/(board+'.img');srcimage=work/'source32.img'
    for packed,out in ((base,image),(source_image,srcimage)):
        assert not out.exists()
        with out.open('wb') as f:run(['xz','-dc',str(packed)],stdout=f)
    loops=[];mounts=[]
    root=work/'root';source=work/'source';root.mkdir();source.mkdir()
    try:
        for img,target,partition in ((srcimage,source,'p2'),(image,root,'p1')):
            loop=subprocess.check_output(['losetup','--find','--show','--partscan',str(img)],text=True).strip();loops.append(loop)
            # Bases Armbian sunxi oficiais usam rootfs único; falha se a estrutura divergir.
            run(['mount']+(['-o','ro'] if target==source else [])+[loop+partition,str(target)]);mounts.append(target)
        assert (root/'etc/os-release').read_text().find('bookworm')>=0
        assert (root/'boot/armbianEnv.txt').is_file()
        # Expandir apenas a partição rootfs, preservando os setores de U-Boot anteriores a ela.
        run(['umount',str(root)]);mounts.remove(root)
        run(['losetup','-d',loops[1]]);loops.pop()
        with image.open('ab') as f:f.truncate(image.stat().st_size+2*1024**3)
        table=json.loads(subprocess.check_output(['sfdisk','--json',str(image)],text=True))['partitiontable']
        assert len(table['partitions'])==1
        start=table['partitions'][0]['start']
        original=table['partitions'][0]['size']
        # sfdisk -N 1 com tamanho vazio preserva o tamanho antigo nas
        # imagens sunxi. Informar o número exato de setores, sem mexer no
        # início da partição ou nos setores que contêm o U-Boot.
        sectors=image.stat().st_size//512
        size=sectors-start-2048
        assert size>original+1024**3//512,('expansão insuficiente',original,size)
        run(['sfdisk','--no-reread','-N','1',str(image)],
            input=f'{start},{size},83\n',text=True)
        changed=json.loads(subprocess.check_output(['sfdisk','--json',str(image)],text=True))['partitiontable']['partitions'][0]
        assert changed['start']==start and changed['size']==size,('partição não expandida',changed)
        loop=subprocess.check_output(['losetup','--find','--show','--partscan',str(image)],text=True).strip();loops.append(loop)
        result=subprocess.run(['e2fsck','-fy',loop+'p1'],check=False);assert result.returncode in (0,1),'fsck Armbian falhou'
        run(['resize2fs',loop+'p1']);run(['mount',loop+'p1',str(root)]);mounts.append(root)
        spec=importlib.util.spec_from_file_location('builder511',REPO/'ci/build-5.12.py')
        common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)
        before=common.manifest(root)
        with image.open('rb') as f:f.seek(512);bootloader=hashlib.sha256(f.read(start*512-512)).hexdigest()
        configure(root,source)
        after=common.manifest(root)
        for path,row in before.items():
            if (path.startswith('boot/') and path!='boot/armbianEnv.txt') or path.startswith('usr/lib/modules/') or path.startswith('lib/modules/'):
                assert row==after.get(path),('kernel/boot fora do escopo',path)
        for path,row in after.items():assert row['uid']!=1001 and row['gid']!=1001,('dono CI',path)
        with image.open('rb') as f:f.seek(512);assert hashlib.sha256(f.read(start*512-512)).hexdigest()==bootloader,'bootloader alterado'
        # Userland RF protegido é transplantado byte a byte.
        for name in ('MMDVM-Host','DMRGateway','NextionDriver-pu2pny','MMDVM-Display','2pny-direct-core'):
            assert sha(root/'usr/local/bin'/name)==sha(source/'usr/local/bin'/name),name
        run(['sync']);run(['umount',str(root)]);mounts.remove(root);run(['e2fsck','-fn',loop+'p1'])
        run(['mount','-o','ro',loop+'p1',str(root)]);mounts.append(root)
        assert (root/'etc/2pny/version').read_text().strip()=='5.12.000'
        assert 'uart1' in (root/'boot/armbianEnv.txt').read_text()
        assert common.manifest(root)==after,'manifesto RO da placa divergente'
        run(['umount',str(root)]);mounts.remove(root)
        for l in reversed(loops):run(['losetup','-d',l])
        loops=[]
        output=work/'output';output.mkdir(exist_ok=True);name=f'pu2pny-{board}-5.12.img.xz';dest=output/name
        with dest.open('wb') as f:run(['xz','-T2','-6','-c',str(image)],stdout=f)
        run(['xz','-t',str(dest)]);digest=sha(dest)
        (output/(name+'.sha256')).write_text(digest+'  '+name+'\n')
        info={'version':'5.12.000','classification':'ALPHA_HW_TEST_CANDIDATE','architecture':board,'source_commit':commit,'base':lock,'userland_sha256':sha(source_image),'image_sha256':digest,'bytes':dest.stat().st_size,'validation':{'filesystem':'PASS','xz':'PASS','sha256':'PASS','chroot':'PASS','kernel_bootloader':'PASS','full_scope_manifest':'RECORDED','uid_gid_1001':'ABSENT','HW':'NOT_VERIFIED','PROD':'NOT_APPROVED'}}
        (output/f'BUILD-INFO-{board}.json').write_text(json.dumps(info,indent=2)+'\n')
        (output/f'MANIFEST-{board}.json').write_text(json.dumps({'before':before,'after':after},sort_keys=True))
        print('BOARD_512_VERIFIED',board,digest)
    finally:
        for p in reversed(mounts):subprocess.run(['umount',str(p)],check=False)
        for l in reversed(loops):subprocess.run(['losetup','-d',l],check=False)

if __name__=='__main__':main()
