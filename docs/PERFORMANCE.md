# 2PNY — Performance and resource contract

Performance is a release requirement, not a post-release optimization.

## Supported hardware families

2PNY must keep the same panel/workflow across the Raspberry Pi family, but one binary image cannot safely cover every CPU generation.

| Family | Architecture path | 2PNY image |
|---|---|---|
| Raspberry Pi Zero / Zero W | BCM2835, ARM1176, 32-bit | `armv6/armhf` image |
| Raspberry Pi 2 | 32-bit compatibility baseline | `armhf` image |
| Raspberry Pi Zero 2 W | 64-bit Cortex-A53 | `arm64` image |
| Raspberry Pi 3 / 3+ | 64-bit capable | `arm64` image |
| Raspberry Pi 4 / 400 | 64-bit | `arm64` image |
| Raspberry Pi 5 | 64-bit | `arm64` image |

The current Alpha image is ARM64. Original Pi Zero/Zero W support therefore requires a separate 32-bit build; it must not be advertised as working from the ARM64 image.

## Architectural rules

- No Docker/containers in normal operation.
- No permanent Node.js or Python web runtime.
- No MySQL/PostgreSQL/Apache dependency.
- `2pnyd` stays a single native Go control process with local static UI.
- MMDVMHost and gateways are native binaries and are started only when required.
- Protocol gateways not enabled by the user remain stopped.
- No tight polling loops. Prefer events, systemd, NetworkManager dispatcher, MQTT/SSE only where justified.
- Logs are bounded. High-volume diagnostic logging is opt-in and temporary.
- Persistent SD writes are minimized; volatile state belongs under `/run` where possible.
- No overclocking and no forced performance governor.
- Configuration writes must be atomic with backup and rollback.

## Resource budgets

These are engineering gates to be measured on physical hardware before Stable. They are targets, not claims until measured.

### Process budgets

- `2pnyd` idle RSS target: <= 20 MiB.
- MMDVMHost idle RSS target: <= 24 MiB.
- Core 2PNY + MMDVMHost combined RSS target: <= 55 MiB.
- No single optional gateway may add > 35 MiB idle RSS without explicit review.
- No memory growth > 10% during an 8-hour idle soak test.

### CPU budgets

- Idle 2PNY services target: <= 5% of one CPU core on Zero 2 W / Pi 3 / Pi 4 / Pi 5.
- Original Pi Zero gets a separate measured budget because it is single-core ARMv6.
- No periodic task faster than 1 Hz unless it is directly required for radio timing or an active UI session.
- UI polling must back off when the page is hidden or disconnected.

### Responsiveness budgets

- Local panel first useful response target: < 200 ms after TCP connection on Pi 3+ under idle load.
- Save-to-disk for a normal configuration change target: < 250 ms.
- Apply/restart of a local radio service target: < 1 s when no network reconnection is required.
- First-access transitions must expose real state instead of blocking the browser on a long request.

### Thermal/power rule

Software cannot guarantee a fixed temperature because ambient temperature, enclosure, power supply, RF HAT and cooling vary. 2PNY must instead avoid unnecessary CPU wakeups, busy loops and forced clocks, expose the SoC temperature, and treat sustained thermal throttling as a diagnostic failure.

## Regression gate

Every release candidate must record at least:

- boot time;
- `2pnyd` RSS and CPU;
- MMDVMHost RSS and CPU when enabled;
- total available/used RAM;
- SoC temperature;
- load average;
- time to save/apply configuration;
- panel response latency;
- network reconnect time;
- SD write activity during idle.

A regression > 10% versus the previous accepted build must be explained or fixed before promotion to Stable.

## Runtime tooling

`2pny-perf-snapshot` is intentionally on-demand. It reads `/proc` and sysfs and does not create a permanent monitoring daemon. Future panel telemetry should reuse these low-cost kernel interfaces rather than adding another service.
