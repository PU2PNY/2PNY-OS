#!/usr/bin/env python3
"""PU2PNY-OS 5.13.003 display/network software regression tests."""
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"ci/patch-image-5.13.003.py"
DISPLAY=ROOT/"src/2pny-display-core-0.3.31.py"

def load_display():
    spec=importlib.util.spec_from_file_location("pny_display_513003",DISPLAY)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    patch_text=PATCH.read_text()
    compile(patch_text,str(PATCH),"exec")
    for path in (ROOT/"ci/build-5.13.003.py",ROOT/"ci/test-5.13.003-ap.py"):
        compile(path.read_text(),str(path),"exec")
    for marker in ("dhcp-leasefile=%s/dnsmasq-ap.leases",
                   "check_ap_health","ap_dhcp=","ap_dns=","ap_http=",
                   "2pny-display-core-0.3.31.py","board-id","enable_ap_forwarding(){",
                   "systemctl --no-block restart 2pnyd.service"):
        assert marker in patch_text, "missing patch marker: "+marker
    display=load_display()
    with tempfile.TemporaryDirectory(prefix="pny-display-test-") as tmp:
        base=Path(tmp);proc=base/"proc";sys=base/"sys";root=base/"root"
        (proc/"device-tree").mkdir(parents=True)
        (proc/"device-tree"/"model").write_bytes(b"Orange Pi Zero H2+\0")
        (proc/"meminfo").write_text("MemTotal: 524288 kB\nMemAvailable: 262144 kB\n")
        (proc/"uptime").write_text("172800.0 0.0\n")
        (proc/"stat").write_text("cpu 100 0 100 800 0 0 0 0 0 0\n")
        (sys/"class/thermal/thermal_zone0").mkdir(parents=True)
        (sys/"class/thermal/thermal_zone0"/"temp").write_text("52000\n")
        (sys/"devices/system/cpu/cpu0/cpufreq").mkdir(parents=True)
        (sys/"devices/system/cpu/cpu0/cpufreq"/"scaling_cur_freq").write_text("1000000\n")
        root.mkdir()
        telemetry={"cpu_percent":24,"temperature_c":52,"memory_used_mb":256,
                   "memory_total_mb":512,"disk_used_percent":71}
        hardware={"mmdvm":{"detected":True,"profile":"MMDVM_HS",
                           "description":"MMDVM_HS_Hat-v1.6.1","protocol_version":2,
                           "cpu":"STM32","capabilities":["DMR","D-Star","YSF","P25","NXDN","POCSAG"]}}
        network={"uplink_type":"AP","setup_ip":"10.43.0.1"}
        info=display.collect_display_info(telemetry,hardware,network,proc,sys,root)
        assert info["board_model"]=="Orange Pi Zero H2+"
        assert info["cpu_percent"]==24 and info["temperature_c"]==52
        assert info["memory_percent"]==50 and info["disk_used_percent"]==71
        assert info["cpu_frequency_mhz"]==1000
        assert info["ip"]=="10.43.0.1" and info["uplink_type"]=="AP"
        assert info["mmdvm_detected"] is True and "DMR" in info["mmdvm_capabilities"]
        assert "CPU 24%" in display.display_system_line(info)
        assert "Orange Pi Zero H2+" in display.display_info_line(info,0)
        assert "MMDVM_HS_Hat-v1.6.1" in display.display_info_line(info,1)
        assert "DMR" in display.display_info_line(info,1)
        assert "UP 2d" in display.display_info_line(info,2)
        unknown=display.collect_display_info({}, {}, {},proc_root=base/"missing-proc",
                                             sys_root=base/"missing-sys",root_path=root)
        assert unknown["temperature_c"] is None and unknown["mmdvm_detected"] is False
        assert "MMDVM NOT CONFIRMED" in display.display_info_line(unknown,1)

    # Active RF panels retain the previously approved network, source/target
    # and quality fields. New hardware telemetry rotates only on standby.
    original_reader=display.read_network_status
    display.read_network_status=lambda: {"uplink_type":"wifi","default_ip":"10.43.0.1"}
    try:
        live={"active":{"mode":"rx","protocol":"DMR","source":"TEST","target":"TG 6",
                        "direction":"NET","operator":{"name":"TEST NAME"}},
              "internet":{"quality":"good","latency_ms":42}}
        drv=display.Nextion("nextion_mmdvm",width=320,height=240)
        nextion_commands=[]
        drv.send_page=lambda page,cmds:nextion_commands.extend(cmds)
        drv.render(live,{"protocol":"DMR"},{"_display_info":info})
        assert any("TEST" in c for c in nextion_commands)
        assert any("TG 6" in c for c in nextion_commands)
        assert any("10.43.0.1" in c for c in nextion_commands), "Nextion network information lost during RX"
        lcd=object.__new__(display.LCD)
        lcd.cols=20;lcd.rows=4
        captured=[]
        lcd.show=lambda lines:captured.extend(lines)
        lcd.render(live,{"protocol":"DMR"},{"_display_info":info})
        assert captured[0].startswith("RX DMR")
        assert captured[2]=="TG 6"
        assert "10.43.0.1" in captured[3], "LCD network information lost during RX"
    finally:
        display.read_network_status=original_reader
    print("5.13.003_DISPLAY_TELEMETRY_SW_PASS")

if __name__=="__main__":main()
