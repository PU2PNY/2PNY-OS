#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re
root=Path('.')

# 0.1.3 network hardening on top of 0.1.2.
p=root/'builder/build-image.sh'
s=p.read_text().replace('VERSION="${VERSION:-0.1.2-alpha}"','VERSION="${VERSION:-0.1.3-alpha}"')
needle='chmod 0600 "${ROOT_MNT}/etc/NetworkManager/system-connections/"*.nmconnection\n'
insert='''chmod 0600 "${ROOT_MNT}/etc/NetworkManager/system-connections/"*.nmconnection
CMDLINE="${ROOT_MNT}/boot/firmware/cmdline.txt"
grep -qw 'network-config=disabled' "$CMDLINE" || sed -i '1 s/$/ network-config=disabled/' "$CMDLINE"
grep -qw 'cfg80211.ieee80211_regdom=BR' "$CMDLINE" || sed -i '1 s/$/ cfg80211.ieee80211_regdom=BR/' "$CMDLINE"
mkdir -p "${ROOT_MNT}/var/lib/NetworkManager"
cat > "${ROOT_MNT}/var/lib/NetworkManager/NetworkManager.state" <<'NMSTATE'
[main]
NetworkingEnabled=true
WirelessEnabled=true
WWANEnabled=true
NMSTATE
rm -f "${ROOT_MNT}/var/lib/systemd/rfkill/"*:wlan 2>/dev/null || true
'''
if needle in s:
    s=s.replace(needle,insert,1)
p.write_text(s)

p=root/'src/2pnyd/main.go'
s=p.read_text().replace('appVersion      = "0.1.2-alpha"','appVersion      = "0.1.3-alpha"').replace('<b>Alpha 0.1.2:</b>','<b>Alpha 0.1.3:</b>')
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.3-alpha\n')

cloud=root/'rootfs-overlay/etc/cloud/cloud.cfg.d'; cloud.mkdir(parents=True,exist_ok=True)
(cloud/'99-2pny-appliance.cfg').write_text('''network:
  config: disabled
disable_network_activation: true
preserve_hostname: true
''')

nmstate=root/'rootfs-overlay/var/lib/NetworkManager'; nmstate.mkdir(parents=True,exist_ok=True)
(nmstate/'NetworkManager.state').write_text('''[main]
NetworkingEnabled=true
WirelessEnabled=true
WWANEnabled=true
''')

conn=root/'rootfs-overlay/etc/NetworkManager/system-connections'; conn.mkdir(parents=True,exist_ok=True)
(conn/'2pny-ethernet.nmconnection').write_text('''[connection]
id=2PNY-Ethernet
uuid=7ec42a49-a77d-49f7-a181-2a4f00000001
type=ethernet
autoconnect=true
autoconnect-priority=50
mdns=2

[ethernet]

[ipv4]
method=auto
address1=169.254.2.1/16
link-local=4
dhcp-timeout=10

[ipv6]
method=auto
addr-gen-mode=default

[proxy]
''')
(conn/'2pny-setup.nmconnection').write_text('''[connection]
id=2PNY-SETUP
uuid=5d9da2d9-3b48-4936-8201-2a4f00000002
type=wifi
autoconnect=true
autoconnect-priority=100
mdns=2

[wifi]
mode=ap
band=bg
channel=6
ssid=2PNY-SETUP

[wifi-security]
key-mgmt=wpa-psk
psk=2pnysetup

[ipv4]
method=shared
address1=10.42.0.1/24

[ipv6]
method=disabled

[proxy]
''')

# Event driven Ethernet fallback + hardware refresh.
disp=root/'rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity'
disp.write_text(r'''#!/bin/bash
IFACE="${1:-unknown}"
ACTION="${2:-unknown}"
logger -t 2pny-net "interface=${IFACE} action=${ACTION}"
case "$ACTION" in
  up|dhcp4-change)
    if [[ "$(nmcli -g GENERAL.TYPE device show "$IFACE" 2>/dev/null || true)" == "ethernet" ]]; then
      ip address add 169.254.2.1/16 dev "$IFACE" 2>/dev/null || true
    fi
    /usr/local/sbin/2pny-hardware-detect >/dev/null 2>&1 || true
    ;;
  down|connectivity-change)
    /usr/local/sbin/2pny-hardware-detect >/dev/null 2>&1 || true
    ;;
esac
exit 0
''')

# Robust first boot.
fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
LOG=/var/log/2pny-firstboot.log
mkdir -p "$STATE"
exec >>"$LOG" 2>&1

echo "[$(date -Is)] 2PNY first boot 0.1.3-alpha"
hostnamectl set-hostname 2pny || true
systemctl start NetworkManager.service || true
systemctl start avahi-daemon.service || true
if [[ -f "$STATE/provisioned" ]]; then exit 0; fi
raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
for f in /var/lib/systemd/rfkill/*:wlan; do [[ -e "$f" ]] && echo 0 > "$f" 2>/dev/null || true; done
rfkill unblock wifi 2>/dev/null || true
nmcli radio wifi on 2>/dev/null || true
for _ in {1..60}; do nmcli -t -f DEVICE,TYPE device status >/dev/null 2>&1 && break; sleep 1; done
ETH_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1;exit}')"
if [[ -n "${ETH_IF:-}" ]]; then
  nmcli connection modify 2PNY-Ethernet connection.autoconnect yes connection.autoconnect-priority 50 2>/dev/null || true
  nmcli --wait 12 connection up 2PNY-Ethernet ifname "$ETH_IF" >/dev/null 2>&1 || true
  ip address add 169.254.2.1/16 dev "$ETH_IF" 2>/dev/null || true
fi
WIFI_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"
AP_OK=0
if [[ -n "${WIFI_IF:-}" ]]; then
  ip link set "$WIFI_IF" up 2>/dev/null || true
  rfkill unblock wifi 2>/dev/null || true
  nmcli radio wifi on 2>/dev/null || true
  for attempt in {1..6}; do
    if nmcli --wait 15 connection up 2PNY-SETUP ifname "$WIFI_IF" >/dev/null 2>&1; then AP_OK=1; break; fi
    if [[ "$attempt" -eq 2 ]]; then
      nmcli connection delete 2PNY-SETUP >/dev/null 2>&1 || true
      if nmcli --wait 15 device wifi hotspot ifname "$WIFI_IF" con-name 2PNY-SETUP ssid 2PNY-SETUP band bg channel 6 password 2pnysetup >/dev/null 2>&1; then
        nmcli connection modify 2PNY-SETUP ipv4.method shared ipv4.addresses 10.42.0.1/24 connection.autoconnect yes connection.autoconnect-priority 100 connection.mdns yes >/dev/null 2>&1 || true
        AP_OK=1; break
      fi
    fi
    raspi-config nonint do_wifi_country BR 2>/dev/null || true
    rfkill unblock wifi 2>/dev/null || true
    nmcli radio wifi on 2>/dev/null || true
    sleep 5
  done
else
  AP_OK=1
fi
systemctl restart avahi-daemon.service || true
systemctl restart 2pnyd.service || true
if [[ "$AP_OK" -ne 1 ]]; then exit 1; fi
exit 0
''')

svc=root/'rootfs-overlay/etc/systemd/system/2pny-firstboot.service'
svc.write_text('''[Unit]
Description=2PNY first boot provisioning
After=NetworkManager.service avahi-daemon.service
Wants=NetworkManager.service avahi-daemon.service
ConditionPathExists=!/var/lib/2pny/provisioned
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/2pny-firstboot
RemainAfterExit=yes
Restart=on-failure
RestartSec=10
TimeoutStartSec=180

[Install]
WantedBy=multi-user.target
''')

p=root/'rootfs-overlay/etc/systemd/system/2pnyd.service'
ss=p.read_text().replace('After=NetworkManager.service network-online.target\nWants=NetworkManager.service network-online.target','After=NetworkManager.service\nWants=NetworkManager.service')
p.write_text(ss)

# Replace setup backend with asynchronous AP -> client handoff plus status API.
p=root/'src/2pnyd/main.go'; s=p.read_text()
helpers=r'''
const setupStateFile = "/var/lib/2pny/setup-state.json"

type SetupState struct {
	State string `json:"state"`
	Message string `json:"message"`
	Updated string `json:"updated"`
}

func writeSetupState(state, message string) {
	st := SetupState{State: state, Message: message, Updated: time.Now().UTC().Format(time.RFC3339)}
	b, _ := json.Marshal(st)
	_ = os.WriteFile(setupStateFile, b, 0600)
}

func setupStatusHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Cache-Control", "no-store")
	if fileExists(provisionedFile) {
		writeJSON(w, http.StatusOK, SetupState{State:"connected", Message:"Conectado. Abrindo o painel.", Updated:time.Now().UTC().Format(time.RFC3339)})
		return
	}
	b, err := os.ReadFile(setupStateFile)
	if err != nil { writeJSON(w,http.StatusOK,SetupState{State:"ready",Message:"Pronto para configurar.",Updated:time.Now().UTC().Format(time.RFC3339)}); return }
	var st SetupState
	if json.Unmarshal(b,&st)!=nil { writeJSON(w,http.StatusOK,SetupState{State:"ready",Message:"Pronto para configurar.",Updated:time.Now().UTC().Format(time.RFC3339)}); return }
	writeJSON(w,http.StatusOK,st)
}

func wifiInterface() string {
	b,err:=exec.Command("nmcli","-t","-f","DEVICE,TYPE","device","status").Output(); if err!=nil{return ""}
	for _,line:=range strings.Split(string(b),"\n"){p:=strings.SplitN(strings.TrimSpace(line),":",2); if len(p)==2&&p[1]=="wifi"&&p[0]!=""{return p[0]}}
	return ""
}

func restoreSetupAP(iface string) {
	if iface==""{iface=wifiInterface()}; if iface==""{return}
	exec.Command("rfkill","unblock","wifi").Run(); exec.Command("nmcli","radio","wifi","on").Run()
	if exec.Command("nmcli","--wait","15","connection","up","2PNY-SETUP","ifname",iface).Run()==nil{return}
	exec.Command("nmcli","connection","delete","2PNY-SETUP").Run()
	if exec.Command("nmcli","--wait","15","device","wifi","hotspot","ifname",iface,"con-name","2PNY-SETUP","ssid","2PNY-SETUP","band","bg","channel","6","password","2pnysetup").Run()==nil{
		exec.Command("nmcli","connection","modify","2PNY-SETUP","ipv4.method","shared","ipv4.addresses","10.42.0.1/24","connection.autoconnect","yes","connection.autoconnect-priority","100","connection.mdns","yes").Run()
	}
}

func connectConfiguredWiFi(ssid,password string) error {
	iface:=wifiInterface(); if iface==""{return fmt.Errorf("interface Wi-Fi não encontrada")}
	exec.Command("nmcli","connection","down","2PNY-SETUP").Run(); time.Sleep(800*time.Millisecond)
	exec.Command("nmcli","connection","delete","2PNY-WIFI").Run(); exec.Command("nmcli","device","wifi","rescan","ifname",iface).Run()
	args:=[]string{"--wait","30","device","wifi","connect",ssid,"ifname",iface,"name","2PNY-WIFI"}; if password!=""{args=append(args,"password",password)}
	b,err:=exec.Command("nmcli",args...).CombinedOutput(); if err!=nil{restoreSetupAP(iface); msg:=strings.TrimSpace(string(b)); if msg==""{msg=err.Error()}; return fmt.Errorf("Wi-Fi não conectou: %s",msg)}
	exec.Command("nmcli","connection","modify","2PNY-WIFI","connection.autoconnect","yes","connection.autoconnect-priority","60","connection.mdns","yes").Run()
	return nil
}
'''
marker='func setupHandler(w http.ResponseWriter, r *http.Request) {'
if marker not in s: raise SystemExit('setup handler marker not found')
s=s.replace(marker,helpers+'\n'+marker,1)

new_handler=r'''func setupHandler(w http.ResponseWriter, r *http.Request) {
	setupMu.Lock(); defer setupMu.Unlock()
	if r.Method != http.MethodPost { http.Error(w,"POST required",http.StatusMethodNotAllowed); return }
	var in struct{ Callsign string `json:"callsign"`; DMRID string `json:"dmr_id"`; WiFiSSID string `json:"wifi_ssid"`; WiFiPassword string `json:"wifi_password"`; AdminPassword string `json:"admin_password"` }
	if err:=json.NewDecoder(http.MaxBytesReader(w,r.Body,32<<10)).Decode(&in);err!=nil{writeJSON(w,400,map[string]string{"error":"dados inválidos"});return}
	in.Callsign=strings.ToUpper(strings.TrimSpace(in.Callsign)); in.DMRID=strings.TrimSpace(in.DMRID); in.WiFiSSID=strings.TrimSpace(in.WiFiSSID)
	if !callsignRx.MatchString(in.Callsign){writeJSON(w,400,map[string]string{"error":"indicativo inválido"});return}
	if !dmrRx.MatchString(in.DMRID){writeJSON(w,400,map[string]string{"error":"DMR ID inválido"});return}
	if len(in.AdminPassword)<10{writeJSON(w,400,map[string]string{"error":"a senha do painel deve ter pelo menos 10 caracteres"});return}
	if err:=os.MkdirAll(dataDir,0750);err!=nil{writeJSON(w,500,map[string]string{"error":"falha ao preparar armazenamento"});return}
	salt:=randomHex(16); cfg:=Config{Callsign:in.Callsign,DMRID:in.DMRID,WiFiSSID:in.WiFiSSID,AdminHash:hashPassword(in.AdminPassword,salt),AdminSalt:salt,CreatedAt:time.Now().UTC().Format(time.RFC3339)}
	raw,_:=json.MarshalIndent(cfg,"","  "); tmp:=configFile+".tmp"; if err:=os.WriteFile(tmp,raw,0600);err!=nil{writeJSON(w,500,map[string]string{"error":"não foi possível salvar"});return}; if err:=os.Rename(tmp,configFile);err!=nil{writeJSON(w,500,map[string]string{"error":"não foi possível finalizar configuração"});return}
	if in.WiFiSSID!=""{
		writeSetupState("connecting","Dados salvos. Preparando a conexão Wi-Fi...")
		writeJSON(w,http.StatusAccepted,map[string]any{"ok":true,"transitioning":true,"message":"Dados salvos. Conectando ao Wi-Fi.","next":"http://2pny.local","wait_seconds":25})
		ssid,password:=in.WiFiSSID,in.WiFiPassword
		go func(){
			time.Sleep(4*time.Second); writeSetupState("connecting","Conectando ao Wi-Fi...")
			if err:=connectConfiguredWiFi(ssid,password);err!=nil{_ = os.Remove(provisionedFile); _ = os.WriteFile(filepath.Join(dataDir,"last-setup-error"),[]byte(err.Error()+"\n"),0600); writeSetupState("error","Não foi possível conectar. O 2PNY-SETUP foi restaurado para corrigir a rede ou a senha."); log.Printf("setup Wi-Fi failed: %v",err); return}
			writeSetupState("connected","Wi-Fi conectado. Finalizando e abrindo o painel..."); _ = os.Remove(filepath.Join(dataDir,"last-setup-error"))
			if err:=os.WriteFile(provisionedFile,[]byte(time.Now().UTC().Format(time.RFC3339)+"\n"),0600);err!=nil{writeSetupState("error","Wi-Fi conectou, mas a configuração não pôde ser finalizada."); restoreSetupAP(""); return}
			exec.Command("systemctl","restart","avahi-daemon.service").Run()
		}(); return
	}
	writeSetupState("connected","Configuração concluída pela Ethernet.")
	if err:=os.WriteFile(provisionedFile,[]byte(time.Now().UTC().Format(time.RFC3339)+"\n"),0600);err!=nil{writeJSON(w,500,map[string]string{"error":"não foi possível concluir"});return}
	writeJSON(w,200,map[string]any{"ok":true,"message":"Configuração inicial concluída.","next":"http://2pny.local","direct":"http://169.254.2.1"})
}'''
pat=re.compile(r'func setupHandler\(w http\.ResponseWriter, r \*http\.Request\) \{.*?\n\}\n\nfunc fileExists',re.S)
if not pat.search(s): raise SystemExit('setup handler block not found')
s=pat.sub(new_handler+'\n\nfunc fileExists',s,count=1)

route='http.HandleFunc("/api/setup", setupHandler)'
s=s.replace(route,route+'\n\thttp.HandleFunc("/api/setup-status", setupStatusHandler)',1)

start=s.find('async function save(){'); end=s.find('\nboot();',start)
if start<0 or end<0: raise SystemExit('save js not found')
js=r'''async function probeSetup(){let u=['/api/setup-status','http://2pny.local/api/setup-status'];for(let x of u){try{let r=await fetch(x,{cache:'no-store',mode:'cors'});if(r.ok)return await r.json()}catch(e){}}return null}
function waitms(ms){return new Promise(r=>setTimeout(r,ms))}
async function watchSetup(){let m=document.getElementById('msg'),deadline=Date.now()+120000;while(Date.now()<deadline){let s=await probeSetup();if(s&&s.state==='connected'){m.className='ok';m.innerHTML='<b>✓ Conectado.</b><br>Wi-Fi conectado com sucesso.<br><b>Abrindo o painel automaticamente...</b>';await waitms(1500);window.location.href='http://2pny.local/';return}if(s&&s.state==='error'){m.className='err';m.innerHTML='<b>Não conectou.</b><br>'+s.message+'<br><br>Reconecte em <b>2PNY-SETUP</b> e tente novamente.';return}m.className='ok';m.innerHTML='<b>Conectando...</b><br>'+((s&&s.message)||'Aguardando a conexão Wi-Fi...')+'<br><small>Esta tela muda automaticamente quando terminar.</small>';await waitms(1200)}m.className='err';m.innerHTML='<b>A conexão está demorando.</b><br>Procure novamente <b>2PNY-SETUP</b> e confira a senha do Wi-Fi.'}
async function save(){let m=document.getElementById('msg');m.className='';m.innerHTML='<b>Salvando...</b><br>Gravando os dados no 2PNY.';let body={callsign:callsign.value,dmr_id:dmrid.value,wifi_ssid:ssid.value,wifi_password:wpass.value,admin_password:apass.value};try{let r=await fetch('/api/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});let j=await r.json().catch(()=>({error:'falha inesperada'}));if(!r.ok){m.className='err';m.textContent=j.error||'Erro ao configurar.';return}if(j.transitioning){m.className='ok';m.innerHTML='<b>Dados salvos ✓</b><br>Conectando ao Wi-Fi...';watchSetup();return}m.className='ok';m.innerHTML='<b>Conectado ✓</b><br>'+j.message+'<br><b>Abrindo o painel...</b>';setTimeout(()=>window.location.href='http://2pny.local/',1200)}catch(e){m.className='err';m.textContent='A conexão caiu antes da confirmação. Reconecte em 2PNY-SETUP e tente novamente.'}}'''
s=s[:start]+js+s[end:]

s=s.replace('Endereços de emergência: http://2pny.local e http://10.42.0.1 durante o modo de configuração.','A tela acompanha a conexão automaticamente. Wi-Fi de configuração: http://10.42.0.1 • cabo direto: http://169.254.2.1')
p.write_text(s)

# Validation.
v=root/'builder/validate-source.sh'; vs=v.read_text()
vs += '''\ngrep -q 'setupStatusHandler' src/2pnyd/main.go\ngrep -q '/api/setup-status' src/2pnyd/main.go\ngrep -q 'Abrindo o painel automaticamente' src/2pnyd/main.go\ngrep -q '169.254.2.1/16' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet.nmconnection\n'''
v.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
chmod +x builder/build-image.sh builder/validate-source.sh rootfs-overlay/usr/local/sbin/2pny-firstboot rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity

echo "2PNY 0.1.3 live setup status, automatic transition and direct Ethernet fallback applied"
