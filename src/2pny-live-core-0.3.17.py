#!/usr/bin/env python3
"""PU2PNY live-state core 0.3.1.

Authoritative live telemetry comes from MMDVM-Host's local MQTT JSON stream.
Journal parsing remains only as a compatibility fallback.  The state machine
is bounded, RAM-first and has no RF/configuration write path.
"""
from __future__ import annotations
import datetime as dt
import re
import time
from collections import deque

DMR_HEADER_RE = re.compile(
    r"DMR Slot (\d), received (RF|network) voice header from (.+?) to (TG )?([^,]+)", re.I)
DMR_END_HEAD_RE = re.compile(
    r"DMR Slot (\d), (?:received )?(RF|network) "
    r"(?:end of voice transmission|voice transmission lost|watchdog has expired)", re.I)
DURATION_RE = re.compile(r"([0-9.]+) seconds", re.I)
LOSS_RE = re.compile(r"([0-9.]+)% packet loss", re.I)
BER_RE = re.compile(r"BER:\s*([0-9.]+)%", re.I)
RSSI_RE = re.compile(r"RSSI:\s*([^,]+?dBm)(?:$|,)", re.I)
IDLE_RE = re.compile(r"(?:Debug:\s*)?Mode set to Idle", re.I)
ALIAS_RE = re.compile(r"DMR Slot (\d).*?(?:talker alias|alias).*?[:=]\s*(.+)$", re.I)
LIVE_BER_RE = re.compile(r"DMR Slot (\d).*?BER:\s*([0-9.]+)%", re.I)
LIVE_RSSI_RE = re.compile(r"DMR Slot (\d).*?(?:reported )?RSSI[:=]\s*(-?[0-9.]+)\s*dBm", re.I)

DSTAR_START_RE = re.compile(
    r"D-Star, received (RF|network) (?:header|late entry) from\s+([^/\s,]+)\s*(?:/\s*([^\s,]+))?\s+to\s+([^,]+?)(?:\s+via\s+([^,]+))?$", re.I)
DSTAR_END_RE = re.compile(
    r"D-Star, (?:received )?(RF|network) (?:end of transmission|transmission lost).*?from\s+([^/\s,]+)\s*(?:/\s*([^\s,]+))?\s+to\s+([^,]+)", re.I)

YSF_RF_START_RE = re.compile(r"YSF, received RF (?:header|late entry) from\s+(.+?)\s+to DG-ID\s+(\d+)", re.I)
YSF_NET_START_RE = re.compile(r"YSF, received network data from\s+(.+?)\s+to DG-ID\s+(\d+)(?:\s+at\s+(.+))?$", re.I)
YSF_END_RE = re.compile(r"YSF, received (RF|network) end of transmission from\s+(.+?)\s+to DG-ID\s+(\d+)", re.I)

P25_START_RE = re.compile(r"P25, received (RF|network) (?:voice )?transmission from\s+(.+?)\s+to\s+(TG\s+)?(\d+)", re.I)
P25_END_RE = re.compile(r"P25, (?:received )?(RF|network) (?:end of voice transmission|end of transmission) from\s+(.+?)\s+to\s+(TG\s+)?(\d+)", re.I)

NXDN_START_RE = re.compile(r"NXDN, received (RF|network) (?:header|transmission|late entry) from\s+(.+?)\s+to\s+(TG\s+)?(\d+)", re.I)
NXDN_END_RE = re.compile(r"NXDN, (?:received )?(RF|network) end of transmission from\s+(.+?)\s+to\s+(TG\s+)?(\d+)", re.I)

def iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()

def _clean(value):
    return str(value or "").strip()

def _source_callsign(text):
    text=_clean(text)
    if not text:
        return ""
    # MMDVM's src_info is normally "<callsign> / <id>" or a callsign/ID.
    for token in re.split(r"[\s/]+", text):
        u=token.upper()
        if re.fullmatch(r"[A-Z]{1,3}\d[A-Z0-9]{1,4}", u):
            return u
    m=re.search(r"\b\d{5,9}\b", text)
    return m.group(0) if m else text[:40]

def quality(ber=None, rssi=None):
    if ber is None and rssi is None:
        return {"label":"unavailable","score":None}
    score=100.0
    if ber is not None:
        score-=min(70.0,float(ber)*14.0)
    if rssi is not None:
        value=float(rssi)
        score-=45 if value < -125 else 25 if value < -115 else 10 if value < -105 else 0
    score=max(0,min(100,round(score)))
    return {"label":"excellent" if score>=80 else "good" if score>=55 else "poor","score":score}

class LiveState:
    def __init__(self, history_limit=200, metric_limit=64):
        self.history=deque(maxlen=history_limit)
        self.metrics=deque(maxlen=metric_limit)
        self.active={"RF":None,"NETWORK":None}
        self.aliases={}
        self.network={"state":"unknown","message":"waiting","updated":None}
        self.sequence=0
        self.changed=True

    def _touch(self):
        self.sequence+=1
        self.changed=True

    def _start(self, protocol, direction, source, target, ts, **extra):
        direction=direction.upper()
        event={
            "event":"start","protocol":protocol,"direction":direction,
            "mode":"tx" if direction=="RF" else "rx",
            "source":_clean(source),"target":_clean(target),
            "started_at":iso(ts),"started_unix_ms":round(ts*1000),
            "ber":None,"rssi":None,"rssi_min":None,"rssi_avg":None,
            "rssi_peak":None,"quality":quality(),
        }
        event.update({k:v for k,v in extra.items() if v not in (None,"")})
        self.active[direction]=event
        if direction=="NETWORK" and self.network.get("state")!="connected":
            self.network={"state":"connected","message":"traffic confirmed","updated":iso(ts)}
        self._touch()
        return event

    def _finish(self, direction, ts, duration=None, ber=None, loss=None, rssi_values=None, reason=None, **fallback):
        direction=direction.upper()
        current=self.active.get(direction)
        if current:
            result=dict(current)
        else:
            duration=float(duration or 0)
            result={
                "protocol":fallback.get("protocol",""),
                "direction":direction,"mode":"tx" if direction=="RF" else "rx",
                "source":_clean(fallback.get("source")),"target":_clean(fallback.get("target")),
                "started_at":iso(ts-duration),"started_unix_ms":round((ts-duration)*1000),
            }
            for key in ("slot","reflector","module","dgid"):
                if fallback.get(key) not in (None,""):
                    result[key]=fallback[key]
        if duration is None:
            started=int(result.get("started_unix_ms") or round(ts*1000))/1000.0
            duration=max(0.0,ts-started)
        result.update({"event":"end","ended_at":iso(ts),"duration":round(float(duration),2)})
        if ber is not None: result["ber"]=float(ber)
        if loss is not None: result["loss"]=float(loss)
        if rssi_values:
            vals=[float(x) for x in rssi_values]
            result["rssi"]=vals[-1];result["rssi_min"]=min(vals);result["rssi_peak"]=max(vals)
            result["rssi_avg"]=round(sum(vals)/len(vals),1)
        if reason: result["ended_by"]=reason
        result["quality"]=quality(result.get("ber"),result.get("rssi_avg",result.get("rssi")))
        self.history.appendleft(result)
        self.active[direction]=None
        if direction=="NETWORK" and self.network.get("state")!="connected":
            self.network={"state":"connected","message":"traffic confirmed","updated":iso(ts)}
        self._touch()
        return result

    def _metric(self, protocol, slot=None, ber=None, rssi=None):
        current=None
        # LIVE-016: BER/RSSI originate from the RF modem. Never attach them to
        # a simultaneous NETWORK event just because protocol/slot matches.
        rf_item=self.active.get("RF")
        if rf_item and rf_item.get("protocol")==protocol and (slot is None or rf_item.get("slot") in (None,slot)):
            current=rf_item
        if not current:
            return None
        if ber is not None: current["ber"]=float(ber)
        if rssi is not None:
            value=float(rssi);current["rssi"]=value
            samples=current.setdefault("_rssi_samples",[])
            samples.append(value);del samples[:-32]
            current["rssi_min"]=min(samples);current["rssi_peak"]=max(samples)
            current["rssi_avg"]=round(sum(samples)/len(samples),1)
        current["quality"]=quality(current.get("ber"),current.get("rssi_avg",current.get("rssi")))
        self._touch()
        return current

    def ingest_json(self, payload, ts=None):
        ts=time.time() if ts is None else float(ts)
        if not isinstance(payload,dict): return None
        if isinstance(payload.get("MMDVM"),dict):
            mode=str(payload["MMDVM"].get("mode") or "").lower()
            if mode=="idle" and any(self.active.values()):
                out=[]
                for direction,current in list(self.active.items()):
                    if current: out.append(self._finish(direction,ts,reason="idle"))
                return out[-1] if out else None
            return None
        if isinstance(payload.get("RSSI"),dict):
            j=payload["RSSI"];proto=str(j.get("mode") or "").replace("D-Star","DSTAR").replace("YSF","YSF").upper()
            return self._metric(proto,int(j["slot"]) if j.get("slot") is not None else None,rssi=j.get("value"))
        if isinstance(payload.get("BER"),dict):
            j=payload["BER"];proto=str(j.get("mode") or "").replace("D-Star","DSTAR").upper()
            return self._metric(proto,int(j["slot"]) if j.get("slot") is not None else None,ber=j.get("value"))

        for key,proto in (("DMR","DMR"),("D-Star","DSTAR"),("YSF","YSF"),("P25","P25"),("NXDN","NXDN")):
            j=payload.get(key)
            if not isinstance(j,dict): continue
            action=str(j.get("action") or "").lower()
            source=str(j.get("source") or "").lower().strip()
            direction="RF" if source=="rf" else "NETWORK" if source=="network" else ""
            slot=int(j.get("slot") or 0) or None

            if action in ("start","late_entry"):
                # Start/late-entry messages from MMDVMHost always carry source.
                # If an exotic firmware omits it, prefer RF rather than creating
                # a phantom network event; the following end/idle will still close it.
                if not direction: direction="RF"
                if proto=="DMR":
                    src=_source_callsign(j.get("src_info"))
                    target=("TG " if str(j.get("group")).lower()=="yes" else "")+str(j.get("dst_id") or "")
                    return self._start(proto,direction,src,target,ts,slot=slot,
                                       src_info=_clean(j.get("src_info")))
                if proto=="DSTAR":
                    src=_clean(j.get("src_callsign"));ext=_clean(j.get("src_ext"))
                    return self._start(proto,direction,src,_clean(j.get("dst_callsign")),ts,
                                       src_ext=ext,reflector=_clean(j.get("reflector")))
                if proto=="YSF":
                    return self._start(proto,direction,_clean(j.get("src_callsign")),"DG-ID "+str(j.get("dg-id") or 0),ts,
                                       dgid=j.get("dg-id"),reflector=_clean(j.get("reflector")))
                src=_source_callsign(j.get("src_info"))
                target=("TG " if str(j.get("group")).lower()=="yes" else "")+str(j.get("dst_id") or "")
                return self._start(proto,direction,src,target,ts,src_info=_clean(j.get("src_info")))

            if action in ("end","lost","timeout"):
                # Important upstream detail: MMDVMHost's RF and network END JSON
                # records contain action/duration/BER/loss but do NOT contain
                # source=rf/network. Infer the direction from the matching live
                # event instead of treating a source-less END as network.
                if not direction:
                    candidates=[]
                    for d,cur in self.active.items():
                        if not cur or cur.get("protocol")!=proto: continue
                        if slot is not None and cur.get("slot") not in (None,slot): continue
                        candidates.append((d,cur))
                    if candidates:
                        # If both directions somehow coexist, close the most
                        # recently started matching event.
                        direction=max(candidates,key=lambda x:int(x[1].get("started_unix_ms") or 0))[0]
                    else:
                        return None

                duration=j.get("duration")
                ber=j.get("ber")
                loss=j.get("loss")
                rssi=j.get("rssi")
                rssi_values=None
                if isinstance(rssi,dict):
                    vals=[rssi.get("min"),rssi.get("ave"),rssi.get("max")]
                    rssi_values=[v for v in vals if isinstance(v,(int,float))]
                try: duration=float(duration) if duration is not None else None
                except Exception: duration=None
                try: ber=float(ber) if ber is not None else None
                except Exception: ber=None
                try: loss=float(loss) if loss is not None else None
                except Exception: loss=None
                return self._finish(direction,ts,duration=duration,ber=ber,loss=loss,
                                    rssi_values=rssi_values,reason=action,
                                    protocol=proto,slot=slot)
        return None

    def ingest(self, message, ts=None, gateway=False):
        ts=time.time() if ts is None else float(ts)
        message=str(message or "").strip()
        if not message:return None
        if gateway:return self._gateway(message,ts)

        alias=ALIAS_RE.search(message)
        if alias:self.aliases[int(alias.group(1))]=alias.group(2).strip()[:80]

        h=DMR_HEADER_RE.search(message)
        if h:
            slot=int(h.group(1));direction=h.group(2).upper()
            ev=self._start("DMR",direction,h.group(3),("TG " if h.group(4) else "")+h.group(5).strip(),ts,slot=slot)
            if slot in self.aliases:ev["alias"]=self.aliases[slot]
            return ev

        e=DMR_END_HEAD_RE.search(message)
        if e:
            duration=DURATION_RE.search(message);loss=LOSS_RE.search(message);ber=BER_RE.search(message)
            rv=RSSI_RE.search(message+",");vals=re.findall(r"-?\d+(?:\.\d+)?",rv.group(1)) if rv else []
            return self._finish(e.group(2),ts,float(duration.group(1)) if duration else None,
                                float(ber.group(1)) if ber else None,float(loss.group(1)) if loss else None,vals,
                                protocol="DMR",slot=int(e.group(1)))

        h=DSTAR_START_RE.search(message)
        if h:return self._start("DSTAR",h.group(1),h.group(2),h.group(4),ts,src_ext=_clean(h.group(3)),reflector=_clean(h.group(5)))
        e=DSTAR_END_RE.search(message)
        if e:
            d=DURATION_RE.search(message);b=BER_RE.search(message);rv=RSSI_RE.search(message+",")
            vals=re.findall(r"-?\d+(?:\.\d+)?",rv.group(1)) if rv else []
            return self._finish(e.group(1),ts,float(d.group(1)) if d else None,float(b.group(1)) if b else None,
                                rssi_values=vals,protocol="DSTAR",source=e.group(2),target=e.group(4))

        h=YSF_RF_START_RE.search(message)
        if h:return self._start("YSF","RF",h.group(1),"DG-ID "+h.group(2),ts,dgid=int(h.group(2)))
        h=YSF_NET_START_RE.search(message)
        if h and not self.active.get("NETWORK"):return self._start("YSF","NETWORK",h.group(1),"DG-ID "+h.group(2),ts,dgid=int(h.group(2)),reflector=_clean(h.group(3)))
        e=YSF_END_RE.search(message)
        if e:
            d=DURATION_RE.search(message);b=BER_RE.search(message);rv=RSSI_RE.search(message+",");loss=LOSS_RE.search(message)
            vals=re.findall(r"-?\d+(?:\.\d+)?",rv.group(1)) if rv else []
            return self._finish(e.group(1),ts,float(d.group(1)) if d else None,float(b.group(1)) if b else None,
                                float(loss.group(1)) if loss else None,vals,protocol="YSF",source=e.group(2),target="DG-ID "+e.group(3))

        h=P25_START_RE.search(message)
        if h:return self._start("P25",h.group(1),h.group(2),("TG " if h.group(3) else "")+h.group(4),ts)
        e=P25_END_RE.search(message)
        if e:
            d=DURATION_RE.search(message);b=BER_RE.search(message);rv=RSSI_RE.search(message+",");loss=LOSS_RE.search(message)
            vals=re.findall(r"-?\d+(?:\.\d+)?",rv.group(1)) if rv else []
            return self._finish(e.group(1),ts,float(d.group(1)) if d else None,float(b.group(1)) if b else None,
                                float(loss.group(1)) if loss else None,vals,protocol="P25",source=e.group(2),target=("TG " if e.group(3) else "")+e.group(4))

        h=NXDN_START_RE.search(message)
        if h:return self._start("NXDN",h.group(1),h.group(2),("TG " if h.group(3) else "")+h.group(4),ts)
        e=NXDN_END_RE.search(message)
        if e:
            d=DURATION_RE.search(message);b=BER_RE.search(message);rv=RSSI_RE.search(message+",")
            vals=re.findall(r"-?\d+(?:\.\d+)?",rv.group(1)) if rv else []
            return self._finish(e.group(1),ts,float(d.group(1)) if d else None,float(b.group(1)) if b else None,
                                rssi_values=vals,protocol="NXDN",source=e.group(2),target=("TG " if e.group(3) else "")+e.group(4))

        if IDLE_RE.search(message) and any(self.active.values()):
            out=[]
            for direction,current in list(self.active.items()):
                if current:out.append(self._finish(direction,ts,reason="idle"))
            return out[-1] if out else None

        ber,rssi=LIVE_BER_RE.search(message),LIVE_RSSI_RE.search(message)
        if ber or rssi:
            slot=int((ber or rssi).group(1))
            return self._metric("DMR",slot,float(ber.group(2)) if ber else None,float(rssi.group(2)) if rssi else None)
        return None

    def clear_stale(self, max_age=300, now=None):
        now=time.time() if now is None else float(now);changed=False
        for direction,current in list(self.active.items()):
            if not current:continue
            started=float(current.get("started_unix_ms") or 0)/1000.0
            if started and now-started>max_age:
                self._finish(direction,now,reason="stale-timeout");changed=True
        return changed

    def _gateway(self,message,ts):
        low=message.lower();state=None;summary=""
        if any(x in low for x in ("logged into the master successfully","login successful","linked to","network is connected","login accepted")):
            state,summary="connected","linked"
        elif any(x in low for x in ("authentication failed","login failed","login rejected","incorrect password","timed out waiting","network is down")):
            state,summary="error",message[-180:]
        elif any(x in low for x in ("connecting to xlx","sending authorisation","sending configuration","linking to","opening network","connecting to")):
            state,summary="connecting","authenticating"
        elif "closing" in low and ("network" in low or "xlx" in low):
            state,summary="disconnected","closed"
        if state and (state!=self.network["state"] or summary!=self.network["message"]):
            self.network={"state":state,"message":summary,"updated":iso(ts)};self._touch();return self.network
        return None

    def add_probe(self,ok,latency_ms=None,now=None):
        now=time.time() if now is None else now
        self.metrics.append({"ts":now,"ok":bool(ok),"latency_ms":latency_ms if ok else None});self._touch()

    def mtr_summary(self):
        vals=[x["latency_ms"] for x in self.metrics if x["ok"] and x["latency_ms"] is not None]
        loss=100*(1-sum(1 for x in self.metrics if x["ok"])/len(self.metrics)) if self.metrics else None
        jitter=sum(abs(b-a) for a,b in zip(vals,vals[1:]))/(len(vals)-1) if len(vals)>1 else None
        latency=vals[-1] if vals else None
        label="offline" if self.metrics and not vals else "excellent" if latency is not None and latency<60 and (loss or 0)<1 else "good" if latency is not None and latency<150 and (loss or 0)<5 else "poor" if latency is not None else "unknown"
        return {"latency_ms":round(latency,1) if latency is not None else None,
                "loss_percent":round(loss,1) if loss is not None else None,
                "jitter_ms":round(jitter,1) if jitter is not None else None,
                "quality":label,"samples":len(self.metrics)}

    def snapshot(self):
        candidates=[x for x in self.active.values() if x]
        active=max(candidates,key=lambda x:x["started_unix_ms"]) if candidates else None
        if active:active={k:v for k,v in active.items() if not k.startswith("_")}
        hist=[]
        for item in self.history:
            hist.append({k:v for k,v in item.items() if not k.startswith("_")})
        return {"schema":2,"sequence":self.sequence,"active":active,"standby":active is None,
                "network":self.network,"internet":self.mtr_summary(),"history":hist,"updated":iso(time.time())}
