package main

import (
	"bytes"
	"encoding/json"
 "net/url"
	"fmt"
	"log"
	"net"
	"net/http"
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
	dataDir         = "/var/lib/2pny"
	configFile      = "/var/lib/2pny/config.json"
	provisionedFile = "/var/lib/2pny/provisioned"
	listenAddr      = "0.0.0.0:80"
	appVersion      = "0.2.9-alpha"
	hardwareFile    = "/var/lib/2pny/hardware.json"
	hardwareProbeFile = "/var/lib/2pny/hardware-probe.json"
	hardwareScanStateFile = "/run/2pny/hardware-scan-state.json"
	rfApplyStateFile  = "/var/lib/2pny/rf-apply-state.json"
	wizardFile        = "/usr/share/2pny/wizard.html"
	dashboardFile     = "/usr/share/2pny/dashboard.html"
	wifiScanStateFile = "/var/lib/2pny/wifi-scan.json"
	displayOverrideFile = "/var/lib/2pny/display-override.json"
)

type Config struct {
	Callsign      string `json:"callsign"`
	DMRID         string `json:"dmr_id"`
	WiFiSSID      string `json:"wifi_ssid,omitempty"`
	UseMode       string `json:"use_mode"`
	RXHz          int64  `json:"rx_hz"`
	TXHz          int64  `json:"tx_hz"`
	RXOffsetHz    int64  `json:"rx_offset_hz"`
	TXOffsetHz    int64  `json:"tx_offset_hz"`
	Protocol      string `json:"protocol"`
	Operation     string `json:"operation"`
	ServerName    string `json:"server_name,omitempty"`
	ServerAddress string `json:"server_address,omitempty"`
	ServerPort    int    `json:"server_port,omitempty"`
	NetworkKind   string `json:"network_kind,omitempty"`
	ColorCode     int    `json:"color_code,omitempty"`
	DMRSlot       string `json:"dmr_slot,omitempty"`
	XLXModule     string `json:"xlx_module,omitempty"`
	ESSID         string `json:"essid,omitempty"`
	BMAPIConfigured bool `json:"bm_api_configured,omitempty"`
	NetworkState  string `json:"network_state,omitempty"`
	CreatedAt     string `json:"created_at"`
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

func (h *liveStateHub) publish(data []byte) {
	if len(data) == 0 || !json.Valid(data) { return }
	h.mu.Lock()
	if bytes.Equal(h.snapshot, data) { h.mu.Unlock(); return }
	h.sequence++
	h.snapshot = append(h.snapshot[:0], data...)
	event := liveEvent{id:h.sequence, data:append([]byte(nil), data...)}
	for ch := range h.subscribers {
		select {
		case ch <- event:
		default:
			select { case <-ch: default: }
			select { case ch <- event: default: }
		}
	}
	h.mu.Unlock()
}

func (h *liveStateHub) current() liveEvent {
	h.mu.RLock(); defer h.mu.RUnlock()
	return liveEvent{id:h.sequence, data:append([]byte(nil), h.snapshot...)}
}

func watchLiveState(path string) {
	var lastMod time.Time
	var lastSize int64 = -1
	for {
		if stat, err := os.Stat(path); err == nil && (stat.ModTime() != lastMod || stat.Size() != lastSize) {
			if data, err := os.ReadFile(path); err == nil {
				liveHub.publish(data); lastMod, lastSize = stat.ModTime(), stat.Size()
			}
		}
		time.Sleep(80 * time.Millisecond)
	}
}

type ConnectivityStatus struct {
	Internet         bool     `json:"internet"`
	InternetLatencyMS int64   `json:"internet_latency_ms,omitempty"`
	InternetQuality string    `json:"internet_quality"`
	DefaultInterface string   `json:"default_interface,omitempty"`
	Ethernet         bool     `json:"ethernet"`
	EthernetInterface string  `json:"ethernet_interface,omitempty"`
	WiFi             bool     `json:"wifi"`
	WiFiSSID         string   `json:"wifi_ssid"`
	WiFiInterfaces   []string `json:"wifi_interfaces"`
	WiFiCount        int      `json:"wifi_count"`
	ClientInterface  string   `json:"client_interface,omitempty"`
	APActive         bool     `json:"ap_active"`
	APInterface      string   `json:"ap_interface,omitempty"`
	APSSID           string   `json:"ap_ssid"`
	IPv4             []string `json:"ipv4"`
}

type RFApplyState struct {
	State   string `json:"state"`
	Message string `json:"message"`
	Updated string `json:"updated"`
}

var (
	callsignRx = regexp.MustCompile(`^[A-Z0-9/-]{3,16}$`)
	dmrRx      = regexp.MustCompile(`^[0-9]{6,9}$`)
	applyMu    sync.Mutex
	hardwareScanMu sync.Mutex
 hardwareScanning bool
 wifiScanMu sync.Mutex
	wifiScanning bool
	connectivityCacheMu sync.Mutex
	connectivityCache ConnectivityStatus
	connectivityCacheAt time.Time
	liveCacheMu sync.Mutex
	liveCache []byte
	liveCacheAt time.Time
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

func currentWiFiSSID() string {
	out, err := exec.Command("nmcli", "-t", "--escape", "no", "-f", "ACTIVE,SSID", "dev", "wifi", "--rescan", "no").Output()
	if err != nil { return "" }
	for _, line := range strings.Split(string(out), "\n") {
		if strings.HasPrefix(line, "yes:") {
			return strings.TrimSpace(strings.TrimPrefix(line, "yes:"))
		}
	}
	return ""
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
		if err != nil { continue }
		_ = conn.Close()
		ms := time.Since(started).Milliseconds()
		if ms < 1 { ms = 1 }
		if best == 0 || ms < best { best = ms }
	}
	if best == 0 { return false, 0, "Offline" }
	if best < 80 { return true, best, "Ótimo" }
	if best < 160 { return true, best, "Bom" }
	return true, best, "Ruim"
}

func apActive() bool {
	out, err := exec.Command("/usr/local/sbin/2pny-ap-control", "status").Output()
	return err == nil && strings.TrimSpace(string(out)) == "active"
}

func connectivitySnapshot() ConnectivityStatus {
	wifis := wifiInterfaces()
	eth := ethernetInterface()
	client := readRunFile("uplink-iface")
	apif := readRunFile("ap-iface")
	ssid := currentWiFiSSID()
	wifiUp := ssid != ""
	internet, latency, quality := internetProbe()
	return ConnectivityStatus{
		Internet: internet,
		InternetLatencyMS: latency,
		InternetQuality: quality,
		DefaultInterface: defaultRouteInterface(),
		Ethernet: eth != "" && interfaceUp(eth),
		EthernetInterface: eth,
		WiFi: wifiUp,
		WiFiSSID: ssid,
		WiFiInterfaces: wifis,
		WiFiCount: len(wifis),
		ClientInterface: client,
		APActive: apActive(),
		APInterface: apif,
		APSSID: "pu2pny",
		IPv4: ipv4Addresses(),
	}
}

func cachedConnectivitySnapshot() ConnectivityStatus {
	connectivityCacheMu.Lock()
	defer connectivityCacheMu.Unlock()
	if !connectivityCacheAt.IsZero() && time.Since(connectivityCacheAt) < 15*time.Second {
		return connectivityCache
	}
	connectivityCache = connectivitySnapshot()
	connectivityCacheAt = time.Now()
	return connectivityCache
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	c := cachedConnectivitySnapshot()
	writeJSON(w, http.StatusOK, Status{
		Name: "PU2PNY-OS",
		Version: appVersion,
		Provisioned: fileExists(provisionedFile),
		Ethernet: c.Ethernet,
		WiFi: c.WiFi,
		IPv4: c.IPv4,
	})
}

func connectivityHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
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
		"state": state,
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
	st := map[string]any{"state":"idle", "networks":[]any{}}
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
			if msg == "" { msg = "não foi possível buscar redes Wi-Fi" }
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
		startWiFiScan()
		st = readWiFiScanState()
	}
	writeJSON(w, http.StatusOK, st)
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
	st := map[string]any{"state":"idle"}
	if b, err := os.ReadFile(filepath.Join(dataDir, "network-connect.json")); err == nil {
		_ = json.Unmarshal(b, &st)
	}
	st["connectivity"] = connectivitySnapshot()
	st["resume_url"] = "http://pu2pny.local/wizard"
	st["setup_url"] = "http://10.43.0.1/wizard"
	writeJSON(w, http.StatusOK, st)
}

func networkConnectHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	var in struct {
		SSID string `json:"ssid"`
		Password string `json:"password"`
		BSSID string `json:"bssid"`
		KeepAP bool `json:"keep_ap"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 16<<10)).Decode(&in); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"dados de rede inválidos"})
		return
	}
	in.SSID = strings.TrimSpace(in.SSID)
	if in.SSID == "" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"selecione uma rede Wi-Fi"})
		return
	}

	snap := connectivitySnapshot()
	keep := in.KeepAP && snap.WiFiCount >= 2
	willDisconnect := snap.APActive && snap.WiFiCount < 2
	writeNetworkConnectState("queued", "Conexão recebida. Preparando troca de rede...", in.SSID)

	ssid, password, bssid := in.SSID, in.Password, strings.TrimSpace(in.BSSID)
	time.AfterFunc(2500*time.Millisecond, func() {
		writeNetworkConnectState("connecting", "Conectando à rede "+ssid+"...", ssid)
		keepArg := "0"
		if keep { keepArg = "1" }
		out, err := exec.Command("/usr/local/sbin/2pny-network-switch", "connect", ssid, password, keepArg, bssid).CombinedOutput()
		msg := strings.TrimSpace(string(out))
		if err != nil {
			if msg == "" { msg = err.Error() }
			writeNetworkConnectState("error", msg, ssid)
			log.Printf("wifi connect failed: %v: %s", err, msg)
			return
		}
		if msg == "" { msg = "Wi-Fi conectado." }
		writeNetworkConnectState("connected", msg, ssid)
	})

	writeJSON(w, http.StatusAccepted, map[string]any{
		"ok":true,
		"state":"queued",
		"ssid":in.SSID,
		"will_disconnect":willDisconnect,
		"keep_ap":keep,
		"message":"Configuração recebida. O Wi-Fi será conectado em seguida.",
		"reconnect_url":"http://pu2pny.local/wizard",
		"setup_url":"http://10.43.0.1/wizard",
	})
}

func maintenanceHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		out, err := exec.Command("/usr/local/sbin/2pny-auto-maintenance", "status").CombinedOutput()
		if err != nil || len(strings.TrimSpace(string(out))) == 0 {
			writeJSON(w, http.StatusOK, map[string]any{"state":"unknown","enabled":fileExists(filepath.Join(dataDir, "auto-maintenance.enabled"))})
			return
		}
		var st map[string]any
		if json.Unmarshal(out, &st) != nil {
			st = map[string]any{"state":"unknown","message":strings.TrimSpace(string(out))}
		}
		st["enabled"] = fileExists(filepath.Join(dataDir, "auto-maintenance.enabled"))
		writeJSON(w, http.StatusOK, st)
	case http.MethodPost:
		var in struct { Enabled bool `json:"enabled"` }
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4096)).Decode(&in); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false,"error":"opção inválida"})
			return
		}
		action := "disable"
		if in.Enabled { action = "enable" }
		out, err := exec.Command("/usr/local/sbin/2pny-auto-maintenance", action).CombinedOutput()
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]any{"ok":false,"error":strings.TrimSpace(string(out))})
			return
		}
		writeJSON(w, http.StatusOK, map[string]any{"ok":true,"enabled":in.Enabled})
	default:
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
	}
}

func triggerMaintenance() {
	_ = exec.Command("systemctl", "start", "--no-block", "2pny-auto-maintenance.service").Run()
}

func networkRefreshHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	_ = exec.Command("systemctl", "restart", "2pny-network-core.service").Run()
	time.Sleep(2200 * time.Millisecond)
	writeJSON(w, http.StatusOK, map[string]any{"ok":true, "connectivity":connectivitySnapshot()})
}

func applyDisplayOverrideToProbe() {
	ob, err := os.ReadFile(displayOverrideFile)
	if err != nil { return }
	var ov map[string]any
	if json.Unmarshal(ob, &ov) != nil || ov["enabled"] != true { return }
	hb, err := os.ReadFile(hardwareProbeFile)
	if err != nil { return }
	var h map[string]any
	if json.Unmarshal(hb, &h) != nil { return }
	m, _ := h["mmdvm"].(map[string]any)
	if m == nil || m["detected"] != true { return }
	h["display"] = map[string]any{
		"detected":true,
		"class":"nextion_mmdvm",
		"state":"manual_override",
		"model":"Nextion via MMDVM",
		"port":"modem",
		"confidence":"manual",
		"message":"Nextion habilitada manualmente na porta de display da MMDVM; nenhum HMI foi alterado.",
	}
	raw, _ := json.Marshal(h)
	_ = os.WriteFile(hardwareProbeFile, raw, 0600)
}

func displayOverrideHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		enabled := false
		if b, err := os.ReadFile(displayOverrideFile); err == nil {
			var ov map[string]any
			if json.Unmarshal(b, &ov) == nil { enabled, _ = ov["enabled"].(bool) }
		}
		layout := 2
		if b, err := os.ReadFile(displayOverrideFile); err == nil { var ov map[string]any; if json.Unmarshal(b,&ov)==nil { if n,ok:=ov["layout"].(float64); ok { layout=int(n) } } }
		writeJSON(w, http.StatusOK, map[string]any{"enabled":enabled,"type":"nextion_mmdvm","layout":layout})
	case http.MethodPost:
		var in struct { Enabled bool `json:"enabled"`; Layout int `json:"layout"` }
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4096)).Decode(&in); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false,"error":"opção de display inválida"})
			return
		}
		if in.Enabled {
			if in.Layout == 0 { in.Layout = 2 }
			if in.Layout != 2 && in.Layout != 3 {
				writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false,"error":"layout Nextion deve ser ON7LDS (2) ou ON7LDS-DIY (3)"})
				return
			}
			if _, err := detectedModemPort(); err != nil {
				writeJSON(w, http.StatusConflict, map[string]any{"ok":false,"error":"MMDVM precisa estar detectada antes de habilitar a Nextion"})
				return
			}
			raw, _ := json.Marshal(map[string]any{"enabled":true,"type":"nextion_mmdvm","speed":9600,"layout":in.Layout,"updated":time.Now().UTC().Format(time.RFC3339)})
			_ = os.WriteFile(displayOverrideFile, raw, 0600)
			applyDisplayOverrideToProbe()
		} else {
			raw, _ := json.Marshal(map[string]any{"enabled":false})
			_ = os.WriteFile(displayOverrideFile, raw, 0600)
		}
		if fileExists(filepath.Join(dataDir,"rf-configured")) { _, _ = exec.Command("/usr/local/sbin/2pny-display-apply").CombinedOutput() }
		writeJSON(w, http.StatusOK, map[string]any{"ok":true,"enabled":in.Enabled,"layout":in.Layout})
	default:
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
	}
}

func hardwareHandler(w http.ResponseWriter, r *http.Request) {
	b, err := os.ReadFile(hardwareFile)
	if err != nil {
		writeJSON(w, http.StatusOK, map[string]any{"raspberry_model":"detectando...", "serial_ports":[]string{}, "i2c_buses":[]string{}, "mmdvm":map[string]any{"detected":false}})
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
		for k, v := range scan { probe[k] = v }
	}
	if len(probe) == 0 {
		probe["state"] = "not_scanned"
	}
	writeJSON(w, http.StatusOK, probe)
}

func writeHardwareState(state, stage, message string) {
	_ = os.MkdirAll(filepath.Dir(hardwareScanStateFile), 0755)
	b, _ := json.Marshal(map[string]any{"state":state, "stage":stage, "message":message, "updated":time.Now().UTC().Format(time.RFC3339)})
	_ = os.WriteFile(hardwareScanStateFile, b, 0644)
}

func hardwareScanHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
 hardwareScanMu.Lock()
 if hardwareScanning {hardwareScanMu.Unlock();writeJSON(w,http.StatusAccepted,map[string]any{"state":"preparing"});return}
 hardwareScanning=true;hardwareScanMu.Unlock()
	writeHardwareState("preparing", "drivers", "Preparando drivers e firmware...")
	// Respond immediately; display/driver work must never block the POST.
	go func() {
  defer func(){hardwareScanMu.Lock();hardwareScanning=false;hardwareScanMu.Unlock()}()
		_ = exec.Command("timeout", "5", "/usr/local/sbin/2pny-display-status", "hardware", "PU2PNY-OS: hardware").Run()
		prep := exec.Command("timeout", "-k", "2", "25", "/usr/local/sbin/2pny-hardware-prepare")
		if b, err := prep.CombinedOutput(); err != nil {
			log.Printf("hardware prepare warning: %v: %s", err, strings.TrimSpace(string(b)))
		}
		writeHardwareState("scanning", "hardware", "Detectando MMDVM e display...")
		cmd := exec.Command("timeout", "-k", "2", "60", "/usr/local/sbin/2pny-hardware-probe")
		if b, err := cmd.CombinedOutput(); err != nil {
			msg := strings.TrimSpace(string(b))
			if msg == "" { msg = err.Error() }
			writeHardwareState("error", "hardware", msg)
			_ = exec.Command("/usr/local/sbin/2pny-display-status", "error", "Falha ao detectar hardware").Run()
			log.Printf("hardware probe failed: %v: %s", err, msg)
			return
		}
		applyDisplayOverrideToProbe()
		_ = os.Remove(hardwareScanStateFile)
		_ = exec.Command("/usr/local/sbin/2pny-display-status", "display", "Hardware detectado").Run()
	}()
	writeJSON(w, http.StatusAccepted, map[string]any{"ok":true, "state":"preparing", "stage":"drivers"})
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
	st := RFApplyState{State:state, Message:message, Updated:time.Now().UTC().Format(time.RFC3339)}
	b, _ := json.Marshal(st)
	_ = os.WriteFile(rfApplyStateFile, b, 0600)
}

func rfStatusHandler(w http.ResponseWriter, r *http.Request) {
	b, err := os.ReadFile(rfApplyStateFile)
	if err != nil {
		writeJSON(w, http.StatusOK, RFApplyState{State:"ready", Message:"Aguardando configuração.", Updated:time.Now().UTC().Format(time.RFC3339)})
		return
	}
	var st RFApplyState
	if json.Unmarshal(b, &st) != nil {
		writeJSON(w, http.StatusOK, RFApplyState{State:"ready", Message:"Aguardando configuração.", Updated:time.Now().UTC().Format(time.RFC3339)})
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
			Detected bool `json:"detected"`
			Port string `json:"port"`
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
	if err := os.MkdirAll(dataDir, 0750); err != nil { return err }
	raw, _ := json.MarshalIndent(c, "", "  ")
	tmp := configFile + ".tmp"
	if err := os.WriteFile(tmp, raw, 0600); err != nil { return err }
	return os.Rename(tmp, configFile)
}


type applyTransaction struct {
	dir string
	paths []string
	existed map[string]bool
	active map[string]bool
	enabled map[string]bool
}

func beginApplyTransaction() (*applyTransaction, error) {
	if err := os.MkdirAll("/run/2pny", 0750); err != nil { return nil, err }
	dir, err := os.MkdirTemp("/run/2pny", "apply-tx-")
	if err != nil { return nil, err }
	t := &applyTransaction{
		dir:dir,
		paths:[]string{
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
			filepath.Join(dataDir, "secrets", "brandmeister-api.key"),
		},
		existed:map[string]bool{},
		active:map[string]bool{},
		enabled:map[string]bool{},
	}
	for _, service := range []string{"2pny-mmdvmhost.service", "2pny-dmrgateway.service", "2pny-display.service"} {
		t.active[service] = serviceActive(service)
		t.enabled[service] = exec.Command("systemctl", "is-enabled", "--quiet", service).Run() == nil
	}
	for i,p := range t.paths {
		if !fileExists(p) { t.existed[p]=false; continue }
		t.existed[p]=true
		dst := filepath.Join(dir, strconv.Itoa(i))
		if out, e := exec.Command("cp", "-a", "--", p, dst).CombinedOutput(); e != nil {
			_ = os.RemoveAll(dir)
			return nil, fmt.Errorf("backup transacional falhou: %s", strings.TrimSpace(string(out)))
		}
	}
	return t,nil
}

func (t *applyTransaction) rollback() {
	if t == nil { return }
	for i,p := range t.paths {
		if t.existed[p] {
			_ = exec.Command("cp", "-a", "--", filepath.Join(t.dir, strconv.Itoa(i)), p).Run()
		} else {
			_ = os.Remove(p)
		}
	}
	for _, service := range []string{"2pny-dmrgateway.service", "2pny-mmdvmhost.service", "2pny-display.service"} {
        enableAction := "disable"
        if t.enabled[service] { enableAction = "enable" }
        _ = exec.Command("systemctl", enableAction, service).Run()
        action := "stop"
        if t.active[service] { action = "restart" }
        _ = exec.Command("systemctl", action, service).Run()
    }
	_ = os.RemoveAll(t.dir)
}

func (t *applyTransaction) commit() {
	if t != nil { _ = os.RemoveAll(t.dir) }
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
		Callsign string `json:"callsign"`
		DMRID string `json:"dmr_id"`
		UseMode string `json:"use_mode"`
		RX string `json:"rx"`
		TX string `json:"tx"`
		RXOffset string `json:"rx_offset"`
		TXOffset string `json:"tx_offset"`
		Protocol string `json:"protocol"`
		Operation string `json:"operation"`
		ServerName string `json:"server_name"`
		ServerAddress string `json:"server_address"`
		ServerPort int `json:"server_port"`
		ServerPassword string `json:"server_password"`
		ServerOptions string `json:"server_options"`
		NetworkKind string `json:"network_kind"`
		ColorCode int `json:"color_code"`
		DMRSlot string `json:"dmr_slot"`
		XLXModule string `json:"xlx_module"`
		ESSID string `json:"essid"`
		BMAPIKey string `json:"bm_api_key"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 32<<10)).Decode(&in); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"configuração inválida"})
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
	if in.DMRSlot == "" { in.DMRSlot = "2" }
	if in.ColorCode < 0 || in.ColorCode > 15 {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"Color Code DMR inválido"})
		return
	}
	if !callsignRx.MatchString(in.Callsign) {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"indicativo inválido"})
		return
	}
	if !dmrRx.MatchString(in.DMRID) {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"DMR ID inválido"})
		return
	}
	if in.UseMode != "hotspot" && in.UseMode != "repeater" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"selecione Hotspot ou Repetidora"})
		return
	}
	validProtocol := map[string]bool{"DSTAR":true, "DMR":true, "YSF":true, "P25":true, "NXDN":true}
	if !validProtocol[in.Protocol] {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"protocolo inválido"})
		return
	}
	if in.Operation != "normal" && in.Operation != "crossmode" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"selecione Normal ou Crossmode"})
		return
	}
	if in.Operation == "crossmode" {
		writeJSON(w, http.StatusConflict, map[string]any{"ok":false, "error":"Crossmode ainda está em desenvolvimento nesta Alpha; use operação Normal"})
		return
	}
	if in.Protocol == "DSTAR" || in.Protocol == "YSF" || in.Protocol == "P25" || in.Protocol == "NXDN" {
		if in.ServerName == "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"selecione um servidor/refletor para o protocolo"})
			return
		}
		if len(in.ServerName)>128 || len(in.ServerAddress)>255 || hasUnsafeControl(in.ServerName) || hasUnsafeControl(in.ServerAddress) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"servidor/refletor inválido"})
			return
		}
		if in.Protocol == "DSTAR" && (len(in.XLXModule)!=1 || in.XLXModule[0]<'A' || in.XLXModule[0]>'Z') {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"D-Star exige módulo A-Z"})
			return
		}
	}
	if in.Protocol == "DMR" {
		if in.ServerName == "" || in.ServerAddress == "" || in.ServerPort < 1 || in.ServerPort > 65535 {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"selecione um servidor/master DMR válido"})
			return
		}
		if len(in.ServerName)>128 || len(in.ServerAddress)>255 || len(in.ServerPassword)>128 || len(in.ServerOptions)>512 ||
			hasUnsafeControl(in.ServerName) || hasUnsafeControl(in.ServerAddress) || hasUnsafeControl(in.ServerPassword) || hasUnsafeControl(in.ServerOptions) {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"campos do servidor DMR contêm tamanho ou caracteres inválidos"})
			return
		}
		if in.DMRSlot != "1" && in.DMRSlot != "2" && in.DMRSlot != "both" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"slot DMR inválido"})
			return
		}
		if in.UseMode == "hotspot" && in.DMRSlot == "both" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"hotspot simplex deve usar TS1 ou TS2"})
			return
		}
		if in.XLXModule != "" && (len(in.XLXModule) != 1 || in.XLXModule[0] < 'A' || in.XLXModule[0] > 'Z') {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"módulo XLX inválido"})
			return
		}
		if in.ESSID != "" && (len(in.ESSID) != 2 || in.ESSID[0] < '0' || in.ESSID[0] > '9' || in.ESSID[1] < '0' || in.ESSID[1] > '9') {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"ESSID deve ter dois dígitos"})
			return
		}
		if strings.EqualFold(in.NetworkKind, "BrandMeister") && in.ServerPassword == "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"BrandMeister exige a senha Hotspot Security"})
			return
		}
	}
	rxOffset := strings.TrimSpace(in.RXOffset)
	txOffset := strings.TrimSpace(in.TXOffset)
	if rxOffset == "" { rxOffset = "0" }
	if txOffset == "" { txOffset = "0" }
	rxOffsetHz, err := strconv.ParseInt(rxOffset, 10, 64)
	if err != nil || rxOffsetHz < -10000000 || rxOffsetHz > 10000000 {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"RX Offset inválido; use Hz entre -10000000 e 10000000"})
		return
	}
	txOffsetHz, err := strconv.ParseInt(txOffset, 10, 64)
	if err != nil || txOffsetHz < -10000000 || txOffsetHz > 10000000 {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"TX Offset inválido; use Hz entre -10000000 e 10000000"})
		return
	}
	rxArg, rxHz, err := normalizeFrequency(in.RX)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"RX: "+err.Error()})
		return
	}
	txArg, txHz := rxArg, rxHz
	if in.UseMode == "repeater" {
		txArg, txHz, err = normalizeFrequency(in.TX)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"TX: "+err.Error()})
			return
		}
	} else {
		// A hotspot simplex always uses the same RF frequency for RX and TX.
		in.TX = in.RX
	}
	port, err := detectedModemPort()
	if err != nil {
		writeJSON(w, http.StatusConflict, map[string]any{"ok":false, "error":err.Error()})
		return
	}
	duplex := "0"
	if in.UseMode == "repeater" { duplex = "1" }
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
		defer func(){ if committed { tx.commit() } else { tx.rollback() } }()
		cmd := exec.Command("/usr/local/sbin/2pny-rf-apply", rxArg, txArg, rxOffset, txOffset, duplex, port, in.Callsign, in.DMRID)
		out, err := cmd.CombinedOutput()
		msg := strings.TrimSpace(string(out))
		if err != nil {
			if msg == "" { msg = err.Error() }
			writeRFApplyState("error", msg)
			log.Printf("basic RF apply failed: %v: %s", err, msg)
			return
		}
		modeOut, modeErr := exec.Command("/usr/local/sbin/2pny-mode-apply", in.Protocol, in.Operation, in.UseMode).CombinedOutput()
		if modeErr != nil {
			m := strings.TrimSpace(string(modeOut)); if m == "" { m = modeErr.Error() }
			writeRFApplyState("error", "RF validada, mas o protocolo não pôde ser aplicado: "+m)
			log.Printf("mode apply failed: %v: %s", modeErr, m)
			return
		}

		networkState := "rf-only"
		if in.Protocol == "DMR" || in.Protocol == "DSTAR" || in.Protocol == "YSF" || in.Protocol == "P25" || in.Protocol == "NXDN" {
			netOut, netErr := exec.Command("/usr/local/sbin/2pny-protocol-network-apply",
				in.Protocol, in.ServerName, in.ServerAddress, strconv.Itoa(in.ServerPort),
				in.ServerPassword, in.UseMode, strconv.Itoa(in.ColorCode), in.DMRSlot,
				in.XLXModule, in.ESSID, in.NetworkKind, in.ServerOptions).CombinedOutput()
			if netErr != nil {
				m := strings.TrimSpace(string(netOut)); if m == "" { m = netErr.Error() }
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
		if b, e := os.ReadFile(filepath.Join(dataDir, "uplink-ssid")); e == nil { wifiSSID = strings.TrimSpace(string(b)) }
		cfg := Config{
			Callsign:in.Callsign, DMRID:in.DMRID, WiFiSSID:wifiSSID, UseMode:in.UseMode,
			RXHz:rxHz, TXHz:txHz, RXOffsetHz:rxOffsetHz, TXOffsetHz:txOffsetHz, Protocol:in.Protocol, Operation:in.Operation,
			ServerName:in.ServerName, ServerAddress:in.ServerAddress, ServerPort:in.ServerPort,
			NetworkKind:in.NetworkKind, ColorCode:in.ColorCode, DMRSlot:in.DMRSlot, XLXModule:in.XLXModule,
			ESSID:in.ESSID, BMAPIConfigured:apiConfigured, NetworkState:networkState,
			CreatedAt:time.Now().UTC().Format(time.RFC3339),
		}
		if err := saveConfig(cfg); err != nil {
			writeRFApplyState("error", "RF aplicada, mas não foi possível salvar a configuração.")
			return
		}
		if err := os.WriteFile(provisionedFile, []byte(time.Now().UTC().Format(time.RFC3339)+"\n"), 0600); err != nil {
			writeRFApplyState("error", "Configuração aplicada, mas não foi possível finalizar o assistente.")
			return
		}
		_ = exec.Command("systemctl", "restart", "avahi-daemon.service").Run()
		done := "RF e MMDVMHost configurados."
		if networkState == "connecting" {
			done = "RF configurada e rede "+in.Protocol+" aplicada. Acompanhe o estado no painel principal."
		}
		committed = true
		writeRFApplyState("applied", done)
	}( )
	writeJSON(w, http.StatusAccepted, map[string]any{"ok":true, "state":"applying"})
}

func rfApplyHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	if err := r.ParseForm(); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"formulário RF inválido"})
		return
	}
	keys := []string{"rx","tx","rx_offset","tx_offset","duplex","port","callsign","dmr_id"}
	args := make([]string, 0, len(keys))
	for _, k := range keys {
		v := strings.TrimSpace(r.FormValue(k))
		if v == "" {
			writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"campo obrigatório: "+k})
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
			if msg == "" { msg = err.Error() }
			writeRFApplyState("error", msg)
			return
		}
		if msg == "" { msg = "RF aplicada e MMDVMHost ativo." }
		writeRFApplyState("applied", msg)
	}(append([]string(nil), args...))
	writeJSON(w, http.StatusAccepted, map[string]any{"ok":true, "state":"applying"})
}

func serversHandler(w http.ResponseWriter, r *http.Request) {
	proto := strings.ToUpper(strings.TrimSpace(r.URL.Query().Get("protocol")))
	if proto == "" { proto = "DMR" }
	query := strings.TrimSpace(r.URL.Query().Get("q"))
	if r.Method == http.MethodPost {
		out, err := exec.Command("/usr/local/sbin/2pny-hostfiles-update").CombinedOutput()
		if err != nil {
			writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok":false,"error":strings.TrimSpace(string(out))})
			return
		}
	}
	if r.Method != http.MethodGet && r.Method != http.MethodPost {
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
		return
	}
	args := []string{proto}
	if query != "" { args = append(args, query) }
	out, err := exec.Command("/usr/local/sbin/2pny-server-catalog", args...).CombinedOutput()
	if err != nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"protocol":proto,"servers":[]any{},"error":strings.TrimSpace(string(out))})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(out)
}

func liveStatusHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "GET required", http.StatusMethodNotAllowed)
		return
	}
	out := liveHub.current().data
	if len(out) == 0 { out = []byte(`{"schema":1,"sequence":0,"active":null,"standby":true,"network":{"state":"unknown","message":"worker unavailable"},"internet":{"quality":"unknown"},"history":[]}`) }
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(out)
}

func liveEventsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet { http.Error(w, "GET required", http.StatusMethodNotAllowed); return }
	flusher, ok := w.(http.Flusher)
	if !ok { http.Error(w, "streaming unsupported", http.StatusInternalServerError); return }
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache, no-store")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")
	ch := make(chan liveEvent, 1)
	liveHub.mu.Lock(); liveHub.subscribers[ch] = struct{}{}
	initial := liveEvent{id:liveHub.sequence, data:append([]byte(nil), liveHub.snapshot...)}
	liveHub.mu.Unlock()
	defer func(){ liveHub.mu.Lock(); delete(liveHub.subscribers, ch); close(ch); liveHub.mu.Unlock() }()
	send := func(event liveEvent) bool {
		if len(event.data) == 0 { return true }
		if _, err := fmt.Fprintf(w, "id: %d\nevent: live\ndata: %s\n\n", event.id, event.data); err != nil { return false }
		flusher.Flush(); return true
	}
	if !send(initial) { return }
	heartbeat := time.NewTicker(15*time.Second); defer heartbeat.Stop()
	for {
		select {
		case event := <-ch: if !send(event) { return }
		case <-heartbeat.C:
			if _, err := fmt.Fprint(w, ": keepalive\n\n"); err != nil { return }; flusher.Flush()
		case <-r.Context().Done(): return
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
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"schema":1, "error":"module status unavailable"})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(out)
}

func apControlHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet {
		writeJSON(w, http.StatusOK, map[string]any{"active":apActive(), "ssid":"pu2pny", "open":true, "interface":readRunFile("ap-iface")})
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
		return
	}
	if err := r.ParseForm(); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"pedido inválido"})
		return
	}
	action := strings.TrimSpace(r.FormValue("action"))
	if action != "on" && action != "off" {
		writeJSON(w, http.StatusBadRequest, map[string]any{"ok":false, "error":"action deve ser on ou off"})
		return
	}
	out, err := exec.Command("/usr/local/sbin/2pny-ap-control", action).CombinedOutput()
	msg := strings.TrimSpace(string(out))
	if err != nil {
		if msg == "" { msg = err.Error() }
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"ok":false, "error":msg, "active":apActive()})
		return
	}
	time.Sleep(700*time.Millisecond)
	writeJSON(w, http.StatusOK, map[string]any{"ok":true, "message":msg, "active":apActive(), "ssid":"pu2pny", "open":true})
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
	if b, err := os.ReadFile(filepath.Join(dataDir,"network-radio.json")); err == nil { _ = json.Unmarshal(b,&networkRuntime) }
	baud := strings.TrimSpace(func() string { b,_:=os.ReadFile(filepath.Join(dataDir,"mmdvm-baud")); return string(b) }())
	writeJSON(w, http.StatusOK, map[string]any{
		"name":"PU2PNY-OS",
		"version":appVersion,
		"provisioned":fileExists(provisionedFile),
		"radio_active":serviceActive("2pny-mmdvmhost.service"),
		"dmrgateway_active":serviceActive("2pny-dmrgateway.service"),
		"dstargateway_active":serviceActive("2pny-dstargateway.service"),
		"ysfgateway_active":serviceActive("2pny-ysfgateway.service"),
		"p25gateway_active":serviceActive("2pny-p25gateway.service"),
		"nxdngateway_active":serviceActive("2pny-nxdngateway.service"),
		"display_active":serviceActive("2pny-display.service"),
		"mqtt_active":serviceActive("mosquitto.service"),
		"mmdvm_baud":baud,
		"config":cfg,
		"connectivity":cachedConnectivitySnapshot(),
		"hardware":hardware,
		"network_runtime":networkRuntime,
		"display_runtime":func() map[string]any { d:=map[string]any{}; if b,e:=os.ReadFile(filepath.Join(dataDir,"display-runtime.json")); e==nil { _=json.Unmarshal(b,&d) }; return d }(),
		"telemetry":readPublicJSON("/run/2pny/telemetry.json"),
	})
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
		"captive": !fileExists(provisionedFile),
		"user-portal-url": base + "/wizard",
	})
}

func captivePortalHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store, no-cache, must-revalidate")
	if !fileExists(provisionedFile) {
		http.Redirect(w, r, "/wizard", http.StatusFound)
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


func readPublicJSON(path string) map[string]any { d:=map[string]any{};if b,e:=os.ReadFile(path);e==nil {json.Unmarshal(b,&d)};return d }
func sameOrigin(r *http.Request) bool { o:=r.Header.Get("Origin");if o=="" {return true};u,e:=url.Parse(o);return e==nil && u.Host==r.Host }
func stationSettingsHandler(w http.ResponseWriter,r *http.Request) {
 if r.Method==http.MethodGet {writeJSON(w,200,map[string]any{"qrz_configured":fileExists("/var/lib/2pny/secrets/qrz.json"),"ssh_active":serviceActive("ssh.service")});return}
 if r.Method!=http.MethodPost || !sameOrigin(r) {http.Error(w,"request rejected",403);return}
 r.Body=http.MaxBytesReader(w,r.Body,8192)
 var in struct{Action string `json:"action"`;Username string `json:"username"`;Password string `json:"password"`;Key string `json:"key"`}
 if json.NewDecoder(r.Body).Decode(&in)!=nil {http.Error(w,"invalid JSON",400);return}
 switch in.Action {
 case "qrz":
  if in.Username=="" || in.Password=="" {http.Error(w,"Informe usuário e senha QRZ",400);return}
  os.MkdirAll("/var/lib/2pny/secrets",0700);b,_:=json.Marshal(map[string]string{"username":in.Username,"password":in.Password})
  if e:=os.WriteFile("/var/lib/2pny/secrets/qrz.json",b,0600);e!=nil {http.Error(w,"save failed",500);return}
 case "qrz-remove":os.Remove("/var/lib/2pny/secrets/qrz.json")
 case "ssh-enable","ssh-disable":
  cmd:=exec.Command("/usr/local/sbin/2pny-expert-ssh",in.Action);cmd.Stdin=strings.NewReader(in.Key)
  if out,e:=cmd.CombinedOutput();e!=nil {writeJSON(w,400,map[string]any{"error":strings.TrimSpace(string(out))});return}
 default:http.Error(w,"unknown action",400);return
 }
 writeJSON(w,200,map[string]any{"ok":true})
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
	http.HandleFunc("/admin", func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, "/dashboard", http.StatusFound) })
	http.HandleFunc("/ui-language.js",func(w http.ResponseWriter,r *http.Request){http.ServeFile(w,r,"/usr/share/2pny/ui-language.js")})
	http.HandleFunc("/api/status", statusHandler)
	http.HandleFunc("/api/dashboard", dashboardDataHandler)
	http.HandleFunc("/api/connectivity", connectivityHandler)
	http.HandleFunc("/api/wifi/scan", wifiScanHandler)
	http.HandleFunc("/api/network/connect", networkConnectHandler)
	http.HandleFunc("/api/network/connect/status", networkConnectStatusHandler)
	http.HandleFunc("/api/network/refresh", networkRefreshHandler)
	http.HandleFunc("/api/maintenance", maintenanceHandler)
	http.HandleFunc("/api/hardware", hardwareHandler)
	http.HandleFunc("/api/hardware/status", hardwareStatusHandler)
	http.HandleFunc("/api/hardware/scan", hardwareScanHandler)
	http.HandleFunc("/api/display/override", displayOverrideHandler)
	http.HandleFunc("/api/config", publicConfigHandler)
	http.HandleFunc("/api/servers", serversHandler)
	http.HandleFunc("/api/live", liveStatusHandler)
	http.HandleFunc("/api/live/events", liveEventsHandler)
 http.HandleFunc("/api/station/settings", stationSettingsHandler)
 http.HandleFunc("/api/contacts",func(w http.ResponseWriter,r *http.Request){writeJSON(w,200,readPublicJSON("/run/2pny/contacts.json"))})
 http.Handle("/operator-photo/",http.StripPrefix("/operator-photo/",http.FileServer(http.Dir("/var/cache/2pny/photos"))))
	http.HandleFunc("/api/basic/apply", basicApplyHandler)
	http.HandleFunc("/api/rf", rfStatusHandler)
	http.HandleFunc("/api/rf/apply", rfApplyHandler)
	http.HandleFunc("/api/modules", moduleStatusHandler)
	http.HandleFunc("/api/ap", apControlHandler)
	http.HandleFunc("/healthz", healthzHandler)
	http.HandleFunc("/captive-api", captiveAPIHandler)
	for _, p := range []string{"/generate_204","/gen_204","/hotspot-detect.html","/library/test/success.html","/connecttest.txt","/ncsi.txt","/canonical.html","/success.txt","/check_network_status.txt","/connectivity-check.html","/redirect"} {
		http.HandleFunc(p, captivePortalHandler)
	}
	log.Printf("PU2PNY-OS %s listening on %s", appVersion, listenAddr)
	log.Fatal(http.ListenAndServe(listenAddr, nil))
}
