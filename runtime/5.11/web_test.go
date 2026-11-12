package main
import("net/http/httptest";"testing";"strings")
func Test511CaptiveCanonical(t *testing.T){
 for _,path:=range []string{"/generate_204","/hotspot-detect.html","/connecttest.txt","/unknown-probe"}{
  r:=httptest.NewRequest("GET","http://probe.invalid"+path,nil);w:=httptest.NewRecorder();captivePortalHandler(w,r)
  if w.Code!=302||w.Header().Get("Location")!="http://EXPECTED_HOST/wizard?captive=1"{t.Fatalf("redirect %s: %d %s",path,w.Code,w.Header().Get("Location"))}
 }
}
func Test511MutationsRejectForeignOrigin(t *testing.T){
 for _,handler:=range []func(*httptest.ResponseRecorder){
  func(w *httptest.ResponseRecorder){r:=httptest.NewRequest("POST","http://localhost/api/voice/settings",strings.NewReader(`{"dmr":false,"language":"pt"}`));r.Header.Set("Origin","https://foreign.invalid");voice511Handler(w,r)},
  func(w *httptest.ResponseRecorder){r:=httptest.NewRequest("POST","http://localhost/api/mode/settings",strings.NewReader(`{"mode":"off"}`));r.Header.Set("Origin","https://foreign.invalid");mode511Handler(w,r)},
 }{w:=httptest.NewRecorder();handler(w);if w.Code!=403{t.Fatalf("origem estrangeira: %d",w.Code)}}
}
func Test511DestinationValidation(t *testing.T){
 for _,proto:=range []string{"../secrets","DSTAR",""}{r:=httptest.NewRequest("GET","http://localhost/api/mode/destinations?protocol="+proto,nil);w:=httptest.NewRecorder();mode511Destinations(w,r);if w.Code!=400{t.Fatalf("protocolo rejeitado: %d",w.Code)}}
}
