#!/usr/bin/env python3
"""PU2PNY-OS 5.x local Unix datagram event bus/state cache."""
from __future__ import annotations
import json, os, signal, socket, tempfile, time
from pathlib import Path
from typing import Any

RUN = Path(os.environ.get("PU2PNY_RUN", "/run/pu2pny"))
SOCK = RUN / "event.sock"
STATE = RUN / "state.json"
running = True

def stop(_sig: int, _frame: Any) -> None:
    global running
    running = False

def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.chmod(tmp, 0o644); os.replace(tmp, path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def main() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    try: SOCK.unlink()
    except FileNotFoundError: pass
    state: dict[str, Any] = {"schema": 1, "version": "5.00.000", "seq": 0, "events": {}}
    s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    s.bind(str(SOCK)); os.chmod(SOCK, 0o666); s.settimeout(1.0)
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    atomic_json(STATE, state)
    try:
        while running:
            try: raw = s.recv(65535)
            except socket.timeout: continue
            try:
                obj = json.loads(raw.decode("utf-8"))
                if not isinstance(obj, dict): continue
                topic = str(obj.get("topic", "")).strip()
                if not topic or len(topic) > 96: continue
                state["seq"] += 1; state["updated"] = time.time()
                state["events"][topic] = {"seq": state["seq"], "ts": state["updated"], "data": obj.get("data")}
                atomic_json(STATE, state)
            except (UnicodeDecodeError, json.JSONDecodeError, OSError):
                continue
    finally:
        s.close()
        try: SOCK.unlink()
        except FileNotFoundError: pass
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
