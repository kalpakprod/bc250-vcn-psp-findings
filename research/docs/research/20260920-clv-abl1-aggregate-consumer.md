# Exact CLV ABL1 aggregate+0x2BC downstream consumer

## Result

A concrete in-payload consumer of the selected aggregate exists outside function `0x95FC`:

```text
Function 0x75CC receives context in r0
  -> r6 = r0
  -> 0x7E3E: r0 = [r6]
  -> 0x7E40: r6 = [r0 + 0x2BC]
  -> 0x7E52: r1 = r6
  -> 0x7E54: BL 0x751C
  -> result converted/stored and passed to BL 0x130C
```

Classifier `0x751C` loads a PC-relative halfword policy table (`0x751E`, table bytes at `0x7540`), compares the aggregate in `r1` against that table and returns class `0` or `7` based on its `r0` selector. The caller converts/stores the result and forwards it through `0x130C`.

This is a real downstream control-class consumer with shared-structure provenance. It is **not** evidence of MHz units, MCLK/UCLK/FCLK identity, a divider, 1:1 synchronization or hardware acceptance.

## Exact checks

- ABL1 payload SHA-256: `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- `0x75CC` prologue and `r0 -> r6` preservation checked.
- `0x7E3E` root load and `0x7E40` `[root+0x2BC]` load checked.
- `0x7E52 -> r1` and `BL 0x751C` checked.
- `0x751C` PC-relative policy-table load/bytes, compare/class return (`0`/`7`) checked.
- Post-class result conversion/storage and `BL 0x130C` presence checked.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-aggregate-consumer/abl1_aggregate_consumer_verify.py
```

Exit status: `0`; `18/18` checks passed.

Machine result: `evidence/firmware-audit/20260920-clv-abl1-aggregate-consumer/abl1-aggregate-consumer-result.json`.
Runner: `evidence/firmware-audit/20260920-clv-abl1-aggregate-consumer/abl1_aggregate_consumer_verify.py`.

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Boundary

The downstream owner of the aggregate is identified as an ABL1 control-classifier path. Its service `0x130C`, units and relation to native `$INV`/AGESA fields remain unresolved; no 1:1 or physical clock claim is made.
