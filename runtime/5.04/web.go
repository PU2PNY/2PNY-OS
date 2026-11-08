package main

import (
	"context"
	"encoding/json"
	"net/http"
	"os/exec"
	"regexp"
	"strings"
	"time"
)

var expertIDRx = regexp.MustCompile(`^[a-z]{3,12}$`)

// IDENTITY-054: narrow endpoint that only changes callsign and DMR ID.
func identity504Handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost || !sameOrigin(r) || !fileExists(provisionedFile) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	var in struct {
		Callsign string `json:"callsign"`
		DMRID    string `json:"dmr_id"`
	}
	if json.NewDecoder(http.MaxBytesReader(w, r.Body, 2048)).Decode(&in) != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "pedido inválido"})
		return
	}
	in.Callsign = strings.ToUpper(strings.TrimSpace(in.Callsign))
	in.DMRID = strings.TrimSpace(in.DMRID)
	if !callsignRx.MatchString(in.Callsign) {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "indicativo inválido"})
		return
	}
	if !dmrRx.MatchString(in.DMRID) {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "DMR ID inválido (6 a 9 dígitos)"})
		return
	}
	if !applyMu.TryLock() {
		writeJSON(w, http.StatusConflict, map[string]any{"ok": false, "error": "outra configuração está em andamento"})
		return
	}
	writeRFApplyState("applying", "Alterando indicativo e DMR ID...")
	go func(call, id string) {
		defer applyMu.Unlock()
		ctx, cancel := context.WithTimeout(context.Background(), 150*time.Second)
		defer cancel()
		out, err := exec.CommandContext(ctx, "/usr/local/sbin/2pny-identity-apply", call, id).CombinedOutput()
		var res struct {
			OK      bool   `json:"ok"`
			Error   string `json:"error"`
			Message string `json:"message"`
		}
		_ = json.Unmarshal(out, &res)
		if err != nil || !res.OK {
			msg := res.Error
			if msg == "" {
				msg = strings.TrimSpace(string(out))
			}
			if msg == "" && err != nil {
				msg = err.Error()
			}
			writeRFApplyState("error", msg)
			return
		}
		_ = exec.Command("systemctl", "restart", "avahi-daemon.service").Run()
		msg := res.Message
		if msg == "" {
			msg = "Indicativo e DMR ID alterados."
		}
		writeRFApplyState("applied", msg)
	}(in.Callsign, in.DMRID)
	writeJSON(w, http.StatusAccepted, map[string]any{"ok": true, "state": "applying"})
}

// EXPERT-054: list and run fixed read-only diagnostics; the request never carries a command line.
func expert504Handler(w http.ResponseWriter, r *http.Request) {
	if !fileExists(provisionedFile) || (r.Method != http.MethodGet && (r.Method != http.MethodPost || !sameOrigin(r))) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	arg := "list"
	if r.Method == http.MethodPost {
		var in struct {
			ID string `json:"id"`
		}
		if json.NewDecoder(http.MaxBytesReader(w, r.Body, 512)).Decode(&in) != nil || !expertIDRx.MatchString(in.ID) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "comando inválido"})
			return
		}
		arg = in.ID
	}
	ctx, cancel := context.WithTimeout(r.Context(), 120*time.Second)
	defer cancel()
	data, _ := exec.CommandContext(ctx, "/usr/bin/python3", "/usr/local/libexec/pu2pny/expert-cmd-504.py", arg).Output()
	if !json.Valid(data) {
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok": false, "error": "diagnóstico indisponível"})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(data)
}
