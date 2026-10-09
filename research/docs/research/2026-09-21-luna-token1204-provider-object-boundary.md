# Native `$INV 0x1204` Provider-Object Boundary Analysis

## Scope and Intent

- Artifact: `AmdFabricAriPei` (`c5b99650a442...`) from pinned plain CLV 5.00 (`ea578104...`).
- Objective: evaluate the post-reader indirect provider edge `0x266F -> 0x25D3 -> [ECX+0x34]` to establish whether it consumes or forwards the native UclkDiv1M0 (`$INV 0x1204`) token serialized from `AmdSetup+0x330`.
- Constraint: retain operator request (`Memory Clock Speed = 1800MHz`), evaluate physical 1:1:1 hypothesis statically, offline only, no firmware or hardware writes.

## Observed Disassembly and Dataflow

### 1. Provider Object Acquisition (`0x25D3`)

The provider object pointer is not acquired through PEI Service Table (`LocatePpi`) or static GUID lookup. Instead, it reads the CPU IDTR base:

```x86asm
25D3: 55                      push   ebp
25D4: 8B EC                   mov    ebp, esp
25D6: 83 EC 0C                sub    esp, 0xC
25D9: 8D 45 F4                lea    eax, [ebp-0xC]
25DC: 89 45 FC                mov    DWORD PTR [ebp-0x4], eax
25DF: 8B 45 FC                mov    eax, DWORD PTR [ebp-0x4]
25E2: 0F 01 08                sidtd  [eax]              ; Store IDTR at [ebp-0xC]
25E5: 8B 45 F6                mov    eax, DWORD PTR [ebp-0xA] ; Extract IDTR.Base
25E8: 8B 40 FC                mov    eax, DWORD PTR [eax-0x4] ; Load pointer at [IDTR.Base - 4]
25EB: C9                      leave
25EC: C3                      ret
```

In early AMD PEI/CAR environments, `[IDTR.Base - 4]` is the standard anchor pointing to the execution context / AGESA internal dispatch structure.

### 2. Indirect Method Dispatch (`0x266F`)

The wrapper `0x266F` invokes `0x25D3` to retrieve this execution context pointer, dereferences its vtable at `[EAX]`, and executes method `+0x34`:

```x86asm
266F: 55                      push   ebp
2670: 8B EC                   mov    ebp, esp
2672: 51                      push   ecx
2673: E8 5B FF FF FF          call   0x25D3             ; Acquire execution context
2678: 8B 08                   mov    ecx, DWORD PTR [eax] ; Vtable pointer
267A: 8D 55 FC                lea    edx, [ebp-0x4]     ; Output pointer
267D: 52                      push   edx
267E: FF 75 0C                push   DWORD PTR [ebp+0xC] ; Arg2
2681: FF 75 08                push   DWORD PTR [ebp+0x8] ; Arg1
2684: 50                      push   eax                ; This pointer
2685: FF 51 34                call   DWORD PTR [ecx+0x34] ; Invoke method 0x34
2688: 83 C4 10                add    esp, 0x10
268B: 85 C0                   test   eax, eax
268D: 7D 04                   jge    0x2693
268F: 83 65 FC 00             and    DWORD PTR [ebp-0x4], 0x0
2693: 8B 45 FC                mov    eax, DWORD PTR [ebp-0x4]
2696: C9                      leave
2697: C3                      ret
```

### 3. Direct Caller Audit in `AmdFabricAriPei`

There are two direct callers invoking `0x266F`:

- **Caller 1 (`0x2698..0x269E`)**:
  - Arguments: `arg1 = 4` (selector/size), `arg2 = EDI + 0x18` (output buffer).
  - Post-call action (`0x26A9..0x26C0`): adjusts returned pointer and copies 4 DWORDs (`[ESI+0..0xC]` to `[EAX-0x10..EAX-0x4]`).
  - No token ID or UCLK divider value is passed.
- **Caller 2 (`0x26D5..0x26DA`)**:
  - Arguments: `arg1 = 2` (selector), `arg2 = 0x30` (size), `arg3 = ESI` (buffer).
  - Post-call action (`0x26E7..0x2720`): populates structure fields.
  - No token ID or UCLK divider value is passed.

### 4. Direct Census of Token `0x1204`

- Entire `AmdFabricAriPei` binary lacks any direct push of `0x1204` (`68 04 12 00 00` does not occur).
- Range `[0x25D3, 0x2720]` contains no immediate `0x1204` or clock ratio calculation.

## Findings and Boundary Verdict

1. **Non-discriminating for UclkDiv1M0:**
   The `0x266F -> 0x25D3 -> [ECX+0x34]` provider edge is an AGESA internal service call dispatching through `[IDTR.Base - 4]`. It does not consume or actuate token `0x1204`.
2. **Handoff Boundary Confirmed:**
   Token `0x1204` is serialized by `CbsBasePei` into the NVTB/HOB buffer structure. Inside `AmdFabricAriPei`, the NVTB generic reader parses records, but `AmdFabricAriPei` directly queries only `0x10FF` and `0x1104`. Token `0x1204` is NOT requested directly in this PEIM.
3. **Implication for Downstream Trace:**
   Downstream consumption of `0x1204` occurs outside this direct provider edge (e.g., via ABL1/APOB handoff, indirect table scan, or SMU mailbox).

## Verification Artifacts

- Script: `evidence/firmware-audit/20260921-luna-token1204-provider-object-boundary/verify_token1204_provider_boundary.py`
- Result JSON: `evidence/firmware-audit/20260921-luna-token1204-provider-object-boundary/token1204-provider-boundary-result.json`
- Checks: 45/45 PASSED, exit 0, stderr empty.
