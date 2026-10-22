# Display — única regra ativa / baseline aprovado

## Estado confirmado
Em 22/10/2026, Dario informou sobre a versão 5.00.002: **“a tela funcionou perfeito”**, identificando o modo **NextionDriver ON7LDS**. Estado: **HW PASS — funcionamento geral da tela no conjunto testado**. Esta é a referência obrigatória das próximas versões.

## Implementação protegida
MMDVM-Display oficial externo → PTY → NextionDriver ON7LDS → UDP loopback exclusivo do display → MQTT `host/display-in` → MMDVM-Host → modem/Nextion. Retorno: `host/display-out` → bridge → NextionDriver. O MMDVM-Host continua dono exclusivo da UART do modem. A bridge não altera configuração RF e os metadados usam whitelist sem segredos.

Preservar o código e dependências da imagem v5.00.002, commit fonte `56a0b6a4a97fee4cd35314e0f3943918a32fbc2d`. Preservar a configuração efetivamente aprovada. Não forçar layout, porta ou baud novos: L3/L3 HS, arquitetura e modelo não foram especificados nesta aprovação.

## Regras permanentes
1. Funcionando e aprovado = preservar. Não refatorar, substituir ou renomear o caminho aprovado por conveniência.
2. Não reintroduzir renderer próprio/PU2PNY Moderno nem renderer Nextion embutido inexistente no host MQTT. Não executar writers concorrentes ou fallback automático para modos não aprovados.
3. Não gravar HMI/TFT/firmware automaticamente; manter o hardening do NextionDriver. Não executar comandos de shell recebidos da tela.
4. Antes de qualquer correção autorizada: conferir hashes do baseline, investigar a regressão, limitar o diff ao defeito, preservar rollback, executar SW/CI/VPS aplicáveis e novo HW. Build/VPS não substituem HW.
5. Aprovação não se estende automaticamente a G4KLX, OLED/LCD, outros modelos, ARM32/ARM64, toque, reboot ou cada campo de telemetria. Registrar apenas o que foi relatado ou comprovado.
6. Não remover drivers/arquivos por suposta limpeza antes de verificar suas dependências, inclusive fallback usado por OLED/LCD existentes. Não mexer no runtime aprovado nesta atualização de regras.
7. Informações conflitantes de versões anteriores são histórico e não devem orientar novas implementações. Não reaplicar patches históricos sobre este baseline. Não apagar evidências/rollback para ocultar falhas anteriores.

## Evidência e proveniência
- Imagens e checksums: https://github.com/PU2PNY/2PNY-OS/releases/tag/v5.00.002
- Fonte: https://github.com/PU2PNY/2PNY-OS/commit/56a0b6a4a97fee4cd35314e0f3943918a32fbc2d
- CI SW/estrutura: https://github.com/PU2PNY/2PNY-OS/actions/runs/39775950167
- Relato físico do usuário nesta conversa em 22/10/2026. Não há logs/fotos adicionais anexados a esta aprovação.
- `PU2PNY-OS_DISPLAY_BASELINE.json`: hashes dos fontes e imagens para comparação futura.
