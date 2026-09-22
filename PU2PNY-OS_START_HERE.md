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

## Ciclo ativo — 0.3.20-alpha — 2026-09-22

- Branch: `pu2pny-os-0.3.20-alpha`.
- Base: `pu2pny-os-0.3.19-alpha`.
- Rollback pré-ciclo: `backup/0.3.19-pre-0.3.20-20260922`.
- Backup pré-organização documental: `backup/0.3.20-pre-doc-governance-20260922`.
- DMR simplex e YSF/C4FM simplex permanecem baseline protegidos.
- D-Star: novas configurações usam módulo local/RPT1 B, selecionável A–D; módulo remoto do refletor é independente; comando de rádio só promove estado efetivo após confirmação real do gateway.
- 0.3.20 não pode ser divulgado como HW PASS sem os testes físicos pendentes.
