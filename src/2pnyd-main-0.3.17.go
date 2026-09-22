package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	dataDir               = "/var/lib/2pny"
	configFile            = "/var/lib/2pny/config.json"
	provisionedFile       = "/var/lib/2pny/provisioned"
	listenAddr            = "0.0.0.0:80"
	appVersion            = "0.3.17-alpha"
	hardwareFile          = "/var/lib/2pny/hardware.json"
	hardwareProbeFile     = "/var/lib/2pny/hardware-probe.json"
	hardwareScanStateFile = "/run/2pny/hardware-scan-state.json"
	rfApplyStateFile      = "/var/lib/2pny/rf-apply-state.json"
	wizardFile            = "/usr/share/2pny/wizard.html"
	dashboardFile         = "/usr/share/2pny/dashboard.html"
	hotspotFile           = "/usr/share/2pny/hotspot.html"
	displayFile           = "/usr/share/2pny/display.html"
	internetFile          = "/usr/share/2pny/internet.html"
	protocolsFile         = "/usr/share/2pny/protocols.html"
	historyFile           = "/usr/share/2pny/history.html"
	aprsFile              = "/usr/share/2pny/aprs.html"
	systemFile            = "/usr/share/2pny/system.html"
	expertFile            = "/usr/share/2pny/expert.html"
	radioIDFile           = "/usr/share/2pny/radioid.html"
	directFile            = "/usr/share/2pny/direct.html"
	wifiScanStateFile     = "/var/lib/2pny/wifi-scan.json"
	wifiCountryFile       = "/var/lib/2pny/wifi-country"
	displayOverrideFile   = "/var/lib/2pny/display-override.json"
)

type Config struct {
	Callsign        string `json:"callsign"`
	DMRID           string `json:"dmr_id"`
	WiFiSSID        string `json:"wifi_ssid,omitempty"`
	UseMode         string `json:"use_mode"`
	RXHz            int64  `json:"rx_hz"`
	TXHz            int64  `json:"tx_hz"`
	RXOffsetHz      int64  `json:"rx_offset_hz"`
	TXOffsetHz      int64  `json:"tx_offset_hz"`
	Protocol        string `json:"protocol"`
	Operation       string `json:"operation"`
	ServerName      string `json:"server_name,omitempty"`
	ServerAddress   string `json:"server_address,omitempty"`
	ServerPort      int    `json:"server_port,omitempty"`
	NetworkKind     string `json:"network_kind,omitempty"`
	ColorCode       int    `json:"color_code,omitempty"`
	DMRSlot         string `json:"dmr_slot,omitempty"`
	XLXModule       string `json:"xlx_module,omitempty"`
	ESSID           string `json:"essid,omitempty"`
	BMAPIConfigured bool   `json:"bm_api_configured,omitempty"`
	NetworkState    string `json:"network_state,omitempty"`
	CreatedAt       string `json:"created_at"`
}

type Status struct {
	Name        string   `json:"name"`
	Version     string   `json:"version"`
	Provisioned bool     `json:"provisioned"`
	Ethernet    bool     `json:"ethernet"`
	WiFi        bool     `json:"wifi"`
	IPv4        []string `json:"ipv4"`
}

type liveEvent struct {
	id   uint64
	data []byte
}

type liveStateHub struct {
	mu          sync.RWMutex
	sequence    uint64
	snapshot    []byte
	subscribers map[chan liveEvent]struct{}
}

var liveHub = &liveStateHub{subscribers: make(map[chan liveEvent]struct{})}
var hostfilesUpdateMu sync.Mutex
var hostfilesUpdating bool

func startHostfilesUpdate() bool {
	hostfilesUpdateMu.Lock()
	if hostfilesUpdating {
		hostfilesUpdateMu.Unlock()
		return false
	}
	hostfilesUpdating = true
	hostfilesUpdateMu.Unlock()
	go func() {
		out, err := exec.Command("/usr/local/sbin/2pny-hostfiles-update").CombinedOutput()
		if err != nil {
			log.Printf("hostfiles update failed: %v: %s", err, strings.TrimSpace(string(out)))
		}
		hostfilesUpdateMu.Lock()
		hostfilesUpdating = false
		hostfilesUpdateMu.Unlock()
	}()
	return true
}

func isHostfilesUpdating() bool {
	hostfilesUpdateMu.Lock()
	defer hostfilesUpdateMu.Unlock()
	return hostfilesUpdating
}

func (h *liveStateHub) publish(data []byte) {
	if len(data) == 0 || !json.Valid(data) {
		return
	}
	h.mu.Lock()
	if bytes.Equal(h.snapshot, data) {
		h.mu.Unlock()
		return
	}
	h.sequence++
	h.snapshot = append(h.snapshot[:0], data...)
	event := liveEvent{id: h.sequence, data: append([]byte(nil), data...)}
	for ch := range h.subscribers {
		select {
		case ch <- event:
		default:
			select {
			case <-ch:
			default:
			}
			select {
			case ch <- event:
			default:
			}
		}
	}
	h.mu.Unlock()
}

func (h *liveStateHub) current() liveEvent {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return liveEvent{id: h.sequence, data: append([]byte(nil), h.snapshot...)}
}

func watchLiveState(path string) {
	var lastMod time.Time
	var lastSize int64 = -1
	for {
		if stat, err := os.Stat(path); err == nil && (stat.ModTime() != lastMod || stat.Size() != lastSize) {
			if data, err := os.ReadFile(path); err == nil {
				liveHub.publish(data)
				lastMod, lastSize = stat.ModTime(), stat.Size()
			}
		}
		time.Sleep(80 * time.Millisecond)
	}
}

type ConnectivityStatus struct {
	Internet          bool     `json:"internet"`
	InternetLatencyMS int64    `json:"internet_latency_ms,omitempty"`
	InternetQuality   string   `json:"internet_quality"`
	DefaultInterface  string   `json:"default_interface,omitempty"`
	Ethernet          bool     `json:"ethernet"`
	EthernetInterface string   `json:"ethernet_interface,omitempty"`
	WiFi              bool     `json:"wifi"`
	WiFiSSID          string   `json:"wifi_ssid"`
	WiFiSignal        int      `json:"wifi_signal,omitempty"`
	WiFiQuality       string   `json:"wifi_quality,omitempty"`
	WiFiRSSIDBm       float64  `json:"wifi_rssi_dbm,omitempty"`
	WiFiInterfaces    []string `json:"wifi_interfaces"`
	WiFiCount         int      `json:"wifi_count"`
	ClientInterface   string   `json:"client_interface,omitempty"`
	APActive          bool     `json:"ap_active"`
	APInterface       string   `json:"ap_interface,omitempty"`
	APSSID            string   `json:"ap_ssid"`
	IPv4              []string `json:"ipv4"`
}

type RFApplyState struct {
	State   string `json:"state"`
	Message string `json:"message"`
	Updated string `json:"updated"`
}

var (
	callsignRx          = regexp.MustCompile(`^[A-Z0-9/-]{3,16}$`)
	dmrRx               = regexp.MustCompile(`^[0-9]{6,9}$`)
	applyMu             sync.Mutex
	hardwareScanMu      sync.Mutex
	hardwareScanning    bool
	wifiScanMu          sync.Mutex
	wifiScanning        bool
	connectivityCacheMu sync.Mutex
	connectivityCache   ConnectivityStatus
	connectivityCacheAt time.Time
	liveCacheMu         sync.Mutex
	liveCache           []byte
	liveCacheAt         time.Time
	cpuSampleMu         sync.Mutex
	cpuPrevTotal        uint64
	cpuPrevIdle         uint64
)

func fileExists(p string) bool { _, e := os.Stat(p); return e == nil }

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func interfaceUp(name string) bool {
	b, err := os.ReadFile(filepath.Join("/sys/class/net", name, "operstate"))
	return err == nil && strings.TrimSpace(string(b)) == "up"
}

func ipv4Addresses() []string {
	var out []string
	ifaces, _ := net.Interfaces()
	for _, i := range ifaces {
		addrs, _ := i.Addrs()
		for _, a := range addrs {
			if ipnet, ok := a.(*net.IPNet); ok && ipnet.IP.To4() != nil && !ipnet.IP.IsLoopback() {
				out = append(out, ipnet.IP.String())
			}
		}
	}
	return out
}

func lanResumeURLs(ips []string) []string {
	seen := map[string]bool{}
	out := []string{"http://pu2pny.local"}
	seen[out[0]] = true
	for _, raw := range ips {
		ip := net.ParseIP(strings.TrimSpace(raw))
		if ip == nil || ip.To4() == nil || ip.IsLoopback() || ip.IsLinkLocalUnicast() {
			continue
		}
		v := ip.String()
		if strings.HasPrefix(v, "10.43.0.") {
			continue
		}
		u := "http://" + v
		if !seen[u] {
			seen[u] = true
			out = append(out, u)
		}
	}
	return out
}

func wifiInterfaces() []string {
	entries, _ := os.ReadDir("/sys/class/net")
	var out []string
	for _, e := range entries {
		name := e.Name()
		if fileExists(filepath.Join("/sys/class/net", name, "wireless")) {
			out = append(out, name)
		}
	}
	return out
}

func currentWiFiLink() (string, string, int, string, float64) {
	iface := ""
	if out, err := exec.Command("nmcli", "-t", "--escape", "no", "-f", "DEVICE,TYPE,STATE", "device", "status").Output(); err == nil {
		for _, line := range strings.Split(string(out), "\n") {
			f := strings.Split(line, ":")
			if len(f) >= 3 && f[1] == "wifi" && strings.HasPrefix(f[2], "connected") {
				iface = strings.TrimSpace(f[0])
				break
			}
		}
	}
	if iface == "" {
		d := defaultRouteInterface()
		if d != "" && fileExists(filepath.Join("/sys/class/net", d, "wireless")) {
			iface = d
		}
	}
	if iface == "" {
		return "", "", 0, "", 0
	}
	ssid := ""
	rssi := float64(0)
	if out, err := exec.Command("iw", "dev", iface, "link").Output(); err == nil {
		for _, raw := range strings.Split(string(out), "\n") {
			line := strings.TrimSpace(raw)
			if strings.HasPrefix(line, "SSID: ") {
				ssid = strings.TrimSpace(strings.TrimPrefix(line, "SSID: "))
			}
			if strings.HasPrefix(line, "signal: ") {
				f := strings.Fields(line)
				if len(f) >= 2 {
					rssi, _ = strconv.ParseFloat(f[1], 64)
				}
			}
		}
	}
	signal := 0
	if out, err := exec.Command("nmcli", "-t", "--escape", "no", "-f", "ACTIVE,SIGNAL", "dev", "wifi", "--rescan", "no").Output(); err == nil {
		for _, line := range strings.Split(string(out), "\n") {
			if strings.HasPrefix(line, "yes:") {
				signal, _ = strconv.Atoi(strings.TrimSpace(strings.TrimPrefix(line, "yes:")))
				break
			}
		}
	}
	if ssid == "" {
		if out, err := exec.Command("nmcli", "-t", "--escape", "no", "-f", "ACTIVE,SSID", "dev", "wifi", "--rescan", "no").Output(); err == nil {
			for _, line := range strings.Split(string(out), "\n") {
				if strings.HasPrefix(line, "yes:") {
					ssid = strings.TrimSpace(strings.TrimPrefix(line, "yes:"))
					break
				}
			}
		}
	}
	quality := ""
	if signal > 0 {
		if signal >= 70 {
			quality = "Ótimo"
		} else if signal >= 45 {
			quality = "Bom"
		} else {
			quality = "Ruim"
		}
	} else if rssi != 0 {
		if rssi >= -60 {
			quality = "Ótimo"
		} else if rssi >= -72 {
			quality = "Bom"
		} else {
			quality = "Ruim"
		}
	}
	return iface, ssid, signal, quality, rssi
}

func ethernetInterface() string {
	entries, _ := os.ReadDir("/sys/class/net")
	for _, e := range entries {
		n := e.Name()
		if n == "lo" {
			continue
		}
		if strings.HasPrefix(n, "eth") || strings.HasPrefix(n, "en") {
			return n
		}
	}
	return ""
}

func readRunFile(name string) string {
	b, err := os.ReadFile(filepath.Join("/run/2pny", name))
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(b))
}

func defaultRouteInterface() string {
	b, err := exec.Command("ip", "-4", "route", "show", "default").Output()
	if err != nil {
		return ""
	}
	fields := strings.Fields(string(b))
	for i := 0; i+1 < len(fields); i++ {
		if fields[i] == "dev" {
			return fields[i+1]
		}
	}
	return ""
}

func internetProbe() (bool, int64, string) {
	best := int64(0)
	for _, addr := range []string{"1.1.1.1:443", "8.8.8.8:53"} {
		started := time.Now()
		conn, err := net.DialTimeout("tcp", addr, 1200*time.Millisecond)
		if err != nil {
			continue
		}
		_ = conn.Close()
		ms := time.Since(started).Milliseconds()
		if ms < 1 {
			ms = 1
		}
		if best == 0 || ms < best {
			best = ms
		}
	}
	if best == 0 {
		return false, 0, "Offline"
	}
	if best < 80 {
		return true, best, "Ótimo"
	}
	if best < 160 {
		return true, best, "Bom"
	}
	return true, best, "Ruim"
}

func apActive() bool {
	// Prefer the process/runtime truth written by network-core.  ap-control can
	// reflect desired state while hostapd is still actually broadcasting.
	runtimeCheck := exec.Command("sh", "-c",
		`test -s /run/2pny/hostapd.pid && kill -0 "$(cat /run/2pny/hostapd.pid)" 2>/dev/null && grep -qx 'hostapd=active' /run/2pny/network-status.txt`)
	if runtimeCheck.Run() == nil {
		return true
	}
	out, err := exec.Command("/usr/local/sbin/2pny-ap-control", "status").Output()
	return err == nil && strings.TrimSpace(string(out)) == "active"
}

func connectivitySnapshot() ConnectivityStatus {
	wifis := wifiInterfaces()
	eth := ethernetInterface()
	client := readRunFile("uplink-iface")
	apif := readRunFile("ap-iface")
	wifiIface, ssid, wifiSignal, wifiQuality, wifiRSSI := currentWiFiLink()
	wifiUp := wifiIface != "" && interfaceUp(wifiIface)
	if client == "" && wifiUp {
		client = wifiIface
	}
	internet, latency, quality := internetProbe()
	return ConnectivityStatus{
		Internet:          internet,
		InternetLatencyMS: latency,
		InternetQuality:   quality,
		DefaultInterface:  defaultRouteInterface(),
		Ethernet:          eth != "" && interfaceUp(eth),
		EthernetInterface: eth,
		WiFi:              wifiUp,
		WiFiSSID:          ssid,
		WiFiSignal:        wifiSignal,
		WiFiQuality:       wifiQuality,
		WiFiRSSIDBm:       wifiRSSI,
		WiFiInterfaces:    wifis,
		WiFiCount:         len(wifis),
		ClientInterface:   client,
		APActive:          apActive(),
		APInterface:       apif,
		APSSID:            "pu2pny",
		IPv4:              ipv4Addresses(),
	}
}

func cachedConnectivitySnapshot() ConnectivityStatus {
	connectivityCacheMu.Lock()
	defer connectivityCacheMu.Unlock()
	if !connectivityCacheAt.IsZero() && time.Since(connectivityCacheAt) < 2*time.Second {
		return connectivityCache
	}
	connectivityCache = connectivitySnapshot()
	connectivityCacheAt = time.Now()
	return connectivityCache
}

func invalidateConnectivityCache() {
	connectivityCacheMu.Lock()
	connectivityCacheAt = time.Time{}
	connectivityCache = ConnectivityStatus{}
	connectivityCacheMu.Unlock()
}

func cpuSample() (uint64, uint64) {
	b, err := os.ReadFile("/proc/stat")
	if err != nil {
		return 0, 0
	}
	line := strings.SplitN(string(b), "\n", 2)[0]
	f := strings.Fields(line)
	if len(f) < 5 || f[0] != "cpu" {
		return 0, 0
	}
	var vals []uint64
	for _, x := range f[1:] {
		n, e := strconv.ParseUint(x, 10, 64)
		if e != nil {
			n = 0
		}
		vals = append(vals, n)
	}
	var total uint64
	for _, n := range vals {
		total += n
	}
	idle := vals[3]
	if len(vals) > 4 {
		idle += vals[4]
	}
	return total, idle
}

func fallbackTelemetry() map[string]any {
	total, idle := cpuSample()
	cpu := 0.0
	cpuSampleMu.Lock()
	if cpuPrevTotal > 0 && total > cpuPrevTotal {
		dt := total - cpuPrevTotal
		di := idle - cpuPrevIdle
		if dt > 0 && di <= dt {
			cpu = 100 * (1 - float64(di)/float64(dt))
		}
	}
	cpuPrevTotal, cpuPrevIdle = total, idle
	cpuSampleMu.Unlock()
	cpu = float64(int(cpu*10+0.5)) / 10
	temp := -1.0
	if b, e := os.ReadFile("/sys/class/thermal/thermal_zone0/temp"); e == nil {
		if n, e2 := strconv.ParseFloat(strings.TrimSpace(string(b)), 64); e2 == nil {
			temp = float64(int((n/1000)*10+0.5)) / 10
		}
	}
	memUsed := int64(0)
	memTotal := int64(0)
	if b, e := os.ReadFile("/proc/meminfo"); e == nil {
		vals := map[string]int64{}
		for _, ln := range strings.Split(string(b), "\n") {
			ff := strings.Fields(ln)
			if len(ff) >= 2 {
				n, _ := strconv.ParseInt(ff[1], 10, 64)
				vals[strings.TrimSuffix(ff[0], ":")] = n
			}
		}
		memTotal = vals["MemTotal"] / 1024
		memUsed = (vals["MemTotal"] - vals["MemAvailable"]) / 1024
	}
	return map[string]any{"cpu_percent": cpu, "temperature": temp, "memory_used_mb": memUsed, "memory_total_mb": memTotal}
}

func mergedTelemetry() map[string]any {
	t := readPublicJSON("/run/2pny/telemetry.json")
	f := fallbackTelemetry()
	for k, v := range f {
		if old, ok := t[k]; !ok || old == nil || old == "" {
			t[k] = v
		}
	}
	return t
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	c := cachedConnectivitySnapshot()
	writeJSON(w, http.StatusOK, Status{
		Name:        "PU2PNY-OS",
		Version:     appVersion,
		Provisioned: fileExists(provisionedFile),
		Ethernet:    c.Ethernet,
		WiFi:        c.WiFi,
		IPv4:        c.IPv4,
	})
}

func connectivityHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	if r.URL.Query().Get("fresh") == "1" {
		invalidateConnectivityCache()
		writeJSON(w, http.StatusOK, connectivitySnapshot())
		return
	}
	writeJSON(w, http.StatusOK, cachedConnectivitySnapshot())
}

func preferredClientWiFi() string {
	iface := readRunFile("uplink-iface")
	if iface != "" && fileExists(filepath.Join("/sys/class/net", iface)) {
		return iface
	}
	apif := readRunFile("ap-iface")
	for _, w := range wifiInterfaces() {
		if w != apif {
			return w
		}
	}
	if apif != "" && fileExists(filepath.Join("/sys/class/net", apif)) {
		return apif
	}
	return ""
}

func writeWiFiScanState(state, message string, networks any) {
	_ = os.MkdirAll(dataDir, 0750)
	payload := map[string]any{
		"state":   state,
		"message": message,
		"updated": time.Now().UTC().Format(time.RFC3339),
	}
	if networks != nil {
		payload["networks"] = networks
	}
	b, _ := json.Marshal(payload)
	_ = os.WriteFile(wifiScanStateFile, b, 0600)
}

func readWiFiScanState() map[string]any {
	st := map[string]any{"state": "idle", "networks": []any{}}
	if b, err := os.ReadFile(wifiScanStateFile); err == nil {
		_ = json.Unmarshal(b, &st)
	}
	return st
}

func startWiFiScan() {
	wifiScanMu.Lock()
	if wifiScanning {
		wifiScanMu.Unlock()
		return
	}
	wifiScanning = true
	wifiScanMu.Unlock()
	writeWiFiScanState("scanning", "Buscando redes Wi-Fi próximas...", nil)
	go func() {
		defer func() {
			wifiScanMu.Lock()
			wifiScanning = false
			wifiScanMu.Unlock()
		}()
		// Give the HTTP response time to leave before a single-radio AP is paused.
		time.Sleep(900 * time.Millisecond)
		out, err := exec.Command("timeout", "-k", "3", "40", "/usr/local/sbin/2pny-network-switch", "scan-json").CombinedOutput()
		if err != nil {
			msg := strings.TrimSpace(string(out))
			if msg == "" {
				msg = "não foi possível buscar redes Wi-Fi"
			}
			writeWiFiScanState("error", msg, []any{})
			return
		}
		var networks []map[string]any
		if err := json.Unmarshal(out, &networks); err != nil {
			writeWiFiScanState("error", "resposta inválida da busca de Wi-Fi", []any{})
			return
		}
		writeWiFiScanState("ready", fmt.Sprintf("%d rede(s) encontrada(s)", len(networks)), networks)
	}()
}

func wifiScanHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	st := readWiFiScanState()
	if r.URL.Query().Get("refresh") == "1" || st["state"] == "idle" {
		// NET-024: every explicit refresh is a new bounded scan. A previously
		// persisted error is not treated as a permanent terminal state.
		writeWiFiScanState("idle", "Nova busca solicitada.", []any{})
		startWiFiScan()
		st = readWiFiScanState()
	}
	writeJSON(w, http.StatusOK, st)
}

func networkCountryHandler(w http.ResponseWriter, r *http.Request) {
	country := "BR"
	if b, err := os.ReadFile(wifiCountryFile); err == nil {
		value := strings.ToUpper(strings.TrimSpace(string(b)))
		if regexp.MustCompile("^[A-Z]{2}$").MatchString(value) {
			country = value
		}
	}
	if r.Method == http.MethodGet {
		writeJSON(w, http.StatusOK, map[string]any{"country": country})
		return
	}
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	var in struct {
		Country string `json:"country"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1024)).Decode(&in); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "país inválido"})
		return
	}
	country = strings.ToUpper(strings.TrimSpace(in.Country))
	if !regexp.MustCompile("^[A-Z]{2}$").MatchString(country) {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "use código ISO de duas letras"})
		return
	}
	if err := os.WriteFile(wifiCountryFile, []byte(country+"\n"), 0600); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"ok": false, "error": "não foi possível salvar o país"})
		return
	}
	_ = exec.Command("iw", "reg", "set", country).Run()
	writeWiFiScanState("idle", "País Wi-Fi atualizado; faça uma nova busca.", []any{})
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "country": country})
}

func writeNetworkConnectState(state, message, ssid string) {
	_ = os.MkdirAll(dataDir, 0750)
	b, _ := json.Marshal(map[string]any{
		"state": state, "message": message, "ssid": ssid,
		"updated": time.Now().UTC().Format(time.RFC3339),
	})
	_ = os.WriteFile(filepath.Join(dataDir, "network-connect.json"), b, 0600)
}

func networkConnectStatusHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	st := map[string]any{"state": "idle"}
	if b, err := os.ReadFile(filepath.Join(dataDir, "network-connect.json")); err == nil {
		_ = json.Unmarshal(b, &st)
	}
	c := connectivitySnapshot()
	if state, _ := st["state"].(string); state == "connected" {
		wanted, _ := st["ssid"].(string)
		if !c.WiFi || (wanted != "" && c.WiFiSSID != wanted) {
			st["state"] = "error"
			st["message"] = "O perfil foi salvo, mas o rádio Wi-Fi não permaneceu conectado ao SSID solicitado. O cabo continua disponível; tente o Wi-Fi novamente."
		}
	}
	st["connectivity"] = c
	st["resume_url"] = "http://pu2pny.local/wizard"
	st["resume_urls"] = lanResumeURLs(c.IPv4)
	st["setup_url"] = "http://10.43.0.1/wizard"
	st["eta_seconds"] = 75
	writeJSON(w, http.StatusOK, st)
}

func networkConnectHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost { http.Error(w, "POST required", http.StatusMethodNotAllowed); return }
	var in struct {
		SSID string `json:"ssid"`
		Password string `json:"password"`
		BSSID string `json:"bssid"`
		KeepAP bool `json:"keep_ap"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 16<<10)).Decode(&in); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false,"error":"dados de rede inválidos"}); return
	}
	in.SSID = strings.TrimSpace(in.SSID); in.BSSID = strings.TrimSpace(in.BSSID)
	if in.SSID == "" { writeJSON(w,400,map[string]any{"ok":false,"error":"selecione uma rede Wi-Fi"}); return }
	if in.BSSID != "" && !regexp.MustCompile("(?i)^([0-9a-f]{2}:){5}[0-9a-f]{2}$").MatchString(in.BSSID) {
		writeJSON(w,400,map[string]any{"ok":false,"error":"BSSID inválido"}); return
	}
	snap := connectivitySnapshot()
	writeNetworkConnectState("associating","Associando à rede Wi-Fi selecionada…",in.SSID)
	keep := "0"; if in.KeepAP { keep = "1" }
	go func(ssid,password,bssid,keep string){
		time.Sleep(900*time.Millisecond)
		out,err := exec.Command("/usr/local/sbin/2pny-network-switch","connect",ssid,password,keep,bssid).CombinedOutput()
		msg := strings.TrimSpace(string(out))
		if err != nil { if msg=="" { msg="não foi possível concluir a associação Wi-Fi" }; writeNetworkConnectState("error",friendlyNetworkError(msg),ssid); invalidateConnectivityCache(); return }
		invalidateConnectivityCache(); cs := connectivitySnapshot()
		if !cs.WiFi || (ssid!="" && cs.WiFiSSID!=ssid) {
			writeNetworkConnectState("error","O rádio não permaneceu associado à rede selecionada. A conexão anterior/AP foi preservada.",ssid); return
		}
		writeNetworkConnectState("associated","Wi-Fi associado. Confirmando endereço IPv4…",ssid)
		if cs.ClientInterface=="" {
			writeNetworkConnectState("error","A associação Wi-Fi ocorreu, mas a interface cliente não foi confirmada.",ssid);return
		}
		ipOut,_:=exec.Command("ip","-4","-o","addr","show","dev",cs.ClientInterface,"scope","global").Output()
		if strings.TrimSpace(string(ipOut))=="" {
			writeNetworkConnectState("error","Wi-Fi associado, mas não recebeu IPv4. A configuração anterior/AP foi preservada.",ssid);return
		}
		writeNetworkConnectState("ipv4","IPv4 confirmado. Validando rota local…",ssid)
		route:=defaultRouteInterface()
		if route=="" {
			writeNetworkConnectState("error","IPv4 confirmado, mas nenhuma rota padrão ficou disponível.",ssid);return
		}
		writeNetworkConnectState("route","Rota confirmada. Validando DNS efetivo…",ssid)
		dnsOK:=false
		if b,e:=exec.Command("nmcli","-g","IP4.DNS","device","show",cs.ClientInterface).Output(); e==nil && strings.TrimSpace(string(b))!="" { dnsOK=true }
		if !dnsOK {
			if b,e:=os.ReadFile("/etc/resolv.conf"); e==nil && regexp.MustCompile(`(?m)^\\s*nameserver\\s+\\S+`).Match(b) { dnsOK=true }
		}
		if !dnsOK {
			writeNetworkConnectState("error","Rede associada e com IPv4, mas o DNS efetivo não foi confirmado.",ssid);return
		}
		writeNetworkConnectState("dns","DNS efetivo confirmado. Finalizando acesso local…",ssid)
		_ = exec.Command("/usr/local/sbin/2pny-mdns-guard").Run()
		invalidateConnectivityCache()
		writeNetworkConnectState("connected","Wi-Fi conectado e validado: associação, IPv4, rota e DNS confirmados. Internet externa é verificada separadamente.",ssid)
	}(in.SSID,in.Password,in.BSSID,keep)
	writeJSON(w,http.StatusAccepted,map[string]any{
		"ok":true,"state":"associating","ssid":in.SSID,"will_reboot":false,
		"message":"Associando à rede e validando IPv4, rota e DNS. Se a mesma placa estiver sendo usada pelo AP, a página continuará procurando o PU2PNY na nova rede.",
		"reconnect_url":"http://pu2pny.local/wizard","resume_urls":lanResumeURLs(snap.IPv4),
		"setup_url":"http://10.43.0.1/wizard","eta_seconds":30,
	})
}

func friendlyNetworkError(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" { return "Não foi possível concluir a operação de rede." }
	if strings.Contains(raw, "unbound variable") || strings.Contains(raw, "line ") {
		log.Printf("network helper detail: %s", raw)
		return "A operação de Wi-Fi encontrou uma falha interna e foi cancelada com segurança. A rede anterior foi preservada."
	}
	return raw
}

func wifiProfilesHandler(w http.ResponseWriter, r *http.Request) {
	statePath := filepath.Join(dataDir,"wifi-profile-state.json")
	readState := func() map[string]any { st:=readPublicJSON(statePath); if len(st)==0 { st=map[string]any{"state":"idle"} }; return st }
	writeState := func(state,message string){ b,_:=json.Marshal(map[string]any{"state":state,"message":message,"updated":time.Now().UTC().Format(time.RFC3339)}); _=os.WriteFile(statePath,b,0600) }
	if r.Method==http.MethodGet {
		out,err:=exec.Command("/usr/local/sbin/2pny-wifi-profiles","list-json").CombinedOutput()
		if err!=nil { writeJSON(w,503,map[string]any{"error":friendlyNetworkError(string(out)),"operation":readState()}); return }
		var obj map[string]any; if json.Unmarshal(out,&obj)!=nil { writeJSON(w,503,map[string]any{"error":"estado Wi-Fi inválido","operation":readState()}); return }
		obj["operation"]=readState(); writeJSON(w,200,obj); return
	}
	if r.Method!=http.MethodPost || !sameOrigin(r) { http.Error(w,"request rejected",403); return }
	var in struct { Action string `json:"action"`; SSID string `json:"ssid"`; Password string `json:"password"`; BSSID string `json:"bssid"` }
	if json.NewDecoder(http.MaxBytesReader(w,r.Body,16<<10)).Decode(&in)!=nil { writeJSON(w,400,map[string]any{"error":"dados Wi-Fi inválidos"}); return }
	in.SSID=strings.TrimSpace(in.SSID); in.BSSID=strings.TrimSpace(in.BSSID)
	switch in.Action {
	case "save-secondary":
		if in.SSID=="" || len(in.SSID)>64 || len(in.Password)>128 { writeJSON(w,400,map[string]any{"error":"SSID/senha inválidos"}); return }
		if in.BSSID!="" && !regexp.MustCompile("(?i)^([0-9a-f]{2}:){5}[0-9a-f]{2}$").MatchString(in.BSSID) { writeJSON(w,400,map[string]any{"error":"BSSID inválido"}); return }
		out,err:=exec.Command("/usr/local/sbin/2pny-wifi-profiles","save-secondary",in.SSID,in.Password,in.BSSID).CombinedOutput()
		if err!=nil { writeJSON(w,503,map[string]any{"error":friendlyNetworkError(string(out))}); return }
		writeState("saved","Segunda rede salva e pronta para uso."); writeJSON(w,200,map[string]any{"ok":true,"message":strings.TrimSpace(string(out))})
	case "switch":
		writeState("switching","Trocando para a rede reserva. A anterior será restaurada automaticamente se a nova falhar.")
		go func(){ time.Sleep(600*time.Millisecond); out,err:=exec.Command("/usr/local/sbin/2pny-wifi-profiles","switch").CombinedOutput(); invalidateConnectivityCache(); if err!=nil { writeState("error",friendlyNetworkError(string(out))); return }; _=exec.Command("/usr/local/sbin/2pny-mdns-guard").Run(); writeState("connected",strings.TrimSpace(string(out))) }()
		writeJSON(w,202,map[string]any{"ok":true,"state":"switching"})
	case "remove-secondary":
		out,err:=exec.Command("/usr/local/sbin/2pny-wifi-profiles","remove-secondary").CombinedOutput(); if err!=nil { writeJSON(w,503,map[string]any{"error":friendlyNetworkError(string(out))}); return }; writeState("idle","Segunda rede removida."); writeJSON(w,200,map[string]any{"ok":true})
	default: writeJSON(w,400,map[string]any{"error":"ação Wi-Fi inválida"})
	}
}

func networkDNSHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method!=http.MethodPost || !sameOrigin(r) { http.Error(w,"request rejected",403); return }
	var in struct { Provider string `json:"provider"` }
	if json.NewDecoder(http.MaxBytesReader(w,r.Body,2048)).Decode(&in)!=nil { writeJSON(w,400,map[string]any{"error":"opção DNS inválida"}); return }
	provider:=strings.ToLower(strings.TrimSpace(in.Provider))
	servers:=map[string]string{"cloudflare":"1.1.1.1 1.0.0.1","google":"8.8.8.8 8.8.4.4","opendns":"208.67.222.222 208.67.220.220","automatic":""}
	dns,ok:=servers[provider]; if !ok { writeJSON(w,400,map[string]any{"error":"provedor DNS inválido"}); return }
	iface:=defaultRouteInterface(); if iface=="" { writeJSON(w,409,map[string]any{"error":"não há rota ativa para alterar DNS"}); return }
	connOut,err:=exec.Command("nmcli","-g","GENERAL.CONNECTION","device","show",iface).Output(); if err!=nil { writeJSON(w,409,map[string]any{"error":"conexão ativa não identificada"}); return }
	conn:=strings.TrimSpace(string(connOut)); if conn=="" || conn=="--" { writeJSON(w,409,map[string]any{"error":"perfil de rede ativo não identificado"}); return }
	get:=func(key string) string { out,_:=exec.Command("nmcli","-g",key,"connection","show",conn).Output(); return strings.TrimSpace(string(out)) }
	oldIgnore,oldDNS:=get("ipv4.ignore-auto-dns"),get("ipv4.dns")
	backupDir:=filepath.Join(dataDir,"backups","network-dns"); _=os.MkdirAll(backupDir,0700)
	raw,_:=json.Marshal(map[string]any{"connection":conn,"interface":iface,"ignore_auto_dns":oldIgnore,"dns":oldDNS,"created":time.Now().UTC().Format(time.RFC3339)}); _=os.WriteFile(filepath.Join(backupDir,time.Now().UTC().Format("20060102T150405Z")+".json"),raw,0600)
	apply:=func(ignore,value string) error {
		out,e:=exec.Command("nmcli","connection","modify",conn,"ipv4.ignore-auto-dns",ignore,"ipv4.dns",value).CombinedOutput(); if e!=nil { return fmt.Errorf("%s",strings.TrimSpace(string(out))) }
		out,e=exec.Command("nmcli","device","reapply",iface).CombinedOutput(); if e!=nil { return fmt.Errorf("%s",strings.TrimSpace(string(out))) }; _=exec.Command("resolvectl","flush-caches").Run(); return nil
	}
	ignore:="yes"; if provider=="automatic" { ignore="no" }
	if err:=apply(ignore,dns); err!=nil { writeJSON(w,503,map[string]any{"error":"não foi possível aplicar DNS: "+err.Error()}); return }
	if exec.Command("timeout","-k","1","4","getent","ahostsv4","example.com").Run()!=nil { _=apply(oldIgnore,oldDNS); writeJSON(w,503,map[string]any{"error":"o DNS novo não resolveu nomes; configuração anterior restaurada"}); return }
	readEffective:=func() []string {
		effective:=[]string{}
		if out,e:=exec.Command("resolvectl","dns",iface).Output(); e==nil {
			seen:=map[string]bool{}
			for _,field:=range strings.Fields(string(out)) {
				ip:=strings.Trim(field,"[](),")
				if net.ParseIP(ip)!=nil && !seen[ip] { seen[ip]=true; effective=append(effective,ip) }
			}
		}
		return effective
	}
	expected:=strings.Fields(dns);effective:=[]string{};confirmed:=false;deadline:=time.Now().Add(6*time.Second)
	for time.Now().Before(deadline) {
		effective=readEffective()
		if provider=="automatic" {
			confirmed=len(effective)>0
		} else {
			for _,want:=range expected { for _,got:=range effective { if got==want { confirmed=true;break } }; if confirmed { break } }
		}
		if confirmed { break }
		time.Sleep(250*time.Millisecond)
	}
	if !confirmed {
		_ = apply(oldIgnore,oldDNS)
		writeJSON(w,503,map[string]any{"error":"o DNS solicitado não apareceu como efetivo; configuração anterior restaurada"})
		return
	}
	invalidateConnectivityCache()
	writeJSON(w,200,map[string]any{"ok":true,"provider":provider,"servers":dns,"effective_dns":effective,"interface":iface})
}

func maintenanceHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		out,err:=exec.Command("/usr/local/sbin/2pny-auto-maintenance","status").CombinedOutput()
		if err!=nil || len(strings.TrimSpace(string(out)))==0 { writeJSON(w,200,map[string]any{"state":"unknown","enabled":fileExists(filepath.Join(dataDir,"auto-maintenance.enabled"))}); return }
		var st map[string]any; if json.Unmarshal(out,&st)!=nil { st=map[string]any{"state":"unknown","message":strings.TrimSpace(string(out))} }; st["enabled"]=fileExists(filepath.Join(dataDir,"auto-maintenance.enabled")); writeJSON(w,200,st)
	case http.MethodPost:
		var in struct { Enabled *bool `json:"enabled"`; Action string `json:"action"` }
		if json.NewDecoder(http.MaxBytesReader(w,r.Body,4096)).Decode(&in)!=nil { writeJSON(w,400,map[string]any{"ok":false,"error":"opção inválida"}); return }
		action:=strings.ToLower(strings.TrimSpace(in.Action)); if action=="" && in.Enabled!=nil { if *in.Enabled { action="enable" } else { action="disable" } }
		switch action {
		case "enable","disable": out,err:=exec.Command("/usr/local/sbin/2pny-auto-maintenance",action).CombinedOutput(); if err!=nil { writeJSON(w,500,map[string]any{"ok":false,"error":strings.TrimSpace(string(out))}); return }; writeJSON(w,200,map[string]any{"ok":true,"enabled":action=="enable"})
		case "run": if err:=exec.Command("systemctl","start","--no-block","2pny-auto-maintenance.service").Run(); err!=nil { writeJSON(w,500,map[string]any{"ok":false,"error":"não foi possível iniciar a manutenção"}); return }; writeJSON(w,202,map[string]any{"ok":true,"state":"running"})
		case "force": go func(){ _,_=exec.Command("/usr/local/sbin/2pny-auto-maintenance","force").CombinedOutput() }(); writeJSON(w,202,map[string]any{"ok":true,"state":"running"})
		default: writeJSON(w,400,map[string]any{"ok":false,"error":"ação de manutenção inválida"})
		}
	default: http.Error(w,"GET or POST required",http.StatusMethodNotAllowed)
	}
}

func triggerMaintenance() {
	_ = exec.Command("systemctl", "start", "--no-block", "2pny-auto-maintenance.service").Run()
}

func networkRefreshHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method!=http.MethodPost { http.Error(w,"POST required",http.StatusMethodNotAllowed); return }
	invalidateConnectivityCache(); var cs ConnectivityStatus; deadline:=time.Now().Add(12*time.Second)
	for { cs=connectivitySnapshot(); if cs.Internet || cs.Ethernet || time.Now().After(deadline) { break }; time.Sleep(750*time.Millisecond); invalidateConnectivityCache() }
	if cs.DefaultInterface!="" { _=exec.Command("/usr/local/sbin/2pny-mdns-guard").Run(); invalidateConnectivityCache(); cs=connectivitySnapshot() }
	writeJSON(w,200,map[string]any{"ok":true,"connectivity":cs})
}

func applyDisplayOverrideToProbe() {
	ob, err := os.ReadFile(displayOverrideFile)
	if err != nil {
		return
	}
	var ov map[string]any
	if json.Unmarshal(ob, &ov) != nil || ov["enabled"] != true {
		return
	}
	hb, err := os.ReadFile(hardwareProbeFile)
	if err != nil {
		return
	}
	var h map[string]any
	if json.Unmarshal(hb, &h) != nil {
		return
	}
	m, _ := h["mmdvm"].(map[string]any)
	if m == nil || m["detected"] != true {
		return
	}
	// A manual override allows applying a known Nextion through the modem, but
	// it is not physical detection evidence. Keep detected=false until connect/comok
	// or another hardware-level proof confirms the display.
	h["display"] = map[string]any{
		"detected":      false,
		"class":         "nextion_mmdvm",
		"state":         "manual_override",
		"model":         "Nextion via MMDVM",
		"port":          "modem",
		"confidence":    "manual",
		"model_profile": ov["model_profile"],
		"resolution":    ov["resolution"],
		"message":       "Nextion habilitada manualmente pela MMDVM; aguardando confirmação física do display.",
	}
	raw, _ := json.Marshal(h)
	_ = os.WriteFile(hardwareProbeFile, raw, 0600)
}

func displayOverrideHandler(w http.ResponseWriter, r *http.Request) {
	readOverride := func() map[string]any {
		ov := map[string]any{
			"enabled": false, "type": "nextion_mmdvm", "layout": 9,
			"renderer": "pu2pny-modern-v2", "model_profile": "auto", "resolution": "",
		}
		if b, err := os.ReadFile(displayOverrideFile); err == nil {
			var stored map[string]any
			if json.Unmarshal(b, &stored) == nil {
				for k, v := range stored { ov[k] = v }
			}
		}
		return ov
	}
	switch r.Method {
	case http.MethodGet:
		writeJSON(w, http.StatusOK, readOverride())
	case http.MethodPost:
		if !sameOrigin(r) {
			http.Error(w, "request rejected", http.StatusForbidden)
			return
		}
		var in struct {
			Enabled      bool   `json:"enabled"`
			Layout       int    `json:"layout"`
			Renderer     string `json:"renderer"`
			ModelProfile string `json:"model_profile"`
			Resolution   string `json:"resolution"`
		}
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 8192)).Decode(&in); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "opção de display inválida"})
			return
		}
		in.Renderer = strings.ToLower(strings.TrimSpace(in.Renderer))
		if in.Renderer == "" {
			if in.Layout == 2 || in.Layout == 3 { in.Renderer = "mmdvmhost-native" } else { in.Renderer = "pu2pny-modern-v2" }
		}
		if in.Renderer != "pu2pny-modern-v2" && in.Renderer != "mmdvmhost-native" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "renderer de display inválido"})
			return
		}
		if in.Enabled {
			// DISPLAY-018: this endpoint controls Nextion through the modem.
			// Hardware validation regressed with the MQTT/vector bridge, so the
			// proven MMDVMHost-native writer is authoritative here.
			in.Renderer = "mmdvmhost-native"
			if in.Layout != 2 && in.Layout != 3 { in.Layout = 2 }
		} else if in.Renderer == "pu2pny-modern-v2" {
			in.Layout = 9
		} else if in.Layout != 2 && in.Layout != 3 {
			in.Layout = 2
		}
		in.ModelProfile = strings.TrimSpace(in.ModelProfile)
		if in.ModelProfile == "" { in.ModelProfile = "auto" }
		allowedProfiles := map[string]bool{
			"auto":true,"nextion-24-320x240":true,"nextion-28-320x240":true,"nextion-32-400x240":true,
			"nextion-35-480x320":true,"nextion-43-480x272":true,"nextion-50-800x480":true,
			"nextion-70-800x480":true,"nextion-101-1024x600":true,
		}
		if !allowedProfiles[in.ModelProfile] {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "perfil físico Nextion inválido"})
			return
		}
		in.Resolution = strings.ToLower(strings.TrimSpace(in.Resolution))
		if in.Resolution != "" && !regexp.MustCompile(`^[0-9]{3,4}x[0-9]{3,4}$`).MatchString(in.Resolution) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "resolução de display inválida"})
			return
		}
		oldOverride, oldOverrideErr := os.ReadFile(displayOverrideFile)
		oldOverrideExists := oldOverrideErr == nil
		if in.Enabled {
			if _, err := detectedModemPort(); err != nil {
				writeJSON(w, http.StatusConflict, map[string]any{"ok": false, "error": "MMDVM precisa estar detectada antes de habilitar a Nextion"})
				return
			}
			raw, _ := json.Marshal(map[string]any{
				"enabled": true, "type": "nextion_mmdvm", "speed": 9600,
				"layout": in.Layout, "renderer": in.Renderer,
				"model_profile": in.ModelProfile, "resolution": in.Resolution,
				"updated": time.Now().UTC().Format(time.RFC3339),
			})
			_ = os.WriteFile(displayOverrideFile, raw, 0600)
			applyDisplayOverrideToProbe()
		} else {
			raw, _ := json.Marshal(map[string]any{"enabled": false, "renderer": in.Renderer, "layout": in.Layout, "model_profile": in.ModelProfile, "resolution": in.Resolution})
			_ = os.WriteFile(displayOverrideFile, raw, 0600)
		}
		if fileExists(filepath.Join(dataDir, "rf-configured")) {
			res, err := runPrivilegedRequest("2pny-display-apply-request.service", "/run/2pny/display-apply-request.json", "/run/2pny/display-apply-result.json", map[string]any{"apply": true})
			if err != nil {
				if oldOverrideExists { _ = os.WriteFile(displayOverrideFile, oldOverride, 0600) } else { _ = os.Remove(displayOverrideFile) }
				_, _ = runPrivilegedRequest("2pny-display-apply-request.service", "/run/2pny/display-apply-request.json", "/run/2pny/display-apply-result.json", map[string]any{"rollback": true})
				writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok": false, "error": "Não foi possível aplicar o display; a configuração anterior foi restaurada.", "detail": err.Error(), "result": res})
				return
			}
		}
		runtime := readPublicJSON(filepath.Join(dataDir, "display-runtime.json"))
		writeJSON(w, http.StatusOK, map[string]any{"ok": true, "enabled": in.Enabled, "layout": in.Layout, "renderer": in.Renderer, "model_profile": in.ModelProfile, "resolution": in.Resolution, "runtime": runtime})
	default:
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
	}
}

func displayDetectionHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet {
		result := readPublicJSON(filepath.Join(dataDir, "display-detection.json"))
		status := readPublicJSON("/run/2pny/display-detect-status.json")
		if len(result) == 0 {
			result = map[string]any{"state": "idle", "displays": []any{}}
		}
		for k, v := range status { result[k] = v }
		writeJSON(w, http.StatusOK, result)
		return
	}
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	_ = os.MkdirAll("/run/2pny", 0755)
	raw, _ := json.Marshal(map[string]any{"requested": time.Now().UTC().Format(time.RFC3339)})
	if err := os.WriteFile("/run/2pny/display-detect-request.json", raw, 0640); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"ok": false, "error": "não foi possível solicitar a detecção do display"})
		return
	}
	writeJSON(w, http.StatusAccepted, map[string]any{"ok": true, "state": "detecting", "message": "Detecção de display solicitada."})
}

func udpDiagnostic(port int) map[string]any {
	state := map[string]any{"port": port, "listening": false}
	out, err := exec.Command("ss", "-H", "-lun").Output()
	if err != nil { return state }
	for _, raw := range strings.Split(string(out), "\n") {
		fields := strings.Fields(raw)
		if len(fields) < 5 { continue }
		local := fields[3]
		if strings.HasSuffix(local, ":"+strconv.Itoa(port)) || strings.HasSuffix(local, "]:"+strconv.Itoa(port)) {
			state["listening"] = true
			state["local"] = local
			break
		}
	}
	return state
}

func diagnosticsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	cfg := readPublicJSON(configFile)
	proto, _ := cfg["protocol"].(string)
	gateways := map[string]string{
		"DMR":"2pny-dmrgateway.service","DSTAR":"2pny-dstargateway.service","YSF":"2pny-ysfgateway.service",
		"P25":"2pny-p25gateway.service","NXDN":"2pny-nxdngateway.service","POCSAG":"2pny-dapnetgateway.service",
	}
	gateway := gateways[strings.ToUpper(proto)]
	writeJSON(w, http.StatusOK, map[string]any{
		"protocol": strings.ToUpper(proto),
		"mmdvmhost_active": serviceActive("2pny-mmdvmhost.service"),
		"gateway": gateway,
		"gateway_active": gateway != "" && serviceActive(gateway),
		"udp": map[string]any{"dstar": udpDiagnostic(20010), "ysf": udpDiagnostic(4200)},
		"mqtt_preflight": readPublicJSON("/run/2pny/mqtt-preflight.json"),
		"protocol_health": readPublicJSON("/run/2pny/protocol-health.json"),
		"display_runtime": readPublicJSON(filepath.Join(dataDir, "display-runtime.json")),
		"display_detection": readPublicJSON(filepath.Join(dataDir, "display-detection.json")),
		"display_settings": readPublicJSON(filepath.Join(dataDir, "display-settings.json")),
		"operational_result": readPublicJSON("/run/2pny/operational-result.json"),
		"boot_restore": readPublicJSON(filepath.Join(dataDir, "last-boot-restore.json")),
		"last_rollback": readPublicJSON(filepath.Join(dataDir, "last-protocol-rollback.json")),
		"network_connect": readPublicJSON(filepath.Join(dataDir, "network-connect.json")),
		"updated": time.Now().UTC().Format(time.RFC3339),
	})
}

func hardwareHandler(w http.ResponseWriter, r *http.Request) {
	b, err := os.ReadFile(hardwareFile)
	if err != nil {
		writeJSON(w, http.StatusOK, map[string]any{"raspberry_model": "detectando...", "serial_ports": []string{}, "i2c_buses": []string{}, "mmdvm": map[string]any{"detected": false}})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(b)
}

func hardwareStatusHandler(w http.ResponseWriter, r *http.Request) {
	probe := map[string]any{}
	if b, err := os.ReadFile(hardwareProbeFile); err == nil {
		_ = json.Unmarshal(b, &probe)
	}
	scan := map[string]any{}
	if b, err := os.ReadFile(hardwareScanStateFile); err == nil {
		_ = json.Unmarshal(b, &scan)
	}
	// Scan progress is transient. Never replace a previously confirmed modem/display
	// merely to show "preparing" or "scanning" in the wizard.
	if state, _ := scan["state"].(string); state == "preparing" || state == "scanning" {
		for k, v := range scan {
			probe[k] = v
		}
	}
	if len(probe) == 0 {
		probe["state"] = "not_scanned"
	}
	writeJSON(w, http.StatusOK, probe)
}

func writeHardwareState(state, stage, message string) {
	_ = os.MkdirAll(filepath.Dir(hardwareScanStateFile), 0755)
	b, _ := json.Marshal(map[string]any{"state": state, "stage": stage, "message": message, "updated": time.Now().UTC().Format(time.RFC3339)})
	_ = os.WriteFile(hardwareScanStateFile, b, 0644)
}

func hardwareScanHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	hardwareScanMu.Lock()
	if hardwareScanning {
		hardwareScanMu.Unlock()
		writeJSON(w, http.StatusAccepted, map[string]any{"state": "preparing"})
		return
	}
	hardwareScanning = true
	hardwareScanMu.Unlock()
	writeHardwareState("preparing", "drivers", "Preparando drivers e firmware...")
	// Respond immediately; display/driver work must never block the POST.
	go func() {
		defer func() { hardwareScanMu.Lock(); hardwareScanning = false; hardwareScanMu.Unlock() }()
		_ = exec.Command("timeout", "5", "/usr/local/sbin/2pny-display-status", "hardware", "PU2PNY-OS: hardware").Run()
		prep := exec.Command("timeout", "-k", "2", "25", "/usr/local/sbin/2pny-hardware-prepare")
		if b, err := prep.CombinedOutput(); err != nil {
			log.Printf("hardware prepare warning: %v: %s", err, strings.TrimSpace(string(b)))
		}
		writeHardwareState("scanning", "hardware", "Detectando MMDVM e display...")
		cmd := exec.Command("timeout", "-k", "2", "60", "/usr/local/sbin/2pny-hardware-probe")
		if b, err := cmd.CombinedOutput(); err != nil {
			msg := strings.TrimSpace(string(b))
			if msg == "" {
				msg = err.Error()
			}
			writeHardwareState("error", "hardware", msg)
			_ = exec.Command("/usr/local/sbin/2pny-display-status", "error", "Falha ao detectar hardware").Run()
			log.Printf("hardware probe failed: %v: %s", err, msg)
			return
		}
		applyDisplayOverrideToProbe()
		// Candidate Nextion should be tried automatically; this helper never steals
		// the modem UART from an active MMDVMHost.
		_, _ = exec.Command("timeout", "-k", "2", "15", "/usr/local/sbin/2pny-nextion-autodetect").CombinedOutput()
		_ = os.Remove(hardwareScanStateFile)
		_ = exec.Command("/usr/local/sbin/2pny-display-status", "display", "Hardware detectado").Run()
	}()
	writeJSON(w, http.StatusAccepted, map[string]any{"ok": true, "state": "preparing", "stage": "drivers"})
}

func publicConfigHandler(w http.ResponseWriter, r *http.Request) {
	b, err := os.ReadFile(configFile)
	if err != nil {
		writeJSON(w, http.StatusOK, map[string]any{})
		return
	}
	var c Config
	if json.Unmarshal(b, &c) != nil {
		writeJSON(w, http.StatusOK, map[string]any{})
		return
	}
	writeJSON(w, http.StatusOK, c)
}

func writeRFApplyState(state, message string) {
	st := RFApplyState{State: state, Message: message, Updated: time.Now().UTC().Format(time.RFC3339)}
	b, _ := json.Marshal(st)
	_ = os.WriteFile(rfApplyStateFile, b, 0600)
}

func rfStatusHandler(w http.ResponseWriter, r *http.Request) {
	b, err := os.ReadFile(rfApplyStateFile)
	if err != nil {
		writeJSON(w, http.StatusOK, RFApplyState{State: "ready", Message: "Aguardando configuração.", Updated: time.Now().UTC().Format(time.RFC3339)})
		return
	}
	var st RFApplyState
	if json.Unmarshal(b, &st) != nil {
		writeJSON(w, http.StatusOK, RFApplyState{State: "ready", Message: "Aguardando configuração.", Updated: time.Now().UTC().Format(time.RFC3339)})
		return
	}
	writeJSON(w, http.StatusOK, st)
}

func detectedModemPort() (string, error) {
	b, err := os.ReadFile(hardwareProbeFile)
	if err != nil {
		return "", fmt.Errorf("hardware ainda não foi detectado")
	}
	var h struct {
		MMDVM struct {
			Detected bool   `json:"detected"`
			Port     string `json:"port"`
		} `json:"mmdvm"`
	}
	if json.Unmarshal(b, &h) != nil || !h.MMDVM.Detected || strings.TrimSpace(h.MMDVM.Port) == "" {
		return "", fmt.Errorf("MMDVM não confirmada; volte à etapa Hardware e detecte novamente")
	}
	return strings.TrimSpace(h.MMDVM.Port), nil
}

func normalizeFrequency(v string) (string, int64, error) {
	s := strings.ReplaceAll(strings.TrimSpace(v), ",", ".")
	f, err := strconv.ParseFloat(s, 64)
	if err != nil || f <= 0 {
		return "", 0, fmt.Errorf("frequência inválida")
	}
	if f < 1000 {
		f *= 1000000
	} else if f < 1000000 {
		f *= 1000
	}
	hz := int64(f + 0.5)
	if hz < 100000000 || hz > 1000000000 {
		return "", 0, fmt.Errorf("frequência fora do intervalo de segurança 100 MHz..1 GHz")
	}
	return strconv.FormatInt(hz, 10), hz, nil
}

func saveConfig(c Config) error {
	if err := os.MkdirAll(dataDir, 0750); err != nil {
		return err
	}
	raw, _ := json.MarshalIndent(c, "", "  ")
	tmp := configFile + ".tmp"
	if err := os.WriteFile(tmp, raw, 0600); err != nil {
		return err
	}
	return os.Rename(tmp, configFile)
}

type applyTransaction struct {
	dir     string
	paths   []string
	existed map[string]bool
	active  map[string]bool
	enabled map[string]bool
}

func beginApplyTransaction() (*applyTransaction, error) {
	if err := os.MkdirAll("/run/2pny", 0750); err != nil {
		return nil, err
	}
	dir, err := os.MkdirTemp("/run/2pny", "apply-tx-")
	if err != nil {
		return nil, err
	}
	t := &applyTransaction{
		dir: dir,
		paths: []string{
			"/var/lib/2pny/mmdvm/MMDVM-Host.ini",
			filepath.Join(dataDir, "basic-radio.json"),
			filepath.Join(dataDir, "network-radio.json"),
			configFile,
			provisionedFile,
			filepath.Join(dataDir, "rf-configured"),
			filepath.Join(dataDir, "display-runtime.json"),
			filepath.Join(dataDir, "display", "MMDVM-Display.ini"),
			filepath.Join(dataDir, "mmdvm-baud"),
			filepath.Join(dataDir, "dmr", "DMRGateway.ini"),
			filepath.Join(dataDir, "dmr", "XLXHosts.txt"),
			filepath.Join(dataDir, "dstar", "DStarGateway.ini"),
			filepath.Join(dataDir, "ysf", "YSFGateway.ini"),
			filepath.Join(dataDir, "ysf", "YSFHosts.json"),
			filepath.Join(dataDir, "ysf", "FCSRooms.txt"),
			filepath.Join(dataDir, "p25", "P25Gateway.ini"),
			filepath.Join(dataDir, "p25", "P25Hosts.json"),
			filepath.Join(dataDir, "nxdn", "NXDNGateway.ini"),
			filepath.Join(dataDir, "nxdn", "NXDNHosts.json"),
			filepath.Join(dataDir, "pocsag", "DAPNETGateway.ini"),
			filepath.Join(dataDir, "secrets", "brandmeister-api.key"),
		},
		existed: map[string]bool{},
		active:  map[string]bool{},
		enabled: map[string]bool{},
	}
	for _, service := range []string{
		"2pny-mmdvmhost.service", "2pny-dmrgateway.service", "2pny-dstargateway.service",
		"2pny-ysfgateway.service", "2pny-p25gateway.service", "2pny-nxdngateway.service",
		"2pny-dapnetgateway.service", "2pny-display.service",
	} {
		t.active[service] = serviceActive(service)
		t.enabled[service] = exec.Command("systemctl", "is-enabled", "--quiet", service).Run() == nil
	}
	for i, p := range t.paths {
		if !fileExists(p) {
			t.existed[p] = false
			continue
		}
		t.existed[p] = true
		dst := filepath.Join(dir, strconv.Itoa(i))
		if out, e := exec.Command("cp", "-a", "--", p, dst).CombinedOutput(); e != nil {
			_ = os.RemoveAll(dir)
			return nil, fmt.Errorf("backup transacional falhou: %s", strings.TrimSpace(string(out)))
		}
	}
	return t, nil
}

func (t *applyTransaction) rollback() {
	if t == nil {
		return
	}
	for i, p := range t.paths {
		if t.existed[p] {
			_ = exec.Command("cp", "-a", "--", filepath.Join(t.dir, strconv.Itoa(i)), p).Run()
		} else {
			_ = os.Remove(p)
		}
	}
	for _, service := range []string{
		"2pny-dmrgateway.service", "2pny-dstargateway.service", "2pny-ysfgateway.service",
		"2pny-p25gateway.service", "2pny-nxdngateway.service", "2pny-dapnetgateway.service",
		"2pny-mmdvmhost.service", "2pny-display.service",
	} {
		enableAction := "disable"
		if t.enabled[service] {
			enableAction = "enable"
		}
		_ = exec.Command("systemctl", enableAction, service).Run()
		action := "stop"
		if t.active[service] {
			action = "restart"
		}
		_ = exec.Command("systemctl", action, service).Run()
	}
	_ = os.RemoveAll(t.dir)
}

func (t *applyTransaction) commit() {
	if t != nil {
		_ = os.RemoveAll(t.dir)
	}
}

func hasUnsafeControl(s string) bool {
	return strings.ContainsAny(s, "\r\n\x00")
}

func basicApplyHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	var in struct {
		Callsign       string `json:"callsign"`
		DMRID          string `json:"dmr_id"`
		UseMode        string `json:"use_mode"`
		RX             string `json:"rx"`
		TX             string `json:"tx"`
		RXOffset       string `json:"rx_offset"`
		TXOffset       string `json:"tx_offset"`
		Protocol       string `json:"protocol"`
		Operation      string `json:"operation"`
		ServerName     string `json:"server_name"`
		ServerAddress  string `json:"server_address"`
		ServerPort     int    `json:"server_port"`
		ServerPassword string `json:"server_password"`
		ServerOptions  string `json:"server_options"`
		NetworkKind    string `json:"network_kind"`
		ColorCode      int    `json:"color_code"`
		DMRSlot        string `json:"dmr_slot"`
		XLXModule      string `json:"xlx_module"`
		ESSID          string `json:"essid"`
		BMAPIKey       string `json:"bm_api_key"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 32<<10)).Decode(&in); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "configuração inválida"})
		return
	}
	in.Callsign = strings.ToUpper(strings.TrimSpace(in.Callsign))
	in.DMRID = strings.TrimSpace(in.DMRID)
	in.UseMode = strings.ToLower(strings.TrimSpace(in.UseMode))
	in.Protocol = strings.ToUpper(strings.TrimSpace(in.Protocol))
	in.Operation = strings.ToLower(strings.TrimSpace(in.Operation))
	in.ServerName = strings.TrimSpace(in.ServerName)
	in.ServerAddress = strings.TrimSpace(in.ServerAddress)
	in.ServerPassword = strings.TrimSpace(in.ServerPassword)
	in.ServerOptions = strings.TrimSpace(in.ServerOptions)
	in.NetworkKind = strings.TrimSpace(in.NetworkKind)
	in.DMRSlot = strings.ToLower(strings.TrimSpace(in.DMRSlot))
	in.XLXModule = strings.ToUpper(strings.TrimSpace(in.XLXModule))
	in.ESSID = strings.TrimSpace(in.ESSID)
	in.BMAPIKey = strings.TrimSpace(in.BMAPIKey)
	if in.DMRSlot == "" {
		in.DMRSlot = "2"
	}
	if in.ColorCode < 0 || in.ColorCode > 15 {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "Color Code DMR inválido"})
		return
	}
	if !callsignRx.MatchString(in.Callsign) {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "indicativo inválido"})
		return
	}
	if !dmrRx.MatchString(in.DMRID) {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "DMR ID inválido"})
		return
	}
	if in.UseMode != "hotspot" && in.UseMode != "repeater" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "selecione Hotspot ou Repetidora"})
		return
	}
	validProtocol := map[string]bool{"DSTAR": true, "DMR": true, "YSF": true, "P25": true, "NXDN": true, "POCSAG": true}
	if !validProtocol[in.Protocol] {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "protocolo inválido"})
		return
	}
	if in.Operation != "normal" && in.Operation != "crossmode" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "selecione Normal ou Crossmode"})
		return
	}
	if in.Operation == "crossmode" {
		writeJSON(w, http.StatusConflict, map[string]any{"ok": false, "error": "Crossmode ainda está em desenvolvimento nesta Alpha; use operação Normal"})
		return
	}
	if in.Protocol == "DSTAR" || in.Protocol == "YSF" || in.Protocol == "P25" || in.Protocol == "NXDN" || in.Protocol == "POCSAG" {
		if in.ServerName == "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "selecione um servidor/refletor para o protocolo"})
			return
		}
		if len(in.ServerName) > 128 || len(in.ServerAddress) > 255 || hasUnsafeControl(in.ServerName) || hasUnsafeControl(in.ServerAddress) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "servidor/refletor inválido"})
			return
		}
		if in.Protocol == "DSTAR" && (len(in.XLXModule) != 1 || in.XLXModule[0] < 'A' || in.XLXModule[0] > 'Z') {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "D-Star exige módulo A-Z"})
			return
		}
	}
	if in.Protocol == "POCSAG" {
		if in.ServerName == "" || in.ServerAddress == "" || in.ServerPort < 1 || in.ServerPort > 65535 || in.ServerPassword == "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "POCSAG/DAPNET exige servidor, porta e AuthKey"})
			return
		}
		if len(in.ServerPassword) > 128 || hasUnsafeControl(in.ServerPassword) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "DAPNET AuthKey inválida"})
			return
		}
	}
	if in.Protocol == "DMR" {
		if in.ServerName == "" || in.ServerAddress == "" || in.ServerPort < 1 || in.ServerPort > 65535 {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "selecione um servidor/master DMR válido"})
			return
		}
		if len(in.ServerName) > 128 || len(in.ServerAddress) > 255 || len(in.ServerPassword) > 128 || len(in.ServerOptions) > 512 ||
			hasUnsafeControl(in.ServerName) || hasUnsafeControl(in.ServerAddress) || hasUnsafeControl(in.ServerPassword) || hasUnsafeControl(in.ServerOptions) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "campos do servidor DMR contêm tamanho ou caracteres inválidos"})
			return
		}
		if in.DMRSlot != "1" && in.DMRSlot != "2" && in.DMRSlot != "both" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "slot DMR inválido"})
			return
		}
		if in.UseMode == "hotspot" && in.DMRSlot == "both" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "hotspot simplex deve usar TS1 ou TS2"})
			return
		}
		if in.XLXModule != "" && (len(in.XLXModule) != 1 || in.XLXModule[0] < 'A' || in.XLXModule[0] > 'Z') {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "módulo XLX inválido"})
			return
		}
		if in.ESSID != "" && !regexp.MustCompile(`^(0[1-9]|[1-9][0-9])$`).MatchString(in.ESSID) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "Identificação do hotspot deve ser 01 a 99"})
			return
		}
		if strings.EqualFold(in.NetworkKind, "BrandMeister") && in.ServerPassword == "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "BrandMeister exige a senha Hotspot Security"})
			return
		}
	}
	rxOffset := strings.TrimSpace(in.RXOffset)
	txOffset := strings.TrimSpace(in.TXOffset)
	if rxOffset == "" {
		rxOffset = "0"
	}
	if txOffset == "" {
		txOffset = "0"
	}
	rxOffsetHz, err := strconv.ParseInt(rxOffset, 10, 64)
	if err != nil || rxOffsetHz < -10000000 || rxOffsetHz > 10000000 {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "RX Offset inválido; use Hz entre -10000000 e 10000000"})
		return
	}
	txOffsetHz, err := strconv.ParseInt(txOffset, 10, 64)
	if err != nil || txOffsetHz < -10000000 || txOffsetHz > 10000000 {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "TX Offset inválido; use Hz entre -10000000 e 10000000"})
		return
	}
	rxArg, rxHz, err := normalizeFrequency(in.RX)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "RX: " + err.Error()})
		return
	}
	txArg, txHz := rxArg, rxHz
	if in.UseMode == "repeater" {
		txArg, txHz, err = normalizeFrequency(in.TX)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "TX: " + err.Error()})
			return
		}
	} else {
		// A hotspot simplex always uses the same RF frequency for RX and TX.
		in.TX = in.RX
	}
	port, err := detectedModemPort()
	if err != nil {
		writeJSON(w, http.StatusConflict, map[string]any{"ok": false, "error": err.Error()})
		return
	}
	duplex := "0"
	if in.UseMode == "repeater" {
		duplex = "1"
	}
	writeRFApplyState("applying", "Validando modem, frequência e configuração básica...")
	_ = exec.Command("/usr/local/sbin/2pny-display-status", "rf", "Configurando radio").Run()
	go func() {
		applyMu.Lock()
		defer applyMu.Unlock()
		tx, txErr := beginApplyTransaction()
		if txErr != nil {
			writeRFApplyState("error", "Não foi possível criar o rollback antes da configuração: "+txErr.Error())
			return
		}
		committed := false
		defer func() {
			if committed {
				tx.commit()
			} else {
				tx.rollback()
			}
		}()
		cmd := exec.Command("/usr/local/sbin/2pny-rf-apply", rxArg, txArg, rxOffset, txOffset, duplex, port, in.Callsign, in.DMRID)
		out, err := cmd.CombinedOutput()
		msg := strings.TrimSpace(string(out))
		if err != nil {
			if msg == "" {
				msg = err.Error()
			}
			writeRFApplyState("error", msg)
			log.Printf("basic RF apply failed: %v: %s", err, msg)
			return
		}
		modeOut, modeErr := exec.Command("/usr/local/sbin/2pny-mode-apply", in.Protocol, in.Operation, in.UseMode).CombinedOutput()
		if modeErr != nil {
			m := strings.TrimSpace(string(modeOut))
			if m == "" {
				m = modeErr.Error()
			}
			writeRFApplyState("error", "RF validada, mas o protocolo não pôde ser aplicado: "+m)
			log.Printf("mode apply failed: %v: %s", modeErr, m)
			return
		}

		networkState := "rf-only"
		if in.Protocol == "DMR" || in.Protocol == "DSTAR" || in.Protocol == "YSF" || in.Protocol == "P25" || in.Protocol == "NXDN" || in.Protocol == "POCSAG" {
			netOut, netErr := exec.Command("/usr/local/sbin/2pny-protocol-network-apply",
				in.Protocol, in.ServerName, in.ServerAddress, strconv.Itoa(in.ServerPort),
				in.ServerPassword, in.UseMode, strconv.Itoa(in.ColorCode), in.DMRSlot,
				in.XLXModule, in.ESSID, in.NetworkKind, in.ServerOptions).CombinedOutput()
			if netErr != nil {
				m := strings.TrimSpace(string(netOut))
				if m == "" {
					m = netErr.Error()
				}
				writeRFApplyState("error", "RF validada, mas a rede "+in.Protocol+" não pôde ser aplicada: "+m)
				log.Printf("%s network apply failed: %v: %s", in.Protocol, netErr, m)
				return
			}
			networkState = "connecting"
		}

		apiConfigured := false
		apiPath := filepath.Join(dataDir, "secrets", "brandmeister-api.key")
		if strings.EqualFold(in.NetworkKind, "BrandMeister") && in.BMAPIKey != "" {
			_ = os.MkdirAll(filepath.Dir(apiPath), 0700)
			if err := os.WriteFile(apiPath, []byte(in.BMAPIKey+"\n"), 0600); err != nil {
				writeRFApplyState("error", "Rede aplicada, mas não foi possível guardar a API Key com segurança.")
				return
			}
			apiConfigured = true
		} else if strings.EqualFold(in.NetworkKind, "BrandMeister") {
			apiConfigured = fileExists(apiPath)
		} else {
			_ = os.Remove(apiPath)
		}
		wifiSSID := ""
		if b, e := os.ReadFile(filepath.Join(dataDir, "uplink-ssid")); e == nil {
			wifiSSID = strings.TrimSpace(string(b))
		}
		cfg := Config{
			Callsign: in.Callsign, DMRID: in.DMRID, WiFiSSID: wifiSSID, UseMode: in.UseMode,
			RXHz: rxHz, TXHz: txHz, RXOffsetHz: rxOffsetHz, TXOffsetHz: txOffsetHz, Protocol: in.Protocol, Operation: in.Operation,
			ServerName: in.ServerName, ServerAddress: in.ServerAddress, ServerPort: in.ServerPort,
			NetworkKind: in.NetworkKind, ColorCode: in.ColorCode, DMRSlot: in.DMRSlot, XLXModule: in.XLXModule,
			ESSID: in.ESSID, BMAPIConfigured: apiConfigured, NetworkState: networkState,
			CreatedAt: time.Now().UTC().Format(time.RFC3339),
		}
		if err := saveConfig(cfg); err != nil {
			writeRFApplyState("error", "RF aplicada, mas não foi possível salvar a configuração.")
			return
		}
		if err := os.WriteFile(provisionedFile, []byte(time.Now().UTC().Format(time.RFC3339)+"\n"), 0600); err != nil {
			writeRFApplyState("error", "Configuração aplicada, mas não foi possível finalizar o assistente.")
			return
		}
		// APRS messaging is provisioned automatically; it remains position-silent
		// until real coordinates are explicitly supplied.
		_ = ensureAPRSDefaults()
		_ = exec.Command("systemctl", "restart", "avahi-daemon.service").Run()
		done := "RF e MMDVMHost configurados."
		if networkState == "connecting" {
			done = "RF configurada e rede " + in.Protocol + " aplicada. Acompanhe o estado no painel principal."
		}
		committed = true
		writeRFApplyState("applied", done)
	}()
	writeJSON(w, http.StatusAccepted, map[string]any{"ok": true, "state": "applying"})
}

func rfApplyHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	if err := r.ParseForm(); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "formulário RF inválido"})
		return
	}
	keys := []string{"rx", "tx", "rx_offset", "tx_offset", "duplex", "port", "callsign", "dmr_id"}
	args := make([]string, 0, len(keys))
	for _, k := range keys {
		v := strings.TrimSpace(r.FormValue(k))
		if v == "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "campo obrigatório: " + k})
			return
		}
		args = append(args, v)
	}
	writeRFApplyState("applying", "Validando RF e iniciando MMDVMHost...")
	go func(values []string) {
		applyMu.Lock()
		defer applyMu.Unlock()
		out, err := exec.Command("/usr/local/sbin/2pny-rf-apply", values...).CombinedOutput()
		msg := strings.TrimSpace(string(out))
		if err != nil {
			if msg == "" {
				msg = err.Error()
			}
			writeRFApplyState("error", msg)
			return
		}
		if msg == "" {
			msg = "RF aplicada e MMDVMHost ativo."
		}
		writeRFApplyState("applied", msg)
	}(append([]string(nil), args...))
	writeJSON(w, http.StatusAccepted, map[string]any{"ok": true, "state": "applying"})
}

func rfPowerHandler(w http.ResponseWriter, r *http.Request) {
	readLevel := func() (int, bool) {
		b, err := os.ReadFile("/var/lib/2pny/mmdvm/MMDVM-Host.ini")
		if err != nil {
			return 0, false
		}
		inModem := false
		for _, raw := range strings.Split(string(b), "\n") {
			line := strings.TrimSpace(raw)
			if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
				inModem = strings.EqualFold(line, "[Modem]")
				continue
			}
			if inModem && strings.HasPrefix(strings.ToLower(line), "rflevel=") {
				n, err := strconv.Atoi(strings.TrimSpace(strings.SplitN(line, "=", 2)[1]))
				return n, err == nil
			}
		}
		return 0, false
	}
	hw := readPublicJSON(hardwareProbeFile)
	model := ""
	if m, ok := hw["mmdvm"].(map[string]any); ok {
		model, _ = m["model"].(string)
		if model == "" {
			model, _ = m["firmware"].(string)
		}
	}
	level, found := readLevel()
	upper := strings.ToUpper(model)
	supported := found || strings.Contains(upper, "MMDVM_HS") || strings.Contains(upper, "ZUM") || strings.Contains(upper, "ADF7021") || strings.Contains(upper, "HS HAT")
	if r.Method == http.MethodGet {
		writeJSON(w, 200, map[string]any{"supported": supported, "rf_level": level, "model": model})
		return
	}
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	var in struct {
		RFLevel int `json:"rf_level"`
	}
	if json.NewDecoder(http.MaxBytesReader(w, r.Body, 2048)).Decode(&in) != nil || in.RFLevel < 0 || in.RFLevel > 100 {
		writeJSON(w, 400, map[string]any{"error": "RFLevel deve estar entre 0 e 100"})
		return
	}
	if !supported {
		writeJSON(w, 409, map[string]any{"error": "O modem não confirmou suporte a RFLevel."})
		return
	}
	res, err := runPrivilegedRequest("2pny-rflevel-apply.service", "/run/2pny/rflevel-request.json", "/run/2pny/rflevel-result.json", map[string]any{"rf_level": in.RFLevel})
	if err != nil {
		writeJSON(w, 503, map[string]any{"error": err.Error(), "result": res})
		return
	}
	writeJSON(w, 200, res)
}

func serversHandler(w http.ResponseWriter, r *http.Request) {
	proto := strings.ToUpper(strings.TrimSpace(r.URL.Query().Get("protocol")))
	if proto == "" {
		proto = "DMR"
	}
	query := strings.TrimSpace(r.URL.Query().Get("q"))
	if r.Method == http.MethodPost {
		_ = startHostfilesUpdate()
	}
	if r.Method != http.MethodGet && r.Method != http.MethodPost {
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
		return
	}
	args := []string{proto}
	if query != "" {
		args = append(args, query)
	}
	out, err := exec.Command("/usr/local/sbin/2pny-server-catalog", args...).CombinedOutput()
	if err != nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"protocol": proto, "servers": []any{}, "error": strings.TrimSpace(string(out))})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	if isHostfilesUpdating() {
		w.Header().Set("X-PU2PNY-Catalog-Updating", "1")
	}
	_, _ = w.Write(out)
}

func liveStatusHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	out := liveHub.current().data
	if len(out) == 0 {
		out = []byte(`{"schema":1,"sequence":0,"active":null,"standby":true,"network":{"state":"unknown","message":"worker unavailable"},"internet":{"quality":"unknown"},"history":[]}`)
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(out)
}

func liveEventsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache, no-store")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")
	ch := make(chan liveEvent, 1)
	liveHub.mu.Lock()
	liveHub.subscribers[ch] = struct{}{}
	initial := liveEvent{id: liveHub.sequence, data: append([]byte(nil), liveHub.snapshot...)}
	liveHub.mu.Unlock()
	defer func() { liveHub.mu.Lock(); delete(liveHub.subscribers, ch); close(ch); liveHub.mu.Unlock() }()
	send := func(event liveEvent) bool {
		if len(event.data) == 0 {
			return true
		}
		if _, err := fmt.Fprintf(w, "id: %d\nevent: live\ndata: %s\n\n", event.id, event.data); err != nil {
			return false
		}
		flusher.Flush()
		return true
	}
	if !send(initial) {
		return
	}
	heartbeat := time.NewTicker(15 * time.Second)
	defer heartbeat.Stop()
	for {
		select {
		case event := <-ch:
			if !send(event) {
				return
			}
		case <-heartbeat.C:
			if _, err := fmt.Fprint(w, ": keepalive\n\n"); err != nil {
				return
			}
			flusher.Flush()
		case <-r.Context().Done():
			return
		}
	}
}

func moduleStatusHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	out, err := exec.Command("/usr/local/sbin/2pny-module-status").Output()
	if err != nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"schema": 1, "error": "module status unavailable"})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(out)
}

func apControlHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet {
		writeJSON(w, http.StatusOK, map[string]any{"active": apActive(), "ssid": "pu2pny", "open": true, "interface": readRunFile("ap-iface")})
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
		return
	}
	if err := r.ParseForm(); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "pedido inválido"})
		return
	}
	action := strings.TrimSpace(r.FormValue("action"))
	if action != "on" && action != "off" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "action deve ser on ou off"})
		return
	}
	out, err := exec.Command("/usr/local/sbin/2pny-ap-control", action).CombinedOutput()
	msg := strings.TrimSpace(string(out))
	if err != nil {
		if msg == "" {
			msg = err.Error()
		}
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok": false, "error": msg, "active": apActive()})
		return
	}
	time.Sleep(700 * time.Millisecond)
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "message": msg, "active": apActive(), "ssid": "pu2pny", "open": true})
}

func serviceActive(name string) bool {
	return exec.Command("systemctl", "is-active", "--quiet", name).Run() == nil
}

func recentActivity() []string {
	out, err := exec.Command("journalctl", "-u", "2pny-mmdvmhost.service", "-n", "40", "--no-pager", "-o", "short-iso").Output()
	if err != nil {
		return []string{}
	}
	lines := strings.Split(strings.TrimSpace(string(out)), "\n")
	result := make([]string, 0, 20)
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "-- No entries --") {
			continue
		}
		result = append(result, line)
		if len(result) > 20 {
			result = result[len(result)-20:]
		}
	}
	return result
}

func dashboardDataHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	var cfg Config
	if b, err := os.ReadFile(configFile); err == nil {
		_ = json.Unmarshal(b, &cfg)
	}
	hardware := map[string]any{}
	if b, err := os.ReadFile(hardwareProbeFile); err == nil {
		_ = json.Unmarshal(b, &hardware)
	}
	networkRuntime := map[string]any{}
	if b, err := os.ReadFile(filepath.Join(dataDir, "network-radio.json")); err == nil { _ = json.Unmarshal(b, &networkRuntime) }
	if b, err := os.ReadFile("/run/2pny/network-runtime.json"); err == nil { var rt map[string]any; if json.Unmarshal(b,&rt)==nil { for k,v := range rt { networkRuntime[k]=v } } }
	if _, ok := networkRuntime["server_name"]; !ok && cfg.ServerName != "" {
		networkRuntime["server_name"] = cfg.ServerName
	}
	if _, ok := networkRuntime["address"]; !ok && cfg.ServerAddress != "" {
		networkRuntime["address"] = cfg.ServerAddress
	}
	if _, ok := networkRuntime["port"]; !ok && cfg.ServerPort > 0 {
		networkRuntime["port"] = cfg.ServerPort
	}
	if _, ok := networkRuntime["kind"]; !ok && cfg.NetworkKind != "" {
		networkRuntime["kind"] = cfg.NetworkKind
	}
	if _, ok := networkRuntime["module"]; !ok && cfg.XLXModule != "" {
		networkRuntime["module"] = cfg.XLXModule
	}
	baud := strings.TrimSpace(func() string { b, _ := os.ReadFile(filepath.Join(dataDir, "mmdvm-baud")); return string(b) }())
	telemetry := mergedTelemetry()
	netdiag := readPublicJSON("/run/2pny/netdiag.json")
	writeJSON(w, http.StatusOK, map[string]any{
		"name":                 "PU2PNY-OS",
		"version":              appVersion,
		"provisioned":          fileExists(provisionedFile),
		"radio_active":         serviceActive("2pny-mmdvmhost.service"),
		"dmrgateway_active":    serviceActive("2pny-dmrgateway.service"),
		"dstargateway_active":  serviceActive("2pny-dstargateway.service"),
		"ysfgateway_active":    serviceActive("2pny-ysfgateway.service"),
		"p25gateway_active":    serviceActive("2pny-p25gateway.service"),
		"nxdngateway_active":   serviceActive("2pny-nxdngateway.service"),
		"dapnetgateway_active": serviceActive("2pny-dapnetgateway.service"),
		"display_active":       serviceActive("2pny-display-core.service") || serviceActive("2pny-display.service"),
		"display_core_active":  serviceActive("2pny-display-core.service"),
		"mqtt_active":          serviceActive("mosquitto.service"),
		"mdns_active":          serviceActive("avahi-daemon.service"),
		"mmdvm_baud":           baud,
		"config":               cfg,
		"connectivity":         cachedConnectivitySnapshot(),
		"hardware":             hardware,
		"network_runtime":      networkRuntime,
		"display_runtime": func() map[string]any {
			d := map[string]any{}
			if b, e := os.ReadFile(filepath.Join(dataDir, "display-runtime.json")); e == nil {
				_ = json.Unmarshal(b, &d)
			}
			return d
		}(),
		"telemetry": telemetry,
		"netdiag":   netdiag,
	})
}

func pageHandler(path string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if !fileExists(provisionedFile) {
			http.Redirect(w, r, "/wizard", http.StatusFound)
			return
		}
		b, err := os.ReadFile(path)
		if err != nil {
			http.Error(w, "página indisponível", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		_, _ = w.Write(b)
	}
}

func protocolStatusHandler(w http.ResponseWriter, r *http.Request) {
	cfg := Config{}
	if b, err := os.ReadFile(configFile); err == nil {
		_ = json.Unmarshal(b, &cfg)
	}
	nr := readPublicJSON(filepath.Join(dataDir, "network-radio.json"))
	if rt:=readPublicJSON("/run/2pny/network-runtime.json"); len(rt)>0 { for k,v:=range rt { nr[k]=v } }
	p := strings.ToUpper(cfg.Protocol)
	active := false
	gateway := ""
	switch p {
	case "DMR":
		gateway = "DMRGateway"
		active = serviceActive("2pny-dmrgateway.service")
	case "DSTAR":
		gateway = "DStarGateway"
		active = serviceActive("2pny-dstargateway.service")
	case "YSF":
		gateway = "YSFGateway"
		active = serviceActive("2pny-ysfgateway.service")
	case "P25":
		gateway = "P25Gateway"
		active = serviceActive("2pny-p25gateway.service")
	case "NXDN":
		gateway = "NXDNGateway"
		active = serviceActive("2pny-nxdngateway.service")
	case "POCSAG":
		gateway = "DAPNETGateway"
		active = serviceActive("2pny-dapnetgateway.service")
	}
	connected := false
	if v, ok := nr["connected"].(bool); ok { connected = v }
	if v, ok := nr["linked"].(bool); ok && v { connected = true }
	state := "parado"
	if active { state = "gateway_active" }
	if active && connected { state = "connected" }
	writeJSON(w, http.StatusOK, map[string]any{"protocol": p, "active": active, "connected": connected, "state": state, "gateway": gateway,
		"server_name": nr["server_name"], "kind": nr["kind"], "module": nr["module"], "address": nr["address"], "port": nr["port"],
		"link_state": nr["link_state"], "last_command": nr["last_command"], "last_command_target": nr["last_command_target"],
		"last_command_source": nr["last_command_source"]})
}

func protocolApplyHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	var in struct {
		Protocol      string `json:"protocol"`
		ServerName    string `json:"server_name"`
		ServerAddress string `json:"server_address"`
		ServerPort    int    `json:"server_port"`
		NetworkKind   string `json:"network_kind"`
		Module        string `json:"module"`
		ColorCode     int    `json:"color_code"`
		DMRSlot       string `json:"dmr_slot"`
		ESSID          string `json:"essid"`
		Password      string `json:"password"`
	}
	if json.NewDecoder(http.MaxBytesReader(w, r.Body, 16<<10)).Decode(&in) != nil {
		http.Error(w, "JSON inválido", 400)
		return
	}
	in.Protocol = strings.ToUpper(strings.TrimSpace(in.Protocol))
	in.ServerName = strings.TrimSpace(in.ServerName)
	in.ServerAddress = strings.TrimSpace(in.ServerAddress)
	in.NetworkKind = strings.TrimSpace(in.NetworkKind)
	in.Module = strings.ToUpper(strings.TrimSpace(in.Module))
	in.DMRSlot = strings.TrimSpace(in.DMRSlot)
	in.ESSID = strings.TrimSpace(in.ESSID)
	in.Password = strings.TrimSpace(in.Password)
	valid := map[string]bool{"DMR": true, "DSTAR": true, "YSF": true, "P25": true, "NXDN": true, "POCSAG": true}
	if !valid[in.Protocol] || in.ServerName == "" {
		writeJSON(w, 400, map[string]any{"error": "protocolo/servidor inválido"})
		return
	}
	if hasUnsafeControl(in.ServerName) || hasUnsafeControl(in.ServerAddress) || hasUnsafeControl(in.Password) || len(in.ServerName) > 128 || len(in.ServerAddress) > 255 || len(in.Password) > 128 {
		writeJSON(w, 400, map[string]any{"error": "campos inválidos"})
		return
	}
	if in.Protocol == "DSTAR" && (len(in.Module) != 1 || in.Module[0] < 'A' || in.Module[0] > 'Z') {
		writeJSON(w, 400, map[string]any{"error": "selecione módulo D-Star A-Z"})
		return
	}
	if in.Protocol == "DMR" && in.ESSID != "" && !regexp.MustCompile(`^(0[1-9]|[1-9][0-9])$`).MatchString(in.ESSID) {
		writeJSON(w, 400, map[string]any{"error": "identificação DMR deve ser 01 a 99"})
		return
	}
	if in.Protocol != "DMR" {
		in.ESSID = ""
	}
	var cfg Config
	if b, e := os.ReadFile(configFile); e != nil || json.Unmarshal(b, &cfg) != nil {
		writeJSON(w, 409, map[string]any{"error": "configuração inicial ausente"})
		return
	}
	if in.ColorCode < 0 || in.ColorCode > 15 {
		in.ColorCode = cfg.ColorCode
	}
	if in.DMRSlot == "" {
		in.DMRSlot = cfg.DMRSlot
	}
	if in.DMRSlot == "" {
		in.DMRSlot = "2"
	}
	if in.Module == "" {
		in.Module = cfg.XLXModule
	}
	if in.Protocol == "DSTAR" && in.Module == "" {
		in.Module = "D"
	}
	changed := strings.ToUpper(cfg.Protocol) != in.Protocol || cfg.ServerName != in.ServerName || cfg.ServerAddress != in.ServerAddress ||
		cfg.ServerPort != in.ServerPort || cfg.NetworkKind != in.NetworkKind || cfg.XLXModule != in.Module ||
		(in.Protocol == "DMR" && (cfg.ColorCode != in.ColorCode || cfg.DMRSlot != in.DMRSlot || cfg.ESSID != in.ESSID || in.Password != ""))
	if !changed {
		writeJSON(w, 200, map[string]any{"ok": true, "changed": false})
		return
	}
	applyMu.Lock()
	defer applyMu.Unlock()
	args := []string{in.Protocol, in.ServerName, in.ServerAddress, strconv.Itoa(in.ServerPort), in.Password, cfg.UseMode, strconv.Itoa(in.ColorCode), in.DMRSlot, in.Module, in.ESSID, in.NetworkKind, ""}
	out, err := exec.Command("/usr/local/sbin/2pny-protocol-network-apply", args...).CombinedOutput()
	if err != nil {
		msg := strings.TrimSpace(string(out))
		if msg == "" {
			msg = err.Error()
		}
		writeJSON(w, 503, map[string]any{"ok": false, "error": msg})
		return
	}
	cfg.Protocol = in.Protocol
	cfg.ServerName = in.ServerName
	cfg.ServerAddress = in.ServerAddress
	cfg.ServerPort = in.ServerPort
	cfg.NetworkKind = in.NetworkKind
	cfg.XLXModule = in.Module
	cfg.ColorCode = in.ColorCode
	cfg.DMRSlot = in.DMRSlot
	cfg.ESSID = in.ESSID
	cfg.NetworkState = "connecting"
	if err := saveConfig(cfg); err != nil {
		writeJSON(w, 500, map[string]any{"error": "rede aplicada, mas não foi possível salvar resumo"})
		return
	}
	if in.Password != "" {
		secretDir := filepath.Join(dataDir, "protocol-secrets")
		_ = os.MkdirAll(secretDir, 0700)
		_ = os.WriteFile(filepath.Join(secretDir, strings.ToLower(in.Protocol)+".secret"), []byte(in.Password+"\n"), 0600)
	}
	profile := map[string]any{"protocol":in.Protocol,"rx_hz":cfg.RXHz,"tx_hz":cfg.TXHz,"use_mode":cfg.UseMode,
		"server_name":cfg.ServerName,"server_address":cfg.ServerAddress,"server_port":cfg.ServerPort,
		"network_kind":cfg.NetworkKind,"xlx_module":cfg.XLXModule,"color_code":cfg.ColorCode,"dmr_slot":cfg.DMRSlot,"essid":cfg.ESSID}
	if raw,e:=json.Marshal(profile); e==nil {
		cmd:=exec.Command("/usr/local/sbin/2pny-protocol-profiles","save-json");cmd.Stdin=bytes.NewReader(raw);_ = cmd.Run()
	}
	writeJSON(w, 200, map[string]any{"ok": true, "changed": true})
}


func protocolProfilesHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method==http.MethodGet {
		out,err:=exec.Command("/usr/local/sbin/2pny-protocol-profiles","list-json").CombinedOutput()
		if err!=nil { writeJSON(w,503,map[string]any{"error":strings.TrimSpace(string(out))}); return }
		var obj map[string]any
		if json.Unmarshal(out,&obj)!=nil { writeJSON(w,503,map[string]any{"error":"estado dos perfis inválido"}); return }
		writeJSON(w,200,obj);return
	}
	if r.Method!=http.MethodPost || !sameOrigin(r) { http.Error(w,"request rejected",403);return }
	var in struct {
		Action string `json:"action"`
		Protocol string `json:"protocol"`
		RX string `json:"rx"`
		TX string `json:"tx"`
		UseMode string `json:"use_mode"`
		ServerName string `json:"server_name"`
		ServerAddress string `json:"server_address"`
		ServerPort int `json:"server_port"`
		NetworkKind string `json:"network_kind"`
		Module string `json:"module"`
		ColorCode int `json:"color_code"`
		DMRSlot string `json:"dmr_slot"`
		ESSID string `json:"essid"`
		Password string `json:"password"`
	}
	if json.NewDecoder(http.MaxBytesReader(w,r.Body,16<<10)).Decode(&in)!=nil { writeJSON(w,400,map[string]any{"error":"perfil inválido"});return }
	in.Protocol=strings.ToUpper(strings.TrimSpace(in.Protocol));in.UseMode=strings.ToLower(strings.TrimSpace(in.UseMode));in.ESSID=strings.TrimSpace(in.ESSID)
	if in.Protocol=="DMR" && in.ESSID!="" && !regexp.MustCompile(`^(0[1-9]|[1-9][0-9])$`).MatchString(in.ESSID) { writeJSON(w,400,map[string]any{"error":"identificação DMR deve ser 01 a 99"});return }
	if in.Protocol!="DMR" { in.ESSID="" }
	if in.Action=="activate" {
		if !regexp.MustCompile("^(DMR|DSTAR|YSF|P25|NXDN|POCSAG)$").MatchString(in.Protocol) { writeJSON(w,400,map[string]any{"error":"protocolo inválido"});return }
		applyMu.Lock();defer applyMu.Unlock()
		out,err:=exec.Command("/usr/local/sbin/2pny-protocol-profiles","activate",in.Protocol).CombinedOutput()
		if err!=nil { writeJSON(w,503,map[string]any{"error":strings.TrimSpace(string(out))});return }
		var obj map[string]any;_ = json.Unmarshal(out,&obj);if obj==nil { obj=map[string]any{"ok":true} };writeJSON(w,200,obj);return
	}
	if in.Action!="save" { writeJSON(w,400,map[string]any{"error":"ação de perfil inválida"});return }
	rx,rxHz,e:=normalizeFrequency(in.RX);_ = rx
	if e!=nil { writeJSON(w,400,map[string]any{"error":"RX: "+e.Error()});return }
	txHz:=rxHz
	if in.UseMode=="repeater" { _,txHz,e=normalizeFrequency(in.TX);if e!=nil { writeJSON(w,400,map[string]any{"error":"TX: "+e.Error()});return } } else { in.UseMode="hotspot" }
	profile:=map[string]any{"protocol":in.Protocol,"rx_hz":rxHz,"tx_hz":txHz,"use_mode":in.UseMode,
		"server_name":strings.TrimSpace(in.ServerName),"server_address":strings.TrimSpace(in.ServerAddress),"server_port":in.ServerPort,
		"network_kind":strings.TrimSpace(in.NetworkKind),"xlx_module":strings.ToUpper(strings.TrimSpace(in.Module)),
		"color_code":in.ColorCode,"dmr_slot":in.DMRSlot,"essid":in.ESSID}
	raw,_:=json.Marshal(profile);cmd:=exec.Command("/usr/local/sbin/2pny-protocol-profiles","save-json");cmd.Stdin=bytes.NewReader(raw)
	out,err:=cmd.CombinedOutput();if err!=nil { writeJSON(w,503,map[string]any{"error":strings.TrimSpace(string(out))});return }
	if in.Password!="" { d:=filepath.Join(dataDir,"protocol-secrets");_ = os.MkdirAll(d,0700);_ = os.WriteFile(filepath.Join(d,strings.ToLower(in.Protocol)+".secret"),[]byte(in.Password+"\n"),0600) }
	var obj map[string]any;_ = json.Unmarshal(out,&obj);writeJSON(w,200,obj)
}

func brandmeisterAPIKeyHandler(w http.ResponseWriter, r *http.Request) {
	secretDir := filepath.Join(dataDir, "secrets")
	apiPath := filepath.Join(secretDir, "brandmeister-api.key")
	configured := func() bool {
		st, err := os.Stat(apiPath)
		return err == nil && st.Mode().IsRegular() && st.Size() > 0
	}
	if r.Method == http.MethodGet {
		writeJSON(w, 200, map[string]any{"configured": configured()})
		return
	}
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	var in struct {
		Action string `json:"action"`
		APIKey string `json:"api_key"`
	}
	if json.NewDecoder(http.MaxBytesReader(w, r.Body, 8<<10)).Decode(&in) != nil {
		writeJSON(w, 400, map[string]any{"error": "pedido de API BrandMeister inválido"})
		return
	}
	in.Action = strings.ToLower(strings.TrimSpace(in.Action))
	in.APIKey = strings.TrimSpace(in.APIKey)
	switch in.Action {
	case "save":
		if len(in.APIKey) < 32 || len(in.APIKey) > 4096 || strings.ContainsAny(in.APIKey, "\r\n\x00\t ") {
			writeJSON(w, 400, map[string]any{"error": "API Key BrandMeister inválida"})
			return
		}
		if err := os.MkdirAll(secretDir, 0700); err != nil {
			writeJSON(w, 500, map[string]any{"error": "não foi possível preparar armazenamento seguro"})
			return
		}
		tmp, err := os.CreateTemp(secretDir, ".brandmeister-api.*")
		if err != nil {
			writeJSON(w, 500, map[string]any{"error": "não foi possível guardar a API Key"})
			return
		}
		tmpName := tmp.Name()
		ok := false
		defer func() {
			if !ok {
				_ = os.Remove(tmpName)
			}
		}()
		if err = tmp.Chmod(0600); err == nil {
			_, err = tmp.WriteString(in.APIKey + "\n")
		}
		if err == nil {
			err = tmp.Sync()
		}
		if closeErr := tmp.Close(); err == nil {
			err = closeErr
		}
		if err == nil {
			err = os.Rename(tmpName, apiPath)
		}
		if err != nil {
			writeJSON(w, 500, map[string]any{"error": "não foi possível guardar a API Key com segurança"})
			return
		}
		ok = true
	case "remove":
		if err := os.Remove(apiPath); err != nil && !os.IsNotExist(err) {
			writeJSON(w, 500, map[string]any{"error": "não foi possível remover a API Key"})
			return
		}
	default:
		writeJSON(w, 400, map[string]any{"error": "ação de API BrandMeister inválida"})
		return
	}
	if b, err := os.ReadFile(configFile); err == nil {
		var cfg Config
		if json.Unmarshal(b, &cfg) == nil {
			cfg.BMAPIConfigured = configured()
			if err := saveConfig(cfg); err != nil {
				log.Printf("brandmeister api key summary update failed: %v", err)
			}
		}
	}
	writeJSON(w, 200, map[string]any{"ok": true, "configured": configured()})
}

func netdiagHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, readPublicJSON("/run/2pny/netdiag.json"))
}
func historySummaryHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, readPublicJSON("/run/2pny/history-summary.json"))
}

func updateStatusHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method==http.MethodPost {
		if !sameOrigin(r) { http.Error(w,"request rejected",403);return }
		var in struct { Action string `json:"action"`; URL string `json:"url"`; SHA256 string `json:"sha256"`; Version string `json:"version"`; KeepBackup bool `json:"keep_backup"`; Backup string `json:"backup"` }
		if json.NewDecoder(http.MaxBytesReader(w,r.Body,16<<10)).Decode(&in)!=nil { writeJSON(w,400,map[string]any{"error":"pedido de atualização inválido"});return }
		var cmd *exec.Cmd
		switch in.Action {
		case "download":
			cmd=exec.Command("/usr/local/sbin/2pny-update-manager","download",in.URL,in.SHA256,in.Version)
		case "install-staged":
			keep:="0";if in.KeepBackup { keep="1" }
			cmd=exec.Command("/usr/local/sbin/2pny-update-manager","install-staged",in.SHA256,in.Version,keep)
		case "install":
			// Compatibility with older UI: the manager still stages and verifies
			// before touching the live system.
			keep:="0";if in.KeepBackup { keep="1" }
			cmd=exec.Command("/usr/local/sbin/2pny-update-manager","install",in.URL,in.SHA256,in.Version,keep)
		case "rollback": cmd=exec.Command("/usr/local/sbin/2pny-update-manager","rollback",in.Backup)
		case "delete-backup": cmd=exec.Command("/usr/local/sbin/2pny-update-manager","delete-backup",in.Backup)
		default: writeJSON(w,400,map[string]any{"error":"ação de atualização inválida"});return
		}
		go func(){ out,err:=cmd.CombinedOutput();if err!=nil { log.Printf("update action failed: %s",strings.TrimSpace(string(out))) } }()
		writeJSON(w,202,map[string]any{"ok":true,"state":"running"});return
	}
	if r.Method!=http.MethodGet { http.Error(w,"GET or POST required",405);return }
	client:=&http.Client{Timeout:6*time.Second}
	req,_:=http.NewRequest(http.MethodGet,"https://api.github.com/repos/PU2PNY/2PNY-OS/releases?per_page=12",nil);req.Header.Set("User-Agent","PU2PNY-OS/"+appVersion)
	resp,err:=client.Do(req)
	updater:=map[string]any{"state":"idle","backups":[]any{}}
	if out,e:=exec.Command("/usr/local/sbin/2pny-update-manager","status").CombinedOutput();e==nil { _=json.Unmarshal(out,&updater) }
	if err!=nil { writeJSON(w,503,map[string]any{"current":appVersion,"error":"catálogo de atualizações indisponível","updater":updater});return }
	defer resp.Body.Close();if resp.StatusCode!=200 { writeJSON(w,503,map[string]any{"current":appVersion,"error":"GitHub respondeu "+resp.Status,"updater":updater});return }
	type asset struct { Name string `json:"name"`; URL string `json:"browser_download_url"`; Digest string `json:"digest"` }
	var releases []struct { Tag string `json:"tag_name"`;Name string `json:"name"`;Body string `json:"body"`;HTML string `json:"html_url"`;Draft bool `json:"draft"`;Prerelease bool `json:"prerelease"`;Assets []asset `json:"assets"` }
	if json.NewDecoder(http.MaxBytesReader(w,resp.Body,2<<20)).Decode(&releases)!=nil { writeJSON(w,503,map[string]any{"current":appVersion,"error":"catálogo inválido","updater":updater});return }
	items:=[]map[string]any{}
	for _,rel:=range releases {
		if rel.Draft { continue }
		version:=strings.TrimPrefix(rel.Tag,"v");bundleURL:="";bundleSHA:=""
		for _,a:=range rel.Assets {
			if strings.Contains(a.Name,"-update.tar.gz") { bundleURL=a.URL;if strings.HasPrefix(a.Digest,"sha256:"){bundleSHA=strings.TrimPrefix(a.Digest,"sha256:")} }
		}
		notes:=strings.TrimSpace(rel.Body);if len(notes)>300 { notes=notes[:300]+"…" }
		items=append(items,map[string]any{"version":version,"name":rel.Name,"notes":notes,"url":rel.HTML,"prerelease":rel.Prerelease,"bundle_url":bundleURL,"bundle_sha256":bundleSHA,"installable":bundleURL!=""&&bundleSHA!=""})
	}
	latest:="";if len(items)>0 { latest,_=items[0]["version"].(string) }
	writeJSON(w,200,map[string]any{"current":appVersion,"latest":latest,"available":latest!=""&&latest!=appVersion,"releases":items,"updater":updater})
}

func runPrivilegedRequest(service, requestPath, resultPath string, payload map[string]any) (map[string]any, error) {
	if err := os.MkdirAll(filepath.Dir(requestPath), 0750); err != nil {
		return nil, err
	}
	pathUnit := strings.TrimSuffix(service, ".service") + ".path"
	if err := exec.Command("systemctl", "is-active", "--quiet", pathUnit).Run(); err != nil {
		return nil, fmt.Errorf("mecanismo privilegiado indisponível: %s", pathUnit)
	}
	// Remove the previous result before publishing the new request. The .path
	// unit watches the atomic rename below and starts only the dedicated root
	// helper; the web daemon never receives generic systemctl/root privilege.
	_ = os.Remove(resultPath)
	raw, _ := json.Marshal(payload)
	tmp := requestPath + ".tmp"
	if err := os.WriteFile(tmp, raw, 0600); err != nil {
		return nil, err
	}
	if err := os.Rename(tmp, requestPath); err != nil {
		return nil, err
	}
	deadline := time.Now().Add(20 * time.Second)
	for time.Now().Before(deadline) {
		if b, err := os.ReadFile(resultPath); err == nil {
			var res map[string]any
			if json.Unmarshal(b, &res) == nil {
				if ok, _ := res["ok"].(bool); !ok {
					msg, _ := res["error"].(string)
					if msg == "" {
						msg = "operação privilegiada falhou"
					}
					return res, fmt.Errorf("%s", msg)
				}
				return res, nil
			}
		}
		time.Sleep(120 * time.Millisecond)
	}
	return nil, fmt.Errorf("%s não confirmou a operação dentro do limite", service)
}

func runTimezoneRequest(tz string) (map[string]any, error) {
	if err := os.MkdirAll("/run/2pny", 0750); err != nil {
		return nil, err
	}
	if err := exec.Command("systemctl", "is-active", "--quiet", "2pny-timezone-apply.path").Run(); err != nil {
		return nil, fmt.Errorf("mecanismo privilegiado de fuso indisponível")
	}
	// SEC-024: unique files avoid stale-result races and give PathExistsGlob a
	// fresh object for every operation without granting systemctl/root to 2pnyd.
	requestID := fmt.Sprintf("%d", time.Now().UnixNano())
	requestPath := filepath.Join("/run/2pny", "timezone-request-"+requestID+".json")
	resultPath := filepath.Join("/run/2pny", "timezone-result-"+requestID+".json")
	payload := map[string]any{"request_id": requestID, "timezone": tz}
	raw, _ := json.Marshal(payload)
	tmp := requestPath + ".tmp"
	if err := os.WriteFile(tmp, raw, 0600); err != nil {
		return nil, err
	}
	if err := os.Rename(tmp, requestPath); err != nil {
		_ = os.Remove(tmp)
		return nil, err
	}
	defer os.Remove(requestPath)
	defer os.Remove(resultPath)

	deadline := time.Now().Add(20 * time.Second)
	for time.Now().Before(deadline) {
		if b, err := os.ReadFile(resultPath); err == nil {
			var res map[string]any
			if json.Unmarshal(b, &res) == nil {
				if rid, _ := res["request_id"].(string); rid != requestID {
					return res, fmt.Errorf("resposta de fuso não corresponde ao pedido")
				}
				if ok, _ := res["ok"].(bool); !ok {
					msg, _ := res["error"].(string)
					if msg == "" { msg = "operação de fuso falhou" }
					return res, fmt.Errorf("%s", msg)
				}
				return res, nil
			}
		}
		time.Sleep(100 * time.Millisecond)
	}
	return nil, fmt.Errorf("2pny-timezone-apply não confirmou a operação dentro do limite")
}

func systemControlHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet {
		tz := strings.TrimSpace(string(func() []byte {
			b, _ := exec.Command("timedatectl", "show", "-p", "Timezone", "--value").Output()
			return b
		}()))
		syncv := strings.TrimSpace(string(func() []byte {
			b, _ := exec.Command("timedatectl", "show", "-p", "NTPSynchronized", "--value").Output()
			return b
		}()))
		voice := readPublicJSON(filepath.Join(dataDir, "voice-settings.json"))
		writeJSON(w, 200, map[string]any{"timezone": tz, "ntp_synchronized": syncv == "yes", "local": time.Now().Format(time.RFC3339), "utc": time.Now().UTC().Format(time.RFC3339), "operational": serviceActive("2pny-mmdvmhost.service"), "voice": voice, "voice_hourly": fileExists(filepath.Join(dataDir, "voice-hourly.enabled"))})
		return
	}
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", 403)
		return
	}
	var in struct {
		Action   string `json:"action"`
		Timezone string `json:"timezone"`
		Enabled  bool   `json:"enabled"`
		Hourly   bool   `json:"hourly"`
		Language string `json:"language"`
	}
	if json.NewDecoder(http.MaxBytesReader(w, r.Body, 4096)).Decode(&in) != nil {
		http.Error(w, "JSON inválido", 400)
		return
	}
	switch in.Action {
	case "timezone":
		tz := strings.TrimSpace(in.Timezone)
		if tz == "" || strings.Contains(tz, "..") || strings.HasPrefix(tz, "/") || !fileExists(filepath.Join("/usr/share/zoneinfo", tz)) {
			writeJSON(w, 400, map[string]any{"error": "fuso horário inválido"})
			return
		}
		res, err := runTimezoneRequest(tz)
		if err != nil {
			writeJSON(w, 500, map[string]any{"error": "Não foi possível aplicar o fuso horário com segurança.", "detail": err.Error(), "result": res})
			return
		}
		out, _ := exec.Command("timedatectl", "show", "-p", "Timezone", "--value").Output()
		effective := strings.TrimSpace(string(out))
		if effective != tz {
			writeJSON(w, 500, map[string]any{"error": "O sistema não confirmou o novo fuso horário.", "effective": effective})
			return
		}
	case "sync-google":
		_ = os.MkdirAll("/etc/systemd/timesyncd.conf.d", 0755)
		if e := os.WriteFile("/etc/systemd/timesyncd.conf.d/pu2pny-google.conf", []byte("[Time]\nNTP=time.google.com time1.google.com time2.google.com time3.google.com\nFallbackNTP=pool.ntp.org\n"), 0644); e != nil {
			writeJSON(w, 500, map[string]any{"error": e.Error()})
			return
		}
		_ = exec.Command("timedatectl", "set-ntp", "true").Run()
		_ = exec.Command("systemctl", "restart", "systemd-timesyncd.service").Run()
	case "voice-settings":
		lang := strings.ToLower(strings.TrimSpace(in.Language))
		if lang != "pt" && lang != "en" && lang != "es" {
			lang = "pt"
		}
		raw, _ := json.Marshal(map[string]any{"enabled": in.Enabled, "language": lang})
		if err := os.WriteFile(filepath.Join(dataDir, "voice-settings.json"), raw, 0600); err != nil {
			writeJSON(w, 500, map[string]any{"error": "falha ao salvar voz"})
			return
		}
		marker := filepath.Join(dataDir, "voice-hourly.enabled")
		if in.Hourly {
			_ = os.WriteFile(marker, []byte("1\n"), 0600)
		} else {
			_ = os.Remove(marker)
		}
		if serviceActive("2pny-dmrgateway.service") {
			_ = exec.Command("systemctl", "restart", "2pny-dmrgateway.service").Run()
		}
	case "operational-off":
		res, e := runPrivilegedRequest("2pny-operational-apply.service", "/run/2pny/operational-request.json", "/run/2pny/operational-result.json", map[string]any{"action": "off"})
		if e != nil {
			writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok": false, "error": "Não foi possível desligar o operacional com confirmação.", "detail": e.Error(), "result": res})
			return
		}
		writeJSON(w, http.StatusOK, res)
		return
	case "operational-on":
		res, e := runPrivilegedRequest("2pny-operational-apply.service", "/run/2pny/operational-request.json", "/run/2pny/operational-result.json", map[string]any{"action": "on"})
		if e != nil {
			writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok": false, "error": "O operacional não ficou ativo.", "detail": e.Error(), "result": res})
			return
		}
		writeJSON(w, http.StatusOK, res)
		return
	case "reboot":
		go func() { time.Sleep(800 * time.Millisecond); _ = exec.Command("systemctl", "reboot").Run() }()
	case "poweroff":
		go func() { time.Sleep(800 * time.Millisecond); _ = exec.Command("systemctl", "poweroff").Run() }()
	default:
		writeJSON(w, 400, map[string]any{"error": "ação inválida"})
		return
	}
	writeJSON(w, 200, map[string]any{"ok": true})
}

func dashboardHandler(w http.ResponseWriter, r *http.Request) {
	if !fileExists(provisionedFile) {
		http.Redirect(w, r, "/wizard", http.StatusFound)
		return
	}
	b, err := os.ReadFile(dashboardFile)
	if err != nil {
		http.Error(w, "painel indisponível", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(b)
}

func healthzHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("PU2PNY OK\n"))
}

func wizardHandler(w http.ResponseWriter, r *http.Request) {
	b, err := os.ReadFile(wizardFile)
	if err != nil {
		http.Error(w, "assistente indisponível", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(b)
}

func captiveAPIHandler(w http.ResponseWriter, r *http.Request) {
	host := r.Host
	base := "http://10.43.0.1"
	if strings.HasPrefix(host, "10.43.0.") {
		base = "http://10.43.0.1"
	} else if strings.Contains(host, "pu2pny") {
		base = "http://pu2pny.local"
	}
	w.Header().Set("Content-Type", "application/captive+json")
	w.Header().Set("Cache-Control", "no-store")
	_ = json.NewEncoder(w).Encode(map[string]any{
		"captive":         !fileExists(provisionedFile),
		"user-portal-url": base + "/wizard",
	})
}

func captivePortalHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store, no-cache, must-revalidate")
	w.Header().Set("Pragma", "no-cache")
	w.Header().Set("Expires", "0")
	if !fileExists(provisionedFile) {
		// Use an absolute local URL. Clients probe with foreign Host headers
		// (Microsoft/Google/Apple); a relative redirect can keep that probe host
		// in the address bar even though DNS is intercepted.
		http.Redirect(w, r, "http://10.43.0.1/wizard?captive=1", http.StatusFound)
		return
	}
	switch r.URL.Path {
	case "/generate_204", "/gen_204":
		w.WriteHeader(http.StatusNoContent)
	case "/connecttest.txt":
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		_, _ = w.Write([]byte("Microsoft Connect Test"))
	case "/ncsi.txt":
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		_, _ = w.Write([]byte("Microsoft NCSI"))
	case "/hotspot-detect.html", "/library/test/success.html":
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = w.Write([]byte("<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>"))
	case "/canonical.html", "/success.txt":
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		_, _ = w.Write([]byte("success\n"))
	case "/check_network_status.txt", "/connectivity-check.html":
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		_, _ = w.Write([]byte("NetworkManager is online\n"))
	default:
		http.Redirect(w, r, "/wizard", http.StatusFound)
	}
}

func readPublicJSON(path string) map[string]any {
	d := map[string]any{}
	if b, e := os.ReadFile(path); e == nil {
		json.Unmarshal(b, &d)
	}
	return d
}
func sameOrigin(r *http.Request) bool {
	o := r.Header.Get("Origin")
	if o == "" {
		return true
	}
	u, e := url.Parse(o)
	return e == nil && u.Host == r.Host
}
func stationSettingsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet {
		writeJSON(w, 200, map[string]any{"qrz_configured": fileExists("/var/lib/2pny/secrets/qrz.json"), "ssh_active": serviceActive("ssh.service")})
		return
	}
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", 403)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 8192)
	var in struct {
		Action   string `json:"action"`
		Username string `json:"username"`
		Password string `json:"password"`
		Key      string `json:"key"`
	}
	if json.NewDecoder(r.Body).Decode(&in) != nil {
		http.Error(w, "invalid JSON", 400)
		return
	}
	switch in.Action {
	case "qrz":
		if in.Username == "" || in.Password == "" {
			http.Error(w, "Informe usuário e senha QRZ", 400)
			return
		}
		os.MkdirAll("/var/lib/2pny/secrets", 0700)
		b, _ := json.Marshal(map[string]string{"username": in.Username, "password": in.Password})
		if e := os.WriteFile("/var/lib/2pny/secrets/qrz.json", b, 0600); e != nil {
			http.Error(w, "save failed", 500)
			return
		}
	case "qrz-remove":
		os.Remove("/var/lib/2pny/secrets/qrz.json")
	case "ssh-enable", "ssh-disable":
		if in.Action == "ssh-enable" {
			key := strings.TrimSpace(in.Key)
			valid := regexp.MustCompile("^(ssh-(ed25519|rsa)|ecdsa-sha2-nistp(256|384|521))[[:space:]]+[A-Za-z0-9+/=]+([[:space:]].*)?$")
			if !valid.MatchString(key) {
				writeJSON(w, 400, map[string]any{"error": "Chave pública SSH inválida. Use uma linha OpenSSH completa, como ssh-ed25519 AAAA... computador"})
				return
			}
			in.Key = key
		}
		res, e := runPrivilegedRequest("2pny-ssh-apply.service", "/run/2pny/ssh-request.json", "/run/2pny/ssh-result.json", map[string]any{"action": in.Action, "key": in.Key})
		if e != nil {
			writeJSON(w, 400, map[string]any{"error": e.Error(), "result": res})
			return
		}
	default:
		http.Error(w, "unknown action", 400)
		return
	}
	writeJSON(w, 200, map[string]any{"ok": true})
}

func ensureAPRSDefaults() map[string]any {
	const settingsPath = "/var/lib/2pny/aprs-settings.json"
	settings := readPublicJSON(settingsPath)
	if len(settings) > 0 {
		return settings
	}
	var cfg Config
	if b, err := os.ReadFile(configFile); err != nil || json.Unmarshal(b, &cfg) != nil || strings.TrimSpace(cfg.Callsign) == "" {
		return settings
	}
	// APRS-012: messaging is ready after onboarding without inventing a
	// position. Latitude/longitude are deliberately absent until the operator
	// supplies real coordinates.
	settings = map[string]any{
		"enabled": true, "callsign": strings.ToUpper(strings.TrimSpace(cfg.Callsign)),
		"server": "soam.aprs2.net", "port": 14580, "ssid": 10,
		"interval_seconds": 1800, "comment": "PU2PNY-OS hotspot",
		"symbol_table": "/", "symbol": "r",
	}
	raw, _ := json.MarshalIndent(settings, "", "  ")
	tmp := settingsPath + ".tmp"
	if os.WriteFile(tmp, raw, 0600) == nil {
		if os.Rename(tmp, settingsPath) == nil {
			_ = exec.Command("systemctl", "restart", "2pny-aprs.service").Run()
		}
	}
	return settings
}

func aprsSettingsHandler(w http.ResponseWriter, r *http.Request) {
	const settingsPath = "/var/lib/2pny/aprs-settings.json"
	const statusPath = "/run/2pny/aprs-status.json"
	if r.Method == http.MethodGet {
		settings := ensureAPRSDefaults()
		if _, ok := settings["callsign"]; !ok {
			var cfg Config
			if b, err := os.ReadFile(configFile); err == nil && json.Unmarshal(b, &cfg) == nil && cfg.Callsign != "" {
				settings["callsign"] = cfg.Callsign
			}
		}
		writeJSON(w, http.StatusOK, map[string]any{"settings": settings, "status": readPublicJSON(statusPath), "service_active": serviceActive("2pny-aprs.service")})
		return
	}
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 8192)
	var in struct {
		Enabled         bool     `json:"enabled"`
		Latitude        *float64 `json:"latitude"`
		Longitude       *float64 `json:"longitude"`
		Server          string   `json:"server"`
		Port            int     `json:"port"`
		IntervalSeconds int     `json:"interval_seconds"`
		Comment         string  `json:"comment"`
		SymbolTable     string  `json:"symbol_table"`
		Symbol          string  `json:"symbol"`
		SSID            int     `json:"ssid"`
	}
	if json.NewDecoder(r.Body).Decode(&in) != nil {
		http.Error(w, "invalid JSON", http.StatusBadRequest)
		return
	}
	in.Server = strings.TrimSpace(in.Server)
	in.Comment = strings.TrimSpace(in.Comment)
	if in.Server == "" {
		in.Server = "soam.aprs2.net"
	}
	if in.Port == 0 {
		in.Port = 14580
	}
	if in.IntervalSeconds == 0 {
		in.IntervalSeconds = 1800
	}
	if in.SymbolTable == "" {
		in.SymbolTable = "/"
	}
	if in.Symbol == "" {
		in.Symbol = "r"
	}
	if in.SSID < 0 || in.SSID > 15 {
		http.Error(w, "SSID APRS deve ficar entre 0 e 15", http.StatusBadRequest)
		return
	}
	if len(in.Server) > 255 || hasUnsafeControl(in.Server) || in.Port < 1 || in.Port > 65535 {
		http.Error(w, "Servidor APRS-IS inválido", http.StatusBadRequest)
		return
	}
	if in.IntervalSeconds < 300 || in.IntervalSeconds > 86400 {
		http.Error(w, "Intervalo APRS deve ficar entre 300 e 86400 segundos", http.StatusBadRequest)
		return
	}
	if (in.Latitude == nil) != (in.Longitude == nil) {
		http.Error(w, "Informe latitude e longitude juntas ou deixe ambas vazias", http.StatusBadRequest)
		return
	}
	if in.Latitude != nil && (*in.Latitude < -90 || *in.Latitude > 90 || *in.Longitude < -180 || *in.Longitude > 180) {
		http.Error(w, "Latitude/longitude inválidas", http.StatusBadRequest)
		return
	}
	if len(in.Comment) > 60 || len(in.SymbolTable) != 1 || len(in.Symbol) != 1 || hasUnsafeControl(in.Comment) {
		http.Error(w, "Configuração APRS inválida", http.StatusBadRequest)
		return
	}
	var cfg Config
	if b, err := os.ReadFile(configFile); err != nil || json.Unmarshal(b, &cfg) != nil || cfg.Callsign == "" {
		http.Error(w, "Configure o indicativo do hotspot antes do APRS", http.StatusConflict)
		return
	}
	obj := map[string]any{
		"enabled": in.Enabled, "callsign": cfg.Callsign,
		"server": in.Server, "port": in.Port, "interval_seconds": in.IntervalSeconds, "comment": in.Comment,
		"symbol_table": in.SymbolTable, "symbol": in.Symbol, "ssid": in.SSID,
	}
	if in.Latitude != nil {
		obj["latitude"] = *in.Latitude
		obj["longitude"] = *in.Longitude
	}
	raw, _ := json.MarshalIndent(obj, "", "  ")
	tmp := settingsPath + ".tmp"
	if err := os.WriteFile(tmp, raw, 0600); err != nil {
		http.Error(w, "Falha ao salvar APRS", 500)
		return
	}
	if err := os.Rename(tmp, settingsPath); err != nil {
		http.Error(w, "Falha ao aplicar APRS", 500)
		return
	}
	action := "restart"
	if !in.Enabled {
		action = "stop"
	}
	if out, err := exec.Command("systemctl", action, "2pny-aprs.service").CombinedOutput(); err != nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok": false, "error": strings.TrimSpace(string(out))})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "enabled": in.Enabled})
}

func aprsMessageHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost || !sameOrigin(r) {
		http.Error(w, "request rejected", http.StatusForbidden)
		return
	}
	var in struct {
		To   string `json:"to"`
		Text string `json:"text"`
	}
	if json.NewDecoder(http.MaxBytesReader(w, r.Body, 4096)).Decode(&in) != nil {
		http.Error(w, "JSON inválido", 400)
		return
	}
	to := strings.ToUpper(strings.TrimSpace(in.To))
	msg := strings.TrimSpace(in.Text)
	if !regexp.MustCompile(`^[A-Z0-9]{1,6}(?:-[0-9]{1,2})?$`).MatchString(to) {
		writeJSON(w, 400, map[string]any{"error": "destino APRS inválido"})
		return
	}
	if msg == "" || len(msg) > 60 || hasUnsafeControl(msg) {
		writeJSON(w, 400, map[string]any{"error": "mensagem deve ter 1 a 60 caracteres"})
		return
	}

	settings := ensureAPRSDefaults()
	enabled, _ := settings["enabled"].(bool)
	if !enabled {
		writeJSON(w, http.StatusConflict, map[string]any{"error": "APRS-IS está desativado nas configurações. Ative-o para enviar mensagens."})
		return
	}

	dir := "/var/lib/2pny/aprs-outbox"
	if err := os.MkdirAll(dir, 0700); err != nil {
		writeJSON(w, 500, map[string]any{"error": "não foi possível abrir a caixa de saída"})
		return
	}
	now := time.Now()
	queueID := fmt.Sprintf("%d-%d", now.UnixNano(), os.Getpid())
	messageID := fmt.Sprintf("%05d", now.UnixNano()/1e6%100000)
	raw, _ := json.Marshal(map[string]any{"to": to, "text": msg, "id": messageID})
	tmp := filepath.Join(dir, "."+queueID+".tmp")
	dst := filepath.Join(dir, queueID+".json")
	if err := os.WriteFile(tmp, raw, 0600); err != nil {
		writeJSON(w, 500, map[string]any{"error": "falha ao enfileirar mensagem"})
		return
	}
	if err := os.Rename(tmp, dst); err != nil {
		_ = os.Remove(tmp)
		writeJSON(w, 500, map[string]any{"error": "falha ao publicar mensagem"})
		return
	}
	status := readPublicJSON("/run/2pny/aprs-status.json")
	verified, _ := status["verified"].(bool)
	delivery := "waiting_connection"
	if verified {
		delivery = "queued_for_send"
	}
	writeJSON(w, 200, map[string]any{
		"ok": true, "queued": true, "message_id": messageID,
		"verified": verified, "delivery": delivery,
	})
}

func directProxyHandler(localPath string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet && r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if r.Method == http.MethodPost && !sameOrigin(r) {
			http.Error(w, "request rejected", http.StatusForbidden)
			return
		}
		if !serviceActive("2pny-direct.service") {
			_ = exec.Command("systemctl", "start", "2pny-direct.service").Run()
			time.Sleep(220 * time.Millisecond)
		}
		var body []byte
		if r.Method == http.MethodPost {
			var err error
			body, err = io.ReadAll(http.MaxBytesReader(w, r.Body, 8192))
			if err != nil {
				http.Error(w, "invalid body", http.StatusBadRequest)
				return
			}
		}
		req, err := http.NewRequest(r.Method, "http://127.0.0.1:43071"+localPath, bytes.NewReader(body))
		if err != nil {
			http.Error(w, "Direct unavailable", http.StatusServiceUnavailable)
			return
		}
		req.Header.Set("Content-Type", "application/json")
		client := &http.Client{Timeout: 15 * time.Second}
		resp, err := client.Do(req)
		if err != nil {
			writeJSON(w, http.StatusServiceUnavailable, map[string]any{"error": "PU2PNY Direct indisponível", "detail": err.Error()})
			return
		}
		defer resp.Body.Close()
		out, _ := io.ReadAll(io.LimitReader(resp.Body, 65536))
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		w.WriteHeader(resp.StatusCode)
		_, _ = w.Write(out)
	}
}

func main() {
	if err := os.MkdirAll(dataDir, 0750); err != nil {
		log.Fatal(err)
	}
	go watchLiveState("/run/2pny/live-state.json")
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		if fileExists(provisionedFile) {
			http.Redirect(w, r, "/dashboard", http.StatusFound)
		} else {
			http.Redirect(w, r, "/wizard", http.StatusFound)
		}
	})
	http.HandleFunc("/wizard", wizardHandler)
	http.HandleFunc("/dashboard", dashboardHandler)
	http.HandleFunc("/live", dashboardHandler)
	http.HandleFunc("/hotspot", pageHandler(hotspotFile))
	http.HandleFunc("/display", pageHandler(displayFile))
	http.HandleFunc("/internet", pageHandler(internetFile))
	http.HandleFunc("/protocols", func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, "/hotspot#protocols", http.StatusFound) })
	http.HandleFunc("/protocols/embed", pageHandler(protocolsFile))
	http.HandleFunc("/history", pageHandler(historyFile))
	http.HandleFunc("/aprs", pageHandler(aprsFile))
	http.HandleFunc("/system", pageHandler(systemFile))
	http.HandleFunc("/expert", pageHandler(expertFile))
	http.HandleFunc("/radioid", pageHandler(radioIDFile))
	http.HandleFunc("/direct", pageHandler(directFile))
	http.HandleFunc("/admin", func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, "/dashboard", http.StatusFound) })
	http.HandleFunc("/ui-language.js", func(w http.ResponseWriter, r *http.Request) { http.ServeFile(w, r, "/usr/share/2pny/ui-language.js") })
	http.HandleFunc("/ui-0.3.0.css", func(w http.ResponseWriter, r *http.Request) { http.ServeFile(w, r, "/usr/share/2pny/ui-0.3.0.css") })
	http.HandleFunc("/ui-common-0.3.0.js", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "/usr/share/2pny/ui-common-0.3.0.js")
	})
	http.HandleFunc("/api/status", statusHandler)
	http.HandleFunc("/api/dashboard", dashboardDataHandler)
	http.HandleFunc("/api/connectivity", connectivityHandler)
	http.HandleFunc("/api/wifi/scan", wifiScanHandler)
	http.HandleFunc("/api/network/country", networkCountryHandler)
	http.HandleFunc("/api/network/connect", networkConnectHandler)
	http.HandleFunc("/api/network/connect/status", networkConnectStatusHandler)
	http.HandleFunc("/api/network/refresh", networkRefreshHandler)
	http.HandleFunc("/api/network/wifi/profiles", wifiProfilesHandler)
	http.HandleFunc("/api/network/dns", networkDNSHandler)
	http.HandleFunc("/api/maintenance", maintenanceHandler)
	http.HandleFunc("/api/hardware", hardwareHandler)
	http.HandleFunc("/api/hardware/status", hardwareStatusHandler)
	http.HandleFunc("/api/hardware/scan", hardwareScanHandler)
	http.HandleFunc("/api/display/override", displayOverrideHandler)
	http.HandleFunc("/api/display/detection", displayDetectionHandler)
	http.HandleFunc("/api/diagnostics", diagnosticsHandler)
	http.HandleFunc("/api/config", publicConfigHandler)
	http.HandleFunc("/api/servers", serversHandler)
	http.HandleFunc("/api/protocol/status", protocolStatusHandler)
	http.HandleFunc("/api/protocol/apply", protocolApplyHandler)
	http.HandleFunc("/api/protocol/profiles", protocolProfilesHandler)
	http.HandleFunc("/api/brandmeister/api-key", brandmeisterAPIKeyHandler)
	http.HandleFunc("/api/netdiag", netdiagHandler)
	http.HandleFunc("/api/history/summary", historySummaryHandler)
	http.HandleFunc("/api/system", systemControlHandler)
	http.HandleFunc("/api/update", updateStatusHandler)
	http.HandleFunc("/api/live", liveStatusHandler)
	http.HandleFunc("/api/live/events", liveEventsHandler)
	http.HandleFunc("/api/station/settings", stationSettingsHandler)
	http.HandleFunc("/api/aprs", aprsSettingsHandler)
	http.HandleFunc("/api/aprs/message", aprsMessageHandler)
	http.HandleFunc("/api/direct", directProxyHandler("/status"))
	http.HandleFunc("/api/direct/peers", directProxyHandler("/peers"))
	http.HandleFunc("/api/direct/pair", directProxyHandler("/pair"))
	http.HandleFunc("/api/direct/unpair", directProxyHandler("/unpair"))
	http.HandleFunc("/api/direct/call", directProxyHandler("/call"))
	http.HandleFunc("/api/direct/hangup", directProxyHandler("/hangup"))
	http.HandleFunc("/api/contacts", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, readPublicJSON("/run/2pny/contacts.json"))
	})
	http.Handle("/operator-photo/", http.StripPrefix("/operator-photo/", http.FileServer(http.Dir("/var/cache/2pny/photos"))))
	http.Handle("/flags/", http.StripPrefix("/flags/", http.FileServer(http.Dir("/usr/share/2pny/flags"))))
	http.HandleFunc("/api/basic/apply", basicApplyHandler)
	http.HandleFunc("/api/rf", rfStatusHandler)
	http.HandleFunc("/api/rf/apply", rfApplyHandler)
	http.HandleFunc("/api/rf/power", rfPowerHandler)
	http.HandleFunc("/api/modules", moduleStatusHandler)
	http.HandleFunc("/api/ap", apControlHandler)
	http.HandleFunc("/healthz", healthzHandler)
	http.HandleFunc("/captive-api", captiveAPIHandler)
	for _, p := range []string{"/generate_204", "/gen_204", "/hotspot-detect.html", "/library/test/success.html", "/connecttest.txt", "/ncsi.txt", "/canonical.html", "/success.txt", "/check_network_status.txt", "/connectivity-check.html", "/redirect"} {
		http.HandleFunc(p, captivePortalHandler)
	}
	log.Printf("PU2PNY-OS %s listening on %s", appVersion, listenAddr)
	log.Fatal(http.ListenAndServe(listenAddr, nil))
}
