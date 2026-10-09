# SMU clock entrypoint map — action log

## Intent (recorded before task evidence writes)

- Timestamp: 2026-09-21T14:20:50+05:00 (Asia/Almaty).
- Actor: `/root/smu_clock_entrypoints`.
- Target: immutable exact plain-CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; contained Robin-5 SMU payload and existing exact disassemblies/source maps.
- Preserved baseline: ROM `AmdSetup+0x316` is at absolute offset `0x7E5`, raw request byte `0x24` (exact-CLV IFR label `1800MHz`); this task will not modify ROM, Setup, NVRAM, or any candidate.
- Question/hypothesis: identify request-bearing SMU entrypoints for candidate memory/fabric clock control, separating them from Queue 0 query/telemetry commands. Candidate H1 is Queue 3 `0x1D` dynamic per-domain clock update; candidate H2 is Queue 5 `0x07` DF P-state selection. Their exact physical MCLK/UCLK/FCLK identities and caller linkage to `AmdSetup` fields may remain unresolved.
- Existing-route/G3 check: reuse `evidence/firmware-audit/20260919-oc-clock-provenance/verify-clock-handlers.py` (Q3 `0x1D` dispatch, data split, target-state update, actuator call) and `verify-fabric-domains.py` (Q5 `0x07` DF P-state entry, static table/rate mapping), plus their already-retained Ghidra instruction windows. These exactly address the bounded map; no duplicate analyzer, firmware extraction, `$INV` scan, or query-only probe is planned. Copies will differ only in result-output path so prior evidence files stay unchanged.
- Procedure: create only `evidence/firmware-audit/20260921-smu-clock-entrypoints-next/`; copy the two existing verifier scripts there, retarget their result JSON paths inside that unique directory, execute each with `python3 -B`, and capture stdout/stderr/exit. Reopen all captures/results and hash inputs/outputs before writing the research summary.
- Expected effect: exact, address-backed static map of request-oriented Q3 `0x1D` and Q5 `0x07` entry/callee chains and their encoded numeric units or unresolved units; no assertion that a request reached the board or that any named physical clock changed.
- Scope/safeguards: offline only; no board/register/NVRAM/network/install/ROM patch, candidate, flash, or other worker artifact modification. Source ROM and the 1800 request remain immutable.
- Rollback: remove only this task's unique evidence directory and report if the result is invalidated; preserve this append-only action log. Do not revert or alter any pre-existing evidence.

## G7 correction discovered during execution

The retained `verify-fabric-domains.py` and older reports label the `0x1E720` DF P-state entry as “Queue 5 msg 0x07” while reading dispatch offset `0x79EC`. Direct local source/API inspection shows the mailbox API defines queues `0..4`; the raw Robin-5 table places this entry at `0x79E8 + 4 = 0x79EC` under the table headed Queue 4 (`0x79B8` base), with Queue 5 starting at `0x7A60`. Therefore this report will name the byte-backed location `dispatch table 0x79E8/entry 0x79EC (raw table Queue 4, msg 0x07)` and retain “Queue 5” only as a historical label. The handler/callee bytes and result are unchanged; the queue-number label is corrected, not the control-flow finding.

Measurement disproving the old label: `raw_messages__smu_fw_robin_5.txt` records Queue 4 at `0x79B8` and msg `0x07` at `0x79E8`, while `bc250_smu/api.py` defines queue IDs only `0,1,2,3,4`; `0x79EC` contains handler pointer `0x0001E720`. No hardware action occurred.

### Queue-label wording refinement

The `Queue 5` spelling in older notes / `Queue4Mixin._q5_0x07` is a one-based or legacy method label; it is not a different physical request path. The byte-backed raw map and API integer are Queue ID `4`, message `0x07` (`0x79E8` entry, `0x79EC` handler pointer). State both labels with that qualification to avoid a second off-by-one inference. The table/callee result remains the same.

## Result and readback

- Both reused verifiers started and exited `0`; `source-check.stderr` is empty.
- Exact CLV/Robin-5 identity and preserved `AmdSetup+0x316=0x24` checks passed.
- Machine summary: `evidence/firmware-audit/20260921-smu-clock-entrypoints-next/clock-entrypoints-summary.json`, SHA-256 `4427add2890006487b397516111709ba6f74f56764eecd3498a6150eddae98e0`.
- Queue correction capture: `queue-map-correction.txt`, SHA-256 `ec8a452452eb72c264f84869a72487682d11883c537681a600ae2eedee91e441`.
- Final evidence manifest: `SHA256SUMS.final`, SHA-256 `345d48c51222c34ee4622217da558f179df5bcf5f58e1ba779252237e5d79507`; `sha256sum -c` returned `OK` for every listed artifact.
- Research report was reopened after writing; final SHA-256: `7988f9d29124659c4b72c6e0389db2604a1d44a704fb3a3d8793e66c7262fc37`.
- Remaining status: static request candidates identified; provider-to-Setup/ABL1 join, physical clock identity/units, hardware invocation and acceptance remain unresolved/unrun.
