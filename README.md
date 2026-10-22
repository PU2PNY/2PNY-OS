# PU2PNY-OS 5.00.002 — somente display

**Candidata para teste físico / Alpha. SW/CI PASS; HW PENDENTE.**

[Release e downloads](https://github.com/PU2PNY/2PNY-OS/releases/tag/v5.00.002) · [Build verificado](https://github.com/PU2PNY/2PNY-OS/actions/runs/39775950167) · [Guia de teste](docs/DISPLAY-5.00.002.md)

Correção do caminho Nextion para o MMDVM-Host MQTT instalado: MMDVM-Display oficial externo, G4KLX/L2 e ON7LDS L3/L3 HS com NextionDriver e bridge exclusiva de display. Firmware/HMI, motor RF, protocolos, gateways e rede preservados. OLED/LCD diretos mantêm o caminho existente, sem alegação de paridade integral Pi-Star não testada.

| Arquitetura | Imagem | SHA-256 |
|---|---|---|
| ARM64 | [Baixar](https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.002/PU2PNY-OS-5.00.002-arm64.img.xz) | `f14e952df5396cc04f30feefcc6c0485f54be3c78fcb07f887a5bb06178e4271` |
| ARM32 | [Baixar](https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.002/PU2PNY-OS-5.00.002-arm32.img.xz) | `9189df04882eff46a2824e5af6a367545edc21ae6f1714bac5042537714f5f12` |

Commit das imagens/tag: `56a0b6a4a97fee4cd35314e0f3943918a32fbc2d`. Branch: `pu2pny-os-5.00.002-display-only`. Baseline: imagens publicadas v5.00.001 verificadas por SHA-256.

Leia `PU2PNY-OS_START_HERE.md` antes de alterar o projeto.
