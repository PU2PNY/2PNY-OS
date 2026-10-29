package main

import (
	"context"
	"encoding/json"
	"net/http"
	"os/exec"
	"sync"
	"time"
)

var reset502Mu sync.Mutex

func reset502Handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost || !sameOrigin(r) || !fileExists(provisionedFile) {
		http.Error(w, "request rejected", http.StatusForbidden); return
	}
	var in struct { Confirmation string `json:"confirmation"` }
	if json.NewDecoder(http.MaxBytesReader(w,r.Body,1024)).Decode(&in) != nil || in.Confirmation != "RESET MMDVM" {
		http.Error(w,"explicit confirmation required",http.StatusBadRequest); return
	}
	if !reset502Mu.TryLock() { http.Error(w,"reset in progress",http.StatusConflict); return }
	defer reset502Mu.Unlock()
	result, err := runPrivilegedRequest("2pny-reset-mmdvm.service", "/run/2pny/reset-mmdvm-request.json", "/run/2pny/reset-mmdvm-result.json", map[string]any{"action":"reset-mmdvm"})
	if err != nil { writeJSON(w,http.StatusConflict,map[string]any{"ok":false,"error":err.Error(),"result":result}); return }
	writeJSON(w,http.StatusOK,result)
}

func diagnostic502Handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet { http.Error(w,"GET required",405); return }
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()
	data, err := exec.CommandContext(ctx,"/usr/bin/python3","/usr/local/libexec/pu2pny/diagnostics-502.py").Output()
	if err != nil || !json.Valid(data) { writeJSON(w,503,map[string]any{"ok":false,"error":"diagnostic_unavailable"}); return }
	w.Header().Set("Content-Type","application/json; charset=utf-8")
	w.Header().Set("Cache-Control","no-store")
	w.Header().Set("Content-Disposition","attachment; filename=pu2pny-5.02-diagnostico.json")
	w.Write(data)
}
