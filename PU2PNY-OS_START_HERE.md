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

## Ciclo 5.12.000 P0 — PUBLICADO, CANDIDATA PARA TESTE FÍSICO

**Estado verificado em 13/11/2026:** a prerelease [PU2PNY-OS 5.12.000 P0 ALPHA](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.000-p0) está **PUBLICADA** como **candidata para teste físico**, não produção. Código/commit imutável dos quatro artefatos: [`1b2a0a0068303b9bf091c26c90012755708f2bb1`](https://github.com/PU2PNY/2PNY-OS/commit/1b2a0a0068303b9bf091c26c90012755708f2bb1). O [CI 43488577915](https://github.com/PU2PNY/2PNY-OS/actions/runs/43488577915) finalizou com **6/6 jobs success** (`tests`, `build (arm32)`, `build (arm64)`, `boards (opizero)`, `boards (nanopineo)`, `publish`). O publish executou `xz -t`, `sha256sum -c` e conferiu `BUILD-INFO` das quatro placas; na release há quatro arquivos não vazios .img.xz, quatro .sha256 e quatro manifestos. **HW NÃO VERIFICADO**; **PROD NÃO APROVADO**.

| Placa | Imagem 5.12 P0 | Verificação |
|---|---|---|
| Raspberry ARM32 | [pu2pny-32-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-32-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-32-5.12.img.xz.sha256) |
| Raspberry ARM64 | [pu2pny-64-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-64-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-64-5.12.img.xz.sha256) |
| Orange Pi Zero H2+ | [pu2pny-opizero-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-opizero-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-opizero-5.12.img.xz.sha256) |
| NanoPi NEO H3 | [pu2pny-nanopineo-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-nanopineo-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-nanopineo-5.12.img.xz.sha256) |

**Escopo efetivamente corrigido em SW/CI (P0):** BOOT-512 (remove a espera artificial de 300 s dos serviços opcionais do caminho crítico e preserva timers) e NET-512 (inclui e habilita `2pnyd.service` no empacotamento Orange Pi Zero/NanoPi NEO). **Não comprova boot/AP/HTTP em hardware**. Continuam sem correção ou verificação física: DMRGateway, D-Star `connected:false`, reinicialização MMDVMHost, Nextion SIGSEGV, Avahi/mDNS, subtensão, nomes/IP por placa, redesign e backlog completo da 5.12. Preservar a baseline da 5.11, o ON7LDS HW aprovado e demais RF. Issue [#23](https://github.com/PU2PNY/2PNY-OS/issues/23) permanece aberta para as pendências.

---

## Ciclo atual: 5.11.000 ALPHA — PUBLICADA, EM HOMOLOGAÇÃO FÍSICA

[Release 5.11 e quatro imagens](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.11.000) · [CI completo: 6/6 jobs success](https://github.com/PU2PNY/2PNY-OS/actions/runs/43252249844). Commit fonte/tag: `92914a3a19b9713416b541cfa93fc98b37261c9c`. **SW/CI PASS; HW PENDENTE; PROD NÃO APROVADO.** Não aplicar a 5.11 automaticamente em equipamentos aprovados; antes, testar e confirmar rollback. As referências históricas abaixo a 5.00.002 e as afirmações antigas "não entregue" não são o estado atual da publicação. Preserve a baseline Nextion ON7LDS aprovada e todas as baselines RF.

Base 5.10 `1a280662d4ab48bb1ea9726874a11c1e5a126c55`; branch `release/pu2pny-5.11`. Consulte a seção REL-511 mais recente dos documentos canônicos e a [ordem completa](docs/PU2PNY-OS_5.11_ORDEM_DE_TRABALHO.md).

## DISPLAY-041 — BASELINE ATIVO APROVADO EM HARDWARE — 2026-10-22

**PU2PNY-OS 5.00.002 / NextionDriver ON7LDS = HW PASS por relato explícito do usuário: “a tela funcionou perfeito”. FUNCIONANDO + APROVADO = PROTEGER.**

A regra única de display está em `docs/PU2PNY-OS_DISPLAY_BASELINE.md` (a partir de docs/, usar o nome sem prefixo docs/). Este bloco substitui orientações anteriores conflitantes sobre o display testado. Conteúdo de versões anteriores abaixo é histórico de investigação, nunca instrução para reconfigurar o baseline atual.

- Preservar o caminho MMDVM-Display oficial → PTY → NextionDriver ON7LDS → bridge exclusiva de display → MQTT → MMDVM-Host → modem/tela.
- Não voltar ao renderer Nextion inexistente no MMDVM-Host MQTT; não reintroduzir PU2PNY Moderno, renderização própria, writers concorrentes, fallback automático ou flash HMI/TFT.
- Manter a seleção, o layout, a porta, o baud e a configuração que funcionaram. O usuário confirmou ON7LDS, mas não informou nesta aprovação L3 versus L3 HS, arquitetura nem modelo: não inventar, alterar por suposição ou promover as alternativas a HW PASS.
- Preservar o código de display da imagem `v5.00.002`, fonte `56a0b6a4a97fee4cd35314e0f3943918a32fbc2d`; alterações futuras exigem defeito reportado ou ordem explícita, comparação com este baseline, rollback e novo teste físico.
- Aprovação é do funcionamento geral da tela no conjunto testado. Toque, reboot, cada métrica, outros displays/arquiteturas e modos não relatados mantêm seus próprios estados NÃO VERIFICADO/PENDENTE.
- RF, protocolos, gateways, rede e demais funções continuam congelados. Nenhuma mudança de runtime/configuração é aplicada por este registro.

---

# PU2PNY-OS — START HERE

**Documento obrigatório de entrada do projeto.**

Antes de analisar, corrigir, programar, publicar, gerar imagem, alterar GitHub, CI/CD, servidor, RF, rede, display ou documentação do PU2PNY-OS, leia nesta ordem:

1. `PU2PNY-OS_START_HERE.md`
2. `PU2PNY-OS_MASTER_SPEC.md`
3. `PU2PNY-OS_RELEASE_STATUS.md`
4. `PU2PNY-OS_TEST_MATRIX.md`
5. `PU2PNY-OS_CHANGELOG.md`
6. `PU2PNY-OS_PROJECT_INSTRUCTIONS.md` como resumo operacional permanente
7. `docs/PU2PNY-MASTER-PLAN.md` apenas como histórico consolidado anterior
8. o código da branch efetivamente em trabalho

## Fontes de verdade

- **MASTER_SPEC**: requisitos funcionais e técnicos aprovados.
- **RELEASE_STATUS**: estado real da release e bloqueadores.
- **TEST_MATRIX**: o que foi realmente testado e em qual nível.
- **CHANGELOG**: decisões e alterações registradas.
- **Código/repositório**: implementação existente.
- **PROJECT_INSTRUCTIONS**: regras permanentes resumidas de execução.
- Documentos em `docs/` são técnicos/históricos salvo indicação explícita em contrário.

## Regras invariáveis

- `funcionando + aprovado = preservar`: baseline aprovado não pode ser alterado fora do escopo sem ordem explícita.
- DMR simplex TX/RX comprovadamente funcional é baseline obrigatório; defeito duplex não autoriza reescrever simplex.
- PU2PNY-OS é sistema próprio; não é fork de Pi-Star/WPSD.
- Não reiniciar o projeto do zero.
- Antes de mudar RF, modem, baud, offsets, MMDVMHost, gateways, HMI/TFT, rede ou boot: registrar estado, criar rollback e limitar o escopo.
- Se uma função regredir, localizar a última versão funcional e restaurar somente o necessário.
- Não chamar de testado algo apenas compilado/instalado/inspecionado.
- Não inventar BER, RSSI, chamadas, gateways, progresso, localização ou estado. Sem evidência: `—`/indisponível/não verificado.
- Quando aplicável sem RF real, validar em VPS via SentinelX e usar plugins/conectores/fontes oficiais para confirmação cruzada.
- VPS não substitui Raspberry Pi/MMDVM/Nextion/RF real.
- Preservar CPU, RAM e SD; evitar polling e logs excessivos.
- Usuário final não deve depender de terminal.
- Toda decisão permanente recebe ID e atualiza MASTER_SPEC, CHANGELOG, RELEASE_STATUS quando aplicável e TEST_MATRIX.

## Níveis de validação

- **DOC** — documentação/código.
- **SW** — software/CI.
- **VPS** — ambiente Linux/VPS.
- **HW** — Raspberry Pi + hardware real.
- **PROD** — produção/uso real.

Estados auxiliares: PENDENTE, EM TESTE, APROVADO, FALHOU, REGRESSÃO, BLOQUEADO e NÃO VERIFICADO.

## Ordem de implementação

Base/Boot → Rede/Wizard → Hardware → RF/MMDVM → DMR → D-Star → YSF/C4FM → demais protocolos → Runtime/Event Bus → Ao Vivo → Painel/API → Displays/Nextion → APRS/DPRS → QRZ → Direct/P2P/CGNAT → Update/Backup/Rollback → Segurança → testes físicos → RC → Produção.

## Gate de release

Antes de divulgar imagem: requisito → implementação → teste → resultado → regressão → pendência.

Não liberar como completa com requisito crítico ausente, regressão conhecida de DMR/RF/rede/wizard/boot, build ARM64 incompleto, imagem sem validação estrutural/SHA-256 ou afirmação HW sem teste físico.

**REL-015:** toda imagem deve passar por pré-validação montada em somente leitura antes do validador final. Falha exige correção no fonte/overlay/builder e novo build; nunca enfraquecer o gate.

## Identidade canônica

- Nome canônico aprovado: `PU2PNY-OS`.
- Repositório canônico aprovado: `PU2PNY/PU2PNY-OS`.
- Enquanto a metadata do GitHub retornar `PU2PNY/2PNY-OS`, esse é o caminho real observado.
- Título da aba: exatamente `PU2PNY-OS`.

## Ciclo consolidado — 0.3.31.110 — 2026-10-05

- Branch de código observada: `pu2pny-os-0.3.31.110`.
- Commit observado: `1c91b26fd561eb7a727df896f2179fd951b6681a`.
- Snapshot de baseline: `docs/PU2PNY-OS_BASELINE_0.3.31.110.md`.
- A 0.3.31.110 é o estado mais novo do código, não uma promoção automática para HW PASS.
- A 0.3.30-alpha continua sendo a última candidata de display com SW/CI/VPS formalmente registrado: run `36341170897`, com Nextion/OLED/LCD físico ainda HW PENDENTE.
- Baselines HW protegidas incluem DMR simplex, D-Star simplex e YSF/C4FM simplex conforme evidências consolidadas no snapshot; duplex e recursos avançados mantêm seus estados próprios.
- `REL-026`: os cinco documentos canônicos devem distinguir código atual de evidência de validação e nunca inferir HW por SW/VPS.


## 2026-10-22 — display isolado
Ciclo corrente: 5.00.002, branch pu2pny-os-5.00.002-display-only, base publicada v5.00.001. Escopo exclusivo display; docs/DISPLAY-5.00.002.md. Demais subsistemas congelados por ordem do usuário.


Entrega corrente: **5.00.002**, candidata para teste físico publicada. Fonte `56a0b6a4a97fee4cd35314e0f3943918a32fbc2d`; branch `pu2pny-os-5.00.002-display-only`. https://github.com/PU2PNY/2PNY-OS/releases/tag/v5.00.002 . CI/VPS conforme matriz; HW PENDENTE. Escopo somente display, demais subsistemas congelados.
