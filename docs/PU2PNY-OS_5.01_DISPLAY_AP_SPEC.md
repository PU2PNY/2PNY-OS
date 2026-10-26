# PU2PNY-OS v5.01 — AP diferenciado e recuperação de displays
Estado: especificação autorizada, implementação pendente de validação.

## Ordem obrigatória
1. AP ARM32: **pu2pny-32**; AP ARM64: **pu2pny-64**. Preservar senha, UUID/connection ID, IPv4 compartilhado, recovery AP, DNS/mDNS, rede salva e DHCP. Validar SSID real do perfil NM e processo que recria o AP antes de publicar.
2. Verificar alimentação real (throttled/undervoltage em Raspberry quando possível; distinguir energia de Wi-Fi power-save, USB autosuspend e tempo ocioso do modem). Não forçar alterações globais sem evidência.
3. Nextion ON7LDS: preservar a baseline HW v5.00.002; detectar modem vs display sem inferir HMI; garantir evento MQTT MMDVMHost → MMDVM-Display → NextionDriver e informações externas validadas, UART com dono único; distinguir serviço ativo de RX/TX exibido; nada de auto-flash.
4. OLED, HD44780, LCDproc e TFT apenas onde hardware real suportar; ajustar fonte/linhas conforme dimensão real e limites do driver/HMI; não inventar resolução. Retestar layout sem corte para standby/RX/TX.
5. Testes regressão DMR/D-Star/YSF, AP/STA/Ethernet e fallback; ARM32/ARM64 separadamente; SW/VPS não é HW.
6. Identidade de apresentação: **PU2PNY-OS v5.01**. Não renomear repositório nem alterar título do navegador canônico **PU2PNY-OS** sem ordem explícita.

## Restrições
Mudanças por etapas isoladas e reversíveis. Sem alteração arbitrária RF, baud, power save ou MMDVMHost. Nunca prometer suporte universal a telas não identificadas. Sem HW: não verificado. Em caso de incompatibilidade física ou HMI com dimensões fixas, expor limitação concreta.
