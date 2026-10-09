# t28 Open Questions — Worker A report (2026-09-17)

Read-only analysis of `/tmp/t28_old.bin` (native 0.58.6.0, sha ebd9a7d2...) and
`/tmp/t28_new.bin` (P5.00, sha 5b6828bf...), 107888 bytes each. Disassembler:
capstone 5.0.7 via `/tmp/capvenv/bin/python` (CS_ARCH_ARM, CS_MODE_THUMB,
skipdata on). All addresses are file offsets = body offsets; run addresses add
the load base. Marked [observed] / [inference] per claim.

## OQ-V3a: load base and semantics of the (r5) table @0x188D8

### Load base = 0x00E00000 [observed]

u32 literal-pool scan over the whole image (step 4):

- Base `0x00E00000`: **484** u32 words fall in `[0x00E00000, 0x00E00000+0x1A550)`
  (i.e. map to plausible body offsets). Examples: `0x00E01A1C` referenced from
  61 pool slots (body offset 0x1A1C — inside the body), `0x00E1899C`,
  `0x00E18964`, `0x00E18B68`, `0x00E18930`, ...
- Base `0x0E000000`: only 3 in-range u32s, all of which are instruction bytes
  misread as words (`0x0E00F04F`, `0x0E019800` = mov.w/add encodings), not
  literals.
- Base `0x000E0000`: only 4 in-range u32s (`0x000EE890`, `0x000F0100`,
  `0x000EEA00`, `0x000FF000`) — these are actually SMN/status immediates
  (0xFF000-family), not pointers.

Decisive corroboration: `0x00E01A1C` (body 0x1A1C) appears as a pool literal 61
times; a base of `0x00E00000` maps it to a body offset, no other candidate base
does. Conclusion: load base `0x00E00000`; body offset = pointer − 0x00E00000.

Caveat [inference]: not every 32-bit literal of the form `0x0…xxxxx` is a
pointer. E.g. `0x0900C004`, `0x0001F8A4`, `0x0001F820` are SMN addresses, and
`0x100A140A`, `0x00E97A88` (word @0xE82C) do not map into the body under any
tested base — the latter are pointers/addresses in regions outside the t28
image.

### The table @0x188D8 is NOT credible as (SMN addr, value) pairs

Release/apply function (old @0xFCC8, new @0xFD9C — byte-identical logic,
[observed]):

```
old:                                  new:
0x00FCC8: movs r1, #1                 0x00FD9C: movs r1, #1
0x00FCCA: ldr  r0, [pc, #0x2c]        0x00FD9E: ldr  r0, [pc, #0x2c]
0x00FCCC: push {r4, r5, lr}           0x00FDA0: push {r4, r5, lr}
0x00FCCE: movs r2, #4                 0x00FDA2: movs r2, #4
0x00FCD0: svc  #0x7c                  0x00FDA4: svc  #0x7c      ; 1 -> 0x0900C004
0x00FCDA: ldr  r5, [pc, #0x24]        0x00FDAE: ldr  r5, [pc, #0x24]
0x00FCDE: movs r4, #0                 0x00FDB0: movs r4, #0
0x00FCE0: add.w r1, r5, r4, lsl #3    0x00FDB4: add.w r1, r5, r4, lsl #3
0x00FCE4: ldr.w r0, [r5, r4, lsl #3]  0x00FDB8: ldr.w r0, [r5, r4, lsl #3]
0x00FCE8: ldr  r1, [r1, #4]           0x00FDBC: ldr  r1, [r1, #4]
0x00FCEA: svc  #0x7c                  0x00FDBE: svc  #0x7c
0x00FCEC: cmp  r0, #0                 0x00FDC0: cmp  r0, #0
0x00FCEE: bne  #0xfcf6                0x00FDC2: bne  #0xfdca
0x00FCF0: adds r4, r4, #1             0x00FDC4: adds r4, r4, #1
0x00FCF2: cmp  r4, #5                 0x00FDC6: cmp  r4, #5
0x00FCF4: blo  #0xfcde                0x00FDC8: blo  #0xfdb2
```

Literals [observed]: old `0xFCF8=0x0900C004`, `0xFCFC=0x0001F8A4`,
`0xFD00=0x00E188D8`; new `0xFDCC=0x0900C004`, `0xFDD0=0x0001F8A4`,
`0xFDD4=0x00E188D8`. Table bytes @0x188D8 are **identical in old and new**
[observed]:

```
+0x00: low 0x84322C7F  high 0xDAEB1DBC   (qword 0xDAEB1DBC84322C7F)
+0x08: low 0x626A87B9  high 0x65C947F6   (qword 0x65C947F6626A87B9)
+0x10: low 0x81A345A2  high 0x9A7D67E1   (qword 0x9A7D67E181A345A2)
+0x18..+0x28: zeros                      (entries 4 and 5)
```

If the loop's (r0=addr, r1=value, r2=4) convention held uniformly, the five SMN
addresses would be `0x84322C7F, 0x626A87B9, 0x81A345A2, 0x00000000, 0x00000000`.
Verdict: **this interpretation is not credible** [inference from observed
bytes]: all three nonzero low dwords are 32-bit-unaligned (end in 0x7F, 0xB9,
0xA2) and are far outside the SMN ranges used elsewhere in this blob
(`0x1F8A4`, `0x1F820`, `0x0900C004`). The three nonzero qwords look like opaque
pseudo-random 64-bit constants (token/hash/key material), and the table is
zero-padded to 5 entries only because the same loop bound (5) is reused by a
companion read-back loop.

That companion loop [observed] at old `0x11360` (r5 loaded from literal
@0x11380 = `0x00E188D8`):

```
0x011360: push {r4, r5, lr}
0x011362: ldr  r5, [pc, #0x1c]        ; -> 0x11380 = 0x00E188D8
0x011364: movs r4, #0
0x011366: add.w r1, r5, r4, lsl #3
0x01136A: adds  r1, r1, #4
0x01136C: movs  r2, #4
0x01136E: ldr.w r0, [r5, r4, lsl #3]
0x011372: svc  #0x7b                  ; READ primitive (sibling of 0x7C)
0x011374: cmp  r0, #0
0x011376: bne  #0x1137e
0x011378: adds  r4, r4, #1
0x01137A: cmp   r4, #5
0x01137C: blo   #0x11366
```

So the same 5-entry table is consumed by svc `#0x7C` (write) at 0xFCC8/0xFD9C
and by svc `#0x7B` (read) at 0x11360. Bottom line for V3a:

- Load base: **0x00E00000** [observed, 484 in-range literals + 61 refs to
  0x00E01A1C].
- Table @0x188D8: **3 nonzero 64-bit constants + 2 zero entries; not plausible
  (SMN addr, value) pairs** [observed bytes; interpretation inferred]. If forced
  into (addr,value) the five SMN addresses would be `0x84322C7F`,
  `0x626A87B9`, `0x81A345A2`, `0x0`, `0x0` — rejected as above. Resolving the
  true semantics requires the svc `#0x7B`/`#0x7C` handler outside t28.

## OQ-V3c: r1 = 0x00185103 in the fw_type-13 svc #0x7C call — value, not pointer

fw_type-13 handler, old:

```
0x00E7BC: movs r2, #4
0x00E7BE: ldr  r0, [pc, #0x64]        ; -> 0xE824 = 0x0001F820
0x00E7C0: ldr  r1, [pc, #0x64]        ; -> 0xE828 = 0x00185103
0x00E7C2: svc  #0x7c
```

New binary, same logic at 0xE88C with literals @0xE8F4 = `0x0001F820`,
@0xE8F8 = `0x00185103` [observed].

r1 is a **32-bit immediate value loaded from the literal pool**, not a pointer:
in every other svc `#0x7C` call site in this blob r1 carries the value written
(`movs r1, #1` in the release block; `ldr r1, [r1, #4]` = table dword in the
loop — table dwords like `0xDAEB1DBC` are not body pointers either). Also,
`0x00185103` cannot be a body pointer under base 0x00E00000 (would be body
offset 0x185103, far past the 0x1A550 end), and the value is used with
r2 = 4 = length. Verdict: **r1 = immediate value 0x00185103**, i.e. the call
writes the 32-bit value 0x00185103 to SMN address 0x1F820. Meaning of the
packed fields (0x18, 0x51, 0x03) is undetermined — [inference] it looks like a
bitfield-packed register value, but nothing in t28 decodes it further.

## OQ-V3e: nothing in t28 writes to the 0x69D38 region

Searches run on both binaries [observed]:

1. Full-linear capstone scan for `movw` with immediate in 0x9D00–0x9DFF and for
   `movt` with immediate 6, and for any operand text containing `0x69d` /
   `0x9d38`: **0 hits in both binaries**.
2. u32 word scan for values in 0x069000–0x069FFF: 168 hits in each binary,
   **all of them inside the static pointer-table cluster at body offsets
   ~0x18Axx–0x18Cxx** — these are data, not code. The cluster contains the
   fw_type pointer table @0x18B70 (`0x00069D38 + i*8`, 14 entries
   0x69D38..0x69DA8, then further tables: 0x69DAC-step-8 series @0x18BAC,
   step-4 series @0x18BEC, 0x69BD4-step-4 series @0x18C2C, series from
   0x69CAC @0x18AAC, ...).
3. Direct-store dataflow scan: for every literal load whose value lands in
   0x69000–0x6A000, inspected the next ≤25 instructions for `str`/`strd`/`stm`
   with that register as base: **0 hits in both binaries**.
4. Indirect use of the 0x18B70 table [observed]: t28 loads the table base from
   pool literals (0x00E18B70 @0xE818 old / @0xE8EC-ish new; also @0x8EC4,
   0xCC04, 0xE698, 0x12028) and:
   - passes the loaded entry `[0xE18B70]` = **0x69D38** to svc `#0x5E`
     (0xE71E–0xE722 old) and svc `#0x5F` (0xE7EE–0xE7F2 old);
   - stores into the **t28-side copy** of the table, not into 0x69D38:
     `0xE7FC: ldr r1,[pc,#0x2c]` (-> 0xE82C = 0x00E97A88, an address outside
     the body) then `str.w r2, [r1, r0, lsl #3]` with r2=0xFF and `str r2,[r0,#4]`
     with r2=0 — i.e. it invalidates slots of a table located at 0xE97A88.
   - function @0xE5D4 and @0x8E30 read fields of the 0x18B70 struct and store
     into `[r0,#8]`, `[r0,#0x18]` — again the body copy.

Verdict: **no code in t28 (old or new) writes to the 0x69D38–0x69FFF region**.
t28 only (a) statically stores pointers INTO that region in its own tables,
(b) hands the region base 0x69D38 to svc `#0x5E`/`#0x5F`, and (c) reads/writes
its own body copies. Whoever populates 0x69D38 does it outside t28 (another PSP
component or the svc `#0x5E` handler). This is definitive for t28 only; the
sweep of other blobs is out of this task's scope.

## Bonus: where the ~0xFFFF0006 status is produced

[observed] Unknown-fw_type path in the service dispatcher (function @0xE6A8):

```
0x00E79E: ldr  r7, [pc, #0x74]        ; -> 0xE814 = 0xFFFF0006
0x00E7A0: adds r7, r7, #3             ; r7 = 0xFFFF0009
0x00E7A2: b    #0xe7ee
...
0x00E80C: mov  r0, r7
0x00E80E: b    #0xe718
0x00E718: add  sp, #0x18
0x00E71A: pop.w {r4, r5, r6, r7, r8, sb, sl, fp, pc}   ; returns r0
```

Note a correction to the parent's summary: the **literal** at 0xE814 is
0xFFFF0006, but the code adds 3, so the status actually returned to the caller
is **0xFFFF0009** (same literal and same `adds #3` pattern in the new binary;
literal @0xE8E4). It is produced only for fw_type values not in
{4, 8, 0xD, 0x21, 0x22, 0x33, 0x3C, 0x3D, 0x65, 0x66, 0x67} (dispatch chain
0xE764–0xE79C) and propagates: caller wrapper @0x11FEC (`bl 0xe6a8`;
`cmp r0,#0; bne` at 0x12014 → propagates nonzero to its caller) — observed at
least one caller at 0xE65E. A nonzero return from the memory-reservation call
`bl 0x11460` (0xE736–0xE73A) also propagates directly via the same 0xE80C/0xE718
path; the service caller receives it in r0.

## Unrun checks

- svc `#0x7B`/`#0x7C`/`#0x5E`/`#0x5F` handler semantics (live in PSP director
  code outside t28) — not disassembled here.
- Whether any other PSP blob populates 0x69D38 — out of scope.
- Hardware behavior — none of this is hardware-verified; everything above is
  static analysis class `static-analysis` / `observed-bytes`.
