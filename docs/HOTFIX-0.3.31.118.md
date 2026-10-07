# PU2PNY-OS 0.3.31.118 — Nextion ON7LDS virtual-port hotfix

## Origem
Teste físico reportado em 2026-10-07 na imagem 0.3.31.117.

## Evidência HW
- MMDVM detectada em `/dev/serial0`, baud 115200; MMDVMHost e DMRGateway permaneceram ativos.
- Nextion identificada por COMOK como `NX3224T024_011R`, 320x240, firmware 163, 4 MiB, `physical_confirmed=true`.
- O HMI físico permaneceu na tela inicial `USE NextionDriver - ON7LDS`.
- Ao selecionar `Pi-Star/WPSD avançado · ON7LDS NextionDriver`, o painel informou que não foi possível aplicar e restaurou a configuração anterior.
- Após rollback, runtime voltou para `mmdvmhost-native`, preservando o rádio.

Classificação: **DISPLAY-025 HW FAIL na 0.3.31.117**. O rollback foi efetivo e o caminho DMR observado permaneceu ativo; isso não autoriza promover outros casos HW não testados.

## Causa raiz confirmada
O NextionDriver upstream pinado define o link PTY como `/dev/ttyNextionDriver`. A 0.3.31.117 executa o driver como `User=mmdvm` e espera a porta em `/run/2pny-nextiondriver/ttyNextionDriver`. O usuário não privilegiado não deve criar links em `/dev`, e o apply espera um caminho diferente do hard-coded pelo binário. Assim o serviço não disponibiliza a porta virtual esperada e o apply executa rollback.

## DISPLAY-026 — Porta virtual ON7LDS não privilegiada
O NextionDriver endurecido deve ser compilado com `NEXTIONDRIVERLINK=/run/2pny-nextiondriver/ttyNextionDriver`, dentro do `RuntimeDirectory=2pny-nextiondriver` pertencente ao usuário do serviço. É proibido corrigir o problema elevando o NextionDriver a root ou liberando escrita geral em `/dev`.

Critério de aceite SW/CI:
1. source upstream continua pinado na mesma revisão usada pela 0.3.31.117;
2. hardening HMI→shell/download/flash da 0.3.31.117 permanece;
3. binário ARM64 contém `/run/2pny-nextiondriver/ttyNextionDriver` e não contém `/dev/ttyNextionDriver`;
4. unit continua `User=mmdvm`, `NoNewPrivileges=yes` e `RuntimeDirectory=2pny-nextiondriver`;
5. `2pny-display-apply` continua consumindo o mesmo caminho em `/run`;
6. MMDVMHost, DMR/D-Star/YSF, helpers RF/protocolo, rede, wizard e UI permanecem byte-idênticos à imagem 0.3.31.117;
7. imagem ARM64 passa montagem read-only, `xz -t` e SHA-256.

Critério HW: selecionar `on7lds-compatible` no equipamento real e comprovar que a tela sai do splash, mostra standby e reage a RX/TX sem regressão do MMDVMHost/DMR. Continua **PENDENTE HW** até novo teste do operador.

## Rollback
Ponto de retorno: branch `backup/0.3.31.117-nextion-hw-fail-20261007`, commit `088ba5901bfc918503430df658f1a7b5728ef64e`.
