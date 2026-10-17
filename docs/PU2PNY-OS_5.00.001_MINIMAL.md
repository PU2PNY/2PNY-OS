# PU2PNY-OS 5.00.001 Minimal

Status: EM IMPLEMENTAÇÃO

## Objetivo

Reconstruir ARM32 e ARM64 a partir de uma base Raspberry Pi OS mínima oficial, sem reutilizar o root filesystem da 4.x/5.00.000. A 5.00.000 pode ser usada somente como doadora de payload próprio do PU2PNY (painel/scripts/configuração), nunca como sistema operacional base.

## Base oficial fixada

- ARM32: RPi-Distro/pi-gen `master` @ `59b67461533c2eef3564bc48eb3ce5c16e5c62ee`.
- ARM64: RPi-Distro/pi-gen `arm64` @ `d346cd53562b3c6b4f94c9155175f814258c456d`.
- Release: Raspberry Pi OS Trixie.
- A imagem usa somente stage0 + stage1 + stage2 customizado PU2PNY. Stages desktop não participam.

## Motores RF fixados nesta candidata

- MMDVM-Host @ `a819ae64edd5de5a7468b24e47d673a53f94fc9f`.
- DMRGateway @ `ad172eae396fed562e14c92375d63479e9fe689a`.

Esses componentes são compilados para cada arquitetura durante o build. O CI não promove isso a HW PASS.

## Princípios

- rootfs novo, sem overlay do sistema 4.x;
- NetworkManager + Avahi para rede/mDNS;
- `pu2pny.local` canônico;
- runtime 5.x instalado separadamente;
- build dependencies removidas antes de exportar a imagem;
- logs e caches de build removidos;
- SSH desativado por padrão;
- dados não verificados permanecem `—`/NÃO VERIFICADO;
- DMR/D-Star/YSF e demais baselines HW anteriores continuam protegidas como requisitos, mas precisam de novo gate HW nesta base.

## Compatibilidade de painel

Até que todos os assets web sejam fonte-controlados individualmente, o build pode extrair exclusivamente o payload de aplicação da release 5.00.000 (`/usr/share/2pny`, `/usr/local/sbin/2pny-*`, `/etc/2pny` quando existir). O restante do rootfs 5.00.000 é descartado. Isso preserva o contrato visual sem herdar o sistema operacional antigo.

## Gate de release

Cada arquitetura deve passar:

1. build pi-gen minimal;
2. arquivo de imagem existente e não vazio;
3. montagem das partições;
4. arquitetura de binários compatível;
5. presença de MMDVMHost, DMRGateway, NetworkManager, Avahi, runtime 5.x e painel;
6. `systemd-analyze verify` quando possível offline;
7. `fsck` somente leitura;
8. compactação XZ + `xz -t`;
9. SHA-256;
10. publicação somente se ARM32 e ARM64 passarem.

A release deve ser classificada como ALPHA / CANDIDATA PARA TESTE FÍSICO até existir evidência HW real.
