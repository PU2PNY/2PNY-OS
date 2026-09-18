#!/usr/bin/env python3
import json, os, sys, time, termios
from pathlib import Path

STATE = Path("/var/lib/2pny")
HW = STATE / "hardware-probe.json"
STATUS = STATE / "display-status.json"
START = 0xE0
SERIAL = 0x80

PROGRESS = {
    "boot": (10, "PU2PNY iniciando"),
    "network": (25, "Preparando rede"),
    "maintenance": (38, "Atualizando componentes"),
    "hardware": (55, "Detectando hardware"),
    "display": (68, "Preparando display"),
    "rf": (82, "Configurando radio"),
    "ready": (100, "PU2PNY pronto"),
    "warning": (70, "Atencao"),
    "error": (100, "Verifique o painel"),
}

def write_state(state, message, sent=False, transport="none"):
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "state": state, "message": message, "sent": sent,
        "transport": transport, "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }, ensure_ascii=False))
    os.chmod(tmp, 0o600)
    os.replace(tmp, STATUS)

def speed_const(baud):
    return getattr(termios, "B" + str(int(baud)), termios.B115200)

def open_serial(path, baud):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    a = termios.tcgetattr(fd)
    a[0] = 0; a[1] = 0
    a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    a[3] = 0
    sp = speed_const(baud)
    a[4] = sp; a[5] = sp
    a[6][termios.VMIN] = 0
    a[6][termios.VTIME] = 1
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return fd

def cmd_bytes(command):
    return command.encode("ascii", "replace") + b"\xff\xff\xff"

def mmdvm_frame(payload):
    if len(payload) > 250:
        raise ValueError("payload too large")
    return bytes((START, len(payload) + 3, SERIAL)) + payload

def read_for(fd, seconds):
    end = time.monotonic() + seconds
    out = bytearray()
    while time.monotonic() < end:
        try:
            b = os.read(fd, 512)
            if b: out.extend(b)
        except BlockingIOError:
            pass
        except OSError:
            break
        time.sleep(0.02)
    return bytes(out)

def mmdvm_serial_payloads(raw):
    out = []
    i = 0
    while i + 3 <= len(raw):
        if raw[i] != START:
            i += 1; continue
        ln = raw[i+1]
        if ln == 0 or i + ln > len(raw):
            i += 1; continue
        if raw[i+2] == SERIAL:
            out.append(raw[i+3:i+ln])
        i += ln
    return out

def bridge_probe(port, baud):
    fd = open_serial(port, baud)
    try:
        payload = cmd_bytes("connect")
        os.write(fd, mmdvm_frame(payload))
        raw = read_for(fd, 1.0)
        data = b"".join(mmdvm_serial_payloads(raw))
        text = data.replace(b"\xff", b"").decode("ascii", "replace").strip("\x00\r\n ")
        return text if "comok" in text.lower() else ""
    finally:
        os.close(fd)

def bridge_send(port, baud, commands):
    fd = open_serial(port, baud)
    try:
        for command in commands:
            os.write(fd, mmdvm_frame(cmd_bytes(command)))
            time.sleep(0.04)
    finally:
        os.close(fd)

def direct_send(port, baud, commands):
    fd = open_serial(port, baud)
    try:
        for command in commands:
            os.write(fd, cmd_bytes(command))
            time.sleep(0.04)
    finally:
        os.close(fd)

def safe(s, limit=28):
    s = (s or "").encode("ascii", "replace").decode("ascii")
    return s.replace('"', "'")[:limit]

def screen_commands(state, message):
    pct, title = PROGRESS.get(state, (50, "PU2PNY"))
    msg = safe(message or title)
    fillw = max(2, int(276 * max(0, min(100, pct)) / 100))
    accent = 63488 if state == "error" else (65504 if state == "warning" else 2016)
    # Uses generic Nextion drawing instructions. No HMI firmware is replaced.
    return [
        "bkcmd=0",
        "dim=80",
        "cls 0",
        "draw 12,12,307,218,33808",
        "xstr 22,24,276,34,0,65535,0,1,1,1,\"PU2PNY\"",
        f"xstr 22,72,276,28,0,{accent},0,1,1,1,\"{safe(title)}\"",
        "draw 22,124,297,146,65535",
        f"fill 23,125,{fillw},20,{accent}",
        f"xstr 22,160,276,24,0,65535,0,1,1,1,\"{msg}\"",
        f"xstr 22,190,276,20,0,33808,0,1,1,1,\"{pct}%\"",
    ]

def service_active(name):
    return os.system(f"systemctl is-active --quiet {name} >/dev/null 2>&1") == 0

def radio_or_display_active():
    return service_active("2pny-mmdvmhost.service") or service_active("2pny-display.service")

def main():
    state = sys.argv[1] if len(sys.argv) > 1 else "boot"
    message = sys.argv[2] if len(sys.argv) > 2 else PROGRESS.get(state, (0, "PU2PNY"))[1]
    if radio_or_display_active():
        write_state(state, message, False, "radio-display-active")
        return 0

    try:
        hw = json.loads(HW.read_text())
    except Exception:
        write_state(state, message, False, "not-detected")
        return 0

    d = hw.get("display") or {}
    m = hw.get("mmdvm") or {}
    commands = screen_commands(state, message)

    try:
        if d.get("class") == "nextion" and d.get("port"):
            direct_send(str(d["port"]), int(d.get("baud") or 9600), commands)
            write_state(state, message, True, "nextion-direct")
            return 0

        if d.get("class") == "nextion_mmdvm" and m.get("port"):
            bridge_send(str(m["port"]), int(m.get("baud") or 115200), commands)
            write_state(state, message, True, "nextion-mmdvm")
            return 0
    except Exception as exc:
        write_state(state, message, False, "error:" + type(exc).__name__)
        return 0

    write_state(state, message, False, str(d.get("class") or "unsupported"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

