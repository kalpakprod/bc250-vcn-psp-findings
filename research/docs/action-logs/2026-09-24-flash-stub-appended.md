# 2026-09-24 — FLASH STUB-appended on BC250-01

## FLASH INTENT (operator-approved, BEFORE any write)

- Operator approval: «Всё, я подключил программатор, прошивай» (2026-09-24)
  following the exact-image proposal: STUB-appended on BC250-01.
- Image: `firmware-flash-pkg/20260924-vcn-driver-STUB_no-hw-ops_appended-at-end/BC250_vcn-driver-STUB_no-hw-ops_appended-at-end.bin`
  SHA-256: `0133a34b3f6744b3517f7d01abfc2c2b78d0784cd6fcb8e09e3817a670e36ae3`
  (alias v007r-noop; package `SHA256SUMS` verified before write).
- What it is: booted pre-dump + STUB driver APPENDED at FV end (same surgery
  as FULL-appended, zero HW ops); preflight 10/10 GO.
- Why: discriminate H1 (append structure rejected → expect 1 blink, fix the
  builder) vs H19 (FULL code wedges only late → expect boot, go secure-reads).
- Target: BC250-01, Winbond W25Q128.V via CH347 (`flashrom ch347_spi`,
  1.875M), operator states programmer connected, board unpowered.
- Procedure: chip identity → DOUBLE read a/b (`pre-stub-appended-read-*`,
  cmp must match) → drift check vs FULL-app readback → package sha → write
  (erase+write+verify) → INDEPENDENT readback + cmp + sha → result here.
- Rollback (primary): fresh pre-write dump. Secondary: FULL-appended
  pre-reads (`evidence/programmer/reads/20260924-full-appended/`).
- STOP: any mismatch at any step.
- Post-flash: operator restores bench circuit → cold boot → signs → verdict.

## FLASH RESULT (AFTER)

- Chip identity: Winbond W25Q128.V, 16 MiB on ch347_spi @1.875M (first try).
- Double read: `pre-stub-appended-read-a/b.bin` CMP-MATCH, sha256
  `de435501a7af02b910f042916a4e3885fc18ef2bbbbc769760d405ee92bbcb45` —
  primary rollback. Drift vs FULL-app readback: 62 B in 0x1b4f–0x3ce2
  (NVRAM; the 1-blink boot attempt still wrote PEI-phase NVRAM).
- Package sha: OK. WRITE erase 0..0xFFFFFF + verify: VERIFIED, rc=0.
- INDEPENDENT readback sha256
  `0133a34b3f6744b3517f7d01abfc2c2b78d0784cd6fcb8e09e3817a670e36ae3`,
  cmp vs candidate = FLASH VERIFIED EXACT.
- Dumps: `evidence/programmer/reads/20260924-stub-appended/`.
- Chip now = STUB-appended. NEXT: bench circuit → cold boot → signs → H1/H19.

## COLD-BOOT VERDICT (2026-09-24, operator: booted to Linux)

- H19 WINS. Append structure is fine; FULL code wedges only against
  initialized SMU. Surgery/position questions are CLOSED permanently.
- Driver poll audit: all loops bounded (`REG_POLL_TIMEOUT_LOOPS` 125,
  mailbox 5 s cap, `EFI_TIMEOUT` returns) — the stuck-CPU mechanism is
  SMU-side, not a driver poll. Prime suspects: raw reads (probe3) then
  gasket writes (D12–D19 precedent).
- Registry: STUB-appended `FLASHED-OK`. NEXT: flash safe-reads (needs
  exact operator approval).
