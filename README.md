# PU2PNY-OS

**PU2PNY-OS — Digital Radio Operating System**

Sistema operacional headless para Raspberry Pi destinado a hotspots MMDVM, com foco em baixo consumo, configuração simples, diagnóstico de rede e evolução para operação multiprotocolo.

## Estado atual

**0.1.1 Alpha — fundação de boot, rede e primeiro acesso.**

Esta versão ainda **não deve ser usada para transmissão RF**. A etapa atual valida boot, Ethernet/Wi‑Fi, painel local, mDNS e provisionamento inicial antes de integrar MMDVMHost e gateways.

## Primeiro acesso da Alpha

- Wi‑Fi de configuração: `2PNY-SETUP`
- Senha temporária: `2pnysetup`
- URL principal: `http://2pny.local`
- Fallback durante o setup: `http://10.42.0.1`

## Roadmap principal

- detecção de Raspberry Pi, MMDVM, firmware e capabilities;
- detecção de displays compatíveis;
- calibração BER/RXOffset/TXOffset;
- DMR, D‑Star, YSF/C4FM, P25 e NXDN;
- XLX026 como perfil recomendado: DMR XLX026-C/TG6, D‑Star XLX026-D e BR‑XLX026/YSF72426;
- BrandMeister, TGIF, FreeDMR, DMR+, XLX e redes personalizadas;
- RadioID, QRZ opcional, GPS/APRS e histórico;
- diagnóstico de Internet, failover Ethernet/Wi‑Fi e reconexão automática;
- PU2PNY Direct para chamadas ponto a ponto em etapa futura.

## Build

A imagem ARM64 é construída por GitHub Actions em runner ARM64 a partir do Raspberry Pi OS Lite 64-bit e publicada como artefato `.img.xz` acompanhado de SHA‑256.

> Projeto em desenvolvimento. Não use a Alpha como substituto do Pi‑Star/WPSD em operação crítica até a camada RF passar por teste físico.
