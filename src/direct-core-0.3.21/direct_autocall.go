package main

import (
	"encoding/json"
	"os"
	"strings"
	"time"
)

type autoLive struct {
	Active *struct {
		Direction string `json:"direction"`
		Mode string `json:"mode"`
		Protocol string `json:"protocol"`
		Target string `json:"target"`
		Started int64 `json:"started_unix_ms"`
	} `json:"active"`
}

type autoContacts struct {
	Contacts []map[string]any `json:"contacts"`
}

func normalizedDigits(v any) string {
	s:=strings.TrimSpace(strings.TrimSuffix(strings.TrimPrefix(strings.TrimSpace(strings.ReplaceAll(strings.ReplaceAll(strings.TrimSpace(toText(v))," ",""),".0","")),"+"),"-"))
	for _,r:=range s { if r<'0'||r>'9' { return "" } }
	return s
}

func toText(v any) string {
	switch x:=v.(type) {
	case string:return x
	case float64:
		if x==float64(int64(x)) { return fmtInt64(int64(x)) }
	}
	return ""
}

func fmtInt64(v int64) string {
	if v==0{return "0"}
	neg:=v<0;if neg{v=-v}
	var b [24]byte;i:=len(b)
	for { i--;b[i]=byte('0'+v%10);v/=10;if v==0{break} }
	if neg{i--;b[i]='-'}
	return string(b[i:])
}

func resolveAutoPeer(peers map[string]peer, live autoLive, contacts autoContacts) string {
	if live.Active==nil || strings.ToUpper(strings.TrimSpace(live.Active.Direction))!="RF" { return "" }
	proto:=strings.ToUpper(strings.TrimSpace(live.Active.Protocol))
	target:=strings.ToUpper(strings.TrimSpace(live.Active.Target))
	if proto=="DSTAR" {
		target=strings.ReplaceAll(target," ","")
		if target=="CQCQCQ" || !callRE.MatchString(target) { return "" }
		if _,ok:=peers[target];ok{return target}
		return ""
	}
	if proto=="DMR" {
		if strings.HasPrefix(target,"TG ") { return "" }
		id:=normalizedDigits(target)
		if len(id)<6||len(id)>9{return ""}
		for _,row:=range contacts.Contacts {
			rid:=normalizedDigits(row["id"]);if rid!=id{continue}
			call:=strings.ToUpper(strings.TrimSpace(toText(row["callsign"])))
			if _,ok:=peers[call];ok&&callRE.MatchString(call){return call}
		}
	}
	return ""
}

func (c *core) autoCallLoop() {
	const livePath="/run/2pny/live.json"
	const contactsPath="/run/2pny/contacts.json"
	var lastMod time.Time
	var lastSig string
	for {
		st,err:=os.Stat(livePath)
		if err==nil && st.ModTime()!=lastMod {
			lastMod=st.ModTime()
			var l autoLive
			if b,e:=os.ReadFile(livePath);e==nil&&json.Unmarshal(b,&l)==nil&&l.Active!=nil {
				sig:=l.Active.Protocol+"|"+l.Active.Direction+"|"+l.Active.Target+"|"+fmtInt64(l.Active.Started)
				if sig!=lastSig {
					lastSig=sig
					var ct autoContacts
					if b,e:=os.ReadFile(contactsPath);e==nil {_=json.Unmarshal(b,&ct)}
					c.mu.Lock()
					peers:=make(map[string]peer,len(c.peers));for k,v:=range c.peers{peers[k]=v}
					idle:=!c.st.RadioActive&&(c.st.Status==""||c.st.Status=="idle")
					c.mu.Unlock()
					to:=resolveAutoPeer(peers,l,ct)
					if idle&&to!=""&&strings.EqualFold(currentProtocol(),l.Active.Protocol) {
						c.mu.Lock()
						c.st.InitiatedBy="radio";c.st.RequestedTarget=to;c.st.Traversal="UDP hole punching";c.writeState()
						c.mu.Unlock()
						go func(target string){ _=c.call(target) }(to)
					}
				}
			}
		}
		time.Sleep(500*time.Millisecond)
	}
}
