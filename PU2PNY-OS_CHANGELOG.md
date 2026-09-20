# PU2PNY-OS — CHANGELOG

## 2026-09-19 — início do ciclo corretivo pós-0.3.3-alpha

### Governança
- Criado backup imutável de trabalho `backup/0.3.3-hw-feedback-20260919` a partir de `pu2pny-os-0.3.3-alpha`.
- Criada branch de correção `pu2pny-os-0.3.4-alpha`.
- Instituídos os documentos canônicos START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX e CHANGELOG.
- `docs/PU2PNY-MASTER-PLAN.md` permanece incorporado por referência; nenhum requisito anterior foi removido.

### Feedback físico 0.3.3 registrado, sem afirmar correção
- AP `pu2pny` e acesso inicial por `pu2pny.local`: aprovados no teste reportado e congelados como baseline.
- Handoff para Wi-Fi do roteador: falhou após salvar/reiniciar; AP de recuperação reapareceu.
- UI reportou AP desligado enquanto o SSID permanecia visível.
- Ethernet permitiu acesso por IP DHCP `192.168.100.22`; comportamento de mDNS/retomada ainda precisa correção.
- Hardware/RF básico: reportado como validado.
- Troca para D-Star e YSF: falhou ao reiniciar MMDVMHost com erro MQTT; rollback devolveu o estado anterior e foi aprovado como mecanismo de segurança.
- Ao Vivo: submenu "+" fecha sozinho; duração precisa maior destaque; BER/RSSI indisponíveis devem ser ocultados.
- Nextion: flicker/retângulo vermelho e estado/dados inconsistentes; novo contrato de standby/RX/TX/erro registrado.
- APRS: Notification permission negada; fallback de painel passa a ser obrigatório.
- Expert/rede: registrados requisitos de visualização, explicação, rota/DNS e acesso SSH seguro.
- Nova tela inicial de idioma registrada.
- Alerta de 180 s para **recepção originada em RF** registrado como alerta de atividade, não como corte/TOT.
- VPN automática rejeitada como comportamento padrão; WireGuard/PU2PNY Direct permanece opt-in.

### Estado
Nenhum item acima é marcado como "corrigido" neste changelog. A implementação e validação entram em commits posteriores com referência aos IDs do MASTER_SPEC e casos do TEST_MATRIX.
