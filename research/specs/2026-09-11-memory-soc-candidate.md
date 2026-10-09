# BC-250 Separate Memory and SoC-Voltage Candidate Specification

## Scope

This specification defines two independent offline candidate tracks based on the matching CH347T baseline. It does not authorize flashing, register writes, JTAG target-memory writes, or board experiments.

- Baseline: `evidence/programmer/reads/20260911/read-a.bin` and `read-b.bin`
- Baseline SHA-256: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`
- Baseline size: `0x1000000` (16 MiB)
- Direct fresh NVAR: `AmdSetup` record at relative `0x4BB`, body `0x8B5` bytes
- Baseline body SHA-256: `6f266c3c78a544d73eae5cea465756dd73e343fe16e2725d2300d08ba176d055`

## Planning anchor

The current AmdSetup body exposes the following static fields:

| Field | AmdSetup offset | Type | Current value | Static interpretation |
|---|---:|---|---:|---|
| `MemoryClockSpeed` | `0x316` | `u8` | `0xFF` | IFR `Auto`; enumerated labels include 1330–2000 MHz |
| `UclkDiv1M0` | `0x330` | `u8` | `0xFF` | IFR `Auto`; `Enabled=1`; 1:1 meaning is inferred from historical notes |
| `FclkDpm` | `0x6A3` | `u8` | `0x0F` | IFR `Auto`; not a frequency value |
| `DfClockOverrideControl` | `0x703` | `u8` | `0xFF` | IFR `Auto`; separate control |
| `DfClockOvrd` | `0x704` | `u16` | `1000` | IFR range `0..2000`; physical consumer/unit requires corroboration |
| `VddcrVddOffsetControl` | `0x6E5` | `u8` | `0` | IFR `Auto` vs `Manual=1` |
| `VddcrVddOffset` | `0x6E6` | `u32` | `0` | IFR numeric `u32`; physical unit/sign/consumer unknown |
| `VddcrGfxOffsetControl` | `0x6EA` | `u8` | `0` | IFR `Auto` vs `Manual=1` |
| `VddcrGfxOffset` | `0x6EB` | `u32` | `0` | IFR numeric `u32`; physical unit/sign/consumer unknown |

The current APCB also contains `DFG` (`gid 0x1703`) and `MEMG` (`gid 0x1704`) groups. The IPDS descriptor has two `UMC` instances. These are observed structures, not a proven mapping from each Setup byte to memory training behavior.

Evidence maps:

- `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`
- `evidence/firmware-audit/vcn-evidence-map.json`
- `evidence/programmer/reads/20260911/manifest.json`

## Connected existing logic

- `CbsSetupDxe`, `CbsBasePei`, `AmdNbioBaseARIPei`, `AmdNbioGfxARIPei`, and `AmdNbioPcieARIPei` contain static Setup/DF literals. Literal presence does not establish direction or consumer semantics.
- `AmdMemAm4Pei` and `AmdMemoryHobInfoPeim` are present in the extracted PEI set. The current Rizin triage finds `34` functions in `AmdMemAm4Pei`; its targeted scalar scan has no matching field literals. This is not proof that the fields are unused.
- `AmdNbioSmuV10Pei` and `AmdNbioSmuV10Dxe` are present. The latter contains Q2 mailbox address literals in the current static scan. Exact message/field semantics remain closed or unresolved.
- Historical OC profiles show coherent-looking deltas, but they are historical static artifacts and are rejected as current flash sources. Their voltage comments are claims, not unit proof.

## Use cases

### MEM-UC1: offline memory-clock candidate

A candidate may change only a defined memory-clock field or one tightly justified synchronization control. It must not include a SoC voltage change in the same first variant. The candidate is a hypothesis for static and later controlled testing, not a stability claim.

### SOC-UC1: offline SoC-voltage candidate

No binary is generated until the control/value encoding, units, sign, allowed range, SMU consumer, training dependency, and live rail telemetry are established. A historical `+35`, `+80`, or `+100` comment is insufficient.

### MEM-UC2/SOC-UC2: validation

Every eventual candidate must preserve signed PSP/`$PS1`, BHD, FV/FFS, unrelated NVAR variables, and the other track's fields. It needs source/output hashes, exact changed ranges, parser checks, an independent byte diff, and independent review.

## Implementation checklist

### Static mapping gate

- [x] Hash and preserve two matching fresh reads.
- [x] Parse current NVAR and `AmdSetup` directly from a fresh read.
- [x] Record IFR field types, options, and control/value separation.
- [x] Record APCB `MEMG`/`DFG` group locations and hashes.
- [ ] Obtain read-only CutterMCP function-context results for the pending PEI/DXE consumers.
- [ ] Trace a field from Setup/NVAR through PEI/SMU or prove the trace unavailable.
- [ ] Establish field units and whether values are defaults, requests, or applied settings.
- [ ] Establish memory training dependencies and failure observables.

### Memory candidate gate

- [ ] Select one variable and one changed value from a documented source, not a guess.
- [ ] Define expected boot/training/clock signal and stop condition.
- [ ] Generate a new image from a matching fresh read with an overwrite refusal.
- [ ] Validate NVAR and all outer firmware structures.
- [ ] Independent review of diff and recovery plan.

### SoC-voltage candidate gate

- [ ] Identify whether the field is offset, VID code, or another encoding.
- [ ] Prove units and sign using source, disassembly, or a known-good pair.
- [ ] Prove control-byte behavior and allowable range.
- [ ] Map the SMU/PMFW consumer and training interaction.
- [ ] Define read-only rail telemetry and thermal/current limits.
- [ ] Only then generate a separate candidate; no automatic or combined candidate.

### Hardware gate

- [ ] Complete recovery dump and matching-read checks (passed for the current baseline).
- [ ] Verify exact board revision, chip marking, orientation, and recovery method.
- [ ] Obtain independent review.
- [ ] Obtain exact per-image/per-board approval before any write. Required form:
  `Подтверждаю запись файла <exact path> SHA-256: <exact hash> на плату <identifier>`
- [ ] Post-write readback and cold-boot validation remain separate gates.

## Open questions

### Blocking

- Which PEI/DXE function reads each AmdSetup field, and which SMU message consumes it?
- Does `UclkDiv1M0=1` actually change UMC behavior on this BC-250 build, or is it ignored/overridden?
- Is `DfClockOvrd` in MHz, and is it applied by PMFW or overwritten during initialization?
- Is `VddcrVddOffset` a signed mV offset, a VID encoding, or another unit?
- Which memory-training errors and read-only telemetry distinguish a failed setting from a fallback to Auto?

### Non-blocking

- Whether current board silicon tolerates a particular memory setting.
- Which Linux driver version exposes reliable UCLK/FCLK/SoC metrics after a stock boot.

## Decisions

- Keep memory and SoC-voltage candidates separate.
- Do not guess or recommend a voltage value.
- Treat historical OC profiles and comments as static references only.
- Treat a parser-valid candidate as unverified until review and any authorized hardware test.
- Keep the existing APCB DFG VCN candidate separate from both tracks.

## Current status

- APCB-only VCN candidate: built and statically verified at `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`.
- Memory candidate: not built; blocked on consumer/training mapping.
- SoC-voltage candidate: not built; blocked on units/encoding/consumer/training/telemetry.
- No firmware write or hardware mutation has occurred.


## Status update — one-field memory candidate (2026-09-11T07:15:32.422652+00:00)

- Offline candidate built: `candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin`, SHA-256 `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee`.
- Transform: only `AmdSetup+0x316` / absolute `0x7E5`, `0xFF` (Auto) -> `0x23` (IFR-labelled 1750MHz). No UCLK/FCLK/voltage/timing/APCB/PSP/`$PS1`/BHD/FV field changed.
- Validation reports: `evidence/candidates/BC250_MemoryClock_1750_only_v001/nvar-primary.json` SHA-256 `06710664aa71770881221401da74c1fa1ce224e8eaf1e5940176490a69a927f5` and `firmware-audit.json` SHA-256 `83b82cd738bc7d668ac90f568066ef451ffc2075af36d2b2fde5bc4e951dcae8`; build manifest SHA-256 `f9c72180e2d67c0eef7c3128456dde87478b89d5b1a06d20f76e63539db4f61f`.
- Static candidate checks pass. Runtime memory training, live MCLK/UCLK/FCLK, stability, and bootability are unrun. Independent review is pending.
- SoC-voltage candidate remains explicitly not built; no voltage value was selected or recommended.


## Independent review status (2026-09-11T07:22:15.916133+00:00)

- Gemini review for the memory candidate: `evidence/candidates/BC250_MemoryClock_1750_only_v001/independent-review-gemini.md`, SHA-256 `47a9b6a7be4628861ac04031e959a6ea76b1b67bfe7f724c8ba0b66b330123fb`. Root rechecked the artifact.
- Review PASS covers exact one-byte diff, NVAR/full-parser reports, unchanged selected fields, and read-only scope. Runtime/training/boot/stability checks remain unrun.
- APCB VCN candidate has a separate independent review; neither candidate is flash-approved.


## Root static review status (2026-09-11T09:42:20.709652+00:00)

- Root review artifact: `evidence/firmware-audit/soc-voltage-static-review-root.md`, SHA-256 `d9cfbaca981c33181b04c7f9bc17aed35192cad4e762763ae25a9809f56a341b`.
- Result: field location/type/control PASS; physical unit/sign/encoding, consumer, training, and live telemetry INCONCLUSIVE/UNRUN. The SoC-voltage candidate remains NOT BUILT.
