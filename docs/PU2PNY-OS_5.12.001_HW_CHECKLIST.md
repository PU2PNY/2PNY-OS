# PU2PNY-OS 5.12.001 P1 — Plano de homologação física

> **Classificação confirmada em 14/11/2026:** ALPHA, candidata para teste físico. [Imagens 5.12.001 P1 publicadas](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.001-p1) com quatro SHA-256 e [CI 6/6 PASS](https://github.com/PU2PNY/2PNY-OS/actions/runs/43597269377). **Não é produção.** O teste de build NÃO constitui evidência de RF, Nextion, Orange/Nano AP ou transcoding.

## Escopo limitado do P1

- **UI-NAV-5121:** links HTML de navegação presentes independentemente do carregamento de JavaScript. O menu JS existente continua dono do estado ativo. A causa-raiz do desaparecimento no hardware e o carregamento da API **ainda exigem diagnóstico**.
- **CLOCK-5121:** remove apenas o CSS ocultador da seção Relógio no Sistema. Backend com detecção de fuso IANA do navegador e NTP já existia; **fuso efetivo não homologado**, e a 5.12.000 de teste mostrou `Europe/London` apesar do usuário estar no Brasil.
- **DISPLAY-5121:** OLED SSD1306/SH1106 (128×32 e 128×64) e LCD HD44780 recebem páginas específicas da atividade MMDVM e dados OS, sem alterar MMDVMHost, UART ou driver ON7LDS.
- **EXPERT-5121:** relatório `.txt` limitado a 160.000 caracteres com comandos adicionais somente de leitura sobre HTTP, gateway, IP e mDNS; revisar antes do compartilhamento, pois o mascaramento automático não substitui inspeção humana.
- **BOOT/NET 512 P0:** mantidos como estavam nas quatro imagens base publicadas.

## Baseline protegido

NextionDriver ON7LDS de 5.00.002 foi aprovado em hardware. Nenhum novo writer Nextion, HMI/TFT flash, porta, baud, perfil ou script RF autorizado em P1. Arquivos MMDVMHost, RF, protocolos, scripts de rede, kernel/bootloader têm de ser idênticos à imagem 5.12.000 da placa; arquivos modificados em P1 devem manter cópia `.pre-5.12.1`.

**Não afirmar telemetria extra visível no Nextion** sem verificar HMI/layout e compatibilidade de campos oficiais. Issue #28.

## Checklist por testador — sem terminal

1. **Usar cartão microSD separado**, manter cartão que funcionou. Anotar placa exata, RAM, modelo do modem MMDVM, modo simplex/duplex, tipo de tela e versão.
2. Depois de gravar a imagem, verificar **SSID AP**, associação e endereço IP recebido do hotspot. No AP, abrir primeiro `http://10.43.0.1/` e depois o nome mDNS `http://pu2pny32.local/` (ARM32) ou `http://pu2pny64.local/` (ARM64), onde suportado. **Não declarar conectado apenas pela presença do SSID**.
3. Abrir **Ao Vivo, Internet, Protocolos, Display, Sistema e Expert**. Menu deve permanecer visível inclusive se uma API não responder. Não enviar novas configurações de RF repetidas por `Failed to fetch`.
4. **Sistema:** conferir hora local, fuso efetivo e NTP. Ajuste automático usa o fuso IANA informado pelo navegador e NTP para a hora, não estimativa baseada em IP público; se não aplicar, coletar relatório, não presumir resultado.
5. **Expert → Rodar tudo → Baixar .txt**. Se possível, também executar separadamente **Painel HTTP e endereços locais**, **Estado RF e gateways por protocolo** e **Relógio e fuso**. Não compartilhar chaves/senhas/identificadores privados inadvertidamente.
6. **Display OLED 128×32/64:** validar PU2PNY-OS, indicativo configurado, protocolo, IP, temperatura/disco no standby; durante transmissão recebida, indicativo de origem, TG/slot/duração e BER/RSSI apenas quando coletados. Não inventar valores.
7. **HD44780 16×2/20×4:** conferir páginas de 4 s, indicativo/protocolo/IP/CPU/temp e transmissão real; a tela não pode provocar restart de MMDVMHost.
8. **Nextion ON7LDS:** verificar somente preservação da função aprovada; extra CPU/disco/IP não é HW PASS e não houve flash/alteração de HMI. Informar campos faltantes no Issue #28.
9. **DMR, D-Star e YSF:** checar troca de perfil, TX/RX real e confirmação de gateway/refletor. DMRGateway falhou no relatório Pi4 em 14/11/2026; não considerar corrigido sem evidência física.
10. **Orange Pi Zero H2+:** AP aparecer sem abrir painel = falha. Confirmar se o navegador chega ao IP `10.43.0.1`, se há IPv4 na interface e se o HTML abre. Enviar foto da URL e resultado dos campos; a nova imagem **não tem correção HW confirmada** do defeito.
11. **NanoPi NEO H3:** versão original usa **Ethernet**; sem Wi-Fi USB compatível com AP não deve aparecer AP. Conectar por cabo ao roteador, achar IP no painel do roteador e abrir `http://<IP-da-placa>/`. Se possível verificar display I2C real.
12. **Raspberry Pi 4:** se houver subtensão `vcgencmd get_throttled 0x50005` e `Undervoltage detected!`, corrigir alimentação com fonte adequada e cabo antes de classificar RF como estável.

## Critérios objetivos para aceitar correções

| Item | Mínimo de evidência | Status inicial |
|---|---|---|
| Integridade das imagens | CI, `xz -t`, `sha256sum -c`, arquivos >0, commit/tag | PENDENTE DE PUBLICAÇÃO |
| Navegação web | Menu presente após cold boot, todas as páginas e link HTTP ativo | HW NÃO VERIFICADO |
| OLED/LCD | Foto/vídeo de standby e TX/RX reais por display/placa | SW PASS / HW PENDENTE |
| NextionDriver ON7LDS | Campo real exibido sem modificar driver ou HMI | Baseline original HW PASS; novos campos NÃO VERIFICADOS |
| DMR/YSF/D-Star | TX e RX reais com gateway/refletor confirmado | REGRESSÃO REPORTADA / PENDENTE |
| Orange AP e HTTP | IP, associação, GET `/healthz` e interface web completa | REGRESSÃO REPORTADA |
| NanoPi Ethernet e display | DHCP IPv4, painel e RF/UI reais | HW NÃO VERIFICADO |
| Fuso e NTP | IANA efetivo correto, NTP sincronizado e persistência | PENDENTE (5.12 original em Europe/London) |
| AMBE/transcoding | Backend real, duas direções, gravação áudio e testes RF | NÃO IMPLEMENTADO/COMPROVADO |
| Direct CGNAT | Duas redes CGNAT reais, relay, 2+ participantes, voz RF | NÃO IMPLEMENTADO/COMPROVADO |

## Bloqueadores rastreados

- #23 — falhas P0/5.11 e provas físicas.
- #24 — DMR/YSF/D-Star `Failed to fetch`.
- #25 — desaparecimento de menu/Ao Vivo sem dados.
- #26 — Direct P2P privado e grupo sob CGNAT com ICE/STUN e relay autenticado.
- #27 — codecs e backend real de transcoding.
- #28 — metadados extras NextionDriver ON7LDS.
- #29 — Orange Pi AP sem painel e NanoPi Ethernet/compatibilidade.\n- #30 — divergência de versão: badge do backend 5.11.000 vs imagem 5.12.001.

## Fontes upstream

- [WPSD — configuração oficial de displays](https://manual.wpsd.radio/initial_startup/)
- [NextionDriver ON7LDS oficial](https://github.com/on7lds/NextionDriver)
- [Opções do NextionDriver](https://github.com/on7lds/NextionDriver/blob/master/README-options.md)
- [MMDVM-Display upstream](https://github.com/g4klx/MMDVM-Display)
- [Raspberry Pi — alimentação](https://www.raspberrypi.com/documentation/hardware/raspberrypi/power.html)
- [TURN — RFC 8656](https://www.rfc-editor.org/rfc/rfc8656.html)
