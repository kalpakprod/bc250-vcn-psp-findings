# SMU domain 0x18 identity — action log

## Intent (recorded before evidence writes)

- Timestamp: 2026-09-21T17:58:33+05:00 (Asia/Almaty).
- Actor: continuation executor (root-owned offline analysis scope).
- Active object: immutable CLV donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`) and exact embedded Robin-5 SMU body at ROM offset `0x8FEF00` (262,400 bytes, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`). Preserved request byte: `AmdSetup+0x316`, ROM `0x7E5`, value `0x24` (`1800MHz` IFR label); no source bytes or request values may change.
- Last confirmed result: Queue-3 selector 11 maps dynamic domain ID `0x18` through an internal Group-6 descriptor to program/poll window `0x0116D150/0x0116D174`; this is static path identity, not a physical clock name. The prior exact-CLV report and independent register-header corroboration report still do not name the target as MCLK/UCLK/FCLK. Historical Robin-3 slot-map entry 24 uses domain index 6/raw `0x6D150`, with `semantic_name=null`; Robin-3 is cross-version evidence only.
- Question: does a narrow exact Robin-5 slice through the generic slot metadata and metrics exporter create an address-backed semantic edge from domain ID `0x18` / raw `0x6D150` to a named physical clock, or does slot 24 remain unlabelled even if sibling Group-6 slots are labelled?
- Existing route check (G3): reuse existing Ghidra 12.1.3 headless executable, copied `OCConsumer` project, and inspected `OcConsumerRead.java`; the script checks complete program memory against the exact input body and accepts an explicit address list. Use only aligned functions `0x2387C`, `0x2375C`, `0x23CB4`, `0x29E34`; do not repeat the earlier 301-instruction Queue-3 listing, selector/table census, or register-header match test. Read existing exact-Robin-5 metrics listing only for comparison, and search the bounded local symbol/source corpus for slot-24 / `0xFA38` names.
- Hypothesis: the descriptor/program destination and group relationship are provable, but exact physical identity of the selector's slot remains unresolved. Sibling metric labels (if found) do not transfer by association to slot 24.
- Procedure: create `evidence/firmware-audit/20260921-smu-domain18-identity/`, copy the existing Ghidra project into that disposable area, run the focused script slice against the pinned exact body, preserve stdout/stderr/status/listing and the copied-project readback. Record direct local symbol/source hits and classify exact Robin-5 versus Robin-3/external evidence separately.
- Acceptance event: the focused Ghidra process starts and exits with captured status and instruction/decompile output; the exact input/output hashes, relevant local hits/no-hits, and limitations are reopened before report completion.
- Scope: offline only. No board, hardware, register, mailbox, sysfs, NVRAM, network, install, firmware, or ROM action; no new tool install or worker dispatch.
- Rollback: remove only the new report `docs/research/2026-09-21-smu-domain18-identity.md` and its unique evidence directory if invalidated. Preserve the target ROM, all existing evidence/projects/reports, and this append-only action log.

## Boundary adjustment before follow-up slice

- Observed result from the first focused run: Ghidra exit `0`, whole-memory check passed, and the exact current Robin-5 `FUN_00029E34` listing was captured. Address `0x23CB4` was not an existing function in the copied project, so the script emitted no disassembly for that requested entry; this is an analysis database boundary, not a firmware error.
- Correction: prior imported decoder notes describe `0x23CB4` as a writer, but that note is not itself exact current Robin-5 Ghidra function evidence. To avoid repeating the same missing-entry request, use a second disposable copy and probe the nearby aligned function entry `0x23CB8` plus the preceding call window `0x23CA8`. Keep any result as current Robin-5 static evidence only; do not transfer Robin-3 slot semantics.
- Expected effect: either capture the exact current writer/decompiler slice or preserve a bounded unresolved boundary; no input or project source changes.

## Observed result (2026-09-21)

- Exact donor/body rehash matched the pinned values; ROM `0x7E5` remained `0x24`; `dd` of the ROM slice at `0x8FEF00` yielded the same Robin-5 body SHA-256. The copied `OCConsumer` project was byte-identical to its source before analysis; the original project manifest later rechecked 18/18 entries.
- Focused Ghidra command on the first copied project started and exited `0`; output begins `PASS: entire loaded program memory equals clv-matching robin-5 body, bytes=262400`. It decoded `0x2387C`, `0x2375C`, and `0x29E34`, but reported `0x23CB4 NO EXISTING FUNCTION`.
- Corrected boundary follow-up used another copied project and aligned `0x23CB8`; it exited `0`, passed the same 262,400-byte memory equality, and decoded `FUN_00023CB8`. This helper shows float/integer arithmetic only; no physical clock-name edge was found. `0x23CA8` did not resolve as a function entry and is not interpreted.
- Current Robin-5 `FUN_00029E34` exports source-float fields from `0xF904`, `0xFA00`, `0xFA1C` to metric offsets `+0x48`, `+0x4C`, `+0x4A`; its bounded body does not access program/poll target `0x0116D150/0x0116D174`. Adjacent VCLK/DCLK field names in older/interface evidence do not assign this dynamic domain to a physical clock.
- Raw byte readback confirms pointer cell `0xFA5C` = `0x0006D150`; the exact prior selector trace labels the descriptor as internal Group 6. The old Robin-3 map has `semantic_name=null` and is cross-version only.
- Scoped source search exited `0` (matches found), stderr empty; it found internal/historical Group-6/slot labels and false hits from the unrelated SMU tick-handler slot table / ABL disassembly, but no physical name for this current target. Reused register-header result remains `NO_DIRECT_HEADER_MATCH` (4/4 bounded checks passed; zero address literals), with its 5/5 artifact manifest rechecked.
- Conclusion: **internal Group 6/address path is static-proven; physical MCLK/UCLK/FCLK/VCLK/DCLK/VCN identity is unresolved.** Hardware/physical counters remain unrun.
- Observed tool errors and correction are preserved in `VERIFICATION.txt`: `xxd` unavailable (exit 127), replaced with Python raw-byte extraction (exit 0); one manifest-check command used the wrong cwd and printed open/read failures, then the corrected root-relative manifest check passed 18/18. No input/source project was modified.
- Evidence directory: `evidence/firmware-audit/20260921-smu-domain18-identity/`; new report: `docs/research/2026-09-21-smu-domain18-identity.md`.

## Final artifact readback

- Final report path reopened: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-smu-domain18-identity.md`; SHA-256 at report readback: `644a12f1cad5c9542756e54027b2f1d54e23236fc400aa67a94ecb1043c086e6`.
- Machine result reopened and JSON-parsed: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smu-domain18-identity/domain18-identity-result.json`; SHA-256 `f4a005400dba428ff8ba8f782d67bfa608c9e5fc714c5771075c48d6467e5cbe`.
- `SHA256SUMS.final` SHA-256 `1a85994ae38eb24fa28034ea609885a2f5ec38f1ed2cd559f522e4bce03f33f2`; all 20 listed evidence files verify `OK`. Both copied-project manifests separately verify all 18 entries each.
- `VERIFICATION.txt` SHA-256 is covered by the final evidence manifest and records commands, inputs, literal captures/statuses, hashes, and the observed tool-error corrections.
- Original ROM, SMU body, prior reports, prior evidence directories, and original Ghidra project remain unchanged by this task.
