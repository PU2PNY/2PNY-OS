package main

import (
	"crypto/ecdh"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"
)

const version = "0.3.7-alpha"
const defaultServer = "xlx026.net:43070"
const defaultAPIAddr = "127.0.0.1:43071"

type identity struct {
	Callsign string `json:"callsign"`
	EdPriv   string `json:"ed25519_private"`
	EdPub    string `json:"ed25519_public"`
	XPriv    string `json:"x25519_private"`
	XPub     string `json:"x25519_public"`
}

type peer struct {
	Callsign    string `json:"callsign"`
	EdPub       string `json:"ed25519_public"`
	XPub        string `json:"x25519_public"`
	Fingerprint string `json:"fingerprint"`
	PairedAt    string `json:"paired_at"`
}

type state struct {
	Version     string `json:"version"`
	Enabled     bool   `json:"enabled"`
	Callsign    string `json:"callsign"`
	Server      string `json:"server"`
	Status      string `json:"status"`
	Peer        string `json:"peer,omitempty"`
	Path        string `json:"path"`
	Encrypted   bool   `json:"encrypted"`
	LatencyMS   int64  `json:"latency_ms,omitempty"`
	Fingerprint string `json:"fingerprint,omitempty"`
	Protocol    string `json:"protocol,omitempty"`
	RadioActive bool   `json:"radio_active"`
	GatewayRestore bool `json:"gateway_restore,omitempty"`
	LastError   string `json:"last_error,omitempty"`
	Updated     string `json:"updated"`
}

type ctrl struct {
	T        string `json:"t"`
	From     string `json:"from,omitempty"`
	To       string `json:"to,omitempty"`
	Ed       string `json:"ed,omitempty"`
	X        string `json:"x,omitempty"`
	FP       string `json:"fp,omitempty"`
	Nonce    string `json:"nonce,omitempty"`
	Endpoint string `json:"endpoint,omitempty"`
	Packet   string `json:"packet,omitempty"`
	TS       int64  `json:"ts,omitempty"`
	Sig      string `json:"sig,omitempty"`
	Error    string `json:"error,omitempty"`
	Protocol string `json:"protocol,omitempty"`
}

type securePacket struct {
	From  string `json:"from"`
	To    string `json:"to"`
	Seq   uint64 `json:"seq"`
	Kind  string `json:"kind"`
	Nonce string `json:"nonce"`
	Data  string `json:"data"`
}

type pairFile struct {
	Peers map[string]peer `json:"peers"`
}

type core struct {
	mu            sync.Mutex
	dir           string
	server        string
	id            identity
	edPriv        ed25519.PrivateKey
	edPub         ed25519.PublicKey
	xPriv         *ecdh.PrivateKey
	conn          *net.UDPConn
	serverAddr    *net.UDPAddr
	peers         map[string]peer
	peerEndpoints map[string]*net.UDPAddr
	lastSeq       map[string]uint64
	seq           uint64
	st            state
	pending       map[string]chan ctrl
	probeWait     map[string]chan time.Duration
	forceRelay    bool
	radioConn     *net.UDPConn
	radioStop     chan struct{}
	radioProto    string
	gatewayUnit   string
	gatewayWasActive bool
	lastPeerTraffic time.Time
}

var callRE = regexp.MustCompile(`^[A-Z0-9]{3,8}(?:-[A-Z0-9]{1,2})?$`)

func b64(b []byte) string            { return base64.RawStdEncoding.EncodeToString(b) }
func unb64(s string) ([]byte, error) { return base64.RawStdEncoding.DecodeString(s) }
func fingerprint(pub []byte) string {
	h := sha256.Sum256(pub)
	return strings.ToUpper(hex.EncodeToString(h[:6]))
}
func atomic(path string, data []byte, mode os.FileMode) error {
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, data, mode); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

func loadOrCreateIdentity(dir, callsign string) (identity, ed25519.PrivateKey, ed25519.PublicKey, *ecdh.PrivateKey, error) {
	p := filepath.Join(dir, "identity.json")
	if b, err := os.ReadFile(p); err == nil {
		var v identity
		if json.Unmarshal(b, &v) == nil && strings.EqualFold(v.Callsign, callsign) {
			ep, _ := unb64(v.EdPriv)
			eu, _ := unb64(v.EdPub)
			xp, _ := unb64(v.XPriv)
			xk, e := ecdh.X25519().NewPrivateKey(xp)
			if e == nil && len(ep) == ed25519.PrivateKeySize && len(eu) == ed25519.PublicKeySize {
				return v, ed25519.PrivateKey(ep), ed25519.PublicKey(eu), xk, nil
			}
		}
	}
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return identity{}, nil, nil, nil, err
	}
	xk, err := ecdh.X25519().GenerateKey(rand.Reader)
	if err != nil {
		return identity{}, nil, nil, nil, err
	}
	v := identity{Callsign: callsign, EdPriv: b64(priv), EdPub: b64(pub), XPriv: b64(xk.Bytes()), XPub: b64(xk.PublicKey().Bytes())}
	raw, _ := json.MarshalIndent(v, "", "  ")
	if err := atomic(p, raw, 0600); err != nil {
		return identity{}, nil, nil, nil, err
	}
	return v, priv, pub, xk, nil
}

func loadPeers(dir string) map[string]peer {
	out := map[string]peer{}
	b, e := os.ReadFile(filepath.Join(dir, "peers.json"))
	if e != nil {
		return out
	}
	var pf pairFile
	if json.Unmarshal(b, &pf) == nil && pf.Peers != nil {
		return pf.Peers
	}
	return out
}
func savePeers(dir string, p map[string]peer) error {
	raw, _ := json.MarshalIndent(pairFile{Peers: p}, "", "  ")
	return atomic(filepath.Join(dir, "peers.json"), raw, 0600)
}

func signBytes(c ctrl) []byte {
	return []byte(strings.Join([]string{c.T, c.From, c.To, c.Ed, c.X, c.Nonce, c.Protocol, fmt.Sprint(c.TS)}, "|"))
}
func (c *core) sign(m *ctrl) {
	m.TS = time.Now().Unix()
	m.Sig = b64(ed25519.Sign(c.edPriv, signBytes(*m)))
}
func verifyCtrl(m ctrl, pub ed25519.PublicKey) bool {
	if time.Since(time.Unix(m.TS, 0)) > 2*time.Minute || time.Until(time.Unix(m.TS, 0)) > 2*time.Minute {
		return false
	}
	sig, e := unb64(m.Sig)
	return e == nil && ed25519.Verify(pub, signBytes(m), sig)
}

func currentProtocol() string {
	b, err := os.ReadFile("/var/lib/2pny/config.json")
	if err != nil { return "" }
	var v struct { Protocol string `json:"protocol"` }
	if json.Unmarshal(b, &v) != nil { return "" }
	p := strings.ToUpper(strings.TrimSpace(v.Protocol))
	switch p {
	case "DMR","DSTAR","YSF","P25","NXDN","POCSAG":
		return p
	default:
		return ""
	}
}

func newCore(dir, callsign, server string) (*core, error) {
	callsign = strings.ToUpper(strings.TrimSpace(callsign))
	if !callRE.MatchString(callsign) {
		return nil, errors.New("invalid callsign")
	}
	id, priv, pub, xk, err := loadOrCreateIdentity(dir, callsign)
	if err != nil {
		return nil, err
	}
	ra, err := net.ResolveUDPAddr("udp", server)
	if err != nil {
		return nil, err
	}
	conn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4zero, Port: 0})
	if err != nil {
		return nil, err
	}
	c := &core{dir: dir, server: server, id: id, edPriv: priv, edPub: pub, xPriv: xk, conn: conn, serverAddr: ra, peers: loadPeers(dir), peerEndpoints: map[string]*net.UDPAddr{}, lastSeq: map[string]uint64{}, pending: map[string]chan ctrl{}, probeWait: map[string]chan time.Duration{}}
	c.st = state{Version: version, Enabled: true, Callsign: callsign, Server: server, Status: "idle", Path: "Offline", Encrypted: true, Fingerprint: fingerprint(pub), Protocol: currentProtocol(), Updated: time.Now().UTC().Format(time.RFC3339)}
	c.writeState()
	return c, nil
}
func (c *core) writeState() {
	c.st.Updated = time.Now().UTC().Format(time.RFC3339)
	raw, _ := json.MarshalIndent(c.st, "", "  ")
	_ = os.MkdirAll("/run/2pny", 0755)
	_ = atomic("/run/2pny/direct-state.json", raw, 0644)
}
