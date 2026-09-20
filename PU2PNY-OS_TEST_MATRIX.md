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
| TEST-SW-034-001 | prepare 0.3.4 | overlay aplica e todos os scripts passam sintaxe/compile | PENDENTE | SW |
| TEST-SW-034-002 | Wi-Fi staged/boot | persistência de segredo, associação real e IPv4 antes de sucesso | PENDENTE | SW |
| TEST-SW-034-003 | MQTT preflight/rollback | preflight presente + MMDVMHost restaurado deterministicamente | PENDENTE | SW |
| TEST-SW-034-004 | Ao Vivo | expansão persistente, métricas condicionais, alerta RF 180 s | PENDENTE | SW |
| TEST-SW-034-005 | UI/Expert/APRS | idioma inicial, rodapé versão, JSON recolhido, alerta APRS interno | PENDENTE | SW |
| TEST-SW-034-006 | Nextion overlay | sem limpeza total repetitiva, estado/uplink/IP preservando OLED/LCD | PENDENTE | SW |
| TEST-SW-034-007 | imagem ARM64 | xz íntegro, SHA-256, montagem e APIs 0.3.4 | PENDENTE | SW |

**Regra:** PASS nesses casos permite distribuir somente uma **imagem alpha para teste**. Não converte TEST-NET/PROTO/DISPLAY de HW para PASS.
