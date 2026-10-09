# Serialized `$INV` to APOB/ABL1/SMU handoff — targeted boundary

## Current

The one targeted static test passed `46/46` on the pinned plain CLV donor. It closes a **positive** APOB-PPI GUID join and keeps the native `MemoryClockSpeed=1800` request unchanged. It does **not** establish that `$INV 0x11ED` feeds the APOB service, the joined PPI fields, ABL1 runtime context, or SMU/PMFW.

The first missing boundary is the input population of the APOB service/PPI path, before memory-training or clock-actuator semantics:

```text
CbsBasePei / AmdNbioSmuV10Pei:
  AmdSetup+0x316 (0x24) -> `$INV` record 0x11ED
       [missing byte-backed edge]
AmdMemAm4Pei:
  service 0x9E3B14C, message 0x61, argument 0xFF
  -> PPI GUID e54e6e84-020b-4081-8156-37e9c62c1ed6
       [positive GUID join]
AmdMemoryHobInfoPeim:
  LocatePpi -> PPI fields +0x28/+0x2C/+0x30/+0x31/+0x40
  -> InstallPeiMemory (RVA 0x299)

ABL1 (separate provider namespace):
  token 7/timepoint 2 -> selector 0x0F/group 0x1707
  enum 0x24 -> policy value 0x708 (1800)
       [no `$INV 0x11ED` join]

SMU PMFW body:
  no `$INV`/`NVTB` marker and no direct 0x11ED literal in this bounded carrier check
```

The existing `0x1204` serializer/HOB boundary was deliberately not repeated.

## Exact target and inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM size: `16,777,216` bytes
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Module census: `evidence/firmware-audit/20260919-inv-token-consumers/census.json`, SHA-256 `506b8eefd0ef3847782dddd88a458b95e32082f473346d7d645703dce6b60d39`
- ABL1 decompressed payload: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Robin-5 PMFW body: `archives/imported/recon-evidence/legacy-tmp-bc250-recon/robin5_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.7.1.body`, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`

Exact extracted module hashes:

| Module                 | SHA-256                                                            |
| ---------------------- | ------------------------------------------------------------------ |
| `CbsBasePei`           | `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77` |
| `AmdNbioSmuV10Pei`     | `905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80` |
| `AmdMemAm4Pei`         | `1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8` |
| `AmdMemoryHobInfoPeim` | `aad3f828ccef4cf8878cad8c9ee1e47743748f652a1ef54af04de759983b4619` |

## Observed static edges

### 1. Open UEFI `$INV` producers — `0x11ED`, not `0x1204`

Both open UEFI producer copies preserve the Setup byte without a conversion:

| Module             |                  Record header |                        Setup load |              Value store |
| ------------------ | -----------------------------: | --------------------------------: | -----------------------: |
| `CbsBasePei`       | RVA `0x9837`: `BA ED 11 00 00` | RVA `0x9857`: `8A 82 16 03 00 00` | RVA `0x985D`: `88 41 03` |
| `AmdNbioSmuV10Pei` | RVA `0xB8B7`: `BA ED 11 00 00` | RVA `0xB8D7`: `8A 82 16 03 00 00` | RVA `0xB8DD`: `88 41 03` |

TE RVAs were translated through the exact section maps; the failed initial direct-RVA trial is retained in the action log as an address-convention correction. The pinned ROM has `AmdSetup` body base `0x4CF`, so `ROM[0x4CF+0x316] = 0x24`. The native request remains the IFR-labelled `1800MHz` option; this is a stored UI value, not a physical clock result.

### 2. Positive APOB-PPI GUID join and memory-HOB consumer

`AmdMemAm4Pei` builds an EFI PEI PPI descriptor with GUID pointer `0x9E3AFC0`. Under module image base `0x09E39E20`, this is module RVA `0x11A0` (raw section offset `0x1008`). `AmdMemoryHobInfoPeim` calls `LocatePpi` with GUID pointer `0x9EB92F4`; under image base `0x09EB7CB4`, this is RVA `0x1640` (raw section offset `0x14A8`). Both locations contain the same GUID bytes:

```text
e54e6e84-020b-4081-8156-37e9c62c1ed6
```

The request/provider and consumer bytes are:

```text
AmdMemAm4Pei:
  RVA 0x08A0: push 0x9E3B14C             ; APOB service pointer
  RVA 0x08CA: push 0xFF                  ; argument
  RVA 0x08CF: push 0x61                  ; message
  RVA 0x08D1: call 0xCD9                 ; opaque service gateway
  RVA 0x03B1: descriptor flags 0x80000010
  RVA 0x03B7: descriptor GUID = 0x9E3AFC0
  RVA 0x03D7: PPI object +0x44 = 0x9E3A06E
  RVA 0x03E5: call [PEI services +0x18] ; InstallPpi

AmdMemoryHobInfoPeim:
  RVA 0x026D: GUID pointer = 0x9EB92F4
  RVA 0x0277: call [PEI services +0x20] ; LocatePpi
  RVA 0x0AD0: read returned PPI +0x28
  RVA 0x0AD6: read returned PPI +0x2C
  RVA 0x0ADE: read returned PPI +0x30
  RVA 0x0AE4: read returned PPI +0x31
  RVA 0x0AE7: read returned PPI +0x40
  RVA 0x0299: call [returned PEI services +0x44] ; InstallPeiMemory
```

This is a positive static interface join, not a claim that the runtime PPI is invoked or that its fields are training inputs.

### 3. ABL1 provider namespace is semantically concordant but not byte-joined

The exact ABL1 payload has a separate APCB/CBS config getter:

```text
RVA 0x2264: MOVS R0,#7 (raw bytes `07 20`)
RVA 0x2266: BL 0x1F2C
RVA 0x4810: MOVS R0,#0x0F (raw bytes `0F 20`)
RVA 0x4B0E: selector/group setup containing `0x1707`
RVA 0x228A: TBB table; enum 0x24 selects target RVA 0x2318
RVA 0x2318: MOVW ...,#0x708 (raw `40 F2 08 70`)
```

Thus the exact ABL1 path maps a separate config enum `0x24` to policy value `0x708` (decimal `1800`). It does not establish that ABL1 token `7` is native `$INV 0x11ED`, nor that the value reaches the PPI fields above. The APCB parser has two raw CBSG rows whose second byte is `7` (`0xAB1464` and `0xAB1710`); they remain raw parser fields and are not relabelled as native `$INV` records.

The exact ABL1 payload contains no `$INV` marker and no direct little-endian `0x11ED` literal in this bounded test.

### 4. SMU carrier boundary

The exact Robin-5 PMFW body contains no `$INV`, `NVTB`, or direct little-endian `0x11ED` marker. This is bounded carrier evidence only. It does not exclude computed, indirect, DMA, or runtime data delivery, and does not identify an SMU consumer or actuator.

## Reproduction

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  evidence/firmware-audit/20260921-apob-abl-handoff/handoff_trace_verify.py \
  > evidence/firmware-audit/20260921-apob-abl-handoff/verifier.stdout \
  2> evidence/firmware-audit/20260921-apob-abl-handoff/verifier.stderr
```

Observed exit status: `0`.

Literal stdout:

```json
{
  "status": "PASS",
  "checks": 46,
  "result": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-handoff/apob-abl-handoff-result.json",
  "first_missing_boundary": {
    "location": "between Cbs/AmdNbioSmuV10Pei `$INV 0x11ED` buffer production and AmdMemAm4Pei APOB service/PPI population; downstream ABL1 provider table remains separate"
  }
}
```

Stderr is empty; `verifier.stderr` SHA-256 is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Owned evidence:

- Verifier: `evidence/firmware-audit/20260921-apob-abl-handoff/handoff_trace_verify.py`, SHA-256 `bcd9d779791b0c6ad7ac7a862431ca2f0f385c0dc73361dd9a7c4c3bdb4af35e`
- Result: `evidence/firmware-audit/20260921-apob-abl-handoff/apob-abl-handoff-result.json`, SHA-256 `36abcbcb636b330457c00ab59e74a17b8ae5976c774b80f9c29f3912918da2a6`
- Stdout: `evidence/firmware-audit/20260921-apob-abl-handoff/verifier.stdout`, SHA-256 `d6e88339eb1e82d338791fe990e164941c53763c65b386abba1f8bfd209dc7f8`
- Stderr: `evidence/firmware-audit/20260921-apob-abl-handoff/verifier.stderr`, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## Boundary and status

- **PASS:** exact CLV hash/size and module hashes.
- **PASS:** `CbsBasePei` and `AmdNbioSmuV10Pei` `Setup+0x316 -> $INV 0x11ED` byte paths.
- **PASS:** positive `AmdMemAm4Pei` descriptor GUID ↔ `AmdMemoryHobInfoPeim` `LocatePpi` GUID join.
- **PASS:** APOB service pointer/message/argument and PPI install/consumer offsets.
- **PASS:** exact ABL1 token-7/provider path and `0x24 -> 0x708` static policy mapping.
- **PASS:** bounded PMFW carrier marker check.
- **UNRESOLVED:** the service output/input dataflow from `$INV 0x11ED` to APOB/PPI; ABL1 runtime context population; SMU mailbox/actuator; physical clock, training, synchronization, voltage and hardware behavior.
- **UNRUN:** firmware execution, PPI invocation, APOB service execution, ABL1 execution, SMU execution and all hardware checks.

No ROM, firmware, NVRAM, register, hardware, network, candidate, plan, or shared memory was modified.
