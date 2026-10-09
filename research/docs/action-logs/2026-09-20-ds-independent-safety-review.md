# Independent safety review — BC250 DF/MCLK 1800 MHz and SoC 1.15 V targets

Timestamp: 2026-09-20 (Asia/Almaty)
Actor: `/root/ds_independent_safety_review` (DeepSeek V4.1 Flash worker, `flash_builder`), independent of the authors of the reviewed artifacts.

Bounded question: do the two current OC targets — a stored **DF/MCLK 1800 MHz** request and a **SoC 1.15 V** ceiling — have any board-specific evidence that they are representable, achievable, or safe on BC-250, and does any existing repository candidate actually request a voltage change?

Pinned target: ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`), its `AmdSetup` NVAR record (body base `0x4CF`), exact `CbsSetupDxe` PE32 (`7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`) with the existing IFR parser `import/from-windows/Users/kukuruza/bc250-bios/tools/uefi/e1_ifr_dump.py`, and every `candidates/*.bin` plus its `.build.json` manifest.

Reason: `specs/2026-09-20-clv-sync-development-plan.md` and `memory/oc-recheck.md` record `AmdSetup+0x316=0x24` as IFR-labelled `1800MHz`, while `memory/firmware-audit.md` records `+0x316=0xFF` (`Auto`) for a different capture, and the only historical `DF 1800` report is associated with a physical feedback modification and a reported SoC above `1.2 V`, outside the operator ceiling. The `+0x6E5/+0x6E6` (VDDCR_VDD) and `+0x6EA/+0x6EB` (VDDCR_GFX) offset pairs have no proven unit, sign, or consumer. These claims must be re-measured, not repeated.

Scope of the checks (offline, read-only with respect to inputs):

1. Pin the ROM, module, candidate, and manifest hashes.
2. Re-read the literal `AmdSetup` field bytes for the clock and voltage fields from the pinned ROM.
3. Re-derive the IFR option→label mapping for the `MemoryClockSpeed` question from the pinned ROM's own `CbsSetupDxe` and decide whether stored `0x24` is labelled `1800MHz` there.
4. Recompute, for every candidate image, the changed-byte set against the pinned ROM, classify each change as voltage-touching or not, and cross-check the recorded `.build.json` metadata against the recomputation.
5. Emit a safety-claim matrix that marks each required evidence class for both targets as pass/fail/inconclusive/unrun, and name the decisive missing test.

Expected effect: one machine-readable review result plus a human report; either a bounded supportable claim or an explicit no-evidence/no-go statement for each target. No ROM, NVRAM, register, candidate, or hardware mutation; no new candidate build; no web research.

Rollback: delete only `docs/action-logs/2026-09-20-ds-independent-safety-review.md`, `docs/research/2026-09-20-ds-independent-safety-review-1800-115v.md`, and the unique evidence directory `evidence/firmware-audit/20260920-ds-independent-safety-review/`. All reviewed inputs stay untouched.

## Observed result

Timestamp: 2026-09-20 (Asia/Almaty). The bounded review ran to completion offline; no input changed.

Verifier: `evidence/firmware-audit/20260920-ds-independent-safety-review/verify_safety_review.py` (SHA-256 `18f07423d5f9114cfa39aee87efe2f96e0017b49ff5e28832e8fe53c102520a0`).
Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-ds-independent-safety-review/verify_safety_review.py`.
Final run (`run2`): exit status `0` (file `run2.exit`, SHA-256 `19eaf43821a7660ec323a87c8457bf74823beb296c39f5e01aa8a683aa50f061`), stderr `0` bytes (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), stdout `917` bytes (SHA-256 `c592df416ebd23b6b47be9a1a2c60a8c0f092c987e704dedf8e17a38ca8a7211`) reporting `SAFETY_REVIEW_COMPLETE`, `13/13` checks passed.

`run1.*` in the same directory is the earlier pre-classifier execution (10/10 checks, same inputs) retained as history; it was superseded by the classifier change that separates a deliberate voltage request from unconfigured `0xFF` lineage bytes. No source input was edited.

Findings (all from literal bytes re-read in this run):

1. Pinned donor `+0x316` / absolute `0x7E5` = `0x24`; the donor's own IFR question QID `527` at that offset labels `0x24` as `1800MHz` and `0x23` as `1750MHz`, `0xFF` as `Auto`. The recorded conflict (`0x24` vs `0xFF`) is a different-image artifact; only the pinned donor hash is in scope.
2. Pinned donor voltage fields are `Auto`/zero: `+0x6E5=0x00`, `+0x6E6 u32=00000000`, `+0x6EA=0x00`, `+0x6EB u32=00000000`. DF clock `+0x703=0x01`, `+0x704=0x058C` (1420).
3. 41 `candidates/*.bin` re-diffed against the donor. 10 are pinned-clv lineage and all 10 recorded `.build.json` changed-offset and `voltage_changed` metadata matched the recomputation (`manifest_disagreements: []`). 4 unflashed candidates deliberately request a nonzero VDDCR_VDD offset — control `0x01` (Manual), value `50 00 00 00` (80): `BC250_5.00_clv_OC_vdd80_v001.bin`, `_vdd80_v002.bin`, `_OC_sync1750_vdd80_v001.bin`, `BC250_5.00_clv_MeiMeiDXE_SteamLogo_Sync1to1_v001.bin`. GFX voltage is untouched in all four. Three further images carry unconfigured `0xFF`/`FFFFFFFF` Setup bytes from the C0A-stock lineage; those are classified as lineage bytes, not requests.
4. Hash-pinned consumer-boundary result re-read: status `PARTIAL_BLOCKED_AT_CONSUMER`, two direct reader tokens (`0x10FF`, `0x1104`), `requested_0x1364 = false`.
5. The historical `DF1800` recipe in `specs/2026-09-20-clv-sync-development-plan.md` is associated with a physical feedback modification and a reported SoC above `1.2 V`, outside the 1.15 V ceiling.

Verdict: `NO_GO_FOR_VOLTAGE_CHANGE_AND_UNPROVEN_FOR_1800MHz`; flash recommendation `NOT_RECOMMENDED`. 1.15 V remains an unvalidated operator ceiling; `80` has no established unit, sign, encoding, or located consumer; 1800 MHz is the donor's stored option, not a measured applied clock.

Unrun/limits: no board contact; no flash, NVRAM, register, or candidate write; the corpus-wide `0x1363`/`0x1364` sweep recorded in `memory/oc-recheck.md` was not rerun; C0A/M2-lineage images were diffed against the clv donor only.

## Final artifact readback

- Report: `docs/research/2026-09-20-ds-independent-safety-review-1800-115v.md`, SHA-256 `5fd8274b328a492032ee851f27aa075d3c036a3e099475ec7ab98455a3f3f087`.
- Machine result: `evidence/firmware-audit/20260920-ds-independent-safety-review/safety-review-result.json`, SHA-256 `f30047365887213baeba0033ab4be062509455f89503640ac3b970abec249623`.
- Manifest covering evidence, report, and this action log: `evidence/firmware-audit/20260920-ds-independent-safety-review/SHA256SUMS.final`.
- This action log: SHA-256 recorded after the manifest is written; verified with `sha256sum -c`.
