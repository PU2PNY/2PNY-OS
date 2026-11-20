#!/usr/bin/env python3
"""Rebuild the current backend with the 5.13 maintenance changes."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2]
subprocess.run([sys.executable, str(repo/'ci/prepare-5.11-backend.py'),str(out),arch],check=True)
main = out/'main.go'
source = main.read_text()


def replace(old, new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old,new,1)


replace('appVersion            = "5.11.000"', 'appVersion            = "5.13.002"')
replace('func runTimezoneRequest(tz string)', 'func runTimezoneRequest(tz, action string, dstManual bool, epochMS int64)')
replace('map[string]any{"request_id": requestID, "timezone": tz}', 'map[string]any{"request_id": requestID, "timezone": tz, "action": action, "dst_manual": dstManual, "epoch_ms": epochMS}')
replace('"local": time.Now().Format(time.RFC3339)', '"local": localClock513(tz).Format(time.RFC3339)')
replace('"ntp_synchronized": syncv == "yes"', '"ntp_synchronized": syncv == "yes" && clockSettings["ntp"] != false')

start=source.index('\tcase "auto-time":',source.index('func systemControlHandler('))
end=source.index('\tcase "voice-settings":',start)
replace(source[start:end],'''
	case "auto-time", "initialize-zone", "timezone", "dst-display", "sync-google", "set-time":
		clock513Mu.Lock()
		defer clock513Mu.Unlock()
		var result map[string]any
		var err error
		if in.Action == "set-time" {
			result, err = runClockRequest(strings.TrimSpace(in.LocalTime))
		} else {
			if in.Action == "initialize-zone" && !clock513LocalClient(r) {
				http.Error(w, "request rejected", http.StatusForbidden)
				return
			}
			result, err = runTimezoneRequest(strings.TrimSpace(in.Timezone), in.Action, in.DSTManual, 0)
		}
		if err != nil {
			writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok":false,"error":err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, result)
		return
''')
replace('in.SSID=strings.TrimSpace(in.SSID); in.BSSID=strings.TrimSpace(in.BSSID)', 'in.BSSID=strings.TrimSpace(in.BSSID)')
replace('in.SSID=="" || len(in.SSID)>64 || len(in.Password)>128',
        'strings.TrimSpace(in.SSID)=="" || len(in.SSID)>32 || len(in.Password)>64 || strings.ContainsAny(in.SSID+in.Password,"\\r\\n\\x00")')
replace('Segunda rede salva e pronta para uso.', 'Segunda rede salva para recuperação.')
replace('    payload := map[string]any{"mode":request.Mode,"confirmation":request.Confirmation,"allowed":list}',
        """    if !applyMu.TryLock() {
        writeJSON(w,http.StatusConflict,map[string]any{"ok":false,"error":"outra alteração está em andamento"})
        return
    }
    defer applyMu.Unlock()
    payload := map[string]any{"mode":request.Mode,"confirmation":request.Confirmation,"allowed":list}""")
start=source.index('func captiveAPIHandler(')
end=source.index('func readPublicJSON(',start)
block=source[start:end]
before=block.index('switch r.URL.Path')
end_switch=block.index('\n\tdefault:',before)
success=block[before:end_switch]
replace(block,'''
func captiveAPIHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/captive+json")
    w.Header().Set("Cache-Control", "no-store")
    _ = json.NewEncoder(w).Encode(map[string]any{
        "captive": captive513Request(r),
        "user-portal-url": captive513URL(),
    })
}

func captivePortalHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Cache-Control", "no-store")
    if captive513Request(r) {
        http.Redirect(w, r, captive513URL(), http.StatusFound)
        return
    }
    '''+success+'''
    default:
        http.NotFound(w, r)
    }
}

''')
replace('if fileExists(provisionedFile) {\n\t\t\thttp.Redirect(w, r, "/dashboard", http.StatusFound)', '''
        if captive513Request(r) {
            http.Redirect(w, r, captive513Path(), http.StatusFound)
        } else if fileExists(provisionedFile) {
			http.Redirect(w, r, "/dashboard", http.StatusFound)'''.lstrip('\n').lstrip())
main.write_text(source)

# Replace the obsolete 5.11 expectation of a redirect on every network.
test=out/'web511_test.go'
source=test.read_text()
a=source.index('func Test511CaptiveCanonical')
b=source.index('func Test511MutationsRejectForeignOrigin',a)
test.write_text(source[:a]+source[b:])
for name in ('web513.go','web513_test.go'):
    (out/name).write_bytes((repo/'runtime/5.13'/name).read_bytes())
oled=out/'web505.go'
source=oled.read_text()
replace('LCD    string `json:"lcd"`','LCD    string `json:"lcd"`\n\t\tRotation int `json:"rotation"`')
replace('cfg := map[string]any{"type": in.Type}', '''
	if in.Rotation != 0 && in.Rotation != 180 {
		writeJSON(w,http.StatusBadRequest,map[string]any{"ok":false,"error":"rotação OLED inválida"})
		return
	}
	cfg := map[string]any{"type": in.Type}
	if in.Type == "auto" || in.Type == "ssd1306" || in.Type == "sh1106" {
		cfg["rotation"] = in.Rotation
	}
''')
oled.write_text(source)

# Keep the existing first-access clock endpoint and use the same privileged owner.
(out/'web506.go').write_text("""package main

import (
    "encoding/json"
    "net/http"
    "strings"
)

func clock506Handler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost || !sameOrigin(r) || !clock513LocalClient(r) {
        http.Error(w,"request rejected",http.StatusForbidden)
        return
    }
    var in struct {
        Timezone string `json:"timezone"`
        EpochMS int64 `json:"epoch_ms"`
    }
    if json.NewDecoder(http.MaxBytesReader(w,r.Body,1024)).Decode(&in) != nil {
        http.Error(w,"JSON inválido",http.StatusBadRequest)
        return
    }
    clock513Mu.Lock()
    defer clock513Mu.Unlock()
    result, err := runTimezoneRequest(strings.TrimSpace(in.Timezone),"initialize-zone",false,in.EpochMS)
    if err != nil {
        writeJSON(w,http.StatusServiceUnavailable,map[string]any{"ok":false,"error":err.Error()})
        return
    }
    writeJSON(w,http.StatusOK,result)
}
""")

clock_status = out/'web508.go'
source = clock_status.read_text()
replace('if _, err := os.Stat("/run/systemd/timesync/synchronized"); err == nil {',
        'if _, err := os.Stat("/run/systemd/timesync/synchronized"); err == nil || kernelClockSynced513() {')
clock_status.write_text(source)
