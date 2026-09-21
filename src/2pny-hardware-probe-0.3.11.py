#!/usr/bin/env python3
"""PU2PNY hardware discovery probe 0.3.11.

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

# 2PNY_RF_OWNERSHIP_GUARD
# Once MMDVMHost owns the modem, do not open the same UART merely to refresh the dashboard.
def radio_service_active():
    try:
        import subprocess
        return subprocess.run(["systemctl", "is-active", "--quiet", "2pny-mmdvmhost.service"], timeout=1).returncode == 0
    except Exception:
        return False



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
            driver = ""
            try:
                driver = (Path("/sys/class/tty") / Path(real).name / "device/driver").resolve().name
            except Exception:
                pass
            out.append({"path": dev, "realpath": real, "driver": driver})
    return out


def set_serial(fd, baud):
    attrs = termios.tcgetattr(fd)
    attrs[0] = 0
    attrs[1] = 0
    attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[3] = 0
    speed_map = {}
    for value, name in (
        (9600, "B9600"), (19200, "B19200"), (38400, "B38400"),
        (57600, "B57600"), (115200, "B115200"), (230400, "B230400"),
        (460800, "B460800"), (921600, "B921600"),
    ):
        if hasattr(termios, name):
            speed_map[value] = getattr(termios, name)
    if baud not in speed_map:
        raise ValueError("unsupported baud")
    speed = speed_map[baud]
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
    errors = []
    for baud in (115200, 460800):
        if baud == 460800 and not hasattr(termios, "B460800"):
            continue
        try:
            fd = open_port(dev, baud)
        except Exception as exc:
            errors.append(str(exc))
            continue
        try:
            request = bytes((0xE0, 0x03, 0x00))
            os.write(fd, request)
            result = parse_mmdvm(read_for(fd, 0.45))
            if result:
                result["baud"] = baud
                return result, None
        except Exception as exc:
            errors.append(str(exc))
        finally:
            try:
                os.close(fd)
            except Exception:
                pass
    return None, (errors[-1] if errors else None)



def parse_mmdvm_serial_payloads(raw):
    payloads = []
    i = 0
    while i + 3 <= len(raw):
        if raw[i] != 0xE0:
            i += 1
            continue
        length = raw[i + 1]
        if length < 3 or i + length > len(raw):
            i += 1
            continue
        if raw[i + 2] == 0x80:
            payloads.append(raw[i + 3:i + length])
        i += length
    return payloads


def probe_nextion_mmdvm(dev, modem_baud):
    # The MMDVM firmware serial-data channel (frame type 0x80) can bridge
    # commands to a display UART. A real "comok" reply confirms a Nextion.
    try:
        fd = open_port(dev, int(modem_baud or 115200))
    except Exception:
        return None
    try:
        command = b"connect\xff\xff\xff"
        frame = bytes((0xE0, len(command) + 3, 0x80)) + command
        os.write(fd, frame)
        raw = read_for(fd, 1.0)
        data = b"".join(parse_mmdvm_serial_payloads(raw))
        text = data.replace(b"\xff", b"").decode("ascii", "replace").strip("\x00\r\n ")
        if "comok" not in text.lower():
            return None
        parts = [part.strip() for part in text.split(",")]
        model = parts[2] if len(parts) >= 3 and parts[2] else "Nextion"
        return {
            "detected": True,
            "class": "nextion_mmdvm",
            "state": "mmdvm_serial_confirmed",
            "model": model,
            "port": "modem",
            "modem_port": dev,
            "modem_baud": int(modem_baud or 115200),
            "response": text,
            "confidence": "protocol",
            "message": "Nextion confirmou resposta pelo canal serial da MMDVM.",
        }
    except Exception:
        return None
    finally:
        try:
            os.close(fd)
        except Exception:
            pass

def probe_nextion(dev):
    # Identification only. Never uploads HMI firmware and never changes baud.
    for baud in (9600, 19200, 38400, 57600, 115200, 230400, 921600):
        try:
            fd = open_port(dev, baud)
        except Exception:
            continue
        try:
            os.write(fd, b"connect\xff\xff\xff")
            raw = read_for(fd, 0.45)
            text = raw.replace(b"\xff", b"").decode("ascii", "replace").strip("\x00\r\n ")
            if "comok" in text.lower():
                parts = [part.strip() for part in text.split(",")]
                model = parts[2] if len(parts) >= 3 and parts[2] else "Nextion"
                return {
                    "detected": True,
                    "class": "nextion",
                    "state": "direct_serial",
                    "port": dev,
                    "baud": baud,
                    "response": text,
                    "model": model,
                    "confidence": "protocol",
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




def usb_devices():
    found = []
    for base in sorted(Path("/sys/bus/usb/devices").glob("*")):
        vid = read_text(base / "idVendor")
        pid = read_text(base / "idProduct")
        if not vid or not pid:
            continue
        found.append({
            "vendor_id": vid,
            "product_id": pid,
            "manufacturer": read_text(base / "manufacturer"),
            "product": read_text(base / "product"),
            "serial": read_text(base / "serial"),
        })
    return found



def spi_devices():
    found = []
    for base in sorted(Path("/sys/bus/spi/devices").glob("spi*")):
        name = read_text(base / "modalias") or read_text(base / "name") or base.name
        found.append({"device": base.name, "name": name})
    return found


def usb_display():
    words = ("nextion", "tjc", "display", "screen", "lcd", "oled", "tft", "hdmi")
    for item in usb_devices():
        text = " ".join(str(item.get(k, "")) for k in ("manufacturer", "product")).lower()
        if any(w in text for w in words):
            model = item.get("product") or item.get("manufacturer") or "USB display"
            cls = "nextion" if ("nextion" in text or "tjc" in text) else "usb_display"
            return {
                "detected": True,
                "state": "usb_metadata",
                "class": cls,
                "model": model,
                "confidence": "usb_metadata",
            }
    return None


def display_outputs():
    found = []
    for status in sorted(Path("/sys/class/drm").glob("card*-*/status")):
        if read_text(status).lower() != "connected":
            continue
        found.append({"connector": status.parent.name, "state": "connected"})
    return found

def probe_configured_display(i2c, hat):
    addresses = {str(item.get("address", "")).lower() for item in i2c}
    candidate = None
    if "0x3c" in addresses or "0x3d" in addresses:
        addr = "0x3c" if "0x3c" in addresses else "0x3d"
        candidate = {"detected": False, "state": "i2c_candidate", "class": "display_candidate", "model": "Possível display I2C", "address": addr, "confidence": "candidate"}
    elif "0x27" in addresses or "0x3f" in addresses:
        addr = "0x27" if "0x27" in addresses else "0x3f"
        candidate = {"detected": False, "state": "i2c_candidate", "class": "display_candidate", "model": "Possível LCD/expansor I2C", "address": addr, "confidence": "candidate"}
    h = " ".join(str(hat.get(k, "")) for k in ("product", "vendor")).lower()
    if any(word in h for word in ("display", "screen", "lcd", "oled", "tft")):
        return {"detected": True, "state": "hat_metadata", "class": "hat_display", "model": hat.get("product") or "Display HAT", "confidence": "hat_metadata"}
    for fb in sorted(glob.glob("/sys/class/graphics/fb*")):
        name = read_text(Path(fb) / "name")
        low = name.lower()
        if name and any(word in low for word in ("tft", "lcd", "ili", "st77", "fb_", "waveshare")):
            return {"detected": True, "state": "framebuffer", "class": "framebuffer", "model": name, "device": fb, "confidence": "kernel"}
    return candidate

state = {
    "state": "scanning",
    "raspberry": {"model": read_text("/proc/device-tree/model"), "serial": ""},
    "hat": hat_info(),
    "serial_ports": serial_candidates(),
    "i2c": i2c_devices(),
    "usb": usb_devices(),
    "spi": spi_devices(),
    "display_outputs": display_outputs(),
    "mmdvm": {"detected": False, "duplex": "unknown", "capabilities": []},
    "display": {"detected": False, "state": "not_found"},
}

for line in read_text("/proc/cpuinfo").splitlines():
    if line.lower().startswith("serial") and ":" in line:
        state["raspberry"]["serial"] = line.split(":", 1)[1].strip()
        break
if radio_service_active() and OUT.exists():
    try:
        previous = json.loads(OUT.read_text())
        previous["state"] = "complete"
        previous["radio_engine"] = "active"
        save(previous)
        print(json.dumps(previous, ensure_ascii=False))
        raise SystemExit(0)
    except (ValueError, OSError):
        pass

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

if not state["mmdvm"].get("detected"):
    for item in state["serial_ports"]:
        if item.get("path") == "/dev/serial0":
            state["mmdvm"]["candidate_port"] = item["path"]
            state["mmdvm"]["candidate_realpath"] = item["realpath"]
            state["mmdvm"]["candidate_reason"] = "primary_uart"
            break

for item in state["serial_ports"]:
    if item["realpath"] == mmdvm_real:
        continue
    nextion = probe_nextion(item["path"])
    if nextion:
        state["display"] = dict(nextion, state="direct_serial")
        break

usb_candidate = usb_display()
if not state["display"].get("detected") and usb_candidate:
    state["display"] = usb_candidate

configured_display = probe_configured_display(state["i2c"], state["hat"])
if not state["display"].get("detected") and configured_display:
    state["display"] = configured_display

if not state["display"].get("detected"):
    for item in state.get("spi") or []:
        low = str(item.get("name", "")).lower()
        if any(word in low for word in ("ili934", "ili948", "st773", "st778", "gc9a", "ssd13", "lcd", "tft", "oled")):
            state["display"] = {
                "detected": True,
                "state": "spi_kernel",
                "class": "spi_display",
                "model": item.get("name") or "SPI display",
                "device": item.get("device"),
                "confidence": "kernel",
            }
            break

kernel_display = state.get("display_outputs") or []
if not state["display"].get("detected") and kernel_display:
    connector = kernel_display[0].get("connector", "display")
    state["display"] = {"detected": True, "state": "kernel_connector", "class": "video_output", "model": connector, "confidence": "kernel"}

if not state["display"].get("detected") and state["mmdvm"].get("detected"):
    # Do not reopen the MMDVM UART for display probing during the hardware step.
    # The modem version handshake already proved the radio hardware.  Nextion
    # confirmation through the modem is deferred until MMDVMHost owns the UART
    # and the MQTT display bridge is active, avoiding serial-state/race regressions.
    state["display"] = {
        "detected": False,
        "state": "mmdvm_display_candidate",
        "class": "display_candidate",
        "model": "Porta de display da MMDVM disponível",
        "port": "modem",
        "confidence": "candidate",
        "message": "MMDVM confirmada. A Nextion pela porta do modem será verificada automaticamente depois que o rádio iniciar.",
    }

state["state"] = "complete"
save(state)
print(json.dumps(state, ensure_ascii=False))