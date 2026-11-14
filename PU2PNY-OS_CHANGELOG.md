## 2026-11-14 — PU2PNY-OS 5.12.001 P1 ALPHA PUBLICADA: 4 placas, TESTE FÍSICO PENDENTE

**Entrega verificável:** [release oficial P1](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.001-p1), [CI 43597269377](https://github.com/PU2PNY/2PNY-OS/actions/runs/43597269377) com **6/6 jobs concluídos em sucesso**, tag/commit do código `38f3ac23582e4c5a424b09a5901b03f828aa617a`. Quatro assets `.img.xz` de tamanho >0, quatro `.sha256`, quatro manifestos `BUILD-INFO`, verificados por CI (`xz -t` + `sha256sum -c`, filesystem RO, hashes e alterações autorizadas, Nextion/RF/kernel/bootloader protegidos). **HW: NÃO VERIFICADO para P1; PROD: NÃO APROVADO**.

| Placa | Imagem publicada | SHA |
|---|---|---|
| Raspberry Pi ARM32 | [32-5.12.001.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-32-5.12.001.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-32-5.12.001.img.xz.sha256) |
| Raspberry Pi ARM64 | [64-5.12.001.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-64-5.12.001.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-64-5.12.001.img.xz.sha256) |
| Orange Pi Zero H2+ | [opizero-5.12.001.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-opizero-5.12.001.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-opizero-5.12.001.img.xz.sha256) |
| NanoPi NEO H3 | [nanopineo-5.12.001.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-nanopineo-5.12.001.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-nanopineo-5.12.001.img.xz.sha256) |

**Escopo implementado e SW PASS:** fallback de menu em HTML se o JS falhar (`UI-NAV-5121`); relógio da página Sistema novamente visível (`CLOCK-5121`, sem comprovação do fuso efetivo); OLED 128×32/64 e LCD HD44780 com PU2PNY-OS, indicativo, IP, protocolo, duração, BER/RSSI **somente se medidos**, CPU temperatura/disco (`DISPLAY-5121`); Expert `Rodar tudo` de leitura ampliado para diagnóstico HTTP/AP/gateways, arquivo TXT até 160 mil caracteres (`EXPERT-5121`). O **Nextion ON7LDS aprovado permanece byte-idêntico** no código da imagem; **novos campos Nextion não foram implementados nesta P1**.

**Problemas não resolvidos:** DMRGateway falha e rollback (#23/#24), D-Star sem confirmação de link remoto (#23), navegação/HTTP HW não homologados (#25), AP Orange sem painel e NanoPi HW pendente (#29), transcodificação sem backend/vocoder real (#27), Direct privado/grupo em CGNAT sem relay operacional (#26), extras Nextion CPU/disco/IP pendentes (#28), badge backend ainda pode dizer 5.11.000 apesar de `/etc/2pny/version=5.12.001` (#30). O diagnóstico Pi4 ARM64 5.12.000 em 14/11/2026 mostrou `Europe/London` apesar de NTP sincronizado, DMRGateway rollback, D-Star `connected:false` e **subtensão real reiterada** (`throttled=0x50005`). Não inventar correção ou medição.

**Checklist HW canônico:** [docs/PU2PNY-OS_5.12.001_HW_CHECKLIST.md](docs/PU2PNY-OS_5.12.001_HW_CHECKLIST.md). Preservar a imagem P0 para rollback, sem flash HMI/TFT e sem mudar RF aprovado. **Não declarar entrega plena do escopo 5.12** somente porque esta prerelease P1 está publicada.

---

## 2026-11-14 — REG-510-NAV: menu ausente no Ao Vivo; telemetria indisponível

**Evidência HW reportada:** captura em `http://pu2pny64.local/dashboard` com cabeçalho sem links de navegação e campos RF/rede/CPU como `—`. Usuário relata início dos problemas na **5.10**; versão exata desta captura isolada **não visível**. O wizard da mesma sessão exibia **5.11.000** e `Failed to fetch` em DMR, YSF e D-Star (REG-511-BASIC-APPLY, [#24](https://github.com/PU2PNY/2PNY-OS/issues/24)). **REGRESSÃO NO PAINEL / causa NÃO VERIFICADA**. A navegação é gerada no navegador por `PNY.nav` quando `/ui-common-0.3.0.js` carrega/executa. Os *fontes* de `ui-common`, `ui-language` (substituições 5.10) e JavaScript embutido no dashboard passaram em teste de sintaxe; **HTTP/JS no hardware NÃO VERIFICADO**. Hipóteses: script estático indisponível, execução JavaScript, rede/mDNS, backend `2pnyd`, CSS. Nenhuma delas foi comprovada. 5.09 é somente candidata de comparação anterior, com release ALPHA não homologada fisicamente. **Bloqueador [#25](https://github.com/PU2PNY/2PNY-OS/issues/25)**; manter [#24](https://github.com/PU2PNY/2PNY-OS/issues/24) para ativação dos protocolos. Exigir comparação e logs HTTP, rollback por cartão SD e testes específicos de menu + protocolos em hardware antes de publicar correção. **Não alterar RF/display, não declarar 5.10/5.11/5.12 PROD; release 5.12 P0 permanece candidata SW/CI, não homologada HW.**

---

## 2026-11-14 — REG-511-BASIC-APPLY: REGRESSÃO EM HW REPORTADA (NÃO CORRIGIDA)

**Evidência do usuário:** três capturas do wizard **PU2PNY-OS 5.11.000** com o modal `Salvando e ativando DMR`, `Salvando e ativando YSF` e `Salvando e ativando D-Star`, cada um exibindo `Failed to fetch`. **Status: REGRESSÃO / FAIL de interface no hardware testado, causa técnica NÃO VERIFICADA.** O erro informa perda/falha de comunicação com a API comum `/api/basic/apply` ou polling `/api/rf`; não comprova que os gateways falharam nem que nenhuma alteração foi aplicada. 5.12 P0 herda esse fluxo; **não é uma correção homologada desta regressão**. Preservar últimos baselines de DMR simplex, D-Star, YSF e Nextion ON7LDS, sem alterar configurações de RF, sem troca automática de protocolo, sem upgrade até evidência e rollback. Inspeção do código aponta como hipóteses a disponibilidade do servidor HTTP, mDNS/hostname, rede AP/STA e reinício/transição de serviço após aceite HTTP 202; requer log/relatório Expert com dados sensíveis ocultados e correlação no horário do teste. **Issue [#24](https://github.com/PU2PNY/2PNY-OS/issues/24) aberto como bloqueador**; ver também [#23](https://github.com/PU2PNY/2PNY-OS/issues/23). Não promover PROD.

---

## 2026-11-13 — Publicação PU2PNY-OS 5.12.000 P0 (quatro placas)

**Estado verificado em 13/11/2026:** a prerelease [PU2PNY-OS 5.12.000 P0 ALPHA](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.000-p0) está **PUBLICADA** como **candidata para teste físico**, não produção. Código/commit imutável dos quatro artefatos: [`1b2a0a0068303b9bf091c26c90012755708f2bb1`](https://github.com/PU2PNY/2PNY-OS/commit/1b2a0a0068303b9bf091c26c90012755708f2bb1). O [CI 43488577915](https://github.com/PU2PNY/2PNY-OS/actions/runs/43488577915) finalizou com **6/6 jobs success** (`tests`, `build (arm32)`, `build (arm64)`, `boards (opizero)`, `boards (nanopineo)`, `publish`). O publish executou `xz -t`, `sha256sum -c` e conferiu `BUILD-INFO` das quatro placas; na release há quatro arquivos não vazios .img.xz, quatro .sha256 e quatro manifestos. **HW NÃO VERIFICADO**; **PROD NÃO APROVADO**.

| Placa | Imagem 5.12 P0 | Verificação |
|---|---|---|
| Raspberry ARM32 | [pu2pny-32-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-32-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-32-5.12.img.xz.sha256) |
| Raspberry ARM64 | [pu2pny-64-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-64-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-64-5.12.img.xz.sha256) |
| Orange Pi Zero H2+ | [pu2pny-opizero-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-opizero-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-opizero-5.12.img.xz.sha256) |
| NanoPi NEO H3 | [pu2pny-nanopineo-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-nanopineo-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-nanopineo-5.12.img.xz.sha256) |

**Escopo efetivamente corrigido em SW/CI (P0):** BOOT-512 (remove a espera artificial de 300 s dos serviços opcionais do caminho crítico e preserva timers) e NET-512 (inclui e habilita `2pnyd.service` no empacotamento Orange Pi Zero/NanoPi NEO). **Não comprova boot/AP/HTTP em hardware**. Continuam sem correção ou verificação física: DMRGateway, D-Star `connected:false`, reinicialização MMDVMHost, Nextion SIGSEGV, Avahi/mDNS, subtensão, nomes/IP por placa, redesign e backlog completo da 5.12. Preservar a baseline da 5.11, o ON7LDS HW aprovado e demais RF. Issue [#23](https://github.com/PU2PNY/2PNY-OS/issues/23) permanece aberta para as pendências.

**Alterações desta sincronização documental:** atualização do START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX, CHANGELOG e README, sem mudar firmware/MMDVMHost/DMRGateway/Nextion/DMR-D-Star-YSF e sem novo build do runtime. Arquivos da release apontam para o commit imutável de código `1b2a0a0068303b9bf091c26c90012755708f2bb1`; commits posteriores de documentação não alteram essas imagens.

---

## 2026-10-22 — REL-5.00.003: correção boot/protocolos/display + construção de imagens
- Identificada via montagem read-only da imagem ARM64 a presença de `2pny-profile-autostart`, mas sem symlink habilitado em `multi-user.target.wants`, mecanismo já validava último perfil comprovado, uplink, MMDVM, gateway.
- Imagem overlay habilita serviço original e adiciona timer guardado contra troca de gateway já ativo. Não altera binários RF nem lógica de gateways.
- Serviço de display reconciliador aplica somente perfil previamente salvo após detecção de hardware e inicialização do broker, usando gerenciamento de display isolado.
- Adicionado build independente ARM32/ARM64 a partir da base v5.00.002 por SHA oficial; manifesto, checagem do filesystem, XZ e SHA obrigatórios antes da publicação alpha. HW continua pendente.

---

## 2026-10-22 — 5.00.003 correção adicional conservadora

`runtime/display/apply.py`: se não houver override explícito, usa layout salvo **somente** para tipos Nextion e layouts permitidos, sem forçar mudanças de RF. Teste estático acrescentado. Alterações anteriores de separação OLED/Nextion mantidas. **Sem declarar boot/protocolo corrigido, nem CI/HW PASS ou imagem gerada.**

---

## 2026-10-22 — 5.00.003 investigação e correção parcial OLED

Commit de runtime: `19e012e19b45a548c1a36849bae78c2b307cbce5`. Removida a inferência de Nextion baseada apenas na presença de MMDVM e preservada a delegação OLED/LCD sem desabilitar antes o adaptador. Teste de regressão estático adicionado. **Ainda não houve CI nem teste HW e a falha de protocolo/reboot não foi corrigida. Imagem 5.00.003 não publicada.**

---

## 2026-10-22 — DISPLAY-041 / aprovação física e consolidação

Usuário aprovou explicitamente a tela da 5.00.002 em NextionDriver ON7LDS: “a tela funcionou perfeito”. Registrado HW PASS geral para o conjunto testado e baseline protegido. Documentação ativa passa a ter uma regra única; guia anterior preservado em histórico, sem servir como recomendação atual. Outros layouts/modelos/arquiteturas e subtestes não informados não recebem aprovação por inferência. Código, configuração, imagens publicadas e RF não foram alterados.

---

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

### 2026-09-22 — D-Star voice assets no builder da 0.3.19
- A validação montada detectou que a imagem não carregava os `.ambe/.indx` nativos do DStarGateway, apesar de o caminho `[Paths] Data=/usr/local/share/dstargateway.d/` estar correto.
- O builder manual instalava somente o binário `dstargateway`; foi adicionado um hook antes da remoção do checkout pinado para instalar os packs de voz nativos em `/usr/local/share/dstargateway.d/`.
- O hook exige fisicamente `en_GB.ambe` e `en_GB.indx` antes de continuar.
- Não são copiados/reescritos hostfiles PU2PNY, frequências, offsets, baud ou configurações RF.
- Criado rollback `backup/0.3.19-pre-dstar-voice-assets-fix-20260922`.


### 2026-09-22 — pré-validação obrigatória antes do validador final
- Criado **REL-015** como regra permanente para todas as versões.
- Novo `ci/preflight-image.sh` monta a imagem gerada em modo somente leitura antes do validador final.
- O gate confirma XZ/SHA-256, identidade/versão, runtime essencial, título `PU2PNY-OS`, DMR baseline, serviços críticos e assets nativos D-Star.
- O workflow 0.3.19 agora executa `Pre-validate generated image` antes de `Validate final image`.
- Falha de pré-validação bloqueia validador/publicação e exige correção no fonte/builder + novo build; não é permitido mascarar o erro alterando a imagem pronta ou removendo o gate.
- Criados **TEST-REL-015A/B**.
- Rollback preservado: `backup/0.3.19-pre-prevalidation-rule-20260922b`.


### 2026-09-22 — D-Star host catalog após REL-015 PASS
- O run `35758692012` comprovou a nova ordem: imagem ARM64 → XZ/SHA → preflight REL-015 PASS → validador final.
- O validador final detectou `DStar_Hosts.json` ausente no diretório `/usr/local/share/dstargateway.d/`; a release não foi publicada.
- O catálogo não será buscado de uma fonte nova: a correção reaproveita o `DStar_Hosts.json` pinado já seeded pela cadeia 0.3.1 e o coloca no overlay antes da criação da imagem.
- O preflight REL-015 passa a exigir o mesmo arquivo com tamanho mínimo antes de chamar o validador.
- Criado `TEST-BUILD-0319-DSTAR-HOSTS`.
- Rollback: `backup/0.3.19-pre-dstar-hostfile-fix-20260922`.
- Nenhum parâmetro RF, baud, frequência, offset, DMR, YSF ou rede foi alterado.


### 2026-09-22 — 0.3.19-alpha publicada com REL-015
- Run `35760337205` concluiu source, staged source, ARM64, XZ/SHA-256, **preflight REL-015**, validador final, artefato e publish em PASS.
- O catálogo `DStar_Hosts.json` e os assets nativos `en_GB.ambe/.indx` foram confirmados na imagem antes do validador final.
- Publicada prerelease `v0.3.19-alpha` no commit `c4db3e0098e2af1cd0ec1504e8946d30ac8c6391`.
- Imagem: `PU2PNY-OS-0.3.19-alpha-arm64.img.xz`, 597725788 bytes.
- SHA-256: `5f14e62b5811129f42f6dd9b7c637cfaa0944a370db42637abc56d1ac62f2355`.
- Estado permanece **ALPHA/HW-TEST**; CI não substitui validação física.


## 2026-09-22 — 0.3.20-alpha / REL-016
- Criado rollback GitHub `backup/0.3.19-pre-0.3.20-20260922` e branch isolada `pu2pny-os-0.3.20-alpha`; a 0.3.19 publicada permaneceu intacta.
- Registrados UI-037, LIVE-020/021, NET-027, PERF-004, PROTO-029/030/031/032/033, RF-020, UI-038, P2P-008, APRS-014, DISPLAY-020/021, SYS-001/002/003 e UPDATE-007.
- **D-Star HW observado na 0.3.19:** mudar refletor pelo painel aplicou de fato XLX300D e permitiu comunicação; comandos pelo rádio para trocar refletor alteravam somente o painel. Causa de UI confirmada: o worker promovia `Link command ... issued` a servidor/módulo efetivo antes do `... link ... established`. Causa de resolução XLX: o DStar_Hosts.json pinado não contém a lista XLX completa; o apply adicionava apenas o refletor atualmente selecionado.
- 0.3.20 separa pedido de link de estado efetivo e mescla a lista XLX validada no catálogo D-Star. Falha/destino desconhecido não é mais mostrado como conectado.
- Módulo local D-Star/RPT1 deixa de ser fixo C: novas configurações usam B por decisão de produto e podem selecionar A–D; módulo remoto do refletor continua independente. Upgrades preservam o valor efetivo anterior.
- DMR: XLX primeiro; ESSID não vaza BrandMeister→XLX; ordem MMDVMHost→DMRGateway; comandos TG4000–4026/4099 passam a aceitar TS1 e TS2.
- Ao Vivo: TOT amarelo 2:30–2:49, vermelho 2:50–3:00; S-meter aparece apenas em RF real.
- UI global oculta indicadores sem dado real; Protocolos separa conectividade IP de link remoto.
- Nextion via modem exige COMOK real pela bridge MQTT antes de declarar tela física; Moderno V2 vira layout padrão após confirmação.
- APRS renomeado e recebe comandos operacionais inspirados na lógica observada em xlx026.net, sem alterar o servidor de referência.
- Sistema recebe lista completa de timezones, ajuste manual de relógio e download de logs sanitizados.
- OTA recebe instalar agora/depois e rollback automático em falha de aplicação.
- Direct recebe gatilho por atividade RF real para D-Star/DMR mantendo pareamento e criptografia.
- VPS WartyWallaby: regressões Python/Shell/JS e backend Go passaram; a compilação Direct não pôde ser executada nessa VPS porque o Go 1.19 não possui `crypto/ecdh`. O gate oficial usa Go 1.24 no CI.


## 2026-09-22 — organização documental e governança permanente
- Criado rollback `backup/0.3.20-pre-doc-governance-20260922` antes da organização.
- Registrados **ARCH-006**, **REL-017** e **TEST-008**.
- Baseline aprovado passa a ser explicitamente protegido; DMR simplex funcional não pode ser alterado para corrigir duplex sem necessidade direta.
- Reforçada validação por SentinelX/VPS quando aplicável, GitHub/CI, plugins/conectores e fontes oficiais, sem promover SW/VPS para HW.
- `README.md` foi atualizado do estado obsoleto 0.1.1 para o ciclo real 0.3.20-alpha.
- `PU2PNY-OS_START_HERE.md` e `PU2PNY-OS_PROJECT_INSTRUCTIONS.md` foram consolidados com as regras permanentes atuais.
- Criado `docs/README.md` para separar fontes canônicas de documentos históricos/técnicos.
- Documentos antigos não foram apagados por idade: permanecem úteis para regressão, auditoria e rastreabilidade.
- Nenhum teste físico é promovido por esta alteração documental.


### 2026-09-22 — 0.3.20-alpha publicada
- Run GitHub Actions `35798691612`: source, staged source, ARM64, XZ/SHA-256, REL-015, validador final, artefato e publish em PASS.
- Publicada prerelease `v0.3.20-alpha` no commit `0e6063688396ad2a0f1cf60cfe5e60915e711019`.
- Imagem: `PU2PNY-OS-0.3.20-alpha-arm64.img.xz`, 614874612 bytes.
- SHA-256: `f42756bfcce537a7890b6296db3da3258fd8e909a45c7856f1530c8b363bed56`.
- README principal ampliado para refletir a 0.3.20, seus recursos, download, baselines e pendências reais.
- Estado permanece **ALPHA / PARA TESTE FÍSICO**; nenhum item RF/Nextion pendente foi promovido para HW PASS.

## 2026-09-22/23 — abertura da 0.3.21-alpha após teste físico da 0.3.20

- A 0.3.20-alpha publicada permanece rollback/base; criada a linha pu2pny-os-0.3.21-alpha.
- D-Star simplex e DMR simplex foram aprovados pelo mantenedor e passam a baseline física protegida explícita. Correções duplex não autorizam reescrever simplex.
- Registrados REL-018, PROTO-034/035/036, UI-039/040/041, NET-028/029, WIZ-010, P2P-009, APRS-015, DISPLAY-022/023, PERF-005, RF-022 e SYS-004.
- DMR duplex foi isolado por use_mode=repeater: transporte local TS1/TS2 e diagnóstico específico; caminho simplex permanece protegido.
- Arbitragem de voz DMR foi limitada ao estado efetivo SENDING para evitar silenciar tráfego de rede enquanto a voz apenas aguarda.
- Estado de TG separa pedido e confirmação; DMR mostra TG real, não módulo obsoleto. D-Star usa refletor/módulo; YSF usa sala/refletor.
- DNS/Wi‑Fi receberam convergência de estado, alerta de Internet, perfil backup e histerese de sinal.
- Idioma passa a ser persistido e perguntado apenas no primeiro provisionamento; wizard retoma em Hardware quando a rede já está funcional.
- Direct passa a direct-only para payload: servidor apenas rendezvous; D-Star/DMR podem iniciar pelo rádio, e relay-data é rejeitado. CGNAT restritivo sem caminho UDP direto é reportado como bloqueado, não mascarado.
- APRS preserva fila/retry e passa a diagnosticar ACK/REJ por origem+ID; coordenadas manuais ficam disponíveis em HTTP. M-SMS/H-SMS entram como pesquisa/documentação; DMR SMS nativo não é declarado entregue sem confirmação real.
- Nextion deixa explícito TX-only/unconfirmed sem COMOK; HMI mantém renderer PU2PNY e não grava TFT automaticamente.
- Relógio passa a automático por NTP/timezone validado, com DST manual somente na apresentação.
- Journald é limitado/rotacionado; calibração BER recebe helper RXOffset transacional com medição/salvar/restaurar.
- A release só poderá ser publicada após VPS quando aplicável, regressões 0.3.20, build ARM64, SHA-256, preflight REL-015, validador final e artifact publicado. Itens RF/Nextion continuam HW PENDENTE.

### 2026-09-23 — 0.3.21-alpha publicada
- Run GitHub Actions `35815292900` concluiu source, staged source, ARM64, XZ/SHA-256, preflight REL-015, validador final, artefato e publish em **PASS**.
- Publicada prerelease `v0.3.21-alpha` no commit `c585b0e6ae10b93f3272f8783eb2832045983194`.
- Imagem: `PU2PNY-OS-0.3.21-alpha-arm64.img.xz`, 610089972 bytes.
- SHA-256: `c2ec6b729b3f60153274909c8280fc2f73a07d5e426fdd129a7982d4f9d420ab`.
- O gate final confirmou a política Direct sem relay por selftest executável, além dos gates de rede, idioma, Nextion/COMOK, APRS ACK, BER, journald e proteção simplex.
- Estado permanece **ALPHA / PARA TESTE FÍSICO**. Nenhum item RF/Nextion/Direct foi promovido de SW/VPS para HW sem teste real.

## 2026-09-25 — abertura da 0.3.24-alpha
- O mantenedor confirmou como **concluído e ótimo** o ajuste da atividade 24h: o ícone de informações de Gateway só aparece quando Gateway difere do indicativo e há identificação real de repetidora. Esse comportamento passa a baseline protegida e não é alterado no overlay 0.3.24.
- Criado rollback `backup/0.3.23-pre-0.3.24-20260925` antes das mudanças.
- Criados **SYS-005**, **UI-042**, **P2P-010** e **REL-019**.
- Relógio: removido o bloqueio artificial ao timezone/data-hora manual; o helper seguro já existente continua autoritativo. O navegador fornece timezone IANA automático somente quando não existe escolha manual persistida.
- Idioma: PT/EN/ES passa a sincronizar backend + navegador, atributo `lang`, locale de data/hora/número e gate contra frases híbridas nas páginas staged.
- Direct: P2P-010 substitui apenas a política `direct-only` de P2P-009. O cliente tenta UDP direto e, quando necessário, encaminha pelo relay somente o pacote já criptografado ponta a ponta.
- Chamada Direct recebida não toma RF/gateway antes da aceitação pelo rádio. Encerramento/timeout restaura o serviço anterior preservando a configuração persistida.
- O servidor 0.3.24 recebe limite específico para envelope relay e cadência compatível com tráfego de voz, mantendo rate limiting.
- O overlay 0.3.24 não substitui fontes RF/MMDVM/DMR/D-Star/YSF. Baselines simplex e Nextion 0.3.23 permanecem congeladas; validação HW continua obrigatória.

### 2026-09-25 — servidor público Direct 0.3.24
- Confirmado pré-estado no XLX026: nenhuma unit/processo/listener em UDP 43070.
- Implantado serviço isolado `pu2pny-direct-relay.service`; nenhuma porta/serviço do XLXD foi substituído.
- UFW recebeu somente a regra UDP 43070 para Direct, com backup das regras anteriores e instrução de rollback.
- WartyWallaby, externamente ao XLX026, registrou dois peers sintéticos e confirmou encaminhamento opaco `relay-data` A→B em `xlx026.net:43070`: PASS de rede/VPS.
- O teste não equivale a RF real; Direct A↔B com rádios/hotspots e restauração do destino anterior continua HW PENDENTE.

### 2026-09-25 — 0.3.24-alpha publicada
- Run GitHub Actions `36134610081` concluiu source, staged source, ARM64, XZ/SHA-256, preflight, validador final, artifact e publish em **PASS**.
- Publicada prerelease `v0.3.24-alpha` no commit `1a25e43e6997ea514c407f29e0e396d82d4c0bcb`.
- Imagem: `PU2PNY-OS-0.3.24-alpha-arm64.img.xz`, 592789908 bytes.
- SHA-256: `996dd6c4a08eae9cb332f66e4a19cc83957ad314d1de5aa552825115504eb1ef`.
- O servidor público Direct no XLX026 e UDP 43070 tiveram teste externo VPS/NET **PASS**; RF/CGNAT real entre dois hotspots continua HW PENDENTE.
- Estado: **ALPHA / PARA TESTE FÍSICO**, sem promoção para PROD antes das regressões físicas exigidas.


## 2026-09-25 — abertura da 0.3.25-alpha
- Feedback físico da 0.3.24: relógio **APROVADO**; YSF/C4FM simplex TX/RX **APROVADO**; troca de módulo/TG DMR pelo rádio **APROVADA**; aviso de voz após conexão DMR **APROVADO**. Esses itens entram em baseline protegido.
- Falha observada: após seleção do Wi-Fi a página ficou aguardando; posteriormente a tela Internet mostrou Wi-Fi conectado. Fonte confirma que o helper Wi-Fi e o fluxo de conexão do wizard são os mesmos da 0.3.23; portanto a correção não reescreve Wi-Fi.
- Falha observada: por Ethernet, `http://pu2pny.local/wizard` não resolveu, embora acesso pelo IP LAN funcionasse.
- Correção autorizada: Ethernet com Internet equivale a Wi-Fi no primeiro acesso e robustez de publicação `pu2pny.local`/mDNS.
- Criado rollback `backup/0.3.24-pre-0.3.25-20260925`.


## 2026-09-25 — abertura da 0.3.26-alpha
- Criado rollback `backup/0.3.25-pre-0.3.26-20260925`.
- Escopo solicitado limitado a detecção MMDVM, velocidade/precisão Wi-Fi, Wi-Fi 2/failover e feedback imediato de reboot.
- Pesquisa upstream MMDVMHost confirmou GET_VERSION e velocidades UART suportadas; detector passou a cobrir aliases persistentes e classes GPIO/USB adicionais, com espera apenas para CDC-ACM reset-prone.
- Wi-Fi: removidas varreduras redundantes; NetworkManager continua autoritativo, com autoconnect/retries, prioridade maior para Wi-Fi 1 e backup para Wi-Fi 2, histerese preservada e rollback em falha.
- Internet recebe botão dedicado para escanear Wi-Fi 2.
- Sistema mostra reinício imediatamente antes da chamada ao backend.
- Nenhum comportamento de protocolo/RF aprovado é alterado por este ciclo.

### 2026-09-25 — 0.3.26-alpha publicada
- GitHub Actions run `36190497369` concluiu source, ARM64, XZ/SHA-256, preflight, validador final e publish em **PASS**.
- VPS WartyWallaby confirmou teste focal, sintaxe Python/Shell, backend Go e JavaScript das telas em **PASS**.
- Publicada prerelease `v0.3.26-alpha` no commit `fad9d4c7ca147e04520a9a09b64d2aa797d4e766`.
- Imagem: `PU2PNY-OS-0.3.26-alpha-arm64.img.xz`, 606220720 bytes; SHA-256 `ffa6f4d89dbc5d7c08791d81b82a366636a33207a3ff274742dbf4c7867851da`.
- MMDVM real específica e failover físico Wi-Fi 1→2 continuam **HW PENDENTE**; não foram promovidos por CI/VPS.


## 2026-09-26 — abertura da 0.3.27-alpha
- Criado rollback `backup/0.3.26-pre-0.3.27-20260926`.
- Auditoria histórica/código de YSF/C4FM, D-Star e DMR concluiu que os runtimes atuais aprovados não devem ser reescritos; gates comparam helpers/serviços/patches à v0.3.26.
- YSF: Wires-X local, portas e resolução de Startup preservados; operação real pelo rádio continua HW PENDENTE.
- D-Star simplex e DMR simplex permanecem baselines físicas protegidas; DMR duplex continua isolado e HW PENDENTE.
- APRS convertido para message-only no daemon/API/UI, preservando inbox/outbox/ACK/REJ/retries.
- BrandMeister Hotspot Security recebe campo dedicado, persistência privada/rollback e reutilização sem devolver o segredo ao navegador.
- Novo documento: `docs/PROTOCOL-AUDIT-0.3.27.md`.

### 2026-09-26 — 0.3.27-alpha publicada
- O primeiro run 0.3.27 foi bloqueado antes da construção da imagem por um regex de versão incorretamente escapado no workflow; o gate foi corrigido sem alterar runtime de rádio.
- GitHub Actions run `36254445940` concluiu source, staged source, build ARM64, XZ/SHA-256, preflight montado, validador final, artefato e publish em **PASS**.
- VPS/SentinelX WartyWallaby confirmou auditoria byte a byte dos runtimes protegidos, regressões herdadas, sintaxe Go/Python/JS e testes APRS de mensagem/ACK/REJ em **PASS**.
- Publicada prerelease `v0.3.27-alpha` no commit de imagem `928bc063aeecabf6462469629fa18edef313c2c1`.
- Imagem: `PU2PNY-OS-0.3.27-alpha-arm64.img.xz`, 606874868 bytes.
- SHA-256: `a8077ae3f2855e37ff25124aa56f0de6c318e3bf272a0429f18418a438bd84c5`.
- Estado: **ALPHA / PARA TESTE FÍSICO**. Wires-X real, regressão simplex da nova imagem, DMR duplex, autenticação BrandMeister real e ACK APRS externo continuam pendentes de evidência HW/NET real.


## 2026-09-26 — 0.3.27 rejeitada em HW e abertura da 0.3.28
- Teste físico rejeitou a 0.3.27: Wi-Fi salvo não voltou após reboot; Ethernet exigiu localizar manualmente o IPv4 192.168.100.8; protocolos ficaram sem TX/RX.
- Investigação mostrou que a 0.3.26 havia encurtado associação NetworkManager de 45 s para 14 s, DHCP candidato de 30 s para 12 s e retries persistentes de 3 para 2. Essa otimização deixa de ser baseline: confiabilidade da 0.3.23 volta a prevalecer.
- Criado rollback `backup/0.3.27-rejected-pre-0.3.28-20260926` e branch `pu2pny-os-0.3.28-alpha`.
- Novos requisitos permanentes: NET-034, NET-035, PROTO-045, LIVE-022 e REL-023.


## 2026-09-26 — 0.3.28-alpha publicada
- Recuperada a janela de associação Wi-Fi comprovada da 0.3.23 sem remover as melhorias de scan/UI e Wi-Fi 2.
- Criado reconciliador event-driven para mDNS, atualização de hostfiles e retomada segura do perfil selecionado.
- Hostfiles/listas públicas passam a atualizar ao ficar online e a cada 8 horas (3 vezes/dia), com `Persistent=true`, lock e preservação do cache anterior.
- Ao Vivo agora informa dentro do box TX quando o perfil selecionado não está ativo ou quando não há conexão confirmada com o servidor.
- Gate estrutural mantém helpers RF/DMR/D-Star/YSF byte a byte protegidos contra a base anterior.
- GitHub Actions run `36260579797`: build ARM64, SHA-256, preflight, validador final e publish **PASS**.
- SentinelX/VPS na tag exata: **PASS**.
- Publicada `v0.3.28-alpha`, commit da imagem `6924abcc74e946f41c83a98c341c335c75855171`.
- Imagem `PU2PNY-OS-0.3.28-alpha-arm64.img.xz`, 594602484 bytes, SHA-256 `ea3d5619e891089e287ceea355d0c638222fa5d4ecbc223fdc119b791feecb6c`.
- Estado correto: **ALPHA / PARA TESTE FÍSICO**. 0.3.27 continua rejeitada em HW.


## 2026-09-27 — 0.3.29-alpha

- Criado rollback `backup/0.3.28-pre-0.3.29-20260927` e branch `pu2pny-os-0.3.29-alpha`.
- Decisão NET-036: SSID de setup/recuperação passa a `PU2PNY-OS`, preservando hostname `pu2pny.local`, IP `10.43.0.1` e lógica de rede da 0.3.28.
- Decisão PROTO-046: YSF/C4FM funcional permanece congelado; Wires-X físico continua pendente.
- Decisão PROTO-047: não habilitar MMDVM-CrossMode sem MMDVM-Transcoder comprovado; não declarar P25/NXDN no programa inicial upstream.
- Decisão UI-045: relatório técnico é local, sanitizado e sob ação explícita; sem telemetria/envio oculto.
- Decisão UI-046: título de aba canônico `PU2PNY-OS`.
- Nenhum favicon novo foi criado sem o asset aprovado.


### 2026-09-27 — 0.3.29-alpha publicada
- Primeiro run `36328675011` falhou antes do build da imagem porque o patch procurava um marcador visual antigo do Expert; nenhum artefato foi publicado nesse run.
- O marcador foi corrigido para a estrutura staged real do Expert 0.3.19 sem tocar em runtime RF/gateways.
- Run final `36328999571`: source, staging, ARM64, XZ/SHA-256, preflight, validador final, artefato e publish **PASS**.
- SentinelX/VPS confirmou `PATCH_0329_OK`, `REGRESSION_0329_OK`, `PROTECTED_IDENTICAL` e `EXPERT_INLINE_JS_OK`.
- Link da imagem validado por HTTP 200 com `Content-Length: 598139288`.
- Imagem: `PU2PNY-OS-0.3.29-alpha-arm64.img.xz`.
- SHA-256: `7135ef22a374cda74d7c4fd0d78cfa0a14460c1d6fc23b538d9e86a15c81d132`.
- Classificação permanece **ALPHA / PARA TESTE FÍSICO**. Nenhum item RF/duplex/Wires-X/display/cross-mode foi promovido a HW PASS por CI.


## 2026-09-27 — abertura 0.3.30-alpha — somente displays

- Criados rollback `backup/0.3.29-pre-0.3.30-display-20260927` e branch `pu2pny-os-0.3.30-alpha`.
- Registrados **DISPLAY-024** e **REL-025**.
- Diagnóstico objetivo: o renderer PU2PNY 0.3.21 executava `cls 0` em toda atualização ativa, produzindo redesenho integral e risco direto de flicker. A UI de Display também forçava Moderno V2 enquanto o handler backend ainda forçava o renderer nativo, tornando a seleção incoerente.
- Correção proposta: cache de componentes Nextion com limpeza somente em transição de página/estado; campos inalterados não são retransmitidos.
- Detector passa a publicar metadados reais da resposta `comok` (modelo/firmware/MCU/serial/flash) sem inferir HMI/layout.
- UI passa a oferecer Moderno V2 ou fallback MMDVMHost nativo G4KLX/0, ON7LDS L2/2 e L3/3. NextionDriver/L3 HS não é anunciado como disponível sem instalação/validação.
- Aplicador reforça exclusividade de writer. TFT/HMI permanece sem gravação automática.
- Overlay calcula hashes de DMR/D-Star/YSF/rede/APRS/Direct e aborta se qualquer protegido mudar.
- Validação concluída em SW/CI/VPS: WartyWallaby passou testes incrementais/COMOK/fallback/JS e staging `PROTECTED_IDENTICAL`; GitHub Actions run `36341170897` passou source, staging, ARM64, SHA-256, preflight, validador final, artifact e publish.
- Publicada prerelease `v0.3.30-alpha` no commit `3ec9b8cd1228f1e722595ff5ff1e1de5bd70bb60`, SHA-256 da imagem `fa1cbb43c7497432972e4da852c3ce49277e8bebe9a18f4bdbdc52bf3423437b`.
- Estado: **ALPHA / PARA TESTE FÍSICO**. Nenhum resultado físico foi promovido para PASS; flicker real, COMOK, Nextion/OLED/LCD, reboot/persistência e regressões RF permanecem HW PENDENTE.

## 0.3.31.116 — REL-026 / consolidação segura

- Adotado `REL-026`: nenhuma candidata consolidada recebe link de imagem antes de gates combinados, build ARM64, validação estrutural e SHA-256.
- Recovery 0.3.31.112 consolidado após PASS SW/CI e VPS Debian 12; updater 0.3.20 permanece ativo e byte-idêntico porque a CLI 0.3.31.112 não é compatível com as chamadas atuais do painel/backend. O engine novo é empacotado de forma versionada e não autoritativa.
- Mantidos Baseline Guard 0.3.31.113, contrato de display 0.3.31.114 e PT/EN/ES 0.3.31.115.
- Debian 13/Trixie não é misturado nesta candidata.
- DMR/D-Star/YSF, MMDVMHost, RF, frequências, offsets, rede e wizard permanecem fora do escopo.
- Estado físico permanece `PENDENTE HW`; build ou VPS não substituem Raspberry Pi/MMDVM/Nextion.

## 0.3.31.117 — 2026-10-06 — REL-027

- NET-037: após conexão Wi-Fi confirmada, a UI passa a reencontrar o painel por `pu2pny.local` e pelos endereços reais fornecidos pelo backend; nenhum navegador é falsamente considerado “autoaberto” em Ethernet.
- LIVE-023: `Wi-Fi / Uplink` passa a representar sinal Wi-Fi real; Ethernet mostra cabo sem RSSI/porcentagem inventada.
- DISPLAY-025: adicionada compatibilidade explícita Pi-Star/WPSD/ON7LDS com NextionDriver pinado em `03b904270c9cb54f720d71753fc209afb1d9598f`, hardening contra HMI→shell/download autônomo, Transparent Data para display no modem, single-writer e sem flash automático de HMI/TFT.
- Protegidos: MMDVMHost, DMR/D-Star/YSF, DMRGateway/helpers, RF, frequências, offsets, `2pny-network-switch`, `2pny-network-online` e wizard permanecem sem alteração pelo overlay.
- Build/runtime commit: `1ab827b1e91ea0cac1bffa294c2242b0faf72f13`; imagem SHA-256 `c323d796135d8e69eca9240d50e40a8f529d79b1992d94a7753946f88a4f403b`; SW/CI: https://github.com/PU2PNY/2PNY-OS/actions/runs/37547804310; VPS: APROVADO (source gates + overlay fixture + NextionDriver x86_64; Go indisponível na VPS); HW: PENDENTE.

## 0.3.31.118 — 2026-10-07 — REL-028 / DISPLAY-026

- Registrado HW FAIL da compatibilidade ON7LDS na 0.3.31.117: Nextion `NX3224T024_011R` foi confirmada por COMOK, mas permaneceu no splash do HMI `USE NextionDriver - ON7LDS`; a aplicação do renderer avançado falhou e executou rollback seguro.
- Causa raiz confirmada em código/upstream: NextionDriver usa `/dev/ttyNextionDriver`, enquanto a integração 0.3.31.117 roda como `mmdvm` e espera `/run/2pny-nextiondriver/ttyNextionDriver`.
- DISPLAY-026 recompila o mesmo upstream pinado e o mesmo hardening da 0.3.31.117, alterando somente `NEXTIONDRIVERLINK` para o RuntimeDirectory não privilegiado.
- Ponto de retorno: `backup/0.3.31.117-nextion-hw-fail-20261007` @ `088ba5901bfc918503430df658f1a7b5728ef64e`.
- Build/runtime commit: `824a54c317fc872743808f6c9c9b8bf8fba6d5f4`; imagem SHA-256 `111db204ab8f407aa0b25f503db0c612f3fc59575c437340314f173bd12d6dfc`; SW/CI: https://github.com/PU2PNY/2PNY-OS/actions/runs/37567112033; VPS: BLOQUEADO no runner SentinelX por diretório de trabalho não gravável; CI reproduz e valida o subset não-RF; HW: PENDENTE.

## 0.3.31.119 — 2026-10-07 — REL-029 / DISPLAY-027

- Removido do fluxo ativo de Nextion o renderer `PU2PNY Moderno V2`.
- O seletor Renderer agora apresenta diretamente os quatro perfis padrão suportados: Modem/G4KLX (`0`), ON7LDS L2 (`2`), ON7LDS L3 (`3`) e ON7LDS L3 HS (`4`).
- Corrigido o parse de layout que convertia `ScreenLayout=0` em fallback porque zero era tratado como falso.
- Mantida detecção não destrutiva de hardware; modelo físico não é usado para inventar HMI/layout. Quando não houver evidência, o operador escolhe o Renderer manualmente.
- Mantidos NextionDriver endurecido, PTY em `/run/2pny-nextiondriver/ttyNextionDriver`, Transparent Data com `SendFrameType=1`, single-writer e proibição de flash automático.
- Referência oficial adicionada: `g4klx/MMDVM-Host` para Transparent Data; ON7LDS NextionDriver para o caminho `Port=modem`.
- Base/rollback: `v0.3.31.118` / branch `pu2pny-os-0.3.31.118-nextion-hotfix`.
- Build/runtime commit: `a97f79c16c987de13fa5d31ba2648dbfc9597e54`; imagem SHA-256 `ab787f47c27566c9f057b3517320674c010904ea98b82e478993fb75a6fa3978`; SW/CI: https://github.com/PU2PNY/2PNY-OS/actions/runs/37650989580; VPS: NÃO VERIFICADO nesta execução; CI ARM64 valida o subset SW e não substitui hardware; HW: PENDENTE.

## 0.3.31.120 — 2026-10-08 — REL-030 / DISPLAY-028 / NET-038

- Corrigida reaplicação ON7LDS: após escrever a configuração, `NextionDriver` é habilitado e reiniciado explicitamente antes de validar o PTY; rollback existente é preservado.
- Mantidos sem alteração o binário NextionDriver, MMDVMHost e a regra de um único writer; nenhum HMI/TFT é gravado automaticamente.
- Corrigido `pu2pny.local`: Avahi recebe hostname explícito `pu2pny` e reanúncio event-driven nas mudanças relevantes do NetworkManager, sem polling.
- Nenhum perfil Wi-Fi/Ethernet, RF, DMR, D-Star, YSF, frequência, gateway ou wizard é alterado.
- Base/rollback: `v0.3.31.119` / branch `pu2pny-os-0.3.31.119-display-autodetect`.
- Build/runtime commit: `776f7d6676fc1f31ce2c8167aed7bb766c168c6d`; imagem SHA-256 `43fa01b610519c3c8e63a474a6494a6cd6247b7750c8eb0815a9328b9ffe1a03`; SW/CI: https://github.com/PU2PNY/2PNY-OS/actions/runs/37862675745; VPS: NÃO VERIFICADO nesta execução; CI ARM64 valida SW e não substitui hardware; HW: PENDENTE.

## 0.3.31.121 — 2026-10-09 — REL-031 / DISPLAY-029
- Corrigido handoff ON7LDS: NextionDriver passa por clean stop/start após a configuração ser gravada.
- PTY stale é removido antes do start; `-i` upstream evita abortar por instância detectada durante transição.
- Aplicação só confirma o modo após NextionDriver, `2pny-mmdvmhost.service` e PTY estarem simultaneamente estáveis; falha restaura a configuração anterior.
- MMDVMHost e binário NextionDriver permanecem byte-idênticos à 0.3.31.120.
- Build/runtime commit: `9b9ddc4ab4cdff8f516ab02eef3c4f7d8c7d949f`; imagem SHA-256 `ee00e310f12ad89aefe9508e009c5bc36f156b306ac02788de2040a3a11c8b22`; SW/CI: https://github.com/PU2PNY/2PNY-OS/actions/runs/37878210638; HW: PENDENTE.

### 4.00.000 (2026-10-14)
- Iniciado ecossistema global orientado por capacidades, sem amarrar o PU2PNY-OS a uma Raspberry Pi, um modem MMDVM ou um display específicos.
- Adicionado inventário conservador de hardware/protocolos/display/transcoder/acesso remoto e endpoint /api/capabilities.
- Adicionada atualização por PathChanged com fallback de 15 minutos, sem polling agressivo e sem escrita RF.
- Adicionado gate CI que prova handlers protegidos RF/DMR/display/rede/Ao Vivo byte-idênticos à cadeia baseline antes da camada 4.00.000.
- Helix passa a ser backend opcional local, pinado, padrão off; HVC e AMBE nativo continuam bloqueados enquanto faltarem gates próprios.
- A família 4.00.000 usa artefatos por arquitetura quando necessário; não forçar uma imagem única que invalide Pi Zero/ARMv6 ou ARM64.
- Validação VPS da camada de capacidades/backend concluída sem promover nenhum estado para HW.


### Fechamento de build/publicação 4.00.000 — 2026-10-14
- O primeiro reparo ARM32 falhou apenas no gate de arquitetura porque um runner x86_64 tentou executar `/usr/bin/dpkg` ARMHF via `chroot`, resultando em `Exec format error`; toolchain, Helix ARMv6, backend, overlay, fsck e scanner já haviam passado.
- Commit `14a5a2a054f5b563db70860192dcd3165694e82b` aplicou correção cirúrgica de uma linha: a arquitetura passou a ser lida pela base dpkg montada, sem executar binário ARM. O novo run `38582443780` concluiu ARMHF/ARMv6 integralmente com PASS.
- A primeira tentativa de publicação falhou somente com `HTTP 403 Resource not accessible by integration` ao criar release apontando para um commit que modifica workflows; os dois artefatos já haviam passado a revalidação XZ/SHA.
- O publicador separado, commit `ecef5fc85bb5419797927d5efe8b3316ce263e7a`, reutilizou exatamente os artefatos aprovados, revalidou ambos e publicou `v4.00.000` no run `38584440709` com PASS. A tag usa `main` somente como âncora administrativa; `BUILD-INFO` e notas preservam o commit fonte real `684820f49896d9a478644e7418932ed40a3a8870`.
- SHA-256 final ARM64: `3ec52631dfe44b9a466bd1f1f4a8b910c6fdac3663736f7d643091b8c5a13dd7`.
- SHA-256 final ARMHF/ARMv6/Pi Zero: `b7edc16b4a7786e0b0664eef7a1a3f53b449f6abf55aa47d31516a170163760c`.
- Nenhuma dessas correções alterou o caminho RF aprovado, MMDVMHost, DMRGateway, NextionDriver, Wi-Fi profiles ou comportamento de protocolo protegido.
- Estado final deste ciclo: **SW/CI PASS / prerelease candidata para teste físico; HW/PROD continuam PENDENTE**.

<!-- PU2PNY-OS-4.00.001-CANONICAL -->
## 2026-10-14 — 4.00.001: display upstream, timezone persistente e ARM32 leve

- **DISPLAY-032:** por solicitação explícita do usuário, a política anterior de telas foi supersedida. A implementação passa a seguir o modelo Pi-Star/WPSD: G4KLX/ON7LDS via MMDVMHost e ON7LDS NextionDriver; nenhum HMI/TFT é auto-gravado e COMOK não é gate para display atrás do modem.
- Causa técnica confirmada no código upstream ON7LDS: a opção `-d` chama `go_daemon()`/fork. A unidade PU2PNY usava `Type=simple` junto com `-d`; 4.00.001 remove `-d` e deixa o systemd supervisionar o processo em foreground.
- O upstream também declara que `checkDisplay()` não consegue checar/atualizar displays conectados via `Port=modem`; portanto auto-identificação física não pode ser usada como condição para aplicar esse modo.
- **BOOT-051:** o fuso IANA salvo pelo painel é reafirmado no boot localmente, sem depender de nova detecção de região.
- **PERF-051:** o watcher de estado Ao Vivo reduz wakeups de 80 ms para 160 ms. Nenhuma alteração RF/gateway acompanha essa otimização.
- **ARCH-010:** software/local permanece a estratégia de transcodificação, mas o Helix atual continua experimental para HVC/codec legado e não é promovido silenciosamente a produção.
- A 4.00.000 permanece ponto de rollback; a 4.00.001 é derivada diretamente de seus artefatos para preservar todo o restante confirmado como funcionando.

<!-- PU2PNY-OS-4.00.002-CANONICAL -->
## 4.00.002 — Display Pi-Star/WPSD + Helix experimental
- Substitui o caminho ativo de configuração de display próprio pelo contrato MMDVMHost/ON7LDS usado por Pi-Star/WPSD.
- Registra `DISPLAY-033..035`, `ARCH-011`, `PERF-052` e `REL-052`.
- Corrige a supervisão do ON7LDS NextionDriver com base no comportamento real do upstream: `-d` mantém o processo em foreground; a 4.00.001 havia removido esse sinalizador por interpretação incorreta e não é baseline aprovada de display.
- Nenhum `.hmi/.tft` é auto-gravado. O layout selecionado deve corresponder ao que já está na tela.
- Helix ganha controle explícito off/shadow/process para teste; cross-mode legado continua indisponível sem backend codec externo real/autorizado.
- RF/DMR/D-Star/YSF/rede/wizard/Ao Vivo e demais áreas confirmadas funcionando permanecem baseline protegida.


## 2026-10-22 — display isolado
5.00.002 DISPLAY ONLY: causa confirmada em binário/código: 5.00.001 usava aplicador histórico 0.3.30 e desligava MMDVM-Display; host MQTT não possui renderer Nextion. Novo aplicador controla apenas display, restaura renderer oficial e liga ON7LDS via adapter local. Nenhuma mudança RF/rede/protocolos. Não afirmar HW PASS.


### Evidência local final — 5.00.002 / 2026-10-22
- PASS SW: 6 testes de configuração/segredos/porta RF/MQTT.
- PASS SW: renderer oficial 96a0705 compilado x86_64, broker Mosquitto isolado, comandos standby com identidade da fixture e DMR com chamador/TG da fixture capturados em host/display-in. Dados de teste não são instalados nem telemetria real.
- PASS SW: ida e volta ON7LDS UDP loopback↔MQTT, preservando framing 0x80.
- HW: PENDENTE. OLED/LCD paridade integral: NÃO VERIFICADO; implementação existente preservada.
- GitHub push: BLOQUEADO pela revisão automática por publicação externa considerada não autorizada. Não contornar. Workflow ARM32/ARM64 e publicação não iniciados.
- Imagens novas: NÃO ENTREGUES. Retomar por revisão/publicação da branch local pu2pny-os-5.00.002-display-only, executar CI e resolver falhas antes de disponibilizar assets.


### Retomada autorizada — 2026-10-22
Usuário autorizou explicitamente publicação, correções automáticas e build das imagens para teste físico. Bloqueio anterior de autorização superado. Build/CI em preparação; nenhuma imagem nova entregue ainda.


## 5.00.002 — entrega verificada / 2026-10-22
- Estado: ALPHA / CANDIDATA PARA TESTE FÍSICO, publicada. SW/CI PASS; VPS PASS para configuração/whitelist em memória; HW PENDENTE.
- Branch: `pu2pny-os-5.00.002-display-only`. Commit fonte das imagens e tag: `56a0b6a4a97fee4cd35314e0f3943918a32fbc2d`.
- Release: https://github.com/PU2PNY/2PNY-OS/releases/tag/v5.00.002
- CI: https://github.com/PU2PNY/2PNY-OS/actions/runs/39775950167 — source, ARM32, ARM64 e publish PASS. Baseline Guard e CI Policy também PASS.
- ARM64: `PU2PNY-OS-5.00.002-arm64.img.xz`, 597946604 bytes, SHA-256 `f14e952df5396cc04f30feefcc6c0485f54be3c78fcb07f887a5bb06178e4271`.
- ARM32: `PU2PNY-OS-5.00.002-arm32.img.xz`, 683461636 bytes, SHA-256 `9189df04882eff46a2824e5af6a367545edc21ae6f1714bac5042537714f5f12`.
- Ambos: arquitetura ELF, manifesto completo de conteúdo fora de display/versionamento preservado, fsck, montagem somente leitura, XZ e SHA-256 PASS. Assets existem e digest publicado corresponde ao checksum.
- Sem mudança no motor RF, gateways, protocolos, Wi-Fi ou firmware/HMI. OLED/LCD diretos preservados, sem paridade física integral comprovada.
- Para HMI que exibe USE NextionDriver/ON7LDS: habilitar Display e selecionar ON7LDS L3 (ou L3 HS somente se esse for o HMI instalado); salvar; testar standby/RX/TX e persistência após reboot. COMOK não comprova o HMI nem atualização visual.


## 2026-11-08 — DISPLAY-045 (candidata de correção, base v5.02 `eec7a9f`) — NÃO PUBLICADA
- Defeito reportado pelo usuário: telas conectadas não mostram os dados da MMDVM e o perfil anterior não volta após desligar/ligar (relatos de usuários da imagem 32 bits).
- Causa no código (SW, reproduzida em teste): `runtime/display/apply.py::select_persisted_modem_display` tratava `display_candidate`/`mmdvm_display_candidate`, estado que o probe grava no boot, como classificação real de OLED/LCD, ignorava o perfil `nextion_mmdvm` salvo e seguia pelo aplicador OLED/LCD legado. O serviço `2pny-display-reconcile` então nunca reativava a Nextion.
- Alteração mínima: apenas essa seleção em `runtime/display/apply.py`. Sem mudança em RF, MMDVMHost, gateways, protocolos, rede/Wi-Fi, wizard, NextionDriver, HMI/TFT.
- Teste novo: `ci/test-display-045-boot-reapply.py` (falha no arquivo original, passa no corrigido).
- NÃO resolvido nesta entrega: restauração automática do perfil de protocolo após reboot (`2pny-profile-autostart`). Causa não comprovada; depende de logs do aparelho afetado.
- Validação: SW PASS apenas pelo teste acima. VPS, HW e imagem ARM32/ARM64: NÃO VERIFICADO / PENDENTE.


## 2026-11-08 — NET-045 (candidata de correção, base v5.02 `eec7a9f` + DISPLAY-045) — NÃO PUBLICADA
- Defeito reportado: às vezes o hotspot não reconecta sozinho ao Wi-Fi depois de desligar/ligar (imagem 32 bits/Pi Zero).
- Causa provável no código (SW): `runtime/5x/2pny-wifi-apply.py` não definia `connection.autoconnect-retries`; o NetworkManager desiste após poucas tentativas. Causa real em hardware: NÃO VERIFICADA (sem log de aparelho afetado).
- Alteração mínima: `2pny-wifi-apply.py` passa a gravar `connection.autoconnect-retries=0`; novos `runtime/5x/2pny-wifi-retry-reconcile.py` e `.service` reparam perfis já salvos. Sem mudança em RF, MMDVMHost, gateways, protocolos, display ou wizard.
- Teste novo: `ci/test-net-045-wifi-autoconnect.py` (falha no arquivo original, passa no corrigido).
- Validação: SW PASS apenas pelo teste. VPS e HW: NÃO VERIFICADO / PENDENTE. Instalação do reconcile em imagem exige patch de imagem e pipeline ainda não criados.

## 2026-11-08 — PU2PNY-OS 5.03 desenvolvimento, atualização de baseline
- Release base 5.02.1 publicada em 2026-11-08: tag pu2pny-v5.02.1, commit 4763df6d03aa371554e813c2fed30e70f4601926; CI 42474128395, builds/publish PASS. Entradas históricas 5.02.1 “NÃO PUBLICADA” são snapshots anteriores a esse resultado e não retratam o estado atual.
- Criada branch release/pu2pny-5.03 a partir da tag/commit da 5.02.1; primeira correção 9f0d6b0 (BOOT-053/DISPLAY-053), builder de imagem protegido 45380f2.
- BOOT-053: corrigida a falsa condição de saudável no wrapper de retry; adicionada ativação do retry baseada em atualização de hardware-probe sem remover o timer existente. MMDVMHost, gateways, autostart principal e perfil comprovado não são alterados.
- DISPLAY-053: OLED passa a listar URL, temperatura SoC real e uptime, sem tocar o fluxo aprovado Nextion ON7LDS nem os drivers LCD/OLED.
- Nenhum erro físico do Pi Zero, LED ou ganho de performance medido foi dado como corrigido. Nem edição de indicativo/DMR ID nem abertura forçada de navegador em STA/Ethernet foram implementadas.

## 2026-11-08 — REL-053: PUBLICAÇÃO VERIFICADA 5.03.000
- Tag: pu2pny-v5.03.000; commit da imagem e do CI: 9e4dce71cb16c9cd3bee7bcaf20533b418d25343.
- Release: https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.03.000
- CI: https://github.com/PU2PNY/2PNY-OS/actions/runs/42518978228 — tests, build ARM32, build ARM64, publish: success.
- ARM32 (ARMv6 base preservada): pu2pny-32-5.03.img.xz, 675225472 bytes, SHA-256 d010b67ca9f13709b4ca47aab4767ed564008b3377a8f42c40ae53616d5c2ecd.
- ARM64: pu2pny-64-5.03.img.xz, 597888840 bytes, SHA-256 12bf3ebe51df34392ffec1c6de5fbf97dd985250760c8cc424f38bba6e8aa9d7.
- Dois BUILD-INFO-*.json e dois arquivos .sha256 presentes no GitHub. Verificações XZ, hash, filesystem, diff completo de escopo e preservação de binários RF passaram em CI.
- BOOT-053, DISPLAY-053 e REL-053: SW/CI PASS. Níveis VPS/HW/PROD: NÃO VERIFICADO / PENDENTE / NÃO APROVADO, respectivamente.
- Esta release é **ALPHA PARCIAL PARA TESTE FÍSICO**: o erro de reconhecimento no Pi Zero, LED por modelo, desempenho medido de boot/troca/rede, displays SH1106/LCD/Nextion de outros modelos, edição de indicativo/DMR ID e captive portal em STA/Ethernet NÃO foram resolvidos nesta versão. Não reivindicar a correção desses itens.
- Os relatos anteriores de “sem imagem” aplicavam-se à fase de desenvolvimento; esta seção registra a publicação final real.

## 2026-11-08 — 5.04.000 (em desenvolvimento, SW)
- IDENTITY-054: página Protocolos ganha card para alterar indicativo e DMR ID (`/api/identity/apply` -> `2pny-identity-apply`: 2pny-rf-apply, depois 2pny-protocol-profiles activate, depois config.json; falha restaura a identidade anterior).
- EXPERT-054: página Expert ganha diagnóstico por botões (`/api/expert/cmd`): lista fixa de comandos somente leitura, senhas/chaves ocultadas, copiar/baixar. A requisição nunca carrega linha de comando.
- DISPLAY-054: LCD HD44780 16x2/20x4 passa a exibir páginas rotativas (indicativo/ID, IP, pu2pny.local, temperatura SoC, uptime, dados de chamada); só valores medidos.
- 2pnyd reconstruído (duas rotas novas); demais binários RF e perfil idênticos à 5.03. Defeito de regex (backtracking) no mascaramento de segredos encontrado e corrigido durante os testes.
- Não resolvido: erro de reconhecimento do Pi Zero (sem causa no código; o código só lê o modelo), medição/ganho de velocidade, SH1106/Nextion ampliados, captive portal em STA/Ethernet. LED = telas (esclarecido pelo usuário).

## 2026-11-08 — 5.05.000 (em desenvolvimento, SW)
- DISPLAY-055: causa do OLED apagado encontrada no código: o probe só lista I2C já registrado pelo kernel (um OLED comum nunca aparece) e, com MMDVM presente, substitui qualquer indício por "Nextion pelo modem"; o display-core então nunca iniciava o OLED/LCD. Agora o display-core varre o I2C (leitura, 0x3C/0x3D/0x27/0x3F), respeita /var/lib/2pny/oled.json e nunca sobrepõe Nextion comprovado/persistido.
- Expert: seleção SSD1306 / SH1106 / 128x32 / LCD 16x2 / 20x4 / nenhuma (`/api/oled/config`), como no Pi-Star/WPSD; diagnóstico de telas mostra config.txt, módulos i2c/spi, oled.json e display-status.
- OLED e LCD: páginas com modem MMDVM (tipo, firmware, porta@baud, modos, MCU, UDID curto) e Raspberry (placa, carga, RAM livre, SD livre, MHz). Valores ausentes são omitidos.
- Não verificado em hardware. Habilitação do I2C no sistema (dtparam=i2c_arm=on) não foi verificada na partição de boot desta imagem.

## 2026-11-09 — 5.06.000 (em desenvolvimento, SW)
- CLOCK-056: relato "escolho America/Sao_Paulo, saio do menu e volta Europe/London". Causa NÃO comprovada (diagnóstico enviado não traz `timedatectl`). Encontrado: a página já fazia detecção automática por navegador mas só ajustava o fuso, nunca a hora, e erros de aplicação eram engolidos. Mudanças: helper privilegiado confirma o fuso e, se `timedatectl` não fixar, grava o link `/etc/localtime` (+drop-in `ReadWritePaths=/etc`); rota `/api/clock/browser` ajusta fuso e, com NTP não sincronizado e deriva >2 min, a hora a partir do navegador (devolvendo o NTP depois); fuso manual sempre vence; Expert ganha "Relógio e fuso" para coletar a evidência.
- VOICE-056: não existia gerador de hora cheia (o marcador `voice-hourly.enabled` não era lido por ninguém). Novo timer horário monta a frase a partir de `TIME_en_GB` (somente inglês; não há voz de hora em português nos dados do gateway) e transmite com `dgwvoicetransmit`. Só atua com voz+hora cheia ligadas, protocolo D-Star, MMDVMHost e gateway ativos. Alias `linkedto` no índice en_GB (o gateway registrava "Cannot find the AMBE index for *linkedto*"). Aceitação pelo gateway/porta do `dgwvoicetransmit`: NÃO VERIFICADO.
- BOOT-056: `2pny-fast-resume` (ExecStartPre do autostart) inicia MMDVMHost e o gateway D-Star sem regenerar configuração quando `network-radio.json` comprova o último perfil; qualquer dúvida cai na ativação original, inalterada. Ganho de tempo: NÃO MEDIDO.
- PROTO-056/crossmode: leitura de documentação: `MMDVM_CM` (transcodificação por software) lista Pi 2/3/4 e não suporta Pi Zero/1, variantes D-Star "ainda não funcionais"; refletores XLX com transcodificação convertem no servidor. Expert mostra o estado real; runtime local permanece desabilitado conforme PROTO-047.
- Não alterados: MMDVMHost, DMRGateway, NextionDriver, probe, autostart, apply de perfil/RF/Wi-Fi.

## 2026-11-09 — 5.07.000 (em desenvolvimento, SW)
- Origem: teste em Pi Zero W com 5.05 (carga 7,16 em núcleo único; `Failed to fetch` ao salvar DMR; Expert sem dados; `pu2pny.local` igual ao da imagem 64 bits).
- BOOT-057: o timer de retomada (90 s) disputava CPU com o "Salvar" do usuário (rf-apply expirava em 45 s). Novo `ExecCondition` `2pny-retry-gate`: não roda durante ativação em curso, nem com carga > 2×núcleos, e recua 90 s → 30 min; reinicia o recuo quando há perfil novo. Timeouts de `2pny-protocol-profiles` 45/55 s → 150 s e espera do assistente 90 s → 240 s (só o limite). Drop-ins `CPUWeight` baixo em netdiag/aprs/station/display-core. Retomada rápida estendida a DMR e YSF (além de D-Star), mesma regra de prova completa.
- SPEED-057: `/api/dashboard` chamava `systemctl is-active` 11 vezes por requisição; agora uma chamada em lote com cache de 3 s.
- EXPERT-057: comandos "Carga e processos" (`load`) e "Aplicação de perfil" (`apply`), e `boot` com jobs/cadeia crítica, para achar a causa da carga.
- HOST-057 (somente imagem 32 bits): nome mDNS `pu2pny32.local` (hostname, hosts, avahi, guard, alias, wizard, captive, OLED/LCD, daemon). Imagem 64 bits mantém `pu2pny.local`.
- Não resolvido/não verificado: reinícios repetidos do MMDVMHost (dentro dos scripts RF protegidos, não alterados), causa real da carga do Pi Zero, campos Nextion "?", OLED/LED, `2pny-display-boot.service` falhado, selo "Internet não conectada", modo Direct privado ponto a ponto (precisa de desenho: sem servidor/IP fixo exige ponto de encontro). Tudo SW; HW pendente.

## 2026-11-09 — 5.08 (SW)
- **CLOCK-058:** `timedatectl`/`systemd-timedated` retornam "Permission denied" nas imagens de campo, e `/etc/timezone` (lido pelo timedatectl) divergia do link `/etc/localtime` (lido pela libc). O fuso passa a ser lido e confirmado só pelo link; o helper grava o link de forma atômica, `/etc/timezone` e confirma por realpath. A restauração no boot usa o mesmo caminho. O painel deixa de consultar `timedatectl show`.
- **DISPLAY-058:** `i2c-dev` carregado no boot e antes do display-core; varredura I2C também quando a classe é `nextion_mmdvm` sem confirmação física (override manual); `2pny-display-apply` mantém/inicia o display-core quando acha OLED/LCD; timeout do pedido 35→120 s. Nextion confirmado nunca é substituído.
- **SPEED-058:** foto do operador baixada em job assíncrono (cache primeiro), espaçamento da consulta 15→4 s.
- **BOOT-058:** mascarados `userconfig.service`, timers apt-daily/apt-daily-upgrade/man-db/e2scrub/dpkg-db-backup, ModemManager, triggerhappy e udisks2 (links para /dev/null; reversível removendo o link).
- **UI-058:** barra Wi-Fi com % calculado de dBm quando ausente; cores verde/amarelo/vermelho por qualidade; logotipo transparente no cabeçalho/assistente e favicon (assets/brand/web).
- **EXPERT-058:** comandos Wi-Fi (nmcli, iw, scan), NetworkManager, uptime/tempos de unidades, /dev/i2c-*, `errors`.
- **NÃO CORRIGIDO (investigar com dados de campo):** lentidão de ativação (reinícios do MMDVMHost nos scripts protegidos), YSF sem conectar, Nextion exibindo só CPU, assistente preso em "Conectando…" após queda do AP, Wi-Fi não persistido no Pi 4, subtensão (throttled=0x50000).

## 2026-11-09 — 5.09 (SW)
- **WIZ-059:** relato de campo (32 bits): o DMR conectou, mas o assistente mostrou "signal is aborted without reason". Causa: `getj` cancelava toda chamada após 15 s e "salvar e ativar" demora mais no Pi Zero; o rádio continuava ativando. Agora a chamada tem 150 s e, se a espera for cancelada, o assistente segue para a consulta do estado real (`/api/rf`) em vez de acusar erro. Não altera RF, MMDVMHost nem gateways.
- **DISPLAY-059:** relato de campo (OLED 128×64, funcionou pela primeira vez na 5.08): letras pequenas e borradas. Causa: fonte bitmap padrão (6×11) achatada à força para 9 px. Em painéis com 48+ linhas, o texto passa a usar DejaVu Sans Mono Bold 12 em tamanho nativo (4 linhas de dados + título); painéis de 32 linhas mantêm o desenho anterior. Falha ao abrir a fonte volta ao desenho anterior.
- **NÃO CORRIGIDO:** lentidão de ativação, YSF sem conectar, assistente preso em "Conectando…", Wi-Fi não salvo no Pi 4. Crossmode e bases Orange Pi/NanoPi planejados para a 5.10.

## 2026-11-09 — 5.10 (SW)
Diagnósticos de campo da 5.08 (Pi Zero W 32 bits e Pi 4 64 bits) analisados contra o código da imagem.
- **CLOCK-060:** o fuso nunca mudava. Causa: `2pny-timezone-apply.service` roda com `ProtectSystem=full` e `ReadWritePaths=/run/2pny /etc/timezone`; o helper (5.06 via timedatectl bloqueado, 5.08 via link) não podia substituir `/etc/localtime` (somente leitura no sandbox). Drop-in `ReadWritePaths=/etc` só para essa unidade oneshot. O teste da 5.08 não pegava isso por rodar fora do sandbox; ver TEST_MATRIX.
- **DIRECT-060:** a imagem 32 bits trazia `2pny-direct-core` AArch64 (ELF 64-bit, máquina 183) que o Pi Zero W não executa; `2pny-direct.service` reiniciava a cada ~8 s (carga 5,3 num núcleo, CPU 86%, Ao Vivo travado após o TOT). Build ARMv6 (GOARM=6) do código do projeto (`src/direct-core`, mesmos 5 arquivos do build 0.3.16), autoteste sob qemu no CI; a unidade passa a parar após 4 falhas em 15 min (`RestartSec=30`).
- **BOOT-060:** `2pny-auto-maintenance` e `2pny-hostfiles-update` esperam 5 min após o boot (sleep, sem CPU).
- **UI-060:** logo = nome PU2PNY-OS sem a frase pequena, 30/38 px; Protocolos ganha botão "Editar indicativo e ID" no topo (o cartão já existia no fim da página, com a API `/api/identity/apply`). `protocols.html` deixou de ser byte-idêntico por ordem explícita do usuário.
- **EXPERT-060:** dono dos arquivos do NetworkManager e arquivos de pedido/resultado do relógio.
- **ACHADOS NÃO ALTERADOS:** (a) o NetworkManager do 64 bits recusa `2pny-setup`, `2pny-ethernet-setup` e `2pny-ethernet` ("File owner (1001) is insecure"): possível relação com o AP/captive e com "Wi-Fi não salvo"; corrigir muda a rede e exige decisão/teste, então só foi instrumentado no Expert; (b) subtensão no 64 bits (`throttled=0x50000`, "Undervoltage detected" repetido): fonte/cabo; (c) 2 abas ao entrar no AP e wizard "welcome" em equipamento já configurado: causa não confirmada; (d) Nextion sem TEMP/CYCLES/LOAD/DISK/IP: causa não confirmada; (e) D-Star `connected:false` logo após ativar: sem log do gateway.


## 2026-11-12 — 5.11 em implementação (não entregue)
Base confirmada: `release/pu2pny-5.10`, tag `pu2pny-v5.10.000`, commit `1a280662d4ab48bb1ea9726874a11c1e5a126c55`. Branch de trabalho: `release/pu2pny-5.11`. Ordem completa: [docs/PU2PNY-OS_5.11_ORDEM_DE_TRABALHO.md](docs/PU2PNY-OS_5.11_ORDEM_DE_TRABALHO.md). CLOCK-060, DIRECT-060, BOOT-060, UI-060 e EXPERT-060 preservados. Nenhuma imagem 5.11 publicada; CI/VPS finais e HW ainda pendentes.

| ID | Implementação e critério de aceite | Estado atual |
| --- | --- | --- |
| SEC-511 | Corrigir UID/GID 1001, preservar outros donos intencionais, gate global de donos e manifesto com metadados; `/var/lib/2pny` root:root 0755 | código; imagem pendente |
| PERF-511 | Seguidor journal único, EOF removido, retentativa 5→60 s, select 1 s, probes 30 s ocioso/2 s ativo; preservar snapshots/histórico | SW local PASS para EOF/CPU; integração pendente |
| NET-511 | Autoconnect infinito, recuperação AP sem clientes/sem operação manual, lock, recuo 2→5 min, checagens pesadas a cada 12 s; dispatchers fora de nmcli síncrono | código; simulação completa pendente |
| BOOT-511 | Retomada MMDVM até 45 s com diagnóstico, mDNS atômico/idempotente e prioridade baixa de manutenção; preservar atraso BOOT-060 | código; VPS/HW pendente |
| DISPLAY-511 | OLED fixa 128×64/128×32, páginas I2C incrementais, CPU standby próprio e sysfs legível; sem alterar ON7LDS/HMI/TFT | SW local OLED PASS; barramento/HW pendente |
| HOST-511 | pu2pny64.local/pu2pny32.local, inclusive escritores legados de hostname; portal canônico | overlay fixture SW PASS; navegador/HW pendente |
| UI-511 | Textos neutros, relógio oculto com DOM preservado, aviso de subtensão atual/histórica | código; navegador pendente |
| VOICE-511 | DMR/D-Star/P25/NXDN separados, INIs aplicados com rollback; hora cheia só D-Star | SW local edição e rollback PASS; serviço/API/HW pendente |
| PROTO-511 | MMDVM_CM pinado 7328c9e, compilação ARMv6 no rootfs Raspbian descartável, cinco modos, exclusividade e rollback | implementação em teste; CI/HW pendente |
| P2P-511 | DMR em grupo, BEP5 a cada 5 min, UDP direto, autenticação/anti-replay e cifra quando disponível, sem relay | SW loopback autenticado PASS; DHT/NAT/RF pendente |
| BOARD-511 | Orange Pi Zero H2+ e NanoPi NEO H3; bases Armbian Bookworm minimal, UART1/I2C0, chroot e gates | base Orange localizada; base Nano minimal verificável ainda não localizada |
| REL-511 | Quatro imagens, SHA, commit/tag, CI, fsck, RO, manifesto e HW NOT_VERIFIED | NÃO ENTREGUE |

Exceção de baseline autorizada PROTO-511: `2pny-protocol-profiles` recebe somente chamada a `2pny-crossmode off` antes de ativar outro perfil. A geração RF e de gateways permanece intacta; os binários MMDVM-Host, DMRGateway, NextionDriver, MMDVM-Display e Direct core permanecem protegidos byte a byte.

Pendências herdadas: velocidade real, YSF remoto, D-Star logo após ativar, wizard após queda de AP e duplicação de abas não estão comprovadamente resolvidas. URL canônica não garante uma única aba. Chroot executa o userland, não testa boot do kernel nem UART/RF real. Subtensão requer verificar fonte/cabo; software não comprova a correção física.

Fontes: [systemd 252](https://www.freedesktop.org/software/systemd/man/252/systemd.service.html), [BEP5](https://www.bittorrent.org/beps/bep_0005.html), [MMDVM_CM pinado](https://github.com/juribeparada/MMDVM_CM/tree/7328c9e9532d29cf4d9d7d24541d57f825207be4), [MMDVM-Host DMRNetwork pinado](https://github.com/g4klx/MMDVM-Host/blob/590c531/DMRNetwork.cpp), [NanoPi NEO fabricante](https://wiki.friendlyelec.com/wiki/index.php/NanoPi_NEO), [Armbian Orange Pi](https://armbian.com/boards/orangepizero), [Armbian NanoPi](https://armbian.com/boards/nanopineo).


### 5.11 — correção após validação de integração, 2026-11-12
- PROTO-511: causa SW comprovada: DMR2YSF/DMR2NXDN upstream aguardavam RPTL/RPTC indefinidamente; o MMDVM-Host 590c531 em modo Gateway emite DMRD/DMRP. `ci/patch-cm-gateway-5.11.py` adapta somente os conversores pinados: inicializa o ID com a configuração real, remove a espera pelo login antigo e responde DMRP. Não modifica MMDVM-Host/INI. Teste com os dois executáveis nativos: inicialização e ping raw PASS; codec/RF/HW pendentes. BUILD-INFO registra SHA do patch.
- SEC-511/REL-511: primeiro CI 43229285369 reprovou o teste de fixture porque o runner UID 1001 não tem permissão de chown. A normalização é operação root por projeto; o teste foi corrigido para executar como root e injetar explicitamente donos 1001. Não foi removido nem enfraquecido o gate de imagem.
- VOICE-511/P2P-511: integração deve incluir as unidades `.path` dedicadas; timeout do backend para esses dois helpers passa a 180 s. O request é consumido antes de aplicar. Testes reais dos watchers ainda pendentes.
- P2P-511: negociação autenticada de capacidade de cifra permite pares com e sem cryptography, com indicação por par. Direct individual recebe controles explícitos liga/desliga e preserva a limitação DIRECT-060.


### 5.11 — evidência SW/VPS e ajuste de identidade, 2026-11-12
- CI 43231353765: job tests PASS (regressão 5.10, novos testes 5.11, dois conversores nativos em Gateway raw e backend). Builds ARM32/ARM64 iniciados; isso ainda não comprova imagem entregue.
- VPS SentinelX: backend nativo e testes HTTP PASS; watchers systemd reais com pastas/gateways simulados PASS para aplicação de voz, rollback de voz e rollback do modo, preservando INI RF. Script reproduzível: `ci/test-vps-5.11.py`. Nenhuma unidade RF de produção foi instalada ou acionada nesse teste.
- P2P-511: teste acrescenta resposta get_peers simulada, token e announce_peer com implied_port=1; não comprova DHT pública/NAT.
- PROTO-511: YSF→NXDN exige ID NXDN real (campo próprio, configuração explícita ou lookup por indicativo). Não reutilizar/supor DMR ID como NXDN ID.
- NET-511: aguardar 2 min depois de subir o AP de recuperação antes da primeira retentativa e gravar a transição de recuperação uma vez, sem regravar o mesmo estado a cada 12 s.
- BOARD-511: base NanoPi Bookworm minimal ainda BLOQUEADA. Há Bookworm CLI 23.11.1 no arquivo oficial, que não foi substituída silenciosamente pela variante minimal solicitada. Imagem 5.11 completa continua NÃO ENTREGUE.


### 5.11 — BOARD-511: base NanoPi desbloqueada e política de boot, 2026-11-12

- Localizada no arquivo oficial antigo a **Armbian 23.8.1 NanoPi NEO Bookworm minimal**, kernel 6.1.47. A imagem foi baixada na VPS: **265906900 bytes**, SHA-256 `4167ff841ff68592c8d8704072079c18e44f38175f836a3d234be0594ad6ecda`, integridade XZ **PASS**. Checksum idêntico no servidor oficial e no espelho. URL e checksum fixados em `ci/board-bases-5.11.json`; nenhuma troca para Trixie/Jammy/CLI.
- Montagem somente leitura confirma Debian 12 Bookworm, `BOARD=nanopineo`, overlays `sun8i-h3-uart1.dtbo` e `sun8i-h3-i2c0.dtbo`. Isso não comprova boot/UART/RF físico. A base é histórica; kernel e bootloader seguem preservados pelos gates.
- A base NanoPi habilita `armbian-firstrun-config.service`, além de firstrun. O transplante agora mascara também essa unidade e os serviços/socket de systemd-networkd, habilitando NetworkManager explicitamente. Objetivo: nenhum assistente Armbian concorrente, um único dono da rede. O resize separado permanece intacto.
- Teste novo reproduz essas unidades em filesystem temporário e verifica máscaras, NetworkManager, preservação de resize e idempotência. Na VPS: **TEST_511_BOARD_BOOT_POLICY_OK**, junto de **TEST_511_OK**, **TEST_511_MODE_I2C_OK** e **TEST_511_NETWORK_SIMULATION_OK**.
- CI anterior [43233187118](https://github.com/PU2PNY/2PNY-OS/actions/runs/43233187118): testes e builds Raspberry ARM32/ARM64 **PASS**. O job NanoPi falhou por base ausente antes deste ajuste. As quatro imagens finais precisam de novo CI no mesmo commit; **release 5.11 ainda NÃO ENTREGUE; HW PENDENTE**.
- Critério de aceite BOARD-511: as duas bases Bookworm minimal verificadas, chroot/dependências/unidades, NetworkManager exclusivo, kernel/U-Boot preservados, fsck/RO/XZ/SHA PASS; só promover boot/UART/RF após teste HW.

Fontes: [arquivo oficial NanoPi](https://rsync.armbian.com/oldarchive/nanopineo/archive/), [checksum oficial](https://rsync.armbian.com/oldarchive/nanopineo/archive/Armbian_23.8.1_Nanopineo_bookworm_current_6.1.47_minimal.img.xz.sha), [espelho de download](https://armbian.hosthatch.com/archive/nanopineo/archive/), [pinout do fabricante](https://wiki.friendlyelec.com/wiki/index.php/NanoPi_NEO).

## 2026-11-12 — REL-511: prerelease 5.11.000 publicada (SW/CI PASS; HW pendente)

**REL-511 (documentação pós-publicação):** sincronizados estado real, rastreabilidade da release e hash dos quatro artefatos; nenhuma alteração de RF, protocolos, drivers, sistema de arquivos das imagens ou código de execução.

- Release: [pu2pny-v5.11.000](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.11.000), publicada em 12/11/2026 às 16:18 UTC como **prerelease ALPHA**, não produção.
- Código-fonte exato das quatro imagens e tag: [`92914a3a19b9713416b541cfa93fc98b37261c9c`](https://github.com/PU2PNY/2PNY-OS/commit/92914a3a19b9713416b541cfa93fc98b37261c9c); branch `release/pu2pny-5.11`.
- [GitHub Actions `43252249844`](https://github.com/PU2PNY/2PNY-OS/actions/runs/43252249844): seis jobs concluídos com **success**: `tests`, `build (arm32)`, `build (arm64)`, `boards (opizero)`, `boards (nanopineo)` e `publish`.
- A etapa `publish` verificou os quatro arquivos `.img.xz`, `xz -t`, `sha256sum -c` e os quatro `BUILD-INFO-*.json` com versão `5.11.000`, commit fonte correto, filesystem `PASS` e `HW=NOT_VERIFIED`.
- Gate SW/CI: **PASS** para os testes executados e as quatro imagens publicadas. VPS: testes de backend e simulações anteriores documentados; não equivale a teste RF. **HW: PENDENTE; PROD: NÃO APROVADO**.
- Regressões físicas ainda não homologadas na 5.11: boot/retomada do último protocolo, Ethernet e Wi-Fi de recuperação, hotspot/AP, mDNS, OLED, Nextion e dados CPU, voz DMR/D-Star/P25/NXDN, cinco crossmodes, Direct DMR em duas redes com DHT/NAT reais, RF e boot físico nas placas Orange Pi/NanoPi. Limitações MMDVM_CM, CGNAT e disponibilidade de cifra continuam explícitas nas notas da release.
- As afirmações anteriores de que a 5.11 não foi entregue **eram verdadeiras no momento daqueles registros históricos**; esta evidência posterior as substitui somente quanto ao estado de build/publicação, sem converter pendências de hardware em PASS.

| Placa | Artefato | SHA-256 (digest publicado) |
|---|---|---|
| Raspberry ARM32 | [`pu2pny-32-5.11.img.xz`](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.11.000/pu2pny-32-5.11.img.xz) | `6a90ac0080fd72c28d3df8d52b44d076bb7764bd530b5673798180987a1262d9` |
| Raspberry ARM64 | [`pu2pny-64-5.11.img.xz`](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.11.000/pu2pny-64-5.11.img.xz) | `b8b6d844230c0611566625ab050e30dfbf89ca7adb367412e4f14a4bcf0bb103` |
| Orange Pi Zero H2+ | [`pu2pny-opizero-5.11.img.xz`](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.11.000/pu2pny-opizero-5.11.img.xz) | `343390b1c0d8edc1a4c3e32e2afb67f2103adfc136486756c79103c40ac8f1ad` |
| NanoPi NEO H3 | [`pu2pny-nanopineo-5.11.img.xz`](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.11.000/pu2pny-nanopineo-5.11.img.xz) | `7119966a09e77d0297209973c5e9bc47a746cff18e4bf74f7c66786703c21eb7` |

## 2026-11-13 — início das correções P0 da 5.12

- Base confirmada: `release/pu2pny-5.11`; branch isolada `release/pu2pny-5.12`; issue #23 aberta para as evidências Raspberry Pi 3, Raspberry Pi 4, Orange Pi Zero e relato ARM32. Nada alterado na release 5.11 aprovada como origem/rollback.
- **BOOT-512:** localizada a espera `ExecStartPre=/bin/sleep 300` introduzida na 5.10. Patch novo remove somente o drop-in de atraso após preflight, remove habilitação de boot direta de manutenção/listas, mantém hostfiles timer e agenda manutenção por timer. Backups preservados. **SW/VPS PASS em fixture**, tempo real em Raspberry segue HW PENDENTE.
- **NET-512:** construtor Armbian 5.11 excluía `2pnyd.service` por usar glob `2pny-*`. Novo `ci/build-board-5.12.py` copia e valida explicitamente a unidade e seu link multi-user. **SW/VPS PASS em fixture**, acesso real pelo AP Orange Pi/Nano HW PENDENTE.
- `ci/build-5.12.py` prepara overlay independente sobre a imagem 5.11 imutável, verifica diferenças autorizadas e arquivos RF protegidos. Build completo/CI/SHA/asset físico ainda PENDENTES nesta etapa.
- Não foram alterados MMDVMHost, DMRGateway, NextionDriver, frequência, slots, TG, color code, configurações de rede ou IP de AP. Não foi aplicado redesign visual: UI-512 permanece registrado como PENDENTE e depende dos gates P0.
- Evidências e matriz detalhada em `docs/PU2PNY-OS_5.12_RETORNO_TESTADORES.md`. Publicação da nova imagem requer gates documentados; nenhuma versão 5.12 foi declarada entregue.
