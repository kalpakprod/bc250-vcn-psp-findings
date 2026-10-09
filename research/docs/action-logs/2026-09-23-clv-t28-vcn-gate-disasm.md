# clv t28 VCN gate — static disassembly

Date: 2026-09-23. Read-only static analysis. No image/hardware modified.

Base image: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
(16 MiB, sha256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`).
t28 (PSP dir type 0x28): FILE 0x984f00, size 0x1a770, ends 0x99f670.

All disassembly via capstone 5.0.7 (`CS_ARCH_ARM` + `CS_MODE_THUMB`) over a carved
t28 body. **Every conclusion below is STATIC. Static analysis is not proof of
hardware behavior.**

---

## 1. Addressing model — CONFIRMED (community CODE offsets are body-relative)

The loaded body = `t28[0x100 : 0x100+0x1A000]` (the TOC header at t28+0x100 is the
first thing loaded). PSP dir type 0x28 loads at the TOC load-base field
(t28+0x104 = `0x00E00000`).

**Mapping formula**

```
VA        = 0x00E00000 + body_off
FILE_off  = 0x00985000 + body_off          (= 0x984F00 t28-start + 0x100 header + body_off)
body_off  = FILE_off - 0x985000 = VA - 0xE00000
```

Verification (all landed on coherent Thumb code / self-consistent literal pools):

- producer `FUN_0000fc50` → body 0xfc50 (VA 0xE0FC50, FILE 0x991C50): real prologue,
  contains `svc #0xa6` at body 0xfc6a.
- walker `0x12B08` → body 0x12b14 (VA 0xE12B14, FILE 0x997B14): classic 8-reg
  `push.w` prologue (community 0x12B08 points a few bytes early, into the prior
  function's literal pool).
- gate-check literal pool: the constants `0x00E18B70` and `0x80000203` sit at body
  0x1220c / 0x12214 and resolve exactly under this mapping (see §4).

**Caveat / inconsistency to note:** the community DATA reference "`0x9970F4 =
t28+0x121F4`" uses **t28-relative** addressing (t28-rel = body_off + 0x100), i.e. a
DIFFERENT base than the community CODE offsets. `t28+0x121F4` = body 0x120F4 =
FILE 0x9970F4, bytes `05 46` (`mov r5, r0`) — an adjacent helper, NOT the operative
gate CBZ (that is at body 0x121d8, see §4). Treat community code offsets as
body-relative (VA base 0xE00000) and community "t28+X" data notes as +0x100.

---

## 2. Registration walker (0x12B08) and producer (0x115b6 / 0xfc50)

### Walker / lookup — body 0x12b14 (FILE 0x997B14, VA 0xE12B14)

```
E12B14  push.w {r4,r5,r6,r7,r8,sb,sl,lr}
E12B18  ldr.w  sb, [pc,#0x80]        ; sb = literal@E12B9C = 0x80000A01  (default/status const)
E12B1E  ldr.w  r8, [pc,#0x80]        ; r8 = literal@E12BA0 = 0x00E6AD78  (TABLE BASE, runtime)
E12B22  movs   r4, #0                ; index
E12B28  add.w  r1, r4, r4, lsl #1    ; r1 = idx*3
E12B2C  add.w  r6, r8, r1, lsl #3    ; entry = base + idx*0x18   <-- ENTRY STRIDE = 0x18 (24B)
E12B30  ldr    r0, [r6,#4]           ; entry+4 = valid flag
E12B32  cmp    r0, #1                ; == 1 -> active
E12B3C  movs   r2,#0x10 ; mov r1,sl ; add.w r0,r6,#0xc ; bl 0xE01450  ; memcmp(entry+0xC, key, 0x10)
```

Per-entry (stride 0x18): `+0` field, `+4` = valid==1, `+8` field, `+0xC` = 16-byte
key/GUID matched by memcmp. It is a **key lookup**, returning `sb`=0x80000A01 on miss.

### Producer — body 0x115b6 (FILE 0x9965B6, VA 0xE115B6)

Builds descriptor entries of **stride 0x38**, `memcpy`ing a 0x20-byte blob
(`blx 0xE01570`) into `entry+0x10`. Source-table base loaded from
literal@body 0x11634 = `0x00E35CF8`.

### The table is NOT static in t28 (key finding)

Both table bases are **outside the loaded image** (body size 0x1A000):

- walker table `0x00E6AD78` = body 0x6AD78 ≫ 0x1A000 → runtime RAM/heap
- producer source `0x00E35CF8` = body 0x35CF8 ≫ 0x1A000 → runtime RAM/heap

So the op/descriptor arrays are **constructed at runtime**, not stored in t28.
**There is no static 31/32-entry table in the t28 image to dump or count.** The
"op-id / tag" per entry cannot be statically enumerated from this blob.

Also: the community "`svc #0xf2` per table entry" was **not found** — a full
resync capstone sweep of the body finds **zero** `svc #0xf2`. The producer path uses
`svc #0xa6`; the gate init uses `svc #0x5e/0x5f/0x61/0x6c/0xa1`. `svc #0xf2` is
likely a P3.00 detail or misattribution; it does not exist in clv t28.

The tag constants `0xC096` and the pair `0x1024→0xC096` do **not** appear as
16- or 32-bit literals anywhere in the body (they are computed at runtime, or are
P3-era). `0x0900C004` (SMN VCN clamp-release) DOES appear as three 32-bit literals
at body 0xD2BC / 0xFD4C / 0xFECC (FILE 0x9922BC / 0x994D4C / 0x994ECC), so the
VCN-clamp-release write path IS present in the image.

---

## 3. VCN / type-13 entry: PRESENT-BUT-GATED, not statically countable as ABSENT

Because the op array is runtime-built (§2), the "31 vs 32 entries / missing 32nd"
claim **cannot be verified statically** — there is no static array in t28.

What IS statically true:

- The VCN handler machinery is **present in the image**: the SMN `0x0900C004`
  clamp-release write literals (×3), the gate-check that returns the reported VCN
  error `0x80000203` (§4), and the gate byte it reads all exist.
- The operative disable is the **gate byte = 0x00** at VA 0xE18B70 (§4), written 0
  during init (§4a).

Static verdict: this is a **present-but-disabled feature gate**, not a demonstrably
absent table entry. Re-adding a "missing entry" is **not** a bounded static data
edit here — the entry would have to be _registered at runtime_, and the registration
source itself lives in runtime RAM, not in t28.

---

## 4. Gate-check site producing 0x80000203 — body 0x121d0 (FILE 0x9971D0, VA 0xE121D0)

```
E121D0  0e 4b        ldr   r3, [pc,#0x38]   ; r3 = literal@E1220C = 0x00E18B70  (gate struct)
E121D2  30 b5        push  {r4,r5,lr}
E121D4  86 b0        sub   sp, #0x18
E121D6  1c 78        ldrb  r4, [r3]         ; r4 = gate byte [0xE18B70]
E121D8  b4 b1        cbz   r4, #0xE12208    ; gate==0  -> error path     <-- OPERATIVE CHECK
E121DA  d3 e9 04 43  ldrd  r4, r3, [r3,#0x10] ; (gate!=0) use struct fields +0x10/+0x14
        ... proceeds, does real work ...
E12208  02 48        ldr   r0, [pc,#8]      ; r0 = literal@E12214 = 0x80000203  (RETURN CODE)
E1220A  fb e7        b     #0xE12204        ; -> pop, return 0x80000203
; literal pool:
E1220C  70 8b e1 00  = 0x00E18B70   (gate struct address)
E12210  40 7b e9 00  = 0x00E97B40
E12214  03 02 00 80  = 0x80000203   (error code)
```

Behavior (static): **if byte[0xE18B70] == 0, the function returns 0x80000203** — the
community-described "FEATURE-DISABLED" gate for the type-13/VCN load. Not a signature
check; a single global flag-byte read.

Gate struct at VA 0xE18B70 = **body 0x18B70 = FILE 0x99DB70**. It is INSIDE the
loaded image's data region (TOC field t28+0x108 = `0x00E18000` marks the data/BSS
start). Its static value in clv is **0x00** (zero-filled sub-region) = DISABLED.
(It is a small struct, not a lone byte: check reads byte+0 as the flag and
`ldrd [+0x10]` later; init writes +0/+4/+8, see §4a.)

Key file offsets:

- gate CBZ (`b4 b1`): FILE **0x9971D8**
- gate-byte pointer literal (0x00E18B70): FILE 0x99720C
- error-code literal (0x80000203): FILE 0x997214
- gate struct base (value 0x00): FILE 0x99DB70

### 4a. The DISABLE-ASSERT writer — body 0xcd0c…0xcdb8 (FILE 0x991D0C…0x991DB8)

An init function writes the disable value 0 into the gate struct:

```
E0CD0C  ldr.w  r8, [pc,#0xb8]        ; r8 = literal@E0CDC8 = 0x00E18B70  (gate struct)
   ...
E0CD38  mov.w  sb, #0                ; sb = 0   (the value that gets written)   FILE 0x991D38
   ; 23-slot feature-flag loop (op/feature disable pass):
E0CD3E  ldr    r7, [pc,#0x94]        ; r7 = feature-flag byte array
E0CD40  movs   r4, #1
E0CD42  ldrb   r0, [r7,r4]           ; per-slot flag
E0CD44  cbz    r0, +               ; skip if already 0
E0CD50  bl     0xE0E2FC              ; query op availability
E0CD54  cbnz   r0, +
E0CD56  strb.w sb, [r7,r4]           ; slot disabled (write 0)
E0CD5C  cmp    r4, #0x17             ; loop slots 1..0x16  (0x17 = 23 slots)
E0CD5E  blo    E0CD42
   ...
E0CDAC  str.w  sb, [r8,#4]           ; gate struct +4 = 0                        FILE 0x991DAC
E0CDB2  strb.w sb, [r8]              ; gate byte  [0xE18B70] = 0  (DISABLE)       FILE 0x991DB2
E0CDB8  str.w  sb, [r8,#8]           ; gate struct +8 = 0                        FILE 0x991DB8
```

`sb` is set to 0 at body 0xcd38 and is never reassigned to a nonzero value before
the store, so **the gate byte is written 0 (disabled) at init** — the "disable is the
wired state." The enable value would be 1.

Sites for neutralizing the disable-assert (each is a CODE edit → see §5):

- write the disable value: `strb.w sb,[r8]` at FILE **0x991DB2** (needs `sb`=1).
- source of the value: `mov.w sb,#0` at FILE **0x991D38** (patch imm 0→1 would also
  flip the +4/+8 stores).
- OR the check itself: `cbz r4` at FILE **0x9971D8** (bytes `b4 b1`) — NOP/invert to
  ignore the flag.
- The 23-slot op/feature disable loop (which zeroes per-op enable bytes on query
  failure) is at FILE 0x991D42…0x991D5E; op-id-8 would be slot index 8 of that array
  (array base = literal@body 0x11640-ish region, runtime-resolved), but the array is
  RAM, so this loop _clears_ flags rather than being a static skip you can edit.

Note: community's proposed P3-only 2-byte-NOP site (`t28+0x121F4` = FILE 0x9970F4,
`05 46`) is an ADJACENT helper, not this gate CBZ; the clv operative CBZ is FILE
0x9971D8. This is consistent with "the P3 NOP did not work on hardware."

---

## 5. Is t28's $PS1/RSA signature verified before execution? — STATIC ANSWER: YES (by format), enforcement code is off-blob

t28 is a signed AMD PSP entry:

- PSP directory `$PSP` @ FILE 0x8e0000, 19 entries; type 0x28 entry = FILE 0x984f00,
  size 0x1a770 (matches). Type **0x01 = PSP bootloader** (FILE 0x8e0400, 0xB600) is a
  SEPARATE entry — it is the loader/authenticator, **not** part of t28.
- t28 `$PS1` header @ FILE 0x984f10: magic `$PS1` (`24 50 53 31`), signed-size field
  `0x0001A570`, version, and a key/fingerprint id. Every signed PSP entry in the image
  carries a `$PS1` header (22 found).
- t28 trailing 0x100 bytes (FILE 0x99f570…0x99f670): RSA-2048 signature.
  Shannon entropy 7.206 bits/byte, 166 distinct byte values — consistent with a raw
  RSA signature. (Location noted only; bytes not reproduced.)

**Enforcement:** the code that verifies the `$PS1`/RSA signature is NOT inside t28 —
on AMD PSP it lives in the on-die bootROM (verifies the type-0x01 PSP bootloader
against a fused root key) and in that type-0x01 bootloader (verifies each subsequent
PSP-dir entry's `$PS1` signature before load/exec). This is the standard AMD PSP
secure-boot chain. The very presence of a 256-byte RSA-2048 signature over the entry
exists to be checked; an entry that was never verified would not carry one.

Contrast with unsigned data: `APCB` (FILE 0xab1000, inside a `$BHD`/BIOS region) has
NO `$PS1` wrapper and is consumed as configuration data — that is the class of blob
that can be edited freely. t28 is not in that class.

**Consequence (static):** any edit to the t28 BODY (including every gate patch in
§4a) changes bytes covered by the RSA-2048 signature and will **fail signature
verification** on a correctly-functioning PSP loader. **Editing t28's body to flip the
VCN gate is therefore a dead route** unless one of the following (neither observable
from this blob) holds: (a) the type-0x01 PSP bootloader does not actually verify
type-0x28 (would require disassembling that separate, itself-verified entry to
disprove), or (b) signature checking is disabled by SoC fuses. The realistic route to
flip the gate is **runtime privileged PSP code-exec (CE)** that writes 1 to the gate
byte at VA 0xE18B70 (or drives SMN 0x0900C004) _after_ t28 is already running as
authenticated code — not a static image edit.

---

## 6. File-offset index (all body_off + 0x985000)

| item                                                    | body_off             | FILE                       | VA       |
| ------------------------------------------------------- | -------------------- | -------------------------- | -------- |
| TOC header / load base                                  | 0                    | 0x985000                   | 0xE00000 |
| producer FUN_fc50 (has `svc #0xa6`)                     | 0xfc50               | 0x991C50                   | 0xE0FC50 |
| producer FUN_115b6                                      | 0x115b6              | 0x9965B6                   | 0xE115B6 |
| gate disable-assert: `mov sb,#0`                        | 0xcd38               | 0x991D38                   | 0xE0CD38 |
| gate disable-assert: `strb sb,[r8]` (write 0)           | 0xcdb2               | 0x991DB2                   | 0xE0CDB2 |
| gate ptr literal (writer)                               | 0xcdc8               | 0x991DC8                   | 0xE0CDC8 |
| walker/lookup prologue                                  | 0x12b14              | 0x997B14                   | 0xE12B14 |
| walker table base literal (0xE6AD78, RAM)               | 0x12ba0              | 0x997BA0                   | 0xE12BA0 |
| gate CHECK fn entry                                     | 0x121d0              | 0x9971D0                   | 0xE121D0 |
| gate CHECK `cbz r4` (`b4 b1`)                           | 0x121d8              | 0x9971D8                   | 0xE121D8 |
| gate ptr literal (check)                                | 0x1220c              | 0x99720C                   | 0xE1220C |
| error 0x80000203 literal                                | 0x12214              | 0x997214                   | 0xE12214 |
| gate struct base (value 0x00)                           | 0x18b70              | 0x99DB70                   | 0xE18B70 |
| SMN 0x0900C004 literals                                 | 0xd2bc/0xfd4c/0xfecc | 0x9922BC/0x994D4C/0x994ECC | —        |
| $PS1 header of t28                                      | —                    | 0x984F10                   | —        |
| RSA-2048 sig (location only)                            | —                    | 0x99F570…0x99F670          | —        |
| community P3 NOP site (`05 46`, adjacent, not the gate) | 0x120f4              | 0x9970F4                   | 0xE120F4 |
