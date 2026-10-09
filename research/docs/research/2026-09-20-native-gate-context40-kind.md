# ABL1 `context+0x40` source and kind1–4 selection capability

Supplemental exact-byte dataflow review. It traces the high-bit merge source and evaluates only structural kind-selection capability; it does not claim an active runtime provider or physical map.

Current: exact `context+0x40` source / full-u32 provider field proven / kind1–4 structurally selectable / runtime object/value unresolved.

## Source chain

Exact bytes establish:

```text
initializer 0x7378:
  R5 = arg0                         (0x737C)
  R6 = arg1                         (0x7384)
  R4 = [R6+0x3C4]                   (0x73AE)
  [R5+0x8] = R4                     (0x73B2)
  R0 = [R4+0x4]                     (0x73B6)
  [R5+0x40] = R0                    (0x73B8)

callback 0x9AD8:
  R0 = [R5+0x40]                    (0x9B82)
  BFI descriptor bits15..19         (0x9B88)
  BFI descriptor bits20..27         (0x9B92)
  BFI descriptor bits28..31         (0x9B98)
  kind = descriptor bits27..29      (0x9C00)
```

The merge replaces descriptor mask `0xFFFF8000` and preserves the low 15 bits, including raw descriptor low12. The source is a full 32-bit child-object field (`[arg1+0x3C4]+0x4`), not a byte-limited selector.

## Can it select kind1–4?

Yes, structurally. With the joined fallback raw descriptor `0x006F47C0`, symbolic source values produce:

| `context+0x40` source | merged kind | bit30 | preserved low12 |
| --------------------: | ----------: | ----: | --------------: |
|          `0x08000000` |           1 |     0 |         `0x7C0` |
|          `0x10000000` |           2 |     0 |         `0x7C0` |
|          `0x18000000` |           3 |     0 |         `0x7C0` |
|          `0x20000000` |           4 |     0 |         `0x7C0` |

These examples prove only that the exact merge can redirect the branch to the existing kind1–4 constructors. They do not reveal the actual child field at runtime. The active dispatcher loads the callback pointer from `[R0+0x660]`; this exact static slice does not join that current object to the `0x7378` parent `R5` object. Therefore the actual runtime kind, `context+0x40` value, HEAP/fallback branch, SVC#4 translation, and physical target remain unknown.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-context40-kind/verify_context40_kind.py
```

Observed: exit `0`; `38/38` checks passed; stderr empty. Machine result status `CAPABILITY_STATIC_RUNTIME_VALUE_UNRESOLVED`.

Owned evidence: `evidence/firmware-audit/20260920-native-gate-context40-kind/`.

Evidence class: `observed-bytes` + `static-analysis`. No ROM/candidate, firmware, hardware, settings, shared plan, MCP/global configuration, installation, or commit changed.

## Decision boundary

The exact provider chain is now known statically, and kind1–4 selection is possible in the dataflow. It is **not** evidence that the current callback uses any particular kind or mapped SMN address. A runtime object-identity/provider capture or an independent static join to the active dispatcher is required before map/clock claims.
