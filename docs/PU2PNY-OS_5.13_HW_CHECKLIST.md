# PU2PNY-OS 5.13.002 · Checklist para teste físico

Base 5.12.002 P2. Use um cartão separado e guarde o cartão da versão anterior para voltar rapidamente. A integridade das imagens e os dados de build são verificados pelo CI. A aprovação de hardware depende dos testes abaixo.

| Teste | Como conferir na placa |
|---|---|
| Primeiro acesso | Conecte ao AP de configuração e abra `http://10.43.0.1/`. Repita com Ethernet conectada e desconectada. Confirme que o assistente abre e que a conexão permanece estável. Registre se o sistema operacional abriu uma segunda janela. |
| Orange Pi Zero H2+ / NanoPi NEO H3 | Abra o painel pelo IP do AP e pelo IPv4 recebido do roteador depois de conectado à rede. No NanoPi sem Wi‑Fi integrado, use cabo de rede ou adaptador Wi‑Fi que suporte AP. |
| Segunda rede Wi-Fi | Em Internet, salve uma rede diferente como backup. O painel deve confirmar o perfil sem trocar o IP. Depois desligue a rede principal e confirme que a reserva associa e obtém IPv4. Teste também um backup indisponível e verifique o AP de recuperação. |
| Relógio | Confira o fuso inicial detectado pelo navegador, a sincronização NTP depois de conectar à internet, a hora UTC e a persistência do fuso escolhido manualmente após desligar e ligar. Repita com o hotspot sem internet. |
| Nextion | Use o mesmo modelo HMI/TFT e layout da instalação anterior. Confirme hora em repouso, frequências RX/TX, campos do protocolo, entrada/saída de tráfego e restauração depois de reiniciar. Os campos visíveis dependem do layout gravado. |
| OLED 128×32/64 | Em Expert, selecione 180° e aplique. Confira a orientação após recarregar a página e após reiniciar. Volte para 0° e confirme. |
| Acesso RF | Em Protocolos, abra Acesso RF, aplique a política desejada e confira o estado efetivo. O modo Público mantém a confirmação explícita. Valide via RF com estações autorizadas e retorne à política anterior ao concluir. |
| Baseline RF | Repita um teste de ida e volta em DMR simplex, D-Star e YSF com a configuração anterior. |
| Versão | Confira `5.13.002` no rodapé e no Sistema. |

O painel foi projetado para acesso direto na rede local. Para acesso externo, use uma rede privada autenticada. A publicação das imagens é independente do acesso administrativo ao hotspot.

Referências de integração: [ON7LDS NextionDriver](https://github.com/on7lds/NextionDriver), [MMDVM-Display](https://github.com/g4klx/MMDVM-Display), [API de portal cativo RFC 8908](https://www.rfc-editor.org/rfc/rfc8908).
