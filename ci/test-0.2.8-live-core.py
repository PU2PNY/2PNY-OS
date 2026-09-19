#!/usr/bin/env python3
import importlib.util, json, pathlib, sys, time, tracemalloc

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("core", ROOT/"src/2pny-live-core-0.2.8.py")
core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

s = core.LiveState(history_limit=200, metric_limit=64)
t = 1_700_000_000.0
start = s.ingest("M: 2023-11-14 22:13:20.000 DMR Slot 2, received RF voice header from PU2PNY to TG 6", t)
assert start["mode"] == "tx" and start["ber"] is None and start["rssi"] is None
assert s.snapshot()["active"]["source"] == "PU2PNY"
end = s.ingest("M: DMR Slot 2, received RF end of voice transmission, 4.2 seconds, BER: 0.8%, RSSI: -112/-108/-104 dBm", t+4.2)
assert end["ber"] == 0.8 and end["rssi_min"] == -112 and end["rssi_peak"] == -104
assert s.snapshot()["standby"] and len(s.snapshot()["history"]) == 1

s.ingest("M: DMR Slot 1, received network voice header from 724001 to TG 724", t+5)
assert s.snapshot()["active"]["mode"] == "rx"
s.ingest("M: DMR Slot 1, BER: 1.2%, reported RSSI: -99 dBm", t+6)
assert s.snapshot()["active"]["ber"] == 1.2 and s.snapshot()["active"]["rssi"] == -99
s.ingest("Logged into the master successfully", t+7, gateway=True)
assert s.snapshot()["network"]["state"] == "connected"

for i in range(100): s.add_probe(i % 20 != 0, 30 + (i % 5))
assert len(s.metrics) == 64 and s.mtr_summary()["samples"] == 64

tracemalloc.start(); before = tracemalloc.get_traced_memory()[0]; started = time.perf_counter()
for i in range(36000):
    base=t+10+i
    s.ingest(f"DMR Slot 2, received RF voice header from PU2PNY to TG {i%100}", base)
    s.ingest("DMR Slot 2, received RF end of voice transmission, 1.0 seconds, BER: 0.1%, RSSI: -110 dBm", base+1)
after, peak = tracemalloc.get_traced_memory(); elapsed=time.perf_counter()-started
assert len(s.history) == 200 and after-before < 3_000_000
result={"events":72000,"elapsed_seconds":round(elapsed,3),"events_per_second":round(72000/elapsed),
        "retained_bytes":after-before,"peak_bytes":peak,"snapshot_bytes":len(json.dumps(s.snapshot()))}
print(json.dumps(result, separators=(",", ":")))
