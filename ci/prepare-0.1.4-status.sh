#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
p=Path('src/2pnyd/main.go')
s=p.read_text()

# Add a small persistent setup-state API. No Wi-Fi password is stored here.
marker='func setupHandler(w http.ResponseWriter, r *http.Request) {'
status_code=r'''
const setupStateFile = "/var/lib/2pny/setup-state.json"

type SetupState struct {
	State   string `json:"state"`
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
		writeJSON(w, http.StatusOK, SetupState{State: "connected", Message: "Conectado. Abrindo o painel.", Updated: time.Now().UTC().Format(time.RFC3339)})
		return
	}
	b, err := os.ReadFile(setupStateFile)
	if err != nil {
		writeJSON(w, http.StatusOK, SetupState{State: "ready", Message: "Pronto para configurar.", Updated: time.Now().UTC().Format(time.RFC3339)})
		return
	}
	var st SetupState
	if json.Unmarshal(b, &st) != nil {
		writeJSON(w, http.StatusOK, SetupState{State: "ready", Message: "Pronto para configurar.", Updated: time.Now().UTC().Format(time.RFC3339)})
		return
	}
	writeJSON(w, http.StatusOK, st)
}

'''
if 'func setupStatusHandler(' not in s:
    if marker not in s:
        raise SystemExit('setup handler marker not found')
    s=s.replace(marker,status_code+marker,1)

# Mark the live state before the browser is released from the setup AP.
old='''\t\tssid, password := in.WiFiSSID, in.WiFiPassword
\t\tgo func() {
\t\t\ttime.Sleep(4 * time.Second)
\t\t\tif err := connectConfiguredWiFi(ssid, password); err != nil {
\t\t\t\t_ = os.Remove(provisionedFile)
\t\t\t\t_ = os.WriteFile(filepath.Join(dataDir, "last-setup-error"), []byte(err.Error()+"\\n"), 0600)
\t\t\t\tlog.Printf("setup Wi-Fi failed: %v; setup AP restored", err)
\t\t\t\treturn
\t\t\t}
\t\t\t_ = os.Remove(filepath.Join(dataDir, "last-setup-error"))
\t\t\tif err := os.WriteFile(provisionedFile, []byte(time.Now().UTC().Format(time.RFC3339)+"\\n"), 0600); err != nil {
\t\t\t\tlog.Printf("cannot mark provisioning complete: %v", err)
\t\t\t\trestoreSetupAP("")
\t\t\t\treturn
\t\t\t}
\t\t\texec.Command("systemctl", "restart", "avahi-daemon.service").Run()
\t\t\tlog.Printf("setup complete; joined Wi-Fi SSID=%q", ssid)
\t\t}()
'''
new='''\t\tssid, password := in.WiFiSSID, in.WiFiPassword
\t\twriteSetupState("connecting", "Dados salvos. Preparando a conexão Wi-Fi...")
\t\tgo func() {
\t\t\ttime.Sleep(4 * time.Second)
\t\t\twriteSetupState("connecting", "Conectando ao Wi-Fi...")
\t\t\tif err := connectConfiguredWiFi(ssid, password); err != nil {
\t\t\t\t_ = os.Remove(provisionedFile)
\t\t\t\t_ = os.WriteFile(filepath.Join(dataDir, "last-setup-error"), []byte(err.Error()+"\\n"), 0600)
\t\t\t\twriteSetupState("error", "Não foi possível conectar. O 2PNY-SETUP foi restaurado para você corrigir a rede ou a senha.")
\t\t\t\tlog.Printf("setup Wi-Fi failed: %v; setup AP restored", err)
\t\t\t\treturn
\t\t\t}
\t\t\twriteSetupState("connected", "Wi-Fi conectado. Finalizando e abrindo o painel...")
\t\t\t_ = os.Remove(filepath.Join(dataDir, "last-setup-error"))
\t\t\tif err := os.WriteFile(provisionedFile, []byte(time.Now().UTC().Format(time.RFC3339)+"\\n"), 0600); err != nil {
\t\t\t\twriteSetupState("error", "Wi-Fi conectou, mas a configuração não pôde ser finalizada. O 2PNY-SETUP será restaurado.")
\t\t\t\tlog.Printf("cannot mark provisioning complete: %v", err)
\t\t\t\trestoreSetupAP("")
\t\t\t\treturn
\t\t\t}
\t\t\texec.Command("systemctl", "restart", "avahi-daemon.service").Run()
\t\t\tlog.Printf("setup complete; joined Wi-Fi SSID=%q", ssid)
\t\t}()
'''
if old not in s:
    raise SystemExit('async Wi-Fi handoff anchor not found')
s=s.replace(old,new,1)

# Ethernet-only setup is immediately connected.
eth='''\tif err := os.WriteFile(provisionedFile, []byte(time.Now().UTC().Format(time.RFC3339)+"\\n"), 0600); err != nil {'''
if eth in s and 'writeSetupState("connected", "Configuração concluída pela Ethernet.")' not in s:
    s=s.replace(eth,'\twriteSetupState("connected", "Configuração concluída pela Ethernet.")\n'+eth,1)

# Add endpoint route.
route='http.HandleFunc("/api/setup", setupHandler)'
if 'http.HandleFunc("/api/setup-status", setupStatusHandler)' not in s:
    s=s.replace(route,route+'\n\thttp.HandleFunc("/api/setup-status", setupStatusHandler)',1)

# Replace the first-access save UX with real-time state and automatic transition.
start=s.find('async function save(){')
end=s.find('\nboot();', start)
if start < 0 or end < 0:
    raise SystemExit('save() JavaScript block not found')
js=r'''async function probeSetup(){
 let urls=['/api/setup-status','http://2pny.local/api/setup-status'];
 for(let u of urls){try{let r=await fetch(u,{cache:'no-store',mode:'cors'});if(r.ok)return await r.json()}catch(e){}}
 return null
}
function waitms(ms){return new Promise(r=>setTimeout(r,ms))}
async function watchSetup(){
 let m=document.getElementById('msg'),deadline=Date.now()+120000,last='';
 while(Date.now()<deadline){
  let s=await probeSetup();
  if(s&&s.state){
   if(s.state==='connected'){
    m.className='ok';m.innerHTML='<b>✓ Conectado.</b><br>Wi-Fi conectado com sucesso.<br><b>Abrindo o painel automaticamente...</b>';
    await waitms(1500);window.location.href='http://2pny.local/';return
   }
   if(s.state==='error'){
    m.className='err';m.innerHTML='<b>Não conectou.</b><br>'+(s.message||'Revise a rede e a senha.')+'<br><br>Reconecte em <b>2PNY-SETUP</b> e tente novamente.';return
   }
   if(s.state!==last){m.className='ok';m.innerHTML='<b>Conectando...</b><br>'+(s.message||'Preparando a rede Wi-Fi...')+'<br><small>Esta tela muda automaticamente quando a conexão terminar.</small>';last=s.state}
  }else{
   m.className='ok';m.innerHTML='<b>Conectando...</b><br>O 2PNY-SETUP pode desaparecer durante a troca para sua rede normal.<br><small>Se o notebook voltar automaticamente ao seu Wi-Fi, esta tela localizará o 2PNY e abrirá o painel.</small>'
  }
  await waitms(1200)
 }
 m.className='err';m.innerHTML='<b>A conexão está demorando.</b><br>Procure novamente <b>2PNY-SETUP</b>. Se ele reapareceu, confira a senha do Wi-Fi e tente outra vez.'
}
async function save(){
 let m=document.getElementById('msg');m.className='';m.innerHTML='<b>Salvando...</b><br>Gravando os dados no 2PNY.';
 let body={callsign:callsign.value,dmr_id:dmrid.value,wifi_ssid:ssid.value,wifi_password:wpass.value,admin_password:apass.value};
 try{
  let r=await fetch('/api/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  let j=await r.json().catch(()=>({error:'falha inesperada'}));
  if(!r.ok){m.className='err';m.textContent=j.error||'Erro ao configurar.';return}
  if(j.transitioning){m.className='ok';m.innerHTML='<b>Dados salvos ✓</b><br>Conectando ao Wi-Fi...';watchSetup();return}
  m.className='ok';m.innerHTML='<b>Conectado ✓</b><br>'+j.message+'<br><b>Abrindo o painel...</b>';setTimeout(()=>window.location.href='http://2pny.local/',1200)
 }catch(e){m.className='err';m.textContent='A conexão com o 2PNY caiu antes da confirmação. Reconecte em 2PNY-SETUP e tente novamente.'}
}'''
s=s[:start]+js+s[end:]

p.write_text(s)

# Make CI fail if the live status/auto transition disappears later.
v=Path('builder/validate-source.sh')
vs=v.read_text()
checks="""
grep -q 'setupStatusHandler' src/2pnyd/main.go
grep -q '/api/setup-status' src/2pnyd/main.go
grep -q 'Conectando ao Wi-Fi' src/2pnyd/main.go
grep -q 'Abrindo o painel automaticamente' src/2pnyd/main.go
"""
if "grep -q 'setupStatusHandler' src/2pnyd/main.go" not in vs:
    vs += checks
v.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
chmod +x builder/validate-source.sh

echo "2PNY 0.1.4 live connection status and automatic dashboard transition applied"
