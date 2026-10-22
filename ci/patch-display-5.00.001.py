#!/usr/bin/env python3
"""Surgical display fixes for the 5.00.000 published-baseline overlay.

Modes: --go <input.go> <output.go> or --display-apply <input.py> <output.py>.
The source of RF/modem/gateway handling is never changed by this patch.
"""
from pathlib import Path
import argparse
import ast

def replace_once(text, old, new):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"display patch anchor mismatch: {old[:70]!r} count={count}")
    return text.replace(old, new, 1)

def patch_go(text):
    # Previously, Go POST always coerced G4KLX (layout 0) to ON7LDS L2 (2).
    if 'if in.Layout != 2 && in.Layout != 3 { in.Layout = 2 }' in text:
        text = replace_once(text,
            'if in.Layout != 2 && in.Layout != 3 { in.Layout = 2 }',
            'if in.Layout != 0 && in.Layout != 2 && in.Layout != 3 { in.Layout = 2 }')
    elif 'if in.Layout != 0 && in.Layout != 2 { in.Layout = 0 }' in text:
        # The 0.3.31.119 patch chain already fixed G4KLX layout 0.
        pass
    else:
        raise SystemExit('unrecognized display layout policy; refuse speculative change')
    # Do not silently swallow persistent display override write failures.
    text = replace_once(text,
        '_ = os.WriteFile(displayOverrideFile, raw, 0600)\n\t\t\tapplyDisplayOverrideToProbe()',
        'if err := os.WriteFile(displayOverrideFile, raw, 0600); err != nil {\n'
        '\t\t\t\twriteJSON(w, http.StatusInternalServerError, map[string]any{"ok":false,"error":"falha ao salvar display"})\n'
        '\t\t\t\treturn\n\t\t\t}\n\t\t\tapplyDisplayOverrideToProbe()')

    # Access-policy changes are independent of existing RF/DMR protocol paths.
    handler = """
func rfAccessPolicyHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method == http.MethodGet {
        data := readPublicJSON("/var/lib/2pny/access/policy.json")
        if len(data) == 0 { data = map[string]any{"mode":"legacy_unchanged","verified":false} }
        writeJSON(w,http.StatusOK,map[string]any{"ok":true,"policy":data})
        return
    }
    if r.Method != http.MethodPost {
        http.Error(w,"GET or POST required",http.StatusMethodNotAllowed)
        return
    }
    if !sameOrigin(r) || !fileExists(provisionedFile) {
        http.Error(w,"request rejected",http.StatusForbidden)
        return
    }
    var request struct {
        Mode string _BT_json:"mode"_BT_
        Confirmation string _BT_json:"confirmation"_BT_
        Allowed []struct {
            Callsign string _BT_json:"callsign"_BT_
            DMRID string _BT_json:"dmr_id"_BT_
        } _BT_json:"allowed"_BT_
    }
    if err := json.NewDecoder(http.MaxBytesReader(w,r.Body,32768)).Decode(&request); err != nil {
        writeJSON(w,http.StatusBadRequest,map[string]any{"ok":false,"error":"invalid_request"})
        return
    }
    if request.Mode != "private" && request.Mode != "semi_public" && request.Mode != "public" {
        writeJSON(w,http.StatusBadRequest,map[string]any{"ok":false,"error":"invalid_access_mode"})
        return
    }
    if request.Mode == "public" && request.Confirmation != "ABRIR RF PUBLICO" {
        writeJSON(w,http.StatusBadRequest,map[string]any{"ok":false,"error":"public_requires_explicit_confirmation"})
        return
    }
    if len(request.Allowed)>200 {
        writeJSON(w,http.StatusBadRequest,map[string]any{"ok":false,"error":"too_many_entries"})
        return
    }
    list := make([]map[string]string,0,len(request.Allowed))
    for _,item := range request.Allowed {
        list=append(list,map[string]string{"callsign":item.Callsign,"dmr_id":item.DMRID})
    }
    payload := map[string]any{"mode":request.Mode,"confirmation":request.Confirmation,"allowed":list}
    res,err := runPrivilegedRequest("2pny-rf-access.service",
        "/run/2pny/access-request.json","/run/2pny/access-result.json",payload)
    if err != nil {
        writeJSON(w,http.StatusConflict,map[string]any{"ok":false,"error":err.Error(),"result":res})
        return
    }
    writeJSON(w,http.StatusOK,res)
}

"""
    handler = handler.replace("_BT_", chr(96))
    # Do not present a 5.00.000 backend as the newer 5.00.001 image.
    if 'appVersion            = "5.00.000"' in text:
        text = replace_once(text, 'appVersion            = "5.00.000"',
                            'appVersion            = "5.00.001"')
    text = replace_once(text, "func main() {", handler + "func main() {")
    text = replace_once(text,
        '\thttp.HandleFunc("/api/display/override", displayOverrideHandler)',
        '\thttp.HandleFunc("/api/display/override", displayOverrideHandler)\n'
        '\thttp.HandleFunc("/api/rf/access", rfAccessPolicyHandler)')
    text = replace_once(text,
        '\thttp.HandleFunc("/display", pageHandler(displayFile))',
        '\thttp.HandleFunc("/display", pageHandler(displayFile))\n'
        '\thttp.HandleFunc("/rf-access", pageHandler("/usr/share/2pny/rf-access.html"))')
    return text

def patch_apply(text):
    # Important: Python's "0 or 9" discards the legitimate G4KLX layout 0.
    text = replace_once(text,
        'requested=int(ov.get("layout") or 9)',
        'requested=int(ov.get("layout",9))')
    # Ensure the advanced NextionDriver cannot fight the native or PU2PNY writer.
    text = replace_once(text,
        'LEGACY="2pny-display.service"',
        'LEGACY="2pny-display.service"\nDRIVER="2pny-nextiondriver.service"')
    text = text.replace('ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)',
                        'ctl("disable","--now",LEGACY);ctl("disable","--now",CORE);ctl("disable","--now",DRIVER)')
    text = replace_once(text,
        'ctl("disable","--now",LEGACY)\nif kind=="nextion_mmdvm":',
        'ctl("disable","--now",LEGACY)\nctl("disable","--now",DRIVER)\nif kind=="nextion_mmdvm":')
    # Never say physical Nextion is active just because the RF engine is active.
    text = replace_once(text,
        '"state":"active" if active(MMDVM) else "configured","active":active(MMDVM),',
        '"state":"active" if d.get("physical_confirmed") is True and active(MMDVM) else "tx_only_unconfirmed",'
        '"active":d.get("physical_confirmed") is True and active(MMDVM),')
    ast.parse(text)
    return text

def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("go", "display-apply"))
    p.add_argument("source", type=Path)
    p.add_argument("destination", type=Path)
    a = p.parse_args()
    before = a.source.read_text()
    after = patch_go(before) if a.mode == "go" else patch_apply(before)
    if after == before:
        raise SystemExit("display patch is a no-op")
    a.destination.write_text(after)
    print("DISPLAY_500001_SURGICAL_PATCH_OK")

if __name__ == "__main__":
    main()
