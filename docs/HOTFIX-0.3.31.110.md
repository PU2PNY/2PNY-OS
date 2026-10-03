# PU2PNY-OS 0.3.31.110 — hotfix MMDVMHost/autostart

Data: 2026-10-03
Base: `v0.3.31-alpha` / commit `88ab36d60897f41bc2b35687f115651fa12f03ec`
Escopo: somente regressão de restauração do perfil/MMDVMHost no boot.

## Fato reproduzido

Em teste determinístico com equipamento já provisionado, MMDVM detectada, perfil DMR salvo e rota disponível:

- autostart da 0.3.30 chama `2pny-protocol-profiles activate DMR`;
- autostart da 0.3.31 sai sem ativar quando `/var/lib/2pny/last-active-profile.json` ainda não existe;
- quando o arquivo proven existe, o caminho 0.3.31 tenta ativar normalmente.

A regressão foi introduzida ao transformar `last-active-profile.json` em pré-condição absoluta de restauração. Isso pode deixar MMDVMHost/gateway parados após boot/rede antes de existir o primeiro snapshot proven.

## Correção 0.3.31.110

Restaurar byte-for-byte o `2pny-profile-autostart` comprovado da 0.3.30 (`src/2pny-profile-autostart-0.3.28.py`) na imagem 0.3.31.110.

O mecanismo 0.3.31 de snapshot `last-active-profile.json` permanece instalado, mas deixa de bloquear a restauração do perfil salvo. Nenhum helper de RF/protocolo é alterado.

## Baseline protegido

O workflow exige hash idêntico antes/depois para:

- `MMDVM-Host`;
- `2pny-dmr-apply`;
- `2pny-protocol-network-apply`;
- `2pny-display-apply`;
- `2pny-network-online`;
- `2pny-profile-proven`;
- `hotspot.html`.

Portanto este hotfix não altera DMR, D-Star, YSF/C4FM, RF, frequências, offsets, gateways, display, rede, áudio ou UI.

## Testes

- reprodução da regressão 0.3.30 → 0.3.31: PASS SW/VPS;
- teste determinístico do fallback: PASS SW/VPS;
- sintaxe Python/Shell: PASS SW/VPS;
- build ARM64, montagem da imagem, hashes protegidos, `e2fsck`, preflight montado read-only e SHA-256: executados pelo workflow da release;
- Raspberry Pi + MMDVM real: PENDENTE HW até o operador testar a imagem.

## Estado

Classificação: `ALPHA / PARA TESTE FÍSICO`.
Não promover a HW PASS apenas por CI PASS.
