# BIOS 5 (robin_5) port of the public SMU exploit — gate + overflow geometry

Date: 2026-09-23. Source body: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` (262,400 B). Decompiled via Ghidra 12.1.3 headless, program `smu_fw_robin_5` from project `/tmp/ghidra_chain_proj/BC250_chain` (fix for the earlier exit-2: `-process smu_fw_robin_5`, not the project name). Scripts output: `evidence/firmware-audit/20260923-bios5-gate-port/port-dev{1,2}-out.c`.

## 1. The secure-access gate (BIOS-5 equivalent of DBG_DISABLE 0x7B3C)

The Q2 `0x0A` handler `FUN_00025414` guards every action with `FUN_0002a018(9)`:
nonzero -> the message is rejected with response 0.

```c
uint FUN_0002a018(uint p) {           // decompiled verbatim, simplified
    return (*(uint *)(DAT_000170a4 + 0x2e8) >> (p & 0x1f)) & 1;
}
```

Literal dump (file offset = vaddr, base 0):

| literal        | value                                   | meaning                  |
| -------------- | --------------------------------------- | ------------------------ |
| `DAT_000170a4` | `0x031FFE00`                            | control-block base       |
| guard word     | `0x031FFE00 + 0x2E8` = **`0x032000E8`** | bit 9 = the Q2 0x0A gate |

**Gate = bit 9 of the u32 at `0x032000E8`.** Clearing that bit unlocks the whole
`q2_0x0A` class (the class the public exploit needs for transfer-table ops).

## 2. The Q2 0x23 handler = transfer-record engine `FUN_0002D620`

Collective table (`tables/known_messages_smu_fw_robin_5.txt` line 120): Q2 `0x23`
@ slot `0x73F8` -> `FUN_0002D620` (`PPSMC_MSG_TransferTableDram2Smu` family).

Decoded mechanics (4 message words w0..w3):

- `w3 >> 24` = class. Class `0xC0`: sub-op `w3 & 0xFFFF`:
  `1` = arm record-add for instance `(w3 >> 20) & 0xF`,
  `0x20`/`0x21` = set instance flags at `+0x7D`/`+0x7E`.
  Class `0x01` = add record; anything else -> response `0xFF`.
- Instance array base: literal `PTR_DAT_000181b0` = **`0x188A0`**, instance stride
  **`0x794`**, instance bound check `(w3 >> 20) & 0xF` ∈ {0,1}.
- Sub-command `sc = (w3 & 0xF) - 1` ∈ {0..3}; per-instance region holds `0x1E`
  records of `0x10` bytes.
- Record slot: `(count + sc*0x1E) * 0x10 + inst * 0x794` relative to `0x188A0`,
  where `count = *(u32 *)(base + inst*0x794 + sc*4 + 0x780) & 0xFF`.
- Record content: `[0] = w0 + (inst ? 0x16E00000 : 0x16C00000)`, `[+4] = w2`,
  `[+8] = w1`, `[+0xC] = 1`; then `count += 1` (full u32, read masked to u8).
- Index bound: `w0 <= DAT_00017c5c` (`0x1FFFFF`).

## 3. Overflow geometry (ZD-1 on BIOS 5)

`count` is masked to 8 bits but is a full u32 in memory and there is no bound
against the `0x1E`-record region: repeated class-`0x01` adds walk the record
pointer up to `(0xFF + 3*0x1E) * 0x10 = 0xE10` bytes past the region start.

| instance | max write address (count=0xFF, sc=3)  |
| -------- | ------------------------------------- |
| 0        | `0x188A0 + 0xE10` = `0x196B0`         |
| 1        | `0x188A0 + 0x794 + 0xE10` = `0x19EA4` |

So instance-1 overflow covers `0x196B0..0x19EA4`, which includes the dispatcher
state literals: `0x197D0` (`PTR_DAT_000184DC`), `0x197E0` (`PTR_DAT_000185C4`,
busy/state variable in `FUN_00036428`), `0x197E4` (`PTR_DAT_000185D0`).
The BIOS-3 `TR_TABLE_PTR 0x19784` equivalent sits below instance 1's window;
the fake-table route (forge the consumer pointer, as rw-r-r-0644 do) needs the
record consumer identified — next decode step (xrefs to `0x188A0`/`0x18FB4`).

## 4. Supporting literals (all from the same dump)

`0x181A4 -> 0x18FB4` (instance flag array), `0x181A8 -> 0x16E00000`,
`0x181AC -> 0x16C00000` (record value bases), `0x17580 -> 0x08000000` (mutex),
`0x185C4 -> 0x197E0`, `0x184DC -> 0x197D0`, `0x185CC -> 0x364F8` (jump table),
`0x185D0 -> 0x197E4`, `0x17C5C = 0x1FFFFF`.

## 5. Product mapping (in-image chain)

DXE payload (our proven unsigned-DXE carrier) drives the mailbox (PCI `0xB8/0xBC`)
with: Q2 `0x23` adds to walk `count` -> overwrite -> clear gate bit 9 @
`0x032000E8` -> then the VCN payload: `FUN_00023B14(6, 1)` (domain power, host-
proven by thelamer) + second-gate slots `0x16/0x17/0x18`. No hardware, no rig:
everything ships inside one flashable image.

## Next decode steps

1. Xref/consumer of the `0x188A0` transfer tables (what executes/follows forged
   records) — the BIOS-5 fake-table params.
2. Exact overflow schedule (how many 0x23 adds per step, which words land on
   `0x197D0/0x197E0/0x197E4` or the consumer pointer).
3. Rewrite the payload from "clear debug byte" to VCN enable calls.

## 6. Second-gate MMIO map (FUN_00023AE0 / FUN_00024594 / FUN_00023680)

The VCN "second gate" (thelamer's open threads) decodes to concrete SMN blocks;
all values below from the literal pool of the same body:

| block                              | address                                                | role                                                                                                                                              |
| ---------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| packed clock plan                  | `0x0115D000` / `0x0115D004`                            | two interleaved shadow copies; read bit-wise by `FUN_0001CD80(bit_index, width)` (e.g. bits `0x2B00` w9, `0x2B17` w7)                             |
| per-domain lookup table            | `0x01100000` (base `0x010FFE00`+0x200, mask `0xFFFFF`) | config words consumed by the power-on handler                                                                                                     |
| clock controller regs              | `0x0115F800..0x0115F974`                               | `FUN_00024594` builds divider/mux words (+0x200, +0x210/0x214 7-bit divs, +0x250..+0x26C, +0x2B4), enable bit +0x208, +0x218 = 1, polls bit 0x100 |
| request bits                       | `0x0115AE00 + 0x3A8/0x3D0/0x3F8`                       | `FUN_000235C8(addr, (reg \| 0x11) & mask)` — power/clock request bit pairs                                                                        |
| status block                       | `0x01D80200`                                           | +0x14 &= `0xFFFFF3FF`, poll +0x18 & `0x0C00` != 0                                                                                                 |
| domain descriptors (in-image SRAM) | `0xF728`/`0xF72C`/`0xF780`, 0x1C stride, 27 domains    | fields +0x7C..+0xD2 updated from config reads                                                                                                     |
| clock-slot structs (in-image SRAM) | `0xF568`, 0x48 stride, 8 slots                         | per-slot state consumed by `FUN_00023EF8`/`FUN_00023F18`                                                                                          |

Consequence: the second gate is **data-driven over SMN space** — writable through
the BIOS-3-proven recipe (unlock secure SMN access, then host-side SMN writes) or
through the V9 applier primitive; no SMU code exec required.

## 7. Open item (RESOLVED same day — see section 8)

The gate word (`0x032000E8`, bit 9) sits in the message-args block, OUTSIDE both
the fw image and the count-walk reach (`0x188A0..0x1A5D0`). Candidates were:

1. V9 applier wrap-write reaching `0x032000E8` — ELIMINATED: the decompiled
   `FUN_0002D620` bounds `w0 <= 0x1FFFFF` (`DAT_00017C5C`), so the applier
   windows are only `0x02000000..0x021FFFFF` / `0x02400000..0x025FFFFF`. The
   original V9 probe target `0x02B10060` was outside both — the V9 script
   silently ignored the bound; corrected in `scripts/smu_forged_record_plan.py`.
2. A legit enable message writing the args block — never found; the second
   `0x031FFE00` reference (`0xBE8`) is a header-table data word, not code.
3. BIOS-3 TR-forge route — unnecessary after the section-8 discovery.

## 8. COLLAPSE: the second gate needs NO exploit — mailbox-only chain (2026-09-23)

Decoding the community DXE unlock driver (RescueMei/BC250-DXE-SMU-Core-Unlock,
`Bc250CoreUnlockDxe.c`) revealed the host-side SMN primitives, and the robin_5 body
provides the write-what-we-want message pair:

**Host SMN access (proven on hardware by the community driver):**

- SMN read AND write via the config-space pair `0xB8/0xBC` on PCI `00:00.0`
  (`SmnRead32`/`SmnWrite32` — used for the Q3 mailbox registers themselves:
  CMD `0x03B10A20`, RSP `0x03B10A80`, ARG `0x03B10A88`).
- Q3 message send order: wait RSP ∈ {1,0xFF,0xFE,0xFD,0xFC}; RSP=0; ARG=arg1;
  ARG+4=arg2; CMD=opcode; wait.

**robin_5 message pair = arbitrary 32-bit SMN write, NO guard:**

- `q3_0x28` (`FUN_00027F20`): `*(u32*)0x8B08 = arg` — store the target address.
- `q3_0x29` (`FUN_00027F38`): `**(u32**)0x8B08 = arg` — write the VALUE through the
  stored pointer, directly in SMU-visible space (SMN/SRAM).
- `q3_0x2C` (`FUN_00027F94`): writes ARG to `*(u32*)0x8B08+4` via `FUN_0002A74`
  (the mapped-aperture writer; sizes 0=byte/1=short/2=word) — the address for 0x2C
  comes from slot[1]. `q3_0x98` = the same aperture writer with the value HARDCODED
  to 0xFF (that is why the community driver "force-writes 0x00FF"; thelamer's
  "arbitrary SMN write" is arbitrary in ADDRESS only).
- None of 0x28/0x29/0x2C calls the secure guard `FUN_0002A018`. The "secure_access"
  names in the collective tables describe intent, not enforcement.

**The VCN power/clock path is message-driven:**

- `q3_0x1A` (`FUN_0002A968`) calls the domain power handler `FUN_00023AE0` (two
  call sites = enable/disable branches). thelamer's host-proven
  `FUN_00023B14(6, 1)` = domain 6 (VCN) enable through this message.
- `q3_0x87` (`FUN_0002937C`) drives the clock-controller programming
  (`FUN_00024594`).

**Product chain (all host-side, zero novel exploitation):**

1. DXE driver (our proven carrier + RescueMei's EDK2/UEFITool pipeline).
2. Read the SMU-populated clock plan via the config pair (SMN reads are open).
3. Adjust VCN fields / write controller + request registers via `0x28`→`0x29`.
4. `q3_0x1A(6, 1)` to power the domain; `q3_0x87` for the clock program.
5. Status polls via SMN reads (`0x01D80218` etc. — inside the PSP-readable map
   per the Habr probe listing).

The V11 exploit ladder (ZD-1 walk, gate bit 9 @ `0x032000E8`, literal forging)
is NOT needed for the second gate; it stays as the deep-research fallback for
gates that DO check the guard bit.

## Next steps (revised)

1. Extract the exact register sequence+values: decompile `q3_0x1A`/`q3_0x87`
   argument handling and the `FUN_00024594` field packing (bit offsets from the
   plan table).
2. Build the DXE driver: mailbox sequence above; reuse RescueMei's build scripts.
3. Candidate image + static verification + flash-approval request.

## 9. Message semantics decoded (2026-09-23, later passes)

- `q3_0x1A` (`FUN_0002A968`) = the DOMAIN POWER TRANSITION message: entry calls
  `FUN_0002A044` (no direct args; the message arguments are read from the args
  block, base `DAT_000170A4`, word at `+0x3F0`). `FUN_0002A044` = full transition
  state machine: lock, `FUN_0002A038(3)` step, clock-fence clears with status
  polls (`+0x214` bits 0/1), register tail (`+0x12C = (old&0xFFFFFFE8)|8`,
  `+0x130 = (old&0xFFFFFFFE)|0xE`, `+0x134 &= ~0x30`, `+0x120 |= 2`), engine
  steps `FUN_0002BF1C`/`FUN_0002E1E0`/`FUN_0002B0B8`, `FUN_0002A038(0)`,
  `FUN_0001F678(1,1)`, then bookkeeping. The two `FUN_00023AE0` call sites
  (`0x2B10C/0x2B111`) sit in this handler's body (enable/disable branches).
- `q3_0x87` (`FUN_0002937C`) = CLOCK PROGRAM dispatcher: arg>>4 < 0x12 selects
  one of 18 sub-ops via jump table `0x17F28`; out-of-range -> response 0.
- Mailbox message IDs (Q3, robin_5): `0x1A` power transition, `0x87` clock
  program sub-ops, `0x28` store SMN address (`0x8B08` slot 0), `0x29` write
  through slot 0 (arbitrary value), `0x2C` write ARG via aperture to slot 1,
  `0x98` write 0xFF (hardcoded) to ARG.

The deep decode (full 0x1A body, the 18 sub-ops of 0x87, the `FUN_00024594`
bit packing) is running as a bounded worker task; output = the message-level
runbook draft.
