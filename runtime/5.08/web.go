package main

// PU2PNY-OS 5.08: clock state read from files (no timedated activation), Wi-Fi signal from dBm,
// brand assets. Everything here is read-only except the static brand route.

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

// tzFileOutput returns the zone libc really uses, taken from the /etc/localtime link (CLOCK-058).
// `timedatectl show -p Timezone` reads /etc/timezone on Debian and started systemd-timedated on every
// poll of the System page (a single-core Pi Zero paid ~3 s of CPU each time).
func tzFileOutput() ([]byte, error) {
	target, err := filepath.EvalSymlinks("/etc/localtime")
	if err != nil {
		return nil, err
	}
	root, rerr := filepath.EvalSymlinks("/usr/share/zoneinfo")
	if rerr != nil || root == "" {
		root = "/usr/share/zoneinfo"
	}
	if strings.HasPrefix(target, root+"/") {
		return []byte(strings.TrimPrefix(target, root+"/") + "\n"), nil
	}
	return nil, os.ErrNotExist
}

// ntpSyncOutput mirrors NTPSynchronized: systemd-timesyncd touches this file after a successful sync.
func ntpSyncOutput() ([]byte, error) {
	if _, err := os.Stat("/run/systemd/timesync/synchronized"); err == nil {
		return []byte("yes\n"), nil
	}
	return []byte("no\n"), nil
}

// wifiSignalFromRSSI converts dBm to a 1..100 percentage (2*(dBm+100), the usual NetworkManager scale).
func wifiSignalFromRSSI(rssi float64) int {
	v := int(2 * (rssi + 100))
	if v < 1 {
		return 1
	}
	if v > 100 {
		return 100
	}
	return v
}

func init() {
	files := http.FileServer(http.Dir("/usr/share/2pny/brand"))
	http.Handle("/brand/", http.StripPrefix("/brand/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "public, max-age=86400")
		files.ServeHTTP(w, r)
	})))
}
