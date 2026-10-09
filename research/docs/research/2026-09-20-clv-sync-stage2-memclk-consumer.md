# Stage 2 — Native MemoryClockSpeed consumer bounded audit

## Result

The exact clv `MemoryClockSpeed` field is a native serializer input:

```text
AmdSetup+0x316 (body base 0x4CF; pinned clv byte 0x24 / 36)
  -> CbsBasePei record 0x11ED
  -> value store at CbsBasePei RVA 0x985D
```

The selected native memory-init module bodies contain **no direct `0x11ED` literal or `Setup+0x316` source load**:

- `AmdMemAm4Pei` — 1510 instruction records, no direct hit.
- `PlatformMemoryConfigurationPei` — 17 instruction records, no direct hit.
- `AmdMemoryHobInfoPeim` — 1885 instruction records, no direct hit.

This bounded result does not show the native memory-training consumer or an MHz enum/range decode. The concrete missing edge is the AGESA/PSP/APOB memory-init path or an HOB/config structure populated after the CBS `$INV` serializer. A direct token scan is insufficient to decide that the field is ignored because indirect protocol/HOB consumers and closed firmware remain possible.

## Control-flow pivot

The tiny `PlatformMemoryConfigurationPei` body is exactly `xor eax,eax; ret` (17 instruction records including padding decode) and has no calls; it is not a memory-init producer.

`AmdMemAm4Pei` has an actual entry path:

```text
RVA 0x240 -> call 0x876 -> jump 0x2F6
```

The helper at `0x876` calls `0xDDE` and `0x5F1`, then invokes a service helper at `0xB09` with preserved literal `0x9E3B14C` and invokes a second service path at `0xCD9` with message/argument literals `0x61`/`0xFF`. It validates returned structures by magic values:

```text
0x424F5041  = "APOB"
0x50535024  = "$PSP"
0x44484224  = "$BHD"
```

Checksum/validation helpers `0xBC9` and `0xBE2` are called before success. The main path at `0x2F6` uses protocol method offsets `+0x4C` and `+0x18` to obtain/copy opaque structures, but does not expose `AmdSetup+0x316`, an MHz enum, or a direct DRAM clock write in this bounded body.

This is a concrete boundary: the next required component is the opaque service/AGESA/PSP memory-init consumer behind the `AmdMemAm4Pei` protocol and APOB structures, not another direct `0x11ED` search.

## PEI service-table identification

The local EDK II `EFI_PEI_SERVICES` layout is byte-compatible with the observed IA32 calls: `EFI_TABLE_HEADER` is `0x18` bytes, `InstallPpi` is table slot `+0x18`, `InstallPeiMemory` is `+0x44`, and `AllocatePool` is `+0x4C`.

Exact `AmdMemAm4Pei` entry/dataflow:

```text
RVA 0x240: call 0x876
RVA 0x245: EAX = [ESP+8] (second PEIM entry argument)
RVA 0x249: jump 0x2F6
RVA 0x30F: ESI = EAX (pointer to the PeiServices table pointer)
RVA 0x311: EAX = [ESI] (load the EFI_PEI_SERVICES table)
RVA 0x316: [[ESI]+0x4C] with size 0x48 (AllocatePool)
RVA 0x3AA: [[ESI]+0x4C] with size 0x0C (AllocatePool)
RVA 0x3E5: [[ESI]+0x18] (InstallPpi)
```

The registered descriptor carries flags `0x80000010`, data pointer literal `0x9E3AFC0`, and an interface pointer; the interface receives `0x9E3A06E` at `+0x44`. The bounded main path contains no `[[ESI]+0x44]` call, so it does **not** call `InstallPeiMemory`. This identifies `AmdMemAm4Pei` as a PEI PPI/data-handoff wrapper, not proof of a direct DRAM training engine. The helper `0x876` additionally validates APOB/`$PSP`/`$BHD` structures; exact GUID/interface names and the downstream AGESA consumer remain unresolved.

## Exact serializer evidence

`CbsBasePei` exact instructions:

```text
0x9837: baed110000       record header 0x11ED
0x9857: 8a8216030000     load AmdSetup+0x316
0x985D: 884103           store value into current record
```

Pinned clv direct read: body base `0x4CF + 0x316 = ROM 0x7E5`, raw `0x24` (36).

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-memclk-consumer/memclk_consumer_verify.py
```

Observed exit `0`; stderr empty; `12/12` checks passed.

Observed stdout:

```text
{"checks": {"failed": 0, "passed": 12, "total": 12}, "conclusion": "The exact native memory-init modules in this bounded set contain no direct 0x11ED literal or Setup+0x316 source load. Existing evidence therefore ends at the CBS INV serializer; the missing edge is the AGESA/PSP/APOB memory-init consumer or a HOB/config structure populated after INV handoff. No MHz decode or accepted-range claim is established.", "modules": {"AmdMemAm4Pei": {"direct_11ed_or_setup316_hits": [], "instruction_count": 1510, "sha256": "1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8"}, "AmdMemoryHobInfoPeim": {"direct_11ed_or_setup316_hits": [], "instruction_count": 1885, "sha256": "aad3f828ccef4cf8878cad8c9ee1e47743748f652a1ef54af04de759983b4619"}, "PlatformMemoryConfigurationPei": {"direct_11ed_or_setup316_hits": [], "instruction_count": 17, "sha256": "6a1ab7fe72ad3ee0e8f9238e2ba2d166c97e44812761e6d16a725525e1817085"}}, "status": "PASS"}
```

## Boundary

- **PASS:** exact field bytes and CBS serializer handoff.
- **PASS:** selected native memory-init module no-hit check.
- **UNRESOLVED:** AGESA/PSP/APOB/HOB consumer, MHz enum/range, training decision, and hardware application.
- **UNRUN:** firmware execution, training, hardware, clocks, voltage, and performance.
