# Stage 2 supplemental — Distinguishing Memory P-state, Phy Power Saving, and FCLK_DPM

> Audit 2026-09-27: literal Observed stdout below is from the earlier superseded mapping and intentionally retained. Its 0x1238/0x123D/0x1332 IDs are not the corrected table (0x1237/0x123C/0x1331). An old PASS does not validate the corrected revision.

## Result

The exact clv native controls are three distinct bytes/questions/serializer records:

| Control            | AmdSetup offset | IFR QID / form                            |      Flags | Exact enum/default                         | CbsBasePei `$INV` record |
| ------------------ | --------------: | ----------------------------------------- | ---------: | ------------------------------------------ | -----------------------: |
| Phy Power Saving   |         `0x368` | `0x259` / DRAM Power Options `0x7032`     |     `0x10` | Auto `0xFF`, Enabled `1`, Disabled `0`     |                 `0x1237` |
| **Memory P-state** |     **`0x36D`** | **`0x25E` / DRAM Power Options `0x7032`** | **`0x10`** | **Auto `0xFF`, Enabled `1`, Disabled `0`** |             **`0x123C`** |
| FCLK_DPM           |         `0x6A3` | `0x7045` / SMU Features `0x703E`          |     `0x14` | Disabled `0`, Enabled `1`, Auto `0x0F`     |                 `0x1331` |

Therefore the DF help phrase's “Memory P-state is disabled” maps by label to `AmdSetup+0x36D`, not `Phy Power Saving +0x368` and not `FCLK_DPM +0x6A3`. This is a static UI/serializer mapping only.

## Direct profile bytes

At `AmdSetup` body base `0x4CF`:

| Field                     |    clv absolute/raw | historical ULTIMATE absolute/raw |
| ------------------------- | ------------------: | -------------------------------: |
| Phy Power Saving `+0x368` | `0x837 = FF` (Auto) |          `0x837 = 00` (Disabled) |
| Memory P-state `+0x36D`   | `0x83C = FF` (Auto) |          `0x83C = 00` (Disabled) |
| FCLK_DPM `+0x6A3`         | `0xB72 = 0F` (Auto) |          `0xB72 = 00` (Disabled) |

The ULTIMATE filename/profile does not distinguish these three controls: it disables all three. It cannot serve as evidence that only the Memory P-state field satisfied the DF help text.

## Serializer bytes

Exact `CbsBasePei` bytes independently checked:

- `+0x368`: record header `0x1237` at RVA `0xA6C7`, then load/store at `0xA6E7/0xA6ED`.
- `+0x36D`: record header `0x123C` at RVA `0xA7C1`, then load/store at `0xA7E1/0xA7E7`.
- `+0x6A3`: record header `0x1331` at RVA `0xD9E0`, then load/store at `0xDA00/0xDA06`.

The default initializer independently writes `+0x368=FF`, `+0x36D=FF`, and `+0x6A3=0F` at RVAs `0x1D42`, `0x1D74`, and `0x294B`.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate-discrimination/discrimination_verify.py
```

Observed exit status: `0`; stderr empty; `19/19` checks passed.

Observed stdout:

```text
{"checks": {"failed": 0, "passed": 19, "total": 19}, "profiles": {"FclkDpm": {"absolute_clv": "0xb72", "body_offset": "0x6a3", "clv": 15, "ultimate": 0}, "MemoryPstate": {"absolute_clv": "0x83c", "body_offset": "0x36d", "clv": 255, "ultimate": 0}, "PhyPowerSaving": {"absolute_clv": "0x837", "body_offset": "0x368", "clv": 255, "ultimate": 0}}, "records": {"FclkDpm": "0x1332", "MemoryPstate": "0x123d", "PhyPowerSaving": "0x1238"}, "status": "PASS"}
```

## Boundary

- **PASS:** exact labels, offsets, QIDs, forms, enum/default encodings, profile bytes, and serializer record IDs.
- **UNRESOLVED:** downstream consumers, actual FCLK/UCLK/MCLK application, training acceptance, and whether disabling one/all controls creates synchronous operation.
- **UNRUN:** BIOS UI save/reset, firmware execution, hardware, voltage, clocks, latency, and performance.

The help text remains generic UI guidance and is not promoted to a hardware constraint.
