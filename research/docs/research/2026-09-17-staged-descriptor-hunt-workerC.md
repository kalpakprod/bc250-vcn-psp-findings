# OQ-V3d (Worker C): Flash-side staging source for the PSP SRAM table at 0x69D38

Date: 2026-09-17. Read-only analysis of `dump/2.bin` (native 0.58.6.0) and
`evidence/donor/retroweb-20260916/BC250_5.00.bin` (donor P5.00). No project files
modified except this report.

## Headline verdict

**A flash-side table of PSP-SRAM pointers covering 0x69B8C–0x69E28 EXISTS inside the
type-0x28 PSP blob itself** — body offsets 0x18AAC–0x18D48 (file `0x99DBAC`–`0x99DE48`
in both images, byte-identical). It includes the fw_type-table words `0x69D38..0x69D90`
(12 × stride 8) at body `0x18B70`, and the run continues to `0x69DA0`/`0x69DA8` — the
fw_type-13 slot value. This **corrects** the premise "nothing in flash stores these
pointers as literals": the u32 `0x69D38` is stored in flash at file `0x99DC70`
(body `0x18B70`) in both images.

However, no code in the blob consumes these words through direct PC-relative literal
loads (see F3), so the region is a **data table**, not a code literal pool. Whether t28
copies it into SRAM 0x69xxx or consumes it in place is **unresolved** (see OQ-1).
No staging source exists in any *other* PSP entry.

## Method

- PSP directory re-parsed with corrected layout: header at `0x8E0000`
  (cookie `$PSP` = `0x50535024`, num=19 at +8), **entries are 16 bytes**
  (type u32, size u32, addr u32, pad u32), file offset = addr − `0xFF000000`.
  All 19 types of the parent's list (0x1,0x2,0x8,0x9,0x12,0x13,0x20,0x24,0x28,
  0x30,0x31,0x32,0x33,0x34,0x44,0x45,0x4F,0x50,0x51) are present.
- Whole-image scans of both 16 MiB images for: u32 values in `0x60000–0x70000`
  (all offsets), ascending runs with stride 8/0x10 (run ≥ 4), `u32 13` within 16
  bytes of `u32 58`, ascending u32 arrays 0..N (stride 4, len ≥ 8).
- Capstone 5.0.7 Thumb disassembly of the t28 blob body (body file start
  `0x985100`, presumed load base `0x00E00000`): full-coverage linear sweep
  (restart after data gaps), tracing `ldr rX,[pc,#imm]` into pool words, `adr`,
  `add rX,pc`, and `movw/movt` pairs building `0x6xxxx`.

## F1 — PSP entry inventory (task item 2), native / donor

| type | native off/size | native sha256 (body) | donor off/size | donor sha256 | u32 in 0x60000–0x70000 |
|---|---|---|---|---|---|
| 0x30 | 0x99F700/0x440 | 8591b9e8… | 0x99F700/0x520 | 0859507c… | none |
| 0x31 | 0x99FC00/0xBED0 | a1392564… | 0x99FD00/0xC020 | 95ae7826… | none |
| 0x32 | 0x9ABB00/0x3F70 | 7bec6003… | 0x9ABE00/0x40C0 | e8e90a60… | none |
| 0x33 | 0x9AFB00/0xA160 | a29f61ad… | 0x9AFF00/0xA2A0 | d2264338… | none |
| 0x34 | 0x9B9D00/0x9FE0 | 8ae6efff… | 0x9BA200/0xA1D0 | 3398a5d8… | native: `0x65268` @0x9C3B44 only |
| 0x44 | 0x9C3D00/0x6610 | 4d8b8d27… (identical in donor) | 0x9C4400/0x6610 | 4d8b8d27… | `0x60306`, `0x60802` (twice each; PCI-ish 0x060300-class values, not SRAM table) |
| 0x45 | 0x9CA400/0x6E0 | 272514c0… (identical in donor) | 0x9CAB00/0x6E0 | 272514c0… | none |
| 0x4F | 0x9CAB00/0x10200 | 4435c945… (identical in donor) | 0x9CB200/0x10200 | 4435c945… | single `0x60606` @0x9CBB00 (value pattern 0x0606xx, not a pointer run) |
| 0x50 | 0x9DAD00/0xDD0 | 78c3fe9b… | 0x9DB400/0xDD0 | 78c3fe9b… | none ($PS1 container, first64 begins `0024 5053 31d0…`) |
| 0x51 | 0x9DBB00/0x740 | 1ca4d22f… (identical in donor) | 0x9DC200/0x740 | 1ca4d22f… | none ($PS1 container) |

First/last 64 bytes of every entry were dumped during analysis (reproducible with the
scan script in /tmp; command not preserved here — hashes above anchor the content).
None of 0x30–0x51 contains anything address-like in `0x69D00–0x69E00`. The only
PSP-side structure touching `0x69xxx` heavily is the type-0x28 blob itself.

Side observations (other entries, not table-related): type 0x08 contains scattered
`0x6C000/0x6C800/0x6D000/0x6C0F4…` u32s (27 hits, both images) — a different SRAM
region, not 0x69D38; type 0x24 contains `0x6885C/0x6895B/0x681C8/0x682C7/0x69A80/0x69A83`.

## F2 — The staged-pointer table (task item 3): observed bytes

Both images, file offsets `0x99DBAC`–`0x99DE48` (region byte-identical native↔donor;
verified by u32 compare), i.e. t28 body `0x18AAC`–`0x18D48`:

```
099dba0                             00069cac 00069cb4 00069cbc 00069cc4
099dbc0 00069ccc 00069cd4 00069cdc 00069ce4 00069cec 00069cf4 00069cfc
099dbd0 00069cfc…00069d0c 00069d14 00069d1c 00069d24 00069cb0 00069cb8
099dc20 …00069d28 00069d2c 00069d34 00069d3c 00069d44 00069d4c 00069d54
099dc60 00069d94 00069d9c 00069da4 00069d30 00069d38 00069d40 00069d48
099dc80 00069d50 00069d58 00069d60 00069d68 00069d70 00069d78 00069d80
099dca0 00069d88 00069d90 00069d98 00069da0 00069da8 00069dac 00069db4
099dcc0 …00069de4 00069dec 00069df4 00069dfc 00069e04 00069e0c 00069e14
099dd20 …00069e28 00069bd4 00069bd8 00069bdc …00069c18 00069b8c 00069b90
099dd80 00069b94 …00069bb4
```

Structure (observed): four interleaved ascending sequences of SRAM addresses:
- `0x69CAC + 8i` paired with `0x69CB0 + 8i` (two 16-word runs),
- `0x69D2C + 8i` paired with `0x69D30 + 8i` — the second run starting at
  file `0x99DC6C`/`0x99DC70` contains `0x69D38, 0x69D40, …, 0x69D90`
  (12 words, stride 8) and continues `0x69D98, 0x69DA0, 0x69DA8` —
  exactly the parent's fw_type table @`0x69D38 + i*8` with slot 13 → `0x69DA0`;
- `0x69BD4 + 4i` and `0x69B8C + 4i` (stride-4 runs of ~18 words).

Interpretation (inference, single-source): this is a flash-resident descriptor table
whose records point into the PSP-SRAM workspace `0x69B8C–0x69E28`; it is the most
plausible flash-side input to whatever builds/fills the SRAM table at 0x69D38.

## F3 — Code consumers (static-analysis, linear sweep of t28 body)

- Of all ~190 pool words in `0x60000–0x70000`, only two are consumed by
  `ldr rX,[pc,#imm]`:
  - `0x6A1B0` loaded at VA `0xE11B5C`, used as the address argument to
    `svc #0x7B` (r2=4, twice at +0/+4): a PSP service access into 0x6xxxx SRAM
    (observed disassembly quoted in the analysis session).
  - `0x69BC8` at VA `0xE188D4` — this "consumer" sits in a region my sweep
    disassembled out of alignment; treat as **unconfirmed**.
- **No** `ldr`-literal consumer for `0x69D38`, `0x69D30`, `0x69CAC`, `0x69B8C`,
  `0x69E28`, `0x69BD4`, or `0x69DA0` was found anywhere in the sweep → the
  F2 region is data referenced by computed indexing or copied, not a code literal pool.
- ~75 scattered u32 literals throughout the blob (VA `0xE01A40`–`0xE16B84`) hold
  values in `0xE18A00–0xE18B90` (e.g. `0xE18AF8` ×15, `0xE18B70` ×6) — pointers into
  the blob's own tail workspace. The blob therefore addresses 0xE18Axx directly while
  never directly loading the 0x69xxx table words. (`0xE18B70` as a *value* appears at
  literal `0xE08EC4`, `0xE0CC04`, `0xE0E698`, `0xE0E818`, `0xE12028`.)
- No `movw/movt` pair constructing any `0x6xxxx` value was found.
- No `adr`/`add rX,pc` targets inside `0xE18A00–0xE18F00` except `adr r1,#0x160`
  at `0xE18928` → `0xE18A88`.

## F4 — Negative searches (both images)

- `u32 13` within 16 bytes of `u32 58`: **0 hits** in either image.
- Ascending u32 arrays `0..N` (stride 4, len ≥ 8): only two candidates —
  native `0x912FE0` (len 8, inside PSP type-0x08 blob) / donor `0x912DF8` (same
  entry), and `0xE32D10` (len 16, UEFI region, identical in both images).
  Inference: likely small inline tables/coincidences, not fw_type descriptors
  (no 13/58 markers nearby); unverified further.

## Verdict

1. **The premise "the 0x69D38 table is not stored anywhere in flash" is FALSE.**
   The pointer sequence `0x69D38..0x69DA8` is stored as data inside the type-0x28
   blob at body `0x18AAC–0x18D48`, byte-identical in native and donor.
2. No staging source exists outside the t28 blob: PSP entries 0x30–0x34, 0x44,
   0x45, 0x4F, 0x50, 0x51 contain nothing address-like in the target range
   (F1), and no UEFI/ABL-side candidate surfaced (F4).
3. **Remaining open question (OQ-1, decisive test needed):** does t28 code copy the
   body-`0x18AAC` region into PSP SRAM `0x69Bxx–0x69Exx` at init, or is the SRAM
   table at `0x69D38` built record-by-record from these descriptors via computed
   indexing (e.g. through `svc #0x7B`-style service calls as seen at `0xE11B5C`)?
   Decisive check: full function-level (not linear-sweep) disassembly of the code
   around the fw_type dispatch (`0xE6A8`) and the fw_type-13 handler (`0xE7BC`)
   tracing how the `0xE18B70` pointer reaches `0x69D38`, or a QEMU/Unicorn run of
   the blob body watching stores into `0x69D38–0x69E00`.

## Evidence class / provenance

- F1, F2, F4: `observed-bytes` (scripts: /tmp/psp_scan2.py and inline capstone
  scans; inputs hashed: native `dump/2.bin` sha 83c4e420…, donor `BC250_5.00.bin`
  sha 0d6f136c…, per parent context).
- F3: `static-analysis` (Capstone 5.0.7 Thumb linear sweep; sweep restarts after
  data gaps, so individual "uses" away from the two quoted are reliable-negative
  only at the `ldr`-literal level, not for computed addressing).
- OQ-1 resolution and any hardware implication: **unrun**.
