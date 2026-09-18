#!/usr/bin/env python3
import json,re,subprocess,datetime

def journal():
    try:
        p=subprocess.run(["journalctl","-u","2pny-mmdvmhost.service","-n","160","--no-pager","-o","short-iso"],
                         text=True,capture_output=True,timeout=3)
        return [x.strip() for x in p.stdout.splitlines() if x.strip()]
    except Exception:
        return []

lines=journal()
useful=[x for x in lines if "MQTT Error connecting" not in x and "unable to start the MQTT Publisher" not in x]

net={"state":"unknown","message":"Aguardando estado da rede digital."}
for line in reversed(useful):
    low=line.lower()
    if "logged into the master successfully" in low:
        net={"state":"connected","message":"Conectado ao servidor DMR."}; break
    if "connection to the master has timed out" in low or "login failed" in low or "authentication failed" in low:
        net={"state":"error","message":line.split(" MMDVM-Host")[-1].strip()}; break
    if "sending authorisation" in low or "sending configuration" in low or "opening dmr network" in low:
        net={"state":"connecting","message":"Conectando/autenticando no servidor DMR..."}; break
    if "closing dmr network" in low:
        net={"state":"disconnected","message":"Rede DMR desconectada."}; break

events=[]
live={"active":False}
header_re=re.compile(r"DMR Slot (\d), received (RF|network) voice header from (.+?) to (TG )?([^,]+)",re.I)
end_re=re.compile(r"DMR Slot (\d), received (RF|network) end of voice transmission.*?([0-9.]+) seconds(?:, ([0-9.]+)% packet loss)?(?:, BER: ([0-9.]+)%)?(?:, RSSI: ([^,]+? dBm))?$",re.I)

for line in useful[-120:]:
    if "DMR Slot" not in line and "DMR," not in line:
        continue
    m=header_re.search(line)
    if m:
        slot=int(m.group(1)); direction=m.group(2).upper()
        source=m.group(3).strip(); target=("TG " if m.group(4) else "")+m.group(5).strip()
        ev={"type":"start","protocol":"DMR","slot":slot,"direction":direction,
            "source":source,"target":target,"line":line}
        events.append(ev)
        live={"active":True,"protocol":"DMR","slot":slot,"direction":direction,
              "source":source,"target":target}
        continue
    m=end_re.search(line)
    if m:
        ev={"type":"end","protocol":"DMR","slot":int(m.group(1)),"direction":m.group(2).upper(),
            "duration":float(m.group(3)),"line":line}
        if m.group(4): ev["loss"]=float(m.group(4))
        if m.group(5): ev["ber"]=float(m.group(5))
        if m.group(6): ev["rssi"]=m.group(6).strip()
        events.append(ev)
        live={"active":False,"protocol":"DMR","slot":int(m.group(1)),"direction":m.group(2).upper(),
              "duration":float(m.group(3))}
        if "ber" in ev: live["ber"]=ev["ber"]
        if "rssi" in ev: live["rssi"]=ev["rssi"]
        continue
    if "DMR," in line:
        events.append({"type":"network","protocol":"DMR","line":line})

events=events[-30:]
print(json.dumps({
    "network":net,
    "live":live,
    "events":events,
    "updated":datetime.datetime.now(datetime.timezone.utc).isoformat()
},ensure_ascii=False))
