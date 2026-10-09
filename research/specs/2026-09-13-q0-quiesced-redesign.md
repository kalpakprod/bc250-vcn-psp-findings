# Q0-2 quiesced rerun (attempt 3) — specification

Date: 2026-09-13. Status: PROPOSED, awaiting operator execution approval.

## 1. Title and scope

Re-run the Q0-2 SMU driver-table READ (Q0 `0x04`/`0x05` + `0x06`) with the
exact THP script from attempt 2, on a quiesced boot with amdgpu blacklisted
(`linux-cachyos-vcn-bc250-mode2`, limine line 275). One variable changes versus
attempt 2: driver present/absent. Goal is attribution of the attempt-2 wedge,
not a table recovery.

Explicitly NOT in scope for this run: Q0 `0x07`, `0x5C`, any DF/gasket/MMIO
write, runtime driver unbind, flash. A future `0x07`-post design is contingent
on a clean quiesced `0x06` and needs a separate approval.

## 2. Planning anchor

Attempt-2 evidence (2026-09-13 14:26+05:00, boot `2b77d998`, mode1 with live
driver): `0x04/0x05 OK`, `0x06 st=255 ret=0`, `changed_len=0`,
`alive_after=false` (still dead +90 s), amdgpu collateral (`SMU: No response
msg_reg: 6`, `Failed to export SMU metrics table!`, one gfx ring timeout).
Inference: the `0x04`/`0x05` stole the table-location pointer from the driver's
live metrics-export flow. Full record:
`docs/action-logs/2026-09-12-q0-table-track.md` (attempt 2).

Proven facts reused: mode2+blacklist boots to full userspace + SSH (v3 boot);
SMU PCI transport is amdgpu-independent (S2 stage5 ran unlocked msgs on a
blacklist boot); THP `madvise` + settle delivers a 512-page DMA run at t+0
(attempt 2); cold cycle clears an SMU firmware wedge (recovery-3).

## 3. Connected groups and observed existing logic

- S2-L5 gate byte `[0xcec8+0xf6] == 0xff` on driverless boots: with no driver
  post, the SMU holds no driver table, so quiesced `0x06` is expected to bail
  (likely 255 again) rather than transfer — the discriminating question is
  whether it bails CLEANLY (`alive_after=true`) or wedges again.
- Driver metrics-export flow (suspected collision partner in attempt 2) is
  absent when amdgpu never loads: no periodic table traffic exists to desync.
- Q0-1/B3 queries are proven-safe in both contexts and serve as the
  pre/post baseline.

## 4. Use cases

- UC1 (this run): fire quiesced `0x04`/`0x05` (checked) + `0x06` (unchecked).
  - E1: `0x06` returns any status, `alive_after=true` → attempt-2 wedge is
    attributed to the driver collision; `0x06` is safe quiesced.
    `changed_len>0` additionally yields fw-default table bytes (baseline for
    any future crafted `0x07`); `=0` means nothing posted (expected).
  - E2: `alive_after=false` again → `0x06` is inherently unsafe; CLOSE the Q0
    table track (both contexts exhausted, no third context exists).
  - E3: `0x04`/`0x05` rejected → staging is gated without a driver; report.
- UC2 (contingent, NOT approved): only after E1, a later design may propose
  our own `0x07` post + `0x06` readback + `0x5C` on the quiesced boot.

Honest boundary: a quiesced `0x06` CANNOT recover the driver-posted table —
none is posted on that boot. Its value is wedge attribution plus the
fw-default baseline.

## 5. Implementation checklist

- [ ] Operator (local console): select the mode2 limine entry (line 275,
  `modprobe.blacklist=amdgpu`, verbose), report "board up".
- [ ] Root: verify NEW boot_id; `lsmod | grep amdgpu` empty AND
  `/sys/module/amdgpu` absent (quiesce proof); `assess_S1.py`
  (`alive=True`); Q0-1 versions `0x02/0x03` baseline. Abort the run (report
  only) if amdgpu is loaded or SMU is not alive.
- [ ] Root: `sudo rm` stale root-owned `/tmp/q0_2_*`; re-verify script hash
  `4c61c702fb87f84bfcb7c06508444f2b97d97f8e4cf708169ed87e552d28927c`
  on board (re-transfer on mismatch).
- [ ] Root: launch the IDENTICAL THP script detached (`setsid`, same
  `--out/--log` paths); poll hold.log + result JSON via separate SSH reads.
- [ ] Root: record the outcome (E1/E2/E3) in the Q0 track log with hashes;
  holder disposition follows the existing rule (stays only if `loc_set`).
- [ ] Rollback (any outcome): holder + operator cold cycle; no flash touched;
  default boot entry (mode1) unchanged.

## 6. Open questions

- OQ1 (blocking for interpretation, not for the run): does quiesced `0x06`
  bail 255 (no table posted) or attempt DMA? Either answer is informative.
- OQ2 (non-blocking): exact fw-default table bytes — available only post-run
  if `changed_len>0`.
- OQ3 (blocking for any FUTURE `0x07`, out of this run): crafted-table format
  and sane field values.

## 7. Decision log

- 2026-09-13: operator chose quiesced redesign over closing Q0 or standing
  down (`Q0 future` structured choice).
- Script byte-identical to attempt 2 (one variable: driver present/absent) —
  the cleanest possible discriminator; no new code to review.
- No compaction sysctl, no hugetlbfs pool, no runtime driver unbind in this
  run (each would add a second variable or a new risk class).
