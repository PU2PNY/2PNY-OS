#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
cat > builder/validate-source.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo '[1/8] Shell syntax'
bash -n builder/build-image.sh
for f in \
  rootfs-overlay/usr/local/sbin/2pny-firstboot \
  rootfs-overlay/usr/local/sbin/2pny-networkd \
  rootfs-overlay/usr/local/sbin/2pny-ap-control \
  rootfs-overlay/usr/local/sbin/2pny-rf-apply; do
  bash -n "$f"
done

echo '[2/8] Go source/build'
gofmt -w src/2pnyd/main.go
go test ./...
mkdir -p rootfs-overlay/usr/local/bin
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o rootfs-overlay/usr/local/bin/2pnyd ./src/2pnyd
file rootfs-overlay/usr/local/bin/2pnyd | grep -q 'ARM aarch64'

echo '[3/8] 2PNY core services'
test -x rootfs-overlay/usr/local/bin/2pnyd
test -f rootfs-overlay/etc/systemd/system/2pnyd.service
test -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pnyd.service
grep -q 'MemoryMax=64M' rootfs-overlay/etc/systemd/system/2pnyd.service
grep -q '0.1.8-alpha' src/2pnyd/main.go
grep -q '0.1.8-alpha' rootfs-overlay/etc/2pny/version

echo '[4/8] Explicit AutoAP + Ethernet rescue'
test -s rootfs-overlay/etc/hostapd/hostapd-2pny.conf
test -s rootfs-overlay/etc/dnsmasq.d/2pny-setup.conf
grep -q '^ssid=2PNY-SETUP$' rootfs-overlay/etc/hostapd/hostapd-2pny.conf
! grep -Eq '^(wpa|wpa_passphrase|wpa_key_mgmt)=' rootfs-overlay/etc/hostapd/hostapd-2pny.conf
grep -q 'dhcp-range=interface:wlan0,10.42.0.20,10.42.0.80' rootfs-overlay/etc/dnsmasq.d/2pny-setup.conf
grep -q 'dhcp-range=interface:eth0,10.43.0.20,10.43.0.80' rootfs-overlay/etc/dnsmasq.d/2pny-setup.conf
grep -q '10.42.0.1' rootfs-overlay/usr/local/sbin/2pny-networkd
grep -q '10.43.0.1' rootfs-overlay/usr/local/sbin/2pny-networkd
test -f rootfs-overlay/etc/systemd/system/2pny-networkd.service
test -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-networkd.service
test ! -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-setup-watch.service

echo '[5/8] Panel APIs / captive portal / modules'
for token in '/healthz' '/api/ap' '/generate_204' '/hotspot-detect.html' '/api/modules' '/api/hardware/scan' '/api/setup-status'; do
  grep -q "$token" src/2pnyd/main.go
done
grep -q '2PNY_MODULE_STATUS_API_V1' src/2pnyd/main.go
test -x rootfs-overlay/usr/local/sbin/2pny-module-status
test -s rootfs-overlay/usr/share/2pny/modules.json
python3 -m json.tool rootfs-overlay/usr/share/2pny/modules.json >/dev/null

echo '[6/8] MMDVM/RF/Talker Alias'
test -f rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service
grep -q 'MemoryMax=96M' rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service
grep -q '590c531391dfd3146073afbc3956f70d42c62a46' builder/build-image.sh
grep -q '^DumpTAData=1$' rootfs-overlay/usr/local/sbin/2pny-rf-apply

echo '[7/8] Networking source contract'
grep -Fq 'no-auto-default=*' rootfs-overlay/etc/NetworkManager/conf.d/20-2pny-appliance.conf
# Base OS and package presence are checked directly in the final mounted image.

echo '[8/8] Lean runtime / state'
grep -q 'Storage=volatile' rootfs-overlay/etc/systemd/journald.conf.d/2pny.conf
test ! -e rootfs-overlay/var/lib/2pny/provisioned
test ! -e rootfs-overlay/var/lib/2pny/ap-disabled

echo 'OK: 2PNY 0.1.8 source contracts valid'
EOF
chmod 0755 builder/validate-source.sh
bash -n builder/validate-source.sh
echo '2PNY 0.1.8 authoritative validator installed'
