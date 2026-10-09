# SMU chain development — ZD-1 to code exec and SMU-originated C2P (2026-09-23)

Body: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`,
262400 B, sha256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`
(re-verified this session). File offset = SRAM address (proven convention;
checked: literal at `0x181B0` = `0x000188A0`, gate byte at `0xCFD6` = `0x00`).
Ghidra 12.1.3 headless, `Xtensa:LE:32:default`, project `/tmp/ghidra_chain_proj`.
Reproduction scripts and raw outputs: `evidence/firmware-audit/20260923-smu-chain/`
(`ChainDev*.java`, `chain_dev_out.txt`, `chain_consumers.txt`, `chain_senders2.txt`,
`chain_send.txt`, `chain_ack.txt`, `mmio_literals.txt`, `literal_users.txt`,
`applier_callers.txt`). All offsets below are body/SRAM offsets; instruction bytes
quoted verbatim from the disassembly.

Baseline read: `docs/research/2026-09-19-zero-day-confirmation.md` and
`evidence/firmware-audit/20260919-zd/`.

## 1. Ring geometry for Q2 msg `0x23` (`FUN_0002D620`, body `0x2D620`–`0x2D782`)

Decoded arithmetic (bytes at `0x2D708`–`0x2D756`):

```
0002d708 l32r  a10,0x000181ac     ; a10 = 0x16C00000  (ring-0 record base tag)
0002d70b j     0x0002d711
0002d70e l32r  a10,0x000181a8     ; a10 = 0x16E00000  (ring-1 record base tag)
0002d711 l32r  a14,0x000181b0     ; a14 = 0x000188A0  (ring base literal)
0002d714 movi  a9,0x794
0002d717 mul16s a9,a12,a9         ; a12 = ring index 0/1 (arg3 bits 20-23)
0002d71e addi.n a10,a11,-0x1      ; slot = (arg3 & 0xf) - 1, validated to 0..3
0002d720 extui a10,a10,0x0,0x8
0002d723 addx4 a15,a10,a9         ; base_r + slot*4
0002d726 addmi a15,a15,0x600
0002d729 l32i  a11,a15,0x180      ; count = *(base_r + slot*4 + 0x780)   <- counter
0002d72c movi  a12,0x1e
0002d72e mul16s a10,a10,a12       ; slot * 0x1E
0002d731 extui a11,a11,0x0,0x8    ; index = count & 0xFF                 <- 8-bit only here
0002d736..2d740                 ; entry = base_r + ((count&0xFF) + slot*0x1E) * 0x10
0002d742 s32i.n a8,a9,0x0         ; entry[0] = arg0 + 0x16C00000/0x16E00000
0002d744 s32i.n a4,a6,0x4         ; entry[1] = arg2
0002d746 s32i.n a5,a6,0x8         ; entry[2] = arg1
0002d748 s32i.n a13,a6,0xc        ; entry[3] = 1 (arg3 low byte, validated == 1)
0002d74a l32i  a14,a15,0x180      ; counter re-read as full u32
0002d751 addi.n a14,a14,0x1       ; +1, NO upper bound
0002d753 s32i  a14,a15,0x180      ; store back
```

Layout (ring r base: r0 = `0x188A0`, r1 = `0x188A0 + 0x794` = `0x19034`):

| region                       | r0                  | r1                  |
| ---------------------------- | ------------------- | ------------------- |
| slot s entries (30 × 0x10 B) | `0x188A0 + s*0x1E0` | `0x19034 + s*0x1E0` |
| counters (4 × u32, slot*4)   | `0x19020`–`0x1902C` | `0x197B4`–`0x197C0` |
| struct end                   | `0x19034`           | `0x197C8`           |

Everything from `0x188A0` to `0x1B000` is zero in the image (BSS-class); code
resumes at `0x1B000` (first nonzero bytes at `0x1B000: f0004136 …`).

### First out-of-bounds writes (r0 slot0 as the driver, count = 8-bit index)

| count               | entry start | lands on                                                               |
| ------------------- | ----------- | ---------------------------------------------------------------------- |
| ≥ 0x1E (30)         | `0x18A80`   | slot1's record region — still in-struct (record overlap, benign shape) |
| 0x78 (120)          | `0x19020`   | **r0's own four counters** — attacker sets every count word            |
| 0x7C (124)          | `0x19040`   | r1's record region (forged records in the other ring)                  |
| 0xF2 (242)          | `0x197C0`   | entry spans `0x197C0–0x197CF`: +4 hits `0x197C4`, +0xC hits `0x197CC`  |
| 0xF9 (249)          | `0x197D0`   | **context pointer global** consumed by ~45 functions                   |
| 0xFC (252)          | `0x19800`   | entry spans `0x19800–0x1980F`: +4 hits `0x19804` (state)               |
| — r1 slot0 0x7D     | `0x197F4`   | `0x197F4/0x19804/0x19808/0x19810` state words                          |
| max (r1 slot3, 255) | `0x1A5C4`   | `0x1A5D0` — hard ceiling, **0x530 bytes short of code at `0x1B000`**   |

## 2. What consumes the overflowed words (the "transfer-engine table")

The ring entries are not dead data: they ARE the transfer-engine records. The
applier is `FUN_0002D4E0` (`0x2D4E0`), called from `FUN_0002D308`, `FUN_0002D35C`,
and the VCN/clock paths `FUN_0001F814`/`FUN_0001FAF0` (caller list in
`applier_callers.txt`). Decoded:

- queue-0 record table = `0x18E20`, record count at table + `0x1FC` = `0x1901C`
  (literals `0x1818C` = `0x00018E20`; consumer `FUN_0002d4e0@0x2d4eb`);
- queue-1 record table = `0x18C5C` / count base `0x195B4` + `0x1FC` = `0x197B0`
  (literals `0x181A0`, `0x18198`);
- record fields `{addr, and_mask, or_mask}`, stride `0x10` — the exact shape one
  msg-`0x23` append writes;
- application (decompile of `FUN_0002d4e0`, verbatim):

```c
*(uint *)(*piVar5 + iVar1 + 0x200) = piVar5[1] & piVar5[2] | *(uint *)(*piVar5 + iVar1 + 0x200) & (piVar5[2] ^ 0xffffffff);
```

with `iVar1 = DAT_00018190 = 0xEB3FFE00` (queue 0) / `DAT_0001819C = 0xEB5FFE00`
(queue 1) and record addr = `arg0 + 0x16C00000` / `arg0 + 0x16E00000`. The two
tags cancel: effective target = `arg0 + 0x02000000` (queue 0) /
`arg0 + 0x02400000` (queue 1), 32-bit mod 2^32. So each staged record is a
read-modify-write of `(old & and) | (or & and …)` at a fully attacker-chosen
address and masks, executed by the SMU on the next state transition. This is the
generic MMIO write primitive the "DBG_DISABLE reachable" claim rests on.

Globals inside the overflow window and their consumers (full lists in
`literal_users.txt` / `chain_dev_out.txt`):

- `0x197CC` — poll-retry max counter, read+write by `FUN_000326D0` (`0x3277D/0x32782`):
  `*(uint *)PTR_DAT_000184c0 = (uVar3 < uVar2) * uVar2 + …` — data only.
- `0x197D0` — context/heap pointer (literal `0x184DC`), used by ~45 functions
  (`0x32C18`–`0x39353`). `FUN_000390C0` (`0x390CD`) writes through it:
  `*(undefined1 *)(iVar2 + 0x80) = 0xff` for 16 bytes (`iVar2 = ptr + 0x780`),
  and zeroes `ptr+0x810/0x814/0x818`. Corrupting `0x197D0` therefore yields
  fixed-value (`0xFF`/`0x00`) writes at an attacker-chosen SMU SRAM address,
  including the code region `0x0–0x40000`.
- `0x197E0/0x197E4/0x197E8` — dispatch state read/written by `FUN_00036428`
  (the `0x53`-command dispatcher) and `FUN_00036E64` — data/state corruption only.
- `0x19804/0x19808/0x19810` — state words of `FUN_0003711C`/`FUN_000393D4`/`FUN_00039410`.

## 3. Code-execution verdict: DATA ONLY, no static path to control flow

- Reference scan of the whole program (`chain_dev_out.txt`): **zero** CALL or
  JUMP references into the overflow window `0x188A0–0x1A5D0`.
- The three indirect control-transfer mechanisms in the body all live **outside**
  the window: the RTOS dispatcher `FUN_00000EBC` calls handlers via
  `(*(code *)*piVar4)(param_1)` where the descriptor table is `*(0x7898)`-based
  (SRAM `0x7000` region, outside window); the command jump table of
  `FUN_00036428` is at `0x185CC` (literal `0x185CC` = `0x000364F8`, below ring
  base); scheduler tables at `0xAEC0`/`0xAE80` (below ring base). None can be
  reached by the overflow's `0x188A0–0x1A5D0` range.
- Closest partial primitive: `0x197D0` corruption → `FUN_000390C0` writes fixed
  `0xFF` bytes at `ptr+0x800..0x80F` and `0x00` at `ptr+0x810..0x818` with a
  controlled `ptr` — code bytes can be corrupted but only with `0xFF`/`0x00`
  patterns (no attacker-chosen instruction words). Not an arbitrary-exec
  primitive; HYPOTHESIS-class, low value.
- **Verdict: the overflow cannot redirect execution statically. It is a
  data-only primitive whose exploit value is (a) forged transfer records →
  arbitrary masked MMIO write at `0x02000000+addr` / `0x02400000+addr` applied by
  `FUN_0002D4E0`, and (b) fixed-byte SRAM/code corruption via the `0x197D0`
  context pointer.** Runtime input that would close an exec link: a body/runtime
  trace showing any function-pointer or jump-table variable stored in
  `0x188A0–0x1A5D0` at boot (none exists in the static image).

## 4. C2P senders: none found for PSP command mailboxes

Scans run (all negative for PSP-directed C2P):

1. Whole-body 4-byte word scan (`MP1_02B1xxxx`: 0 hits; `MP0_0305xxxx`: 4 raw
   hits at `0x1BCCC/0x26CE0/0x282D0/0x29128`, all with `refs=[]`, i.e. unaligned
   instruction bytes, not literals; `0x58180–0x58300` C2P low range: 0 hits).
2. Ghidra literal scan for MMIO-valued words `0x01000000–0x04000000` with their
   referencing functions (`mmio_literals.txt`): every window base is clock/power
   space (`0x0300FE00`, `0x0320FE00`, `0x0302FE00`, `0x031FFE00`, `0x013/017/018xx`,
   `0x02BFFF80` → window-0 target `0x02C00000+off`). No PSP APB window.
3. All 280 call sites of the window writer `FUN_00002A74` / reader `FUN_000029F8`
   extracted with preceding `movi/l32r` context (`chain_dev_out.txt`): offsets
   used are clock/power register offsets (`0x40/0x80/0x100/0x50130/0x5227C/
0x80410/0xF0014/0x402DC`-class). **No call passes an offset in any C2P range.**

What the SMU does have outbound (candidates evaluated):

- **Own-transport doorbells**: literals `0x700C/0x7010/0x7014` =
  `0x03010A48 / 0x03010A68 / 0x03010A08`, written by the accessor cluster around
  `0xF7C–0x1024` and `FUN_0001B374` (`0x1B38A`). These are the MP1-side
  C2PMSG-class registers of the SMU's own Q-ring transport (ack/doorbell face),
  not PSP command mailboxes. Ownership MP1 = inference, addresses = fact.
- **`FUN_000010D0` mailbox** (`0x10D0`): request/response transaction against
  base `0x01210600` (literal `0xBA8`): args at `+0x100/+0x104`, command
  `(msg & 0xFF) << 16` at `+0x118`, poll bit-31, response readback; mutex at
  SRAM `0x7ADC`. Message IDs used by the 8 call sites (`literal_users.txt`):
  **`0x07`** (`FUN_0001B460`, retried), **`0x19`** (`FUN_0001F814`, `FUN_0001FAF0`
  — the VCN/clock paths), **`0xFD`** (`FUN_0003144C`), **`0xFF`** (`FUN_00027AF0`).
  Receiver not identified as PSP; `FUN_0001B514` (the second-SMU-core register
  route) calls it at `0x1B520`, which points to the second SMU core as the
  remote end — HYPOTHESIS (second-core firmware is not in this body).
- **Ring response descriptors** (SRAM `0x7000` table, written by `FUN_00000FA8`):
  the per-transaction response channel PSP already polls. This is the only
  provably PSP-visible outbound channel, and it is tied to a PSP-issued request.

**Verdict: the SMU has NO dedicated C2P sender to the PSP in this body.** A
SMU-originated fresh C2P message would have to be synthesized either through the
forged-record MMIO write of §2 (if `0x02000000+addr` decodes onto PSP APB
registers `0x02B1xxxx` — unproven, needs one runtime readback probe), or through
the response descriptors of a transaction PSP initiated. The measured-negative
host→PSP result therefore does not get bypassed by a firmware sender: there is
no `smu_send_c2p(cmd_id)` helper to hijack.

## 5. Chain verdict

| link                                                                                                                                                                        | status                                                                                                                                                                                                                                                    |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HOST → Q2 msg `0x23` ring append (ZD-1, `FUN_0002D620`)                                                                                                                     | PROVEN-STATIC (prior work, re-confirmed byte-level above)                                                                                                                                                                                                 |
| overflow → forged transfer-record tables (`0x18E20/0x18C5C/counts `0x1901C/0x197B0`) → `FUN_0002D4E0`applies arbitrary masked MMIO write`0x02000000+arg0`/`0x02400000+arg0` | PROVEN-STATIC                                                                                                                                                                                                                                             |
| overflow → SMU code execution                                                                                                                                               | **NO** (data-only; zero CALL/JUMP refs into `0x188A0–0x1A5D0`; all indirect-call tables out of reach)                                                                                                                                                     |
| overflow / exec → SMU-originated C2P to PSP                                                                                                                                 | **NO dedicated sender exists**; only in-transaction responses (proven), `FUN_000010D0` mailbox IDs `0x07/0x19/0xFD/0xFF` (remote end likely second SMU core, HYPOTHESIS), or forged-record MMIO reaching PSP APB (HYPOTHESIS, needs runtime decode probe) |

## 6. Falsification / what closes the open links

- Code-exec link: closed (negatively) by the reference scan in §3; reopened only
  if a runtime dump shows a function pointer resident in `0x188A0–0x1A5D0`.
- C2P link: closed by one probe — stage a forged record (`arg0` = candidate PSP
  APB offset, e.g. `0x02B10060 - 0x02000000 = 0x00B10060`) and observe PSP-side
  C2PMSG state change; negative result retires the last SMU-originated-C2P route.
- `FUN_000010D0` remote end: identifiable only from the second SMU core's
  firmware, which is not in this body.
