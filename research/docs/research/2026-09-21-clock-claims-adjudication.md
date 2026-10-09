# Clock-claims adjudication: `AmdFabricAriPei` `0x25D3`/`0x266F`

## Conclusion

The local PI headers and the exact CLV disassembly resolve the main contradiction:

1. `0x25D3` is an IDT-cached PEI Services Table Pointer lookup matching the local EDK II `PeiServicesTablePointerLibIdt` implementation. Calling the selected edge a private AGESA dispatch is an over-description. The binary still uses an indirect call, but the interface at `0x2685` is the standard `EFI_PEI_SERVICES.CreateHob` slot (`+0x34`), not an unidentified private method.
2. The HOB created at `0x26D8` has `Type = 0x2`, which PI defines as `EFI_HOB_TYPE_MEMORY_ALLOCATION`. `EFI_HOB_TYPE_RESOURCE_DESCRIPTOR` is `0x3`, not `0x2`. The older “Type-2 resource descriptor” wording is wrong. The observed `Length = 0x30` and subsequent module-specific stores should not be promoted to a complete standard memory-allocation-HOB semantic mapping without runtime state.
3. The no-immediate result is bounded: this module/edge contains no direct `push 0x1204` and no clock/divider operand in the selected window. It does **not** prove that there are no indirect, computed, later-phase, ABL1/APOB, SMU, or hardware consumers. ABL1/APOB/SMU handoff remains an open candidate boundary, not an observed handoff or a proven absence.
4. The prior direct-caller wording also needs one narrow correction: the `push esi` at `0x26D5` is a saved-register push, not a third argument to `0x266F`; `0x26D6`/`0x26D8` provide the wrapper's `0x30`/`0x2` arguments. This does not change the Type-2 classification.

Evidence class: `observed-bytes` + `static-analysis` + `external-primary` (local pinned EDK II source). No firmware execution, HOB capture, hardware, ROM, or network test was performed.

## Exact inputs and provenance

| Input                                                                                                 | SHA-256 / identity                                                 |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin`               | `c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78` |
| `evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.instructions.json` | `77b1d4be4393fbbf920847398ae5667c42b3841066d40c2aaace1b49036c81e1` |
| `evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442-0.asm`             | `9c4744e1129052c965828694995bc60b250ce4bdb66d858584d090ea092b9f95` |
| Local EDK II tree                                                                                     | commit `04679c85b43cd11bd076a9196b77864fde2091b7`                  |
| `MdePkg/Include/Pi/PiHob.h`                                                                           | `b113f174f2bb0faddf810218a0ca5e9399a50e2432eb622b0e14fe56a2b31bd4` |
| `MdePkg/Include/Pi/PiPeiCis.h`                                                                        | `10ce3dc7d1261432acf03fe6380879bf4ecb45f4b9cbb787b0988e23722fe5ef` |
| `MdePkg/Include/Uefi/UefiMultiPhase.h`                                                                | `d4ca140abf49811bcad80bf9274d65278fe46b7d9ee51cb5c7cb7f590e938550` |
| `MdePkg/Library/PeiServicesTablePointerLibIdt/PeiServicesTablePointer.c`                              | `b35f3883974602a153d068a3dbfaa43bcf768b85c934e6136770f72bcb0a42f3` |

The pinned report that used the “AGESA internal” wording is retained unchanged at
`docs/research/2026-09-21-luna-token1204-provider-object-boundary.md`. The retained
machine result with the Type-2 naming error is likewise unchanged at
`evidence/firmware-audit/20260921-token1204-provider-boundary/token1204-provider-boundary-result.json`.
This adjudication does not rewrite either artifact.

## Direct byte and header adjudication

### `0x25D3` and `0x266F`

The exact bytes are:

```text
25D3: 0F 01 08                 sidtd  [eax]
25E5: 8B 45 F6                 mov    eax,DWORD PTR [ebp-0xA]   ; IDTR.Base
25E8: 8B 40 FC                 mov    eax,DWORD PTR [eax-0x4]
2673: E8 5B FF FF FF           call   0x25D3
2678: 8B 08                    mov    ecx,DWORD PTR [eax]
2685: FF 51 34                 call   DWORD PTR [ecx+0x34]
```

The local `PeiServicesTablePointerLibIdt/PeiServicesTablePointer.c` has the same
interface-level operation: `AsmReadIdtr (&Idtr)`, read `*(UINTN *)(Idtr.Base -
sizeof (UINTN))`, and return the cached `CONST EFI_PEI_SERVICES **`. The local
`PiPeiCis.h` table declares `GetHobList` immediately followed by `CreateHob`;
`UefiMultiPhase.h` defines `EFI_TABLE_HEADER` as one `UINT64` and four `UINT32`
fields (`0x18` bytes). On this IA-32 PEIM, six 4-byte service slots precede
`GetHobList`, placing `CreateHob` at `0x18 + 6*4 + 4 = 0x34`.
The local declaration gives `CreateHob(PeiServices, UINT16 Type, UINT16 Length,
VOID **Hob)`.

This resolves the function/interface identity at static level. It does not observe
the live pointer stored before IDT, the runtime PEI table contents, or the service's
return status. “Standard EDK II PI PEI service dispatch through an IDT-cached PEI
Services pointer” is therefore the supported wording; “private AGESA dispatch” is
not.

### HOB type

At `0x269C`, the parser path pushes `0x4` before calling `0x266F`; at `0x26D6` and
`0x26D8` it pushes `0x30` and `0x2` respectively:

```text
2698: 8D 47 18                 lea    eax,[edi+0x18]
269B: 50                       push   eax
269C: 6A 04                    push   0x4
269E: E8 CC FF FF FF           call   0x266F

26D5: 56                       push   esi       ; saved register, not a 3rd 0x266F argument
26D6: 6A 30                    push   0x30
26D8: 6A 02                    push   0x2
26DA: E8 90 FF FF FF           call   0x266F
```

The local PI constants are decisive:

```c
#define EFI_HOB_TYPE_MEMORY_ALLOCATION    0x0002
#define EFI_HOB_TYPE_RESOURCE_DESCRIPTOR  0x0003
#define EFI_HOB_TYPE_GUID_EXTENSION       0x0004
```

Therefore the `0x26D8` call requests a Type-2 **Memory Allocation** HOB with a
`0x30` length argument. Type 3 is the Resource Descriptor HOB and must not be used
as the name for this call. The Type-4 call is a GUID Extension HOB by the same
header. Stores at `0x26E7..0x2720` align with the local Type-2 allocation layout:
zero Name GUID at `+0x08..+0x17`, Base at `+0x18/+0x1C`, Length at `+0x20/+0x24`,
`MemoryType=0xA` at `+0x28`, and zero Reserved at `+0x2C`. The generic header (8
bytes) plus allocation fields (16+8+8+4+4 bytes) totals `0x30`, matching the
requested length. This identifies the static construction shape; actual runtime
HOB contents and downstream use remain uncaptured.

### No-immediate boundary

The direct test found no `68 04 12 00 00` (`push 0x1204`) in the complete
`AmdFabricAriPei` body and no direct `0x1204` or clock/divider operand in the
`0x25D3..0x26DA` provider/HOB window. This supports only:

> The selected standard PEI HOB edge is not a direct immediate-token `0x1204`
> requester or a byte-backed clock actuator in this bounded view.

It does not support any of these stronger claims:

- no consumer of `0x1204` exists anywhere in firmware;
- no computed/indirect caller can reach the provider;
- the NVTB/HOB reader is the terminal point of the dataflow;
- an ABL1/APOB/SMU handoff was observed;
- physical clocks or synchronization are absent or present.

The retained `AmdFabricAriPei` reader evidence positively identifies direct lookup
requests for `0x10FF` and `0x1104`; it does not close the `0x1204` downstream edge.
The next discriminating input is a concrete reader/consumer of the GUID-HOB/NVTB
payload (or a decoded ABL1/APOB/SMU interface), not another literal scan of this
same provider window.

## Adjudication table

| Existing claim                                                                           | Decision                                            | Correct wording                                                                                                                       |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `0x25D3` is an AGESA/private execution-context dispatch                                  | **Corrected**                                       | IDT-cached `PeiServicesTablePointerLibIdt` pattern; runtime table contents remain unobserved.                                         |
| `0x2685 [ECX+0x34]` is standard `PeiServices->CreateHob`                                 | **Supported statically**                            | PI table order and `EFI_PEI_CREATE_HOB` declaration match `+0x34`; no runtime invocation claim.                                       |
| Type `0x2` is a Resource Descriptor HOB                                                  | **Wrong**                                           | Type `0x2` is `EFI_HOB_TYPE_MEMORY_ALLOCATION`; Resource Descriptor is `0x3`.                                                         |
| `0x26D5` passes `ESI` as a third argument / is an EDK II `BuildMemoryAllocationHob` call | **Wrong stack interpretation / helper attribution** | `push esi` saves ESI; wrapper arguments are Type `0x2` and Length `0x30`; local code directly calls `CreateHob` then fills the block. |
| No immediate `0x1204` proves no consumer / proves ABL1 handoff                           | **Unsupported overclaim**                           | Bounded negative only; downstream consumer and handoff remain unresolved.                                                             |

## Direct command and literal output

The following read-only command checked the exact body, disassembly, PI constants,
PEI service signature/order, and IDT library source without creating or changing an
evidence file:

```text
python3 -B - <<'PY'
from pathlib import Path
import hashlib,sys
root=Path('/home/OWNER/orca/projects/bc250')
asm=(root/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442-0.asm').read_text()
fab=(root/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin').read_bytes()
pi=(root/'archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/edk2/MdePkg/Include/Pi/PiHob.h').read_text()
cis=(root/'archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/edk2/MdePkg/Include/Pi/PiPeiCis.h').read_text()
idt=(root/'archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/edk2/MdePkg/Library/PeiServicesTablePointerLibIdt/PeiServicesTablePointer.c').read_text()
table=(root/'archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/edk2/MdePkg/Include/Uefi/UefiMultiPhase.h').read_text()
checks=[]
def ck(name,ok,detail): checks.append((name,ok,detail))
def line(addr,frag): return any(addr+':' in x and frag in x for x in asm.splitlines())
ck('fabric_sha256',hashlib.sha256(fab).hexdigest()=='c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78',hashlib.sha256(fab).hexdigest())
ck('sidt',line('25e2','0f 01 08') and line('25e2','sidtd'),'25e2 0f 01 08 sidtd')
ck('idtr_base_minus_4',line('25e8','8b 40 fc') and line('25e8','[eax-0x4]'),'25e8 load [IDTR.Base-4]')
ck('createhob_slot_34',line('2685','ff 51 34') and line('2685','[ecx+0x34]'),'0x2685 [ECX+0x34]')
ck('guid_type4',line('269c','6a 04'),'0x269C push 4')
ck('type2_length30',line('26d6','6a 30') and line('26d8','6a 02'),'0x26D6 length 0x30; 0x26D8 type 2')
ck('no_push_1204',b'\x68\x04\x12\x00\x00' not in fab,'whole AmdFabricAriPei body')
ck('pi_type2_memory','EFI_HOB_TYPE_MEMORY_ALLOCATION    0x0002' in pi,'PiHob.h')
ck('pi_type3_resource','EFI_HOB_TYPE_RESOURCE_DESCRIPTOR  0x0003' in pi,'PiHob.h')
ck('pi_createhob_signature','EFI_PEI_CREATE_HOB' in cis and 'IN UINT16                            Type' in cis and 'IN UINT16                            Length' in cis,'PiPeiCis.h')
ck('pi_slot_order','EFI_PEI_GET_HOB_LIST              GetHobList;\n  EFI_PEI_CREATE_HOB                CreateHob;' in cis,'PiPeiCis.h')
header_fields=['UINT64    Signature;','UINT32    Revision;','UINT32    HeaderSize;','UINT32    CRC32;','UINT32    Reserved;']
ck('createhob_slot_offset',all(x in table for x in header_fields) and (8+4*4+6*4+4)==0x34,'UefiMultiPhase.h header + six preceding IA-32 service slots + GetHobList slot')
allocation_fields=['EFI_GUID                Name;','EFI_PHYSICAL_ADDRESS    MemoryBaseAddress;','UINT64                  MemoryLength;','EFI_MEMORY_TYPE         MemoryType;','UINT8                   Reserved[4];','EFI_HOB_GENERIC_HEADER              Header;','EFI_HOB_MEMORY_ALLOCATION_HEADER    AllocDescriptor;']
ck('type2_allocation_layout',all(x in pi for x in allocation_fields) and (8+16+8+8+4+4)==0x30,'PiHob.h Type-2 fields and size match the requested 0x30-byte HOB')
ck('idt_source_standard','AsmReadIdtr (&Idtr);' in idt and 'Idtr.Base - sizeof (UINTN)' in idt and 'GetPeiServicesTablePointer' in idt,'PeiServicesTablePointerLibIdt')
passed=sum(ok for _,ok,_ in checks)
for name,ok,detail in checks: print(f'{name}: {"PASS" if ok else "FAIL"} ({detail})')
print(f'SUMMARY: {passed}/{len(checks)} PASS; exit={0 if passed==len(checks) else 1}')
sys.exit(0 if passed==len(checks) else 1)
PY
```

Observed output:

```text
fabric_sha256: PASS (c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78)
sidt: PASS (25e2 0f 01 08 sidtd)
idtr_base_minus_4: PASS (25e8 load [IDTR.Base-4])
createhob_slot_34: PASS (0x2685 [ECX+0x34])
guid_type4: PASS (0x269C push 4)
type2_length30: PASS (0x26D6 length 0x30; 0x26D8 type 2)
no_push_1204: PASS (whole AmdFabricAriPei body)
pi_type2_memory: PASS (PiHob.h)
pi_type3_resource: PASS (PiHob.h)
pi_createhob_signature: PASS (PiPeiCis.h)
pi_slot_order: PASS (PiPeiCis.h)
createhob_slot_offset: PASS (UefiMultiPhase.h header + six preceding IA-32 service slots + GetHobList slot)
type2_allocation_layout: PASS (PiHob.h Type-2 fields and size match the requested 0x30-byte HOB)
idt_source_standard: PASS (PeiServicesTablePointerLibIdt)
SUMMARY: 14/14 PASS; exit=0
```

## Scope and unrun checks

- **Passed:** exact module hash, byte-backed `SIDT`/IDTR-base-minus-four path,
  `CreateHob` slot `+0x34`, Type-4 and Type-2 callsite pushes, local PI constants,
  PEI service declaration/order, and local IDT library source comparison.
- **Unrun:** firmware execution, PEI dispatch tracing, runtime HOB dump, ABL1/APOB
  payload execution, SMU mailbox observation, physical clock measurement, and
  hardware verification.
- **Unchanged:** no ROM, candidate, firmware, board, source, shared report, shared
  memory, network, or global configuration state was modified.
