# Flash-ladder audit + APCB-DFG correction log (2026-09-12, Asia/Almaty)

## Intent (before any memory edit)

- Actor: root. Trigger: operator asked for a critical audit of all actions,
  whether the flash ladder went the wrong way, and new VCN bypass methods.
- Scope of this log entry: read-only audit (no flash, no register write, no
  hardware operation) + two memory corrections (G7) for a verdict disproved
  by direct byte measurement this session.
- Edits planned after this intent record:
  1. Append G7 correction to `memory/firmware-audit.md` (APCB DFG verdict).
  2. Update P3.2 status in `docs/research/2026-09-12-unlock-paths-map.md`.
  3. Append current board-state line to `memory/project-state.md`.
- Rollback for these edits: git working-tree diff (no commit planned).

## Method (all read-only)

- Read to end: all 7 project skills covering this domain
  (bc250-reverse-engineering, firmware-forensics, apcb-policy-analysis,
  uefi-dxe-validation, vcn-smu-probing, artifact-verification,
  cutter-reverse-engineering), all 6 `memory/instincts/*.yaml`,
  `memory/firmware-audit.md` (613 lines), `project-state.md`,
  `open-questions.md`, `decisions.md`, `tools.md`, `corpus.md`,
  `evidence-model.md`, `docs/research/2026-09-12-unlock-paths-map.md`,
  `candidates/d19-gasket-c830-only/build_d19.py`.
- Independent re-verification of D19 (exact commands preserved):
  - `sha256sum` candidate vs `evidence/programmer/reads/20260912/d19/postwrite-d19.bin`
    -> identical `2551ef66...`; `cmp` exit 0.
  - Extracted `extract/modules/0000_Bc250CoreUnlockDxe_pe32.bin` sha256 ==
    shipped `.efi` `dd242b34...`.
  - `scripts/firmware_audit.py postwrite-d19.bin --output /tmp/d19-audit.json`
    (input untouched, output to /tmp): 16 MiB, PSP Fletcher `0x63FFFCC8`
    match, BHD `0xECE7B2E6` match, APCB `0x32` match, 4 FVs.
  - Independent single-variable probe `/tmp/d19_single_variable_check.py`
    (kept under /tmp, not committed): decompressed FV 4,325,392 B in both
    images, FFS@0x88, payload@0xA4, bytes outside the 12,288 B PE32 payload
    identical, payload == shipped `.efi`, signed region
    `0x8E0000:0xAE0000` identical, bytes outside capsule region identical.
    Result: SINGLE-VARIABLE PASS.
  - Direct APCB byte read (struct `<I` at `0xAB1000+0x130/+0x16C/+0x10`):
    D10R rollback, D18 pre-write, and D19 post-write ALL carry DFG
    `0x007FFF00/0x007FFF00`, checksum `0x32` — NOT stock `0x001FFF00/0xF2`.

## Observed results

1. D19 SPI write/readback/parse claims: all PASS, independently reproduced.
   Single-variable claim (D19 = D10R + one ReadyToBoot write
   `0x0900C830 <- 0x00FFFFFB`): PASS at the decompressed-FV layer.
   Cold-boot discriminator (mode1 SSH up, `alive=False`, Q3 `0x2A` timeout):
   NOT re-observed by root in this audit (prior session hardware evidence;
   accepted as recorded, class hardware-verified-by-record).
2. D-substrate confound (new, observed-bytes): the whole D-ladder baseline
   (D10R and everything derived from it) already carries the mutated APCB DFG
   `0x007FFF00`. D8/D9R/D10R/D13-D19 boot to Linux with it, which DISPROVES
   the 2026-09-11 verdict "APCB DFG is boot-unsafe" (that verdict rested on
   the pre-wiring-fix no-video series, later ruled non-discriminating).
3. Consequence for attribution: D17/D19 wedge verdicts ("C234 alone / C830
   alone wedges SMU at ReadyToBoot") stand as single-variable results ON a
   DFG-mutated substrate. The DFG grant (lock 2 of the two-lock theory) was
   therefore PRESENT in every D-wedge test — the wedge is a transport/context
   effect (unpowered island at ReadyToBoot), not a missing-grant effect.
4. G6 breach: D11R/D12/D13/D14 are 4+ same-class failures (DXE-time gasket ->
   SMU dead) before any method-class change; D15-D19 continued the class to
   9 flashes for ~3 bits of elimination. The breaker should have fired after
   D14 at the latest.
5. Flash count: 15 D-series programmer write cycles on 2026-09-12
   (d5..d19 evidence dirs) plus ~8 earlier cycles (APCB-only, D3-B2,
   policy-only, E1, stock restore, APCB restore, 2x D3-B2 retest, D3-A
   rollback) in ~30 h.

## Memory corrections written after this intent (G7)

- `memory/firmware-audit.md`: appended correction section (see file tail).
- `docs/research/2026-09-12-unlock-paths-map.md`: P3.2 status corrected.
- `memory/project-state.md`: board-state line (D19 in chip, D10R rollback needed).

## Remaining uncertainty

- C834-only control: unbuilt/unrun; recommended AGAINST (no actionable bit).
- Whether the DFG-mutated substrate masks any additional wedge variable:
  unknown, but D10R boots + unlocks cleanly, so substrate is a valid control
  for the gasket-wedge series.
- Board currently holds the SMU-dead D19 image; one recovery flash to D10R
  is outstanding, then a flash moratorium is proposed.
