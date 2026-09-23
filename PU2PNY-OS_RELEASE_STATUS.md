# PU2PNY-OS — RELEASE STATUS

**Branch de trabalho:** `pu2pny-os-0.3.20-alpha`  
**Base preservada:** `pu2pny-os-0.3.19-alpha`  
**Rollback do ciclo:** `backup/0.3.19-pre-0.3.20-20260922`  
**Backup pré-organização documental:** `backup/0.3.20-pre-doc-governance-20260922`  
**Data do último feedback físico incorporado:** 2026-09-22  
**Estado global:** ALPHA / PARA TESTE FÍSICO. **Não PROD.**

> As seções de versões anteriores abaixo são histórico de validação e regressão. O estado corrente é o bloco 0.3.20-alpha e os documentos canônicos indicados em START_HERE.

## Baseline que não pode regredir

| Área | Estado | Evidência | Observação |
|---|---|---|---|
| AP `pu2pny` no primeiro acesso | HW PASS | usuário | conexão ao AP funcionou corretamente |
| `http://pu2pny.local/` no AP | HW PASS | usuário | acesso considerado excelente |
| Hardware Pi/MMDVM detectado | HW PASS | usuário + UI | preparação chegou a 100% |
| RF básica validada | HW PASS | usuário | não ampliar escopo antes de preservar |
| DMR funcional anterior | HW baseline | histórico físico do projeto | regressão obrigatória em toda nova imagem |
| Rollback ao falhar troca de protocolo | HW PASS | usuário | DMR/estado anterior voltou após erro |

## Bloqueadores atuais

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| NET-002 Wi-Fi pós-save/reboot | FALHA | HW | SSID selecionado não conectou ao roteador; AP reapareceu |
| NET-003 estado real do AP | FALHA | HW | painel mostrou "AP desligado" enquanto SSID permanecia visível |
| NET-004 Ethernet/mDNS pós-hotplug | PARCIAL | HW | IP DHCP `192.168.100.22` abriu; `pu2pny.local/wizard` não acompanhou o fluxo imediatamente |
| PROTO-002 D-Star | FALHA | HW | MMDVMHost não permaneceu ativo; rollback executado |
| PROTO-003 YSF | FALHA | HW | mesmo padrão; rollback executado |
| PROTO-005/006 preflight MQTT | FALHA | HW/DOC | log: `MQTT Error connecting: No such file or directory`; precisa diagnóstico antes do restart |
| LIVE-002 submenu atividade | FALHA | HW | abre e fecha com atualização |
| LIVE-003 BER/RSSI condicional | PENDENTE | HW | campos vazios ocupam a tela |
| LIVE-004 duração destacada | PENDENTE | HW | tempo difícil de localizar |
| DISPLAY-002..005 Nextion runtime | FALHA/PARCIAL | HW | flicker/retângulo vermelho e dados instáveis |
| APRS-001 notificação | PARCIAL | HW/browser | permissão negada; precisa fallback in-app |
| WIZ-001 idioma inicial | PENDENTE | DOC | requisito novo registrado |
| UI/NET diagnóstico Expert/rota | PENDENTE | DOC | requisito novo registrado |

## Diagnóstico técnico atual do erro MQTT

**Fato HW:** antes da falha, o MMDVMHost encerra normalmente por SIGTERM. Na tentativa com D-Star/YSF, o novo MMDVMHost registra erro de conexão MQTT e o serviço cai; a transação restaura a configuração anterior.

**Fato DOC/código:** a imagem 0.3.3 configura Mosquitto em loopback e o serviço MMDVMHost declara dependência de `mosquitto.service`. O aplicador multi-protocolo reescreve a configuração e reinicia MMDVMHost, porém hoje não executa um gate explícito comprovando que o broker está acessível para o usuário do rádio imediatamente antes do restart.

**Conclusão permitida neste momento:** existe uma falha no caminho de restart/preflight MQTT durante troca de protocolo. **A causa raiz exata ainda não é HW confirmada**; não atribuir a broker, biblioteca, arquivo ou permissão sem capturar estado runtime no momento da falha.

## Próxima sequência obrigatória

Rede/Wizard primeiro; depois preflight RF/MQTT; DMR regressão; D-Star; YSF; somente então Live/UI/Nextion/APRS. Cada bloco só avança após testes do bloco anterior e rollback disponível.

## Implementação 0.3.4 já staged

O código corretivo está na branch de trabalho, mas os estados HW da tabela acima continuam válidos até novo teste físico.

- Rede/Wi-Fi: correção staged; **SW/CI pendente, HW pendente**.
- Estado real do AP: correção staged; **SW/CI pendente, HW pendente**.
- MMDVMHost/MQTT/D-Star/YSF: preflight e rollback determinístico staged; **não chamar D-Star/YSF de funcionando antes do HW**.
- Ao Vivo, idioma, Expert, APRS e rodapé: implementação staged; **SW/CI pendente**.
- Nextion: mudança de renderização staged; **HW obrigatório** para confirmar ausência de flicker.
- Artefato 0.3.4: **ainda não liberado** até ARM64 + validação estrutural + SHA-256.

A causa raiz do erro observado ao trocar protocolos permanece classificada como não confirmada em HW. O código agora impede uma troca quando o endpoint MQTT local não está pronto e produz evidência mais específica para o próximo teste.

## Build 0.3.4-alpha publicado

**Estado do artefato:** SW PASS / Alpha para teste físico.

- GitHub Actions: source PASS.
- Build ARM64: PASS.
- Validação estrutural da imagem: PASS.
- SHA-256: gerado e anexado à release.
- Publicação: prerelease `v0.3.4-alpha`.
- Tamanho da imagem comprimida: 584112608 bytes.
- SHA-256 da imagem: `4bc808da8f4c3fc259dd72a66a08e68e1a704b5cf13f754692c9864b40282e2c`.

**Importante:** isso não muda os casos HW que ainda estavam FAIL/PENDENTE. Wi-Fi pós-reboot, DMR regressão, D-Star, YSF, Nextion e comportamento físico do Ao Vivo precisam ser retestados no Raspberry Pi/MMDVM/display real antes de qualquer estado PROD.

## Feedback físico da 0.3.4-alpha — 2026-09-20

### Preservar como HW PASS/positivo
- Primeiro AP `pu2pny` apareceu e `http://pu2pny.local/` abriu o primeiro acesso.
- Tela inicial de idioma foi aprovada visualmente.
- Preparação de Hardware chegou a 100% e foi considerada correta.
- RF foi validada.
- DMR conectou ao XLX e houve aviso de voz de conexão.
- TOT de 180 s efetivamente derrubou TX contínuo.
- Página Internet: conexão ativa, Ethernet e MTR foram aprovados.
- Submenu `+` do Ao Vivo agora permanece aberto.
- Página Protocolos foi aprovada visualmente.
- Nextion exibe ID/nome/RX/TX/TG/BER/CPU/temperatura/qualidade de Internet, embora o layout ainda precise ser substituído.
- Voz enviada ao rádio foi aprovada.

### Falhas/bloqueadores confirmados em HW
- Busca Wi-Fi inicial pode ficar presa em "Buscando..." sem lista.
- Hotplug Ethernet/reverificação não atualizou Internet imediatamente.
- Após Ethernet, `pu2pny.local` falhou com DNS_PROBE_FINISHED_NXDOMAIN; IP LAN abriu.
- Wi-Fi selecionado novamente não associou ao roteador; Ethernet permaneceu funcional.
- D-Star e YSF continuam falhando no restart do MMDVMHost com `MQTT Error connecting: No such file or directory`; rollback funcionou.
- DMR RF/XLX: TX e RX estão funcionando. Ao usar TG de controle para trocar módulo (ex.: 4003/C → 4002/B), o gateway muda/conecta corretamente, porém o painel continuava exibindo o módulo configurado C. Classificado como falha de sincronização de estado/UI, não falha RF.
- Ao Vivo/Histórico ainda pobres em colunas/dados.
- APRS: botões de notificação/atualização não deram feedback observável; mensagem saiu como enfileirada.
- Navegação "Trocar rede" força refazer etapas de primeiro acesso.
- Nextion precisa de layout PU2PNY moderno e pré-alerta de TOT.
- Timezone exibido de forma incoerente.
- Temperatura observada em torno de 51 °C; investigar carga/throttling antes de qualquer intervenção.
- Atualização anterior via painel ficou presa em 30% na Nextion; mecanismo deve ser fail-safe.

### Estado da 0.3.5-alpha
Branch criada a partir da 0.3.4-alpha publicada, com backup `backup/0.3.4-hw-feedback-20260920`. **Ainda não liberar imagem** até Rede/Wizard → DMR → D-Star → YSF → UI/Display/Update passarem pelos gates SW/VPS aplicáveis.


## Build 0.3.5-alpha publicado

**Estado do artefato:** SW PASS / Alpha para teste físico. **Não PROD.**

- GitHub Actions run `35513524374`: source PASS.
- Overlay 0.3.4 restaurado antes do overlay 0.3.5: PASS.
- Validação staged: PASS.
- Build ARM64: PASS.
- Normalização + SHA-256: PASS.
- Validação estrutural da imagem: PASS.
- Publicação da prerelease `v0.3.5-alpha`: PASS.
- Imagem: `PU2PNY-OS-0.3.5-alpha-arm64.img.xz`.
- Tamanho comprimido: 579582048 bytes.
- SHA-256 da imagem: `616d6089e2e699187e577104b070e757698d6f27a0917b5afb4d27ecaec1f5a9`.
- Commit do artefato: `77eb8322b66944f703273f9e8263ec39952d4d5d`.

### O que o CI comprova
Código Go/Python/Bash/JS válido nos gates definidos, overlay completo, build ARM64, integridade XZ, checksum, montagem/validação estrutural e publicação.

### O que continua exigindo HW
Wi-Fi pós-save/reboot, troca entre duas redes, mDNS após handoff, DMR módulo B/C no painel em tempo real, D-Star, YSF, Nextion PU2PNY Moderno, contagem TOT 10→0, APRS toast e atualização/manutenção no Raspberry Pi real. Nenhum desses itens foi promovido automaticamente para HW PASS por causa do CI.


## Feedback físico da 0.3.5-alpha — ciclo 0.3.6 aberto em 2026-09-20

**Regra de escopo:** REL-004. As novas funções aprovadas neste feedback pertencem à própria 0.3.6-alpha e não serão tratadas como roadmap futuro por conveniência. Quando uma função depender de hardware/cliente externo, a implementação deve chegar ao nível SW/VPS verificável nesta versão e continuar marcada como HW PENDENTE até o teste real.

### Baseline preservada
- DMR da 0.3.5 foi considerado excelente e permanece baseline de regressão obrigatória.
- Preparação de hardware automática foi considerada excelente e deve ser preservada.
- Não alterar caminho RF/DMR para corrigir UI, rede, D-Star, YSF, display ou update.

### Bloqueadores e funções obrigatórias da 0.3.6
- AP→Wi‑Fi ainda falha no handoff inicial; captive portal deve ser melhorado sem depender exclusivamente da abertura automática do navegador.
- Gerenciamento Wi‑Fi 1/2 apresentou erro `unbound variable`; edição pós-provisionamento não pode voltar ao wizard completo.
- DNS efetivo ficou inconsistente após troca; UI precisa confirmação de operações e retorno ao módulo.
- Tradução integral PT/EN/ES, timezone via backend autorizado e Expert com Estado Ao Vivo são obrigatórios.
- APRS: localização com permissão + toast global de mensagem.
- Display: layout profissional para Nextion e demais displays, com conteúdo proporcional à capacidade real.
- Histórico: atalhos QRZ/RadioID opcionais somente quando URL válida.
- D-Star e YSF permanecem HW FAIL de tráfego de rede e bloqueiam qualquer afirmação de protocolo funcional.
- Perfis independentes por protocolo são obrigatórios nesta versão.
- Update oficial com verificação, backup opcional, rollback e downgrade entra nesta versão.
- Manutenção deve mostrar último resultado e próxima execução elegível.
- Toda correção comum deve ser global.

### Gate
A 0.3.6-alpha só pode ser publicada para teste físico depois que os novos casos SW/CI de NET/UI/APRS/DISPLAY/UPDATE/PROTO passarem e o build ARM64 + validação estrutural + SHA-256 concluírem. A publicação será Alpha; D-Star/YSF/Wi‑Fi/perfis/display/update só viram HW PASS após novo teste real.

## Escopo adicional da 0.3.6-alpha — Rádio 1/2 e BrandMeister API

- Criado ponto de retorno antes da mudança DMR: `backup/0.3.6-pre-bm-suffix-api-20260920` no commit `116cab3b521af46d68e52af14efdbe1dbbba2d59`.
- **PROTO-010:** entra nesta própria 0.3.6-alpha a seleção `Rádio 1 (01)`, `Rádio 2 (02)` e aliases 01..99 para hotspot pessoal BrandMeister. O formato oficial é Radio ID de 7 dígitos + alias de 2 dígitos, total 9 dígitos.
- **PROTO-011/SEC-021:** BrandMeister recebe campo de API Key opcional, armazenado como segredo separado. Não será criado campo de `API Secret`, porque a documentação oficial consultada descreve uma única API Key/token.
- Hotspot Security continua sendo a credencial de conexão ao master BrandMeister; API Key não será usada como senha DMR.
- O helper DMR fisicamente validado não deve ser reescrito para esta função: a implementação deve reutilizar o suporte ESSID/alias já existente e limitar a mudança ao contrato UI/backend/segredo.
- Estes itens só podem ser marcados HW PASS depois de novo teste físico DMR com pelo menos `01` e `02`.

### Implementação/evidência — alias DMR e API BrandMeister
- Código da 0.3.6 implementa seleção `Rádio 1 (01)` … `Rádio 99 (99)` no wizard e na página Protocolos; o perfil DMR preserva o alias escolhido.
- O helper DMR fisicamente aprovado da linha 0.2.9/0.3.5 **não foi reescrito**: o teste determinístico comprovou `7240000 + 01 → 724000001` e `7240000 + 02 → 724000002`, mantendo `Id=7240000` no MMDVMHost.
- Backend rejeita alias fora de `01..99` antes do apply.
- BrandMeister API Key ganhou endpoint dedicado `/api/brandmeister/api-key`, armazenamento privado `0600` e resposta somente configurada/não configurada. O handler não executa `systemctl` nem reinicia MMDVMHost/DMRGateway.
- Hotspot Security permanece separada e obrigatória para a conexão BrandMeister.
- Evidência VPS em `6c95904614064340d97917e71a361af8cc2d7d4c`: Go compile PASS, Python/JS/Bash PASS e **12/12 testes determinísticos PASS**.
- Ainda não é HW PASS: Rádio 1/2 e API devem ser retestados no Raspberry Pi/MMDVM após a imagem ARM64 publicada.

## Novo bloqueador HW — APRS mensagens — 2026-09-20

- Teste físico reportado pelo usuário: **APRS não enviou e não recebeu mensagens**.
- Classificação atual: **APRS-004 = HW FAIL**.
- A 0.3.6-alpha deve incorporar a correção antes da próxima imagem.
- O estado `Mensagem enfileirada` não será tratado como envio concluído.
- O cliente APRS deve validar `logresp verified`, preservar a fila em falha, receber mensagens/ACKs e mostrar diagnóstico observável.
- Ponto de retorno criado antes da correção: `backup/0.3.6-pre-aprs-msgfix-20260920` no commit `769de1a2dcadf26fdb0af48457a83b94d90a7128`.
- Mesmo após SW/VPS PASS, APRS continua **HW PENDENTE** até novo teste real de envio e recebimento.

## Build/publicação final da 0.3.6-alpha — 2026-09-20

- GitHub Actions run `35531259706`: **PASS**.
- Source validation: **PASS**.
- Overlay completo/staged source: **PASS**.
- Bundle de atualização verificado: **PASS**.
- Build ARM64: **PASS**.
- XZ + SHA-256: **PASS**.
- Validação estrutural da imagem: **PASS**.
- Publicação da prerelease: **PASS**.
- Release: `v0.3.6-alpha`.
- Target commit da release: `0967a020eefc0f997211b46d97d3cc3d5600b5db`.
- Imagem: `PU2PNY-OS-0.3.6-alpha-arm64.img.xz`.
- SHA-256 da imagem: `ec1f2676fa2a21715d5da99dc43a25607e8a7433b4580b9122416063e99eaa82`.
- Tamanho comprimido: `579089116` bytes.
- Bundle in-place: `PU2PNY-OS-0.3.6-alpha-update.tar.gz`, SHA-256 `7dfad819d3fb36d00dd46dce4ee473214059ed7454b2396059740de7720b1bb5`.
- APRS: 6 testes determinísticos PASS; VPS resolveu `soam.aprs2.net` e recebeu greeting do servidor na porta 14580. Isso é evidência VPS de transporte, **não** substitui envio/recebimento HW real.
- A imagem está liberada como **Alpha para teste físico**. DMR da 0.3.5 continua baseline; D-Star/YSF/Wi-Fi/APRS/perfis/displays/update permanecem HW pendente até confirmação no Raspberry Pi/MMDVM.

## Checkpoint 0.3.6 hwfix2 — 20/09/2026

Estado antes do CI final:

- DMR: baseline preservada; nenhuma alteração no helper DMR fisicamente aprovado.
- YSF: baseline preservada; nenhuma alteração funcional no gateway já validado pelo usuário.
- D-Star: correção implementada para o schema do binário `612f388`; **SW pendente do workflow final e HW pendente de novo teste RF/rede**.
- Wi-Fi/AP: handoff sem reboot obrigatório, busca dos dois perfis e DNS efetivo corrigidos; **SW pendente do workflow e HW pendente de novo teste de primeiro boot/handoff**.
- APRS: motor bidirecional existente preservado; interface recebeu teste/ajuda, fallback correto de geolocalização e resposta por clique; **SW pendente e HW/APRS-IS real pendente**.
- P25: configuração estática coberta por teste determinístico; **sem HW**.
- Display: layout TX/RX e telas compactas ajustados sem sobrescrever HMI; foto dinâmica Nextion permanece condicionada a HMI compatível.
- Update: download e instalação separados; instalação fica bloqueada até download 100% + SHA-256.
- Release completa: **NÃO declarada PROD** até ARM64/estrutura/SHA concluírem e as pendências HW críticas forem repetidas no equipamento.

## Escopo adicional — displays genéricos e Raspberry Pi 32-bit — 2026-09-20

- DISPLAY-012 passa a exigir Standby/TX/RX em OLED/LCD e demais drivers genéricos suportados, com ativação pelo painel/auto-detecção segura e sem terminal.
- O Display Core atual já possui renderers para SSD1306/SH1106 e HD44780/PCF8574; isso é evidência de código, não HW PASS.
- ARCH-004/REL-007 abrem uma linha ARM32 armhf paralela, sem substituir ARM64. O artefato será .img.xz, adequado a cartão SD Raspberry Pi, e terá pipeline/gates próprios.
- Base primária: Raspberry Pi OS Legacy Lite Bookworm 32-bit de 15/09/2026, alinhada à base Bookworm efetivamente fixada pela cadeia completa do builder ARM64 e oficialmente compatível com Zero/Zero W, 1A+/1B+, 2B e modelos posteriores listados. Trixie 32-bit fica fora deste primeiro ciclo para reduzir variáveis.
- Target próprio Go proposto: GOARCH=arm GOARM=6; binários C/C++ serão reconstruídos para armhf.
- Pi Zero/1 possuem recursos muito menores; PERF-003 exige modo enxuto e prioridade absoluta para RF/rede.
- Estado atual ARM32: DOC/planejado, sem build e sem HW PASS.

## Evidência ARM32 experimental — 2026-09-20

- GitHub Actions experimental run `35545030803`: build Bookworm `armhf` completo PASS.
- Imagem `.img.xz`: integridade, checksum e validador estrutural 0.3.6 PASS.
- Rootfs reportou arquitetura `armhf` e executou nativamente no runner ARM64, sem QEMU.
- `2pnyd`, `MMDVM-Host`, `DMRGateway`, `dstargateway`, `YSFGateway`, `P25Gateway`, `NXDNGateway` e `DAPNETGateway`: todos confirmados como ELF 32-bit ARM EABI5.
- Artefato CI `pu2pny-os-0.3.6-arm32-experimental`, ID `10615957423`, ZIP digest `sha256:dc80891b18ae59e3002bfb4e492c3b9283037401e9523581d794a76a517586a7`.
- Classificação: **SW/estrutural PASS; HW PENDENTE**. Pode ser usado somente como EXPERIMENTAL/HW-TEST até boot/RF em Raspberry Pi antigo.

## Evidência ARM64 hwfix2 — 2026-09-20

- GitHub Actions run `35544963950`: source, overlay, staged source, bundle, build ARM64, XZ/SHA, validação estrutural e publicação PASS.
- Prerelease `v0.3.6-alpha` atualizada no commit `4ffbce890e839f51e6977836cf0b647fb3fe348e`.
- Imagem ARM64 SHA-256: `8460357f780577abdd12cb5cf91288aad48d27d4c130a96c97d737f8d050a50c`.
- Continua Alpha/SW para as correções deste ciclo; os gates HW continuam obrigatórios.

## Abertura 0.3.7-alpha — Direct/P2P + Display Moderno V2 + voz — 2026-09-20

- Backup de retorno: `backup/0.3.6-pre-direct-display-20260920`.
- Branch: `pu2pny-os-0.3.7-alpha`.
- REL-008 congela toda a funcionalidade/correção da 0.3.6 como baseline.
- P2P-002..006 tornam PU2PNY Direct obrigatório nesta linha: chamada por indicativo/agenda, mesmo protocolo na fase 1, Direct→Relay sob CGNAT, identidade criptográfica e infraestrutura própria.
- DISPLAY-013 exige renderer Moderno V2 gráfico onde o hardware permite; nenhum HMI/TFT é sobrescrito automaticamente.
- PROTO-013 exige aviso de conexão por voz somente após confirmação real do gateway, sem derrubar RF em caso de falha.
- D-Star: schema `v20260323-612f388` já está corrigido em SW, mas RF↔rede ainda precisa novo HW PASS.
- Estado inicial: implementação 0.3.7 em andamento. Não há autorização para chamar Direct/D-Star/YSF/display de HW PASS sem teste físico.

## Requisito novo registrado — 2026-09-20

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| DISPLAY-014 — tela genérica touch 7" | PENDENTE | DOC/HW | requisito registrado; suporte físico ainda precisa implementação/validação no modelo real |
| TEST-DISPLAY-014A..014D | PENDENTE | HW | vídeo, touch, estados runtime e falha isolada precisam teste em Raspberry + tela real |

## Feedback físico 0.3.7-alpha — Nextion

- **DISPLAY-001/002/013: HW FAIL observado.**
- Durante o teste normal, antes de o usuário abrir o menu Display, a Nextion permaneceu travada em `Pronto` e não avançou para o estado operacional/runtime.
- Isso prova uma falha do fluxo automático de inicialização/atualização do display; não deve ser atribuída a configuração manual do menu Display.
- Causa raiz ainda não determinada. Não alterar HMI/TFT automaticamente e não tocar no caminho RF para diagnosticar este defeito.
- Novo caso: `TEST-HW-037-NEXTION-READY`.

## Feedback físico 0.3.7-alpha — DNS/UI

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| UI-013 / NET-016 | FALHA | HW/browser | troca de DNS mostrou feedback de aplicação, mas "DNS efetivo" e diagnóstico não atualizaram sozinhos; exigiu refresh manual, em uma tentativa duas vezes |

## Feedback físico 0.3.7-alpha — Wi-Fi 1/2

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| NET-018 / UI-014 | FALHA | HW/browser | Wi-Fi 1 não mostrou claramente estado salvo/conectado; Wi-Fi 2 tentou conectar ao usar "Salvar"; sem Mostrar/Ocultar senha; erro bruto em inglês; troca/configuração ainda instáveis |
| NET-017/018 | FALHA | HW | handoff deve ser rápido e transacional, mas ainda não há confirmação confiável de associação/IP nos dois perfis |

## Função adicionada ao escopo 0.3.7-alpha — canais Wi-Fi

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| NET-019 — gráfico e recomendação de canal Wi-Fi | PENDENTE | DOC | requisito registrado; implementação/validação ainda necessárias |
| TEST-NET-019A..019E | PENDENTE | SW/HW | gráfico 2,4/5 GHz, canal ativo, recomendação explicável e scan leve precisam passar pelos testes |

## Função adicionada ao escopo 0.3.7-alpha — perfis rápidos

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| LIVE-011 / PROTO-014 | PENDENTE | DOC | Ao Vivo deve trocar perfis rapidamente; Hotspot deve configurar perfis; filtros de atividade permanecem separados |
| TEST-LIVE-011A..D / TEST-PROTO-014A..B | PENDENTE | SW/HW | implementação e validação ainda necessárias |

## Feedback físico 0.3.7-alpha — Direct

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| P2P-007 | FALHA/PENDENTE | HW/browser | chamada sem peer pareado exibiu `HTTP 409`; fluxo precisa pré-condição e mensagens operacionais em português |
| UI-015 | FALHA | HW/browser | página Direct abriu com layout/cabeçalho/menu quebrados |
| P2P-006B | PENDENTE | HW | ainda não existe segundo hotspot 0.3.7 para validar RF A↔B; não classificar Direct/Relay como HW PASS |

## Feedback físico 0.3.7-alpha — APRS/D-PRS

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| APRS-006 — assistente de login APRS-IS | FALHA | HW/browser | teste exibiu erro de login não confirmado sem explicar o que é o login ou indicar a etapa exata que falhou |
| APRS-002 — toast global 5 s | PENDENTE/NÃO IMPLEMENTADO GLOBALMENTE | DOC/SW/HW | código atual avisa dentro da página APRS; falta toast global clicável em qualquer página |
| APRS-004 transporte bidirecional | HW PENDENTE | SW/VPS/HW | não promover a HW PASS até login verificado + envio + recebimento reais |

| APRS-007 — D-PRS | PENDENTE | DOC/HW | código atual ainda indica `Sem DPRS`; funcionalidade precisa implementação e teste físico D-Star/GPS antes de qualquer HW PASS |

## Função adicionada ao escopo 0.3.7-alpha — Histórico/Ao Vivo enriquecidos

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| LIVE-012 / DATA-001 | PARCIAL/PENDENTE | DOC/SW/HW | UI atual já mostra parte da identidade/direção/módulo/TG/QRZ-RID; falta padronizar e ampliar servidor/rede, contexto Internet, contagem/tempo acumulado e origem lógica sem dados inventados |
| TEST-LIVE-012A..F | PENDENTE | SW/HW | precisam implementação completa e validação com eventos RF e Internet reais |

## Feedback físico 0.3.7-alpha — Sistema

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| UI-016 — fuso horário pelo painel | FALHA | HW/browser | alteração de timezone bloqueada por `Access denied`; usuário não consegue ajustar pelo painel |
| UI-006 / UI-016 | BLOQUEADOR DE UX | HW | hora/fuso precisam permanecer coerentes e ajustáveis sem terminal; correção deve preservar RF/gateways |

## Feedback físico 0.3.7-alpha — cabeçalho

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| UI-017 — cabeçalho global | FALHA | HW/browser + DOC | Sistema apresenta cabeçalho mais alto e relógio esmagado; código confirma ausência de inicialização do relógio nessa página e flex sem proteção suficiente contra quebra |

## Feedback físico 0.3.7-alpha — Expert

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| UI-018 — Expert realtime | FALHA/PARCIAL | HW/browser + DOC | Estado Ao Vivo usa polling de 15 s; precisa reutilizar SSE do Ao Vivo e ganhar dashboard/gráficos leves |
| UI-019 — Resumo operacional | PENDENTE | DOC | substituir "Configuração pública" por resumo técnico seguro e mais completo |
| SEC-021 — SSH assistido | FALHA UX / HW PENDENTE | HW/browser | chave inválida foi rejeitada corretamente, mas fluxo não ensina/prevalida; ssh.service ainda não foi validado com chave pública válida |

## Função adicionada ao escopo 0.3.7-alpha — BER / calibração RF

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| RF-013 — autoajuste BER/RXOffset | PENDENTE | DOC/HW | requisito registrado; ainda não implementado/validado em hardware |
| RF-014 — proteção TXOffset | PENDENTE | DOC/HW | TXOffset não será alterado automaticamente sem feedback confiável do receptor |
| UI-020 — Calibração RF no Expert | PENDENTE | DOC/SW/HW | gráfico BER, autoajuste RX, manual RX/TX, rollback e toast de falha precisam implementação e teste |

## Função adicionada ao escopo 0.3.7-alpha — Ao Vivo / saúde da comunicação

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| LIVE-013 — RF/Wi-Fi/Internet | PENDENTE | DOC/SW/HW | SSE e RSSI/BER já existem parcialmente; falta S-meter seguro, sinal do Wi-Fi ativo e indicadores integrados |
| LIVE-014 — RX/TX contextual | PENDENTE | DOC/SW/HW | conteúdo deve adaptar-se à direção real sem inventar RSSI/BER de tráfego vindo da Internet |
| UI-021 — sugestões acionáveis | PENDENTE | DOC/SW/HW | atalhos contextuais para BER, Wi-Fi, Internet e protocolo precisam implementação/validação |

## Feedback/escopo 0.3.7-alpha — potência RF e idiomas

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| RF-015 / UI-022 — potência MMDVM | PENDENTE | DOC/SW/HW | RFLevel é suportado por MMDVMHost/MMDVM_HS compatível, mas PU2PNY ainda não possui controle seguro implementado/validado |
| UI-023 — PT/EN/ES integral | FALHA | HW/browser + DOC | teste em English mostrou mistura de idiomas; mecanismo atual deixa texto original quando não encontra tradução |
| TEST-UI-023-CI | PENDENTE | SW | falta gate automático que impeça release com chaves/textos sem tradução completa |

## Feedback físico 0.3.7-alpha — boot/religamento, Wi-Fi e Nextion

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| BOOT-001 — restauração operacional após boot | **FALHA / BLOQUEADOR** | HW | após retorno da alimentação MMDVMHost/gateway não restauraram automaticamente o último perfil; usuário precisou entrar em Protocolos e ativar o perfil |
| BOOT-001 — Ligar operacional | **FALHA UX/FUNCIONAL** | HW/browser | botão não produziu mudança confirmada; backend atual descarta erros de `systemctl start` e responde sucesso genérico |
| NET-020 — Wi-Fi pós-boot/estado real | **FALHA DE ESTADO UI** | HW/browser | Internet/rota estavam em `wlan0`, mas SSID e RSSI apareceram vazios; não há evidência suficiente para classificar o Wi-Fi como desconectado |
| DISPLAY-015 — estados transitórios | **FALHA** | HW | Nextion ficou presa em `Iniciando` após boot e em `Manutenção` após execução manual |
| Gate de release | **BLOQUEADO até nova correção SW + novo teste HW** | REL | 0.3.8 não pode ser tratada como pronta para novo ciclo enquanto boot operacional e display transitório não estiverem corrigidos no código/build |

## Build/publicação 0.3.8-alpha — 2026-09-21

- GitHub Actions run `35560842909`: **PASS**.
- Source validation: **PASS**.
- Staged source/regressões: **PASS**.
- Build ARM64: **PASS**.
- Normalização XZ + SHA-256: **PASS**.
- Validação estrutural final: **PASS**.
- Publicação da prerelease `v0.3.8-alpha`: **PASS**.
- Target commit: `3876e50df5f02bea3a1f761c464db5797ab29742`.
- Imagem: `PU2PNY-OS-0.3.8-alpha-arm64.img.xz`.
- Tamanho: `591931160` bytes.
- SHA-256 da imagem: `1997b05612159e0d1178e6ab0ab2dc73f1404a8f2a9e7e909e00dfb126557510`.

**Classificação:** liberada como **Alpha para teste físico**. As correções BOOT-001, NET-020 e DISPLAY-015 estão em SW/estrutura PASS, mas continuam **HW PENDENTE** até repetição no Raspberry Pi + MMDVM + Nextion. D-Star, YSF bidirecional, APRS/D-PRS, Direct entre dois hotspots e demais pendências físicas não são promovidos a HW PASS por este build.

## Estado corrente 0.3.9-alpha — 2026-09-21

**Estado global:** ALPHA / correção. **Não PROD.**

### Baseline preservada
- AP→Wi-Fi da 0.3.8: HW PASS no cenário testado.
- Wi-Fi reconectou após reboot.
- DMR TX/RX anterior: baseline HW obrigatória.
- Histórico: aprovado pelo usuário e congelado para regressão.
- Direct: layout aprovado; P2P entre dois hotspots ainda HW PENDENTE.
- APRS-IS: login verificado observado; mensagens/D-PRS continuam HW PENDENTE.

### Bloqueadores que a 0.3.9 corrige em software
- BOOT-001 restauração do último perfil.
- PROTO-002/007/012 D-Star falso negativo UDP 20010.
- PROTO-003/008 YSF falso negativo UDP 4200.
- DISPLAY-001/013/015 estados/layout Nextion.
- NET-012/017/018/019/020 captive portal, scan, gráfico e coerência do estado.
- UI-013 DNS efetivo.
- UI-018 Expert SSE em tempo real.
- UI-016 timezone.
- SEC-021 SSH.
- UI-023 tradução.
- LIVE-013/014 e PROTO-014 hierarquia visual/configuração.

### Gate atual
Fontes corretivas estão em `pu2pny-os-0.3.9-alpha`. Build ARM64, XZ, SHA-256, validação estrutural e publicação ainda devem concluir antes de existir imagem 0.3.9 para teste. Nenhum FAIL HW acima é promovido por CI.

## Build 0.3.9-alpha publicado — 2026-09-21

**Estado do artefato:** SW PASS / ALPHA para teste físico. **Não PROD.**

- GitHub Actions run: `35569995279`.
- Commit da release: `0b35a555a642ced6e13150e434072415e24175b5`.
- Source gate: PASS.
- Staged source: PASS.
- Build ARM64: PASS.
- XZ: PASS.
- SHA-256: PASS.
- Validação estrutural final da imagem montada: PASS.
- Publicação: prerelease `v0.3.9-alpha`.
- Artefato: `PU2PNY-OS-0.3.9-alpha-arm64.img.xz`.
- SHA-256: `09ea47002f60471e3359186717370861e0090bf03c5f5fb3e2dc32456261ec71`.

Os casos BOOT/D-Star/YSF/Nextion/rede/UI que dependem de Raspberry Pi + MMDVM/display real continuam PENDENTE/FAIL anterior até novo teste HW. O CI não os promove para HW PASS.


## Feedback físico 0.3.9-alpha — primeiro acesso AP — 2026-09-21

- **NET-021 / TEST-NET-021A: HW FAIL:** ao conectar ao AP `pu2pny`, a página de configuração não abriu automaticamente.
- **Baseline congelada como HW PASS após abertura manual:** ao abrir `http://pu2pny.local/`, o sistema localizou automaticamente a rede Wi-Fi, aceitou senha e salvou, mostrou a mensagem de conexão, após o handoff a página abriu sozinha, reconheceu o hardware automaticamente e avançou para a página de configurações.
- Escopo da correção: somente captive portal do primeiro acesso. Não modificar scan Wi-Fi, handoff, retorno da página, detecção de hardware, RF/DMR ou navegação posterior que foram aprovados neste teste.
- Ponto de retorno criado antes da correção: `backup/0.3.9-pre-captive-fix-20260921`.
- A correção deve remover a dependência de DHCP Option 114 com URL HTTP local e impedir Internet transparente no AP enquanto o sistema ainda estiver não provisionado.

## Feedback físico 0.3.9 — D-Star / Hotspot — 2026-09-21

- **D-Star: HW FAIL no apply atual.** RF foi validada; DStarGateway carregou a lista D-Plus e registrou o indicativo no auth.dstargateway.org, porém o helper declarou ausência da bridge UDP local 20010 e executou rollback.
- Inspeção do código identificou defeito determinístico no validador `udp_listener()`: em `ss -H -lun`, o helper consultava `cols[4]` (peer/remoto) em vez de `cols[3]` (endereço local). Isso pode produzir falso negativo para D-Star/20010 e YSF/4200.
- As portas/configuração não serão trocadas por tentativa; a correção é limitada ao detector, mantendo rollback e DMR baseline.
- **UI:** Hotspot/Protocolos via iframe foi rejeitada no teste visual. A decisão é manter a página unificada conforme PROTO-014, porém reconstruí-la nativamente sob UI-024, usando Direct como referência visual.
- **Baseline congelada:** página Direct aprovada visualmente; Histórico aprovado e não deve ser modificado.
- **UX:** ao clicar Salvar e continuar no D-Star, o aviso visual de salvando/carregando não apareceu como esperado. UI-008/TEST-UI-024C passa a cobrir esse fluxo.
- Ponto de retorno antes desta intervenção: `backup/0.3.9-pre-dstar-hotspot-ui-20260921`.

## Feedback físico 0.3.9 — Nextion e relógio — 2026-09-21

- **DISPLAY-016 / HW FAIL atual:** marcar "Usar Nextion pela MMDVM" não produziu mudança visível; a Nextion não mostrou o conjunto de informações solicitado.
- A 0.3.9 atual desliga o PU2PNY Display Core para qualquer Nextion pela MMDVM e força fallback nativo ON7LDS quando "Moderno V2" é escolhido. Isso explica por que o renderer próprio não aparece.
- A correção passa a separar renderer próprio e renderer nativo, com exclusão mútua para evitar disputa de writer.
- O painel atual possui apenas três opções de layout e não separa isso do modelo físico. DISPLAY-016 adiciona perfis de tamanho/resolução documentados para a família Nextion, mantendo HW PENDENTE por modelo.
- **UI-017 continua HW FAIL:** o relógio visual continua sem a correção esperada. A nova implementação deve usar horário/fuso retornado pelo backend e layout de cabeçalho estável.
- **D-Star:** além do parser local UDP, PROTO-015 acrescenta confirmação explícita do MMDVM-Host.ini e espera limitada de readiness após subir MMDVMHost → DStarGateway.
- Ponto de retorno adicional: `backup/0.3.9-pre-nextion-clock-20260921`.

## DISPLAY-017 — Auto-detection/provisioning
- Novo requisito registrado após feedback físico da 0.3.9.
- Implementação inicial deve ser isolada da detecção de hardware já existente para reduzir regressão.
- Primeira etapa: arquitetura + detector não destrutivo Nextion/OLED + catálogo local + bootstrap/path/hotplug.
- Gravação automática de TFT **não é permitida**. Flash futuro exigirá asset real, SHA-256 e confirmação explícita.
- Estado desta frente: DOC / SW-syntax em desenvolvimento; HW PENDENTE.

## Prioridades de hardening registradas — 2026-09-21
Ordem de execução aprovada neste ciclo:
1. Display Auto-Detection/Auto-Provisioning + regressão Nextion;
2. PROTO-016 wait-for-bridge D-Star/YSF;
3. BOOT-002 restore transacional;
4. PROTO-017 MQTT preflight;
5. NET-022 máquina de estados Wi-Fi;
6. UPDATE-006, LIVE-015, SEC-022, UI-025 e i18n dinâmico.

Nenhum item novo é HW PASS neste momento. Direct e Histórico permanecem baseline aprovada e não entram em refatoração desnecessária.

## 0.3.10-alpha — ciclo de imagem aberto — 2026-09-21

- Branch ativa: `pu2pny-os-0.3.10-alpha`.
- Base: estado corretivo acumulado da `pu2pny-os-0.3.9-alpha`.
- Rollback da abertura: `backup/0.3.9-pre-0.3.10-image-20260921`.
- Objetivo: consolidar na imagem as correções já registradas de captive inicial, D-Star/YSF, Hotspot sem iframe, wizard, Nextion/Display, relógio, restore/MQTT, Wi-Fi por estados e diagnóstico Expert.
- Histórico e Direct permanecem baselines preservadas.
- Estado atual: implementação em fonte; CI/ARM64/SHA/validação final ainda PENDENTES. Não divulgar link de imagem até esses gates passarem.

## 0.3.10-alpha publicada — 2026-09-21

- Run final: `35600972295`.
- Commit validado/publicado: `ad3e09f8c29d85abfb891e7c5e4f05423df4fd9c`.
- Release: `v0.3.10-alpha`.
- Artefato: `PU2PNY-OS-0.3.10-alpha-arm64.img.xz`.
- SHA-256: `9bbbffe310401dbe4dffe10316a11fc8647465112070592275a45bee3d0c23ee`.
- Source, overlays, staged source, ARM64, XZ, checksum, validação final, transferência e publicação: **SW PASS**.
- Estado da release: **Alpha / HW-TEST**. D-Star, YSF, Nextion, captive popup e restore continuam pendentes de novo teste físico.

## 2026-09-21 — ciclo corretivo 0.3.11-alpha aberto após teste HW da 0.3.10
- Teste físico da 0.3.10 confirmou que a MMDVM foi identificada em `/dev/ttyAMA0` com baud detectado, porém o fluxo exibiu `MMDVMHost failed with detected baud 115200; rolling back` e não avançou como esperado.
- A mensagem era genérica: o aplicador atribuía qualquer falha de inicialização do MMDVMHost ao baud detectado, sem provar que o baud era a causa.
- A etapa Hardware também podia manter uma mensagem de erro transitória mesmo depois de a MMDVM já estar confirmada.
- Foi confirmada mistura de idioma: mensagem técnica em inglês apareceu com a interface selecionada em português.
- Rollback criado: `backup/0.3.10-hw-feedback-20260921`.
- Branch corretiva: `pu2pny-os-0.3.11-alpha`.
- Implementação em fonte: HW-003, RF-016, WIZ-006 e UI-026.
- Estado atual: **DOC/SW em preparação; HW PENDENTE**. DMR/RF funcional anterior continua baseline obrigatória de regressão.
- A 0.3.11 só poderá ser divulgada como imagem de teste após build ARM64, XZ, SHA-256 e validação estrutural completos. Nenhuma correção acima é HW PASS antes de novo teste físico.

## 0.3.11-alpha — feedback físico e abertura da 0.3.12 — 2026-09-21

- **HW FAIL:** após a configuração básica, MMDVMHost ainda não iniciou e o rollback preservou a configuração anterior; o wizard não pôde concluir porque /api/rf não chegou a applied.
- O erro não será atribuído ao baud sem evidência. O baud detectado continua obrigatório.
- Revisão do código mostrou duas lacunas objetivas: o preflight MQTT 0.3.11 provava somente abertura TCP, não CONNECT/CONNACK; e o validador da imagem não provava a presença do executável do broker Mosquitto.
- A detecção MMDVM também não compartilhava o mesmo lock de UART usado pela transição RF.
- Rollback criado: backup/0.3.11-pre-0.3.12-fix-20260921.
- Branch corretiva: pu2pny-os-0.3.12-alpha.
- Escopo congelado: não alterar frequências, offsets, DMRGateway, Direct, Histórico ou o fluxo AP→Wi-Fi já aprovado.
- Estado da 0.3.12 neste ponto: DOC/SW em implementação; build ARM64 e HW ainda PENDENTES.
## 0.3.12-alpha — publicação e primeiro lote de feedback físico — 2026-09-21

- Run de publicação: `35620934999`.
- Commit publicado: `567c8b4014540aa9e84fb184ab883ff09af65fed`.
- Release: `v0.3.12-alpha`.
- Artefato ARM64: `PU2PNY-OS-0.3.12-alpha-arm64.img.xz`.
- SHA-256 do artefato publicado: `944bc588e74be10261105da90de77025a4dd20fed9cea7f7503f18981279962e`.
- Source, build ARM64, XZ, checksum, validação estrutural e publicação: **SW PASS**.
- Estado permanece **Alpha / HW-TEST**.

### Resultado HW recebido
- **NET/WIZ — HW PASS e baseline congelada:** reconhecimento do Wi-Fi, conexão automática e abertura direta do painel funcionaram na 0.3.12. Não alterar esse fluxo em correções de RF/TGIF/i18n.
- **RF/WIZ — HW FAIL:** a etapa de configuração MMDVM continua gerando erro e bloqueando o avanço do wizard. O relato reafirma que a estrutura equivalente funcionava nas versões anteriores, com referência explícita à 0.3.6 e funcionamento até 0.3.8.
- **UI/i18n — HW FAIL:** foi observada mistura de Português e Inglês na mesma interface apesar de Português estar selecionado.
- **DMR/TGIF — HW FAIL reportado / causa ainda não isolada:** a Security Key foi informada, porém o hotspot não confirmou login na TGIF. A MMDVM recebe o RF do HT, mas isso não constitui prova de entrega à rede; painel/TGIF não refletiram a atividade.
- A revisão de código confirma que a chave TGIF chega ao campo `Password=` do DMRGateway; portanto não há evidência para classificar a chave copiada como causa.
- A revisão também confirma diferença estrutural relevante: a 0.3.6 provava primeiro MMDVMHost com `MQTTLevel=0`, `DisplayLevel=0` e redes desativadas; a 0.3.12 tornou MQTT parte da primeira ativação. Isso é uma regressão arquitetural plausível a eliminar por RF-018, sem afirmar ainda que seja a única causa física.
- O helper DMR atual trata TGIF pelo perfil DMR genérico. A autenticação/roteamento TGIF será isolada sob PROTO-019 somente depois que o bootstrap RF passar, preservando o helper DMR anteriormente aprovado fora do escopo TGIF.
- Branch de registro/diagnóstico deste lote: `test/0.3.12-hw-findings-20260921`.

## 0.3.13-alpha — implementação corretiva aberta — 2026-09-21

- Branch: `pu2pny-os-0.3.13-alpha`.
- Rollback: `backup/0.3.12-pre-0.3.13-20260921`.
- **Baseline congelada:** reconhecimento do Wi-Fi, conexão automática e abertura direta do painel, todos com HW PASS na 0.3.12. Nenhum helper Wi-Fi foi substituído pelo overlay 0.3.13.
- **RF-018 implementado em fonte:** MMDVMHost passa primeiro por bootstrap mínimo com `MQTTLevel=0` e `DisplayLevel=0`; só após confirmar a UART o sistema valida MQTT por CONNECT/CONNACK, habilita MQTT/display e reinicia o host de forma transacional.
- Revisão encontrou um defeito concreto capaz de bloquear a 0.3.12: `ExecStartPre` era executado como usuário `mmdvm` e o preflight tentava persistir diagnóstico em `/run/2pny`. A 0.3.13 usa preflight não persistente no service e a persistência root continua disponível no apply. Isso ainda exige novo HW para provar que era a causa do bloqueio físico.
- **PROTO-019 implementado em fonte:** TGIF usa perfil explícito compatível com o DMRGateway embarcado, preserva a Security Key, distingue `secured`/legado e não grava a chave no estado público.
- **UI-028 implementado no wizard:** rótulos operacionais têm base PT consistente e catálogo exato PT/EN/ES; conteúdo normal fica oculto brevemente até o idioma selecionado ser aplicado, mantendo a tela inicial de idioma como única superfície intencionalmente multilíngue.
- Direct, Histórico, frequências, offsets e caminhos DMR não-TGIF permanecem preservados.
- Estado atual: **fonte implementada; CI/ARM64/XZ/SHA/validação final PENDENTES; HW PENDENTE**.

## Identidade visual — próximo ciclo após 0.3.13
- O mantenedor aprovou em 2026-09-21 um logotipo oficial para uso nas próximas versões do PU2PNY-OS.
- Requisito registrado como **UI-029**.
- A 0.3.13-alpha em build não será alterada por esta decisão, evitando mudança fora do escopo corretivo MMDVM/TGIF/i18n.
- A integração visual entra no próximo ciclo, com asset otimizado e testes de legibilidade/desempenho.

## 0.3.13-alpha — publicada para teste físico — 2026-09-21

- Run final: `35631645881`.
- Commit construído/publicado: `f00aba3d556ab6ee0bb48ba79ea5a591ace11d81`.
- Release: `v0.3.13-alpha`.
- Artefato: `PU2PNY-OS-0.3.13-alpha-arm64.img.xz`.
- SHA-256 da imagem: `1cb0f862c09825b25394cf0cfbb6812d7e24c04a5034cab9940bc90763db67ec`.
- Source/regressões, overlay herdado, staged source, build ARM64, XZ/checksum, validador estrutural, transferência e publicação: **SW PASS**.
- Estado: **Alpha / HW-TEST**.
- Ainda não promover RF-018, PROTO-019 ou UI-028 a HW PASS antes de novo teste físico.

## 0.3.13-alpha — segundo resultado físico e abertura da 0.3.14 — 2026-09-21

- **RF-018 Fase A: HW PASS.** A MMDVM passou no teste básico e MMDVMHost conseguiu assumir a UART com MQTT/display logging desativados.
- **PROTO-018/Fase B MQTT: HW FAIL.** Mensagem observada: `A MMDVM passou no teste básico, mas o broker MQTT local não ficou pronto. A configuração anterior foi restaurada.`
- A falha agora está isolada depois da prova real da MMDVM; não há evidência de problema de baud/UART nesta etapa.
- **WIZ: HW FAIL associado:** após a falha MQTT o fluxo saiu da tela de Configuração Básica, comportamento que deve ser impedido.
- TGIF e demais validações posteriores continuam **PENDENTES**, pois o apply não ultrapassou a Fase B MQTT.
- Rollback criado: `backup/0.3.13-pre-0.3.14-20260921`.
- Branch corretiva: `pu2pny-os-0.3.14-alpha`.
- Escopo: broker MQTT/readiness + permanência do wizard na Configuração Básica. Wi-Fi aprovado e bootstrap MMDVM da 0.3.13 ficam congelados.

## 0.3.14-alpha — feedback HW e abertura da 0.3.15 — 2026-09-21
- **HW PASS preservado:** MMDVM passa no teste básico/UART.
- **HW FAIL:** o primeiro provisionamento continua bloqueado pelo broker MQTT e não chega à Conclusão.
- Comparação GitHub 0.3.6/0.3.8 mostrou que o fluxo funcional encerrava o RF apply logo após MMDVMHost ativo com `MQTTLevel=0`; no DMR, o helper também operava com `MQTTLevel=0` e sem preflight MQTT.
- A 0.3.14 introduziu dois gates que não existiam nesse caminho comprovado: Fase B MQTT dentro do RF apply e preflight MQTT antes de delegar DMR.
- Branch corretiva: `pu2pny-os-0.3.15-alpha`.
- Rollback: `backup/0.3.14-pre-0.3.15-20260921`.
- Escopo congelado: somente remover esses dois bloqueios MQTT do primeiro provisionamento DMR. Demais módulos permanecem inalterados.

## 0.3.15-alpha publicada — 2026-09-21
- GitHub Actions run final: `35647296002` — **success**.
- Commit validado/publicado: `820ae691a49ee49ebc4974b9345b75aa1f875d75`.
- Release: `v0.3.15-alpha` — prerelease / Alpha / HW-TEST.
- Artefato: `PU2PNY-OS-0.3.15-alpha-arm64.img.xz`.
- SHA-256: `4caea4a281c67cd8c5a15ba134e6720dbf4adb7a675a4395052ff13be10bb690`.
- Source, regressões, overlay, staged source, build ARM64, XZ, SHA-256, validação estrutural da imagem, transferência e publicação: **SW PASS**.
- Correção focal: onboarding DMR não é mais bloqueado por MQTT quando MMDVMHost/DMRGateway operam com `MQTTLevel=0`.
- **HW PENDENTE:** confirmar em Raspberry Pi + MMDVM que Configuração Básica avança para Conclusão e dashboard.

## Abertura 0.3.16-alpha — feedback HW pós-0.3.15 — 2026-09-21

**Estado:** implementação corretiva em andamento. Não publicada.

Baseline congelada: todo o restante do sistema foi aprovado pelo mantenedor neste ciclo; somente os bugs listados entram no escopo.

Falhas/ajustes observados:
- Sistema: fuso America/Sao_Paulo não aplica; **HW FAIL**.
- SSH: fluxo não habilitou; chave pública vazia é rejeitada corretamente, mas o request/helper e UX precisam ser determinísticos; **HW FAIL de operação**.
- Ao Vivo: não mostrar sinal RF sem RF real.
- Wi-Fi: perfil salvo não reconectou após retorno/reboot; Ethernet demorou a refletir; Wi-Fi 1/2 sem scan utilizável; **HW FAIL**.
- Hotspot/Protocolos: overlay termina antes da confirmação remota.
- Voz DMR: anúncio do sistema mistura com tráfego NETWORK→RF.
- Direct para PU2UJY/0.3.14: **HW FAIL**, causa a isolar sem enfraquecer identidade.
- APRS-IS: TCP para soam.aprs2.net:14580 falhou; mensagem ficou waiting_ack; conexão automática/fallback pendentes.
- Nextion: nenhuma opção ativou a tela; regressão frente à 0.3.8 que já enviava informação; **HW FAIL**.
- D-Star: ainda não conecta; gerador atual diverge do schema do gateway embarcado em pontos concretos.
- Rollback: `backup/0.3.15-pre-0.3.16-20260921`.
- Branch: `pu2pny-os-0.3.16-alpha`.


## Publicação 0.3.16-alpha — 2026-09-22

- Commit da imagem publicada: `1c5ec75548374ac13be6948fc86eae46bd9eeddf`.
- GitHub Actions run final: `35669972163` — source **PASS**, staged source **PASS**, build ARM64 **PASS**, XZ/SHA-256 **PASS**, imagem montada/validação estrutural **PASS**, publicação **PASS**.
- Release: `v0.3.16-alpha` — prerelease / Alpha / HW-TEST.
- Artefato: `PU2PNY-OS-0.3.16-alpha-arm64.img.xz` — 614130916 bytes.
- SHA-256 da imagem: `8329b976c733054787052484974fc86663e337bfdce4b31e461361fbfa465426`.
- Escopo SW validado: NET-023/024, LIVE-016, UI-030, PROTO-022, P2P-006, APRS-012, DISPLAY-018, SEC-023/UI-031 e PROTO-023 em seus gates determinísticos/estruturais.
- D-Star atual: identidade local `Band=C`, independente do módulo remoto; `ReloadTimer` e `DStar_Hosts.json` customizado conforme o gateway embarcado.
- Nextion via modem: caminho nativo MMDVMHost/`Port=modem` restaurado no código e na imagem.
- **HW PENDENTE:** nenhuma das correções 0.3.16 é promovida a HW PASS até reteste em Raspberry Pi + MMDVM + Nextion/rede real. DMR TX/RX permanece baseline obrigatória de regressão.

## Abertura 0.3.17-alpha — feedback HW da 0.3.16 — 2026-09-21

**Estado:** correção focal em andamento. Não publicada.

### Baseline congelada
O mantenedor aprovou como ótimo/perfeito todo o restante da 0.3.16 que não foi citado neste feedback. Esses componentes não entram no escopo da 0.3.17.

### Defeitos observados
- **D-Star rede/conexão:** DStarGateway conecta e recebe da rede — **HW PASS parcial**.
- **D-Star rede→RF:** Hotspot não mostra a recepção e a MMDVM não transmite o tráfego recebido da rede — **HW FAIL**.
- **Comandos D-Star via rádio/DR:** precisam funcionar `I`, `E`, `U`, link do default e link/troca de módulo/refletor, com voz/status do gateway — **HW PENDENTE/FAIL funcional**.
- **Fuso horário:** continua sem permitir aplicar a zona selecionada — **HW FAIL**.

### Diagnóstico de código antes da correção
- 0.3.16 configurava DStarGateway local como `Band=C`, mas ainda escrevia o **módulo remoto selecionado** em `MMDVMHost [D-Star] Module=`, criando identidade local divergente no loopback.
- 0.3.16 usava `ReflectorReconnect=Fixed`; no DStarGateway embarcado, o handler retorna antes de processar comandos de link/unlink quando reconnect é Fixed.
- O DStarGateway embarcado possui suporte nativo aos comandos URCALL `_______I` e `_______E`, e ao handler de `L/U`; a correção deve habilitar esse caminho, não criar protocolo paralelo.
- Timezone usa helper/path one-shot, mas o teste HW confirma que escrever o request ainda não resulta em mudança aplicada.

### Controle de mudança
- Rollback: `backup/0.3.16-pre-0.3.17-20260921`.
- Branch: `pu2pny-os-0.3.17-alpha`.
- Escopo: PROTO-024, LIVE-017, UI-032, SEC-024 e gates REL-010.

## 0.3.18-alpha — correção pré-reteste — 2026-09-22

- A 0.3.17-alpha foi construída em SW, mas **não será usada como candidata de reteste**: revisão do código upstream mostrou que o pack de voz/status do DStarGateway é instalado em `/usr/local/share/dstargateway.d/`, enquanto o gerador 0.3.17 ainda apontava para `/usr/share/2pny/audio/dstar/`.
- Branch: `pu2pny-os-0.3.18-alpha`.
- Rollback: `backup/0.3.17-pre-0.3.18-20260922`.
- Escopo: somente corrigir `[Paths] Data` e exigir os AMBE/INDX reais na imagem. Todo o restante permanece congelado.
- D-Star já preservado no código 0.3.17: MMDVMHost módulo local C, gateway Band C, 20010/20011, `ReflectorReconnect=Never`, `ReloadTime=72`, comandos nativos I/E/U/L/link e parser NETWORK→RF.
- Timezone já preservado no código 0.3.17: request/result único via PathExistsGlob + helper root restrito a `timedatectl set-timezone`.
- Estado: implementação/CI; HW PENDENTE.

## Adição SEC-025 à 0.3.18-alpha — 2026-09-22

- A tag `v0.3.18-alpha` ainda não estava publicada quando o mantenedor solicitou administração pelo rádio.
- Rollback adicional antes da mudança: `backup/0.3.18-pre-sec025-20260922`.
- Novo requisito: **SEC-025**; controle de escopo: **REL-012**.
- Comandos: `PNYARM`, `PNYOFF`, `PNYRBT`, `PNYDMR`, `PNYDST`, `PNYYSF`, `PNYP25`, `PNYNXD`, `PNYPOC`.
- Segurança: MYCALL1 deve corresponder ao callsign configurado; ação exige armamento one-shot de 30 s; gateway apenas escreve request local; helper root possui allowlist fixa.
- Poweroff é desligamento seguro do Linux. Corte físico da alimentação exige hardware externo.
- D-Star I/E/U/L/link, correção NETWORK→RF, pack de voz e timezone continuam no mesmo ciclo; todo o restante permanece congelado.
- Estado: implementação/CI; HW PENDENTE.


## 0.3.19-alpha — manutenção focal solicitada em 2026-09-22

- Branch: `pu2pny-os-0.3.19-alpha`.
- Rollback: `backup/0.3.18-pre-0.3.19-20260922` no commit `453df760fc75e105abda0f22d1d8d2c18fc40fe4`.
- Base: 0.3.18-alpha integral; componentes não citados permanecem congelados.
- Requisitos: REL-013, NET-025/026, LIVE-018, UI-033/034, PROTO-025/026, APRS-013, DISPLAY-019, SEC-026/027, DATA-002.
- Implementado em fonte:
  - DNS sem `device reapply` incompatível;
  - Wi-Fi 1 atual / Wi-Fi 2 alternativa + canal atual/melhor;
  - Live/Expert ocultam dados transitórios em standby e TOT é regressivo;
  - Protocolos com 6 casas, vírgula/ponto e ajuda por protocolo;
  - APRS toast global de 5 s fora da página APRS;
  - display network-online limitado + splash 0–100 em renderer compatível;
  - timezone drena requests;
  - voz/horário default-on somente sem preferência salva;
  - SSH gera chave no navegador e envia somente pública;
  - Expert possui log de erros sob demanda/download;
  - D-Star mostra módulo remoto somente com confirmação real do gateway e expõe rejeições RF.
- D-Star local continua C e portas 20011/20010; DMR/RF baseline não foi alterada.
- Commits de implementação até o momento: `ccd7b722d7b7a9d7a96c42b831d8d45e2434bb18`, `caa452aff4a18966faf45a0d6fec1b371b9f1653`, `87264ff535b6f7ac87e96855f7604f90e5adf485`, `4cd992d8714438cd4e29b663d91c68a61ff1cacc`.
- Estado atual: **DOC/implementado em fonte; CI iniciado; HW PENDENTE**. Não promover para HW/PROD sem teste físico.


## Ampliação 0.3.19-alpha — YSF/C4FM e duplex — 2026-09-22

- Novo rollback antes de alterar RF/gateways: `backup/0.3.19-pre-ysf-duplex-20260922`, criado no commit `66daecb821b5bb6ded31ed7f1449153ffd4f516b`.
- Requisitos adicionados: **REL-014, RF-019, LIVE-019, PROTO-027 e PROTO-028**.
- Feedback HW atual:
  - YSF/C4FM: serviço local fica ativo, porém o painel permanece em `gateway_active` sem confirmação remota — **HW FAIL de conexão remota**;
  - DMR duplex: RF→rede e rede→RF não estão funcionais; tráfego chega da Internet ao hotspot mas não é retransmitido ao rádio — **HW FAIL**;
  - Ao Vivo em duplex precisa exibir RX e TX separadamente.
- Referência histórica recuperada: o problema YSF foi reportado na 0.3.7 e a cadeia seguinte preservou bridge 3200/4200 e `WiresXCommandPassthrough=0`; isso será usado como referência de implementação, **não** como novo HW PASS.
- Diagnóstico de código antes da correção:
  - o gerador YSF pode criar uma entrada cujo nome efetivo vira `YSF-<nome>`, porém manter `Startup=<nome>`; o upstream faz busca exata por nome e então não encontra o refletor;
  - o helper DMR atual habilita TS1/TS2 conforme o slot salvo mesmo em `Duplex=1`; em repetidora isso pode deixar um dos caminhos locais desabilitado;
  - o helper de modo recebe `use_mode`, mas não reforça `[General] Duplex`, deixando caminhos de ativação dependentes da ordem anterior.
- Estado: **implementação iniciada / HW PENDENTE**. DMR simplex funcional permanece baseline e não pode regredir.


### Gate de build D-Star — 2026-09-22
- Run ARM64 anterior falhou antes de gerar imagem porque o hook do patch `SEC-025` procurou `RepeaterHandler.cpp` após a compilação do DStarGateway.
- Correção: anchor determinístico imediatamente antes de `make -C DStarGateway`.
- Estado: **SW corrigido; novo build ARM64 obrigatório antes de disponibilizar download**.


## 2026-09-22 — Identidade canônica e aba do navegador
- **ARCH-005 / DOC:** nome canônico aprovado: `PU2PNY/PU2PNY-OS`.
- **GitHub observado antes da renomeação administrativa:** `PU2PNY/2PNY-OS`; não declarar a renomeação concluída até a API do GitHub confirmar o novo nome.
- **UI-035 / SW fonte:** branch `pu2pny-os-0.3.19-alpha` normaliza o `<title>` para exatamente `PU2PNY-OS` e reforça o mesmo título no JS comum.
- **HW/PROD:** sem mudança de estado; esta manutenção não altera RF, MMDVM, gateways, rede ou protocolos.


### Gate TGIF da imagem 0.3.19 — 2026-09-22
- O run `35754924972` passou source, staging, build ARM64 e SHA-256, mas a validação montada bloqueou a publicação ao detectar ausência da baseline TGIF 0.3.13 no helper DMR 0.3.19.
- A imagem desse run **não foi publicada**.
- Correção aplicada: restauração do routing/auth TGIF com extensão duplex limitada aos dois slots RF locais.
- Rollback: `backup/0.3.19-pre-tgif-duplex-fix-20260922`.
- Estado: **SW corrigido / novo build+imagem montada obrigatórios / HW PENDENTE**.

### Gate D-Star voice assets da imagem 0.3.19 — 2026-09-22
- O run `35756725766` passou source, staging, ARM64, XZ/SHA e todos os gates até PROTO-024, mas bloqueou a publicação porque `/usr/local/share/dstargateway.d/en_GB.ambe` não existia na imagem.
- Causa confirmada no builder herdado: ele compilava/instalava apenas `DStarGateway/dstargateway` e removia o checkout sem instalar os arquivos `Data/*.ambe/*.indx` do mesmo commit pinado.
- Correção: copiar somente os packs de voz nativos `.ambe/.indx` para `/usr/local/share/dstargateway.d/` antes de remover o source; hostfiles/configuração PU2PNY não são substituídos.
- Rollback: `backup/0.3.19-pre-dstar-voice-assets-fix-20260922`.
- Estado: **SW corrigido / novo build e validação montada obrigatórios / HW PENDENTE**.


### REL-015 — pré-validação permanente antes do validador final
- Regra aprovada em 2026-09-22: toda imagem deve passar por pré-validação montada em modo somente leitura antes do validador final da versão.
- O preflight verifica XZ/SHA-256, identidade/versão, arquivos essenciais, título canônico, DMR baseline e assets D-Star obrigatórios.
- Falha no preflight bloqueia o validador final e a publicação; a correção deve ocorrer no fonte/overlay/builder e exigir novo build.
- Implementação atual: `ci/preflight-image.sh` + etapa `Pre-validate generated image` no workflow 0.3.19.
- Estado: **implementado em código; CI PENDENTE até o novo run concluir**.


### Run 35758692012 — REL-015 funcionou; novo bloqueador D-Star identificado
- Source, staging, ARM64, XZ/SHA-256 e **Pre-validate generated image**: PASS.
- O preflight confirmou `en_GB.ambe` e `en_GB.indx` antes do validador final.
- O validador final bloqueou a publicação porque `/usr/local/share/dstargateway.d/DStar_Hosts.json` ainda não estava presente.
- Causa de empacotamento: o catálogo pinado já existia no cache staged da cadeia herdada, mas não era duplicado para o diretório de dados do DStarGateway.
- Correção staged: copiar o mesmo catálogo pinado para o overlay do diretório de dados antes do build e exigir sua presença/tamanho também no REL-015.
- Rollback: `backup/0.3.19-pre-dstar-hostfile-fix-20260922`.
- Estado: **SW corrigido / novo CI obrigatório / publicação bloqueada até PASS**.


### Run 35760337205 — 0.3.19 publicada
- Source: PASS.
- Staged source: PASS.
- ARM64: PASS.
- XZ + SHA-256: PASS.
- Preflight REL-015: PASS.
- Validador final: PASS.
- Artefato: PASS.
- Publish: PASS.
- Prerelease: `v0.3.19-alpha`.
- Imagem: `PU2PNY-OS-0.3.19-alpha-arm64.img.xz` — 597725788 bytes.
- SHA-256 da imagem: `5f14e62b5811129f42f6dd9b7c637cfaa0944a370db42637abc56d1ac62f2355`.
- Commit da release: `c4db3e0098e2af1cd0ec1504e8946d30ac8c6391`.
- Nível: **SW/CI PASS; ALPHA/HW-TEST**. DMR/YSF/D-Star/duplex e demais correções físicas continuam exigindo reteste HW antes de promoção.


## 0.3.20-alpha — REL-016 — 2026-09-22
- **Base:** 0.3.19-alpha publicada + rollback `backup/0.3.19-pre-0.3.20-20260922`.
- **Branch:** `pu2pny-os-0.3.20-alpha`.
- **Classificação atual:** ALPHA / PARA TESTE FÍSICO.
- **SW/CI:** run `35798691612` PASS em source, staged source, ARM64, XZ/SHA-256, REL-015, validador final, artefato e publish. **VPS:** WartyWallaby validou testes Python/Shell/JS e backend Go; Direct não compilou nessa VPS por Go 1.19, mas o CI oficial usa Go 1.24.
- **HW:** PENDENTE para D-Star RF real, troca de refletor por rádio, DMR duplex áudio/TX/RX, Nextion física/COMOK/Moderno V2, S-meter/RSSI/BER reais e Direct entre dois hotspots.
- **Baseline obrigatório:** DMR simplex TX/RX aprovado e YSF/C4FM simplex reportado funcionando perfeitamente não podem regredir.
- **Falha D-Star confirmada na 0.3.19:** painel aplicava corretamente mudança manual de refletor (XLX300D comprovado); comando de rádio para troca alterava apenas estado visual sem confirmar execução. PROTO-032 corrige sem promover HW PASS antes do novo teste.
- **Módulo local D-Star:** padrão de nova configuração B, seletor A–D; upgrades preservam configuração anterior.
- **Gate de imagem:** source → staging → ARM64 → XZ/SHA-256 → REL-015 preflight → `validate-0.3.20-image.sh` → prerelease: **PASS no run `35798691612`**.


## Governança documental sincronizada — 2026-09-22
- **ARCH-006:** documentação canônica separada de material histórico/técnico; `docs/README.md` criado como índice.
- **REL-017:** baseline aprovado passa a ter proteção explícita e permanente; DMR simplex continua baseline crítico e correção duplex não autoriza alteração do simplex.
- **TEST-008:** VPS/SentinelX, GitHub/CI, plugins/conectores e fontes oficiais devem ser usados conforme aplicabilidade; nível HW continua reservado a hardware real.
- README e START_HERE foram alinhados ao ciclo 0.3.20-alpha e deixaram de apresentar 0.1.1 como estado atual.
- Escopo desta organização: documentação/governança. Nenhum estado HW é promovido por esta alteração.


### Run 35798691612 — 0.3.20 publicada
- Source: PASS.
- Staged source: PASS.
- Build ARM64: PASS.
- XZ + SHA-256: PASS.
- Preflight REL-015: PASS.
- Validador final: PASS.
- Artefato transferido/verificado: PASS.
- Publish: PASS.
- Prerelease: `v0.3.20-alpha`.
- Imagem: `PU2PNY-OS-0.3.20-alpha-arm64.img.xz` — 614874612 bytes.
- SHA-256 da imagem: `f42756bfcce537a7890b6296db3da3258fd8e909a45c7856f1530c8b363bed56`.
- Commit publicado: `0e6063688396ad2a0f1cf60cfe5e60915e711019`.
- Nível: **SW/CI PASS; ALPHA/PARA TESTE FÍSICO**.
- Permanecem HW PENDENTE: D-Star RF/comandos por rádio, DMR duplex RF↔rede, regressão física do DMR simplex nesta imagem, Nextion/COMOK/Moderno V2, BER/RSSI/S-meter reais e Direct entre dois hotspots.

## 0.3.21-alpha — correções do teste físico de 22/09/2026

**Base:** 0.3.20-alpha integral. **Baseline HW protegida desta rodada:** D-Star simplex PASS e DMR simplex PASS. Tudo que não foi reportado como falha permanece congelado.

### Implementado em fonte / candidato a SW
- DMR duplex: TS1/TS2 locais explícitos, MMDVMHost antes do DMRGateway e arbitragem de voz limitada ao estado SENDING para não silenciar áudio NETWORK→RF.
- DMR TG: separação entre TG solicitado e TG confirmado; Ao Vivo/Protocolos mostram TG real em vez de módulo DMR obsoleto.
- DNS: confirmação assíncrona verdadeira e recuperação visual; aviso global de perda de Internet.
- Wi‑Fi: rede atual + uma rede backup, failover e seleção por sinal com histerese; estado identifica Wi‑Fi 1/2.
- Wizard/idioma: idioma persistente perguntado uma vez; com Internet já configurada, retoma em Hardware.
- Direct: chamada disparada pelo rádio; D-Star por indicativo/URCALL e DMR por Private Call/Radio ID; payload QSO direct-only, sem relay de servidor.
- APRS: ACK/REJ por origem+ID, retry limitado, diagnóstico de ACK e coordenadas manuais em HTTP; M-SMS/H-SMS documentados como pesquisa/compatibilidade, sem alegar DMR SMS entregue.
- Nextion: estado físico permanece não confirmado sem COMOK; caminho TX-only é mostrado como tal.
- Relógio: NTP/timezone automático; DST manual apenas na apresentação.
- Logs: journal persistente limitado/comprimido.
- BER: assistente RXOffset com medida real, melhor valor da sessão, salvar/restaurar e rollback.
- HMI: boot/progresso, idioma persistente e dados operacionais somente quando reais.
- CI 0.3.21 inclui regressões da 0.3.20, proteção simplex, preflight REL-015 e validador montado específico.

### Pendências que continuam HW
- DMR duplex RF→rede e rede→RF com áudio real, timeout, TS/CC e Ao Vivo.
- Regressão DMR simplex TX/RX e D-Star simplex após a imagem 0.3.21.
- Nextion física COMOK/render real.
- Direct RF A↔B entre dois hotspots.
- BER/RSSI reais e recomendação RXOffset em Raspberry/MMDVM.
- ACK dos IDs históricos 89018, 70182 e 42231 não pode ser retroativamente confirmado sem log/ACK correspondente.

**Classificação alvo:** ALPHA / PARA TESTE FÍSICO. Não promover itens HW por CI/VPS.

### Run 35815292900 — 0.3.21-alpha publicada
- Source: **PASS**.
- Staged source: **PASS**.
- Build ARM64: **PASS**.
- XZ + SHA-256: **PASS**.
- Preflight REL-015: **PASS**.
- Validador final 0.3.21: **PASS**.
- Artefato: **PASS**.
- Publish: **PASS**.
- Prerelease: `v0.3.21-alpha`.
- Commit publicado: `c585b0e6ae10b93f3272f8783eb2832045983194`.
- Imagem: `PU2PNY-OS-0.3.21-alpha-arm64.img.xz` — **610089972 bytes**.
- SHA-256 da imagem: `c2ec6b729b3f60153274909c8280fc2f73a07d5e426fdd129a7982d4f9d420ab`.
- VPS/SentinelX: regressões 0.3.20 + 0.3.21, sintaxe Python/Shell, diagnóstico duplex selftest e limites de journal: **PASS**.
- Classificação real: **ALPHA / PARA TESTE FÍSICO**. DMR duplex, regressão simplex na nova imagem, Nextion física, Direct A↔B e BER/RSSI reais continuam **HW PENDENTE**.

