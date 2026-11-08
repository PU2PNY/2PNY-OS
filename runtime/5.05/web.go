package main

import (
	"context"
	"encoding/json"
	"net/http"
	"os"
	"os/exec"
	"time"
)

const oled505File = "/var/lib/2pny/oled.json"

// DISPLAY-055: explicit I2C display type, like the OLED/LCD type choice in Pi-Star and WPSD.
func oled505Handler(w http.ResponseWriter, r *http.Request) {
	if !fileExists(provisionedFile) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	if r.Method == http.MethodGet {
		cfg := map[string]any{"type": "auto"}
		if b, err := os.ReadFile(oled505File); err == nil {
			_ = json.Unmarshal(b, &cfg)
		}
		writeJSON(w, http.StatusOK, cfg)
		return
	}
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	var in struct {
		Type   string `json:"type"`
		Height int    `json:"height"`
		LCD    string `json:"lcd"`
	}
	if json.NewDecoder(http.MaxBytesReader(w, r.Body, 1024)).Decode(&in) != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "pedido inválido"})
		return
	}
	cfg := map[string]any{"type": in.Type}
	switch in.Type {
	case "auto", "none":
	case "ssd1306", "sh1106":
		if in.Height != 32 && in.Height != 64 {
			in.Height = 64
		}
		cfg["height"] = in.Height
	case "lcd":
		cols, rows := 20, 4
		if in.LCD == "16x2" {
			cols, rows = 16, 2
		} else if in.LCD != "20x4" && in.LCD != "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "LCD inválido (16x2 ou 20x4)"})
			return
		}
		cfg["lcd_cols"], cfg["lcd_rows"] = cols, rows
	default:
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "tipo de tela inválido"})
		return
	}
	b, _ := json.Marshal(cfg)
	tmp := oled505File + ".tmp"
	if os.WriteFile(tmp, b, 0644) != nil || os.Rename(tmp, oled505File) != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"ok": false, "error": "não foi possível salvar a escolha"})
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 20*time.Second)
	defer cancel()
	_ = exec.CommandContext(ctx, "systemctl", "restart", "2pny-display-core.service").Run()
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "config": cfg})
}
