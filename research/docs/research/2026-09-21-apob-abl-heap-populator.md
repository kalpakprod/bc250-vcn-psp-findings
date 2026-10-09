# ABL1 HEAP key 0xA04E producer and APOB/INV boundary

## Result

A bounded exact-byte test closes the HEAP node writer/data-source edge for the selector-0x0F provider path:

```text
ABL1 provider 0x49CC:
  fixed key 0xA04E at 0x4B1A
  miss descriptor SP+0x14
  BL 0x6238 at 0x4B5C
        |
        v
HEAP producer 0x6238:
  descriptor +4 -> node key at node+0
  source R10 -> byte-copy helper 0x6B78 -> node+0x10 payload
        |
        v
ABL1 constructor 0xC00:
  caller outer object R1 (from 0xB84/0xBD2)
  outer+0x864 saved as provider source pointer at SP+0xA4
  outer+0x864 initialized with external pointer 0x006CD4D0
```

The first unresolved cross-stage boundary is now narrower: the producer/meaning of the outer object passed as R1 at 0xB84/0xBD2, and the population of its +0x864 field relative to the AmdMemAm4Pei APOB service (0x9E3B14C, message 0x61, argument 0xFF) and native INV 0x11ED. No byte-backed path joins those sources.

No PPI GUID proof and no 0x1204 serializer/HOB proof was repeated.

## Exact target and inputs

- ROM: /home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin, 16 MiB, SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8
- ABL1 payload: evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin, SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a
- ABL1 ELF object/listing basis: evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o, SHA-256 54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135
- AmdMemAm4Pei: evidence/firmware-audit/20260919-inv-token-consumers/AmdMemAm4Pei-1ef4e7b94467.bin, SHA-256 1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8
- CbsBasePei: evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin, SHA-256 6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77

## Observed HEAP producer edge

### Provider key and miss descriptor

Exact ABL1 raw bytes:

```text
0x4B1A: 4A F2 4E 06       MOVW R6,#0xA04E
0x4B34: 09 A8             ADD  R0,SP,#0x24       ; lookup descriptor
0x4B38: 09 96             STR  R6,[SP,#0x24]      ; requested key
0x4B4E: CD E9 05 06       STRD R0,R6,[SP,#0x14]   ; miss descriptor fields
0x4B52: 04 20             MOVS R0,#4              ; metadata
0x4B54: 29 99             LDR  R1,[SP,#0xA4]      ; source pointer
0x4B56: 8D F8 1C 00       STRB R0,[SP,#0x1C]
0x4B5A: 05 A8             ADD  R0,SP,#0x14
0x4B5C: 01 F0 6C FB       BL   0x6238
```

The existing lookup 0x6374 returns a null/non-null status; this test follows the miss-side producer call into 0x6238 rather than redoing the selector/reader chain.

### HEAP node writer and payload copy

```text
0x6238: 2D E9 F8 4F       PUSH ...
0x623C: 04 46             MOV  R4,R0              ; producer descriptor
0x6242: 8A 46             MOV  R10,R1             ; source pointer
0x6278: 62 68             LDR  R2,[R4,#4]
0x62FA: 60 68             LDR  R0,[R4,#4]
0x62FC: 28 60             STR  R0,[R5]            ; node+0 = key
0x631E: 53 46             MOV  R3,R10
0x6320: 00 F0 2A FC       BL   0x6B78
```

The copy helper at 0x6B78 enters a byte loop (0x6B7A) that reads from R1 and writes to R0; therefore the node payload begins at the allocated node body (node+0x10 in the producer setup) and is copied from the source pointer passed in R10.

The runtime HEAP base and sentinel literals are byte-backed:

```text
0x6360: 00 30 07 00       0x00073000
0x6364: 48 45 41 50       HEAP
```

## Exact source-field producer inside ABL1

The only inspected source assignment for SP+0xA4 is in constructor 0xC00, reached from caller 0xB84 / 0xBD2:

```text
0xBD0: 20 46             MOV  R0,R4
0xBD2: 00 F0 15 F8       BL   0xC00

0xC00: 2D E9 FC 41       PUSH ...
0xC04: 07 46             MOV  R7,R0
0xC06: 88 46             MOV  R8,R1
0xC29E: 01 F6 64 00      ADDW R0,R1,#0x864
0xC2A2: C1 F8 6C 28      STR.W R2,[R1,#0x86C]
0xC2A8: 29 90             STR  R0,[SP,#0xA4]
0xC2AA: 01 F5 07 60      ADD.W R0,R1,#0x870
0xC2AE: C1 F8 64 28      STR.W R2,[R1,#0x864]
```

The literal pool entry at 0xC4B4 is little-endian D0 D4 6C 00, i.e. 0x006CD4D0. Thus this bounded path establishes:

```text
provider source pointer = outer_object_R1 + 0x864
outer_object_R1[+0x864] = 0x006CD4D0   (constructor initialization)
```

R1 itself is supplied to 0xC00 by the caller incoming object (R5 at 0xB84); its upstream producer is not resolved in this test.

## APOB and native INV boundary context

The exact open x86 PEI service bytes remain separate from the ABL1 source field:

```text
AmdMemAm4Pei RVA 0x08A0: push 0x9E3B14C
AmdMemAm4Pei RVA 0x08CA: push 0xFF
AmdMemAm4Pei RVA 0x08CF: push 0x61
AmdMemAm4Pei RVA 0x08D1: call 0xCD9

CbsBasePei RVA 0x9837: mov edx,0x11ED
CbsBasePei RVA 0x9857: mov al,[edx+0x316]
```

The ABL1 payload contains no direct INV marker, no direct little-endian 0x11ED literal, and no direct little-endian 0x9E3B14C service pointer. These are bounded direct-literal checks only; no absence claim is made for computed, indirect, DMA, or runtime delivery.

## Reproduction

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-apob-abl-heap-populator/heap_populator_verify.py > evidence/firmware-audit/20260921-apob-abl-heap-populator/verifier.stdout 2> evidence/firmware-audit/20260921-apob-abl-heap-populator/verifier.stderr
```

Observed exit: 0; literal status PASS; 34/34 checks; stderr empty.

Machine result: evidence/firmware-audit/20260921-apob-abl-heap-populator/heap-populator-result.json, SHA-256 acad9717893994744064d2f9573661aec0ad65024fd2816f39296e811d81a617.

Owned verifier SHA-256: 41bdf4e173dc91e840f7d16e35281c878b37207c52d9d039ebb37185803d1f9f.

## Boundary and status

- PASS: fixed selector-case HEAP key 0xA04E reaches the miss descriptor and 0x6238.
- PASS: 0x6238 writes descriptor key to node key and copies payload bytes from its source pointer through 0x6B78.
- PASS: source pointer is outer_object+0x864; constructor initializes that field with 0x006CD4D0.
- PASS: APOB service and native INV 0x11ED context addresses/hash-pinned bytes reopened without repeating PPI GUID or 0x1204 proofs.
- UNRESOLVED: upstream producer of the outer ABL1 object at 0xB84/0xBD2; whether outer+0x864/0x006CD4D0 is populated from APOB service 0x9E3B14C/0x61/0xFF, native INV 0x11ED, or another runtime source; ABL1 loader/runtime execution; SMU actuator; physical clock/training/synchronization/hardware.
- UNRUN: firmware/ABL1/APOB execution, HOB capture, SMU execution and hardware checks.

No ROM, firmware, NVRAM, register, hardware, network, candidate, shared plan, or shared memory was modified.

## Independent disassembly readback

After local raw-byte oracle corrections, fresh LLVM Thumb windows were run successfully (exit `0`, stderr empty) for provider `0x4B1A..0x4B64`, HEAP writer `0x6238..0x6344`, copy helper `0x6B78..0x6B84`, and constructor `0xBD0..0xC2B4`. The windows independently decode the fixed key/call, node-key store/copy call, byte-copy loop, and `outer+0x864` stores.

Owned listing captures are under `evidence/firmware-audit/20260921-apob-abl-heap-populator/` (`provider-window.stdout`, `heap-window.stdout`, `copy-window.stdout`, `ctor-window.stdout`, with matching empty `.stderr` captures).
