#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
cat > builder/validate-source.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo '[1/7] Shell syntax'
bash -n builder/build-image.sh
for f in \
  rootfs-overlay/usr/local/sbin/2pny-firstboot \
  rootfs-overlay/usr/local/sbin/2pny-network-core \
  rootfs-overlay/usr/local/sbin/2pny-network-switch \
  rootfs-overlay/usr/local/sbin/2pny-ap-control \
  rootfs-overlay/usr/local/sbin/2pny-rf-apply; do
  bash -n "$f"
done

echo '[2/7] Go tests'
gofmt -w src/2pnyd/main.go
go test ./...

echo '[3/7] ARM64 build'
mkdir -p rootfs-overlay/usr/local/bin
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o rootfs-overlay/usr/local/bin/2pnyd ./src/2pnyd
file rootfs-overlay/usr/local/bin/2pnyd | grep -q 'ARM aarch64'

echo '[4/7] Core files'
test -s rootfs-overlay/etc/systemd/system/2pnyd.service
test -s rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service
test -x rootfs-overlay/usr/local/sbin/2pny-network-core
test -x rootfs-overlay/usr/local/sbin/2pny-network-switch
test -x rootfs-overlay/usr/local/sbin/2pny-ap-control
test -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-network-core.service
! test -e rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-setup-watch.service

echo '[5/7] Network core'
grep -q '0.1.8-alpha' src/2pnyd/main.go
grep -q 'raspios_oldstable_lite_arm64' builder/build-image.sh
grep -q 'hostapd dnsmasq-base iw rfkill avahi-daemon' builder/build-image.sh
grep -q '^ssid=2PNY-SETUP$' rootfs-overlay/usr/share/2pny/network/hostapd.template
grep -q '^wpa=0$' rootfs-overlay/usr/share/2pny/network/hostapd.template
grep -q '^interface=@IFACE@$' rootfs-overlay/usr/share/2pny/network/hostapd.template
grep -q 'dhcp-range=10.42.0.20,10.42.0.200' rootfs-overlay/usr/share/2pny/network/dnsmasq-ap.template
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' rootfs-overlay/usr/share/2pny/network/dnsmasq-eth.template
grep -q 'ip addr add 10.42.0.1/24' rootfs-overlay/usr/local/sbin/2pny-network-core
grep -q 'ip addr add 10.43.0.1/24' rootfs-overlay/usr/local/sbin/2pny-network-core
! grep -q 'ipv4.method shared' rootfs-overlay/usr/local/sbin/2pny-network-core
grep -q '2PNY_NETWORK_CORE_HANDOFF_V1' src/2pnyd/main.go
grep -q 'systemctl stop 2pny-network-core.service' rootfs-overlay/usr/local/sbin/2pny-network-switch

echo '[6/7] RF and modules'
grep -q '^DumpTAData=1$' rootfs-overlay/usr/local/sbin/2pny-rf-apply
grep -q 'MemoryMax=96M' rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service
test -s rootfs-overlay/usr/share/2pny/modules.json
python3 -m json.tool rootfs-overlay/usr/share/2pny/modules.json >/dev/null

echo '[7/7] Panel contract'
grep -q '/healthz' src/2pnyd/main.go
grep -q '/api/modules' src/2pnyd/main.go
grep -q '/api/ap' src/2pnyd/main.go

echo 'OK: 2PNY 0.1.8 source valid'
EOF
chmod 0755 builder/validate-source.sh
bash -n builder/validate-source.sh
echo '2PNY 0.1.8 clean validator installed'
