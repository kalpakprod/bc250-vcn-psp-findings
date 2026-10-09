# Offline non-aliased clock evidence route for CLV

## Conclusion

A bounded register-header check identifies one real non-aliased measurement mechanism in the retained AMD register map: paired hardware counters for `GFXCLK` and `REFCLK` with independent run/reset/sample controls and valid bits.

Exact offsets from `gc_10_1_0_offset.h`:

- `mmRLC_CLK_COUNT_GFXCLK_LSB/MSB = 0x4C30/0x4C31`
- `mmRLC_CLK_COUNT_REFCLK_LSB/MSB = 0x4C32/0x4C33`
- `mmRLC_CLK_COUNT_CTRL = 0x4C34`
- `mmRLC_CLK_COUNT_STAT = 0x4C35`

Exact masks from `gc_10_1_0_sh_mask.h` provide separate GFXCLK and REFCLK run/reset/sample bits (`0x01/0x02/0x04` and `0x08/0x10/0x20`) plus independent validity bits (`STAT bit0` and `bit1`). A ratio of sampled GFXCLK count to sampled REFCLK count is therefore a non-aliased hardware-counter measurement route, unlike the retained software metric aliases.

## What this does not prove

The retained register headers identify **GFXCLK**, not exact CLV MCLK, UCLK, or FCLK. This bounded check found no exact UMC/DF/UCLK counter/status mapping. Therefore:

- Do not relabel RLC GFXCLK as FCLK.
- Do not infer MCLK/UCLK/FCLK identity from the counter pair.
- Synchronous crossing requires a separate UMC/DF mode/status or divider/crossing selector, plus independent counter ratios for each domain.
- Equal software metrics and SMU queries remain insufficient; existing evidence explicitly classifies them as aliases/software state.

## Minimal truthful measurement mechanism

For offline route design, the minimum non-aliased evidence package is:

1. Exact domain-specific counter pair `DCLK/REFCLK` for MCLK, UCLK, and FCLK, each with valid/sample controls.
2. One common reference window and simultaneous counter snapshots.
3. Independent ratio conversion/calibration for each counter pair.
4. A dedicated synchronous-crossing status/selector bit or divider mode readback; equal ratios alone do not prove crossing mode.
5. A mapping from each domain counter to exact board IP/clock source, not a driver alias.

Only item 1 is partially demonstrated offline here, for GFXCLK/REFCLK. Recovering exact UMC/DF register definitions from the exact firmware/driver path is the next offline gate; no MMIO write or live probe is proposed.

## Reproduction and evidence

```text
python3 evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock_counter_route_verify.py
```

Observed status: `23/23 PASS`.

- Machine result: `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-route-result.json`, SHA-256 `6eaa6a027118cc88a47d909bfcce39841eac29870561c8c05a82f3da3f43dda0`.
- Verifier: `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock_counter_route_verify.py`, SHA-256 `08bcf62bbbdb04d9c228de8d884a232bbaf941de8fc32cd6fafc1c1d0cdddb4c`.
- Offset header SHA-256: `a0ad8bffb3c07ec3824d306aff49c77bc40057f8760aec7a76ee58a60cc8e6a2`.
- Mask header SHA-256: `cba20414ecf02e91bafdcfbff7d4ba686326f0bdaf236d1a883364f08410c167`.

Evidence class: observed external-primary/register definitions + static analysis. No board, firmware, settings, or hardware operation occurred.

## Exact-CLV applicability gate

A second bounded check tested whether the external RLC counter prototype is actually bound into the pinned CLV PMFW image.

- Input ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- PSP type `0x08`: container offset `0x8FEE00`, container size `0x40200`; extracted body length `0x40100`, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`.
- Direct scalar scan of the exact body found no little-endian literals `0x4C30`, `0x4C31`, `0x4C32`, `0x4C33`, `0x4C34`, or `0x4C35`.
- The retained `smu_v11_0.c` source has no direct `RLC_CLK_COUNT_GFXCLK` use. The existing actuator report states that its software metrics do not sample hardware PLL counters.

Machine result: `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-applicability-result.json`, verifier `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock_counter_applicability_verify.py`, status `23/23 PASS`.

Decision: this is a precise static applicability gap, not an exact-board measurement route. The header-backed GFXCLK/REFCLK mechanism remains an external-primary/source prototype. No exact CLV MCLK/UCLK/FCLK counter/status mapping, computed indirect access, synchronous-crossing selector, live read, or hardware proof was established. Do not relabel GFXCLK as FCLK and do not infer physical clock identity or synchronization from software aliases.

Limits: the scan does not exclude computed/indirect register access; DWORD-index declarations are not converted to board MMIO addresses; no hardware or firmware/settings write occurred.
