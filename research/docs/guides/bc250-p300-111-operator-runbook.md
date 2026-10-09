# BC-250 operator runbook: staged native-menu overclock toward 1:1:1 (P3.00 board)

Status: OPERATOR PROCEDURE, clock-only, no voltage. Supersedes nothing;
it grounds `docs/research/2026-09-20-clv-native-menu-1to1-guide.md` (T0–T6)
on the live board state measured 2026-09-21 ~23:55+05:00.

## 1. Live starting point (measured, not assumed)

| Item | Live value | Source |
|---|---|---|
| Board / OS | `cachyos`, kernel `7.2.6-1.1-cachyos-bore-vcn-bc250`, `bc250_vcn_mode=1` | SSH readback |
| BIOS (DMI) | `P3.00`, `12/09/2021` | `/sys/class/dmi/id` |
| GPU | `1002:13fe` | lspci |
| `AmdSetup` live body | 2229 B, SHA-256 `6f266c3c…d055` | efivar dump |
| MCLK `+0x316` | `0xFF` Auto | live NVRAM |
| UclkDiv1M0 `+0x330` | `0xFF` Auto | live NVRAM |
| MemPstate `+0x36D` | `0xFF` Auto | live NVRAM |
| FCLK_DPM `+0x6A3` | `0x0F` Auto | live NVRAM |
| DF control `+0x703` | `0xFF` Auto | live NVRAM |
| DF value `+0x704` | `1000` | live NVRAM |
| VDD/GFX offsets | `0/0`, `0/0` | live NVRAM |
| Committed `mclk/sclk/fclk` | `450* / 2000* / 450*` MHz (software alias, deltas only) | amdgpu sysfs |

Evidence: `evidence/runtime/20260921-takeover-live-baseline/`
(`SHA256SUMS`). Log: `docs/action-logs/2026-09-21-takeover-live-baseline.md`.

WARNING: the chip runs P3.00, not CLV 5.00. The static CLV menu paths below
are search leads. If a control is absent on P3.00, record `UNREACHABLE` and
continue with the next test; do not force visibility.

## 2. What the BIOS actually offers (and what it does not prove)

Clock knobs (VarStore `AmdSetup`, all `RESET_REQUIRED` on CLV-static):

| Control | CLV-static path lead | Offsets | Live now |
|---|---|---|---|
| Memory Clock Speed | UMC Common → GDDR6 Common → DRAM Timing → I Accept | `+0x316`, QID `0x20F` | Auto |
| UclkDiv1M0 | AMD CBS → UMC Debug → GDDR6 Debug → GDDR6 DRAM Timing | `+0x330`, QID `0x229` | Auto |
| Memory P-state | … → GDDR6 DRAM Controller → DRAM Power Options | `+0x36D`, QID `0x25E` | Auto |
| FCLK_DPM | SMU Debug Options → SMU Features | `+0x6A3`, QID `0x7045` | Auto |
| DF Override control/value | SMU Debug Options → SMU Debug | `+0x703/+0x704`, QIDs `0x37D/0x37E` | Auto/1000 |

Voltage knobs: fixed VCORE/GFX/MEMIO fields exist in a separate `Setup`
store and offset fields exist in `AmdSetup`, BUT: no SoC rail mapping
exists, the `+0x6EA=80` community recipe is a proven inert placebo
(no consumer in any firmware component), IFR bounds are not safe limits.
Disposition: **no voltage change in this runbook.**

## 3. Procedure

### T0 — baseline lock (no changes)

1. Reboot into Setup. Photograph or transcribe all six clock controls above
   plus any voltage page (values only, change nothing).
2. Record for each control: visible? exact shown value? options offered?
3. Exit without saving. Boot to OS normally.
4. Report the six screen values to the assistant session; it will compare
   them against the saved live NVRAM (`6f266c3c…`) and confirm T0.

### Stage A — one variable at a time (clock only)

Run from the T0 baseline. For EACH test: set exactly one field, save, reset,
confirm Setup returns, boot OS, report. The assistant reads back NVRAM +
clocks remotely after every boot. Restore the baseline value before the
next test.

| Order | Test | Set to | Pass bar |
|---|---|---|---|
| T1 | Memory Clock | `1800MHz` (enum `0x24`) | persists + boots + NVRAM readback `0x24` |
| T2 | UclkDiv1M0 | `Enabled` (`0x01`) | persists + boots + readback `0x01` |
| T3 | FCLK_DPM | `Disabled` (`0x00`) | persists + boots + readback `0x00` |
| T4 | Memory P-state | `Disabled` (`0x00`) | diagnostic only; recovery ready |
| T5 | DF control | `Manual` (`0x01`), value untouched | persists + boots, `+0x704` still `1000` |
| T6 | DF value | one value in `[0,2000]` (suggest `1800`) — ONLY if T5 left control `Manual` as the new recorded baseline; else `NOT_RUN` | persists + boots + u16 readback |

Per-test evidence: screen photo, POST/display/boot outcome, remote NVRAM
readback hash, `pp_dpm_mclk/sclk/fclk` before/after, one `amdgpu_top`
snapshot. A persisting value + clean boot = `PASS — menu persistence`.
Without independent clock counters it is still `INCONCLUSIVE` on physics.

### Stage B — combined hypothesis (only if every Stage A test passed)

One profile, one boot, full rollback ready:

`MCLK 1800MHz + UclkDiv1M0 Enabled + FCLK_DPM Disabled + Memory P-state Auto
+ DF Manual 1800`, voltage untouched.

This mirrors the historical `1750`-shaped request at the pinned `1800`
label. It is a hypothesis, not a proven `1:1:1`. Same evidence as Stage A
plus three cold boots. Any failure → Stage A values, then T0.

## 4. Rollback and stop

- Normal rollback: restore the recorded T0 value of the changed field,
  save/reset, verify readback, cold boot, verify POST/OS.
- If a value will not restore: board CMOS/NVRAM reset procedure, then
  re-read all six fields before continuing.
- STOP immediately on: no POST/display/OS, training loop, GPU reset,
  thermal alarm, corrected/uncorrected errors, any voltage value changed
  unexpectedly, any value that fails to persist. Preserve the failure state
  and report before any further boot.
- No flash, no NVRAM direct edit, no register write is authorized by this
  runbook. A later firmware candidate needs its own recovery/approval gate.

## 5. What this runbook cannot give (honest boundary)

- Physical `MCLK=UCLK=FCLK` proof: needs independent domain counters, which
  this project has not recovered for CLV/P3.00. Committed `pp_dpm_*` numbers
  are before/after deltas, never sync proof.
- SoC `1.15 V`: no mapped field, no rail proof, no safe ceiling. Not in
  this runbook by design.
- Latency numbers: no benchmark harness is installed on the board. After a
  stable Stage B, the next step is a controlled A/B protocol (separate doc),
  not a percentage claim.
