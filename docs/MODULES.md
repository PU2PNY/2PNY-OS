# 2PNY — arquitetura modular

O 2PNY deve evoluir por módulos independentes, com dependências explícitas e sem transformar o painel em um monólito.

## Módulos

1. **Core** — configuração, estado global, eventos, versionamento e API local.
2. **Provisioning** — primeiro acesso, indicativo, DMR ID, senha e transição do 2PNY-SETUP para a rede normal.
3. **Network** — Ethernet, Wi-Fi, mDNS, DHCP, fallback direto, DNS/NTP/Internet, failover e reconexão.
4. **Hardware** — Raspberry Pi, GPIO, serial, I2C, USB e perfis de placas.
5. **MMDVM/RF** — detecção ativa, firmware, simplex/duplex, frequências, offsets, BER e calibração.
6. **Protocols** — DMR, D-Star, YSF/C4FM e, depois, P25/NXDN/POCSAG/APRS/M17 conforme suporte real.
7. **Networks** — XLX, BrandMeister, TGIF, FreeDMR, DMR+/IPSC2, Phoenix, HBLink e perfis customizados.
8. **Display** — Nextion, OLED SSD1306, HD44780, TFT serial/LCDproc e fallback sem display.
9. **UI** — shell visual, temas, acessibilidade, dashboard, wizard, navegação e estado em tempo real.
10. **Diagnostics** — 2PNY Doctor, logs, health, testes de rede, hardware e serviços.
11. **Updates** — atualização segura, rollback, imagem A/B no futuro e migração de configuração.

## Regras de arquitetura

- O Core não deve depender da UI.
- A UI consome estado por API/eventos; não deve raspar logs.
- Cada módulo deve poder informar `unknown`, `detecting`, `ready`, `warning` ou `error`.
- Nenhum módulo deve inventar hardware ou estado que não conseguiu confirmar.
- Falha em um módulo não deve derrubar o painel inteiro.
- O fluxo normal deve funcionar sem terminal.
- Configuração persistente fica separada do sistema base para facilitar atualização e rollback.
- O painel deve funcionar localmente sem Internet e sem fontes, scripts ou CDNs externos.

## Ordem atual de implementação

1. Core + Provisioning + Network — **validado fisicamente na Pi 4**.
2. UI profissional + fluxo contínuo do primeiro acesso.
3. Hardware/MMDVM + Display/Nextion.
4. RF/calibração.
5. DMR/D-Star/YSF e redes.
6. Diagnóstico, histórico, atualizações e recursos avançados.
