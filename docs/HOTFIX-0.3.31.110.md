# PU2PNY-OS 0.3.31.110 — hotfix MMDVMHost/autostart

Data: 2026-10-03
Base: `v0.3.31-alpha` / commit `88ab36d60897f41bc2b35687f115651fa12f03ec`
Escopo: somente regressão da cadeia `last-active-profile` → restauração de MMDVMHost/gateway.

## Fatos reproduzidos

### 1. Snapshot virou pré-condição absoluta

No autostart da 0.3.31, se `/var/lib/2pny/last-active-profile.json` não existir ou não estiver válido, o script sai sem chamar `2pny-protocol-profiles activate`.

Em teste determinístico, o comportamento anterior da 0.3.30 reativa o perfil salvo, enquanto a 0.3.31 não executa ativação quando o snapshot ainda não existe.

### 2. DMR bem-sucedido nunca gerava o snapshot

O helper DMR protegido escreve `network-radio.json` com `state=configured` somente depois de confirmar MMDVMHost ativo e DMRGateway ativo.

O gravador `2pny-profile-proven` da 0.3.31 aceitava somente `gateway_active`, `active` ou `ready`. Consequência: uma ativação DMR válida não criava `last-active-profile.json`; no boot seguinte o autostart não tinha o arquivo que ele próprio exigia.

## Correção 0.3.31.110

- `2pny-profile-proven` passa a aceitar `state=configured` **somente quando o protocolo é DMR**. Os demais protocolos conservam o gate anterior.
- O autostart continua preferindo `last-active-profile.json` quando ele existe.
- Se o snapshot estiver ausente por migração/evento perdido, o fallback só é permitido quando `network-radio.json` representa um estado anteriormente bem-sucedido e coincide com o protocolo/servidor salvo. Um rascunho divergente não é ativado automaticamente.
- Falhas/exceções de restore são tratadas; o rascunho salvo continua preservado.

## Baseline protegido

O workflow exige hash idêntico antes/depois para:

- `MMDVM-Host`;
- `2pny-dmr-apply`;
- `2pny-protocol-network-apply`;
- `2pny-display-apply`;
- `2pny-network-online`;
- `hotspot.html`;
- units systemd de autostart/snapshot.

Portanto o hotfix não modifica o caminho RF/DMR/D-Star/YSF, frequências, offsets, gateways, display, rede, áudio ou UI. Somente os dois scripts da cadeia proven-profile/autostart e a identidade da versão são substituídos.

## Conferência dos pedidos da 0.3.31

Verificação DOC/SW no código-base da 0.3.31:

- D-Star: `Type=HB`, HBPort 20010, porta do repetidor 20011 e espera da bridge de 12 s presentes — preservado.
- YSF/C4FM: overlay 0.3.31 altera `Reconnect=0` para `Reconnect=1` — preservado; funcionamento RF real ainda exige HW.
- Salvar ≠ Ativar: separação existente — preservada.
- Display Native-First: implementado — preservado.
- UI diferencia `EDITANDO PERFIL` de `ATIVO NO RÁDIO` e contém guia PT/EN/ES — preservado.
- Logo novo: não houve asset novo na diferença 0.3.30→0.3.31; o logo anterior foi preservado. Este hotfix não amplia escopo para branding.

## Testes

- reprodução da ausência de ativação sem snapshot na 0.3.31: PASS SW/VPS;
- reprodução de DMR `state=configured` não aceito pelo snapshot 0.3.31: PASS SW/VPS;
- DMR `configured` aceito somente pelo hotfix: PASS SW/VPS;
- fallback com runtime/perfil coincidentes: PASS SW/VPS;
- fallback bloqueado para rascunho divergente: PASS SW/VPS;
- caminho normal com snapshot existente: PASS SW/VPS;
- D-Star `gateway_active` continua aceito: PASS SW/VPS;
- sintaxe Python/Shell: gate de CI;
- build ARM64, hash de componentes protegidos, `e2fsck`, preflight montado read-only e SHA-256: gate do workflow de release;
- Raspberry Pi + MMDVM real: PENDENTE HW até teste do operador.

## Estado

Classificação: `ALPHA / PARA TESTE FÍSICO`.
CI PASS não será convertido em HW PASS.
