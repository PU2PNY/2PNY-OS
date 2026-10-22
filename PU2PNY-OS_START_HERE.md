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
