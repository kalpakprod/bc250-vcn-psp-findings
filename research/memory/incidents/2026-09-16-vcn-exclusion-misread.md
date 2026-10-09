# G7 correction: VCN must WORK, "разговором" was "разгоном" (overclocking)

Date: 2026-09-16. Source: direct operator statement (chat), disproving root's
speech-to-text interpretation from the 2026-09-16 deep-research request.

## Wrong claim (retracted)
Root interpreted the garbled phrase "собрать новый исключенным блоком ВСИН
с разговором..." as "build a new image with the VCN block EXCLUDED".

## Corrected requirement
- The donor-based target BIOS must have a WORKING VCN block (enable, not exclude).
- The target BIOS must have a WORKING overclocking block ("разгон", not "разговор"):
  memory/GFX clocks, and where provable voltage/power controls.
- Also wanted in the base: FastBoot, a TPM route, and generally a more modern,
  more working BIOS than the current BC250 stock (`dump/2.bin` P3.00-lineage).
- Strategy pivot: take an already-working BIOS from same-chip hardware
  (AMD 4700S, PlayStation 5 lineage, anything Ariel/Oberon-based found in the
  open internet) as the base, then add what BC250 needs; validate by
  flash-and-test loop with recovery.

## Impact
- The 2026-09-16 deep-research synthesis line "reject 4700S/coreboot/OVMF" is
  a worker claim whose rationale was never delivered; the 4700S rejection is
  now explicitly contested by the operator (same Ariel die) and must be
  re-examined with inspected evidence, not assumed.
- VCN-exclusion playbook material from that synthesis is void; VCN-enablement
  remains the objective, consistent with the whole D-candidate/S2-A campaign.
- Standing brief for the re-run: `docs/research/deepresearch-donor-bios-brief.md`,
  triggered by an operator message starting with `/deepresearch`.
