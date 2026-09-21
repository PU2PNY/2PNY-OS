# PU2PNY-OS — RELEASE STATUS

**Branch de trabalho:** `pu2pny-os-0.3.6-alpha`  
**Base preservada:** `pu2pny-os-0.3.5-alpha`  
**Backup criado antes das mudanças:** `backup/0.3.5-hw-feedback-20260920`  
**Data do último feedback físico incorporado:** 2026-09-20  
**Estado global:** ALPHA / correção. **Não PROD.**

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
