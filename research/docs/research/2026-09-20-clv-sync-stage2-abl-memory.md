# Stage 2 — Exact ABL1 memory-policy source/binary applicability

## Bounded falsification result

The exact clv ABL1 payload is recovered and hash-pinned:

- PSP type `0x31`, SPI offset `0x99FD00`, `$PS1` container SHA-256 `95ae7826a69ea56b8c52ac703b85f181d45bdc309de334c2b7f9f4130376d515`.
- zlib-decompressed payload length `94624`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- ARM entry bytes `10402de904209fe532ff2fe11080bde8`.

Historical `ABL1_decompiled.c` is version-label aligned (`d00_e09_ABL1~0x31_22.4.6.0`) and contains a memory-speed/P-state routine lead (`FUN_000096fc`), but direct source-to-current-binary applicability is **falsified at the address-anchor level**:

| Historical source string/address                               | Exact clv decompressed string offset | Direct address match |
| -------------------------------------------------------------- | -----------------------------------: | -------------------: |
| `Determine DRAM Target MEMCLK` @ `0x82D4`                      |                             `0x81D4` |                   no |
| `Synchronize MEMCLK Across Channels and Set Limits` @ `0x99D8` |                             `0x820C` |                   no |
| `Memory P-state Enabled.` @ `0x8370`                           |                             `0x8271` |                   no |
| `Memory P-state Disabled.` @ `0x838C`                          |                             `0x828D` |                   no |
| `Current Memory P-state: %d` @ `0x894C`                        |                             `0x884D` |                   no |

Bytes at each historical address are different payload text/code, not the named anchor. Thus the retained source cannot be applied to exact clv as a bound function/control-flow map. This does not prove algorithmic dissimilarity; it proves that a further ARM disassembly/dataflow match is required.

## Acceptance boundary

- **PASS:** exact clv ABL1 container extraction/decompression/hash/ISA.
- **PASS:** version-aligned historical source provenance retained.
- **PASS:** five direct source-address versus exact-payload string-anchor mismatches.
- **UNRESOLVED:** exact ABL1 memory training function, input structure, units, and consumer of `AmdSetup+0x316`/INV `0x11ED`.
- **UNRUN:** ARM payload execution, firmware/hardware/training, clocks, voltage, settings.

No signed blob, ROM, firmware, hardware, plan, memory, or shared service was modified.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/abl_memory_falsification.py
```

Observed exit `0`; stderr empty; `21/21` checks passed. Exact decompressed payload is retained as `ABL1-clv-decompressed.bin` in the own evidence directory.
