# 2PNY OS 0.1.8 — Network Core

Design goal: first access must remain reachable even when one transport fails.

- Wi-Fi setup AP: hostapd, SSID `2PNY-SETUP`, open, `10.42.0.1/24`.
- Wi-Fi DHCP/DNS: explicit dnsmasq instance, captive DNS to `10.42.0.1`.
- Direct Ethernet: static `10.43.0.1/24` plus independent DHCP-only dnsmasq instance.
- Ethernet and setup AP are independent and simultaneous before provisioning.
- NetworkManager `shared` mode is not part of first-access networking.
- `2pny-network-core` owns first-access interfaces and self-heals IP/daemon state.
- After provisioning, interfaces return to NetworkManager for normal client networking.
- The panel listens on all interfaces at port 80.
- Existing MMDVMHost, RF rollback, module inventory and DMR Talker Alias are preserved.

The architecture is informed by Pi-Star's explicit hostapd/dnsmasq AutoAP model and WPSD's separation of Ethernet, normal Wi-Fi and AutoAP, while keeping the 2PNY implementation independent.
