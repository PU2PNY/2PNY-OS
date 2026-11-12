#!/usr/bin/env python3
"""PROTO-511/P2P-511: um modo por vez; planejamento sem alterar RF e rollback."""
import configparser
import fcntl
import io
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path
from importlib.machinery import SourceFileLoader

BASE=Path(os.environ.get('PNY_STATE','/var/lib/2pny'))
RUN=Path(os.environ.get('PNY_RUN','/run/2pny'))
LIB=Path(os.environ.get('PNY_LIB','/usr/local/libexec/pu2pny'))
BIN=Path(os.environ.get('PNY_BIN','/usr/local/bin'))
MODES={'dmr2ysf':'DMR2YSF','ysf2dmr':'YSF2DMR','dmr2nxdn':'DMR2NXDN','ysf2nxdn':'YSF2NXDN','ysf2p25':'YSF2P25'}
GATEWAYS={'DMR':'2pny-dmrgateway.service','YSF':'2pny-ysfgateway.service'}


def readj(p):
    try:return json.loads(p.read_text())
    except (OSError,ValueError):return {}


def atomic(p,data):
    import tempfile
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+p.name,dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def ini(p):
    c=configparser.ConfigParser(interpolation=None,strict=False);c.optionxform=str
    with p.open() as f:c.read_file(f)
    return c


def dump(c):
    f=io.StringIO();c.write(f,space_around_delimiters=False);return f.getvalue().encode()


def setv(c,section,**values):
    if not c.has_section(section):c.add_section(section)
    for k,v in values.items():
        v=str(v)
        if '\n' in v or '\r' in v:raise ValueError('valor INI inválido')
        c.set(section,k,v)


def catalogue(proto):
    row=readj(BASE/'hosts'/(proto+'Hosts.json'))
    rows=row.get('reflectors',[]) if isinstance(row,dict) else []
    return [{'id':str(r.get('designator') or ''),'name':str(r.get('name') or ''),
             'address':str(r.get('ipv4') or r.get('address') or ''),'port':r.get('port')}
            for r in rows if isinstance(r,dict) and str(r.get('designator') or '').isdigit()]


def plan(mode,destination,nxdn_id=""):
    if mode not in MODES:raise ValueError('crossmode inválido')
    cfg=readj(BASE/'config.json');proto='DMR' if mode.startswith('dmr') else 'YSF'
    if cfg.get('protocol')!=proto:raise ValueError('ative primeiro o perfil '+proto)
    host=ini(BASE/'mmdvm/MMDVM-Host.ini')
    c=ini(LIB/'cm-templates'/(MODES[mode]+'.ini'))
    if not re.fullmatch(r'[A-Z0-9/]{3,16}',str(cfg.get('callsign') or '')):raise ValueError('indicativo ausente')
    identity=int(cfg.get('dmr_id') or 0)
    if not 10000<=identity<=999999999:raise ValueError('ID digital ausente')
    own=BASE/'crossmode'/mode
    nxdn_identity=None
    if mode=='ysf2nxdn':
        value=str(nxdn_id or cfg.get('nxdn_id') or readj(BASE/'crossmode/settings.json').get('nxdn_id') or '')
        if not value:
            try:
                for line in (BASE/'hosts/NXDN.csv').read_text().splitlines():
                    fields=re.split(r'[,\t]',line)
                    if len(fields)>1 and fields[1].strip().upper()==cfg['callsign'].upper():value=fields[0].strip();break
            except OSError:pass
        if not re.fullmatch(r'[0-9]{1,5}',value) or not 1<=int(value)<=65535:raise ValueError('informe o ID NXDN real no campo do crossmode')
        nxdn_identity=int(value)
    setv(c,'Log',FileLevel=0,DisplayLevel=1,FilePath=str(RUN),FileRoot=mode)
    setv(c,'DMR Id Lookup',File=str(BASE/'hosts/DMRIds.dat'))
    if c.has_section('NXDN Id Lookup'):setv(c,'NXDN Id Lookup',File=str(BASE/'hosts/NXDN.csv'))
    if c.has_section('aprs.fi'):setv(c,'aprs.fi',Enable=0)
    if c.has_section('Info'):
        # Nenhuma localização é inferida do indicativo ou do país.
        c.remove_section('Info')
    if proto=='DMR':
        setv(c,'DMR Network',Id=identity,RptAddress='127.0.0.1',LocalAddress='127.0.0.1',
             RptPort=host.getint('DMR Network','LocalPort'),LocalPort=host.getint('DMR Network','GatewayPort'))
    else:
        section='System Fusion Network'
        setv(c,'YSF Network',Callsign=cfg['callsign'],Daemon=0,DstAddress='127.0.0.1',LocalAddress='127.0.0.1',
             DstPort=host.getint(section,'LocalPort'),LocalPort=host.getint(section,'GatewayPort'))
    gateway=None
    if mode=='ysf2dmr':
        profile=(readj(BASE/'protocol-profiles.json').get('profiles') or {}).get('DMR') or {}
        address=str(profile.get('server_address') or '')
        if not re.fullmatch(r'[A-Za-z0-9.-]{1,253}',address):raise ValueError('salve antes o servidor do perfil DMR')
        port=int(profile.get('server_port') or 0)
        if not 0<port<65536:raise ValueError('porta DMR ausente')
        if not destination.isdigit() or not 1<=int(destination)<=16777215:raise ValueError('TG inválido')
        password=(BASE/'protocol-secrets/dmr.secret').read_text().strip()
        kind=str(profile.get('network_kind') or '').upper()
        values=dict(Id=identity,Address=address,Port=port,Password=password,StartupDstId=destination,
                    StartupPC=0,Local=62039,TGListFile=str(own/'tg-list.txt'))
        if kind=='XLX':
            if not re.fullmatch(r'[A-Z]',str(profile.get('xlx_module') or '')):raise ValueError('módulo XLX ausente')
            match=re.fullmatch(r'XLX([0-9]{3})',str(profile.get('server_name') or '').upper())
            if not match:raise ValueError('nome XLX inválido')
            values.update(XLXModule=profile['xlx_module'],XLXReflector=int(match[1]),XLXFile=str(own/'XLXHosts.txt'))
        setv(c,'DMR Network',**values)
    else:
        target='YSF' if mode=='dmr2ysf' else 'P25' if mode=='ysf2p25' else 'NXDN'
        selected=next((r for r in catalogue(target) if r['id']==destination),None)
        if not selected:raise ValueError('destino ausente na lista '+target)
        g=configparser.ConfigParser(interpolation=None);g.optionxform=str
        if target=='YSF':
            setv(c,'YSF Network',Callsign=cfg['callsign'],GatewayAddress='127.0.0.1',GatewayPort=4200,LocalAddress='127.0.0.1',LocalPort=3200,Daemon=0)
            setv(c,'DMR Network',DefaultDstTG=9,TGListFile=str(own/'tg-list.txt'))
            setv(g,'General',Callsign=cfg['callsign'],Suffix='ND',Id=identity,RptAddress='127.0.0.1',RptPort=3200,LocalAddress='127.0.0.1',LocalPort=4200,Daemon=0)
            setv(g,'Network',Startup=destination,Reconnect=1,Revert=0,InactivityTimeout=10)
            setv(g,'YSF Network',Enable=1,Port=42000,Hosts=str(BASE/'hosts/YSFHosts.json'),ReloadTime=60)
            setv(g,'FCS Network',Enable=0)
            binary='YSFGateway'
        else:
            rp,lp,np=(32010,42020,42010) if target=='P25' else (14021,14020,14050)
            net=target+' Network'
            if mode=='dmr2nxdn':
                setv(c,net,GatewayAddress='127.0.0.1',GatewayPort=lp,LocalAddress='127.0.0.1',LocalPort=rp,DefaultID=destination,Daemon=0)
            else:setv(c,net,Id=nxdn_identity if target=='NXDN' else identity,StartupDstId=destination,DstAddress='127.0.0.1',DstPort=lp,LocalAddress='127.0.0.1',LocalPort=rp,TGListFile=str(own/'tg-list.txt'))
            setv(g,'General',Callsign=cfg['callsign'],RptAddress='127.0.0.1',RptPort=rp,LocalPort=lp,Daemon=0)
            if target=='NXDN':setv(g,'General',RptProtocol='Icom',Suffix='NXDN')
            setv(g,'Network',Port=np,HostsFile1=str(BASE/'hosts'/(target+'Hosts.json')),HostsFile2=str(BASE/'hosts'/(target+'Hosts.txt')),Static=destination,ReloadTime=60,RFHangTime=120,NetHangTime=60)
            setv(g,'Voice',Enabled=0)
            binary=target+'Gateway'
        setv(g,'Log',DisplayLevel=1,MQTTLevel=0)
        setv(g,'APRS',Enable=0)
        setv(g,'Remote Commands',Enable=0)
        gateway=(binary,dump(g))
    return {'ini':dump(c),'gateway':gateway,'original':GATEWAYS[proto], 'dir':own,
            'tglist':(('9;'+destination+'\n') if mode=='dmr2ysf' else '').encode(),
            'xlx': (match[1]+';'+address+';'+str(4000+ord(profile['xlx_module'])-64)+'\n').encode() if mode=='ysf2dmr' and kind=='XLX' else b''}


def ctl(*args):
    return subprocess.run(['systemctl',*args],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30).returncode==0


def off(control=ctl):
    state=readj(BASE/'special-mode.json')
    if not state:return
    mode=state.get('mode')
    if mode in MODES:
        control('stop','2pny-cm@'+mode+'.service');control('stop','2pny-cm-gateway@'+mode+'.service')
    elif mode=='direct-group':control('stop','2pny-direct-group.service')
    else:raise ValueError('estado salvo inválido')
    original=state.get('original')
    if original not in GATEWAYS.values():raise ValueError('gateway de rollback inválido')
    if not control('start',original):raise RuntimeError('gateway anterior não voltou; rollback pendente')
    atomic(BASE/'special-mode.json',b'{}\n')
    direct=readj(BASE/'direct-group.json');direct['enabled']=False
    atomic(BASE/'direct-group.json',json.dumps(direct).encode())
    if readj(BASE/'direct-settings.json').get('enabled') is True:control('start','2pny-direct.service')


def activate(mode,destination='',code='',control=ctl,wait=time.sleep,nxdn_id=''):
    if readj(BASE/'special-mode.json').get('mode'):raise ValueError('desligue o modo atual antes de trocar')
    if mode=='direct-group':
        if readj(BASE/'config.json').get('protocol')!='DMR':raise ValueError('ative primeiro DMR')
        if not re.fullmatch(r'[A-Za-z0-9_-]{22,128}',code):raise ValueError('código do grupo inválido')
        original=GATEWAYS['DMR'];unit='2pny-direct-group.service'
    else:
        planned=plan(mode,destination,nxdn_id);original=planned['original'];unit='2pny-cm@'+mode+'.service'
        if not (BIN/MODES[mode]).is_file():raise ValueError('conversor não instalado')
        atomic(planned['dir']/'converter.ini',planned['ini']);atomic(planned['dir']/'tg-list.txt',planned['tglist'])
        atomic(planned['dir']/'XLXHosts.txt',planned['xlx'])
        if planned['gateway']:
            binary,data=planned['gateway']
            if not (BIN/binary).is_file():raise ValueError('gateway de destino ausente')
            atomic(planned['dir']/'gateway.ini',data)
            atomic(planned['dir']/'gateway-binary',binary.encode())
    # Prova local de runtime apenas; nenhuma alegação de conexão remota/RF.
    if not control('is-active','--quiet','2pny-mmdvmhost.service'):raise ValueError('MMDVMHost inativo')
    record={'mode':mode,'original':original,'destination':destination,'state':'starting','HW':'NOT_VERIFIED'}
    atomic(BASE/'special-mode.json',json.dumps(record).encode())
    try:
        if not control('stop',original):raise RuntimeError('não foi possível parar o gateway original')
        control('stop','2pny-direct.service')
        if mode=='direct-group':
            atomic(BASE/'direct-group.json',json.dumps({'enabled':True,'code':code}).encode())
        elif planned['gateway'] and not control('start','2pny-cm-gateway@'+mode+'.service'):
            raise RuntimeError('gateway dedicado não iniciou')
        if not control('start',unit):raise RuntimeError('modo não iniciou')
        for _ in range(5):
            wait(1)
            if not control('is-active','--quiet',unit):raise RuntimeError('modo encerrou no preflight')
        record['state']='process_active';atomic(BASE/'special-mode.json',json.dumps(record).encode())
        if mode=='ysf2nxdn' and nxdn_id:atomic(BASE/'crossmode/settings.json',json.dumps({'nxdn_id':str(nxdn_id)}).encode())
    except Exception:
        off(control)
        raise


def main():
    if sys.argv[1:]==['--gate']:raise SystemExit(1 if readj(BASE/'special-mode.json').get('mode') else 0)
    if sys.argv[1:]==['--legacy-gate']:raise SystemExit(0 if readj(BASE/'direct-settings.json').get('enabled') is True and not readj(BASE/'special-mode.json').get('mode') else 1)
    RUN.mkdir(parents=True,exist_ok=True)
    with (RUN/'mode511.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:
            if sys.argv[1:] == ['--gate']:
                raise SystemExit(1 if readj(BASE/'special-mode.json').get('mode') else 0)
            if sys.argv[1:] == ['--legacy-gate']:
                raise SystemExit(0 if readj(BASE/'direct-settings.json').get('enabled') is True and not readj(BASE/'special-mode.json').get('mode') else 1)
            if sys.argv[1:] == ['--boot-reset']:
                group=readj(BASE/'direct-group.json');group['enabled']=False
                atomic(BASE/'direct-group.json',json.dumps(group).encode())
                atomic(BASE/'special-mode.json',b'{}\n')
                return
            if sys.argv[1:] == ['--request']:
                request=RUN/'mode-request.json'
                req=json.loads(request.read_text());request.unlink()
                mode=req.get('mode')
                if mode not in (*MODES,'off','direct-group','legacy-on','legacy-off'):raise ValueError('modo inválido')
                code=str(req.get('code') or '')
                if mode=='direct-group' and req.get('create'):code=secrets.token_urlsafe(24)
                if mode in ('legacy-on','legacy-off'):
                    if mode=='legacy-on' and readj(BASE/'special-mode.json').get('mode'):raise ValueError('saia do modo atual antes de ativar Direct individual')
                    settings=readj(BASE/'direct-settings.json');settings['enabled']=mode=='legacy-on'
                    atomic(BASE/'direct-settings.json',json.dumps(settings).encode())
                    ctl('reset-failed','2pny-direct.service')
                    if not ctl('start' if mode=='legacy-on' else 'stop','2pny-direct.service'):raise RuntimeError('não foi possível alterar Direct individual')
                elif mode=='off':off()
                else:activate(mode,str(req.get('destination') or ''),code,nxdn_id=str(req.get('nxdn_id') or ''))
                result={'ok':True,'code':code if mode=='direct-group' else ''}
                atomic(RUN/'mode-result.json',json.dumps(result).encode())
            elif sys.argv[1:] == ['off']:off()
            elif len(sys.argv)==3:activate(sys.argv[1],sys.argv[2])
            else:raise ValueError('uso: 2pny-crossmode off|MODO DESTINO')
        except Exception as exc:
            result={'ok':False,'error':str(exc)}
            if sys.argv[1:]==['--request']:atomic(RUN/'mode-result.json',json.dumps(result).encode())
            print(json.dumps(result,ensure_ascii=False));raise SystemExit(1)

if __name__=='__main__':main()
