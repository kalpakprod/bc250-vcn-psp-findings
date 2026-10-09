# Corrected `$INV 0x1204/0x1374` consumer edge — bounded direct requester result

Supplemental exact-code edge review. It traces the native serializer records into the exact AmdFabric generic `$INV` reader and enumerates direct requester callsites; it does not claim absence of indirect/HOB/DMA/runtime consumers.

Current: exact Cbs/AmdFabric PEI edge / direct requesters remain `0x10FF` and `0x1104` / next = resolve indirect or later-phase delivery before assigning an actuator.

## Result

The exact reader at `AmdFabricAriPei` RVA `0x1D3C` is a generic token lookup:

1. It validates the `$INV` header at `0x1DFC`.
2. It advances to the first record at `0x1E11`.
3. It reads each record type at `record+0x2` (`0x1E16`), decodes payload width, loads the token at `record+0` (`0x1E67`), and compares it to the caller-supplied requested token at `[EBP+8]` (`0x1E6A`).
4. It advances by the record width until a matching token or `0xFFFF` terminator.

The exact AmdFabric instruction census has only two direct calls to this reader:

| Callsite |   Immediate requested token | Exact role            |
| -------: | --------------------------: | --------------------- |
| `0x1EBD` | `0x10FF` pushed at `0x1EB0` | Direct reader request |
| `0x1F94` | `0x1104` pushed at `0x1F8B` | Direct reader request |

No direct push/request for corrected tokens `0x1204` or `0x1374` exists in this bounded AmdFabric census. AmdFabric does contain serializer literals `0x1204` at RVA `0xD224` and `0x1374` at RVA `0x11C98`; those are record producers, not reader requests.

CbsBasePei independently emits the native fields:

- `Setup+0x330` load at RVA `0x9CE4` into `$INV` token `0x1204` (header `0x9CC4`, value store `0x9CEA`).
- `Setup+0x704` load at RVA `0xE75B` into `$INV` token `0x1374` (header `0xE738`, u16 value store `0xE762`).

**Decision:** the corrected native records are statically produced and generically parseable, but this exact direct AmdFabric route does not request them. Do not call either field applied, consumed by a clock actuator, or connected to the ABL1 fallback descriptor. Indirect/computed callers and later HOB/DMA/runtime paths remain open.

## Direct verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-inv-consumer-edge/verify_inv_consumer_edge.py
```

Observed: exit `0`; `35/35` checks passed; stderr empty. Machine result status `PARTIAL_BOUNDED_EDGE`, decision `NO_DIRECT_1204_OR_1374_REQUESTER_IN_EXACT_AMDFABRIC_CENSUS`.

Inputs and hashes:

- CLV donor: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- `CbsBasePei` body: `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77` (exact body SHA-256; local body: `evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin`).
- `AmdFabricAriPei` body: SHA-256 `c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78`.
- Instruction metadata hashes are recorded in the owned machine result and manifest.

Evidence class: `observed-bytes` + `static-analysis`. No ROM/candidate, firmware, settings, hardware, shared plan, MCP/global state, installation, or commit changed.

## Boundary

This closes only the selected direct AmdFabric reader boundary. It does not prove a census-wide absence of computed/indirect token requests, HOB/DMA migration, runtime delivery, training, divider/clock actuation, or hardware behavior. No `1:1:1` claim follows.
