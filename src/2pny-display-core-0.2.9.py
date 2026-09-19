#!/usr/bin/env python3
"""PU2PNY Display Core 0.2.9.

Adaptive local renderer for Nextion (direct or through MMDVM MQTT bridge),
SSD1306/SH1106 OLED and HD44780/PCF8574 LCD.  It never owns RF settings and
never reads radio logs: all live information comes from PU2PNY snapshots.
"""
import json, os, re, subprocess, termios, time
from pathlib import Path

STATE=Path("/var/lib/2pny")
RUN=Path("/run/2pny")
HW=STATE/"hardware-probe.json"
CFG=STATE/"config.json"
LIVE=RUN/"live-state.json"
TELEM=RUN/"telemetry.json"
STATUS=STATE/"display-runtime.json"
SETTINGS=STATE/"display-settings.json"

BLACK=0; WHITE=65535; CYAN=2047; GREEN=2016; RED=63488; YELLOW=65504; GRAY=33808; BLUE=31
END=b"\xff\xff\xff"

def read_json(path, default=None):
    try:return json.loads(Path(path).read_text())
    except Exception:return {} if default is None else default

def write_status(**kw):
    kw["updated"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    STATUS.parent.mkdir(parents=True,exist_ok=True)
    tmp=STATUS.with_suffix(".tmp");tmp.write_text(json.dumps(kw,ensure_ascii=False));os.chmod(tmp,0o644);os.replace(tmp,STATUS)

def safe(s,n=34):
    return str(s or "").replace("\\","/").replace('"',"'").replace("\r"," ").replace("\n"," ")[:n]

def baud_flag(baud):
    return {9600:termios.B9600,19200:termios.B19200,38400:termios.B38400,57600:termios.B57600,115200:termios.B115200}.get(baud,termios.B9600)

class Nextion:
    def __init__(self, integration, port="", baud=9600, width=320, height=240):
        self.integration=integration;self.port=port;self.baud=baud;self.w=width;self.h=height;self.fd=None
    def open(self):
        if self.integration=="nextion_mmdvm":
            return True
        self.fd=os.open(self.port,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
        attrs=termios.tcgetattr(self.fd);attrs[0]=attrs[1]=attrs[3]=0;attrs[2]=termios.CS8|termios.CREAD|termios.CLOCAL
        attrs[4]=attrs[5]=baud_flag(self.baud);attrs[6][termios.VMIN]=0;attrs[6][termios.VTIME]=2
        termios.tcsetattr(self.fd,termios.TCSANOW,attrs)
        return True
    def close(self):
        if self.fd is not None:
            try:os.close(self.fd)
            except Exception:pass
            self.fd=None
    def send(self, commands):
        payload=b"".join(str(c).encode("ascii","replace")+END for c in commands)
        if self.integration=="nextion_mmdvm":
            p=subprocess.run(["mosquitto_pub","-h","127.0.0.1","-t","host/display-in","-s"],
                             input=payload,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2)
            if p.returncode:raise RuntimeError("MQTT display bridge unavailable")
        else:
            if self.fd is None:self.open()
            os.write(self.fd,payload)
    def text(self,x,y,w,h,text,color=WHITE,font=0,align=0):
        return f'xstr {x},{y},{w},{h},{font},{color},{BLACK},{align},1,1,"{safe(text,50)}"'
    def flag(self,cc,x,y):
        cc=(cc or "").upper()
        cmds=[f"draw {x},{y},{x+43},{y+27},{GRAY}"]
        if cc=="BR":
            cmds += [f"fill {x+1},{y+1},42,26,{GREEN}",
                     f"line {x+5},{y+14},{x+21},{y+4},{YELLOW}",f"line {x+21},{y+4},{x+38},{y+14},{YELLOW}",
                     f"line {x+38},{y+14},{x+21},{y+24},{YELLOW}",f"line {x+21},{y+24},{x+5},{y+14},{YELLOW}",
                     f"cir {x+21},{y+14},6,{BLUE}"]
        elif cc=="US":
            cmds += [f"fill {x+1},{y+1},42,26,{WHITE}",f"fill {x+1},{y+1},18,13,{BLUE}"]
            for yy in range(y+2,y+26,4):cmds.append(f"line {x+1},{yy},{x+42},{yy},{RED}")
        elif cc=="GB":
            cmds += [f"fill {x+1},{y+1},42,26,{BLUE}",f"fill {x+19},{y+1},6,26,{WHITE}",f"fill {x+1},{y+11},42,6,{WHITE}",
                     f"fill {x+21},{y+1},2,26,{RED}",f"fill {x+1},{y+13},42,2,{RED}"]
        elif cc:
            cmds += [self.text(x+1,y+3,42,20,cc,WHITE,0,1)]
        return cmds
    def render(self,live,cfg,tel):
        a=live.get("active") or {}
        proto=str(a.get("protocol") or cfg.get("protocol") or "PU2PNY").replace("DSTAR","D-STAR")
        mode=a.get("mode") or "standby"
        color=GREEN if mode=="tx" else RED if mode=="rx" else CYAN
        title="TX" if mode=="tx" else "RX" if mode=="rx" else "STANDBY"
        source=safe(a.get("source") or cfg.get("callsign") or "PU2PNY",18)
        op=a.get("operator") or {}
        target=safe(a.get("target") or "",20)
        rx=float(cfg.get("rx_hz") or 0)/1e6;tx=float(cfg.get("tx_hz") or 0)/1e6
        cpu=(tel.get("cpu_percent") if isinstance(tel,dict) else None);temp=tel.get("temperature") if isinstance(tel,dict) else None
        internet=live.get("internet") or {};qual=internet.get("quality") or "unknown"
        lat=internet.get("latency_ms");loss=internet.get("loss_percent")
        w,h=self.w,self.h
        if w<=330:
            cmds=["cls 0",f"fill 0,0,{w},34,{color}",self.text(4,4,w-8,26,f"PU2PNY  {title}  {proto}",BLACK if mode!="standby" else WHITE,0,0)]
            cmds += self.flag(op.get("country_code"),w-49,40)
            cmds += [self.text(8,42,w-64,31,source,WHITE,0,0),
                     self.text(8,75,w-16,26,(op.get("name") or target or "Pronto / Ready"),CYAN,0,0),
                     self.text(8,105,w-16,24,f"RX {rx:.5f}  TX {tx:.5f}",WHITE,0,0),
                     self.text(8,132,w-16,24,f"{target}  BER {a.get('ber','-')}  RSSI {a.get('rssi_avg',a.get('rssi','-'))}",WHITE,0,0),
                     self.text(8,160,w-16,24,f"CPU {cpu if cpu is not None else '-'}%  {temp if temp is not None else '-'}C",WHITE,0,0),
                     self.text(8,188,w-16,24,f"NET {qual}  {lat if lat is not None else '-'}ms  PER {loss if loss is not None else '-'}%",RED if qual in ("poor","offline") else GREEN,0,0)]
        else:
            cmds=["cls 0",f"fill 0,0,{w},42,{color}",self.text(12,7,w-24,28,f"PU2PNY-OS   {title}   {proto}",BLACK if mode!="standby" else WHITE,0,0)]
            cmds += self.flag(op.get("country_code"),w-62,54)
            cmds += [self.text(18,58,w-92,42,source,WHITE,0,0),
                     self.text(18,102,w-36,30,op.get("name") or target or "Hotspot pronto / Ready",CYAN,0,0),
                     self.text(18,140,w-36,26,f"Destino {target or '-'}",WHITE,0,0),
                     self.text(18,172,w-36,26,f"RX {rx:.6f} MHz     TX {tx:.6f} MHz",WHITE,0,0),
                     self.text(18,204,w-36,26,f"BER {a.get('ber','-')}%   RSSI {a.get('rssi_avg',a.get('rssi','-'))} dBm",WHITE,0,0),
                     self.text(18,h-54,w-36,22,f"CPU {cpu if cpu is not None else '-'}%  TEMP {temp if temp is not None else '-'}C",WHITE,0,0),
                     self.text(18,h-30,w-36,22,f"NET {qual} LAT {lat if lat is not None else '-'}ms PER {loss if loss is not None else '-'}%",RED if qual in ("poor","offline") else GREEN,0,0)]
        self.send(cmds)

class I2CBase:
    def __init__(self,bus=1,address=0x3c):
        import smbus
        self.bus=smbus.SMBus(bus);self.addr=address
    def close(self):
        try:self.bus.close()
        except Exception:pass

class OLED(I2CBase):
    def __init__(self,bus=1,address=0x3c,sh1106=False):
        super().__init__(bus,address);self.sh1106=sh1106
        from PIL import Image,ImageDraw,ImageFont
        self.Image=Image;self.ImageDraw=ImageDraw;self.font=ImageFont.load_default()
        self.cmd(0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0x00,0x40,0x8D,0x14,0x20,0x00,0xA1,0xC8,0xDA,0x12,0x81,0xCF,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0xAF)
    def cmd(self,*vals):
        for v in vals:self.bus.write_byte_data(self.addr,0x00,v)
    def show(self,lines):
        img=self.Image.new("1",(128,64));d=self.ImageDraw.Draw(img)
        for i,line in enumerate(lines[:6]):d.text((0,i*10),safe(line,22),font=self.font,fill=255)
        pix=img.load()
        for page in range(8):
            if self.sh1106:self.cmd(0xB0+page,0x02,0x10)
            else:self.cmd(0xB0+page,0x00,0x10)
            data=[]
            for x in range(128):
                byte=0
                for bit in range(8):
                    if pix[x,page*8+bit]:byte|=1<<bit
                data.append(byte)
            for off in range(0,128,16):
                self.bus.write_i2c_block_data(self.addr,0x40,data[off:off+16])
    def render(self,live,cfg,tel):
        a=live.get("active") or {};mode=a.get("mode") or "standby";proto=a.get("protocol") or cfg.get("protocol") or "-"
        rx=float(cfg.get("rx_hz") or 0)/1e6;tx=float(cfg.get("tx_hz") or 0)/1e6
        if mode=="standby":
            lines=[f"PU2PNY {proto} READY",f"RX {rx:.5f}",f"TX {tx:.5f}",f"CPU {tel.get('cpu_percent','-')}% {tel.get('temperature','-')}C",f"NET {(live.get('internet') or {}).get('quality','-')}"]
        else:
            lines=[f"{mode.upper()} {proto}",a.get("source") or "-",a.get("target") or "-",f"BER {a.get('ber','-')} RSSI {a.get('rssi_avg',a.get('rssi','-'))}",f"CPU {tel.get('cpu_percent','-')}% {tel.get('temperature','-')}C"]
        self.show(lines)

class LCD(I2CBase):
    def __init__(self,bus=1,address=0x27,cols=20,rows=4):
        super().__init__(bus,address);self.cols=cols;self.rows=rows;self.bl=0x08
        time.sleep(.05)
        for n in (0x30,0x30,0x30,0x20):self._nibble(n);time.sleep(.002)
        for cmd in (0x28,0x08,0x01,0x06,0x0C):self.command(cmd)
    def _nibble(self,n):
        self.bus.write_byte(self.addr,(n&0xF0)|self.bl|0x04);self.bus.write_byte(self.addr,(n&0xF0)|self.bl)
    def command(self,n):self._nibble(n);self._nibble(n<<4)
    def data(self,n):
        self.bus.write_byte(self.addr,(n&0xF0)|self.bl|0x05);self.bus.write_byte(self.addr,(n&0xF0)|self.bl|0x01)
        self.bus.write_byte(self.addr,((n<<4)&0xF0)|self.bl|0x05);self.bus.write_byte(self.addr,((n<<4)&0xF0)|self.bl|0x01)
    def show(self,lines):
        addrs=[0x00,0x40,0x14,0x54] if self.cols>=20 else [0x00,0x40]
        for row in range(self.rows):
            self.command(0x80+addrs[row]);txt=safe(lines[row] if row<len(lines) else "",self.cols).ljust(self.cols)
            for ch in txt:self.data(ord(ch) if ord(ch)<128 else ord("?"))
    def render(self,live,cfg,tel):
        a=live.get("active") or {};mode=a.get("mode") or "standby";proto=a.get("protocol") or cfg.get("protocol") or "-"
        if self.rows>=4:
            if mode=="standby":
                lines=[f"PU2PNY {proto} PRONTO",f"RX {float(cfg.get('rx_hz') or 0)/1e6:.5f}",f"TX {float(cfg.get('tx_hz') or 0)/1e6:.5f}",f"CPU {tel.get('cpu_percent','-')}% {tel.get('temperature','-')}C"]
            else:
                lines=[f"{mode.upper()} {proto} {a.get('source','-')}",a.get("target") or "-",f"BER {a.get('ber','-')} R {a.get('rssi_avg',a.get('rssi','-'))}",f"CPU {tel.get('cpu_percent','-')}% {tel.get('temperature','-')}C"]
        else:
            lines=[f"{mode.upper()} {proto} {a.get('source') or 'PU2PNY'}",a.get("target") or f"CPU {tel.get('cpu_percent','-')}%"]
        self.show(lines)

def nextion_size(model):
    m=str(model or "").upper()
    if "8048" in m:return 800,480
    if "4832" in m:return 480,320
    if "4827" in m:return 480,272
    if "4024" in m:return 400,240
    return 320,240

def create_driver(hw):
    d=hw.get("display") or {};cls=str(d.get("class") or "");state=str(d.get("state") or "")
    settings=read_json(SETTINGS)
    if settings.get("enabled") is False:return None,"disabled"
    if cls in ("nextion","nextion_mmdvm") or state=="mmdvm_display_candidate":
        integration="nextion_mmdvm" if cls=="nextion_mmdvm" or state=="mmdvm_display_candidate" else "nextion"
        w,h=nextion_size(d.get("model"))
        return Nextion(integration,str(d.get("port") or ""),int(d.get("baud") or 9600),w,h),integration
    addr=d.get("address")
    if isinstance(addr,str):
        try:addr=int(addr,16)
        except Exception:addr=None
    if addr in (0x3c,0x3d):
        model=str(d.get("model") or "").lower()
        return OLED(1,addr,"sh1106" in model),"oled"
    if addr in (0x27,0x3f):
        cols=int(settings.get("lcd_cols") or 20);rows=int(settings.get("lcd_rows") or 4)
        return LCD(1,addr,cols,rows),"lcd"
    return None,"unsupported"

def main():
    driver=None;kind="";last_sig=None;last_hw=0;failures=0
    while True:
        try:
            now=time.time()
            if driver is None or now-last_hw>30:
                hw=read_json(HW);last_hw=now
                if driver is None:
                    driver,kind=create_driver(hw)
                    if driver:
                        if hasattr(driver,"open"):driver.open()
                        # Own PU2PNY renderer is authoritative; avoid competing commands.
                        subprocess.run(["systemctl","stop","2pny-display.service"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                        write_status(state="active",active=True,type=kind,driver="pu2pny-display-core",message="PU2PNY display ativo")
            live=read_json(LIVE,{"standby":True});cfg=read_json(CFG);tel=read_json(TELEM)
            active=live.get("active") or {}
            sig=(live.get("sequence"),active.get("source"),active.get("target"),active.get("mode"),
                 tel.get("cpu_percent"),tel.get("temperature"),(live.get("internet") or {}).get("quality"))
            if driver and sig!=last_sig:
                driver.render(live,cfg,tel);last_sig=sig;failures=0
            elif not driver:
                write_status(state="not_configured",active=False,type=kind,message="Nenhum display suportado detectado")
            time.sleep(.35 if active else 1.5)
        except KeyboardInterrupt:break
        except Exception as exc:
            failures+=1;write_status(state="warning",active=False,type=kind,message=type(exc).__name__)
            if driver and failures>=3:
                try:driver.close()
                except Exception:pass
                driver=None;last_sig=None
            time.sleep(min(15,2*failures))
    if driver:
        try:driver.close()
        except Exception:pass

if __name__=="__main__":main()
