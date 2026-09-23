# Display 0.3.23-alpha: teste físico sem terminal

**Estado:** [imagem 0.3.23-alpha](https://github.com/PU2PNY/2PNY-OS/releases/tag/v0.3.23-alpha) publicada após [CI ARM64 PASS](https://github.com/PU2PNY/2PNY-OS/actions/runs/35832041581). O visual da Nextion física só recebe HW PASS após fotografias e teste no hat CA6JAU.

## O que mudou

As duas fotos da 0.3.22 mostram dados RX antigos (ID, cidade, medidor) sobre a tela de espera. O renderer anterior enviava quadros acima de 252 bytes via MQTT ao MMDVMHost; seu buffer serial retardado podia ser substituído por outro quadro. Agora cada envio contém comandos Nextion completos e tem até 240 bytes; os envios são espaçados conforme a UART. Cada quadro inicia com limpeza completa. Standby, RX e TX usam áreas separadas em 320×240; há ajuste proporcional para 480×320 e 800×480. Textos do operador e localidade continuam somente quando disponíveis. O cabeçalho TX usa verde, RX usa vermelho; sem medição física, BER/RSSI aparecem como `—`.

## Verificação no aparelho

1. Após ligar, a página azul **MODEL 10 / ON7LDS** pode aparecer: ela vem do HMI já gravado na Nextion e não foi apagada pela imagem Linux.
2. Após o serviço de rádio subir: standby deve mostrar PU2PNY-OS, protocolo, indicativo, relógio, espera RF e estado de rede, com texto sem cruzar outro bloco. Sem Internet confirmada não deve afirmar “online”.
3. Receber DMR: RX vermelho, indicativo legível, destino TG sem repetição `TG TG`, nome/cidade somente se houver fonte real. Finalizada a portadora, nenhum ID ou medidor anterior pode permanecer sobre standby.
4. Transmitir: TX verde e cronômetro. Na reta final do TOT, os últimos dez segundos ocupam a tela inteira. Confirme que o tempo mostrado coincide com o evento real.
5. Repetir D-Star simplex e YSF simplex que funcionavam antes; observar que o painel e o áudio continuam funcionais. DMR simplex também deve transmitir e receber com áudio.

Se a tela ainda se misturar, fotografar exatamente durante standby e após um RX, anotando modo, horário e tamanho/modelo da Nextion. Não alterar manualmente UART, HMI ou `.tft`. Para retornar à tela anterior, regravar a [imagem 0.3.22-alpha](https://github.com/PU2PNY/2PNY-OS/releases/tag/v0.3.22-alpha).

**Limite de entrega:** sem compilar e instalar um HMI próprio na tela, a página ON7LDS exibida antes do Linux iniciar não pode ser trocada apenas com o renderer Linux. O HMI PD0DIB atual tem licença com condições próprias; não foi redistribuído, modificado ou gravado automaticamente.
