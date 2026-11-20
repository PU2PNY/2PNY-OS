package main

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
)

func Test513PortalUsesSetupInterface(t *testing.T) {
	for _, path := range []string{"/generate_204", "/hotspot-detect.html", "/connecttest.txt"} {
		req := httptest.NewRequest("GET", "http://probe.invalid"+path, nil)
		req = req.WithContext(context.WithValue(req.Context(), http.LocalAddrContextKey, &net.TCPAddr{IP: net.ParseIP(setup513IP), Port: 80}))
		w := httptest.NewRecorder()
		captivePortalHandler(w, req)
		if w.Code != http.StatusFound || w.Header().Get("Location") != "http://10.43.0.1"+captive513Path() {
			t.Fatalf("setup path %s: %d %s", path, w.Code, w.Header().Get("Location"))
		}
	}
	req := httptest.NewRequest("GET", "http://"+setup513IP+"/generate_204", nil)
	w := httptest.NewRecorder()
	captivePortalHandler(w, req)
	if w.Code != http.StatusNoContent {
		t.Fatalf("a Host header must not activate the portal: %d", w.Code)
	}
}
