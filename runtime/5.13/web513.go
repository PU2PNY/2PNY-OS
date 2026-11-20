package main

import (
	"net"
	"net/http"
	"sync"
	"time"
)

const setup513IP = "10.43.0.1"

var clock513Mu sync.Mutex

func localClock513(zone string) time.Time {
	now := time.Now()
	if loc, err := time.LoadLocation(zone); err == nil && zone != "" {
		return now.In(loc)
	}
	return now
}

func clock513LocalClient(r *http.Request) bool {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return false
	}
	ip := net.ParseIP(host)
	return ip != nil && (ip.IsPrivate() || ip.IsLoopback() || ip.IsLinkLocalUnicast())
}

func captive513Request(r *http.Request) bool {
	addr, _ := r.Context().Value(http.LocalAddrContextKey).(net.Addr)
	if addr == nil {
		return false
	}
	host, _, err := net.SplitHostPort(addr.String())
	return err == nil && host == setup513IP
}

func captive513Path() string {
	if fileExists(provisionedFile) {
		return "/internet"
	}
	return "/wizard"
}

func captive513URL() string {
	return "http://" + setup513IP + captive513Path()
}
