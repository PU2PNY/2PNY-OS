#!/usr/bin/env python3
"""PU2PNY display detector 0.3.9.

Non-destructive display discovery. It never flashes firmware, never changes RF,
and never steals the MMDVM serial port while MMDVMHost is active.
"""
from __future__ import annotations
import fcntl, glob, json, os, re, subprocess, termios, time
from pathlib import Path
from typing import Any, Dict, List, Optional

STATE=Path("/var/lib/2pny");RUN=Path("/run/2pny")
OUT=STATE/"display-detection.json";STATUS=RUN/"display-detect-status.json"
HARDWARE=STATE/"hardware-probe.json";CATALOG=Path("/usr/share/2pny/display-catalog.json")
LOCK=RUN/"display-detect.lock"
NEXTION_BAUDS=(9600,115200);OLED_ADDRS={"0x3c","0x3d"};LCD_ADDRS={"0x27","0x3f"}
RESOLUTION_CODES={"3224":(320,240),"4024":(400,240),"4832":(480,320),"4827":(480,272),"8048":(800,480),"1060":(1024,600)}
SIZE_CODES={"024":"2.4","028":"2.8","032":"3.2","035":"3.5","043":"4.3","050":"5.0","070":"7.0","101":"10.1"}

def read_text(path):
    try:return Path(path).read_text(errors="ignore").replace("\x00","").strip()
    except Exception:return ""

def read_json(path):
    try:
        obj=json.loads(Path(path).read_text());return obj if isinstance(obj,dict) else {}
    except Exception:return {}

def atomic_json(path,obj,mode=0o644):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name("."+path.name+".tmp")
    with tmp.open("w") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
    os.chmod(tmp,mode);os.replace(tmp,path)

def publish(state,message,**extra):
    obj={"state":state,"message":message,"updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())};obj.update(extra);atomic_json(STATUS,obj)

def service_active(unit):
    return subprocess.run(["systemctl","is-active","--quiet",unit],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def serial_candidates():
    patterns=["/dev/serial/by-id/*","/dev/ttyUSB*","/dev/ttyACM*","/dev/serial0","/dev/ttyAMA0"]
    out=[];seen=set()
    for pattern in patterns:
        for raw in sorted(glob.glob(pattern)):
            real=os.path.realpath(raw)
            if real in seen or not os.path.exists(raw):continue
            seen.add(real);out.append({"path":raw,"realpath":real})
    return out

def speed_const(baud):return {9600:termios.B9600,115200:termios.B115200}[baud]

def open_serial(path,baud):
    fd=os.open(path,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK);a=termios.tcgetattr(fd)
    a[0]=0;a[1]=0;a[2]=termios.CS8|termios.CREAD|termios.CLOCAL;a[3]=0;sp=speed_const(baud);a[4]=sp;a[5]=sp
    a[6][termios.VMIN]=0;a[6][termios.VTIME]=1;termios.tcsetattr(fd,termios.TCSANOW,a);termios.tcflush(fd,termios.TCIOFLUSH);return fd

def read_for(fd,seconds):
    end=time.monotonic()+seconds;out=bytearray()
    while time.monotonic()<end:
        try:
            b=os.read(fd,1024)
            if b:out.extend(b)
        except BlockingIOError:pass
        except OSError:break
        time.sleep(.02)
    return bytes(out)

def nextion_command(fd,command,wait=.55):
    os.write(fd,command.encode("ascii","replace")+b"\xff\xff\xff");return read_for(fd,wait)

def nextion_dimensions(model):
    upper=str(model or "").upper();res={}
    m=re.search(r"(?:NX|TJC|ONX)(3224|4024|4832|4827|8048|1060)",upper)
    if m and m.group(1) in RESOLUTION_CODES:
        w,h=RESOLUTION_CODES[m.group(1)];res.update({"width":w,"height":h,"resolution":f"{w}x{h}"})
    size=re.search(r"(?:T|K|P|F|G)(024|028|032|035|043|050|070|101)(?:_|$)",upper)
    if size and size.group(1) in SIZE_CODES:res["size_inch"]=SIZE_CODES[size.group(1)]
    return res

def parse_connect(raw):
    text=raw.replace(b"\xff",b"").decode("ascii","replace").strip("\x00\r\n ");idx=text.lower().find("comok")
    if idx<0:return None
    text=text[idx:];parts=[p.strip() for p in text.split(",")];model=""
    for part in parts:
        if re.match(r"^(NX|TJC|ONX)[A-Za-z0-9_\-]+$",part,re.I):model=part;break
    if not model and len(parts)>=3:model=parts[2]
    info={"response":text[:240],"model":model or "Nextion","confidence":"protocol"};info.update(nextion_dimensions(model));return info

def parse_nextion_string(raw):
    idx=raw.find(b"\x70")
    if idx<0:return None
    end=raw.find(b"\xff\xff\xff",idx+1)
    if end<0:return None
    return raw[idx+1:end].decode("utf-8","replace").strip()

def probe_2pny_hmi_marker(fd):
    value=parse_nextion_string(nextion_command(fd,"get pnyver.txt",.4))
    return {"hmi_status":"pu2pny","hmi_version":value} if value else {"hmi_status":"unknown","hmi_version":None}

def probe_nextion_direct(path):
    for baud in NEXTION_BAUDS:
        try:fd=open_serial(path,baud)
        except Exception:continue
        try:
            info=parse_connect(nextion_command(fd,"connect",.7))
            if not info:continue
            info.update(probe_2pny_hmi_marker(fd));info.update({"detected":True,"class":"nextion","transport":"uart","port":path,"baud":baud,"state":"identified"});return info
        except Exception:pass
        finally:
            try:os.close(fd)
            except Exception:pass
    return None

def modem_realpath():
    hw=read_json(HARDWARE);m=hw.get("mmdvm") if isinstance(hw.get("mmdvm"),dict) else {};port=str((m or {}).get("port") or "")
    return os.path.realpath(port) if port else ""


def probe_nextion_mmdvm_bridge():
    """Probe a modem-attached Nextion without opening the protected UART."""
    if not service_active("2pny-mmdvmhost.service"):
        return None
    sub=None
    try:
        subprocess.run(["systemctl","start","mosquitto.service"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
        sub=subprocess.Popen(["mosquitto_sub","-h","127.0.0.1","-t","host/display-out","-C","1","-W","3","-N"],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        time.sleep(.15)
        pub=subprocess.run(["mosquitto_pub","-h","127.0.0.1","-t","host/display-in","-s"],
                           input=b"connect\xff\xff\xff",stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=4)
        if pub.returncode:
            return None
        out,_=sub.communicate(timeout=4)
        info=parse_connect(out or b"")
        if not info:
            return None
        info.update({"detected":True,"class":"nextion_mmdvm","transport":"mmdvm-mqtt",
                     "port":"modem","baud":None,"state":"identified","confidence":"protocol",
                     "physical_confirmed":True,"hmi_status":"unknown","hmi_version":None})
        return info
    except Exception:
        try:
            if sub is not None:
                sub.kill()
        except Exception:
            pass
        return None

def confirmed_mmdvm_nextion():
    hw=read_json(HARDWARE);d=hw.get("display") if isinstance(hw.get("display"),dict) else {}
    if not d or d.get("class")!="nextion_mmdvm" or d.get("detected") is not True or d.get("confidence") not in ("protocol","manual"):return None
    # A previous manual selection is a candidate, never a fresh COMOK reply.
    info={"detected":False,"class":"nextion_mmdvm","transport":"mmdvm","state":"candidate","port":"modem","model":d.get("model") or "Nextion via MMDVM","confidence":"previous_configuration","physical_confirmed":False,"hmi_status":"unknown","hmi_version":None}
    info.update(nextion_dimensions(str(info["model"])));return info

def usb_devices():
    found=[]
    for base in sorted(Path("/sys/bus/usb/devices").glob("*")):
        vid=read_text(base/"idVendor");pid=read_text(base/"idProduct")
        if not vid or not pid:continue
        found.append({"vendor_id":vid,"product_id":pid,"manufacturer":read_text(base/"manufacturer"),"product":read_text(base/"product"),"serial":read_text(base/"serial")})
    return found

def i2c_devices():
    found=[]
    for path in sorted(Path("/sys/bus/i2c/devices").glob("*-*")):
        m=re.match(r"^(\d+)-([0-9a-fA-F]{4})$",path.name)
        if not m:continue
        compatible=read_text(path/"of_node"/"compatible") if (path/"of_node"/"compatible").exists() else ""
        found.append({"bus":int(m.group(1)),"address":"0x"+m.group(2)[-2:].lower(),"name":read_text(path/"name"),"compatible":compatible})
    return found

def oled_candidates(i2c):
    out=[]
    for item in i2c:
        addr=str(item.get("address") or "").lower()
        if addr not in OLED_ADDRS:continue
        meta=(str(item.get("name") or "")+" "+str(item.get("compatible") or "")).lower();driver=""
        if "sh1106" in meta:driver="sh1106"
        elif "ssd1306" in meta:driver="ssd1306"
        out.append({"detected":bool(driver),"class":"oled","state":"identified" if driver else "candidate","transport":"i2c","bus":item.get("bus"),"address":addr,"driver":driver or "ssd1306_or_sh1106","model":driver.upper() if driver else "OLED 128x64 candidato","width":128,"height":64,"resolution":"128x64","confidence":"kernel" if driver else "address_candidate","message":"Controlador confirmado por metadata do kernel." if driver else "0x3C/0x3D não distingue sozinho SSD1306 de SH1106."})
    return out

def lcd_candidates(i2c):
    out=[]
    for item in i2c:
        addr=str(item.get("address") or "").lower()
        if addr in LCD_ADDRS:out.append({"detected":False,"class":"lcd_i2c_candidate","state":"candidate","transport":"i2c","bus":item.get("bus"),"address":addr,"model":"HD44780/PCF8574 candidato","confidence":"address_candidate"})
    return out

def spi_devices():
    out=[]
    for base in sorted(Path("/sys/bus/spi/devices").glob("spi*")):
        out.append({"device":base.name,"model":read_text(base/"modalias") or read_text(base/"name") or base.name})
    return out

def generic_video_and_touch():
    displays=[];touch=[]
    for dev in sorted(Path("/sys/class/input").glob("event*")):
        name=read_text(dev/"device"/"name");low=name.lower()
        if name and any(w in low for w in ("touch","touchscreen","digitizer")):touch.append(name)
    for status in sorted(Path("/sys/class/drm").glob("card*-*/status")):
        if read_text(status).lower()!="connected":continue
        displays.append({"detected":True,"class":"generic_video_display","state":"identified","transport":"drm","model":status.parent.name,"touch":bool(touch),"touch_devices":touch,"confidence":"kernel","message":"Display genérico detectado – layout básico; renderer touch completo é fase posterior."})
    return displays

def catalog_match(device):
    catalog=read_json(CATALOG);profiles=catalog.get("profiles") if isinstance(catalog.get("profiles"),list) else [];model=str(device.get("model") or "")
    for profile in profiles:
        if not isinstance(profile,dict):continue
        pattern=str(profile.get("model_regex") or "")
        if pattern:
            try:
                if re.search(pattern,model,re.I):return profile
            except re.error:continue
        if device.get("resolution") and profile.get("resolution")==device.get("resolution"):return profile
    return {}

def main():
    RUN.mkdir(parents=True,exist_ok=True);STATE.mkdir(parents=True,exist_ok=True)
    with LOCK.open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);publish("detecting","Detectando displays conectados…")
        radio_active=service_active("2pny-mmdvmhost.service");modem=modem_realpath();serial=serial_candidates();usb=usb_devices();i2c=i2c_devices();spi=spi_devices();results=[]
        publish("detecting","Verificando USB e UART…")
        bridge=probe_nextion_mmdvm_bridge() if radio_active else None
        if not bridge:bridge=confirmed_mmdvm_nextion()
        if bridge:results.append(bridge)
        for item in serial:
            if modem and item["realpath"]==modem:continue
            found=probe_nextion_direct(item["path"])
            if found:results.append(found);break
        publish("detecting","Verificando I2C…");results.extend(oled_candidates(i2c));results.extend(lcd_candidates(i2c))
        publish("detecting","Verificando SPI e saídas de vídeo…")
        for item in spi:
            low=str(item.get("model") or "").lower()
            if any(w in low for w in ("ssd13","sh110","st77","ili9","gc9a","tft","oled","lcd")):results.append({"detected":True,"class":"spi_display","state":"identified","transport":"spi","model":item.get("model"),"device":item.get("device"),"confidence":"kernel"})
        results.extend(generic_video_and_touch())
        for device in results:
            match=catalog_match(device)
            if not match:continue
            device["catalog_profile"]=match.get("id");asset=match.get("tft") if isinstance(match.get("tft"),dict) else {}
            device["recommended_hmi"]={"version":asset.get("version"),"filename":asset.get("filename"),"sha256":asset.get("sha256"),"url":asset.get("url"),"status":asset.get("status") or "unpublished"}
            if str(device.get("class") or "").startswith("nextion"):
                current=device.get("hmi_version");recommended=asset.get("version")
                if current and recommended and current==recommended:device["provisioning"]="up_to_date"
                elif asset.get("sha256") and asset.get("url"):device["provisioning"]="confirmation_required"
                else:device["provisioning"]="asset_unpublished"
        confirmed=[x for x in results if x.get("detected") is True];candidates=[x for x in results if x.get("detected") is not True]
        payload={"state":"ready","radio_engine_active":radio_active,"mmdvm_port_protected":bool(radio_active and modem),"usb":usb,"serial":serial,"i2c":i2c,"spi":spi,"displays":results,"confirmed_count":len(confirmed),"candidate_count":len(candidates),"updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
        atomic_json(OUT,payload);publish("ready",f"Detecção concluída: {len(confirmed)} confirmado(s), {len(candidates)} candidato(s).",confirmed=len(confirmed),candidates=len(candidates));print(json.dumps(payload,ensure_ascii=False));return 0

if __name__=="__main__":raise SystemExit(main())
