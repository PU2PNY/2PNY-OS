# PU2PNY-OS — Feedback físico consolidado em 2026-10-19

**Fonte:** relato direto do usuário + testes reproduzidos por outros usuários (sem logs/modelos anexados nesta rodada).
**Release publicada mais recente ao verificar o GitHub:** `v5.00.000`, ARM32/ARM64, publicada em 2026-10-17.
**Versão exata gravada por todos os participantes:** NÃO VERIFICADA (mensagem menciona “última versão”, sem nome/commit de cada cartão).
**Branch 5.00.001-minimal:** em desenvolvimento, sem nova release validada nesta rodada.

## Baseline protegida

O usuário confirmou que, excluídas as telas, **todo o restante ficou perfeito e funcionando**. Proteger integralmente os módulos atuais de RF/MMDVM, DMR/D-Star/YSF, gateways, rede, Wi-Fi/AP/mDNS, painel, áudio, boot e demais funções existentes. Esse feedback de campo **não substitui** ensaios granulares por protocolo/função; é critério de não regressão.

## Defeitos/ausências

1. **DISPLAY-501 / HW FAIL reportado — geral:** nenhuma variação de display funcionou nos Raspberry Pi testados. Inclui Nextion e outras famílias testadas; a matriz precisa discriminar modelos/barramentos e ainda não possui essa lista exaustiva. Não atribuir causa única sem prova e não marcar HW PASS.
2. **PROTO-501 / FUNÇÃO AUSENTE:** faltam **Público** e **Semi-público** no painel. O contrato desejado é RF por operador, não acesso à administração HTTP:
   - Privado: operador próprio (padrão de nova instalação);
   - Semi-público: próprio + allowlist explícita; lista vazia deve falhar fechada (efetivamente Privado);
   - Público: aberto a operadores válidos, somente habilitação avançada, confirmada e informada, sem confundir com abrir painel web.
   - Em instalação existente, conservar o comportamento atual até mudança explícita e migração segura.
3. **REL-501 / risco 5.00.001:** `ci/build-5.00.001-minimal.sh` não instala explicitamente MMDVM-Display nem NextionDriver; o respectivo validator não os exige. Esse fato no builder **não estabelece** a causa do problema relatado na imagem já publicada, mas é bloqueador de promoção da nova candidata.

## Critérios de aceite

- Comparar código/boot/service/INI da imagem realmente testada com última versão funcional de cada tela, sem ampliar escopo.
- Integrar MMDVM-Display/NextionDriver quando aplicável ao hardware e ao fluxo correto, sob supervisão de serviço e com um único writer por tela; não disputar UART do modem nem gravar HMI/TFT.
- Validar Nextion em modem e UART direta, OLED I2C, HD44780 e demais tipos implementados, por cenários independentes de standby/RX/TX; registrar **modelos reais testados**.
- Garantir que configurador, serviço e runtime do display existam na imagem e estejam compatíveis por arquitetura ARM32/ARM64, CI/SW e depois HW.
- Implementar controle de acesso com `SelfOnly` e listas conforme suporte real por protocolo, sem adivinhar formato de lista, sem vazamento de configuração entre protocolos e com rollback.
- Sem regressão em DMR/YSF/D-Star/áudio/rede; preservar configuração anterior e pontos de retorno.
- Registrar teste SW/CI/VPS separados do HW; não liberar versão “display corrigido” até HW físico comprovar.

## Referências

- [Issue #18 — Displays](https://github.com/PU2PNY/2PNY-OS/issues/18)
- [Issue #19 — Acesso público/semi-público](https://github.com/PU2PNY/2PNY-OS/issues/19)
- [MMDVM-Display oficial](https://github.com/g4klx/MMDVM-Display)
- [ON7LDS NextionDriver oficial](https://github.com/on7lds/NextionDriver)
- [Manual WPSD — operação multiusuário](https://manual.wpsd.radio/advanced/repeater_operation/)

**Estado da execução em 2026-10-19:** feedback/documentação registrados; nenhuma alteração RF/runtime; nenhuma nova imagem gerada ou publicada. DISPLAY HW FAIL; PROTO-501 PENDENTE.
