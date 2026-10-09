# Decision record: plain CLV 5.00 is the offline development TARGET

Date: 2026-09-21 (Asia/Almaty)

## Decision

Bind offline development `TARGET` to the immutable plain CLV 5.00 image:

`/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`

SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`  
Size: `16,777,216` bytes (16 MiB)  
Mode: `0644`; no immutable attribute is asserted, so “immutable” here means the workflow source is preserved and must not be modified in place.

The operator has clarified that, before applying any selected settings, they will flash whichever BIOS the project selects. This removes the current-installed GitHub image as an **offline-development blocker**. It does not authorize a flash now, establish current chip contents, or waive the separate hardware gate.

## Source identity and provenance

- `stat`, `sha256sum`, and `lsattr` were run on the exact target path. The observed hash and size above match the pinned CLV identity in `memory/oc-recheck.md`, `specs/2026-09-20-clv-sync-development-plan.md`, and the prior ROM ledger.
- `evidence/donor/retroweb-20260916/manifest.json` identifies this as a 2026-09-16 RetroWeb community redistribution for BC-250 board page ID 20611; uploader is unknown and the manifest explicitly says it is research-only, not built/reviewed/flash-approved.
- Existing CLV static evidence is reused, not re-run: native fields include `AmdSetup+0x316` (`Memory Clock Speed`, stored `0x24`, menu label `1800MHz`), `+0x330` (`UclkDiv1M0`), `+0x6A3` (`FCLK_DPM`), `+0x703/+0x704` (DF override), and the mapped Memory P-state field. The exact static reports and the phase-2 checkpoint remain qualified as partial.
- This donor is not being treated as the current board image, a user readback, a safe BIOS, or a hardware-accepted release.

## Requirements bound to this target

1. Preserve the native memory request: do not silently lower or replace the CLV `1800MHz` request while tracing the route.
2. Require evidence for **physical** `MCLK:UCLK:FCLK = 1:1:1`; equal menu values, aliased Linux metrics, stored NVRAM bytes, or a successful build are insufficient.
3. Keep SoC `1.15 V` as the operator's desired target/ceiling constraint only. It is not a proven safe rating, not a recommendation, and must not be substituted with VCORE, GFX, MEMIO, or an unresolved `VDDCR_VDD` offset.
4. Keep CPU, memory, SoC, GFX, VCORE, and MEMIO domains separate. Do not add voltage, CPU, or timing changes to a clock experiment.
5. Preserve the CLV source and all signed/provenance material. Any future candidate must be a new output with independent review; no candidate is created by this decision.

## First unfinished technical action (offline; independent of current board state)

**Complete the native clock-field consumer/actuator handoff, starting with the unresolved indirect registration/provider path for `$INV` token `0x1204` (`UclkDiv1M0`) from the CLV PEI serializers into the ABL1/HOB/APOB/SMU-side consumer path.**

This is the first unfinished action because:

- direct serializer ownership and selected containing-function boundaries are already closed in the retained evidence;
- the project checkpoint explicitly leaves wrapper registration/indirect or callback-table/HOB/DMA/runtime delivery unresolved;
- the same phase-2 gate still lacks the field-to-divider/training actuator, units/rate conversion, Memory-P-state interaction, and synchronous-crossing selection needed to make an offline 1:1:1 candidate defensible;
- current board identity, current installed firmware, and hardware telemetry are not prerequisites for this static handoff trace.

The bounded action must follow existing evidence rather than repeat scans: inspect the already extracted exact CLV ABL1/PSP/HOB/APOB/PEI artifacts and resolve one concrete provider/consumer edge for token `0x1204`; retain the adjacent `0x11ED` (native `1800MHz`) and the FCLK/DF fields as context, but do not change their bytes. Stop with an explicit unresolved edge if the provider, runtime base, units, or actuator cannot be established from the available artifacts.

## Not authorized by this decision

- No SPI flash, NVRAM write, register/MMIO/SMU write, voltage application, physical feedback change, or board modification.
- No claim that CLV is safe, bootable on the present board, synchronized, trained at 1800, or performance-improving.
- No request for a current GitHub image, current full dump, or board photo merely to begin this offline trace.
- No candidate build until the consumer/semantic gate and migration/default specification are complete; any later build remains experimental and separately gated.

## Evidence boundary

Current status is `offline target bound; phase 2 partial`. Source identity is `observed-bytes`; existing field/consumer work is `static-analysis`; no new hardware result was produced. Hardware acceptance remains separate and requires exact target identity, recovery/readback, independent clock/divider observation, training/error screening, and controlled performance measurements.
