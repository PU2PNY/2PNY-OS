#!/usr/bin/env python3
"""Deterministic 0.3.6 regressions. No RF hardware or real systemd changes."""
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
        self.assertNotIn('/wizard?step=1&return=internet',internet)
        self.assertIn("Melhor opção",internet)
        self.assertIn("PNY.operation",internet)
        expert=(ROOT/"src/expert-0.3.6.html").read_text()
        self.assertNotIn('/wizard?step=1',expert);self.assertNotIn('/wizard?step=3',expert)
        self.assertIn('href="/hotspot"',expert);self.assertIn('href="/protocols"',expert)
        wizard=(ROOT/"src/wizard-0.3.6.html").read_text()
        self.assertIn("Ex.: PU2ABC",wizard);self.assertIn("Ex.: 7240000",wizard);self.assertIn(">Radio ID<",wizard)

    def test_aprs_and_identity_links(self):
        aprs=(ROOT/"src/aprs-0.3.6.html").read_text()
        self.assertIn("navigator.geolocation",aprs);self.assertIn("Usar minha localização",aprs)
        for name in ("history-0.3.6.html","dashboard-0.3.6.html"):
            s=(ROOT/"src"/name).read_text()
            self.assertIn("https://www.qrz.com/db/",s)
            self.assertIn("https://radioid.net/api/dmr/user/",s)
            self.assertIn('target="_blank"',s)

    def test_translation_and_global_operation_ui(self):
        lang=(ROOT/"src/ui-language-0.3.6.js").read_text()
        for term in ("Wi-Fi Network 1","Red Wi-Fi 1","Best option","Mejor opción","Protocol profile","Perfil del protocolo"):
            self.assertIn(term,lang)
        self.assertIn("MutationObserver",lang)
        common=(ROOT/"src/ui-common-0.3.6.js").read_text()
        self.assertIn("function operation",common)
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

    def test_dstar_native_gateway_sections(self):
        files,out=self._run_apply("DSTAR","XLX026","82.152.175.30",0,"D","XLX")
        ini=files["dstar/DStarGateway.ini"]
        for section in ("[Gateway]","[ircddb_1]","[Repeater_1]","[HostsFiles]","[DPlus]","[DCS]","[XLX]","[DRats]","[Remote]"):
            self.assertIn(section,ini)
        self.assertIn("reflector=XLX026 D",ini)
        self.assertIn("port=20011",ini)
        self.assertIn("NETWORK_APPLY_OK protocol=DSTAR",out)

    def test_ysf_selected_name_is_exactly_resolvable(self):
        files,out=self._run_apply("YSF","BR-XLX026","82.152.175.30",42000,"","YSF")
        obj=json.loads(files["ysf/YSFHosts.json"])
        rows=obj["reflectors"]
        self.assertTrue(any(x.get("country")=="BR" and x.get("name")=="XLX026" for x in rows),rows)
        ini=files["ysf/YSFGateway.ini"]
        self.assertIn("Startup=BR-XLX026",ini)
        self.assertIn("NETWORK_APPLY_OK protocol=YSF",out)

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

    def test_updater_restricts_official_assets_and_hash(self):
        s=(ROOT/"src/2pny-update-manager-0.3.6.py").read_text()
        self.assertIn("https://github.com/PU2PNY/2PNY-OS/releases/download/",s)
        self.assertIn("sha256(pkg)",s)
        self.assertIn("issym()",s);self.assertIn("islnk()",s)
        self.assertIn("rollback",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
