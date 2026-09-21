package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/ecdh"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net"
	"strings"
	"time"
)

func (c *core) sendCtrl(addr *net.UDPAddr, m ctrl) {
	raw, _ := json.Marshal(m)
	if _, err := c.conn.WriteToUDP(raw, addr); err != nil {
		log.Printf("Direct UDP send failed: %v", err)
	}
}
func (c *core) register() {
	log.Printf("Direct register %s -> %s", c.id.Callsign, c.serverAddr)
	m := ctrl{T: "reg", From: c.id.Callsign, Ed: c.id.EdPub, X: c.id.XPub, FP: fingerprint(c.edPub), Protocol: currentProtocol()}
	c.sign(&m)
	c.sendCtrl(c.serverAddr, m)
}

func (c *core) lookup(to string) (ctrl, error) {
	to = strings.ToUpper(strings.TrimSpace(to))
	// P2P-006: refresh our rendezvous record immediately before lookup. This
	// reduces cross-version/stale-registration failures without changing the
	// signed identity, fingerprint or pairing trust model.
	c.register()
	time.Sleep(120 * time.Millisecond)
	nonceRaw := make([]byte, 12)
	_, _ = rand.Read(nonceRaw)
	n := b64(nonceRaw)
	ch := make(chan ctrl, 1)
	c.mu.Lock()
	c.pending[n] = ch
	c.mu.Unlock()
	defer func() { c.mu.Lock(); delete(c.pending, n); c.mu.Unlock() }()
	m := ctrl{T: "lookup", From: c.id.Callsign, To: to, Nonce: n, Ed: c.id.EdPub, X: c.id.XPub}
	c.sign(&m)
	c.sendCtrl(c.serverAddr, m)
	select {
	case v := <-ch:
		if v.Error != "" {
			return v, errors.New(v.Error)
		}
		return v, nil
	case <-time.After(4 * time.Second):
		return ctrl{}, errors.New("rendezvous timeout")
	}
}

func (c *core) peerKey(p peer) ([]byte, error) {
	xb, e := unb64(p.XPub)
	if e != nil {
		return nil, e
	}
	pk, e := ecdh.X25519().NewPublicKey(xb)
	if e != nil {
		return nil, e
	}
	shared, e := c.xPriv.ECDH(pk)
	if e != nil {
		return nil, e
	}
	h := sha256.Sum256(append([]byte("PU2PNY-DIRECT-v1|"+min(c.id.Callsign, p.Callsign)+"|"+max(c.id.Callsign, p.Callsign)+"|"), shared...))
	return h[:], nil
}
func min(a, b string) string {
	if a < b {
		return a
	}
	return b
}
func max(a, b string) string {
	if a > b {
		return a
	}
	return b
}

func (c *core) encrypt(to, kind string, plain []byte) ([]byte, error) {
	c.mu.Lock()
	p, ok := c.peers[to]
	c.seq++
	seq := c.seq
	c.mu.Unlock()
	if !ok {
		return nil, errors.New("peer not paired")
	}
	key, e := c.peerKey(p)
	if e != nil {
		return nil, e
	}
	block, e := aes.NewCipher(key)
	if e != nil {
		return nil, e
	}
	g, e := cipher.NewGCM(block)
	if e != nil {
		return nil, e
	}
	nonce := make([]byte, g.NonceSize())
	binary.BigEndian.PutUint64(nonce[len(nonce)-8:], seq)
	h := sha256.Sum256([]byte(c.id.Callsign))
	copy(nonce, h[:len(nonce)-8])
	aad := []byte(c.id.Callsign + "|" + to + "|" + kind)
	enc := g.Seal(nil, nonce, plain, aad)
	pkt := securePacket{From: c.id.Callsign, To: to, Seq: seq, Kind: kind, Nonce: b64(nonce), Data: b64(enc)}
	return json.Marshal(pkt)
}
func (c *core) decrypt(raw []byte) (securePacket, []byte, error) {
	var pkt securePacket
	if json.Unmarshal(raw, &pkt) != nil {
		return pkt, nil, errors.New("bad packet")
	}
	c.mu.Lock()
	p, ok := c.peers[pkt.From]
	high := c.lastSeq[pkt.From]
	c.mu.Unlock()
	if !ok {
		return pkt, nil, errors.New("unpaired peer")
	}
	if pkt.Seq <= high {
		return pkt, nil, errors.New("replay")
	}
	key, e := c.peerKey(p)
	if e != nil {
		return pkt, nil, e
	}
	block, e := aes.NewCipher(key)
	if e != nil {
		return pkt, nil, e
	}
	g, e := cipher.NewGCM(block)
	if e != nil {
		return pkt, nil, e
	}
	nonce, e := unb64(pkt.Nonce)
	if e != nil {
		return pkt, nil, e
	}
	enc, e := unb64(pkt.Data)
	if e != nil {
		return pkt, nil, e
	}
	plain, e := g.Open(nil, nonce, enc, []byte(pkt.From+"|"+pkt.To+"|"+pkt.Kind))
	if e != nil {
		return pkt, nil, e
	}
	c.mu.Lock()
	c.lastSeq[pkt.From] = pkt.Seq
	c.mu.Unlock()
	return pkt, plain, nil
}

func (c *core) sendSecure(to, kind string, payload []byte, forceRelay bool) error {
	raw, e := c.encrypt(to, kind, payload)
	if e != nil {
		return e
	}
	c.mu.Lock()
	ep := c.peerEndpoints[to]
	c.mu.Unlock()
	if !forceRelay && ep != nil {
		if _, e = c.conn.WriteToUDP(raw, ep); e == nil {
			return nil
		}
	}
	m := ctrl{T: "relay", From: c.id.Callsign, To: to, Packet: b64(raw)}
	c.sign(&m)
	c.sendCtrl(c.serverAddr, m)
	return nil
}

func (c *core) call(to string) error {
	to = strings.ToUpper(strings.TrimSpace(to))
	c.mu.Lock()
	paired := c.peers[to]
	c.mu.Unlock()
	if paired.Callsign == "" {
		return errors.New("pareie o indicativo antes da chamada")
	}
	res, e := c.lookup(to)
	if e != nil {
		return e
	}
	if !strings.EqualFold(res.Ed, paired.EdPub) || !strings.EqualFold(res.X, paired.XPub) {
		return errors.New("identidade remota diferente do pareamento salvo")
	}
	localProto := currentProtocol()
	remoteProto := strings.ToUpper(strings.TrimSpace(res.Protocol))
	if localProto != "" && remoteProto != "" && localProto != remoteProto {
		return fmt.Errorf("protocolo remoto incompatível: local %s, remoto %s", localProto, remoteProto)
	}
	ep, e := net.ResolveUDPAddr("udp", res.Endpoint)
	if e != nil {
		return e
	}
	c.mu.Lock()
	c.peerEndpoints[to] = ep
	c.st.Status = "connecting"
	c.st.Peer = to
	c.st.Path = "Offline"
	c.st.LastError = ""
	c.st.Protocol = localProto
	c.writeState()
	c.mu.Unlock()
	ch := make(chan time.Duration, 1)
	c.mu.Lock()
	c.probeWait[to] = ch
	c.mu.Unlock()
	defer func() { c.mu.Lock(); delete(c.probeWait, to); c.mu.Unlock() }()
	if !c.forceRelay {
		_ = c.sendSecure(to, "probe", []byte(fmt.Sprintf("%d", time.Now().UnixNano())), false)
		select {
		case d := <-ch:
			c.mu.Lock()
			c.st.Status = "connected"
			c.st.Path = "Direct"
			c.st.LatencyMS = d.Milliseconds()
			c.lastPeerTraffic = time.Now()
			c.writeState()
			c.mu.Unlock()
			if err := c.enterRadio(localProto); err != nil {
				_ = c.sendSecure(to, "hangup", []byte("radio-setup-failed"), false)
				c.mu.Lock()
				c.st.Status = "error"; c.st.Path = "Offline"; c.st.LastError = err.Error(); c.writeState()
				c.mu.Unlock()
				return err
			}
			return nil
		case <-time.After(2500 * time.Millisecond):
		}
	}
	_ = c.sendSecure(to, "probe", []byte(fmt.Sprintf("%d", time.Now().UnixNano())), true)
	select {
		case d := <-ch:
			c.mu.Lock()
			c.st.Status = "connected"
			c.st.Path = "Relay"
			c.st.LatencyMS = d.Milliseconds()
			c.lastPeerTraffic = time.Now()
			c.writeState()
			c.mu.Unlock()
			if err := c.enterRadio(localProto); err != nil {
				_ = c.sendSecure(to, "hangup", []byte("radio-setup-failed"), true)
				c.mu.Lock()
				c.st.Status = "error"; c.st.Path = "Offline"; c.st.LastError = err.Error(); c.writeState()
				c.mu.Unlock()
				return err
			}
			return nil
	case <-time.After(4 * time.Second):
			c.mu.Lock()
			c.st.Status = "error"
			c.st.Path = "Offline"
			c.st.LastError = "peer sem resposta"
			c.writeState()
			c.mu.Unlock()
			return errors.New("peer sem resposta")
	}
	return nil
}
