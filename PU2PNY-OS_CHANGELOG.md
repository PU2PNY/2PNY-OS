# PU2PNY-OS — CHANGELOG

## 2026-09-19 — início do ciclo corretivo pós-0.3.3-alpha

### Governança
- Criado backup imutável de trabalho `backup/0.3.3-hw-feedback-20260919` a partir de `pu2pny-os-0.3.3-alpha`.
- Criada branch de correção `pu2pny-os-0.3.4-alpha`.
- Instituídos os documentos canônicos START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX e CHANGELOG.
- `docs/PU2PNY-MASTER-PLAN.md` permanece incorporado por referência; nenhum requisito anterior foi removido.

### Feedback físico 0.3.3 registrado, sem afirmar correção
- AP `pu2pny` e acesso inicial por `pu2pny.local`: aprovados no teste reportado e congelados como baseline.
- Handoff para Wi-Fi do roteador: falhou após salvar/reiniciar; AP de recuperação reapareceu.
- UI reportou AP desligado enquanto o SSID permanecia visível.
- Ethernet permitiu acesso por IP DHCP `192.168.100.22`; comportamento de mDNS/retomada ainda precisa correção.
- Hardware/RF básico: reportado como validado.
- Troca para D-Star e YSF: falhou ao reiniciar MMDVMHost com erro MQTT; rollback devolveu o estado anterior e foi aprovado como mecanismo de segurança.
- Ao Vivo: submenu "+" fecha sozinho; duração precisa maior destaque; BER/RSSI indisponíveis devem ser ocultados.
- Nextion: flicker/retângulo vermelho e estado/dados inconsistentes; novo contrato de standby/RX/TX/erro registrado.
- APRS: Notification permission negada; fallback de painel passa a ser obrigatório.
- Expert/rede: registrados requisitos de visualização, explicação, rota/DNS e acesso SSH seguro.
- Nova tela inicial de idioma registrada.
- Alerta de 180 s para **recepção originada em RF** registrado como alerta de atividade, não como corte/TOT.
- VPN automática rejeitada como comportamento padrão; WireGuard/PU2PNY Direct permanece opt-in.

### Estado
Nenhum item acima é marcado como "corrigido" neste changelog. A implementação e validação entram em commits posteriores com referência aos IDs do MASTER_SPEC e casos do TEST_MATRIX.

## 2026-09-19 — implementação 0.3.4-alpha

### Correções implementadas em código — validação HW ainda pendente
- **NET-002:** perfil Wi-Fi staged agora preserva a flag hidden conforme origem da rede, recarrega o perfil, verifica SSID/senha persistidos antes de reiniciar e, no boot, confirma associação real + IPv4 antes de considerar sucesso.
- **NET-003:** API passa a consultar o runtime real do hostapd/PID antes do estado lógico do controlador.
- **NET-004/006:** network-core publica tipo de uplink/IP; diagnóstico leve passa a expor interface, gateway, hops e DNS efetivos.
- **NET-007:** Cloudflare/Google/OpenDNS podem ser comparados por teste real e cacheado; nenhuma troca é automática.
- **PROTO-005/006:** criado preflight MQTT local e dependência explícita de mosquitto antes do MMDVMHost; troca não-DMR aborta antes de tocar RF se o broker não estiver acessível; rollback agora reinicia explicitamente o MMDVMHost anterior antes dos gateways.
- **LIVE-002/003/004/005/010:** estado do submenu expansível é preservado; BER/RSSI somem sem telemetria; duração ganha destaque; atividade originada em RF pulsa brevemente e mostra aviso após 180 s; tráfego vindo da Internet não usa esse aviso.
- **WIZ-001/UI-001:** primeira visita ganha tela de idioma PT/EN/ES; páginas operacionais ganham rodapé com versão instalada.
- **UI-003:** Expert passa a priorizar cards/estado visual e recolhe JSON em detalhes técnicos.
- **APRS-001:** alerta interno permanece funcional quando Notification API é negada ou exige contexto seguro.
- **DISPLAY-002..005:** overlay de build preserva o driver multi-display existente, remove limpeza total repetitiva da Nextion, atualiza por cadência controlada e acrescenta hora/uplink/IP/estado RF-rede sem sobrescrever HMI/TFT.
- **REL-003:** adicionados prepare/validator 0.3.4; build ARM64/CI ainda precisa executar antes de qualquer divulgação de imagem.

### Evidência
Neste ponto os itens acima estão **implementados em código**. Não são HW PASS até nova instalação/teste no Raspberry Pi + MMDVM + Nextion. DMR permanece baseline de regressão obrigatória.

### Build e publicação 0.3.4-alpha
- GitHub Actions concluiu validação de fonte, build ARM64, normalização, checksum e validação estrutural final sem erro.
- Artefato publicado como prerelease `v0.3.4-alpha`.
- Imagem: `PU2PNY-OS-0.3.4-alpha-arm64.img.xz`.
- SHA-256 da imagem: `4bc808da8f4c3fc259dd72a66a08e68e1a704b5cf13f754692c9864b40282e2c`.
- Nível de validação permanece **SW** até novo ciclo físico. DMR/D-Star/YSF/Nextion/Wi-Fi não foram promovidos a HW PASS por causa do CI.

## 2026-09-20 — feedback HW da 0.3.4 e abertura da 0.3.5

- Criado backup `backup/0.3.4-hw-feedback-20260920`.
- Criada branch `pu2pny-os-0.3.5-alpha`.
- Registrados como baseline físico os itens aprovados: AP/primeiro acesso, tela de idioma, hardware, RF, DMR/XLX com voz de conexão, TOT 180 s, Internet/Ethernet/MTR, submenu + persistente, Protocolos, telemetria Nextion e voz.
- Registradas sem mascarar: regressões Wi-Fi/mDNS, D-Star/YSF/MQTT, sincronização visual do módulo DMR após TG de controle, navegação pós-provisionamento, APRS UX, layout Ao Vivo/Histórico, Nextion, timezone, térmica e update preso.
- Novos requisitos: WIZ-003/004, NET-009/010/011, UI-005/006, PROTO-007, LIVE-006/007, APRS-002, DISPLAY-007/008/009, RF-011, PERF-002, UPDATE-001/002 e TEST-002.

### Correção de classificação DMR/XLX
- Teste físico esclarecido: DMR está transmitindo e recebendo no XLX.
- TG4002/4003 altera o módulo no gateway, mas o painel mantinha a letra do módulo salvo originalmente.
- Nenhuma mudança no caminho RF/DMRGateway foi aplicada para este defeito.
- Implementado tracking de módulo efetivo em runtime a partir dos eventos do DMRGateway; a API do painel passa a usar esse runtime sobre o preset salvo.
- Exemplo obrigatório de regressão: preset C/TG4003 → comando TG4002 → runtime/painel B → falar em TG6 → continuar exibindo B.


### Build e publicação 0.3.5-alpha
- Backend 0.3.5 foi reconstruído a partir do fonte 0.3.4 preservado após o primeiro CI detectar corrupção/sintaxe; a baseline 0.3.4 permaneceu intacta.
- Workflow corrigido para aplicar explicitamente `prepare-0.3.4-alpha.py` antes do overlay 0.3.5.
- Gate do Wi-Fi ajustado para a grafia visual `Wi‑Fi` sem alterar a funcionalidade.
- GitHub Actions run `35513524374` concluiu source, staged source, build ARM64, checksum, validação final, artefato e publicação com PASS.
- Prerelease publicada: `v0.3.5-alpha`.
- Imagem: `PU2PNY-OS-0.3.5-alpha-arm64.img.xz`.
- SHA-256: `616d6089e2e699187e577104b070e757698d6f27a0917b5afb4d27ecaec1f5a9`.
- Validação permanece **SW**; D-Star/YSF/Wi-Fi/Nextion e demais mudanças físicas ainda precisam novo ciclo HW.


## 2026-09-20 — feedback HW da 0.3.5 e abertura da 0.3.6-alpha

### Governança
- Criado backup `backup/0.3.5-hw-feedback-20260920` no commit `98511695e64f0960f4918370c61b11e0f7ab6bb5`.
- Criada branch de trabalho `pu2pny-os-0.3.6-alpha`.
- DMR funcional da 0.3.5 permanece baseline e não pode regredir.
- O usuário determinou que as novas funções deste feedback devem entrar **nesta própria versão corretiva**, e não ser adiadas por conveniência. Registrado como **REL-004**.

### Feedback físico registrado — ainda não marcado como corrigido
- AP e primeiro acesso abriram por `pu2pny.local/wizard`, porém o captive portal deve tentar abrir/oferecer automaticamente o painel quando o cliente suportar.
- Handoff inicial AP→Wi‑Fi falhou e depois a rede apareceu conectada sem tempo de convergência claro.
- Preparação de hardware foi aprovada; exemplos de indicativo/ID precisam ser genéricos e o rótulo deve usar Radio ID quando aplicável.
- Tradução precisa ser integral ao idioma selecionado.
- Segunda rede apresentou erro de script `paused: unbound variable`; configuração detalhada redirecionou indevidamente ao primeiro acesso.
- Troca de DNS acumulou Google + Cloudflare em `DNS efetivo`; qualquer operação precisa feedback visual e retorno ao contexto.
- Rota/diagnóstico devem ser compreensíveis para leigos e usar classificação Melhor/Bom/Ruim/Péssimo.
- APRS precisa localização assistida por permissão e toast global de mensagem.
- Displays precisam layout profissional por capacidade, preservando estados standby/RX/TX.
- Timezone falhou com `Access denied`.
- Manutenção exibiu runner interno sem Última execução/Próxima elegível.
- Expert não apresentou Estado Ao Vivo e atalhos RF/Protocolo levaram à configuração básica.
- Histórico/Última atividade precisam atalhos opcionais QRZ/RadioID quando URL válida.
- D-Star mostrou conectado na UI, mas não houve tráfego RF↔rede e a troca de módulo no rádio não refletiu no painel; voz de conexão ausente.
- YSF recebeu RF local, porém não encaminhou/recebeu tráfego da rede.
- Perfis independentes por protocolo passam a ser requisito para RF/rede.
- Update deve verificar repositório oficial, permitir instalação segura, backup opcional, rollback e downgrade.
- Correções compartilhadas devem ser globais.

## 2026-09-20 — Rádio 1/Rádio 2 e API BrandMeister adicionados ao escopo 0.3.6

### Decisão técnica
- Pesquisa em documentação BrandMeister confirmou que hotspot pessoal usa o Radio ID de 7 dígitos acrescido de alias de **dois dígitos**: `01`, `02`, etc.; um único dígito não é aceito como formato equivalente.
- A UI passa a tratar isso como identificação amigável `Rádio 1 (01)`, `Rádio 2 (02)` sem mudar o Radio ID programado no equipamento.
- A API BrandMeister usa **API Key/token** independente da senha SelfCare e da Hotspot Security. O pedido inicial de `API key/secret` foi normalizado para uma única API Key, evitando inventar um segundo segredo não documentado.
- A chave será armazenada em área privada e a API do PU2PNY só exporá o estado configurada/não configurada.
- A Hotspot Security continua sendo a senha usada pelo DMRGateway para conectar ao master BrandMeister.
- Backup anterior à alteração: `backup/0.3.6-pre-bm-suffix-api-20260920`.

### Implementação 0.3.6 — alias DMR e API BrandMeister
- Adicionado seletor `Rádio 1 (01)` … `Rádio 99 (99)` no primeiro acesso e em Protocolos.
- O backend agora aplica/persiste ESSID DMR `01..99` e rejeita valores inválidos antes de alterar a rede.
- Perfis DMR passaram a carregar o alias junto com frequência/rede.
- Adicionado gerenciamento seguro da BrandMeister API Key por endpoint dedicado; valor nunca é retornado ao navegador depois de salvo.
- API Key e Hotspot Security permanecem credenciais independentes; salvar/remover a API Key não reinicia o caminho DMR.
- DMRGateway helper existente foi preservado. Testes VPS confirmaram os IDs efetivos de 9 dígitos para sufixos `01` e `02`.
- Validação de fonte/VPS: 12 testes determinísticos PASS; build ARM64 e teste físico ainda são gates.

## 2026-09-20 — APRS: falha física de mensagens adicionada à 0.3.6

- Novo feedback HW: mensagens APRS não foram enviadas nem recebidas.
- Criado requisito **APRS-004** para transporte APRS-IS bidirecional real, login verificado, fila persistente, ACK/REJ, retry limitado, deduplicação e diagnóstico visível.
- O estado anterior de `Mensagem enfileirada` deixa de ser evidência de envio.
- Será preservado o baixo consumo: conexão única, sem polling externo pesado, histórico limitado e retries limitados.
- Backup pré-correção: `backup/0.3.6-pre-aprs-msgfix-20260920`.

### Build e publicação 0.3.6-alpha com correção APRS
- O cliente APRS foi atualizado para exigir `logresp verified` antes de transmitir, manter outbox em falha, reconhecer ACK/REJ, deduplicar RX e realizar retry limitado com o mesmo message ID.
- O painel APRS agora mostra login verificado, endereço de recebimento, fila pendente, último RX, último TX de mensagem e último erro.
- Porta 14580 permanece como transporte bidirecional filtrado; pool preferencial passa a `soam.aprs2.net`, com servidores alternativos configuráveis.
- Testes determinísticos APRS: **6/6 PASS**.
- VPS: resolução do pool sul-americano e conexão TCP/14580 com greeting APRS-IS confirmadas; não foi usado indicativo real para fingir teste de mensagem.
- GitHub Actions run `35531259706`: source, staged source, bundle, ARM64, checksum, validação final e publicação **PASS**.
- Prerelease `v0.3.6-alpha` atualizada no target `0967a020eefc0f997211b46d97d3cc3d5600b5db`.
- Imagem SHA-256: `ec1f2676fa2a21715d5da99dc43a25607e8a7433b4580b9122416063e99eaa82`.
- A classificação permanece **Alpha/SW+VPS** para os recursos novos; APRS, D-Star, YSF, Wi-Fi, perfis e displays ainda exigem HW PASS.

## 0.3.6 hwfix2 — 20/09/2026

- Corrige D-Star para o schema real do F4FXL DStarGateway `v20260323-612f388`, eliminando a incompatibilidade que produzia `General.Callsign` vazio, ausência de repetidores e `Log.DisplayLevel=info` inválido.
- Mantém DMR e YSF sem alteração funcional.
- Remove reboot obrigatório após Wi-Fi já validado; mantém rollback para rede anterior/AP.
- Torna busca Wi-Fi tolerante à pausa temporária do AP e disponibiliza busca/manual nos perfis Wi-Fi 1 e 2.
- Corrige parsing de DNS efetivo e torna comparação de resposta dinâmica em cache leve de 180 s.
- Restaura seletor de idioma em instalação não provisionada mesmo com dados antigos do navegador.
- APRS: adiciona teste/ajuda, explicação de geolocalização bloqueada em HTTP e resposta direta ao clicar no remetente.
- RadioID: substitui abertura de JSON bruto por visualização legível sob demanda; QRZ/RID também em atividade recente.
- Update: separa download e instalação; exige 100% + SHA-256 + confirmação de risco antes de aplicar.
- Display: melhora hierarquia TX/RX e inclui identidade/localização/rede em OLED/LCD compactos sem gravar HMI.
- Adiciona teste SW de configuração P25; HW continua pendente.

## 2026-09-20 — displays genéricos e planejamento ARM32

- Registrado DISPLAY-012: OLED SSD1306/SH1106, LCD HD44780/PCF8574 e novos displays genéricos suportados devem operar Standby/TX/RX sem terminal, com layouts proporcionais à capacidade.
- O código existente já possui renderers OLED/LCD e autoaplicação do Display Core, mas permanece HW pendente.
- Registrados ARCH-004, PERF-003 e REL-007 para uma imagem Raspberry Pi 32-bit paralela.
- A imagem será distribuída como .img.xz para cartão SD, não como ISO de PC.
- Inspeção da cadeia completa mostrou que os overlays fixam o builder final em Raspberry Pi OS Legacy Lite Bookworm 64-bit. A estratégia ARM32 foi corrigida para Bookworm Legacy Lite 32-bit de 15/09/2026 + GOARCH=arm GOARM=6; Trixie fica para avaliação posterior, evitando divergência desnecessária.
- Pesquisa externa: Raspberry Pi OS 32-bit segue disponível; a edição Legacy 32-bit Bookworm cobre modelos antigos. MMDVM-Host/MMDVM-Display declaram suporte a Linux 32-bit.
- Nenhuma afirmação de funcionamento ARM32/HW foi feita nesta etapa.

## 2026-09-20 — POC ARM32 concluída em CI

- O runner ARM64 executou o rootfs oficial Raspberry Pi OS Legacy Lite Bookworm `armhf` sem QEMU.
- A cadeia completa 0.3.6 foi portada de forma isolada para `GOARCH=arm GOARM=6` e base Bookworm 32-bit.
- A imagem ARM32 foi gerada, passou integridade/checksum e o validador estrutural completo.
- Todos os binários críticos inspecionados são ELF 32-bit ARM EABI5.
- Artefato experimental de CI criado para o primeiro ciclo HW; não é Alpha/PROD e não altera a linha ARM64.
- Em paralelo, o run ARM64 `35544963950` passou todos os gates e publicou a 0.3.6-alpha atualizada com SHA-256 `8460357f780577abdd12cb5cf91288aad48d27d4c130a96c97d737f8d050a50c`.

## 2026-09-20 — abertura 0.3.7-alpha e nova regra permanente

- Criado backup `backup/0.3.6-pre-direct-display-20260920` e branch `pu2pny-os-0.3.7-alpha`.
- Registrado REL-008: nenhuma correção ou recurso da 0.3.6 pode se perder nesta evolução.
- Registrados P2P-002..006 para PU2PNY Direct real: chamada por indicativo/agenda, primeiro mesmo protocolo, descoberta/NAT, Direct/Relay explícitos, criptografia, pareamento/revogação e control plane próprio.
- Registrado DISPLAY-013 para Moderno V2 em Nextion/OLED e apresentação coerente em LCD/outros displays confirmados.
- Registrado PROTO-013 para aviso de conexão por voz após confirmação real em todos os protocolos tecnicamente capazes.
- D-Star corrigido em software continua HW pendente; nenhuma afirmação de RF↔rede funcional foi promovida sem teste físico.
- Nova imagem só pode sair após TEST-007.

## 2026-09-20 — requisito permanente: tela genérica touch de 7"

- Requisito **DISPLAY-014** adicionado: tela genérica touch de 7 polegadas deve funcionar como interface operacional PU2PNY, sem depender de terminal.
- Escopo inicial: HDMI + USB touch e/ou DSI quando expostos pelo hardware/kernel, com detecção separada de vídeo e toque.
- A interface deve usar o mesmo estado do Display Core/painel, ter operação touch adequada e não afetar RF/gateways se o display falhar.
- Criados TEST-DISPLAY-014A..014D.
- Estado atual: **DOC registrado / HW PENDENTE**. Não afirmar funcionamento físico até teste em tela real.

## 2026-09-20 — feedback HW 0.3.7: DNS exige refresh manual

- Registrado **UI-013**: operações concluídas no painel devem atualizar o estado efetivo na própria tela.
- No teste físico da página Internet, a troca de DNS exibiu corretamente a mensagem de atualização, porém o novo DNS não apareceu automaticamente.
- Para visualizar o estado novo foi necessário recarregar a página; em uma tentativa foram necessárias duas atualizações.
- O defeito é classificado como sincronização UI/backend pós-operação. A troca de DNS em si não será marcada como falha apenas por este sintoma sem evidência adicional.
- Criado `TEST-UI-013-DNS` = HW/browser FAIL.

## 2026-09-20 — feedback HW 0.3.7: Wi-Fi 1/2 e mensagens

- Registrado **NET-018** para separar claramente "salvar perfil" de "trocar conexão".
- "Salvar Rede Wi-Fi 2" não deve conectar/trocar automaticamente; a troca fica em ação explícita própria.
- A busca única que alimenta os dois seletores é aceita e deve ser compartilhada para reduzir custo/tempo.
- Cada perfil deve exibir estado real de salvo/conectado e atualizar a tela dinamicamente.
- Registrado **UI-014**: Mostrar/Ocultar senha nos dois perfis e mensagens no idioma selecionado.
- No teste PT-BR apareceu a mensagem bruta em inglês `signal is aborted without reason`; isso é falha de UI/localização, mantendo o detalhe técnico apenas para Expert/log.
- A troca deve priorizar convergência rápida, mas nunca pulando autenticação, IPv4 e rollback.

## 2026-09-20 — gráfico e recomendação de canal Wi-Fi

- Registrado **NET-019** para a página Internet.
- Será exibido gráfico dos canais Wi-Fi observados, com destaque para o canal real da rede ativa e intensidade das redes vizinhas quando disponível.
- O painel deverá sugerir o melhor canal com justificativa baseada em interferência/ocupação observada, sobreposição e sinal.
- A recomendação não muda automaticamente o roteador.
- Scan será sob demanda/cacheado e deve preservar conexão Wi-Fi, AP de recuperação, CPU/RAM e baixo consumo.
- Criados `TEST-NET-019A..019E`; estado atual DOC/PENDENTE até implementação e validação.

## 2026-09-20 — perfis de protocolo no Ao Vivo

- Registrado **LIVE-011**: os botões por protocolo da tela Ao Vivo passam a funcionar como troca rápida de perfil/protocolo.
- O perfil ativo deve ficar destacado; perfil não configurado leva à configuração em vez de tentar aplicar.
- A troca usa o fluxo transacional existente com progresso real e rollback.
- A filtragem de atividade não será removida; ficará em controle separado e compacto.
- Registrado **PROTO-014**: na página Hotspot os perfis permanecem, mas a ação principal será **Configurar** cada protocolo.
- Objetivo de UX: **Ao Vivo = operar/trocar rapidamente; Hotspot = configurar**.

## 2026-09-20 — feedback HW 0.3.7: PU2PNY Direct

- Página Direct reportada visualmente quebrada; registrado **UI-015** para obrigar uso do layout comum/responsivo do painel.
- Tentativa de chamada sem contatos pareados exibiu `HTTP 409`.
- Inspeção do código confirmou que o backend usa 409 quando a pré-condição de chamada não é atendida, incluindo o caso `pareie o indicativo antes da chamada`.
- Registrado **P2P-007**: a UI não deve expor o código HTTP bruto; `Chamar` deve ser desabilitado/assistido até existir peer pareado.
- Como ainda não há segundo PU2PNY 0.3.7 disponível neste teste, o 409 observado não é evidência de falha de NAT/CGNAT ou Relay. O transporte entre dois hotspots continua HW PENDENTE.
- Criados TEST-P2P-007A..D e TEST-UI-015A..B.

## 2026-09-20 — feedback HW 0.3.7: APRS-IS difícil para usuário leigo

- Atualização de servidor e salvamento apresentaram feedback visual adequado.
- O teste APRS-IS falhou e a mensagem `login APRS-IS ainda não foi confirmado` não explica o conceito ao usuário.
- Inspeção do código confirmou que o cliente já monta internamente a identificação APRS-IS com indicativo/SSID e passcode técnico e só transmite após `logresp verified`.
- Registrado **APRS-006** para transformar isso em fluxo assistido: Internet → servidor/porta → TCP → identificação → resposta → verificado.
- O usuário não deve precisar fornecer ou conhecer o passcode APRS-IS para operação normal do PU2PNY.
- **APRS-002** foi reafirmado: toast global de nova mensagem por ~5 s, clicável, abrindo APRS para resposta. A implementação atual possui aviso apenas dentro da página APRS e não atende ainda ao comportamento global.
- Geolocalização automática em HTTP continua com fallback manual; isso é limitação do contexto do navegador, não falha do motor APRS.

- Registrado **APRS-007**: a área APRS / D-PRS não pode continuar com D-PRS apenas nominal. O código atual ainda contém `Sem DPRS`; D-PRS real via D-Star entra como requisito explícito e permanece HW PENDENTE até rádio compatível ser testado.

## 2026-09-20 — Histórico e Últimas atividades com mais contexto

- Registrado **LIVE-012** para enriquecer Histórico e Ao Vivo/Últimas atividades com direção RF↔Internet, identidade, localização quando conhecida, protocolo, destino, servidor/refletor, módulo/TG, slot/CC, horário, duração, contagem e tempo acumulado.
- BER/RSSI continuam exclusivos de telemetria RF real; tráfego recebido pela Internet não ganha métricas falsas.
- Direct/Relay/Gateway podem aparecer como origem lógica somente quando confirmados pelo runtime.
- IP remoto não será mostrado por padrão; diagnóstico de rede fica no Expert.
- Registrado **DATA-001** para manter um único evento normalizado usado pelas duas telas.
- A implementação atual já possui vários desses campos (direção, identidade, cidade/país, protocolo, módulo/TG, duração, QRZ/RadioID), mas o requisito novo exige ampliar e padronizar o contexto sem inventar dados.

## 2026-09-20 — feedback HW 0.3.7: fuso horário bloqueado

- Registrado **UI-016**: o fuso horário deve ser alterável pelo painel sem terminal.
- Teste físico: ao aplicar o fuso, a operação foi bloqueada com `Access denied`.
- Inspeção do backend mostrou que a rota chama `timedatectl set-timezone` diretamente e, em fallback, tenta atualizar `/etc/localtime` e `/etc/timezone`; essas operações exigem privilégio que o contexto atual do serviço web não possui/autoriza.
- A correção deve usar privilégio mínimo específico para timezone, sem liberar root/shell genérico ao painel.
- Após aplicar, o backend deve reler o timezone efetivo antes de declarar sucesso e atualizar a UI dinamicamente.

## 2026-09-20 — feedback HW 0.3.7: cabeçalho Sistema quebra o relógio

- Registrado **UI-017**.
- No teste físico/browser, ao entrar em Sistema o cabeçalho ficou mais alto e o relógio foi comprimido verticalmente.
- Comparação com Display e inspeção do código mostraram que Sistema não chama `PNY.startClock()`; o elemento `clockLocal` permanece no placeholder `--:--:--`.
- O CSS atual também permite que a pill do relógio encolha/quebre quando a navegação ocupa muito espaço.
- Correção requerida: inicialização global coerente + `white-space: nowrap`/dimensão mínima dos navtools + comportamento responsivo consistente.
- A unificação Hotspot/Protocolos reduz pressão horizontal, mas não substitui a correção estrutural.

## 2026-09-20 — feedback HW 0.3.7: Expert

- Registrado **UI-018**: Expert evolui para cockpit/dashboard técnico em tempo real com cards e gráficos leves.
- Inspeção do código confirmou que Expert usa polling fixo de 15 s para `/api/live`, enquanto Ao Vivo já usa SSE `/api/live/events` com fallback leve. Expert deve reutilizar o mesmo stream.
- Hardware ganhará visualizações de CPU, temperatura, RAM, load, frequência/throttling, serviços e hardware detectado, sem scans pesados automáticos.
- Registrado **UI-019**: `Configuração pública` será renomeada para **Resumo operacional** e exibirá mais contexto seguro, sem credenciais.
- Registrado **SEC-021** para UX do SSH.
- No teste atual, a operação parou em validação de chave pública: `Chave pública SSH inválida`. Isso não prova falha do `ssh.service`; prova que o fluxo atual é inadequado para usuário sem conhecimento de chaves OpenSSH.
- SSH continuará sem root/senha, com chave válida, confirmação do serviço e instruções claras.

## 2026-09-20 — BER alto / ajuste automático assistido

- Registrado **RF-013**: detectar BER RF alto de forma persistente e tentar autoajuste protegido de **RXOffset**.
- A automação exige múltiplas amostras reais, snapshot/rollback, passos pequenos, limite de tentativas e melhora mensurável antes de persistir.
- Registrado **RF-014**: TXOffset não será autoajustado com base apenas no BER medido pelo próprio hotspot; essa métrica descreve o caminho de recepção local e não prova o erro do transmissor do hotspot.
- Registrado **UI-020**: seção `Calibração RF / BER` no Expert com gráfico, RXOffset/TXOffset, ajuste automático de RX, ajuste manual guiado e restauração.
- Se o automático não convergir, toast global leva diretamente ao Expert para ajuste manual.
- Nenhuma correção automática pode mudar frequência nominal, simplex/duplex, modem, baud ou gateway.
- DMR validado continua baseline obrigatória de regressão.

## 2026-09-20 — Ao Vivo: S-meter e saúde da comunicação

- Registrado **LIVE-013**: faixa `Saúde da comunicação` no Ao Vivo com Sinal RF, Wi-Fi/Uplink e Internet.
- S-meter usa apenas RSSI real do MMDVM; sem RSSI, mostra indisponível. Escala S1..S9 não será inventada sem calibração/conversão confiável.
- Wi-Fi usa o sinal da conexão já associada, sem rescan; Ethernet aparece como Link ativo.
- Internet reutiliza NET-011 e diagnóstico cacheado de latência/perda/jitter, sem MTR contínuo.
- Registrado **LIVE-014**: conteúdo do bloco principal muda entre RF→Internet, Internet→RF e Standby, mostrando apenas métricas pertinentes a cada direção.
- Registrado **UI-021**: alertas acionáveis levam a BER/Expert, canais Wi-Fi, diagnóstico de Internet ou configuração de protocolo.
- O código 0.3.7 já possui SSE de Ao Vivo e campos `rssi/rssi_avg/ber`; a nova UI deve reutilizar esse fluxo, sem polling RF adicional.

## 2026-09-20 — potência MMDVM no Expert e tradução integral

- Registrado **RF-015 / UI-022**: controle seguro do `RFLevel` no Expert para modems que comprovadamente suportem o parâmetro.
- O valor não será apresentado como watts/mW; `RFLevel` é um controle do modem. Ajuste será transacional, bloqueado durante TX e com rollback.
- `RFLevel` não será confundido com `TXLevel`/desvio e não será aumentado automaticamente por causa de BER.
- Registrado **UI-023** após teste físico/browser em English mostrar conteúdo ainda em Português.
- Inspeção do i18n 0.3.7 confirmou a causa estrutural: a tradução usa correspondência exata de texto e, quando uma frase não existe no dicionário, retorna o texto original. Isso permite mistura silenciosa de idiomas.
- A internacionalização passa a exigir catálogo central por chaves, cobertura PT/EN/ES de toda UI e mensagens dinâmicas, com teste automático de completude.

## 2026-09-21 — feedback HW 0.3.7: boot não restaura operacional e Nextion fica em estado transitório

- Após corte/retorno de alimentação, o painel voltou acessível, porém MMDVMHost e gateway apareceram parados e o protocolo salvo não reconectou sozinho.
- Para voltar a operar foi necessário entrar em Protocolos e clicar em `Ativar perfil`; isso confirma uma regressão de restauração operacional de boot e não deve ser exigido do usuário final.
- Registrado **BOOT-001**: sistema provisionado deve restaurar automaticamente o último perfil/protocolo após boot, exceto quando houver estado persistente de `Desligar operacional` solicitado pelo usuário.
- O botão **Ligar operacional** também falhou silenciosamente no teste. Inspeção do backend mostrou que ele chama `systemctl start` e ignora o retorno dos serviços, respondendo sucesso genérico mesmo se MMDVMHost/gateway não permanecerem ativos.
- A captura da página Internet mostra rota/default interface em `wlan0` e Internet online, mas SSID/RSSI vazios. Portanto não é correto concluir que o Wi-Fi falhou; o defeito comprovado é inconsistência da leitura/estado exibido. Registrado **NET-020**.
- A Nextion permaneceu em **Iniciando** depois do boot porque o operacional não foi restaurado.
- Ao executar **Manutenção**, a rotina envia estado `maintenance` ao display e, no final, envia novamente `maintenance` com texto `Componentes prontos`; isso explica o display visualmente preso em Manutenção. Registrado **DISPLAY-015** para tornar esses estados transitórios e devolver a tela ao estado operacional real.
- A correção 0.3.8 deve preservar DMR/RF já aprovados, usar inicialização idempotente dos serviços salvos, confirmar o resultado real e manter painel/rede disponíveis em caso de falha.

## 2026-09-21 — imagem 0.3.8-alpha publicada para novo teste físico

- A primeira tentativa após BOOT-001/NET-020/DISPLAY-015 gerou a imagem ARM64, porém o validador final bloqueou a publicação porque a página Direct havia perdido a orientação explícita sobre **CGNAT** exigida pelo gate P2P.
- O gate não foi removido. A página Direct foi corrigida para explicar que o sistema tenta Direct primeiro e usa Relay próprio quando CGNAT/NAT restritivo impedir o caminho direto.
- Novo build GitHub Actions run `35560842909` concluiu source, staged source, build ARM64, XZ, SHA-256, validação estrutural e publicação com **PASS**.
- Prerelease: `v0.3.8-alpha`.
- Target: `3876e50df5f02bea3a1f761c464db5797ab29742`.
- Imagem: `PU2PNY-OS-0.3.8-alpha-arm64.img.xz`.
- SHA-256: `1997b05612159e0d1178e6ab0ab2dc73f1404a8f2a9e7e909e00dfb126557510`.
- A imagem está liberada somente como **Alpha/HW-TEST**. O novo ciclo deve começar por boot/religamento → Wi-Fi → MMDVM/DMR baseline → protocolo ativo → Nextion/manutenção, sem chamar essas correções de HW PASS antes do teste real.

## 2026-09-21 — abertura e implementação corretiva 0.3.9-alpha

### Governança
- Preservado o commit base da 0.3.8 em `backup/0.3.8-hw-feedback-20260921`.
- Criada branch `pu2pny-os-0.3.9-alpha`.
- DMR, Histórico e página Direct aprovada visualmente permanecem baseline; a 0.3.9 não substitui esses componentes por conveniência.

### Feedback físico 0.3.8 incorporado
- Wi-Fi pós-provisionamento e reconexão após reboot funcionaram, porém o último perfil/protocolo não voltou ativo.
- Captive portal não abriu automaticamente no cliente testado.
- D-Star e YSF sofreram rollback por falsos negativos das bridges UDP 20010/4200.
- Nextion ficou presa em estados transitórios e a troca de layout pela MMDVM não foi confirmada.
- Scan Wi-Fi retornou somente a rede associada; gráfico não representou corretamente 5 GHz.
- DNS demorou a refletir estado efetivo; consulta de update produziu falso estado visual de desconexão.
- Expert Ao Vivo não acompanhou eventos em tempo real.
- Timezone e SSH permaneceram inadequados para operação normal.
- Histórico foi aprovado; Direct foi aprovado visualmente; APRS-IS atingiu login verificado.

### Correções implementadas em código — HW ainda pendente
- D-Star/YSF: substituída regex defeituosa por validação determinística do socket UDP local.
- Boot: restauração aguarda serial/MQTT, possui retry controlado e confirma MMDVMHost + gateway.
- Wi-Fi: scan sob demanda combina múltiplas varreduras limitadas e não encerra apenas por encontrar a SSID atual.
- Canal Wi-Fi: UI separa 2,4/5/6 GHz e aumenta a legibilidade.
- DNS: backend relê resolvedor efetivo e reverte se o pedido não for confirmado.
- Expert/Ao Vivo: listeners passam a consumir o evento SSE nomeado `live`.
- Ao Vivo: Saúde da comunicação fica compacta dentro do card principal; perfil rápido fica recolhido.
- Hotspot/Protocolos: configuração integrada sobe para o topo.
- Nextion: MMDVMHost passa a ser writer exclusivo no caminho via modem; layout 2/3 é verificado antes do sucesso; erro não usa 100%.
- Timezone/SSH/operacional/RFLevel/display: pedidos privilegiados usam units `.path` dedicados; o backend não ganha root/sudo genérico.
- SSH confirma serviço e listener TCP 22.
- Timezone possui fallback root controlado apenas para `/etc/localtime` e `/etc/timezone`, seguido de releitura.
- i18n: tradução passa a guardar todos os nós de texto visíveis e aplicar catálogo/fallback guardado, não apenas correspondências exatas.
- Captive portal: opção DHCP 114 usa o endereço canônico 10.43.0.1 e o fallback histórico 10.42 é removido do overlay final.
- Adicionados testes determinísticos e validador estrutural específicos da 0.3.9.

### Estado
As correções acima estão implementadas em fonte. Ainda não são HW PASS. Build ARM64, validação estrutural, SHA-256 e publicação são o próximo gate.

## 2026-09-21 — 0.3.9-alpha publicada para HW-TEST

- Run final GitHub Actions: `35569995279`.
- Commit: `0b35a555a642ced6e13150e434072415e24175b5`.
- Source/staged source/ARM64/XZ/SHA-256/validação estrutural da imagem: PASS.
- Artefato: `PU2PNY-OS-0.3.9-alpha-arm64.img.xz`.
- SHA-256: `09ea47002f60471e3359186717370861e0090bf03c5f5fb3e2dc32456261ec71`.
- Prerelease: `v0.3.9-alpha`.
- Nenhum requisito físico foi promovido para HW PASS sem novo teste no Raspberry Pi/MMDVM/display.


## 2026-09-21 — 0.3.9-alpha — captive portal inicial isolado

- Teste físico confirmou que **somente o primeiro disparo automático do portal ao conectar no AP falhou**.
- Depois da abertura manual de `http://pu2pny.local/`, o restante do onboarding foi aprovado integralmente: scan Wi-Fi automático, senha/salvar, feedback de conexão, handoff, reabertura automática da página, detecção de hardware e avanço para configuração.
- Esses passos passam a ser baseline congelada e não devem ser alterados pela correção.
- Criado backup `backup/0.3.9-pre-captive-fix-20260921`.
- Registrado **NET-021**: durante o primeiro acesso não provisionado, o AP deve permanecer realmente cativo e não oferecer Internet transparente que faça o cliente considerar a rede online.
- O uso atual de DHCP Option 114 com endpoint HTTP local será removido. A opção 114 só deve voltar quando existir API Captive Portal HTTPS válida conforme RFC 8908/8910.
- A compatibilidade continuará usando probes HTTP conhecidos de Windows/Android/Apple/NetworkManager e fallback `10.43.0.1` / `pu2pny.local`.

## 2026-09-21 — feedback HW 0.3.9: D-Star e Hotspot/Protocolos

- Registrado o D-Star HW FAIL: DStarGateway iniciou, carregou hosts e registrou o indicativo, mas a transação voltou por suposta ausência de UDP 20010.
- Identificada causa concreta no código 0.3.9: `udp_listener()` lia a coluna peer de `ss -H -lun`, não a coluna do socket local. O mesmo erro afeta a prova YSF/4200.
- A correção será restrita ao validador de bridge; portas e DMR não serão alterados.
- Hotspot/Protocolos com iframe foi rejeitada visualmente.
- Registrado **UI-024**: manter Hotspot/Protocolos unificado, porém nativo, sem iframe, no padrão visual mestre aprovado na Direct.
- Direct e Histórico ficam congelados como baseline visual e não entram nesta refatoração.
- Reafirmado UI-008: Salvar/Ativar deve mostrar imediatamente estado visual de aplicação; o teste D-Star relatou ausência desse aviso.
- Criado rollback `backup/0.3.9-pre-dstar-hotspot-ui-20260921`.

## 2026-09-21 — feedback HW 0.3.9: Nextion, relógio e readiness D-Star

- Registrado **DISPLAY-016**: Nextion via MMDVM deve ter renderer realmente selecionável, sem dois writers. Moderno V2 volta a usar o Display Core através da bridge MQTT/serial do MMDVMHost; G4KLX/ON7LDS permanece como modo nativo alternativo.
- O painel passa a separar modelo/resolução do display de layout/renderer e incluir perfis 2,4", 2,8", 3,2", 3,5", 4,3", 5", 7" e 10,1", sem promover nenhum modelo novo a HW PASS.
- Nenhum HMI/TFT será gravado automaticamente.
- UI-017 foi reafirmado após novo teste: o relógio continua visualmente incorreto/inalterado. O cabeçalho deverá sincronizar com o horário/fuso do PU2PNY via backend e impedir quebra vertical.
- Registrado **PROTO-015**: D-Star/YSF ganham verificação do INI efetivo e janela de readiness após a ordem MMDVMHost → gateway, mantendo rollback.
- Criado rollback `backup/0.3.9-pre-nextion-clock-20260921`.

## 2026-09-21 — DISPLAY-017 auto-detection + auto-provisioning
- Adicionado requisito para detecção no boot, painel e hotplug.
- Definida prioridade USB/UART/I2C/SPI/DRM-touch.
- Nextion deve usar `connect/comok`; OLED 0x3C/0x3D só recebe identificação exata quando houver prova suficiente.
- Catálogo de TFT passa a exigir URL + SHA-256 reais; campos desconhecidos permanecem nulos/unpublished.
- Flash TFT será sempre confirmado pelo usuário e transacional; não haverá sobrescrita silenciosa.
- MMDVMHost mantém ownership do modem durante operação; detector não pode roubar a serial.
- Criado rollback `backup/0.3.9-pre-display-autoprovision-20260921`.

## 2026-09-21 — prioridades concretas de hardening 0.3.9
- Registrados PROTO-016, BOOT-002, PROTO-017, NET-022, UPDATE-006, LIVE-015, SEC-022 e UI-025.
- D-Star/YSF passam a exigir estado intermediário waiting_bridge e evidência de health-check.
- Restore passa a ter sequência explícita serial→MQTT→MMDVMHost→gateway→health.
- MQTT preflight vira gate obrigatório, com endpoint/erro legível.
- Wi-Fi deixa de resumir conexão em uma única flag e passa a estados associação→IPv4→rota→DNS.
- Expert ganhará diagnóstico das portas UDP, writer do display, último rollback e restore.
- Direct e Histórico permanecem congelados como baseline.
- Criado rollback `backup/0.3.9-pre-stability-hardening-20260921`.

## 2026-09-21 — abertura 0.3.10-alpha
- Criada branch `pu2pny-os-0.3.10-alpha` e rollback `backup/0.3.9-pre-0.3.10-image-20260921`.
- Hotspot/Protocolos nativo sem iframe entra no overlay final.
- Wizard ganha overlay real de Salvar/Ativar.
- D-Star/YSF usam porta local correta + wait-for-bridge + evidência/rollback.
- Restore de boot passa a provar MQTT e bridge do protocolo.
- Wi-Fi passa por associação → IPv4 → rota → DNS antes de conectado.
- Nextion ganha dois writers mutuamente exclusivos: PU2PNY Moderno V2 via MQTT/MMDVM ou MMDVMHost nativo.
- Detector/catálogo de displays entram na imagem; TFT continua sem gravação silenciosa.
- Relógio global sincroniza com timezone do PU2PNY.
- Expert recebe diagnóstico sob demanda de UDP/MQTT/display/restore/rollback.
- Criado workflow/release independente 0.3.10-alpha; publicação continua condicionada a ARM64 + XZ + SHA-256 + validação estrutural.

## 2026-09-21 — 0.3.10-alpha publicada
- Corrigidos gates herdados que ainda exigiam iframe, renderer antigo Nextion e implementação antiga de readiness D-Star/YSF.
- Os gates foram alinhados aos requisitos UI-024, DISPLAY-016 e PROTO-016 sem remover proteção.
- Run final `35600972295` passou source, staged source, ARM64, XZ/SHA-256, validação estrutural, transferência e publicação.
- Imagem publicada: `PU2PNY-OS-0.3.10-alpha-arm64.img.xz`.
- SHA-256: `9bbbffe310401dbe4dffe10316a11fc8647465112070592275a45bee3d0c23ee`.
- Release permanece Alpha/HW-TEST até a validação física.

## 2026-09-21 — abertura corretiva 0.3.11-alpha após teste HW da 0.3.10
- Criado rollback `backup/0.3.10-hw-feedback-20260921` e branch `pu2pny-os-0.3.11-alpha`.
- Registrados HW-003, RF-016, WIZ-006 e UI-026.
- A etapa Hardware deixa de reabrir a serial da MMDVM para tentar confirmar Nextion antes do MMDVMHost; a confirmação via modem fica para depois que o rádio estiver ativo.
- O aplicador RF continua usando o baud realmente detectado, mas deixa de atribuir qualquer falha ao baud: serializa contra o detector de display, prova MQTT, tenta inicialização controlada, registra diagnóstico e faz rollback.
- O wizard limpa erro transitório quando a MMDVM está confirmada e restaura o avanço automático de 5 s.
- A camada de idioma passa a normalizar mensagens técnicas conhecidas para uma chave/canonical PT e então renderizar PT/EN/ES conforme a escolha do usuário.
- Nenhuma alteração foi feita para mudar frequência, offsets, DMRGateway ou o baseline RF/DMR aprovado.

## 2026-09-21 — 0.3.12-alpha — correção da regressão MMDVMHost/MQTT da 0.3.11

- Preservada a 0.3.11 em backup/0.3.11-pre-0.3.12-fix-20260921.
- Criada branch pu2pny-os-0.3.12-alpha sem refatorar módulos aprovados.
- RF-017: hardware probe e RF apply passam a compartilhar /run/2pny/mmdvm-serial.lock; a passagem de ownership para MMDVMHost espera a identificação terminar.
- PROTO-018: preflight MQTT passa de teste TCP para MQTT CONNECT/CONNACK real.
- PROTO-018: build passa a exigir o pacote mosquitto e adiciona listener local exclusivo em 127.0.0.1:1883.
- O gate MQTT aprovado permanece obrigatório; falha de broker não é mascarada como erro de baud.
- UI-027: wizard mantém a tela de seleção bilíngue, remove rótulos-base desnecessariamente em inglês no restante e ganha traduções exatas adicionais PT/EN/ES para onboarding e erros dinâmicos.
- Validação 0.3.12 passa a conferir binário Mosquitto, configuração loopback, preflight protocolar, lock compartilhado e idioma, além de toda regressão herdada.
- DMRGateway, RF frequencies/offsets, Direct e Histórico não foram alterados por esta correção.
## 2026-09-21 — feedback HW 0.3.12-alpha: Wi-Fi aprovado; MMDVM/TGIF/i18n pendentes

- Confirmado **HW PASS** na 0.3.12 para reconhecimento do Wi-Fi, conexão automática e abertura direta do painel. Esse fluxo passa a baseline congelada para a próxima correção.
- Confirmado **HW FAIL** no módulo de configuração MMDVM: o erro continua impedindo o avanço do wizard.
- Comparação com a 0.3.6 mostrou diferença objetiva: o bootstrap antigo primeiro provava MMDVMHost com MQTT/display e redes desativados; a 0.3.12 passou a exigir MQTT já na primeira ativação.
- Registrado **RF-018**: recuperar a semântica comprovada de bootstrap mínimo da 0.3.6 como Fase A e aplicar MQTT/display/protocolo somente na Fase B transacional, preservando os recursos atuais e os gates PROTO-017/018 antes da operação completa.
- Confirmado **HW FAIL i18n**: ainda há mistura de PT/EN. Registrado **UI-028** para migrar mensagens normais a chaves estáveis PT/EN/ES, deixando substituição pós-renderização apenas como compatibilidade.
- Registrado **HW FAIL TGIF com causa ainda não isolada**: Security Key foi fornecida, MMDVM recebeu RF do HT, mas não houve confirmação de login/atividade no servidor.
- A inspeção do código mostrou que a Security Key fornecida é repassada ao `Password=` do DMRGateway; não foi encontrada evidência de que copiar/colar a chave seja a causa.
- Registrado **PROTO-019** para isolar TGIF: modo seguro explícito, ESSID/Network ID correto, configuração DMRGateway compatível, diagnóstico de autenticação sem vazar segredo e distinção entre RF local e entrega à rede.
- Nenhum código de DMR baseline, Wi-Fi aprovado, Direct ou Histórico foi alterado neste registro.
- Criada branch de diagnóstico `test/0.3.12-hw-findings-20260921` antes de qualquer futura correção.

## 2026-09-21 — abertura e implementação da 0.3.13-alpha

- Criado rollback `backup/0.3.12-pre-0.3.13-20260921` e branch `pu2pny-os-0.3.13-alpha`.
- O overlay corretivo não substitui os módulos Wi-Fi aprovados fisicamente na 0.3.12.
- **RF-018:** restaurado o bootstrap mínimo comprovado da 0.3.6: primeira partida com MQTT/display logging desativados e todas as redes desativadas; somente depois da prova da UART entra a Fase B.
- Identificado defeito concreto no caminho 0.3.12: o `ExecStartPre` de MMDVMHost roda como `mmdvm`, enquanto o preflight tentava escrever diagnóstico em `/run/2pny`. Na 0.3.13 o preflight do service usa `--no-publish --respect-log-level`, e o apply root continua responsável pelo diagnóstico persistente.
- Removido `Requires=mosquitto.service` do bootstrap; Mosquitto permanece como `Wants` e continua obrigatório na Fase B operacional via CONNECT/CONNACK real.
- **PROTO-019:** TGIF ganhou perfil separado baseado no contrato do DMRGateway embarcado, com `TGRewrite`/`SrcRewrite`, Security Key preservada, modo seguro/legado explícito e segredo ausente do JSON público.
- **UI-028:** wizard recebeu base PT coerente para os rótulos reportados, traduções exatas PT/EN/ES e proteção contra exibir o idioma-base antes de a seleção ser aplicada.
- DMR XLX/BrandMeister, Direct, Histórico, frequências e offsets permanecem fora do escopo da correção.
- Adicionados prepare, testes de regressão e validador estrutural próprios da 0.3.13. Publicação continua bloqueada até ARM64 + XZ + SHA-256 + validação final.

## 2026-09-21 — logotipo oficial para próximas versões
- O logotipo enviado pelo mantenedor foi definido como referência visual oficial do PU2PNY-OS.
- Registrado **UI-029** para adoção nas próximas versões.
- A 0.3.13-alpha atualmente em validação permanece sem essa mudança para preservar o escopo corretivo e evitar regressão durante o build.
- A primeira integração deverá usar asset otimizado, manter proporção/contraste e não aumentar de forma relevante o peso do painel ou o uso de recursos.

## 2026-09-21 — 0.3.13-alpha publicada
- Run `35631645881` concluiu com source, build-arm64 e publish em **success**.
- Imagem publicada: `PU2PNY-OS-0.3.13-alpha-arm64.img.xz`.
- SHA-256: `1cb0f862c09825b25394cf0cfbb6812d7e24c04a5034cab9940bc90763db67ec`.
- O build aplicou toda a cadeia herdada e o overlay 0.3.13; staged source, regressões novas/herdadas e validador final passaram.
- RF-018, PROTO-019 e UI-028 continuam aguardando validação física; a release permanece Alpha/HW-TEST.

## 2026-09-21 — feedback HW 0.3.13 e abertura da 0.3.14-alpha
- Confirmado **HW PASS** do bootstrap mínimo MMDVM da 0.3.13: a Fase A isolou e validou UART/MMDVM.
- Confirmado **HW FAIL** na Fase B MQTT com a mensagem de broker local não pronto e rollback.
- Confirmado problema de UX do wizard: em falha MQTT o usuário não deve sair da Configuração Básica.
- Criados **PROTO-020**, **WIZ-007** e **REL-007**.
- Criado rollback `backup/0.3.13-pre-0.3.14-20260921` e branch `pu2pny-os-0.3.14-alpha`.
- Escopo 0.3.14: tornar o Mosquitto local determinístico, habilitado e validado por CONNECT/CONNACK com espera/retry limitados; manter etapa 3 em qualquer falha de apply.
- Wi-Fi aprovado da 0.3.12, bootstrap MMDVM que passou na 0.3.13, Direct, Histórico, RF/baud/frequências e caminhos não relacionados permanecem congelados.

## 2026-09-21 — abertura da 0.3.15-alpha: remover bloqueio MQTT do onboarding DMR
- Feedback físico da 0.3.14: MMDVM continua passando no teste básico, porém o broker MQTT ainda impede concluir a Configuração Básica.
- Revisão do GitHub confirmou o comportamento funcional 0.3.6/0.3.8: RF apply encerrava após MMDVMHost ativo com MQTT/display logging desativados; DMR helper também mantinha MQTTLevel=0 e não fazia preflight do broker.
- Identificada regressão arquitetural atual: Fase B MQTT foi inserida dentro do RF apply e a 0.3.14 também inseriu preflight MQTT antes do helper DMR.
- Registrados PROTO-021, WIZ-008 e REL-008.
- Criados rollback `backup/0.3.14-pre-0.3.15-20260921` e branch `pu2pny-os-0.3.15-alpha`.
- Escopo: remover somente esses gates no onboarding DMR, preservando todo restante.

## 2026-09-21 — 0.3.15-alpha publicada
- Removidos os dois bloqueios MQTT indevidos do primeiro provisionamento DMR: Fase B MQTT dentro do RF apply e preflight MQTT antes do helper DMR.
- Mantido `MQTTLevel=0` no bootstrap MMDVM e no helper DMR, conforme semântica comprovada em 0.3.6/0.3.8.
- Mosquitto e o preflight MQTT continuam presentes para recursos que realmente habilitem MQTT; não foram removidos do sistema.
- Dois gates antigos do validador ainda exigiam o comportamento superado e bloquearam builds intermediários. Esses gates foram alinhados ao PROTO-021; nenhuma imagem desses builds foi publicada.
- Run final `35647296002`: source, regressões, staged source, ARM64, XZ, SHA-256, validação final e publish em **success**.
- Publicada `v0.3.15-alpha`, SHA-256 da imagem `4caea4a281c67cd8c5a15ba134e6720dbf4adb7a675a4395052ff13be10bb690`.
- Release permanece **Alpha/HW-TEST** até o teste físico confirmar o avanço da Configuração Básica.

## 2026-09-21 — abertura da 0.3.16-alpha, somente bugs

- O mantenedor declarou o restante do sistema aprovado; a partir deste ciclo, módulos sem bug reportado ficam congelados.
- Criados `REL-009`, `NET-023`, `NET-024`, `LIVE-016`, `UI-030`, `PROTO-022`, `P2P-006`, `APRS-012`, `DISPLAY-018`, `SEC-023`, `UI-031` e `PROTO-023`.
- Criado rollback `backup/0.3.15-pre-0.3.16-20260921` e branch `pu2pny-os-0.3.16-alpha`.
- Diagnóstico inicial:
  - cache de conectividade do backend pode manter estado por 15 s e a página Internet consulta em intervalos maiores;
  - scan Wi-Fi pode ficar preso em estado `error` persistido;
  - RSSI/BER pode ser associado a evento não-RF;
  - overlay de ativação fecha ~1,2 s após helper local, antes de prova remota;
  - DMRGateway permite tráfego network e voz XLX escreverem no mesmo slot no mesmo ciclo;
  - APRS usa apenas um endpoint regional por tentativa;
  - Nextion via modem regrediu do writer nativo comprovado na 0.3.8 para dependência da bridge MQTT/Display Core;
  - os requests privilegiados usam `PathChanged`, sujeito a gatilho inconsistente;
  - gerador D-Star usa `ReloadTime` onde o gateway embarcado espera `ReloadTimer` e mistura banda local com módulo remoto.
- Nenhuma frequência, offset, baud, fluxo DMR de rede, TGIF, Wi-Fi onboarding visual aprovado, Histórico ou módulos não citados será alterado fora do mínimo necessário.


## 2026-09-22 — build e publicação 0.3.16-alpha

- A correção permaneceu bugfix-only sobre a 0.3.15; módulos sem defeito reportado não foram redesenhados.
- Pesquisa upstream confirmou para o MMDVMHost atual: D-Star local em módulo C, rede loopback 20010/20011 e Nextion com `Port=modem`/layout ON7LDS suportados. O D-Star foi alinhado para `Band=C` local, independente do módulo remoto do refletor.
- A Nextion via modem voltou ao writer nativo do MMDVMHost; OLED/LCD/Nextion direta preservam seus caminhos existentes.
- APRS-IS ganhou provisionamento automático para mensagens, fallback limitado regional→mundial e distinção explícita entre `waiting_ack` e ACK confirmado, sem inventar posição.
- DMRGateway recebeu somente um patch estreito de arbitragem: voz de sistema/XLX bloqueia áudio NETWORK→RF concorrente no mesmo slot enquanto WAITING/SENDING; RF→rede e o outro slot não são bloqueados.
- Direct renova rendezvous antes de lookup e usa janelas limitadas mais tolerantes, sem alterar fingerprint/pareamento.
- Wi-Fi/Internet, Ao Vivo, overlay de protocolo, timezone/SSH e D-Star receberam apenas as correções registradas em NET-023/024, LIVE-016, UI-030, SEC-023/UI-031 e PROTO-023.
- Builds intermediários falharam somente em gates CI obsoletos (`PU2PNY Moderno` e `PathChanged`) que contrariavam os requisitos novos; os gates foram corrigidos, sem reintroduzir comportamento superado.
- Run final `35669972163`: source, regressões, staged source, ARM64, XZ, SHA-256, imagem montada, artefato e publicação em **success**.
- Publicada prerelease `v0.3.16-alpha` no commit `1c5ec75548374ac13be6948fc86eae46bd9eeddf`.
- Imagem: `PU2PNY-OS-0.3.16-alpha-arm64.img.xz` (614130916 bytes).
- SHA-256: `8329b976c733054787052484974fc86663e337bfdce4b31e461361fbfa465426`.
- Estado permanece **Alpha/HW-TEST**. Nenhuma correção 0.3.16 é declarada HW PASS antes do novo teste físico em Raspberry Pi + MMDVM + Nextion/rede real.

## 2026-09-21 — abertura da 0.3.17-alpha: D-Star RX/comandos e timezone

- O mantenedor determinou que tudo que não foi citado como defeito na 0.3.16 deve ser considerado ótimo/perfeito e congelado.
- Criados `REL-010`, `PROTO-024`, `LIVE-017`, `UI-032` e `SEC-024`.
- Criados rollback `backup/0.3.16-pre-0.3.17-20260921` e branch `pu2pny-os-0.3.17-alpha`.
- Feedback HW: DStarGateway já conecta e recebe da rede, porém o tráfego não chega ao RF/MMDVM e não aparece no Hotspot.
- Diagnóstico de fonte: o gateway 0.3.16 usa `Band=C`, mas MMDVMHost ainda recebe `Module=<módulo remoto>`; isso quebra o contrato de identidade local que deveria ser C/C.
- Diagnóstico de comandos: `ReflectorReconnect=Fixed` bloqueia o handler de comandos `L/U` no DStarGateway embarcado. O código upstream já implementa `I`, `E`, `L`, `U` e troca de refletor/módulo via URCALL; a correção habilitará esse caminho existente.
- O fuso continua HW FAIL; o fluxo será corrigido para esperar confirmação real do helper privilegiado e do Timezone aplicado.
- Nenhuma outra página, protocolo, rede, display, DMR, APRS, Direct, RF, frequência, offset ou baud entra neste ciclo.

## 2026-09-22 — abertura 0.3.18-alpha antes do reteste

- A 0.3.17-alpha passou CI, mas não foi entregue como candidata final após revisão adicional do upstream.
- Encontrado defeito objetivo: o DStarGateway pinado instala seus arquivos de áudio/status em `/usr/local/share/dstargateway.d/`; o gerador 0.3.17 ainda configurava `/usr/share/2pny/audio/dstar/`.
- Isso impediria respostas de voz/status mesmo com os comandos I/E/U/L reconhecidos pelo gateway.
- Criado `REL-011`; branch `pu2pny-os-0.3.18-alpha`; rollback `backup/0.3.17-pre-0.3.18-20260922`.
- Nenhum outro módulo será alterado. Os gates 0.3.18 passam a exigir a presença física de `en_GB.ambe` e `en_GB.indx` dentro da imagem.

## 2026-09-22 — SEC-025 incorporado à 0.3.18 antes da publicação
- O mantenedor solicitou desligar, reiniciar e trocar perfil pelo próprio rádio D-Star.
- Criados **SEC-025** e **REL-012**; rollback `backup/0.3.18-pre-sec025-20260922`.
- Comandos definidos: `PNYARM`, `PNYOFF`, `PNYRBT`, `PNYDMR`, `PNYDST`, `PNYYSF`, `PNYP25`, `PNYNXD`, `PNYPOC`.
- O DStarGateway somente converte URCALL reservado em request local; ação privilegiada é executada por helper one-shot com allowlist fixa.
- Toda ação administrativa exige MYCALL do proprietário e janela `PNYARM` de 30 s consumida uma vez.
- A troca por rádio só ativa perfil já salvo; não altera frequência, offset, servidor ou credenciais.
- Shutdown por software não é confundido com corte físico de 5 V.
- REL-011 permanece válido para a correção do pack de voz; REL-012 documenta a ampliação explícita de escopo antes da publicação.


## 2026-09-22 — abertura e implementação 0.3.19-alpha

- Criados REL-013, NET-025/026, LIVE-018, UI-033/034, PROTO-025/026, APRS-013, DISPLAY-019, SEC-026/027 e DATA-002.
- Criado rollback `backup/0.3.18-pre-0.3.19-20260922`; trabalho em `pu2pny-os-0.3.19-alpha`.
- DNS: removido `nmcli device reapply` do fluxo de aplicação de DNS; o perfil salvo é reativado no mesmo device e o DNS efetivo continua verificado/rollbackável.
- Internet: Wi-Fi 1 mostra a conexão ativa, Wi-Fi 2 exclui a atual e oferece alternativas; gráfico identifica canal atual/melhor; rótulos técnicos foram simplificados.
- Ao Vivo/Sistema: dados RF/DMR transitórios ficam ocultos em standby; TOT 180 s passa a regressivo durante RF TX.
- Protocolos: título simplificado, MHz com seis casas, entrada ponto/vírgula, estados Salvando/Atualizando e ajuda específica por protocolo.
- D-Star: ajuda DR em linhas; módulo local C preservado; módulo remoto só aparece conectado com evidência `link_state=linked`; Expert mostra rejeições de header/RPT1.
- APRS: toast interno de 5 s fora da página APRS; não foi criada tentativa de burlar exigência HTTPS da Notification API.
- Display: detector limitado após network-online e splash 0–100 no renderer compatível; nenhuma gravação HMI/TFT automática.
- Timezone: helper passa a drenar requests pendentes de maneira limitada e emitir resultado por request.
- Voz: defaults avisos/horário ativos somente quando ainda não existe preferência salva.
- SSH: geração de par no navegador; chave privada fica no cliente e apenas a pública é enviada ao helper existente.
- Expert: Estado Ao Vivo oculto sem TX; log de erros sob demanda, redaction e download em texto.
- CI 0.3.19 adicionada sobre a cadeia completa 0.3.18, com gates focais e validação de imagem. Estado CI/HW será atualizado após evidência.


## 2026-09-22 — 0.3.19 ampliada: YSF/C4FM e duplex

- O mantenedor adicionou regressão YSF/C4FM e modo duplex ao escopo antes de concluir a 0.3.19.
- Criados **REL-014, RF-019, LIVE-019, PROTO-027 e PROTO-028**.
- Criado rollback específico `backup/0.3.19-pre-ysf-duplex-20260922` no commit `66daecb821b5bb6ded31ed7f1449153ffd4f516b`.
- YSF atual: `gateway_active` sem confirmação remota. A investigação do binário pinado mostra que o startup usa busca exata de nome; o gerador pode produzir nome completo diferente do `Startup`. A correção deve resolver o refletor deterministically sem alterar a bridge 3200/4200.
- DMR duplex atual: helper mantém slots locais derivados do perfil simplex; será corrigido para manter TS1/TS2 disponíveis localmente em `Duplex=1`, preservando semântica de um único slot da rede XLX.
- Ao Vivo em duplex passará a identificar RX/TX explicitamente com seis casas.
- O helper de modo passará a reforçar `General.Duplex` conforme `use_mode` para todos os protocolos.
- Nenhum baud, offset ou frequência será recalculado. DMR simplex permanece baseline obrigatória.
- Tudo continua **HW PENDENTE** até reteste físico.


### 2026-09-22 — correção do builder D-Star antes da publicação 0.3.19
- Corrigida a ordem do hook `SEC-025/REL-012`: o patch de comandos administrativos D-Star agora é aplicado imediatamente antes de `make -C DStarGateway`.
- O anchor genérico anterior podia executar só depois da compilação/limpeza do fonte e causar `DStarGateway source for PU2PNY radio-admin patch not found`.
- Escopo: **build/reprodutibilidade apenas**; nenhuma mudança funcional adicional em RF, D-Star, YSF ou DMR.

- Ajuste adicional do gate de build: o alvo real do builder é `make -j"$JOBS" DStarGateway/dstargateway`; o patch SEC-025 agora ancora exatamente nessa chamada, antes da compilação.


## 2026-09-22 — Nome canônico do repositório e título da aba
- Rollbacks criados: `backup/0.3.19-pre-repo-title-rename-20260922` e, após avanço concorrente da branch, `backup/0.3.19-pre-repo-title-rename-20260922b`.
- Criado ARCH-005: nome canônico do repositório passa a ser `PU2PNY/PU2PNY-OS`.
- Criado UI-035: a aba do navegador deve mostrar somente `PU2PNY-OS`, sem versão e sem nome da página.
- Fontes HTML atuais, JS comum e etapa de preparação da imagem passam a normalizar o título; páginas herdadas também ficam cobertas pelo build.
- Adicionados TEST-ARCH-005A e TEST-UI-035A.
- Nenhuma alteração em RF, modem, MMDVMHost, DMRGateway, gateways de protocolo, rede ou boot.


### 2026-09-22 — identidade visual futura
- Criado **UI-036**: a partir da versão posterior à 0.3.19-alpha, o painel deve incorporar o logotipo oficial fornecido pelo mantenedor.
- O ativo **não** será introduzido na 0.3.19-alpha durante o build/validação para evitar ampliar novamente o escopo desta release.
- Criado **TEST-UI-039** para presença do ativo, fallback, carregamento local e ausência de regressão visual.


### 2026-09-22 — TGIF preservado no helper duplex da 0.3.19
- A validação final da imagem detectou uma regressão real antes da publicação: o helper DMR 0.3.19 havia preservado portas/DMR duplex, porém perdido a lógica TGIF já aprovada na 0.3.13.
- Criado rollback adicional `backup/0.3.19-pre-tgif-duplex-fix-20260922`.
- Restaurados `Name=TGIF_Network`, `TGRewrite/SrcRewrite` local↔TS2, senha TGIF entre aspas, distinção `legacy/secured` e `auth_mode`.
- Em duplex, os rewrites TGIF agora são gerados para os dois slots RF locais, mantendo o lado de rede TGIF em TS2. Em simplex, permanece o slot selecionado pelo operador.
- BrandMeister continua usando pass-through e, em duplex, cobre TS1/TS2. XLX continua com um único slot remoto selecionado.
- Nenhuma porta, baud, offset, frequência ou credencial foi alterada fora dessa restauração.
