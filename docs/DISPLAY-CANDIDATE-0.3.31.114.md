# PU2PNY-OS 0.3.31.114 — display-only candidate

## Decision

The audited 0.3.30 display runtime already implements the requested safe behavior. This candidate therefore **does not rewrite the display runtime**. It revalidates and freezes the existing implementation for isolated display testing.

Reused runtime, unchanged:
- `src/2pny-display-detector-0.3.30.py`
- `src/2pny-display-core-0.3.30.py`
- `src/2pny-display-apply-0.3.30.py`
- `src/display-0.3.30.html`

## DISPLAY-031 — Real physical detection

Nextion detection uses `connect` and requires a real `comok` response to claim physical confirmation. Model/firmware/MCU/serial/flash metadata are parsed only from the actual response. Physical hardware identity and HMI/layout identity remain separate; model does not prove PU2PNY/G4KLX/ON7LDS/WPSD HMI.

For a modem-connected Nextion while MMDVMHost owns the serial port, detection uses the existing MMDVMHost MQTT display bridge instead of opening the protected UART. Lack of COMOK remains unconfirmed, never promoted to physical PASS.

## DISPLAY-032 — Exactly one writer

Two mutually exclusive modes remain supported:
1. `pu2pny-modern-v2`: MMDVMHost owns the modem serial transport; PU2PNY Display Core is the single logical renderer through the MMDVM bridge.
2. `mmdvmhost-native`: MMDVMHost owns transport and native Nextion rendering; PU2PNY Display Core is stopped.

A writer conflict is an error. No second renderer may compete for the same display.

## DISPLAY-033 — Incremental rendering

Nextion page rendering clears only on a real logical page/state transition. Inside the same page, command targets are cached and unchanged fields are suppressed. The modem bridge keeps complete commands in bounded frames.

## DISPLAY-034 — Safe compatibility fallback

Native fallback remains available for:
- G4KLX / ScreenLayout 0;
- ON7LDS L2 / ScreenLayout 2;
- ON7LDS L3 / ScreenLayout 3.

NextionDriver/L3 HS is not silently enabled and must only be offered when the driver is actually installed/validated. No TFT/HMI is flashed automatically.

## Scope and rollback

This candidate adds only CI/test/documentation for revalidation. RF, MMDVM, DMR, D-Star, YSF/C4FM, frequencies, offsets, gateways, Wi-Fi/wizard, APRS, Direct and update runtime remain unchanged relative to the parent candidate. Since no display runtime is replaced here, rollback is simply reverting this candidate branch/gate.

## Validation

- DOC: IMPLEMENTED.
- SW: PENDING execution of `.github/workflows/0.3.31.114-display-candidate.yml`.
- VPS: PENDING on a confirmed PU2PNY-OS test VPS.
- HW: PENDING Raspberry Pi + physical display. COMOK, visual stability and writer ownership must be observed on real hardware.
- PROD: NOT APPROVED.
