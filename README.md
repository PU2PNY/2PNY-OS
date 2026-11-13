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
