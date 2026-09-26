#!/usr/bin/env python3
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]

# REL-022: protocol implementation is protected from the 0.3.26 physical baseline.
protected=[
 "src/2pny-protocol-network-apply-0.3.21.py",
 "src/2pny-protocol-network-apply-all-0.3.20.py",
 "src/2pny-dstargateway-0.2.9.service",
 "src/2pny-ysfgateway-0.2.9.service",
 "src/2pny-mmdvmhost-0.3.13.service",
 "ci/patch-dmrgateway-pu2pny-0.3.20.py",
 "ci/patch-dmrgateway-voice-arbiter-0.3.21.py",
]
for p in protected:
    current=(root/p).read_bytes()
    prior=subprocess.check_output(["git","show","v0.3.26-alpha:"+p],cwd=root)
    assert current==prior, "protected protocol baseline changed: "+p

allp=(root/"src/2pny-protocol-network-apply-all-0.3.20.py").read_text()
dmr=(root/"src/2pny-protocol-network-apply-0.3.21.py").read_text()
hot=(root/"src/hotspot-0.3.27.html").read_text()
main=(root/"src/2pnyd-main-0.3.27.go").read_text()
aprs=(root/"src/2pny-aprs-0.3.27.py").read_text()
aprsui=(root/"src/aprs-0.3.27.html").read_text()

# YSF/C4FM + Wires-X local command path.
for token in (
 'setsec(cp,"System Fusion",{"Enable":"1" if proto=="YSF" else "0"})',
 '"System Fusion Network",{"Enable":"1" if proto=="YSF" else "0","LocalAddress":"127.0.0.1","LocalPort":"3200","GatewayAddress":"127.0.0.1","GatewayPort":"4200"',
 'RptPort=3200','LocalPort=4200','WiresXCommandPassthrough=0',
 'Startup={startup}','Reconnect=0','Revert=0','Hosts={d/"YSFHosts.json"}',
):
    assert token in allp, "YSF contract missing: "+token
assert 'YSF Startup não corresponde a nenhum refletor resolvível' in allp

# D-Star protected simplex/local bridge contract.
for token in (
 'setsec(cp,"D-Star",{"Enable":"1" if proto=="DSTAR" else "0"',
 '"D-Star Network",{"Enable":"1" if proto=="DSTAR" else "0","LocalAddress":"127.0.0.1","LocalPort":"20011","GatewayAddress":"127.0.0.1","GatewayPort":"20010"',
 'ReflectorAtStartup=1','ReflectorReconnect=Never','[D-Plus]','[Dextra]','[DCS]','[XLX]',
):
    assert token in allp, "D-Star contract missing: "+token

# DMR: simplex stays protected; duplex remains isolated to repeater branch.
for token in (
 'duplex=1 if usemode=="repeater" else 0',
 'route_slots=(1,2) if duplex',
 '"local_transport":"gateway-explicit" if duplex else "simplex-protected"',
 '"GatewayPort":"62031"','"LocalPort":"62032"','BrandMeister requires the Hotspot Security password',
):
    assert token in dmr, "DMR contract missing: "+token
assert 'if duplex:' in dmr
assert 'sections["DMR Network"].update' in dmr

# BrandMeister secret UX/persistence: browser gets boolean only, never saved value.
assert 'id="bmSecurityPassword"' in hot and 'type="password"' in hot
assert 'protocolPassword()' in hot
assert '"hotspot_security_configured": securityConfigured' in main
assert '"brandmeister_security_configured": securityConfigured' in main
assert 'filepath.Join(dataDir, "protocol-secrets", "dmr.secret")' in main
assert 'os.WriteFile(filepath.Join(secretDir, "dmr.secret"), []byte(in.ServerPassword+"\\n"), 0600)' in main
assert 'passwordProvided := in.Password != ""' in main
assert 'in.Password = strings.TrimSpace(string(b))' in main
config_struct=main[main.index("type Config struct"):main.index("}",main.index("type Config struct"))]
assert "Password" not in config_struct and "Secret" not in config_struct

# APRS is message-only while ACK/REJ, outbox and incoming messaging remain.
for token in ('def msg_packet','def parse_message','"type":"ack"','"type":"rej"','retry_unacked','consume_outbox','send(sock,msg_packet(call,m["source"],"ack"+m["id"]))'):
    assert token in aprs, "APRS messaging contract missing: "+token
for forbidden in ('cfg.get("latitude")','cfg.get("longitude")','beacon(cfg','def beacon(','def degmin('):
    assert forbidden not in aprs, "APRS position path remains: "+forbidden
low=aprsui.lower()
for forbidden in ('id="lat"','id="lon"','uselocation','aprs.fi','mapstub','radarcore','último beacon','próximo beacon'):
    assert forbidden not in low, "APRS UI location feature remains: "+forbidden
assert "message_only" in main
print("PROTOCOL_AUDIT_0327_OK")
