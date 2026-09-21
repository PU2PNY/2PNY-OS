# PU2PNY-OS — MASTER SPEC

**Fonte oficial dos requisitos do projeto.**  
**Estado:** consolidado para o ciclo corretivo 0.3.6-alpha após feedback físico da 0.3.5 em 2026-09-20.

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

## 11. Requisitos incorporados após teste físico da 0.3.4-alpha — 2026-09-20

### WIZ-003 — Avanço automático seguro
Quando uma etapa do assistente atingir PASS real e estável, iniciar contagem visual de 5 s e avançar automaticamente para a próxima etapa. O botão manual deve permanecer disponível e qualquer erro/cancelamento interrompe a contagem. Nunca avançar por timeout presumindo sucesso.

### WIZ-004 — Boas-vindas bilíngue
A primeira tela deve perguntar o idioma de forma imediatamente compreensível em Português e Inglês, mantendo PT/EN/ES como opções selecionáveis.

### NET-009 — Wi-Fi rápido, estável e com dois perfis gerenciáveis
Além do NET-005, o painel operacional deve permitir adicionar/editar/remover pelo menos duas redes Wi-Fi, definir prioridade e alternar entre rede 1 e rede 2 sem refazer o wizard completo. Troca deve usar o perfil já salvo, validar associação+IPv4 rapidamente, preservar a rede anterior até o novo link ficar válido e manter Ethernet ativa quando existir.

### NET-010 — Rádio Wi-Fi e canais
Mostrar canal/frequência em uso, banda, intensidade real quando disponível e uma visão leve dos canais próximos/ocupados. Sugestão de canal deve ser informativa; nunca reconfigurar roteador externo automaticamente.

### UI-005 — Edição posterior sem refazer primeiro acesso
Ações como "Trocar rede" no Hotspot/Internet devem abrir somente o módulo correspondente e retornar ao painel operacional. Não exigir Hardware → Configuração básica → Conclusão novamente quando o equipamento já está provisionado e essas etapas continuam válidas.

### NET-011 — Qualidade da rota explicável
A rota até o servidor deve classificar a medição observada como Ótima/Boa/Ruim com critérios visíveis, identificar gateway/local, destino final e número de hops. Hops sem ICMP não são automaticamente falha.

### LIVE-008 — DMR: módulo XLX efetivo deve acompanhar TG de controle
O caminho DMR/XLX RF→servidor e servidor→RF já validado não deve ser alterado para corrigir UI. Quando um TG de controle 4001..4026 selecionar o módulo A..Z, o estado em tempo real do painel deve refletir imediatamente o módulo efetivo (ex.: TG4002 → B, TG4003 → C), inclusive durante transmissões posteriores em TG6. O preset salvo pode permanecer no módulo inicial; o runtime deve ter precedência visual. TG4000 deve refletir desligado/desvinculado. Não reiniciar MMDVMHost/DMRGateway só para atualizar essa indicação.

### LIVE-006 — Tabela operacional rica
Ao Vivo e Histórico devem compartilhar o mesmo modelo de colunas, inspirado no painel XLX026 já aprovado: número/bandeira, Status, Indicativo, Nome, Hotspot/Repetidora, Cidade, Protocolo, Módulo/TG, origem RF/Internet, Tempo TX/RX e horário. Coluna sem dado real mostra —; não inventar dados.

### LIVE-007 — Standby com radar
No box Ao Vivo em espera, remover texto redundante "Aguardando" duplicado e usar um radar leve/animado para indicar monitoramento de RF, sem polling extra ou animação pesada.

### APRS-002 — Toast de mensagem
Nova mensagem APRS deve gerar um balão no canto superior direito por 5 s. O balão mostra remetente/resumo, é clicável e abre APRS para responder. O alerta interno funciona mesmo quando Notification API do navegador estiver bloqueada.

### DISPLAY-007 — Layout PU2PNY próprio
Criar um renderer/layout PU2PNY independente dos layouts Pi-Star/ON7LDS, sem transformar o projeto em fork e sem sobrescrever HMI/TFT automaticamente. A UI de configuração deve oferecer "PU2PNY Moderno" como opção quando tecnicamente compatível.

### DISPLAY-008 — Conteúdo moderno e identidade
Splash: logo PU2PNY + "Iniciando / Starting". Standby: hora, protocolo, uplink/IP e estado. RX/TX: foto quando houver fonte válida, indicativo destacado, nome, cidade, país/bandeira, protocolo, origem, TG/módulo, duração, BER/RSSI quando reais. Falta de foto/dado usa layout limpo, sem placeholders feios.

### RF-011 — Pré-alerta do TOT
O TOT de 180 s continua sendo proteção de TX do RF. Nos últimos 10 s antes do corte, painel e display devem mostrar contagem regressiva 10→0 e alerta visual controlado. Isso não se aplica a RX nem a tráfego somente Internet.

### UI-006 — Fuso horário coerente
Hora exibida, timezone atual e seletor devem permanecer coerentes. Se o sistema estiver em America/Sao_Paulo, a UI deve refletir exatamente esse timezone e não exibir país/fuso diferente como se fosse o ativo.

### PERF-002 — Térmica observável
Temperatura deve ser lida do hardware real e acompanhada de CPU/load/frequência/throttling quando disponível. O sistema pode reduzir polling/serviços ociosos, mas não deve alterar RF ou clock arbitrariamente. Meta: eliminar processos desnecessários e manter appliance leve.

### UPDATE-001 — Atualização segura e recuperável
Atualização pelo painel não pode ficar indefinidamente em progresso sem estado/timeout. Exibir etapas reais, progresso somente quando mensurável, timeout, erro acionável, preservação da versão atual e rollback. A/B só pode ser habilitado depois de validação estrutural e HW.

### UPDATE-002 — Manutenção
Adicionar manutenção manual/automática no painel: verificar componentes oficiais ausentes, listas públicas, integridade básica, espaço/logs e estado de serviços com baixa prioridade. Não executar `apt full-upgrade`, não alterar RF/rede sem confirmação e não escrever continuamente no SD. Deve haver "Executar agora", ativar/desativar automática, último resultado e próximo momento elegível.

### DISPLAY-009 — Atualização nunca pode travar o display
Durante update/manutenção, display deve mostrar progresso apenas quando o backend fornecer progresso real. Se uma etapa parar/falhar, sair do estado de progresso e mostrar erro/rollback; nunca congelar em "30%" fabricado.

### TEST-002 — Fluxo pós-provisionamento
Depois que o hotspot estiver provisionado, editar rede/protocolo/display não pode apagar ou reiniciar etapas independentes já validadas.


## 12. Requisitos incorporados após teste físico da 0.3.5-alpha — 2026-09-20

### NET-012 — Captive portal de primeiro acesso
Ao conectar ao AP `pu2pny`, o sistema deve responder aos endpoints de detecção de captive portal usados por Android, iOS/macOS, Windows e navegadores compatíveis para abrir ou sugerir imediatamente o primeiro acesso. A abertura automática depende do sistema operacional do cliente e não pode ser tratada como garantia; `http://pu2pny.local/wizard` e `http://10.43.0.1/` permanecem caminhos de recuperação obrigatórios.

### NET-013 — Wi-Fi 1 e Wi-Fi 2 operacionais
A nomenclatura da UI passa a ser `Rede Wi‑Fi 1` e `Rede Wi‑Fi 2`. Busca automática e inclusão manual devem funcionar no painel operacional depois do provisionamento. Erro interno de script como `unbound variable` nunca pode aparecer como resposta normal ao usuário; deve haver mensagem simples, log técnico separado e rollback.

### NET-014 — DNS efetivo consistente
Ao trocar DNS, somente os resolvedores efetivamente ativos devem aparecer em `DNS efetivo`. O sistema deve aplicar a troca transacionalmente, confirmar conclusão ao usuário e retornar à página Internet. Não acumular Google + Cloudflare na UI quando apenas um perfil estiver ativo.

### NET-015 — Diagnóstico de rota para leigos
`Rota até o servidor` deve explicar em linguagem simples o que está sendo medido, destino, gateway, hops, latência/perda quando disponíveis e classificar a qualidade em `Melhor opção`, `Bom`, `Ruim` ou `Péssimo` com critérios visíveis. Hops sem resposta ICMP não são automaticamente falha.

### WIZ-005 — Exemplos genéricos
Indicativo e identificador digital mostrados como exemplo no primeiro acesso nunca devem usar dados reais do operador. Usar valores demonstrativos genéricos. A UI deve usar o rótulo `Radio ID` quando o campo for aplicável a identificador digital geral; nomes específicos de protocolo permanecem onde tecnicamente necessários.

### UI-007 — Tradução integral
Ao selecionar PT, EN ou ES, 100% do texto apresentado ao usuário nas páginas operacionais, wizard, avisos, botões, status e mensagens de erro deve seguir o idioma selecionado. Termos técnicos/protocolares podem permanecer como nomes próprios quando não houver tradução apropriada.

### UI-008 — Feedback de operações e retorno ao contexto
Toda ação iniciada pelo painel que salvar, aplicar, atualizar, reiniciar, verificar ou executar manutenção deve abrir feedback visual imediato com: ação solicitada, etapa atual, sucesso/erro em linguagem simples e, ao terminar, retornar ao mesmo módulo/página de origem. Progresso numérico 0–100 só pode ser exibido quando houver progresso real mensurável; caso contrário usar etapas determinísticas sem percentual inventado.

### UI-009 — Pós-provisionamento permanente
Depois do primeiro acesso concluído, links de Internet, Wi‑Fi, RF, protocolo, display, manutenção e Expert nunca devem redirecionar silenciosamente para o wizard completo. O wizard só reabre por ação explícita do usuário ou quando o sistema realmente estiver não provisionado.

### UI-010 — Fuso horário com privilégio correto
Alterar timezone no painel deve usar backend privilegiado/controlado, nunca depender de permissão direta do navegador/usuário não privilegiado. Falha como `Failed to set time zone: Access denied` deve ser convertida em diagnóstico claro e não deixar relógio/UI incoerentes.

### UI-011 — Expert e organização de RF/protocolos
O modo Expert deve mostrar o mesmo estado Ao Vivo normalizado do painel principal, com detalhes técnicos adicionais. Atalhos de RF e protocolos devem pertencer à área Hotspot/rádio e não redirecionar para configuração básica do primeiro acesso.

### LIVE-009 — Identidade externa opcional no histórico
Ao Vivo, Última atividade e Histórico podem mostrar mini-ícones QRZ e RadioID quando for possível construir uma URL válida para o indicativo/ID observado. O clique abre nova aba. Se a URL não puder ser validada/gerada, o ícone não aparece. A página não pode depender desses serviços para carregar.

### APRS-003 — Localização assistida por permissão
Na configuração APRS/DPRS, oferecer `Usar minha localização`. O navegador deve pedir permissão antes de acessar geolocalização e, se autorizada, preencher latitude/longitude. Sempre manter edição manual; negar permissão não pode bloquear APRS.

### DISPLAY-010 — Visualização profissional em todos os displays
Nextion, TFT, OLED, LCD e demais displays suportados devem usar uma apresentação coerente com a identidade PU2PNY e adequada à resolução disponível. Deve haver estados distintos para standby, RX e TX; em telas capazes, mostrar indicativo, nome, país/bandeira, cidade, protocolo, destino/TG/módulo, duração, horário e métricas reais de recepção. Em telas simples, priorizar informação essencial legível. Nunca inventar dados ausentes.

### UPDATE-003 — Atualização integrada com GitHub e downgrade seguro
O hotspot deve verificar automaticamente, em baixa frequência e sem polling pesado, se existe atualização do canal escolhido no repositório oficial. Ao encontrar versão nova, informar o usuário e permitir baixar/instalar pelo painel com verificação de integridade e rollback. Antes da instalação perguntar se deseja preservar a versão atual como ponto de retorno; depois permitir excluir esse backup. Downgrade deve ser uma ação explícita e usar somente artefato oficial/verificado.

### UPDATE-004 — Manutenção observável
Manutenção deve registrar `Última execução`, resultado resumido e `Próxima execução elegível` quando automática estiver habilitada. Estado `runner` interno não é informação suficiente para o usuário.

### PROTO-007 — D-Star operacional completo
D-Star deve transmitir RF→rede e rede→RF, refletir imediatamente servidor/módulo efetivo, fornecer feedback/voz de conexão quando disponível e expor no painel somente parâmetros tecnicamente relevantes. Porta `0` não pode ser apresentada como configuração válida quando a integração exige porta concreta; quando a porta for gerenciada internamente pelo protocolo/gateway, a UI deve explicar isso em vez de exibir um valor enganoso.

### PROTO-008 — YSF/C4FM operacional completo
YSF/C4FM deve transmitir RF→rede e rede→RF, reproduzir tráfego recebido do servidor e feedback/voz de conexão quando suportado. Receber apenas o sinal local do rádio sem encaminhar à rede não é considerado funcionamento.

### PROTO-009 — Perfis independentes por protocolo
Cada protocolo deve possuir perfil próprio de RF/rede, incluindo frequência e parâmetros específicos permitidos. A troca de DMR para D-Star/YSF etc. deve selecionar o perfil correspondente sem obrigar o usuário a reconfigurar frequência toda vez. Isso reduz interferência/ruído entre rádios de protocolos diferentes na mesma frequência. Troca de perfil continua transacional, com preflight e rollback.

### ARCH-003 — Correções compartilhadas devem ser globais
Correções de navegação, tradução, feedback de operação, estado Ao Vivo, identidade, tratamento de erros, segurança e componentes comuns devem ser aplicadas no componente compartilhado correspondente, não apenas em uma página/protocolo isolado, salvo quando o comportamento for tecnicamente específico.

### REL-004 — Novas funções deste ciclo entram na própria versão corretiva
As novas funções explicitamente aprovadas no feedback físico da 0.3.5 não devem ser empurradas para uma versão futura por conveniência de escopo. Elas fazem parte da versão corretiva atualmente em construção (`0.3.6-alpha`). Se alguma função depender de validação física, integração externa ou limitação do cliente, ela ainda deve ser implementada até o nível verificável (DOC/SW/VPS) nesta versão e permanecer marcada como HW/PENDENTE até o teste real. Não declarar pronta uma função que ainda não atingiu o nível de validação necessário.

### REL-005 — DMR 0.3.5 é baseline de regressão
O comportamento DMR considerado excelente no teste físico da 0.3.5 deve ser preservado. Mudanças para Wi‑Fi, D-Star, YSF, perfis, display, update ou UI não podem alterar o caminho DMR funcional sem evidência, backup, teste e rollback.

## 13. Requisitos BrandMeister incorporados em 2026-09-20

### PROTO-010 — Identificação DMR por rádio/hotspot
Para hotspot pessoal BrandMeister, manter o Radio ID base de 7 dígitos e permitir selecionar um alias/ESSID de **dois dígitos** `01..99`. A interface deve apresentar nomes leigos como `Rádio 1 (01)`, `Rádio 2 (02)` etc. O ID efetivo de rede passa a ser o Radio ID de 7 dígitos acrescido desses dois dígitos, totalizando 9 dígitos, sem alterar o Radio ID programado no rádio. Não usar sufixo de um único dígito. Perfis/hotspots diferentes devem poder usar aliases distintos e a UI deve recomendar frequências diferentes quando houver mais de um hotspot. Em redes que não aceitam esse mecanismo, não inventar compatibilidade.

### PROTO-011 — BrandMeister API Key separada da autenticação DMR
Quando a rede selecionada for BrandMeister, o painel deve permitir cadastrar/remover uma **API Key BrandMeister** opcional. A API Key é destinada às funções de gerenciamento disponibilizadas pela API BrandMeister (por exemplo, informações do hotspot e gerenciamento suportado de talkgroups) e **não substitui** a Hotspot Security usada para autenticar o hotspot no master DMR. A implementação não deve pedir nem inventar um `API Secret`: a documentação BrandMeister atual descreve uma única API Key/token. A chave deve ser armazenada fora da configuração pública, com permissão restrita, nunca devolvida pela API do PU2PNY e nunca registrada em log. O painel pode informar apenas `configurada/não configurada`.

### SEC-021 — Segredos BrandMeister
Hotspot Security e BrandMeister API Key são segredos distintos. Ambos devem permanecer fora de respostas públicas, histórico, logs e arquivos exportados sem proteção. Alterar/remover a API Key não deve reiniciar MMDVMHost nem DMRGateway. Alterar ESSID/alias DMR pode exigir reconexão do gateway, mas deve preservar rollback e a baseline DMR da 0.3.5.

## 14. Correção APRS incorporada após teste físico — 2026-09-20

### APRS-004 — Mensagens APRS-IS bidirecionais funcionais
O recurso de mensagens APRS deve realmente **enviar e receber** via APRS-IS. Não basta enfileirar uma mensagem nem considerar um socket TCP aberto como conexão válida. O cliente deve:
- conectar a porta bidirecional/filtrada apropriada;
- aguardar e interpretar a confirmação de login APRS-IS (`logresp`) antes de transmitir beacon ou mensagens;
- distinguir conexão TCP de login APRS-IS verificado;
- manter mensagem na fila quando não houver sessão verificada;
- receber mensagens endereçadas ao indicativo/SSID APRS configurado, gerar ACK quando houver message ID e registrar a entrada;
- reconhecer ACK/REJ recebidos e refletir o estado da mensagem enviada;
- aplicar retry limitado e de baixo custo para mensagens sem ACK, reutilizando o mesmo message ID e evitando flood;
- deduplicar mensagens recebidas repetidas pelo mesmo remetente/message ID, ainda respondendo ACK;
- expor no painel estado claro de login verificado, último RX, último TX de mensagem, fila pendente e último erro;
- preservar histórico limitado, baixo consumo e poucas gravações em SD.

A implementação deve usar porta APRS-IS bidirecional recomendada e servidores/pools atuais documentados; para América do Sul, preferir o pool regional oficial quando disponível, mantendo fallback configurável.

## 13. Ajustes permanentes da 0.3.6 — validação física de 20/09/2026

- **PROTO-012 — Compatibilidade D-Star com o binário fixado:** enquanto a imagem utilizar F4FXL DStarGateway `v20260323-612f388`, o gerador deve usar o schema dessa revisão (`[General]`, `[Repeater 1]`, `[IRCDDB 1]`, `[Hosts Files]` e níveis numéricos de log). É proibido misturar o schema atual da branch develop com esse binário. Alteração exige teste e rollback próprios.
- **NET-016 — DNS efetivo e comparação dinâmica leve:** mostrar apenas resolvedores efetivos da interface da rota padrão, informar quando a comparação foi medida e refazer o teste em cache limitado (alvo atual: 180 s), sem aplicar automaticamente o DNS sugerido.
- **NET-017 — Wi-Fi 1/2 configurável e handoff sem reboot obrigatório:** os dois perfis devem oferecer busca real, SSID manual e senha. A troca só é concluída após associação + IP; se validada, não reiniciar apenas para confirmar o perfil. Em falha, restaurar conexão anterior ou AP de recuperação.
- **WIZ-006 — Idioma no primeiro provisionamento real:** a seleção de idioma deve reaparecer em hotspot não provisionado mesmo quando o navegador traz `localStorage` de uma instalação antiga.
- **APRS-005 — Operação assistida e resposta direta:** a página APRS deve explicar o bloqueio de geolocalização em HTTP, manter preenchimento manual, oferecer teste/ajuda sob demanda e permitir clicar no remetente para preencher automaticamente o destino da resposta.
- **UI-012 — Identidade externa legível:** QRZ e RadioID devem aparecer também em Atividade recente. RadioID não deve abrir JSON bruto; a consulta oficial será apresentada em página legível, somente sob demanda.
- **UPDATE-005 — Download verificado antes da instalação:** atualização deve baixar em segundo plano, exibir progresso real quando mensurável, atingir 100%, validar SHA-256 e somente então permitir instalação após confirmação explícita. Falha de rede antes de 100% não pode modificar o sistema. A confirmação deve alertar sobre alimentação, rollback e possibilidade de regravar o cartão em falha grave.
- **DISPLAY-011 — TX/RX e telas compactas:** TX/RX deve priorizar indicativo, nome, cidade/país, protocolo, origem/destino e estado RF/rede. OLED/LCD compactos devem incluir identidade e contexto de rede/IP dentro do espaço disponível. Foto dinâmica em Nextion só pode ser habilitada com HMI explicitamente compatível; o sistema não deve sobrescrever HMI/TFT automaticamente.
- **TEST-006 — P25 sem hardware disponível:** nesta etapa P25 só pode receber DOC/SW/VPS. Não declarar HW/PROD até teste com rádio P25 real.

## 15. Displays genéricos e linha Raspberry Pi 32-bit — 2026-09-20

### DISPLAY-012 — OLED/LCD/eLED e displays genéricos operacionais
Displays suportados detectados pelo PU2PNY devem ser ativados pelo PU2PNY Display Core sem exigir terminal. O comportamento mínimo obrigatório é:
- Standby: identidade PU2PNY, hora, protocolo, frequência quando real, uplink/IP e estado de rede dentro do espaço disponível;
- TX: protocolo, indicativo/identidade, destino/TG/módulo quando aplicável, direção, duração e métricas RF somente quando reais;
- RX: protocolo, origem/indicativo/nome quando disponível, destino/TG/módulo, direção, duração e BER/RSSI somente quando reais;
- telas pequenas devem usar layout compacto e legível, sem rolagem/polling agressivo;
- suportar inicialmente OLED SSD1306/SH1106 e LCD HD44780/PCF8574 já presentes no Display Core; novos drivers genéricos devem entrar por adaptadores isolados;
- endereço I2C isolado pode ser tratado como candidato, não como identidade absoluta do modelo. Quando não houver confirmação segura do controlador, usar tentativa controlada/diagnóstico e rollback sem afetar RF;
- Nextion/HMI continua obedecendo DISPLAY-006/011: nenhuma gravação automática de HMI/TFT.

### ARCH-004 — Artefato paralelo Raspberry Pi 32-bit
Manter a imagem ARM64 como linha principal e criar uma imagem ARM 32-bit (armhf) separada, baseada inicialmente em Raspberry Pi OS Legacy Lite Bookworm 32-bit da mesma data/base efetivamente fixada pela cadeia completa da linha ARM64, reduzindo divergência de userland. Trixie 32-bit só deve ser avaliado em branch futura após a linha Bookworm ARM32 estar estável. O artefato deve ser uma imagem de cartão Raspberry Pi (.img.xz), não ISO de PC. O alvo mínimo é Raspberry Pi Zero/Zero W, 1A+/1B+ e 2B, mantendo compatibilidade com modelos 32-bit posteriores quando a base oficial suportar.

O binário Go próprio deve ser compilado com GOOS=linux GOARCH=arm GOARM=6 para cobrir ARMv6 e superiores. Gateways/MMDVM e demais binários nativos precisam ser compilados dentro do rootfs armhf ou por toolchain compatível; nenhum binário ARM64 pode ser reutilizado no artefato 32-bit.

### PERF-003 — Perfil para Raspberry Pi antigos
Na linha 32-bit, priorizar Raspberry Pi OS Lite, serviços mínimos, sem desktop, logs limitados, polling reduzido, cache limitado e nenhuma função visual pesada no host. O painel web continua completo, mas processamento opcional de alto custo deve permanecer sob demanda. Em Raspberry Pi Zero/1 com 512 MB, estabilidade de RF/rede tem precedência sobre efeitos visuais ou coleta não essencial.

### REL-007 — Gate independente ARM32
A imagem ARM32 só pode ser publicada como Alpha quando: build armhf completo, xz -t, SHA-256, montagem/validação estrutural, confirmação de arquitetura dos binários críticos e boot/teste HW em pelo menos um Raspberry Pi ARMv6 ou ARMv7. O PASS ARM64 não vale como HW PASS ARM32 e vice-versa. A falha do pipeline 32-bit não pode bloquear nem alterar silenciosamente a imagem ARM64 já validada. Um artefato de CI explicitamente marcado EXPERIMENTAL/HW-TEST pode ser disponibilizado após todos os gates SW/estruturais passarem, somente para obter a validação física inicial; isso não o transforma em Alpha, HW PASS, PROD nem substitui a imagem ARM64.

## 16. Regras obrigatórias adicionadas para 0.3.7-alpha — 2026-09-20

### REL-008 — Continuidade integral da 0.3.6
A 0.3.7-alpha deve ser construída sobre a 0.3.6-alpha preservando integralmente tudo que já foi aprovado, implementado e validado. Nenhuma correção anterior pode desaparecer para acomodar Direct/P2P, display ou voz. DMR TX/RX fisicamente aprovado continua baseline de regressão e não pode ser alterado sem teste/rollback próprios.

### P2P-002 — Chamada PU2PNY Direct por indicativo/agenda
PU2PNY Direct deve permitir comunicação entre dois equipamentos PU2PNY pela Internet sem exigir BrandMeister, XLX, YSF Room ou FCS. Na primeira fase, o transporte de rádio é somente entre o mesmo protocolo: DMR↔DMR, D-Star↔D-Star e YSF/C4FM↔YSF/C4FM. Cross-mode fica fora deste gate inicial. O usuário escolhe um indicativo/contato no painel; não deve informar IP, porta, NAT ou comandos de terminal.

### P2P-003 — NAT/CGNAT: direto primeiro, relay somente quando necessário
O módulo `direct-core` deve tentar caminho direto autenticado entre os dois PU2PNY usando descoberta de endpoint/NAT compatível com ICE/STUN e transporte criptografado. Se NAT/firewall/CGNAT impedir o caminho direto, deve usar relay PU2PNY autenticado. O painel deve mostrar exatamente `Direct`, `Relay` ou `Offline`, nunca chamar uma conexão relay de direta. Latência e estado de criptografia devem ser visíveis quando medidos.

### P2P-004 — Infraestrutura própria e separação control/data plane
O serviço de controle PU2PNY Direct deve ser próprio/self-hosted, responsável por registro, identidade, chaves, presença, autorização e rendezvous. O tráfego de voz/dados não deve passar pelo control plane. Em fallback Relay, somente o relay explicitamente destinado ao transporte encaminha pacotes já criptografados de ponta a ponta. Não depender de conta/comercial de terceiros para funcionamento normal.

### P2P-005 — Pareamento e segurança
Cada hotspot possui identidade criptográfica própria. Contato/pareamento exige autorização explícita do dono e deve permitir revogação. Nenhuma porta administrativa deve ser aberta indiscriminadamente. Chaves privadas ficam fora da API pública, com permissões mínimas. Direct é opt-in e não muda a rota normal dos demais protocolos quando não está em uso.

### P2P-006 — Integração de rádio mesma-modalidade
O Direct Core deve separar sinalização do transporte de quadros de rádio. D-Star deve respeitar a identidade/callsign/URCALL; DMR deve respeitar Radio ID/slot/TG ou chamada privada conforme o modo Direct definido; YSF deve preservar a identidade de origem/destino disponível. O primeiro gate de release exige implementação verificável do caminho local e testes determinísticos de encapsulamento/anti-replay; funcionamento RF ponta a ponta permanece HW até dois hotspots reais.

### DISPLAY-013 — PU2PNY Moderno V2 em displays suportados
Nextion e displays gráficos suportados devem usar apresentação visual PU2PNY própria, limpa e moderna, com splash, cards, ícones/indicadores, estados visuais distintos de Standby/TX/RX, boa hierarquia e alto contraste. O desenho deve ser feito pelo renderer quando possível, sem sobrescrever HMI/TFT do usuário. OLED SSD1306/SH1106 deve usar layout gráfico compacto, não apenas linhas de texto. LCD HD44780/PCF8574 continua textual por limitação física, mas deve ter hierarquia coerente. Framebuffer/SPI/TFT só pode ser ativado quando houver driver/kernel confirmado; nunca adivinhar hardware.

### PROTO-013 — Aviso de conexão por voz em todos os protocolos suportados
Quando uma conexão de rede de protocolo for confirmada por evidência real do gateway, o PU2PNY deve poder emitir aviso de voz pelo rádio no protocolo ativo, respeitando configuração de idioma/voz e sem fabricar confirmação. DMR preserva o mecanismo já aprovado. D-Star, YSF, P25 e NXDN devem usar mecanismo nativo/compatível quando tecnicamente disponível; POCSAG não deve fingir voz. Falha do anúncio nunca pode derrubar RF, gateway ou conexão. O anúncio só ocorre após estado `connected` real, com rate-limit para evitar repetição/flood.

### TEST-007 — Gate de nova imagem
Antes de divulgar a 0.3.7-alpha: source tests, regressões 0.3.6, testes Direct/Display/Voice, build ARM64, XZ, SHA-256 e validação estrutural precisam passar. D-Star/YSF/Direct/Displays permanecem HW PENDENTE onde ainda não houver equipamento real testado.

## 17. Tela genérica touch de 7 polegadas — 2026-09-20

### DISPLAY-014 — Tela genérica touch de 7 polegadas
O PU2PNY-OS deve suportar tela genérica touch de 7 polegadas compatível com Raspberry Pi sem exigir terminal para operação normal. O suporte deve ser orientado por capacidade real, sem presumir fabricante ou controlador.

Critérios obrigatórios:
- suportar, quando o hardware/kernel realmente expuser, telas 7" por HDMI + USB touch e/ou DSI;
- detectar separadamente vídeo e dispositivo de toque; não marcar touch como funcional apenas porque existe framebuffer/DRM;
- usar DRM/KMS/framebuffer e entrada evdev/libinput ou equivalentes disponíveis no sistema, evitando driver proprietário quando não necessário;
- iniciar automaticamente uma interface PU2PNY própria em modo tela cheia/kiosk adequada a 7", com botões e alvos de toque dimensionados para uso sem mouse/teclado;
- consumir o mesmo estado normalizado do painel/Display Core para Standby, RX, TX, protocolo, TG/módulo/refletor, rede, alertas e métricas reais;
- permitir operação essencial pelo toque: Ao Vivo, Hotspot/Protocolos unificados, troca segura de perfil/protocolo, RF permitido pela política, Internet, Display e Sistema;
- preservar modo claro/escuro, alto contraste, legibilidade e responsividade;
- se o touch não for reconhecido, manter vídeo/painel utilizável e informar diagnóstico claro, sem derrubar RF, MMDVMHost ou gateways;
- nenhuma tela genérica pode ser declarada suportada em hardware antes de teste HW real do modelo/conjunto correspondente.

## 18. Atualização dinâmica de estado após operações — 2026-09-20

### UI-013 — Atualização dinâmica após operação
Quando uma operação do painel for concluída com sucesso — especialmente DNS, rede, protocolo, RF, display, update ou configuração equivalente — a mesma página deve atualizar automaticamente o estado efetivo retornado pelo backend, sem exigir F5, recarga manual ou repetição da operação.

Para troca de DNS:
- ao concluir a aplicação e validação, a mensagem de "atualizando/aplicando" deve ser substituída pelo resultado real;
- o card "DNS efetivo" deve refletir imediatamente os resolvedores ativos da interface da rota padrão;
- a seção de diagnóstico deve usar o mesmo estado atualizado;
- nenhum valor antigo pode permanecer visível até refresh manual;
- se a convergência do sistema ainda estiver em andamento, mostrar estado intermediário real e atualizar quando confirmado, com timeout e erro claro;
- preservar NET-016: mostrar somente DNS efetivamente ativos e nunca inventar sucesso.

## 19. Ajustes Wi-Fi confirmados no teste físico 0.3.7 — 2026-09-20

### NET-018 — Perfis Wi-Fi 1/2 com semântica clara e troca rápida
A página Internet deve tratar Wi-Fi 1 e Wi-Fi 2 como dois perfis persistentes e distintos.

Regras:
- **Salvar Rede Wi-Fi 2** deve somente persistir/validar o perfil, sem trocar imediatamente a conexão ativa, salvo se o usuário escolher explicitamente "Conectar agora";
- a troca efetiva entre Wi-Fi 1 e Wi-Fi 2 deve ocorrer pelo controle próprio de troca e continuar transacional;
- cada perfil deve mostrar claramente: SSID salvo, estado `Salva`, `Conectada`, `Disponível`, `Falhou` ou equivalente, além do IP quando aquele perfil estiver ativo;
- a busca de redes pode alimentar os dois seletores em uma única varredura compartilhada, evitando scan duplicado e consumo desnecessário;
- a troca deve ser otimizada para convergir o mais rápido possível, sem reboot ou espera artificial quando não necessários;
- velocidade nunca pode substituir validação: associação, autenticação e IPv4 precisam ser confirmados antes de declarar sucesso;
- em falha, restaurar imediatamente o perfil anterior ou AP de recuperação, mantendo o painel acessível quando houver outro caminho de rede.

### UI-014 — UX de credenciais e estado Wi-Fi
Nos campos de senha de Wi-Fi 1 e Wi-Fi 2 deve existir controle `Mostrar/Ocultar` para o usuário conferir o que digitou. Após salvar/aplicar, a própria página deve atualizar dinamicamente o estado do perfil e da conexão sem refresh manual.

Mensagens técnicas brutas de NetworkManager/systemd não devem aparecer ao usuário final quando houver tradução segura disponível. Com PT-BR selecionado, erros como `signal is aborted without reason` devem ser apresentados em português, preservando o detalhe técnico em área Expert/log.

## 20. Análise visual de canais Wi-Fi — 2026-09-20

### NET-019 — Gráfico de ocupação e recomendação de canal Wi-Fi
A página Internet deve incluir uma visualização gráfica leve dos canais Wi-Fi observados no ambiente e indicar o canal atualmente usado pela rede à qual o PU2PNY está conectado.

Requisitos:
- exibir separadamente as bandas disponíveis no hardware (por exemplo 2,4 GHz e 5 GHz);
- mostrar por canal as redes observadas e sua intensidade de sinal quando essa telemetria estiver disponível;
- identificar claramente o SSID/rede atualmente conectada e seu canal real;
- considerar sobreposição de canais, intensidade dos APs vizinhos, quantidade de redes, largura de canal quando detectável e domínio regulatório configurado;
- calcular uma recomendação explicável de **Melhor canal sugerido**, com motivo resumido, por exemplo: menor interferência estimada/menor ocupação;
- não afirmar que um canal é "livre" quando o scan apenas não observou redes naquele instante;
- a recomendação deve ser informativa: o PU2PNY não altera automaticamente o canal do roteador do usuário;
- permitir nova medição manual e usar cache/intervalo mínimo para evitar scans agressivos, quedas de associação, aumento de CPU ou interferência no AP de recuperação;
- se a interface Wi-Fi estiver ocupada com conexão crítica ou AP de recuperação, o scan deve ser adiado/limitado de forma segura em vez de derrubar a conectividade;
- dados sem evidência devem aparecer como indisponíveis, nunca inventados.

A recomendação deve priorizar estabilidade e qualidade real, não apenas o menor número de redes encontradas.

## 21. Perfis de protocolo no Ao Vivo e configuração no Hotspot — 2026-09-20

### LIVE-011 — Perfis rápidos de protocolo no Ao Vivo
Na página **Ao Vivo**, a faixa hoje usada como filtros por protocolo deve passar a apresentar os perfis rápidos dos protocolos configurados, mantendo rótulos claros como DMR, D-Star, YSF/C4FM, P25, NXDN e POCSAG conforme suportados.

Regras:
- o protocolo/perfil ativo deve ficar visualmente destacado;
- cada botão deve mostrar, quando disponível, protocolo + frequência e estado configurado/não configurado;
- clicar em um perfil configurado deve iniciar a troca transacional já existente, com preflight, tela de progresso real, confirmação de sucesso e rollback em falha;
- perfil não configurado não pode fingir troca: deve direcionar para sua configuração;
- a troca não pode reiniciar serviços desnecessários nem alterar o caminho DMR validado fora do escopo requerido;
- o estado da página Ao Vivo deve atualizar automaticamente após a troca, sem F5.

Os filtros de atividade por protocolo **não podem ser removidos**: devem permanecer disponíveis em controle separado/compacto, porque filtragem e troca de perfil são funções diferentes.

### PROTO-014 — Hotspot como área de configuração dos perfis
Na página **Hotspot**, os perfis rápidos dos protocolos devem permanecer, porém sua ação principal passa a ser **Configurar** o perfil selecionado, e não duplicar a função de troca rápida do Ao Vivo.

Cada perfil deve permitir abrir a configuração correspondente de RF/rede/frequência/servidor/TG/módulo conforme o protocolo. A página Hotspot continua sendo a referência para configuração; a página Ao Vivo passa a ser a referência para troca operacional rápida.

## 22. Correções PU2PNY Direct após teste físico 0.3.7 — 2026-09-20

### P2P-007 — Fluxo de pareamento/chamada com estado explícito
A interface PU2PNY Direct deve impedir chamadas inválidas e traduzir estados técnicos em mensagens operacionais claras.

Regras:
- `Chamar` só pode ser habilitado para contato/indicativo previamente pareado e válido;
- quando não houver nenhum peer pareado, a UI deve explicar `Pareie um PU2PNY antes de chamar` e não expor `HTTP 409`;
- se o indicativo não estiver registrado/online no rendezvous, informar em português `PU2PNY não encontrado ou offline`;
- se houver peer pareado, mas sem resposta, informar `Contato sem resposta` e manter o gateway/RF anterior preservado;
- incompatibilidade de protocolo deve citar local/remoto em linguagem clara e não alterar RF;
- códigos HTTP e mensagens brutas ficam disponíveis apenas em diagnóstico/Expert;
- estado `Offline` do Direct deve significar ausência de sessão Direct/Relay, não Internet geral offline;
- nenhum sucesso pode ser mostrado antes de pareamento, descoberta, autenticação, compatibilidade de protocolo e estabelecimento real do caminho.

### UI-015 — Página Direct deve usar o layout comum do painel
A página Direct deve usar o mesmo cabeçalho, navegação, tipografia, espaçamento, responsividade, tema e componentes comuns das demais páginas do PU2PNY.

Não pode haver menu concatenado, campos ocupando largura indevida, botões desalinhados ou quebra visual em desktop/tablet/mobile. A UI deve permanecer legível em PT/EN/ES e atualizar estado sem refresh manual.

## 23. APRS-IS assistido após teste físico 0.3.7 — 2026-09-20

### APRS-006 — Assistente leigo de conexão APRS-IS
A página APRS/D-PRS deve explicar em linguagem simples o que é o login APRS-IS e mostrar o processo de conexão por etapas, sem exigir que o usuário conheça termos como `logresp`, passcode ou sessão TCP.

Regras:
- explicar que o PU2PNY usa o indicativo configurado + SSID APRS para se identificar no APRS-IS;
- o passcode técnico deve ser tratado internamente pelo software; o usuário final não deve precisar digitá-lo nem conhecê-lo para operação normal;
- exibir uma breve descrição: `APRS-IS é a rede de Internet do APRS. O PU2PNY conecta ao servidor, identifica seu indicativo/SSID e aguarda a confirmação do servidor antes de enviar posição ou mensagens.`;
- o botão `Testar estado agora` deve mostrar etapas reais: Internet → servidor/porta → TCP → identificação enviada → resposta do servidor → verificado/não verificado;
- traduzir `logresp verified/unverified`, timeout e demais erros para PT/EN/ES, mantendo o detalhe bruto apenas no Expert;
- quando falhar, mostrar exatamente o que conferir: indicativo efetivo, SSID, servidor, porta, Internet e resposta do servidor;
- nunca declarar mensagem enviada ou beacon transmitido antes de sessão APRS-IS verificada;
- manter a configuração de localização manual quando HTTP bloquear geolocalização.

### APRS-002 — Toast global de mensagem reafirmado
O requisito existente APRS-002 permanece obrigatório e deve ser global ao painel: ao chegar nova mensagem APRS, mostrar um balão por aproximadamente 5 s em qualquer página aberta do PU2PNY. O balão deve exibir remetente e resumo, ser clicável e abrir `/aprs?to=<remetente>`. O alerta interno deve funcionar mesmo sem permissão de Notification API.

### APRS-007 — D-PRS real integrado ao D-Star
A área APRS / D-PRS deve oferecer D-PRS funcional quando o protocolo D-Star estiver ativo e o rádio fornecer dados compatíveis.

Regras:
- receber e interpretar dados D-PRS/GPS válidos originados do D-Star;
- converter/gatear para APRS-IS somente quando houver identidade e posição válidas;
- não duplicar beacons nem gerar posição inventada;
- indicar claramente origem `D-PRS/D-Star` no histórico/estado;
- falha de D-PRS nunca pode derrubar D-Star, MMDVMHost ou o cliente APRS-IS;
- D-PRS só pode ser marcado HW PASS depois de teste físico com rádio D-Star compatível enviando posição real;
- a UI não pode apresentar `APRS / D-PRS` como completo enquanto o caminho D-PRS não existir.

## 24. Histórico e Últimas atividades enriquecidos — 2026-09-20

### LIVE-012 — Identidade e contexto rico em Histórico/Últimas atividades
As páginas **Histórico** e **Ao Vivo → Últimas atividades/Atividade recente** devem exibir o máximo de contexto útil disponível sobre cada transmissão, principalmente tráfego que chega pela Internet ao hotspot, sem inventar dados e sem consultas externas agressivas.

Campos/estado desejados quando realmente disponíveis:
- direção explícita: `RF → Internet` ou `Internet → RF`;
- indicativo e/ou Radio ID/identidade de origem;
- nome, cidade, estado, país e bandeira quando já resolvidos por fonte local/cache confiável;
- protocolo;
- destino: TG, módulo, refletor, DG-ID ou destino equivalente;
- servidor/refletor/rede efetivamente usados;
- slot e Color Code em DMR quando existentes;
- módulo/refletor em D-Star/XLX e contexto equivalente em YSF/P25/NXDN quando existente;
- horário de início/fim, duração e quantidade de ocorrências;
- tempo acumulado por indicativo no período;
- frequência/perfil local aplicado quando relevante;
- BER/RSSI somente para eventos com telemetria RF real;
- origem lógica do caminho (`Gateway/Servidor`, `Direct`, `Relay`) quando o runtime realmente souber;
- atalhos QRZ e RadioID somente quando houver identificador válido.

Regras:
- para tráfego vindo da Internet, não exibir BER/RSSI como se fossem métricas do transmissor remoto;
- não mostrar IP público/remoto por padrão: é pouco útil operacionalmente e expõe informação desnecessária; detalhes de rede ficam no Expert apenas quando realmente necessários;
- não chamar um hotspot/repetidora/gateway pelo nome se o runtime não fornecer essa identidade;
- valores ausentes devem ser omitidos ou `—`;
- Histórico e Ao Vivo devem usar o mesmo evento normalizado para evitar divergência;
- enriquecimento de identidade deve usar cache local e consultas sob demanda/limitadas, preservando PERF-001.

### DATA-001 — Evento normalizado enriquecido
O Event Bus deve disponibilizar campos normalizados opcionais para suportar LIVE-012, mantendo compatibilidade com eventos antigos. Campos novos só recebem valor quando houver evidência real no gateway/MMDVM/cache de identidade. A UI não deve inferir valores inexistentes.

## 25. Sistema / fuso horário — feedback físico 0.3.7 — 2026-09-20

### UI-016 — Fuso horário ajustável pelo painel sem terminal
A página **Sistema** deve permitir ao usuário alterar o fuso horário pelo painel, sem terminal e sem exigir autenticação Polkit interativa.

Regras:
- validar o fuso contra `/usr/share/zoneinfo`;
- executar somente a alteração de timezone por um mecanismo de privilégio mínimo e explicitamente autorizado;
- não conceder shell/root genérico ao serviço web;
- após aplicar, reler o fuso efetivo do sistema e só então mostrar sucesso;
- hora local, UTC e campo `Fuso horário` devem atualizar automaticamente sem F5;
- se a alteração falhar, preservar o fuso anterior e mostrar mensagem em português; detalhe técnico fica no Expert/log;
- a correção não deve reiniciar RF, MMDVMHost ou gateways;
- `America/Sao_Paulo` deve funcionar quando selecionado e disponível no sistema.

A implementação não deve depender de o daemon web poder editar livremente `/etc`; usar helper/serviço de privilégio restrito ou mecanismo equivalente com superfície mínima.

## 26. Cabeçalho global / Sistema — feedback físico 0.3.7 — 2026-09-20

### UI-017 — Cabeçalho global estável e relógio sem quebra
Todas as páginas operacionais devem usar o mesmo cabeçalho, com a mesma altura e distribuição dos controles na mesma largura de viewport.

Regras:
- o relógio do cabeçalho deve ser inicializado em todas as páginas que exibem `clockLocal`;
- o relógio deve permanecer em uma única linha, com largura mínima suficiente e sem encolher até quebrar verticalmente;
- seletor de idioma, relógio, tema e botão Expert/Básico não podem ser esmagados pela navegação;
- em largura insuficiente, a navegação deve degradar de forma responsiva/rolável sem aumentar desnecessariamente a altura do cabeçalho;
- a página Sistema não pode ter cabeçalho mais alto que Display/Ao Vivo nas mesmas condições;
- a futura unificação Hotspot + Protocolos pode reduzir um item da navegação, mas UI-017 deve funcionar independentemente dessa mudança.

Diagnóstico confirmado no código 0.3.7: `system-0.3.6.html` não chama `PNY.startClock()`, enquanto páginas como Display chamam; o placeholder `--:--:--` permanece e pode ser comprimido/quebrado pelo flex do cabeçalho.

## 27. Expert — dashboard técnico em tempo real — feedback físico 0.3.7 — 2026-09-20

### UI-018 — Expert como cockpit técnico em tempo real
O modo **Expert** deve funcionar como um dashboard técnico/operacional visual, inspirado em painéis de monitoramento/CRM, sem virar uma tela de JSON bruto.

Estrutura obrigatória:
- cards de saúde: versão, uptime, MMDVMHost, gateway ativo, Display Core, protocolo/perfil, uplink e estado geral;
- **Estado Ao Vivo realmente em tempo real**, consumindo o mesmo `/api/live/events` usado pelo Ao Vivo, com fallback leve apenas se SSE falhar;
- gráficos leves em memória do navegador para CPU, temperatura, RAM, load, frequência CPU e throttling;
- gráficos de rede para latência/perda/jitter usando métricas já coletadas/cacheadas, sem executar MTR/traceroute continuamente;
- gráfico/linha RF apenas quando existirem BER/RSSI reais;
- cards de hardware para Raspberry Pi, MMDVM, porta/baud, display, armazenamento e interfaces detectadas quando disponíveis;
- serviços/gateways com estado real e último erro disponível;
- detalhes JSON/log bruto somente em seções expansíveis.

Atualização:
- eventos RF/live via Event Bus/SSE;
- telemetria leve somente enquanto a aba estiver visível;
- nenhuma varredura de hardware, MTR ou consulta externa pesada em loop;
- séries históricas do dashboard ficam preferencialmente em memória do navegador para não aumentar gravações no SD.

### UI-019 — Renomear e enriquecer “Configuração pública”
O bloco `Configuração pública` do Expert passa a se chamar **Resumo operacional**.

Deve exibir, sem segredos:
- indicativo e Radio ID;
- protocolo/perfil ativo;
- RX/TX, offsets, simplex/duplex e modem quando disponíveis;
- servidor/refletor, módulo/TG/DG-ID, slot e Color Code conforme protocolo;
- interface de rede, IP local, DNS efetivo e uplink;
- timezone;
- display configurado/ativo;
- voz, APRS/D-PRS e Direct apenas com estados reais;
- versão instalada.

Senhas, API keys, passcodes, Hotspot Security, credenciais QRZ e outros segredos nunca aparecem.

### SEC-021 — SSH assistido e verificável
O SSH Expert deve continuar **por chave**, sem root e sem senha, mas a interface deve ser utilizável por quem não conhece OpenSSH.

Regras:
- explicar em português o que é uma chave pública SSH e mostrar exemplo completo do formato aceito;
- validar a chave no navegador/backend antes de tentar habilitar;
- diferenciar claramente `chave ausente`, `formato inválido`, `sshd inválido`, `serviço não iniciou` e `SSH ativo`;
- após habilitar, confirmar `ssh.service` ativo e mostrar usuário `radioexpert`, porta e IP local para conexão;
- botão de desativar deve confirmar que o serviço realmente parou;
- não gerar senha/root nem abrir terminal web privilegiado;
- a UI pode oferecer ajuda para criar/importar uma chave, mas nunca exibir ou armazenar chave privada do usuário no hotspot.

O teste atual com `Chave pública SSH inválida` é classificado como falha de UX/preflight; o transporte SSH ainda precisa ser testado com uma chave pública válida antes de ser marcado como HW FAIL ou PASS.

## 28. BER / calibração assistida — 2026-09-20

### RF-013 — Diagnóstico e autoajuste seguro de BER/RXOffset
O PU2PNY deve detectar BER RF persistentemente alto e tentar corrigir automaticamente o **RXOffset** quando houver evidência suficiente e o hardware suportar ajuste por offset.

Regras de segurança:
- atuar somente sobre eventos com BER RF real; tráfego Internet → RF não participa do cálculo;
- não ajustar com uma única transmissão curta;
- exigir amostras suficientes da mesma origem/protocolo e condições minimamente estáveis antes de iniciar qualquer tentativa;
- registrar RXOffset atual e criar rollback antes de testar outro valor;
- variar RXOffset em passos pequenos e limitados, compatíveis com a prática MMDVM_HS, avaliando BER real após cada passo;
- nunca alterar frequência nominal, simplex/duplex, modem, baud ou gateway para tentar “corrigir BER”;
- não executar varredura automática enquanto houver uma chamada/transmissão operacional que não seja a janela de calibração;
- escolher novo offset somente se houver melhora consistente; se não houver melhoria confiável, restaurar exatamente o valor anterior;
- limitar número de tentativas e duração para não causar caça contínua, CPU alta ou gravação excessiva;
- manter DMR fisicamente validado como baseline e executar regressão após qualquer mudança de offset;
- o ajuste automático deve ser cancelável e mostrar progresso/valor atual/resultado.

O sistema pode usar detecção automática de BER alto como gatilho, mas a alteração RF só ocorre dentro do fluxo de calibração protegido.

### RF-014 — TXOffset não pode ser inferido do BER local
O BER observado pelo hotspot mede a qualidade da recepção do próprio MMDVM. Portanto, **TXOffset não deve ser autoajustado apenas a partir desse BER local**.

TXOffset pode ser:
- ajustado manualmente no Expert;
- calibrado com MMDVMCal/equipamento de teste;
- ou futuramente automatizado somente se existir feedback confiável do receptor remoto/rádio.

Sem essa evidência, o PU2PNY deve preservar TXOffset e nunca “adivinhar” correção.

### UI-020 — Assistente BER no Expert e alerta ao usuário
O Expert deve incluir um bloco **Calibração RF / BER** com:
- BER atual e histórico curto/mediana quando houver amostras válidas;
- protocolo, origem e RSSI real associados às amostras;
- RXOffset atual;
- TXOffset atual;
- botão **Tentar ajuste automático de RX**;
- controles manuais de RXOffset e TXOffset com limites, validação, aplicar, testar e restaurar;
- valor anterior sempre visível antes de salvar;
- gráfico leve BER × tempo e, durante calibração, BER × RXOffset;
- explicação simples do que está sendo ajustado.

Se o sistema detectar BER persistentemente alto:
1. tenta primeiro o fluxo automático seguro de RXOffset quando houver condições;
2. se convergir, informa a melhora e mantém o novo valor;
3. se não convergir ou não houver amostras confiáveis, não força alteração;
4. mostra aviso global em português por alguns segundos: **“BER alto detectado. O ajuste automático não conseguiu corrigir com segurança. Clique para abrir a Calibração RF no Expert.”**
5. clicar no aviso abre diretamente a seção de calibração no Expert.

Nenhum aviso deve afirmar defeito de modem ou rádio sem evidência.

## 29. Ao Vivo — medidores de sinal e qualidade — 2026-09-20

### LIVE-013 — Medidores RF, Wi-Fi e Internet no Ao Vivo
A página **Ao Vivo** deve incluir uma faixa compacta de **Saúde da comunicação** com três indicadores independentes: **Sinal RF**, **Wi-Fi/Uplink** e **Internet**.

#### Sinal RF / S-meter
- durante recepção originada do rádio (`RF → Internet`), mostrar um medidor visual tipo S-meter alimentado exclusivamente por RSSI real fornecido pelo MMDVM/runtime;
- mostrar também o valor em dBm quando disponível e BER real ao lado;
- usar `rssi_avg` quando existir, com fallback para `rssi`;
- se não houver RSSI real, mostrar `— / indisponível`, sem fabricar barras ou nível;
- unidades S1..S9 só podem aparecer quando existir conversão/calibração explicitamente confiável para aquele hardware; caso contrário o componente mantém aparência de S-meter, mas sua escala numérica principal é RSSI/dBm;
- o medidor deve reagir ao mesmo Event Bus/SSE da transmissão, sem polling RF adicional.

#### Qualidade Wi-Fi / uplink
- quando a rota ativa usar Wi-Fi, mostrar intensidade/qualidade da **conexão já associada**, sem provocar novo scan;
- classificar de forma simples em `Ótimo`, `Bom` ou `Ruim`, usando critério documentado/centralizado e mostrando o valor bruto do NetworkManager quando disponível;
- se o uplink ativo for Ethernet, mostrar `Ethernet · Link ativo` em vez de inventar qualidade Wi-Fi;
- clicar no indicador abre a página Internet para diagnóstico/canais.

#### Qualidade da Internet
- mostrar `Ótima`, `Boa`, `Ruim` ou `Offline`, reutilizando NET-011 e as métricas cacheadas de latência, perda e jitter já existentes;
- não executar MTR/traceroute continuamente para alimentar o Ao Vivo;
- quando a medição detalhada estiver antiga/indisponível, usar apenas a informação de conectividade disponível e marcar a qualidade como estimada, sem inventar perda/jitter;
- clicar no indicador abre a página Internet no diagnóstico de rota.

### LIVE-014 — Conteúdo contextual para RX/TX
O bloco principal do Ao Vivo deve mudar de conteúdo conforme o estado real.

**Quando RF → Internet (hotspot recebendo o rádio):**
- RX/RF destacado;
- indicativo/Radio ID, nome/local quando disponíveis;
- protocolo;
- destino TG/módulo/refletor/DG-ID;
- frequência RX/perfil ativo;
- duração;
- RSSI/S-meter e BER reais;
- servidor/gateway de saída quando conhecido.

**Quando Internet → RF (hotspot transmitindo para o rádio):**
- TX/RF destacado;
- identidade da estação remota quando disponível;
- protocolo;
- destino TG/módulo/refletor/DG-ID;
- frequência TX/perfil ativo;
- duração;
- servidor/gateway/origem lógica quando conhecida;
- não mostrar RSSI/BER remoto como se fossem medidos localmente.

**Em Standby:**
- protocolo/perfil ativo;
- RX/TX configurados;
- uplink atual;
- estado resumido RF/Wi-Fi/Internet;
- radar leve já definido em LIVE-007.

### UI-021 — Sugestões acionáveis no Ao Vivo
A faixa de saúde pode mostrar somente avisos úteis e clicáveis:
- BER persistente alto → abrir `Expert → Calibração RF / BER` conforme UI-020;
- Wi-Fi ruim → abrir `Internet → canais/qualidade`;
- Internet ruim → abrir `Internet → rota/DNS`;
- gateway/protocolo offline → abrir configuração Hotspot/Protocolos unificada.

Não exibir recomendações quando não houver evidência suficiente e não transformar o Ao Vivo em painel técnico poluído.

## 30. Expert — potência MMDVM e internacionalização completa — 2026-09-20

### RF-015 — Controle seguro de potência RFLevel no Expert
O modo Expert deve permitir aumentar/reduzir o nível de potência de transmissão do MMDVM **somente quando o modem/firmware realmente suportar o parâmetro RFLevel**.

Regras:
- detectar a capacidade do modem antes de habilitar o controle;
- usar o parâmetro `RFLevel` do MMDVMHost/MMDVM_HS quando suportado;
- não apresentar RFLevel como watts/mW calibrados: é um nível de controle do modem, não medição absoluta de potência;
- exibir valor atual e permitir ajuste dentro do intervalo aceito pelo firmware, com passos controlados;
- antes de aplicar: snapshot da configuração ativa + rollback disponível;
- não alterar potência durante TX ativo;
- aplicar de forma transacional e confirmar que MMDVMHost permanece ativo;
- se o serviço falhar ou o modem rejeitar a configuração, restaurar o valor anterior automaticamente;
- não misturar potência RF com `TXLevel`/desvio de modulação; são parâmetros diferentes;
- BER alto não autoriza aumento automático de potência;
- ajuste deve ser global ao modem, salvo evidência futura de suporte real por protocolo;
- registrar o valor efetivo no Resumo operacional/Expert.

### UI-022 — Controle de potência no Expert
Adicionar no bloco RF/MMDVM do Expert:
- `Potência RF do MMDVM (RFLevel)`;
- valor atual;
- slider/controle numérico;
- `Aplicar e testar`;
- `Restaurar valor anterior`;
- explicação simples: `Este controle altera o nível de saída RF do modem. Não representa watts medidos.`;
- controle desabilitado com motivo quando o hardware não suportar RFLevel.

### UI-023 — Internacionalização integral PT/EN/ES
Quando o usuário selecionar Português, English ou Español, **100% do conteúdo operacional do sistema deve usar o idioma selecionado**, sem mistura de idiomas na mesma interface.

Cobertura obrigatória:
- wizard e primeiro acesso;
- menu/cabeçalho/rodapé;
- Ao Vivo, Internet, Hotspot/Protocolos, Direct, APRS/D-PRS, Histórico, Display, Sistema e Expert;
- títulos, botões, labels, placeholders, tooltips, textos de ajuda e confirmações;
- modais, toasts, estados transitórios e mensagens de sucesso/erro;
- mensagens dinâmicas vindas do backend;
- estados como conectado/desconectado, ótimo/bom/ruim, aguardando, aplicando etc.;
- unidades e nomes técnicos universais podem permanecer como termos técnicos quando não houver tradução apropriada (ex.: BER, RSSI, MMDVM, DMR, D-Star, YSF, IP, DNS).

Arquitetura:
- substituir tradução frágil por comparação de texto literal por um catálogo central baseado em chaves estáveis;
- nenhum novo texto visível ao usuário pode ser adicionado diretamente sem chave de tradução;
- backend deve preferir retornar códigos/estados estáveis + detalhes técnicos, permitindo que a UI traduza a mensagem amigável;
- mensagens técnicas brutas permanecem apenas em Expert/log, claramente separadas da mensagem traduzida;
- fallback ausente deve ser detectado em teste/build, não silenciosamente exibir Português em English/Español;
- mudança de idioma deve atualizar a página atual imediatamente sem F5 sempre que possível e persistir entre páginas/reboot do navegador.

O mecanismo atual 0.3.7, baseado em dicionário de correspondência exata, deixa o texto original quando não encontra chave; por isso produz mistura de idiomas e deve ser substituído/endurecido.

## 31. Boot/restauração operacional e display transitório — 2026-09-21

### BOOT-001 — Restaurar automaticamente o último estado operacional após boot
Depois que o hotspot já estiver provisionado, um reboot ou retorno da alimentação deve restaurar automaticamente o último perfil/protocolo operacional salvo, sem exigir que o usuário entre em Protocolos e clique em `Ativar perfil`.

Regras:
- iniciar MMDVMHost e exatamente o gateway correspondente ao protocolo salvo;
- aguardar dependências locais necessárias (dispositivo MMDVM, MQTT e rede quando aplicável) e validar que os serviços permaneceram ativos;
- não regravar RF/perfis em todo boot se bastar iniciar os serviços já configurados;
- se a restauração falhar, manter painel/rede acessíveis, registrar diagnóstico acionável e não declarar `Ligado`;
- `Desligar operacional` deve criar estado persistente explícito; somente nesse caso o reboot permanece operacionalmente desligado;
- `Ligar operacional` pelo painel deve remover esse estado, iniciar MMDVMHost + gateway salvo, confirmar o resultado e exibir erro real se algum serviço não permanecer ativo;
- nenhuma restauração de boot pode apagar perfil, frequência, offsets, identidade ou configuração de rede já aprovada;
- DMR TX/RX fisicamente validado permanece baseline obrigatória de regressão.

### NET-020 — Reconexão e estado Wi-Fi coerentes após boot
Perfis Wi-Fi salvos devem permanecer com autoconnect e prioridade determinística. Depois do boot, se houver associação Wi-Fi real + IPv4, a UI deve mostrar a interface, SSID, RSSI/sinal e qualidade correspondentes.

Regras:
- se a rota padrão estiver em `wlan*` e a interface estiver realmente associada, não mostrar SSID/RSSI como `—`;
- usar estado real da interface/NetworkManager e fallback local via `iw`, sem rescan pesado;
- Wi-Fi 1/2 continuam obedecendo NET-018 e rollback existente;
- Ethernet pode coexistir; a UI deve distinguir link físico de interface efetivamente usada pela rota padrão;
- falha de Wi-Fi não pode ser inferida apenas porque um campo de UI ficou vazio.

### DISPLAY-015 — Estados transitórios não podem deixar a tela física travada
Mensagens de boot, manutenção, atualização, detecção e diagnóstico são temporárias. Ao terminar a operação, a tela física deve voltar ao estado operacional normal apropriado.

Regras:
- `Iniciando` deve evoluir para Standby/Pronto quando o rádio voltar;
- `Manutenção` deve sair automaticamente ao concluir, falhar ou ficar aguardando rede;
- se o operacional estiver explicitamente desligado, mostrar esse estado em vez de `Pronto` falso;
- rotina de manutenção não pode tomar permanentemente a Nextion nem competir com o renderer ativo do MMDVMHost/Display Core;
- nenhum HMI/TFT é gravado automaticamente;
- manutenção continua sem alterar RF, protocolo ou gateway.
