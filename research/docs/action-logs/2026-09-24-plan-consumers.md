# 2026-09-24: clock-plan consumer census + static slot/descriptor decode (0b derivation, session 1)

Intent: derive the vcn-mailbox runbook step 0b donor values (the VCN clock-plan
window fill) for the v003b build. Static Ghidra work on the pinned robin_5
body (scratch copy sha-verified == cae8617c... this session) + read-only
hardware probes (the Linux 0x2A route, SMU alive throughout).

## Hardware probes (read-only)

- probe4l5 extended (END 0x0115D7B8): the REAL plan block is ~2 KB, not 0x5AC.
  Full read 495 words, alive: **everything past byte 0x334 is ZERO on this
  board** — the DPM tables (bits 0x2F45+, 0x30F1+), the flag cluster
  (0x36D3+), the VCN window (0x2B00+), and the health bit 0x3DB9 are all
  empty. The live plan = the low state region (0x000-0x0F4, words CHANGING
  between runs: 0x01570049->0x0157004a, 0x01830007->0x01840008 — live
  counters) + the plain-word struct at 0x300-0x334
  (0xc0000000, 100000, 1, 1, 0x6003, 0x10, 0x17, 1, 0x3f).
- JSON: evidence/runtime/20260924-004912-probe4l5-fullplan-ext.json (pulled).

## Static census (Ghidra 12.1.3 headless, existing /tmp/ghidra_chain_proj

BC250_chain / smu_fw_robin_5, -noanalysis, read-only scripts)

Scripts + outputs: evidence/firmware-audit/20260924-plan-consumers/
(PlanConsumers.java, PlanWriter.java, Dec32840.java + *-out.txt).

1. **20 caller functions of the bit reader FUN_0001cd80**, each with its
   plan-bit literal set (full map in plan-consumers-out.txt). Notable:
   FUN_00024594 = the VCN window (0x2B00-0x2C15, known); FUN_0002687c =
   32-entry table at 0x2F45+ (stride 0x0C bits); FUN_00021138 = 27-entry
   table at 0x30F1+ (stride 0x08); the 0x36D3-0x37F9 flag cluster shared by
   four functions (21058/221e0/22d6c/306c8); FUN_0001c844 reads
   0x3D6A/0x3D6E/0x3D72 (three w4 fields -> a version word, decompiled).
2. **The plan-base literals 0x0115D000/0x0115D004 are used ONLY by the reader
   itself** — no bit-wise writer exists through that path.
3. **ASCII console discovery**: FUN_000328a8 (called from the console
   dispatcher FUN_000337d4) parses S1-class text commands; command '0'
   (0x17 '0') calls FUN_00032840(DAT_000184c8=0x5D000 raw plan base,
   PTR_DAT_000184cc=**bit 0x3DB9**, width 7) and checks == 1 -> return
   0x13 ('S'?) vs 5. FUN_00032840 = the same bit-extraction arithmetic as
   FUN_0001cd80 but base-parameterized, reading via FUN_000029f8(0, addr, 2)
   (the debug transport). So the SMU's own console exposes a PLAN HEALTH
   check on bit 0x3DB9 — and that bit is 0 on this board (the check would
   fail). Data neighborhood 0x184c0: float 1.28 (0x3FA3D70A) at 0x184c4.
4. **Static slot/descriptor tables decoded (start)**:
   - Clock-slot structs at 0xF568, 0x48 stride: each carries a RAW window
     address (slot0 0x5B000, slot1 0x5B800 — the IPC-window family), float
     coefficients (0.1f = 0x3DCCCCCC, 1.95f = 0x3FF33333), and the LIST of
     controller register offsets (0x4C/0x9C/0xA0/0xB4/0x88/0x8C/0x26C/0x258/
     0x260/0x2A8; second slot 0x44/0x94/0x98/0xAC/0x80/0x84/0x214/0x200/
     0x208...) — the same offsets the plan fields feed (0x200/0x208/0x210/
     0x214/0x250-0x26C per the runbook section 4).
   - Domain-descriptor table (0xF728+): entries carry 0.1f, 01, offset
     lists, and RAW program addresses — **0x5F800 (the VCN clock controller
     window) at 0xF768** and the run 0x5B934/0x5B95C/0x5B984/0x5B9AC/
     0x5B9D4 with idx bytes 01 02/01 03/01 04/01 05/02 00, plus **0x5C0FC
     (the FCLK domain raw) at 0xF944** — matching the R3 section 1 table.
   - The upper plan's emptiness + the R3 note that channel-sync is "fed from
     PPTable byte [0x17120+0x61] x [0x17450]" point to the PPTable as the
     likely origin of the upper-plan fields; the miner firmware's PPTable
     appears to lack them.

## State of the 0b derivation (honest)

NOT DERIVED YET. No sibling VCN-shaped descriptor exists in the plan (the
VCN window is unique); no static donor values for the plan bits; the
community patches.hex = core-unlock code patches (BIOS 3); v2000a delivers
VCN config via its SIGNED carrier (no local APCB). Remaining route:
(a) finish the slot/descriptor decode (alignment + the VCN descriptor's
register list + coefficients);
(b) find the plan-field INITIALIZER (PPTable->plan path) to learn where the
upper-plan values come from on full-APU builds;
(c) derive VCN divider/code values from the controller semantics + validate
in the existing EmuSmu harness (FUN_00024594 with the fill must build sane
0x0115F6xx/8xx words and reach the tail poll honestly).

Gates: no repo state changed besides the listed new files (census scripts,
outputs, the pulled JSON, this log); pytest/make not re-run this sub-pass
(no project code touched — evidence-only additions).

## Session 1 continuation: descriptor layout CONFIRMED + FUN_00024594 fully decoded

- **Descriptor table formula validated 9/9** against the R3 section-1 proven
  pairs: raws[idx] = u32 @ 0xF7BC + idx*0x1C; slot byte @ 0xF7A8 + idx*0x1C;
  heads (register offset lists + 0.1f coefficients) @ 0xF728 + idx*0x1C;
  27 entries. The R3 doc's "domain id" column = THESE indices (0x18 = idx 24
  etc.) — numbering unified.
- **VCN area decoded**: idx 22/23/24 (theLamer's "slots 0x16/0x17/0x18" =
  indices 22/23/24) = the second-gate clock/reset/isolation trio, raws
  0x6D100/0x6D128/0x6D150 (SMN 0x0116D1xx), all clock-slot 6; idx 25/26 =
  the two VCN power steps (FUN_00023AE0 args 0x19/0x1A), raws 0x5F8FC/
  0x5F924 (SMN 0x0115F8FC/0x0115F924 — INSIDE the VCN clock-controller
  block), slot 7.
- **FUN_00024594 fully decompiled** (census output): the exact controller
  word construction from the plan bits —
  *(base+0x200) = w9(0x2B00)[8:0] | w4(0x2B09)<<9 | w5(0x2B0D)<<0xD |
  w4(0x2B12)<<0x16 (masks 0xFFFC1FFF/0xFC3FFFFF);
  +0x210/+0x214 = w7 dividers (0x2B17/0x2C15);
  +0x250/+0x258/+0x260/+0x268 = 4-entry table, each 3x w4 (0x2B20-class)
  - w2 (0x2B2C-class)<<0x19, constant OR 0x06900000 baked into +0x250;
    +0x254/+0x25C/+0x264/+0x26C = 4x w8 codes (0x2B2E/0x2B46/0x2B60/0x2B76);
    +0x2B4 = 4x w4 nibbles (0x2B9C/0x2BBC/0x2BDC/0x2BFC);
    +0x208 = w1 ENABLE (0x2B16); +0x218 = 1 unconditional; then the ready
    poll (bit 0x100 of the status word via the [0x1745c+0x22c] slot);
    tail: +0x358 = PTR_DAT_00017560, +0x374 = 0. No clamps beyond the masks:
    any in-range value lands; "sane" = what makes the hardware PLL assert
    0x100.
- **Populated 4-entry byte table spotted in the live plan**: single bytes
  0x83/0x68/0x55/0x68 at 0x0115D053/57/5B/5F (stride 4) — PLL-code-class
  values, same cardinality as the VCN window's 4-code table. No 1cd80
  reader covers bits 0x298-0x300 → a plain-word struct; consumer unknown.
  Candidate donor-code class, NOT yet proven to be VCN-related.

Next (still open for the 0b derivation): the field semantics (w9/w4/w5 =
mux/source/divider?) via FUN_00023ef8/0x23f18 + FUN_00023AE0 decompiles;
the origin of the populated byte table; then value derivation + the EmuSmu
validation of the filled window.

## Session 2: encoder semantics closed + NO-WRITER verdict + LIVE controller state (probe4l6)

- **Encoder chain fully decoded** (Dec2360c.java, dec2360c-out.txt):
  FUN_0002360c = slot register decode: freq_MHz = (reg & 0x1FF) +
  (reg >> 16) / 65536 (DAT_00017460 = 1/65536) — the slot program windows
  hold frequency in 16.16 fixed-point MHz. FUN_0001cad8 = piecewise DPM
  decode (0.25 MHz/code via DAT_00017270, top 128.0 = DAT_00017274).
  FUN_00023ecc = feedback-divider code encoder (piecewise on 4095/8191
  thresholds, floor 8). FUN_00023cb8 = packed post-divide encoder
  (2999/11998 integer refinement, 0x00010001-class output). FUN_00023c78
  = VCLK/DCLK code builder: eccc(decode(reg) x 0.1 x 256 x ratio + 63).
  FUN_0003acf8 = soft-float multiply (no FPU; all float ops are integer
  bit-trick implementations).
- **Power step**: FUN_00023a64(idx, val): freq = slot_freq(float) x val,
  code = eccc(freq x 256), write via FUN_00023890. FUN_00023AE0(idx) reads
  the descriptor raw window, stores status nibbles, recalcs slot + all
  dependent descriptors.
- **Bring-up chain mapped** (EncCallers/VcnEntry): FUN_0002a184 = the full
  VCN bring-up (gate releases 0x0220FE00/0x0115A200-class, mode writes,
  builder call, power step 0x19 with *(PTR_DAT_00017e90+0x3A0), enables at
  0x0100AE00 (+0x204/+0x208 = 1), 0x0100B200+0xE0 = 0xF, state -> 2, then
  FUN_0002b0f4 = steps 0x19/0x1A gated by policy check FUN_0001dd34(6)).
  Entries: FUN_0001fc50 (direct), FUN_0002a044 = teardown (state 3).
  FUN_0001b024 = boot init (calls FUN_00023680 sampler + steps idx 2/0).
- **Register-window bases dumped from the image**: VCN clock controller
  base = SMN 0x0115F600 (DAT_00017204); poll = 0x0115F964 bit 0x100;
  SMN read window = raw + 0x01100000; gate blocks 0x0220FE00/0x0115A200/
  0x01D80600/0x0100AE00/0x0100B200; init defaults block 0x01159A00.
- **NO-WRITER verdict (decisive for 0b)**: the plan-window field offset
  DATs (0x17978/0x17998/0x179b8/0x17a0c/0x17994/0x17990) are referenced by
  FUN_00024594 ONLY — no function in the SMU image writes the 0x2B00+
  window. The plan window is filled externally (PSP/loader) or not at all.
  Template hunt negative: no verbatim copy of the live plan low-region
  signature (0x300 struct / byte table) in the board dump, FD 3.00 donor,
  retroweb 2.00/3.00, or the 4700S C0A image (PSP region encrypted; the
  static float/metric sources are all zero in-image).
- **probe4l6 (20260924-012740, board up, gate already open, SMU alive
  after)**: the VCN clock controller block is ALIVE and boot-programmed:
  +0x200 = 0x0000000E (matches the R3 "plan A=B=0x0E" reading),
  +0x208 = 0x00000002 (ENABLE bit0 NOT set), +0x210 = 0x013C000D,
  +0x250/+0x254/+0x258/+0x25C = 0x3E000000/0x68000000/0x55000000/0x68000000,
  +0x264 = 0x0000000A, +0x268 = 0x0000000F; everything the bring-up would
  still write is zero: +0x218, poll 0x0115F964, +0x358/+0x374/+0x35C, all
  power-step windows 0x0115F8FC/0x0115F924(+acks), init-defaults block.
  The second-gate PLL program windows 0x0116D100/0x0116D128/0x0116D150
  (+acks) = ALL ZERO.
- **Plan-mirror identification**: the live plan words 0x0115D050-0x5C
  (0x83000000/0x68000000/0x55000000/0x68000000) mirror the controller
  table region — 0x68/0x55/0x68 match byte-for-byte at +0x254/+0x258/
  +0x25C. The plan low region is a COPY of the controller state, not an
  independent source.
- **Route consequence for v003b**: the board's own boot flow already
  programmed a PLL table into the controller; the missing piece is the
  bring-up tail only (enable bit, +0x218=1, poll wait, power steps, gate
  releases). Calling FUN_0002a184 (or its message entry) with the EMPTY
  plan would make FUN_00024594 zero +0x200/+0x210 (destroying 0x0E/
  0x013C000D) and then hang forever on the 0x0115F964 poll (bit 0x100
  can never assert with ENABLE=0) — an SMU wedge. The safe design = the
  driver REPLAYS the bring-up tail writes directly (skip the builder,
  keep the boot table): route B. Donor values are no longer needed; the
  board is its own donor.

Open for the next session: dump slot 6/7 raw windows (the power-step
targets); decompile-read FUN_00023890 (already in decrecalc-out.txt),
FUN_00024878, FUN_0002a2f4 (the remaining bring-up pieces); assemble the
exact replay write list with the 0x01D8-class write risk flagged; validate
in the EmuSmu harness; then build v003b (route B driver).

## Session 2 (cont): route-B assembly evidence

- **Slot pages decoded** (slot table 0xF568, word[2] = page base, word[7]/
  word[0xB] = offsets): slot 0 = 0x0115B04C, 1 = 0x0115B844, 2 = 0x0115C034,
  3 = 0x0115C834, 4 = 0x0116C034, 5 = 0x0116C838, 6 = 0x0116D038,
  7 = 0x0115F834 (INSIDE the VCN clock-controller page). All slots carry
  coeff 0.1f. The VCN clock domain = slot 7.
- **Entry chain**: FUN_0001fc50 (the bring-up wrapper) is reached by a
  COMPUTED_CALL from dispatcher FUN_0001fcec and sits in a pointer table at
  0x15220 — the SMU-side PowerUpVcn handler EXISTS in this firmware; the
  earlier "NULL" verdict was the host amdgpu side not sending it.
- **FUN_00023890 (power-step writer) decoded**: target raw = slot-table
  base 0xF568 + idx*0x1C + 0x254 (idx 25 -> 0x5F8FC -> SMN 0x0115F8FC,
  idx 26 -> 0x5F924 -> 0x0115F924; both measured ZERO today = the steps
  never ran). Sequence: optional FUN_00023d78(slot,1) if slot byte +0x14
  == 0; optional FUN_000239c0 if desc byte +0x98; optional code dance
  (FUN_00023fb8/0x24128/0x24084) if desc byte +0x83; then FUN_000235c8
  (raw, code) = plain SMN write at raw|0x01100000 (policy-gated variant
  via FUN_0001b514 for a DAT-bounded range); poll (raw+0x24)|0x01100000
  bit 0x10000; post-writes; descriptor bytes +0x82/+0x86 updated; recalc
  FUN_00023f18. idx 0x13 has a special 0x18-bit handshake at
  DAT_000178cc+0x214/0x218 (not our domain).
- **Remaining bring-up pieces decoded** (dectail-out.txt): FUN_0002a2f4 =
  enable-block handshake (0x0100AE00-class +0x234: write packed pair
  PTR_DAT_00017fac/0x17fb0, |= 1, poll bit 2); FUN_0002a344 = the big
  table pump (16 iterations of FUN_0001ee3c(...,0xd0) into the gate block
  +0x3CC/+0x3D4/+0x3D8, then ~60 register copies from the state struct);
  FUN_0001fea0 = component enable walk (3-byte rows, per-row message ops);
  FUN_0002bf1c = linear map setter (param x DAT_00017338 + DAT_00017278);
  FUN_00002b2c = timer delay; FUN_0002a038 = state byte setter.
- **Field coexistence insight**: the live controller registers hold MORE
  than the builder's fields (e.g. +0x210 = 0x013C000D: [6:0] = 0x0D =
  builder's 7-bit divider, [31:16] = 0x013C = boot-written). The builder
  writes whole words, so calling it would zero the boot-written parts —
  route C (fill plan + send message) would destroy the boot table fields
  the builder does not know. Route B (replay tail writes only) preserves
  them. The +0x200 = 0x0000000E IS exactly builder-shaped (w9 = 0x0E,
  others 0), so the boot and builder formats agree at least there.

Open: decompile FUN_00023d78/0x239c0/0x23fb8/0x24128/0x24084 (the
power-step helpers); decode the 0x2a344 table pump + FUN_0001ee3c; decide
the step-0x19 value source (the 0x2b0f4 internal path needs none);
assemble the exact route-B write list; emu validation; build v003b.

## Session 2 (final): route-B sequence assembled

- **probe4l7 (20260924-013438, clean, SMU alive after)**: all 8 slot
  program windows (0x0115B04C/0x0115B844/0x0115C034/0x0115C834/0x0116C034/
  0x0116C838/0x0116D038/0x0115F834) = ZERO; ack windows = 0x80000042 (s1)
  / 0x80000002 (s2..s7) — the acks share a common bit-31 marker; the
  s7 gate guesses 0x0115F838/0x0115F83C = ZERO (they were WRONG windows,
  see below).
- **Struct dump corrections (image, pointer zoo)**: PTR_DAT_00017900 ->
  0xF730, PTR_DAT_00017904 -> 0xF740 (column views of the same table
  area); PTR_DAT_00017560 -> 0x00010000 (the value written to +0x358);
  PTR_DAT_000171dc -> 0x00012f2c (the state struct), PTR_DAT_00017e90 ->
  0x000104dc (the SetVcnClock ratio struct).
  Slot 7 struct words: page w2 = 0x5F800; program offset w7 = 0x34 ( ->
  0x0115F834); acks w8/w9/w10 = 0x84/0x88/0x9C; raw2 w11 = 0x70 ( ->
  0x0115F870); THE REAL POWER-GATE WINDOWS w13/w14/w15 = 0x164/0x150/
  0x158 -> SMN 0x0115F964 (ready poll, bits 0x100/0x1000/0x10000 by
  operation) / 0x0115F950 (gate control) / 0x0115F958 (iso/gate 2 = the
  builder's +0x358 target!). w5 (+0x14) = 1 = the slot power gate is
  ALREADY ON at boot (FUN_00023d78(slot7,1) skips). w17 (+0x44) =
  0x5F8F4 (an absolute raw near the power-step windows).
  Descriptor 25/26 (0xF568-base rows): +0x08 raws 0x5B1B4/0x5B1DC,
  +0x10 = 0x500/0x600; the +0x254 power-step targets = 0x5F8FC/0x5F924
  (= the +0x8C DPM raws of the 0xF730 view — same cells); flags (0xF728
  view): idx 25/26 slot byte 0x07, all optional-path bytes (+0x82/+0x83/
  +0x98/+0x6A) ZERO -> every optional branch of FUN_00023890 SKIPS for
  the VCN steps. The step = write code to 0x0115F8FC/0x0115F924, poll
  +0x24 bit 0x10000, update bytes, recalc.
- **Power-step arg format = FLOAT RATIO**: init steps used 0.4 (idx 2)
  and 0.5 (idx 0); the step-0x19 ratio field (0x104DC+0x3A0) starts 0.0
  (runtime-filled, the SetVcnClock message 0x1A target). With ratio 0:
  code = eccc(0) = 8 = the MINIMUM PLL state — the safe first light.
- **Minimal replay sequence (route B, concrete)**:
  1. gate releases per FUN_0002a184 (0x0220FE00+0x200 &= ~4; the
     0x0115A200 mode ops; delay; 0x0115A200+0x12C |= 0x17; 0x01D80600+
     0x214 |= 2 [0x01D8 WRITE = risk item, the bring-up does it, reads
     are banned]; the FUN_0002a344 table pump [~60 writes, 16x
     FUN_0001ee3c command pulses into the 0x01C1CE00 block]; the
     FUN_0002a2f4 handshake at 0x0100AE00-class +0x234; 0x0100AE00+
     0x204/+0x208 = 1; 0x0100B200+0xE0 = 0xF);
  2. the BUILDER TAIL ONLY (skipping FUN_00024594 preserves the boot
     table): 0x0115F808 |= 1 (RMW! live value 0x2, the builder would
     write =1 and clobber bit 1), 0x0115F818 = 1, poll 0x0115F964
     bit 0x100, 0x0115F958 = 0x10000, 0x0115F974 = 0;
  3. power steps: 0x0115F8FC = 8, poll 0x0115F920 bit 0x10000;
     0x0115F924 = 8, poll 0x0115F948 bit 0x10000;
  4. state byte -> 2 + the FUN_0001fea0 component walk (the PSP-side
     notifications, 7 rows) + the FUN_0002a9d4/0x2a344 bookkeeping.
- **Transport**: FUN_000235c8 = plain SMN write at raw|0x01100000 (the
  same address form the probes read); the policy-gated variant =
  FUN_0001b514 -> message 0xFE. The driver's write path choice (mailbox
  0xFE vs direct Q2/DMA write) is a v003b design decision.

Open: the 0x2a344 pump decode (is it required for VCN wake or another
subsystem?); the 0x01D8 write risk decision; the FUN_0001b488(9) exchange
decode; emu validation of the replay; then v003b build.

## Session 2 (closeout): decode complete + replay list artifact

- **Policy lock measured**: PTR_DAT_0001739c -> 0xCCB0; the policy word at
  0xCCB8 (image initial) = 0x00000000 — bit 6 (the FUN_0001dd34 gate of
  the 0x2b0f4 tail steps) = 0. The SMU NEVER runs the tail power steps on
  this board. Route B (driver replay) is not a shortcut, it is the only
  route short of rewriting the policy bitmap in SRAM.
- **The "9" exchange decoded**: FUN_0001b488/0x1b4c0 = a PSP doorbell
  notification (args block 0x01210600+0x100/0x104/0x118, doorbell
  0x7ADC, cmd 9, empty args, response NOT checked) — skippable in the
  replay.
- **Pump identity**: FUN_0002a344 writes the 0x01130600/0x01109A00/
  0x01C1CE00-class blocks (NOT the VCN gate block — my earlier attribution
  was wrong); the 16 command ids 0x10..0x37; subsystem identity
  unestablished. v1 skips it (one variable per flash).
- **emu-phase2 report re-read = the exact write list of the bring-up**
  (8865 steps, completed, tracked writes incl. 0x0100B004/8 = 1,
  0x0100B00C = 0x75767570, 0x0100B034 = 3, 0x0100B2E0 = 0xF,
  0x0115A32C = 0x17, 0x0115A330 = 1, 0x0115A334 = 0x30, 0x0115A338 = 1,
  0x01D80814 = 2, 0x0115F8FC = 0x3F, 0x0115F958 = 0x10000,
  0x0115F95C = 0x4C000, 0x0115F974 = 0). The emu also CONFIRMS the
  builder's destructive path: with the empty plan it writes 0 into
  0x0115F800/808/810/814/850-86C/8B4 (only +0x218 = 1 and the tail
  survive) — the replay must RMW |= 1 at 0x0115F808 instead.
- **ARTIFACT**: evidence/firmware-audit/20260924-plan-consumers/
  vcn_replay_writes.json — the 24-step replay sequence with ops, values,
  emu cross-refs, live-state notes, the transport (the phase-1-validated
  0x28/0x29 mailbox write pair), the v1 skips (0x01D8 write, pump,
  unsafe-read gate release) and the abort guards. This is the input for
  the v003b driver build.
