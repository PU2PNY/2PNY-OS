package main

import (
    "bytes"
    "encoding/json"
    "net/http/httptest"
    "os"
    "path/filepath"
    "testing"
    "strings"
    "time"
)

func Test502CanonicalCaptivePortal(t *testing.T) {
    for _, host := range []string{"10.43.0.1", "pu2pny.local", "untrusted.example"} {
        r := httptest.NewRequest("GET", "http://"+host+"/api/captive", nil)
        w := httptest.NewRecorder()
        captiveAPIHandler(w,r)
        var data map[string]any
        if err := json.Unmarshal(w.Body.Bytes(),&data); err != nil { t.Fatal(err) }
        portal, _ := data["user-portal-url"].(string)
        if !strings.HasPrefix(portal,"http://pu2pny.local/") { t.Fatal("noncanonical captive portal",host,portal) }
        if w.Header().Get("Content-Type")!="application/captive+json" { t.Fatal("wrong captive API type") }
    }
}

func Test502AtomicLiveUpdates(t *testing.T) {
    dir := t.TempDir()
    path := filepath.Join(dir,"live-state.json")
    go watchLiveState502(path)
    for _, payload := range []string{`{"sequence":1}`,`{"sequence":2}`,`{"sequence":3}`} {
        tmp := path+".tmp"
        if err := os.WriteFile(tmp,[]byte(payload),0600); err != nil { t.Fatal(err) }
        if err := os.Rename(tmp,path); err != nil { t.Fatal(err) }
        deadline := time.Now().Add(2*time.Second)
        for !bytes.Equal(liveHub.current().data,[]byte(payload)) {
            if time.Now().After(deadline) { t.Fatal("lost atomic update",payload) }
            time.Sleep(10*time.Millisecond)
        }
    }
    sequence := liveHub.current().id
    os.WriteFile(filepath.Join(dir,"unrelated.json"),[]byte(`{}`),0600)
    time.Sleep(50*time.Millisecond)
    if liveHub.current().id != sequence { t.Fatal("unrelated event published") }
}
