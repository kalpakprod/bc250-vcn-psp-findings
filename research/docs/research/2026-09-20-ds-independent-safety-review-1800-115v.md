# Independent safety review: BC250 DF/MCLK 1800 MHz and SoC 1.15 V targets

Historical offline safety review. The former `1.15 V target corresponds to a known field` PASS row was too strong: `AmdSetup+0x6E6` is a VDDCR_VDD **offset request**, not a demonstrated absolute SoC-voltage control. The corrected matrix row governs this document. Board reachability quoted from older memory is dated, not a live status check.

Author: `/root/ds_independent_safety_review` (DeepSeek V4.1 Flash worker). Independent of the authors of the reviewed images, manifests, and reports. This review re-measured bytes; it did not repeat prior wording.

Date: 2026-09-20 (Asia/Almaty). No ROM, NVRAM, register, candidate, or hardware mutation was performed.

## Current

One bounded offline review re-read the pinned clv donor ROM, walked the clv `CbsSetupDxe` IFR to recover option labels, and recomputed the changed-byte set of all 41 `candidates/*.bin` images against the pinned donor. Result: **NO-GO for any voltage change; unproven for 1800 MHz.**

## Method and pinned inputs

| Input                                                                                                       | SHA-256                                                            | Note                                           |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------- |
| `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`                                                       | `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` | 16,777,216 B, base for all re-measurement      |
| `evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin`                         | `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8` | exact IFR source                               |
| `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py`                        | hashed in result JSON                                              | existing parser, reused (no new parser)        |
| `evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/voltage-offset-boundary-result.json` | `4026f8cebb814fc11fddb58eb5f5fd4e1e41fc878dbba3d3745161ddb7667bd3` | hashed, machine-read for the consumer boundary |
| `candidates/*.bin` (41 images) + `.build.json`                                                              | per-image hashes in result JSON                                    | each diff recomputed independently             |

Command (reproducible):

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-ds-independent-safety-review/verify_safety_review.py
```

Observed: exit status `0`, `13/13` independent checks passed, stderr empty. Evidence class: `observed-bytes` + `static-analysis`.

## Findings

### F1 — The pinned clv donor already stores the 1800 MHz option (observed bytes)

`AmdSetup` body base `0x4CF`. Literal byte at `+0x316` / absolute `0x7E5` is `0x24` (36). The clv ROM's own IFR question at that offset is QID `527` (`0x20F`), prompt `Memory Clock Speed`, `ONE_OF`, with option `0x24` labelled `1800MHz` and `0x23` labelled `1750MHz`; `0xFF` is `Auto`.

So "1800 MHz" is the donor's own persisted request, not an exotic synthetic value. This also resolves the recorded conflict between `+0x316=0x24` (`memory/oc-recheck.md`, `specs/2026-09-20-clv-sync-development-plan.md`) and `+0x316=0xFF` (`memory/firmware-audit.md`): those describe different images. Only the pinned donor hash is in scope here.

Stored request ≠ applied clock. No artifact in this repository measures the resulting MCLK/UCLK/FCLK on hardware.

### F2 — The voltage fields are Auto/zero in the donor (observed bytes)

- `+0x6E5` (VDDCR_VDD Voltage Offset Control, QID `875`): `0x00` = `Auto`.
- `+0x6E6` u32 (VDDCR_VDD Voltage Offset, QID `876`, NUMERIC): `00 00 00 00`.
- `+0x6EA` / `+0x6EB` (VDDCR_GFX control/value, QID `877`/`878`): `0x00` / `00 00 00 00`.

DF clock is `+0x703=0x01` (Manual) with `+0x704=0x058C` (1420), matching the recorded baseline.

### F3 — Independent candidate delta audit (observed bytes)

All 41 images in `candidates/` were re-diffed against the pinned donor. 10 images are on the pinned-clv lineage and every one of their recorded `.build.json` `changed_offsets`/`voltage_changed` metadata fields matched the recomputation (`manifest_disagreements: []`). The remaining 31 are on other base lineages (C0A/8c/MeiMeiDXE mixes).

Deliberate nonzero voltage requests exist in 4 unflashed candidates, all setting the same request — VDDCR_VDD control `0x01` (Manual) with value `50 00 00 00` (decimal 80):

| Candidate                                                         | changed bytes | VDD control | VDD value     |
| ----------------------------------------------------------------- | ------------- | ----------- | ------------- |
| `candidates/BC250_5.00_clv_OC_vdd80_v001.bin`                     | 2             | `0x01`      | `50 00 00 00` |
| `candidates/BC250_5.00_clv_OC_vdd80_v002.bin`                     | 2             | `0x01`      | `50 00 00 00` |
| `candidates/BC250_5.00_clv_OC_sync1750_vdd80_v001.bin`            | 8             | `0x01`      | `50 00 00 00` |
| `candidates/BC250_5.00_clv_MeiMeiDXE_SteamLogo_Sync1to1_v001.bin` | 1,340,274     | `0x01`      | `50 00 00 00` |

GFX voltage is untouched (`Auto`/zero) in all four. Three further images (`BC250_M2_C0A_MEMG`, `BC250_M2full_C0A_APCB-native`, `BC250_M4_M2full_BL-native`) show `0xFF` / `FF FF FF FF` in those fields; that is an unconfigured `0xFF`-filled Setup region from the C0A-stock lineage, not a deliberate voltage request, and is classified as such in the result JSON.

The value `80` still has **no established unit, sign, or encoding**. It is not 1.15 V, not proven +80 mV, and not proven mV at all.

### F4 — The voltage request has no located consumer (static, hashed re-use)

The pinned consumer-boundary result is `PARTIAL_BLOCKED_AT_CONSUMER`: the serializer emits `$INV` record `0x1364` for `+0x6E6`, and the exact `AmdFabricAriPei` generic reader has two direct calls requesting only `0x10FF` and `0x1104` — no direct `0x1364` requester. My run re-verified that status, the two-token inventory, and `requested_0x1364 = false` from the hash-pinned JSON. `memory/oc-recheck.md` records a broader corpus sweep (seven emitter modules, nine modules touching the `+0x6E5`/`+0x6E6` pair, no compare/read/index of the record id). I did not rerun that sweep; treat it as a cross-reference, not my measurement.

Consequence: writing `80` into the Setup field is a request with no demonstrated path to the SMU/rail.

### F5 — The reported historical 1800 MHz result does not establish a ceiling-compliant recipe

`specs/2026-09-20-clv-sync-development-plan.md` records that the historical `DF 1800` report (`772341`–`772344`) is associated with a physical feedback modification and a chat-partner-reported SoC around `1.2 V`. This report is not a reproducible, ceiling-compliant recipe. It does not prove that every possible 1800 MHz configuration **requires** that modification or voltage.

## Safety claim matrix

| Claim                                                           | Required evidence                       | Status                                                                                                                                                         |
| --------------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1800 MHz is representable as a stored request in the pinned ROM | bytes + IFR label                       | **PASS** (F1)                                                                                                                                                  |
| 1800 MHz is actually applied / MCLK=UCLK=FCLK                   | independent hardware clock measurement  | **UNRUN**                                                                                                                                                      |
| 1800 MHz stored + boot/stability on this board                  | boot log, stability run                 | **INCONCLUSIVE** — clv-based boot evidence not recorded; `memory/project-state.md` records the chip as holding `W11 3c50bc9a`, board unreachable at last check |
| Thermal/power margin at 1800 MHz                                | rail/thermal measurement                | **UNRUN**                                                                                                                                                      |
| Historical `DF1800` recipe usable under the 1.15 V ceiling      | reproducible procedure                  | **NOT ESTABLISHED** — the reported result used manual feedback adjustment and ~1.2 V; no compliant recipe was shown                                            |
| 1.15 V target corresponds to a known absolute SoC control       | rail mapping + units + applied readback | **NOT ESTABLISHED** — `+0x6E6` (QID `876`) is only an unresolved offset request                                                                                |
| Unit/sign/encoding of that field is known                       | consumer or measurement                 | **FAIL** — unresolved; `80` has no established meaning                                                                                                         |
| Consumer of `$INV 0x1364` exists                                | traced consumer                         | **INCONCLUSIVE** (F4)                                                                                                                                          |
| 1.15 V is a board-specific safe rating                          | measurement or vendor rating            | **FAIL** — no such evidence in the repository                                                                                                                  |
| Rail voltage measured under load                                | measurement                             | **UNRUN**                                                                                                                                                      |
| No repository candidate requests a voltage change               | byte audit                              | **FAIL** — 4 unflashed candidates request `50` (F3)                                                                                                            |

## Verdict

1. **No voltage-changing candidate should be flashed on this evidence.** The reviewed CBS offset has unknown units and consumer; it cannot be called "1.15 V" or safe at any value. A later [fixed-voltage Setup trace](2026-09-20-clv-fixed-voltage-consumer.md) found a distinct static PEI path, but neither its dispatch nor physical rail/output is verified.
2. **1800 MHz is already the donor's stored option and cannot be reported as a working overclock.** No applied-clock, thermal, or stability evidence exists here; one historical chat-partner report associates DF 1800 with a physical feedback modification and ~1.2 V, without establishing necessity or a safe recipe.
3. **1.15 V must remain a ceiling, not a setpoint.** Nothing in this repository establishes it as a rating; it is an operator-imposed constraint.

## Decisive missing tests

1. Rail-voltage measurement under load on the target board, with a known-good baseline image and a verified recovery image — before any voltage value is interpreted.
2. Independent applied-clock measurement (hardware counter or equivalent), not BIOS/menu or OS display values.
3. A located, traced consumer for `$INV` record `0x1364` (or a demonstrated absence), before the offset field is treated as an applied request.

## Limits and unrun checks

- Offline static review only. No board was contacted; no flash, NVRAM, or register write occurred.
- The C0A/M2-lineage images were diffed against the clv donor only; their own base lineages were not reconstructed here.
- The corpus-wide `0x1363`/`0x1364` sweep in `memory/oc-recheck.md` was not rerun by me.
- `memory/project-state.md` chip-identity and reachability statements are recorded state, not my measurement.

## Artifacts

- Verifier: `evidence/firmware-audit/20260920-ds-independent-safety-review/verify_safety_review.py`
- Machine result: `evidence/firmware-audit/20260920-ds-independent-safety-review/safety-review-result.json`
- Literal stdout/stderr/exit: `run2.stdout`, `run2.stderr`, `run2.exit`
- Manifest: `evidence/firmware-audit/20260920-ds-independent-safety-review/SHA256SUMS.final`
- Action log: `docs/action-logs/2026-09-20-ds-independent-safety-review.md`
