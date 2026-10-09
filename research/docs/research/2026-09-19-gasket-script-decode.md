# Step 1 result: the SEC_GASKET script is fully decoded — and the lock is a closed DF window

## Status (2026-09-19T14:55+0500, Asia/Almaty)

Static decode complete. No hardware action. This file supersedes the model in
`2026-09-19-vcn-path-roadmap.md`; see "Correction" below.

## Correction (G7)

The roadmap said: the blocker is a 1379-step scripted table, our DXE table is a fragment,
stop poking single registers and replay the whole script.

That model was **wrong**, and the evidence that disproved it was already in the repository,
in the imported corpus. The decode had been done before:

- `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/source-docs/VCN-LOCK-MECHANISM.md`
  — full group structure, byte-exact Robin↔Cezanne cross-table (420 shared registers,
  158 differing, 758 Robin-only, 399 Cezanne-only), and the identified kill set.
- `.../docs/01-psp-policy-chain.md` — how the values reach hardware
  (`svc 0x7c(0x000003E810, value, 4)`), and that the consumer of these records is
  **not present in the SPI image**.
- `.../docs/source-docs/unclamp_decode.md`, `roadmap_A_results.md`, `VCN-EXPLOIT-SPEC.md`.

I found them only after finishing my own parse. My instruction to replay 1379 writes was
therefore based on a stale model, and the decode below is a **verification** of that
corpus, not new discovery. The corpus is imported evidence, so every claim used here was
re-checked against the ROM bytes; the checks are in this file.

## Verified structure (independent, byte-exact)

Carrier: PSP type `0x24`, SPI `0x982000`, body `0x2E50`.

```
body 0x2E50 = 0x10  header fragment
            + 0x08  $PS1 magic + sub_size (0x2C50)
            + 0x130 preamble
            + 1409 x 8  record table  (starts at body 0x148)
            + 0x100  RSA-2048 signature
```

Arithmetic closes with zero slack: `0x148 + 1409*8 + 0x100 = 0x2E50`.

- Corpus states the table base as `0x140`. Measured base is **`0x148`**: at `0x140` the
  arithmetic is off by `-8`, at `0x148` it is exact. One-record correction.
- Corpus states "1405 records". Measured: **1409** = 1405 data records + 4 group-header
  words. Equivalent accounting; the group boundaries agree exactly.

Layout: record = `{u32 addr, u32 value}`; a group is introduced by a header word
`{small_addr, count}` and followed by exactly `count` data records.

| group | header          | count | window                                |
| ----- | --------------- | ----- | ------------------------------------- |
| 0     | —               | 1230  | `0x201` SMN banks + DF windows + NBIO |
| 1     | `0x203 <- 0x1F` | 31    | `0x0322` varA                         |
| 2     | `0x210 <- 0x0D` | 13    | `0x3E810` + twelve `0x3E814`          |
| 3     | `0x280 <- 0x64` | 100   | recommit: DF windows + donor VCN bank |
| 4     | `0x281 <- 0x1F` | 31    | `0x0322` varB (TOS mirror)            |

## Cross-check of the corpus against the ROM (all PASS)

| address                                    | corpus claim                 | measured in `BC250_5.00_clv.bin`                         |
| ------------------------------------------ | ---------------------------- | -------------------------------------------------------- |
| `0x03E810`                                 | stock `0x0`, "the main kill" | `0x0` (single write)                                     |
| `0x03A2011C`                               | stock `0x87FF` (no bit 12)   | `0x87FF`, twice                                          |
| `0x03A20124`                               | stock explicit `0x0`         | `0x0`                                                    |
| `0x03A20120`                               | `0xFFFF0000`                 | `0xFFFF0000`, twice                                      |
| bank 12 `0x0900Cxxx`                       | **absent on Robin**          | **0 records in the whole `0x0900C000-0x0900CFFF` range** |
| `0x0900C234` / `0x0900CB80` / `0x0900C910` | absent                       | not present                                              |
| `0x0001C780` fabric block                  | absent                       | not present                                              |
| `0x090189A0` NBIO bridge                   | absent                       | not present                                              |
| `0x0001F8A4`                               | `0x0B`                       | `0x0B`                                                   |
| `0x0322011C`                               | `0x8000` then `0x80FF`       | `0x8000` then `0x80FF`                                   |

## The mechanism, now pinned

The lock is not a policy flag and not a sequence-ordering puzzle. It is **a closed Data
Fabric window**:

- `0x03A2011C` is a DF window mask. Stock `0x87FF` has **bit 12 clear**; the donor sets
  `0x107FF`, i.e. bit 12 set.
- Bit 12 is what makes **HWID 12 — the VCN bank `0x0900Cxxx` — visible at all.**
- The bank itself is **entirely absent** from the stock script (0 of 56 donor records).

This single fact explains every observation in the campaign, including the ones that
looked contradictory:

- Writes to `0x0900Cxxx` were **accepted** (memory: "59 donor gasket writes, `commit=1`")
  while reads of VCN registers returned `0xffffffff`. Writes post into a window that is
  not mapped; reads do not route. Consistent, not contradictory.
- `mmUVD_PGFSM_STATUS` reads `0x000FFFFF` in mode 2 — an all-ones read of a non-routed
  address, **not** an unpowered block. The block is not reachable, so it can never reach 0.
- Our DXE `mGasketBank12Writes` (56 entries) had no effect for the same reason.
- `secure=False` at Linux: the gate is closed before the kernel, and nothing at DXE
  re-opens the window in the right order.

## Ordering consequence (this is the actionable part)

If the window over bank 12 is closed, then **any bank-12 write issued before
`0x03A2011C` has bit 12 set is silently posted into an unmapped window.** Every attempt
so far that mixed these registers without ordering is therefore uninformative — including
ours. The required order is:

1. `0x03A2011C <- 0x000107FF` (bit 12 on — opens the DF window over VCN bank 12)
2. `0x03A20124 <- 0x00010FFF`
3. `0x03E810 <- 0x00000006` (VCN_SEG enable)
4. then, and only then, the bank-12 block `0x0900C234 .. 0x0900CB80`
5. `0x0322011C/124/12C` IOHC windows; `0x1C760..0x1C788`; `0x090189A0..E4`; `0x03D2` mirror
6. read back `mmUVD_PGFSM_STATUS` and re-read a VCN register to confirm routing, not power

## Why the carrier route is closed and the runtime route is not

The complete recipe is an edit to the type-`0x24` carrier, and that carrier is
RSA-2048-signed by `96ea7cfc` — a BC-250-family vendor key. Measured separately
(`docs/research/2026-09-19-zero-day-confirmation.md` §5.6): the chain root is external to
the image and identical across six ROMs including a different product. Signature forgery
is closed. The corpus reached the same wall and marked its own artifact
`..._UNSIGNED_DO_NOT_FLASH.bin`.

Therefore the recipe must be **applied at runtime**, and the only privilege level that can
write fabric registers pre-nest from inside the platform is the SMU, whose code execution
we already have (Q3 `0x32`, slot `0x7774`, thunk `0x3FF00`, returns status `0x1`, SMU
survives).

## Next experiment (step 2), falsifiable

Replay the ordered set above **from inside the SMU** via the Q3 `0x32` thunk at
ReadyToBoot, staged smallest-first: first only items 1–3 (three 32-bit SMN writes), and
observe `mmUVD_PGFSM_STATUS` in `bc250_vcn_mode=2`. Prediction: the read stops returning
all-ones. If it does, item 4 and onward.

Not yet proven: that the DF window can be re-opened after the vendor's script has run
(the translate table may latch), and that a rewrite of `0x03A2011C` from the SMU is
honoured at all. Both are decided by the three-write probe.
