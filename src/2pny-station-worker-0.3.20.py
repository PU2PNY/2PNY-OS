#!/usr/bin/env python3
"""PU2PNY resident station worker 0.3.2.

One process owns live telemetry, bounded history, RadioID/QRZ enrichment,
network probes and CPU telemetry.  Browsers and physical displays only consume
the snapshots; opening extra tabs never starts extra collectors.
"""
import concurrent.futures, datetime, json, os, re, selectors, sqlite3, subprocess, time
import urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from importlib.machinery import SourceFileLoader

CORE=SourceFileLoader("pny_live_core","/usr/local/lib/2pny-live-core.py").load_module()
RUN=Path("/run/2pny"); STATE=Path("/var/lib/2pny/station"); PHOTOS=Path("/var/cache/2pny/photos"); NETWORK_RUNTIME=RUN/"network-runtime.json"

COUNTRY_CODES={
 "brazil":"BR","brasil":"BR","united states":"US","usa":"US","united kingdom":"GB",
 "england":"GB","portugal":"PT","spain":"ES","france":"FR","germany":"DE","italy":"IT",
 "argentina":"AR","uruguay":"UY","paraguay":"PY","chile":"CL","bolivia":"BO","peru":"PE",
 "colombia":"CO","mexico":"MX","canada":"CA","japan":"JP","australia":"AU","new zealand":"NZ",
 "netherlands":"NL","belgium":"BE","switzerland":"CH","austria":"AT","poland":"PL","norway":"NO",
 "sweden":"SE","denmark":"DK","finland":"FI","ireland":"IE","south africa":"ZA",
}

def atomic(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp");tmp.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")))
    os.chmod(tmp,0o644);os.replace(tmp,path)

def read_json(path,default=None):
    try:return json.loads(Path(path).read_text())
    except Exception:return {} if default is None else default

def fetch(url,data=None,limit=2*1024*1024):
    req=urllib.request.Request(url,data=data,headers={"User-Agent":"PU2PNY-OS/0.3.2"})
    with urllib.request.urlopen(req,timeout=5) as r:
        b=r.read(limit+1)
        if len(b)>limit:raise ValueError("response too large")
        return b

def qrz_photo(call):
    call=str(call or "").upper().strip()
    if not re.fullmatch(r"[A-Z0-9/]{3,16}",call):return ""
    PHOTOS.mkdir(parents=True,exist_ok=True)
    dest=PHOTOS/(call.replace("/","_")+".img")
    if dest.exists() and time.time()-dest.stat().st_mtime<7*86400:
        return "/operator-photo/"+dest.name
    url=""
    cfg=read_json("/var/lib/2pny/secrets/qrz.json")
    if cfg.get("username") and cfg.get("password"):
        def xml(values):
            root=ET.fromstring(fetch("https://xmldata.qrz.com/xml/current/",urllib.parse.urlencode(values).encode(),512*1024))
            return {e.tag.split("}")[-1]:e.text or "" for e in root.iter()}
        auth=xml({"username":cfg["username"],"password":cfg["password"],"agent":"PU2PNY-OS-0.3.2"})
        if auth.get("Key"):
            url=xml({"s":auth["Key"],"callsign":call}).get("image","")
    if not url:
        try:
            page=fetch("https://www.qrz.com/db/"+urllib.parse.quote(call),limit=1024*1024).decode("utf-8","ignore")
            m=re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',page,re.I)
            if not m:
                m=re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',page,re.I)
            if m:url=m.group(1)
        except Exception:return ""
    try:
        p=urllib.parse.urlparse(url)
        allowed=p.scheme=="https" and (p.hostname in ("cdn-bio.qrz.com","files.qrz.com") or
                (p.hostname=="s3.amazonaws.com" and p.path.startswith("/files.qrz.com/")))
        if not allowed:return ""
        data=fetch(url,limit=3*1024*1024)
        if not (data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"RIFF")):
            return ""
        tmp=dest.with_suffix(".tmp");tmp.write_bytes(data);os.replace(tmp,dest)
        for old in sorted(PHOTOS.glob("*.img"),key=lambda x:x.stat().st_mtime)[:-300]:old.unlink(missing_ok=True)
        return "/operator-photo/"+dest.name
    except Exception:return ""

def identity_key(source):
    key=str(source or "").strip().upper()
    return key if re.fullmatch(r"(?:[0-9]{5,9}|[A-Z0-9]{3,12}(?:/[A-Z0-9]{1,6})?)",key) else ""

def lookup(key):
    field="id" if key.isdigit() else "callsign"
    obj=json.loads(fetch("https://radioid.net/api/dmr/user/?"+urllib.parse.urlencode({field:key}),limit=1024*1024))
    rows=obj.get("results",[])
    if not rows:return {}
    row=next((x for x in rows if str(x.get("id"))==key or str(x.get("callsign","")).upper()==key),rows[0])
    person={k:str(row.get(k) or "")[:120] for k in ("callsign","city","state","country","id")}
    person["name"]=" ".join(dict.fromkeys(str(row.get(k) or "").strip() for k in ("fname","surname") if row.get(k))) or str(row.get("name") or "")
    cc=str(row.get("country_code") or row.get("countryCode") or "").upper()
    if not re.fullmatch(r"[A-Z]{2}",cc):cc=COUNTRY_CODES.get(person["country"].lower(),"")
    person["country_code"]=cc
    person["photo"]=qrz_photo(person["callsign"]) if person["callsign"] else ""
    person["updated"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    return person

def update_network_runtime_from_gateway(msg, ts=None, unit=""):
    """Track the effective XLX module selected over RF without rewriting the saved preset."""
    msg=str(msg or "")
    if not msg:return
    runtime=read_json(NETWORK_RUNTIME,{})
    changed=False
    # Custom PU2PNY group-call control, e.g. TG4002 -> module B.
    m=re.search(r"PU2PNY, XLX module control:\s*TG(40(?:0[1-9]|1[0-9]|2[0-6]))\s*->\s*module\s+([A-Z])",msg,re.I)
    if m:
        runtime.update({"protocol":"DMR","requested_module":m.group(2).upper(),"requested_module_tg":int(m.group(1)),
                        "module_source":"rf-control","link_state":"linking"})
        changed=True
    # Upstream confirms/relinks the effective room using the module letter.
    m=re.search(r"XLX,\s*(?:Re-)?Linking to reflector\s+XLX([0-9]{3})\s+([A-Z])",msg,re.I)
    if m:
        letter=m.group(2).upper()
        runtime.update({"protocol":"DMR","server_name":"XLX"+m.group(1),"module":letter,
                        "module_tg":4000+(ord(letter)-64),"module_source":"gateway","linked":True})
        changed=True
    if "PU2PNY, XLX module control: unlinked by TG4000" in msg:
        runtime.update({"protocol":"DMR","module":"","module_tg":4000,"module_source":"rf-control","linked":False})
        changed=True
    if re.search(r"XLX,\s*Unlinking from XLX[0-9]{3}",msg,re.I):
        runtime.update({"linked":False})
        changed=True
    # D-Star: F4FXL DStarGateway confirms successful outgoing links with
    # "DExtra/D-Plus/DCS link to <reflector> established".  Reflector names
    # carry the module as their last character (for example XLX026 D).
    if unit=="2pny-dstargateway.service":
        # PROTO-024/UI-032: expose only command/link evidence emitted by the
        # pinned gateway. Do not infer a remote link from process state.
        m=re.search(r"Link command from\s+(.+?)\s+to\s+([A-Z0-9 ]{4,9})\s+issued via\s+(.+?)\s+by\s+(.+)$",msg,re.I)
        if m:
            target=m.group(2).strip().upper()
            runtime.update({"protocol":"DSTAR","last_command":"link","last_command_target":target,
                            "last_command_source":m.group(3).strip(),"last_command_user":m.group(4).strip(),
                            "requested_server":target[:-1].strip() if len(target)>=2 and target[-1].isalpha() else target,
                            "requested_module":target[-1] if len(target)>=2 and target[-1].isalpha() else "",
                            "link_state":"linking"})
            changed=True
        m=re.search(r"Unlink command issued via\s+(.+?)\s+by\s+(.+)$",msg,re.I)
        if m:
            runtime.update({"protocol":"DSTAR","last_command":"unlink","last_command_source":m.group(1).strip(),
                            "last_command_user":m.group(2).strip(),"link_state":"unlinking"})
            changed=True
        m=re.search(r"(?:DExtra|D-Plus|DCS) link to\s+([A-Z0-9]{3,8})(?:\s+([A-Z]))?\s+established",msg,re.I)
        if m:
            server=m.group(1).upper();letter=(m.group(2) or "").upper()
            runtime.update({"protocol":"DSTAR","server_name":server,"module":letter,
                            "linked":True,"connected":True,"module_source":"gateway","link_state":"linked",
                            "requested_server":"","requested_module":"","last_command_error":""})
            changed=True
        unknown=re.search(r"([A-Z0-9 ]{4,9})\s+is unknown, ignoring link request",msg,re.I)
        if unknown:
            runtime.update({"protocol":"DSTAR","linked":False,"connected":False,"link_state":"failed",
                            "last_command_error":"refletor desconhecido: "+unknown.group(1).strip(),
                            "requested_server":"","requested_module":""});changed=True
        elif re.search(r"link (?:to .* )?(?:failed|refused|has failed)|not linked|unlink(?:ed|ing)?",msg,re.I):
            if not re.search(r"Link command",msg,re.I):
                runtime.update({"protocol":"DSTAR","linked":False,"connected":False,"link_state":"unlinked",
                                "requested_server":"","requested_module":""});changed=True
    # YSF: G4KLX YSFGateway logs "Linked to <reflector>" only after a poll
    # reply is received.  "Link has failed, polls lost" is the negative proof.
    if unit=="2pny-ysfgateway.service":
        m=re.search(r"\bLinked to\s+(.+?)\s*$",msg,re.I)
        if m:
            ref=m.group(1).strip().strip('"')
            runtime.update({"protocol":"YSF","server_name":ref,"linked":True,"connected":True})
            changed=True
        if re.search(r"Link has failed, polls lost|disconnect|unlinked",msg,re.I):
            runtime.update({"protocol":"YSF","linked":False,"connected":False});changed=True
    if changed:
        runtime["updated"]=CORE.iso(ts or time.time())
        atomic(NETWORK_RUNTIME,runtime)

def configured_host():
    for filename in ("/var/lib/2pny/network-radio.json","/var/lib/2pny/protocol-network.json"):
        data=read_json(filename)
        for key in ("address","host","server","gateway"):
            value=str(data.get(key) or "").strip()
            if re.fullmatch(r"[A-Za-z0-9.-]{1,253}",value):return value
    return "1.1.1.1"

def ping(host):
    started=time.monotonic()
    try:
        p=subprocess.run(["ping","-n","-c","1","-W","1",host],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=2)
        m=re.search(r"time[=<]([0-9.]+)\s*ms",p.stdout)
        return p.returncode==0,float(m.group(1)) if m else (time.monotonic()-started)*1000
    except Exception:return False,None

def journal_rows(unit,since="-210 seconds"):
    try:
        p=subprocess.run(["journalctl","-b","-u",unit,"--since",since,"--no-pager","-o","json"],text=True,capture_output=True,timeout=5)
        return p.stdout.splitlines()[-700:]
    except Exception:return []

def decode_journal(raw):
    try:
        row=json.loads(raw);msg=str(row.get("MESSAGE") or "").strip();micro=int(row.get("__REALTIME_TIMESTAMP") or 0)
        return msg,micro/1_000_000 if micro else time.time()
    except Exception:return "",time.time()

def start_follow(unit):
    return subprocess.Popen(["journalctl","-b","-u",unit,"-f","-n","0","-o","json"],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=1)

def start_mqtt():
    return subprocess.Popen(["mosquitto_sub","-h","127.0.0.1","-t","host/json","-t","dmr-gateway/json","-v"],
                            text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=1)

def persist_end(db,event):
    if not event or not isinstance(event,dict) or event.get("event")!="end":return
    event=dict(event)
    if str(event.get("protocol") or "").upper()=="DMR" and not event.get("module"):
        rt=read_json(NETWORK_RUNTIME,{})
        if rt.get("module"):
            event["module"]=rt.get("module")
            event["module_tg"]=rt.get("module_tg")
    key=f'{event.get("started_unix_ms",0)}:{event.get("direction")}:{event.get("protocol")}:{event.get("slot","")}'
    db.execute("INSERT OR REPLACE INTO history(id,stamp,data) VALUES(?,?,?)",
               (key,event.get("ended_at",""),json.dumps(event,ensure_ascii=False)));db.commit()

def network_telemetry():
    result={"wifi":{},"ethernet":{}}
    for base in Path("/sys/class/net").glob("*"):
        name=base.name
        if name=="lo":continue
        is_wifi=(base/"wireless").exists()
        try:carrier=int((base/"carrier").read_text().strip())
        except Exception:carrier=0
        def stat(key):
            try:return int((base/"statistics"/key).read_text().strip())
            except Exception:return 0
        if is_wifi:
            wifi={"interface":name,"carrier":bool(carrier),"rx_errors":stat("rx_errors"),"tx_errors":stat("tx_errors"),
                  "rx_dropped":stat("rx_dropped"),"tx_dropped":stat("tx_dropped")}
            try:
                out=subprocess.check_output(["iw","dev",name,"link"],text=True,timeout=1,stderr=subprocess.DEVNULL)
                m=re.search(r"SSID:\\s*(.+)",out);sig=re.search(r"signal:\\s*(-?[0-9.]+)\\s*dBm",out)
                wifi["ssid"]=m.group(1).strip() if m else ""
                wifi["rssi_dbm"]=float(sig.group(1)) if sig else None
            except Exception:pass
            result["wifi"]=wifi
        else:
            eth={"interface":name,"carrier":bool(carrier),"rx_errors":stat("rx_errors"),"tx_errors":stat("tx_errors"),
                 "rx_dropped":stat("rx_dropped"),"tx_dropped":stat("tx_dropped")}
            try:eth["speed_mbps"]=int((base/"speed").read_text().strip())
            except Exception:pass
            try:eth["duplex"]=(base/"duplex").read_text().strip().lower()
            except Exception:pass
            # Prefer an active wired interface when multiple USB/Ethernet NICs exist.
            if carrier or not result["ethernet"]:result["ethernet"]=eth
    return result

def telemetry(previous):
    nums=list(map(int,Path("/proc/stat").read_text().splitlines()[0].split()[1:]));total=sum(nums[:8]);idle=nums[3]+nums[4]
    usage=0 if not previous or total==previous[0] else max(0,min(100,100*(1-(idle-previous[1])/(total-previous[0]))))
    temp=-1;freq=-1
    try:temp=float(Path("/sys/class/thermal/thermal_zone0/temp").read_text())/1000
    except Exception:pass
    try:freq=float(Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq").read_text())/1000
    except Exception:pass
    mem={l.split(":")[0]:int(l.split()[1]) for l in Path("/proc/meminfo").read_text().splitlines()}
    try:load1,load5,load15=os.getloadavg()
    except Exception:load1=load5=load15=0.0
    throttled_raw=None;throttled_active=None
    try:
        p=subprocess.run(["vcgencmd","get_throttled"],text=True,capture_output=True,timeout=1)
        m=re.search(r"0x([0-9A-Fa-f]+)",p.stdout or "")
        if m:
            throttled_raw=int(m.group(1),16);throttled_active=bool(throttled_raw & 0xF)
    except Exception:pass
    info={"cpu_percent":round(usage,1),"temperature":round(temp,1),"cpu_frequency_mhz":round(freq,0),
          "load_1":round(load1,2),"load_5":round(load5,2),"load_15":round(load15,2),
          "throttled_raw":throttled_raw,"throttled_active":throttled_active,
          "memory_used_mb":round((mem["MemTotal"]-mem["MemAvailable"])/1024),
          "memory_total_mb":round(mem["MemTotal"]/1024),"network":network_telemetry()}
    try:
        ip=json.loads(subprocess.check_output(["ip","-j","-4","addr","show","scope","global"],timeout=2))
        addresses=[{"name":i["ifname"],"ipv4":a["local"]} for i in ip for a in i.get("addr_info",[]) if a.get("family")=="inet"]
        for obj in ({"CPU":{"temperature":temp,"frequency":freq,"load":usage/100}},{"Addresses":addresses}):
            subprocess.run(["mosquitto_pub","-h","127.0.0.1","-t","info/json","-m",json.dumps(obj)],timeout=2,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception:pass
    atomic(RUN/"telemetry.json",info)
    return (total,idle),info

def history_summary(db):
    rows=[]
    for (raw,) in db.execute("SELECT data FROM history ORDER BY stamp DESC LIMIT 1000"):
        try: rows.append(json.loads(raw))
        except Exception: pass
    cfg=read_json("/var/lib/2pny/config.json")
    station_type="Repetidora" if str(cfg.get("use_mode") or "").lower()=="repeater" else "Hotspot"
    by_call={};by_proto={};by_target={};tx_count=rx_count=0;tx_seconds=rx_seconds=0.0
    for e in rows:
        rawcall=str(e.get("source") or "").strip().upper()
        if not rawcall: continue
        person={}
        row=db.execute("SELECT data FROM contacts WHERE key=?",(rawcall,)).fetchone()
        if row:
            try: person=json.loads(row[0])
            except Exception: person={}
        call=str(person.get("callsign") or rawcall).strip().upper()
        proto=str(e.get("protocol") or "—").upper()
        target=str(e.get("target") or "—")
        dur=float(e.get("duration") or 0)
        direction=str(e.get("direction") or "").upper()
        if direction=="RF": tx_count+=1;tx_seconds+=dur
        else: rx_count+=1;rx_seconds+=dur
        by_proto[proto]=by_proto.get(proto,0)+1
        by_target[target]=by_target.get(target,0)+1
        e=dict(e);e["operator"]=person;e["station_type"]=station_type
        g=by_call.setdefault(call,{"callsign":call,"name":person.get("name") or "","city":person.get("city") or "",
            "state":person.get("state") or "","country":person.get("country") or "","country_code":person.get("country_code") or "",
            "photo":person.get("photo") or "","station_type":station_type,"count":0,"tx_count":0,"rx_count":0,"seconds":0.0,
            "last":e.get("ended_at") or e.get("started_at"),"last_protocol":proto,"last_target":target,
            "last_module":e.get("module") or "","items":[]})
        g["count"]+=1;g["seconds"]+=dur
        g["tx_count"]+=1 if direction=="RF" else 0;g["rx_count"]+=1 if direction!="RF" else 0
        if not g.get("last_module") and e.get("module"):g["last_module"]=e.get("module")
        if len(g["items"])<60:g["items"].append(e)
    groups=sorted(by_call.values(),key=lambda x:x.get("last") or "",reverse=True)
    top_proto=max(by_proto,key=by_proto.get) if by_proto else None
    top_target=max(by_target,key=by_target.get) if by_target else None
    return {"groups":groups[:120],"totals":{"events":len(rows),"tx_count":tx_count,"rx_count":rx_count,
        "tx_seconds":round(tx_seconds,1),"rx_seconds":round(rx_seconds,1),
        "most_used_protocol":top_proto,"most_used_target":top_target},
        "protocols":sorted([{"name":k,"count":v} for k,v in by_proto.items()],key=lambda x:x["count"],reverse=True),
        "targets":sorted([{"name":k,"count":v} for k,v in by_target.items()],key=lambda x:x["count"],reverse=True)[:20],
        "updated":datetime.datetime.now(datetime.timezone.utc).isoformat()}

def enrich_snapshot(db,state):
    snap=state.snapshot()
    objects=([snap["active"]] if snap.get("active") else [])+list(snap.get("history") or [])
    for event in objects:
        if not event:continue
        key=identity_key(event.get("source"))
        if not key:continue
        row=db.execute("SELECT data FROM contacts WHERE key=?",(key,)).fetchone()
        if row:
            try:event["operator"]=json.loads(row[0])
            except Exception:pass
    return snap

def main():
    RUN.mkdir(parents=True,exist_ok=True);STATE.mkdir(parents=True,exist_ok=True);PHOTOS.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(STATE/"operators.sqlite");db.execute("PRAGMA journal_mode=WAL");db.execute("PRAGMA journal_size_limit=1048576")
    db.execute("CREATE TABLE IF NOT EXISTS history(id TEXT PRIMARY KEY,stamp TEXT,data TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS contacts(key TEXT PRIMARY KEY,checked REAL,data TEXT)")
    state=CORE.LiveState(history_limit=200)
    for row in db.execute("SELECT data FROM history ORDER BY stamp DESC LIMIT 200"):
        try:state.history.append(json.loads(row[0]))
        except Exception:pass
    # Journal bootstrap is fallback only; live MQTT takes precedence once online.
    for raw in journal_rows("2pny-mmdvmhost.service"):
        msg,ts=decode_journal(raw);persist_end(db,state.ingest(msg,ts))
    gateway_units=("2pny-dmrgateway.service","2pny-dstargateway.service","2pny-ysfgateway.service","2pny-p25gateway.service","2pny-nxdngateway.service","2pny-dapnetgateway.service")
    for unit in gateway_units:
        for raw in journal_rows(unit,"-15 minutes"):
            msg,ts=decode_journal(raw);state.ingest(msg,ts,gateway=True)
            update_network_runtime_from_gateway(msg,ts,unit)

    hostlog=start_follow("2pny-mmdvmhost.service");gwlogs=[(unit,start_follow(unit)) for unit in gateway_units];mqtt=start_mqtt()
    sel=selectors.DefaultSelector()
    sel.register(hostlog.stdout,selectors.EVENT_READ,("journal",False,"2pny-mmdvmhost.service"))
    for unit,gwlog in gwlogs:sel.register(gwlog.stdout,selectors.EVENT_READ,("journal",True,unit))
    sel.register(mqtt.stdout,selectors.EVENT_READ,("mqtt",False,"mqtt"))
    pool=concurrent.futures.ThreadPoolExecutor(max_workers=2,thread_name_prefix="pny")
    probe=None;lookup_job=None;last_lookup=0;next_probe=0;last_write=0;last_seq=-1;dirty=True
    last_contacts=0;last_history_summary=0;last_housekeeping=0;last_telemetry=0;previous_cpu=None

    while True:
        now=time.monotonic();wall=time.time()
        for key,_ in sel.select(timeout=0.10):
            raw=key.fileobj.readline()
            if not raw:continue
            kind,gateway,unit=key.data
            event=None
            if kind=="mqtt":
                try:
                    topic,payload=raw.split(" ",1);obj=json.loads(payload)
                    if topic=="host/json":event=state.ingest_json(obj,wall)
                    elif topic=="dmr-gateway/json":
                        link=obj.get("link") if isinstance(obj,dict) else None
                        if isinstance(link,dict):
                            action=str(link.get("action") or "")
                            if action in ("linking","linked","connected"):
                                state.network={"state":"connected","message":action,"updated":CORE.iso(wall)};state._touch()
                                rt=read_json(NETWORK_RUNTIME,{})
                                rt.update({"protocol":"DMR","linked":True,"updated":CORE.iso(wall)});atomic(NETWORK_RUNTIME,rt)
                            elif action in ("unlinked","disconnected"):
                                state.network={"state":"disconnected","message":action,"updated":CORE.iso(wall)};state._touch()
                                rt=read_json(NETWORK_RUNTIME,{})
                                rt.update({"protocol":"DMR","linked":False,"updated":CORE.iso(wall)});atomic(NETWORK_RUNTIME,rt)
                except Exception:pass
            else:
                msg,ts=decode_journal(raw);event=state.ingest(msg,ts,gateway=gateway)
                if gateway:update_network_runtime_from_gateway(msg,ts,unit)
                # Actual network traffic is stronger evidence than a service
                # process being active. Keep the connected flag truthful.
                if event and str(event.get("protocol") or "").upper() in ("DSTAR","YSF"):
                    rt=read_json(NETWORK_RUNTIME,{})
                    rt.update({"protocol":str(event.get("protocol") or "").upper(),"linked":True,"connected":True,"updated":CORE.iso(ts)})
                    atomic(NETWORK_RUNTIME,rt)
            persist_end(db,event)
            if event:dirty=True

        state.clear_stale(300,wall)

        if probe and probe.done():
            try:ok,lat=probe.result()
            except Exception:ok,lat=False,None
            state.add_probe(ok,lat);probe=None;dirty=True
            next_probe=now+(1.0 if any(state.active.values()) else 5.0)
        if probe is None and now>=next_probe:probe=pool.submit(ping,configured_host())

        if lookup_job and lookup_job[1].done():
            ident,fut=lookup_job
            try:person=fut.result()
            except Exception:person={}
            old=db.execute("SELECT data FROM contacts WHERE key=?",(ident,)).fetchone()
            if not person and old:
                try:person=json.loads(old[0]);person["stale"]=True
                except Exception:person={}
            db.execute("INSERT OR REPLACE INTO contacts VALUES(?,?,?)",(ident,wall,json.dumps(person,ensure_ascii=False)));db.commit()
            lookup_job=None;dirty=True

        # Pick one stale identity at a time; never hammer RadioID/QRZ.
        if not lookup_job and wall-last_lookup>=15:
            candidates=[]
            cfg=read_json("/var/lib/2pny/config.json")
            for own in (cfg.get("callsign"),cfg.get("dmr_id")):
                if own:candidates.append({"source":str(own)})
            active=state.snapshot().get("active")
            if active:candidates.append(active)
            candidates+=list(state.history)[:25]
            for ev in candidates:
                ident=identity_key(ev.get("source"))
                if not ident:continue
                row=db.execute("SELECT checked,data FROM contacts WHERE key=?",(ident,)).fetchone()
                person={}
                if row:
                    try:person=json.loads(row[1])
                    except Exception:pass
                ttl=86400 if person and not person.get("stale") else 3600
                if not row or wall-row[0]>ttl:
                    lookup_job=(ident,pool.submit(lookup,ident));last_lookup=wall;break

        telem_interval=3 if any(state.active.values()) else 15
        if wall-last_telemetry>=telem_interval:
            try:previous_cpu,_=telemetry(previous_cpu)
            except Exception:pass
            last_telemetry=wall

        if state.sequence!=last_seq or dirty or now-last_write>=15:
            snap=enrich_snapshot(db,state)
            atomic(RUN/"live-state.json",snap)
            last_seq=state.sequence;last_write=now;dirty=False

        if wall-last_history_summary>=15:
            try: atomic(RUN/"history-summary.json",history_summary(db))
            except Exception: pass
            last_history_summary=wall

        if wall-last_contacts>=30:
            contacts=[]
            for data,keyname in db.execute("SELECT data,key FROM contacts ORDER BY checked DESC LIMIT 500"):
                try:
                    p=json.loads(data)
                    if p:contacts.append(dict(p,cache_key=keyname))
                except Exception:pass
            atomic(RUN/"contacts.json",{"contacts":contacts});last_contacts=wall

        if wall-last_housekeeping>=3600:
            cutoff=datetime.datetime.fromtimestamp(wall-86400,datetime.timezone.utc).isoformat()
            db.execute("DELETE FROM history WHERE stamp<?",(cutoff,))
            db.execute("DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY stamp DESC LIMIT 1000)")
            db.execute("DELETE FROM contacts WHERE key NOT IN (SELECT key FROM contacts ORDER BY checked DESC LIMIT 5000)")
            db.commit();last_housekeeping=wall

if __name__=="__main__":main()
