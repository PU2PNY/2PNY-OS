#!/usr/bin/env python3
"""PU2PNY unified protocol catalog 0.3.1.

The backend keeps complete cached catalogs; the UI decides how much to render.
Nothing is silently truncated here.
"""
import json,re,sys
from pathlib import Path
BASE=Path("/var/lib/2pny/hosts")
AZ=[chr(x) for x in range(65,91)]

SEED={
 "DMR":[
  {"name":"XLX026","id":"026","address":"82.152.175.30","port":62030,"kind":"XLX","priority":0,"description":"XLX026 Brasil","default_module":"C","modules":AZ,"default_tg":6,"default_password":"passw0rd"},
  {"name":"BM 7242 Brasil","id":"7242","address":"7242.master.brandmeister.network","port":62031,"kind":"BrandMeister","priority":1,"description":"BrandMeister Brasil","default_password":""},
 ],
 "DSTAR":[
  {"name":"XLX026","id":"026","address":"82.152.175.30","port":0,"kind":"XLX","priority":0,"description":"XLX026 Brasil","default_module":"D","modules":AZ},
 ],
 "YSF":[{"name":"BR-XLX026","id":"72426","address":"82.152.175.30","port":42000,"kind":"YSF","priority":0,"description":"YSF XLX026 Brasil"}],
 "POCSAG":[
  {"name":"DAPNET","address":"dapnet.afu.rwth-aachen.de","port":43434,"kind":"DAPNET","priority":0,"description":"DAPNET POCSAG","password_label":"DAPNET AuthKey","password_required":True},
 ],
 "APRS":[
  {"name":"Brasil APRS2","address":"brazil.aprs2.net","port":14580,"kind":"APRS-IS","priority":0,"description":"Servidor APRS-IS no Brasil"},
  {"name":"APRS2 Rotate","address":"rotate.aprs2.net","port":14580,"kind":"APRS-IS","priority":1,"description":"Balanceamento global Tier 2"},
  {"name":"APRS2 América do Norte","address":"noam.aprs2.net","port":14580,"kind":"APRS-IS","priority":10,"description":"Pool América do Norte"},
  {"name":"APRS2 Europa","address":"euro.aprs2.net","port":14580,"kind":"APRS-IS","priority":10,"description":"Pool Europa"},
 ]
}

def clean(v,n=180):return str(v or "").strip()[:n]
def decorate(x):
    x=dict(x);kind=x.get("kind","")
    if kind=="BrandMeister":
        x.update(password_label="Hotspot Security",password_required=True,api_supported=True,essid_supported=True)
    elif kind=="XLX":
        x.setdefault("modules",AZ);x.setdefault("default_module","C");x.setdefault("default_password","passw0rd")
        x["module_supported"]=True;x["password_required"]=False
    elif kind=="DAPNET":
        x.setdefault("password_label","DAPNET AuthKey");x["password_required"]=True
    elif kind in ("TGIF","FreeDMR","DMR+","HBLink","DMR"):
        x.setdefault("essid_supported",True);x.setdefault("password_required",False)
    return x

def read_dmr():
    p=BASE/"DMR_Hosts.txt";out=[]
    if p.exists():
        for raw in p.read_text(errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#"):continue
            parts=line.split()
            if len(parts)<5:continue
            name,ident,address,password,port=parts[:5]
            try:port=int(port)
            except Exception:continue
            u=name.upper()
            kind="BrandMeister" if u.startswith("BM_") else "FreeDMR" if u.startswith(("FREEDMR_","FD_")) else "TGIF" if "TGIF" in u else "XLX" if u.startswith("XLX_") else "DMR+" if u.startswith("DMR+_") or "IPSC2" in u else "HBLink" if u.startswith("HB_") else "DMR"
            if name in ("DMRGateway","DMR2YSF","DMR2NXDN"):continue
            out.append(decorate({"name":name,"id":ident,"address":address,"port":port,"default_password":password,"kind":kind,"description":name.replace("_"," ")}))
    # XLX master list is authoritative for reflector completeness.
    p=BASE/"XLXHosts.txt"
    if p.exists():
        for raw in p.read_text(errors="ignore").splitlines():
            parts=raw.strip().split(";")
            if len(parts)<3 or raw.lstrip().startswith("#"):continue
            ident,address,room=map(str.strip,parts[:3])
            if not re.fullmatch(r"[0-9A-Z]{3}",ident):continue
            try:room_i=int(room)
            except Exception:room_i=4003
            module=chr(64+max(1,min(26,room_i-4000))) if 4001<=room_i<=4026 else "C"
            out.append(decorate({"name":"XLX"+ident,"id":ident,"address":address,"port":62030,"kind":"XLX","description":"XLX "+ident,"default_module":module,"modules":AZ,"default_tg":6,"default_password":"passw0rd"}))
    return out

def read_dstar():
    out=[]
    # Pinned upstream JSON is a local fallback included in the image. Runtime
    # Pi-Star text lists, when newer, are merged below and deduplicated.
    p=BASE/"DStar_Hosts.json"
    if p.exists():
        try:
            raw=json.loads(p.read_text(errors="ignore"))
            rows=raw.get("reflectors",raw if isinstance(raw,list) else [])
            for row in rows:
                if not isinstance(row,dict):continue
                name=clean(row.get("name")).upper()
                kind=clean(row.get("reflector_type") or row.get("type"))
                address=clean(row.get("ipv4") or row.get("host") or row.get("address"))
                if not name or not address:continue
                if kind in ("D-Plus","DPLUS"):kind="DPlus"
                if kind in ("D-Extra","DEXTRA"):kind="DExtra"
                if kind.upper()=="DCS":kind="DCS"
                if name.startswith("REF"):kind="DPlus"
                elif name.startswith("XRF"):kind="DExtra"
                elif name.startswith("DCS"):kind="DCS"
                elif name.startswith("XLX"):kind="XLX"
                if kind not in ("DPlus","DExtra","DCS","XLX"):continue
                port={"DPlus":20001,"DExtra":30001,"DCS":30051,"XLX":0}[kind]
                out.append({"name":name,"address":address,"port":port,"kind":kind,
                            "description":name,"modules":AZ,"default_module":"D" if name=="XLX026" else "A",
                            "module_supported":True})
        except Exception:
            pass
    for filename,kind,prefix in (("DPlus_Hosts.txt","DPlus","REF"),("DExtra_Hosts.txt","DExtra","XRF"),("DCS_Hosts.txt","DCS","DCS")):
        p=BASE/filename
        if not p.exists():continue
        for raw in p.read_text(errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#"):continue
            parts=line.replace(";"," ").split()
            if len(parts)<2:continue
            name,address=parts[:2]
            port={"DPlus":20001,"DExtra":30001,"DCS":30051}.get(kind,0)
            out.append({"name":name.upper(),"address":address,"port":port,"kind":kind,"description":f"{prefix} {name}","modules":AZ,"default_module":"C","module_supported":True})
    p=BASE/"XLXHosts.txt"
    if p.exists():
        for raw in p.read_text(errors="ignore").splitlines():
            parts=raw.strip().split(";")
            if len(parts)<2 or raw.lstrip().startswith("#"):continue
            ident,address=parts[0].strip(),parts[1].strip()
            if re.fullmatch(r"[0-9A-Z]{3}",ident):
                out.append({"name":"XLX"+ident,"id":ident,"address":address,"port":0,"kind":"XLX","description":"XLX "+ident+" (porta gerenciada pelo DStarGateway)","modules":AZ,"default_module":"D" if ident=="026" else "A","module_supported":True})
    return out

def read_ysf():
    out=[];p=BASE/"YSFHosts.txt"
    if p.exists():
        for raw in p.read_text(errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#"):continue
            parts=line.split(";")
            if len(parts)<5:continue
            try:port=int(parts[4])
            except Exception:continue
            out.append({"id":clean(parts[0]),"name":clean(parts[1]),"description":clean(parts[2]),"address":clean(parts[3]),"port":port,"kind":"YSF"})
    p=BASE/"FCSHosts.txt"
    if p.exists():
        for raw in p.read_text(errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#"):continue
            parts=line.replace(";"," ").split()
            if len(parts)>=2:out.append({"name":parts[0],"address":parts[1],"port":42001,"kind":"FCS","description":parts[0]})
    return out

def read_simple(filename,kind):
    out=[];p=BASE/filename
    if not p.exists():return out
    for raw in p.read_text(errors="ignore").splitlines():
        line=raw.strip()
        if not line or line.startswith("#"):continue
        parts=line.replace(";"," ").split()
        if len(parts)<3:continue
        name,address,port_s=parts[:3]
        try:port=int(port_s)
        except Exception:continue
        ident=(re.search(r"\d{2,7}",name) or re.search(r"\d{2,7}",line))
        out.append({"name":name,"id":ident.group(0) if ident else "","address":address,"port":port,"kind":kind,"description":name.replace("_"," ")})
    return out

def dedupe(proto,items):
    result=[];seen=set()
    for x in [*SEED.get(proto,[]),*items]:
        x=decorate(x)
        key=(x.get("kind"),x.get("name"),x.get("address"),x.get("port"))
        if key in seen:continue
        seen.add(key);result.append(x)
    result.sort(key=lambda x:(int(x.get("priority",50)),str(x.get("kind","")),str(x.get("name","")).lower()))
    return result

def main():
    proto=(sys.argv[1] if len(sys.argv)>1 else "DMR").upper().replace("-","")
    query=(sys.argv[2] if len(sys.argv)>2 else "").lower().strip()
    if proto=="DMR":items=read_dmr()
    elif proto=="DSTAR":items=read_dstar()
    elif proto=="YSF":items=read_ysf()
    elif proto=="P25":items=read_simple("P25Hosts.txt","P25")
    elif proto=="NXDN":items=read_simple("NXDNHosts.txt","NXDN")
    elif proto=="POCSAG":items=[]
    elif proto=="APRS":items=[]
    else:items=[]
    items=dedupe(proto,items)
    total=len(items)
    if query:items=[x for x in items if query in " ".join(str(v) for v in x.values()).lower()]
    families=sorted({str(x.get("kind") or proto) for x in items})
    print(json.dumps({"protocol":proto,"servers":items,"total":total,"matched":len(items),"families":families,
                      "cache_updated":(BASE/".updated").exists()},ensure_ascii=False))
if __name__=="__main__":main()
