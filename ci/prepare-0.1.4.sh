#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re

root = Path('.')

# Version bump in image builder.
p = root/'builder/build-image.sh'
s = p.read_text()
s = s.replace('VERSION="${VERSION:-0.1.3-alpha}"','VERSION="${VERSION:-0.1.4-alpha}"')
p.write_text(s)

# Deterministic direct-cable address while keeping normal DHCP.
# Windows APIPA clients use 169.254/16 when no DHCP server exists, so
# 169.254.2.1/16 gives the appliance a documented address without running
# a DHCP server on an unknown LAN.
conn = root/'rootfs-overlay/etc/NetworkManager/system-connections'
eth = conn/'2pny-ethernet.nmconnection'
es = eth.read_text()
if 'address1=169.254.2.1/16' not in es:
    es = es.replace('[ipv4]\nmethod=auto\n', '[ipv4]\nmethod=auto\naddress1=169.254.2.1/16\n', 1)
eth.write_text(es)

# Enforce the emergency address whenever an Ethernet interface is activated.
disp = root/'rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity'
disp.write_text(r'''#!/bin/bash
# 2PNY connectivity event hook. Keep this tiny: it runs inside NetworkManager's dispatcher.
IFACE="${1:-unknown}"
ACTION="${2:-unknown}"
logger -t 2pny-net "interface=${IFACE} action=${ACTION}"

case "$ACTION" in
  up|dhcp4-change)
    if [[ "$(nmcli -g GENERAL.TYPE device show "$IFACE" 2>/dev/null || true)" == "ethernet" ]]; then
      # Keep a deterministic local address in parallel with DHCP.
      # This makes a direct Pi <-> PC cable reachable at http://169.254.2.1
      # while a router can still assign the normal LAN address.
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

# Also enforce it during first boot immediately after Ethernet activation.
fb = root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fs = fb.read_text()
fs = fs.replace('2PNY first boot 0.1.3-alpha', '2PNY first boot 0.1.4-alpha')
anchor = 'echo "Ethernet prepared on ${ETH_IF}; DHCP + link-local fallback"'
if anchor not in fs:
    raise SystemExit('firstboot Ethernet anchor not found')
fs = fs.replace(anchor, 'ip address add 169.254.2.1/16 dev "$ETH_IF" 2>/dev/null || true\n  echo "Ethernet prepared on ${ETH_IF}; DHCP + 169.254.2.1 direct-cable fallback"', 1)
fb.write_text(fs)

# Update backend so the HTTP request completes BEFORE Wi-Fi AP -> client handoff.
p = root/'src/2pnyd/main.go'
s = p.read_text()
s = s.replace('appVersion      = "0.1.3-alpha"','appVersion      = "0.1.4-alpha"')
s = s.replace('<b>Alpha 0.1.3:</b>','<b>Alpha 0.1.4:</b>')

helpers = r'''
func wifiInterface() string {
	b, err := exec.Command("nmcli", "-t", "-f", "DEVICE,TYPE", "device", "status").Output()
	if err != nil {
		return ""
	}
	for _, line := range strings.Split(string(b), "\n") {
		p := strings.SplitN(strings.TrimSpace(line), ":", 2)
		if len(p) == 2 && p[1] == "wifi" && p[0] != "" {
			return p[0]
		}
	}
	return ""
}

func restoreSetupAP(iface string) {
	if iface == "" {
		iface = wifiInterface()
	}
	if iface == "" {
		return
	}
	exec.Command("rfkill", "unblock", "wifi").Run()
	exec.Command("nmcli", "radio", "wifi", "on").Run()
	if err := exec.Command("nmcli", "--wait", "15", "connection", "up", "2PNY-SETUP", "ifname", iface).Run(); err == nil {
		return
	}
	// Last-resort recreation if the saved AP profile was lost.
	exec.Command("nmcli", "connection", "delete", "2PNY-SETUP").Run()
	c := exec.Command("nmcli", "--wait", "15", "device", "wifi", "hotspot", "ifname", iface,
		"con-name", "2PNY-SETUP", "ssid", "2PNY-SETUP", "band", "bg", "channel", "6", "password", "2pnysetup")
	if c.Run() == nil {
		exec.Command("nmcli", "connection", "modify", "2PNY-SETUP", "ipv4.method", "shared",
			"ipv4.addresses", "10.42.0.1/24", "connection.autoconnect", "yes",
			"connection.autoconnect-priority", "100", "connection.mdns", "yes").Run()
	}
}

func connectConfiguredWiFi(ssid, password string) error {
	iface := wifiInterface()
	if iface == "" {
		return fmt.Errorf("interface Wi-Fi não encontrada")
	}

	// The Pi 4 has one Wi-Fi radio. The setup AP and the home Wi-Fi cannot both
	// own the same device, so stop the AP only after the browser already received
	// the setup response.
	exec.Command("nmcli", "connection", "down", "2PNY-SETUP").Run()
	time.Sleep(800 * time.Millisecond)
	exec.Command("nmcli", "connection", "delete", "2PNY-WIFI").Run()
	exec.Command("nmcli", "device", "wifi", "rescan", "ifname", iface).Run()

	args := []string{"--wait", "30", "device", "wifi", "connect", ssid, "ifname", iface, "name", "2PNY-WIFI"}
	if password != "" {
		args = append(args, "password", password)
	}
	cmd := exec.Command("nmcli", args...)
	if b, err := cmd.CombinedOutput(); err != nil {
		restoreSetupAP(iface)
		msg := strings.TrimSpace(string(b))
		if msg == "" {
			msg = err.Error()
		}
		return fmt.Errorf("Wi-Fi não conectou: %s", msg)
	}
	exec.Command("nmcli", "connection", "modify", "2PNY-WIFI",
		"connection.autoconnect", "yes", "connection.autoconnect-priority", "60", "connection.mdns", "yes").Run()
	return nil
}
'''

if 'func wifiInterface() string' not in s:
    marker = 'func setupHandler(w http.ResponseWriter, r *http.Request) {'
    if marker not in s:
        raise SystemExit('setup handler marker not found')
    s = s.replace(marker, helpers + '\n' + marker, 1)

new_handler = r'''func setupHandler(w http.ResponseWriter, r *http.Request) {
	setupMu.Lock()
	defer setupMu.Unlock()
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	var in struct {
		Callsign      string `json:"callsign"`
		DMRID         string `json:"dmr_id"`
		WiFiSSID      string `json:"wifi_ssid"`
		WiFiPassword  string `json:"wifi_password"`
		AdminPassword string `json:"admin_password"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 32<<10)).Decode(&in); err != nil {
		writeJSON(w, 400, map[string]string{"error": "dados inválidos"})
		return
	}
	in.Callsign = strings.ToUpper(strings.TrimSpace(in.Callsign))
	in.DMRID = strings.TrimSpace(in.DMRID)
	in.WiFiSSID = strings.TrimSpace(in.WiFiSSID)
	if !callsignRx.MatchString(in.Callsign) {
		writeJSON(w, 400, map[string]string{"error": "indicativo inválido"})
		return
	}
	if !dmrRx.MatchString(in.DMRID) {
		writeJSON(w, 400, map[string]string{"error": "DMR ID inválido"})
		return
	}
	if len(in.AdminPassword) < 10 {
		writeJSON(w, 400, map[string]string{"error": "a senha do painel deve ter pelo menos 10 caracteres"})
		return
	}
	if err := os.MkdirAll(dataDir, 0750); err != nil {
		writeJSON(w, 500, map[string]string{"error": "falha ao preparar armazenamento"})
		return
	}

	salt := randomHex(16)
	cfg := Config{
		Callsign: in.Callsign, DMRID: in.DMRID, WiFiSSID: in.WiFiSSID,
		AdminHash: hashPassword(in.AdminPassword, salt), AdminSalt: salt,
		CreatedAt: time.Now().UTC().Format(time.RFC3339),
	}
	raw, _ := json.MarshalIndent(cfg, "", "  ")
	tmp := configFile + ".tmp"
	if err := os.WriteFile(tmp, raw, 0600); err != nil {
		writeJSON(w, 500, map[string]string{"error": "não foi possível salvar"})
		return
	}
	if err := os.Rename(tmp, configFile); err != nil {
		writeJSON(w, 500, map[string]string{"error": "não foi possível finalizar configuração"})
		return
	}

	// Critical UX rule: respond while 2PNY-SETUP is still alive. The actual
	// AP -> client transition starts a few seconds later in the background.
	if in.WiFiSSID != "" {
		writeJSON(w, http.StatusAccepted, map[string]any{
			"ok": true,
			"transitioning": true,
			"message": "Dados salvos. Em alguns segundos o 2PNY-SETUP será desligado e o equipamento tentará entrar na sua rede Wi-Fi. A desconexão desta página é esperada.",
			"next": "http://2pny.local",
			"fallback": "http://10.42.0.1",
			"wait_seconds": 25,
		})
		ssid, password := in.WiFiSSID, in.WiFiPassword
		go func() {
			time.Sleep(4 * time.Second)
			if err := connectConfiguredWiFi(ssid, password); err != nil {
				_ = os.Remove(provisionedFile)
				_ = os.WriteFile(filepath.Join(dataDir, "last-setup-error"), []byte(err.Error()+"\n"), 0600)
				log.Printf("setup Wi-Fi failed: %v; setup AP restored", err)
				return
			}
			_ = os.Remove(filepath.Join(dataDir, "last-setup-error"))
			if err := os.WriteFile(provisionedFile, []byte(time.Now().UTC().Format(time.RFC3339)+"\n"), 0600); err != nil {
				log.Printf("cannot mark provisioning complete: %v", err)
				restoreSetupAP("")
				return
			}
			exec.Command("systemctl", "restart", "avahi-daemon.service").Run()
			log.Printf("setup complete; joined Wi-Fi SSID=%q", ssid)
		}()
		return
	}

	// Ethernet-only setup: complete immediately. Ethernet keeps DHCP and also
	// the deterministic 169.254.2.1/16 emergency address for a direct PC cable.
	if err := os.WriteFile(provisionedFile, []byte(time.Now().UTC().Format(time.RFC3339)+"\n"), 0600); err != nil {
		writeJSON(w, 500, map[string]string{"error": "não foi possível concluir"})
		return
	}
	writeJSON(w, 200, map[string]any{
		"ok": true,
		"message": "Configuração inicial concluída. Pelo roteador use 2pny.local; com cabo direto ao computador use 169.254.2.1.",
		"next": "http://2pny.local",
		"direct": "http://169.254.2.1",
	})
}'''

pattern = re.compile(r'func setupHandler\(w http\.ResponseWriter, r \*http\.Request\) \{.*?\n\}\n\nfunc fileExists', re.S)
if not pattern.search(s):
    raise SystemExit('setup handler block not found')
s = pattern.sub(new_handler + '\n\nfunc fileExists', s, count=1)

old_js = "async function save(){let m=document.getElementById('msg');m.className='';m.textContent='Salvando...';let body={callsign:callsign.value,dmr_id:dmrid.value,wifi_ssid:ssid.value,wifi_password:wpass.value,admin_password:apass.value};let r=await fetch('/api/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});let j=await r.json().catch(()=>({error:'falha inesperada'}));if(r.ok){m.className='ok';m.innerHTML='<b>Concluído.</b> '+j.message+'<br>Depois acesse <b>http://2pny.local</b>.'}else{m.className='err';m.textContent=j.error||'Erro ao configurar.'}}"
new_js = "async function save(){let m=document.getElementById('msg');m.className='';m.textContent='Salvando os dados localmente...';let body={callsign:callsign.value,dmr_id:dmrid.value,wifi_ssid:ssid.value,wifi_password:wpass.value,admin_password:apass.value};try{let r=await fetch('/api/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});let j=await r.json().catch(()=>({error:'falha inesperada'}));if(r.ok){m.className='ok';if(j.transitioning){m.innerHTML='<b>Dados salvos.</b><br>'+j.message+'<br><br><b>Aguarde cerca de '+(j.wait_seconds||25)+' segundos.</b> Depois reconecte o notebook à sua rede Wi-Fi normal e abra <b>http://2pny.local</b>.<br>Se a senha do Wi-Fi estiver errada, a rede <b>2PNY-SETUP</b> voltará automaticamente.'}else{m.innerHTML='<b>Concluído.</b> '+j.message+'<br>Endereço normal: <b>http://2pny.local</b><br>Cabo direto: <b>http://169.254.2.1</b>.'}}else{m.className='err';m.textContent=j.error||'Erro ao configurar.'}}catch(e){m.className='err';m.textContent='A conexão caiu antes da confirmação. Aguarde 30 segundos; tente 2pny.local. Se não abrir, procure novamente 2PNY-SETUP.'}}"
if old_js not in s:
    raise SystemExit('save() JavaScript anchor not found')
s = s.replace(old_js, new_js, 1)

s = s.replace('Endereços de emergência: http://2pny.local e http://10.42.0.1 durante o modo de configuração.',
              'Acesso: http://2pny.local • Wi-Fi de configuração: http://10.42.0.1 • cabo direto ao computador: http://169.254.2.1')
p.write_text(s)

(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.4-alpha\n')

# Validation guards: fail the build if the fixes disappear.
p = root/'builder/validate-source.sh'
vs = p.read_text()
extra = r'''
grep -q '169.254.2.1/16' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet.nmconnection
grep -q '169.254.2.1/16' rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity
grep -q 'connectConfiguredWiFi' src/2pnyd/main.go
grep -q 'time.Sleep(4 \* time.Second)' src/2pnyd/main.go
grep -q '2PNY-SETUP.*voltará automaticamente' src/2pnyd/main.go
'''
if "grep -q 'connectConfiguredWiFi' src/2pnyd/main.go" not in vs:
    vs += extra
p.write_text(vs)
PY

chmod +x builder/build-image.sh builder/validate-source.sh \
  rootfs-overlay/usr/local/sbin/2pny-firstboot \
  rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity

echo "2PNY 0.1.4 direct-Ethernet and asynchronous Wi-Fi handoff patch applied"
