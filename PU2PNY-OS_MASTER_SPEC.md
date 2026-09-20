# PU2PNY-OS — MASTER SPEC

**Fonte oficial dos requisitos do projeto.**  
**Estado:** consolidado para o ciclo corretivo pós-0.3.3-alpha em 2026-09-19.

> `docs/PU2PNY-MASTER-PLAN.md` e os requisitos já aprovados nas versões anteriores permanecem válidos e incorporados por referência. Este arquivo não autoriza apagar ou simplificar funcionalidades anteriores. Em conflito, a decisão mais recente e explicitamente identificada por requisito neste arquivo prevalece.

## 1. Arquitetura e continuidade

### ARCH-001 — Sistema próprio
PU2PNY-OS é uma distribuição/appliance próprio para rádio digital. Pode integrar componentes upstream como MMDVMHost e gateways, mas não deve se tornar fork de Pi-Star ou WPSD.

### ARCH-002 — Modularidade
Boot, Network, Hardware, RF, Protocol, Live/Event Bus, UI, Display, APRS, P2P e Update devem permanecer módulos separáveis. Recurso opcional não pode impedir boot, rede local, RF ou painel.

### REL-001 — Baseline preservada
Toda nova versão parte do último estado validado, cria rollback e executa regressão. DMR TX/RX fisicamente aprovado é baseline obrigatória.

### PERF-001 — Appliance leve
Baixo uso de CPU/RAM, pouca escrita em SD, logs limitados/rotacionados, sem polling pesado e sem carga proporcional ao número de abas.

## 2. Primeiro acesso, rede e wizard

### NET-001 — Acesso de setup
SSID de setup: `pu2pny`; endereço local de setup `10.43.0.1`; acesso normal `http://pu2pny.local/`. O AP deve continuar recuperável se o provisionamento falhar.

### NET-002 — Wi-Fi salvo precisa voltar conectado
Ao selecionar SSID, informar senha e salvar, o sistema deve validar/salvar de forma transacional, reiniciar quando necessário e voltar conectado ao Wi-Fi escolhido. Em falha, preservar a configuração anterior e restaurar AP sem perda de acesso.

### NET-003 — Estado AP deve refletir a realidade
Se o SSID `pu2pny` estiver efetivamente transmitindo, API/UI não podem afirmar "AP desligado". O estado deve ser derivado do runtime real, não apenas de arquivo de intenção.

### NET-004 — Ethernet hotplug e mDNS
Ethernet ligada depois do boot deve obter DHCP, atualizar o painel e anunciar `pu2pny.local` sem exigir descoberta manual do IP. O IP direto permanece fallback.

### NET-005 — Duas redes Wi-Fi salvas
Suportar pelo menos dois perfis Wi-Fi com prioridade/failover controlado, sem derrubar o AP de recuperação até existir uplink válido.

### NET-006 — Diagnóstico de rota e DNS
Painel deve mostrar interface de saída, IP, gateway, DNS efetivos, resolução, latência, perda quando mensurável, traceroute/MTR sob demanda, número de saltos e destino do servidor do protocolo. Diagnóstico deve ser leve e sob demanda/cached.

### NET-007 — DNS configurável com recomendação explicável
Permitir DNS automático e perfis manuais (por exemplo Cloudflare, Google, OpenDNS ou servidor customizado), porém nunca trocar silenciosamente. Sugestão deve usar teste real de resolução/latência e explicar o motivo.

### NET-008 — VPN não é correção automática de rota
Não rotear tráfego por VPN pública automaticamente com base em um único ping/DNS. WireGuard/PU2PNY Direct é recurso opt-in. Qualquer failover futuro exige medição, histerese, rollback, indicação visual e preservação de UDP/MTU.

### WIZ-001 — Seleção de idioma primeiro
Na primeira abertura, antes dos demais campos, apresentar tela de boas-vindas e idioma. PT/EN/ES devem permanecer disponíveis depois no painel.

### WIZ-002 — Fluxo simples
Primeiro acesso mostra somente o necessário. Ajustes avançados ficam após provisionamento; Expert não deve poluir o fluxo inicial.

## 3. Hardware, RF e protocolos

### HW-001 — Detecção real
Raspberry Pi, MMDVM e display só podem ser marcados como detectados quando houver evidência. Sem adivinhar modelo. Timeout obrigatório.

### RF-001 — Configuração transacional
MMDVMHost deve usar configuração ativa em área gravável apropriada, temporários em `/run`, escrita atômica, backup e rollback automático se o serviço não iniciar/permanecer ativo.

### RF-002 — Simplex e duplex
Hotspot simplex usa RX=TX. Repetidora/duplex permite RX/TX separados. Modelo de modem e simplex/duplex são conceitos separados.

### RF-010 — TOT de transmissão RF
TOT do transmissor RF tem padrão de 180 s quando aplicável. É proteção de TX; não confundir com duração de recepção.

### PROTO-001 — DMR baseline
Preservar o caminho DMR MMDVMHost ↔ DMRGateway ↔ rede e todos os parâmetros já fisicamente aprovados.

### PROTO-002 — D-Star
Troca para D-Star deve aplicar gateway/rede sem derrubar MMDVMHost. Em falha, rollback automático para o estado anterior.

### PROTO-003 — YSF/C4FM
Troca para YSF deve aplicar gateway/rede sem derrubar MMDVMHost. Em falha, rollback automático para o estado anterior.

### PROTO-004 — Demais protocolos
P25, NXDN e POCSAG/DAPNET devem ser concluídos e testados modularmente somente após DMR, D-Star e YSF estarem estáveis.

### PROTO-005 — Preflight antes de reiniciar rádio
Antes de aplicar troca de protocolo, validar dependências locais necessárias (incluindo broker MQTT quando habilitado, arquivo INI legível, porta serial e gateway correspondente). Se o preflight falhar, não tocar no estado RF ativo.

### PROTO-006 — Falha MQTT não pode destruir RF funcional
Erro de conexão MQTT deve gerar diagnóstico específico e rollback. O painel não deve reduzir o erro a bloco de log bruto. Deve informar broker, endereço/porta, serviço, último teste e ação segura.

## 4. Ao Vivo e histórico

### LIVE-001 — Estado ativo rico
Mostrar direção, origem (RF ou Internet), protocolo, indicativo/ID/nome quando disponível, destino/TG/refletor, slot/CC quando aplicável, duração e rede/servidor.

### LIVE-002 — Atividade recente expansível
O botão "+" deve manter o submenu aberto mesmo quando chegar atualização ao vivo. Mostrar detalhes de cada ocorrência e não recriar estado visual de forma que feche o item sozinho.

### LIVE-003 — Métricas somente quando existem
BER e RSSI só aparecem quando houver valor real. Não ocupar espaço com campos vazios ou `—` durante uma recepção sem telemetria.

### LIVE-004 — Duração destacada
Tempo da transmissão/recepção ativa deve ser grande, legível e de fácil localização.

### LIVE-005 — Alerta visual para atividade RF
Quando houver recepção originada em RF, o painel pode usar destaque/pulso visual discreto e acessível. Não usar animação agressiva contínua.

### LIVE-010 — Alerta de recepção RF prolongada
Ao completar 180 s de recepção originada em RF, emitir alerta visual/sonoro opcional de "atividade RF prolongada". Isso **não encerra RX** e não é TOT. Recepção originada da Internet não usa esse alerta.

## 5. Interface e Expert

### UI-001 — Rodapé/versionamento
Todas as páginas operacionais devem exibir discretamente `PU2PNY-OS` e versão efetivamente instalada.

### UI-002 — Responsividade e temas
Desktop/tablet/mobile, claro/escuro, legibilidade e alto contraste sem regressão.

### UI-003 — Diagnóstico visual
Estado vivo de rede/sistema deve priorizar cards, gráficos leves e explicações. JSON/log bruto fica em seção técnica expansível.

### UI-004 — Sugestões sem automação destrutiva
O sistema pode diagnosticar e sugerir ações, mas deve distinguir fato, hipótese e recomendação. Mudança de DNS, rota, VPN, RF ou serviço exige confirmação salvo recuperação automática previamente aprovada.

### SEC-020 — Acesso Expert/SSH
Baseline segura: SSH opcional, não-root, por chave, desabilitado por padrão. Um terminal web só poderá ser habilitado quando for local-only, usuário `radioexpert`, sem root/sudo, sessão temporária, proteção de origem/CSRF, timeout, auditoria limitada e testes de segurança. Até lá, preferir console de diagnóstico com comandos permitidos.

## 6. Display / Nextion

### DISPLAY-001 — Máquina de estados única
Web e display físico devem consumir o mesmo estado normalizado: standby, RX-RF, RX-NET, TX-RF, erro/atenção.

### DISPLAY-002 — Standby
Mostrar hora, protocolo conectado, forma de uplink (Wi-Fi/Ethernet), IP e estado pronto, sem piscar componentes incorretos.

### DISPLAY-003 — RX
Mostrar protocolo, indicativo/nome/ID quando disponível, origem RF/Internet, destino e duração. Dados indisponíveis não devem ser inventados.

### DISPLAY-004 — TX
Mostrar protocolo, indicativo do operador/configurado, destino e duração da própria transmissão.

### DISPLAY-005 — Falhas visuais
Eliminar retângulo vermelho/piscadas causadas por componentes HMI incompatíveis. Em erro real, usar uma indicação controlada e legível.

### DISPLAY-006 — HMI seguro
Não gravar/substituir HMI/TFT automaticamente sem confirmação. Detectar incompatibilidade e oferecer diagnóstico/manual.

## 7. APRS / notificações

### APRS-001 — Notificação resiliente
Notificação do navegador é opcional e depende da permissão/contexto do browser. Se for negada/indisponível, manter alertas dentro do painel e explicar como habilitar, sem bloquear APRS/DPRS.

## 8. P2P / CGNAT

### P2P-001 — PU2PNY Direct
Conexão PU2PNY↔PU2PNY deve tentar caminho direto quando possível e usar relay autorizado quando necessário. WireGuard é uma opção de túnel; não deve substituir automaticamente o uplink normal de protocolos sem política explícita.

## 9. Segurança, backup e release

### BACKUP-001 — Ponto de retorno
Toda alteração estrutural cria ponto de retorno antes de modificar a branch/código em produção.

### SEC-001 — Menor privilégio
Sem root remoto por padrão, segredos fora de APIs públicas, configs com permissões mínimas, serviços hardenizados sem bloquear áreas graváveis necessárias.

### TEST-001 — Matriz obrigatória
Toda correção deve possuir caso em `PU2PNY-OS_TEST_MATRIX.md` e estado DOC/SW/VPS/HW/PROD.

### REL-002 — Release não pode ocultar bloqueador
Wi-Fi/wizard, RF/DMR e boot são gates críticos. Falha conhecida impede declarar release completa/produção.

### REL-003 — Artefato
Build ARM64, validação estrutural e SHA-256 são obrigatórios antes de divulgação de imagem.

## 10. Achados físicos 0.3.3 incorporados como requisitos

Os relatos físicos de 2026-09-19 fazem parte deste MASTER_SPEC por meio dos IDs acima. Em especial: AP/mDNS inicial aprovados; handoff Wi-Fi falhou; status do AP divergiu da realidade; D-Star e YSF falharam no restart do MMDVMHost com erro MQTT mas rollback funcionou; submenu de atividade fecha sozinho; Nextion apresenta flicker/estado incompleto; notificação de navegador APRS foi negada; Expert precisa ganhar explicação/visualização; painel deve melhorar duração/BER/RSSI/rota/DNS.

Nenhuma dessas observações autoriza remover o que já está funcionando na 0.3.3.
