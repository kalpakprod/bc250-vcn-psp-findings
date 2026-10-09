# Stage 2 supplemental — Native Memory P-state control mapping

> SUPERSEDED MAPPING: the final correction below establishes Setup+0x36D -> token0x123C, not 0x123D. Earlier PASS counts and output belong to the old pairing method. Do not use the opening mapping as current evidence.

## Conclusion

The exact clv native control matching the DF help phrase **“Memory P-state is disabled”** is:

- `AmdSetup + 0x36D`, `u8`, question `QID 0x25E`, label **Memory P-state**;
- form `0x7032` **DRAM Power Options**;
- options: `Auto=0xFF` (declared default), `Enabled=0x01`, `Disabled=0x00`;
- IFR flags `0x10`: reset-required, not callback, not read-only;
- no enclosing conditional scope in the exact forms package;
- unconditional CBS navigation path in this package: `0x7000 -> 0x7008 -> 0x702E -> 0x7030 -> 0x7032`.

A concrete native serializer maps this field to `$INV` record ID `0x123D`: `CbsBasePei` loads `Setup+0x36D` and stores it as the record value. The pinned clv NVRAM byte is currently `0xFF` (`Auto`), and the compiled default helper also writes `0xFF`.

This identifies the native control and serializer handoff. It does **not** prove that `Disabled=0` is accepted by memory training, that the DF override consumer reads record `0x123D`, or that it enforces FCLK/UCLK/MCLK synchronization. The help string remains UI guidance, not a hardware constraint.

## Pinned inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact `CbsSetupDxe`: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin`
- Module SHA-256: `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`
- Existing parser: `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py`
- Existing exact-menu report: `evidence/firmware-audit/20260920-df-init-route/menu-result.json`

## Exact IFR control and gating

Raw form walk on the exact module found:

```text
QID          0x25e
Form         0x7032 (DRAM Power Options)
VarStore     0x5000 (AmdSetup)
Offset       0x36D
Flags        0x10 (RESET_REQUIRED; no CALLBACK; not READ_ONLY)
Conditions   []
Options      Auto=0xFF [default], Enabled=0x01, Disabled=0x00
```

The question has no `SUPPRESS_IF`, `GRAY_OUT_IF`, or `DISABLE_IF` enclosing scope in the exact package. The CBS-only unconditional form-ref chain is:

```text
0x7000 AMD CBS
  -> 0x7008 UMC Debug Options
  -> 0x702E GDDR6 DRAM Debug Options
  -> 0x7030 GDDR6 DRAM Controller Configuration
  -> 0x7032 DRAM Power Options
```

This proves package-local navigation metadata only. Main AMITSE/external registration and live screen exposure remain unverified.

## Byte-backed serializer mapping

The retained exact `CbsBasePei` instruction records show:

|      RVA | Bytes          | Meaning                                   |
| -------: | -------------- | ----------------------------------------- |
| `0xA7C1` | `ba3c120000`   | begin `$INV` record ID `0x123C`           |
| `0xA7E1` | `8a826d030000` | load `AmdSetup+0x36D`                     |
| `0xA7E7` | `884103`       | store loaded byte to record value `+0x3`  |
| `0xA7F3` | `ba3d120000`   | begin `$INV` record ID `0x123D`           |
| `0xA7FB` | `668910`       | write record ID (following pointer setup) |

The `0x123D` record is the serializer handoff for `Memory P-state`. Downstream record consumer, physical domain meaning, training branch, and synchronization behavior are not established by this edge.

Direct pinned-ROM readback at `AmdSetup` body base `0x4CF`:

```text
body+0x36D = absolute ROM 0x83C = ff (255 / Auto)
```

The existing compiled default initializer writes the same `0xFF` at `CbsBasePei` instruction RVA `0x1D74`.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate/memory_pstate_verify.py
```

Observed exit status: `0`; stderr empty; `9864/9864` checks passed.

Observed stdout:

```text
{"checks": {"failed": 0, "passed": 9864, "total": 9864}, "current_raw": "0xff", "question": {"conditions": [], "flags": "0x10", "form": "0x7032", "label": "Memory P-state", "module_offset": "0x12870", "offset": "0x36d", "options": [{"default": true, "label": "Auto", "value": 255}, {"default": false, "label": "Enabled", "value": 1}, {"default": false, "label": "Disabled", "value": 0}], "qid": "0x25e", "varstore": "0x5000"}, "serializer_record": "0x123d", "status": "PASS", "unconditional_path": ["0x7000", "0x7008", "0x702e", "0x7030", "0x7032"]}
```

## Acceptance boundary and implication

- **PASS** — exact clv ROM/module hashes and direct current byte.
- **PASS** — native IFR question, options, default, flags, conditions, and package-local navigation.
- **PASS** — `AmdSetup+0x36D -> $INV record 0x123D` serializer edge.
- **UNRESOLVED** — downstream consumer of record `0x123D`, training/application semantics, units, and synchronization.
- **UNRUN** — BIOS browser execution, save/reset, firmware execution, hardware, clocks, voltage, and performance.

A candidate that claims to satisfy the DF help condition would need to set `AmdSetup+0x36D=0x00` (Disabled) through the native control or an equivalent authoritative path, then independently trace/read back the consumer and training result. The field mapping alone does not authorize or justify that change.

## Superseded mapping, 2026-09-23

Unequal-marker execution of unchanged native CbsBasePei proves +6A3 ->1331 and +36D ->123C. The earlier report paired the value load with the NEXT record ID across pointer increment. See docs/research/2026-09-23-zen2-bc250-parameter-map.md and evidence/firmware-audit/20260923-oc-parameter-map/discriminator/result.json. Other scope limits still apply.
