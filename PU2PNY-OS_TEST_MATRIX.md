# PU2PNY-OS — TEST MATRIX

Legenda: **DOC**, **SW**, **VPS**, **HW**, **PROD**.  
Resultado: PASS / FAIL / PENDENTE / PARCIAL.

| ID | Caso de teste | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|
| TEST-NET-001 / NET-001 | Boot limpo sem uplink → AP | SSID `pu2pny`, 10.43.0.1 e wizard acessíveis | PASS | HW |
| TEST-NET-002 / NET-001 | Acessar `pu2pny.local` pelo AP | wizard abre sem descobrir IP | PASS | HW |
| TEST-NET-003 / NET-002 | Selecionar SSID + senha + salvar + reboot | associa ao SSID, recebe IPv4 e `pu2pny.local` volta | FAIL | HW |
| TEST-NET-004 / NET-002 | Wi-Fi falha | perfil anterior preservado e AP de recuperação volta | PARCIAL: AP voltou | HW |
| TEST-NET-005 / NET-003 | Comparar UI AP com RF/hostap real | UI = estado efetivo do SSID | FAIL | HW |
| TEST-NET-006 / NET-004 | Conectar Ethernet depois do boot | DHCP + painel + mDNS atualizam sem reboot | PARCIAL | HW |
| TEST-NET-007 / NET-005 | Dois perfis Wi-Fi | prioridade/failover sem perda do acesso | PENDENTE | — |
| TEST-NET-008 / NET-006 | Diagnóstico rota/DNS sob demanda | gateway, DNS, hops, ping/MTR coerentes e baixo custo | PENDENTE | — |
| TEST-WIZ-001 / WIZ-001 | Primeiro acesso novo | idioma antes do restante do wizard | PENDENTE | — |
| TEST-HW-001 / HW-001 | Preparar hardware real | Pi/MMDVM detectados sem travar | PASS | HW |
| TEST-RF-001 / RF-001 | Aplicar RF já funcional | MMDVMHost permanece ativo | PASS no baseline | HW |
| TEST-RF-002 / RF-001 | Forçar falha de apply | volta config/serviços anteriores | PASS no erro D-Star/YSF | HW |
| TEST-PROTO-001 / PROTO-001 | DMR TX/RX regressão completa | TX e RX iguais ao baseline aprovado | PENDENTE para 0.3.4 | HW requerido |
| TEST-PROTO-002 / PROTO-002 | DMR→D-Star | MMDVMHost + DStarGateway ativos e RF funcional | FAIL | HW |
| TEST-PROTO-003 / PROTO-003 | DMR→YSF | MMDVMHost + YSFGateway ativos e RF funcional | FAIL | HW |
| TEST-PROTO-004 / PROTO-005 | Broker preflight | antes do restart: serviço + TCP 127.0.0.1:1883 + pub/sub local comprovados | PENDENTE | SW/VPS/HW |
| TEST-PROTO-005 / PROTO-006 | Broker indisponível | aplicação aborta antes de tocar no RF ativo; mensagem clara | PENDENTE | SW/HW |
| TEST-LIVE-001 / LIVE-002 | Abrir "+" em atividade | permanece aberto em atualizações subsequentes | FAIL | HW |
| TEST-LIVE-002 / LIVE-003 | Evento sem BER/RSSI | campos não aparecem | FAIL/PENDENTE | HW |
| TEST-LIVE-003 / LIVE-004 | TX/RX ativo | duração destacada e atualizada | PARCIAL | HW |
| TEST-LIVE-004 / LIVE-010 | RX de RF por 180 s | alerta de atividade prolongada sem cortar RX | PENDENTE | HW |
| TEST-LIVE-005 / LIVE-010 | RX vindo da Internet | sem alerta de 180 s | PENDENTE | HW |
| TEST-DISPLAY-001 / DISPLAY-002 | Standby Nextion | hora, protocolo, uplink e IP estáveis; sem flicker | FAIL | HW |
| TEST-DISPLAY-002 / DISPLAY-003 | RX RF/NET | protocolo, origem, chamador e destino corretos | PENDENTE/FAIL | HW |
| TEST-DISPLAY-003 / DISPLAY-004 | TX | dados da estação/protocolo/destino/duração | PENDENTE | HW |
| TEST-DISPLAY-004 / DISPLAY-005 | Estado normal | nenhum retângulo vermelho espúrio/piscada | FAIL | HW |
| TEST-APRS-001 / APRS-001 | Browser sem Notification permission | APRS continua com alerta interno e instrução | FAIL atual | HW/browser |
| TEST-UI-001 / UI-001 | Todas as páginas | rodapé PU2PNY-OS + versão real | PENDENTE | — |
| TEST-UI-002 / UI-002 | 390px/768px/desktop + claro/escuro | sem overflow/regressão | PENDENTE 0.3.4 | SW/HW |
| TEST-SEC-001 / SEC-020 | SSH Expert | não-root, key-only, off por padrão | DOC baseline; retestar | SW/HW |
| TEST-PERF-001 / PERF-001 | Idle + Ao Vivo | CPU/RAM/logs sem regressão | PENDENTE | HW |
| TEST-REL-001 / REL-003 | Imagem ARM64 | build, montagem, validação estrutural e SHA-256 | PENDENTE | SW |

## Gate de conclusão

A 0.3.4 não pode ser chamada de release completa enquanto TEST-NET-003, TEST-NET-005, TEST-PROTO-001/002/003 e testes críticos de display/wizard associados permanecerem FAIL/PENDENTE. Compilar/CI não substitui HW.

## Casos SW/CI específicos da 0.3.4

| ID | Caso SW/CI | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|
| TEST-SW-034-001 | prepare 0.3.4 | overlay aplica e todos os scripts passam sintaxe/compile | PASS | SW |
| TEST-SW-034-002 | Wi-Fi staged/boot | persistência de segredo, associação real e IPv4 antes de sucesso | PASS estrutural/CI | SW |
| TEST-SW-034-003 | MQTT preflight/rollback | preflight presente + MMDVMHost restaurado deterministicamente | PASS estrutural/CI | SW |
| TEST-SW-034-004 | Ao Vivo | expansão persistente, métricas condicionais, alerta RF 180 s | PASS sintaxe/CI | SW |
| TEST-SW-034-005 | UI/Expert/APRS | idioma inicial, rodapé versão, JSON recolhido, alerta APRS interno | PASS sintaxe/CI | SW |
| TEST-SW-034-006 | Nextion overlay | sem limpeza total repetitiva, estado/uplink/IP preservando OLED/LCD | PASS estrutural/CI | SW |
| TEST-SW-034-007 | imagem ARM64 | xz íntegro, SHA-256, montagem e APIs 0.3.4 | PASS | SW |

**Regra:** PASS nesses casos permite distribuir somente uma **imagem alpha para teste**. Não converte TEST-NET/PROTO/DISPLAY de HW para PASS.

## Casos adicionados para 0.3.5-alpha

| ID | Caso de teste | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|
| TEST-WIZ-003 / WIZ-003 | etapa 100% válida | contador 5 s e avanço automático; botão manual disponível | PENDENTE | SW/HW |
| TEST-NET-009 / NET-009 | salvar 2 Wi-Fi e alternar | troca rápida, associação+IPv4, rollback sem refazer wizard | PENDENTE | HW |
| TEST-NET-010 / NET-010 | scan de canais | canal/freq/sinal e ocupação sem quebrar AP/Ethernet | PENDENTE | HW |
| TEST-NET-011 / NET-011 | rota ativa | rótulo Ótima/Boa/Ruim + gateway/destino/hops coerentes | PENDENTE | SW/HW |
| TEST-LIVE-008 / LIVE-008 | DMR XLX: TG4003/C → TG4002/B e depois TG6 | TX/RX continuam; painel muda runtime C→B e mantém B durante TG6 | FAIL UI atual; RF HW PASS | HW |
| TEST-LIVE-006 / LIVE-006 | Ao Vivo/Histórico | tabela rica compartilhada, sem dados inventados | PENDENTE | SW/HW |
| TEST-LIVE-007 / LIVE-007 | standby | radar leve e sem "Aguardando" duplicado | PENDENTE | SW/HW |
| TEST-APRS-002 / APRS-002 | mensagem recebida | toast 5 s clicável → APRS | PENDENTE | SW/HW |
| TEST-DISPLAY-007 / DISPLAY-007 | layout PU2PNY | opção própria sem gravar HMI/TFT | PENDENTE | SW/HW |
| TEST-DISPLAY-008 / DISPLAY-008 | splash/RX/TX | conteúdo moderno com identidade e fallback limpo | PENDENTE | HW |
| TEST-RF-011 / RF-011 | TX chega a 170 s | contagem 10→0 em web/display e corte nativo aos 180 s | PENDENTE | HW |
| TEST-UI-006 / UI-006 | timezone | relógio, timezone atual e seletor coerentes | PENDENTE | SW/HW |
| TEST-PERF-002 / PERF-002 | temperatura/idle | CPU/load/freq/throttling observáveis; sem polling agressivo | PENDENTE | HW |
| TEST-UPDATE-001 / UPDATE-001 | atualização falha/interrompe | nunca congela progresso; preserva versão e informa rollback | PENDENTE | SW/VPS/HW |
| TEST-UPDATE-002 / UPDATE-002 | manutenção | manual/auto, baixa prioridade, sem full-upgrade/RF mutation | PENDENTE | SW/VPS |
| TEST-UI-005 / UI-005 | Trocar rede após provisionar | retorna ao painel sem repetir HW/RF/conclusão | FAIL atual | HW |


## Casos SW/CI específicos da 0.3.5

| ID | Caso SW/CI | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|
| TEST-SW-035-001 | fontes 0.3.5 | Go/Python/Bash/JS passam validação | PASS | SW |
| TEST-SW-035-002 | cadeia de overlays | 0.3.4 completo é aplicado antes da 0.3.5, preservando baseline | PASS | SW |
| TEST-SW-035-003 | MMDVMHost INI D-Star/YSF | candidato usa delimitador nativo `Key=Value` e gate contra formato incompatível | PASS estrutural | SW |
| TEST-SW-035-004 | DMR módulo runtime | estado de módulo efetivo pode sobrescrever apenas a apresentação, sem reiniciar DMRGateway/MMDVMHost | PASS estrutural | SW |
| TEST-SW-035-005 | rede/UI | segunda Wi-Fi, DNS manual, rota/canais, wizard e retorno pós-provisionamento presentes | PASS estrutural/JS | SW |
| TEST-SW-035-006 | Live/Histórico/APRS | tabela rica, radar, TOT UI e toast APRS passam sintaxe/gates | PASS estrutural/JS | SW |
| TEST-SW-035-007 | Display/Manutenção | PU2PNY Moderno, splash, TOT 10→0 e manutenção sem percentual inventado passam compile/gates | PASS estrutural | SW |
| TEST-SW-035-008 | imagem ARM64 | build, XZ, SHA-256, montagem, APIs e validador final | PASS | SW |

**Regra:** estes PASS autorizam somente a imagem **0.3.5 Alpha para teste físico**. Os casos NET/PROTO/LIVE/DISPLAY/APRS de nível HW permanecem PENDENTE/FAIL até o novo teste no equipamento.


## Casos adicionados para 0.3.6-alpha após teste físico da 0.3.5

| ID | Caso de teste | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|
| TEST-NET-012 / NET-012 | conectar cliente ao AP | captive portal é oferecido/aberto quando suportado; fallback local sempre funciona | PENDENTE | SW/HW/client |
| TEST-NET-013 / NET-013 | buscar/salvar Wi‑Fi 2 no painel | sem `unbound variable`; rede salva e UI permanece em Internet | FAIL reportado | HW |
| TEST-NET-014 / NET-014 | Google → Cloudflare | DNS efetivo mostra somente perfil ativo e confirma retorno à página | FAIL reportado | HW |
| TEST-NET-015 / NET-015 | diagnóstico de rota | explicação leiga + Melhor/Bom/Ruim/Péssimo com critérios | PENDENTE | SW/HW |
| TEST-WIZ-005 / WIZ-005 | primeiro acesso | exemplos genéricos; rótulo Radio ID aplicável | FAIL visual atual | SW/HW |
| TEST-UI-007 / UI-007 | alternar PT/EN/ES | 100% dos textos de UI/avisos seguem idioma selecionado | FAIL/PARCIAL atual | SW/HW |
| TEST-UI-008 / UI-008 | salvar/aplicar/atualizar | feedback imediato, etapa real, resultado e retorno ao contexto | FAIL/PARCIAL atual | SW/HW |
| TEST-UI-009 / UI-009 | abrir configuração detalhada após provisionar | não volta ao primeiro acesso | FAIL reportado | HW |
| TEST-UI-010 / UI-010 | trocar timezone | backend autorizado aplica; sem Access denied | FAIL reportado | SW/HW |
| TEST-UI-011 / UI-011 | Expert | estado Ao Vivo aparece e RF/protocolo ficam em Hotspot | FAIL reportado | SW/HW |
| TEST-LIVE-009 / LIVE-009 | histórico/última atividade | QRZ/RadioID aparecem só com URL válida e abrem nova aba | PENDENTE | SW/HW |
| TEST-APRS-003 / APRS-003 | usar localização | pede permissão, preenche lat/lon, manual continua disponível | PENDENTE | browser/HW |
| TEST-DISPLAY-010 / DISPLAY-010 | Nextion/OLED/TFT/LCD | standby/RX/TX profissionais e responsivos à capacidade da tela | FAIL visual atual | HW |
| TEST-UPDATE-003 / UPDATE-003 | versão nova/downgrade | check leve, checksum, backup opcional, install/rollback e downgrade explícito | PENDENTE | SW/VPS/HW |
| TEST-UPDATE-004 / UPDATE-004 | manutenção | mostra última execução e próxima elegível | FAIL reportado | SW/HW |
| TEST-PROTO-007 / PROTO-007 | D-Star XLX026 | RF→rede, rede→RF, módulo efetivo e feedback de conexão | FAIL reportado | HW |
| TEST-PROTO-008 / PROTO-008 | YSF72426 | RF→rede e rede→RF com tráfego real | FAIL reportado | HW |
| TEST-PROTO-009 / PROTO-009 | perfis DMR/D-Star/YSF | cada protocolo restaura sua RF/rede sem reconfiguração manual | PENDENTE | SW/HW |
| TEST-ARCH-003 / ARCH-003 | mudança comum | comportamento corrigido em todas as páginas/protocolos aplicáveis | PENDENTE | SW |
| TEST-REL-004 / REL-004 | escopo 0.3.6 | novas funções deste feedback estão implementadas no nível verificável nesta versão | PENDENTE | DOC/SW/VPS |
| TEST-REL-005 / REL-005 | regressão DMR | TX/RX DMR permanecem iguais à 0.3.5 aprovada | HW requerido | HW |

## Casos adicionais 0.3.6-alpha — alias DMR e BrandMeister API

| ID | Caso de teste | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|
| TEST-PROTO-010A / PROTO-010 | Radio ID base de 7 dígitos + `Rádio 1 (01)` | DMRGateway recebe ID de rede de 9 dígitos terminando em `01`; Radio ID base permanece inalterado | PASS determinístico; HW pendente | VPS/HW |
| TEST-PROTO-010B / PROTO-010 | trocar para `Rádio 2 (02)` | somente alias/ESSID muda para `02`; apply é transacional e DMR volta conectado | PASS determinístico; HW pendente | VPS/HW |
| TEST-PROTO-010C / PROTO-010 | sufixo inválido `1`, `00`, texto ou >99 | backend rejeita antes de alterar DMR funcional | PASS | VPS |
| TEST-PROTO-011A / PROTO-011 | salvar BrandMeister API Key | segredo vai para arquivo restrito; resposta retorna apenas `configured=true` | PASS estrutural/compile; runtime HW pendente | SW |
| TEST-PROTO-011B / PROTO-011 | remover BrandMeister API Key | segredo é removido sem reiniciar MMDVMHost/DMRGateway | PASS estrutural; runtime HW pendente | SW |
| TEST-PROTO-011C / PROTO-011 | API Key x Hotspot Security | API Key nunca é enviada como senha do master; Hotspot Security continua obrigatória | PASS estrutural; HW pendente | SW/HW |
| TEST-SEC-021 / SEC-021 | logs/API/config pública | valor da API Key não aparece em JSON público, logs ou estado do protocolo | PASS estrutural/compile; runtime HW pendente | SW |
| TEST-REL-006 / REL-005 | regressão DMR após alias/API | DMR TX/RX da 0.3.5 permanece baseline; API isolada não reinicia o rádio | HW requerido | HW |

## Casos adicionais 0.3.6-alpha — APRS mensagens

| ID | Caso de teste | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|
| TEST-APRS-004A / APRS-004 | TCP conecta mas `logresp` ainda não confirmou | nenhuma mensagem/beacon sai; UI mostra aguardando autenticação | PASS determinístico | SW/VPS |
| TEST-APRS-004B / APRS-004 | `logresp ... verified` | sessão muda para verificada e fila pode transmitir | PASS determinístico; login real HW pendente | SW/HW |
| TEST-APRS-004C / APRS-004 | mensagem na outbox com sessão verificada | pacote APRS correto é enviado; histórico marca tentativa/estado | PASS determinístico; rede real HW pendente | SW/HW |
| TEST-APRS-004D / APRS-004 | mensagem recebida com ID | inbox registra uma vez e cliente envia `ack<ID>` | PASS determinístico; rede real HW pendente | SW/HW |
| TEST-APRS-004E / APRS-004 | mesma mensagem recebida novamente | não duplica inbox/unread e reenvia ACK | PASS determinístico | SW |
| TEST-APRS-004F / APRS-004 | ACK/REJ remoto | mensagem enviada muda para `ack`/`rejected` | PASS determinístico; rede real HW pendente | SW/HW |
| TEST-APRS-004G / APRS-004 | sem ACK após envio | retry limitado usa o mesmo ID e para após limite, sem flood | PASS determinístico | SW |
| TEST-APRS-004H / APRS-004 | servidor/login indisponível | fila é preservada; painel mostra erro/fila pendente sem perda da mensagem | PASS fila/erro em SW + TCP `soam.aprs2.net:14580` alcançável em VPS; HW pendente | VPS/HW |

## Casos adicionados — 0.3.6 hwfix2

| ID | Requisito | Caso | Nível alvo neste build | Estado antes do CI |
|---|---|---|---|---|
| TEST-036-DSTAR-SCHEMA | PROTO-012 | Gerar DStarGateway.ini e exigir General/Repeater 1/IRCDDB 1/Hosts Files + log numérico; rejeitar Gateway/Repeater_1 | SW | PENDENTE |
| TEST-036-WIFI-HANDOFF | NET-017 | Verificar busca tolerante à pausa do AP, SSID manual nos dois perfis e ausência de reboot obrigatório após associação+IP | SW/HW | PENDENTE |
| TEST-036-DNS-EFFECTIVE | NET-016 | Validar parsing IPv4 de nmcli/resolvectl/resolv.conf e janela de 180 s | SW | PENDENTE |
| TEST-036-APRS-UX | APRS-005 | Validar fallback de contexto inseguro, links de ajuda/teste e preenchimento de destinatário pelo remetente | SW | PENDENTE |
| TEST-036-RADIOID-UI | UI-012 | Garantir que Live/Histórico não apontem diretamente ao endpoint JSON e que a página legível faça consulta sob demanda | SW | PENDENTE |
| TEST-036-UPDATE-STAGED | UPDATE-005 | Simular download/estado; instalação só aceita pacote staged verificado e SHA correspondente | SW | PENDENTE |
| TEST-036-P25-STATIC | TEST-006 | Gerar P25Gateway/MMDVMHost sem systemd/RF real e conferir portas/seções | SW | PENDENTE |
| TEST-036-DISPLAY-CONTEXT | DISPLAY-011 | Verificar campos essenciais de TX/RX e contexto de IP/uplink nos renderers compactos | SW | PENDENTE |

## Casos adicionados — displays genéricos e Raspberry Pi 32-bit

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-DISPLAY-012A | DISPLAY-012 | OLED SSD1306/SH1106 | ativa sem terminal e mostra Standby/TX/RX com dados reais/compactos | código parcial existente; HW pendente | SW/HW |
| TEST-DISPLAY-012B | DISPLAY-012 | LCD HD44780/PCF8574 | ativa sem terminal e mostra Standby/TX/RX conforme linhas/colunas | código parcial existente; HW pendente | SW/HW |
| TEST-DISPLAY-012C | DISPLAY-012 | display genérico candidato/ambíguo | não marca modelo como confirmado sem evidência; falha do driver não afeta RF | PENDENTE | SW/HW |
| TEST-ARCH-004A | ARCH-004 | build armhf/GOARM=6 | binário 2pnyd é ARM 32-bit e rootfs contém somente componentes compatíveis | PASS: imagem gerada; 2pnyd + MMDVMHost + gateways DMR/D-Star/YSF/P25/NXDN/DAPNET confirmados ELF 32-bit ARM EABI5 | SW |
| TEST-ARCH-004B | ARCH-004 | boot em Pi Zero/1/2 | boot, rede, painel, MMDVM e ao menos DMR baseline sem regressão | PENDENTE | HW |
| TEST-PERF-003 | PERF-003 | idle e TX/RX em 512 MB | sem OOM, sem swapping excessivo, RF estável e polling/logs controlados | PENDENTE | HW |
| TEST-REL-007 | REL-007 | artefato ARM32 | .img.xz íntegro, SHA-256, validação estrutural e arquitetura correta | PASS SW/estrutural no run 35545030803; HW boot/RF ainda PENDENTE | SW/HW |

## Casos adicionados — 0.3.7 Direct/Display/Voice

| ID | Requisito | Caso | Resultado esperado | Nível |
|---|---|---|---|---|
| TEST-REL-008 | REL-008 | regressão completa 0.3.6 | todos os testes/gates anteriores continuam PASS no nível já alcançado | SW/HW |
| TEST-P2P-002A | P2P-002 | escolher contato/indicativo | chamada pode ser preparada sem IP/porta/terminal e rejeita protocolo incompatível | SW |
| TEST-P2P-003A | P2P-003 | endpoint direto disponível | estado `Direct`, peer autenticado, latência real quando mensurável | SW/VPS/HW |
| TEST-P2P-003B | P2P-003 | NAT restritivo | fallback `Relay`, sem rotular como Direct, mantendo criptografia ponta a ponta | VPS/HW |
| TEST-P2P-005 | P2P-005 | parear/revogar | chaves privadas não saem na API; peer revogado deixa de ser autorizado | SW/VPS |
| TEST-P2P-006A | P2P-006 | encapsular quadros DMR/D-Star/YSF | envelope autenticado, sequência/anti-replay e protocolo preservados | SW |
| TEST-P2P-006B | P2P-006 | dois hotspots reais | RF A→Direct→RF B e retorno no mesmo protocolo | HW |
| TEST-DISPLAY-013A | DISPLAY-013 | Nextion | Standby/TX/RX Moderno V2 sem HMI flash automático/flicker espúrio | SW/HW |
| TEST-DISPLAY-013B | DISPLAY-013 | OLED SSD1306/SH1106 | layout gráfico compacto com header/estado/identidade/rede | SW/HW |
| TEST-DISPLAY-013C | DISPLAY-013 | LCD | layout textual coerente, sem tentar recursos gráficos inexistentes | SW/HW |
| TEST-PROTO-013A | PROTO-013 | gateway confirma link | anúncio é solicitado uma vez após `connected`, com rate-limit | SW/HW |
| TEST-PROTO-013B | PROTO-013 | link falha/não confirmado | nenhum anúncio falso é enviado | SW/HW |
| TEST-007 | TEST-007 | imagem 0.3.7 | build+XZ+SHA+validador final PASS antes de publicar | SW |

## Casos adicionados — tela genérica touch 7"

| ID | Requisito | Caso | Resultado esperado | Nível/Estado |
|---|---|---|---|---|
| TEST-DISPLAY-014A | DISPLAY-014 | vídeo 7" HDMI/DSI | imagem PU2PNY correta em boot/runtime, resolução utilizável, sem exigir terminal | HW PENDENTE |
| TEST-DISPLAY-014B | DISPLAY-014 | touch USB/DSI | toque reconhecido, coordenadas corretas, navegação e botões funcionais sem mouse | HW PENDENTE |
| TEST-DISPLAY-014C | DISPLAY-014 | operação Standby/RX/TX | estados e dados reais acompanham o mesmo runtime do painel sem travar RF | HW PENDENTE |
| TEST-DISPLAY-014D | DISPLAY-014 | touch ausente/falha | vídeo/painel continuam e RF/gateways não caem; diagnóstico claro | HW PENDENTE |

## Feedback físico 0.3.7-alpha — Nextion

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-HW-037-NEXTION-READY | DISPLAY-001/002/013 | Boot/wizard concluído sem abrir menu Display | Nextion sai de "Pronto" e acompanha automaticamente o runtime/Standby, sem depender de configuração manual no menu Display | **FAIL** — permaneceu travada em "Pronto" | HW |

## Feedback físico 0.3.7-alpha — atualização dinâmica de DNS

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-UI-013-DNS | UI-013 / NET-016 | trocar DNS e aguardar conclusão | mensagem de aplicação termina e "DNS efetivo" + diagnóstico mudam automaticamente para o estado confirmado, sem F5 | **FAIL** — foi necessário atualizar a página, inclusive duas vezes em uma tentativa | HW/browser |

## Feedback físico 0.3.7-alpha — Wi-Fi 1/2

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-NET-018A | NET-018 | salvar Wi-Fi 1 | perfil persiste e a página mostra imediatamente `Salva/Conectada` conforme estado real | **FAIL** — após aplicar não ficou claro que foi salvo/conectado | HW/browser |
| TEST-NET-018B | NET-018 | salvar Wi-Fi 2 | salva o perfil sem trocar de rede automaticamente; troca só por ação explícita | **FAIL** — botão "Salvar Rede Wi-Fi 2" tentou conectar/trocar | HW/browser |
| TEST-NET-018C | NET-018 | trocar Wi-Fi 1↔2 | mensagem transacional + associação/IP rápidos, sem reboot desnecessário, com rollback em falha | **FAIL** — operação terminou com erro; rede/configuração ainda instáveis | HW |
| TEST-UI-014A | UI-014 | senha Wi-Fi 1/2 | botão Mostrar/Ocultar funciona nos dois campos | **FAIL** — não há controle para visualizar a senha digitada | HW/browser |
| TEST-UI-014B | UI-014 / UI-007 | erro de rede em PT-BR | mensagem principal em português; detalhe bruto apenas no Expert/log | **FAIL** — exibiu `signal is aborted without reason` em inglês | HW/browser |
| TEST-UI-014C | UI-014 / UI-013 | salvar/aplicar perfil | estado do perfil/conexão atualiza sozinho, sem F5 | **FAIL** — retorno não mostrou claramente perfil salvo/conectado | HW/browser |
