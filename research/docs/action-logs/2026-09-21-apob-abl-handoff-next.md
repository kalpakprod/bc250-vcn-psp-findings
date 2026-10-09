# Serialized `$INV` to APOB/ABL1/SMU handoff — targeted boundary

## Intent (before owned evidence writes)

- Timestamp: 2026-09-21T14:25:00+05:00 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`; offline read-only)
- Target: exact plain CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; size 16 MiB. Preserve native `MemoryClockSpeed=1800` (`AmdSetup+0x316=0x24`) unchanged.
- Scope: one targeted static/source test for the first unresolved handoff after existing UEFI `$INV` serializers: compare the exact `0x11ED` producer in `CbsBasePei` and `AmdNbioSmuV10Pei` with the exact ABL1 APCB/CBS token-7 getter and the `AmdMemAm4Pei` APOB service request; classify the first missing provider boundary. The already-proven `0x1204` serializer/HOB boundary is not repeated.
- Existing routes reused: exact extracted module bodies/instruction listings under `evidence/firmware-audit/20260919-inv-token-consumers/`, exact decompressed ABL1 under `evidence/firmware-audit/20260920-clv-abl-memory-review/`, existing APCB detail JSON under `evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/`, and the pinned Robin-5 SMU body under the imported provenance tree. No new parser or candidate is planned.
- Hypothesis: the native serialized memory enum (`$INV 0x11ED`, value `0x24`) is semantically concordant with ABL1's token-7 `0x24 -> 0x708` policy mapping, but the bytes do not join `$INV` to the APOB service or the ABL1 provider; the first missing boundary is the opaque service/runtime provider path, not the serializer or memory-HOB byte path.
- Expected effect: create only a machine-readable targeted result, report, verifier, literal stdout/stderr/exit captures, and manifest under the uniquely named evidence directory. No ROM, firmware, NVRAM, register, hardware, network, source, memory, plan, or candidate writes.
- Rollback: remove only `evidence/firmware-audit/20260921-apob-abl-handoff/`, this report, and this action log; immutable inputs and existing evidence remain unchanged.
- Acceptance event: verifier starts, exits, and emits the targeted result with exact input hashes, addresses, first missing boundary, and explicit static-only limits.

## Correction to initial verifier offset assumption (before evidence execution)

The first trial used PEI instruction RVAs as direct offsets into extracted TE `.bin` section bodies. It failed immediately (exit `1`) on the first assertion: raw section byte at `0x9837` was `ba f5 11 00 00`, while the instruction listing at RVA `0x9837` was `ba ed 11 00 00`. The existing token-matrix verifier explicitly maps TE RVA to raw offset `RVA - 0x190`; this failure is an address-convention mismatch, not artifact evidence. The corrected verifier must use that mapping for CbsBasePei and AmdNbioSmuV10Pei and must stop using the faulty initial run as a finding. No input changed.

## Correction to second verifier trial (before successful execution)

The corrected TE RVA mapping then reached the positive PPI join but stopped on a local assertion-width error (exit `1`): the check requested 10 bytes while the expected concatenated instruction sequence was 11 bytes. The exact split is `0xADE` (`8A4830`), `0xAE4` (`8A4831`), and `0xAE7` (`8B4040`); no input artifact or finding changed.

## Correction to third verifier trial (before successful execution)

The positive PPI join and instruction-width corrections then reached raw ABL1 bytes but used disassembly word-order for two Thumb `MOVS` checks. The trial exited `1` (`raw 0x2264 = 07 20`, not listing text `20 07`). The verifier now distinguishes raw byte order from printed Thumb halfwords (`0x4810 = 0F 20`); no input artifact or finding changed.

## Observed result after owned writes

- Timestamp: 2026-09-21T14:39:00+05:00 (Asia/Almaty)
- Verifier command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-apob-abl-handoff/handoff_trace_verify.py`
- Exit status: `0`
- Literal stdout status: `PASS`, `46` checks, result path `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-handoff/apob-abl-handoff-result.json`
- Literal stderr: empty
- Positive result: `AmdMemAm4Pei` descriptor GUID pointer `0x9E3AFC0` and `AmdMemoryHobInfoPeim` `LocatePpi` GUID pointer `0x9EB92F4` resolve to the same GUID `e54e6e84-020b-4081-8156-37e9c62c1ed6`; the latter reads PPI fields `+0x28/+0x2C/+0x30/+0x31/+0x40` and calls `InstallPeiMemory` at RVA `0x299`.
- Native producer result: `CbsBasePei` RVAs `0x9837/0x9857/0x985D` and `AmdNbioSmuV10Pei` RVAs `0xB8B7/0xB8D7/0xB8DD` preserve `AmdSetup+0x316=0x24` as `$INV 0x11ED`.
- ABL1 result: exact provider path uses token `7`, selector `0x0F`, group `0x1707`, and maps enum `0x24` to `0x708` (1800); this remains a separate namespace without a byte-backed `$INV 0x11ED` join.
- First missing boundary: APOB service/PPI population input between `$INV 0x11ED` production and `AmdMemAm4Pei` service output; no training/clock/SMU actuator or hardware claim.
- PMFW bounded carrier check: `$INV=0`, `NVTB=0`, direct `0x11ED` literal `0`; no computed/indirect/DMA absence claim.

Readback hashes:

```text
f8c8d1610ae89a933b3060b3917ec57a2b1f69d7c6fd4f3620baec2de6f991db  docs/research/2026-09-21-apob-abl-handoff-next.md
bcd9d779791b0c6ad7ac7a862431ca2f0f385c0dc73361dd9a7c4c3bdb4af35e  evidence/firmware-audit/20260921-apob-abl-handoff/handoff_trace_verify.py
36abcbcb636b330457c00ab59e74a17b8ae5976c774b80f9c29f3912918da2a6  evidence/firmware-audit/20260921-apob-abl-handoff/apob-abl-handoff-result.json
d6e88339eb1e82d338791fe990e164941c53763c65b386abba1f8bfd209dc7f8  evidence/firmware-audit/20260921-apob-abl-handoff/verifier.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  evidence/firmware-audit/20260921-apob-abl-handoff/verifier.stderr
ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8  evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
506b8eefd0ef3847782dddd88a458b95e32082f473346d7d645703dce6b60d39  evidence/firmware-audit/20260919-inv-token-consumers/census.json
```

No ROM, firmware, NVRAM, register, hardware, network, candidate, plan, shared memory, or source input changed. Hardware/runtime checks remain unrun. Rollback is deletion of this owned report, action log, and evidence directory only.

## Evidence manifest readback

- `sha256sum -c evidence/firmware-audit/20260921-apob-abl-handoff/SHA256SUMS.final`: `4/4 OK`.
- Manifest SHA-256: `315bb47fa145b759b4e058190abcdb47d7cbc50f6f16bd142844c6593261e5f4`.
- Final report SHA-256: `f8c8d1610ae89a933b3060b3917ec57a2b1f69d7c6fd4f3620baec2de6f991db`.
- Final action-log SHA-256 is recomputed after this append-only entry below.
