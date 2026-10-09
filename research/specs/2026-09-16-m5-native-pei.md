# M5: 4700S base + native PEI phase + native NVRAM (definitive PSP test)

Date: 2026-09-16. Actor: root. Status: SPEC (build next).
Supersedes: nothing (first PEI-phase experiment; M0/M2-full/M4 eliminated
as-is compat, APCB data, L1 BL). T1 shelved per operator base choice.

## 1. Title and scope
M5 keeps the 4700S base (C0A PSP directory + BL graft + DXE FV with the
fTPM stack) and transplants the entire native PEI phase (2 MB
`0xE00000-0x100000`: SEC, reset vector, PEI core, inner FV incl. training
and microcode) plus the native NVRAM FV (`0x0-0x20000`: AmdSetup/Setup
NVARs + VSS store). One conceptual variable: the x86 PEI phase is native.
Out of scope: surgical module swaps (PPI-coupling risk, ambiguous on
failure), DXE changes, NVRAM value edits (T1's pin NOT carried: M5 base
is M4, whose NVRAM is being replaced wholesale by native-with-Auto).

## 2. Planning anchor
Exact base: M4 `candidates/BC250_M4_M2full_BL-native_v001.bin`
(`856af24b...`: C0A + native APCB + native L1 BL graft).
Exact donor ranges from pre-m0 (`3f836668...`):
- `0x000000-0x020000` (FVH len 0x20000 both images, identical layout)
- `0xE00000-0x100000` (FVH len 0x200000 both; nested FV 0xE02000 len
  0x1FE000 both; BHD type-0x62 BIOS entries identical
  type/flags/size/location/destination, bodies differ by drop).
Required preconditions: C0A NVRAM lacks AmdSetup (zeros at 0x4BB —
  OBSERVED, forces the FV@0x0 swap); no-PSB evidence inherited
  (D12 DXE wedge proved unsigned DXE executes; PEI region unproven but
  same fuse).
Builder: `scripts/build_m5_m4_native_pei.py` (hash asserts, FVH/length
asserts, whole-image diff confinement to the two ranges).
Output: `candidates/BC250_M5_M4_PEI-native_v001.bin`.

## 3. Connected groups and observed existing logic
- FV layouts byte-identical (bases/lengths/hdr size) across images, so the
  swap is layout-trivially same-slot; transplanted FVs carry their own
  valid checksums (self-consistent).
- BHD type-0x62 BIOS (2 MB @0xE02000 -> RAM 0x9E00000): loaded by ABL;
  container format same-family (residual risk R1).
- HOB handoff PEI->DXE is architectural (EDK II/PI standard); cross-drop
  AGESA HOB skew is residual risk R2.
- Native PEI + C0A PSP policy gap (0x20/0x24/0x45 absent): native PEI
  querying PSP policy is residual risk R3.

## 4. Use cases
- P0 POST+video: any sign of life (LED/LAN/video/serial). Boot =>
  4700S Frankenstein base ACHIEVED (C0A PSP+DXE/fTPM + native PEI/data);
  continue OC (host governor + menus) -> VCN (Shell probe -> inject) ->
  TPM (fTPM DXE live on C0A base) on M5.
- Silence => PEI phase eliminated as the blocker locus. Remaining loci:
  (a) C0A PSP/ABL stage never starts (favored: 4th silent rung, zero
  signs of life across all variables), or (b) PEI->DXE handoff mismatch
  (R2). 4700S base then dead WITH PROOF at the PSP/handoff stage; only
  remaining 4700S-flavored route would be native-DXE (== Track B).
  Rollback images preserved (all rungs + pre-m0).

## 5. Implementation checklist
- [x] FV layout compare (identical) + BHD-0x62 compare (entries ident)
- [x] C0A-NVRAM-lacks-AmdSetup proof (forces FV@0x0 swap)
- [ ] M5 build + structural verify (audit/PSPTool/diff/FV/reset-vector)
- [ ] Independent review PASS
- [ ] Operator exact-text approval + CH347 -w + VERIFIED + readback
- [ ] Cold boot P0 verdict (+ P1/P2 if alive)

## 6. Open questions
- OQ-M5a (residual, answered by boot): C0A-ABL loading native 0x62 image.
- OQ-M5b (residual, answered by boot): native-PEI -> C0A-DXE HOB compat.
- OQ-M5c (non-blocking): UART header presence (operator never answered;
  would discriminate PSP-halt vs PEI-hang on silence).

## 7. Decision log
- MD1 2026-09-16: whole-phase swap over surgical module swap (internal
  PEI consistency; HOB handoff standard; failure narrows locus cleanly).
- MD2 2026-09-16: include FV@0x0 NVRAM swap (C0A lacks AmdSetup; native
  CbsBasePei requires it).
- MD3 2026-09-16: build on M4 (keep APCB+BL grafts; harmless, possibly
  needed; removing them adds variables).
- MD4 2026-09-16: operator chose 4700S base over Track B (explicit
  decision prompt; G7: plan trigger != base-change approval).
