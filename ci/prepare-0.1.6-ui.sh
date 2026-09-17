#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path

root = Path('.')

# If MMDVMHost already owns the modem, preserve the last hardware result instead
# of racing the daemon for the UART.
p = root/'rootfs-overlay/usr/local/sbin/2pny-hardware-probe'
s = p.read_text()
old = '''save(state)\n\nmmdvm_real = None\nfor item in state['serial_ports']:'''
new = '''if radio_service_active() and OUT.exists():\n    try:\n        previous = json.loads(OUT.read_text())\n        previous['state'] = 'complete'\n        previous['radio_engine'] = 'active'\n        save(previous)\n        print(json.dumps(previous, ensure_ascii=False))\n        raise SystemExit(0)\n    except (ValueError, OSError):\n        pass\n\nsave(state)\n\nmmdvm_real = None\nfor item in state['serial_ports']:'''
if old not in s:
    raise SystemExit('hardware ownership use anchor not found')
s = s.replace(old, new, 1)
p.write_text(s)

# Add non-blocking RF apply/status API to the existing Go control daemon.
p = root/'src/2pnyd/main.go'
s = p.read_text()
marker = '// 2PNY_RF_ASYNC_API_V1'
if marker not in s:
    anchor = 'func wizardHandler(w http.ResponseWriter, r *http.Request) {'
    if anchor not in s:
        raise SystemExit('RF API insertion anchor not found')
    code = r'''
// 2PNY_RF_ASYNC_API_V1
const rfApplyStateFile = "/var/lib/2pny/rf-apply-state.json"

type RFApplyState struct {
	State   string `json:"state"`
	Message string `json:"message"`
	Updated string `json:"updated"`
}

func writeRFApplyState(state, message string) {
	st := RFApplyState{State: state, Message: message, Updated: time.Now().UTC().Format(time.RFC3339)}
	b, _ := json.Marshal(st)
	_ = os.WriteFile(rfApplyStateFile, b, 0600)
}

func rfStatusHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	b, err := os.ReadFile(rfApplyStateFile)
	if err != nil {
		writeJSON(w, http.StatusOK, RFApplyState{State: "ready", Message: "Aguardando configuração RF.", Updated: time.Now().UTC().Format(time.RFC3339)})
		return
	}
	var st RFApplyState
	if json.Unmarshal(b, &st) != nil {
		writeJSON(w, http.StatusOK, RFApplyState{State: "ready", Message: "Aguardando configuração RF.", Updated: time.Now().UTC().Format(time.RFC3339)})
		return
	}
	writeJSON(w, http.StatusOK, st)
}

func rfApplyHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	if err := r.ParseForm(); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "formulário RF inválido"})
		return
	}
	keys := []string{"rx", "tx", "rx_offset", "tx_offset", "duplex", "port", "callsign", "dmr_id"}
	args := make([]string, 0, len(keys))
	for _, k := range keys {
		v := strings.TrimSpace(r.FormValue(k))
		if v == "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "campo obrigatório: " + k})
			return
		}
		args = append(args, v)
	}
	writeRFApplyState("applying", "Validando RF e iniciando MMDVMHost...")
	go func(values []string) {
		cmd := exec.Command("/usr/local/sbin/2pny-rf-apply", values...)
		out, err := cmd.CombinedOutput()
		msg := strings.TrimSpace(string(out))
		if err != nil {
			if msg == "" { msg = err.Error() }
			writeRFApplyState("error", msg)
			log.Printf("RF apply failed: %v: %s", err, msg)
			return
		}
		if msg == "" { msg = "RF aplicada e MMDVMHost ativo." }
		writeRFApplyState("applied", msg)
	}(append([]string(nil), args...))
	writeJSON(w, http.StatusAccepted, map[string]any{"ok": true, "state": "applying"})
}

'''
    s = s.replace(anchor, code + anchor, 1)

route_anchor = '\thttp.HandleFunc("/api/hardware/scan", hardwareScanHandler)'
if '/api/rf/apply' not in s:
    if route_anchor not in s:
        raise SystemExit('RF route anchor not found')
    s = s.replace(route_anchor, route_anchor + '\n\thttp.HandleFunc("/api/rf", rfStatusHandler)\n\thttp.HandleFunc("/api/rf/apply", rfApplyHandler)', 1)

# Theme-compatible form controls, no external CSS/JS.
css_anchor = '.notice{color:var(--muted)}'
css_extra = '.notice{color:var(--muted)}.formgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.field{display:grid;gap:6px}.field label{font-size:12px;color:var(--muted);font-weight:700}.field input,.field select{width:100%;border:1px solid var(--line);background:var(--panel2);color:var(--txt);border-radius:10px;padding:11px 12px;font:inherit;outline:none}.field input:focus,.field select:focus{border-color:var(--blue);box-shadow:0 0 0 3px color-mix(in srgb,var(--blue) 20%,transparent)}.rfresult{margin-top:14px;padding:12px 14px;border:1px solid var(--line);border-radius:11px;background:var(--panel2)}'
if '.formgrid{' not in s:
    if css_anchor not in s:
        raise SystemExit('RF CSS anchor not found')
    s = s.replace(css_anchor, css_extra, 1)
    s = s.replace('@media(max-width:820px){.app{display:block}', '@media(max-width:820px){.formgrid{grid-template-columns:1fr}.app{display:block}', 1)

old_rf = '<section id="rf" class="hidden"><div class="card"><h2>Etapa 4 — Configuração RF</h2><p class="sub">A MMDVM foi identificada. Esta tela prepara frequência, modo simplex/duplex e offsets; a aplicação segura desses parâmetros entra junto com MMDVMHost/MMDVMCal.</p><div class="rfbox"><b>Próximo módulo técnico</b><p class="notice">RX/TX Frequency • RX/TX Offset • BER • níveis • calibração assistida. Nenhum valor será aplicado até a rotina de validação e rollback estar pronta.</p></div><div class="actions"><button class="btn" onclick="showHW()">← Hardware</button><button class="btn primary" disabled>Salvar RF e continuar</button></div></div></section>'
new_rf = '''<section id="rf" class="hidden"><div class="card"><h2>Etapa 4 — Configuração RF</h2><p class="sub">Informe os parâmetros do hotspot. O 2PNY salva de forma atômica, inicia o MMDVMHost e volta automaticamente ao backup se a validação falhar.</p><div class="formgrid"><div class="field"><label for="rf-rx">Frequência RX (Hz)</label><input id="rf-rx" inputmode="numeric" placeholder="Ex.: 433500000" autocomplete="off"></div><div class="field"><label for="rf-tx">Frequência TX (Hz)</label><input id="rf-tx" inputmode="numeric" placeholder="Ex.: 433500000" autocomplete="off"></div><div class="field"><label for="rf-rxoff">RX Offset (Hz)</label><input id="rf-rxoff" inputmode="numeric" value="0"></div><div class="field"><label for="rf-txoff">TX Offset (Hz)</label><input id="rf-txoff" inputmode="numeric" value="0"></div><div class="field"><label for="rf-duplex">Modo do modem</label><select id="rf-duplex"><option value="0">Simplex</option><option value="1">Duplex</option></select></div><div class="field"><label for="rf-port">Porta MMDVM detectada</label><input id="rf-port" readonly></div><div class="field"><label for="rf-callsign">Indicativo</label><input id="rf-callsign" autocomplete="off" autocapitalize="characters"></div><div class="field"><label for="rf-dmrid">DMR ID</label><input id="rf-dmrid" inputmode="numeric" autocomplete="off"></div></div><div class="rfresult" id="rf-result"><b>Aguardando dados RF.</b><div class="notice">Nesta etapa todos os protocolos e redes continuam desligados; primeiro validamos modem, frequência e estabilidade do MMDVMHost.</div></div><div class="actions"><button class="btn" onclick="showHW()">← Hardware</button><button class="btn primary" id="rf-apply" onclick="applyRF()">Salvar e validar RF</button></div></div></section>'''
if old_rf not in s:
    raise SystemExit('RF wizard section anchor not found')
s = s.replace(old_rf, new_rf, 1)

# Keep detected port synchronized with the RF form.
port_anchor = "$('m-port').textContent=m.port||'—';"
if "$('rf-port').value=m.port||'';" not in s:
    if port_anchor not in s:
        raise SystemExit('RF port JS anchor not found')
    s = s.replace(port_anchor, port_anchor + "$('rf-port').value=m.port||'';", 1)

js_anchor = 'function showRF(){'
if 'async function applyRF()' not in s:
    if js_anchor not in s:
        raise SystemExit('RF JS insertion anchor not found')
    js = r'''async function rfPoll(){let end=Date.now()+15000;while(Date.now()<end){try{let r=await fetch('/api/rf',{cache:'no-store'});if(r.ok){let x=await r.json();if(x.state==='applied'){ $('rf-result').innerHTML='<b>✓ RF validada</b><div class="notice">'+esc(x.message||'MMDVMHost ativo.')+'</div>';$('rf-apply').disabled=false;return}if(x.state==='error'){ $('rf-result').innerHTML='<b>Não foi possível aplicar</b><div class="notice">'+esc(x.message||'Rollback executado.')+'</div>';$('rf-apply').disabled=false;return}}}catch(e){}await new Promise(r=>setTimeout(r,500))}$('rf-result').innerHTML='<b>A validação está demorando</b><div class="notice">O painel continua ativo. Consulte novamente antes de alterar outros parâmetros.</div>';$('rf-apply').disabled=false}async function applyRF(){let data={rx:$('rf-rx').value.trim(),tx:$('rf-tx').value.trim(),rx_offset:$('rf-rxoff').value.trim(),tx_offset:$('rf-txoff').value.trim(),duplex:$('rf-duplex').value,port:$('rf-port').value.trim(),callsign:$('rf-callsign').value.trim().toUpperCase(),dmr_id:$('rf-dmrid').value.trim()};for(let k of Object.keys(data)){if(data[k]===''){ $('rf-result').innerHTML='<b>Preencha todos os campos.</b><div class="notice">Nenhuma alteração foi aplicada.</div>';return}}$('rf-apply').disabled=true;$('rf-result').innerHTML='<b>Aplicando...</b><div class="notice">Salvando, validando a porta MMDVM e iniciando o motor RF.</div>';try{let body=new URLSearchParams(data);let r=await fetch('/api/rf/apply',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});let x=await r.json();if(!r.ok){throw new Error(x.error||'Falha ao iniciar validação RF')}rfPoll()}catch(e){$('rf-result').innerHTML='<b>Falha antes de aplicar</b><div class="notice">'+esc(e.message)+'</div>';$('rf-apply').disabled=false}}'''
    s = s.replace(js_anchor, js + js_anchor, 1)

p.write_text(s)
PY

gofmt_target="$ROOT/src/2pnyd/main.go"
# gofmt is performed by validate-source; keep this patch usable before Go setup too.

echo '2PNY 0.1.6 asynchronous RF wizard applied'
