#!/usr/bin/env python3
import importlib.util, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("core",ROOT/"src/2pny-live-core-0.2.9.py")
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)

t=1_700_000_000.0
s=core.LiveState(history_limit=20,metric_limit=8)
s.ingest("M: DMR Slot 2, received network voice header from PU4RMF to TG 6",t)
assert s.snapshot()["active"]["mode"]=="rx"
assert s.snapshot()["network"]["state"]=="connected"
e=s.ingest("M: DMR Slot 2, received network end of voice transmission from PU4RMF to TG 6, 12.4 seconds, 0% packet loss, BER: 0.2%",t+12.4)
assert e and e["duration"]==12.4 and e["ber"]==0.2
assert s.snapshot()["standby"]

s.ingest("M: DMR Slot 2, received RF voice header from PU2PNY to TG 6",t+20)
e=s.ingest("M: DMR Slot 2, received RF end of voice transmission from PU2PNY to TG 6, 3.2 seconds, BER: 0.3%, RSSI: -101/-96/-88 dBm",t+23.2)
assert e["rssi_min"]==-101 and e["rssi_peak"]==-88 and s.snapshot()["standby"]

s.ingest("M: DMR Slot 2, received RF voice header from PU2PNY to TG 72444",t+30)
s.ingest("M: Debug: Mode set to Idle",t+34)
assert s.snapshot()["standby"]
assert s.snapshot()["history"][0]["ended_by"]=="idle"
print("0.2.9 live parser regression: OK")
