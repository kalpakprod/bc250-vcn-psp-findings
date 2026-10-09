# Action Log: 2026-09-19 OC Clock Actuator Chain & Handler Provenance

## Retrospective Discrepancy Log

- Discrepancy 1: Prior worker promised durable research report `docs/research/oc-clock-actuator-chain.md`, but root direct read showed it DID NOT EXIST on disk (prior worker only modified `verify-clock-handlers.py`, `clock-handlers-verification.json`, `docs/research/oc-clock-handler-provenance.md`, and Ghidra project metadata).
- Discrepancy 2: Prior worker report path `.empryo/dispatch/tab-2b1b21ce-2a6d-4a9d-bf6c-9de206ecb4cb/call_UgB5kSwks9qhwTsi0d3Vy1sr/agent-1.md` was not found as a separate standalone file on disk (retrieved via session checkpoint `6ac4eccd-10c1-48fb-8286-4a520937c5da/session.jsonl`).
- Discrepancy 3: Untrusted temp decompilations `/tmp/gh_clock_actuators.txt`, `/tmp/gh_clock_deep.txt`, and `/tmp/gh_pstate_trace.txt` were generated without prior byte-pinning against the authoritative binary. Byte-level verification against Robin-5 (`cae8617c...`) now confirms 269, 349, and 37 instruction sequences match with 0 mismatches.
- Discrepancy 4: Prior research claimed "applied frequency" for internal firmware state floats at `0x13F48`. Without physical hardware readback or PLL counter sampling, these represent **software committed state floats**, not verified live physical clock frequencies.

## Intent — 2026-09-19T23:05:00+05:00

- Actor: code / RE agent.
- Model limitation: Configured default model/effort unverified; local offline evidence/docs only; NO originals, candidates, builder, hardware, or network writes.
- Scope:
  1. Verify claimed 1-based domain index 1..20, formula `0x1402c + index * 12`, row stride 100 and 80-byte window offset `0x48`:
     - Confirm `0x1402c` is a prebiased base (`0x14038 - 12`) for 1-based index `1..20`.
     - Evaluate `0x7b5c + pstate * 100 + 0x48` in `FUN_0002e9dc`: note that reading 80 bytes (20 uint32 entries) from offset `0x48` (72) exceeds 100 bytes (reaches offset 152), but preserve uncertainty (structure-of-arrays or prebiased base) before claiming an overlap bug.
  2. Trace findings from verified decompilations into exact helper -> register evidence:
     - `FUN_0002e788` -> `FUN_00023890` -> `FUN_000235c8` -> SMN apertures `0x0115Bxxx`, `0x0116Cxxx`, `0x0116Dxxx`, and Domain 0x13 gate `0x01D80414`.
     - Confirm absence of UCLK, UMC, or DF register accesses in this chain.
  3. Correct unsupported "applied" frequency claims to "software committed state" without hardware readback.
  4. Write `docs/research/oc-clock-actuator-chain.md` with evidence classes, exact commands, known edges, and unknowns.
  5. Update `verify-clock-handlers.py`, `clock-handlers-verification.json`, `docs/research/oc-clock-handler-provenance.md`, and `memory/oc-recheck.md`.
  6. Confirm artifact existence via readback before claiming completion.

## Follow-up Review Correction & Helper Disassembly Archive — 2026-09-19T23:45:00+05:00

- Corrected overstatement: absence of DF/UMC register addresses in the observed SMN loop cannot prove UCLK is not controlled (clock generator or PLL architecture may use other apertures or indirect mechanism).
- Memory `memory/oc-recheck.md`, research doc `docs/research/oc-clock-actuator-chain.md`, and verifier JSON `evidence/firmware-audit/20260919-oc-clock-provenance/clock-handlers-verification.json` corrected to 'UCLK mapping/control unestablished; observed address set only'. No claim of physical clock synchronization.
- Ran Ghidra analyzeHeadless with `OcConsumerRead.java` on pinned Robin-5 (cae8617c...) and clv ROM (ea578104...) at offset 0x8FEF00 to archive disassembly and decompilation of helpers 0x23890, 0x235c8, 0x23994, 0x23ab0, 0x23ac4, 0x23c78 under `evidence/firmware-audit/20260919-oc-clock-provenance/ghidra-helpers-decompiles.txt`.
- Explicitly scoped helper findings as static disassembly only; verifier does not cover dynamic dispatch or indirect routing.
- Verified test suite passes and ROM / SMU hashes remain completely untouched.
