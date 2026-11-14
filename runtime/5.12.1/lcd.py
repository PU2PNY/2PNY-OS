#!/usr/bin/env python3
"""DISPLAY-5121: paginated HD44780 pages for real MMDVM/network telemetry."""
import time
import unicodedata
from pathlib import Path
from os import statvfs

def clean(v):
    return unicodedata.normalize('NFKD',str(v)).encode('ascii','ignore').decode().replace('\n',' ').strip()

def net(path=Path('/run/2pny/network-status.txt')):
    try: return dict(line.split('=',1) for line in path.read_text().splitlines() if '=' in line)
    except (OSError,UnicodeError): return {}

def temp(tel):
    try:
        f=float(tel.get('temperature'))
        return f'{f:.0f}C' if -20<=f<=125 else '-'
    except (ValueError,TypeError): 
        try:
            f=float(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000.0
            return f'{f:.0f}C' if -20<=f<=125 else '-'
        except (ValueError,OSError): return '-'

def free():
    try:
        s=statvfs('/')
        return f'{s.f_bavail*s.f_frsize/1073741824:.1f}G'
    except OSError: return '-'

def duration(active,now=None):
    try:
        t=max(0,int((time.time() if now is None else now)-float(active['started_unix_ms'])/1000))
        return f'{t//60:02d}:{t%60:02d}'
    except (KeyError,ValueError,TypeError): return '--:--'

def rows_for(live,cfg,tel,cols,rows,network=None,now=None):
    cfg=cfg if isinstance(cfg,dict) else {}
    active=(live or {}).get('active') or {}
    n=network if network is not None else net()
    ip=n.get('default_ip') or '-'
    proto=str(active.get('protocol') or cfg.get('protocol') or '-').replace('DSTAR','D-Star')
    call=str(active.get('source') or cfg.get('callsign') or '-')
    mode=str(active.get('mode') or active.get('direction') or 'RX').upper()
    target=str(active.get('target') or cfg.get('server_name') or '-')
    cc=str(active.get('color_code') if active.get('color_code') is not None else '-')
    ber=str(active.get('ber') if active.get('ber') is not None else '-')
    rssi=str(active.get('rssi_avg',active.get('rssi')) if active.get('rssi_avg',active.get('rssi')) is not None else '-')
    if active:
        pg1=[f'{proto} {mode} {duration(active,now)}',call,f'{target}',f'BER {ber} RSSI {rssi}']
        pg2=['PU2PNY-OS',f'TG {target}',f'SLOT {active.get("slot") or "-"} CC {cc}',f'IP {ip}']
        alternatives=[pg1,pg2]
    else:
        alternatives=[
            ['PU2PNY-OS',call,f'{proto} STANDBY',f'RF {cfg.get("rx_hz") or "-"}'],
            [f'IP {ip}',str(n.get('uplink_type') or 'REDE').upper(),f'{proto} {target}',f'ID {cfg.get("dmr_id") or "-"}'],
            ['PU2PNY-OS',f'CPU {temp(tel)}',f'DISCO {free()}',f'LOAD {tel.get("load_1") if tel.get("load_1") is not None else "-"}'],
        ]
    return [[clean(v)[:cols] for v in page[:rows]] for page in alternatives]

def render(self,live,cfg,tel):
    alternatives=rows_for(live,cfg,tel,self.cols,self.rows)
    phase=int(time.monotonic()//4)%len(alternatives)
    lines=alternatives[phase]
    key=(phase,tuple(lines))
    if getattr(self,'_5121_signature',None)==key:return phase,len(alternatives)
    self.show(lines)
    self._5121_signature=key
    return phase,len(alternatives)
