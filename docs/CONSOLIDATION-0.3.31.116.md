# PU2PNY-OS 0.3.31.116 — consolidação para teste físico

Base imutável: `v0.3.31.110`, commit `1c91b26fd561eb7a727df896f2179fd951b6681a`.

Escopo: Recovery 0.3.31.112 (SW/CI + VPS Debian 12 PASS), Baseline Guard 0.3.31.113, Display 0.3.31.114 (SW/CI; Nextion HW pendente), PT/EN/ES 0.3.31.115 e gates/build da 0.3.31.116.

O backend atual chama a CLI histórica `status|download|install-staged|install|rollback|delete-backup`. O engine 0.3.31.112 usa `preflight|prepare|activate|rollback|status`; substituir o updater ativo seria regressão. A 0.3.31.116 preserva o updater 0.3.20 byte-idêntico e instala o engine endurecido em caminho versionado sob `/usr/local/libexec`.

Fora do escopo: Debian 13/Trixie; DMR/D-Star/YSF; MMDVMHost; RF/frequências/offsets/baud/serial; rede/wizard. Nenhum item físico recebe PASS antes de teste real.
