#!/usr/bin/env python3
"""PU2PNY Display Core 0.3.21 — Moderno V2.

Adaptive local renderer for Nextion (direct or through MMDVM MQTT bridge),
SSD1306/SH1106 OLED and HD44780/PCF8574 LCD.  It never owns RF settings and
never reads radio logs: all live information comes from PU2PNY snapshots.
"""
import datetime, json, os, re, subprocess, termios, time, unicodedata
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

STATE=Path("/var/lib/2pny")
RUN=Path("/run/2pny")
NETWORK=RUN/"network-status.txt"
HW=STATE/"hardware-probe.json"
CFG=STATE/"config.json"
LIVE=RUN/"live-state.json"
TELEM=RUN/"telemetry.json"
STATUS=STATE/"display-runtime.json"
SETTINGS=STATE/"display-settings.json"
LANGUAGE=STATE/"language"

BLACK=0; WHITE=65535; CYAN=2047; GREEN=2016; RED=63488; YELLOW=65504; GRAY=33808; BLUE=31
END=b"\xff\xff\xff"
MODERN_V2="PU2PNY Moderno V2"

def read_json(path, default=None):
    try:return json.loads(Path(path).read_text())
    except Exception:return {} if default is None else default

def write_status(**kw):
    kw["updated"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    STATUS.parent.mkdir(parents=True,exist_ok=True)
    tmp=STATUS.with_suffix(".tmp");tmp.write_text(json.dumps(kw,ensure_ascii=False));os.chmod(tmp,0o644);os.replace(tmp,STATUS)

def safe(s,n=34):
    return str(s or "").replace("\\","/").replace('"',"'").replace("\r"," ").replace("\n"," ")[:n]

def selected_language():
    try:
        v=LANGUAGE.read_text().strip().lower()
        return v if v in ("pt","en","es") else "pt"
    except Exception:return "pt"

def tr(pt,en,es):
    return {"pt":pt,"en":en,"es":es}.get(selected_language(),pt)

def display_hm():
    # SYS-004: UTC/system time stays NTP-correct. Optional manual DST is a
    # presentation-only +1h override so logs/protocol timestamps are untouched.
    clock=read_json(STATE/"settings/clock.json")
    zone=str(clock.get("timezone") or "").strip()
    try:
        now=datetime.datetime.now(ZoneInfo(zone)) if zone else datetime.datetime.now().astimezone()
    except (ZoneInfoNotFoundError, ValueError):
        now=datetime.datetime.now().astimezone()
    # A Raspberry Pi without an RTC can boot with an invalid epoch before
    # network time arrives. Do not present that date as a valid clock.
    if now.year<2024:return "--:--"
    if bool(clock.get("dst_manual")):now+=datetime.timedelta(hours=1)
    return now.strftime("%H:%M")

def read_network_status():
    out={}
    try:
        for raw in NETWORK.read_text(errors="ignore").splitlines():
            if "=" in raw:
                k,v=raw.split("=",1);out[k.strip()]=v.strip()
    except Exception:pass
    return out

def baud_flag(baud):
    return {9600:termios.B9600,19200:termios.B19200,38400:termios.B38400,57600:termios.B57600,115200:termios.B115200}.get(baud,termios.B9600)

class Nextion:
    def __init__(self, integration, port="", baud=9600, width=320, height=240):
        self.integration=integration;self.port=port;self.baud=baud;self.w=width;self.h=height;self.fd=None;self.first_render=True;self.last_page=None
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
        frames=[str(c).encode("ascii","replace")+END for c in commands]
        if self.integration=="nextion_mmdvm":
            # MMDVMHost has a single 252-byte immediate serial write; larger
            # messages use a shared delayed buffer. A second MQTT update can
            # replace that buffer while the first frame is still draining.
            # Send bounded complete commands in order and pace the modem UART.
            chunks=[];chunk=bytearray()
            for frame in frames:
                if len(frame)>240:raise ValueError("Nextion command exceeds modem frame")
                if len(chunk)+len(frame)>240:
                    chunks.append(bytes(chunk));chunk.clear()
                chunk.extend(frame)
            if chunk:chunks.append(bytes(chunk))
            for payload in chunks:
                p=subprocess.run(["mosquitto_pub","-h","127.0.0.1","-t","host/display-in","-s"],
                                 input=payload,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2)
                if p.returncode:raise RuntimeError("MQTT display bridge unavailable")
                time.sleep(len(payload)*10/max(9600,self.baud)+.04)
        else:
            if self.fd is None:self.open()
            for frame in frames:
                view=memoryview(frame)
                while view:
                    try:n=os.write(self.fd,view)
                    except BlockingIOError:
                        time.sleep(.01);continue
                    view=view[n:]
    def text(self,x,y,w,h,text,color=WHITE,font=0,align=0,bg=BLACK):
        # A stock Nextion font is not guaranteed to contain UTF-8 glyphs.
        # Transliterate instead of sending '?' for accented labels/dashes.
        plain=unicodedata.normalize("NFKD",safe(text,50).replace("—","-").replace("–","-").replace("·","|").replace("…","..."))
        plain=plain.encode("ascii","ignore").decode("ascii")
        return f'xstr {x},{y},{w},{h},{font},{color},{bg},{align},1,1,"{plain}"'
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
    def splash(self, pct=0, status=None):
        w,h=self.w,self.h;y=max(120,h//2+34);barw=max(80,w-60)
        pct=max(0,min(100,int(pct)))
        status=status or tr("Inicializando","Starting","Iniciando")
        fill=int((barw-4)*pct/100)
        commands=["cls 0",f"fill 0,0,{w},{h},{BLACK}",self.text(0,max(28,h//3-24),w,44,"PU2PNY-OS",CYAN,0,1),
                  self.text(0,max(76,h//3+24),w,28,status,WHITE,0,1),f"draw 30,{y},{30+barw},{y+18},{GRAY}",
                  self.text(0,y+24,w,24,f"{pct}%",WHITE,0,1)]
        if fill:commands.append(f"fill 32,{y+2},{fill},14,{GREEN}")
        self.send(commands)
        self.first_render=False;self.last_page=("splash","")

    def render(self,live,cfg,tel):
        a=live.get("active") or {}
        proto=str(a.get("protocol") or cfg.get("protocol") or "PU2PNY").replace("DSTAR","D-STAR")
        mode=a.get("mode") or "standby"
        direction=str(a.get("direction") or "").upper()
        title="TX" if mode=="tx" else "RX" if mode=="rx" else "STANDBY"
        header=RED if mode=="tx" else GREEN if mode=="rx" else CYAN
        own=safe(cfg.get("callsign") or "PU2PNY",12)
        source=safe(a.get("source") or own,18)
        op=a.get("operator") or {}
        target=safe(a.get("target") or "",20)
        rx=float(cfg.get("rx_hz") or 0)/1e6;tx=float(cfg.get("tx_hz") or 0)/1e6
        internet=live.get("internet") or {};qual=internet.get("quality") or "unknown"
        lat=internet.get("latency_ms");loss=internet.get("loss_percent")
        ns=read_network_status();uplink=(ns.get("uplink_type") or "rede").upper();ip=ns.get("default_ip") or "-"
        now=display_hm()
        started=float(a.get("started_unix_ms") or 0)/1000.0
        elapsed=max(0,int(time.time()-started)) if started else 0
        duration=f"{elapsed//60:02d}:{elapsed%60:02d}"
        origin="RF" if direction=="RF" else tr("INTERNET","INTERNET","INTERNET") if direction=="NETWORK" else ""
        ber=a.get("ber");rssi=a.get("rssi_avg",a.get("rssi"))
        city=safe(op.get("city") or "",18);country=safe(op.get("country") or "",18)
        name=safe(op.get("name") or "",22)
        nr=read_json(RUN/"network-runtime.json")
        is_dmr=str(a.get("protocol") or cfg.get("protocol") or "").upper()=="DMR"
        module=safe(a.get("module") or "",3)
        dmr_tg=(nr.get("connected_tg") or nr.get("requested_tg") or a.get("target")) if is_dmr else None
        rfparts=[]
        if ber is not None:rfparts.append(f"BER {ber}%")
        if rssi is not None:rfparts.append(f"RSSI {rssi}")
        rfline="  ".join(rfparts)
        tot_left=max(0,180-elapsed) if direction=="RF" and mode=="tx" else None
        w,h=self.w,self.h
        if tot_left is not None and tot_left<=10:
            # Reserve the entire screen for the final ten seconds. This is a
            # display warning; the RF timeout remains enforced by MMDVMHost.
            countdown=min(10,tot_left)
            self.send(["cls 0",f"fill 0,0,{w},{h},{RED}",
                       self.text(0,max(8,h//9),w,30,tr("LIMITE DE TX","TX LIMIT","LIMITE DE TX"),WHITE,0,1),
                       self.text(0,max(45,h//3),w,70,str(countdown),WHITE,1,1),
                       self.text(0,h-45,w,30,tr("Solte o PTT","Release PTT","Suelte PTT"),WHITE,0,1)])
            self.last_page=("tot-countdown",proto)
            return
        page=(title,proto)
        cmds=[]
        # Each frame is self-contained. The previous page can have left
        # components on the ON7LDS HMI canvas; changing page state alone did
        # not reliably erase those components on the physical display.
        cmds.append("cls 0");self.first_render=False;self.last_page=page
        if w>=320 and h>=240:
            def box(x,y,bw,bh,color):return f"fill {int(x*w/320)},{int(y*h/240)},{max(1,int(bw*w/320))},{max(1,int(bh*h/240))},{color}"
            def label(x,y,bw,bh,value,color=WHITE,align=0,bg=BLACK):
                return self.text(int(x*w/320),int(y*h/240),max(1,int(bw*w/320)),max(1,int(bh*h/240)),value,color,0,align,bg)
            # Designed on a 320x240 grid; all boxes are clipped by construction.
            cmds += [box(0,0,320,240,BLACK),box(0,0,320,30,BLUE),
                     label(10,3,165,24,"PU2PNY-OS",WHITE,0,BLUE),
                     label(176,3,134,24,proto.upper(),WHITE,1,BLUE)]
            if mode=="standby":
                net_online=qual not in ("offline","unknown","")
                net_label=tr("INTERNET ATIVA","INTERNET ONLINE","INTERNET ACTIVA") if net_online else tr("SEM INTERNET","NO INTERNET","SIN INTERNET") if qual=="offline" else tr("REDE —","NETWORK —","RED —")
                cmds += [box(10,40,300,116,GRAY),box(12,42,296,112,BLACK),
                         label(20,45,280,35,own,CYAN,0,1),
                         label(20,81,280,34,now,WHITE,0,1),
                         label(20,119,280,27,tr("AGUARDANDO RF","WAITING FOR RF","ESPERANDO RF"),GREEN,0,1),
                         box(10,166,300,29,GREEN if net_online else RED if qual=="offline" else GRAY),
                         label(18,168,284,25,net_label,BLACK if net_online else WHITE,1,GREEN if net_online else RED if qual=="offline" else GRAY),
                         label(14,205,292,26,f"{uplink}  {ip}",WHITE,0,1)]
            else:
                net_label=(tr("SEM INTERNET","NO INTERNET","SIN INTERNET") if qual=="offline" else f"{uplink} {ip}")
                destination=f"TG {dmr_tg}" if is_dmr and dmr_tg else target or "—"
                cmds += [box(10,39,300,39,header),label(17,44,286,29,source,BLACK,1,header),
                         label(13,84,294,26,name or ("RF" if direction=="RF" else "NET"),WHITE,0,1),
                         box(10,114,300,38,GRAY),box(12,116,296,34,BLACK),
                         label(17,119,286,26,destination,CYAN,0,1),
                         label(13,158,145,27,f"{origin}  {duration}",YELLOW),
                         label(162,158,145,27,rfline or "—",WHITE),
                         box(10,194,300,1,GRAY),label(13,201,294,26,net_label,RED if qual=="offline" else GREEN)]
                if tot_left is not None and tot_left<=20:
                    cmds += [box(0,196,320,44,RED if tot_left<=10 else YELLOW),
                             label(6,199,308,35,f"TOT {tot_left} s",WHITE if tot_left<=10 else BLACK,1,RED if tot_left<=10 else YELLOW)]
            self.send(cmds)
            return
        cmds += [f"fill 0,0,{w},38,{header}",self.text(8,5,w-16,28,f"PU2PNY-OS  {own}  {proto}",BLACK if mode!="standby" else WHITE,0,0)]
        if qual=="offline":
            cmds += [f"fill 0,38,{w},25,{RED}",self.text(0,39,w,22,tr("INTERNET SEM CONEXÃO","INTERNET OFFLINE","SIN INTERNET"),WHITE,0,1)]
        if mode=="standby":
            # Clean standby: clock + radar-like concentric circles + network context.
            cx=w//2;cy=96 if h<=260 else 118
            cmds += [f"cir {cx},{cy},38,{GREEN}",f"cir {cx},{cy},24,{GREEN}",f"cir {cx},{cy},8,{GREEN}",
                     self.text(0,cy+46,w,28,tr("Rastreando sinais","Scanning signals","Rastreando señales"),CYAN,0,1),
                     self.text(10,cy+78,w-20,24,f"{own}   {now}   {proto}",WHITE,0,1),
                     self.text(10,cy+104,w-20,22,f"{uplink}  {ip}",WHITE,0,1)]
            if h>=300:cmds += [self.text(10,h-54,w-20,20,f"RX {rx:.6f}  TX {tx:.6f}",GRAY,0,1),
                               self.text(10,h-30,w-20,20,f"NET {qual}  {lat if lat is not None else '-'} ms",GREEN if qual not in ("poor","offline") else RED,0,1)]
        else:
            # TX/RX identity card. Keep it HMI-independent: stock Nextion
            # serial commands can display picture resources already compiled
            # into the HMI, but not arbitrary caller JPEG/PNG files.  We never
            # overwrite the user's TFT automatically, so use a clean avatar
            # and reserve dynamic photos for an explicitly compatible HMI.
            avatar=source[:2].upper() if source else "ID"
            info_y=48
            cmds += [f"fill 8,{info_y},88,92,{GRAY}",f"fill 10,{info_y+2},84,88,{BLACK}",
                     f"cir 52,{info_y+39},29,{CYAN}",f"cir 52,{info_y+39},25,{BLACK}",
                     self.text(20,info_y+25,64,28,avatar,CYAN,0,1)]
            cmds += self.flag(op.get("country_code"),30,info_y+62)
            cmds += [self.text(106,50,max(90,w-116),36,source,CYAN,0,0),
                     self.text(106,86,max(90,w-116),28,name or "—",WHITE,0,0),
                     self.text(106,116,max(90,w-116),22,(" · ".join([x for x in (city,country) if x])) or tr("Localização —","Location —","Ubicación —"),GRAY,0,0),
                     f"line 10,143,{w-10},143,{GRAY}",
                     self.text(12,149,w-24,24,f"{origin}  {duration}  {proto}",YELLOW if origin=="RF" else CYAN,0,0),
                     self.text(12,177,w-24,23,(f"TG {dmr_tg}" if is_dmr and dmr_tg else f"{target or '-'}"+(f"  · Mód {module}" if module else "")),WHITE,0,0)]
            if rfline:cmds += [self.text(12,202,w-24,20,rfline,WHITE,0,0)]
            if tot_left is not None:
                # Keep the warning inside a 320x240 Nextion as well as larger
                # screens; the old lower bound drew it below the 240px edge.
                alert_y=max(0,h-36)
                cmds += [f"fill 0,{alert_y},{w},30,{RED if tot_left<=10 else YELLOW}",
                         self.text(0,alert_y+2,w,26,f"TOT: corte em {tot_left} s",WHITE if tot_left<=10 else BLACK,0,1)]
            else:
                net_color=GREEN if qual not in ("poor","offline") else RED
                cmds += [f"line 10,{h-58},{w-10},{h-58},{GRAY}",
                         self.text(12,h-54,w-24,21,f"{uplink} {ip}  NET {qual}",net_color,0,0),
                         self.text(12,h-31,w-24,19,f"LAT {lat if lat is not None else '-'} ms  PER {loss if loss is not None else '-'}%",GRAY,0,0)]
        self.send(cmds)

class I2CBase:
    def __init__(self,bus=1,address=0x3c):
        import smbus
        self.bus=smbus.SMBus(bus);self.addr=address
    def close(self):
        try:self.bus.close()
        except Exception:pass

class OLED(I2CBase):
    """Graphical renderer for SSD1306 128x32/128x64 and SH1106 128x64.

    Moderno V2 deliberately renders shapes/status hierarchy instead of a
    terminal-like list. It only consumes PU2PNY snapshots and never polls RF.
    """
    def __init__(self,bus=1,address=0x3c,sh1106=False,height=64):
        super().__init__(bus,address);self.sh1106=sh1106;self.w=128;self.h=height
        from PIL import Image,ImageDraw,ImageFont
        self.Image=Image;self.ImageDraw=ImageDraw;self.font=ImageFont.load_default()
        self.cmd(0xAE,0xD5,0x80,0xA8,height-1,0xD3,0x00,0x40,0x8D,0x14,0x20,0x00,0xA1,0xC8,0xDA,0x02 if height==32 else 0x12,0x81,0xCF,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0xAF)
    def cmd(self,*vals):
        for v in vals:self.bus.write_byte_data(self.addr,0x00,v)
    def show_image(self,img):
        pix=img.load()
        for page in range(self.h//8):
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
    def label(self,d,xy,text):
        d.text(xy,safe(text,22),font=self.font,fill=255)
    def bars(self,d,x,y,value=None):
        level=0
        try:
            if value is not None:
                rv=float(value); level=max(1,min(4,int((rv+125)/10)+1))
        except Exception:level=0
        for i in range(4):
            h=3+i*2
            if i<level:d.rectangle((x+i*4,y+8-h,x+i*4+2,y+8),fill=255)
            else:d.rectangle((x+i*4,y+8-h,x+i*4+2,y+8),outline=255)
    def render(self,live,cfg,tel):
        a=live.get("active") or {};mode=str(a.get("mode") or "standby").lower()
        proto=str(a.get("protocol") or cfg.get("protocol") or "PU2PNY").replace("DSTAR","D-STAR")
        op=a.get("operator") or {};ns=read_network_status();net=live.get("internet") or {}
        img=self.Image.new("1",(128,self.h));d=self.ImageDraw.Draw(img)
        if self.h==32:
            d.rectangle((0,0,127,10),fill=255)
            d.text((2,1),"PU2PNY",font=self.font,fill=0)
            d.text((91,1),"TX" if mode=="tx" else "RX" if mode=="rx" else "STBY",font=self.font,fill=0)
            if mode=="standby":
                self.label(d,(1,12),f"{proto[:10]} {display_hm()}")
                self.label(d,(1,22),str(ns.get("uplink_type") or "NET").upper()+" "+str(ns.get("default_ip") or "-"))
            else:
                self.label(d,(1,12),f"{proto[:6]} {str(a.get('source') or '-')[:13]}")
                self.label(d,(1,22),str(a.get("target") or "-")[:12])
                self.bars(d,109,21,a.get("rssi_avg",a.get("rssi")))
            self.show_image(img)
            return
        # Header / status pill.
        d.rectangle((0,0,127,12),fill=255)
        d.text((3,2),"PU2PNY",font=self.font,fill=0)
        state="TX" if mode=="tx" else "RX" if mode=="rx" else "STBY"
        d.rectangle((95,1,126,11),fill=0)
        d.text((101,2),state,font=self.font,fill=255)
        d.line((0,14,127,14),fill=255)
        if mode=="standby":
            now=display_hm()
            self.label(d,(3,18),f"{proto}  {now}")
            # Small radar / scanning visual.
            d.ellipse((7,31,31,55),outline=255);d.ellipse((13,37,25,49),outline=255)
            d.line((19,43,29,35),fill=255);d.ellipse((17,41,21,45),fill=255)
            self.label(d,(39,29),tr("RASTREANDO","SCANNING","RASTREANDO"))
            self.label(d,(39,40),str(ns.get("uplink_type") or "NET").upper())
            ip=str(ns.get("default_ip") or "-")
            self.label(d,(39,51),ip[-14:])
        else:
            source=str(a.get("source") or "-").upper()
            target=str(a.get("target") or "-")
            direction="RF>NET" if str(a.get("direction") or "").upper()=="RF" else "NET>RF"
            self.label(d,(3,17),f"{proto} {direction}")
            # Identity card.
            d.rectangle((2,27,88,51),outline=255)
            self.label(d,(6,30),source)
            name=str(op.get("name") or "")
            if name:self.label(d,(6,41),name[:13])
            self.label(d,(93,29),mode.upper())
            self.bars(d,94,43,a.get("rssi_avg",a.get("rssi")))
            # Footer line with target / BER or network status.
            ber=a.get("ber")
            extra=f"B{ber}%" if ber is not None else str(net.get("quality") or "").upper()[:4]
            self.label(d,(3,54),f"{target[:12]} {extra}")
        self.show_image(img)

class LCD(I2CBase):
    def __init__(self,bus=1,address=0x27,cols=20,rows=4):
        super().__init__(bus,address);self.cols=cols;self.rows=rows;self.bl=0x08
        time.sleep(.05)
        for n in (0x30,0x30,0x30,0x20):self._nibble(n);time.sleep(.002)
        for cmd in (0x28,0x08,0x01,0x06,0x0C):self.command(cmd)
    def _nibble(self,n):
        self.bus.write_byte(self.addr,(n&0xF0)|self.bl|0x04);self.bus.write_byte(self.addr,(n&0xF0)|self.bl)
    def command(self,n):self._nibble(n);self._nibble((n<<4)&0xF0)
    def data(self,n):
        self.bus.write_byte(self.addr,(n&0xF0)|self.bl|0x05);self.bus.write_byte(self.addr,(n&0xF0)|self.bl|0x01)
        self.bus.write_byte(self.addr,((n<<4)&0xF0)|self.bl|0x05);self.bus.write_byte(self.addr,((n<<4)&0xF0)|self.bl|0x01)
    def show(self,lines):
        addrs=[0x00,0x40,0x14,0x54] if self.cols>=20 else [0x00,0x40]
        for row in range(self.rows):
            self.command(0x80+addrs[row]);txt=safe(lines[row] if row<len(lines) else "",self.cols).ljust(self.cols)
            for ch in txt:self.data(ord(ch) if ord(ch)<128 else ord("?"))
    def render(self,live,cfg,tel):
        a=live.get("active") or {};mode=a.get("mode") or "standby";proto=str(a.get("protocol") or cfg.get("protocol") or "-").replace("DSTAR","D-STAR");op=a.get("operator") or {}
        if self.rows>=4:
            if mode=="standby":
                ns=read_network_status();lines=[f"PU2PNY {display_hm()}",f"{proto} {tr('PRONTO','READY','LISTO')}",f"RF {float(cfg.get('rx_hz') or 0)/1e6:.5f}",f"{(ns.get('uplink_type') or 'NET').upper()} {ns.get('default_ip') or '-'}"]
            else:
                rv=a.get("rssi_avg",a.get("rssi"));rf=[]
                if a.get("ber") is not None:rf.append(f"B{a.get('ber')}%")
                if rv is not None:rf.append(f"R{rv}")
                ns=read_network_status();place=" / ".join(x for x in (str(op.get("city") or ""),str(op.get("country") or "")) if x)
                who=((a.get("source") or "-")+" "+(op.get("name") or "")).strip()
                internet=live.get("internet") or {};qual=str(internet.get("quality") or "?").upper()
                net=f"{(ns.get('uplink_type') or 'NET').upper()} {ns.get('default_ip') or '-'} {qual[:3]}"
                lines=[f"{mode.upper()} {proto}",who,place or (a.get("target") or "-"),net]
        else:
            ns=read_network_status();lines=[f"{mode.upper()} {proto} {a.get('source') or 'PU2PNY'}",f"{(ns.get('uplink_type') or 'NET').upper()} {ns.get('default_ip') or '-'}"]
        self.show(lines)

def nextion_size(model,settings=None):
    settings=settings or {}
    manual=str(settings.get("resolution") or "").lower().strip()
    if re.fullmatch(r"\d{3,4}x\d{3,4}",manual):
        try:
            w,h=(int(x) for x in manual.split("x",1))
            if 240<=w<=1920 and 160<=h<=1080:return w,h
        except Exception:pass
    m=str(model or "").upper()
    if "1060" in m:return 1024,600
    if "8048" in m:return 800,480
    if "4832" in m:return 480,320
    if "4827" in m:return 480,272
    if "4024" in m:return 400,240
    if "3224" in m:return 320,240
    return 320,240

def create_driver(hw):
    d=hw.get("display") or {};cls=str(d.get("class") or "");state=str(d.get("state") or "")
    settings=read_json(SETTINGS)
    if settings.get("enabled") is False:return None,"disabled"
    if cls in ("nextion","nextion_mmdvm") or state=="mmdvm_display_candidate":
        integration="nextion_mmdvm" if cls=="nextion_mmdvm" or state=="mmdvm_display_candidate" else "nextion"
        w,h=nextion_size(d.get("model"),settings)
        return Nextion(integration,str(d.get("port") or ""),int(d.get("baud") or 9600),w,h),integration
    addr=d.get("address")
    if isinstance(addr,str):
        try:addr=int(addr,16)
        except Exception:addr=None
    if addr in (0x3c,0x3d):
        model=str(d.get("model") or "").lower()
        resolution=str(settings.get("resolution") or d.get("resolution") or "128x64").lower()
        height=32 if resolution=="128x32" and "sh1106" not in model else 64
        return OLED(int(d.get("bus") or 1),addr,"sh1106" in model,height),"oled"
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
                        if kind.startswith("nextion") and hasattr(driver,"splash"):
                            try:
                                driver.splash(0,tr("Inicializando","Starting","Iniciando"))
                                driver.splash(25,tr("Interface iniciada","Display started","Pantalla iniciada"))
                            except Exception:pass
                        # Own PU2PNY renderer is authoritative; avoid competing commands.
                        subprocess.run(["systemctl","stop","2pny-display.service"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                        settings=read_json(SETTINGS)
                        physical_confirmed=bool(settings.get("physical_confirmed"))
                        unconfirmed=kind=="nextion_mmdvm" and not physical_confirmed
                        write_status(state="tx_only_unconfirmed" if unconfirmed else "active",active=True,type=kind,driver="pu2pny-display-core",
                                     renderer="pu2pny-modern-v2",writer="pu2pny-display-core",
                                     physical_confirmed=physical_confirmed,
                                     model_profile=settings.get("model_profile","auto"),
                                     resolution=settings.get("resolution") or f"{getattr(driver,'w',128)}x{getattr(driver,'h',64)}",
                                     message="Comandos enviados; resposta COMOK não confirmada" if unconfirmed else "PU2PNY Moderno V2 ativo")
            live=read_json(LIVE,{"standby":True});cfg=read_json(CFG);tel=read_json(TELEM)
            if driver and kind.startswith("nextion") and driver.last_page==("splash",""):
                if cfg and live:
                    driver.splash(75,tr("Dados carregados","Data loaded","Datos cargados"))
                    driver.splash(100,tr("Pronto","Ready","Listo"))
                else:
                    time.sleep(1);continue
            active=live.get("active") or {}
            cadence=int(now) if active else int(now//60)
            sig=(live.get("sequence"),active.get("source"),active.get("target"),active.get("mode"),active.get("direction"),
                 active.get("ber"),active.get("rssi_avg",active.get("rssi")),active.get("module"),
                 (live.get("internet") or {}).get("quality"),cadence)
            if driver and sig!=last_sig:
                driver.render(live,cfg,tel);last_sig=sig;failures=0
            elif not driver:
                write_status(state="not_configured",active=False,type=kind,message="Nenhum display suportado detectado")
            time.sleep(.5 if active else 2.0)
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
