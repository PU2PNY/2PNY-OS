# Recovery 0.3.31.112 — validation state

- Implementation: present on `pu2pny-os-0.3.31.112-recovery`.
- Runtime activation: **NO**.
- Historical updater `src/2pny-update-manager-0.3.20.py`: unchanged by this candidate.
- SW test workflow: `.github/workflows/0.3.31.112-recovery-ci.yml`.
- GitHub Actions run `37372833165`: **QUEUED / not evidence of PASS** at the time this note was written.
- VPS validation: **NOT VERIFIED** because the SentinelX connection available in this session identifies host `ia-zap`, not a dedicated PU2PNY-OS test VPS. Running recovery tests there would violate environment isolation.
- HW validation: **NOT APPLICABLE** to the isolated engine itself; required later if integration changes RF/display/network services.

Do not promote this candidate to approved or wire it into runtime until SW executes successfully and the recovery path is exercised on the correct PU2PNY test VPS.

## Atualização de estado — 0.3.31.116

- SW/CI: **PASS** — run `37380823933`.
- VPS Debian 12: **PASS** no commit `2570de829bb762030890a5936da22cc0cb703a4a`; 8/8 testes transacionais e allowlist de serviços.
- Integração: o engine 0.3.31.112 pode ser empacotado de forma versionada, mas **não substitui** `/usr/local/sbin/2pny-update-manager` nesta candidata porque a CLI atual do painel/backend exige comandos legados não oferecidos pelo novo engine.
- HW: **PENDENTE** quando futura integração autoritativa afetar serviços físicos.
