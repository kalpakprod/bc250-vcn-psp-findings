# AMIBCP/OC donor-value review

Current: immutable CLV donor / verified stored OC values / live board settings unknown / no voltage or performance claim.

## Conclusion

The existing native-menu guide's donor values are correct for the pinned 5.00 CLV image. A fresh bounded NVAR parse, a copied exact IFR verifier, and independent direct-byte reads agree. These are **donor-stored `AmdSetup` requests**, not the current BC-250 board's NVRAM or applied clocks.

No performance loss, latency gain, applied clock, or safe voltage setpoint can be attributed from this donor. The user-provided `1.15 V` ceiling is an operator limit, not a validated electrical rating. The `VDDCR_VDD` field is a separate unresolved `u32` offset/command field; its rail identity, sign, units, consumer, and conversion remain unproven. Keep voltage controls at `Auto`/zero for any diagnostic baseline; do not enter `1.15`, `0x50`, `0x64`, or another guessed value.

## Exact source and recheck

- Input: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Size: `16,777,216` bytes
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `AmdSetup` body base used for direct reads: `0x4CF`
- Existing menu guide: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-native-menu-1to1-guide.md`
- Existing native map: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-menu-map-amibcp-uefitool.md`
- Existing exact verifier reused: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-df-init-route/menu-verify.py`
- Existing bounded parser reused: `scripts/nvar_audit.py`

### Literal recheck commands and results

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/nvar_audit.py \
  evidence/donor/retroweb-20260916/BC250_5.00_clv.bin \
  --store-offset 0 --store-length 0x10000 --variable AmdSetup \
  --output /tmp/bc250-amibcp-review-fL1YkV/amdsetup.json
```

Observed: exit `0`; stdout `{"records": 53, "selected": 1, "errors": 0}`; stderr empty. Raw variable bodies were not emitted.

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/bc250-amibcp-review-fL1YkV/menu-verify.py
```

The verifier was copied from the existing project script before execution. Observed: exit `0`; stdout status `PASS`; stderr empty. Its output hash was `6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a`; the pinned input assertion passed.

Independent direct-byte reads from the same immutable input reproduced every value below. Temporary NVAR report SHA-256: `4038ec8b6c6f1f3a41e3cb70c50b0ba529e6d54c093521e5659a684fba751d42`.

## Verified donor table

| Control                   |   `AmdSetup` offset | Absolute donor byte(s) | Raw/value        | Static menu meaning                                        | Default/options                                                         | Current board |
| ------------------------- | ------------------: | ---------------------: | ---------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------- | ------------- |
| Memory Clock Speed        |            `+0x316` |                `0x7E5` | `24` / `36`      | IFR label `1800MHz`                                        | `Auto=FF`; labels `125..2000MHz` with exact enum codes                  | **Unknown**   |
| UclkDiv1M0                |            `+0x330` |                `0x7FF` | `01` / `1`       | `Enabled`                                                  | `Auto=FF`; `Enabled=01`                                                 | **Unknown**   |
| Memory P-state            |            `+0x36D` |                `0x83C` | `FF` / `255`     | `Auto`                                                     | `Auto=FF`; `Enabled=01`; `Disabled=00`                                  | **Unknown**   |
| FCLK_DPM                  |            `+0x6A3` |                `0xB72` | `0F` / `15`      | `Auto`                                                     | `Auto=0F`; `Disabled=00`; `Enabled=01`; callback flag set               | **Unknown**   |
| DF Clock Override Control |            `+0x703` |                `0xBD2` | `01` / `1`       | `Manual`                                                   | `Auto=FF`; `Manual=01`                                                  | **Unknown**   |
| DF Clock Override (Value) | `+0x704` (`u16 LE`) |         `0xBD3..0xBD4` | `8C05` / `1420`  | Numeric request                                            | Bounds `[0,2000]`; no direct IFR default opcode                         | **Unknown**   |
| VDDCR_VDD Offset Control  |            `+0x6E5` |                `0xBB4` | `00` / `0`       | `Auto`                                                     | `Auto=0`; `Manual=1`                                                    | **Unknown**   |
| VDDCR_VDD Offset          |    `+0x6E6` (`u32`) |         `0xBB5..0xBB8` | `00000000` / `0` | Numeric offset field; help text says signed integer `[mV]` | IFR numeric bounds `0..0xFFFFFFFF`; no proven unit/sign/rail conversion | **Unknown**   |
| VDDCR_GFX Offset Control  |            `+0x6EA` |                `0xBB9` | `00` / `0`       | `Auto`                                                     | `Auto=0`; `Manual=1`                                                    | **Unknown**   |
| VDDCR_GFX Offset          |    `+0x6EB` (`u32`) |         `0xBBA..0xBBD` | `00000000` / `0` | Numeric offset field                                       | Same unresolved encoding class; no safe value inferred                  | **Unknown**   |

The native package-local form for the voltage pair is `0x7009 SMU Debug Options -> 0x703F SMU Debug`, with QIDs `0x36B` and `0x36C`. Presence in HII is static; live browser reachability and save/reset were not run.

## What is measured versus unknown

**Measured/static:** donor size/hash; exact `AmdSetup` bytes; IFR labels, QIDs, options, flags, bounds, and form paths; serializer copies to `$INV` records. `FCLK_DPM=0` means Disabled and `0x0F` means Auto. `UclkDiv1M0=Enabled` is an enum byte, not a decoded ratio.

**Not measured:** current board NVRAM, current board BIOS image, applied MCLK/UCLK/FCLK, memory-training outcome, physical rail voltage, voltage encoding, voltage consumer, power/thermal margin, latency, FPS, stability, or performance impact.

The retained driver source aliases exported FCLK/MCLK/UCLK values through one `MemclkFrequency` metric; equal exported numbers therefore cannot prove synchronization. The retained voltage serializer copies `+0x6E6` unchanged into an `$INV` record and does not decode it into a rail value. Existing voltage reports explicitly classify `1.15 V` as unvalidated and make no setpoint recommendation.

## Feasible baseline and per-field measurement procedure

This procedure is a future operator-run A/B experiment, not a result of this review:

1. Confirm the authorized board identity and current BIOS/PCI identity. A donor filename or BIOS version alone does not establish the current image. Keep the programmer disconnected during runtime capture; do not flash.
2. Capture the current native Setup values for every field in the table, including the voltage controls. Save an exact current NVRAM/AmdSetup readback if the authorized capture route supports it. The donor table must not substitute for this capture.
3. Establish `B0` with no setting change. Reuse `docs/runbooks/2026-09-20-oc-stock-capture.md`: two idle captures at least 10 seconds apart, exact collector hash, target PCI ID, temperatures/throttle state, and preserved JSON. The runbook's existing collector is read-only and source-redacts command line/hostname/uevent data. A valid host fixture or non-target GPU is not a board baseline.
4. Change one logical field only from `B0`, save/reset, and verify the exact saved value after reset. Do not change voltage in the clock/memory tests. Restore `B0` before the next field.
5. For each field, repeat at least three cold boots and the same fixed workload/capture window. Record POST, training/boot errors, target metrics, temperature, throttling, and recovery events. Use the same kernel, PMFW, driver, workload, ambient/cooling, and run order for A/B pairs.
6. Report each result separately: setting persisted; boot/training passed or failed; clock telemetry observed; independent physical clock measurement unrun; performance/latency delta with sample count and variance. A saved setting or equal software metrics is not a physical-clock result.
7. If a latency claim is required, use one approved deterministic memory-latency benchmark on the board and record its version/invocation. No such benchmark is installed or executed in this review; do not substitute FPS or a duplicated driver metric for memory latency.

Minimum per-field A/B record:

```text
board identity / current-image evidence
B0 NVRAM bytes + capture hashes
one changed QID/offset/value
reset/cold-boot count and training outcome
idle/load clock observations and source provenance
temperature/throttle/error logs
latency/performance benchmark, samples, mean/median/spread
rollback value and post-rollback readback hash
```

A performance result is **confirmatory only** if the field persisted, training/boot remained healthy, the same workload was measured against B0, and the delta is repeatable. It is **inconclusive** if only menu bytes or aliased metrics changed. It is **invalid** if board identity, image, workload, cooling, driver/PMFW, or rollback state changed between A/B.

## Voltage safety decision

- No safe BIOS voltage setpoint is established.
- User `1.15 V` is retained only as an operator ceiling/constraint; it is not a measured board rating and must not be converted into `0x6E6`.
- `VDDCR_VDD` is an unresolved offset/command field, not proven absolute SoC voltage. Historical `+35/+80/+100 mV` comments conflict with the exact `u32` layout and do not establish units or sign.
- For any diagnostic baseline, leave `VDDCR_VDD` and `VDDCR_GFX` controls at `Auto` with zero stored offset. This is a baseline-preservation rule, not a claim that zero is a safe operating limit.
- A voltage experiment remains **NO-GO** until a consumer/rail/unit mapping and board-specific electrical/thermal evidence exist, followed by explicit recovery and approval gates.

## Rollback

This review performed no ROM, BIOS setting, NVRAM, or board write. The report rollback is deletion of this report and its action log only. For any future operator A/B test, restore the recorded B0 field values, save/reset, verify current NVRAM/AmdSetup readback, and stop if rollback readback or POST fails.

## Status

- **PASS:** exact donor identity, direct NVAR parse, copied IFR verifier, independent byte readback, and static option/default/value table.
- **PASS (static only):** exact voltage field width/control pairing and `$INV` serializer handoff.
- **INCONCLUSIVE:** applied clock behavior, current board state, voltage encoding/rail identity, and memory-training relationship.
- **UNRUN:** live board capture, NVRAM readback from current board, physical voltage measurement, latency/performance A/B, and hardware acceptance.
- **NO-GO:** setting a voltage from `1.15 V`, historical mV comments, or raw offset guesses.

No ROM, BIOS setting, NVRAM, hardware, or candidate artifact changed.
