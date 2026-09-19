#!/usr/bin/env python3
"""PU2PNY live-state core.

Consumes each MMDVMHost/DMRGateway journal entry once and keeps the current
transmission in memory.  The browser and HTTP handlers must never read logs.
This module deliberately has no write path to radio or modem configuration.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
import time
from collections import deque

HEADER_RE = re.compile(
    r"DMR Slot (\d), received (RF|network) voice header from (.+?) to (TG )?([^,]+)", re.I
)
END_HEAD_RE = re.compile(
    r"DMR Slot (\\d), (?:received )?(RF|network) "
    r"(?:end of voice transmission|voice transmission lost|watchdog has expired)", re.I
)
DURATION_RE = re.compile(r"([0-9.]+) seconds", re.I)
LOSS_RE = re.compile(r"([0-9.]+)% packet loss", re.I)
BER_RE = re.compile(r"BER:\\s*([0-9.]+)%", re.I)
RSSI_RE = re.compile(r"RSSI:\\s*([^,]+? dBm)(?:$|,)", re.I)
IDLE_RE = re.compile(r"(?:Debug:\\s*)?Mode set to Idle", re.I)
ALIAS_RE = re.compile(r"DMR Slot (\d).*?(?:talker alias|alias).*?[:=]\s*(.+)$", re.I)
LIVE_BER_RE = re.compile(r"DMR Slot (\d).*?BER:\s*([0-9.]+)%", re.I)
LIVE_RSSI_RE = re.compile(r"DMR Slot (\d).*?(?:reported )?RSSI[:=]\s*(-?[0-9.]+)\s*dBm", re.I)


def iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()


def quality(ber=None, rssi=None):
    """A label derived only from measurements actually emitted by the modem."""
    if ber is None and rssi is None:
        return {"label": "unavailable", "score": None}
    score = 100.0
    if ber is not None:
        score -= min(70.0, float(ber) * 14.0)
    if rssi is not None:
        value = float(rssi)
        score -= 45 if value < -125 else 25 if value < -115 else 10 if value < -105 else 0
    score = max(0, min(100, round(score)))
    return {"label": "excellent" if score >= 80 else "good" if score >= 55 else "poor", "score": score}


class LiveState:
    """Bounded state machine.  `ingest` is intentionally side-effect free."""

    def __init__(self, history_limit=200, metric_limit=64):
        self.history = deque(maxlen=history_limit)
        self.metrics = deque(maxlen=metric_limit)
        self.active = {"RF": None, "NETWORK": None}
        self.aliases = {}
        self.network = {"state": "unknown", "message": "waiting", "updated": None}
        self.sequence = 0
        self.changed = True

    def _touch(self):
        self.sequence += 1
        self.changed = True

    def ingest(self, message: str, ts: float | None = None, gateway=False):
        ts = time.time() if ts is None else float(ts)
        message = str(message or "").strip()
        if not message:
            return None
        if gateway:
            return self._gateway(message, ts)

        alias = ALIAS_RE.search(message)
        if alias:
            self.aliases[int(alias.group(1))] = alias.group(2).strip()[:80]

        header = HEADER_RE.search(message)
        if header:
            slot = int(header.group(1))
            direction = header.group(2).upper()
            event = {
                "event": "start", "protocol": "DMR", "direction": direction,
                "mode": "tx" if direction == "RF" else "rx",
                "source": header.group(3).strip(),
                "target": ("TG " if header.group(4) else "") + header.group(5).strip(),
                "slot": slot, "started_at": iso(ts), "started_unix_ms": round(ts * 1000),
                "ber": None, "rssi": None, "rssi_min": None, "rssi_avg": None,
                "rssi_peak": None, "quality": quality(),
            }
            if slot in self.aliases:
                event["alias"] = self.aliases[slot]
            self.active[direction] = event
            if direction == "NETWORK" and self.network.get("state") != "connected":
                self.network = {"state": "connected", "message": "traffic confirmed", "updated": iso(ts)}
            self._touch()
            return event

        end = END_HEAD_RE.search(message)
        if end:
            slot, direction = int(end.group(1)), end.group(2).upper()
            duration_match = DURATION_RE.search(message)
            duration = float(duration_match.group(1)) if duration_match else 0.0
            current = self.active.get(direction)
            result = dict(current or {
                "protocol": "DMR", "direction": direction,
                "mode": "tx" if direction == "RF" else "rx", "slot": slot,
                "source": "", "target": "", "started_at": iso(ts - duration),
                "started_unix_ms": round((ts - duration) * 1000),
            })
            result.update({"event": "end", "ended_at": iso(ts), "duration": duration})
            loss = LOSS_RE.search(message)
            ber_final = BER_RE.search(message)
            rssi_final = RSSI_RE.search(message + ",")
            if loss:
                result["loss"] = float(loss.group(1))
            if ber_final:
                result["ber"] = float(ber_final.group(1))
            if rssi_final:
                values = [float(x) for x in re.findall(r"-?\\d+(?:\\.\\d+)?", rssi_final.group(1))]
                if values:
                    result["rssi"] = values[-1]
                    result["rssi_min"], result["rssi_peak"] = min(values), max(values)
                    result["rssi_avg"] = round(sum(values) / len(values), 1)
            result["quality"] = quality(result.get("ber"), result.get("rssi_avg", result.get("rssi")))
            self.history.appendleft(result)
            self.active[direction] = None
            if direction == "NETWORK" and self.network.get("state") != "connected":
                self.network = {"state": "connected", "message": "traffic confirmed", "updated": iso(ts)}
            self._touch()
            return result

        if IDLE_RE.search(message) and any(self.active.values()):
            for direction, current in list(self.active.items()):
                if not current:
                    continue
                result = dict(current)
                started_ms = int(current.get("started_unix_ms") or round(ts * 1000))
                result.update({
                    "event": "end", "ended_at": iso(ts),
                    "duration": max(0.0, ts - started_ms / 1000.0),
                    "ended_by": "idle",
                })
                self.history.appendleft(result)
                self.active[direction] = None
            self._touch()
            return {"event": "idle"}

        # Some modem builds emit intermediate BER/RSSI lines.  Accept them if
        # present, but never synthesize values when the firmware does not.
        ber, rssi = LIVE_BER_RE.search(message), LIVE_RSSI_RE.search(message)
        slot = int((ber or rssi).group(1)) if (ber or rssi) else None
        current = next((x for x in self.active.values() if x and x.get("slot") == slot), None)
        if current and (ber or rssi):
            if ber:
                current["ber"] = float(ber.group(2))
            if rssi:
                value = float(rssi.group(2)); current["rssi"] = value
                samples = current.setdefault("_rssi_samples", [])
                samples.append(value); del samples[:-32]
                current["rssi_min"] = min(samples); current["rssi_peak"] = max(samples)
                current["rssi_avg"] = round(sum(samples) / len(samples), 1)
            current["quality"] = quality(current.get("ber"), current.get("rssi_avg", current.get("rssi")))
            self._touch()
            return current
        return None

    def _gateway(self, message, ts):
        low = message.lower(); state = None; summary = ""
        if "logged into the master successfully" in low or "login successful" in low:
            state, summary = "connected", "authenticated"
        elif any(x in low for x in ("authentication failed", "login failed", "login rejected",
                 "incorrect password", "timed out waiting", "network is down")):
            state, summary = "error", message[-180:]
        elif any(x in low for x in ("connecting to xlx", "sending authorisation", "sending configuration",
                                     "linking to", "opening network", "connecting to")):
            state, summary = "connecting", "authenticating"
        elif any(x in low for x in ("linked to", "connected to", "network is connected", "login accepted")):
            state, summary = "connected", "linked"
        elif "closing" in low and ("network" in low or "xlx" in low):
            state, summary = "disconnected", "closed"
        if state and (state != self.network["state"] or summary != self.network["message"]):
            self.network = {"state": state, "message": summary, "updated": iso(ts)}
            self._touch(); return self.network
        return None

    def add_probe(self, ok, latency_ms=None, now=None):
        now = time.time() if now is None else now
        self.metrics.append({"ts": now, "ok": bool(ok), "latency_ms": latency_ms if ok else None})
        self._touch()

    def mtr_summary(self):
        values = [x["latency_ms"] for x in self.metrics if x["ok"] and x["latency_ms"] is not None]
        loss = 100 * (1 - sum(1 for x in self.metrics if x["ok"]) / len(self.metrics)) if self.metrics else None
        jitter = sum(abs(b-a) for a, b in zip(values, values[1:])) / (len(values)-1) if len(values) > 1 else None
        latency = values[-1] if values else None
        label = "offline" if self.metrics and not values else "excellent" if latency is not None and latency < 60 and (loss or 0) < 1 else "good" if latency is not None and latency < 150 and (loss or 0) < 5 else "poor" if latency is not None else "unknown"
        return {"latency_ms": round(latency, 1) if latency is not None else None,
                "loss_percent": round(loss, 1) if loss is not None else None,
                "jitter_ms": round(jitter, 1) if jitter is not None else None,
                "quality": label, "samples": len(self.metrics)}

    def snapshot(self):
        candidates = [x for x in self.active.values() if x]
        active = max(candidates, key=lambda x: x["started_unix_ms"]) if candidates else None
        if active:
            active = {k: v for k, v in active.items() if not k.startswith("_")}
        return {"schema": 1, "sequence": self.sequence, "active": active,
                "standby": active is None, "network": self.network,
                "internet": self.mtr_summary(), "history": list(self.history),
                "updated": iso(time.time())}

