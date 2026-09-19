#!/usr/bin/env python3
import importlib.util,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("core",ROOT/"src/2pny-live-core-0.3.1.py")
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
t=1_800_000_000.0

# DMR RF start followed by upstream-style source-less END.
s=core.LiveState(history_limit=20,metric_limit=8)
s.ingest_json({"DMR":{"source":"rf","action":"start","slot":2,"src_info":"PU2PNY / 7240000","group":"yes","dst_id":6}},t)
assert s.snapshot()["active"]["mode"]=="tx"
e=s.ingest_json({"DMR":{"action":"end","slot":2,"duration":3.4,"ber":0.2,
                        "rssi":{"min":-105,"ave":-97,"max":-90}}},t+3.4)
assert e and e["direction"]=="RF" and e["duration"]==3.4 and e["ber"]==0.2
assert s.snapshot()["standby"],s.snapshot()

# DMR network source-less END must close NETWORK rather than invent RF.
s.ingest_json({"DMR":{"source":"network","action":"start","slot":2,"src_info":"PU4RMF / 7249999","group":"yes","dst_id":724}},t+10)
e=s.ingest_json({"DMR":{"action":"end","slot":2,"duration":5.0,"loss":1.5,"ber":0.1}},t+15)
assert e and e["direction"]=="NETWORK" and e["loss"]==1.5
assert s.snapshot()["standby"]

# D-Star uses the same upstream source-less END convention.
s.ingest_json({"D-Star":{"source":"rf","action":"start","src_callsign":"PU2PNY","src_ext":"A","dst_callsign":"CQCQCQ","reflector":"XLX026 D"}},t+20)
e=s.ingest_json({"D-Star":{"action":"end","duration":2.0,"ber":0.3}},t+22)
assert e and e["direction"]=="RF" and e["protocol"]=="DSTAR"
assert s.snapshot()["standby"]

print("0.3.1 MQTT source-less END regression: OK")
