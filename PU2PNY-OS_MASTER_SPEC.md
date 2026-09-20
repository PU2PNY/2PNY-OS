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
Manter a imagem ARM64 como linha principal e criar uma imagem ARM 32-bit (armhf) separada, baseada inicialmente em Raspberry Pi OS Lite Trixie 32-bit da mesma data/base da linha ARM64 para reduzir divergência de userland. Raspberry Pi OS Legacy Lite Bookworm 32-bit permanece fallback de compatibilidade caso o teste HW em modelos antigos mostre regressão. O artefato deve ser uma imagem de cartão Raspberry Pi (.img.xz), não ISO de PC. O alvo mínimo é Raspberry Pi Zero/Zero W, 1A+/1B+ e 2B, mantendo compatibilidade com modelos 32-bit posteriores quando a base oficial suportar.

O binário Go próprio deve ser compilado com GOOS=linux GOARCH=arm GOARM=6 para cobrir ARMv6 e superiores. Gateways/MMDVM e demais binários nativos precisam ser compilados dentro do rootfs armhf ou por toolchain compatível; nenhum binário ARM64 pode ser reutilizado no artefato 32-bit.

### PERF-003 — Perfil para Raspberry Pi antigos
Na linha 32-bit, priorizar Raspberry Pi OS Lite, serviços mínimos, sem desktop, logs limitados, polling reduzido, cache limitado e nenhuma função visual pesada no host. O painel web continua completo, mas processamento opcional de alto custo deve permanecer sob demanda. Em Raspberry Pi Zero/1 com 512 MB, estabilidade de RF/rede tem precedência sobre efeitos visuais ou coleta não essencial.

### REL-007 — Gate independente ARM32
A imagem ARM32 só pode ser publicada como Alpha quando: build armhf completo, xz -t, SHA-256, montagem/validação estrutural, confirmação de arquitetura dos binários críticos e boot/teste HW em pelo menos um Raspberry Pi ARMv6 ou ARMv7. O PASS ARM64 não vale como HW PASS ARM32 e vice-versa. A falha do pipeline 32-bit não pode bloquear nem alterar silenciosamente a imagem ARM64 já validada.
