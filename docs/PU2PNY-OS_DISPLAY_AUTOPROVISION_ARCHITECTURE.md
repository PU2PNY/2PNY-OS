# PU2PNY-OS — Display Auto-Detection + Auto-Provisioning

Status: **arquitetura / implementação inicial 0.3.9 Alpha**  
Validação atual: **DOC + SW local de sintaxe**. Nenhum item abaixo deve ser chamado de HW PASS antes de teste físico.

## 1. Objetivo

Adicionar uma camada de detecção e provisionamento de display que opere como appliance, sem terminal, sem root no painel e sem alterar RF/MMDVM de forma implícita.

A primeira etapa implementa detecção não destrutiva de:

- Nextion/TJC/OpenNextion por UART/USB-TTL;
- Nextion já confirmada pelo canal serial da MMDVM;
- OLED I2C em 0x3C/0x3D, com distinção SSD1306/SH1106 quando o kernel/Device Tree fornecer metadata;
- candidatos HD44780/PCF8574 em 0x27/0x3F;
- SPI identificado pelo kernel;
- framebuffer/DRM e touch genérico como fallback informativo.

## 2. Princípios de segurança

1. **Detecção nunca grava TFT/HMI.**
2. **Download nunca implica gravação.**
3. **Gravação de TFT exige confirmação explícita do usuário.**
4. Todo asset deve ter URL permitida + SHA-256 publicado no catálogo antes de ser elegível.
5. Se o catálogo não tiver URL + SHA-256 reais, o estado é `asset_unpublished` e nenhuma ação de gravação é oferecida.
6. MMDVMHost não perde a porta serial durante operação. Se estiver ativo, o detector não abre diretamente o device real do modem.
7. Para Nextion via MMDVM, o transporte continua pertencendo ao MMDVMHost. O PU2PNY escolhe apenas um renderer lógico por vez.
8. Estado desconhecido é reportado como desconhecido/candidato; nunca como modelo confirmado.

## 3. Componentes

### 3.1 `2pny-display-detector`
Helper privilegiado, não destrutivo. Produz:
- `/var/lib/2pny/display-detection.json`
- `/run/2pny/display-detect-status.json`

Estados: `detecting -> identified/candidate -> ready`. O provisionador futuro adicionará `download_pending -> downloading -> verify -> confirmation_required -> flashing -> validating -> ready/error/rollback`.

### 3.2 `display-catalog.json`
Catálogo local com família/model regex, tamanho, resolução, renderer e, quando publicado, versão/filename/SHA-256/URL do TFT. Nesta etapa assets TFT ficam `unpublished` com URL/SHA nulos.

### 3.3 `2pny-display-bootstrap`
Executa detecção no boot e reaplica a configuração de display já aprovada quando RF estiver configurada. Não faz flash.

### 3.4 `2pny-display-detect.path`
Permite ao backend solicitar nova detecção escrevendo request em `/run/2pny`, mantendo frontend sem root.

### 3.5 Hotplug
Regra udev agenda `2pny-display-detect.service` em eventos tty, drm e input. O serviço continua não destrutivo.

## 4. Fluxo de detecção

### Camada 1 — USB/UART
1. Enumera serial by-id, ttyUSB, ttyACM, serial0 e ttyAMA0.
2. Lê sysfs USB.
3. Exclui o realpath do modem MMDVM.
4. Nextion direto: 9600 e 115200 baud.
5. Envia `connect + FF FF FF`.
6. Aceita como Nextion somente resposta contendo `comok`.
7. Extrai model string e resolução/tamanho quando conhecidos.
8. Consulta não destrutiva `get pnyver.txt`. HMI oficial PU2PNY futuro deverá expor essa variável. Ausência = `unknown`, não “vazio”.

### Camada 2 — Nextion via MMDVM
- Reutiliza prova protocolar do hardware probe quando existente.
- Se MMDVMHost estiver ativo, não abre a serial do modem.
- Renderer próprio pode usar MQTT `display-in`; MMDVMHost continua responsável pelo transporte serial.

### Camada 3 — I2C
- Usa devices enumerados pelo kernel/sysfs.
- 0x3C/0x3D: OLED candidato.
- Metadata `ssd1306`/`sh1106` promove para confirmado.
- Sem metadata permanece `ssd1306_or_sh1106`.
- 0x27/0x3F: candidato HD44780/PCF8574.

### Camada 4 — SPI
Usa modalias/name do kernel e só confirma controladores identificáveis.

### Camada 5 — vídeo/touch genérico
DRM conectado => `generic_video_display`; input touch é associado como contexto. Renderer touch completo é fase posterior.

## 5. Nextion: catálogo e TFT

A gravação de TFT não entra na detecção. O provisionador futuro deve:
1. detectar modelo/resolução;
2. localizar perfil exato;
3. descobrir `pnyver.txt` quando existir;
4. comparar versão;
5. baixar apenas de origem permitida;
6. calcular SHA-256;
7. comparar com SHA publicado;
8. exibir confirmação;
9. somente após confirmação iniciar updater;
10. acompanhar progresso real;
11. validar reconnect/model depois do reboot;
12. em falha restaurar configuração/software possível. Não prometer rollback físico quando o hardware não tiver dual-bank.

## 6. Renderer e MMDVMHost

### `pu2pny-modern-v2`
- renderer Nextion nativo do MMDVMHost desabilitado;
- MMDVMHost mantém MQTT e canal serial do modem;
- PU2PNY Display Core publica comandos em `display-in`;
- um único renderer lógico: PU2PNY.

### `mmdvmhost-native`
- `General.Display=Nextion`;
- `Nextion.Port=modem`;
- ScreenLayout compatível;
- PU2PNY Display Core parado;
- um único renderer lógico: MMDVMHost.

Nunca habilitar os dois ao mesmo tempo.

## 7. Hotplug e carga
- eventos de kernel disparam oneshot;
- sem polling contínuo de serial/I2C;
- lock impede execuções concorrentes;
- estado transitório em `/run`, resultado estável em `/var/lib/2pny`;
- frontend apenas consulta estado e escreve request controlado.

## 8. API/painel — contrato planejado
- `GET /api/display/detection`
- `POST /api/display/detect`
- `GET /api/display/catalog`
- `POST /api/display/provision` — não implementar flash até existir asset real + SHA + teste
- `POST /api/display/confirm-flash` — confirmação futura de curta duração

## 9. Validação
- arquitetura: DOC;
- detector Python: SW sintaxe local;
- imagem/ARM64: pendente CI;
- detecção física: HW PENDENTE;
- gravação TFT: NÃO IMPLEMENTADA nesta etapa;
- telas genéricas: detecção parcial, renderer completo fase posterior.
