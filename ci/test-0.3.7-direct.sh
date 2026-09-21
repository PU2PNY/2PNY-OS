#!/usr/bin/env bash
set -Eeuo pipefail
TMP="$(mktemp -d)"
PIDS=()
cleanup(){
  set +e
  for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done
  rm -rf "$TMP"
}
trap cleanup EXIT

go build -trimpath -o "$TMP/direct" src/direct-core/*.go
"$TMP/direct" --selftest | grep -Fq DIRECT_SELFTEST_OK
python3 -m py_compile server/2pny-direct-server-0.3.7.py

python3 server/2pny-direct-server-0.3.7.py --host 127.0.0.1 --port 44370 >"$TMP/server.log" 2>&1 &
PIDS+=("$!")
sleep .3

start_clients(){
  local force="${1:-}"
  "$TMP/direct" --state-dir "$TMP/a" --callsign PU2AAA --server 127.0.0.1:44370 --api 127.0.0.1:44371 $force >"$TMP/a.log" 2>&1 &
  PIDS+=("$!")
  "$TMP/direct" --state-dir "$TMP/b" --callsign PU2BBB --server 127.0.0.1:44370 --api 127.0.0.1:44372 >"$TMP/b.log" 2>&1 &
  PIDS+=("$!")
  for _ in {1..50}; do
    curl -fsS http://127.0.0.1:44371/status >/dev/null 2>&1 && curl -fsS http://127.0.0.1:44372/status >/dev/null 2>&1 && break
    sleep .1
  done
  curl -fsS http://127.0.0.1:44371/status >/dev/null
  curl -fsS http://127.0.0.1:44372/status >/dev/null
  sleep .4
}

pair_both(){
  curl -fsS -X POST -H 'Content-Type: application/json' -d '{"callsign":"PU2BBB"}' http://127.0.0.1:44371/pair | grep -Fq '"ok":true'
  curl -fsS -X POST -H 'Content-Type: application/json' -d '{"callsign":"PU2AAA"}' http://127.0.0.1:44372/pair | grep -Fq '"ok":true'
}

# Direct path.
start_clients
pair_both
curl -fsS -X POST -H 'Content-Type: application/json' -d '{"callsign":"PU2BBB"}' http://127.0.0.1:44371/call | grep -Fq '"ok":true'
python3 - <<'PY'
import json,urllib.request,time
def get(url):
    with urllib.request.urlopen(url,timeout=2) as r:return json.load(r)
a=get("http://127.0.0.1:44371/status"); b=get("http://127.0.0.1:44372/status")
assert a["status"]=="connected" and a["path"]=="Direct",a
assert b["status"]=="connected" and b["path"]=="Direct",b
assert a["encrypted"] is True and b["encrypted"] is True
PY
curl -fsS -X POST http://127.0.0.1:44371/hangup | grep -Fq '"ok":true'
sleep .2
python3 - <<'PY'
import json,urllib.request
with urllib.request.urlopen("http://127.0.0.1:44372/status",timeout=2) as r:b=json.load(r)
assert b["status"]=="idle" and b["path"]=="Offline",b
PY

# Restart clients with persisted peer identities and force A through the relay.
kill "${PIDS[1]}" "${PIDS[2]}" 2>/dev/null || true
wait "${PIDS[1]}" 2>/dev/null || true
wait "${PIDS[2]}" 2>/dev/null || true
PIDS=("${PIDS[0]}")
start_clients "--force-relay"
sleep .4
curl -fsS -X POST -H 'Content-Type: application/json' -d '{"callsign":"PU2BBB"}' http://127.0.0.1:44371/call | grep -Fq '"ok":true'
python3 - <<'PY'
import json,urllib.request
def get(url):
    with urllib.request.urlopen(url,timeout=2) as r:return json.load(r)
a=get("http://127.0.0.1:44371/status"); b=get("http://127.0.0.1:44372/status")
assert a["status"]=="connected" and a["path"]=="Relay",a
assert b["status"]=="connected" and b["path"]=="Relay",b
assert a["encrypted"] is True and b["encrypted"] is True
PY
curl -fsS -X POST -H 'Content-Type: application/json' -d '{"text":"73"}' http://127.0.0.1:44371/message | grep -Fq '"ok":true'
grep -Fq 'Direct message from PU2AAA: 73' "$TMP/b.log"

# Private keys must never appear in the public API.
! curl -fsS http://127.0.0.1:44371/peers | grep -qi 'private'
test -s "$TMP/a/identity.json"
test "$(stat -c '%a' "$TMP/a/identity.json")" = 600

echo DIRECT_INTEGRATION_OK
