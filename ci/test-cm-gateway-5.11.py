#!/usr/bin/env python3
"""Prova da inicialização Gateway raw sem RPTL/RPTC; não é teste de codec/RF."""
import argparse
import configparser
import socket
import subprocess
import tempfile
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('binary');parser.add_argument('--arch',choices=('native','arm32','arm64'),default='native');parser.add_argument('--sysroot');args=parser.parse_args()
binary=Path(args.binary).resolve();name=binary.name
assert name in ('DMR2YSF','DMR2NXDN')
repo=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    root=Path(td);cfg=configparser.ConfigParser(interpolation=None);cfg.optionxform=str
    cfg.read(repo/'runtime/5.11/cm-templates'/(name+'.ini'))
    host=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);host.bind(('127.0.0.1',0));host.settimeout(.2)
    probe=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);probe.bind(('127.0.0.1',0));port=probe.getsockname()[1];probe.close()
    remote=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);remote.bind(('127.0.0.1',0))
    for k,v in {'Id':1234567,'RptPort':host.getsockname()[1],'LocalPort':port,'TGListFile':str(root/'tg')}.items():cfg['DMR Network'][k]=str(v)
    target='YSF Network' if name=='DMR2YSF' else 'NXDN Network'
    for k,v in {'GatewayPort':remote.getsockname()[1],'LocalPort':0,'FCSRooms':str(root/'rooms')}.items():cfg[target][k]=str(v)
    cfg['Log']['FileLevel']='0';cfg['DMR Id Lookup']['File']=str(root/'ids')
    if cfg.has_section('NXDN Id Lookup'):cfg['NXDN Id Lookup']['File']=str(root/'ids')
    (root/'tg').write_text('9;9999\n');(root/'rooms').touch();(root/'ids').touch()
    path=root/'converter.ini'
    with path.open('w') as f:cfg.write(f,space_around_delimiters=False)
    command=[str(binary),str(path)]
    if args.arch!='native':
        assert args.sysroot
        command=['qemu-arm-static' if args.arch=='arm32' else 'qemu-aarch64-static','-L',args.sysroot,*command]
    with (root/'log').open('w') as log:
        proc=subprocess.Popen(command,stdout=log,stderr=log)
        try:
            reply=None
            for _ in range(50):
                host.sendto(b'DMRP',('127.0.0.1',port))
                try:reply=host.recvfrom(128)[0];break
                except socket.timeout:
                    if proc.poll() is not None:break
            output=(root/'log').read_text()
            assert reply==b'DMRP',(name,proc.poll(),output[-1600:])
            assert 'interface Gateway local pronta' in output,(name,output[-1600:])
            assert 'Waiting for MMDVM' not in output
        finally:
            proc.terminate();proc.wait(timeout=5);host.close();remote.close()
print('CM_GATEWAY_RAW_NO_LOGIN_PASS',name,args.arch)
