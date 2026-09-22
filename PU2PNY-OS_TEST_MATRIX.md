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

## Casos adicionados — gráfico/recomendação de canal Wi-Fi

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-NET-019A | NET-019 | scan de canais 2,4 GHz | gráfico mostra canais observados, SSIDs/força quando disponíveis e destaca o canal da rede ativa | PENDENTE | SW/HW |
| TEST-NET-019B | NET-019 | hardware com 5 GHz | gráfico separa 2,4/5 GHz e respeita canais permitidos pelo domínio regulatório | PENDENTE | SW/HW |
| TEST-NET-019C | NET-019 | recomendação | sugere um canal com justificativa baseada em ocupação/sinal/sobreposição; não altera o roteador | PENDENTE | SW/HW |
| TEST-NET-019D | NET-019 / PERF-001 | repetir análise | scan é manual/cacheado, não derruba Wi-Fi/AP e não cria polling pesado | PENDENTE | HW |
| TEST-NET-019E | NET-019 | dados incompletos | não inventa largura/sinal/canal; mostra indisponível quando não houver evidência | PENDENTE | SW/HW |

## Casos adicionados — perfis rápidos no Ao Vivo / configuração no Hotspot

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-LIVE-011A | LIVE-011 | abrir Ao Vivo | botões DMR/D-Star/YSF/etc. representam perfis e destacam o protocolo ativo | PENDENTE | SW/HW |
| TEST-LIVE-011B | LIVE-011 | clicar perfil configurado | mostra progresso real, faz preflight/apply/rollback e atualiza Ao Vivo sem F5 | PENDENTE | SW/HW |
| TEST-LIVE-011C | LIVE-011 | clicar perfil não configurado | não tenta aplicar; abre configuração correspondente | PENDENTE | SW/HW |
| TEST-LIVE-011D | LIVE-011 | filtros de atividade | continuam disponíveis separadamente e funcionais após a mudança | PENDENTE | SW/HW |
| TEST-PROTO-014A | PROTO-014 | página Hotspot | perfis permanecem visíveis e cada um oferece ação de configurar | PENDENTE | SW/HW |
| TEST-PROTO-014B | PROTO-014 | configurar frequência/rede | abre contexto correto do protocolo sem refazer wizard e sem alterar outro perfil | PENDENTE | SW/HW |

## Feedback físico 0.3.7-alpha — PU2PNY Direct

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-P2P-007A | P2P-007 | nenhum contato pareado + clicar Chamar | botão desabilitado ou mensagem PT explicando que é necessário parear; nenhum `HTTP 409` bruto | **FAIL** — UI exibiu `HTTP 409` | HW/browser |
| TEST-P2P-007B | P2P-007 | indicativo inexistente/offline | mensagem clara `PU2PNY não encontrado ou offline`; RF inalterado | PENDENTE | SW/VPS/HW |
| TEST-P2P-007C | P2P-007 | peer pareado porém sem resposta | informa sem resposta, restaura/preserva gateway anterior e não deixa estado falso de conectado | PENDENTE | SW/HW |
| TEST-P2P-007D | P2P-007 | protocolos diferentes | bloqueia antes de alterar RF e informa local/remoto | PENDENTE | SW/HW |
| TEST-UI-015A | UI-015 | abrir Direct em desktop | cabeçalho/menu/cards/botões seguem layout padrão sem elementos concatenados ou estourados | **FAIL** — página visualmente quebrada no teste | HW/browser |
| TEST-UI-015B | UI-015 | 390px/768px/desktop | Direct responsiva e usável, sem overflow/controles quebrados | PENDENTE | SW/HW |

## Feedback físico 0.3.7-alpha — APRS-IS assistido

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-APRS-006A | APRS-006 | usuário leigo abre APRS | descrição explica APRS-IS, indicativo/SSID e confirmação do servidor sem jargão obrigatório | **FAIL** — tela fala em "login APRS-IS" sem explicar o que é | HW/browser |
| TEST-APRS-006B | APRS-006 | Testar estado agora | mostra etapas Internet→TCP→identificação→resposta→verificado e ação corretiva | **FAIL** — mensagem genérica apenas pede conferir vários itens | HW/browser |
| TEST-APRS-006C | APRS-006 | servidor responde unverified/timeout | erro principal traduzido; detalhe técnico somente no Expert | PENDENTE | SW/HW |
| TEST-APRS-006D | APRS-006 | sessão não verificada | beacon/mensagem não são marcados como enviados | PENDENTE | SW/HW |
| TEST-APRS-002B | APRS-002 | nova mensagem com usuário em outra página | toast global ~5 s mostra remetente/resumo e clique abre APRS para responder | **NÃO IMPLEMENTADO GLOBALMENTE / HW PENDENTE** | DOC/SW/HW |

| TEST-APRS-007A | APRS-007 | rádio D-Star envia D-PRS válido | posição real é recebida, identificada como D-PRS e encaminhada conforme configuração sem duplicar | PENDENTE | HW |
| TEST-APRS-007B | APRS-007 | quadro D-PRS inválido/sem posição | descarta com diagnóstico e não inventa latitude/longitude | PENDENTE | SW/HW |
| TEST-APRS-007C | APRS-007 | falha APRS-IS durante D-PRS | D-Star/RF permanecem operacionais; posição fica pendente/erro visível | PENDENTE | HW |

## Casos adicionados — Histórico/Últimas atividades enriquecidos

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-LIVE-012A | LIVE-012 | evento Internet → RF | mostra direção, identidade disponível, protocolo, destino, servidor/rede, horário e duração sem BER/RSSI remoto inventado | PENDENTE | SW/HW |
| TEST-LIVE-012B | LIVE-012 | evento RF → Internet | mostra identidade disponível, protocolo, destino, RF real, BER/RSSI somente quando medidos | PENDENTE | SW/HW |
| TEST-LIVE-012C | LIVE-012 | múltiplas transmissões do mesmo indicativo | Histórico agrupa ocorrências e mostra quantidade, tempo acumulado e último evento corretamente | PENDENTE | SW/HW |
| TEST-LIVE-012D | LIVE-012 / DATA-001 | campo não disponível | UI omite ou mostra `—`; não inventa cidade, gateway, RSSI, BER, TG ou módulo | PENDENTE | SW |
| TEST-LIVE-012E | LIVE-012 | QRZ/RadioID | atalhos aparecem somente para identificadores válidos e não abrem JSON bruto | PENDENTE | SW/HW |
| TEST-LIVE-012F | LIVE-012 / PERF-001 | atualização contínua | Ao Vivo atualiza pelo Event Bus sem polling externo pesado; Histórico usa cache/intervalo leve | PENDENTE | SW/HW |

## Feedback físico 0.3.7-alpha — Sistema / fuso horário

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-UI-016-TZ | UI-016 / UI-006 | selecionar America/Sao_Paulo e aplicar | fuso muda pelo painel, estado é relido/confirmado e relógio atualiza sem terminal/F5 | **FAIL** — operação bloqueada por permissão (`Access denied`) | HW/browser |
| TEST-UI-016-TZ-ROLLBACK | UI-016 | falha de privilégio/aplicação | fuso anterior permanece ativo; mensagem amigável; RF/gateways inalterados | PENDENTE | SW/HW |

## Feedback físico 0.3.7-alpha — cabeçalho Sistema

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-UI-017A | UI-017 | abrir Sistema na mesma largura de Display | cabeçalho mantém mesma altura; relógio aparece em uma linha e controles não são esmagados | **FAIL** — relógio foi comprimido/quebrado e cabeçalho ficou mais alto | HW/browser |
| TEST-UI-017B | UI-017 | navegar entre todas as páginas desktop | cabeçalho permanece dimensionalmente estável sem saltos de altura | PENDENTE | SW/HW |
| TEST-UI-017C | UI-017 / UI-002 | viewport tablet/mobile | menu e ferramentas degradam responsivamente sem sobreposição ou relógio vertical | PENDENTE | SW/HW |

## Feedback físico 0.3.7-alpha — Expert

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-UI-018A | UI-018 | transmissão RF/Internet com Expert aberto | Estado Ao Vivo muda pelo Event Bus/SSE praticamente em tempo real | **FAIL** — implementação atual recarrega a cada 15 s | HW/browser + DOC |
| TEST-UI-018B | UI-018 / PERF-001 | dashboard Expert aberto 30 min | CPU/temp/RAM/rede atualizam com gráficos leves sem MTR/scan pesado e sem escrita contínua em SD | PENDENTE | SW/HW |
| TEST-UI-018C | UI-018 | hardware | cards/gráficos mostram dados reais disponíveis e detalhes técnicos ficam recolhidos | PENDENTE | SW/HW |
| TEST-UI-019A | UI-019 | Resumo operacional | substitui "Configuração pública" e mostra RF/protocolo/rede/display/timezone sem qualquer segredo | PENDENTE | SW/HW |
| TEST-SEC-021A | SEC-021 | chave vazia/inválida | explica o problema e o formato esperado antes de tentar habilitar SSH | **FAIL UX** — exibiu apenas "Chave pública SSH inválida" | HW/browser |
| TEST-SEC-021B | SEC-021 | chave pública OpenSSH válida | cria/configura radioexpert, valida sshd, inicia ssh.service e confirma estado/IP/porta na UI | PENDENTE | HW |
| TEST-SEC-021C | SEC-021 | desativar SSH | serviço para e UI confirma estado desativado | PENDENTE | HW |

## Casos adicionados — BER / calibração assistida

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-RF-013A | RF-013 | BER RF alto sustentado com sinal estável | sistema reconhece condição somente após múltiplas amostras válidas e oferece/inicia calibração protegida | PENDENTE | SW/HW |
| TEST-RF-013B | RF-013 | autoajuste RXOffset | testa offsets limitados, mede BER, aplica somente melhora consistente e registra valor anterior | PENDENTE | HW |
| TEST-RF-013C | RF-013 | nenhuma melhora | restaura RXOffset original automaticamente e informa falha segura | PENDENTE | HW |
| TEST-RF-013D | RF-013 / REL-001 | DMR após ajuste | TX/RX DMR continua funcional; sem regressão de frequência/modem/gateway | PENDENTE | HW |
| TEST-RF-014A | RF-014 | BER local alto | TXOffset permanece inalterado durante autoajuste baseado apenas no BER do hotspot | PENDENTE | SW/HW |
| TEST-UI-020A | UI-020 | autoajuste falha/não pode iniciar | toast global orienta usuário e clique abre Expert diretamente na Calibração RF | PENDENTE | SW/HW |
| TEST-UI-020B | UI-020 | ajuste manual Expert | RXOffset/TXOffset podem ser alterados com preflight, validação e rollback; valor antigo permanece recuperável | PENDENTE | HW |

## Casos adicionados — Ao Vivo / Sinal e qualidade

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-LIVE-013A | LIVE-013 | RX originado em RF com RSSI real | S-meter/RSSI acompanha evento em tempo real e mostra dBm + BER reais | PENDENTE | HW |
| TEST-LIVE-013B | LIVE-013 | RX RF sem RSSI | medidor mostra indisponível; nenhuma barra/valor é inventado | PENDENTE | SW/HW |
| TEST-LIVE-013C | LIVE-013 / NET-010 | uplink Wi-Fi | indicador mostra sinal da conexão ativa + Ótimo/Bom/Ruim sem iniciar scan | PENDENTE | SW/HW |
| TEST-LIVE-013D | LIVE-013 | uplink Ethernet | indicador mostra Ethernet/Link ativo e não apresenta qualidade Wi-Fi falsa | PENDENTE | SW/HW |
| TEST-LIVE-013E | LIVE-013 / NET-011 | Internet | qualidade reutiliza latência/perda/jitter cacheados e não dispara MTR em loop | PENDENTE | SW/HW |
| TEST-LIVE-014A | LIVE-014 | RF → Internet | bloco mostra RX, identidade, destino, RX freq, duração, RSSI/BER e gateway quando reais | PENDENTE | HW |
| TEST-LIVE-014B | LIVE-014 | Internet → RF | bloco mostra TX, identidade remota, destino, TX freq, duração e rede; sem RSSI/BER remoto falso | PENDENTE | HW |
| TEST-LIVE-014C | LIVE-014 | Standby | mostra perfil/frequências/uplink/saúde resumida sem campos falsos | PENDENTE | SW/HW |
| TEST-UI-021A | UI-021 | BER/Wi-Fi/Internet ruim | aviso clicável abre exatamente a área de diagnóstico/correção correspondente | PENDENTE | SW/HW |

## Casos adicionados — potência MMDVM e idiomas

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-RF-015A | RF-015 / UI-022 | modem suporta RFLevel | Expert mostra valor real, altera de forma transacional e MMDVMHost permanece ativo | PENDENTE | SW/HW |
| TEST-RF-015B | RF-015 | aplicar valor inválido/falha | configuração anterior é restaurada automaticamente | PENDENTE | SW/HW |
| TEST-RF-015C | RF-015 | TX ativo | alteração é bloqueada/adiada até estado seguro | PENDENTE | HW |
| TEST-RF-015D | RF-015 | modem sem suporte confirmado | controle fica desabilitado e explica o motivo; nenhum valor é inventado | PENDENTE | SW/HW |
| TEST-UI-023-PT | UI-023 | navegar por todas as páginas em Português | 100% dos textos operacionais em PT, sem EN/ES misturado | PENDENTE | SW/HW |
| TEST-UI-023-EN | UI-023 | navegar por todas as páginas em English | 100% dos textos operacionais em EN, sem PT/ES misturado | **FAIL observado na 0.3.7** | HW/browser |
| TEST-UI-023-ES | UI-023 | navegar por todas as páginas em Español | 100% dos textos operacionais em ES, sem PT/EN misturado | PENDENTE | SW/HW |
| TEST-UI-023-DYN | UI-023 | erros/modais/toasts/estados dinâmicos | mensagem amigável acompanha idioma; texto técnico bruto só no Expert/log | PENDENTE | SW/HW |
| TEST-UI-023-CI | UI-023 | build/catalog completeness | build falha se uma chave usada não existir em PT/EN/ES ou se texto operacional novo escapar do catálogo | PENDENTE | SW |

## Feedback físico 0.3.7-alpha — boot, Wi-Fi e display após reinício

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-BOOT-001A | BOOT-001 | reiniciar hotspot com perfil/protocolo ativo salvo | após boot MMDVMHost + gateway do último perfil voltam automaticamente; não exige `Ativar perfil` | **FAIL** — após religar o hotspot o operacional ficou desligado e foi necessário ativar manualmente o perfil | HW |
| TEST-BOOT-001B | BOOT-001 | botão `Ligar operacional` | backend inicia e confirma MMDVMHost + gateway correspondente; UI muda para Ligado ou mostra erro acionável | **FAIL** — clique não apresentou mudança/resultado útil no teste | HW/browser |
| TEST-BOOT-001C | BOOT-001 | usuário desliga operacional explicitamente e reinicia | estado desligado persiste apenas por marcador explícito; nenhum gateway sobe sozinho | PENDENTE | SW/HW |
| TEST-NET-020A | NET-020 | boot com Wi-Fi associado e rota padrão em wlan0 | UI mostra SSID e sinal/RSSI reais da associação ativa sem rescan agressivo | **FAIL UI** — screenshot mostra wlan0/Internet ativos, porém SSID e RSSI aparecem `—` | HW/browser |
| TEST-NET-020B | NET-020 / NET-018 | dois perfis salvos + reboot | NetworkManager escolhe perfil autoconnect conforme prioridade e mantém fallback seguro | PENDENTE | HW |
| TEST-DISPLAY-015A | DISPLAY-015 | boot com Nextion | `Iniciando` é transitório e termina em estado operacional/standby quando serviços sobem | **FAIL** — Nextion permaneceu travada em `Iniciando` enquanto operacional não foi restaurado | HW |
| TEST-DISPLAY-015B | DISPLAY-015 | executar Manutenção pelo painel | tela pode indicar manutenção durante a tarefa, mas ao terminar sai automaticamente desse estado | **FAIL** — Nextion ficou travada mostrando Manutenção | HW |
| TEST-DISPLAY-015C | DISPLAY-015 | manutenção com operacional explicitamente desligado | ao terminar mostra Operacional desligado/atenção, nunca `Pronto` falso | PENDENTE | SW/HW |

## Evidência de build — 0.3.8-alpha ARM64 — 2026-09-21

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-REL-038 | REL-003 | imagem 0.3.8-alpha ARM64 | source + staged source + build ARM64 + XZ + SHA-256 + validação estrutural + publicação concluídos antes da divulgação | **PASS** — GitHub Actions run `35560842909`; imagem publicada em prerelease `v0.3.8-alpha` | SW |
| TEST-BOOT-001A-038 | BOOT-001 | novo boot com restauração do perfil | código/helper de restauração e unit de boot presentes na imagem; comportamento real deve ser repetido no Raspberry Pi | **SW/estrutural PASS; HW PENDENTE** | SW/HW |
| TEST-NET-020A-038 | NET-020 | SSID/RSSI pós-boot | fallback por associação real/`iw` presente na imagem; validação física ainda necessária | **SW/estrutural PASS; HW PENDENTE** | SW/HW |
| TEST-DISPLAY-015A-038 | DISPLAY-015 | Nextion sair de estados Iniciando/Manutenção | fluxo transitório corrigido na imagem; Nextion real ainda precisa repetir boot/manutenção | **SW/estrutural PASS; HW PENDENTE** | SW/HW |

Artefato publicado: `PU2PNY-OS-0.3.8-alpha-arm64.img.xz`. SHA-256: `1997b05612159e0d1178e6ab0ab2dc73f1404a8f2a9e7e909e00dfb126557510`.

## Feedback físico 0.3.8-alpha incorporado à 0.3.9 — 2026-09-21

| ID | Requisito | Caso observado / próximo teste | Estado | Nível |
|---|---|---|---|---|
| TEST-NET-002-038 | NET-002 | AP → selecionar Wi-Fi → salvar → retornar conectado ao roteador | **PASS** no cenário testado; preservar | HW |
| TEST-NET-012-038 | NET-012 | conectar ao AP e aguardar captive portal | **FAIL** — wizard abriu somente pelo endereço manual | HW/client |
| TEST-NET-018-038 | NET-017/018 | Buscar redes para cadastrar Wi-Fi 2 | **FAIL** — retornou somente a SSID atual | HW |
| TEST-NET-019-038 | NET-019 | associação canal 44/5220 MHz + gráfico | **FAIL** — gráfico 2,4 GHz 1–13 e pouca visibilidade | HW/browser |
| TEST-UI-013-DNS-038 | UI-013 / NET-014/016 | trocar DNS e observar valor efetivo | **FAIL** — atualização visual demorou excessivamente | HW/browser |
| TEST-NET-020-038 | NET-020 | verificar atualização mantendo TX/rede ativa | **FAIL UI** — tela aparentou Wi-Fi desconectado, embora TX pela rede funcionasse | HW/browser |
| TEST-BOOT-001A-039BASE | BOOT-001 | reboot com perfil ativo salvo | **FAIL** — Wi-Fi voltou; perfil/gateway exigiu Ativar perfil manual | HW |
| TEST-PROTO-007-038 | PROTO-002/007/012 | aplicar D-Star | **FAIL de aplicação** — falso negativo da bridge UDP 20010; RF↔rede ainda pendente | HW |
| TEST-PROTO-008-038 | PROTO-003/008 | aplicar YSF | **FAIL de aplicação** — log mostrou bridge/link, mas validador fez rollback; RF↔rede ainda pendente | HW |
| TEST-DISPLAY-015-038 | DISPLAY-001/013/015 | boot/manutenção/RF/layout Nextion | **FAIL** — estados presos/100% e seleção MMDVM/2/3 sem efeito visível | HW |
| TEST-UI-018-038 | UI-018 | Estado Ao Vivo no Expert durante tráfego | **FAIL** — não acompanhou em tempo real | HW/browser |
| TEST-UI-016-038 | UI-016 | aplicar timezone pelo painel | **FAIL** — alteração não concluiu | HW/browser |
| TEST-SEC-021-038 | SEC-021 | habilitar SSH | **PENDENTE/FAIL UX** — chave informada não passou validação; retestar transporte com chave pública válida após correção | HW/browser |
| TEST-APRS-006-038 | APRS-004/006 | conexão APRS-IS | **PASS parcial** — login verificado em `soam.aprs2.net`; mensagem TX/RX/ACK continua pendente | HW/browser |
| TEST-HISTORY-038 | LIVE-012 / DATA-001 | uso da página Histórico | **PASS visual/uso** — preservar | HW/browser |
| TEST-P2P-UI-038 | UI-015 / P2P-007 | página Direct | **PASS visual** — preservar; chamada entre dois hotspots segue PENDENTE | HW/browser |
| TEST-REL-039 | REL-003 | build ARM64 0.3.9, XZ, SHA-256 e validador final | **PENDENTE** até execução do workflow | SW |

A 0.3.9 só promove os casos acima depois de nova evidência correspondente. PASS SW/CI não substitui os FAIL/PENDENTE HW.

## Resultado de release 0.3.9-alpha — 2026-09-21

| ID | Caso | Resultado | Nível |
|---|---|---|---|
| TEST-REL-039 | source + staged source + ARM64 + XZ + SHA-256 + imagem montada | **PASS** — GitHub Actions run `35569995279`, commit `0b35a555a642ced6e13150e434072415e24175b5` | SW |
| TEST-REL-039-ASSET | `PU2PNY-OS-0.3.9-alpha-arm64.img.xz` | **PASS** — SHA-256 `09ea47002f60471e3359186717370861e0090bf03c5f5fb3e2dc32456261ec71` | SW |
| TEST-HW-039 | boot restore, DMR regressão, D-Star, YSF, Nextion, Wi-Fi/DNS e UI em hardware | **PENDENTE** — exige novo teste físico | HW |

A prerelease 0.3.9-alpha está liberada somente como **HW-TEST**.


## Feedback físico 0.3.9-alpha — captive portal e fluxo posterior — 2026-09-21

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-NET-021A / NET-021 | conectar cliente ao AP `pu2pny` em imagem não provisionada | SO detecta rede cativa e oferece/abre o primeiro acesso sem digitar URL | **FAIL HW atual** — página não abriu automaticamente | HW/client |
| TEST-NET-021B / NET-021 | AP não provisionado com Ethernet/outro uplink disponível | probes continuam cativos; AP não entrega Internet transparente que mascare o wizard | PENDENTE após correção | SW/HW/client |
| TEST-NET-021C / NET-021 | abrir `http://pu2pny.local/` manualmente e seguir wizard | scan Wi-Fi automático → senha/salvar → mensagem → handoff → página reabre → hardware detectado → configuração | **PASS HW** — fluxo aprovado; preservar sem alterações | HW |

## Casos adicionados — feedback físico 0.3.9 D-Star / Hotspot

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-PROTO-002-039A | PROTO-002/007/012 | aplicar D-Star com DStarGateway ativo em UDP 20010 | parser de `ss` identifica a porta local correta, não gera rollback por falso negativo e mantém MMDVMHost + gateway ativos | HW FAIL anterior / correção SW pendente | SW/HW |
| TEST-PROTO-003-039A | PROTO-003/008 | aplicar YSF com YSFGateway ativo em UDP 4200 | mesma validação da coluna local evita falso negativo sem alterar as portas ou DMR | HW pendente | SW/HW |
| TEST-UI-024A | UI-024 / PROTO-014 | abrir /hotspot | configuração de protocolos é nativa na página, sem iframe, com layout mestre e estado operacional no mesmo contexto | PENDENTE | SW/HW/browser |
| TEST-UI-024B | UI-024 | desktop/tablet/mobile + claro/escuro | sem overflow/iframe, controles legíveis e responsivos, mesmo padrão visual da Direct | PENDENTE | SW/HW/browser |
| TEST-UI-024C | UI-008 / UI-024 | Salvar/Ativar protocolo | overlay de operação aparece imediatamente, mostra etapa real e termina em sucesso/erro acionável sem F5 | HW FAIL observado no fluxo D-Star / correção pendente | SW/HW/browser |

## Casos adicionados — Nextion / relógio / readiness D-Star 0.3.9

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-DISPLAY-016A | DISPLAY-016 | Nextion pela MMDVM + PU2PNY Moderno V2 | MMDVMHost mantém transporte MQTT/serial, renderer nativo fica desativado, Display Core fica ativo e não há dois writers | PENDENTE | SW/HW |
| TEST-DISPLAY-016B | DISPLAY-016 | escolher G4KLX/ON7LDS | Display Core para; MMDVMHost assume Nextion em Port=modem e confirma ScreenLayout efetivo | PENDENTE | SW/HW |
| TEST-DISPLAY-016C | DISPLAY-016 | selecionar modelo/resolução | painel oferece 2,4/2,8/3,2/3,5/4,3/5/7/10,1 e persiste o perfil sem declarar detecção HW falsa | PENDENTE | SW/HW |
| TEST-DISPLAY-016D | DISPLAY-016 / DISPLAY-015 | standby/TX/RX | Nextion volta a exibir estado operacional e sai de telas transitórias; Moderno V2 mostra hierarquia profissional quando renderer próprio estiver selecionado | HW FAIL atual / correção pendente | SW/HW |
| TEST-UI-017D | UI-017 / UI-016 | mudar timezone e observar cabeçalho | relógio ressincroniza com /api/system imediatamente, permanece em uma linha e não usa somente timezone do navegador | HW FAIL reportado / correção pendente | SW/HW/browser |
| TEST-PROTO-015A | PROTO-015 | apply D-Star | confirma Enable/GatewayPort/LocalPort, MMDVMHost sobe antes do gateway e aguarda bridge local com timeout limitado | PENDENTE | SW/HW |
| TEST-PROTO-015B | PROTO-015 | bridge não aparece de verdade | rollback restaura configuração/serviços anteriores e apresenta diagnóstico útil | PENDENTE | SW/HW |

| TEST-DISPLAY-017A | DISPLAY-017 | boot com Nextion direta | `connect/comok` identifica model/baud sem gravar HMI, resultado persiste e painel recebe estado | PENDENTE | SW/HW |
| TEST-DISPLAY-017B | DISPLAY-017 | MMDVMHost ativo + Nextion via MMDVM | detector não abre/rouba a serial do modem; reutiliza prova confirmada ou mantém candidato | PENDENTE | SW/HW |
| TEST-DISPLAY-017C | DISPLAY-017 | OLED em 0x3C/0x3D sem metadata | sistema registra SSD1306/SH1106 candidato, sem inventar controlador | PENDENTE | SW/HW |
| TEST-DISPLAY-017D | DISPLAY-017 | OLED com metadata kernel/DT | controlador e resolução são promovidos a confirmados | PENDENTE | SW/HW |
| TEST-DISPLAY-017E | DISPLAY-017 | hotplug tty/DRM/input | evento dispara oneshot de detecção sem polling contínuo e sem reiniciar RF | PENDENTE | SW/HW |
| TEST-DISPLAY-017F | DISPLAY-017 | catálogo TFT sem URL/SHA | provisionamento permanece `asset_unpublished`; nenhuma gravação é oferecida | PENDENTE | SW |
| TEST-DISPLAY-017G | DISPLAY-017 | tentativa de flash sem confirmação | operação é rejeitada; nenhum byte TFT é enviado | PENDENTE | SW/HW |

## Hardening priorizado — casos 0.3.9

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-PROTO-016A | PROTO-016 | gateway demora alguns segundos para abrir UDP | estado fica waiting_bridge, tenta de forma limitada e só então aprova/reverte | PENDENTE SW/HW |
| TEST-PROTO-016B | PROTO-016 | bridge nunca aparece | rollback + last_rollback_reason + evidência da porta/tentativas | PENDENTE SW/HW |
| TEST-BOOT-002A | BOOT-002 | reboot com perfil D-Star/YSF | serial→MQTT→MMDVMHost→gateway→health convergem sem clique manual | PENDENTE HW |
| TEST-BOOT-002B | BOOT-002 | dependência não fica pronta | painel/rede continuam; restore falha explicitamente, sem sucesso falso | PENDENTE SW/HW |
| TEST-PROTO-017A | PROTO-017 | MQTT 127.0.0.1:1883 indisponível | aplicação bloqueia antes do gateway e mostra diagnóstico amigável | PENDENTE SW/HW |
| TEST-NET-022A | NET-022 | handoff AP→Wi-Fi | só declara conectado após associação+IPv4+rota+DNS; onboarding aprovado permanece igual | PENDENTE HW |
| TEST-UPDATE-006A | UPDATE-006 | artefato SHA inválido | recusa aplicação e mantém versão anterior | PENDENTE SW |
| TEST-LIVE-015A | LIVE-015 | TX/RX | web e display usam os mesmos campos/evento sem divergência inventada | PENDENTE HW |
| TEST-UI-025A | UI-025 | abrir Expert | mostra UDP/MQTT/writer/restore/rollback/Wi-Fi com valores reais ou — | PENDENTE SW/HW |
| TEST-SEC-022A | SEC-022 | revisar endpoints privilegiados | cada ação usa unit/helper dedicado; nenhum sudo/root genérico no web daemon | PENDENTE SW |

## Release 0.3.10-alpha

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-REL-0310-A | REL-003/004 | source/staged source | Go/Python/Bash/JS e gates 0.3.10 passam | PENDENTE CI |
| TEST-REL-0310-B | REL-003/004 | build ARM64 | imagem ARM64 é gerada sem remover baseline | PENDENTE CI |
| TEST-REL-0310-C | REL-003/004 | XZ + SHA-256 | xz -t e checksum são confirmados | PENDENTE CI |
| TEST-REL-0310-D | REL-003/004 | validar imagem montada | captive, DMR baseline, Hotspot sem iframe, Nextion, bridge, MQTT, boot e APIs estruturais passam | PENDENTE CI |
| TEST-REL-0310-E | REL-004 | teste físico | AP popup, onboarding, DMR, D-Star, YSF, reboot restore e Nextion Moderno V2 | PENDENTE HW |

### Resultado final 0.3.10-alpha — run 35600972295

| ID | Resultado |
|---|---|
| TEST-REL-0310-A | SW PASS — source/staged source |
| TEST-REL-0310-B | SW PASS — ARM64 |
| TEST-REL-0310-C | SW PASS — XZ + SHA-256 |
| TEST-REL-0310-D | SW PASS — validador final da imagem |
| TEST-REL-0310-E | PENDENTE HW — Raspberry Pi + MMDVM/display |
| TEST-HW-004 | MMDVM detectada sem ativação RF na etapa Hardware | HW | iniciar detecção com MMDVM real | handshake confirma porta/baud; etapa Hardware não inicia MMDVMHost nem disputa UART com display | PENDENTE |
| TEST-WIZ-010 | avanço automático após MMDVM confirmada | HW | concluir detecção real | mensagem anterior é limpa; botão habilita; contagem 5 s; avança para Configuração | PENDENTE |
| TEST-RF-016 | ativar MMDVMHost após detecção | HW | salvar RF/perfil com MMDVM detectada | usa porta/baud detectados, preflight MQTT, lock contra display, serviço permanece ativo; falha faz rollback com causa real | PENDENTE |
| TEST-I18N-002 | idioma integral em mensagens dinâmicas/erros | SW/HW | selecionar PT/EN/ES e disparar status/erros conhecidos | nenhuma mensagem normal aparece em idioma diferente do selecionado; logs brutos só em diagnóstico técnico | PENDENTE |

## Casos corretivos 0.3.12-alpha — 2026-09-21

| ID | Requisito | Caso | Resultado esperado | Estado inicial | Nível |
|---|---|---|---|---|---|
| TEST-RF-017A | RF-017 | detector e RF apply concorrentes | ambos usam /run/2pny/mmdvm-serial.lock; MMDVMHost só assume a UART após o detector liberar | PENDENTE CI/HW | SW/HW |
| TEST-PROTO-018A | PROTO-018 | inspecionar imagem final | /usr/sbin/mosquitto existe e listener PU2PNY está restrito a 127.0.0.1:1883 | PENDENTE CI | SW |
| TEST-PROTO-018B | PROTO-018 | broker simulado aceita/rejeita CONNECT | preflight só retorna PASS após CONNACK=0 e rejeita CONNACK de erro | PENDENTE CI | SW |
| TEST-WIZ-011 | RF-016/WIZ-006 | Salvar e continuar após MMDVM real detectada | MMDVMHost fica ativo, /api/rf chega a applied e wizard abre Conclusão sem clique repetido | PENDENTE HW | HW |
| TEST-I18N-003 | UI-026/UI-027 | repetir onboarding em PT/EN/ES | fora do seletor inicial não há frase operacional em idioma diferente; siglas/protocolos são exceção | PENDENTE SW/HW | SW/HW |
| TEST-REL-0312-A | REL-005 | source + regressões | sintaxe, handshake MQTT simulado, locks e traduções passam | PENDENTE CI | SW |
| TEST-REL-0312-B | REL-005 | build ARM64 | imagem ARM64 gerada preservando baseline | PENDENTE CI | SW |
| TEST-REL-0312-C | REL-005 | XZ + SHA-256 | arquivo compactado íntegro e checksum gerado | PENDENTE CI | SW |
| TEST-REL-0312-D | REL-005 | imagem montada | broker, config MQTT, MMDVM lock, wizard/i18n e baselines herdadas presentes | PENDENTE CI | SW |
| TEST-REL-0312-E | REL-005 | Raspberry Pi + MMDVM + display | onboarding, MMDVMHost, DMR regressão, reboot e Nextion | PENDENTE | HW |
## Feedback físico 0.3.12-alpha — lote 1 — 2026-09-21

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-NET-021C-0312 | NET-002/NET-021/NET-022 | onboarding da 0.3.12 após seleção da rede | Wi-Fi reconhecido, conexão automática confirmada e painel aberto automaticamente | **PASS HW — baseline congelada** | HW |
| TEST-WIZ-011 | RF-016/WIZ-006 | Salvar e continuar com MMDVM real detectada | MMDVMHost fica ativo, /api/rf chega a applied e wizard conclui | **FAIL HW — bloqueia no módulo MMDVM** | HW |
| TEST-I18N-003 | UI-026/UI-027 | operar a 0.3.12 em Português | nenhuma mensagem normal em Inglês fora do seletor inicial | **FAIL HW — mistura PT/EN observada** | HW/browser |
| TEST-RF-018A | RF-018 | bootstrap mínimo com MMDVM real detectada | com redes/protocolos desativados e sem MQTT/display como pré-condição do bootstrap, MMDVMHost assume a UART e permanece ativo | PENDENTE correção/HW | SW/HW |
| TEST-RF-018B | RF-018/PROTO-018 | ativar Fase B após bootstrap PASS | MQTT/display/protocolo são aplicados transacionalmente; falha identifica a dependência e faz rollback sem acusar baud/MMDVM sem evidência | PENDENTE correção/HW | SW/HW |
| TEST-PROTO-019A | PROTO-019 | TGIF com Security Key fornecida | chave chega intacta ao DMRGateway sem aparecer em logs/UI; configuração segura não cai silenciosamente para legado | PENDENTE correção/SW/HW | SW/HW |
| TEST-PROTO-019B | PROTO-019 | TGIF + ESSID 01..99 | Network ID efetivo e ESSID seguem a regra DMR e a mesma Security Key é usada | PENDENTE correção/SW/HW | SW/HW |
| TEST-PROTO-019C | PROTO-019 | transmitir HT após gateway TGIF ativo | RF local, gateway local e evidência de rede são estados separados; só declarar conectado/entregue com evidência do master | **FAIL HW atual / causa não isolada** | HW |
| TEST-I18N-004 | UI-028 | PT/EN/ES com mensagens estáticas, dinâmicas e erros | toda mensagem usa chave estável e nasce no idioma selecionado; bruto somente no Expert | PENDENTE correção/SW/HW | SW/HW |

## Casos corretivos 0.3.13-alpha — 2026-09-21

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-RF-018C | RF-018 | service MMDVMHost executa preflight como usuário `mmdvm` durante bootstrap | com MQTTLevel=0 o preflight não exige broker nem tenta persistir diagnóstico; MMDVMHost pode provar UART | PENDENTE CI/HW | SW/HW |
| TEST-RF-018D | RF-018/PROTO-018 | bootstrap UART passa e MQTT falha depois | diagnóstico identifica MQTT, rollback restaura estado anterior e não acusa baud/MMDVM | PENDENTE CI/HW | SW/HW |
| TEST-PROTO-019D | PROTO-019 | gerar perfil TGIF com Security Key | TGRewrite/SrcRewrite do DMRGateway embarcado são gerados, chave permanece somente no arquivo privado e estado público registra apenas modo de autenticação | PENDENTE CI/HW | SW/HW |
| TEST-I18N-005 | UI-028 | abrir wizard em PT/EN/ES | fora do seletor inicial, conteúdo operacional só aparece depois de aplicar o idioma e não mistura rótulos conhecidos | PENDENTE CI/HW | SW/HW |
| TEST-NET-0313-REG | NET-002/NET-021/NET-022 | regressão do onboarding aprovado | overlay 0.3.13 não substitui helpers Wi-Fi; comportamento aprovado da 0.3.12 é preservado | PENDENTE CI / baseline HW 0.3.12 | SW/HW |
| TEST-REL-0313-A | REL-006 | source + regressões | Go/Python/Bash/JS e testes 0.3.13 passam junto com regressões herdadas | PENDENTE CI | SW |
| TEST-REL-0313-B | REL-006 | build ARM64 | imagem ARM64 é gerada com overlay 0.3.13 após toda cadeia herdada | PENDENTE CI | SW |
| TEST-REL-0313-C | REL-006 | XZ + SHA-256 | arquivo compactado passa `xz -t` e checksum é confirmado | PENDENTE CI | SW |
| TEST-REL-0313-D | REL-006 | imagem montada | MMDVM bootstrap, MQTT, TGIF, i18n e baselines herdadas são comprovados estruturalmente | PENDENTE CI | SW |
| TEST-REL-0313-E | REL-006 | Raspberry Pi + MMDVM | Wi-Fi regressão, avanço MMDVM, TGIF login/TX-RX e idioma integral | PENDENTE | HW |

## Identidade visual oficial

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-UI-029A | UI-029 | exibir logotipo oficial em telas suportadas | proporção preservada, contraste adequado e nenhuma distorção/corte indevido | PENDENTE próximo ciclo | SW/HW |
| TEST-UI-029B | UI-029/PERF-* | medir impacto do asset | sem regressão perceptível de carregamento, CPU/RAM ou escrita em SD | PENDENTE próximo ciclo | SW/HW |
| TEST-UI-029C | UI-029/DISPLAY-* | adaptar identidade para displays menores | usa derivação legível do mesmo logotipo sem prejudicar dados operacionais | PENDENTE próximo ciclo | SW/HW |

### Resultado final 0.3.13-alpha — run 35631645881

| ID | Resultado |
|---|---|
| TEST-RF-018C | SW PASS estrutural/fonte — service respeita bootstrap sem persistência não privilegiada; HW PENDENTE |
| TEST-RF-018D | SW PASS estrutural/fonte — fases UART/MQTT e causas separadas; HW PENDENTE |
| TEST-PROTO-019D | SW PASS estrutural/fonte — template TGIF, rewrites e segredo fora do estado público; HW PENDENTE |
| TEST-I18N-005 | SW PASS estrutural/fonte — catálogo exato e bloqueio de exibição antes do idioma; HW PENDENTE |
| TEST-NET-0313-REG | SW PASS — overlay 0.3.13 não substitui helpers Wi-Fi; baseline HW 0.3.12 preservada |
| TEST-REL-0313-A | **SW PASS** — source + regressões |
| TEST-REL-0313-B | **SW PASS** — imagem ARM64 |
| TEST-REL-0313-C | **SW PASS** — XZ + SHA-256 |
| TEST-REL-0313-D | **SW PASS** — validação estrutural da imagem |
| TEST-REL-0313-E | PENDENTE HW — Raspberry Pi + MMDVM/TGIF/i18n |

## Feedback físico 0.3.13-alpha e casos 0.3.14 — 2026-09-21

| ID | Requisito | Caso | Resultado esperado | Estado atual | Nível |
|---|---|---|---|---|---|
| TEST-RF-018A-0313 | RF-018 | bootstrap mínimo da MMDVM na 0.3.13 | MMDVMHost assume UART sem MQTT/display como pré-condição | **PASS HW** | HW |
| TEST-PROTO-020A | PROTO-020 | iniciar broker local após bootstrap | unidade PU2PNY/Mosquitto fica active e listener 127.0.0.1:1883 aparece dentro do teto | PENDENTE 0.3.14 | SW/HW |
| TEST-PROTO-020B | PROTO-020 | handshake MQTT real após start | CONNECT recebe CONNACK=0; retries/backoff são limitados | PENDENTE 0.3.14 | SW/HW |
| TEST-PROTO-020C | PROTO-020 | broker falha ao iniciar | diagnóstico diferencia service_start/service_failed/handshake_timeout sem atribuir à MMDVM | PENDENTE 0.3.14 | SW/HW |
| TEST-WIZ-007A | WIZ-007 | erro MQTT durante Salvar e continuar | wizard permanece na etapa 3, campos atuais permanecem, botão é reabilitado | **FAIL HW na 0.3.13 / PENDENTE correção** | HW |
| TEST-WIZ-007B | WIZ-007 | recarregar página após apply falho e ainda não provisionado | abre Configuração Básica; senha não é persistida no browser | PENDENTE 0.3.14 | SW/HW |
| TEST-REL-0314-A | REL-007 | source + regressões | novos testes e herdados passam | PENDENTE CI | SW |
| TEST-REL-0314-B | REL-007 | build ARM64 | imagem gerada preservando baselines | PENDENTE CI | SW |
| TEST-REL-0314-C | REL-007 | XZ + SHA-256 | integridade confirmada | PENDENTE CI | SW |
| TEST-REL-0314-D | REL-007 | imagem montada | broker/unit/readiness/wizard + baselines presentes | PENDENTE CI | SW |
| TEST-REL-0314-E | REL-007 | Raspberry Pi + MMDVM | Fase A continua PASS, MQTT Fase B passa e wizard avança somente após applied | PENDENTE | HW |

## Casos 0.3.15-alpha — correção focal MQTT/onboarding DMR

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-RF-021A | PROTO-021 | RF apply após MMDVM bootstrap | retorna RF_APPLY_OK com MQTTLevel=0; não chama preflight/broker nem habilita MQTT | PENDENTE CI/HW |
| TEST-DMR-021B | PROTO-021 | dispatcher recebe DMR | delega diretamente ao 2pny-dmr-apply sem preflight MQTT | PENDENTE CI/HW |
| TEST-DMR-021C | PROTO-021 | helper DMR efetivo | MMDVMHost/DMRGateway usam MQTTLevel=0 e continuam validando ambos os serviços | PENDENTE CI/HW |
| TEST-WIZ-008A | WIZ-008 | backend conclui RF+DMR | grava provisioned, publica state=applied e wizard executa step(4) | PENDENTE CI/HW |
| TEST-REL-0315-A | REL-008 | regressões/source | 0.3.14 herdado + testes focais 0.3.15 passam | PENDENTE CI |
| TEST-REL-0315-B | REL-008 | build ARM64/XZ/SHA | imagem e checksum válidos | PENDENTE CI |
| TEST-REL-0315-C | REL-008 | imagem montada | RF/DMR sem gate MQTT e baselines herdadas presentes | PENDENTE CI |
| TEST-REL-0315-D | REL-008 | Raspberry Pi + MMDVM + DMR | Configuração Básica avança para Conclusão sem depender do broker MQTT | PENDENTE HW |

### Resultado final 0.3.15-alpha — run 35647296002

| ID | Resultado |
|---|---|
| TEST-RF-021A | **SW PASS** — RF apply termina no bootstrap MMDVM com MQTTLevel=0 e sem gate MQTT |
| TEST-DMR-021B | **SW PASS** — dispatcher DMR delega diretamente ao helper |
| TEST-DMR-021C | **SW PASS** — helper DMR mantém MQTTLevel=0 e valida MMDVMHost + DMRGateway |
| TEST-WIZ-008A | **SW PASS estrutural** — fluxo backend grava provisioned/state=applied e wizard mantém step(4); **HW PENDENTE** |
| TEST-REL-0315-A | **SW PASS** |
| TEST-REL-0315-B | **SW PASS** |
| TEST-REL-0315-C | **SW PASS** |
| TEST-REL-0315-D | **PENDENTE HW** — Raspberry Pi + MMDVM + DMR |

## Casos 0.3.16-alpha — lote HW de bugs

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-NET-023A | NET-023 | salvar Wi-Fi e reiniciar | perfil persistido/autoconnect e reconexão automática | SW PASS estrutural / HW PENDENTE |
| TEST-NET-023B | NET-023 | conectar/desconectar Ethernet | API/UI convergem em poucos segundos | SW PASS estrutural / HW PENDENTE |
| TEST-NET-024A | NET-024 | scan para Wi-Fi 1/2 após erro anterior | nova busca real e ambos seletores populados | SW PASS estrutural / HW PENDENTE |
| TEST-LIVE-016A | LIVE-016 | standby/network RX sem RF | BER/RSSI/Sinal RF ocultos | SW PASS determinístico / HW PENDENTE |
| TEST-UI-030A | UI-030 | ativar perfil | overlay persiste até connected, erro ou timeout diagnosticável | SW PASS estrutural / HW PENDENTE |
| TEST-PROTO-022A | PROTO-022 | anúncio XLX + chegada NETWORK simultânea | voz de sistema não mistura no mesmo slot | SW PASS build/estrutural / HW PENDENTE |
| TEST-P2P-006A | P2P-006 | Direct/Relay com peer pareado | registro/lookup/probes com janela robusta; segurança preservada | SW PASS estrutural/selftest / HW PENDENTE |
| TEST-APRS-012A | APRS-012 | página APRS em instalação provisionada | APRS-IS inicia automaticamente para mensagens | SW PASS estrutural / HW PENDENTE |
| TEST-APRS-012B | APRS-012 | regional indisponível | fallback limitado para rotate.aprs2.net:14580 | SW PASS determinístico / HW PENDENTE |
| TEST-APRS-012C | APRS-012 | mensagem sem ACK | waiting_ack/retry/no_ack sem afirmar entrega | SW PASS determinístico / HW PENDENTE |
| TEST-DISPLAY-018A | DISPLAY-018 | Nextion via modem | MMDVMHost writer, Port=modem, layout 2/3, sem MQTT obrigatório | SW PASS estrutural / HW PENDENTE |
| TEST-SEC-023A | SEC-023 | aplicar America/Sao_Paulo | helper dispara, consome request e confirma fuso | SW PASS estrutural / HW PENDENTE |
| TEST-SEC-023B | SEC-023/UI-031 | habilitar SSH com .pub válida | authorized_keys aplicado; root/senha continuam bloqueados | SW PASS estrutural / HW PENDENTE |
| TEST-PROTO-023A | PROTO-023 | gerar D-Star | schema do gateway embarcado, ReloadTimer, custom host e loopback corretos | SW PASS estrutural / HW PENDENTE |
| TEST-PROTO-023B | PROTO-023 | ativar D-Star | não declara conectado sem evidência de link remoto | PENDENTE HW |
| TEST-REL-0316-A | REL-009 | regressões + source | baselines herdadas + testes focais passam | **SW PASS** |
| TEST-REL-0316-B | REL-009 | build ARM64/XZ/SHA | artefato íntegro | **SW PASS** |
| TEST-REL-0316-C | REL-009 | imagem montada | componentes focais e baselines estruturais presentes | **SW PASS** |
| TEST-REL-0316-D | REL-009 | Raspberry Pi/MMDVM/Nextion | validação física do lote | PENDENTE HW |


**Evidência de release 0.3.16:** GitHub Actions run `35669972163`, commit da imagem `1c5ec75548374ac13be6948fc86eae46bd9eeddf`, artefato ARM64/XZ e validação final em PASS. `TEST-REL-0316-D` e todos os estados HW continuam pendentes.

## Casos 0.3.17-alpha — D-Star RX/comandos e timezone

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-PROTO-024A | PROTO-024 | aplicar D-Star com refletor remoto módulo D | MMDVMHost permanece local `Module=C`; gateway `Band=C`; refletor remoto termina em `D` | PENDENTE SW/HW |
| TEST-PROTO-024B | PROTO-024 | tráfego D-Star recebido do refletor | DStarGateway entrega UDP ao MMDVMHost:20011 e MMDVM transmite RF | PENDENTE HW |
| TEST-PROTO-024C | PROTO-024 | DR/URCALL `_______I` | gateway responde com status/info por RF | PENDENTE HW |
| TEST-PROTO-024D | PROTO-024 | DR/URCALL `_______E` | echo local retorna ao rádio | PENDENTE HW |
| TEST-PROTO-024E | PROTO-024 | DR/URCALL `_______U`, `_______L` | unlink/link default funcionam e status é anunciado | PENDENTE HW |
| TEST-PROTO-024F | PROTO-024 | comando `XLXnnn<mod>L` | troca refletor/módulo remoto sem mudar módulo local C | PENDENTE HW |
| TEST-LIVE-017A | LIVE-017 | chamada D-Star NETWORK→RF | Ao Vivo mostra D-Star/Internet→RF enquanto o modem transmite; sem RSSI/BER inventados | PENDENTE SW/HW |
| TEST-UI-032A | UI-032 | painel D-Star | estado/link e ajuda de comandos aparecem sem declarar conexão falsa | PENDENTE SW/HW |
| TEST-SEC-024A | SEC-024 | aplicar `America/Sao_Paulo` | helper aplica, confirma Timezone e UI atualiza sem terminal | PENDENTE SW/HW |
| TEST-SEC-024B | SEC-024 | timezone inválido/falha helper | mantém zona anterior e devolve causa real | PENDENTE SW/HW |
| TEST-REL-0317-A | REL-010 | regressões/source | baseline 0.3.16 + testes focais passam | PENDENTE CI |
| TEST-REL-0317-B | REL-010 | build ARM64/XZ/SHA | artefato íntegro | PENDENTE CI |
| TEST-REL-0317-C | REL-010 | imagem montada | D-Star local C/comandos/timezone + baselines presentes | PENDENTE CI |
| TEST-REL-0317-D | REL-010 | Raspberry Pi + MMDVM | validação física D-Star e timezone | PENDENTE HW |

## Casos adicionais 0.3.18-alpha

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-PROTO-024G | PROTO-024 | gerar DStarGateway.ini | `[Paths] Data=/usr/local/share/dstargateway.d/` | PENDENTE CI |
| TEST-PROTO-024H | PROTO-024 | imagem ARM64 montada | `en_GB.ambe` e `en_GB.indx` existem no diretório configurado | PENDENTE CI |
| TEST-REL-0318-A | REL-011 | source/regressões 0.3.16/0.3.17 + correção áudio | todos passam | PENDENTE CI |
| TEST-REL-0318-B | REL-011 | ARM64/XZ/SHA-256 | artefato íntegro | PENDENTE CI |
| TEST-REL-0318-C | REL-011 | imagem montada | D-Star/voz/timezone + baseline congelada presentes | PENDENTE CI |
| TEST-REL-0318-D | REL-011 | Raspberry Pi + MMDVM | D-Star rede→RF, I/E/U/L/link, Hotspot e timezone | PENDENTE HW |

## Casos SEC-025 adicionados à 0.3.18-alpha

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-SEC-025A | SEC-025 | `PNYARM` por MYCALL configurado | abre janela one-shot de 30 s e registra origem | PENDENTE SW/HW |
| TEST-SEC-025B | SEC-025 | `PNYRBT`/`PNYOFF` sem armamento | recusa; nenhum reboot/poweroff | PENDENTE SW/HW |
| TEST-SEC-025C | SEC-025 | `PNYRBT` após `PNYARM` | agenda reinício seguro, consome armamento | PENDENTE SW/HW |
| TEST-SEC-025D | SEC-025 | `PNYOFF` após `PNYARM` | agenda shutdown seguro, consome armamento | PENDENTE SW/HW |
| TEST-SEC-025E | SEC-025 | comando de perfil após armamento | ativa somente perfil salvo/validado correspondente | PENDENTE SW/HW |
| TEST-SEC-025F | SEC-025 | MYCALL diferente do callsign configurado | recusa sem ação privilegiada | PENDENTE SW/HW |
| TEST-REL-0318-E | REL-012 | imagem montada | helper/path unit presentes e dstargateway contém handler SEC-025 compilado | PENDENTE CI |


## Casos 0.3.19-alpha — manutenção focal

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-NET-025A | NET-025 | aplicar DNS com perfil contendo autoconnect-retries | não usa device reapply; perfil é reativado e DNS efetivo é verificado | PENDENTE CI/HW |
| TEST-NET-026A | NET-026 | abrir Internet com Wi-Fi conectado + redes próximas | Wi-Fi 1 = atual; Wi-Fi 2 = alternativas; atual/melhor canal identificados | PENDENTE CI/HW |
| TEST-LIVE-018A | LIVE-018 | standby | Slot/CC/RSSI/Sinal transitórios ficam invisíveis | PENDENTE CI/HW |
| TEST-LIVE-018B | LIVE-018 | RF TX contínuo | TOT visível regride 180→0 no Ao Vivo e Sistema | PENDENTE CI/HW |
| TEST-UI-033A | UI-033 | digitar 438,800 ou 438.800 | normaliza/exibe 438.800000 sem alterar intenção | PENDENTE CI/HW |
| TEST-UI-033B | UI-033 | salvar perfil | mostra Salvando e depois Atualizando | PENDENTE CI/HW |
| TEST-PROTO-025A | PROTO-025 | D-Star remoto D configurado mas não confirmado | módulo remoto não é mostrado como conectado | PENDENTE CI/HW |
| TEST-PROTO-025B | PROTO-025 | gateway confirma link D | Ao Vivo/Protocolos mostram módulo remoto D; local continua C | PENDENTE CI/HW |
| TEST-PROTO-025C | PROTO-025 | RF D-Star com header não-repeater/RPT1 errado | MMDVM rejeita e Expert expõe diagnóstico sem alterar RF | PENDENTE CI/HW |
| TEST-PROTO-025D | PROTO-025 | DR I/E/U/L e link XLX/REF | comandos chegam ao gateway e módulo local permanece C | PENDENTE HW |
| TEST-PROTO-026A | PROTO-026 | abrir ajuda DMR/YSF/P25/NXDN/POCSAG | mecanismo real aparece sem comando universal inventado | PENDENTE CI |
| TEST-APRS-013A | APRS-013 | nova mensagem estando fora de /aprs | balão interno aparece ~5 s e clique abre APRS | PENDENTE CI/HW navegador |
| TEST-APRS-013B | APRS-013 | Notification em HTTP não seguro | UI não declara permissão nativa; alerta interno continua | PENDENTE CI/HW navegador |
| TEST-DISPLAY-019A | DISPLAY-019 | network-online | detector roda uma vez, limitado/debounced, sem flash TFT | PENDENTE CI/HW |
| TEST-DISPLAY-019B | DISPLAY-019 | Nextion compatível | inicialização 0–100, indicativo/nome e TOT RF TX aparecem | PENDENTE HW |
| TEST-SEC-026A | SEC-026 | dois requests de timezone pendentes | helper drena ambos e produz resultados correspondentes | PENDENTE CI/HW |
| TEST-SEC-027A | SEC-027 | gerar chave no navegador | privada fica local; apenas pública vai para authorized_keys | PENDENTE CI/HW navegador |
| TEST-DATA-002A | DATA-002 | atualizar/baixar erros | leitura sob demanda, redaction e download funcionam sem polling | PENDENTE CI/HW |
| TEST-UI-034A | UI-034 | instalação sem voice-settings | avisos e horário iniciam ativos | PENDENTE CI/HW |
| TEST-UI-034B | UI-034 | upgrade com preferência de voz existente | preferência existente é preservada | PENDENTE CI/HW |
| TEST-REL-0319-A | REL-013 | source/regressões | baseline 0.3.18 + gates 0.3.19 passam | PENDENTE CI |
| TEST-REL-0319-B | REL-013 | ARM64/XZ/SHA-256 | artefato íntegro | PENDENTE CI |
| TEST-REL-0319-C | REL-013 | imagem montada | overlay 0.3.19 e baselines estruturais presentes | PENDENTE CI |
| TEST-REL-0319-D | REL-013 | Raspberry Pi + MMDVM + Nextion/rede real | validação física completa do lote | PENDENTE HW |


## Casos adicionais 0.3.19-alpha — YSF/C4FM e duplex

| ID | Requisito | Caso | Resultado esperado | Estado |
|---|---|---|---|---|
| TEST-PROTO-027A | PROTO-027 | selecionar YSF por nome/address/port | `Startup` corresponde a nome existente/resolvido no JSON efetivo | PENDENTE CI/HW |
| TEST-PROTO-027B | PROTO-027 | gateway local ativo sem poll remoto | estado permanece aguardando; não declara conectado | PENDENTE CI/HW |
| TEST-PROTO-027C | PROTO-027 | YSFGateway recebe poll do refletor | log/runtime confirma `Linked to ...` e conexão remota | PENDENTE HW |
| TEST-RF-019A | RF-019 | aplicar modo repetidora em D-Star/DMR/YSF/P25/NXDN/POCSAG | `General.Duplex=1`, RX/TX preservados e MMDVMHost ativo | PENDENTE CI/HW |
| TEST-RF-019B | RF-019 | ativar perfil salvo simplex↔duplex | estado efetivo de Duplex acompanha `use_mode` sem mudar baud/offsets | PENDENTE CI/HW |
| TEST-LIVE-019A | LIVE-019 | Ao Vivo em duplex | mostra `RX ... MHz · TX ... MHz`, seis casas | PENDENTE CI/HW |
| TEST-PROTO-028A | PROTO-028 | DMR duplex aplicar rede | MMDVMHost e DMRGateway local ficam com TS1=1/TS2=1 e Duplex=1 | PENDENTE CI/HW |
| TEST-PROTO-028B | PROTO-028 | DMR duplex BrandMeister/TGIF | pass-through cobre TS1 e TS2; RF→rede e rede→RF funcionam | PENDENTE HW |
| TEST-PROTO-028C | PROTO-028 | DMR duplex XLX | transporte local TS1/TS2 ativo; XLX mantém apenas slot de rede escolhido | PENDENTE CI/HW |
| TEST-REL-0319-E | REL-014 | regressão DMR simplex + YSF + duplex | DMR simplex baseline preservada e novo lote passa gates SW antes de imagem | PENDENTE CI |
