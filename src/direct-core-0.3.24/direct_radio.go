package main

import (
	"errors"
	"fmt"
	"net"
	"os/exec"
	"strings"
	"time"
)

type radioProfile struct {
	GatewayPort int
	HostPort    int
	Unit        string
}

var radioGatewayPortOverride int
var radioHostPortOverride int
var skipSystemdForTest bool

var directRadioProfiles = map[string]radioProfile{
	"DMR":   {GatewayPort: 62031, HostPort: 62032, Unit: "2pny-dmrgateway.service"},
	"DSTAR": {GatewayPort: 20010, HostPort: 20011, Unit: "2pny-dstargateway.service"},
	"YSF":   {GatewayPort: 4200, HostPort: 3200, Unit: "2pny-ysfgateway.service"},
}

func systemdActive(unit string) bool {
	return exec.Command("systemctl", "is-active", "--quiet", unit).Run() == nil
}

func waitSystemdInactive(unit string, timeout time.Duration) bool {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if !systemdActive(unit) {
			return true
		}
		time.Sleep(80 * time.Millisecond)
	}
	return !systemdActive(unit)
}

func (c *core) enterRadio(proto string) error {
	proto = strings.ToUpper(strings.TrimSpace(proto))
	p, ok := directRadioProfiles[proto]
	if !ok {
		return fmt.Errorf("PU2PNY Direct RF ainda não suporta %s", proto)
	}
	if radioGatewayPortOverride > 0 { p.GatewayPort = radioGatewayPortOverride }
	if radioHostPortOverride > 0 { p.HostPort = radioHostPortOverride }

	c.mu.Lock()
	if c.st.RadioActive {
		if c.radioProto == proto {
			c.mu.Unlock()
			return nil
		}
		c.mu.Unlock()
		return errors.New("ponte Direct RF já está ativa em outro protocolo")
	}
	c.mu.Unlock()

	wasActive := false
	if !skipSystemdForTest { wasActive = systemdActive(p.Unit) }
	if wasActive {
		if out, err := exec.Command("systemctl", "stop", p.Unit).CombinedOutput(); err != nil {
			return fmt.Errorf("não foi possível pausar %s: %s", p.Unit, strings.TrimSpace(string(out)))
		}
		if !waitSystemdInactive(p.Unit, 2500*time.Millisecond) {
			_ = exec.Command("systemctl", "start", p.Unit).Run()
			return fmt.Errorf("%s não liberou a porta local do protocolo", p.Unit)
		}
	}

	conn, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: p.GatewayPort})
	if err != nil {
		if wasActive {
			_ = exec.Command("systemctl", "start", p.Unit).Run()
		}
		return fmt.Errorf("porta local Direct %d indisponível: %w", p.GatewayPort, err)
	}

	stop := make(chan struct{})
	c.mu.Lock()
	c.radioConn = conn
	c.radioStop = stop
	c.radioProto = proto
	c.gatewayUnit = p.Unit
	c.gatewayWasActive = wasActive
	c.lastPeerTraffic = time.Now()
	c.st.RadioActive = true
	c.st.GatewayRestore = wasActive
	c.st.Protocol = proto
	c.writeState()
	c.mu.Unlock()

	go c.radioLoop(conn, stop, proto, p.HostPort)
	return nil
}

func (c *core) radioLoop(conn *net.UDPConn, stop <-chan struct{}, proto string, hostPort int) {
	buf := make([]byte, 4096)
	for {
		_ = conn.SetReadDeadline(time.Now().Add(2 * time.Second))
		n, src, err := conn.ReadFromUDP(buf)
		if err != nil {
			if ne, ok := err.(net.Error); ok && ne.Timeout() {
				select {
				case <-stop:
					return
				default:
					continue
				}
			}
			return
		}
		// Only accept frames from the local MMDVMHost port. This is a loopback
		// gateway shim, not a general UDP listener.
		if src == nil || !src.IP.IsLoopback() || src.Port != hostPort || n <= 0 {
			continue
		}
		frame := append([]byte(nil), buf[:n]...)
		c.mu.Lock()
		peer := c.st.Peer
		relay := c.st.Path == "Relay"
		connected := c.st.Status == "connected"
		c.mu.Unlock()
		if !connected || peer == "" {
			continue
		}
		_ = c.sendSecure(peer, "radio:"+proto, frame, relay)
	}
}

func (c *core) deliverRadio(proto string, frame []byte) error {
	c.mu.Lock()
	conn := c.radioConn
	active := c.st.RadioActive && c.radioProto == proto
	c.mu.Unlock()
	if !active || conn == nil {
		return errors.New("ponte Direct RF inativa")
	}
	p, ok := directRadioProfiles[proto]
	if !ok {
		return errors.New("protocolo Direct RF inválido")
	}
	if radioHostPortOverride > 0 { p.HostPort = radioHostPortOverride }
	if len(frame) == 0 || len(frame) > 4096 {
		return errors.New("quadro Direct RF inválido")
	}
	_, err := conn.WriteToUDP(frame, &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: p.HostPort})
	return err
}

func (c *core) exitRadio() {
	c.mu.Lock()
	conn := c.radioConn
	stop := c.radioStop
	unit := c.gatewayUnit
	restore := c.gatewayWasActive
	c.radioConn = nil
	c.radioStop = nil
	c.radioProto = ""
	c.gatewayUnit = ""
	c.gatewayWasActive = false
	c.st.RadioActive = false
	c.st.GatewayRestore = false
	c.writeState()
	c.mu.Unlock()

	if stop != nil {
		select {
		case <-stop:
		default:
			close(stop)
		}
	}
	if conn != nil {
		_ = conn.Close()
	}
	if restore && unit != "" {
		_ = exec.Command("systemctl", "start", unit).Run()
	}
}

func (c *core) touchPeerTraffic() {
	c.mu.Lock()
	c.lastPeerTraffic = time.Now()
	c.mu.Unlock()
}

func (c *core) keepaliveLoop() {
	t := time.NewTicker(5 * time.Second)
	defer t.Stop()
	for range t.C {
		c.mu.Lock()
		peer := c.st.Peer
		relay := c.st.Path == "Relay"
		connected := c.st.Status == "connected"
		incoming := c.st.Status == "incoming"
		incomingAt := c.incomingAt
		radio := c.st.RadioActive
		last := c.lastPeerTraffic
		c.mu.Unlock()

		if incoming && !incomingAt.IsZero() && time.Since(incomingAt) > 35*time.Second {
			c.mu.Lock()
			if c.st.Status == "incoming" {
				c.st.Status = "idle"
				c.st.Peer = ""
				c.st.Path = "Offline"
				c.st.LastError = "chamada recebida expirou sem aceitação pelo rádio"
				c.incomingPeer = ""
				c.incomingRelayed = false
				c.incomingProbe = nil
				c.incomingAt = time.Time{}
				c.writeState()
			}
			c.mu.Unlock()
		}
		if connected && peer != "" {
			_ = c.sendSecure(peer, "keepalive", []byte("k"), relay)
		}
		if radio && !last.IsZero() && time.Since(last) > 22*time.Second {
			c.exitRadio()
			c.mu.Lock()
			c.st.Status = "error"
			c.st.Peer = ""
			c.st.Path = "Offline"
			c.st.LatencyMS = 0
			c.st.LastError = "PU2PNY Direct perdeu o peer; gateway anterior restaurado"
			c.writeState()
			c.mu.Unlock()
		}
	}
}
