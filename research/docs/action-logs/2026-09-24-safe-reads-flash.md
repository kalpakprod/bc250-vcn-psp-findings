# Action log: flash safe-reads c935e3ec on BC250-01

Date: 2026-09-24 (UTC). Actor: root. Target: BC250-01, W25Q128.V.

## Intent (before any write)

Operator approval: "шей" on safe-reads after the no-solder decision.
Image: `candidates/BC250_vcn-driver-FULL_safe-reads-only_appended-at-end.bin`
(alias v008-secure), sha256
`c935e3ec4c0faee88fbe0600f003b4d0d16ac13f587ab8fb6943382e28025c6f`.
Question: does DXE complete when the driver reads only via the secure
mailbox. Stage gate from sidecar (flash if STUB boots and FULL-appended
hangs): both met (STUB-early 6500bea5 BOOTS, FULL-appended 9d249397 hangs
1-blink).

Preflight: `scripts/verify_candidate_preflight.py` GO 10/10 with manifest
params (base pre-v003c-read-a 64973ba3, new-off 0x43c018, new-size 0x3022,
window 0xae0088..0xc30a6b, efi-sha 2a20cc1e). First run NO-GO was a usage
error (default window + missing --efi-sha), not an image defect.

On-chip before: d991c817 = FULL-appended 9d249397 + 1309 bytes NVRAM drift.
Backup: `evidence/programmer/reads/20260924-safe-reads/pre-safe-read-a.bin`

- `-b.bin`, byte-identical (cmp). Rollback: STUB-early 6500bea5 (BOOTS) or
  the backup dumps. Programmer CH347 contact verified (chip ID reads).

Plan: `flashrom -w` the candidate, then control read-back and sha compare.
Cold boot + LED/LAN/picture verdict by operator after.

## Result (after)

- `flashrom -w`: Erase/write done 0..ffffff, Verifying flash... VERIFIED.
- Control read-back `post-safe-read.bin` sha256 `c935e3ec...25c6f`:
  byte-identical to the staged candidate. On-chip state confirmed.
- Next: operator cold boot. Watch: LED blink count, LAN link, picture.
  Report decides the branch: boots -> write bisection; hangs -> the
  secure-read path itself wedges, rethink route B.

## Verdict (cold boot 2026-09-24)

No init. safe-reads hangs like FULL-appended.

Source re-read (systematic debug): v008-secure was NEVER reads-only.
Its own header line 8: "same sequence, same writes, same polls" — only
the domain-bitmap reads moved to the secure path. The staged name and
sidecar ("safe-reads-only") lied. All loops are timeout-bounded, no
while/goto, errors propagate — the driver cannot hang in its own code.
Secure reads are live-proven by probe4l6/4l7. Remainder: a WRITE wedges
the box (likely SMN fabric stall on a later touch, unguardable in sw).

Next build: breadcrumb driver (NVRAM progress counter between ops, one
flash identifies the wedging write via programmer readback). Entry also
added to MISTAKES.md (lying experiment name).
