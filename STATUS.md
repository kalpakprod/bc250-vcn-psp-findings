# Evidence status and corrections

Snapshot 2026-10-09. **No board commands, resets, flashes, GPIO operations or codec tests were performed to assemble this handoff.** Dates below describe preserved records, not current board state. Imported reports, community observations, static reasoning, emulation and hardware measurements must not be merged into one evidence category.

## VCN presence is not proof of working silicon

The recorded 2026-09-25 sysfs capture reports VCN **2.0.3**, `harvest=0x0`, three base addresses, and `num_instance=0`: [recorded capture](research/docs/research/2026-09-25-live-vcn-harvest-ssh.md).

This supports the narrow statement that the exposed discovery metadata did not mark VCN as harvested on that sample. It **does not establish the underlying fuse state independently, prove physical VCN health, or settle why BC250 parts were binned**. The original report's stronger phrases “not fused” and “software, not silicon” are retained for historical transparency but are broader than this observation proves. Other boards may differ. No successful encode/decode result is supplied here.

The correspondent's PS5 Linux progress claim is a **reported lead**, not independently verified in this handoff. Even a working VCN on a PS5 would not by itself establish BC250 firmware policy, power sequencing or silicon health.

## SMU/power research contains corrected misattributions

Early records labeled several mailbox/function paths as VCN power control. Later source-table/body analysis reclassified paths as GFX deep-sleep, clocks or telemetry. Read the correction before reusing an old recipe:

- [Second-gate analysis and recorded read-path failure](research/.procoder/plans/2026-09-25-second-gate-passthrough.md).
- [Path C investigation, retractions and limits of the handler census](research/.procoder/plans/2026-09-25-vcn-path-C-research.md).
- [VCN/SMU document audit](research/docs/research/2026-09-27-vcn-smu-status-audit.md).

No demonstrated working software-only path was established by those records. This is **not a proof that no possible future path exists**: unnamed/partially analyzed handlers and unread silicon surfaces leave limits to the negative conclusion. A readable mailbox, a transport with write access and a powered codec island are different conditions. Dangerous reads can wedge the SMU while the OS still responds.

## BIOS/DXE experiments: distinguish milestones

The preserved ladder and logs contain control drivers, early-slot/appended drivers, partial GASKET replays, failures and dated boot observations. The audit documents that some entrypoints return `EFI_SUCCESS` after non-fatal sequence errors. Success of flashing/readback does not imply successful boot; boot does not imply VCN initialization; initialization does not imply encode/decode. There is no new hardware confirmation from publishing this corpus.

## PSP TOCTOU: software work, not a hardware success

- [Legacy-rig audit](research/docs/research/2026-09-27-toctou-document-audit.md): selector/DMA/disarm semantics, inconsistent ordering and wiring claims. A PIO file or a build flag does not prove an active MISO responder.
- [2026-10-07 software result](evidence/reports/waveshare-psp-toctou-20261007/RESULT.md): recorded 24/24 host tests and serve-map checks. Exact stock/candidate identities and the `0x9DB560..0x9DB6A0` window belong to the named image pair, not every BIOS revision. These old checks were not rerun for this handoff.
- [2026-10-08 reset-path investigation](evidence/reports/waveshare-reset-path-20261008/RESULT.md): PROGRAM# → system-reset connectivity narrows a possible route but does not prove diode polarity, FCH SPI high-impedance ownership, safe DPD use or response timing.

The available records do not establish a safe clip-only substitution path or a successful physical PSP TOCTOU run. The latest reset investigation also describes a prepared small-window responder and unresolved first-bit timing; do not collapse the evolving implementation into the older statement that no responder code exists at all. Full response-path acceptance, electrical isolation/ownership and observed PSP read order remain separate obligations.

## Read historical material as historical

Original reports can contradict one another or assert more than their evidence supports. They are published with their paths and context, not endorsed word-for-word. Build/tests/PASS labels are dated source claims unless independently reproduced and documented. Private/decompiled originals withheld from publication remain visible as provenance/exclusion entries in the catalog.
