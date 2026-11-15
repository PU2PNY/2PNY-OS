# PU2PNY-OS 5.12.002 P2 — critérios de testes reais

**Status confirmado 15/11/2026:** [P2 ALPHA publicada](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.002-p2) para Raspberry ARM32/ARM64, Orange Pi Zero e NanoPi NEO, com SHA-256, 4 manifestos e [CI 6/6 PASS](https://github.com/PU2PNY/2PNY-OS/actions/runs/43727451516). Tag/código `a5f9f286d48a88b9fb658f56cb111c9acaa8a737`. **Nada de PRODUÇÃO** sem confirmação física. Versão base 5.12.001 P1, preservada para rollback.

## Regressões priorizadas — evidência
- **Raspberry Pi Zero W ARMv6** (diagnóstico enviado em 14/11/2026): carga média 7.75 em CPU de 1 núcleo, `2pny-operational-restore` reiniciando, `2pny-hostfiles-update` timeouts, `DMRGateway` não consegue ler `/var/lib/2pny/dmr/DMRGateway.ini`. Wi-Fi/IPv4 `192.168.0.26` e HTTP local `/healthz` e `/dashboard` retornaram 200. O modem MMDVM detectou serial0/115200. NTP sincronizado, **fuso incorreto Europe/London**. Não publicar dados da rede nem logs brutos com segredos.
- **Causa DMR verificada em código/teste SW**: `runtime/5.11/voice-apply.py` regrava INI com modo `0600 root:root`, enquanto `2pny-dmrgateway.service` usa `mmdvm`. P2 altera **somente** a função de gravação de INI, mantendo `root:mmdvm 0640`, valida leitura via `runuser` e rollback. Segredos de configuração administrativa continuam `0600`. **RF e conexão XLX/BrandMeister continuam HW PENDENTE**.
- **ARMv6 CPU**: tarefas de manutenção de listas e downloads em segundo plano são adiadas durante boot/CPU ocupada no Pi Zero. Tentativas do restore operacional recebem limite/backoff para não saturar systemd. Sem métricas físicas pós-correção, **não afirmar CPU reduzida**.
- **Orange Pi Zero H2+/NanoPi NEO H3**: usuário relata AP visível sem acesso ao painel. P1 possui unidade e binário `2pnyd` instalados; em namespace/VM o Go web server funciona, mas AP real não foi verificado. P2 mascara unidade do pacote `hostapd.service` para deixar dono único `2pny-network-core`, com `MemoryMax=128M` no painel. Esto não garante que todo celular receba IP/HTTP; registrar falha com teste físico.
- **Histórico DMR/D-Star/YSF simplex:** aprovados em versões anteriores (0.3.x) segundo registros, preservar RF/binaries byte-idênticos; **sem afirmar testes físicos na P2**. Nextion ON7LDS aprovado no 5.00.002 também preservado.

## Procedimento sem terminal (placa por placa)
1. Grave a imagem P2 somente em **outro microSD**, mantenha anterior.
2. Conecte à rede da placa. No **AP**, abra `http://10.43.0.1/` (HTTPS não funciona neste portal local); confirme se o aparelho recebeu IPv4 `10.43.0.x`, gateway `10.43.0.1`. Se apenas SSID aparecer, registrar **FAIL** e não declarar AP funcional.
3. No Pi com Wi-Fi conectado ao roteador, entrar no endereço IPv4 visível no painel do roteador, ou `http://pu2pny32.local/` para ARM32 / `http://pu2pny64.local/` para ARM64.
4. **NanoPi NEO H3 original não tem Wi-Fi embutido**. Conectar Ethernet DHCP. Um AP nesse modelo só é esperado com adaptador Wi-Fi compatível efetivamente detectado.
5. Abra **Ao Vivo/Internet/Protocolos/Display/Sistema/Expert**; confira menu e indicativo. **Não repetir POST/Ativar** quando houver `Failed to fetch` antes de verificar o estado.
6. Em **Expert → Diagnóstico fácil → Rodar tudo → Baixar .txt**, e se possível itens `Painel HTTP`, `Estado RF e gateways`. Inspecionar e ocultar identificadores/senhas/chaves antes de compartilhar.
7. Em **DMR**, selecionar uma vez o perfil já validado e verificar serviço, conexão remota, **RF TX/RX e áudio**, TG/slot (somente com informação real). Testar D-Star e YSF separadamente, não sacrificar simplex por duplex.
8. Na **ARM32 Pi Zero**, após 15–30min comparar carga média e reinícios do gateway, e observar se manutenção atrapalha o rádio. Exigir diferença sob condições comparáveis antes de afirmar melhoria.
9. **Nextion ON7LDS:** não gravar HMI/TFT; checar se dados antigos continuam normais. OLED/LCD verificar standby/IP/CPU/transmissão somente se hardware real conectado.
10. **Relógio:** verificar fuso automático e hora. A P2 NÃO resolve `Europe/London` comprovadamente; não homologar relógio sem reteste.

## Resultado e rollback
| Item | Critério | Estado inicial |
|---|---|---|
| Composição de imagens | SHA-256, xz, ext4, versão/commit, manifestos | **CI PASS / quatro assets publicados** |
| MMDVM/Nextion protegidos | Binários/configuração RF byte-idênticos à P1 | Teste SW durante CI |
| DMRGate INI | root:mmdvm 0640 e usuário mmdvm pode ler | SW PASS local; HW PENDENTE |
| DMR/D-Star/YSF | link externo e TX/RX reais | HW NÃO VERIFICADO |
| PiZero CPU | redução real de load sob cenário equivalente sem travar serviços | HW NÃO VERIFICADO |
| AP Orange | associação, DHCP IPv4, GET de `http://10.43.0.1/` | HW NÃO VERIFICADO/REGRESSÃO REPORTADA |
| NanoPi Ethernet | DHCP, HTTP, RF e display | HW NÃO VERIFICADO |
| Nextion ON7LDS | sem regressão no modo aprovado | Baseline histórico HW PASS, nesta release PENDENTE |
| Horário | fuso IANA aplicado, NTP correto | REGRESSÃO REPORTADA |
| Direct CGNAT/transcoding | áudio e relay/codec funcional | NÃO ENTREGUE |

Relacionados: [#23](https://github.com/PU2PNY/2PNY-OS/issues/23), [#24](https://github.com/PU2PNY/2PNY-OS/issues/24), [#25](https://github.com/PU2PNY/2PNY-OS/issues/25), [#26](https://github.com/PU2PNY/2PNY-OS/issues/26), [#27](https://github.com/PU2PNY/2PNY-OS/issues/27), [#28](https://github.com/PU2PNY/2PNY-OS/issues/28), [#29](https://github.com/PU2PNY/2PNY-OS/issues/29), [#30](https://github.com/PU2PNY/2PNY-OS/issues/30). Documentação upstream: [DMRGateway](https://github.com/g4klx/DMRGateway), [NanoPi NEO H3](https://wiki.friendlyelec.com/wiki/index.php/NanoPi_NEO).
