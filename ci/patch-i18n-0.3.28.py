#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"rootfs-overlay/usr/share/2pny/ui-language.js"
s=p.read_text()
anchor="let language=localStorage.getItem('pu2pny-language')||'pt', originals=new WeakMap();"
add="""Object.assign(D,{
"Ativar perfil selecionado":["Activate selected profile","Activar perfil seleccionado"],
"Ativando perfil…":["Activating profile…","Activando perfil…"],
"Perfil ativado. Aguardando conexão com o servidor.":["Profile activated. Waiting for server connection.","Perfil activado. Esperando conexión con el servidor."],
"Não foi possível ativar o perfil selecionado.":["The selected profile could not be activated.","No se pudo activar el perfil seleccionado."],
"Perfil selecionado não está ativo.":["The selected profile is not active.","El perfil seleccionado no está activo."],
"Não conectado ao servidor.":["Not connected to the server.","No conectado al servidor."]
});
"""
if add not in s:
    if anchor not in s: raise SystemExit("0.3.28 i18n anchor missing")
    s=s.replace(anchor,add+anchor,1)
p.write_text(s)
print("I18N_0328_OK")
