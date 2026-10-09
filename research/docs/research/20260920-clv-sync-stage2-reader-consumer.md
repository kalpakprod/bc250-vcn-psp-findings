# CLV phase-2 concrete CCX reader consumer

## Result

The exact `AmdCcxVhAriDxe` reader at RVA `0x5AC4` is a concrete INV parser whose token input is `CX` (`0x5ADC: 44 0F B7 E1`), whose NVTB/`$INV` header path is byte-backed, and whose token compare is at `0x5C32`.

Its complete parent function (`0x5C68..0x5DA4`) requests:

- token `0x1000` at `0x5CA5`, then consumes returned value in a guarded `WRMSR` path using MSR `C0011029` (`0x5CBC`);
- token `0x1001` at `0x5CF1`, then consumes returned value in a guarded `WRMSR` path using MSR `C0011023` (`0x5D05`).

This is a concrete non-FCLK/UCLK/MemoryPstate CPU-control handoff. It closes the CCX reader branch as unrelated to corrected targets FCLK `0x1331`, UCLK `0x1204`, and MemoryPstate `0x123C`, without making a census-wide absence claim. The relevant clock-token requester remains at the Fabric/AGESA ownership boundary.

## Exact consumer evidence

| Reader request | Parent use                                 | Handoff                                                        |
| -------------: | ------------------------------------------ | -------------------------------------------------------------- |
|       `0x1000` | `r8` returned value checked against `0xFF` | read/modify/write MSR `C0011029` at `0x5CBC`, `WRMSR` `0x5CE5` |
|       `0x1001` | `r8` returned value checked against `3`    | read/modify/write MSR `C0011023` at `0x5D05`, `WRMSR` `0x5D34` |

The reader itself selects 1/2/4/8-byte record widths, writes the decoded value through the caller result pointer, compares the record token against `R12W`, and returns a match/not-found status. The parent then uses the decoded value in CPU MSR bitfields, not a fabric/memory clock register.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-reader-consumer/ccx_reader_consumer_verify.py
```

Exit status: `0`; `22/22` checks passed.

Machine result: `evidence/firmware-audit/20260920-clv-sync-stage2-reader-consumer/ccx-reader-consumer-result.json`.
Runner: `evidence/firmware-audit/20260920-clv-sync-stage2-reader-consumer/ccx_reader_consumer_verify.py`.

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Boundary

This proves a concrete non-clock INV consumer and its CPU MSR handoff. It does not prove absence of computed/indirect clock consumers; it identifies the remaining target boundary as Fabric/AGESA configuration ownership after `$INV` construction.
