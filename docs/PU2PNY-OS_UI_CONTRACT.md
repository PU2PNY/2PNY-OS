# PU2PNY-OS 5.x — UI Contract

Status: canônico para a geração 5.x. Este contrato preserva a experiência e as funções já aprovadas enquanto o backend é reestruturado.

## Princípios
- A arquitetura 5.x pode substituir backend/runtime sem remover silenciosamente funções do painel.
- Função ainda não implementável permanece visível na especificação como PENDENTE; não desaparece por conveniência.
- Estado exibido deve refletir runtime real. Sem evidência: `—`/não verificado.
- PT/EN/ES não podem ser misturados.
- Display e Helix permanecem dentro da navegação principal.
- Operação normal não exige terminal.

## Navegação preservada
1. Ao Vivo
2. Internet
3. Protocolos
4. APRS/DPRS
5. Direct/P2P
6. Histórico
7. Display
8. Helix
9. Sistema
10. Expert/Diagnóstico
11. Update
12. Backup/Recovery

## Ao Vivo
Exibir somente quando disponível: protocolo, direção, origem RF/NET, indicativo, nome, Radio ID, destino/TG/refletor, slot, CC, módulo, servidor, duração, BER, RSSI, foto, cidade e horário. Manter histórico/atividade recente sem fechar controles durante atualizações.

## Internet
Exibir estado real de AP, Wi‑Fi e Ethernet; SSID, sinal/dBm, IPv4, gateway, DNS, canal/banda quando disponíveis. Permitir duas redes salvas, prioridade/failover, troca transacional e diagnóstico sob demanda. `pu2pny.local` deve permanecer o acesso principal em AP/STA/Ethernet.

## Protocolos
Configuração por protocolo sem reexecutar wizard. DMR, D-Star, YSF/C4FM, P25, NXDN e POCSAG/DAPNET aparecem conforme disponibilidade/estado. Mudanças devem passar por manager único, preflight, health-check e rollback.

## APRS/DPRS
Mensagens, inbox/outbox, histórico, notificações internas e APRS-IS opcional. Localização não é obrigatória nem rastreamento padrão.

## Direct/P2P
Chamada por indicativo/ID, estado de conexão, aceite e retorno automático ao estado anterior. CGNAT/relay quando necessário.

## Histórico
Tabela coerente com Ao Vivo, filtros e dados reais. Links externos somente quando válidos.

## Display
Configuração integrada para Nextion/OLED/HD44780/LCDproc/TFT quando suportados. Nunca auto-flash de HMI/TFT. Mostrar detecção/estado real.

## Helix
Página integrada com explicação de OFF/SHADOW/PROCESS, impacto, dependências e limitações. Não alegar AMBE/cross-mode real sem backend comprovado.

## Sistema/Expert
Versão real, arquitetura, uptime, temperatura/throttling quando disponível, serviços e diagnóstico. Logs/JSON técnicos em área expansível, sem segredos.

## Update
Versão atual, versão disponível, arquitetura, checksum, backup opcional, progresso real, rollback/downgrade explícito. Nunca percentual fictício.

## Backup/Recovery
Backup/restore de identidade, rede, RF, protocolos, display, APRS, Direct, Helix e segredos protegidos.

## Requisitos de compatibilidade
- Desktop/tablet/mobile.
- Claro/escuro e alto contraste.
- SSE/WebSocket/Event Bus preferidos; evitar polling agressivo.
- Navegação e estado não podem depender de múltiplos escritores de configuração.


## 2026-10-22 — display isolado
DISPLAY-040 / 5.00.002: página Display preserva seleção G4KLX/ON7LDS existente; backend usa MMDVM-Display oficial externo. Serviço ativo não comprova atualização da tela. HMI/TFT jamais gravado automaticamente. Restante do painel congelado.
