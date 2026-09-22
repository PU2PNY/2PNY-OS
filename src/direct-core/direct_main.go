package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

func (c *core) apiHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	switch r.URL.Path {
	case "/status":
		c.mu.Lock()
		st := c.st
		c.mu.Unlock()
		json.NewEncoder(w).Encode(st)
	case "/peers":
		c.mu.Lock()
		p := c.peers
		c.mu.Unlock()
		json.NewEncoder(w).Encode(map[string]any{"peers": p, "fingerprint": fingerprint(c.edPub)})
	case "/pair":
		if r.Method != "POST" {
			http.Error(w, "method", 405)
			return
		}
		var in struct {
			Callsign string `json:"callsign"`
		}
		if json.NewDecoder(io.LimitReader(r.Body, 4096)).Decode(&in) != nil {
			http.Error(w, "json", 400)
			return
		}
		p, e := c.pairCallsign(in.Callsign)
		if e != nil {
			http.Error(w, e.Error(), 409)
			return
		}
		json.NewEncoder(w).Encode(map[string]any{"ok": true, "peer": p})
	case "/unpair":
		if r.Method != "POST" {
			http.Error(w, "method", 405)
			return
		}
		var in struct {
			Callsign string `json:"callsign"`
		}
		_ = json.NewDecoder(io.LimitReader(r.Body, 4096)).Decode(&in)
		to := strings.ToUpper(strings.TrimSpace(in.Callsign))
		c.mu.Lock()
		delete(c.peers, to)
		e := savePeers(c.dir, c.peers)
		c.mu.Unlock()
		if e != nil {
			http.Error(w, e.Error(), 500)
			return
		}
		json.NewEncoder(w).Encode(map[string]any{"ok": true})
	case "/call":
		if r.Method != "POST" {
			http.Error(w, "method", 405)
			return
		}
		var in struct {
			Callsign string `json:"callsign"`
		}
		if json.NewDecoder(io.LimitReader(r.Body, 4096)).Decode(&in) != nil {
			http.Error(w, "json", 400)
			return
		}
		if e := c.call(in.Callsign); e != nil {
			http.Error(w, e.Error(), 409)
			return
		}
		c.mu.Lock()
		st := c.st
		c.mu.Unlock()
		json.NewEncoder(w).Encode(map[string]any{"ok": true, "state": st})
	case "/hangup":
		c.mu.Lock()
		peer := c.st.Peer
		relay := c.st.Path == "Relay"
		c.mu.Unlock()
		if peer != "" {
			_ = c.sendSecure(peer, "hangup", []byte("bye"), relay)
		}
		c.exitRadio()
		c.mu.Lock()
		c.st.Status = "idle"
		c.st.Peer = ""
		c.st.Path = "Offline"
		c.st.LatencyMS = 0
		c.st.LastError = ""
		c.writeState()
		c.mu.Unlock()
		json.NewEncoder(w).Encode(map[string]any{"ok": true})
	case "/message":
		if r.Method != "POST" {
			http.Error(w, "method", 405)
			return
		}
		var in struct {
			Text string `json:"text"`
		}
		if json.NewDecoder(io.LimitReader(r.Body, 4096)).Decode(&in) != nil || len(in.Text) > 256 {
			http.Error(w, "json", 400)
			return
		}
		c.mu.Lock()
		to := c.st.Peer
		relay := c.st.Path == "Relay"
		c.mu.Unlock()
		if to == "" {
			http.Error(w, "sem chamada", 409)
			return
		}
		if e := c.sendSecure(to, "message", []byte(in.Text), relay); e != nil {
			http.Error(w, e.Error(), 500)
			return
		}
		json.NewEncoder(w).Encode(map[string]any{"ok": true})
	default:
		http.NotFound(w, r)
	}
}

func main() {
	dir := flag.String("state-dir", "/var/lib/2pny/direct", "state dir")
	call := flag.String("callsign", "", "callsign")
	server := flag.String("server", defaultServer, "rendezvous/relay")
	api := flag.String("api", defaultAPIAddr, "local API address")
	selftest := flag.Bool("selftest", false, "crypto self-test")
	forceRelay := flag.Bool("force-relay", false, "disable direct UDP and exercise encrypted relay")
	protoOverride := flag.String("protocol-override", "", "test-only protocol override")
	radioGatewayPort := flag.Int("radio-gateway-port", 0, "test-only local gateway port override")
	radioHostPort := flag.Int("radio-host-port", 0, "test-only local MMDVMHost port override")
	skipSystemd := flag.Bool("skip-systemd", false, "test-only: do not stop/start gateway service")
	flag.Parse()
	protocolOverride = strings.ToUpper(strings.TrimSpace(*protoOverride))
	radioGatewayPortOverride = *radioGatewayPort
	radioHostPortOverride = *radioHostPort
	skipSystemdForTest = *skipSystemd
	if *selftest {
		if err := cryptoSelfTest(); err != nil {
			log.Fatal(err)
		}
		fmt.Println("DIRECT_SELFTEST_OK")
		return
	}
	c, e := newCore(*dir, *call, *server)
	if e != nil {
		log.Fatal(e)
	}
	defer c.conn.Close()
	c.forceRelay = *forceRelay
	go c.udpLoop()
	go c.registerLoop()
	go c.keepaliveLoop()
	go c.autoCallLoop()
	mux := http.NewServeMux()
	mux.HandleFunc("/", c.apiHandler)
	log.Printf("PU2PNY Direct %s %s API %s", version, c.id.Callsign, *api)
	log.Fatal(http.ListenAndServe(*api, mux))
}

func cryptoSelfTest() error {
	td, e := os.MkdirTemp("", "direct-test")
	if e != nil {
		return e
	}
	defer os.RemoveAll(td)
	a, e := newCore(filepath.Join(td, "a"), "PU2AAA", "127.0.0.1:9")
	if e != nil {
		return e
	}
	defer a.conn.Close()
	b, e := newCore(filepath.Join(td, "b"), "PU2BBB", "127.0.0.1:9")
	if e != nil {
		return e
	}
	defer b.conn.Close()
	pa := peer{Callsign: "PU2AAA", EdPub: a.id.EdPub, XPub: a.id.XPub}
	pb := peer{Callsign: "PU2BBB", EdPub: b.id.EdPub, XPub: b.id.XPub}
	a.peers["PU2BBB"] = pb
	b.peers["PU2AAA"] = pa
	raw, e := a.encrypt("PU2BBB", "message", []byte("73"))
	if e != nil {
		return e
	}
	pkt, plain, e := b.decrypt(raw)
	if e != nil {
		return e
	}
	if pkt.From != "PU2AAA" || !bytes.Equal(plain, []byte("73")) {
		return errors.New("roundtrip failed")
	}
	if _, _, e = b.decrypt(raw); e == nil {
		return errors.New("replay accepted")
	}
	return nil
}
