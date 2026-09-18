package main

import (
	"encoding/json"
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
	appVersion      = "0.2.3-alpha"
	hardwareFile    = "/var/lib/2pny/hardware.json"
	hardwareProbeFile = "/var/lib/2pny/hardware-probe.json"
	rfApplyStateFile  = "/var/lib/2pny/rf-apply-state.json"
	wizardFile        = "/usr/share/2pny/wizard.html"
	dashboardFile     = "/usr/share/2pny/dashboard.html"
	wifiScanStateFile = "/var/lib/2pny/wifi-scan.json"
)

type Config struct {
	Callsign   string `json:"callsign"`
	DMRID      string `json:"dmr_id"`
	WiFiSSID   string `json:"wifi_ssid,omitempty"`
	UseMode    string `json:"use_mode"`
	RXHz       int64  `json:"rx_hz"`
	TXHz       int64  `json:"tx_hz"`
	Protocol   string `json:"protocol"`
	Operation  string `json:"operation"`
	CreatedAt  string `json:"created_at"`
}

type Status struct {
	Name        string   `json:"name"`
	Version     string   `json:"version"`
	Provisioned bool     `json:"provisioned"`
	Ethernet    bool     `json:"ethernet"`
	WiFi        bool     `json:"wifi"`
	IPv4        []string `json:"ipv4"`
}

type ConnectivityStatus struct {
	Internet         bool     `json:"internet"`
	DefaultInterface string   `json:"default_interface,omitempty"`
	Ethernet         bool     `json:"ethernet"`
	EthernetInterface string  `json:"ethernet_interface,omitempty"`
	WiFi             bool     `json:"wifi"`
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
	wifiScanMu sync.Mutex
	wifiScanning bool
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

func internetReachable() bool {
	for _, addr := range []string{"1.1.1.1:443", "8.8.8.8:53"} {
		c, err := net.DialTimeout("tcp", addr, 1200*time.Millisecond)
		if err == nil {
			_ = c.Close()
			return true
		}
	}
	return false
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
	wifiUp := false
	for _, w := range wifis {
		if interfaceUp(w) {
			wifiUp = true
			break
		}
	}
	return ConnectivityStatus{
		Internet: internetReachable(),
		DefaultInterface: defaultRouteInterface(),
		Ethernet: eth != "" && interfaceUp(eth),
		EthernetInterface: eth,
		WiFi: wifiUp,
		WiFiInterfaces: wifis,
		WiFiCount: len(wifis),
		ClientInterface: client,
		APActive: apActive(),
		APInterface: apif,
		APSSID: "pu2pny",
		IPv4: ipv4Addresses(),
	}
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	c := connectivitySnapshot()
	writeJSON(w, http.StatusOK, Status{
		Name: "PU2PNY",
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
	writeJSON(w, http.StatusOK, connectivitySnapshot())
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
		out, err := exec.Command("/usr/local/sbin/2pny-network-switch", "scan-json").CombinedOutput()
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
	if r.URL.Query().Get("refresh") == "1" || st["state"] == "idle" || st["state"] == "error" {
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

	ssid, password := in.SSID, in.Password
	time.AfterFunc(2500*time.Millisecond, func() {
		writeNetworkConnectState("connecting", "Conectando à rede "+ssid+"...", ssid)
		keepArg := "0"
		if keep { keepArg = "1" }
		out, err := exec.Command("/usr/local/sbin/2pny-network-switch", "connect", ssid, password, keepArg).CombinedOutput()
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

func networkRefreshHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	_ = exec.Command("systemctl", "restart", "2pny-network-core.service").Run()
	time.Sleep(2200 * time.Millisecond)
	writeJSON(w, http.StatusOK, map[string]any{"ok":true, "connectivity":connectivitySnapshot()})
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
	b, err := os.ReadFile(hardwareProbeFile)
	if err != nil {
		writeJSON(w, http.StatusOK, map[string]any{"state":"not_scanned"})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(b)
}

func writeHardwareState(state, stage, message string) {
	b, _ := json.Marshal(map[string]any{"state":state, "stage":stage, "message":message, "updated":time.Now().UTC().Format(time.RFC3339)})
	_ = os.WriteFile(hardwareProbeFile, b, 0600)
}

func hardwareScanHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	writeHardwareState("preparing", "drivers", "Preparando drivers e firmware...")
	go func() {
		prep := exec.Command("/usr/local/sbin/2pny-hardware-prepare")
		if b, err := prep.CombinedOutput(); err != nil {
			log.Printf("hardware prepare warning: %v: %s", err, strings.TrimSpace(string(b)))
		}
		writeHardwareState("scanning", "hardware", "Detectando MMDVM e display...")
		cmd := exec.Command("/usr/local/sbin/2pny-hardware-probe")
		if b, err := cmd.CombinedOutput(); err != nil {
			msg := strings.TrimSpace(string(b))
			if msg == "" { msg = err.Error() }
			writeHardwareState("error", "hardware", msg)
			log.Printf("hardware probe failed: %v: %s", err, msg)
		}
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
		Protocol string `json:"protocol"`
		Operation string `json:"operation"`
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
	go func() {
		applyMu.Lock()
		defer applyMu.Unlock()
		cmd := exec.Command("/usr/local/sbin/2pny-rf-apply", rxArg, txArg, "0", "0", duplex, port, in.Callsign, in.DMRID)
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
		wifiSSID := ""
		if b, e := os.ReadFile(filepath.Join(dataDir, "uplink-ssid")); e == nil { wifiSSID = strings.TrimSpace(string(b)) }
		cfg := Config{Callsign:in.Callsign, DMRID:in.DMRID, WiFiSSID:wifiSSID, UseMode:in.UseMode, RXHz:rxHz, TXHz:txHz, Protocol:in.Protocol, Operation:in.Operation, CreatedAt:time.Now().UTC().Format(time.RFC3339)}
		if err := saveConfig(cfg); err != nil {
			writeRFApplyState("error", "RF aplicada, mas não foi possível salvar a configuração.")
			return
		}
		if err := os.WriteFile(provisionedFile, []byte(time.Now().UTC().Format(time.RFC3339)+"\n"), 0600); err != nil {
			writeRFApplyState("error", "Configuração aplicada, mas não foi possível finalizar o assistente.")
			return
		}
		_ = exec.Command("systemctl", "restart", "avahi-daemon.service").Run()
		done := "Configuração básica concluída e MMDVMHost ativo."
		if in.Operation == "crossmode" {
			done = "Configuração básica concluída. Perfil Crossmode registrado; os módulos de ponte podem ser ajustados posteriormente."
		}
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
	writeJSON(w, http.StatusOK, map[string]any{
		"name":"PU2PNY",
		"version":appVersion,
		"provisioned":fileExists(provisionedFile),
		"radio_active":serviceActive("2pny-mmdvmhost.service"),
		"config":cfg,
		"connectivity":connectivitySnapshot(),
		"hardware":hardware,
		"activity":recentActivity(),
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
	default:
		http.Redirect(w, r, "/wizard", http.StatusFound)
	}
}

func main() {
	if err := os.MkdirAll(dataDir, 0750); err != nil {
		log.Fatal(err)
	}
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
	http.HandleFunc("/admin", func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, "/dashboard", http.StatusFound) })
	http.HandleFunc("/api/status", statusHandler)
	http.HandleFunc("/api/dashboard", dashboardDataHandler)
	http.HandleFunc("/api/connectivity", connectivityHandler)
	http.HandleFunc("/api/wifi/scan", wifiScanHandler)
	http.HandleFunc("/api/network/connect", networkConnectHandler)
	http.HandleFunc("/api/network/connect/status", networkConnectStatusHandler)
	http.HandleFunc("/api/network/refresh", networkRefreshHandler)
	http.HandleFunc("/api/hardware", hardwareHandler)
	http.HandleFunc("/api/hardware/status", hardwareStatusHandler)
	http.HandleFunc("/api/hardware/scan", hardwareScanHandler)
	http.HandleFunc("/api/config", publicConfigHandler)
	http.HandleFunc("/api/basic/apply", basicApplyHandler)
	http.HandleFunc("/api/rf", rfStatusHandler)
	http.HandleFunc("/api/rf/apply", rfApplyHandler)
	http.HandleFunc("/api/modules", moduleStatusHandler)
	http.HandleFunc("/api/ap", apControlHandler)
	http.HandleFunc("/healthz", healthzHandler)
	http.HandleFunc("/captive-api", captiveAPIHandler)
	for _, p := range []string{"/generate_204","/gen_204","/hotspot-detect.html","/library/test/success.html","/connecttest.txt","/ncsi.txt","/redirect"} {
		http.HandleFunc(p, captivePortalHandler)
	}
	log.Printf("PU2PNY %s listening on %s", appVersion, listenAddr)
	log.Fatal(http.ListenAndServe(listenAddr, nil))
}
