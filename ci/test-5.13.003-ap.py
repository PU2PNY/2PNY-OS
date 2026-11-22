#!/usr/bin/env python3
"""Isolated DHCP, DNS and HTTP captive-portal integration test for Armbian images."""
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

def run(args,check=True,**kwargs):
    return subprocess.run(args,check=check,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kwargs)

def dns_query(namespace,name):
    labels=b"".join(bytes([len(x)])+x.encode("ascii") for x in name.split("."))
    packet=struct.pack("!HHHHHH",0x5133,0x0100,1,0,0,0)+labels+b"\0"+struct.pack("!HH",1,1)
    code=("import socket,struct; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); "
          "s.settimeout(3); s.sendto("+repr(packet)+",('10.43.0.1',53)); "
          "r=s.recvfrom(2048)[0]; "
          "assert struct.unpack('!H',r[6:8])[0]>=1 and bytes([10,43,0,1]) in r, r.hex()")
    run(["ip","netns","exec",namespace,sys.executable,"-c",code])

def main():
    if os.geteuid()!=0:raise SystemExit("AP integration test must run as root")
    if len(sys.argv)!=2:raise SystemExit("usage: test-5.13.003-ap.py ROOTFS")
    root=Path(sys.argv[1]).resolve()
    core=root/"usr/local/sbin/2pny-network-core"
    template=root/"usr/share/2pny/network/dnsmasq-ap.template"
    unit=root/"etc/systemd/system/2pnyd.service"
    wants=root/"etc/systemd/system/multi-user.target.wants/2pnyd.service"
    assert core.is_file() and template.is_file() and unit.is_file()
    core_text=core.read_text()
    assert "dhcp-leasefile=" in core_text and "check_ap_health" in core_text
    subprocess.run(["bash","-n",str(core)],check=True)
    assert wants.is_symlink()
    assert (wants.parent/wants.readlink()).resolve(strict=True)==unit.resolve(strict=True)
    network_unit=root/"etc/systemd/system/2pny-network-core.service"
    network_link=root/"etc/systemd/system/multi-user.target.wants/2pny-network-core.service"
    assert network_unit.is_file() and network_link.is_symlink()
    assert (network_link.parent/network_link.readlink()).resolve(strict=True)==network_unit.resolve(strict=True)
    board_id=(root/"etc/2pny/board-id").read_text().strip()
    assert board_id in ("opizero","nanopineo"),board_id
    display_core=root/"usr/local/sbin/2pny-display-core"
    assert display_core.is_file()
    compile(display_core.read_text(),str(display_core),"exec")

    required=("ip","dnsmasq","busybox","curl","chroot")
    missing=[x for x in required if not shutil.which(x)]
    assert not missing,"missing host test tools: "+",".join(missing)

    suffix=str(os.getpid()%10000)
    ns="pnyap"+suffix
    ap_if="pnya"+suffix
    client_if="pnyc"+suffix
    with tempfile.TemporaryDirectory(prefix="pny-ap-513003-") as tmp:
        temp=Path(tmp)
        dnsconf=temp/"dnsmasq.conf"
        lines=template.read_text().splitlines()
        lines=[x for x in lines if not x.startswith(("dhcp-option-force=114,","dhcp-leasefile=","pid-file=","log-facility="))]
        lines=[x.replace("@IFACE@",ap_if) for x in lines]
        lines.extend([
            "dhcp-leasefile="+str(temp/"dnsmasq.leases"),
            "pid-file="+str(temp/"dnsmasq.pid"),
            "log-facility="+str(temp/"dnsmasq.log"),
            "no-resolv","no-hosts","address=/#/10.43.0.1"
        ])
        dnsconf.write_text("\n".join(lines)+"\n")
        run(["dnsmasq","--test","--conf-file="+str(dnsconf)])
        dns=None;portal=None;namespace_created=False;link_created=False
        try:
            run(["ip","netns","add",ns]);namespace_created=True
            run(["ip","link","add",ap_if,"type","veth","peer","name",client_if]);link_created=True
            run(["ip","link","set",client_if,"netns",ns])
            run(["ip","addr","add","10.43.0.1/24","dev",ap_if])
            run(["ip","link","set",ap_if,"up"])
            run(["ip","netns","exec",ns,"ip","link","set","lo","up"])
            run(["ip","netns","exec",ns,"ip","link","set",client_if,"up"])
            dnslog=(temp/"dnsmasq-process.log").open("w")
            dns=subprocess.Popen(["dnsmasq","--keep-in-foreground","--conf-file="+str(dnsconf)],
                                 stdout=dnslog,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.time()+8
            socket_state=""
            while time.time()<deadline:
                if dns.poll() is not None:raise RuntimeError("dnsmasq exited: "+(temp/"dnsmasq-process.log").read_text())
                socket_state=run(["ss","-H","-lun"],check=False).stdout
                has_dhcp=any(re.search(r":67(?:\s|$)",line) for line in socket_state.splitlines())
                has_dns=any(re.search(r":53(?:\s|$)",line) for line in socket_state.splitlines())
                if has_dhcp and has_dns:break
                time.sleep(.25)
            else:raise RuntimeError("dnsmasq did not bind DHCP/DNS sockets; ss="+socket_state+" log="+(temp/"dnsmasq-process.log").read_text())

            dhscript=temp/"udhcpc-script"
            dhscript.write_text("""#!/bin/sh
printf 'event=%s iface=%s ip=%s\n' "$1" "$interface" "$ip" >> "@TRACE@"
case "$1" in
  bound|renew)
    ip -4 addr flush dev "$interface" 2>/dev/null || true
    ip -4 addr add "$ip/24" dev "$interface" || exit 1
    if [ -n "$router" ]; then
      ip route replace default via "$(printf '%s' "$router" | awk '{print $1}')" dev "$interface" || exit 1
    fi
    if [ -n "$dns" ]; then
      printf 'nameserver %s\n' "$(printf '%s' "$dns" | awk '{print $1}')" > "$TEST_RESOLV" || exit 1
    fi
    ;;
esac
exit 0
""".replace("@TRACE@",str(temp/"udhcpc-script.log")))
            dhscript.chmod(0o755)
            resolv=temp/"client-resolv.conf"
            clientcmd=["ip","netns","exec",ns,"env","TEST_RESOLV="+str(resolv),
                       "busybox","udhcpc","-f","-q","-n","-i",client_if,"-s",str(dhscript),"-t","5","-T","2"]
            client_result=run(clientcmd,check=False,timeout=25)
            if client_result.returncode:
                raise RuntimeError("udhcpc exit="+str(client_result.returncode)+
                                   " output="+client_result.stdout+" dnsmasq="+
                                   (temp/"dnsmasq-process.log").read_text(errors="replace"))
            addr=""
            for _ in range(30):
                addr=run(["ip","netns","exec",ns,"ip","-4","-o","addr","show","dev",client_if]).stdout
                if re.search(r"inet (10\.43\.0\.(\d+)/24)",addr):break
                time.sleep(0.2)
            match=re.search(r"inet (10\.43\.0\.(\d+)/24)",addr)
            if not match or not 20<=int(match.group(2))<=200:
                script_trace=temp/"udhcpc-script.log"
                script_info=script_trace.read_text(errors="replace") if script_trace.exists() else "(not executed)"
                raise RuntimeError("DHCP IPv4 missing: stdout="+client_result.stdout+" addr="+repr(addr)+
                                   " script="+script_info+" dnsmasq="+
                                   (temp/"dnsmasq-process.log").read_text(errors="replace"))
            route=run(["ip","netns","exec",ns,"ip","route","show","default"]).stdout
            assert "via 10.43.0.1" in route,route
            assert resolv.is_file() and "nameserver 10.43.0.1" in resolv.read_text()
            dns_query(ns,"pu2pny.local")
            dns_query(ns,"connectivitycheck.gstatic.com")

            portal_log=(temp/"2pnyd.log").open("w")
            portal=subprocess.Popen(["chroot",str(root),"/usr/local/bin/2pnyd"],
                                    stdout=portal_log,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.time()+15
            while time.time()<deadline:
                if portal.poll() is not None:raise RuntimeError("2pnyd exited: "+(temp/"2pnyd.log").read_text())
                health=run(["ip","netns","exec",ns,"curl","--noproxy","*","-fsS","--connect-timeout","1","--max-time","2","http://10.43.0.1/healthz"],check=False)
                if health.returncode==0 and "PU2PNY OK" in health.stdout:break
                time.sleep(.5)
            else:raise RuntimeError("2pnyd HTTP health failed: "+(temp/"2pnyd.log").read_text())
            headers=run(["ip","netns","exec",ns,"curl","--noproxy","*","-sS","-D","-","-o","/dev/null","http://10.43.0.1/generate_204"]).stdout.replace("\r","")
            assert "Location: http://10.43.0.1/wizard" in headers,headers
            page=run(["ip","netns","exec",ns,"curl","--noproxy","*","-fsSL","--max-time","5","http://10.43.0.1/"]).stdout
            assert "PU2PNY-OS" in page
            print("5.13.003_AP_DHCP_DNS_HTTP_INTEGRATION_PASS",board_id)
        finally:
            if portal:
                portal.terminate()
                try:portal.wait(timeout=3)
                except subprocess.TimeoutExpired:portal.kill()
            if dns:
                dns.terminate()
                try:dns.wait(timeout=3)
                except subprocess.TimeoutExpired:dns.kill()
            if namespace_created:run(["ip","netns","del",ns],check=False)
            if link_created:run(["ip","link","del",ap_if],check=False)

if __name__=="__main__":main()
