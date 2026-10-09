# R1 OC baseline identity and feature reconciliation

## Intent — 2026-09-19T17:26:45+05:00

Actor: root. Root owns local byte reconciliation and the feature manifest; no worker dispatched because extraction and comparisons share one evidence set.
Scope: local, read-only firmware inventory. No board access, flash, voltage changes or candidate generation. Preserve all existing images.
Inputs: named clv/MeiMei/FirstMarker/W9 candidates, programmer readbacks from 20260918 and 20260919, original read-a/read-b/dump/2.bin and the retained runtime CPU logs. Treat filenames and historical reports as leads, not proof.
Existing route: scripts/firmware_audit.py analyze_image, Extractor, FV and section walkers. Reuse these in memory to fingerprint executable and logo sections; no duplicate parser. Existing catalogs do not reconcile later W9/readback features, so add a bounded evidence report.
Procedure: hash inputs before analysis; enforce 16 MiB image size; parse PSP/BHD/APCB and FV metadata; independently sum FV headers; collect executable identities and logo-section fingerprints without persisting executable bodies or security material; compare candidate/readback identities and protected regions. Record selected non-sensitive CPU evidence only, not raw boot command lines.
Outputs: evidence/firmware-audit/20260919-oc-baseline/identity.json, reproduction script, docs/research/2026-09-19-oc-baseline-identity.md, memory/oc-recheck.md append and R1 plan status.
Format assumptions: little-endian 16 MiB SPI images; NVRAM FV at 0..0x20000; PSP at 0x8E0000; BHD/APCB at 0xAB0000/0xAB1000; PI FV/FFS sections including guided LZMA. Parser limits remain explicit; structural success is not boot proof.
Expected result: exact identities, feature presence/absence/unverified and a baseline decision or explicit blocker. Rollback: remove only newly generated R1 reports/script if requested; append corrections rather than rewrite historical evidence. No source image is changed.

## Observed result

Executed `python3 evidence/firmware-audit/20260919-oc-baseline/reproduce.py`: 21 full images hashed and parsed using existing firmware_audit functions. All reported PSP/BHD/APCB and outer FV header checks PASS. identity.json SHA-256 b84f0fec718e3759a1761334e24b09a615d6ae747a3cd3167acfde529c5de742. A separate Python assertion pass rehashed all 21 original files; system sha256sum independently matched W9, FirstMarker recovery and read-a identities.
Independent check procedure: locate GUID EE4E5898-3914-4259-9D6E-DC7BD79403CF in the DXE FV, read section u24 size and guided DataOffset, lzma.decompress(FORMAT_ALONE), count little-endian logo/core/injected-driver GUIDs. W9 and FirstMarker decoded 4309008 bytes, with zero standard logo and MeiMei core GUIDs; SteamLogo v002 decoded 4333584 bytes and contains both. W9 contains the B6250780 driver; SteamLogo v002 does not.
Finding: W9-labelled candidate is byte-identical to W11 readback, not original W9 readback. No feature-complete integrated OC baseline established. Preserved stock recovery equals two additional copies; FirstMarker equals its retained readback. Historical W10 CPU log has 8 cores/16 logical processors, not current-target proof.
INCONCLUSIVE: original W9 readback executable extraction coverage (61 vs 233); no claim of complete FFS validation. UNRUN: current hardware, firmware execution, rail/clock measurements and signatures. No board access or firmware change occurred.
Updated memory/oc-recheck.md with the naming correction and specs/2026-09-19-oc-sync-recovery-plan.md with the blocker. R1 local audit finished; task remains BLOCKED for feature-complete baseline selection. R2/R3 read-only analysis may proceed against hash-pinned clv. Report: docs/research/2026-09-19-oc-baseline-identity.md.
