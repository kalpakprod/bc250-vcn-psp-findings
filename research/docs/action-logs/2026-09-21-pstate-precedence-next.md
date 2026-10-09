# P-state precedence follow-up — intent

- Timestamp: 2026-09-21T13:24:37+05:00
- Actor: `/root/pstate_precedence` (bounded executor)
- Target: exact CLV 5.00 ABL1 payload (`$PSP` type `0x31`) extracted from the pinned donor; read-only offline analysis.
- Scope: identify one previously unreported branch condition in exact ABL1 memory-policy code that may override a per-channel requested rate; do not repeat `AmdSetup` field serialization or generic token-census work.
- Baseline: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. Exact extracted ABL1: `evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; PSP type `0x31`, SPI container offset `0x99FD00`, `$PS1` size `0xC020` as recorded in the reopened exact provenance report.
- Existing route: `evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory-function/abl1_memory_function_verify.py` establishes the structural match of `ABL1+0x95FC` to a memory-speed synchronize routine, and its retained Thumb disassembly is evidence input. It does not test the count/status branch gate or the resulting min/writeback override. Reuse `/usr/bin/llvm-objcopy` and `/usr/bin/llvm-objdump`; no install/network.
- Hypothesis: the `0x95FC` shared-minimum path requires policy count greater than one and a nonzero helper status; it reduces the collected channel policy values to the minimum (zero values normalize to `0x7D1`) and writes that selected value back to all channels at `+0x20`. If true, this is an ABL1 internal override, not proof that the Setup fields `+0x316`, `+0x36D`, `+0x6A3`, UCLK, or DF feed it.
- Next executable action: produce a fresh narrow Thumb disassembly from the hash-pinned extracted ABL1 and run a byte-backed verifier for the branch target/gates, candidate min compare/update, and aggregate/channel writebacks. Preserve exact stdout, stderr, statuses, and hashes under `evidence/firmware-audit/20260921-pstate-precedence-next/`.
- Expected effect: one new static-analysis observation about ABL1 override precedence and one report. No firmware/ROM/NVRAM/register/hardware/source mutation, no candidate, no network, no tool install, and no shared memory edit.
- Stop condition: either the gate/min/writeback branch is byte-backed or a concrete command/disassembly failure is preserved; no inference of physical clock, 1800-MHz application, training acceptance, 1:1:1, or direct Setup-field linkage.
- Rollback: delete only `docs/research/2026-09-21-pstate-precedence-next.md`, this unique action log, and the uniquely named evidence directory. The pinned donor and prior evidence remain unchanged.

## First verifier attempt and correction intent

- Timestamp: 2026-09-21T13:27:10+05:00
- Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-pstate-precedence-next/pstate_precedence_verify.py > evidence/firmware-audit/20260921-pstate-precedence-next/verifier.stdout 2> evidence/firmware-audit/20260921-pstate-precedence-next/verifier.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260921-pstate-precedence-next/verifier.exit`
- Observed exit status: `1`; literal stdout reported `FAIL`, `19/47` checks; stderr empty. Source identity and Setup raw-byte checks passed. Twenty-eight disassembly-string checks failed because the verifier assumed tabs in `llvm-objdump` listing columns while the fresh output uses spaces. This is an assertion-format bug, not a disassembly/tool failure. The initial result/stdout/stderr/exit are preserved as `verifier.attempt1-*` before correction.
- Correction intent: modify only this task-owned verifier to normalize instruction rows by parsed address and regex-match the mnemonic/operands independent of column whitespace; preserve the attempt-1 evidence and rerun the same exact objdump-derived checks. No baseline/disassembly input changes.

## G7 terminology correction and final rerun intent

Fresh disassembly does not establish the semantic owners of stack slots `[SP+0x164]` and `[SP+0x174]`. The initial intent phrasing “policy count” / “helper status” is therefore narrowed: evidence shows only a `<=1` comparison on the value at `[SP+0x164]` and a zero/nonzero test of `[SP+0x174]`. Their meanings remain unknown. This correction changes labels only; branch targets, min/writeback bytes, the 47-check result, and all input hashes are unchanged. Before the final rerun, rename output labels to `slot_164` / `slot_174` and revise the research report to avoid semantic assignment.

## Observed result

- Timestamp: 2026-09-21T13:29:46+05:00 (+05:00)
- Fresh disassembly command: `llvm-objcopy -I binary -O elf32-littlearm -B arm evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin evidence/firmware-audit/20260921-pstate-precedence-next/ABL1-exact.o`; exit `0`.
- Fresh listing command: `llvm-objdump -D --triple=thumbv7 --start-address=0x95fc --stop-address=0x989e evidence/firmware-audit/20260921-pstate-precedence-next/ABL1-exact.o > evidence/firmware-audit/20260921-pstate-precedence-next/abl1-policy-95fc-989e.txt 2> evidence/firmware-audit/20260921-pstate-precedence-next/objdump.stderr`; exit `0`; stderr empty.
- Final verifier command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-pstate-precedence-next/pstate_precedence_verify.py > evidence/firmware-audit/20260921-pstate-precedence-next/verifier.stdout 2> evidence/firmware-audit/20260921-pstate-precedence-next/verifier.stderr`; exit `0`; literal stdout status `PASS`, `47/47` checks; stderr empty.
- Final machine result: `evidence/firmware-audit/20260921-pstate-precedence-next/pstate-precedence-result.json`, SHA-256 `76cf4c684d5e4caaf8a40372b2b5ac71bb851fd2f8c101742efdc3ec72ad87a9`.
- Final literal stdout SHA-256: `71da8ed4eb4bee377101cf0871e2261d739bb29e049b18bbdfcf290277130f4c`; verifier SHA-256: `b5d70cf67ca3c585d8dba3d09ff260d3e44fb8157c2f24b4919ac10333f31043`; fresh disassembly SHA-256: `af1c864b86e4fdd07801f55197e4a2c0157b3033a4913bb88739a8c4c752be81`; manifest SHA-256: `d185ac05a6eda50798d0826e1f1f49af022faea723dbc74957278cf24855d071`.
- Result: byte-backed branch precedence is reproduced. `[SP+0x164] <= 1` bypasses the multi-channel all-channel writeback; `[SP+0x164] > 1` is split by `[SP+0x174]` zero/nonzero; the gather route substitutes `0x7D1` for zero entries, selects a minimum, and writes it to context `+0x2BC` and channel `+0x20`. The exact field sources and helper semantics remain unresolved.
- No ROM, firmware, NVRAM, register, candidate, hardware, installation, network, or shared memory change occurred.
- Evidence manifest check: `sha256sum -c evidence/firmware-audit/20260921-pstate-precedence-next/SHA256SUMS.final` -> all `16` entries `OK`.
- Remaining uncertainty: branch slots `[SP+0x164]`/`[SP+0x174]` are not joined to `MemoryPstate`, `FclkDpm`, UCLK, DF, APOB, `$INV`, APCB, or AmdSetup. Physical rate, training, reset/default migration, and 1:1:1 remain unrun.

## Artifact-path correction

The first failed verifier outputs are preserved under `evidence/firmware-audit/20260921-pstate-precedence-next/attempt1/` (`pstate-precedence-result.json`, `verifier.stdout`, `verifier.stderr`, `verifier.exit`). The earlier phrase `verifier.attempt1-*` was shorthand and is superseded by these explicit paths; no evidence bytes or conclusions changed.
