# PU2PNY-OS — situação verificada em 23/09/2026

## Qual versão baixar

- Última imagem publicada: [0.3.22-alpha ARM64](https://github.com/PU2PNY/2PNY-OS/releases/tag/v0.3.22-alpha). Arquivos: `PU2PNY-OS-0.3.22-alpha-arm64.img.xz` e respectivo `.sha256`.
- Código da imagem: commit `d9fa3bb6311d9dbb12de15675b5843b28efa9275` na branch `pu2pny-os-0.3.22-alpha`.
- [GitHub Actions 35826908880](https://github.com/PU2PNY/2PNY-OS/actions/runs/35826908880): source, build ARM64, preflight da imagem, validador final e publicação **PASS**. Nível **SW/CI**, não **HW**.
- A branch padrão `main` era uma fundação histórica 0.1.1 e não contém a imagem atual. Não inferir versão atual pelo código de `main`.

## Baseline protegida

O usuário aprovou D-Star simplex, DMR simplex e YSF/C4FM simplex em testes anteriores. Não alterar seu fluxo para resolver duplex ou display. Cada nova imagem exige regressão física antes de receber o estado HW PASS.

## Estado dos dez defeitos reportados

| Item | Situação verificável na imagem 0.3.22 | Próximo critério de aceite |
| --- | --- | --- |
| 10. BrandMeister e XLX | O aplicador real reescreve `/var/lib/2pny/dmr/DMRGateway.ini`: seção XLX separada e `[DMR Network 1]` para BM; worker invalida estado antigo ao mudar `/var/lib/2pny/network-radio.json`. **RF→BM não verificado.** A suposição de `[DMR Network 2]` e `/etc/dmrgateway` não corresponde ao layout instalado. | Com rádio, testar TG e slot RF→BM, BM→RF, XLX e painel, preservar simplex. |
| 1. DNS | Convergência de `nmcli` e aviso/reload ajustados no painel e backend; **persistência física de rede não verificada**. | Trocar DNS, reiniciar, verificar lista única efetiva e aviso até recarga. |
| 2. RSSI/BER | Parser compartilhado já consome medidas de MMDVMHost; **RSSI físico e ausência de portadora não verificados nesta imagem**. | Medida real durante RF e `—` em standby. |
| 3. Nextion | Corrigidos terminadores `FF FF FF`, transporte via modem/MQTT e coordenadas TOT 320×240; **COMOK, HMI e imagem física não confirmados**. | Boot, standby e TX/RX na Nextion CA6JAU sem disputa da UART. |
| 4. YSF ao vivo | Parser já contém eventos RF de cabeçalho e fim do MMDVMHost; **cronômetro no hardware não verificado**. | PTT YSF real, duração crescente, término e regressão simplex. |
| 5. Wi-Fi gráfico | Sem teste dirigido conclusivo do indicador nesta imagem. | Sinal percentual real refletido no texto e na barra, sem número inventado. |
| 6. Export | Sem evidência de entrega completa de copiar/baixar dados técnicos nesta imagem. | Botões funcionais, sem expor segredos, em navegador comum. |
| 7. Perfis | Otimização de ativação não comprovada nesta imagem. | Medir tempo antes/depois e ativar só serviços necessários. |
| 8. D-Star duplex | Diagnóstico de loop de unlink ainda é hipótese; ajuste de `TXHang`, `AckReply` e `Reconnect` não homologado. | Unlink por rádio sem reconexão/loop; simplex intacto. |
| 9. LED XLX | Tempo de Carrier/Hang no modem não aferido após PTT; ajuste universal de hang pode causar regressão. | Medir LED e fluxo XLX, então aplicar mudança condicional mínima. |

## Telas e localização

- SSD1306 128×32 configurado e 128×64, SH1106 128×64, LCD 16×2/20×4 e Nextion por resolução conhecida têm código de apresentação. Endereço I²C sozinho **não identifica** controlador ou altura; seleção manual permanece necessária quando não há metadados confiáveis.
- Nextion ligada ao modem CA6JAU é candidata até confirmação física; telas DRM/touch genéricas não têm renderer/compositor completo nesta imagem. Não anunciar detecção universal, touch universal, foto do interlocutor ou idioma 100% como pronto.
- Relógio exibe fuso configurado; sincronização NTP e horário físico dependem de rede/RTC e devem ser testados.

## Organização do repositório

- `PU2PNY-OS_START_HERE.md`: ordem de leitura; `PU2PNY-OS_MASTER_SPEC.md`: requisitos; `PU2PNY-OS_PROJECT_INSTRUCTIONS.md`: regras permanentes; `PU2PNY-OS_RELEASE_STATUS.md`: histórico de versões; `PU2PNY-OS_TEST_MATRIX.md`: testes históricos; `PU2PNY-OS_CHANGELOG.md`: decisões; **este documento**: estado atual sintético, com correções de contexto às anotações históricas.
- `src/`: fontes da versão; `ci/`: sobreposição, testes e validador; `.github/workflows/`: builds; `docs/`: contexto e pendências. Não apagar históricos nem renomear repositório sem mapear links, builds e rollback.
- A documentação histórica que diz “código local ainda não publicado” descreve o instante anterior à release. A fonte de verdade para 0.3.22 é o artefato e o run acima.

## Passagem para a próxima conversa

Prioridade: obter resultados físicos da 0.3.22; reproduzir RF→BM e Nextion no hardware; corrigir somente causa demonstrada. Para cada falha registrar modo, simplex/duplex, slot, TG, modelo/tamanho, horário e trechos de log sem credenciais. Manter estados DOC/SW/VPS/HW separados. Não reutilizar os nomes de arquivos `/etc/dmrgateway` ou `/run/pu2pny/live_status.json` de um roteiro genérico como se descrevessem esta imagem; o runtime presente usa `/var/lib/2pny` e `/run/2pny/live-state.json`.
