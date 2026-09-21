/* PU2PNY-OS 0.3.11 UI translation layer (PT/EN/ES): exact catalog + guarded phrase fallback. */
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
'Identificação do hotspot / rádio':['Hotspot / radio identification','Identificación del hotspot / radio'],
'Sem sufixo / compatibilidade':['No suffix / compatibility','Sin sufijo / compatibilidad'],
'Hotspot / Rádio':['Hotspot / Radio','Hotspot / Radio'],
'BrandMeister API Key (opcional)':['BrandMeister API Key (optional)','BrandMeister API Key (opcional)'],
'Salvar API Key':['Save API Key','Guardar API Key'],'Remover API Key':['Remove API Key','Eliminar API Key'],
'API Key configurada.':['API Key configured.','API Key configurada.'],'API Key não configurada.':['API Key not configured.','API Key no configurada.'],
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
'Continuar':['Continue','Continuar'],'Voltar':['Back','Volver'],'Salvar e continuar':['Save and continue','Guardar y continuar'],'Bem-vindo / Welcome':['Welcome','Bienvenido'],
'Hotspot / Protocolos':['Hotspot / Protocols','Hotspot / Protocolos'],
'Saúde da comunicação':['Communication health','Salud de la comunicación'],
'Sinal RF':['RF signal','Señal RF'],'Wi-Fi / Uplink':['Wi-Fi / Uplink','Wi-Fi / Enlace'],'Link ativo':['Link active','Enlace activo'],
'Aguardando RX do rádio':['Waiting for radio RX','Esperando RX de radio'],'RSSI indisponível':['RSSI unavailable','RSSI no disponible'],
'Configuração integrada ao Hotspot':['Configuration integrated into Hotspot','Configuración integrada al Hotspot'],
'Calibração RF / BER':['RF / BER calibration','Calibración RF / BER'],'Resumo operacional':['Operational summary','Resumen operativo'],
'Potência RF do MMDVM (RFLevel)':['MMDVM RF power (RFLevel)','Potencia RF del MMDVM (RFLevel)'],
'Aplicar e testar':['Apply and test','Aplicar y probar'],'Restaurar valor anterior':['Restore previous value','Restaurar valor anterior'],
'Este controle altera o nível de saída RF do modem. Não representa watts medidos.':['This control changes the modem RF output level. It does not represent measured watts.','Este control cambia el nivel de salida RF del módem. No representa vatios medidos.'],
'Chamada ponto a ponto':['Point-to-point call','Llamada punto a punto'],'Contatos pareados':['Paired contacts','Contactos emparejados'],
'Nenhum contato.':['No contacts.','Sin contactos.'],'Parear':['Pair','Emparejar'],'Chamar':['Call','Llamar'],'Encerrar':['Hang up','Finalizar'],
'Criptografia':['Encryption','Cifrado'],'Latência':['Latency','Latencia'],'Meu PU2PNY':['My PU2PNY','Mi PU2PNY'],
'Configuração do display':['Display configuration','Configuración de pantalla'],
'Usar Nextion pela MMDVM':['Use Nextion through MMDVM','Usar Nextion mediante MMDVM'],
'Aplicando...':['Applying...','Aplicando...'],'Display atualizado e confirmado.':['Display updated and confirmed.','Pantalla actualizada y confirmada.'],
'Fuso horário inválido':['Invalid time zone','Zona horaria inválida'],
'Não foi possível aplicar o fuso horário com segurança.':['Could not safely apply the time zone.','No fue posible aplicar la zona horaria de forma segura.'],
'Chave pública SSH inválida':['Invalid SSH public key','Clave pública SSH inválida'],
'Nenhum servidor no cache local':['No server in local cache','Ningún servidor en la caché local'],
'Carregando...':['Loading...','Cargando...'],'Verificando...':['Checking...','Verificando...'],
'Aguardando':['Waiting','Esperando'],'Indisponível':['Unavailable','No disponible'],
'Ativo':['Active','Activo'],'Configurado':['Configured','Configurado'],'Pronto':['Ready','Listo'],
'Erro':['Error','Error'],'Falha':['Failure','Fallo'],'Aplicando':['Applying','Aplicando'],
'Conectando':['Connecting','Conectando'],'Desconectado':['Disconnected','Desconectado'],
'Ótimo':['Excellent','Óptimo'],'Ótima':['Excellent','Óptima'],'Boa':['Good','Buena'],
'Offline':['Offline','Sin conexión'],'Sem resposta':['No response','Sin respuesta'],
'Trocar perfil rapidamente':['Quick profile switch','Cambio rápido de perfil'],
'Atualizando DNS...':['Updating DNS...','Actualizando DNS...'],
'DNS atualizado e confirmado.':['DNS updated and confirmed.','DNS actualizado y confirmado.'],
'Configuração do display':['Display configuration','Configuración de pantalla'],
'Operacional restaurado':['Operational restored','Operativo restaurado'],
'Rede atual em':['Current network on','Red actual en'],
'MMDVM detectada. O assistente avançará automaticamente em 5 segundos.':['MMDVM detected. The wizard will advance automatically in 5 seconds.','MMDVM detectada. El asistente avanzará automáticamente en 5 segundos.'],
'MMDVMHost não iniciou; a configuração anterior foi restaurada. O diagnóstico técnico foi salvo no Expert.':['MMDVMHost did not start; the previous configuration was restored. Technical diagnostics were saved in Expert.','MMDVMHost no inició; se restauró la configuración anterior. El diagnóstico técnico se guardó en Expert.'],
'O broker MQTT local não ficou pronto; a configuração anterior foi preservada.':['The local MQTT broker was not ready; the previous configuration was preserved.','El broker MQTT local no estuvo listo; se conservó la configuración anterior.'],
'A detecção de display ainda está usando a porta da MMDVM; tente novamente em alguns segundos.':['Display detection is still using the MMDVM port; try again in a few seconds.','La detección de pantalla aún está usando el puerto MMDVM; inténtelo de nuevo en unos segundos.'],
'MMDVM ainda não foi identificada; a configuração RF não será aplicada':['MMDVM has not been identified yet; RF configuration will not be applied','La MMDVM aún no fue identificada; la configuración RF no se aplicará']
};
let language=localStorage.getItem('pu2pny-language')||'pt', originals=new WeakMap();
const loose={
en:[
[/\bConfiguração\b/gi,'Configuration'],[/\bconfiguração\b/gi,'configuration'],[/\bconfigurar\b/gi,'configure'],[/\bSalvar\b/gi,'Save'],[/\bsalvar\b/gi,'save'],
[/\bAtualizar\b/gi,'Refresh'],[/\batualizar\b/gi,'refresh'],[/\bAplicar\b/gi,'Apply'],[/\baplicar\b/gi,'apply'],[/\bAlteração\b/gi,'Change'],[/\balteração\b/gi,'change'],
[/\bEstado\b/gi,'State'],[/\bestado\b/gi,'state'],[/\bRede\b/gi,'Network'],[/\brede\b/gi,'network'],[/\bServidor\b/gi,'Server'],[/\bservidor\b/gi,'server'],
[/\bIndicativo\b/gi,'Callsign'],[/\bNome\b/gi,'Name'],[/\bCidade\b/gi,'City'],[/\bPaís\b/gi,'Country'],[/\bHorário\b/gi,'Time'],[/\bDuração\b/gi,'Duration'],
[/\bAguardando\b/gi,'Waiting'],[/\bConectado\b/gi,'Connected'],[/\bDesconectado\b/gi,'Disconnected'],[/\bAtivo\b/gi,'Active'],[/\bInativo\b/gi,'Inactive'],
[/\bFalha\b/gi,'Failure'],[/\berro\b/gi,'error'],[/\bErro\b/gi,'Error'],[/\binválid[oa]\b/gi,'invalid'],[/\bindisponível\b/gi,'unavailable'],
[/\bnão foi possível\b/gi,'could not'],[/\bnão\b/gi,'not'],[/\bSim\b/g,'Yes'],[/\bNão\b/g,'No'],[/\bDetalhes\b/gi,'Details'],[/\bAjuda\b/gi,'Help'],
[/\bFrequência\b/gi,'Frequency'],[/\bPotência\b/gi,'Power'],[/\bSinal\b/gi,'Signal'],[/\bQualidade\b/gi,'Quality'],[/\bInternet\b/gi,'Internet'],
[/\bUsuário\b/gi,'User'],[/\bSenha\b/gi,'Password'],[/\bChave\b/gi,'Key'],[/\bMensagem\b/gi,'Message'],[/\bEnviar\b/gi,'Send'],
[/\bAbrir\b/gi,'Open'],[/\bFechar\b/gi,'Close'],[/\bVoltar\b/gi,'Back'],[/\bContinuar\b/gi,'Continue'],[/\bReiniciar\b/gi,'Restart'],
[/\bDesligar\b/gi,'Power off'],[/\bLigado\b/gi,'On'],[/\bDesligado\b/gi,'Off'],[/\bIdioma\b/gi,'Language'],[/\bSistema\b/gi,'System'],
[/\bHistórico\b/gi,'History'],[/\bProtocolos\b/gi,'Protocols'],[/\bProtocolo\b/gi,'Protocol'],[/\bAo Vivo\b/gi,'Live'],[/\bExibir\b/gi,'Show'],
[/\bOcultar\b/gi,'Hide'],[/\bDetectado\b/gi,'Detected'],[/\bDetectar\b/gi,'Detect'],[/\bTempo\b/gi,'Time'],[/\bLocal\b/gi,'Local'],[/\bCanal\b/gi,'Channel'],[/\bCanais\b/gi,'Channels'],[/\brede(s)?\b/gi,'network$1'],[/\bobservado(s)?\b/gi,'observed$1'],[/\bmostra(m)?\b/gi,'show$1'],[/\bconfirmado\b/gi,'confirmed']
],
es:[
[/\bConfiguração\b/gi,'Configuración'],[/\bconfiguração\b/gi,'configuración'],[/\bconfigurar\b/gi,'configurar'],[/\bSalvar\b/gi,'Guardar'],[/\bsalvar\b/gi,'guardar'],
[/\bAtualizar\b/gi,'Actualizar'],[/\batualizar\b/gi,'actualizar'],[/\bAplicar\b/gi,'Aplicar'],[/\baplicar\b/gi,'aplicar'],[/\bAlteração\b/gi,'Cambio'],[/\balteração\b/gi,'cambio'],
[/\bEstado\b/gi,'Estado'],[/\bestado\b/gi,'estado'],[/\bRede\b/gi,'Red'],[/\brede\b/gi,'red'],[/\bServidor\b/gi,'Servidor'],[/\bservidor\b/gi,'servidor'],
[/\bIndicativo\b/gi,'Indicativo'],[/\bNome\b/gi,'Nombre'],[/\bCidade\b/gi,'Ciudad'],[/\bPaís\b/gi,'País'],[/\bHorário\b/gi,'Hora'],[/\bDuração\b/gi,'Duración'],
[/\bAguardando\b/gi,'Esperando'],[/\bConectado\b/gi,'Conectado'],[/\bDesconectado\b/gi,'Desconectado'],[/\bAtivo\b/gi,'Activo'],[/\bInativo\b/gi,'Inactivo'],
[/\bFalha\b/gi,'Fallo'],[/\berro\b/gi,'error'],[/\bErro\b/gi,'Error'],[/\binválid[oa]\b/gi,'inválido'],[/\bindisponível\b/gi,'no disponible'],
[/\bnão foi possível\b/gi,'no fue posible'],[/\bnão\b/gi,'no'],[/\bSim\b/g,'Sí'],[/\bNão\b/g,'No'],[/\bDetalhes\b/gi,'Detalles'],[/\bAjuda\b/gi,'Ayuda'],
[/\bFrequência\b/gi,'Frecuencia'],[/\bPotência\b/gi,'Potencia'],[/\bSinal\b/gi,'Señal'],[/\bQualidade\b/gi,'Calidad'],[/\bUsuário\b/gi,'Usuario'],
[/\bSenha\b/gi,'Contraseña'],[/\bChave\b/gi,'Clave'],[/\bMensagem\b/gi,'Mensaje'],[/\bEnviar\b/gi,'Enviar'],[/\bAbrir\b/gi,'Abrir'],[/\bFechar\b/gi,'Cerrar'],
[/\bVoltar\b/gi,'Volver'],[/\bContinuar\b/gi,'Continuar'],[/\bReiniciar\b/gi,'Reiniciar'],[/\bDesligar\b/gi,'Apagar'],[/\bLigado\b/gi,'Encendido'],
[/\bDesligado\b/gi,'Apagado'],[/\bIdioma\b/gi,'Idioma'],[/\bHistórico\b/gi,'Historial'],[/\bProtocolos\b/gi,'Protocolos'],[/\bAo Vivo\b/gi,'En vivo'],[/\bCanal\b/gi,'Canal'],[/\bCanais\b/gi,'Canales'],[/\brede(s)?\b/gi,'red$1'],[/\bobservado(s)?\b/gi,'observado$1'],[/\bconfirmado\b/gi,'confirmado']
]};
const incomingPT=[
  [/^MMDVMHost failed with detected baud (\\d+); rolling back(?: RF configuration)?$/i,(m,b)=>'MMDVMHost não iniciou com o baud detectado '+b+'; a configuração anterior foi restaurada.'],
  [/^MMDVMHost failed; rolling back RF configuration$/i,'MMDVMHost não iniciou; a configuração anterior foi restaurada.'],
  [/^MMDVMHost did not stay active; rolling back(?: RF configuration)?$/i,'MMDVMHost não permaneceu ativo; a configuração anterior foi restaurada.'],
  [/^MMDVMHost could not be enabled$/i,'Não foi possível habilitar o MMDVMHost.'],
  [/^MMDVMHost not active yet$/i,'MMDVMHost ainda não está ativo.'],
  [/^MMDVM not confirmed$/i,'MMDVM não confirmada.'],
  [/^MMDVM has not been identified; refusing RF apply$/i,'MMDVM ainda não foi identificada; a configuração RF não será aplicada'],
  [/^MMDVM detection validation failed$/i,'Falha ao validar a detecção da MMDVM.'],
  [/^root required$/i,'Permissão administrativa interna necessária.'],
  [/^invalid numeric RF value$/i,'Valor numérico de RF inválido.'],
  [/^unsupported modem port$/i,'Porta do modem não suportada.'],
  [/^modem port does not exist: (.+)$/i,(m,p)=>'A porta do modem não existe: '+p],
  [/^invalid callsign$/i,'Indicativo inválido.'],
  [/^invalid DMR ID$/i,'DMR ID inválido.'],
  [/^unsupported or unknown detected MMDVM baud: (.+)$/i,(m,b)=>'Baud da MMDVM detectada não suportado ou desconhecido: '+b],
  [/^requested modem port does not match detected MMDVM: (.+)$/i,(m,p)=>'A porta solicitada não corresponde à MMDVM detectada: '+p],
  [/^RX frequency outside 100 MHz\.\.1 GHz hardware safety envelope$/i,'Frequência RX fora do limite de segurança do hardware (100 MHz..1 GHz).'],
  [/^TX frequency outside 100 MHz\.\.1 GHz hardware safety envelope$/i,'Frequência TX fora do limite de segurança do hardware (100 MHz..1 GHz).'],
  [/^RX offset outside \+\/-10 MHz$/i,'RX Offset fora do limite de ±10 MHz.'],
  [/^TX offset outside \+\/-10 MHz$/i,'TX Offset fora do limite de ±10 MHz.']
];
function normalizeIncoming(text){
  let out=String(text||'').trim();
  if(!out)return out;
  for(const pair of incomingPT){
    if(pair[0].test(out)){out=out.replace(pair[0],pair[1]);break}
  }
  return out;
}
function tx(text){
  let trimmed=normalizeIncoming(text);if(!trimmed)return trimmed;
  if(language==='pt')return trimmed;
  if(D[trimmed])return D[trimmed][language==='en'?0:1];
  let out=trimmed;for(const pair of loose[language]||[])out=out.replace(pair[0],pair[1]);
  return out;
}
function translateNode(node){
  if(!node||!node.parentElement||['SCRIPT','STYLE','CODE','PRE'].includes(node.parentElement.tagName))return;
  let text=node.textContent.trim();if(!text)return;
  let base=originals.get(node);
  // Preserve the original Portuguese text for every visible text node, not
  // only exact catalog hits. This makes the guarded phrase fallback work on
  // static and dynamically-created UI while still excluding logs/code/pre.
  if(!base){base=text;originals.set(node,base)}
  let wanted=language==='pt'?base:tx(base);
  if(text!==wanted)node.textContent=node.textContent.replace(text,wanted)
}
function translate(){
  let walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),node;while(node=walker.nextNode())translateNode(node);
  document.querySelectorAll('input[placeholder],textarea[placeholder]').forEach(el=>{let p=el.getAttribute('data-pny-original-placeholder')||el.placeholder;if(!el.dataset.pnyOriginalPlaceholder)el.dataset.pnyOriginalPlaceholder=p;el.placeholder=language==='pt'?p:tx(p)});
  document.querySelectorAll('[title],[aria-label]').forEach(el=>{for(const a of ['title','aria-label']){if(!el.hasAttribute(a))continue;let key='pnyOriginal'+a.replace('-','');let p=el.dataset[key]||el.getAttribute(a);if(!el.dataset[key])el.dataset[key]=p;el.setAttribute(a,language==='pt'?p:tx(p))}});
  document.documentElement.lang=language==='pt'?'pt-BR':language;
}
function bind(){let selector=document.getElementById('language');if(selector){selector.value=language;selector.onchange=()=>{language=selector.value;localStorage.setItem('pu2pny-language',language);translate()}}}
bind();translate();
let translating=false;new MutationObserver(()=>{if(translating)return;translating=true;queueMicrotask(()=>{try{bind();translate()}finally{translating=false}})}).observe(document.body,{subtree:true,childList:true,characterData:true});
window.translateNavigation=translate;window.PNYT=tx;
})();