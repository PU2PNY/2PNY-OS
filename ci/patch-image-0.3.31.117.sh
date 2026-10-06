#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"
NEXTION_BIN="${2:?hardened NextionDriver binary required}"
NEXTION_SRC="${3:?pinned NextionDriver checkout required}"

test -x "$NEXTION_BIN"
test -f "$NEXTION_SRC/groups.txt"
test -f "$NEXTION_SRC/users.csv"

install -d -m 0755 "$ROOT/usr/local/bin" "$ROOT/usr/share/2pny/nextiondriver" "$ROOT/usr/share/doc/nextiondriver-pu2pny" "$ROOT/etc/systemd/system"
install -m 0755 "$NEXTION_BIN" "$ROOT/usr/local/bin/NextionDriver-pu2pny"
install -m 0644 "$NEXTION_SRC/groups.txt" "$ROOT/usr/share/2pny/nextiondriver/groups.txt"
install -m 0644 "$NEXTION_SRC/users.csv" "$ROOT/usr/share/2pny/nextiondriver/users.csv"
cat >"$ROOT/usr/share/doc/nextiondriver-pu2pny/UPSTREAM" <<'EOF'
NextionDriver upstream: https://github.com/on7lds/NextionDriver
Pinned commit: 03b904270c9cb54f720d71753fc209afb1d9598f
License: GNU GPL v2 or later, per upstream source headers.
PU2PNY-OS hardening: HMI-to-shell execution and driver-managed network downloads are disabled; HMI/TFT flashing is never initiated by the driver.
EOF
ln -sfn /usr/share/common-licenses/GPL-2 "$ROOT/usr/share/doc/nextiondriver-pu2pny/COPYING"

cat >"$ROOT/etc/systemd/system/2pny-nextiondriver.service" <<'EOF'
[Unit]
Description=PU2PNY hardened ON7LDS Nextion compatibility driver
After=local-fs.target network.target
Before=2pny-mmdvmhost.service
ConditionPathExists=/var/lib/2pny/mmdvm/MMDVM-Host.ini

[Service]
Type=simple
User=mmdvm
Group=mmdvm
RuntimeDirectory=2pny-nextiondriver
RuntimeDirectoryMode=0755
ExecStart=/usr/local/bin/NextionDriver-pu2pny -d -c /var/lib/2pny/mmdvm/MMDVM-Host.ini
Restart=on-failure
RestartSec=2
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
LockPersonality=yes
RestrictSUIDSGID=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
IPAddressDeny=any
IPAddressAllow=localhost
ReadWritePaths=/run/2pny-nextiondriver

[Install]
WantedBy=multi-user.target
EOF

ROOT="$ROOT" python3 - <<'PY'
import os,re
from pathlib import Path
root=Path(os.environ['ROOT'])

def load(rel):
    p=root/rel
    if not p.is_file(): raise SystemExit(f'missing image file: {rel}')
    return p,p.read_text()

def save(p,s): p.write_text(s)

def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: anchor count={n}')
    return s.replace(old,new,1)

# NET-037: after the transactional Wi-Fi connect reports CONNECTED, follow the
# canonical mDNS/IP resume candidates instead of leaving the user on the old AP.
p,s=load('usr/share/2pny/internet.html')
reach="async function wifiReachable(base){try{var ctl=window.AbortController?new AbortController():null,t=ctl?setTimeout(function(){ctl.abort()},900):null;await fetch(base+'/healthz?ts='+Date.now(),{mode:'no-cors',cache:'no-store',signal:ctl?ctl.signal:undefined});if(t)clearTimeout(t);return true}catch(e){return false}}"
follow="""\nasync function followPrimaryToPanel(st){
 var bases=['http://pu2pny.local'],rows=(st&&st.resume_urls)||[];
 rows.forEach(function(x){x=String(x||'').replace(/\\/(wizard|internet)\\/?$/,'').replace(/\\/$/,'');if(x&&bases.indexOf(x)<0)bases.push(x)});
 for(var i=0;i<24;i++){
  for(var j=0;j<bases.length;j++)if(await wifiReachable(bases[j])){location.replace(bases[j]+'/internet');return true}
  await new Promise(function(r){setTimeout(r,500)})
 }
 return false
}"""
if s.count(reach)!=1: raise SystemExit('internet wifiReachable anchor missing/ambiguous')
s=s.replace(reach,reach+follow,1)
old="if(st.state==='connected'){op.done(st.message||'Rede Wi‑Fi 1 conectada.');PNY.q('wifiPrimaryPass').value='';PNY.q('wifiPrimaryManual').value='';load();return}"
new="if(st.state==='connected'){op.done(st.message||'Rede Wi‑Fi 1 conectada.');PNY.q('wifiPrimaryPass').value='';PNY.q('wifiPrimaryManual').value='';if(await followPrimaryToPanel(st))return;load();return}"
s=one(s,old,new,'internet connected handoff')
save(p,s)

# LIVE-023: the Ao Vivo bar represents real Wi-Fi signal when Wi-Fi is the
# default uplink. Ethernet deliberately has no fake RSSI/percentage.
p,s=load('usr/share/2pny/dashboard.html')
s=one(s,'<div class="netrow"><span>Internet</span><div class="meter"><i id="netMeter" style="width:100%"></i></div>',
      '<div class="netrow"><span id="uplinkText">Wi-Fi / Uplink</span><div class="meter"><i id="netMeter" style="width:0%"></i></div>',
      'dashboard uplink row')
old="""  PNY.q('netMeter').style.width=(q==='offline'?0:good?100:35)+'%';
  PNY.q('netMeter').style.background=good?'var(--green)':q==='offline'?'var(--red)':'var(--yellow)';"""
new="""  var uplink=String(c.default_interface||c.client_interface||''),eth=String(c.ethernet_interface||''),wifiDefault=!!c.wifi&&(!eth||uplink!==eth),sig=Number(c.wifi_signal||0),rssi=Number(c.wifi_rssi_dbm||0),meter=PNY.q('netMeter'),ut=PNY.q('uplinkText');
  if(eth&&uplink===eth){ut.textContent='Wi-Fi / Uplink · Ethernet';meter.style.width='0%';meter.style.background='var(--blue)';meter.title='RSSI —'}
  else if(wifiDefault&&Number.isFinite(sig)&&sig>0){sig=Math.max(1,Math.min(100,sig));ut.textContent='Wi-Fi / Uplink · '+(c.wifi_ssid||uplink||'Wi-Fi')+' · '+sig+'%'+(Number.isFinite(rssi)&&rssi!==0?' · '+rssi.toFixed(0)+' dBm':'');meter.style.width=sig+'%';meter.style.background=sig>=70?'var(--green)':sig>=45?'var(--yellow)':'var(--red)';meter.title=Number.isFinite(rssi)&&rssi!==0?rssi.toFixed(0)+' dBm':sig+'%'}
  else{ut.textContent='Wi-Fi / Uplink · —';meter.style.width='0%';meter.style.background='var(--line)';meter.title='RSSI —'}"""
s=one(s,old,new,'dashboard real uplink meter')
save(p,s)

# DISPLAY-025: add a third renderer for existing WPSD/Pi-Star/ON7LDS HMIs.
# It uses a hardened NextionDriver over MMDVMHost Transparent Data and never
# auto-flashes TFT/HMI. Existing native and PU2PNY renderer code is preserved.
p,s=load('usr/share/2pny/display.html')
s=one(s,'<option value="pu2pny-modern-v2">PU2PNY Moderno V2</option><option value="mmdvmhost-native">Compatível Pi-Star/WPSD (MMDVMHost nativo)</option>',
      '<option value="pu2pny-modern-v2">PU2PNY Moderno V2</option><option value="mmdvmhost-native">Compatível Pi-Star/WPSD (MMDVMHost nativo)</option><option value="on7lds-compatible">Pi-Star/WPSD avançado · ON7LDS NextionDriver</option>',
      'display renderer option')
s=one(s,'<option value="3">ON7LDS L3 · ScreenLayout 3</option>',
      '<option value="3">ON7LDS L3 · ScreenLayout 3</option><option value="4">ON7LDS L3 HS · ScreenLayout 4</option>',
      'display layout4 option')
s=one(s,"function syncRenderer(){var native=q('rendererSelect').value==='mmdvmhost-native';q('nativeWrap').classList.toggle('hidden',!native)}",
      "function syncRenderer(){var r=q('rendererSelect').value,native=r==='mmdvmhost-native'||r==='on7lds-compatible';q('nativeWrap').classList.toggle('hidden',!native)}",
      'display renderer toggle')
s=one(s,"q('rendererSelect').value=o.renderer==='mmdvmhost-native'?'mmdvmhost-native':'pu2pny-modern-v2';",
      "q('rendererSelect').value=o.renderer==='on7lds-compatible'?'on7lds-compatible':(o.renderer==='mmdvmhost-native'?'mmdvmhost-native':'pu2pny-modern-v2');",
      'display renderer load')
s=one(s,"q('nativeLayout').value=String([0,2,3].includes(Number(o.layout))?Number(o.layout):2);syncRenderer()",
      "q('nativeLayout').value=String([0,2,3,4].includes(Number(o.layout))?Number(o.layout):2);syncRenderer()",
      'display layout load')
s=one(s,"var renderer=q('rendererSelect').value,parts=q('modelSelect').value.split('|'),layout=renderer==='mmdvmhost-native'?Number(q('nativeLayout').value):9;var detail=renderer==='mmdvmhost-native'?'Ativando renderer compatível do MMDVMHost com writer exclusivo…':'Ativando PU2PNY Moderno V2 com atualizações incrementais…';",
      "var renderer=q('rendererSelect').value,parts=q('modelSelect').value.split('|'),layout=renderer==='pu2pny-modern-v2'?9:Number(q('nativeLayout').value);var detail=renderer==='on7lds-compatible'?'Ativando compatibilidade ON7LDS por Transparent Data com writer exclusivo…':(renderer==='mmdvmhost-native'?'Ativando renderer compatível do MMDVMHost com writer exclusivo…':'Ativando PU2PNY Moderno V2 com atualizações incrementais…');",
      'display save mode')
s=one(s,'NextionDriver/L3 HS só deve ser habilitado quando o driver estiver realmente instalado e validado; esta imagem não presume esse suporte.',
      'NextionDriver/L3 HS usa o driver endurecido e fixado desta imagem quando selecionado; TFT/HMI permanece preservado e a validação física continua obrigatória.',
      'display compatibility notice')
save(p,s)

p,s=load('usr/local/sbin/2pny-display-apply')
s=one(s,'MQTT="mosquitto.service"','MQTT="mosquitto.service"\nNEXTIONDRIVER="2pny-nextiondriver.service"','display service constant')
# Base image may contain either the 0.3.30 source defaults or the 0.3.31
# native-default surgical patch. Preserve whichever default is present.
s,n=re.subn(r'if requested not in \(9,0,2,3\):requested=([29])',r'if requested not in (9,0,2,3,4):requested=\1',s,count=1)
if n!=1: raise SystemExit('display requested-layout anchor missing/ambiguous')
s,n=re.subn(r'if renderer not in \("pu2pny-modern-v2","mmdvmhost-native"\):renderer="([^"]+)"',
            r'if renderer not in ("pu2pny-modern-v2","mmdvmhost-native","on7lds-compatible"):renderer="\1"',s,count=1)
if n!=1: raise SystemExit('display renderer allowlist anchor missing/ambiguous')
s=one(s,'if requested in (0,2,3):renderer="mmdvmhost-native"',
      'if requested in (0,2,3) and renderer!="on7lds-compatible":renderer="mmdvmhost-native"\nif requested==4:renderer="on7lds-compatible"',
      'display layout renderer mapping')

insert='''\ndef stop_on7lds():
    ctl("disable","--now",NEXTIONDRIVER)

def patch_on7lds(layout):
    if layout not in (3,4):layout=3
    cp=host_config()
    cp.set("General","Display","Nextion")
    cp.set("Nextion","Port","/run/2pny-nextiondriver/ttyNextionDriver")
    cp.set("Nextion","Brightness",cp.get("Nextion","Brightness",fallback="50"))
    cp.set("Nextion","DisplayClock","1");cp.set("Nextion","UTC","0")
    cp.set("Nextion","IdleBrightness",cp.get("Nextion","IdleBrightness",fallback="20"))
    cp.set("Nextion","ScreenLayout",str(layout))
    if not cp.has_section("Transparent Data"):cp.add_section("Transparent Data")
    for k,v in (("Enable","1"),("RemoteAddress","127.0.0.1"),("RemotePort","40094"),("LocalPort","40095"),("SendFrameType","1")):
        cp.set("Transparent Data",k,v)
    if not cp.has_section("NextionDriver"):cp.add_section("NextionDriver")
    for k,v in (("Port","modem"),("LogLevel","1"),("DataFilesPath","/usr/share/2pny/nextiondriver"),("GroupsFile","groups.txt"),("DMRidFile","users.csv"),("WaitForLan","0"),("ShowModesStatus","1"),("RemoveDim","0"),("SleepWhenInactive","0")):
        cp.set("NextionDriver",k,v)
    backup=HOST.with_name("MMDVM-Host.ini.display-backup")
    write_host(cp,backup)
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    if not ctl("enable","--now",NEXTIONDRIVER):
        shutil.copy2(backup,HOST);raise RuntimeError("NextionDriver endurecido não iniciou; configuração anterior restaurada")
    end=time.monotonic()+7
    link=Path("/run/2pny-nextiondriver/ttyNextionDriver")
    while time.monotonic()<end:
        if active(NEXTIONDRIVER) and link.exists():break
        time.sleep(.25)
    else:
        ctl("disable","--now",NEXTIONDRIVER);shutil.copy2(backup,HOST)
        raise RuntimeError("NextionDriver não disponibilizou a porta virtual; configuração anterior restaurada")
    try:restart_host_or_rollback(backup)
    except Exception:
        ctl("disable","--now",NEXTIONDRIVER);raise
    return backup
'''
anchor='hw=load(HW);ov=load(OVERRIDE);m=hw.get("mmdvm") or {};d=hw.get("display") or {}'
if s.count(anchor)!=1: raise SystemExit('display helper insertion anchor missing/ambiguous')
s=s.replace(anchor,insert+'\n'+anchor,1)

native='if kind=="nextion_mmdvm" and renderer=="mmdvmhost-native":\n'
if s.count(native)!=1: raise SystemExit('display native branch anchor missing/ambiguous')
on7='''if kind=="nextion_mmdvm" and renderer=="on7lds-compatible":
    effective=requested if requested in (3,4) else 3
    patch_on7lds(effective)
    if active(CORE):raise RuntimeError("Conflito de writer: PU2PNY Display Core permaneceu ativo no modo ON7LDS")
    d.update({"class":"nextion_mmdvm","port":"modem","auto_selected":False,
              "message":"Nextion via MMDVM usando ON7LDS NextionDriver endurecido e Transparent Data."})
    hw["display"]=d;write_json(HW,hw)
    settings.update({"enabled":True,"driver":"NextionDriver-pu2pny","renderer":"on7lds-compatible","writer":"on7lds-nextiondriver",
                     "type":kind,"automatic":False,"model_profile":profile,"resolution":resolution,
                     "requested_layout":requested,"effective_layout":effective,"physical_confirmed":bool(d.get("physical_confirmed"))})
    write_json(SETTINGS,settings)
    write_json(STATUS,{"state":"active" if active(MMDVM) and active(NEXTIONDRIVER) else "configured","active":active(MMDVM) and active(NEXTIONDRIVER),
                       "type":kind,"driver":"NextionDriver-pu2pny","renderer":"on7lds-compatible","writer":"on7lds-nextiondriver",
                       "integration":"mmdvm-transparent-data","layout":requested,"effective_layout":effective,
                       "model_profile":profile,"resolution":resolution,"physical_confirmed":bool(d.get("physical_confirmed")),
                       "message":"Compatibilidade Pi-Star/WPSD/ON7LDS ativa; HMI/TFT preservado. Modelo/HMI só são confirmados por evidência física.",
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_APPLY_OK");raise SystemExit(0)

'''
s=s.replace(native,on7+native,1)
s=one(s,native,native+'    stop_on7lds()\n','display native stops compatibility driver')
s=one(s,'# PU2PNY renderer: direct displays use their bus; Nextion/MMDVM uses MQTT.\nctl("disable","--now",LEGACY)',
      '# PU2PNY renderer: direct displays use their bus; Nextion/MMDVM uses MQTT.\nstop_on7lds()\nctl("disable","--now",LEGACY)',
      'display modern stops compatibility driver')
save(p,s)

(root/'etc/2pny/version').write_text('0.3.31.117\n')
PY

python3 -m py_compile "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'followPrimaryToPanel' "$ROOT/usr/share/2pny/internet.html"
grep -Fq "wifi_signal" "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Wi-Fi / Uplink · Ethernet' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'on7lds-compatible' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'mmdvm-transparent-data' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'SendFrameType","1"' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'NoNewPrivileges=yes' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq 'IPAddressAllow=localhost' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
! grep -RqiE '(^|[;&|[:space:]])(upload|flash).*\.tft|\.tft.*(upload|flash)' "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/etc/systemd/system/2pny-nextiondriver.service" || exit 1
test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.117'
echo PATCH_IMAGE_0331117_OK
