#!/usr/bin/env python3
"""Deterministic regressions; no radio, network or real systemctl changes."""
import os, types, contextlib,io,json,re,runpy,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class Regression(unittest.TestCase):
 def test_validator_source_contracts(self):
  validator=(ROOT/'ci/validate-0.2.7-image.sh').read_text()
  names={'NET':'2pny-protocol-network-apply-0.2.7.py','SW':'2pny-network-switch-0.2.7','RF':'2pny-rf-apply-0.2.7','MOSQ':'mosquitto-pu2pny-0.2.7.conf'}
  import shlex
  for line in validator.splitlines():
   words=shlex.split(line)
   if len(words)==4 and words[0]=='grep' and words[1] in ('-Fq','-Fxq') and words[3].lstrip('$') in names:
    src=(ROOT/'src'/names[words[3].lstrip('$')]).read_text()
    self.assertIn(words[2],src,line)
   if line.startswith('for needle in '):
    filename='wizard-0.2.7.html' if 'Time Slot' in line else 'dashboard-0.2.7.html'
    for term in shlex.split(line.split('; do')[0])[3:]:self.assertIn(term,(ROOT/'src'/filename).read_text())
 def test_wifi_bssid_and_colon_ssid(self):
  src=(ROOT/'src/2pny-network-switch-0.2.7').read_text()
  code=src.split("python3 - \"$1\" <<'PY'",1)[1].split('\nPY',1)[0]
  raw='Minha:rede:AA:BB:CC:DD:EE:FF:73:2437 MHz:WPA2\nMinha:rede:AA:BB:CC:DD:EE:00:20:2437:WPA2'
  p=subprocess.run([sys.executable,'-c',code,raw],capture_output=True,text=True,check=True)
  rows=json.loads(p.stdout)
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['ssid'],'Minha:rede');self.assertEqual(rows[0]['bssid'],'AA:BB:CC:DD:EE:FF')
 def live(self,messages,gateway=None):
  now=time.time()
  def fake(args,**kw):
   gw='2pny-dmrgateway.service' in args
   data=gateway if gw else messages
   rows=[json.dumps({'MESSAGE':s,'__REALTIME_TIMESTAMP':str(int((now-age)*1e6)),'_SYSTEMD_UNIT':'2pny-dmrgateway.service' if gw else '2pny-mmdvmhost.service'}) for age,s in (data or [])]
   return subprocess.CompletedProcess(args,0,'\n'.join(rows),'')
  out=io.StringIO()
  with patch('subprocess.run',fake),contextlib.redirect_stdout(out):runpy.run_path(str(ROOT/'src/2pny-live-status-0.2.7.py'))
  return json.loads(out.getvalue())
 def test_long_call_and_direction(self):
  d=self.live([(40,'DMR Slot 2, received RF voice header from PU2PNY to TG 6')])
  self.assertTrue(d['rx']['active']);self.assertFalse(d['tx']['active']);self.assertGreaterEqual(d['rx']['duration'],40)
  self.assertEqual(d['rx']['quality']['score'],0)
 def test_end_metrics_and_lost(self):
  for ending in ['received RF end of voice transmission','RF voice transmission lost']:
   d=self.live([(40,'DMR Slot 2, received RF voice header from PU2PNY to TG 6'),(2,f'DMR Slot 2, {ending} from PU2PNY to TG 6, 38.0 seconds, BER: 1.2%, RSSI: -110/-90/-100 dBm')])
   self.assertFalse(d['rx']['active']);self.assertEqual(d['rx']['ber'],1.2)
 def test_timeout(self):
  d=self.live([(40,'DMR Slot 2, received network voice header from PU2PNY to TG 6'),(2,'DMR Slot 2, network user has timed out')])
  self.assertFalse(d['tx']['active'])
 def test_network_old_login_and_failure(self):
  d=self.live([],[(3600,'BM, Logged into the master successfully')]);self.assertEqual(d['network']['state'],'connected')
  d=self.live([],[(3600,'BM, Logged into the master successfully'),(2,'BM, Login to the master has failed, retrying login ...')]);self.assertEqual(d['network']['state'],'error')
 def test_network_render_and_rollback(self):
  original=(ROOT/'src/2pny-protocol-network-apply-0.2.7.py').read_text()
  with tempfile.TemporaryDirectory() as tmp:
   state=Path(tmp);cfg=state/'mmdvm/MMDVM-Host.ini';cfg.parent.mkdir()
   base='[General]\nCallsign=PU2PNY\nId=7241465\nDuplex=0\n[Modem]\nRXFrequency=439125000\nTXFrequency=439125000\n[DMR]\nEnable=1\n'
   cfg.write_text(base)
   code=original.replace('/var/lib/2pny',tmp)
   def run(kind,essid='',fail=False):
    def fake(args,**kw):
     rc=1 if fail and args[1:]==['restart','2pny-mmdvmhost.service'] else 0
     return subprocess.CompletedProcess(args,rc,'','')
    args=['apply','DMR','XLX_026' if kind=='XLX' else kind,'example.net','62030','test-password','hotspot','1','2','C',essid,kind,'']
    with patch.object(sys,'argv',args),patch('os.geteuid',return_value=0),patch('os.chown'),patch('grp.getgrnam',return_value=types.SimpleNamespace(gr_gid=os.getgid())),patch('subprocess.run',fake),patch('time.sleep'),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):exec(compile(code,'apply','exec'),{})
   run('XLX');gw=state/'dmr/DMRGateway.ini';self.assertIn('TG=6',gw.read_text());self.assertIn('Module=C',gw.read_text());self.assertIn('GatewayAddress=127.0.0.1',cfg.read_text())
   run('BrandMeister','01');self.assertIn('Id=724146501',gw.read_text());self.assertIn('PassAllTG=2',gw.read_text())
   run('TGIF','02');self.assertIn('Name=TGIF_Network',gw.read_text());self.assertIn('Id=724146502',gw.read_text())
   before={p:p.read_bytes() for p in (cfg,gw,state/'network-radio.json')}
   with self.assertRaises(SystemExit):run('BrandMeister','03',True)
   for p,b in before.items():self.assertEqual(p.read_bytes(),b)
   self.assertNotIn('test-password',(state/'network-radio.json').read_text())
 def test_station_history_one_row_per_call(self):
  import sqlite3
  m=runpy.run_path(str(ROOT/'src/2pny-station-worker-0.2.7.py'))
  db=sqlite3.connect(':memory:');db.execute('CREATE TABLE history(id TEXT PRIMARY KEY,stamp TEXT,data TEXT)')
  event={'type':'start','timestamp':'2026-09-18T12:00:00+00:00','source':'7241465','direction':'RF','slot':2}
  for _ in range(2):m['merge_event'](db,event)
  m['merge_event'](db,dict(event,type='end',timestamp='2026-09-18T12:00:25+00:00',duration=25,ber=0.5))
  rows=db.execute('SELECT data FROM history').fetchall();self.assertEqual(len(rows),1)
  result=json.loads(rows[0][0]);self.assertEqual(result['source'],'7241465');self.assertEqual(result['duration'],25)
  self.assertEqual(m['identity_key']('../../etc/passwd'),'')
 def test_dmr_rf_preserved(self):
  for name in ['2pny-rf-apply','2pny-protocol-network-apply','2pny-mmdvmhost','2pny-dmrgateway']:
   suffix='.py' if 'protocol-network' in name else '.service' if name.endswith(('mmdvmhost','dmrgateway')) else ''
   old=(ROOT/'src'/f'{name}-0.2.6{suffix}').read_text().replace('0.2.6','0.2.7')
   self.assertEqual(old,(ROOT/'src'/f'{name}-0.2.7{suffix}').read_text())
if __name__=='__main__':unittest.main()
