# Voltage trace: serializer identified, rail encoding unresolved

Scope: exact clv modules retained in 20260919-clock-trace. No hardware access, candidate creation or changed input images. User ceiling: SoC 1.15 V; not an established device rating. Engineering-board status does not establish other voltage, current or thermal ceilings.

## Observed instructions

| Module           | Field  | Load RVA | File offset | Record | Width |
| ---------------- | ------ | -------- | ----------- | ------ | ----- |
| CbsBasePei       | +0x6E5 | 0xE3E4   | 0xE254      | 0x1363 | u8    |
| CbsBasePei       | +0x6E6 | 0xE419   | 0xE289      | 0x1364 | u32   |
| AmdNbioSmuV10Pei | +0x6E5 | 0x10464  | 0x102D4     | 0x1363 | u8    |
| AmdNbioSmuV10Pei | +0x6E6 | 0x10499  | 0x10309     | 0x1364 | u32   |

Both sites copy the four-byte voltage field unchanged to record+3 and advance the destination by seven bytes; no voltage conversion occurs in these copies. The low flag bits become 2 for the u32 record. This independently corroborates width, not units, sign, target rail or absolute/offset interpretation.

CbsBasePei serializer starts at RVA 0x36F0, ends at 0x11873. It validates caller-provided size against helper(0x11880)+0x20, writes literal 0x564E4924 (little-endian `$INV`) at output+0 and version 1 at +4, starts records at +0x20, terminates with u16 0xFFFF. Direct call at RVA 0x36DE forwards setup pointer and output descriptor. This identifies the output container more precisely than the previous generic record description. It is NOT a decoded SMU voltage command. Indirect caller and eventual $INV consumer remain unresolved.

Evidence: evidence/firmware-audit/20260919-voltage-trace/serialization.json contains four instruction windows and module hashes. CbsBasePei hash 6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77; AmdNbioSmuV10Pei 905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80.

## PEI lifetime continuation

[INV buffer lifetime](2026-09-19-inv-buffer-lifetime.md) resolves the previously missing caller/output edge: AmdFabricAriPei requests FFFFFFFE using sign-extended imm8 `6A FE`; CbsBasePei fills a GUID-HOB heap payload (handle NVTB, INV at HOB+28). Fabric's generic reader is positively located, but its two identified lookup callers request 10FF and1104—not1364. Serializer reachability is therefore established conditionally in the stock compiled chain; a voltage-specific lookup/actuator and rail/units remain unresolved. Earlier unresolved-caller wording above is historical, superseded by that bounded trace, not by a hardware capture.

## Acceptance boundary

PASS: four raw instruction checks, two independently located serialization copies, width and container header recognition. Static evidence only. Final rail/units and 1.15 V encoding INCONCLUSIVE; live voltage and clock synchronization UNRUN. No final BIOS delivered. A synthesized equal-number profile would not satisfy the user's requested actual 1:1:1 or safe optimal performance.

Next unresolved trace target: a compiled requester of record 0x1364, followed through its returned value to physical rail selection and numerical conversion. The generic caller/output handoff is already resolved by the PEI lifetime continuation above and should not be rediscovered. A physical maximum must be backed by board-specific electrical/thermal evidence and tested under load; no fabricated 'upper safe' settings for other rails or limits.
