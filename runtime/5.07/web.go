package main

import (
	"os/exec"
	"strings"
	"sync"
	"time"
)

// SPEED-057: /api/dashboard forked `systemctl is-active` eleven times per call. On a single-core Pi Zero,
// several open pages made the Expert/Live cards time out. One batched call, kept for 3 s, answers all of them.
// Only the read-only dashboard uses this; handlers that wait for a state change keep the live serviceActive.
var (
	svcCacheMu sync.Mutex
	svcCacheAt time.Time
	svcCache   = map[string]bool{}
	svcUnits   = []string{
		"2pny-mmdvmhost.service", "2pny-dmrgateway.service", "2pny-dstargateway.service", "2pny-ysfgateway.service",
		"2pny-p25gateway.service", "2pny-nxdngateway.service", "2pny-dapnetgateway.service", "2pny-display-core.service",
		"2pny-display.service", "mosquitto.service", "avahi-daemon.service",
	}
)

func serviceActiveCached(name string) bool {
	svcCacheMu.Lock()
	defer svcCacheMu.Unlock()
	if _, known := svcCache[name]; !known {
		return serviceActive(name)
	}
	if time.Since(svcCacheAt) > 3*time.Second {
		out, _ := exec.Command("systemctl", append([]string{"is-active"}, svcUnits...)...).Output()
		lines := strings.Split(strings.TrimSpace(string(out)), "\n")
		for i, unit := range svcUnits {
			svcCache[unit] = i < len(lines) && strings.TrimSpace(lines[i]) == "active"
		}
		svcCacheAt = time.Now()
	}
	return svcCache[name]
}

func init() {
	for _, unit := range svcUnits {
		svcCache[unit] = false
	}
}
