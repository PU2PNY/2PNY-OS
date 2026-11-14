#!/usr/bin/env python3
"""Build checked 5.12.001 P1 overlays on each of four published P0 images.
Never transplants bootloaders/kernel; never changes RF, Nextion, UART or network.
SW images are only candidates for physical testing, NOT production.
"""
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
P0={
 '32':('b7c56eee90f0b19763639b010d604f04125cc670541048beb37caf41f03c52f8','p2',1),
 '64':('1481e5877843f8de37c11d5c8962171aa8b6213ef63c1ff2adef9ab9205088a1','p2',2),
 'opizero':('e50b32335b60c6952bfbba548180db940db95792e0a855274a59e5d57cb93b92','p1',1),
 'nanopineo':('e0fb00c22ccf279619831b250cb0cc9610e83d3ccf6e12b5901ab8a77e1215c9','p1',1),
}
def run(argv,**kw):
 return subprocess.run(argv,check=True,**kw)
def sha(path):
 with open(path,'rb') as fh:return hashlib.file_digest(fh,'sha256').hexdigest()
def mod(path,name):
 spec=importlib.util.spec_from_file_location(name,REPO/path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
M=mod('ci/build-5.11.py','old_manifest')
P=mod('ci/patch-image-5.12.1.py','overlay_5121')

def main():
 assert len(sys.argv)==4,'usage: build-5.12.1.py WORKDIR 32|64|opizero|nanopineo COMMIT'
 work=Path(sys.argv[1]).resolve();board=sys.argv[2];commit=sys.argv[3]
 assert os.geteuid()==0 and work!=Path('/') and board in P0
 assert re.fullmatch(r'[a-f0-9]{40}',commit)
 expected,partition,elf_class=P0[board]
 base=work/f'pu2pny-{board}-5.12.img.xz'
 assert base.is_file() and sha(base)==expected,'published P0 SHA mismatch'
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
  assert (root/'etc/2pny/version').read_text().strip()=='5.12.000'
  before=M.manifest(root)
  changed=P.apply(root)
  after=M.manifest(root)
  manifest_changed={p for p in set(before)|set(after) if before.get(p)!=after.get(p)}
  assert manifest_changed==changed,('P1 altered undeclared paths',sorted(manifest_changed^changed))
  for path in M.PROTECTED:
   assert before.get(path)==after.get(path),'RF/Nextion baseline changed: '+path
  for path in changed:
   if path.endswith('.pre-5.12.1'):
    original=path[:-len('.pre-5.12.1')]
    assert before[original]['sha256']==after[path]['sha256'],'rollback hash mismatch: '+path
  assert after['etc/2pny/version']['sha256']!=before['etc/2pny/version']['sha256']
  assert (root/'usr/local/bin/2pnyd').read_bytes()[:4]==b'\x7fELF'
  for bin_name in ('MMDVM-Host','DMRGateway','NextionDriver-pu2pny','MMDVM-Display','2pnyd'):
   hdr=(root/'usr/local/bin'/bin_name).read_bytes()[:20]
   assert hdr[:4]==b'\x7fELF' and hdr[4]==elf_class and struct.unpack('<H',hdr[18:20])[0]==(183 if elf_class==2 else 40),bin_name
  for p,v in after.items():
   assert v['uid']!=1001 and v['gid']!=1001,('CI owner leaked',p)
  run(['sync'])
  run(['umount',str(root)]);mounted=False
  fsck=subprocess.run(['e2fsck','-fn',loop+partition],check=False)
  assert fsck.returncode==0,'ext4 integrity FAIL'
  run(['mount','-o','ro',loop+partition,str(root)]);mounted=True
  assert M.manifest(root)==after,'read-only remount differs'
  assert (root/'etc/2pny/version').read_text().strip()=='5.12.001'
  run(['umount',str(root)]);mounted=False
  run(['losetup','-d',loop]);loop=''
  with image.open('rb') as f:assert hashlib.sha256(f.read(1048576)).hexdigest()==boot_hash,'boot sector modified'
  output=work/'output';output.mkdir(exist_ok=True)
  name=f'pu2pny-{board}-5.12.001.img.xz'
  dest=output/name
  assert not dest.exists()
  with dest.open('wb') as out:run(['xz','-T2','-4','-c',str(image)],stdout=out)
  run(['xz','-t',str(dest)])
  digest=sha(dest)
  (output/(name+'.sha256')).write_text(digest+'  '+name+'\n')
  info={'version':'5.12.001','scope':['UI-NAV-5121','CLOCK-5121','DISPLAY-OLED-LCD-5121','EXPERT-5121'],
        'classification':'ALPHA_HW_TEST_CANDIDATE','architecture':board,
        'source_commit':commit,'base_version':'5.12.000','base_sha256':expected,
        'image_sha256':digest,'bytes':dest.stat().st_size,
        'validation':{'xz':'PASS','sha256':'PASS','filesystem':'PASS','scope_manifest':'PASS',
                      'protected_rf_nextion':'PASS','bootloader_first_mib':'UNCHANGED',
                      'HW':'NOT_VERIFIED','PROD':'NOT_APPROVED'},
        'limitations':['Orange Pi and NanoPi AP/HTTP physical function not verified',
                       'DMRGateway and D-Star still require RF testing',
                       'Nextion telemetry depends on ON7LDS HMI/driver backend',
                       'Transcoding requires proven vocoder',
                       'CGNAT may require relay']}
  (output/f'BUILD-INFO-{board}.json').write_text(json.dumps(info,indent=2)+'\n')
  print('IMAGE_5121_VALIDATED',board,digest,dest.stat().st_size,flush=True)
 finally:
  if mounted:subprocess.run(['umount',str(root)],check=False)
  if loop:subprocess.run(['losetup','-d',loop],check=False)
  if root.exists():shutil.rmtree(root,ignore_errors=True)
  if image.exists():image.unlink()
if __name__=='__main__':main()
