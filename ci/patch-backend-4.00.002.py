#!/usr/bin/env python3
"""PU2PNY-OS 4.00.002 backend overlay.

Adds only local display/Helix control surfaces. RF, protocol, gateway, network,
wizard and live contracts continue to come from the protected 4.00.001 chain.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 3:
    raise SystemExit("usage: patch-backend-4.00.002.py <input-go> <output-go>")

repo = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
base = repo / "ci/patch-backend-4.00.001.py"

with tempfile.TemporaryDirectory(prefix="pu2pny-400002-") as td:
    staged = Path(td) / "main.go"
    subprocess.run([sys.executable, str(base), str(src), str(staged)], check=True)
    text = staged.read_text()

old_version = 'appVersion            = "4.00.001"'
if text.count(old_version) != 1:
    raise SystemExit("4.00.001 appVersion anchor missing/ambiguous")
text = text.replace(old_version, 'appVersion            = "4.00.002"', 1)

main_anchor = "func main() {\n"
if text.count(main_anchor) != 1:
    raise SystemExit("main anchor missing/ambiguous")

handlers = r'''func runLocalJSONHelper400002(w http.ResponseWriter, r *http.Request, helper string) {
	var args []string
	var body []byte
	switch r.Method {
	case http.MethodGet:
		args = []string{"status"}
	case http.MethodPost:
		var err error
		body, err = io.ReadAll(io.LimitReader(r.Body, 64*1024))
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "request_read_failed"})
			return
		}
		if len(bytes.TrimSpace(body)) == 0 || !json.Valid(body) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "invalid_json"})
			return
		}
		args = []string{"apply"}
	default:
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
		return
	}

	cmd := exec.Command(helper, args...)
	if len(body) > 0 {
		cmd.Stdin = bytes.NewReader(body)
	}
	output, err := cmd.CombinedOutput()
	trimmed := bytes.TrimSpace(output)
	if err != nil {
		if json.Valid(trimmed) {
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
			w.Header().Set("Cache-Control", "no-store")
			w.WriteHeader(http.StatusConflict)
			_, _ = w.Write(trimmed)
			return
		}
		writeJSON(w, http.StatusConflict, map[string]any{"ok": false, "error": "helper_failed", "detail": strings.TrimSpace(string(output))})
		return
	}
	if !json.Valid(trimmed) {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"ok": false, "error": "invalid_helper_response"})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(trimmed)
}

func displayConfig400002Handler(w http.ResponseWriter, r *http.Request) {
	runLocalJSONHelper400002(w, r, "/usr/local/sbin/2pny-display-config")
}

func helix400002Handler(w http.ResponseWriter, r *http.Request) {
	runLocalJSONHelper400002(w, r, "/usr/local/sbin/2pny-helix-mode")
}

func helixPage400002Handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	http.ServeFile(w, r, "/usr/share/2pny/helix.html")
}

'''
text = text.replace(main_anchor, handlers + main_anchor, 1)

route_anchor = '\thttp.HandleFunc("/api/capabilities", capabilitiesHandler)\n'
if text.count(route_anchor) != 1:
    raise SystemExit("capabilities route anchor missing/ambiguous")
text = text.replace(
    route_anchor,
    route_anchor
    + '\thttp.HandleFunc("/api/display/config", displayConfig400002Handler)\n'
    + '\thttp.HandleFunc("/api/helix", helix400002Handler)\n'
    + '\thttp.HandleFunc("/helix", helixPage400002Handler)\n',
    1,
)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text)
print("PATCH_BACKEND_400002_OK")
