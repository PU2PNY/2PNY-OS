#!/usr/bin/env python3
"""Deterministic 0.3.6 regressions, including DMR aliases/BrandMeister API isolation. No RF hardware or real systemd changes."""
import contextlib, io, json, os, runpy, subprocess, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class T(unittest.TestCase):
    def test_network_unbound_variable_regression(self):
        s=(ROOT/"src/2pny-network-switch-0.3.6").read_text()
        self.assertIn('test "${paused:-0}" = 1',s)
        self.assertIn('trap - EXIT',s)
        self.assertIn('iw dev "$iface" set type managed',s)
        subprocess.run(["bash","-n",str(ROOT/"src/2pny-network-switch-0.3.6")],check=True)

    def test_ui_operational_contracts(self):
        internet=(ROOT/"src/internet-0.3.6.html").read_text()
        self.assertIn("Rede Wi‑Fi 1 e Rede Wi‑Fi 2",internet)
        self.assertIn('id="wifiSecondManual"',internet)
        self.assertIn('id="wifiPrimaryManual"',internet)
        self.assertIn("dns_refresh_seconds", (ROOT/"src/2pny-netdiag-0.3.6.py").read_text())
        self.assertNotIn('/wizard?step=1&return=internet',internet)
        self.assertIn("Melhor opção",internet)
        self.assertIn("PNY.operation",internet)
        self.assertIn('id="wifiPrimarySelect"',internet)
        self.assertIn('id="wifiSavePrimary"',internet)
        self.assertIn("Continuando automaticamente",internet)
        expert=(ROOT/"src/expert-0.3.6.html").read_text()
        self.assertNotIn('/wizard?step=1',expert);self.assertNotIn('/wizard?step=3',expert)
        self.assertIn('href="/hotspot"',expert);self.assertIn('href="/protocols"',expert)
        wizard=(ROOT/"src/wizard-0.3.6.html").read_text()
        self.assertIn("Ex.: PU2ABC",wizard);self.assertIn("Ex.: 7240000",wizard);self.assertIn(">Radio ID<",wizard)

    def test_aprs_and_identity_links(self):
        aprs=(ROOT/"src/aprs-0.3.6.html").read_text()
        self.assertIn("navigator.geolocation",aprs);self.assertIn("Usar minha localização",aprs)
        self.assertIn("window.isSecureContext",aprs);self.assertIn("replyCall",aprs);self.assertIn("status.aprs2.net",aprs)
        for name in ("history-0.3.6.html","dashboard-0.3.6.html"):
            s=(ROOT/"src"/name).read_text()
            self.assertIn("https://www.qrz.com/db/",s)
            self.assertIn("/radioid?callsign=",s)
            self.assertNotIn('href="https://radioid.net/api/dmr/user/',s)
            self.assertIn('target="_blank"',s)

    def test_translation_and_global_operation_ui(self):
        lang=(ROOT/"src/ui-language-0.3.6.js").read_text()
        for term in ("Wi-Fi Network 1","Red Wi-Fi 1","Best option","Mejor opción","Protocol profile","Perfil del protocolo"):
            self.assertIn(term,lang)
        self.assertIn("MutationObserver",lang)
        common=(ROOT/"src/ui-common-0.3.6.js").read_text()
        self.assertIn("function operation",common)
        self.assertIn("progress:function(percent,msg)",common)
        self.assertIn("/aprs?to=",common)
        segment=common.split("function operation",1)[1].split("function footer",1)[0]
        self.assertNotIn("pnyOpPercent",segment);self.assertIn("animation:pnyop",segment)

    def test_protocol_profile_contract(self):
        s=(ROOT/"src/2pny-protocol-profiles-0.3.6.py").read_text()
        self.assertIn("protocol-profiles.json",s)
        self.assertIn("2pny-rf-apply",s)
        self.assertIn("2pny-protocol-network-apply",s)
        self.assertIn("BACKUPS",s)
        self.assertIn("if rf_changed",s)

    def _run_apply(self,proto,server,address,port,module,kind):
        original=(ROOT/"src/2pny-protocol-network-apply-all-0.3.6.py").read_text()
        with tempfile.TemporaryDirectory() as td:
            state=Path(td)
            host=state/"mmdvm/MMDVM-Host.ini";host.parent.mkdir(parents=True)
            host.write_text("[General]\nCallsign=PU2ABC\nId=7240000\n[Modem]\nRXFrequency=438800000\nTXFrequency=438800000\n")
            (state/"hosts").mkdir()
            (state/"hosts/YSFHosts.json").write_text('{"reflectors":[]}\n')
            (state/"hosts/FCSRooms.txt").write_text("# local\n")
            code=original.replace('/var/lib/2pny',td)
            def fake_run(args,*a,**kw):
                # All local service/preflight operations succeed in this deterministic test.
                return subprocess.CompletedProcess(args,0,"","")
            argv=["apply",proto,server,address,str(port),"","hotspot","1","2",module,"",kind,""]
            out=io.StringIO()
            with patch.object(sys,"argv",argv),patch("os.geteuid",return_value=0),patch("os.chown"),\
                 patch("grp.getgrnam",return_value=types.SimpleNamespace(gr_gid=os.getgid())),\
                 patch("subprocess.run",fake_run),patch("time.sleep"),contextlib.redirect_stdout(out):
                exec(compile(code,"apply036","exec"),{})
            files={str(p.relative_to(state)):p.read_text(errors="ignore") for p in state.rglob("*") if p.is_file()}
            return files,out.getvalue()

    def test_dstar_pinned_612f388_schema(self):
        files,out=self._run_apply("DSTAR","XLX026","82.152.175.30",0,"D","XLX")
        ini=files["dstar/DStarGateway.ini"]
        for section in ("[General]","[IRCDDB 1]","[Repeater 1]","[Hosts Files]","[Log]","[MQTT]","[D-Plus]","[DCS]","[XLX]","[D-Rats]","[Remote Commands]"):
            self.assertIn(section,ini)
        self.assertIn("Callsign=PU2ABC",ini)
        self.assertIn("Band=D",ini)
        self.assertIn("Type=HB",ini)
        self.assertIn("Reflector=XLX026 D",ini)
        self.assertIn("Port=20011",ini)
        self.assertIn("DisplayLevel=2",ini)
        self.assertIn("MQTTLevel=0",ini)
        self.assertNotIn("[Gateway]",ini)
        self.assertNotIn("[Repeater_1]",ini)
        self.assertIn("NETWORK_APPLY_OK protocol=DSTAR",out)

    def test_ysf_selected_name_is_exactly_resolvable(self):
        files,out=self._run_apply("YSF","BR-XLX026","82.152.175.30",42000,"","YSF")
        obj=json.loads(files["ysf/YSFHosts.json"])
        rows=obj["reflectors"]
        self.assertTrue(any(x.get("country")=="BR" and x.get("name")=="XLX026" for x in rows),rows)
        ini=files["ysf/YSFGateway.ini"]
        self.assertIn("Startup=BR-XLX026",ini)
        self.assertIn("NETWORK_APPLY_OK protocol=YSF",out)

    def test_p25_static_configuration_without_claiming_hardware(self):
        files,out=self._run_apply("P25","P25-724","198.51.100.10",42010,"","P25")
        ini=files["p25/P25Gateway.ini"];host=files["mmdvm/MMDVM-Host.ini"]
        self.assertIn("[General]",ini);self.assertIn("[Network]",ini)
        self.assertIn("RptPort=32010",ini);self.assertIn("LocalPort=42020",ini)
        self.assertIn("Static=724",ini)
        self.assertIn("Enable = 1",host.replace("Enable=1","Enable = 1"))
        self.assertIn("NETWORK_APPLY_OK protocol=P25",out)

    def test_runtime_link_evidence(self):
        src=(ROOT/"src/2pny-station-worker-0.3.6.py").read_text()
        core=str(ROOT/"src/2pny-live-core-0.3.1.py")
        with tempfile.TemporaryDirectory() as td:
            src=src.replace('/usr/local/lib/2pny-live-core.py',core)
            src=src.replace('RUN=Path("/run/2pny")',f'RUN=Path({td!r})')
            ns={"__name__":"station_test"}
            exec(compile(src,"station036","exec"),ns)
            runtime=Path(td)/"network-runtime.json"
            ns["update_network_runtime_from_gateway"]("DCS link to XLX026 D established",1234.0,"2pny-dstargateway.service")
            d=json.loads(runtime.read_text());self.assertTrue(d["connected"]);self.assertEqual(d["protocol"],"DSTAR");self.assertEqual(d["module"],"D")
            ns["update_network_runtime_from_gateway"]('Linked to BR-XLX026',1235.0,"2pny-ysfgateway.service")
            d=json.loads(runtime.read_text());self.assertTrue(d["connected"]);self.assertEqual(d["protocol"],"YSF");self.assertEqual(d["server_name"],"BR-XLX026")
            ns["update_network_runtime_from_gateway"]("Link has failed, polls lost",1236.0,"2pny-ysfgateway.service")
            d=json.loads(runtime.read_text());self.assertFalse(d["connected"])


    def _run_dmr_alias(self,essid):
        original=(ROOT/"src/2pny-protocol-network-apply-0.2.9.py").read_text()
        with tempfile.TemporaryDirectory() as td:
            state=Path(td)
            cfg=state/"mmdvm/MMDVM-Host.ini";cfg.parent.mkdir(parents=True)
            cfg.write_text("[General]\nCallsign=PU2ABC\nId=7240000\nDuplex=0\n[Modem]\nRXFrequency=438800000\nTXFrequency=438800000\n[DMR]\nEnable=1\n")
            code=original.replace('/var/lib/2pny',td)
            def fake_run(args,*a,**kw):
                return subprocess.CompletedProcess(args,0,"","")
            argv=["apply","DMR","BM_TEST","master.example.net","62031","hotspot-pass","hotspot","1","2","",essid,"BrandMeister",""]
            out=io.StringIO()
            with patch.object(sys,"argv",argv),patch("os.geteuid",return_value=0),patch("os.chown"),\
                 patch("grp.getgrnam",return_value=types.SimpleNamespace(gr_gid=os.getgid())),\
                 patch("subprocess.run",fake_run),patch("time.sleep"),contextlib.redirect_stdout(out):
                exec(compile(code,"dmr_alias_036","exec"),{})
            return cfg.read_text(),(state/"dmr/DMRGateway.ini").read_text(),out.getvalue()

    def test_brandmeister_radio_alias_01_02(self):
        host,gw,_=self._run_dmr_alias("01")
        self.assertIn("Id=7240000",host)
        self.assertIn("Id=724000001",gw)
        host,gw,_=self._run_dmr_alias("02")
        self.assertIn("Id=7240000",host)
        self.assertIn("Id=724000002",gw)
        ui=(ROOT/"src/protocols-0.3.6.html").read_text()
        self.assertIn("Rádio '+ri+' (",ui)
        self.assertIn("ID efetivo BrandMeister",ui)
        wiz=(ROOT/"src/wizard-0.3.6.html").read_text()
        self.assertIn("Rádio '+i+' (",wiz)

    def test_brandmeister_invalid_alias_is_rejected(self):
        original=(ROOT/"src/2pny-protocol-network-apply-0.2.9.py").read_text()
        with tempfile.TemporaryDirectory() as td:
            state=Path(td);cfg=state/"mmdvm/MMDVM-Host.ini";cfg.parent.mkdir(parents=True)
            cfg.write_text("[General]\nCallsign=PU2ABC\nId=7240000\nDuplex=0\n[Modem]\nRXFrequency=438800000\nTXFrequency=438800000\n")
            code=original.replace('/var/lib/2pny',td)
            argv=["apply","DMR","BM_TEST","master.example.net","62031","hotspot-pass","hotspot","1","2","","1","BrandMeister",""]
            with patch.object(sys,"argv",argv),patch("os.geteuid",return_value=0),self.assertRaises(SystemExit):
                exec(compile(code,"dmr_alias_bad_036","exec"),{})
        backend=(ROOT/"src/2pnyd-main-0.3.6.go").read_text()
        self.assertIn("identificação DMR deve ser 01 a 99",backend)
        profiles=(ROOT/"src/2pny-protocol-profiles-0.3.6.py").read_text()
        self.assertIn("identificação DMR deve ser 01 a 99",profiles)

    def test_brandmeister_api_key_isolated_from_hotspot_password(self):
        backend=(ROOT/"src/2pnyd-main-0.3.6.go").read_text()
        self.assertIn("/api/brandmeister/api-key",backend)
        self.assertIn("brandmeister-api.key",backend)
        self.assertIn("os.CreateTemp(secretDir",backend)
        self.assertIn("tmp.Chmod(0600)",backend)
        start=backend.index("type Config struct")
        end=backend.index("type Status struct",start)
        self.assertNotIn("bm_api_key",backend[start:end].lower())
        hs=backend.index("func brandmeisterAPIKeyHandler")
        he=backend.index("func netdiagHandler",hs)
        self.assertNotIn("exec.Command(",backend[hs:he])
        ui=(ROOT/"src/protocols-0.3.6.html").read_text()
        self.assertIn("não substitui a Hotspot Security",ui)
        self.assertIn("O PU2PNY não pede API Secret",ui)
        self.assertIn("API Key salva sem reiniciar MMDVMHost ou DMRGateway",ui)

    def test_updater_restricts_official_assets_and_hash(self):
        s=(ROOT/"src/2pny-update-manager-0.3.6.py").read_text()
        self.assertIn("https://github.com/PU2PNY/2PNY-OS/releases/download/",s)
        self.assertIn("sha256(pkg)",s)
        self.assertIn("issym()",s);self.assertIn("islnk()",s)
        self.assertIn("rollback",s)
        self.assertIn('cmd=="download"',s);self.assertIn('cmd=="install-staged"',s)
        self.assertIn("progress_percent",s)
        self.assertLess(s.index('if cmd=="status"'),s.index("fcntl.flock"))
        ui=(ROOT/"src/system-0.3.6.html").read_text()
        self.assertIn("Baixar atualização",ui);self.assertIn("100% completo",ui);self.assertIn("regravar o SD",ui)

    def test_network_dns_and_wifi_handoff_regressions(self):
        net=(ROOT/"src/2pny-netdiag-0.3.6.py").read_text()
        self.assertIn('r"(?:\\d{1,3}\\.){3}\\d{1,3}"',net)
        self.assertNotIn('r"(?:\\\\d{1,3}\\\\.){3}\\\\d{1,3}"',net)
        self.assertIn('now-last_dns>180',net)
        backend=(ROOT/"src/2pnyd-main-0.3.6.go").read_text()
        block=backend[backend.index("func networkConnectHandler"):backend.index("func friendlyNetworkError")]
        self.assertIn('"will_reboot": false',block)
        self.assertNotIn('exec.Command("systemctl","reboot")',block)

    def test_radioid_is_formatted_not_raw_api(self):
        for name in ("history-0.3.6.html","dashboard-0.3.6.html"):
            src=(ROOT/"src"/name).read_text()
            self.assertIn('/radioid?callsign=',src)
            self.assertNotIn('radioid.net/api/dmr/user/?callsign=',src)
        page=(ROOT/"src/radioid-0.3.6.html").read_text()
        self.assertIn("/api/contacts",page)
        self.assertIn("JSON bruto",page)

    def test_backend_source_is_single_and_routes_are_unique(self):
        backend=(ROOT/"src/2pnyd-main-0.3.6.go").read_text()
        self.assertEqual(backend.count("package main"),1)
        self.assertEqual(backend.count('http.HandleFunc("/radioid"'),1)
        self.assertNotIn("radioIDPageHandler",backend)
        self.assertIn('radioIDFile           = "/usr/share/2pny/radioid.html"',backend)


if __name__=="__main__":
    unittest.main(verbosity=2)
