#!/usr/bin/env python3
import pathlib, re, unittest
R=pathlib.Path(__file__).resolve().parents[1]

class Test037(unittest.TestCase):
    def test_backend_and_ui(self):
        b=(R/"src/2pnyd-main-0.3.7.go").read_text()
        self.assertIn('"0.3.7-alpha"',b)
        for p in ("/direct","/api/direct/call","/api/direct/pair","/api/direct/hangup"):
            self.assertIn(p,b)
        ui=(R/"src/ui-common-0.3.7.js").read_text()
        self.assertIn("['/direct','Direct','direct']",ui)
        page=(R/"src/direct-0.3.7.html").read_text()
        for x in ("PU2PNY Direct","Direct","Relay","Criptografia","Latência"):
            self.assertIn(x,page)

    def test_direct_crypto_and_rf_contract(self):
        types=(R/"src/direct-core/direct_types.go").read_text()
        session=(R/"src/direct-core/direct_session.go").read_text()
        transport=(R/"src/direct-core/direct_transport.go").read_text()
        radio=(R/"src/direct-core/direct_radio.go").read_text()
        main=(R/"src/direct-core/direct_main.go").read_text()
        self.assertIn("ed25519",types); self.assertIn("X25519",types)
        self.assertIn("aes.NewCipher",session); self.assertIn("cipher.NewGCM",session)
        self.assertIn('errors.New("replay")',session)
        self.assertIn("protocolo remoto incompatível",session)
        for proto in ('"DMR"','"DSTAR"','"YSF"'):
            self.assertIn(proto,radio)
        for port in ("62031","62032","20010","20011","4200","3200"):
            self.assertIn(port,radio)
        self.assertIn("systemctl",radio)
        self.assertIn("gatewayWasActive",radio)
        self.assertIn("keepaliveLoop",radio)
        self.assertIn('strings.HasPrefix(pkt.Kind, "radio:")',transport)
        self.assertIn("c.exitRadio()",transport)
        self.assertIn('flag.Bool("force-relay"',main)
        self.assertIn('flag.Bool("skip-systemd"',main)

    def test_direct_service_fail_safe(self):
        svc=(R/"src/2pny-direct-core-0.3.7.service").read_text()
        rec=(R/"src/2pny-direct-recover-0.3.7").read_text()
        self.assertIn("ExecStopPost=/usr/local/sbin/2pny-direct-recover",svc)
        self.assertIn("NoNewPrivileges=true",svc)
        self.assertIn("gateway_restore",rec)
        for unit in ("2pny-dmrgateway.service","2pny-dstargateway.service","2pny-ysfgateway.service"):
            self.assertIn(unit,rec)

    def test_dstar_schema_and_native_audio(self):
        p=(R/"src/2pny-protocol-network-apply-all-0.3.7.py").read_text()
        for section in ("[General]","[Repeater 1]","[IRCDDB 1]","[Hosts Files]"):
            self.assertIn(section,p)
        self.assertIn('audio_path="/usr/share/2pny/audio/dstar/"',p)
        self.assertIn("Data={audio_path}",p)
        prep=(R/"ci/prepare-0.3.7-alpha.py").read_text()
        self.assertIn("DGWVoiceTransmit/dgwvoicetransmit",prep)
        self.assertIn("Data/*.ambe",prep); self.assertIn("Data/*.indx",prep)
        self.assertIn("DMR helper/binary is deliberately untouched",prep)

    def test_moderno_v2(self):
        d=(R/"src/2pny-display-core-0.3.7.py").read_text()
        self.assertIn("PU2PNY Moderno V2",d)
        self.assertIn("Graphical 128x64 renderer",d)
        self.assertIn("class LCD",d)
        page=(R/"src/display-0.3.7.html").read_text()
        self.assertIn("PU2PNY Moderno V2",page)
        self.assertIn("OLED SSD1306/SH1106",page)

if __name__=="__main__":
    unittest.main(verbosity=2)
