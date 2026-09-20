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

## 2026-09-19 — implementação 0.3.4-alpha

### Correções implementadas em código — validação HW ainda pendente
- **NET-002:** perfil Wi-Fi staged agora preserva a flag hidden conforme origem da rede, recarrega o perfil, verifica SSID/senha persistidos antes de reiniciar e, no boot, confirma associação real + IPv4 antes de considerar sucesso.
- **NET-003:** API passa a consultar o runtime real do hostapd/PID antes do estado lógico do controlador.
- **NET-004/006:** network-core publica tipo de uplink/IP; diagnóstico leve passa a expor interface, gateway, hops e DNS efetivos.
- **NET-007:** Cloudflare/Google/OpenDNS podem ser comparados por teste real e cacheado; nenhuma troca é automática.
- **PROTO-005/006:** criado preflight MQTT local e dependência explícita de mosquitto antes do MMDVMHost; troca não-DMR aborta antes de tocar RF se o broker não estiver acessível; rollback agora reinicia explicitamente o MMDVMHost anterior antes dos gateways.
- **LIVE-002/003/004/005/010:** estado do submenu expansível é preservado; BER/RSSI somem sem telemetria; duração ganha destaque; atividade originada em RF pulsa brevemente e mostra aviso após 180 s; tráfego vindo da Internet não usa esse aviso.
- **WIZ-001/UI-001:** primeira visita ganha tela de idioma PT/EN/ES; páginas operacionais ganham rodapé com versão instalada.
- **UI-003:** Expert passa a priorizar cards/estado visual e recolhe JSON em detalhes técnicos.
- **APRS-001:** alerta interno permanece funcional quando Notification API é negada ou exige contexto seguro.
- **DISPLAY-002..005:** overlay de build preserva o driver multi-display existente, remove limpeza total repetitiva da Nextion, atualiza por cadência controlada e acrescenta hora/uplink/IP/estado RF-rede sem sobrescrever HMI/TFT.
- **REL-003:** adicionados prepare/validator 0.3.4; build ARM64/CI ainda precisa executar antes de qualquer divulgação de imagem.

### Evidência
Neste ponto os itens acima estão **implementados em código**. Não são HW PASS até nova instalação/teste no Raspberry Pi + MMDVM + Nextion. DMR permanece baseline de regressão obrigatória.
