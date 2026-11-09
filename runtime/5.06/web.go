package main

import (
	"encoding/json"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// CLOCK-056: automatic zone + time from the browser on a Pi without RTC. A zone chosen by hand
// (timezone_source == "manual") always wins and is never overwritten here.
func clock506Handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	var in struct {
		Timezone string `json:"timezone"`
		EpochMS  int64  `json:"epoch_ms"`
	}
	if json.NewDecoder(http.MaxBytesReader(w, r.Body, 1024)).Decode(&in) != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "pedido inválido"})
		return
	}
	clockFile := filepath.Join(dataDir, "settings", "clock.json")
	clock := readPublicJSON(clockFile)
	if src, _ := clock["timezone_source"].(string); src == "manual" {
		writeJSON(w, http.StatusOK, map[string]any{"ok": true, "skipped": "manual"})
		return
	}
	tz := strings.TrimSpace(in.Timezone)
	if tz == "" || strings.Contains(tz, "..") || strings.HasPrefix(tz, "/") || !fileExists(filepath.Join("/usr/share/zoneinfo", tz)) {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "fuso IANA inválido"})
		return
	}
	loc, err := time.LoadLocation(tz)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "fuso desconhecido"})
		return
	}
	out := map[string]any{"ok": true}
	cur, _ := exec.Command("timedatectl", "show", "-p", "Timezone", "--value").Output()
	if strings.TrimSpace(string(cur)) != tz {
		if _, err := runTimezoneRequest(tz); err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]any{"ok": false, "error": "não foi possível aplicar o fuso", "detail": err.Error()})
			return
		}
		out["timezone_applied"] = tz
	}
	syncOut, _ := exec.Command("timedatectl", "show", "-p", "NTPSynchronized", "--value").Output()
	if strings.TrimSpace(string(syncOut)) != "yes" && in.EpochMS > 1704067200000 && in.EpochMS < 4102444800000 {
		drift := time.Since(time.UnixMilli(in.EpochMS))
		if drift < 0 {
			drift = -drift
		}
		if drift > 2*time.Minute {
			local := time.UnixMilli(in.EpochMS).In(loc).Format("2006-01-02T15:04:05")
			if _, err := runClockRequest(local); err != nil {
				out["time_error"] = err.Error()
			} else {
				out["time_set"] = local
			}
			// The helper turns NTP off for a manual set; hand the clock back to NTP.
			_ = exec.Command("timedatectl", "set-ntp", "true").Run()
		}
	}
	_ = os.MkdirAll(filepath.Join(dataDir, "settings"), 0700)
	clock["timezone_source"] = "browser-iana"
	clock["timezone"] = tz
	clock["updated"] = time.Now().UTC().Format(time.RFC3339)
	raw, _ := json.Marshal(clock)
	_ = os.WriteFile(clockFile, raw, 0600)
	writeJSON(w, http.StatusOK, out)
}
