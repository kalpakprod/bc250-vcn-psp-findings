# t8 SMU message-table decode — V1 first pass (worker B, 2026-09-17)

Evidence class: `observed-bytes` + `static-analysis` (pypcode 4.0.0 Xtensa:LE:32 linear decode; no GUI disassembler, no project files modified).

## Inputs (hash-verified in-session)

- OLD body: `dump/2.bin` at SPI `0x8FF100`, 262,144 B, SHA-256 `5c805026581ace101ba43ef4d0f6b34354f4a61461a1c78d2fa6a335a53d9936` (matches `evidence/smu-ipc-d-r1/tool-version.txt`-pinned prior work).
- NEW body: `evidence/donor/retroweb-20260916/BC250_5.00.bin` at SPI `0x8FF000`, 262,144 B, SHA-256 `0b290dc5c41a28bf...` (full hash computed in-session; the `13c93c08` in the task brief refers to a different extraction alignment, see "Addressing" below).
- Tooling: `pypcode 4.0.0` (SLEIGH Xtensa) from `~/.cache/uv/archive-v0/15ZwZ34LpoZPWZ8M`; no r2/rizin on PATH, none installed.

## Addressing convention (critical, resolves prior contradictions)

- OLD (5c805026): stored code pointers == body file offsets (SRAM==file). Verified: 128/128 table handler words decode as `entry` at the stored value.
- NEW (0b290dc5): stored code pointers are SRAM addresses = body file offset **+ 0x100**. Verified empirically: testing load-delta L over the 169-entry table, L=256 gives 126/130 `entry` hits (next best 18); after correction all tables validate 100% (see below).
- Under this convention all V1/loop-run-1 anchors reconcile exactly:
  - selector `0x03220038`: old file `0xd38` (SRAM `0xd38`), new file `0xc38` (SRAM `0xd38`) — STABLE in SRAM terms.
  - `0x0900C230`: old SRAM `0x150c0`, new SRAM `0x150c0` — STABLE.
  - window base `0x10FFE00`: old SRAM `0x17148`, new SRAM `0x17160` (+24 = the 94280→94304 shift from loop-run-1).
- The two prior alignment claims (5c805026 @`0x8FF100` vs f546f118 @`0x8FF200`) are the same bytes shifted 0x100; reports mixing them produce phantom ±0x100 shifts. Loop-run-1's "selector @0xC38 identical in both" compares f546-old vs 0b29-new file offsets and is a file-offset coincidence, not an SRAM fact (G7 note).

## Message table structure

Format (both versions): arrays of 8-byte records `{u32 handler; u32 flags}`, indexed `entry = base + msg_id*8`. `flags` observed values: `0x6` (most), `0x201`, `0x206`, plus `{0,0}` for unimplemented. A base-pointer array ("directory") of u32 SRAM addresses is followed by a u16 per-subtable entry-count array.

OLD (file==SRAM):
- directory @`0x7a8c`: `[0x706c, 0x725c, 0x72e4, 0x7464, 0x7464, 0x79ac, 0x7a54, 0x7a74]`
- counts @`0x7aac` (u16): `[62, 17, 48, 169, 169, 21, 4, 3]` — sums consistent with directory boundaries.
- Handler-entry validation (all nonzero words decode as `entry` prologue): t0 36/36, t1 (old 0x725c) 16?→ scored 16/16 nonzero region — measured 36/36 (t0), 17/17 (t5 `0x79ac`), 128/128 (t3), 2/2 (t6).

NEW (SRAM = file+0x100; SRAM quoted below, file = SRAM-0x100):
- directory @file `0x7994` (SRAM `0x7a94`): `[0x706c, 0x725c, 0x72e4, 0x746c, 0x746c, 0x79b4, 0x7a5c, 0x7a7c]` (SRAM)
- counts @file `0x79b4` (SRAM `0x7ab4`): `[62, 17, 49, 169, 169, 21, 4, 3]` — only count change: subtable 2 grew 48→49 entries (0x180→0x188 bytes).
- Handler-entry validation at file offsets (SRAM-0x100): t0 36/36, t1 4/4, t2 44/44, t3 128/128, t5 17/17, t6 2/2, t7 0/0 (all-zero table).

The Q3 message table ("t3") is the 169-entry (IDs `0x00`–`0xA8`) subtable:
- OLD base SRAM `0x7464` (169 entries, `0x548` bytes).
- NEW base SRAM `0x746c` (169 entries), file `0x736c`.
- ID arithmetic `entry = 0x7464 + id*8` (old) is independently confirmed by six anchor mappings derived in prior repo work (`evidence/smu-ipc-d-r1/q3-selected-map.txt`): `0x0b→0x1ba44`, `0x19→0x28650`, `0x1d→0x2e6c8`, `0x21→0x249dc`, `0x5c→0x1f038`, `0x5d→0x1f110`, `0xb7/0xb8→0x1f038/0x1f110` (the latter live in subtable 5). All match the arithmetic exactly.

## Headline answers (NEW body)

- The message table sits at body file offset `0x736c` (SRAM `0x746c`), 169 slots, **128 implemented** (nonzero handler), 41 NULL slots.
- **msg 0x8 (PPSMC_MSG_PowerDownVcn) and msg 0x9 (PPSMC_MSG_PowerUpVcn): NULL in BOTH versions.** Raw bytes: old @`0x74a4`/`0x74ac` = 16×`00`; new @file `0x73ac`/`0x73b4` = 16×`00`. The community claim "PowerDownVcn=0x8/PowerUpVcn=0x9 unimplemented on BC250" is confirmed at byte level for both SMU 0.58.6.0 and P5.00. These are absent slots, not routed-to-stub.
- NULL in both also: IDs `0x00, 0x05, 0x06, 0x07, 0x12, 0x13, 0x16, 0x17, 0x1f, 0x5a, 0x61, 0x63, 0x69, 0x78, 0x79, 0x7c..0x7e, 0x81..0x84, 0x88..0x8a, 0x92..0x95, 0x97, 0x9d..0xa6` (same set both versions).

## Old vs new diff (t3 table)

- ID occupancy: IDENTICAL (same 128 implemented IDs).
- Per-ID flags: IDENTICAL (`0x6` block IDs 0x01–0x26, 0x30–0x70, 0x73–0x77, 0x7a–0x7b, 0x7f–0x80, 0x85–0x87, 0x8b–0x91, 0x96–0x9c; `0x201` block IDs 0x27–0x2f; `0x206` block IDs 0x71–0x72 and 0xa7–0xa8).
- Handler values: all recompiled and moved EXCEPT three pointers that are byte-identical in both versions: id 0x01 → `0x1b3a8`, id 0x02 → `0x1b3c0`, id 0x5b → `0x1b398` (shared helper-thunk functions at unchanged SRAM addresses).
- Selected mappings (SRAM, old → new):
  - 0x21 → `0x249dc` → `0x24c3c`
  - 0x5c → `0x1f038` → `0x1f218` (the domain-power/power-up-domain path; per memory, handler 0x5C is the domain-14 power path)
  - 0x5d → `0x1f110` → `0x1f2f0`
  - 0x98 → `0x280e0` → `0x28340`
  - 0x1a → `0x2a628` → `0x2a968`
- So P5.00 does NOT remap message IDs in t3; it is a recompile with function-address drift only (in this table).

## Response / poll / timeout structure (what is visible statically)

- Handler call convention: `entry a1, 0x20/0x30` → validate helper → work → respond helper. Old helpers: validate `0xffc`, respond `0xfa8` (called with `a11 = 0x1` on success, `0xff` on failure/reject — observed in old msg 0x21 handler `0x249dc`: `mov a10,a2; movi a11,0xff; call8 0xfa8`). New equivalents: validate SRAM `0xefc`, respond SRAM `0xea8` (new msg 0x5c handler at file `0x1f118`: `l8ui a8,a5,0xf6; movi a11,0xff; bne a8,a11,+; call8 0xea8` — returns `0xff` when a state byte is `0xff`).
- Poll/timeout: spin loops on status bits exist in the SMN-window helper family (old `0x233e8` direct-store primitive; `0x23b14` contains `bbci a10,0x8` / `bbsi a10,0x10` retry spins; the `0x10d0`/`0x1241` functions write mailbox window fields via `memw` + selector window `0x0320FE00` with poll-compare value `0xf`/`0xff` patterns). No wall-clock timeout constant was decoded in this pass.
- Not decoded: the instruction-level dispatcher that computes `entry = base + id*8` was not located as a specific function (the table base is consumed via runtime globals; no l32r literal in code equals the directory or table address — verified by exhaustive u32 scan). The arithmetic is verified by the six anchor mappings, not by reading the dispatcher itself.

## Open questions / limits

- Q1: dispatcher function location (which function reads the Q3 command word and indexes t3) — would make the ID map self-contained from code rather than anchors.
- Q2: semantics of flags `0x6` vs `0x201` vs `0x206` (blocks of consecutive IDs suggest classes, e.g. async/argument-carrying vs simple).
- Q3: the other six subtables (t0 62, t1 17, t2 49, t5 21, t6 4, t7 3 entries) — likely other channels/queues (Q2, PMFW phases); t7 is fully NULL in new.
- Hardware acceptance and runtime behavior: UNRUN (static only). Nothing was flashed or probed.

## Reproduction

```python
# bodies
old = open('dump/2.bin','rb').read()[0x8FF100:0x8FF100+0x40000]      # 5c805026..., SRAM==file
new = open('evidence/donor/retroweb-20260916/BC250_5.00.bin','rb').read()[0x8FF000:0x8FF000+0x40000]  # SRAM==file+0x100
# t3 table: old @file 0x7464; new @file 0x736c (SRAM 0x746c); entry = base + id*8, {u32 handler, u32 flags}
```

Validation method: pypcode `Xtensa:LE:32:default` single-instruction decode of each handler word (after the +0x100 new-body correction) — 100% `entry` prologues on all nonzero entries in both bodies (t3: 128/128 old, 128/128 new).
