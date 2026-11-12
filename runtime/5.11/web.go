package main

import (
    "encoding/json"
    "net/http"
)

// VOICE-511: serviço privilegiado aplica INIs antes de confirmar sucesso.
func voice511Handler(w http.ResponseWriter, r *http.Request) {
    if r.Method == http.MethodGet {
        writeJSON(w, http.StatusOK, readPublicJSON(dataDir+"/voice-settings.json"))
        return
    }
    if r.Method != http.MethodPost || !sameOrigin(r) || !fileExists(provisionedFile) {
        http.Error(w,"pedido rejeitado",http.StatusForbidden); return
    }
    var in struct {
        DMR bool `json:"dmr"`
        DStar bool `json:"dstar"`
        P25 bool `json:"p25"`
        NXDN bool `json:"nxdn"`
        Hourly bool `json:"hourly"`
        Language string `json:"language"`
    }
    if json.NewDecoder(http.MaxBytesReader(w,r.Body,2048)).Decode(&in) != nil || (in.Language!="pt" && in.Language!="en" && in.Language!="es") {
        http.Error(w,"opções inválidas",http.StatusBadRequest); return
    }
    if !applyMu.TryLock() { http.Error(w,"outra alteração está em andamento",http.StatusConflict); return }
    defer applyMu.Unlock()
    settings:=map[string]any{"dmr":in.DMR,"dstar":in.DStar,"p25":in.P25,"nxdn":in.NXDN,"hourly":in.Hourly,"language":in.Language}
    res,err:=runPrivilegedRequest("2pny-voice-apply.service","/run/2pny/voice-request.json","/run/2pny/voice-result.json",settings)
    if err!=nil { writeJSON(w,http.StatusServiceUnavailable,map[string]any{"ok":false,"error":"não foi possível aplicar a voz","result":res}); return }
    writeJSON(w,http.StatusOK,res)
}
func init() { http.HandleFunc("/api/voice/settings",voice511Handler) }

func mode511Handler(w http.ResponseWriter,r *http.Request) {
    if r.Method!=http.MethodPost || !sameOrigin(r) || !fileExists(provisionedFile) { http.Error(w,"pedido rejeitado",http.StatusForbidden);return }
    var in struct { Mode string `json:"mode"`; Destination string `json:"destination"`; Code string `json:"code"`; Create bool `json:"create"` }
    if json.NewDecoder(http.MaxBytesReader(w,r.Body,2048)).Decode(&in)!=nil {http.Error(w,"pedido inválido",400);return}
    switch in.Mode {case "off","dmr2ysf","ysf2dmr","dmr2nxdn","ysf2nxdn","ysf2p25","direct-group":default:http.Error(w,"modo inválido",400);return}
    if !applyMu.TryLock(){http.Error(w,"outra alteração está em andamento",409);return};defer applyMu.Unlock()
    req:=map[string]any{"mode":in.Mode,"destination":in.Destination,"code":in.Code,"create":in.Create}
    res,err:=runPrivilegedRequest("2pny-mode-apply.service","/run/2pny/mode-request.json","/run/2pny/mode-result.json",req)
    if err!=nil{writeJSON(w,503,map[string]any{"ok":false,"error":"não foi possível aplicar o modo","result":res});return}
    w.Header().Set("Cache-Control","no-store");writeJSON(w,200,res)
}
func mode511Status(w http.ResponseWriter,r *http.Request){
    if r.Method!=http.MethodGet{http.Error(w,"método inválido",405);return}
    w.Header().Set("Cache-Control","no-store")
    writeJSON(w,200,map[string]any{"mode":readPublicJSON(dataDir+"/special-mode.json"),"direct":readPublicJSON("/run/2pny/direct-group-status.json")})
}
func mode511Destinations(w http.ResponseWriter,r *http.Request){
    if r.Method!=http.MethodGet{http.Error(w,"método inválido",405);return}
    proto:=r.URL.Query().Get("protocol");if proto!="YSF"&&proto!="NXDN"&&proto!="P25"{http.Error(w,"protocolo inválido",400);return}
    obj:=readPublicJSON(dataDir+"/hosts/"+proto+"Hosts.json")
    writeJSON(w,200,map[string]any{"destinations":obj["reflectors"]})
}
func init(){http.HandleFunc("/api/mode/settings",mode511Handler);http.HandleFunc("/api/mode/status",mode511Status);http.HandleFunc("/api/mode/destinations",mode511Destinations)}
func init(){http.HandleFunc("/panel-511.js",func(w http.ResponseWriter,r *http.Request){http.ServeFile(w,r,"/usr/share/2pny/panel-511.js")})}
