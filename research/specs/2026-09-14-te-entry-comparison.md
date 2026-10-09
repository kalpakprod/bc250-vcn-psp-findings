# BC-250 versus AMD 4700S TE entry comparison

## Title and scope

Compare the entry-path control flow of `AmdNbioGfxARIPei` from the exact BC-250 baseline and the imported AMD 4700S C0A donor. This is offline static analysis only.

## Planning anchor

- BC-250 module: `evidence/programmer/reads/20260911/firmware-audit/read-a-extract/modules/0193_AmdNbioGfxARIPei_te.bin`, SHA-256 `63413be2ac290e584bbbeeba5eb573a94b66b9624c4e0ecbea145ded655245b8`.
- 4700S module: `evidence/firmware-audit/20260914-4700s/extracted/modules/0200_AmdNbioGfxARIPei_te.bin`, SHA-256 `73915b610491853db8bf81622f4acfd17e125959e5ab324e55e3a362489bd156`.
- Both are IA32 TE images with entry RVA `0x240`; stripped deltas differ (`0x198` versus `0x1A0`).

## Connected logic

- The compact 4700S entry was already observed to consume `AMD_MEMORY_INFO_HOB` and derive UMA bounds.
- BC-250 has a much larger module and is known to build an internal configuration structure and `$VNI` data, but the matching entry path has not been directly reconciled with the donor.
- Existing `recon/disasm_x86_te.py` linearly disassembles raw file bytes from offset `0x28` with zero-based addresses. It is useful for byte triage but is insufficient for entrypoint semantics because TE virtual addresses require `raw_pointer - (StrippedSize - 40)` mapping.

## Use cases

1. Determine whether the donor and BC-250 entries share a recognizable initialization skeleton.
2. Identify donor-only or BC-250-only early calls before considering any transplant.
3. Reject foreign-module transplantation if control flow or data contracts are not compatible.

## Implementation checklist

- [x] Map TE sections to their virtual addresses with bounds checks.
- [x] Disassemble from the true entry RVA using pypcode IA32.
- [x] Walk bounded direct-call targets without interpreting indirect calls as resolved.
- [x] Preserve exact hashes, header fields, entry traces, and string references.
- [x] Compare observed calls/data references and state unknown semantics explicitly.

## Open questions

- Which BC-250 entry calls correspond structurally to the compact donor entry helpers?
- Does either entry directly program VCN/NBIF/DF state, or only assemble UMA/config data?
- Are apparent donor omissions real feature differences or only a more compact AGESA implementation?

## Decision log

- 2026-09-14: use virtual section mapping rather than the retained raw linear TE disassembler for semantic comparisons.
- 2026-09-14: do not transplant the donor PEIM based on module name or size alone.
- 2026-09-14: both reachable entry CFGs have an identical 380-instruction mnemonic skeleton and identical diagnostic-string sequence; reject the entry function as a donor-only VCN unlock lead.
