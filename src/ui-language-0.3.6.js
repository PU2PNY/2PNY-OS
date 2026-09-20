/* PU2PNY-OS 0.3.6 complete UI translation layer (PT/EN/ES). */
(()=>{
const D={
'Painel':['Dashboard','Panel'],'Painel principal':['Dashboard','Panel principal'],'Ao Vivo':['Live','En vivo'],'Ao vivo':['Live','En vivo'],
'Internet':['Internet','Internet'],'Hotspot':['Hotspot','Hotspot'],'Protocolos':['Protocols','Protocolos'],'Histórico':['History','Historial'],'Display':['Display','Pantalla'],'Sistema':['System','Sistema'],'Expert':['Expert','Experto'],
'APRS / D-PRS':['APRS / D-PRS','APRS / D-PRS'],'Claro':['Light','Claro'],'Escuro':['Dark','Oscuro'],'Básico':['Basic','Básico'],
'Atualizar':['Refresh','Actualizar'],'Atualizar agora':['Refresh now','Actualizar ahora'],'Atualizar visualização':['Refresh view','Actualizar vista'],
'Conexão ativa':['Active connection','Conexión activa'],'Interface':['Interface','Interfaz'],'SSID':['SSID','SSID'],'RSSI Wi‑Fi':['Wi-Fi RSSI','RSSI Wi-Fi'],'IP':['IP','IP'],
'Ethernet':['Ethernet','Ethernet'],'Velocidade':['Speed','Velocidad'],'Duplex':['Duplex','Dúplex'],'Erros / drops':['Errors / drops','Errores / pérdidas'],
'MTR resumido':['MTR summary','Resumen MTR'],'Destino':['Destination','Destino'],'Rota até o servidor':['Route to server','Ruta hasta el servidor'],
'Diagnóstico leve e cacheado no hotspot':['Lightweight diagnostics cached on the hotspot','Diagnóstico ligero almacenado en el hotspot'],
'Qualidade':['Quality','Calidad'],'Saída':['Outbound interface','Salida'],'Gateway / sua rede':['Gateway / your network','Gateway / su red'],'Destino final':['Final destination','Destino final'],'Saltos observados':['Observed hops','Saltos observados'],
'Endereço':['Address','Dirección'],'Latência':['Latency','Latencia'],'Estado':['State','Estado'],'Leitura':['Reading','Lectura'],
'DNS efetivo':['Effective DNS','DNS efectivo'],'Servidores recebidos/configurados na conexão atual.':['Servers effectively used by the current connection.','Servidores usados efectivamente por la conexión actual.'],
'Comparação de resposta':['Response comparison','Comparación de respuesta'],'Provedor':['Provider','Proveedor'],'Servidor':['Server','Servidor'],'Resposta':['Response','Respuesta'],
'Usar Cloudflare':['Use Cloudflare','Usar Cloudflare'],'Usar Google':['Use Google','Usar Google'],'Usar OpenDNS':['Use OpenDNS','Usar OpenDNS'],'Automático / roteador':['Automatic / router','Automático / router'],
'Rede Wi‑Fi 1 e Rede Wi‑Fi 2':['Wi-Fi Network 1 and Wi-Fi Network 2','Red Wi-Fi 1 y Red Wi-Fi 2'],'Rede Wi‑Fi 1':['Wi-Fi Network 1','Red Wi-Fi 1'],'Rede Wi‑Fi 2':['Wi-Fi Network 2','Red Wi-Fi 2'],
'Canal atual':['Current channel','Canal actual'],'Frequência':['Frequency','Frecuencia'],'Canais próximos':['Nearby channels','Canales cercanos'],'Buscar redes':['Scan networks','Buscar redes'],
'Adicionar/alterar Rede Wi‑Fi 2':['Add/change Wi-Fi Network 2','Agregar/cambiar Red Wi-Fi 2'],'Senha':['Password','Contraseña'],'Salvar Rede Wi‑Fi 2':['Save Wi-Fi Network 2','Guardar Red Wi-Fi 2'],'Trocar Rede Wi‑Fi 1 ↔ 2':['Switch Wi-Fi Network 1 ↔ 2','Cambiar Red Wi-Fi 1 ↔ 2'],
'Adicionar rede manualmente':['Add network manually','Agregar red manualmente'],'Nome da rede (SSID)':['Network name (SSID)','Nombre de red (SSID)'],
'Diagnóstico':['Diagnostics','Diagnóstico'],'Concluído.':['Completed.','Completado.'],'Executando':['Running','Ejecutando'],'Aguarde…':['Please wait…','Espere…'],'Fechar':['Close','Cerrar'],
'Melhor opção':['Best option','Mejor opción'],'Bom':['Good','Bueno'],'Ruim':['Poor','Malo'],'Péssimo':['Very poor','Pésimo'],
'Relógio':['Clock','Reloj'],'Hora local':['Local time','Hora local'],'Fuso horário':['Time zone','Zona horaria'],'Sincronizado NTP':['NTP synchronized','NTP sincronizado'],'Novo fuso horário':['New time zone','Nueva zona horaria'],'Aplicar fuso':['Apply time zone','Aplicar zona horaria'],
'Operacional':['Operational','Operativo'],'Ligado':['On','Encendido'],'Desligado':['Off','Apagado'],'Temperatura':['Temperature','Temperatura'],'Frequência CPU':['CPU frequency','Frecuencia CPU'],'Throttling':['Throttling','Limitación térmica'],
'Voz enviada ao rádio':['Voice sent to radio','Voz enviada al radio'],'Ativar avisos por voz':['Enable voice announcements','Activar avisos por voz'],'Informar horário de hora em hora':['Announce time hourly','Informar la hora cada hora'],'Idioma da fala':['Voice language','Idioma de voz'],'Salvar voz':['Save voice','Guardar voz'],
'Proteção de transmissão':['Transmit protection','Protección de transmisión'],'Manutenção':['Maintenance','Mantenimiento'],'Manutenção automática quando houver internet':['Automatic maintenance when internet is available','Mantenimiento automático cuando haya internet'],
'Última execução':['Last run','Última ejecución'],'Próxima elegível':['Next eligible','Próxima elegible'],'Executar agora':['Run now','Ejecutar ahora'],'Atualizações':['Updates','Actualizaciones'],'Verificar atualizações':['Check for updates','Buscar actualizaciones'],'Ver detalhes':['View details','Ver detalles'],
'Instalar atualização':['Install update','Instalar actualización'],'Guardar versão atual para rollback':['Keep current version for rollback','Guardar versión actual para rollback'],'Restaurar versão':['Restore version','Restaurar versión'],'Excluir backup':['Delete backup','Eliminar respaldo'],
'Energia':['Power','Energía'],'Reiniciar hotspot':['Restart hotspot','Reiniciar hotspot'],'Desligar completamente':['Power off','Apagar completamente'],
'Configuração':['Configuration','Configuración'],'Ativar APRS-IS':['Enable APRS-IS','Activar APRS-IS'],'Servidor APRS':['APRS server','Servidor APRS'],'Porta':['Port','Puerto'],'Intervalo beacon':['Beacon interval','Intervalo beacon'],'Latitude':['Latitude','Latitud'],'Longitude':['Longitude','Longitud'],'Comentário':['Comment','Comentario'],
'Atualizar servidores':['Update servers','Actualizar servidores'],'Salvar APRS':['Save APRS','Guardar APRS'],'Usar minha localização':['Use my location','Usar mi ubicación'],'Enviar mensagem':['Send message','Enviar mensaje'],'Indicativo destino':['Destination callsign','Indicativo destino'],'Mensagem':['Message','Mensaje'],'Enviar':['Send','Enviar'],
'Estado atual':['Current state','Estado actual'],'Conectado':['Connected','Conectado'],'Gateway ativo':['Gateway active','Gateway activo'],'Aguardando rede':['Waiting for network','Esperando red'],
'Aplicar mudança':['Apply change','Aplicar cambio'],'Atualizar lista pública':['Update public list','Actualizar lista pública'],'Módulo':['Module','Módulo'],'Avançado — endereço, porta e credenciais':['Advanced — address, port and credentials','Avanzado — dirección, puerto y credenciales'],
'Perfil do protocolo':['Protocol profile','Perfil del protocolo'],'Frequência do perfil':['Profile frequency','Frecuencia del perfil'],'Salvar perfil':['Save profile','Guardar perfil'],'Ativar perfil':['Activate profile','Activar perfil'],
'Identidade':['Identity','Identidad'],'Radio ID':['Radio ID','Radio ID'],'Modo':['Mode','Modo'],'Operação':['Operation','Operación'],'RF / MMDVM':['RF / MMDVM','RF / MMDVM'],'Protocolo / Rede':['Protocol / Network','Protocolo / Red'],'Rede local':['Local network','Red local'],
'Abrir Internet':['Open Internet','Abrir Internet'],'Abrir Protocolos':['Open Protocols','Abrir Protocolos'],'Editar RF':['Edit RF','Editar RF'],
'Estado Ao Vivo':['Live state','Estado en vivo'],'Origem':['Origin','Origen'],'Indicativo / ID':['Callsign / ID','Indicativo / ID'],'BER / RSSI':['BER / RSSI','BER / RSSI'],'Detalhes técnicos do estado':['Technical state details','Detalles técnicos del estado'],
'Rede / rota':['Network / route','Red / ruta'],'Hardware':['Hardware','Hardware'],'Configuração pública':['Public configuration','Configuración pública'],'Fotos QRZ':['QRZ photos','Fotos QRZ'],
'SSH seguro':['Secure SSH','SSH seguro'],'Habilitar SSH':['Enable SSH','Habilitar SSH'],'Desativar SSH':['Disable SSH','Desactivar SSH'],'Salvar':['Save','Guardar'],'Remover':['Remove','Eliminar'],
'Eventos':['Events','Eventos'],'RF → Internet':['RF → Internet','RF → Internet'],'Internet → RF':['Internet → RF','Internet → RF'],'Protocolo mais usado':['Most used protocol','Protocolo más usado'],'Destinos mais usados':['Most used destinations','Destinos más usados'],'Atividade 24h':['24h activity','Actividad 24h'],
'Indicativo':['Callsign','Indicativo'],'Nome':['Name','Nombre'],'Cidade':['City','Ciudad'],'País':['Country','País'],'Direção':['Direction','Dirección'],'Duração':['Duration','Duración'],'Horário':['Time','Hora'],'Protocolo':['Protocol','Protocolo'],
'Detalhes técnicos':['Technical details','Detalles técnicos'],'Redetectar hardware':['Redetect hardware','Redetectar hardware'],'Estado atual':['Current state','Estado actual'],'Tipo':['Type','Tipo'],'Integração':['Integration','Integración'],'Driver':['Driver','Controlador'],'Layout':['Layout','Diseño'],'Porta MMDVM':['MMDVM port','Puerto MMDVM'],'Aplicar Display':['Apply Display','Aplicar pantalla'],
'Preparando hardware':['Preparing hardware','Preparando hardware'],'Configuração básica':['Basic configuration','Configuración básica'],'Radio ID (ex.: 7240000)':['Radio ID (e.g. 7240000)','Radio ID (ej.: 7240000)'],'Indicativo (ex.: PU2ABC)':['Callsign (e.g. PU2ABC)','Indicativo (ej.: PU2ABC)'],
'Continuar':['Continue','Continuar'],'Voltar':['Back','Volver'],'Salvar e continuar':['Save and continue','Guardar y continuar'],'Bem-vindo / Welcome':['Welcome','Bienvenido']
};
let language=localStorage.getItem('pu2pny-language')||'pt', originals=new WeakMap();
function tx(text){
  let trimmed=String(text||'').trim();if(language==='pt'||!trimmed)return trimmed;
  if(D[trimmed])return D[trimmed][language==='en'?0:1];
  return trimmed;
}
function translateNode(node){
  if(!node||!node.parentElement||['SCRIPT','STYLE','CODE','PRE'].includes(node.parentElement.tagName))return;
  let text=node.textContent.trim(),base=originals.get(node);
  if(!base&&D[text]){base=text;originals.set(node,base)}
  if(base){let wanted=language==='pt'?base:D[base][language==='en'?0:1];if(text!==wanted)node.textContent=node.textContent.replace(text,wanted)}
}
function translate(){
  let walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),node;while(node=walker.nextNode())translateNode(node);
  document.querySelectorAll('input[placeholder],textarea[placeholder]').forEach(el=>{let p=el.getAttribute('data-pny-original-placeholder')||el.placeholder;if(!el.dataset.pnyOriginalPlaceholder)el.dataset.pnyOriginalPlaceholder=p;el.placeholder=language==='pt'?p:tx(p)});
  document.documentElement.lang=language==='pt'?'pt-BR':language;
}
function bind(){let selector=document.getElementById('language');if(selector){selector.value=language;selector.onchange=()=>{language=selector.value;localStorage.setItem('pu2pny-language',language);translate()}}}
bind();translate();
new MutationObserver(()=>{bind();translate()}).observe(document.body,{subtree:true,childList:true});
window.translateNavigation=translate;window.PNYT=tx;
})();