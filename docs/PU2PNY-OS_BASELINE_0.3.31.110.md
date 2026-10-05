# PU2PNY-OS — baseline consolidada em 0.3.31.110

Data de consolidação: 2026-10-05.

Este documento é um snapshot de governança. Ele não promove nenhum teste e não altera runtime. Em caso de conflito, prevalecem evidências mais recentes e explicitamente registradas no `PU2PNY-OS_TEST_MATRIX.md` e decisões do `PU2PNY-OS_CHANGELOG.md`.

## Código de referência

- Repositório real observado: `PU2PNY/2PNY-OS`.
- Branch de código mais nova consolidada: `pu2pny-os-0.3.31.110`.
- Commit observado da branch: `1c91b26fd561eb7a727df896f2179fd951b6681a`.
- Mensagem do commit: `0.3.31.110: keep image preflight strictly read-only`.
- A existência da 0.3.31.110 como código mais novo **não** significa aprovação HW.
- A 0.3.30-alpha permanece a última candidata de display com evidência SW/CI/VPS formal completa registrada antes desta consolidação.

## Regra de leitura

`APROVADO` só aparece quando existe evidência correspondente. `PENDENTE`/`NÃO VERIFICADO` não pode ser promovido por compilação, inspeção, CI ou VPS quando o critério exige hardware real.

## Última evidência válida por componente

| Componente | Última evidência confirmada | Nível | Estado consolidado para novas mudanças |
|---|---|---:|---|
| Boot / restauração de perfil | houve correções SW estruturais; o histórico contém falhas HW de restauração automática e não há nova evidência HW posterior suficiente para promover a 0.3.31.110 | SW/HW | **HW NÃO VERIFICADO na 0.3.31.110** |
| AP / primeiro acesso / handoff inicial | fluxo manual via `http://pu2pny.local/` aprovado em HW; onboarding Wi-Fi da 0.3.12 também registrado como PASS HW. Captive portal automático e cenários avançados permaneceram pendentes/falhos em ciclos posteriores | HW | **baseline parcial protegida; regressão HW obrigatória** |
| Ethernet / mDNS / Wi-Fi 2 / failover | contratos SW/VPS posteriores passaram; cenários completos em Raspberry real permaneceram pendentes em registros recentes | SW/VPS/HW | **HW PENDENTE** |
| Detecção MMDVM / bootstrap UART | bootstrap mínimo MMDVM da 0.3.13 registrado como PASS HW; 0.3.31.110 contém recuperação focal de regressões MMDVM sem promover novo HW PASS | HW histórico + SW atual | **baseline HW histórica protegida; reteste 0.3.31.110 PENDENTE** |
| RF geral | aplicação RF funcional e rollback possuem evidência HW histórica | HW | **baseline protegida; reteste por imagem obrigatório** |
| DMR simplex | teste físico do mantenedor em 2026-09-22 declarou TX/RX simplex aprovado; registros posteriores também tratam DMR simplex como baseline obrigatória | HW | **APROVADO como baseline; não alterar para corrigir duplex** |
| DMR troca TG/módulo | 0.3.24: troca de módulo/TG pelo rádio aprovada pelo mantenedor | HW | **APROVADO como baseline** |
| DMR aviso de voz após conexão | 0.3.24: aprovado pelo mantenedor | HW | **APROVADO como baseline** |
| DMR duplex | matriz posterior mantém TX/RX/áudio/timeout/TS/CC como HW pendente; houve problema real reportado em duplex | HW | **NÃO APROVADO / HW PENDENTE** |
| D-Star simplex | teste físico do mantenedor em 2026-09-22 declarou D-Star simplex aprovado; mudanças posteriores não podem reescrever essa baseline sem necessidade direta | HW | **APROVADO como baseline; reteste da imagem atual PENDENTE** |
| D-Star comandos/reflectores avançados | diversos casos I/E/U/L/link e rede↔RF permaneceram pendentes em matrizes posteriores | SW/HW | **HW PENDENTE** |
| YSF/C4FM simplex | TEST-HW-0325-Y1 registra YSF/C4FM simplex da 0.3.24 aprovado pelo mantenedor | HW | **APROVADO como baseline; reteste da imagem atual PENDENTE** |
| Wires-X / recursos YSF avançados | contratos/helpers preservados em SW/VPS; teste real de lista/comando/troca/refletor permaneceu pendente | SW/VPS/HW | **HW PENDENTE** |
| P25 / NXDN / POCSAG | há validações estruturais parciais; não existe evidência suficiente para declarar operação RF completa | SW | **HW PENDENTE** |
| APRS mensagens | 0.3.27 preservou daemon sem beacon/localização e confirmou mensagens/ACK/REJ/outbox/retry em SW/VPS; mensagem real APRS-IS permaneceu pendente | SW/VPS/HW | **SW/VPS APROVADO; HW/NET PENDENTE** |
| PU2PNY Direct / Relay | integração CI e relay externo em VPS passaram; chamada completa entre dois hotspots reais/CGNAT permaneceu pendente | SW/VPS/HW | **SW/VPS APROVADO; HW PENDENTE** |
| Ao Vivo / Event Bus | vários contratos têm PASS estrutural; há feedbacks HW/browser históricos e nenhuma evidência geral que autorize declarar o conjunto completo aprovado | SW/HW | **PARCIAL / regressão obrigatória** |
| Nextion — atualização incremental | 0.3.30: `cls` somente em transição real, frames MQTT limitados, parser `comok` e writer único passaram SW/VPS | SW/VPS | **APROVADO SW/VPS** |
| Nextion — hardware real | 0.3.30 manteve boot/standby/RX/TX/TOT, COMOK/modelo real e ausência de flicker como HW pendente | HW | **HW PENDENTE** |
| OLED/LCD | comportamento existente preservado por código; 0.3.30 ainda exige hardware correspondente | SW/HW | **HW PENDENTE** |
| Idiomas PT/EN/ES | 0.3.24 possui gate de fonte/staging PASS; histórico registra mistura real em EN/PT e o gate completo `TEST-UI-023-CI` estava pendente | SW/HW | **SW PARCIAL; HW/browser NÃO APROVADO como conjunto completo** |
| Update / rollback | existem staging/checksum/rollback em evolução e a 0.3.31.110 tornou o preflight de imagem estritamente read-only | SW | **novo modelo transacional ainda precisa validação SW/VPS/HW** |
| Backup / diagnóstico | relatório sanitizado possui evidência SW/CI/VPS; backup integral deve ser tratado como material sensível e separado do relatório de suporte | SW/VPS | **baseline de segurança; ampliar sem expor segredos** |
| Release ARM64 | 0.3.30: source → staged → ARM64 → SHA → preflight → validador → publish PASS, run `36341170897` | SW/CI | **APROVADO SW/CI para 0.3.30; 0.3.31.110 não é automaticamente uma release HW** |

## Baselines protegidas obrigatórias

1. DMR simplex TX/RX aprovado em HW.
2. D-Star simplex aprovado em HW.
3. YSF/C4FM simplex aprovado em HW na 0.3.24.
4. Troca DMR TG/módulo e aviso de voz DMR aprovados na 0.3.24.
5. Fluxo manual de primeiro acesso aprovado via `pu2pny.local`.
6. Rollback transacional já comprovado não pode ser removido para simplificar uma correção.
7. Display 0.3.30 SW/VPS é baseline de software; não converter para HW PASS sem Nextion/OLED/LCD reais.

## Bloqueios de promoção

- DMR duplex não pode alterar a baseline simplex.
- Display não pode ser marcado HW PASS sem hardware real.
- VPS/CI não substitui RF, UART/GPIO, BER/RSSI, Nextion físico ou chamada Direct entre hotspots reais.
- 0.3.31.110 deve ser tratada como estado mais novo de código, com reteste físico pendente dos componentes que exigem HW.

## REL-026 — sincronização canônica 0.3.31.110

Os cinco documentos canônicos devem apontar para este snapshot e distinguir claramente: estado mais novo do código, última evidência por nível e baselines aprovadas. Nenhuma sincronização documental autoriza alteração funcional.

**Critério de aceite:** START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX e CHANGELOG fazem referência explícita à 0.3.31.110 e não promovem SW/VPS para HW.

**Validação mínima:** DOC. Alterações futuras que usem esta baseline herdam o nível de validação exigido pela área afetada.
