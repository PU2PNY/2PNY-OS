#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
TMP="$(mktemp -d)"
PIDS=()
cleanup(){
  set +e
  for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done
  rm -rf "$TMP"
}
trap cleanup EXIT

go build -trimpath -o "$TMP/direct" src/direct-core-0.3.24/*.go
"$TMP/direct" --selftest | grep -Fq DIRECT_SELFTEST_OK
python3 -m py_compile server/2pny-direct-server-0.3.24.py

python3 server/2pny-direct-server-0.3.24.py --host 127.0.0.1 --port 44370 >"$TMP/server.log" 2>&1 &
PIDS+=("$!")
sleep .3

start_clients(){
  local force="${1:-}"
  "$TMP/direct" --state-dir "$TMP/a" --callsign PU2AAA --server 127.0.0.1:44370 --api 127.0.0.1:44371 --protocol-override DMR --radio-gateway-port 45101 --radio-host-port 45102 --skip-systemd $force >"$TMP/a.log" 2>&1 &
  PIDS+=("$!")
  "$TMP/direct" --state-dir "$TMP/b" --callsign PU2BBB --server 127.0.0.1:44370 --api 127.0.0.1:44372 --protocol-override DMR --radio-gateway-port 45201 --radio-host-port 45202 --skip-systemd >"$TMP/b.log" 2>&1 &
  PIDS+=("$!")
  for _ in {1..60}; do
    curl -fsS http://127.0.0.1:44371/status >/dev/null 2>&1 && curl -fsS http://127.0.0.1:44372/status >/dev/null 2>&1 && break
    sleep .1
  done
  curl -fsS http://127.0.0.1:44371/status >/dev/null
  curl -fsS http://127.0.0.1:44372/status >/dev/null
  sleep .5
}

pair_both(){
  curl -fsS -X POST -H 'Content-Type: application/json' -d '{"callsign":"PU2BBB"}' http://127.0.0.1:44371/pair | grep -Fq '"ok":true'
  curl -fsS -X POST -H 'Content-Type: application/json' -d '{"callsign":"PU2AAA"}' http://127.0.0.1:44372/pair | grep -Fq '"ok":true'
}

wait_incoming(){
  local expected="$1"
  python3 - "$expected" <<'PY'
import json,sys,time,urllib.request
expected=sys.argv[1]
deadline=time.time()+8
while time.time()<deadline:
    with urllib.request.urlopen("http://127.0.0.1:44372/status",timeout=2) as r:s=json.load(r)
    if s.get("status")=="incoming":
        assert s.get("path")==expected,s
        assert s.get("radio_active") is False,s
        print("INCOMING_"+expected.upper())
        break
    time.sleep(.1)
else: raise SystemExit("incoming timeout")
PY
}

accept_b(){
  curl -fsS -X POST -H 'Content-Type: application/json' -d '{"callsign":"PU2AAA"}' http://127.0.0.1:44372/accept | grep -Fq '"ok":true'
}

assert_state(){
  local expected="$1"
  python3 - "$expected" <<'PY'
import json,sys,urllib.request
def get(url):
    with urllib.request.urlopen(url,timeout=2) as r:return json.load(r)
expected=sys.argv[1]
a=get("http://127.0.0.1:44371/status"); b=get("http://127.0.0.1:44372/status")
assert a["status"]=="connected" and a["path"]==expected,a
assert b["status"]=="connected" and b["path"]==expected,b
assert a["encrypted"] is True and b["encrypted"] is True
assert a["radio_active"] is True and b["radio_active"] is True
assert a["protocol"]=="DMR" and b["protocol"]=="DMR"
PY
}

assert_radio_roundtrip(){
  python3 - <<'PY'
import socket,time
A_HOST=45102; A_GW=45101; B_HOST=45202; B_GW=45201
a=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);a.bind(("127.0.0.1",A_HOST));a.settimeout(3)
b=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);b.bind(("127.0.0.1",B_HOST));b.settimeout(3)
time.sleep(.1)
a.sendto(b"DMRD-A-TO-B",("127.0.0.1",A_GW))
data,_=b.recvfrom(4096);assert data==b"DMRD-A-TO-B",data
b.sendto(b"DMRD-B-TO-A",("127.0.0.1",B_GW))
data,_=a.recvfrom(4096);assert data==b"DMRD-B-TO-A",data
a.close();b.close()
PY
}

call_and_accept(){
  local expected="$1"
  curl -fsS -X POST -H 'Content-Type: application/json' -d '{"callsign":"PU2BBB"}' http://127.0.0.1:44371/call >"$TMP/call.out" &
  local cp=$!
  wait_incoming "$expected"
  # Crucial regression: receiving the call must not take over RF before acceptance.
  python3 - <<'PY'
import json,urllib.request
with urllib.request.urlopen("http://127.0.0.1:44372/status",timeout=2) as r:s=json.load(r)
assert s["status"]=="incoming" and s["radio_active"] is False,s
PY
  accept_b
  wait "$cp"
  grep -Fq '"ok":true' "$TMP/call.out"
  assert_state "$expected"
}

# Direct path: incoming is pending until accepted.
start_clients
pair_both
call_and_accept Direct
assert_radio_roundtrip
curl -fsS -X POST http://127.0.0.1:44371/hangup | grep -Fq '"ok":true'
sleep .3

# Relay fallback: still end-to-end encrypted and still waits for radio acceptance.
kill "${PIDS[1]}" "${PIDS[2]}" 2>/dev/null || true
wait "${PIDS[1]}" 2>/dev/null || true
wait "${PIDS[2]}" 2>/dev/null || true
PIDS=("${PIDS[0]}")
start_clients "--force-relay"
sleep .5
call_and_accept Relay
assert_radio_roundtrip
curl -fsS -X POST -H 'Content-Type: application/json' -d '{"text":"73"}' http://127.0.0.1:44371/message | grep -Fq '"ok":true'
for _ in {1..30}; do grep -Fq 'Direct message from PU2AAA: 73' "$TMP/b.log" && break; sleep .1; done
grep -Fq 'Direct message from PU2AAA: 73' "$TMP/b.log"

! curl -fsS http://127.0.0.1:44371/peers | grep -qi 'private'
test -s "$TMP/a/identity.json"
test "$(stat -c '%a' "$TMP/a/identity.json")" = 600

echo DIRECT_0324_INTEGRATION_OK
