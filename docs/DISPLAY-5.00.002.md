# PU2PNY-OS 5.00.002 — somente display

Base: v5.00.001 publicada, não o head posterior que falhou na publicação.
ARM64 base SHA: 293e18cf6ec62a72a5f1f02a1f651c9ea88702aed2db6862409f325f7dcf6a1e.
ARM32 base SHA: a7f1ed85e667fbb169ae52c51327af5f4fca373d7af891eeb7352cb6798b292d.

## Causa confirmada DOC/binário
O host 590c531391dfd3146073afbc3956f70d42c62a46 publica eventos MQTT e recebe bytes em host/display-in. Não tem renderer Nextion. A imagem 5.00.001 contém aplicador histórico que desativa MMDVM-Display e grava Nextion no INI do rádio; esse host não consome esse renderer. Strings do binário e código upstream confirmam a incompatibilidade. Isso explica ausência de renderização nesse caminho; outras causas físicas continuam possíveis.

## Correção e escopo
MMDVM-Display oficial 96a0705d818c4234960a61dd2837e32f9450f811 já instalado passa a ser o renderer. G4KLX/L2 enviam bytes pela bridge MQTT do host. L3/L3 HS usam renderer layout 3 → PTY → NextionDriver com layout 3/4 → UDP loopback dedicado → MQTT host/display-in. Retorno usa host/display-out. Não depende de reconfigurar Transparent Data do motor RF. Metadados de identidade/frequência vêm do INI real com whitelist; IP vem do kernel. Nenhum segredo enviado a tópicos. Serviço de display não reinicia o rádio. Desativação para todos os writers; rollback de arquivos e serviços de display. OLED/LCD diretos preservam caminho anterior: não declarar paridade integral Pi-Star sem drivers compilados e teste do modelo.

## Fontes oficiais
- https://github.com/g4klx/MMDVM-Host
- https://github.com/g4klx/MMDVM-Display/tree/96a0705d818c4234960a61dd2837e32f9450f811
- https://github.com/on7lds/NextionDriver/blob/master/README-modemdisplays.md

## Teste físico sem terminal
1. Gravar a imagem da arquitetura adequada e configurar como na base.
2. Em Display, habilitar e escolher o layout do HMI já instalado. Para tela que mostra USE NextionDriver/ON7LDS, começar por ON7LDS L3; não escolher G4KLX apenas pelo tamanho da tela.
3. Salvar; verificar se sai do splash e mostra o indicativo.
4. Transmitir brevemente no rádio e receber uma chamada da rede. Conferir indicativo, destino/TG e slot quando aplicáveis; ausência de telemetria não deve virar valor inventado.
5. Reiniciar e conferir persistência; desativar display e conferir que o rádio continua operando.
6. Relatar versão, arquitetura, layout escolhido, foto da tela e diagnóstico Display se falhar.

COMOK identifica hardware, não HMI. SW e CI não são HW PASS. Não gravar HMI/TFT nem firmware MMDVM neste ciclo. Rollback: imagem v5.00.001 anterior preservada.
