#!/usr/bin/env python3
from pathlib import Path

release = Path("PU2PNY-OS_RELEASE_STATUS.md")
matrix = Path("PU2PNY-OS_TEST_MATRIX.md")
changelog = Path("PU2PNY-OS_CHANGELOG.md")

old_release = """### 4.00.000 — Ecossistema global
- Estado: EM TESTE / candidata para teste físico após build.
- Branch: pu2pny-os-4.00.000-ecosystem.
- Base protegida ARMHF/ARMv6: 0.3.31.124 / commit 6e7dc53d94a80d8860ce54f513b738313907e5b8.
- Base protegida ARM64: 0.3.31.122, última linha ARM64 protegida antes da trilha Pi Zero.
- Implementado: inventário global de capacidades, /api/capabilities, serviço event-driven/baixa frequência, modelo Helix opcional/default-off e gates de não regressão.
- Safety CI, Baseline Guard e validação VPS da camada 4.00.000: PASS.
- Build dual ARM64/ARMHF: EM TESTE até workflow 4.00.000 concluir.
- HW RF/display/audio: PENDENTE; não classificar como produção.
"""

new_release = """### 4.00.000 — Ecossistema global
- Estado: **SW/CI PASS / prerelease publicada / CANDIDATA PARA TESTE FÍSICO. Não PROD.**
- Branch de construção: `pu2pny-os-4.00.000-ecosystem`.
- Base protegida ARMHF/ARMv6: 0.3.31.124 / commit `6e7dc53d94a80d8860ce54f513b738313907e5b8`.
- Base protegida ARM64: 0.3.31.122, última linha ARM64 protegida antes da trilha Pi Zero.
- Implementado: inventário global de capacidades, `/api/capabilities`, serviço event-driven/baixa frequência, modelo Helix opcional/default-off e gates de não regressão.
- Safety CI, Baseline Guard e validação VPS da camada 4.00.000: PASS.
- Commit fonte real das imagens: `684820f49896d9a478644e7418932ed40a3a8870`.
- ARM64: run `38575811918` — build/overlay protegido/XZ/SHA/estrutura/artefato PASS; SHA-256 `3ec52631dfe44b9a466bd1f1f4a8b910c6fdac3663736f7d643091b8c5a13dd7`.
- ARMHF/ARMv6/Pi Zero: run `38582443780` — toolchain ARMv6, Helix, backend, overlay protegido, fsck, montagem read-only, validação armhf, XZ/SHA e artefato PASS; SHA-256 `b7edc16b4a7786e0b0664eef7a1a3f53b449f6abf55aa47d31516a170163760c`.
- Publicação/revalidação conjunta: run `38584440709` — ambos os artefatos passaram novamente `xz -t` + `sha256sum -c`; prerelease `v4.00.000` publicada e seis assets confirmados.
- Commit da correção do gate ARM32: `14a5a2a054f5b563db70860192dcd3165694e82b`.
- Commit do publicador seguro: `ecef5fc85bb5419797927d5efe8b3316ce263e7a`.
- A tag da release usa `main` apenas como âncora administrativa por restrição do `GITHUB_TOKEN`; a proveniência real das imagens permanece registrada pelos commits/runs acima e nos `BUILD-INFO`.
- Helix está instalado mas **desabilitado por padrão**; `shadow/process` não são ativados automaticamente. HVC e AMBE/AMBE+2 nativo não são declarados produção.
- **HW RF/duplex/BER/RSSI/audio/transcoding/display: PENDENTE**; não promover para HW/PROD antes do teste físico.
"""

s = release.read_text()
if "run `38584440709`" not in s:
    if s.count(old_release) != 1:
        raise SystemExit(f"release status anchor count={s.count(old_release)}")
    release.write_text(s.replace(old_release, new_release, 1))

matrix_marker = "### SW-400000-IMAGE-DUALARCH-20261014 — APROVADO SW/CI"
if matrix_marker not in matrix.read_text():
    with matrix.open("a") as f:
        f.write("""

### SW-400000-IMAGE-DUALARCH-20261014 — APROVADO SW/CI
- Requisitos: `REL-050`, `ARCH-007`, `PROTO-058`; classificação do artefato: **candidata para teste físico**, não PROD.
- Fonte comum das imagens: commit `684820f49896d9a478644e7418932ed40a3a8870`.
- ARM64: run `38575811918` — Helix self-test, backend, base imutável, overlay protegido, inventário de capacidades, hashes protegidos, fsck/estrutura, XZ, SHA-256 e upload do artefato: PASS.
- ARM64 SHA-256: `3ec52631dfe44b9a466bd1f1f4a8b910c6fdac3663736f7d643091b8c5a13dd7`.
- ARMHF/ARMv6/Pi Zero: run `38582443780` — cross-build Helix ARMv6, backend GOARM=6, base 0.3.31.124 verificada, overlay protegido, `systemd-analyze verify`, scanner, fsck, montagem read-only, arquitetura armhf, XZ, SHA-256 e upload: PASS.
- ARMHF/ARMv6 SHA-256: `b7edc16b4a7786e0b0664eef7a1a3f53b449f6abf55aa47d31516a170163760c`.
- Correção mínima do gate ARM32: commit `14a5a2a054f5b563db70860192dcd3165694e82b`; substituiu execução foreign-arch via chroot pela consulta da base dpkg sem executar binário ARM. Nenhum arquivo RF/backend/runtime foi alterado nesse commit.
- Revalidação/publicação: run `38584440709` — downloads dos artefatos já validados, `xz -t` + `sha256sum -c` para ambos, publicação `v4.00.000` e verificação dos seis assets: PASS.
- Baseline Guard após o publicador: run `38584440452` — PASS.
- Helix permanece default-off; HVC/native AMBE não promovidos.
- **HW:** PENDENTE para RF real, simplex/duplex real, BER/RSSI, áudio/transcoding e displays físicos. SW/CI PASS não substitui HW.
""")

change_marker = "### Fechamento de build/publicação 4.00.000 — 2026-10-14"
if change_marker not in changelog.read_text():
    with changelog.open("a") as f:
        f.write("""

### Fechamento de build/publicação 4.00.000 — 2026-10-14
- O primeiro reparo ARM32 falhou apenas no gate de arquitetura porque um runner x86_64 tentou executar `/usr/bin/dpkg` ARMHF via `chroot`, resultando em `Exec format error`; toolchain, Helix ARMv6, backend, overlay, fsck e scanner já haviam passado.
- Commit `14a5a2a054f5b563db70860192dcd3165694e82b` aplicou correção cirúrgica de uma linha: a arquitetura passou a ser lida pela base dpkg montada, sem executar binário ARM. O novo run `38582443780` concluiu ARMHF/ARMv6 integralmente com PASS.
- A primeira tentativa de publicação falhou somente com `HTTP 403 Resource not accessible by integration` ao criar release apontando para um commit que modifica workflows; os dois artefatos já haviam passado a revalidação XZ/SHA.
- O publicador separado, commit `ecef5fc85bb5419797927d5efe8b3316ce263e7a`, reutilizou exatamente os artefatos aprovados, revalidou ambos e publicou `v4.00.000` no run `38584440709` com PASS. A tag usa `main` somente como âncora administrativa; `BUILD-INFO` e notas preservam o commit fonte real `684820f49896d9a478644e7418932ed40a3a8870`.
- SHA-256 final ARM64: `3ec52631dfe44b9a466bd1f1f4a8b910c6fdac3663736f7d643091b8c5a13dd7`.
- SHA-256 final ARMHF/ARMv6/Pi Zero: `b7edc16b4a7786e0b0664eef7a1a3f53b449f6abf55aa47d31516a170163760c`.
- Nenhuma dessas correções alterou o caminho RF aprovado, MMDVMHost, DMRGateway, NextionDriver, Wi-Fi profiles ou comportamento de protocolo protegido.
- Estado final deste ciclo: **SW/CI PASS / prerelease candidata para teste físico; HW/PROD continuam PENDENTE**.
""")

print("FINALIZE_400000_RELEASE_DOCS_OK")
