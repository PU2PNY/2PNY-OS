#!/usr/bin/env python3
"""Single resident producer for PU2PNY live state (RAM-first, bounded)."""
import concurrent.futures, json, os, re, selectors, sqlite3, subprocess, time
from pathlib import Path
from importlib.machinery import SourceFileLoader

CORE = SourceFileLoader("pny_live_core", "/usr/local/lib/2pny-live-core.py").load_module()
RUN = Path("/run/2pny"); STATE = Path("/var/lib/2pny/station")


def atomic(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp"); tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    os.chmod(tmp, 0o644); os.replace(tmp, path)


def journal_rows(unit, since="-210 seconds"):
    try:
        p = subprocess.run(["journalctl", "-b", "-u", unit, "--since", since, "--no-pager", "-o", "json"],
                           text=True, capture_output=True, timeout=5)
        return p.stdout.splitlines()[-700:]
    except Exception:
        return []


def decode(raw):
    try:
        row = json.loads(raw); msg = str(row.get("MESSAGE") or "").strip()
        micro = int(row.get("__REALTIME_TIMESTAMP") or 0)
        return msg, micro / 1_000_000 if micro else time.time()
    except Exception:
        return "", time.time()


def configured_host():
    for filename in ("/var/lib/2pny/network-radio.json", "/var/lib/2pny/protocol-network.json"):
        try:
            data = json.loads(Path(filename).read_text())
            for key in ("address", "host", "server", "gateway"):
                value = str(data.get(key) or "").strip()
                if re.fullmatch(r"[A-Za-z0-9.-]{1,253}", value): return value
        except Exception: pass
    return "1.1.1.1"


def ping(host):
    started = time.monotonic()
    try:
        p = subprocess.run(["ping", "-n", "-c", "1", "-W", "1", host], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2)
        match = re.search(r"time[=<]([0-9.]+)\s*ms", p.stdout)
        return p.returncode == 0, float(match.group(1)) if match else (time.monotonic()-started)*1000
    except Exception:
        return False, None


def persist_call(db, event):
    if event and event.get("event") == "end":
        key = f'{event.get("started_unix_ms",0)}:{event.get("direction")}:{event.get("slot")}'
        db.execute("INSERT OR REPLACE INTO history(id,stamp,data) VALUES(?,?,?)",
                   (key, event.get("ended_at", ""), json.dumps(event, ensure_ascii=False)))
        db.commit()


def start_follow(unit):
    return subprocess.Popen(["journalctl", "-b", "-u", unit, "-f", "-n", "0", "-o", "json"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=1)


def main():
    RUN.mkdir(parents=True, exist_ok=True); STATE.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(STATE/"operators.sqlite")
    db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA journal_size_limit=1048576")
    db.execute("CREATE TABLE IF NOT EXISTS history(id TEXT PRIMARY KEY,stamp TEXT,data TEXT)")
    state = CORE.LiveState(history_limit=200)
    for row in db.execute("SELECT data FROM history ORDER BY stamp DESC LIMIT 200"):
        try: state.history.append(json.loads(row[0]))
        except Exception: pass
    for raw in journal_rows("2pny-mmdvmhost.service"):
        msg, ts = decode(raw); event = state.ingest(msg, ts); persist_call(db, event)
    for raw in journal_rows("2pny-dmrgateway.service", "-15 minutes"):
        msg, ts = decode(raw); state.ingest(msg, ts, gateway=True)

    processes = {False: start_follow("2pny-mmdvmhost.service"), True: start_follow("2pny-dmrgateway.service")}
    selector = selectors.DefaultSelector()
    for gateway, proc in processes.items(): selector.register(proc.stdout, selectors.EVENT_READ, gateway)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="pny-net")
    probe = None; next_probe = 0.0; last_sequence = -1; last_write = 0.0
    while True:
        now = time.monotonic()
        for key, _ in selector.select(timeout=0.1):
            raw = key.fileobj.readline()
            if raw:
                msg, ts = decode(raw); event = state.ingest(msg, ts, gateway=key.data); persist_call(db, event)
        if probe and probe.done():
            try: ok, latency = probe.result()
            except Exception: ok, latency = False, None
            state.add_probe(ok, latency); probe = None
            next_probe = now + (1.0 if any(state.active.values()) else 5.0)
        if probe is None and now >= next_probe:
            probe = pool.submit(ping, configured_host())
        # Write only to tmpfs and only on state change; one forced heartbeat
        # every 15 s lets the daemon detect a stalled producer.
        if state.sequence != last_sequence or now-last_write >= 15:
            atomic(RUN/"live-state.json", state.snapshot())
            last_sequence, last_write, state.changed = state.sequence, now, False


if __name__ == "__main__": main()

