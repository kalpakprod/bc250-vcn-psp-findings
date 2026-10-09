# Exact CLV ABL1 enum-to-IFR option comparison

## Conclusion

An independent byte-level decode of the exact ABL1 selector table finds **20 recognized input codes**. All 20 codes are present in the exact CLV IFR `Memory Clock Speed` option list, and each ABL1 numeric policy output equals the number printed in the corresponding IFR label. This is a strong bounded correlation between the two tables.

The comparison also finds three IFR options that this ABL1 dispatch does not accept:

- `0xFF` — `Auto`, the IFR default — takes the ABL range-invalid path;
- `0x26` (decimal `38`) — `1900MHz` — is a TBB gap and takes the invalid path;
- `0x27` (decimal `39`) — `1950MHz` — is a TBB gap and takes the invalid path.

Therefore the tables are **not identical option sets**. The 20-code agreement does not prove that ABL token `7`, the IFR field `AmdSetup+0x316`, and the numeric values share one runtime namespace. In particular, the direct token-`7` to `$INV 0x11ED` edge remains unresolved. No physical-MHz, clock-domain, synchronization, training, runtime, or hardware claim follows.

## Exact inputs

- ABL1 payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
  - SHA-256: `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- ABL1 listing used only as a cross-check: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-data-thumb-llvm.txt`
- Exact CLV IFR result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-df-init-route/menu-result.json`
  - ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
  - `Memory Clock Speed` question: `AmdSetup+0x316`, QID `0x20F`
  - CbsSetupDxe module SHA-256: `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`

## ABL1 dispatch boundary

The exact payload bytes at `0x2280..0x2289` implement an unsigned range guard and Thumb TBB dispatch:

```text
0x2280: subs r0, r0, #2
0x2282: cmp  r0, #0x27
0x2284: bhs  0x232A
0x2286: tbb  [pc, r0]
```

Consequently, selector bytes `2..40` enter the 39-byte table at `0x228A`; all other byte values branch directly to `0x232A`. Table gaps also target `0x232A`.

For a mapped table entry, the function loads a numeric constant into `r0`, writes it to `[r4+0x04]+0x2C`, and later writes mode `2` to `[r4+0x04]+0x28`. The invalid target at `0x232A` calls opaque helper `0x64C8`, then directly writes mode `2`; this function has no direct policy-value write on that invalid path. Helper side effects remain unknown.

## Complete comparison

|   Code | ABL1 numeric policy value | Exact IFR option | Result            |
| -----: | ------------------------: | ---------------- | ----------------- |
| `0x02` |                       125 | 125MHz           | numeric agreement |
| `0x04` |                       225 | 225MHz           | numeric agreement |
| `0x05` |                       250 | 250MHz           | numeric agreement |
| `0x08` |                       400 | 400MHz           | numeric agreement |
| `0x09` |                       450 | 450MHz           | numeric agreement |
| `0x0A` |                       500 | 500MHz           | numeric agreement |
| `0x0F` |                       750 | 750MHz           | numeric agreement |
| `0x11` |                       850 | 850MHz           | numeric agreement |
| `0x14` |                      1000 | 1000MHz          | numeric agreement |
| `0x19` |                      1250 | 1250MHz          | numeric agreement |
| `0x1A` |                      1330 | 1330MHz          | numeric agreement |
| `0x1B` |                      1375 | 1375MHz          | numeric agreement |
| `0x1E` |                      1500 | 1500MHz          | numeric agreement |
| `0x20` |                      1600 | 1600MHz          | numeric agreement |
| `0x21` |                      1650 | 1650MHz          | numeric agreement |
| `0x22` |                      1700 | 1700MHz          | numeric agreement |
| `0x23` |                      1750 | 1750MHz          | numeric agreement |
| `0x24` |                      1800 | 1800MHz          | numeric agreement |
| `0x25` |                      1850 | 1850MHz          | numeric agreement |
| `0x28` |                      2000 | 2000MHz          | numeric agreement |

All 20 rows agree numerically. This table records observed values and labels; it does not promote the labels to measured physical frequencies.

### IFR entries not accepted by this ABL table

|   Code | IFR option/default   | ABL1 outcome                         |
| -----: | -------------------- | ------------------------------------ |
| `0x26` | `1900MHz`            | TBB gap -> `0x232A` invalid path     |
| `0x27` | `1950MHz`            | TBB gap -> `0x232A` invalid path     |
| `0xFF` | `Auto` (IFR default) | range guard -> `0x232A` invalid path |

Other byte values are likewise invalid for this ABL selector: values below `2`, above `40`, and unsupported gaps inside `2..40`. The complete machine result records the exact dispatch outcome for all 256 byte inputs.

## Reproduction

```text
python3 /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1_ifr_enum_compare.py
```

Observed result: `21/21 PASS`.

Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1-ifr-enum-compare-result.json`.

Evidence class: `observed-bytes` and `static-analysis`. No firmware, settings, candidate, hardware, runtime, or MMIO operation occurred.

## Decision boundary

The correlation justifies carrying the ABL producer and IFR option table as a bounded candidate semantic link, but not merging their namespaces. The pending discriminating edge is still a direct producer/consumer path from token `7`/APCB-CBS output to the exact `AmdSetup+0x316`/`$INV 0x11ED` field or to a proven shared context. Until then, retain the result as static table correlation only.
