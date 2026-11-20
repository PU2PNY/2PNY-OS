#!/usr/bin/env python3
"""Build and validate 5.13 against the four published P2 board images."""
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
P2={
 '32':('98b91cfbed30b7bf81dad8b3f3a522a190372ebbc81484c461f67993c3890dbf','p2',1),
 '64':('2d4bb3c8b59b254356cf3007f21c7fbde5bf99063e9c12f0f331fa4a83f6954a','p2',2),
 'opizero':('35c0cc35bf4173b6b905cbba99ef1ef3ea848f8ffae132e54d06b7b887ead647','p1',1),
 'nanopineo':('74df2d381cc60f7e0999d3bb874ffc06a98e5c4a8ac022d59298bcd08bb3e075','p1',1),
}
def run(argv,**kw):
 return subprocess.run(argv,check=True,**kw)
def sha(path):
 with open(path,'rb') as fh:return hashlib.file_digest(fh,'sha256').hexdigest()
def mod(path,name):
 spec=importlib.util.spec_from_file_location(name,REPO/path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
M=mod('ci/build-5.11.py','old_manifest')
P=mod('ci/patch-image-5.13.py','overlay_513')

def main():
 assert len(sys.argv)==5,'usage: build-5.13.py WORKDIR BOARD COMMIT BACKEND'
 work=Path(sys.argv[1]).resolve();board=sys.argv[2];commit=sys.argv[3];backend=Path(sys.argv[4]).resolve()
 assert os.geteuid()==0 and work!=Path('/') and board in P2
 assert re.fullmatch(r'[a-f0-9]{40}',commit)
 expected,partition,elf_class=P2[board]
 base=work/f'pu2pny-{board}-5.12.002.img.xz'
 assert base.is_file() and sha(base)==expected,'published P2 SHA mismatch'
 run(['xz','-t',str(base)])
 image=work/f'{board}.img';root=work/f'mount-{board}'
 assert not image.exists() and not root.exists()
 with image.open('wb') as out:run(['xz','-dc',str(base)],stdout=out)
 # Never modify partition tables or bootloader; first 1 MiB is checked byte-for-byte.
 with image.open('rb') as f:boot_hash=hashlib.sha256(f.read(1048576)).hexdigest()
 loop='';mounted=False
 try:
  loop=subprocess.check_output(['losetup','--find','--show','--partscan',str(image)],text=True).strip()
  root.mkdir()
  run(['mount',loop+partition,str(root)]);mounted=True
  assert (root/'etc/2pny/version').read_text().strip()=='5.12.002'
  before=M.manifest(root)
  changed=P.apply(root,board,backend)
  after=M.manifest(root)
  manifest_changed={p for p in set(before)|set(after) if before.get(p)!=after.get(p)}
  assert manifest_changed==changed | {p for p in manifest_changed if p not in before and after.get(p,{}).get('dir')},('5.13 altered undeclared paths',sorted(manifest_changed^changed))
  for path in (*M.PROTECTED,'usr/local/sbin/2pny-voice-apply'):
   assert before.get(path)==after.get(path),'RF/Nextion baseline changed: '+path
  for path in changed:
   if path.endswith('.pre-5.13'):
    original=path[:-len('.pre-5.13')]
    assert before[original]['sha256']==after[path]['sha256'],'rollback hash mismatch: '+path
  assert after['etc/2pny/version']['sha256']!=before['etc/2pny/version']['sha256']
  assert (root/'usr/local/bin/2pnyd').read_bytes()[:4]==b'\x7fELF'
  for bin_name in ('MMDVM-Host','DMRGateway','NextionDriver-pu2pny','MMDVM-Display','2pnyd'):
   hdr=(root/'usr/local/bin'/bin_name).read_bytes()[:20]
   assert hdr[:4]==b'\x7fELF' and hdr[4]==elf_class and struct.unpack('<H',hdr[18:20])[0]==(183 if elf_class==2 else 40),bin_name
  if board in ('opizero','nanopineo'):
   assert after['etc/systemd/system/hostapd.service'].get('link')=='/dev/null'
   assert 'MemoryMax=128M' in (root/'etc/systemd/system/2pnyd.service.d/62-board-portal.conf').read_text()
   assert (root/'etc/systemd/system/multi-user.target.wants/2pnyd.service').is_symlink()

  assert (root/'usr/local/bin/2pnyd').read_bytes()==backend.read_bytes()
  for p,v in after.items():
   assert v['uid']!=1001 and v['gid']!=1001,('CI owner leaked',p)
  run(['sync'])
  run(['umount',str(root)]);mounted=False
  fsck=subprocess.run(['e2fsck','-fn',loop+partition],check=False)
  assert fsck.returncode==0,'ext4 integrity FAIL'
  run(['mount','-o','ro',loop+partition,str(root)]);mounted=True
  # Validate Armbian HTTP while ext4 is mounted read-only: no test writes to image.
  if board in ('opizero','nanopineo'):
   script=("set -eu; ip link set lo up; ip addr add 10.43.0.1/32 dev lo; "
           "chroot \"$1\" /usr/local/bin/2pnyd >/tmp/pny5122-http-check.log 2>&1 & "
           "pid=$!; trap 'kill \"$pid\" 2>/dev/null || true; wait \"$pid\" 2>/dev/null || true' EXIT; "
           "for i in 1 2 3 4 5 6 7 8 9 10; do "
           "if chroot \"$1\" /usr/bin/curl -fsS --noproxy '*' --connect-timeout 1 --max-time 2 "
           "http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then "
           "echo BOARD_HTTP_NAMESPACE_PASS; break; fi; sleep 1; done; "
           "curl -fsS --noproxy '*' --max-time 3 http://10.43.0.1/healthz | grep -q 'PU2PNY OK'; "
           "curl -fsS --noproxy '*' --max-time 3 -D - -o /dev/null http://10.43.0.1/generate_204 | tr -d '\\r' | grep -q '^Location: http://10.43.0.1/wizard$'; "
           "curl -fsSL --noproxy '*' --max-time 3 http://10.43.0.1/ | grep -q 'PU2PNY-OS'; "
           "curl -fsS --noproxy '*' --max-time 15 http://10.43.0.1/api/status | grep -q '5.13.002'")
   run(['unshare','--net','--fork','sh','-c',script,'sh',str(root)])
  assert M.manifest(root)==after,'read-only remount differs'
  assert (root/'etc/2pny/version').read_text().strip()=='5.13.002'
  run(['umount',str(root)]);mounted=False
  run(['losetup','-d',loop]);loop=''
  with image.open('rb') as f:assert hashlib.sha256(f.read(1048576)).hexdigest()==boot_hash,'boot sector modified'
  output=work/'output';output.mkdir(exist_ok=True)
  name=f'pu2pny-{board}-5.13.002.img.xz'
  dest=output/name
  assert not dest.exists()
  with dest.open('wb') as out:run(['xz','-T2','-4','-c',str(image)],stdout=out)
  run(['xz','-t',str(dest)])
  digest=sha(dest)
  (output/(name+'.sha256')).write_text(digest+'  '+name+'\n')
  info={'version':'5.13.002','scope':['clock','nextion','oled','setup-ap','board-http','rf-access-request','secondary-wifi','version'],
        'classification':'ALPHA_HW_TEST_CANDIDATE','architecture':board,
        'source_commit':commit,'base_version':'5.12.002','base_sha256':expected,
        'image_sha256':digest,'bytes':dest.stat().st_size,
        'validation':{'xz':'PASS','sha256':'PASS','filesystem':'PASS','scope_manifest':'PASS',
                      'protected_rf_nextion':'PASS','bootloader_first_mib':'UNCHANGED',
                      'HW':'NOT_VERIFIED','PROD':'NOT_APPROVED'},
        'limitations':['Orange Pi and NanoPi AP/HTTP require physical tests',
                       'Nextion needs a compatible HMI; rotation applies to OLED']}
  (output/f'BUILD-INFO-{board}.json').write_text(json.dumps(info,indent=2)+'\n')
  print('IMAGE_513_VALIDATED',board,digest,dest.stat().st_size,flush=True)
 finally:
  if mounted:subprocess.run(['umount',str(root)],check=False)
  if loop:subprocess.run(['losetup','-d',loop],check=False)
  if root.exists():shutil.rmtree(root,ignore_errors=True)
  if image.exists():image.unlink()
if __name__=='__main__':main()
