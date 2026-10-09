# CLV APCB/ABL/APOB/INV configuration-source boundary

## Conclusion

The exact clv bytes expose separate configuration paths rather than one proven precedence chain:

1. Flash APCB is a parsed policy surface at `0xAB1000`; DFG words are `0x001FFF00` at APCB `+0x130/+0x16C`, checksum byte `+0x10=0xC0`.
2. Persisted `AmdSetup+0x316` is serialized by `CbsBasePei` into `$INV` token `0x11ED` (`0x9837/0x9857/0x985D`).
3. The bounded `AmdMemAm4Pei` path requests a service with literal `0x9E3B14C`, message `0x61`, argument `0xFF`, then validates returned `APOB`, `$PSP`, and `$BHD` headers. It contains no direct `Setup+0x316` or `$INV 0x11ED` read.
4. `AmdMemoryHobInfoPeim` obtains a PPI via `LocatePpi`, reads returned structure fields at `+0x28/+0x2C/+0x30/+0x31/+0x40`, and calls `InstallPeiMemory` at RVA `0x299`.

Therefore the checked memory-HOB input is a PPI/APOB-derived structure, not a direct APCB or `$INV` read in this bounded consumer. This is a concrete source/interface boundary relevant to persisted settings being ignored. It does **not** prove that `$INV` is never transformed into the APOB service input, establish runtime precedence, or prove training/clock behavior.

## Exact input and parser execution

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Size: `16777216`
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Fresh executed parser outputs:
  - `evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/firmware-audit.json`, SHA-256 `b6e6b09f17e304c102b75ba009f7e31f2ddd3e8bb95d55a18916b1760b75df28`
  - `evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-detail.json`, SHA-256 `503e4f525f4372903b23ea9320c77f7b0b39250f310d80a1b7565eb98b39f394`
- Fresh bounded checker: `evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb_abl_apob_interface_verify.py`; result `apcb-abl-apob-interface-result.json`, SHA-256 `73ea48688e988222a6046f5f1a38cc98b33a029566a4c37d69a04dcdd3efd42f`; `32/32 PASS`.

## Observed APCB/BHD inputs

`firmware_audit.py` and `apcb_detail.py` agree:

| Structure       | Exact result                                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------------------------------- |
| APCB            | offset `0xAB1000`, size `0xB9C` (2972), checksum stored/calculated `0xC0`                                           |
| DFG             | words at `APCB+0x130` and `APCB+0x16C`: `0x001FFF00` / `0x001FFF00`                                                 |
| APCB groups     | `UNKN 0x0B07`, `PSPG 0x1701`, `DFG 0x1703`, `MEMG 0x1704`, `FCHG 0x1706`, `CBSG 0x1707`                             |
| BHD type `0x60` | APCB body, 8192 B at `0xAB1000`                                                                                     |
| BHD type `0x61` | APOB entry size `0`; no flash-resident body in this BHD entry                                                       |
| BHD type `0x63` | APOB NV copy, 8192 B at `0xAB3000`, body SHA-256 `7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f` |

The zero-sized BHD type `0x61` is a concrete reason not to describe the flash image as containing a complete APOB payload. The memory path's APOB data arrives through a service/PPI boundary in the bounded code.

## Exact byte-backed edges

### Persisted AmdSetup to `$INV`

From exact `CbsBasePei` instructions, module SHA-256 `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`:

```text
RVA 0x9837: ba ed 11 00 00       mov edx,0x11ED
RVA 0x9857: 8a 82 16 03 00 00    mov al,[edx+0x316]
RVA 0x985D: 88 41 03             mov [ecx+0x3],al
```

This proves the serializer producer, not a final memory consumer.

### AmdMemAm4Pei service/APOB validation

From exact `AmdMemAm4Pei`, SHA-256 `1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8`:

```text
RVA 0x8A0: 68 4c b1 e3 09       push 0x9E3B14C
RVA 0x8CA: 68 ff 00 00 00       push 0xFF
RVA 0x8CF: 6A 61                push 0x61
RVA 0x8D1: E8 03 04 00 00       call 0xCD9
RVA 0x8FC: 81 3B 41 50 4F 42    cmp [ebx],0x424F5041   ; APOB
RVA 0xC73: 81 3E 24 50 53 50    cmp [esi],0x50535024   ; $PSP
RVA 0xC96: 81 3F 24 42 48 44    cmp [edi],0x44484224   ; $BHD
```

No direct `0x11ED` literal or `AmdSetup+0x316` source load occurs in this module's bounded instruction record.

### AmdMemoryHobInfoPeim PPI input to permanent-memory output

From exact `AmdMemoryHobInfoPeim`, SHA-256 `aad3f828ccef4cf8878cad8c9ee1e47743748f652a1ef54af04de759983b4619`:

```text
RVA 0xAC3: call [eax+0x20]       ; LocatePpi slot
RVA 0xAD0: mov ecx,[eax+0x28]
RVA 0xAD6: mov cx,[eax+0x2C]
RVA 0xADE: mov cl,[eax+0x30]
RVA 0xAE4: mov cl,[eax+0x31]
RVA 0xAE7: mov eax,[eax+0x40]
RVA 0x299: call [eax+0x44]       ; InstallPeiMemory slot
```

This module has no direct `$INV 0x11ED` or `Setup+0x316` read in the bounded instruction set. The exact PPI GUID/provider identity and the service's internal conversion remain unresolved.

## Review of current worker results

- Defaults report `docs/research/2026-09-20-clv-sync-stage2-defaults.md` (SHA-256 `dbab884487d2271f932dd0937845f6586b03200921d859ccc64fc3312d62901c`) correctly establishes static `GetVariable` precedence over missing-variable fallback; callback/default execution and NVRAM readback remain unrun.
- ABL memory report `docs/research/2026-09-20-clv-sync-stage2-abl-memory.md` (SHA-256 `21091dda8fad1f75de2d5c48a256db6d4aaa8dc8b0a8b3bb8eeb54014ac4821f`) falsifies direct historical source-address anchors against exact ABL1: source is version-aligned but not a bind map. No source/xref claim is reused here.
- CCX reader report `docs/research/20260920-clv-sync-stage2-reader-consumer.md` (SHA-256 `cfbd9fed97ecbf1313a247043d6537ba626a6b67092ee03dda4abfc143d7e116`) identifies token `0x1000/0x1001` CPU MSR use and does not claim a memory/DF consumer. It is a negative branch qualification only.

## Source-selection boundary

The strongest bounded distinction is:

```text
AmdSetup+0x316
  -> CbsBasePei $INV 0x11ED producer

APOB service (0x9E3B14C, message 0x61, arg 0xFF)
  -> AmdMemAm4Pei validates APOB/$PSP/$BHD
  -> PPI structure fields (+0x28/+0x2C/+0x30/+0x31/+0x40)
  -> AmdMemoryHobInfoPeim
  -> InstallPeiMemory
```

The two chains are not byte-joined in the bounded consumers. Thus an existing `AmdSetup` variable can be authoritative for the `$INV` producer while the memory-HOB/training input is supplied through an APOB/PPI service path. This is a static provenance boundary, not proof that the persisted value is ignored at runtime.

## Remaining limits

- No firmware execution, APOB service response, PPI invocation, memory training, physical clock, or hardware result.
- No direct APCB-to-APOB merge edge recovered; APCB is proven as a parsed flash policy input only.
- The exact ABL1 function that consumes memory policy remains unresolved; historical source address anchors do not apply directly.
- The decisive next offline check is a byte-backed provider/consumer trace from the APOB/PPI interface fields to a concrete training or divider input, without assuming that `$INV` token presence is consumption.
