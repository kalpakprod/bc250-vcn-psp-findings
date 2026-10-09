# BC-250 VCN — IF/Fabric Unclamp Plan (deep RE, 2026-08-29)

> Goal: make VCN-MMIO stop reading 0xFFFF_FFFF by re-opening the **IF/Fabric clamp** on the
> VCN_FABRIC aperture (base 0x02403000), via **reversible SMN bit-writes**. Verification probe:
> `mmUVD_VERSION` (amdgpu_regs @ 0x78CA) and `mmUVD_POWER_STATUS` (@ 0x78BC), both in
> VCN_SEG0_MMIO_DW@0x7800. Success marker (V2) = either != 0xFFFF_FFFF.

---

## 0. TL;DR verdict

Power(G1), clock(G2), VRAM-staging+fw(G3), driver path(G4) are DONE. VCN stays
`0xFFFF_FFFF` because the **Fabric/NBIF firewall that gates 0x02403000 was left in a
"match-all secure" (fully clamped) state**, and BC-250's SEC_GASKET image is also missing the
extra firewall windows that the working sibling Cezanne programs. The 56-write Bank-12 replay
(recon/smn_vcn_gasket_unclamp.py) only rebuilt the VCN *bank descriptors* (SMN 0x0900c000); it did
NOT touch the **data-fabric range registers (group 0x280/0x201: 0x3a2011c/0x3a20124/0x1c780/84…)**
that are the real gate. Those are what must be restored from Cezanne's values.

All writes below are **plain 32-bit SMN stores** (same transport as the proven Q3 0x98 smn_write32),
each **reversible by power-cycle** (stock gasket reapplies at boot). No flash. Write-first, then re-read.

---

## 1. Hypothesis — which register/bit clamps VCN, prioritized

Evidence gathered (live board + parsed SEC_GASKET + disasm of AmdNbioGfxARIPei):

- **NBIO source/target/route registers are ALREADY programmed and STABLE** (`0x13b1005c`=0x8000,
  `0x6a140`=0x8000, `0x13b00060`=0xffff, `0x6a144`=0xffff, `0x13b00084`/`0x13b0004c` set,
  `0x6a14c`=0x8, `0x33e0`=0x3820; disasm 0x042b–0x04d0 programs exactly these via helpers 0x6a3/
  0x72d/0x75b). => the routing PATH exists; they are **not** the clamp switch (they don't change
  when the domain is gated). **Do not treat as primary.**
- **Live SMU reads** (`/tmp/_probe_smn_fw.py`, today):
  - Data-Fabric firewall low/high **0x3a2011c / 0x3a20120 / 0x3a20124 / 0x3a20128 = 0xFFFF_FFFF**.
  - Group-0x210 VCN_SEG binding **0x3e810 / 0x3e814 = 0xFFFF_FFFF** (0x3e810=all-ones).
  - NBIF routing-firewall **0x1c780=0x2DF7F, 0x1c784=0xFF100000, 0x1c760=0x1E0A414, 0x1c764=0xFFE1FC17**
    (already populated by BIOS — close to Cezanne, so partly right).
- **SEC_GASKET diff (robin3 vs cezanne dir1)** — exact Robin→Cezanne deltas in group 0x201/0x210:
  - `0x3a2011c` robin=**0x87ff** → cezanne=**0x107ff**  (firewall LOW bound widens)
  - `0x3a20124` robin=**0x0**     → cezanne=**0x10fff**  (firewall HIGH bound)
  - `0x3a20128` robin=**missing** → cezanne=**0xffff0000**
  - `0x3d20114/118/11c/120/124` robin=**missing** → cezanne=0x22222222/0x22222222/0x107ff/0xffff0000/0x10fff
  - `0x1c780/84`, `0x1c760/64/68/6c` robin=**missing** → cezanne = routing/firewall pairs
    (0x1c780=0x2df4d+0, 0x1c784=0xff100000+0, 0x1c760=0x1e0a414+0xff400000, …)
  - `0x3e810` robin=**0x0** → cezanne=**0x6** (bind VCN_SEG0/1 MMIO to fabric; 0x3e814=0x2544c382)

Interpretation (consistent with "range = secured window, out-of-range = host-accessible"):
BC-250's single all-covering window `[0x87ff, 0xffff0000]` swallows 0x02403000 -> master-abort.
Cezanne's narrowed `[0x107ff, 0x10fff]` + the extra 0x201/0x3d201 windows carve VCN_FABRIC out of
the secured zone, so the host can reach it. The missing 0x280 tail (`0x3a20128`) and 0x3d201xx are
supporting windows on Cezanne.

### Priority order of registers

1. **#1 (single reversible bit-write) — 0x3a2011c (Data-Fabric firewall LOW bound)**:
   `0x87FF -> 0x107FF`. Widens/lowers the secured window so 0x02403000 exits it. Highest-leverage,
   smallest change, directly on the VCN_FABRIC aperture. **Try this first.**
2. **#2 — 0x3a20124 (firewall HIGH bound)**: `0x0 -> 0x10FFF`. Completes the [low,high] pair.
   Backup if #1 alone doesn't move UVD_VERSION.
3. **#3 — group 0x201 routing-firewall pair that maps VCN_FABRIC ROUTING (Cezanne-only on Robin)**:
   `0x1c780 -> 0x2DF4D` then `0x1c784 -> 0xFF100000` (pair; Cezanne writes 0x1c780 then 0x0, 0x1c784 then 0x0 —
   i.e. value then a follow-up commit/disable toggle). Then `0x1c760->0x1E0A414`/`0x1c764->0x5F16E2C`
   (`0x1c768->0x1C11823`/`0x1c76c->0x5E514A0`). These were MISSING on Robin's parsed SEC_GASKET.
4. **#4 — 0x3a20128**: `missing -> 0xFFFF0000` (Cezanne 0x280 tail). Backup high-side window.
5. **#5 — 0x3d2011c/120/124 (+114/118)**: replicate Cezanne's parallel firewall bank (0x22222222 x2,
   0x107ff, 0xffff0000, 0x10fff). Backup.
6. **#6 — 0x3e810 / 0x3e814 (group 0x210 VCN_SEG binding)**: `0x3e810 0x0 -> 0x6`; `0x3e814 -> 0x2544C382`.
   Binds VCN_SEG0/1 MMIO to the fabric router. Needed if the aperture isn't routed at all.
7. **#7 — full A1 replay** (replay Bank-0C descriptors + 0x280/0x210 commit sequence together,
   recon/smn_full_gasket_replay.py style) if the single-register writes take effect in SMN-space but
   the x86 side still reads 0xFFFF_FFFF (last-committing-agent / owner-context issue per
   vuln-1-gasket-runtime-reprogram.md).

---

## 2. Concrete reversible write list (SMN_address, current, target, bits, why)

| # | SMN addr | current (live) | target | bits changed | why |
|---|----------|----------------|--------|--------------|-----|
| 1 | 0x3a2011c | 0xFFFF_FFFF | 0x0000_107F | set low bound to 0x107F (was match-all 0xFFF…) | narrows data-fabric secured window off 0x02403000 |
|   |          | (file=0x87FF) |        |              | |
| 2 | 0x3a20124 | 0xFFFF_FFFF | 0x0000_10FF | set high bound 0x10FF | completes [0x107F,0x10FF] pair |
|   |          | (file=0x0)    |        |              | |
| 3a| 0x1c780  | 0x2DF7F  | 0x0002_DF4D | adjust low bound (Cezanne exact) | VCN_FABRIC routing-firewall low |
| 3b| 0x1c784  | 0xFF100000| 0xFF10_0000| unchanged-ish; keep high | VCN_FABRIC routing-firewall high |
| 4 | 0x3a20128| 0xFFFF_FFFF| 0xFFFF_0000| set high window (Cezanne-only on Robin)| secondary fabric window |
| 5 | 0x3d20118| 0xFFFF_FFFF| 0x0022_2222| enable class mask (parallel bank)| redundant firewall copy |
| 6 | 0x3e810  | 0xFFFF_FFFF| 0x0000_0006| bits 0-2 (bind VCN_SEG0/1) | bind VCN MMIO segments to fabric router |
|   |          | (file=0x0)|           |              | |
| 7 | 0x3e814  | 0xFFFF_FFFF| 0x2544_C382 | full binding range | VCN_SEG binding upper |

Notes:
- Write order: **#1 -> re-read -> #2 -> re-read -> (#3..#7 as needed)**. Each write is independent and
  reversible; never batch blind. Commit-style tail (program=0 then write then commit=1) only if a
  register is behind a program/commit gate; the 0x3a201xx and 0x1c7xx are direct SMN stores.
- `0x1c780` on Cezanne is written twice (0x2df4d then 0x0) and `0x1c784` (0xff100000 then 0x0); replicate
  that two-step if the single value alone doesn't stick.

---

## 3. How to verify each write with ONE access

Run on board (sudo), read-only amdgpu_regs:
```
sudo ~/vcn_unlock/read_vcn_direct.py
```
It prints `mmUVD_POWER_STATUS @0x78bc`, `mmUVD_VERSION @0x78ca` (both in VCN_SEG0_MMIO_DW@0x7800).
After **each** candidate write, run it once and watch:
- `mmUVD_VERSION`: 0xFFFFFFFF -> any other value (e.g. 0x0000_XXXX) = VCN now visible. **Primary pass marker.**
- `mmUVD_POWER_STATUS`: 0xFFFFFFFF -> nonzero = domain power visible.

Because both registers sit in the same 0x02403000-derived frame, a successful unclamp flips BOTH.
If #1 moves UVD_VERSION, stop. If it stays 0xFFFFFFFF, apply #2 and re-read; then #3, etc.

---

## 4. Wedge risk — what NOT to touch

Known wedges from the team's evidence:
- **0x1F8xx family = dead responder**; writing there can wedge the SMN bus (dead NBIO offset). Do not
  write into the 0x1F8000..0x1FFFFF region unless you have a verified value.
- **Q3 msg 0x2A (mem64 window)** masks its arg to 20 bits base 0x01100000; a wrong arg -> "queue 3
  msg 0x2A timed out - SMU wedged, cold cycle" (dump_nbio_vcn_route_2026-08-25.out). Avoid blind 0x2A.
- **Read-MMIO-before-enable = bus wedge** (VCN-ATTACK-PLAN §root cause): full gasket replay read VCN
  MMIO while domain gated -> board died (~04:02, ping 100%, SSH no-route; recovered by power-cycle).
  => **WRITE-FIRST**: do the register store, THEN re-read `mmUVD_VERSION`.
- These are register-space writes (no flash); **power-cycle restores stock gasket**. Reversibility is solid.
- Prefer Q3 0x98 (`smn_write32`, already proven) over ad-hoc transports. Watch `smu.alive()` after each
  write (as smn_vcn_gasket_unclamp.py does).

---

## 5. Minimal decision sequence (one reversible write first)

```
S0  --verify read-only baseline (DONE: all FFFF)
S1  WRITE 0x3a2011c  0x87FF -> 0x107F      ; SMU Q3 0x98, one 32-bit store
    verify: sudo read_vcn_direct.py
    -> mmUVD_VERSION != FFFF  => G5 OPEN (stop, record).
S2  if still FFFF: WRITE 0x3a20124  0x0 -> 0x10FFF
    verify.
S3  if still FFFF: WRITE 0x1c780->0x2DF4D, 0x1c784->0xFF100000 (pair), then re-read.
S4  if still FFFF: WRITE 0x3a20128->0xFFFF0000, 0x3d20118->0x22222222, 0x3e810->0x6, 0x3e814->0x2544C382.
S5  if still FFFF: full A1 replay (Bank-0C descriptors + 0x280/0x210 commit, file order) — owner/commit context.
    rollback between steps = power-cycle (or leave writes; all reversible).
```

---

## 6. Open questions to confirm BEFORE the real write (3)

1. **Register identity / reachable gate**: the live policy script reads `0x0322011c` (all FFFF) while
   SEC_GASKET and my SMU probe use `0x3a2011c` (also all FFFF). Are `0x3a2011c` and `0x0322011c`
   the SAME firewall controller (two windows) or two different ones? One reversible SMU read-back
   `smn_read32(0x0322011c)` right after a `0x3a2011c` write settles this. If they differ, rewrite the
   register column of the table above.
2. **Exact semantics / two-step of 0x1c780/84**: Cezanne writes 0x1c780 then 0x0 and 0x1c784 then 0x0.
   Is the second (0x0) a commit, an enable-clear, or a disable-tie-down? Until known, do the primary
   value write first (0x2DF4D) and test before emitting the 0x0 tie-down. Also confirm 0x1c780/84 are
   writable via Q3 0x98 from Linux (my probe only READ them; verify SMU write path doesn't wedge).
3. **Owner / last-committer context**: the 56-write Bank-12 replay took effect in SMN-space (readback OK)
   but x86 MMIO stayed FFFF (vuln-1). This implies the firewall may require a PSP-owned commit or the
   program=0/writes/commit=1 sequence across BOTH 0x201 and 0x280 groups together. Test the single
   register writes first (cheap, reversible); if they read back but don't move MMIO, go straight to
   the ordered A1 sequence rather than more blind writes.
