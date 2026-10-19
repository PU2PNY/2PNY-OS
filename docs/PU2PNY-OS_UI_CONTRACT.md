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

## Controle de acesso por rádio (PROTO-501)
Configuração integrada do acesso RF, separada da autenticação do painel web:
- **Privado**: somente proprietário, padrão de novas instalações.
- **Semi-público**: proprietário + lista explícita de indicativos/Radio IDs autorizados; lista vazia ou inválida **não libera o nó**.
- **Público**: aberto no RF quando suportado, exclusivamente mediante escolha administrativa avançada, confirmação explícita e aviso de responsabilidade.
- Exibir *modo configurado* e *modo efetivo*. Não mascarar falhas de `SelfOnly`, whitelist e suporte por protocolo. Preservar perfil existente durante upgrade até conversão segura.
- Persistência entre reinício, alterações de protocolo e update, com teste prévio e rollback. **Publicar não significa permitir acesso anônimo ao painel**.

## Falha de displays: contrato de diagnóstico (DISPLAY-501)
Depois dos testes multicartão de 2026-10-19, não exibir “Display pronto” sem provar driver/binário presente, serviço operacional e transporte confirmado. Mostrar modelo físico somente quando verificado, HMI separado da detecção da tela, porta, driver, status, erro de seleção e rollback. Nenhum display é HW aprovado nesta rodada; SW/CI/VPS não substitui standby/RX/TX em hardware.

## Requisitos de compatibilidade
- Desktop/tablet/mobile.
- Claro/escuro e alto contraste.
- SSE/WebSocket/Event Bus preferidos; evitar polling agressivo.
- Navegação e estado não podem depender de múltiplos escritores de configuração.
