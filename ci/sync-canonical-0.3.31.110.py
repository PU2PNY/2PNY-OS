#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "start": ROOT / "PU2PNY-OS_START_HERE.md",
    "spec": ROOT / "PU2PNY-OS_MASTER_SPEC.md",
    "release": ROOT / "PU2PNY-OS_RELEASE_STATUS.md",
    "matrix": ROOT / "PU2PNY-OS_TEST_MATRIX.md",
    "changelog": ROOT / "PU2PNY-OS_CHANGELOG.md",
}

SNAPSHOT = "docs/PU2PNY-OS_BASELINE_0.3.31.110.md"
BRANCH = "pu2pny-os-0.3.31.110"
COMMIT = "1c91b26fd561eb7a727df896f2179fd951b6681a"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def append_once(path: Path, marker: str, block: str) -> None:
    text = read(path)
    if marker in text:
        return
    write(path, text.rstrip() + "\n\n" + block.strip() + "\n")


def update_spec_header() -> None:
    path = FILES["spec"]
    text = read(path)
    old = "**Estado:** consolidado para o ciclo ativo 0.3.20-alpha em 2026-09-22. Releases anteriores permanecem registradas como histórico e baseline quando comprovadas."
    new = "**Estado:** consolidado para o código atual 0.3.31.110 em 2026-10-05. Releases anteriores permanecem registradas como histórico e baseline quando comprovadas; validação SW/VPS nunca promove HW."
    if old in text:
        text = text.replace(old, new, 1)
        write(path, text)
    elif new not in text:
        raise SystemExit("MASTER_SPEC: cabeçalho conhecido não encontrado; fail-before-write documental")


def verify_start_here() -> None:
    text = read(FILES["start"])
    required = [
        "## Ciclo consolidado — 0.3.31.110 — 2026-10-05",
        BRANCH,
        COMMIT,
        SNAPSHOT,
        "REL-026",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"START_HERE incompleto: {missing}")


def main() -> int:
    for path in FILES.values():
        if not path.is_file():
            raise SystemExit(f"arquivo canônico ausente: {path}")

    snapshot = ROOT / SNAPSHOT
    if not snapshot.is_file():
        raise SystemExit(f"snapshot ausente: {SNAPSHOT}")

    # Preflight documental: somente depois das verificações começamos a escrever.
    verify_start_here()
    update_spec_header()

    append_once(
        FILES["spec"],
        "## REL-026 — sincronização canônica 0.3.31.110",
        f"""
## REL-026 — sincronização canônica 0.3.31.110

O estado mais novo do código é `{BRANCH}`, commit `{COMMIT}`. A matriz de evidências consolidada está em `{SNAPSHOT}`. Os cinco documentos canônicos devem distinguir explicitamente código atual, última evidência por nível e baseline protegida. Nenhuma atualização documental promove teste SW/VPS para HW.

Critério de aceite: START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX e CHANGELOG apontam para a 0.3.31.110/snapshot, sem alterar runtime e sem reclassificar teste sem evidência. Validação mínima: DOC.
""",
    )

    append_once(
        FILES["release"],
        "## Sincronização 0.3.31.110 — 2026-10-05",
        f"""
## Sincronização 0.3.31.110 — 2026-10-05

- Código atual observado: branch `{BRANCH}`, commit `{COMMIT}`.
- Classificação: **código atual / não promovido automaticamente a HW aprovado**.
- Última candidata de display com evidência formal completa em SW/CI/VPS: `v0.3.30-alpha`, run `36341170897`.
- Estado por componente e últimas evidências: `{SNAPSHOT}`.
- DMR simplex, D-Star simplex e YSF/C4FM simplex permanecem baselines HW protegidas conforme evidência registrada; DMR duplex e Nextion físico permanecem pendentes em seus testes específicos.
- Bloqueador de promoção: retestes HW exigidos pela área afetada. CI/VPS não substituem Raspberry Pi/MMDVM/Nextion/RF real.
""",
    )

    append_once(
        FILES["matrix"],
        "## Consolidação 0.3.31.110 — REL-026 — 2026-10-05",
        f"""
## Consolidação 0.3.31.110 — REL-026 — 2026-10-05

| ID | Caso | Resultado esperado | Estado | Nível |
|---|---|---|---|---|
| TEST-REL-026A | sincronizar código atual e documentos canônicos | os cinco documentos apontam para 0.3.31.110 e para o snapshot sem promover níveis | PASS documental | DOC |
| TEST-REL-026B | separar código atual de validação HW | 0.3.31.110 não transforma PASS SW/VPS em HW PASS | PASS documental | DOC |
| TEST-REL-026C | preservar baselines aprovadas | DMR simplex, D-Star simplex e YSF/C4FM simplex permanecem protegidos; duplex/display seguem estados próprios | PASS documental | DOC |
| TEST-REL-026D | reteste físico da 0.3.31.110 | executar somente em Raspberry Pi/MMDVM/displays reais os casos que exigem HW | PENDENTE | HW |

Snapshot detalhado: `{SNAPSHOT}`.
""",
    )

    append_once(
        FILES["changelog"],
        "## 2026-10-05 — sincronização documental 0.3.31.110 — REL-026",
        f"""
## 2026-10-05 — sincronização documental 0.3.31.110 — REL-026

- Confirmada como estado mais novo de código a branch `{BRANCH}`, commit `{COMMIT}`.
- Criado `{SNAPSHOT}` com a última evidência válida por componente e separação DOC/SW/VPS/HW.
- Registrado explicitamente que a 0.3.31.110 não é promovida automaticamente para HW PASS.
- DMR simplex, D-Star simplex e YSF/C4FM simplex continuam baselines protegidas; estados pendentes de duplex/display não podem reescrever essas baselines.
- Nenhum arquivo de runtime, RF, rede, protocolo, display ou builder é alterado por esta sincronização documental.
""",
    )

    # Pós-condições: todos os canônicos devem conter a versão e/ou REL-026.
    for key, path in FILES.items():
        text = read(path)
        if key == "start":
            ok = "0.3.31.110" in text and "REL-026" in text
        else:
            ok = "REL-026" in text and "0.3.31.110" in text
        if not ok:
            raise SystemExit(f"pós-condição falhou em {path.name}")

    print("OK: documentação canônica sincronizada de forma idempotente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
