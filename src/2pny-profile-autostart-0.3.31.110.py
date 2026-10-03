#!/usr/bin/env python3
import fcntl,json,os,subprocess,tempfile
from pathlib import Path
STATE=Path('/var/lib/2pny');RUN=Path('/run/2pny')
CFG=STATE/'config.json';PROVEN=STATE/'last-active-profile.json';RUNTIME=STATE/'network-radio.json';HW=STATE/'hardware-probe.json';PROVISIONED=STATE/'provisioned'
VALID={'DMR':'2pny-dmrgateway.service','DSTAR':'2pny-dstargateway.service','YSF':'2pny-ysfgateway.service','P25':'2pny-p25gateway.service','NXDN':'2pny-nxdngateway.service','POCSAG':'2pny-dapnetgateway.service'}
RUN.mkdir(parents=True,exist_ok=True); lock=open(RUN/'profile-autostart.lock','w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit(0)
def readj(p):
    try:return json.loads(p.read_text())
    except Exception:return {}
def active(u):return subprocess.run(['systemctl','is-active','--quiet',u],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def log(m):subprocess.run(['logger','-t','pu2pny-profile-autostart','--',m],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def atomic(path,obj):
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        try:os.unlink(tmp)
        except FileNotFoundError:pass
def norm_proto(v):
    p=str(v or '').upper().replace('-','')
    return 'YSF' if p=='C4FM' else p

def runtime_matches_saved(cfg,runtime):
    proto=norm_proto(runtime.get('protocol'))
    if proto not in VALID or norm_proto(cfg.get('protocol'))!=proto:return False
    state=str(runtime.get('state') or '')
    if state not in {'gateway_active','active','ready'} and not (proto=='DMR' and state=='configured'):return False
    pairs=(('server_name','server_name'),('address','server_address'),('port','server_port'),('kind','network_kind'))
    for rk,ck in pairs:
        rv=runtime.get(rk);cv=cfg.get(ck)
        if rv not in (None,'',0) and cv not in (None,'',0) and str(rv)!=str(cv):return False
    return True

if not PROVISIONED.exists():raise SystemExit(0)
draft=readj(CFG);proof=readj(PROVEN);source='proven'
proto=norm_proto(proof.get('protocol'));proven_cfg=proof.get('profile')
if proto not in VALID or not isinstance(proven_cfg,dict):
    runtime=readj(RUNTIME)
    if not isinstance(draft,dict) or not runtime_matches_saved(draft,runtime):
        log('perfil comprovado pendente: snapshot ausente e runtime salvo não coincide');raise SystemExit(0)
    proto=norm_proto(runtime.get('protocol'));proven_cfg=draft;source='validated-runtime-fallback'
gateway=VALID[proto]
mmdvm=readj(HW).get('mmdvm') or {}
if not mmdvm.get('detected'):
    log('perfil comprovado pendente: MMDVM ainda não confirmada');raise SystemExit(0)
if active('2pny-mmdvmhost.service') and active(gateway):raise SystemExit(0)
r=subprocess.run(['ip','-4','route','show','default'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
if r.returncode or not r.stdout.strip():
    log('perfil comprovado pendente: uplink ainda indisponível');raise SystemExit(0)
result=None
try:
    if draft!=proven_cfg:atomic(CFG,proven_cfg)
    result=subprocess.run(['timeout','-k','5','80','/usr/local/sbin/2pny-protocol-profiles','activate',proto],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90)
except Exception:
    log('falha controlada ao restaurar perfil comprovado');raise SystemExit(0)
finally:
    # Saved draft and active runtime are separate concepts; never destroy a draft.
    if draft and draft!=proven_cfg:atomic(CFG,draft)
if result and result.returncode==0:log('perfil restaurado: '+proto+' source='+source)
else:log('perfil permaneceu pendente: '+proto+' source='+source)
