# 2PNY 0.1.6 — RF / MMDVMHost layer

## Goal

Turn the hardware identification from 0.1.5 into the first safe operational RF layer without yet enabling external digital networks.

## Scope

- Build and install upstream G4KLX MMDVMHost as a native binary.
- Pin the upstream source commit for reproducible builds.
- Strip build symbols and remove compiler/source/build dependencies from the final image.
- Run MMDVMHost as an unprivileged `mmdvm` user in the `dialout` group.
- Accept RX/TX frequency, RX/TX offset, simplex/duplex, modem port, callsign and DMR ID from 2PNY.
- Apply configuration atomically.
- Back up the previous RF config before every apply.
- Start/restart MMDVMHost and automatically roll back if the service cannot stay active.
- Keep DMR, D-Star, YSF, P25, NXDN, POCSAG, FM and every external network disabled in this layer. Network/protocol activation belongs to the next module.
- Add an on-demand resource snapshot instead of a permanent monitoring daemon.

## Upstream pin

MMDVMHost repository: `g4klx/MMDVM-Host`

Pinned commit for this Alpha:

`590c531391dfd3146073afbc3956f70d42c62a46`

The build must verify that exact commit before compilation.

## Runtime design

`2pnyd` remains the only web/control daemon. MMDVMHost is only enabled after the RF wizard has a validated MMDVM port and RF configuration.

Systemd owns restart/recovery. There is no watchdog polling process just to check whether MMDVMHost is alive.

## Safety

`2pny-rf-apply` uses broad hardware sanity limits only. It does **not** claim to determine whether a frequency is legally permitted in the operator's jurisdiction. The UI must make the configured frequency explicit before applying it.

The RF apply helper does not enable a digital protocol or network. This prevents an incomplete Alpha from unexpectedly transmitting network traffic while RF parameters are still being validated.

## Completion criteria for 0.1.6

1. 0.1.5 hardware probe identifies the MMDVM and usable port.
2. RF values can be saved from the wizard without a blocking request.
3. Config is written atomically and a backup is retained.
4. MMDVMHost starts against the detected modem and stays active.
5. A failed apply restores the previous configuration automatically.
6. The panel reports apply/start failure instead of silently advancing.
7. Runtime dependency footprint is measured and meets `docs/PERFORMANCE.md` budgets or has an explicit exception.
8. Pi 4 physical test passes before promotion to `main`.
9. ARM64 regression testing covers Zero 2 W / Pi 3 / Pi 4 / Pi 5 compatibility assumptions; original Pi Zero/Zero W remain on the planned 32-bit image track.
