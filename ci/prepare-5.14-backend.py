#!/usr/bin/env python3
"""Rebuild the backend with the 5.14 wizard-unblock changes on top of 5.13.003.

5.14 keeps every 5.13.003 maintenance change and adds only a bounded, honest
first-access path for boards whose protected hardware probe cannot finish in
time (observed on Orange Pi Zero / NanoPi during physical testing). It never
modifies the protected `2pny-hardware-probe` and never fabricates an MMDVM.
"""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2]
subprocess.run([sys.executable, str(repo / 'ci/prepare-5.13.003-backend.py'), str(out), arch], check=True)
main = out / 'main.go'
source = main.read_text()


def replace(old, new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old, new, 1)


# Version badge shown in /api/status and the panel.
replace('appVersion            = "5.13.003"', 'appVersion            = "5.14.000"')

# WIZ-514: shorten the probe wait and, on failure, record the real board model
# and the reason so the wizard shows live data and reaches a terminal state fast
# instead of freezing. The protected probe binary is never touched here.
replace(
'''\t\tcmd := exec.Command("timeout", "-k", "2", "60", "/usr/local/sbin/2pny-hardware-probe")
\t\tif b, err := cmd.CombinedOutput(); err != nil {
\t\t\tmsg := strings.TrimSpace(string(b))
\t\t\tif msg == "" {
\t\t\t\tmsg = err.Error()
\t\t\t}
\t\t\twriteHardwareState("error", "hardware", msg)''',
'''\t\tcmd := exec.Command("timeout", "-k", "2", "30", "/usr/local/sbin/2pny-hardware-probe")
\t\tif b, err := cmd.CombinedOutput(); err != nil {
\t\t\tmsg := strings.TrimSpace(string(b))
\t\t\tif msg == "" {
\t\t\t\tmsg = err.Error()
\t\t\t}
\t\t\twriteHardwareProbeFallback514(msg)
\t\t\twriteHardwareState("error", "hardware", msg)''')

replace(
'func hardwareScanHandler(w http.ResponseWriter, r *http.Request) {',
'''// writeHardwareProbeFallback514 records real board context and the failure
// reason when the protected probe cannot finish, so the wizard shows the board
// model and can offer "continue" instead of staying on "Detectando...". It never
// overwrites a previously confirmed MMDVM and never invents one.
func writeHardwareProbeFallback514(reason string) {
\tif b, err := os.ReadFile(hardwareProbeFile); err == nil {
\t\tvar cur struct {
\t\t\tMMDVM struct {
\t\t\t\tDetected bool `json:"detected"`
\t\t\t} `json:"mmdvm"`
\t\t}
\t\tif json.Unmarshal(b, &cur) == nil && cur.MMDVM.Detected {
\t\t\treturn
\t\t}
\t}
\tmodel := ""
\tif b, err := os.ReadFile("/proc/device-tree/model"); err == nil {
\t\tmodel = strings.TrimRight(strings.ReplaceAll(string(b), "\\x00", ""), "\\n ")
\t}
\tpayload := map[string]any{
\t\t"state":       "complete",
\t\t"raspberry":   map[string]any{"model": model, "serial": ""},
\t\t"mmdvm":       map[string]any{"detected": false, "duplex": "unknown", "capabilities": []string{}},
\t\t"display":     map[string]any{"detected": false, "state": "not_found"},
\t\t"probe_error": reason,
\t\t"updated":     time.Now().UTC().Format(time.RFC3339),
\t}
\tif b, err := json.Marshal(payload); err == nil {
\t\t_ = os.MkdirAll(filepath.Dir(hardwareProbeFile), 0750)
\t\t_ = os.WriteFile(hardwareProbeFile, b, 0600)
\t}
}

func hardwareScanHandler(w http.ResponseWriter, r *http.Request) {''')

main.write_text(source)
print("PREPARE_514_OK", arch)
