# Loop run #1 static verdicts (V1/V2/O4/O3/T1/O1-prep)

Evidence class: `observed-bytes` unless noted. Inputs hashed in-line below.

## V1 — P5.00 SMU t8 (`13c93c08`) vs 0.58.6.0 (`6a3da1ef`)
Bodies (post-0x200 wrapper, 262,144 B each): 139,508 bytes differ across
~82 ranges. Stable anchors: selector literal `0x03220038` @body+0xC38 and
`0x0900C230` @body+0x14FE0 at IDENTICAL offsets in both; SMN window base
literal `0x10FFE00` shifted 94280 -> 94304 (+24 B). Domain-table data
(register lanes 0x34/0x84/0x88/0x9C/0x70/0x74/0x164/0x150/0x158/0x1A0)
byte-identical but relocated -0x30 (old @0xF550, new @0xF520); an embedded
SRAM pointer moved 0x5C8F4 -> 0x5C0F4 accordingly. Dom cmd/status register
literals (0x110009C/0x11002EC/0x1100084/0x1100085/0x1100074), 8-core mask
0x115A870 and gasket literals are ABSENT as LE constants in BOTH bodies
(computed registers). Verdict (static): substantial recompile; no evidence
of changed domain register treatment. Msg-table/PowerUpDomain chain deep
decode deferred to run #2 with the Ghidra lens (V1 open).

## V2 — P5.00 t28 (`5b6828bf`) vs 0.58 (`ebd9a7d2`)
Bodies 107,888 B each; compact delta: single bytes 0x1410/0x1482/0x14D0/
0x154C-d, big recompiled block 0x1A28-0x17D14, 0x1A060-0x1A06D,
0x1A670-0x1A76F. The five-register boot program is INTACT in P5.00:
literals 0x1F8C4/C8/CC/D0/D4 at identical body offsets 100056-100088;
the (addr,value) table @0x188d8 byte-identical (48 B checked); 0x1F8A4
references shifted 64764->64976 and 93936->94132 (+212). Verdict
(static-analysis): P5.00 does NOT change the PSP boot-time five-domain
zero-write treatment; layout shift only.

## O4 — CBSG verdict (all @0xAB1434, schema `CBSG 0717`)
- dump: size 0x73C = 1852 B, 68 tokens; tail ends 0x03E8.
- clv: size 0x768 = 1896 B, 72 tokens (+4 vs dump); 352 bytes differ from
  dump within the first 1852 B; NOT byte-equal; tail differs.
- P5.00: size 0x54 = 84 B stub (36 tokens) followed by 0xFF padding.
Verdict (static): same group schema/version; clv carries 4 extra tokens
and diverging payloads. Clv-CBSG-onto-P5.00 is a real candidate delta, but
CBSG token semantics are undecoded — O4b decode still required before any
graft (operator gate anyway).

## O3 — FCLK candidate map (coupled pairs, IFR static)
- `MemoryClockSpeed` qid=0x20F @ AmdSetup+0x316 (abs 0x7E5): Auto=0xFF,
  125MHz=0x2, 225=0x4, 250=0x5, 400=0x8, 450=0x9, 500=0xA, 750=0xF,
  850=0x11, 1000=0x14, 1250=0x19, 1330=0x1A, 1375=0x1B, 1500, ...
  1750=0x23.
- `FclkDpm` qid=0x7045 @ AmdSetup+0x6A3: Disabled=0x0, Enabled=0x1,
  Auto=0xF.
- `UclkDiv1M0` qid=0x229 @ +0x330; `MemoryPstate` qid=0x25E @ +0x36D.
Historical IFR: semantics static until the current Setup body is decoded.

## T1 — fTPM static census
`AmdPspFtpm*` / `Tcg2` / `Ftpm` strings: 0 hits in P5.00, clv, and native
dump. fTPM stack exists only on the C0A donor (PEI cap/reset logic per
memory/firmware-audit.md line 49). Static verdict: no fTPM app in any BC250
production image; fTPM route stays donor-graft-class.

## O1-prep — T1-down candidate (BUILD ONLY, never flashed)
- Script: `scripts/build_amdsetup_memory_candidate.py` gained `--new-value`
  (default 0x23 unchanged; whitelist {0x23, 0x14}).
- Output: `candidates/BC250_O1prep_T1down_memclk-1000MHz_v001_from_pre-m0.bin`
  sha256 `a8a813b903d3c79aa87ac0d96b55e005e51b299735afd2eaa18e1b174f37260f`
- Source: pre-m0 `3f836668bc194cfaef230de3ea842828e665608b96f9f50c7d3960615fbea5fd`.
- Change: exactly 1 byte @0x7E5: 0xFF -> 0x14 (MemoryClockSpeed 1000 MHz).
  Hardware acceptance: UNVERIFIED (operator gate).

## Unrun this run
V1 deep msg-table decode (needs Ghidra lens), V3 Q3/ISO chain, C3 v2000a
mining + 8c rung doc — carried to run #2.
