# First UclkDiv1M0 test and exact measurement gap

Current: exact CLV native guide / UclkDiv1M0 software semantics unresolved / local capture host is not BC-250 / no physical clock claim.

## Finding

The first relevant manual comparison is `B0` versus `T2-UCLK`: change only `AmdSetup+0x330` (`UclkDiv1M0`, QID `0x229`) to the other exposed enum (`Auto=0xFF` or `Enabled=0x01`), leaving every other clock, P-state, timing, voltage, and power field unchanged. This tests saved-request persistence and any repeatable training/boot/workload correlation. **It cannot identify the divider ratio or prove UCLK=MCLK/FCLK with available channels.**

The initial static native evidence showed a byte-preserving serializer for `+0x330 -> $INV 0x1204`. The later [method-0x250 buffer-edge review](../../../references/DEPENDENCIES.md#unavailable-local-inputs) joins that output buffer to a generic reader, not a token-specific actuator. The menu help says “relative to FCLK,” but no ratio arithmetic, token-specific consumer, units, training connection, or crossing/status selector is established. Do not treat `Enabled` as a `/1` ratio.

## Existing channels: what they do and do not measure

| Channel                                                                                  | Verified source path                                                  | Evidentiary use                                                                                                                      |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `pp_dpm_mclk`                                                                            | `SMU_MCLK -> METRICS_CURR_UCLK -> Current.MemclkFrequency`            | Kernel-reported software metric; aliases FCLK, not an independent MCLK sample.                                                       |
| `pp_dpm_fclk`                                                                            | `SMU_FCLK -> METRICS_CURR_UCLK -> Current.MemclkFrequency`            | Same field as MCLK/UCLK; cannot discriminate physical FCLK.                                                                          |
| `gpu_metrics.current_uclk/current_fclk`, `average_uclk_frequency/average_fclk_frequency` | Retained driver copies `MemclkFrequency` into both fields             | Same metric alias; a raw blob hash detects bytes changed, not physical clock meaning.                                                |
| `pp_dpm_socclk`, `gpu_metrics.*socclk*`                                                  | Separate driver field `Current/Average.SocclkFrequency`               | Separate reported metric field, but not validated as an independent physical counter. Do not promote to measured PLL/rail frequency. |
| SMU Queue 0 `0x11`                                                                       | Handler returns an internal committed frequency float by domain index | Software state only; no PLL sampling.                                                                                                |
| SMU Queue 0 `0x13`                                                                       | Handler returns a P-state index delta/count                           | Not MHz or a clock measurement.                                                                                                      |
| RLC counter prototype                                                                    | GFXCLK/REFCLK only                                                    | Not bound to exact-CLV UMC/DF/UCLK; not a substitute for UCLK/MCLK/FCLK measurement.                                                 |

The read-only collector exposes `pp_dpm_mclk`, `pp_dpm_fclk`, `pp_dpm_socclk`, and raw `gpu_metrics`, but all are kernel-reported observations. The project has **no exact CLV UMC/DF/UCLK counter/status route** and no independent UCLK meter. Equal MCLK/FCLK/UCLK numbers are therefore inconclusive.

## Direct checks actually run

1. Existing verifier was run in place after checking its outputs: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency_unit_verify.py`. Exit `0`, JSON result `PASS`, `11/11` checks passed, stderr empty. Result SHA-256 was unchanged before/after: `6027fd54d8803fbd2a8b22f09c098ec5e9174ddbb143fd2b41f68a5575f7fb0c`. The script's final `SystemExit(0 if failed else 0)` always returns zero; I separately asserted the JSON status and `failed=0`, so the passing check count—not exit code alone—is the evidence.
2. Existing read-only collector was run locally with command-line, hostname, and uevent collection suppressed as in the runbook. Exit `0`; JSON parse exit `0`; result: `cards=[]`, `skipped_cards=[card1, device 0x1900, reason not the BC-250 APU (0x13fe)]`, `hardware_mutation=false`. Capture SHA-256: `18ab5ffa58d04766c3e42605591d5306a9a7b4e3033a7e5cda3f74cfae504a5b`. Collector SHA-256: `46712248ef3f690d82eb42d17592b7c5b4f0fdab20542eda8dcffef8ef70ed82`.

This confirms that this workstation is **not** the target board; no current-board values or live clock capture were produced.

## Minimal operator experiment and remaining input

Exact operator input needed before a live test: an operator-run, read-only capture on authorized BC-250 PCI ID `1002:13fe`, plus a transcription/readback of the **current** `AmdSetup+0x330` and coupled fields. The donor's `0x01` value is not a substitute for current board NVRAM.

1. `B0`: capture current board identity/current image provenance, Setup/NVRAM values for `+0x330` and other clock/P-state/DF fields; save two idle snapshots at least 10 seconds apart with `docs/runbooks/2026-09-20-oc-stock-capture.md`. Do not read command line/journal/serials. Preserve hashes.
2. `T2-UCLK`: toggle only `+0x330` between its currently recorded value and the other native enum. Keep `+0x316`, `+0x36D`, `+0x6A3`, `+0x703`, `+0x704`, timings, voltage, kernel, PMFW, driver, cooling, and workload constant. Save/reset, verify byte readback, perform three cold boots per state, and record POST/training/error outcome. Stop on a repeatable failure.
3. If a deterministic dependent-load latency benchmark is already installed and approved, record its version/hash; run five identical trials per cold boot over three cold boots per state, with the same buffer size, CPU affinity, warm-up, workload, cooling, and capture interval. Compare medians and spread. No benchmark is installed or run in this review; do not install one as part of this test.
4. Restore the exact B0 `+0x330` value, save/reset, and verify readback. On POST/restore failure, stop and use the board's prevalidated CMOS/recovery procedure; do not compensate with voltage or another clock change.

**Interpretation:** persistence/training/workload differences are at most a stored-setting correlation. A physical divider/synchronization claim additionally needs an independent UCLK/MCLK/FCLK source mapped to exact board hardware, a common reference, and a read-only divider/crossing status bit. Without that, report clock semantics `INCONCLUSIVE`, even if metrics match or latency moves.

## Can offline work continue?

Yes. The later [CBS PPI review](../../../references/DEPENDENCIES.md#unavailable-local-inputs) closes the static registration/LocatePpi edge, and the [buffer-edge review](../../../references/DEPENDENCIES.md#unavailable-local-inputs) closes the generic-reader handoff. The next offline question is an actual token-`0x1204` requester and downstream actuator; the separate measurement gap is an exact-CLV UMC/DF/UCLK counter or divider/crossing selector. Runtime PPI invocation and physical confirmation remain unrun. Absence of a direct token literal is not proof of no indirect consumer.

No ROM, BIOS, NVRAM, guest, hardware, AMIBCP, voltage, or firmware changes occurred. No frequency or safe voltage is recommended.
