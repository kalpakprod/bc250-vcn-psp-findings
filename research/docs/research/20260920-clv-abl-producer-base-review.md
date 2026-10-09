# Exact ABL1 producer callback and conditional base `0x57100` review

## Result

Independent raw checks corroborate the corrected producer evidence with a **conditional** runtime-base hypothesis:

- Four absolute pointer literals map under base `0x57100` to local Thumb code:
  - `0x67ABD` → Thumb `0x109BD`, code entry `0x109BC` (`push {r0,r1,r4,lr}`), callback stored in `[r0+0x52C]`.
  - `0x67A95` → Thumb `0x10995`, code entry `0x10994` (`cbz r1`).
  - `0x61E19` → Thumb `0xAD19`, code entry `0xAD18` (`push {r4,r5}`).
  - `0x67A59` → Thumb `0x10959`, code entry `0x10958` (`push {r4,r5}`).
- Producer path: `0x7548 -> r5=[r0+4]`, `0x757C -> [r5+0x60]=0x0320`, `0x7586 -> BL 0x75CC`, then `0x7E00 -> BL 0xAD58` and `0x7E30 -> BL 0x10CC0`.
- The callback at `0x109BC` uses the indexed channel count and writes `[context+0x0C]`; the producer functions write the same per-channel `+0x20` field.
- Classifier literal `0x6DB04` maps under `0x57100` to payload `0x16A04`. Raw halfwords there are:
  `0x06D6, 0x0532, 0x0532, 0x0352, 0x00E1, 0x0000, 0x0000, 0x00E1`.

This is conditional static address coherence, not proof of loader/runtime base. No units or physical-domain meaning is assigned to the table values.

## Boundary

The exact `0x95FC` function still has no direct in-payload `BL/BLX` caller. The callback/producer path is a recovered local edge around the same context and `+0x20` field, but invocation and loader relocation remain unresolved. No MHz, MCLK/UCLK/FCLK, synchronization, training, or hardware result follows.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-abl-producer-base-review/abl1_producer_base_verify.py
```

Observed status: `28/28 PASS`.

Owned result: `evidence/firmware-audit/20260920-clv-abl-producer-base-review/abl1-producer-base-review-result.json` — SHA-256 `ecb7953571d3b008e76798718d216362bf819a4b0ffcb3dc52da58e23e2c483b`.
