# PSP $PS1 verifier destination hunt (static, CLV donor)

Date: 2026-09-23. Read-only session. Input image:
`evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, sha256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, unmodified.
Builds on `evidence/firmware-audit/20260923-verifier-first/REPORT.md` (do not re-derive its results here).

## Tools used (all commands)

1. `llvm-mc --disassemble --hex --triple=thumbv7 --print-imm-hex` (LLVM 22.1.8, `/usr/bin/llvm-mc`) on byte ranges of
   `evidence/firmware-audit/20260923-verifier-first/clv-t02-signed-body.bin` (type-0x02 TOS signed body, 0x13150 bytes, body offset = Ghidra address, base 0).
2. Ghidra 12.1.3 headless (`~/tools/ghidra_12.1.3_PUBLIC/support/analyzeHeadless`) on a COPY of the preserved project
   (`cp -r evidence/firmware-audit/20260923-verifier-first/ghidra-project /tmp/ghidra-hunt`; the original evidence project was not opened or written).
   Two scripts were run against program `clv-t02-signed-body.bin` with `-noanalysis`:
   `Hunt5050.java` (decompile 0x5050 + all functions in 0x5000-0x5600) and `Hunt2.java`
   (decompile 0x470, 0xe1c8, 0xf194, 0x2ac8, 0xe9d4, 0xe20c, 0x12018, 0x1203a, 0x1604, 0x258c, 0x1766). Both exit 0.
3. Python byte scans over the donor image and over the extracted type-0x28 body
   (`SPI 0x984f00 + 0x100, len 0x1a570`, written to `/tmp/t28-body.bin`): literal words, Thumb `movw` immediate encodings, SHA-256 constants, SVC bytes.
4. `python3 scripts/psp_ps1_verify.py evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (read-only re-run).

No image was modified, no hardware, no network. Scratch files live in `/tmp` only.

## Q1: where does SVCF2 service1/op1005 execute — verdict

**UNRESOLVED, leaning ROM-ONLY for the crypto decision itself.** The dispatcher boundary is image-resident (type-0x02 TOS body), but the code that actually
consumes op `0x1005` was not found anywhere in the 16 MB flash image.

Byte-level chain (all offsets are TOS body offsets unless marked SPI):

- SVC 240 -> indirect pointer at body `0x3CC` (word 0x4545, Thumb) -> dispatcher `0x4544`
  (decompile in `evidence/firmware-audit/20260923-verifier-first/tos-dispatch.txt`).
  `param_1 >= 0xF0` -> `FUN_00005050`. Raw decode of `0x5050`: `subs r2,#0xF0; cmp r2,#6; tbb [pc,r2]` — a 7-entry table at body `0x506A`
  (bytes `03 06 09 0d 10 1b 30 bc`) dispatching SVC 0xF0..0xF6. SVC 0xF2 is case `0xF2` of `FUN_00005050` (decompiled in this session, `/tmp/hunt5050.txt`).
- Case 0xF2 body (decompile, verified against raw bytes):
  - reads the INTERRUPTED context's r0 (`uVar5`) and r1 (`uVar9`) from the saved-context struct `*DAT_000050bc` (literal word at body `0x50BC` = `0x6010`, TOS SRAM);
  - `uVar5 <= 0xF` else error `0x2E`; slot = `*(u8*)(0x8430 + id)` (literal at body `0x1D24` = `0x8430`); slot==0 -> `0x2F`;
  - permission check against `0x69B0 + cur_slot*8` (literal `0x1D2C`) — **skipped when id == 1** (the id EEAE uses);
  - sp validation of the DESTINATION context:
    - current component type 5: sp must be `0x400000..0xBFF000`;
    - type 1: `0x200000..0x2FF000`;
    - special slot (byte at ctx `0x6006`): sp in `0xD00000..0xE00000` AND context pointer `uVar11-0x44` in `0xD00044..0xE00044`;
  - then `FUN_00000470(ctx-0x44, cur_ctx, 0x44)` — a 0x44-byte CONTEXT copy (decompiled: plain memcpy), not container type 0x44;
  - `FUN_00002AC8` -> `FUN_0000293C(0xD00000, entry, 3)` and return 0.

  There is no code fetch, no flash read, and no message-content inspection in the handler: SVC 0xF2 is a cooperative CONTEXT SWITCH to component `r0`
  with new stack `r1`. The request buffer (`sp[0]=0x1005, sp[4]=2, ...`) is consumed by whichever code resumes in that component.

- The sender `EEAE` (body `0xEEAE`, full raw decode in `evidence/firmware-audit/20260923-verifier-first/service1005-disassembly.txt`):
  builds msg at sp (`movw r0,#0x1005; str [sp]; movs r0,#2; str [sp,#4]`, args copied to `sp+8..sp+56`), then `movs r0,#1; mov r1,sp; svc #0xF2`,
  then reads `msg+0x3C` and stores it through `r9`. Only the TOS-side immediate `0x1005` exists in the image (see negative scan below).
- Destination classification: the switch targets RAM windows (`0x200000-0x300000` = TOS kernel SRAM, `0x400000-0xC00000`, `0xD00000-0xF00000`).
  The TOS loader literals (body `0x119C0-0x119E8`) point at `0x2050E8/0x2050C4/0x20A000/0x20D000` — the TOS kernel data lives in `0x200000-0x300000`.
  The `0xD00000-0xF00000` window is where `$PS1`-loaded bodies RUN: the type-0x28 body self-describes its load
  (body+4 = `0x00E00000` load base, `0x5244 'DR'` at body+0x08, size `0x1A000`, entry `0xE01A0C`; matches memory/firmware-audit.md:994 "load base 0x0E000000"),
  and `115B8` computes `0xD00000`/`0xE00000` as load destinations (`tos-load-targets.txt`).

### Negative scan (why "not in the image")

- Thumb `movw rX,#0x1005` (encoding `F241 1xx5` form): **0 hits in the whole 16 MB image**.
- Literal word `0x1005`: 7 hits, all unaligned, at SPI `0xE2290D/0xE41B91/0xE5C5F5/0xE76CE1/0xE8E889/0xEA74E1/0xEBD8B9`, evenly spaced by `0x1F284` —
  data inside a high-entropy region, not code references.
- Extracted type-0x28 body: contains SHA-256 constants (`0x428A2F98/0x71374491/0xB5C0FBCF` at body+`0x17928..`, `0x6A09E667/0xBB67AE85` x4 at `0x17750+`)
  and `$PS1` strings (body+`0x16B84/0x17098/0x19F10`), but **no `svc #0xF2` and no `0x1005` immediate/literal** — even if the op-1005 consumer runs at
  `0xE00000` (t28), it dispatches by table, and its handler was not identified.
- The only other SVC-F2 wrapper visible is body `0xEB3C` (yield back) and `FUN_0000F194` (switches away if `FUN_0000FCC8() != 1`).

Interpretation: the crypto decision either executes in on-die PSP ROM (consistent with the standing "verifier lane limited by on-die ROM" note,
memory/firmware-audit.md:928) or in flash-derived code whose dispatch is table-driven and unresolved. What IS proven image-resident: the TOS kernel,
the `$PS1` loader `115B8`, `EEAE`, and the reject plumbing — all inside the type-0x02 container at SPI `0x8EBA00`.

## Q2: where ACCEPT/REJECT returns and how it is consumed

- `120EC` (PS1 entry, `$PS1` magic check at mapped container+0x10, literal `0x31535024` at body `0x1219C`; raw decode in `ps1-loader-disassembly.txt`)
  calls loader `115B8` at callsite `0x1212C`.
- `115B8` maps a flash region (`FUN_0000E9D4`, attributes `0xC0000000`) and calls `EEAE` at callsite `0x116D4`
  (`iVar3 = FUN_0000eeae(local_158, param_3, auStack_7c, 0x20, &local_110, &local_164)`).
- Consumption: `iVar3 != 0 -> 0x117EA -> uVar10 = 0x34` — the whole load is aborted (cleanup at `LAB_00011DF4`, `svc 0x63`-style unwind, return code `0x34`).
  In `120EC` the loader return is `cbnz r0` -> error path (`movw r0,#0x11A`). **No path where a nonzero/unknown/exception return is treated as accept was found
  in this caller.** The service's own verdict arrives in `msg+0x3C` and is stored through `r9`; its subsequent use as `local_110` feeds the load path, not a
  bypass branch.
- Second, independent check after load: `FUN_0000F194(auStack_7c, 0x20, &local_8c, 0x10)` (32-byte and 16-byte arguments — digest vs key material),
  nonzero -> same `0x34` abort path.
- Span usage: `EEAE` receives the SAME pointer/length (`local_158`, `param_3`) that was used for the mapping, and the later load uses the same mapping
  (`local_15c = local_158`). No TOCTOU or span divergence is proven in this pass; the mapping attributes (`0xC0000000`, device/no-cache) differ from
  `FUN_0000E9D4`'s second call site (`0x240000` flag), which was not fully traced.

## Q3: sub-header / tail parse audit

Correction to the task premise: per `scripts/psp_ps1_verify.py:75`, the `$PS1` magic and the signed-length field live in the container HEADER
(`blob[0x10:0x14]` magic, `u32 signed_len` at `blob[0x14]`, kid at `blob[0x38]`); the signature covers `header(0x100) || signed_body(signed_len)`.
Findings from byte dumps of header + body:

1. **Type 0x44 (`@SPI 0x9C4400`, size `0x6610`) signs only 0x10 bytes.** `signed_len = 0x10`; after the 0x100-byte signature there are
   **`0x6400` bytes of UNSIGNED tail** (`0x6610 - 0x100 - 0x10 - 0x100 = 0x6400`). The signed body is two u32 pairs:
   `1d 10 00 00 10 02 00 00 1e 10 00 00 10 34 00 00` (records `0x101D:0x210`, `0x101E:0x3410`). Any consumer that treats the tail as trusted because
   "the container verifies" inherits `0x6400` unauthenticated bytes. Whether the TOS/ROM consumer actually trusts the tail is UNRESOLVED — the entry-table
   parser was not identified in this pass (`FUN_0000E1C8` decompiled as a plain memset helper, not the parser).
2. Type 0x02 and 0x28 have `tail_after_sig = 0` — fully covered by their signatures.
3. Size fields are TRUSTED from the container with only sanity checks: in `120EC` the parsed size (`[sp,#0x18]`) must be `>= 0x800` and a multiple of
   `0x400` (`cmp.w r1,#0x800; blo` / `lsls r0,r1,#0x16; beq`), else error `0x11A`. No recomputation against content length is visible in the decoded path.
   Whether that constitutes an exploitable inconsistency requires the ROM-side consumer, which is outside the image.

## Verdict summary

- Q1: **UNRESOLVED** — dispatcher boundary (SVC 0xF2, body `0x5050`) is image-resident and performs a context switch only; the op-`0x1005` crypto consumer
  is not present as identifiable Thumb code anywhere in the flash image. Leaning ROM-ONLY for the signature decision itself.
- Consequence for patching: the reject plumbing (loader `115B8`, `EEAE`, error `0x34` propagation) IS in the flash image (type-0x02 body), but modifying it
  requires defeating the type-0x02 container's own `$PS1` signature, and the chain above it was not resolved in this pass. No bypass path is claimed.
- Q2: reject-on-nonzero enforced at `115B8`/`0x116D4` -> `0x34`; no accept-on-error path found.
- Q3: type-0x44 container carries `0x6400` unauthenticated tail bytes; container length fields are trusted (align/minimum checks only).

## Where the trace stopped / what would unblock it

1. The op-`0x1005` consumer: needs either (a) the on-die PSP ROM image for this SoC to disassemble the ROM service side, or (b) a runtime trace of the
   context-switch (which code resumes after `svc #0xF2` at `0xEF3C` region) — a hardware/debug or emulation input this static pass cannot produce.
2. The type-0x44 tail consumer: identify which component parses type 0x44 (candidate: t28, which holds `$PS1` strings at body+`0x19F10` near a table);
   its dispatch is table-driven and was not resolved here.
3. Runtime values of the TOS SRAM tables (`0x6006` special-slot byte, `0x8430` id->slot map, `0x6054` component table) are boot-initialized; a
   readback/dump of TOS SRAM would pin which slot component id 1 maps to.
