"""Executa o network-core real contra nmcli/iw/IP simulados; apenas I/O e relógio isolados."""
import json
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
MOCK=r'''#!/usr/bin/env python3
import json,os,sys,time
from pathlib import Path
r=Path(os.environ['SIMROOT']);scenario=os.environ['SIMCASE'];name=Path(sys.argv[0]).name;a=sys.argv[1:]
with (r/'audit').open('a') as f:f.write(json.dumps([name,a])+'\n')
if name=='nmcli':
 if '--wait' in a and 'connection' in a and 'up' in a and 'PU2PNY-WIFI' in a:
  if a[a.index('--wait')+1]=='30' and scenario=='success':(r/'linked').touch();sys.exit(0)
  sys.exit(10)
 if 'TYPE,STATE' in a:print('wifi:disconnected')
 elif 'DEVICE,TYPE,STATE' in a:print('wlan0:wifi:'+('connected' if (r/'linked').exists() else 'disconnected'))
 elif 'NAME' in a:print('PU2PNY-WIFI')
 elif 'connection.interface-name' in a:print('wlan0')
 elif '802-11-wireless-security.key-mgmt' in a:print('wpa-psk')
elif name=='iw':
 if 'station' in a:
  if scenario=='clients':print('Station 02:00:00:00:00:01 (on wlan0)')
  if scenario=='iw-error':sys.exit(1)
 elif 'link' in a and (r/'linked').exists():print('SSID: TestNet')
elif name=='ip':
 if (r/'linked').exists():
  if 'route' in a:print('default via 192.0.2.1 dev wlan0')
  elif 'addr' in a and 'show' in a:print('2: wlan0 inet 192.0.2.2/24 scope global')
elif name in ('hostapd','dnsmasq'):time.sleep(90)
elif name=='sleep':
 if a==['3']:
  p=r/'loops';n=int(p.read_text())+1 if p.exists() else 1;p.write_text(str(n))
  if n>=8:sys.exit(99)
  time.sleep(.02)
'''


def simulate(source):
    for scenario in ('success','failure','clients','iw-error'):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);(r/'run').mkdir();(r/'state').mkdir();(r/'bin').mkdir()
            (r/'sys/wlan0/wireless').mkdir(parents=True)
            (r/'state/provisioned').touch();(r/'state/uplink-ssid').write_text('TestNet')
            for name in ('nmcli','iw','ip','hostapd','dnsmasq','sleep','rfkill','systemctl','sysctl','logger','iptables'):
                p=r/'bin'/name;p.write_text(MOCK);p.chmod(0o755)
            code=source.replace('RUN=/run/2pny','RUN='+shlex.quote(str(r/'run'))).replace('STATE=/var/lib/2pny','STATE='+shlex.quote(str(r/'state')))
            code=code.replace('/usr/bin/nmcli',str(r/'bin/nmcli')).replace('/sys/class/net',str(r/'sys')).replace('RECOVERY_DUE=120','RECOVERY_DUE=0')
            # Templates são dados de I/O; não alterar condições, locks nem retorno ao AP.
            for name in ('hostapd','dnsmasq-ap','dnsmasq-eth'):
                f=r/(name+'.template');f.write_text('interface=@IFACE@\n')
                code=code.replace('/usr/share/2pny/network/'+name+'.template',str(f))
            script=r/'network';script.write_text(code)
            env=dict(os.environ,PATH=str(r/'bin')+':'+os.environ['PATH'],SIMROOT=str(r),SIMCASE=scenario)
            p=subprocess.run(['bash',str(script)],env=env,capture_output=True,text=True,timeout=35)
            assert p.returncode==99,(scenario,p.returncode,p.stdout[-800:],p.stderr[-1200:])
            records=[json.loads(line) for line in (r/'audit').read_text().splitlines()]
            attempts=[args for name,args in records if name=='nmcli' and '--wait' in args and args[args.index('--wait')+1]=='30']
            if scenario in ('clients','iw-error'):assert not attempts,scenario
            else:assert len(attempts)==1,(scenario,attempts)
            if scenario=='success':assert (r/'state/ap-disabled').exists()
            if scenario=='failure':assert sum(name=='hostapd' for name,_ in records)>=2,'AP deve voltar após falha'
            # As consultas pesadas não podem acontecer em todas as oito voltas.
            active=[args for name,args in records if name=='nmcli' and 'DEVICE,TYPE,STATE' in args]
            assert len(active)<10,(scenario,len(active))
    print('TEST_511_NETWORK_SIMULATION_OK')
