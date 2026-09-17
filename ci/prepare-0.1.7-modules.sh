#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

install -m 0755 "$SELF_DIR/../src/2pny-module-status" rootfs-overlay/usr/local/sbin/2pny-module-status

mkdir -p rootfs-overlay/usr/share/2pny
cat > rootfs-overlay/usr/share/2pny/modules.json <<'EOF'
{
  "schema": 1,
  "modules": [
    {"id":"core","integration":"native","license":"2PNY project terms"},
    {"id":"mmdvmhost","integration":"external-service","license":"GPL-2.0","upstream":"https://github.com/g4klx/MMDVM-Host"},
    {"id":"nextion","integration":"native-integration","license":"2PNY implementation"},
    {"id":"direwolf","integration":"external-service","license":"GPL-2.0","upstream":"https://github.com/wb2osz/direwolf"},
    {"id":"dmrgateway","integration":"external-service","license":"GPL-2.0","upstream":"https://github.com/g4klx/DMRGateway"},
    {"id":"m17gateway","integration":"external-service","license":"GPL-2.0","upstream":"https://github.com/M17-Project/M17Gateway"},
    {"id":"openwebrx","integration":"external-application","license":"AGPL-3.0","upstream":"https://github.com/luarvique/openwebrx"}
  ]
}
EOF

python3 - <<'PY'
from pathlib import Path

root = Path('.')

# 0.1.7 is deliberately a read-only module discovery layer. It does not
# enable protocols, transmitters or third-party daemons.
for rel in ['builder/build-image.sh', 'rootfs-overlay/usr/local/sbin/2pny-firstboot', 'src/2pnyd/main.go']:
    p = root / rel
    s = p.read_text()
    s = s.replace('0.1.6-alpha', '0.1.7-alpha').replace('Alpha 0.1.6', 'Alpha 0.1.7')
    p.write_text(s)
(root / 'rootfs-overlay/etc/2pny/version').write_text('0.1.7-alpha\n')

# Add a local read-only API. The helper itself owns module detection so the
# Go daemon stays independent of each third-party implementation.
p = root / 'src/2pnyd/main.go'
s = p.read_text()
marker = '// 2PNY_MODULE_STATUS_API_V1'
if marker not in s:
    anchor = 'func rfStatusHandler(w http.ResponseWriter, r *http.Request) {'
    if anchor not in s:
        raise SystemExit('module API insertion anchor not found')
    code = r'''
// 2PNY_MODULE_STATUS_API_V1
func moduleStatusHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	cmd := exec.Command("/usr/local/sbin/2pny-module-status")
	out, err := cmd.Output()
	if err != nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{
			"schema": 1,
			"error":  "module status unavailable",
		})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(out)
}

'''
    s = s.replace(anchor, code + anchor, 1)

route = '\thttp.HandleFunc("/api/modules", moduleStatusHandler)'
if route not in s:
    anchor = '\thttp.HandleFunc("/api/rf/apply", rfApplyHandler)'
    if anchor not in s:
        raise SystemExit('module route anchor not found')
    s = s.replace(anchor, anchor + '\n' + route, 1)

p.write_text(s)

# Extend source validation instead of weakening previous checks.
p = root / 'builder/validate-source.sh'
vs = p.read_text().replace("grep -q '0.1.6-alpha' src/2pnyd/main.go", "grep -q '0.1.7-alpha' src/2pnyd/main.go")
marker = '# 2PNY_0_1_7_MODULE_SOURCE_CHECK'
if marker not in vs:
    vs += '''\n# 2PNY_0_1_7_MODULE_SOURCE_CHECK\ntest -x rootfs-overlay/usr/local/sbin/2pny-module-status\ntest -s rootfs-overlay/usr/share/2pny/modules.json\npython3 -c 'p="rootfs-overlay/usr/local/sbin/2pny-module-status"; compile(open(p, encoding="utf-8").read(), p, "exec")'\npython3 -m json.tool rootfs-overlay/usr/share/2pny/modules.json >/dev/null\ngrep -q '2PNY_MODULE_STATUS_API_V1' src/2pnyd/main.go\ngrep -q '/api/modules' src/2pnyd/main.go\ngrep -q '0.1.7-alpha' src/2pnyd/main.go\n'''
p.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
chmod 0755 \
  rootfs-overlay/usr/local/sbin/2pny-module-status \
  builder/build-image.sh builder/validate-source.sh rootfs-overlay/usr/local/sbin/2pny-firstboot

python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-module-status
rm -rf rootfs-overlay/usr/local/sbin/__pycache__

echo '2PNY 0.1.7 safe module inventory API applied'
