# Type-0x44 $PSP entry: consumer hunt and signed-body/tail decode (static, CLV donor)

Date: 2026-09-23. Read-only session. Input image: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
(sha256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, unmodified).
Builds on `docs/research/2026-09-23-verifier-destination-hunt.md` (same-day report; its Q3 finding about the
0x6400-byte unsigned tail is corrected/expanded below — the tail is NOT padding, it is two code blobs).

Scratch artifacts: `scratch/t44-hunt/` (extracted containers, signed bodies, ABL decompressions).

## Entry under study

$PSP directory at SPI `0x8E0000`, index 14 (dumped fresh from the image):

```
idx=14 type=0x34 size=0x0A1D0 locraw=0xFF9BA200
idx=15 type=0x44 size=0x06610 locraw=0xFF9C4400   <-- target
idx=16 type=0x45 size=0x006E0 locraw=0xFF9CAB00
```

Container `0x44` @ SPI `0x9C4400`, size `0x6610`, `$PS1` magic at +0x10, `signed_len = 0x10` (u32 at +0x14).
Layout per `scripts/psp_ps1_verify.py`: header `0x100` || signed body `0x10` || signature `0x100` || tail `0x6400`.
Signed body (4-byte hex, read at `0x9C4500`):

```
1d 10 00 00 10 02 00 00   1e 10 00 00 10 34 00 00
```

i.e. two u32 records: `0x101D:0x210` and `0x101E:0x3410`.

## Q2 first: what the signed pairs mean — they are (workload id, code offset) into the tail

The "0x10-byte signed body" is a two-record pointer table. Proof, byte-level:

- `container_start + 0x10 (offset 0x210 from body base 0x9C4500) = SPI 0x9C4710`
- `container_start + 0x3410 = SPI 0x9C7910`

Both addresses are the exact start of an instruction stream, and each is exactly `0xF0` bytes past a
sub-`$PS1` header sitting in the UNSIGNED tail:

```
SPI 0x9C4620 (tail+0x10), blob 1 header:
  24 50 53 31   "$PS1"
  +0x04: 00 30 00 00            (0x3000)
  +0x40: 01
  +0x48: 9a ce 85 d9 b8 08 42 70 af 98 d5 48 3e 11 d8 00   (16-byte id/GUID, identical in blob 2)
  +0x60: 00 30 00 00            (0x3000 again)
  +0x68: 1d 10 01 01            u32 0x0101101D  <-- workload id, high half 0x0101 + low 0x101D
  +0x70: 13 83 29 03            0x03298313
  +0x7C: 00 32 00 00            0x3200
SPI 0x9C4710 = 0x9C4620+0xF0 (code start, matches signed offset 0x210 from body base):
  0e 08 ff ff 0f 08 ff ff 4e 1b 0b 08 09 00 f4 a0 03 80 4f 03 01 00 0e 08 ...

SPI 0x9C7820 (tail+0x3210), blob 2 header: byte-identical except
  +0x68: 1e 10 01 01            u32 0x0101101E
  +0x70: 37 58 19 03            0x03195837
SPI 0x9C7910 = 0x9C7820+0xF0 (code start, matches signed offset 0x3410 from body base).
```

Blob stride: `0x9C7820 - 0x9C4620 = 0x3200` (matches the `0x3200` size field at each sub-header +0x7C;
blob 2 runs to `0x9CAA20`, container end `0x9C4400+0x6610 = 0x9CAA10`).

So the container is: a SIGNED (0x10-byte) table mapping workload id -> code offset, and an UNSIGNED tail
holding two ~0x3200-byte code blobs, each with its own unsigned sub-header carrying the full id
`0x0101_101D` / `0x0101_101E`. The code is not ARM Thumb and not zlib (`0x78DA` magic: 0 hits in the tail);
the 4-byte groups (`0e 08 ff ff`, `03 80 4f 03`, `d1 54 d3 30` ...) are the same SMU-style instruction
encoding seen in the SMU task/workload tables inside the type-0x08 image (e.g. task table at SPI
`0x90BE00`, records `{flags, task_id 0x301E/0x101E/0x501E..., 6 float params}`). The ids `0x101D/0x101E`
themselves appear in-image only as SMU workload/task ids (e.g. word `0x101E` at SPI `0x90BE5C`, inside the
type-0x08 SMU image). Interpretation: type 0x44 carries SMU workload/patch code for tasks 0x101D and
0x101E; the signed part authenticates only the id/offset table, not the code.

## Q1: who parses the 0x44 entry — UNRESOLVED, consumer is not identifiable in the flash image

Everything searched, with the exact negative evidence:

1. **t02 body** (`evidence/firmware-audit/20260923-verifier-first/clv-t02-signed-body.bin`, 0x13150):
   - literal words `0x8E0000`, `0xFF8E0000`, `0x9C4400`, `0xFF9C4400`, `0x101D`, `0x101E`, `0x3410`, `0x210`: **0 hits**
   - Thumb `cmp rN,#0x44` (halfwords `0x2844/0x2944/0x2A44/0x2B44/0x2C44/0x2D44/0x2E44/0x2F44`):
     3 hits (`0xf93c`, `0xfc6b`, `0x19b8`); all three disassembled with
     `llvm-mc --disassemble --hex --triple=thumbv7` — contexts are the t28-container check
     (`movw r8,#0x5244 'DR'` at `0xf93c` region), a `cmp r6,#0x64` (misaligned false positive), and a
     write loop (`strb r2,[r4,#0x8]`). None is a directory walk.
   - `movw #0x101D / #0x101E` encodings (`0xF640/0xF641` + imm8 `0x1D/0x1E`): **0 hits in the whole image**.
2. **t28 body** (SPI `0x984F00+0x100`, len `0x1A570`, extracted to `scratch/t44-hunt/t28-signed-body.bin`):
   same word scan: **0 hits** for `0x101D/0x101E/0x210/0x3410/0x8E0000/0x9C4400`. The `$PSP` string at SPI
   `0x99C380` (body+0x17380) is NOT a directory: bytes after the magic are Thumb code
   (`08 03 00 80 2d e9 f7 4f ...`), parsing it as a directory yields garbage (verified, not shown).
3. **ABL bodies (types 0x30-0x34)**: bodies are zlib (`78 da`); decompressed to
   `scratch/t44-hunt/t3x-decomp.bin` (`0x1F10/0x171A0/0x7680/0x14CD0/0x167C0`). Scans: no `$PSP`/`$PS1`
   directory magic, no `0x8E0000` base, no `0x101D/0x101E`, no directory-walk `cmp #0x44` (hits like t31
   `0x2D44@0x143AF` are data bytes `2d 44` inside config records; t31 table at `0x15950` is a
   `{u32, u16, u8 id}` config array, not entry types).
4. **Whole 16 MB image**: word `0x101D` only at SPI `0x9C4500` (the signed body itself) and 7 unaligned
   hits spaced `0x1F284` apart in the high-entropy data region `0xE22xxx-0xEBDxxx` (same region flagged as
   non-code in the verifier-hunt report). Word `0xFF9C4400` and `0x6610` only inside the directory entry
   itself. Word `0x0101101D/0x0101101E` only inside the two blob sub-headers.

Conclusion for Q1: no flash-resident code contains the entry type, the ids, the offsets, or the directory
base. The parser is consistent with the on-die PSP ROM (which by construction walks `$PSP` and hands
`$PS1` containers to the TOS loader, cf. `120EC` in the t02 body), i.e. outside the image. The SMU is a
plausible downstream consumer of the blobs (id space matches SMU workload ids), but no SMU-side directory
walk is in the image either (type-0x08/0x12 bodies covered by the whole-image scans above).

## Q3: verdict

**UNRESOLVED (leaning TRUSTS-TAIL).** Established as fact, byte-level:

- The signature covers ONLY the 8-byte-per-record table `0x101D:0x210, 0x101E:0x3410` (0x10 bytes).
- The `0x6400`-byte tail is not padding: it holds two ~0x3200-byte SMU-style CODE blobs (sub-headers with
  `$PS1` magic, shared 16-byte id, full tokens `0x0101_101D/0x0101_101E`, code at header+0xF0), at exactly
  the offsets the signed table points at (relative to body base `0x9C4500`).
- Therefore, IF the ROM consumer authenticates the table and then copies/executes code at those offsets
  (the only sane semantics of an id/offset code table), then 0x6400 unauthenticated bytes flow into
  execution — a pre-auth lane by construction. The dispatch path lives outside the flash image, so per the
  task constraint no bypass is claimed and the verdict stays UNRESOLVED until either the on-die PSP ROM is
  disassembled or a runtime trace shows the t44 blob copy.

## What would unblock

1. On-die PSP ROM image for this SoC (ROM walks `$PSP` and would contain the type-0x44 handler).
2. Runtime: TOS SRAM/trace showing whether the ROM copies t44 tail to a fixed address, or whether the SMU
   reads the container directly (SMU has SPI access on this platform).

## Command log (abridged)

- `python3` dir dump @`0x8E0000` (above); container/ABL extraction to `scratch/t44-hunt/` via u32 at +0x14.
- zlib decompress (`python3 zlib.decompress`) of t30-t34 signed bodies.
- Byte scans (`struct.pack` find loops) for words `0x44/0x210/0x3410/0x101D/0x101E/0x8E0000/0xFF8E0000/
0x9C4400/0xFF9C4400/0x6610/0x0101101D/0x0101101E` over t02 body, t28 body, each decompressed ABL, and the
  whole image; halfword scans for `cmp rN,#0x44` and `movw #0x101D/#0x101E` encodings.
- `llvm-mc --disassemble --hex --triple=thumbv7 --print-imm-hex` at t02 body `0xf92c/0xfc64/0x19b0`.
- No image write, no network, no hardware.
