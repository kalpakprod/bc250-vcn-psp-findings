# Findings and corrections

This collection is dated 2026-10-09. We did not run board commands, reset or flash the board, change GPIOs or test codecs to put it together. The dates below refer to recorded experiments, not the board's current state. Imported reports and community observations are separate from static analysis, emulation and hardware measurements.

## What the VCN discovery capture tells us

A [sysfs capture from 2026-09-25](research/docs/research/2026-09-25-live-vcn-harvest-ssh.md) reports VCN **2.0.3**, `harvest=0x0`, three base addresses and `num_instance=0`.

On that sample, the exposed discovery metadata did not mark VCN as harvested. The capture does not independently establish the fuse state, prove that VCN is physically healthy or explain why BC250 parts were binned. Other boards may differ, and this collection has no successful encode/decode result.

The original report says “not fused” and “software, not silicon”. Those claims go further than the observation supports. We've kept the report so readers can see what was said at the time.

The correspondent reported progress on PS5 Linux VCN. We did not independently verify that news here. A working PS5 VCN would not, by itself, establish BC250 firmware policy, power sequencing or silicon health.

## Paths we misidentified as VCN power control

Some early notes labeled mailbox calls and firmware functions as VCN power control. Later analysis of the message tables and function bodies identified GFX deep-sleep, clock or telemetry paths instead. Read these corrections before using an old recipe:

- [Second-gate analysis and recorded read-path failure](research/.procoder/plans/2026-09-25-second-gate-passthrough.md).
- [Path C investigation, retractions and limits of the handler census](research/.procoder/plans/2026-09-25-vcn-path-C-research.md).
- [VCN/SMU document audit](research/docs/research/2026-09-27-vcn-smu-status-audit.md).

Those records did not establish a working software-only path. They also do not prove that a future path is impossible. Unnamed or partly analyzed handlers and unread silicon surfaces limit the negative conclusion.

A mailbox can respond, or a transport can allow writes, without the codec island being powered. Some reads can wedge the SMU while the OS continues to respond.

## What the BIOS/DXE experiments established

The ladder and logs include control drivers, early-slot and appended drivers, partial GASKET replays, failures and dated boot observations. The audit found entrypoints that return `EFI_SUCCESS` after non-fatal errors in the sequence.

Flashing and readback confirm one step. Successful boot, VCN initialization and a real encode/decode test are further steps, and none follows automatically from the previous one. Publishing these records adds no hardware confirmation.

## Where PSP TOCTOU stands

The [legacy-rig audit](research/docs/research/2026-09-27-toctou-document-audit.md) found problems with selector, DMA and disarm semantics, plus inconsistent read-order and wiring claims. A PIO file or build flag does not establish that a MISO responder is active.

The [2026-10-07 software result](evidence/reports/waveshare-psp-toctou-20261007/RESULT.md) records 24/24 host tests and serve-map checks. Its stock/candidate identities and `0x9DB560..0x9DB6A0` window apply to the named image pair, not every BIOS revision. We did not rerun those checks for this collection.

The [2026-10-08 reset-path investigation](evidence/reports/waveshare-reset-path-20261008/RESULT.md) traced PROGRAM# to the system-reset network. That narrows a possible route, but it does not establish diode polarity, FCH SPI high-impedance ownership, safe DPD use or response timing.

The records do not establish a safe clip-only substitution path or a successful physical PSP TOCTOU run. The newer reset investigation describes a prepared small-window responder with unresolved first-bit timing, so the older claim that no responder code exists at all no longer describes the whole implementation. Full response-path acceptance, electrical isolation/ownership and observed PSP read order still need separate evidence.

## Reading the older reports

Reports sometimes contradict one another or state more than their evidence supports. We kept their paths and context without endorsing every sentence. Build, test and PASS labels remain dated source claims unless someone reproduces and documents them. The catalog records provenance and exclusions for private or decompiled originals that were not published.
