#!/usr/bin/env python3
"""Add PU2PNY-OS 4.00.000 capability API without changing RF behavior."""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 3:
    raise SystemExit("usage: patch-backend-4.00.000.py <input.go> <output.go>")
repo = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1])
out = Path(sys.argv[2])

with tempfile.NamedTemporaryFile(prefix="2pny-400000-", suffix=".go", delete=False) as f:
    tmp = Path(f.name)
try:
    subprocess.run([sys.executable, str(repo / "ci/patch-backend-0.3.31.122.py"), str(src), str(tmp)], check=True)
    s = tmp.read_text()
finally:
    tmp.unlink(missing_ok=True)

version_old = 'appVersion            = "0.3.31.122"'
if s.count(version_old) != 1:
    raise SystemExit(f"version anchor count={s.count(version_old)}")
s = s.replace(version_old, 'appVersion            = "4.00.000"', 1)

const_anchor = '\tdisplayOverrideFile   = "/var/lib/2pny/display-override.json"\n'
if s.count(const_anchor) != 1:
    raise SystemExit(f"capabilities const anchor count={s.count(const_anchor)}")
s = s.replace(const_anchor, const_anchor + '\tcapabilitiesFile      = "/run/2pny/capabilities.json"\n', 1)

main_anchor = "func main() {\n"
if s.count(main_anchor) != 1:
    raise SystemExit(f"main anchor count={s.count(main_anchor)}")
handler = r'''func capabilitiesHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	state := readPublicJSON(capabilitiesFile)
	if len(state) == 0 {
		state = map[string]any{
			"schema": 1,
			"os_version": appVersion,
			"state": "unavailable",
			"reason": "capability_snapshot_not_ready",
		}
	}
	writeJSON(w, http.StatusOK, state)
}

'''
s = s.replace(main_anchor, handler + main_anchor, 1)

route_anchor = '\thttp.HandleFunc("/api/hardware", hardwareHandler)\n'
if s.count(route_anchor) != 1:
    raise SystemExit(f"route anchor count={s.count(route_anchor)}")
s = s.replace(route_anchor, route_anchor + '\thttp.HandleFunc("/api/capabilities", capabilitiesHandler)\n', 1)

out.write_text(s)
print("BACKEND_400000_CAPABILITIES_OK")
