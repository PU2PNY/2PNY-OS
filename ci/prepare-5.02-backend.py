#!/usr/bin/env python3
"""Reconstruct the published backend, then apply only the 5.02 scope."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
base = out/'main.go'
subprocess.run([sys.executable, str(repo/'ci/patch-backend-5.00.000.py'), str(repo/'src/2pnyd-main-0.3.27.go'), str(base)], check=True)
subprocess.run([sys.executable, str(repo/'ci/patch-display-5.00.001.py'), 'go', str(base), str(base)], check=True)
text = base.read_text()
for old, new in (
    ('appVersion            = "5.00.001"', 'appVersion            = "5.02.000"'),
    ('go watchLiveState("/run/2pny/live-state.json")', 'go watchLiveState502("/run/2pny/live-state.json")'),
    ('\t// A manual override allows applying a known Nextion through the modem, but',
     '\t// Never erase real I2C display evidence when the generic enable checkbox is saved.\n'
     '\tif d, ok := h["display"].(map[string]any); ok {\n'
     '\t\tclass, _ := d["class"].(string); address, _ := d["address"].(string)\n'
     '\t\taddress = strings.ToLower(address)\n'
     '\t\tif class == "oled" || class == "lcd" || address == "0x3c" || address == "0x3d" || address == "0x27" || address == "0x3f" { return }\n'
     '\t}\n'
     '\t// A manual override allows applying a known Nextion through the modem, but'),
    ('http.HandleFunc("/api/diagnostics/errors", diagnosticErrorsHandler)',
     'http.HandleFunc("/api/diagnostics/errors", diagnosticErrorsHandler)\n\thttp.HandleFunc("/api/diagnostics/full", diagnostic502Handler)\n\thttp.HandleFunc("/api/expert/reset", reset502Handler)'),
    ('http.Redirect(w, r, "http://10.43.0.1/wizard?captive=1", http.StatusFound)',
     'http.Redirect(w, r, "http://pu2pny.local/wizard?captive=1", http.StatusFound)'),
    ('\tswitch r.URL.Path {\n\tcase "/generate_204", "/gen_204":',
     '\tif apActive() { http.Redirect(w,r,"http://pu2pny.local/internet?captive=1",http.StatusFound); return }\n'
     '\tswitch r.URL.Path {\n\tcase "/generate_204", "/gen_204":')
):
    if text.count(old) != 1:
        raise SystemExit('unexpected baseline anchor: '+old)
    text = text.replace(old, new, 1)
start = text.index('func captiveAPIHandler(w http.ResponseWriter, r *http.Request) {')
end = text.index('\nfunc captivePortalHandler(', start)
text = text[:start]+'''func captiveAPIHandler(w http.ResponseWriter, r *http.Request) {
    provisioned := fileExists(provisionedFile)
    portal := "http://pu2pny.local/internet"
    if !provisioned { portal = "http://pu2pny.local/wizard" }
    w.Header().Set("Content-Type", "application/captive+json")
    w.Header().Set("Cache-Control", "no-store")
    _ = json.NewEncoder(w).Encode(map[string]any{
        "captive": apActive() || !provisioned,
        "user-portal-url": portal,
    })
}
''' + text[end:]
base.write_text(text)
for name in ('api.go', 'live_watch.go'):
    (out/name).write_bytes((repo/'runtime/5.02'/name).read_bytes())
print('PREPARE_502_BACKEND_OK')
