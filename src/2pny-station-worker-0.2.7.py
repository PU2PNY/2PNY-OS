#!/usr/bin/env python3
"""Bounded local history and identity cache; never changes RF parameters."""
import concurrent.futures, datetime, hashlib, json, os, re, sqlite3, subprocess, time
import urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
STATE=Path('/var/lib/2pny/station'); RUN=Path('/run/2pny'); PHOTOS=Path('/var/cache/2pny/photos')

def read_json(path, default=None):
    try:return json.loads(Path(path).read_text())
    except Exception:return {} if default is None else default

def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False));os.chmod(tmp,0o644);os.replace(tmp,path)

def fetch(url,data=None,limit=1048576):
    req=urllib.request.Request(url,data=data,headers={'User-Agent':'PU2PNY-OS/0.2.7 (cached operator lookup)'})
    with urllib.request.urlopen(req,timeout=6) as r:
        b=r.read(limit+1)
        if len(b)>limit:raise ValueError('response too large')
        return b

def qrz_photo(call):
    cfg=read_json('/var/lib/2pny/secrets/qrz.json')
    if not cfg.get('username') or not cfg.get('password'):return ''
    dest=PHOTOS/(call+'.img')
    if dest.exists() and time.time()-dest.stat().st_mtime<7*86400:return '/operator-photo/'+call+'.img'
    def xml(values):
        root=ET.fromstring(fetch('https://xmldata.qrz.com/xml/current/',urllib.parse.urlencode(values).encode()))
        return {e.tag.split('}')[-1]:e.text or '' for e in root.iter()}
    auth=xml({'username':cfg['username'],'password':cfg['password'],'agent':'PU2PNY-OS-0.2.7'})
    if not auth.get('Key'):return ''
    result=xml({'s':auth['Key'],'callsign':call});url=result.get('image','');parsed=urllib.parse.urlparse(url)
    # QRZ supplies the URL, but do not allow arbitrary origins or local requests.
    if parsed.scheme!='https' or not (parsed.hostname in ('cdn-bio.qrz.com','files.qrz.com') or (parsed.hostname=='s3.amazonaws.com' and parsed.path.startswith('/files.qrz.com/'))):return ''
    data=fetch(url,limit=2*1024*1024)
    if not (data.startswith(b'\xff\xd8\xff') or data.startswith(b'\x89PNG\r\n\x1a\n')):return ''
    PHOTOS.mkdir(parents=True,exist_ok=True);tmp=dest.with_suffix('.tmp');tmp.write_bytes(data);os.replace(tmp,dest)
    for old in sorted(PHOTOS.glob('*.img'),key=lambda x:x.stat().st_mtime)[:-300]:old.unlink(missing_ok=True)
    return '/operator-photo/'+call+'.img'

def lookup(key):
    field='id' if key.isdigit() else 'callsign'
    obj=json.loads(fetch('https://radioid.net/api/dmr/user/?'+urllib.parse.urlencode({field:key})))
    rows=obj.get('results',[])
    if not rows:return {}
    row=next((x for x in rows if str(x.get('id'))==key or str(x.get('callsign','')).upper()==key),rows[0])
    person={k:str(row.get(k) or '')[:120] for k in ('callsign','city','state','country','id')}
    person['name']=' '.join(dict.fromkeys(str(row.get(k) or '').strip() for k in ('fname','surname') if row.get(k))) or str(row.get('name') or '')
    try:person['photo']=qrz_photo(person['callsign'])
    except Exception:person['photo']=''
    person['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    return person

def identity_key(source):
    key=str(source).strip().upper()
    return key if re.fullmatch(r'(?:[0-9]{5,9}|[A-Z0-9]{3,12}(?:/[A-Z0-9]{1,6})?)',key) else ''

def merge_event(db,event):
    if event.get('type')=='start':
        key=hashlib.sha256((event['timestamp']+event['direction']+str(event.get('slot'))+event.get('source','')).encode()).hexdigest()[:24]
        db.execute('INSERT OR IGNORE INTO history VALUES(?,?,?)',(key,event['timestamp'],json.dumps(event)))
    elif event.get('type')=='end':
        candidates=db.execute('SELECT id,data FROM history WHERE stamp<=? ORDER BY stamp DESC LIMIT 20',(event['timestamp'],)).fetchall()
        for key,raw in candidates:
            e=json.loads(raw)
            if e.get('direction')==event.get('direction') and e.get('slot')==event.get('slot'):
                for k in ('duration','ber','rssi','loss','quality'): 
                    if k in event:e[k]=event[k]
                e['ended']=event['timestamp'];db.execute('UPDATE history SET data=? WHERE id=?',(json.dumps(e),key));break

def telemetry(previous):
    nums=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]));total=sum(nums[:8]);idle=nums[3]+nums[4]
    usage=0 if not previous or total==previous[0] else max(0,min(100,100*(1-(idle-previous[1])/(total-previous[0]))))
    temp=-1;freq=-1
    try:temp=float(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000
    except Exception:pass
    try:freq=float(Path('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq').read_text())/1000
    except Exception:pass
    mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()}
    info={'cpu_percent':round(usage,1),'temperature':temp,'memory_used_mb':round((mem['MemTotal']-mem['MemAvailable'])/1024),'memory_total_mb':round(mem['MemTotal']/1024)}
    try:
        ip=json.loads(subprocess.check_output(['ip','-j','-4','addr','show','scope','global'],timeout=2))
        addresses=[{'name':i['ifname'],'ipv4':a['local']} for i in ip for a in i.get('addr_info',[]) if a.get('family')=='inet']
        for obj in [{'CPU':{'temperature':temp,'frequency':freq,'load':usage/100}},{'Addresses':addresses}]:
            subprocess.run(['mosquitto_pub','-h','127.0.0.1','-t','info/json','-m',json.dumps(obj)],timeout=2,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception:pass
    atomic(RUN/'telemetry.json',info)
    return total,idle

def main():
    STATE.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(STATE/'operators.sqlite');db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA journal_size_limit=1048576')
    db.execute('CREATE TABLE IF NOT EXISTS contacts (key TEXT PRIMARY KEY, checked REAL, data TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS history (id TEXT PRIMARY KEY, stamp TEXT, data TEXT)')
    seen=set();pool=concurrent.futures.ThreadPoolExecutor(max_workers=1);pending=None;last_lookup=0;last_housekeeping=0;last_telemetry=0;previous=None
    while True:
        now=time.time()
        try:
            if pending and pending[1].done():
                key,future=pending
                try:person=future.result()
                except Exception:person={}
                old=db.execute('SELECT data FROM contacts WHERE key=?',(key,)).fetchone()
                if not person and old:person=json.loads(old[0]);person['stale']=True
                db.execute('INSERT OR REPLACE INTO contacts VALUES(?,?,?)',(key,now,json.dumps(person)));db.commit();pending=None
            live=json.loads(subprocess.check_output(['/usr/local/sbin/2pny-live-status'],timeout=9))
            for ev in live.get('events',[]):
                ident=json.dumps(ev,sort_keys=True)
                if ident not in seen:merge_event(db,ev);seen.add(ident)
            if len(seen)>2000:seen=set(json.dumps(e,sort_keys=True) for e in live.get('events',[]))
            db.commit()
            history=[json.loads(r[0]) for r in db.execute('SELECT data FROM history ORDER BY stamp DESC LIMIT 200')]
            objects=[live.get('rx',{}),live.get('tx',{})]+history
            for event in objects:
                key=identity_key(event.get('source',''))
                if not key:continue
                row=db.execute('SELECT checked,data FROM contacts WHERE key=?',(key,)).fetchone()
                person=json.loads(row[1]) if row else {}
                if person:event['operator']=person
                ttl=86400 if person and not person.get('stale') else 3600
                if not pending and now-last_lookup>=15 and (not row or now-row[0]>ttl):
                    pending=(key,pool.submit(lookup,key));last_lookup=now
            live['history']=history;live['history_limit']=200;live['cache_ttl_hours']=24
            atomic(RUN/'live-enriched.json',live)
            atomic(RUN/'contacts.json',{'contacts':[dict(json.loads(r[0]),cache_key=r[1]) for r in db.execute('SELECT data,key FROM contacts ORDER BY checked DESC LIMIT 500') if json.loads(r[0])]})
            if now-last_telemetry>=15:previous=telemetry(previous);last_telemetry=now
            if now-last_housekeeping>=3600:
                cutoff=datetime.datetime.fromtimestamp(now-86400,datetime.timezone.utc).isoformat()
                db.execute('DELETE FROM history WHERE stamp<?',(cutoff,))
                db.execute('DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY stamp DESC LIMIT 1000)')
                db.execute('DELETE FROM contacts WHERE key NOT IN (SELECT key FROM contacts ORDER BY checked DESC LIMIT 5000)');db.commit();last_housekeeping=now
        except Exception as e:print('station-worker:',type(e).__name__,flush=True)
        time.sleep(2)
if __name__=='__main__':main()
