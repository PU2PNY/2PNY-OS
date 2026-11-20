## PU2PNY-OS 5.13.002 · Teste físico · 19/11/2026

[Release candidata](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.13.002) · [GitHub Actions](https://github.com/PU2PNY/2PNY-OS/actions/runs/44647034376) · [Checklist físico](https://github.com/PU2PNY/2PNY-OS/blob/release/pu2pny-5.13/docs/PU2PNY-OS_5.13_HW_CHECKLIST.md)

O salvamento da segunda rede Wi-Fi mantém a conexão atual e a recuperação tenta a reserva quando a principal falha. A versão também corrige o relógio e o fuso, a restauração da Nextion, o portal de configuração de rede e a aplicação da política de Acesso RF. O OLED tem opção de rotação de 180° em Expert.

| Placa | Imagem | SHA-256 |
|---|---|---|
| Raspberry Pi ARM32 | [Baixar imagem](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.13.002/pu2pny-32-5.13.002.img.xz) | [Verificar](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.13.002/pu2pny-32-5.13.002.img.xz.sha256) |
| Raspberry Pi ARM64 | [Baixar imagem](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.13.002/pu2pny-64-5.13.002.img.xz) | [Verificar](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.13.002/pu2pny-64-5.13.002.img.xz.sha256) |
| Orange Pi Zero H2+ | [Baixar imagem](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.13.002/pu2pny-opizero-5.13.002.img.xz) | [Verificar](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.13.002/pu2pny-opizero-5.13.002.img.xz.sha256) |
| NanoPi NEO H3 | [Baixar imagem](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.13.002/pu2pny-nanopineo-5.13.002.img.xz) | [Verificar](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.13.002/pu2pny-nanopineo-5.13.002.img.xz.sha256) |

Commit fonte `800f715e4973f612a1500373f6a54cd35ea69c14`. Os quatro builds passaram em integridade XZ, SHA-256 e ext4. Wi-Fi, HMI, tela, RF e acesso ao painel nas placas ainda precisam de teste físico.

## Versão anterior: 5.12.002 P2 ALPHA — 15/11/2026

**Status:** [release P2 publicada](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.002-p2) · [GitHub Actions 6/6 PASS](https://github.com/PU2PNY/2PNY-OS/actions/runs/43727451516) · [checklist de teste físico](https://github.com/PU2PNY/2PNY-OS/blob/release/pu2pny-5.12.002/docs/PU2PNY-OS_5.12.002_HW_CHECKLIST.md). Tag aponta ao código **`a5f9f286d48a88b9fb658f56cb111c9acaa8a737`**. Quatro imagens `.img.xz`, checksums `.sha256` e quatro manifestos `BUILD-INFO` verificados. **ALPHA PARA TESTE FÍSICO; não homologada em hardware; NÃO produção.**

| Placa | Baixar imagem 5.12.002 | SHA-256 |
|---|---|---|
| Raspberry Pi ARM32 (inclui Pi Zero W) | [Download .img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.002-p2/pu2pny-32-5.12.002.img.xz) | [Verificar](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.002-p2/pu2pny-32-5.12.002.img.xz.sha256) |
| Raspberry Pi ARM64 | [Download .img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.002-p2/pu2pny-64-5.12.002.img.xz) | [Verificar](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.002-p2/pu2pny-64-5.12.002.img.xz.sha256) |
| Orange Pi Zero H2+ | [Download .img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.002-p2/pu2pny-opizero-5.12.002.img.xz) | [Verificar](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.002-p2/pu2pny-opizero-5.12.002.img.xz.sha256) |
| NanoPi NEO H3 | [Download .img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.002-p2/pu2pny-nanopineo-5.12.002.img.xz) | [Verificar](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.002-p2/pu2pny-nanopineo-5.12.002.img.xz.sha256) |

**Correções SW:** permissões dos arquivos `DMRGateway.ini` quando alterados pelo serviço de avisos de voz (leitura comprovada por `mmdvm` e rollback); tarefas de manutenção em Pi Zero W adiadas durante boot/CPU saturada, restaurador operacional com backoff; Orange/Nano com dono único do processo `hostapd` e maior margem de memória do painel. Em CI, `/healthz` das imagens Armbian respondeu em rede isolada; **não é teste físico de AP/DHCP**. RF, modem, MMDVMHost, NextionDriver ON7LDS e bootloader protegidos por manifesto.

**Pendências:** redução efetiva de CPU em Pi Zero ainda precisa ser medida; acesso ao AP/HTTP Orange/Nano ainda não verificado em hardware; DMR, D-Star e YSF simplex tiveram baselines HW históricos, mas precisam de TX/RX e link de gateway comprovados nesta release. Relógio/fuso, transcodificação real, Direct/CGNAT e campos Nextion extras não foram corrigidos ou homologados por este patch. Evitar sobrescrever o microSD anterior.

---

## Regra permanente de atualização

**DOC-README-001:** a cada release/hotfix ou mudança relevante de validação, correção ou bloqueador, atualizar e reler a página principal da `main` e o README da versão antes de encerrar o ciclo. Conferir versão, data, tag, branch, commit, downloads, SHA-256, CI, documentação e pendências. Preservar histórico e distinguir SW/CI de HW/PROD. [Regra completa](PU2PNY-OS_PROJECT_INSTRUCTIONS.md).

---

## 5.12.001 P1 ALPHA — quatro imagens para teste físico (14/11/2026)

[Baixar 5.12.001 P1](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.001-p1) · [CI 6/6 PASS](https://github.com/PU2PNY/2PNY-OS/actions/runs/43597269377) · [Checklist de hardware](docs/PU2PNY-OS_5.12.001_HW_CHECKLIST.md). Quatro imagens ARM32/ARM64/Orange Pi Zero/NanoPi NEO e respectivos SHA-256 publicados, código do artefato `38f3ac23582e4c5a424b09a5901b03f828aa617a`. Implementação limitada: menu fallback, relógio visível, páginas OLED/LCD e diagnóstico Expert ampliado em TXT. **HW PENDENTE, NÃO É PRODUÇÃO.** RF, NextionDriver ON7LDS, bootloader e rede preservados por manifesto. **Não entregues/sem prova física:** correção DMR/YSF/D-Star, HTTP Orange, extras Nextion, transcoding e Direct CGNAT/relay. Versão exibida pelo backend pode permanecer `5.11.000` (#30); `/etc/2pny/version` registra `5.12.001`. Preservar cartão anterior e conferir [issues 23–30](https://github.com/PU2PNY/2PNY-OS/issues).

---

# PU2PNY-OS — release 5.12.000 P0 ALPHA (quatro imagens)

**Estado verificado em 13/11/2026:** a prerelease [PU2PNY-OS 5.12.000 P0 ALPHA](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.000-p0) está **PUBLICADA** como **candidata para teste físico**, não produção. Código/commit imutável dos quatro artefatos: [`1b2a0a0068303b9bf091c26c90012755708f2bb1`](https://github.com/PU2PNY/2PNY-OS/commit/1b2a0a0068303b9bf091c26c90012755708f2bb1). O [CI 43488577915](https://github.com/PU2PNY/2PNY-OS/actions/runs/43488577915) finalizou com **6/6 jobs success** (`tests`, `build (arm32)`, `build (arm64)`, `boards (opizero)`, `boards (nanopineo)`, `publish`). O publish executou `xz -t`, `sha256sum -c` e conferiu `BUILD-INFO` das quatro placas; na release há quatro arquivos não vazios .img.xz, quatro .sha256 e quatro manifestos. **HW NÃO VERIFICADO**; **PROD NÃO APROVADO**.

| Placa | Imagem 5.12 P0 | Verificação |
|---|---|---|
| Raspberry ARM32 | [pu2pny-32-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-32-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-32-5.12.img.xz.sha256) |
| Raspberry ARM64 | [pu2pny-64-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-64-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-64-5.12.img.xz.sha256) |
| Orange Pi Zero H2+ | [pu2pny-opizero-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-opizero-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-opizero-5.12.img.xz.sha256) |
| NanoPi NEO H3 | [pu2pny-nanopineo-5.12.img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-nanopineo-5.12.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.000-p0/pu2pny-nanopineo-5.12.img.xz.sha256) |

**Escopo efetivamente corrigido em SW/CI (P0):** BOOT-512 (remove a espera artificial de 300 s dos serviços opcionais do caminho crítico e preserva timers) e NET-512 (inclui e habilita `2pnyd.service` no empacotamento Orange Pi Zero/NanoPi NEO). **Não comprova boot/AP/HTTP em hardware**. Continuam sem correção ou verificação física: DMRGateway, D-Star `connected:false`, reinicialização MMDVMHost, Nextion SIGSEGV, Avahi/mDNS, subtensão, nomes/IP por placa, redesign e backlog completo da 5.12. Preservar a baseline da 5.11, o ON7LDS HW aprovado e demais RF. Issue [#23](https://github.com/PU2PNY/2PNY-OS/issues/23) permanece aberta para as pendências.

A descrição da versão 5.11 abaixo é histórica e permanece como referência de rollback.

---

## PU2PNY-OS 5.11.000 ALPHA — quatro imagens publicadas

[Release e downloads](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.11.000) · [CI 6/6 jobs aprovados](https://github.com/PU2PNY/2PNY-OS/actions/runs/43252249844) · [Estado](PU2PNY-OS_RELEASE_STATUS.md) · [Testes](PU2PNY-OS_TEST_MATRIX.md).

**SW/CI PASS; HW PENDENTE; PROD NÃO APROVADO.** As quatro imagens foram criadas e publicadas a partir do commit/tag `92914a3a19b9713416b541cfa93fc98b37261c9c`. O CI conferiu integridade XZ, SHA-256 e BUILD-INFO; ainda não há validação de boot, RF, Wi-Fi, Nextion, OLED, crossmode ou Direct P2P em hardware real.

| Placa | Artefato | SHA-256 (digest publicado) |
|---|---|---|
| Raspberry ARM32 | [`pu2pny-32-5.11.img.xz`](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.11.000/pu2pny-32-5.11.img.xz) | `6a90ac0080fd72c28d3df8d52b44d076bb7764bd530b5673798180987a1262d9` |
| Raspberry ARM64 | [`pu2pny-64-5.11.img.xz`](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.11.000/pu2pny-64-5.11.img.xz) | `b8b6d844230c0611566625ab050e30dfbf89ca7adb367412e4f14a4bcf0bb103` |
| Orange Pi Zero H2+ | [`pu2pny-opizero-5.11.img.xz`](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.11.000/pu2pny-opizero-5.11.img.xz) | `343390b1c0d8edc1a4c3e32e2afb67f2103adfc136486756c79103c40ac8f1ad` |
| NanoPi NEO H3 | [`pu2pny-nanopineo-5.11.img.xz`](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.11.000/pu2pny-nanopineo-5.11.img.xz) | `7119966a09e77d0297209973c5e9bc47a746cff18e4bf74f7c66786703c21eb7` |

Os arquivos `.sha256` e `BUILD-INFO-*.json` de cada placa estão na [mesma release](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.11.000). Os registros abaixo sobre a 5.00.002 preservam um baseline histórico de display, não a versão de entrega mais recente.

# PU2PNY-OS 5.00.002 — somente display

**Display NextionDriver ON7LDS: HW PASS por aprovação do usuário em 22/10/2026. Baseline protegido. A aprovação não promove automaticamente outros dispositivos nem a release inteira a produção.**

[Release e downloads](https://github.com/PU2PNY/2PNY-OS/releases/tag/v5.00.002) · [Build verificado](https://github.com/PU2PNY/2PNY-OS/actions/runs/39775950167) · [Guia de teste](docs/DISPLAY-5.00.002.md)

Correção do caminho Nextion para o MMDVM-Host MQTT instalado: MMDVM-Display oficial externo, NextionDriver ON7LDS com bridge exclusiva de display. Manter a configuração que funcionou; consulte a [única regra ativa](docs/PU2PNY-OS_DISPLAY_BASELINE.md). Firmware/HMI, motor RF, protocolos, gateways e rede preservados. OLED/LCD diretos mantêm o caminho existente, sem alegação de paridade integral Pi-Star não testada.

| Arquitetura | Imagem | SHA-256 |
|---|---|---|
| ARM64 | [Baixar](https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.002/PU2PNY-OS-5.00.002-arm64.img.xz) | `f14e952df5396cc04f30feefcc6c0485f54be3c78fcb07f887a5bb06178e4271` |
| ARM32 | [Baixar](https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.002/PU2PNY-OS-5.00.002-arm32.img.xz) | `9189df04882eff46a2824e5af6a367545edc21ae6f1714bac5042537714f5f12` |

Commit das imagens/tag: `56a0b6a4a97fee4cd35314e0f3943918a32fbc2d`. Branch: `pu2pny-os-5.00.002-display-only`. Baseline: imagens publicadas v5.00.001 verificadas por SHA-256.

Leia `PU2PNY-OS_START_HERE.md` antes de alterar o projeto.
