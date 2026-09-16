#!/usr/bin/env python3
"""2PNY hardware discovery probe.

Identification-only. It does not set frequency, RF levels, modem mode, or flash firmware.
"""
import glob
import json
import os
import re
import select
import termios
import time
from pathlib import Path

OUT = Path("/var/lib/2pny/hardware-probe.json")
OUT.parent.mkdir(parents=True, exist_ok=True)


def read_text(path):
    try:
        return Path(path).read_bytes().replace(b"\x00", b"").decode("utf-8", "replace").strip()
    except Exception:
        return ""


def save(obj):
    obj["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, OUT)


def serial_candidates():
    patterns = [
        "/dev/serial0",
        "/dev/ttyAMA0",
        "/dev/ttyS0",
        "/dev/ttyACM*",
        "/dev/ttyUSB*",
        "/dev/serial/by-id/*",
    ]
    out, seen = [], set()
    for pattern in patterns:
        for dev in glob.glob(pattern):
            try:
                real = os.path.realpath(dev)
                st = os.stat(real)
                key = (st.st_rdev, real)
            except Exception:
                continue
            if key in seen:
                continue
            seen.add(key)
            out.append({"path": dev, "realpath": real})
    return out


def set_serial(fd, baud):
    attrs = termios.tcgetattr(fd)
    attrs[0] = 0
    attrs[1] = 0
    attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[3] = 0
    speed = {9600: termios.B9600, 115200: termios.B115200}[baud]
    attrs[4] = speed
    attrs[5] = speed
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 2
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)


def open_port(path, baud):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    set_serial(fd, baud)
    return fd


def read_for(fd, seconds=0.8, limit=1024):
    deadline = time.monotonic() + seconds
    data = bytearray()
    while time.monotonic() < deadline and len(data) < limit:
        wait = max(0.0, min(0.12, deadline - time.monotonic()))
        ready, _, _ = select.select([fd], [], [], wait)
        if not ready:
            continue
        try:
            chunk = os.read(fd, min(256, limit - len(data)))
        except BlockingIOError:
            continue
        if chunk:
            data.extend(chunk)
    return bytes(data)


def parse_mmdvm(raw):
    for pos, value in enumerate(raw):
        if value != 0xE0 or pos + 4 > len(raw):
            continue
        length = raw[pos + 1]
        if length < 4 or pos + length > len(raw):
            continue
        frame = raw[pos : pos + length]
        if frame[2] != 0x00:
            continue

        protocol = frame[3]
        cap1 = cap2 = 0
        cpu = "Não informado"
        udid = ""
        description = ""

        if protocol == 1:
            cap1, cap2 = 0x1F, 0x01
            description = frame[4:].decode("utf-8", "replace").strip("\x00 \r\n")
        elif protocol == 2 and len(frame) >= 23:
            cap1, cap2 = frame[4], frame[5]
            cpu = {0: "Atmel ARM", 1: "NXP ARM", 2: "ST-Micro ARM"}.get(
                frame[6], f"Tipo {frame[6]}"
            )
            udid = "".join(f"{value:02X}" for value in frame[7:23])
            description = frame[23:].decode("utf-8", "replace").strip("\x00 \r\n")
        else:
            description = frame[4:].decode("utf-8", "replace").strip("\x00 \r\n")

        modes = []
        for bit, name in (
            (0x01, "D-Star"),
            (0x02, "DMR"),
            (0x04, "YSF"),
            (0x08, "P25"),
            (0x10, "NXDN"),
            (0x40, "FM"),
        ):
            if cap1 & bit:
                modes.append(name)
        if cap2 & 0x01:
            modes.append("POCSAG")

        profile = "MMDVM compatível"
        low = description.lower()
        if "mmdvm_hs" in low or "mmdvm hs" in low:
            profile = "MMDVM_HS compatível"
        elif "zumspot" in low:
            profile = "ZUMspot (identificação do firmware)"

        return {
            "detected": True,
            "protocol_version": protocol,
            "description": description or "Firmware MMDVM sem descrição",
            "profile": profile,
            "cpu": cpu,
            "udid": udid,
            "capabilities": modes,
            "duplex": "unknown",
        }
    return None


def probe_mmdvm(dev):
    try:
        fd = open_port(dev, 115200)
    except Exception as exc:
        return None, str(exc)
    try:
        # Official framing used by MMDVMHost: frame start E0, len 3, GET_VERSION 00.
        request = bytes((0xE0, 0x03, 0x00))
        os.write(fd, request)
        return parse_mmdvm(read_for(fd, 1.0)), None
    except Exception as exc:
        return None, str(exc)
    finally:
        try:
            os.close(fd)
        except Exception:
            pass


def probe_nextion(dev):
    # Identification only. No HMI upload and no persistent display settings.
    for baud in (9600, 115200):
        try:
            fd = open_port(dev, baud)
        except Exception:
            continue
        try:
            os.write(fd, b"connect\xff\xff\xff")
            raw = read_for(fd, 0.7)
            text = raw.replace(b"\xff", b"").decode("ascii", "replace").strip("\x00\r\n ")
            if "comok" in text.lower():
                parts = [part.strip() for part in text.split(",")]
                model = parts[2] if len(parts) >= 3 and parts[2] else "Nextion"
                return {
                    "detected": True,
                    "port": dev,
                    "baud": baud,
                    "response": text,
                    "model": model,
                }
        except Exception:
            pass
        finally:
            try:
                os.close(fd)
            except Exception:
                pass
    return None


def hat_info():
    base = Path("/proc/device-tree/hat")
    if not base.exists():
        return {"detected": False}
    return {
        "detected": True,
        "product": read_text(base / "product"),
        "vendor": read_text(base / "vendor"),
        "uuid": read_text(base / "uuid"),
    }


def i2c_devices():
    devices = []
    for path in glob.glob("/sys/bus/i2c/devices/*-*"):
        base = os.path.basename(path)
        match = re.match(r"^(\d+)-([0-9a-fA-F]{4})$", base)
        if not match:
            continue
        devices.append(
            {
                "bus": int(match.group(1)),
                "address": "0x" + match.group(2)[-2:].lower(),
                "name": read_text(Path(path) / "name"),
            }
        )
    return devices


state = {
    "state": "scanning",
    "raspberry": {"model": read_text("/proc/device-tree/model"), "serial": ""},
    "hat": hat_info(),
    "serial_ports": serial_candidates(),
    "i2c": i2c_devices(),
    "mmdvm": {"detected": False, "duplex": "unknown", "capabilities": []},
    "display": {"detected": False, "state": "not_found"},
}

for line in read_text("/proc/cpuinfo").splitlines():
    if line.lower().startswith("serial") and ":" in line:
        state["raspberry"]["serial"] = line.split(":", 1)[1].strip()
        break
save(state)

mmdvm_real = None
for item in state["serial_ports"]:
    result, error = probe_mmdvm(item["path"])
    item["mmdvm_probe"] = "ok" if result else ("error" if error else "no_response")
    if result:
        result["port"] = item["path"]
        result["realpath"] = item["realpath"]
        state["mmdvm"] = result
        mmdvm_real = item["realpath"]
        break

for item in state["serial_ports"]:
    if item["realpath"] == mmdvm_real:
        continue
    nextion = probe_nextion(item["path"])
    if nextion:
        state["display"] = dict(nextion, state="direct_serial")
        break

if not state["display"].get("detected") and state["mmdvm"].get("detected"):
    state["display"] = {
        "detected": False,
        "state": "via_mmdvm_pending",
        "message": (
            "MMDVM detectada. A Nextion ligada ao conector do modem será confirmada "
            "pela camada Display/MMDVM."
        ),
    }

state["state"] = "complete"
save(state)
print(json.dumps(state, ensure_ascii=False))
