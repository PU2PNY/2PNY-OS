package main

import (
	"crypto/ed25519"
	"encoding/json"
	"errors"
	"log"
	"net"
	"strconv"
	"strings"
	"time"
)

func (c *core) pairCallsign(to string) (peer, error) {
	to = strings.ToUpper(strings.TrimSpace(to))
	if !callRE.MatchString(to) || to == c.id.Callsign {
		return peer{}, errors.New("indicativo inválido")
	}
	res, e := c.lookup(to)
	if e != nil {
		return peer{}, e
	}
	ed, e := unb64(res.Ed)
	if e != nil || len(ed) != ed25519.PublicKeySize {
		return peer{}, errors.New("identidade remota inválida")
	}
	if !verifyCtrl(res, ed25519.PublicKey(ed)) {
		return peer{}, errors.New("resposta remota não autenticada")
	}
	p := peer{Callsign: to, EdPub: res.Ed, XPub: res.X, Fingerprint: fingerprint(ed), PairedAt: time.Now().UTC().Format(time.RFC3339)}
	c.mu.Lock()
	c.peers[to] = p
	e = savePeers(c.dir, c.peers)
	c.mu.Unlock()
	return p, e
}

func (c *core) handlePacket(raw []byte, addr *net.UDPAddr) {
	var m ctrl
	if json.Unmarshal(raw, &m) == nil && m.T != "" {
		switch m.T {
		case "lookup-query":
			resp := ctrl{T: "lookup-result", From: c.id.Callsign, To: m.From, Nonce: m.Nonce, Ed: c.id.EdPub, X: c.id.XPub, FP: fingerprint(c.edPub), Protocol: currentProtocol()}
			c.sign(&resp)
			c.sendCtrl(c.serverAddr, resp)
		case "lookup-result":
			c.mu.Lock()
			ch := c.pending[m.Nonce]
			c.mu.Unlock()
			if ch != nil {
				select {
				case ch <- m:
				default:
				}
			}
		case "incoming":
			ed, e := unb64(m.Ed)
			if e != nil || len(ed) != ed25519.PublicKeySize || !verifyCtrl(m, ed25519.PublicKey(ed)) {
				return
			}
			c.mu.Lock()
			p := c.peers[m.From]
			c.mu.Unlock()
			if p.Callsign == "" || p.EdPub != m.Ed || p.XPub != m.X {
				return
			}
			if ep, e := net.ResolveUDPAddr("udp", m.Endpoint); e == nil {
				c.mu.Lock()
				c.peerEndpoints[m.From] = ep
				c.mu.Unlock()
			}
		case "relay-data":
			b, e := unb64(m.Packet)
			if e == nil {
				c.handleSecure(b, addr, true)
			}
		}
		return
	}
	c.handleSecure(raw, addr, false)
}
func (c *core) handleSecure(raw []byte, addr *net.UDPAddr, relayed bool) {
	pkt, plain, e := c.decrypt(raw)
	if e != nil {
		return
	}
	c.touchPeerTraffic()
	if !relayed {
		c.mu.Lock()
		c.peerEndpoints[pkt.From] = addr
		c.mu.Unlock()
	}
	switch pkt.Kind {
	case "probe":
		proto := currentProtocol()
		if _, ok := directRadioProfiles[proto]; !ok { return }
		path := "Direct"
		if relayed { path = "Relay" }
		c.mu.Lock()
		c.st.Status = "connected"
		c.st.Peer = pkt.From
		c.st.Path = path
		c.st.Protocol = proto
		c.st.LastError = ""
		c.lastPeerTraffic = time.Now()
		c.writeState()
		c.mu.Unlock()
		if err := c.enterRadio(proto); err != nil {
			c.mu.Lock()
			c.st.Status = "error"; c.st.Path = "Offline"; c.st.LastError = err.Error(); c.writeState()
			c.mu.Unlock()
			return
		}
		_ = c.sendSecure(pkt.From, "probe-ack", plain, relayed)
	case "probe-ack":
		c.mu.Lock()
		ch := c.probeWait[pkt.From]
		c.mu.Unlock()
		if ch != nil {
			d := 25 * time.Millisecond
			if ns, err := strconv.ParseInt(string(plain), 10, 64); err == nil {
				d = time.Since(time.Unix(0, ns))
			}
			select {
			case ch <- d:
			default:
			}
		}
	case "hangup":
		c.exitRadio()
		c.mu.Lock()
		c.st.Status = "idle"
		c.st.Peer = ""
		c.st.Path = "Offline"
		c.st.LatencyMS = 0
		c.st.LastError = ""
		c.writeState()
		c.mu.Unlock()
	case "keepalive":
		_ = c.sendSecure(pkt.From, "keepalive-ack", []byte("k"), relayed)
	case "keepalive-ack":
		// touchPeerTraffic above is sufficient.
	case "message":
		log.Printf("Direct message from %s: %s", pkt.From, string(plain))
	default:
		if strings.HasPrefix(pkt.Kind, "radio:") {
			proto := strings.TrimPrefix(pkt.Kind, "radio:")
			_ = c.deliverRadio(proto, plain)
		}
	}
}
func (c *core) udpLoop() {
	buf := make([]byte, 65535)
	for {
		n, a, e := c.conn.ReadFromUDP(buf)
		if e != nil {
			return
		}
		raw := append([]byte(nil), buf[:n]...)
		go c.handlePacket(raw, a)
	}
}
func (c *core) registerLoop() {
	t := time.NewTicker(20 * time.Second)
	defer t.Stop()
	for {
		c.register()
		<-t.C
	}
}
