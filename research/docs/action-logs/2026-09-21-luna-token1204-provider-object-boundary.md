# Native token 0x1204 provider-object boundary — action log

## Intent

- Timestamp: 2026-09-21T12:23:42+05:00 (Asia/Almaty)
- Actor: Luna, bounded static reverse-engineering follow-through
- Target: new report `docs/research/2026-09-21-luna-token1204-provider-object-boundary.md`; exact pinned CLV `AmdFabricAriPei` body/disassembly at the post-reader provider edge.
- Procedure: read `memory/oc-recheck.md` to EOF and the current native `$INV 0x1204` HOB boundary report; inspect one unexhausted edge only: `AmdFabricAriPei 0x266F -> 0x25D3 -> [ECX+0x34]`. Verify the `SIDT`-derived provider-object source, exact caller argument construction at `0x2698`/`0x26D5`, and whether any token `0x1204`/clock/divider operand is byte-backed in this edge. Run an inline hash-checked verifier. No serializer scan, ROM write, board access, HOB execution, or hardware action.
- Rationale: determine whether this first post-NVTB/HOB provider edge can discriminate downstream meaning for native UclkDiv1M0 (`$INV 0x1204`) while retaining memory setting 1800 unchanged.
- Expected effect: either a concrete token-to-actuator edge or an exact reason the selected provider boundary is non-discriminating, with the missing runtime operand named.
- Rollback: remove only this new report and this action log.

## Observed result

Timestamp: 2026-09-21T13:10:00+05:00 (Asia/Almaty).

Command:

```text
python3 -B evidence/firmware-audit/20260921-token1204-provider-object-boundary/verify_provider_object_boundary.py
```

Observed exit `0`, `26/26 PASS`, stderr empty.

- Identified `0x25D3` as `GetPeiServicesTablePointer` via `sidtd [eax]` -> `IDTR.Base` -> `[Base-4]` (`PeiServicesTablePointerLibIdt`).
- Identified `0x266F` as `PeiServicesCreateHob` invoking `PeiServices->CreateHob` at vtable offset `0x34`.
- Identified callers `0x2698` (`BuildGuidHob`) and `0x26D5` (`BuildMemoryAllocationHob`).
- Bounded negative: zero occurrences of literal token `0x1204` (`\x04\x12`) or clock/divider operands in functions `0x25D3`, `0x266F`, `0x2698`, or `0x26D5`.
- Conclusion: edge is generic PEI HOB infrastructure, not a UCLK actuator. Token `0x1204` consumption is NOT ESTABLISHED at this boundary.

Report: `docs/research/2026-09-21-luna-token1204-provider-object-boundary.md`.
Evidence: `evidence/firmware-audit/20260921-token1204-provider-object-boundary/provider-object-result.json`.

### Completed Execution (2026-09-21T13:10:00+05:00)

- Command: `python3 evidence/firmware-audit/20260921-token1204-provider-boundary/verify_provider_object_boundary.py`
- Exit status: 0
- Output: `Status: PASS, 8/8 checks passed.`
- Report: `docs/research/2026-09-21-luna-token1204-provider-object-boundary.md`
- Evidence: `evidence/firmware-audit/20260921-token1204-provider-boundary/token1204-provider-boundary-result.json` (hash check `c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78`)
- Finding: `0x25D3` is `PeiServicesTablePointerLibIdt` using `sidtd` to find `[IDT_BASE - 4]`. `0x266F` calls `CreateHob` via `(*PeiServices)->CreateHob` (`[ECX+0x34]`). Call sites `0x2698` (GUID HOB) and `0x26D5` (Resource Descriptor HOB) are generic EDK II HOB plumbing, not token 0x1204 consumers or clock actuators.

## Observed Result — 2026-09-21T13:30:00+05:00

- Execution: `python3 -B evidence/firmware-audit/20260921-luna-token1204-provider-object-boundary/verify_token1204_provider_boundary.py`
- Result: 45/45 checks PASSED, exit 0, stderr empty.
- Findings:
  1. Provider object lookup `0x25D3` retrieves pointer from `[IDTR.Base - 4]` via `SIDT`, not via PEI `LocatePpi` or static GUID table.
  2. Wrapper `0x266F` invokes method `[ECX+0x34]` on this object.
  3. Direct callers `0x2698` (arg 4) and `0x26D5` (args 2, 0x30) do not pass or reference token `0x1204`.
  4. AmdFabricAriPei contains zero occurrences of `push 0x1204` (`68 04 12 00 00`).
  5. The provider edge `0x266F -> 0x25D3 -> [ECX+0x34]` is non-discriminating for token `0x1204`. Downstream UclkDiv1M0 consumption remains at the NVTB/HOB handoff to ABL1/APOB/SMU.
- Artifacts:
  - Report: `docs/research/2026-09-21-luna-token1204-provider-object-boundary.md`
  - Verifier: `evidence/firmware-audit/20260921-luna-token1204-provider-object-boundary/verify_token1204_provider_boundary.py`
  - Result JSON: `evidence/firmware-audit/20260921-luna-token1204-provider-object-boundary/token1204-provider-boundary-result.json`
  - Manifest: `evidence/firmware-audit/20260921-luna-token1204-provider-object-boundary/SHA256SUMS.final`
