# CLV PSP/ABL payload provenance inventory — action log

## Intent (before write)

- Timestamp: 2026-09-20 Asia/Almaty
- Actor: independent reviewer, stage-2 checkpoint
- Target: immutable `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Input identity: 16 MiB, expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Procedure: reuse `scripts/firmware_audit.py` and `scripts/psp_ps1_verify.py` results; perform fresh direct-byte parsing of the `$PSP` directory and `$PS1` headers for exact ABL types `0x30..0x34`; compute full-container, signed-body, and decompressed payload hashes; compare against preserved historical Robin payload files and ABL decompilation-source provenance. Inspect ISA indicators without modifying firmware or executing imported payloads.
- Rationale: phase-2 consumer reports need an exact PSP/ABL payload boundary, bootloader payload IDs, offsets, hashes, ISA, and explicit limits on historical ABL source correspondence. Report names alone are insufficient.
- Expected effect: create a machine-readable provenance inventory and an English research report; no input image or shared plan/memory is changed.
- Rollback: remove only the newly created report/evidence files if needed; immutable baseline remains untouched.
  ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8 evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
  2b8cb2c85de39b57264e58e34aab7764b1295a96353e7ace77dd092df8559456 docs/research/20260920-clv-psp-abl-provenance.md
  7fab47054f8548c2bf5812ddc1ee649ec42a22184b4107fef75e210649c29f94 evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json
  32dbcc6353ff0b07c87942558736b3a789d8a259e332f1fa9a6bee06cfd813a1 evidence/firmware-audit/20260920-clv-psp-abl-provenance/stage2-checkpoint-review-result.json
  5e5f5310314ef823674e45e7c136f733081e56e59d859df4eae36370bdd56b5b evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv_psp_abl_inventory.py
  d93e1f0739d14247f3d07e1f0a0705bb55abcda732c6b0dd641b2499efe0de56 evidence/firmware-audit/20260920-clv-psp-abl-provenance/stage2_checkpoint_review.py

## Observed result after write

- Fresh inventory completed with status `PASS`: exact input hash matched; 5/5 ABL payloads parsed, zlib-decoded to declared sizes, and classified by ARM/Thumb entry markers.
- Exact Robin-5 full-container equality: `5/5 PASS`; extracted body-after-0x100 equality: `5/5 PASS`.
- Stage-2 worker result reopen: CBS lifecycle `26/26 PASS`; MemoryClock consumer `12/12 PASS`; memory-init control flow `27/27 PASS`; dispatch selection `21/21 PASS`; caller chain `21/21 PASS` as reported. Independent direct-byte checkpoint: `25/25 PASS`.
- Corrections recorded in the owned report: PEI `EFI_PEI_SERVICES**` double dereference; size-pass versus fill-pass distinction; pointer identity retained without unproven `HOB+0x28` offset; stale FCLK token `0x1332` wording corrected to `0x1331`.
- Readback: report, machine results, scripts, and this action log reopened after writing; hashes recorded above.
- Rollback: remove only owned report/evidence files; immutable CLV baseline remains unchanged.
- Remaining uncertainty: historical ABL source-text-to-binary identity, opaque AGESA/PSP/APOB memory-training consumer, runtime callback invocation, physical clocks, training, hardware acceptance.

## Verification command correction

- Initial JSON readback helper failed with `ValueError: seek of closed file` due a local helper reading a closed file handle; no artifact was changed. Corrected readback reopened both JSON files successfully (status PASS).

## Integration intent amendment (before shared writes)

- Timestamp: 2026-09-20 Asia/Almaty
- Actor: independent reviewer, final checkpoint integration
- Targets: append-only current checkpoint sections to `specs/2026-09-20-clv-sync-development-plan.md` and `memory/oc-recheck.md`.
- Scope: record only the independently reopened PSP/ABL inventory and four current phase-2 role paths; preserve phase-2 `PARTIAL` status and all unrun consumer/training/hardware gates.
- Required qualifications: local pointer identity only; first size pass versus second fill pass; PEI `EFI_PEI_SERVICES**` double dereference; PPI/data handoff is not training; ABL source version alignment is not source/binary identity; current FCLK token `0x1331`.
- Expected effect: shared plan/memory carry the bounded result and absolute evidence paths without promoting a consumer, training, synchronization, or hardware claim.
- Rollback: remove only the two appended sections, preserving prior historical corrections and decisions.

## Integration observed result

- Shared plan and memory append-only integration completed with phase-2 `PARTIAL` status preserved.
- Four absolute current role report paths and their four evidence manifests were reopened before writing and are recorded in the shared sections.
- Integrated qualifications only: exact ABL IDs/offsets/version and Robin-5 byte equality; version-aligned historical source without source/binary identity; PEI `EFI_PEI_SERVICES**` double dereference; PPI/data handoff not training; local pointer identity with size-pass/fill-pass distinction; HOB+0x28 unproven; FCLK `+0x6A3 -> 0x1331`.
- No consumer/training/hardware gate was marked complete. No firmware or candidate artifact changed.
- Readback and hashes after integration:
  9b1c2fb72f249e37dd01045f4507f1f2ae648a2d341941850203a3208369bf9a specs/2026-09-20-clv-sync-development-plan.md
  8fbc0ad3ff9cb04efb9d2aac62de72beeb6206f44c55b36502320960fd8462af memory/oc-recheck.md
- Rollback remains removal of only the two appended sections; prior historical corrections are retained.
