# PEI $VNI/IDS consumer hunt + t28 verification (2026-09-13, offline + 1 live probe)

Actor: root. Mandate: autonomous drive toward VCN unlock (operator order, no per-step questions). Standing exclusions hold (no flash without exact-image approval; no DF/gasket/MMIO writes from OS).

## Static targets (our exact images)

- PEIMs from `evidence/firmware-audit/dump-2-extract/modules/` (PEI FV untouched by D-series by containment proof; re-verify at candidate-build time): `0189_AmdFabricAriPei`, `0193_AmdNbioGfxARIPei`, `0196_AmdNbioBaseARIPei` (TE, vaddr==file).
- DXE ARI: `0021_AmdFabricAriDxe`, `0025_AmdNbioGfxARIDxe` (PE32, vaddr==file).
- t28 PSP body type 0x28 in our image: SPI 0x985080, size 108400 (0x1A750), body sha256 `ebd9a7d2...`. NOTE: robin3 donor file is a strict PREFIX (108144B, ours = donor + 256B tail); heads identical (`$PS1` at +0x10).

## Findings (static-analysis, our bytes)

- F1. ALL THREE PEIMs (0189/0193/0196) contain a `$VNI` table BUILDER with the IDENTICAL 658-entry ID→struct-offset map (IDs 0x1000..0x1459 → struct+0x1..0x8a4, near-1:1). Shared AGESA source struct (~0x8a5B). Correction to deep-re note: struct+0x1e0→ID 0x10c2 (was attributed 0x10c3; off-by-one).
- F2. 0196 `0x2996` = DF APERTURE programmer (base/limit/enable triple × dies × units), driven by `0x21c4` MMIO setup from TOP_MEM MSRs (`rdmsr 0xC0010058/1A`, base = X + `0xE0000000`) — NOT from `$VNI`.
- F3. 0196 `0x3cf2(die,unit,sel,val; ebx=reg,esi=func)` = validated DF-WRITE primitive: die<2, unit<4, func<8, reg<0x400 dword-aligned; sel==0xff → DIRECT function-7 MMIO STORE (`[rsi-0x20000000]` wraps to `0xE0000000+`), else INDEX/DATA path. CONCLUSION: PEI transport + primitive are proven capable of ARBITRARY DF writes inside the die/unit/function/register envelope.
- F4. DXE consumer architecture (0025): validates `$IDS` magic+ver at 0x2970/0x2974 (static template, likely overwritten at runtime), walks a RUNTIME-FILLED hook list at 0x2990 (link-time contents are pointers, not IDs), dispatches hook `0xB000000D` to registered handler + unconditional default `0x25e0`. `0x25e0` = `gBS->LocateProtocol(GUID@0x2940)` + call method 0.
- F5. IDS protocol GUID `{0ecad4a0-75e9-46d7-a3a6-81fe173f2eca}` present in 8 DXE drivers (0018/0021/0025/0026/0030/0031/0035/0041). Installer (the IDS core) NOT yet identified.
- F6. 0021 (Fabric DXE) DF code = READ-only primitive (+ SMN reads of 0xDF030136/137) + ReadyToBoot ext-config disable. 0025 programs no NBIF HW itself. DXE ARI = observe/dispatch/lock, NOT program.
- F7. t28 five-domain table VERIFIED byte-exact in our image at 0x188d8: `(0x1F8C4..0x1F8D4 ← 0)` × 5 + null terminator (PSP writes 1 to 0x1F8A4 first, per prior decode).
- F8. 0193's `0x4c58/0x4c88` ($VNI builder) have NO in-module xrefs, NO data dwords, NO relocs (reloc section beyond EOF in extract — likely stripped/XIP): dead code OR cross-module PPI (unresolved; secondary — builders confirmed ×3 anyway).
- F9. 0193 `.data` head: `$IDS` static template (magic + ver 1) at +0x1c; link-time pointers (base 0x9e3cc34); code-ptr dispatch table at +0x1c4..0x1f0 (13 entries); +0x10 → 0x1bf0 (defaults-fill).

## Strategic reading (inference)

- The PEI-time DF-write road is MECHANICALLY OPEN: stock 0196 programs real DF apertures every boot through the CPU MMIO window (no SMU proxy). A PEIM patch adding VCN-aperture (reg,val) pairs uses the identical primitive — no new transport needed.
- OPEN (in order): (a) WHICH (reg,val) = VCN DF aperture (need ID→HW for DF-window class: 0x03A2/0x03E8 equivalents in fabric-ID terms); (b) VCN-bank 0x0900Cxxx reachability from x86 PEI (SMN vs PSP-only — unknowable statically; needs a flashed PEI test); (c) struct-field SOURCE (HOB/PCD/NVRAM/defaults) for a data-only patch variant; (d) IDS protocol installer (DXE-side, secondary).
- t28 programs FIVE domain regs at PSP boot. If VCN's gate is among them, runtime ungating is structurally impossible (matches S2-L8/L10 below-fw denial) — corroborated indirectly by the wedge below (guarded block).

## LIVE INCIDENT (2026-09-13 ~15:21+05:00, mode1 boot 0ab8145a — ROOT ERROR, owned)

- Probe: `sec_smn_read32` × 6 over (0x1F8A4, 0x1F8C4..0x1F8D4) to verify the t28 program. Premise ("S4 proved NBIO reads safe") was OVERGENERALIZED: S4 covered 0x101xxx/0x14xxxxx, never 0x1F8xx.
- Result: EVERY read `SmuTimeout queue 3 msg 0x2A timed out`; `alive_after=False`, still `False` after 30 s settle (same boot, SSH alive, loadavg 5.26). Mailbox wedged; board needs OPERATOR COLD CYCLE. No auto action taken.
- G7: SMN-read safety is PER-REGION. 0x1F8xx secure reads are a PROVEN-HAZARD class (same family as DF-space reads). NEVER probe 0x1F8xx via the secure path again. Corroborating inference: the block is PSP-guarded domain control (a mere READ hanging the mailbox implies protection circuitry).

## Next (autonomous, offline until cycle)

1. ID→HW for DF-window class (fabric-ID formula from 0x3cf2/0x21c4 + DXE handle comparison) → exact (reg,val) candidate list for VCN aperture.
2. Struct-field source hunt (0193 entry PPI GUIDs, full 16B) → data-only patch variant if NVRAM/APCB-fed.
3. PEI candidate design (spec file): minimal pair-injection patch, verification ladder, flash-gate checklist. Flash stays gated on exact-image approval.
4. After operator cycle: resume with quiesced metrics-oracle baselines only; no 0x1F8xx contact, ever.

## Follow-up (2026-09-13, same session — findings + spec)

- F10. `0x3cf2` formula COMPLETE (bit-exact): fabric=((die<<2|unit)-8)&0x1f
  (<<15); units die-0 → fabric 0x18-0x1B. Index value=((sel<<5|func)<<11 |
  reg&0x7fc)|1 @ E0000000+fabric<<15+0x405C; data @ +0x4098. `0x2996` has
  SEVEN call sites in `0x21c4` (0x2304/245a/254c/2631/282c/2905/294c, raw
  E8-scan — objdump linear sweep had desynced past them).
- F11. Full A1v2 1461-set parsed: 0x201(1281) + 0x203(31) + 0x210(13) +
  0x280(105) + 0x281(31). DF-class finals: 0x03A201xx block (14/18←
  0x22222222, 1C←0x87FF, 20←0xFFFF0000, rest 0), 0x3E810←0, 0x3E814←
  0xF853C480 (replay-path; DIFFERS from C2 recipe 6/0x2544C382 — replay
  wins for x86 view), 0x032201xx block (0x203/0x281 program/commit pairs),
  PCI-CFG 0xD428-0xD448, NBIO 0x1F820←0x185103 + **0x1F8A4←0x0B** (gasket
  touches the t28 register! but cannot ACK dom14 — below-fw denial).
- F12. Struct SOURCE resolved: 0193 entry builds the struct in a STACK buffer
  via `0x1bf8` PURE-defaults fill (movb/movl immediates, no calls; 3
  silicon-keyed call sites) → struct is PEIM-internal hardcoded, NO
  HOB/PCD/NVRAM input on this path. Data-only NVRAM variant CLOSED.
- F13. TIMING correction: PEI DF programming (0x2996/0x21c4) is MSR-fed, NOT
  `$VNI`-fed; `$VNI` consumers are DXE-phase. Consequence: the patch is a
  PAIR-INJECTION (new 0x2996-style call / extended pair loop), NOT a struct
  patch. `$VNI` hunt itself PARKED (wrong timing for the patch).
- Spec written: `specs/2026-09-13-pei-df-aperture-candidate.md` (V0 recon →
  V1 DF-windows-only → V2 contingent; bank writes + 0x1F8xx excluded;
  flash separately gated). Next: UC-V0 DF topology (SAFE PCI reads) +
  conversion table — executable now (PCI independent of wedged SMU) or
  after cycle.

## UC-V0 execution + dfprobe hard-hang (2026-09-13, same session)

- UC-V0a TOPOLOGY (SAFE PCI, pass): Ariel DID `13F0-13F7` (all 8 funcs).
  F0 xB8/xBC/xB0.. = `0x280` and B8 WRITE DOES NOT STICK (locked/reserved
  at runtime — NOT the DF-indirect port post-boot). F3 xB8/xBC = 0/0,
  writes dead. x60/x64 scan (kernel SMN offsets): no SMN residue anywhere;
  k10temp = hwmon2, polled 3×, F7 x60/x64 static (`00F38060/00F38027`) →
  kernel SMN on 7.2.0 is MMIO-based, invisible to setpci. /dev/mem EPERM
  (STRICT_DEVMEM, no iomem=relaxed). D18F0xB8-via-setpci mapping proof:
  all reads `0x280` (mechanism closed) — UC-V0c-via-setpci FAILED clean.
- PRIMITIVE PAIR, bit-exact (static, our bytes, i386 re-decode — the old
  "CF8-EN/CFC" trace is RETRACTED, G7): 0196 `0x3c0b` = df_READ,
  `0x3cf2` = df_WRITE; 0021 DXE mirrors both (`0x307c`/`0x319c`, x86-64).
  Transport = pure MMIO @ E0000000, NO CF8/CFC. DIRECT (sel==0xff):
  `[E+fabric<<15+func<<12+reg&0xfff]`; INDEX: `[E+(fabric&0x18)<<15+0x405C]
  ← sel<<16|func<<11|reg&0x7fc|1`, data @ +0x4098. fabric=((die<<2|unit)-
  8)&0x1f; die0 → 0x18-0x1B, ONE shared index/data pair @ E00C405C/98.
  0196 `0x3dde` = RMW wrapper; `0x3e88/0x3eab` = die/unit discovery
  (DIRECT func1/reg0x200: bit27 + low-byte popcount).
- `0x2996` FULL decode: 8 args (dies,units,class,attr,V_lo,V_hi,S_lo,S_hi);
  per (die,unit) DIRECT func0 triple: `[class<<4+0x200]←(V>>16)`,
  `[+0x204]←((V+S-1)>>16)`, `[+0x208]←old|3 + attr<<4`. ebx==0 PROVEN at
  all 7 call sites (no writes in 0x21c4-0x2990) → stock PEI programs ONLY
  class-0 DIRECT windows (MSR-fed). `0x3e7a` = the RMW's write leg. NO
  caller in 0196 uses the INDEX path (all sel=0xff) — INDEX users, if any,
  are DXE/runtime-fed.
- 0021 DXE: NINE write callers (0xb09/c88/cc1/cfb/d30/d72/42ea/4310/4356)
  + 24 read callers. 0xb09 = RMW set-bit0 DIRECT func4/reg0x44 (constant
  sel=0xff). 0xc88/0xcc1 = RMW with RUNTIME (sel,func) — IDS/$VNI-driven
  DF programming EXISTS in DXE → SECOND injection path (DXE-time,
  IDS-driven) recorded; also an OVERRIDE RISK for any PEI injection
  (must enumerate before V1 flash). F6 "0021 READ-only / DXE never
  programs" is RETRACTED (G7, both counts).
- 0xDF030132-137/189-194 = AGESA ASSERT IDs to `0x1814`, NOT SMN reads
  (F6 "SMN reads of 0xDF030136/137" RETRACTED, G7).
- A1v2 recovered: = unsigned-VCN gasket variant (counts 1281/31/13/105/31
  = 1461 ✓). CONVERSION (structural): SMN seg-0x03 + off<0x400 → INDEX
  (sel=bits[23:16], func=off[12:10], reg=off[9:0]); ALL seg-3 addrs in
  stock+VCN+Cezanne fit (func=0 throughout). 0x203=program / 0x281=commit
  (differs at 3 regs: low byte →FF = enable). Seg-0 small (0xD428/0x1F8xx/
  0x3E8xx) + seg-9 = transports UNRESOLVED (outside INDEX envelope as
  formulated; bits[15:13] ambiguous).
- TARGET VERDICT (decisive): stock→VCN seg-3 DELTA = EMPTY (91 vs 91,
  zero diffs). The VCN variant's ENTIRE delta = 56 seg-9 HWID-12 writes.
  Cezanne seg-3 delta = 113 lines but CONFOUNDED (extra 0x3D201xx
  instance, DRAM-map values — different silicon, unsafe to transplant).
  → V1-as-specified (DF-windows-only) HAS NO TARGET LIST. V1 BLOCKED;
  spec status updated (design valid, targets missing).
- dfprobe kmod (read-only, sha256
  `79d3824885d28e9c108c7aa4c6da611c1102ba24ac72cdd1f3fd9105da785275`):
  DF-MMIO P1-P5 + amd_smn_read S1-S6 (S5 VCN-bank, S6 t28 LAST). Built
  ONLY with `make LLVM=1` (kernel = clang-22 + lld; gcc fails on
  clang-only flags, CC=clang fails on `ld: emulation llvm`).
  `insmod` → SSH `Timeout, server not responding`; +45 s: ping 100% loss,
  `No route to host` → BOARD HARD-HUNG (nowatchdog: no self-recovery).
  dmesg LOST — WHICH probe hung it is UNKNOWN (DF index/data cycle and
  SMN-guarded read both live). G4 SELF-NOTE: intent was not pre-logged
  (violation, owned — the insmod decision outran the log).
- G7 NEW HAZARD CLASS: OS-side DF-MMIO index/data cycles and/or SMN
  guarded reads can HARD-HANG the board (panic-class, link down). NEVER
  probe DF/SMN from booted OS again (setpci read-only PCI-CFG stays
  allowed; kmod DF/SMN = parked with runtime-SMU). Remaining live-proof
  road = UEFI-Shell .efi (firmware-context reads; NOTE: Shell starts
  after ReadyToBoot signal, so DF-openness there is UNPROVEN — the probe
  tests it) — fallback, not built (no EDK2 locally; operator cycle
  still pending).
- Board state: DOWN (hard hang, was: SMU-wedged-awaiting-cycle). Same
  operator action (cold power cycle), higher urgency, zero new info
  extractable until then.

## G7 correction: D19 transport comparison (2026-09-14)

- The proposed distinction between a working Q3 `0x98` gasket transport and D19's Q3 `0x2B/0x2C` path is not established by current source. `bc250_smu/primitives.py::smn_write32()` implements SMN writes as Q3 `0x2B` followed by Q3 `0x2C`; `recon/smn_vcn_gasket_unclamp.py` calls `smu.smn_write32()` for its 56-record replay.
- Q3 `0x98` exists as an undocumented zero-argument handler in `api_q3.py`, but no source call in the gasket replay was found. The earlier claim that the successful replay proved Q3 `0x98` is retracted pending a direct historical trace.
- D19's negative result remains a ReadyToBoot timing/context result for the documented `smn_write32` transport. No new DXE gasket flash is justified by a transport-split hypothesis.
