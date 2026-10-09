# OC candidate recheck

## Intent — 2026-09-19T17:05:31+05:00

Actor: root. Scope: review existing OC candidates, not build or flash. Root owns byte verification and corrections; no worker dispatched. Record the correction in memory/oc-recheck.md. Preserve existing binaries and manifests as historical evidence. Rollback: append a superseding correction; no hardware changes.

## Observed result

Read every candidates/BC250_5.00_clv_OC_*.bin with Python pathlib; compute SHA-256, compare all bytes with evidence/donor/retroweb-20260916/BC250_5.00_clv.bin, and decode little-endian fields at AmdSetup body 0x4CF. Cross-check labels against evidence/firmware-audit/amdsetup-ifr-field-map.json.

Base SHA-256: ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.
All nine candidates are 16777216 bytes, unchanged outside 0x20000. This proves confinement, not application or safety.

- sync_v002 SHA-256 544b3c24d4b969c3b9b5ab7bbcb873b552f2757808a5855806b5324239749b27: memory enum 0x23 (IFR label 1750MHz), DF request 1500, divider enum 1, FclkDpm 0. NOT a demonstrated 1:1:1 profile, even its requested frequency labels differ.
- FclkDpm 0 means Disabled, not Auto (Auto is 0x0F).
- UclkDiv1M0=1 is labelled Enabled only; effective UCLK and clock-domain synchronization remain unproven.
- vdd80 v001/v002 SHA-256 3891f8a6240b594bddc393d8ee55c971229414bad08ca17c7d5883e2357a4948: raw u32 80, NOT proven +80mV or 1.15V. Withdraw calibration/flash recommendation.
- sync1750 v001 variants set Tcl=16 and change multiple controls; withdraw flash recommendation.
- df1430/1450/1470/1500 v002 each change only 0xBD3; those are stored requests, not measured clocks or stability.
- All candidates use plain clv as source, not a verified integrated W9/8-core/Steam-logo baseline. No retention of those added features is established.
- Prior NVAR audit used store offset 0x1000 and selected zero AmdSetup records; it did not validate the edited record at 0x4BB.
- Builder lacks a full-source hash gate and accepts arbitrary voltage/frequency overrides. Its one-variable claim does not hold for sync or combined overrides.

Decision: NO-GO for flashing these OC artifacts from this review. Do not substitute equal requested numbers for a proven synchronous mode. No new image or hardware action performed. Runtime clocks, rail voltage, training, latency and stability UNRUN; independent release review INCOMPLETE. Next: trace voltage consumer/rail and clock telemetry semantics before a single-variable hardware experiment. No evidence establishes 1.15V as a safe limit for this board.
