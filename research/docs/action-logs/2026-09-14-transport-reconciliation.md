# Transport reconciliation (2026-09-14, Asia/Almaty)

## Intent

- Offline-only source reconciliation of the historical gasket replay, D19 DXE, and SMU message table. No board access, flash, or register writes.

## Evidence

- `bc250_smu/primitives.py::smn_write32()` performs Q3 `0x2B` (set SMN write address) followed by Q3 `0x2C` (SMN write value).
- `recon/smn_vcn_gasket_unclamp.py` calls `smu.smn_write32()` for each gasket record; therefore its source path is also Q3 `0x2B/0x2C`.
- The exact D19 PE disassembly contains Q3 `0x2B`, Q3 `0x2C`, SMN address `0x0900C830`, and value `0x00FFFFFB`.
- `community_msg_table_fixed.out` identifies Q3 `0x98` as an undocumented normal handler (`flags=0x00000006`), while Q3 `0x2B/0x2C` are the gated secure SMN-write pair (`flags=0x00000201`).

## Result

- The prior transport-split hypothesis is rejected: available source does not show the successful gasket replay using Q3 `0x98`. Q3 `0x98` remains an unresolved handler, not a proven alternate SMN-write primitive.
- D19's failure is therefore associated with execution context/timing and target-island state, not a demonstrated `0x98` versus `0x2B/0x2C` difference.

## Next static work

- Decode the handler at SMU SRAM `0x280E0` from the preserved PMFW body and identify its arguments and side effects. Do not invoke it on hardware solely from the numeric table entry.
- Map the exact PEI-time DF pair list and identify whether the relevant bridge/isolation state is established before PEI execution. No candidate flash image is built in this record.
