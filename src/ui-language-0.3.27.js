/* PU2PNY-OS 0.3.27 UI translation layer (PT/EN/ES): exact catalog + strict no-mixed-language fallback. */
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
'Ajuste automático':['Automatic setup','Ajuste automático'],'Horário de verão manual':['Manual daylight saving','Horario de verano manual'],
'Rede de backup':['Backup network','Red de respaldo'],'Escolha automática':['Automatic selection','Selección automática'],
'Saída para tela ativa · retorno COMOK não confirmado':['Display output active · COMOK return not confirmed','Salida a pantalla activa · retorno COMOK no confirmado'],
'Talkgroup conectado':['Connected talkgroup','Talkgroup conectado'],
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
Object.assign(D,{"Conectando o PU2PNY à sua rede":["Connecting PU2PNY to your network","Conectando PU2PNY a su red"],"A rede será validada antes de encerrar o AP. Depois da associação e do endereço IP, esta tela procurará o PU2PNY automaticamente na nova rede.":["The network will be validated before the AP is closed. After association and IP assignment, this screen will automatically find PU2PNY on the new network.","La red se validará antes de cerrar el AP. Después de la asociación y la asignación de IP, esta pantalla buscará automáticamente PU2PNY en la nueva red."],"Não desligue o hotspot e não atualize a página.":["Do not power off the hotspot or refresh the page.","No apague el hotspot ni actualice la página."],"Assim que o PU2PNY voltar na nova rede, esta página abrirá Hardware automaticamente.":["As soon as PU2PNY returns on the new network, this page will open Hardware automatically.","En cuanto PU2PNY vuelva a aparecer en la nueva red, esta página abrirá Hardware automáticamente."],"Sistema Operacional de Rádio Digital":["Digital Radio Operating System","Sistema Operativo de Radio Digital"],"Conecte à internet":["Connect to the internet","Conéctese a Internet"],"Detectar e preparar":["Detect and prepare","Detectar y preparar"],"Ajustes essenciais":["Essential settings","Ajustes esenciales"],"Conclusão":["Completion","Finalización"],"Pronto para usar":["Ready to use","Listo para usar"],"Precisa de ajuda?":["Need help?","¿Necesita ayuda?"],"O assistente mostra somente o necessário. Ajustes avançados ficam para depois.":["The wizard shows only what is necessary. Advanced settings are available later.","El asistente muestra solo lo necesario. Los ajustes avanzados quedan para después."],"Primeiro acesso — Internet":["First access — Internet","Primer acceso — Internet"],"A internet é opcional para a configuração local do PU2PNY-OS. Conecte agora se quiser atualizar diretórios e componentes.":["Internet is optional for local PU2PNY-OS setup. Connect now if you want to update directories and components.","Internet es opcional para la configuración local de PU2PNY-OS. Conéctese ahora si desea actualizar directorios y componentes."],"Conectar à internet":["Connect to the internet","Conectarse a Internet"],"Use uma rede Wi‑Fi existente ou um cabo Ethernet. O acesso local continua disponível durante a configuração.":["Use an existing Wi-Fi network or an Ethernet cable. Local access remains available during setup.","Use una red Wi-Fi existente o un cable Ethernet. El acceso local permanece disponible durante la configuración."],"A internet é usada somente para preparar pacotes oficiais, firmware e componentes necessários. Depois disso a detecção do MMDVM é automática.":["Internet is used only to prepare official packages, firmware and required components. After that, MMDVM detection is automatic.","Internet se usa solo para preparar paquetes oficiales, firmware y componentes necesarios. Después, la detección de MMDVM es automática."],"País / região do Wi‑Fi":["Wi-Fi country / region","País / región Wi-Fi"],"Define os canais permitidos antes da busca. Escolher o país correto ajuda a encontrar todas as redes próximas.":["Defines allowed channels before scanning. Choosing the correct country helps find all nearby networks.","Define los canales permitidos antes de la búsqueda. Elegir el país correcto ayuda a encontrar todas las redes cercanas."],"Rede Wi‑Fi encontrada":["Wi-Fi network found","Red Wi-Fi encontrada"],"Buscando redes...":["Scanning networks...","Buscando redes..."],"A busca é feita automaticamente. Selecione a rede e informe somente a senha.":["Scanning is automatic. Select the network and enter only the password.","La búsqueda es automática. Seleccione la red e introduzca solo la contraseña."],"Outra rede / rede oculta":["Other network / hidden network","Otra red / red oculta"],"Mostrar":["Show","Mostrar"],"Manter AP ativo usando a segunda interface Wi‑Fi":["Keep AP active using the second Wi-Fi interface","Mantener el AP activo usando la segunda interfaz Wi-Fi"],"Conectar Wi‑Fi":["Connect Wi-Fi","Conectar Wi-Fi"],"Cabo de rede":["Ethernet cable","Cable de red"],"Primeiro tentamos DHCP. Isso funciona em roteadores e também com Compartilhamento de Internet do computador.":["DHCP is tried first. This works with routers and with computer Internet Sharing.","Primero se intenta DHCP. Funciona con routers y también con el uso compartido de Internet del ordenador."],"Reverificar cabo e internet":["Recheck cable and Internet","Volver a comprobar cable e Internet"],"Preparação automática quando houver internet":["Automatic preparation when Internet is available","Preparación automática cuando haya Internet"],"Atualiza os índices e instala somente drivers/firmware oficiais que estiverem faltando. Não executa upgrade completo do Debian.":["Updates indexes and installs only missing official drivers/firmware. It does not perform a full Debian upgrade.","Actualiza índices e instala solo los controladores/firmware oficiales que falten. No realiza una actualización completa de Debian."],"Continuar sem internet →":["Continue without Internet →","Continuar sin Internet →"],"Buscando drivers e detectando hardware":["Preparing drivers and detecting hardware","Preparando controladores y detectando hardware"],"O PU2PNY-OS prepara firmware oficial e verifica Raspberry Pi, MMDVM e display sem expor detalhes técnicos desnecessários.":["PU2PNY-OS prepares official firmware and checks Raspberry Pi, MMDVM and display without exposing unnecessary technical details.","PU2PNY-OS prepara firmware oficial y comprueba Raspberry Pi, MMDVM y pantalla sin exponer detalles técnicos innecesarios."],"Internet conectada":["Internet connected","Internet conectada"],"Drivers básicos":["Basic drivers","Controladores básicos"],"Preparando firmware e módulos oficiais.":["Preparing official firmware and modules.","Preparando firmware y módulos oficiales."],"Identificação do modem pelo protocolo oficial.":["Modem identification using the official protocol.","Identificación del módem mediante el protocolo oficial."],"Display / Nextion":["Display / Nextion","Pantalla / Nextion"],"Verificação opcional.":["Optional verification.","Verificación opcional."],"Pronto para configuração":["Ready for setup","Listo para configurar"],"Hardware essencial validado.":["Essential hardware validated.","Hardware esencial validado."],"Resumo detectado":["Detected summary","Resumen detectado"],"Somente o que importa para continuar.":["Only what is needed to continue.","Solo lo necesario para continuar."],"Plataforma":["Platform","Plataforma"],"Modem":["Modem","Módem"],"Status geral":["Overall status","Estado general"],"Preparando...":["Preparing...","Preparando..."],"Layout/HMI existente na Nextion":["Existing Nextion layout/HMI","Diseño/HMI existente en la Nextion"],"O PU2PNY-OS não grava o HMI/TFT. Esta opção apenas escolhe os comandos compatíveis com a tela que já está instalada.":["PU2PNY-OS does not write the HMI/TFT. This option only selects commands compatible with the display already installed.","PU2PNY-OS no graba el HMI/TFT. Esta opción solo selecciona comandos compatibles con la pantalla ya instalada."],"Depois da configuração RF, o MMDVM-Display assume a tela e substitui a barra de progresso pelo estado real do rádio.":["After RF setup, MMDVM-Display takes over the screen and replaces the progress bar with the actual radio state.","Después de la configuración RF, MMDVM-Display toma el control de la pantalla y sustituye la barra de progreso por el estado real de la radio."],"Detectar novamente":["Detect again","Detectar de nuevo"],"Ir para configuração básica →":["Go to basic setup →","Ir a configuración básica →"],"Somente os dados necessários para colocar o rádio em funcionamento. O PU2PNY-OS usa a porta e a velocidade realmente detectadas no MMDVM.":["Only the data required to bring the radio online. PU2PNY-OS uses the port and speed actually detected on the MMDVM.","Solo los datos necesarios para poner la radio en funcionamiento. PU2PNY-OS usa el puerto y la velocidad realmente detectados en la MMDVM."],"Modo de uso":["Operating mode","Modo de uso"],"Uso pessoal":["Personal use","Uso personal"],"Operação duplex":["Duplex operation","Operación dúplex"],"Frequência do hotspot (MHz)":["Hotspot frequency (MHz)","Frecuencia del hotspot (MHz)"],"Ajustes avançados de RF":["Advanced RF settings","Ajustes avanzados de RF"],"Use somente para calibração do modem.":["Use only for modem calibration.","Use solo para calibración del módem."],"Protocolo principal":["Primary protocol","Protocolo principal"],"Rede / servidor":["Network / server","Red / servidor"],"Escolha o master/rede. A lista pública é atualizada automaticamente e o último cache válido continua disponível offline.":["Choose the master/network. The public list is updated automatically and the last valid cache remains available offline.","Elija el master/red. La lista pública se actualiza automáticamente y la última caché válida sigue disponible sin conexión."],"Rede / sistema":["Network / system","Red / sistema"],"Atualizar lista pública":["Update public list","Actualizar lista pública"],"Servidor / refletor":["Server / reflector","Servidor / reflector"],"Carregando servidores...":["Loading servers...","Cargando servidores..."],"Aguardando lista pública.":["Waiting for public list.","Esperando la lista pública."],"Avançado — IP, porta e servidor personalizado":["Advanced — IP, port and custom server","Avanzado — IP, puerto y servidor personalizado"],"Endereço / hostname":["Address / hostname","Dirección / hostname"],"Normalmente não é necessário alterar. Use somente para servidor personalizado ou orientação técnica.":["Normally no change is needed. Use only for a custom server or technical guidance.","Normalmente no es necesario cambiarlo. Úselo solo para un servidor personalizado o por indicación técnica."],"Escolha o servidor para ver os campos corretos desta rede.":["Choose the server to see the correct fields for this network.","Elija el servidor para ver los campos correctos de esta red."],"Senha do master":["Master password","Contraseña del master"],"Código de cor":["Color Code","Código de color"],"O rádio precisa usar o mesmo Color Code.":["The radio must use the same Color Code.","La radio debe usar el mismo Color Code."],"Slot de tempo":["Time Slot","Slot de tiempo"],"Hotspot simplex usa um slot; em repetidora duplex é possível usar os dois.":["A simplex hotspot uses one slot; a duplex repeater can use both.","Un hotspot simplex usa un slot; en un repetidor dúplex se pueden usar ambos."],"Opções do master (opcional)":["Master options (optional)","Opciones del master (opcional)"],"Escolha A–Z. Quando o catálogo informar módulos específicos, o PU2PNY prioriza somente os disponíveis.":["Choose A–Z. When the catalog lists specific modules, PU2PNY prioritizes only those available.","Elija A–Z. Cuando el catálogo indique módulos específicos, PU2PNY prioriza solo los disponibles."],"Opera no protocolo selecionado":["Operates on the selected protocol","Opera en el protocolo seleccionado"],"Planejado — ainda não habilitado nesta Alpha":["Planned — not enabled in this Alpha yet","Planificado — todavía no habilitado en esta Alpha"],"Ajustes avançados, redes, salas e parâmetros finos ficam fora do primeiro acesso e podem ser configurados depois.":["Advanced settings, networks, rooms and fine parameters are outside first access and can be configured later.","Los ajustes avanzados, redes, salas y parámetros finos quedan fuera del primer acceso y se pueden configurar después."],"Configuração básica concluída":["Basic setup completed","Configuración básica completada"],"Configuração básica concluída.":["Basic setup completed.","Configuración básica completada."],"O endereço principal é":["The main address is","La dirección principal es"],"Depois de concluído, esse endereço abre diretamente o painel operacional.":["After completion, this address opens the operational dashboard directly.","Después de finalizar, esta dirección abre directamente el panel operativo."],"Alterar rede":["Change network","Cambiar red"],"Rever hardware":["Review hardware","Revisar hardware"],"Editar rádio":["Edit radio","Editar radio"],"Abrir painel principal →":["Open main dashboard →","Abrir panel principal →"],"A MMDVM ainda está sendo verificada; aguarde alguns segundos e tente novamente.":["The MMDVM is still being checked; wait a few seconds and try again.","La MMDVM aún se está verificando; espere unos segundos e inténtelo de nuevo."],"A conexão local mudou durante o início da detecção. Aguardando o PU2PNY responder...":["The local connection changed while detection was starting. Waiting for PU2PNY to respond...","La conexión local cambió al iniciar la detección. Esperando la respuesta de PU2PNY..."],"A detecção demorou mais que o esperado. Use Detectar novamente.":["Detection took longer than expected. Use Detect again.","La detección tardó más de lo esperado. Use Detectar de nuevo."],"Reconectando ao painel enquanto a detecção continua...":["Reconnecting to the dashboard while detection continues...","Reconectando al panel mientras continúa la detección..."],"Validando configuração antes de alterar o rádio…":["Validating configuration before changing the radio…","Validando la configuración antes de cambiar la radio…"],"Configuração aceita. Aplicando RF, MMDVMHost e gateway com rollback…":["Configuration accepted. Applying RF, MMDVMHost and gateway with rollback…","Configuración aceptada. Aplicando RF, MMDVMHost y gateway con rollback…"],"Aguardando confirmação dos serviços…":["Waiting for service confirmation…","Esperando la confirmación de los servicios…"],"A validação demorou mais que o esperado.":["Validation took longer than expected.","La validación tardó más de lo esperado."],"Não foi possível aplicar":["Could not apply","No fue posible aplicar"],"Não foi possível concluir.":["Could not complete.","No fue posible completar."],"Selecione uma rede Wi‑Fi.":["Select a Wi-Fi network.","Seleccione una red Wi-Fi."],"Falha na detecção.":["Detection failed.","Falló la detección."],"Pronto para continuar":["Ready to continue","Listo para continuar"],"MMDVM identificado":["MMDVM identified","MMDVM identificada"],"MMDVM não confirmado":["MMDVM not confirmed","MMDVM no confirmada"],"Nenhum display confirmado":["No display confirmed","Ninguna pantalla confirmada"],"Configuração automática":["Automatic configuration","Configuración automática"],"Não detectado":["Not detected","No detectado"],"Não confirmado":["Not confirmed","No confirmado"]});
Object.assign(D,{
'ID DMR':['DMR ID','ID DMR'],
'Tela':['Display','Pantalla'],
'Tela / Nextion':['Display / Nextion','Pantalla / Nextion'],
'Disposição/HMI existente na Nextion':['Existing Nextion layout/HMI','Disposición/HMI existente en la Nextion'],
'Senha do servidor':['Server password','Contraseña del servidor'],
'Senha de segurança do hotspot':['Hotspot Security password','Contraseña de seguridad del hotspot'],
'Chave de segurança TGIF':['TGIF Security Key','Clave de seguridad TGIF'],
'Chave de autenticação DAPNET':['DAPNET authentication key','Clave de autenticación DAPNET'],
'Obrigatória e diferente da senha da conta.':['Required and different from the account password.','Obligatoria y diferente de la contraseña de la cuenta.'],
'Use a chave de autenticação fornecida pelo DAPNET para seu indicativo.':['Use the authentication key supplied by DAPNET for your callsign.','Use la clave de autenticación proporcionada por DAPNET para su indicativo.'],
'Cole a chave de segurança gerada na sua conta TGIF. Se deixar vazio, será usado o modo legado quando disponível.':['Paste the security key generated in your TGIF account. If left blank, legacy mode will be used when available.','Pegue la clave de seguridad generada en su cuenta TGIF. Si se deja en blanco, se usará el modo heredado cuando esté disponible.'],
'A senha padrão do XLX normalmente é passw0rd.':['The default XLX password is normally passw0rd.','La contraseña predeterminada de XLX normalmente es passw0rd.'],
'Escolha o servidor/rede. A lista pública é atualizada automaticamente e o último cache válido continua disponível sem internet.':['Choose the server/network. The public list is updated automatically and the last valid cache remains available offline.','Elija el servidor/red. La lista pública se actualiza automáticamente y la última caché válida sigue disponible sin Internet.'],
'Opções do servidor (opcional)':['Server options (optional)','Opciones del servidor (opcional)'],
'Somente quando o servidor exigir opções específicas':['Only when the server requires specific options','Solo cuando el servidor requiera opciones específicas'],
'O rádio precisa usar o mesmo código de cor.':['The radio must use the same Color Code.','La radio debe usar el mismo código de color.'],
'A MMDVM foi detectada, mas o MMDVMHost não conseguiu assumir a porta serial no teste básico. A configuração anterior foi restaurada e o diagnóstico foi salvo no Expert.':['The MMDVM was detected, but MMDVMHost could not take ownership of the serial port during the basic test. The previous configuration was restored and diagnostics were saved in Expert.','La MMDVM fue detectada, pero MMDVMHost no pudo asumir el puerto serie durante la prueba básica. Se restauró la configuración anterior y el diagnóstico se guardó en Expert.'],
'A MMDVM passou no teste básico, mas o broker MQTT local não ficou pronto. A configuração anterior foi restaurada.':['The MMDVM passed the basic test, but the local MQTT broker was not ready. The previous configuration was restored.','La MMDVM superó la prueba básica, pero el broker MQTT local no estuvo listo. Se restauró la configuración anterior.'],
'A MMDVM passou no teste básico, mas o MMDVMHost não permaneceu ativo após habilitar MQTT. A configuração anterior foi restaurada e o diagnóstico foi salvo no Expert.':['The MMDVM passed the basic test, but MMDVMHost did not remain active after MQTT was enabled. The previous configuration was restored and diagnostics were saved in Expert.','La MMDVM superó la prueba básica, pero MMDVMHost no permaneció activo después de habilitar MQTT. Se restauró la configuración anterior y el diagnóstico se guardó en Expert.'],
'TGIF Security Key contém caractere não suportado':['TGIF Security Key contains an unsupported character','La clave de seguridad TGIF contiene un carácter no compatible']
});
Object.assign(D,{
'A MMDVM passou no teste básico, mas o MQTT local não ficou pronto após as tentativas automáticas. A configuração anterior foi restaurada. O diagnóstico foi salvo no Expert.':['The MMDVM passed the basic test, but local MQTT was not ready after the automatic attempts. The previous configuration was restored. Diagnostics were saved in Expert.','La MMDVM superó la prueba básica, pero MQTT local no quedó listo después de los intentos automáticos. Se restauró la configuración anterior. El diagnóstico se guardó en Expert.'],
'A MMDVM passou no teste básico, mas o verificador MQTT local não está disponível. A configuração anterior foi restaurada.':['The MMDVM passed the basic test, but the local MQTT checker is unavailable. The previous configuration was restored.','La MMDVM superó la prueba básica, pero el verificador MQTT local no está disponible. Se restauró la configuración anterior.'],
'A última tentativa não foi concluída. Revise a configuração e tente novamente.':['The last attempt did not complete. Review the configuration and try again.','El último intento no se completó. Revise la configuración e inténtelo de nuevo.'],
'MQTT local não ficou pronto.':['Local MQTT was not ready.','MQTT local no quedó listo.']
});
Object.assign(D,{
"Relógio":["Clock","Reloj"],
"O PU2PNY detecta automaticamente o fuso IANA do navegador. Se você escolher um fuso manualmente, essa escolha passa a ter prioridade e permanece após reiniciar.":["PU2PNY automatically detects the browser IANA time zone. If you choose a time zone manually, that choice takes priority and persists after restart.","PU2PNY detecta automáticamente la zona horaria IANA del navegador. Si elige una zona manualmente, esa elección tiene prioridad y persiste después de reiniciar."],
"Detectar região e sincronizar":["Detect region and synchronize","Detectar región y sincronizar"],
"Fuso horário manual":["Manual time zone","Zona horaria manual"],
"Carregando fusos…":["Loading time zones…","Cargando zonas horarias…"],
"Aplicar fuso manual":["Apply manual time zone","Aplicar zona horaria manual"],
"Data e hora manual":["Manual date and time","Fecha y hora manual"],
"Aplicar data/hora manual":["Apply manual date/time","Aplicar fecha/hora manual"],
"Ajustar data/hora manualmente desativa o NTP. Use “Detectar região e sincronizar” para voltar ao relógio automático.":["Setting date/time manually disables NTP. Use “Detect region and synchronize” to return to the automatic clock.","Ajustar fecha/hora manualmente desactiva NTP. Use “Detectar región y sincronizar” para volver al reloj automático."],
"O ajuste de verão altera somente a apresentação; UTC, logs e protocolos permanecem íntegros.":["The daylight-saving adjustment changes only the presentation; UTC, logs and protocols remain intact.","El ajuste de horario de verano cambia solo la presentación; UTC, registros y protocolos permanecen íntegros."],
"Manual":["Manual","Manual"],
"Automática · navegador/rede":["Automatic · browser/network","Automática · navegador/red"],
"Não foi possível carregar os fusos horários.":["Could not load the time zones.","No fue posible cargar las zonas horarias."],
"Fuso horário aplicado:":["Time zone applied:","Zona horaria aplicada:"],
"Fuso confirmado pelo sistema.":["Time zone confirmed by the system.","Zona horaria confirmada por el sistema."],
"Informe a data e a hora.":["Enter the date and time.","Introduzca la fecha y la hora."],
"Ajustando data e hora":["Setting date and time","Ajustando fecha y hora"],
"Desativando NTP e confirmando o horário manual…":["Disabling NTP and confirming the manual time…","Desactivando NTP y confirmando la hora manual…"],
"Data e hora manual aplicadas. NTP desativado até a próxima sincronização automática.":["Manual date and time applied. NTP is disabled until the next automatic synchronization.","Fecha y hora manual aplicadas. NTP está desactivado hasta la próxima sincronización automática."],
"Horário manual confirmado.":["Manual time confirmed.","Hora manual confirmada."],
"PU2PNY Direct":["PU2PNY Direct","PU2PNY Direct"],
"QSO ponto a ponto com fallback criptografado quando NAT/CGNAT impedir o caminho direto.":["Point-to-point QSO with encrypted fallback when NAT/CGNAT blocks the direct path.","QSO punto a punto con respaldo cifrado cuando NAT/CGNAT impide la ruta directa."],
"Sessão ponta a ponta; o relay transporta somente pacotes já criptografados.":["End-to-end session; the relay carries only already-encrypted packets.","Sesión de extremo a extremo; el relay transporta solo paquetes ya cifrados."],
"Chamada recebida":["Incoming call","Llamada entrante"],
"Aguardando aceitação pelo rádio":["Waiting for radio acceptance","Esperando aceptación por radio"],
"A chamada recebida não altera seu TG, refletor ou gateway até você aceitá-la pelo rádio.":["The incoming call does not change your TG, reflector or gateway until you accept it by radio.","La llamada entrante no cambia su TG, reflector ni gateway hasta que la acepte por radio."],
"Direct primeiro · Relay automático":["Direct first · automatic Relay","Direct primero · Relay automático"],
"Se o caminho UDP direto falhar, o PU2PNY usa automaticamente o relay autenticado mantendo a criptografia ponta a ponta.":["If the direct UDP path fails, PU2PNY automatically uses the authenticated relay while keeping end-to-end encryption.","Si falla la ruta UDP directa, PU2PNY usa automáticamente el relay autenticado manteniendo el cifrado de extremo a extremo."],
"Depois do QSO, o gateway anterior é restaurado automaticamente.":["After the QSO, the previous gateway is restored automatically.","Después del QSO, el gateway anterior se restaura automáticamente."],
"Chamada pelo rádio":["Call by radio","Llamada por radio"],
"Contato autorizado. Use o indicativo/ID digital no rádio para chamar ou aceitar.":["Contact authorized. Use the callsign/digital ID on the radio to call or accept.","Contacto autorizado. Use el indicativo/ID digital en la radio para llamar o aceptar."],
"Relay criptografado":["Encrypted relay","Relay cifrado"],
"Conexão direta":["Direct connection","Conexión directa"],
"Chamando":["Calling","Llamando"],
"Esperando aceitação":["Waiting for acceptance","Esperando aceptación"],
"Expirou sem aceitação":["Expired without acceptance","Expiró sin aceptación"]
});
Object.assign(D,{
"Notificações":["Notifications","Notificaciones"],
"Ativar notificações do navegador":["Enable browser notifications","Activar notificaciones del navegador"],
"A localização só é acessada após sua permissão.":["Location is accessed only after your permission.","La ubicación solo se accede después de su permiso."],
"Endereço para receber mensagens":["Address to receive messages","Dirección para recibir mensajes"],
"Sem transmissão":["No transmission","Sin transmisión"],
"Conexão":["Connection","Conexión"],
"Aguardando transmissões":["Waiting for transmissions","Esperando transmisiones"],
"Autorização do contato":["Contact authorization","Autorización del contacto"],
"Estado de validação":["Validation status","Estado de validación"],
"Resolução":["Resolution","Resolución"],
"Detecção":["Detection","Detección"],
"Ver detecção e runtime":["View detection and runtime","Ver detección y runtime"],
"Aplicar mudança de rede":["Apply network change","Aplicar cambio de red"],
"RXOffset · medição real":["RXOffset · real measurement","RXOffset · medición real"],
"Melhor medição da sessão":["Best session measurement","Mejor medición de la sesión"],
"Conexão via cabo":["Wired connection","Conexión por cable"],
"Caminho da conexão":["Connection path","Ruta de la conexión"],
"Mede e só altera com sua confirmação":["Measures and changes only with your confirmation","Mide y cambia solo con su confirmación"],
"Última comparação":["Last comparison","Última comparación"],
"Nova comparação":["New comparison","Nueva comparación"],
"Última atualização":["Last update","Última actualización"],
"Versão —":["Version —","Versión —"],
"versão...":["version...","versión..."],
"Horário de verão manual (+1 h apenas na exibição)":["Manual daylight saving time (+1 h display only)","Horario de verano manual (+1 h solo en pantalla)"],
"Baixar atualização":["Download update","Descargar actualización"],
"Conexão confirmada.":["Connection confirmed.","Conexión confirmada."],
"Repetidora Operação duplex":["Repeater Duplex operation","Repetidor Operación dúplex"],
"Não autentica o hotspot. Serve apenas para funções de gerenciamento no painel.":["Does not authenticate the hotspot. It is used only for management functions in the panel.","No autentica el hotspot. Se usa solo para funciones de administración en el panel."],
"França":["France","Francia"],
"Suíça":["Switzerland","Suiza"],
"Japão":["Japan","Japón"],
"AP manutenção":["Maintenance AP","AP de mantenimiento"],
"Serviços críticos e estado do gateway.":["Critical services and gateway status.","Servicios críticos y estado del gateway."],
"Serviços essenciais":["Essential services","Servicios esenciales"],
"Sistema / recepção":["System / reception","Sistema / recepción"],
"Um indicativo por linha · use + para abrir as transmissões":["One callsign per row · use + to open transmissions","Un indicativo por fila · use + para abrir las transmisiones"],
"Saúde dos serviços":["Service health","Salud de los servicios"],
"+ abre todas as transmissões armazenadas para aquele indicativo":["+ opens all stored transmissions for that callsign","+ abre todas las transmisiones almacenadas para ese indicativo"]
});
Object.assign(D,{
"APRS-IS automático":["Automatic APRS-IS","APRS-IS automático"],
"APRS-IS para envio e recebimento de mensagens. O PU2PNY identifica seu indicativo + SSID e aguarda o login verificado antes de transmitir.":["APRS-IS for sending and receiving messages. PU2PNY identifies your callsign + SSID and waits for a verified login before transmitting.","APRS-IS para enviar y recibir mensajes. PU2PNY identifica su indicativo + SSID y espera un inicio de sesión verificado antes de transmitir."],
"Modo mensagens:":["Message-only mode:","Modo solo mensajes:"],
"esta instalação não publica posição, mapa, GPS, latitude, longitude ou beacon APRS. O APRS é usado somente para mensagens.":["this installation does not publish position, maps, GPS, latitude, longitude, or APRS beacons. APRS is used only for messages.","esta instalación no publica posición, mapas, GPS, latitud, longitud ni balizas APRS. APRS se usa solo para mensajes."],
"Login APRS-IS":["APRS-IS login","Inicio de sesión APRS-IS"],
"O hotspot prepara a identificação internamente e só envia mensagens depois que o servidor confirma o login.":["The hotspot prepares identification internally and sends messages only after the server confirms the login.","El hotspot prepara la identificación internamente y solo envía mensajes después de que el servidor confirma el inicio de sesión."],
"Endereço para receber mensagens":["Address for receiving messages","Dirección para recibir mensajes"],
"Fila pendente":["Pending queue","Cola pendiente"],
"Último RX":["Last RX","Último RX"],
"Última mensagem TX":["Last message TX","Último mensaje TX"],
"Último erro":["Last error","Último error"],
"Último ACK recebido":["Last ACK received","Último ACK recibido"],
"Mensagens e confirmação":["Messages and confirmation","Mensajes y confirmación"],
"As mensagens usam APRS-IS e confirmação ACK/REJ quando o destinatário oferece esse recurso. Mensagens sem ACK permanecem identificadas como não confirmadas.":["Messages use APRS-IS and ACK/REJ confirmation when the recipient supports it. Messages without an ACK remain identified as unconfirmed.","Los mensajes usan APRS-IS y confirmación ACK/REJ cuando el destinatario lo admite. Los mensajes sin ACK permanecen identificados como no confirmados."],
"Mensagens":["Messages","Mensajes"],
"Sem mensagens.":["No messages.","Sin mensajes."],
"Ativar notificações do navegador":["Enable browser notifications","Activar notificaciones del navegador"],
"BrandMeister Hotspot Security Password":["BrandMeister Hotspot Security Password","Contraseña de seguridad del hotspot BrandMeister"],
"Usada somente para autenticar o hotspot. Depois de salva, a senha não é enviada de volta ao navegador nem exibida em texto aberto.":["Used only to authenticate the hotspot. After saving, the password is not sent back to the browser or displayed as plain text.","Se usa solo para autenticar el hotspot. Después de guardarla, la contraseña no se devuelve al navegador ni se muestra como texto visible."],
"Hotspot Security configurada. A senha salva não é exibida.":["Hotspot Security configured. The saved password is not displayed.","Hotspot Security configurada. La contraseña guardada no se muestra."],
"Hotspot Security ainda não configurada.":["Hotspot Security is not configured yet.","Hotspot Security aún no está configurada."],
"Senha já configurada — deixe vazio para manter ou digite outra para substituir":["Password already configured — leave blank to keep it or enter another to replace it","Contraseña ya configurada — déjela vacía para conservarla o escriba otra para reemplazarla"],
"Digite a mesma senha definida no BrandMeister SelfCare":["Enter the same password configured in BrandMeister SelfCare","Introduzca la misma contraseña configurada en BrandMeister SelfCare"],
"Mensagem na fila de envio APRS-IS":["Message queued for APRS-IS delivery","Mensaje en cola para envío APRS-IS"],
"Mensagem preservada na fila":["Message preserved in the queue","Mensaje conservado en la cola"],
"Enviada · aguardando confirmação (ACK)":["Sent · waiting for confirmation (ACK)","Enviado · esperando confirmación (ACK)"],
"Confirmada pelo destinatário (ACK)":["Confirmed by recipient (ACK)","Confirmado por el destinatario (ACK)"],
"Sem confirmação após as tentativas":["No confirmation after retries","Sin confirmación después de los reintentos"],
"Rejeitada pelo destinatário/rede":["Rejected by recipient/network","Rechazado por el destinatario/la red"],
"Recebida":["Received","Recibida"]
});
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
const STRICT_I18N_FALLBACK=true;
const ptLeak=/[ãõç]|(?:não|sim|aplicar|salvar|fuso|horário|relógio|rede|servidor|indicativo|cidade|país|estado|erro|falha|aguardando|conectando|desconectado|atualizar|configuração|senha|mensagem|ajuda|voltar|continuar|reiniciar|desligar|ligado|idioma|histórico|protocolo|frequência|potência|sinal|chamada|recebida|aceitação|rádio|anterior|restaurado|manual|automática|região)/i;
function strictUnknown(original){
  let technical=(String(original).match(/(?:HTTP\s*)?\b\d{3}\b|\b\d+(?:[.,]\d+)?\s*(?:ms|s|MHz|Hz|dBm|%|MB|GB)\b|\b[A-Z0-9_-]{3,}\b/g)||[]).slice(0,4).join(' · ');
  let base=language==='en'?'System message.':language==='es'?'Mensaje del sistema.':'Mensagem do sistema.';
  return technical?base+' '+technical:base;
}
function tx(text){
  let trimmed=normalizeIncoming(text);if(!trimmed)return trimmed;
  if(language==='pt')return trimmed;
  if(D[trimmed])return D[trimmed][language==='en'?0:1];
  let out=trimmed;for(const pair of loose[language]||[])out=out.replace(pair[0],pair[1]);
  if(ptLeak.test(out))return strictUnknown(trimmed);
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
function persistLanguage(v){try{fetch('/api/language',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language:v}),cache:'no-store'}).catch(()=>{})}catch(_){}}
function setLanguage(v,persist){v=String(v||'').toLowerCase();if(!/^(pt|en|es)$/.test(v))return;language=v;localStorage.setItem('pu2pny-language',language);let selector=document.getElementById('language');if(selector)selector.value=language;document.documentElement.lang=language==='pt'?'pt-BR':language;if(persist!==false)persistLanguage(language);translate()}
function bind(){let selector=document.getElementById('language');if(selector){selector.value=language;selector.onchange=()=>setLanguage(selector.value,true)}}
bind();translate();document.documentElement.classList.remove('pny-i18n-pending');
try{fetch('/api/language',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(v=>{if(v&&/^(pt|en|es)$/.test(v.language||''))setLanguage(v.language,false)}).catch(()=>{})}catch(_){};
let translating=false;new MutationObserver(()=>{if(translating)return;translating=true;queueMicrotask(()=>{try{bind();translate()}finally{translating=false}})}).observe(document.body,{subtree:true,childList:true,characterData:true});
window.translateNavigation=translate;window.PNYT=tx;window.PNYSetLanguage=setLanguage;window.PNYLocale=()=>language==='en'?'en-US':language==='es'?'es-ES':'pt-BR';
})();