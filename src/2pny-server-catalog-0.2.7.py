#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
BASE=Path("/var/lib/2pny/hosts")

SEED={
 "DMR":[
   {"name":"XLX_026","id":"026","address":"82.152.175.30","port":62030,"default_password":"passw0rd","kind":"XLX","priority":0,"description":"XLX026 Brasil","reflector":"026","default_module":"C","default_tg":6},
   {"name":"BM_7242_Brazil","id":"7242","address":"7242.master.brandmeister.network","port":62031,"default_password":"","kind":"BrandMeister","priority":1,"description":"BrandMeister Brasil"},
   {"name":"TGIF_Network","id":"0000","address":"tgif.network","port":62031,"default_password":"passw0rd","kind":"TGIF","priority":2,"description":"TGIF Network"},
 ],
 "YSF":[{"name":"BR-XLX026 Brazil","id":"72426","address":"82.152.175.30","port":42000,"kind":"YSF","priority":0,"description":"C4FM/YSF XLX026 Brasil"}],
}

def kind_dmr(name):
    u=name.upper()
    if u.startswith("BM_"): return "BrandMeister"
    if u.startswith("FREEDMR_") or u.startswith("FD_"): return "FreeDMR"
    if "TGIF" in u: return "TGIF"
    if u.startswith("XLX_"): return "XLX"
    if u.startswith("DMR+_") or "IPSC2" in u: return "DMR+"
    if u.startswith("HB_"): return "HBLink"
    if u.startswith("FREESTAR_"): return "FreeSTAR"
    return "DMR"

def decorate(x):
    x=dict(x); kind=x.get("kind") or kind_dmr(str(x.get("name",""))); x["kind"]=kind
    x["slot_supported"]=True
    x["essid_supported"]=kind in ("BrandMeister","TGIF","FreeDMR","DMR+","HBLink","DMR")
    if kind=="BrandMeister":
        x["default_password"]=""
        x["password_label"]="Hotspot Security"
        x["password_required"]=True
        x["api_supported"]=True
        x["api_label"]="BrandMeister API Key"
        x["help"]="Hotspot Security autentica o hotspot. API Key é opcional e serve apenas para gerenciamento."
    elif kind=="XLX":
        x["password_label"]="Senha XLX"
        x["password_required"]=False
        x["default_password"]=x.get("default_password") or "passw0rd"
        m=re.search(r"(\d{3})",str(x.get("name","")))
        if m: x["reflector"]=m.group(1)
        x["module_supported"]=True
        x["default_module"]="C" if x.get("reflector")=="026" else "A"
        x["default_tg"]=6
        x["help"]="XLX usa DMRGateway. No XLX026, TG 6 no rádio e módulo C para voz DMR."
    elif kind=="TGIF":
        x["password_label"]="TGIF Hotspot Security"
        x["password_required"]=False
        x["default_password"]=x.get("default_password") or "passw0rd"
        x["help"]="Use sua chave TGIF para conexão segura ou passw0rd para modo legado quando permitido."
    else:
        x["password_label"]="Senha do master"
        x["password_required"]=False
        x["help"]="Servidor DMR/Homebrew através do DMRGateway."
    return x

def read_dmr():
    out=[]; p=BASE/"DMR_Hosts.txt"
    if p.exists():
        for raw in p.read_text(errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#"): continue
            parts=line.split()
            if len(parts)<5: continue
            name,dmrid,address,password,port=parts[:5]
            try: port=int(port)
            except Exception: continue
            if name in ("DMRGateway","DMR2YSF","DMR2NXDN"): continue
            out.append(decorate({"name":name,"id":dmrid,"address":address,"port":port,
                                 "default_password":password,"kind":kind_dmr(name),
                                 "description":name.replace("_"," ")}))
    return out

def read_ysf():
    out=[]; p=BASE/"YSFHosts.txt"
    if p.exists():
        for raw in p.read_text(errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#"): continue
            parts=line.split(";")
            if len(parts)<5: continue
            try: port=int(parts[4])
            except Exception: continue
            out.append({"id":parts[0].strip(),"name":parts[1].strip(),"description":parts[2].strip(),
                        "address":parts[3].strip(),"port":port,"kind":"YSF"})
    return out

def read_simple(filename,kind):
    out=[]; p=BASE/filename
    if not p.exists(): return out
    for raw in p.read_text(errors="ignore").splitlines():
        line=raw.strip()
        if not line or line.startswith("#"): continue
        parts=line.replace(";"," ").split()
        if len(parts)<3: continue
        try: port=int(parts[2])
        except Exception: continue
        out.append({"name":parts[0],"address":parts[1],"port":port,"kind":kind,"description":parts[0].replace("_"," ")})
    return out

def read_dstar():
    out=[]
    for filename,kind in (("DPlus_Hosts.txt","DPlus"),("DExtra_Hosts.txt","DExtra"),("DCS_Hosts.txt","DCS")):
        p=BASE/filename
        if not p.exists(): continue
        for raw in p.read_text(errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#"): continue
            parts=line.replace(";"," ").split()
            if len(parts)>=2: out.append({"name":parts[0],"address":parts[1],"port":0,"kind":kind,"description":kind+" "+parts[0]})
    return out

def merge_seed(proto,items):
    pinned={str(x["name"]):decorate(x) if proto=="DMR" else dict(x) for x in SEED.get(proto,[])}
    merged=list(pinned.values())
    seen=set(pinned)
    for x in items:
        name=str(x.get("name",""))
        if name in seen: continue
        seen.add(name); merged.append(x)
    pin={name:i for i,name in enumerate(pinned)}
    merged.sort(key=lambda x:(pin.get(str(x.get("name")),50),str(x.get("kind","")),str(x.get("name","")).lower()))
    return merged

def main():
    proto=(sys.argv[1] if len(sys.argv)>1 else "DMR").upper()
    query=(sys.argv[2] if len(sys.argv)>2 else "").lower().strip()
    if proto=="DMR": items=read_dmr()
    elif proto=="YSF": items=read_ysf()
    elif proto=="P25": items=read_simple("P25Hosts.txt","P25")
    elif proto=="NXDN": items=read_simple("NXDNHosts.txt","NXDN")
    elif proto=="DSTAR": items=read_dstar()
    else: items=[]
    items=merge_seed(proto,items)
    if query: items=[x for x in items if query in (" ".join(str(v) for v in x.values())).lower()]
    total=len(items)
    if not query and len(items)>700: items=items[:700]
    print(json.dumps({"protocol":proto,"servers":items,"total":total,"cache_updated":(BASE/".updated").exists()},ensure_ascii=False))
if __name__=="__main__": main()

