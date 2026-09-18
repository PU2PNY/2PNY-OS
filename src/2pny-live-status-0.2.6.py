#!/usr/bin/env python3
import datetime,json,re,subprocess,time

NOW=time.time()
WINDOW=150
ACTIVE_TTL=12

def journal():
    try:
        p=subprocess.run([
            "journalctl","-u","2pny-mmdvmhost.service","-u","2pny-dmrgateway.service",
            "--since",f"-{WINDOW} seconds","-n","500","--no-pager","-o","json"
        ],text=True,capture_output=True,timeout=4)
        out=[]
        for raw in p.stdout.splitlines():
            try:
                j=json.loads(raw); msg=str(j.get("MESSAGE") or "").strip()
                if not msg: continue
                us=int(j.get("__REALTIME_TIMESTAMP") or 0)
                ts=us/1_000_000 if us else NOW
                out.append({"ts":ts,"message":msg,"unit":str(j.get("_SYSTEMD_UNIT") or "")})
            except Exception: pass
        return out
    except Exception:
        return []

def iso(ts):
    return datetime.datetime.fromtimestamp(ts,datetime.timezone.utc).isoformat()

def rssi_num(s):
    if not s: return None
    m=re.search(r"-?\d+(?:\.\d+)?",str(s))
    return float(m.group()) if m else None

def quality(ber=None,rssi=None):
    rv=rssi_num(rssi)
    if ber is not None:
        try: ber=float(ber)
        except Exception: ber=None
    if ber is None and rv is None: return {"label":"Sem dados","score":0}
    score=100
    if ber is not None: score-=min(70,ber*14)
    if rv is not None:
        if rv<-125: score-=45
        elif rv<-115: score-=25
        elif rv<-105: score-=10
    score=max(0,min(100,int(round(score))))
    label="Ótimo" if score>=80 else ("Bom" if score>=55 else "Ruim")
    return {"label":label,"score":score}

rows=journal()
net={"state":"unknown","message":"Aguardando estado do DMRGateway.","updated":None}
for row in reversed(rows):
    if "dmrgateway" not in row["unit"].lower() and "dmr" not in row["message"].lower() and "xlx" not in row["message"].lower():
        continue
    low=row["message"].lower()
    if "logged into the master successfully" in low or "login successful" in low:
        net={"state":"connected","message":"DMRGateway autenticado no servidor.","updated":iso(row["ts"])}; break
    if any(x in low for x in ("authentication failed","login failed","login rejected","incorrect password","connection to the master has timed out","timed out waiting","network is down")):
        net={"state":"error","message":row["message"][-180:],"updated":iso(row["ts"])}; break
    if "connecting to xlx" in low or "sending authorisation" in low or "sending configuration" in low or "opening" in low:
        net={"state":"connecting","message":"DMRGateway conectando/autenticando no servidor.","updated":iso(row["ts"])}; break
    if "closing" in low and ("network" in low or "xlx" in low):
        net={"state":"disconnected","message":"Rede DMR desconectada.","updated":iso(row["ts"])}; break

header_re=re.compile(r"DMR Slot (\d), received (RF|network) voice header from (.+?) to (TG )?([^,]+)",re.I)
end_re=re.compile(r"DMR Slot (\d), received (RF|network) end of voice transmission.*?([0-9.]+) seconds(?:, ([0-9.]+)% packet loss)?(?:, BER: ([0-9.]+)%)?(?:, RSSI: ([^,]+? dBm))?$",re.I)
ta_re=re.compile(r"DMR Slot (\d).*?(?:talker alias|alias).*?[:=]\s*(.+)$",re.I)

channels={"RF":{"active":False,"direction":"RF","label":"RX","path":"Rádio → hotspot"},
          "NETWORK":{"active":False,"direction":"NETWORK","label":"TX","path":"Rede → rádio"}}
last_start={"RF":None,"NETWORK":None}; last_end={"RF":None,"NETWORK":None}; aliases={}
events=[]
for row in rows:
    msg=row["message"]
    m=ta_re.search(msg)
    if m: aliases[int(m.group(1))]=m.group(2).strip()[:80]
    m=header_re.search(msg)
    if m:
        slot=int(m.group(1)); direction=m.group(2).upper(); source=m.group(3).strip()
        target=("TG " if m.group(4) else "")+m.group(5).strip()
        ev={"type":"start","protocol":"DMR","slot":slot,"direction":direction,"source":source,
            "target":target,"timestamp":iso(row["ts"]),"ts":row["ts"]}
        if slot in aliases: ev["alias"]=aliases[slot]
        events.append(ev); last_start[direction]=ev
        continue
    m=end_re.search(msg)
    if m:
        direction=m.group(2).upper()
        ev={"type":"end","protocol":"DMR","slot":int(m.group(1)),"direction":direction,
            "duration":float(m.group(3)),"timestamp":iso(row["ts"]),"ts":row["ts"]}
        if m.group(4): ev["loss"]=float(m.group(4))
        if m.group(5): ev["ber"]=float(m.group(5))
        if m.group(6): ev["rssi"]=m.group(6).strip()
        ev["quality"]=quality(ev.get("ber"),ev.get("rssi"))
        events.append(ev); last_end[direction]=ev

for direction,ch in channels.items():
    st=last_start[direction]; en=last_end[direction]
    if st:
        ch.update({k:v for k,v in st.items() if k not in ("type","ts")})
        ch["last_timestamp"]=st["timestamp"]
    if en and (not st or en["ts"]>=st["ts"]):
        ch["active"]=False
        for k in ("duration","ber","rssi","loss","quality"):
            if k in en: ch[k]=en[k]
        ch["last_timestamp"]=en["timestamp"]
    elif st and NOW-st["ts"]<=ACTIVE_TTL:
        ch["active"]=True
        ch["age_seconds"]=round(NOW-st["ts"],1)
        ch["quality"]={"label":"Ativo","score":100}
    elif st:
        ch["active"]=False
        ch["quality"]={"label":"Finalizado","score":0}
    if "quality" not in ch: ch["quality"]={"label":"Sem dados","score":0}

events=[{k:v for k,v in e.items() if k!="ts"} for e in events[-40:]]
print(json.dumps({
    "network":net,
    "rx":channels["RF"],
    "tx":channels["NETWORK"],
    "events":events,
    "updated":datetime.datetime.now(datetime.timezone.utc).isoformat()
},ensure_ascii=False))
