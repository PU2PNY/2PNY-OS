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
