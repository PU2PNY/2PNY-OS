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
| TEST-PROTO-007 / PROTO-007 | XLX: trocar TG suportado e falar | link muda e áudio RF→XLX passa; TG6 continua funcionando | FAIL atual | HW |
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
