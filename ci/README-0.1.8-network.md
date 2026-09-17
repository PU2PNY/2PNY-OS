# 2PNY 0.1.8 Network Architecture

- Explicit open AutoAP with hostapd
- Explicit DHCP/DNS with dnsmasq
- Wi-Fi setup: 10.42.0.1/24
- Direct Ethernet rescue: 10.43.0.1/24
- Ethernet and AP independent
- Normal station Wi-Fi returned to NetworkManager after provisioning
- NetworkManager keyfiles root-only
- Panel remains on port 80
- DMR Talker Alias preserved

This file also triggers the branch build after workflow creation.
