# Host influence recheck

## Intent — 2026-09-20T00:11:04+05:00

Actor: root. Scope: offline documentation correction and callback tracing; no firmware or hardware writes.
Root read the table-population report and verifier and ran `python3 scripts/verify_df_table_population.py`: PASS. The verifier checks static data, not exhaustive writers. The report's universal no-DMA/no-host-write conclusion exceeds those checks. Callback 0x1BC80 explicitly calls 0x21E8C and conditionally 0x1E010; their effects must be inspected before claiming isolation. Static defaults do not prove immutability. DDR4/GDDR6 rate equivalence and physical domain labels remain unsupported.
Procedure: append G7 correction to memory, correct report, inspect existing callback callees using pinned evidence and existing tooling. Preserve source/candidate bytes. Rollback: retain prior conclusions as superseded history; restore only this turn's documentation if required. No signed PMFW patch is authorized by these findings.

## Worker Intent & Callee Investigation — 2026-09-20T00:35:00+05:00

Actor: code / RE worker agent.
Scope: Offline bounded investigation of callback `0x1BC80` exact callees (`0x21E8C` and conditional `0x1E010`), tracing downstream side effects, register writes, and DF influence.
Baseline inputs confirmed:

- ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, size 16,777,216 bytes).
- SMU: `import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` (SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, size 262,400 bytes).
- Byte correspondence: ROM offset `0x8FEF00` matches SMU body byte-for-byte.
  Tooling & Execution:
- Executed read-only Ghidra headless decompiler script `OcConsumerRead.java` over disposable project `evidence/firmware-audit/20260919-oc-final-consumer-pass/project/OCConsumer` to decompile and dump raw assembly for `0x21E8C`, `0x1E010`, `0x000014FC`, `0x1CBFC`, `0x1CD80`, `0x223B8`, `0x1E448`, and `0x1EF18`.
- Output archived in `evidence/firmware-audit/20260919-oc-final-consumer-pass/smu-pptable-callees-decompiles.txt`.
- Bounded verification updated in `scripts/verify_df_table_population.py`.
- Research documentation updated in `docs/research/oc-df-table-population.md` and new comprehensive side-effects report created at `docs/research/oc-pptable-df-side-effects.md`.
- No originals, candidates, builder scripts, hardware, or network modified. Offline static analysis and documentation only.

## Root verification and correction

Root independently executed pinned-SMU literal/instruction assertions: literal at 0x17120 = 0x7EDC; flag address = 0x7F5A, full PPTable offset = 0x3FE (not 0x7E). Call/store bytes at 0x1BCD2, 0x1BCDA, 0x1E02D matched. Corrected both stale report expressions. Withdrew unsupported DDR4/GDDR6 equivalence and separated authorized offline candidate work from flash approval. `python3 scripts/verify_df_table_population.py` returned BOUNDED_STATIC_CHECKS_PASSED; `python3 -m unittest discover -s tests -q` ran 11 tests, OK (1.836s). These tests do not establish physical clock mapping, runtime isolation or board stability. Worker Ghidra workspace index metadata changed; original-image preservation is distinct from workspace immutability.
