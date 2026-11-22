# PU2PNY-OS 5.13.003 — Checklist de teste físico

**Classificação:** candidata para teste físico após SW/CI aprovado.  
**Placa prioritária:** Orange Pi Zero (imagem específica opizero).  
**Não usar a imagem Raspberry ARM32/ARM64 no Orange Pi.**

## 1. Primeiro boot e AP
- [ ] Gravar a imagem opizero em cartão SD.
- [ ] Ligar a Orange Pi Zero sem Ethernet e sem rede Wi-Fi salva.
- [ ] Confirmar que o AP PU2PNY aparece.
- [ ] Conectar um telefone ao AP.
- [ ] Confirmar que o telefone recebe endereço IPv4 da rede 10.43.0.0/24.
- [ ] Abrir http://10.43.0.1.
- [ ] Abrir http://pu2pny.local quando o telefone/navegador suportar resolução local.
- [ ] Confirmar que o painel/wizard abre sem abrir várias abas.
- [ ] Navegar entre páginas e salvar a primeira rede Wi-Fi.

**Falha crítica:** AP aparece, mas o cliente não recebe IP ou o painel não abre.

## 2. Wi-Fi e persistência
- [ ] Configurar uma rede Wi-Fi principal.
- [ ] Configurar uma segunda rede Wi-Fi.
- [ ] Reiniciar a placa.
- [ ] Confirmar que a rede salva conecta e que o AP só é desativado após associação e IPv4 válidos.
- [ ] Desligar o roteador principal e verificar recuperação pelo AP.
- [ ] Restaurar o roteador e confirmar reconexão sem intervenção.

## 3. Display
- [ ] Confirmar modelo de display e conexão.
- [ ] Em standby, verificar horário e página de estado.
- [ ] Verificar modelo da Orange Pi, CPU, temperatura, RAM e armazenamento.
- [ ] Verificar IP e tipo de uplink.
- [ ] Verificar perfil/firmware/MCU e capacidades MMDVM, quando detectados.
- [ ] Confirmar que campos sem sensor/dado mostram —.
- [ ] Durante RX/TX, confirmar que protocolo, origem/destino e dados RF continuam visíveis.
- [ ] Reiniciar e confirmar que display e perfil voltam corretamente.

## 4. MMDVM e RF
- [ ] Confirmar que o MMDVM é identificado.
- [ ] Confirmar que o MMDVMHost inicia sem erro.
- [ ] Testar DMR simplex RX/TX.
- [ ] Testar D-Star RX/TX.
- [ ] Testar YSF RX/TX.
- [ ] Verificar BER/RSSI somente se fornecidos pelo modem.
- [ ] Confirmar que falha de display/AP não reinicia MMDVMHost nem gateways.
- [ ] Ouvir a voz digital real DMR/D-Star/YSF pelo rádio e comprovar RF→rede e rede→RF.
- [ ] Confirmar se avisos de voz DMR/gateway configurados são transmitidos sem colisão com tráfego real.
- [ ] Não habilitar FM ou reprodução analógica sem hardware/sensor/interface compatíveis.

## 5. Dados a enviar no relatório
- Modelo/revisão da placa Orange Pi.
- Arquitetura/imagem gravada e SHA-256.
- Modelo da MMDVM e firmware identificado.
- Modelo, resolução e conexão do display.
- Resultado do AP, IP recebido e URL testada.
- Fotos/vídeos de standby e RX/TX.
- Resultado após reiniciar.
- Logs/diagnóstico sem senhas, tokens ou credenciais.

**Não publicar credenciais Wi-Fi, tokens, ID privado ou dados de acesso no grupo.**
