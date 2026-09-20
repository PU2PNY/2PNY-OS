# PU2PNY-OS — START HERE

**Documento obrigatório de entrada do projeto.**

Antes de analisar, corrigir, programar, publicar, gerar imagem, alterar GitHub, CI/CD, servidor, RF, rede, display ou documentação do PU2PNY-OS, leia nesta ordem:

1. `PU2PNY-OS_START_HERE.md`
2. `PU2PNY-OS_MASTER_SPEC.md`
3. `PU2PNY-OS_RELEASE_STATUS.md`
4. `PU2PNY-OS_TEST_MATRIX.md`
5. `PU2PNY-OS_CHANGELOG.md`
6. `docs/PU2PNY-MASTER-PLAN.md` para o histórico consolidado anterior
7. o código da branch efetivamente em trabalho

## Fontes de verdade

- **MASTER_SPEC**: requisitos funcionais e técnicos aprovados.
- **RELEASE_STATUS**: estado real da release e seus bloqueadores.
- **TEST_MATRIX**: o que foi realmente testado e em qual nível.
- **Código/repositório**: implementação existente.
- **CHANGELOG**: decisões e alterações registradas.
- `docs/PU2PNY-MASTER-PLAN.md` permanece incorporado por referência. Nada nele é removido silenciosamente; divergências futuras devem ser resolvidas explicitamente no MASTER_SPEC por ID de requisito.

## Regras invariáveis

- PU2PNY-OS é sistema próprio; não é fork de Pi-Star nem WPSD.
- Não reiniciar o projeto do zero.
- Não remover requisito aprovado silenciosamente.
- DMR TX/RX fisicamente aprovado em versões anteriores é baseline obrigatória de regressão.
- Antes de alterar RF, modem, baud, offsets, MMDVMHost, gateways, HMI/TFT, rede ou boot: registrar estado, criar rollback e limitar o escopo.
- Mudança que falha deve voltar ao último estado comprovadamente funcional quando possível.
- Não chamar de "testado" algo apenas compilado ou inspecionado.
- Não inventar BER, RSSI, indicativos, rotas, gateways, progresso ou estado.
- Valor sem fonte confiável deve ser `—`/indisponível.
- Preservar CPU, RAM e cartão SD; evitar polling agressivo e logs persistentes desnecessários.
- Usuário final não deve depender de terminal para operação normal.
- Uma nova decisão só vira requisito permanente depois de entrar no MASTER_SPEC, CHANGELOG, RELEASE_STATUS quando aplicável e TEST_MATRIX.

## Níveis de validação

- **DOC** — conferido em documentação/código.
- **SW** — testado em software/CI.
- **VPS** — testado em ambiente Linux/VPS.
- **HW** — testado em Raspberry Pi + MMDVM/display/hardware real.
- **PROD** — aprovado em produção/uso real.

## Ordem de implementação

Base/Boot → Rede/Wizard → Hardware → RF/MMDVM → DMR → D-Star → YSF/C4FM → P25/NXDN/POCSAG → Runtime/Event Bus → Ao Vivo → Painel/API → Displays/Nextion → APRS/DPRS → QRZ → PU2PNY Direct/P2P/CGNAT → Update/Backup/Rollback → Segurança/Hardening → testes físicos completos → RC → Produção.

## Gate de release

Antes de divulgar imagem: requisito → implementação → teste → resultado → regressão → pendência.

Não liberar como completa com requisito crítico ausente, regressão conhecida de DMR/RF/rede/wizard, build ARM64 incompleto, imagem sem validação estrutural/SHA-256 ou afirmação de hardware sem teste HW.
