#!/usr/bin/env python3
import datetime,json,os,tempfile
from pathlib import Path
STATE=Path('/var/lib/2pny')
CFG=STATE/'config.json'
RUNTIME=STATE/'network-radio.json'
OUT=STATE/'last-active-profile.json'

def readj(p):
    try:return json.loads(p.read_text())
    except Exception:return {}

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        try:os.unlink(tmp)
        except FileNotFoundError:pass

cfg=readj(CFG); runtime=readj(RUNTIME)
proto=str(runtime.get('protocol') or '').upper()
if proto=='C4FM':proto='YSF'
if proto not in {'DMR','DSTAR','YSF','P25','NXDN','POCSAG'}:raise SystemExit(0)
state=str(runtime.get('state') or '')
# DMR's protected helper writes "configured" only after both MMDVMHost and
# DMRGateway were confirmed active. Other protocols write gateway_active.
if state not in {'gateway_active','active','ready'} and not (proto=='DMR' and state=='configured'):
    raise SystemExit(0)
cfgproto=str(cfg.get('protocol') or '').upper().replace('-','')
if cfgproto != proto:raise SystemExit(0)
atomic(OUT,{
 'schema':1,'protocol':proto,'profile':cfg,'runtime':runtime,
 'proven_at':datetime.datetime.now(datetime.timezone.utc).isoformat()
})
