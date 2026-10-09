# 2026-09-21 BC-250 CLV 1:1:1 evidence-guide draft — action log

## Intent — 2026-09-21T14:57:50+05:00

- Actor: delegated project executor (Luna xhigh), root-owned integration.
- Scope: assemble an operator-facing **draft** from current exact CLV menu, baseline, voltage, and latency-protocol evidence. Separate proven static menu paths from not-ready profile claims. No ROM/NVRAM/register/hardware change, no benchmark, no board contact, no network search, and no shared memory edit.
- TARGET: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, plain CLV 5.00, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- User constraints carried into draft: preserve native `1800MHz` request; do not call equal numbers physical `MCLK:UCLK:FCLK=1:1:1`; treat SoC `1.15 V` as an unset target/constraint, not a safe rating; no voltage change; user may flash a later selected BIOS, but this draft authorizes no flash.
- Existing routes reused: `docs/research/2026-09-20-clv-native-menu-1to1-guide.md`, `docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md`, `docs/research/2026-09-21-hardware-baseline-consolidated.md`, `docs/research/2026-09-21-baseline-nvram-ledger.md`, `docs/research/2026-09-21-oc-decision-guide.md`, `docs/research/2026-09-21-latency-protocol-reviewed.md`, voltage evidence reports and the exact CLV decision record. No completed 47-check verifier is rerun.
- Expected effect: one draft guide with exact static paths, field meanings/boundaries, baseline capture protocol, latency/performance protocol, rollback, and explicit missing evidence. This is not goal completion and does not define final profile values.
- Output: `docs/guides/bc250-clv-111-evidence-draft.md`.
- Rollback: remove only the new guide and this action log; preserve source ROM, evidence, reports, and shared memory.

## Observed result — 2026-09-21 (Asia/Almaty)

- Created and reopened `docs/guides/bc250-clv-111-evidence-draft.md`; size `15,394` bytes; SHA-256 `cfa3e245d4f6bc368af7f0fe0262aa410a9d981556b61febece64a050f87faa8`.
- Draft binds plain CLV 5.00 as offline TARGET and separates: (a) static menu paths/QIDs/offsets and stored bytes; (b) historical/current identity limitations; (c) not-ready profile fields; (d) SoC/PUS1 versus core/GFX/PUA1 interpretation; (e) a planned B1800 baseline and 3-cold-boot × 5-trial latency/bandwidth protocol; and (f) settings-only and firmware-image rollback/stop rules.
- The draft explicitly leaves final values, physical `MCLK:UCLK:FCLK=1:1:1`, SoC `1.15 V`, training, performance improvement, and hardware acceptance unset/unproven. It does not create or modify a ROM/candidate.
- Reopened source reports used as citations: `docs/research/2026-09-20-clv-native-menu-1to1-guide.md`; `docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md`; `docs/research/2026-09-21-hardware-baseline-consolidated.md`; `docs/research/2026-09-21-baseline-nvram-ledger.md`; `docs/research/2026-09-21-oc-decision-guide.md`; `docs/research/2026-09-21-latency-protocol-reviewed.md`; `docs/research/2026-09-21-manual-voltage-safety-matrix.md`; `docs/research/2026-09-21-voltage-evidence-integration.md`.
- Formatting/readback check: report and log end with LF, contain no CR or trailing whitespace. No source ROM, shared memory, existing report, NVRAM, register, board, or hardware state changed. This is a draft, not task completion.

## Intent — independent ABL1 heap-populator verifier (2026-09-21T15:58:04+05:00)

- Latest completed artifact: `docs/research/2026-09-21-apob-abl-heap-populator.md`; exact verifier: `evidence/firmware-audit/20260921-apob-abl-heap-populator/heap_populator_verify.py` SHA-256 `41bdf4e173dc91e840f7d16e35281c878b37207c52d9d039ebb37185803d1f9f`.
- TARGET remains plain CLV 5.00 `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Command-array metadata search was limited to the selected artifact directory; if absent, execute the verifier named in its report/action log.
- Run in a disposable copied environment and persist only command/result evidence to unique directory `evidence/firmware-audit/20260921-heap-populator-independent-verify-155804-3347325`. Inspect whether 34 checks stop at source pointer `outer+0x864` versus proving applied clocks; do not extend the separate APOB join, memory item-0x17 route, or SMU-selector work.
- Then update only `docs/guides/bc250-clv-111-evidence-draft.md` and this owned action log with the verified static edge and unresolved join. No board/network/ROM/NVRAM/register/voltage action.

## Observed result — independent heap-populator verifier (2026-09-21T15:58:04+05:00)

- Command: `["/usr/bin/python3", "-B", "/tmp/bc250-heap-populator-verify-ociocbt3/evidence/firmware-audit/20260921-apob-abl-heap-populator/heap_populator_verify.py"]`; disposable CWD `/tmp/bc250-heap-populator-verify-ociocbt3`; verifier source `evidence/firmware-audit/20260921-apob-abl-heap-populator/heap_populator_verify.py` SHA-256 `41bdf4e173dc91e840f7d16e35281c878b37207c52d9d039ebb37185803d1f9f`.
- Literal stdout: `{
"status": "PASS",
"checks": 34,
"result": "/tmp/bc250-heap-populator-verify-ociocbt3/evidence/firmware-audit/20260921-apob-abl-heap-populator/heap-populator-result.json",
"first_unresolved": {
"location": "producer of the outer ABL1 object passed as R1 at 0xB84/0xBD2 and population/meaning of its +0x864 field (initialized with 0x006CD4D0) relative to AmdMem APOB service output and native INV 0x11ED",
"statement": "The exact HEAP node writer is now closed to a runtime field-backed source: provider key 0xA04E -> descriptor -> 0x6238 -> node key/payload. The first missing cross-stage edge is upstream of that field: no byte-backed path joins outer+0x864, APOB service 0x9E3B14C/message0x61/arg0xFF, and `$INV 0x11ED`; no training/clock/SMU actuator is claimed."
}
}`; literal stderr: ``; exit `0`; parsed machine result: `{"status": "PASS", "checks": {"passed": 34, "failed": 0, "total": 34}}`.
- Persisted unique output directory: `evidence/firmware-audit/20260921-heap-populator-independent-verify-155804-3347325`. `sha256sum -c` is required as final reopen step.
- Coverage qualification: the 34 checks establish only ABL1 heap-object/source-pointer bytes, including `outer+0x864 -> 0x006CD4D0`; they do not map that pointer to APOB/`$INV 0x11ED` or prove any applied clock. Missing join: Missing join: identify the producer/meaning of the outer ABL1 object R1 entering 0xB84/0xBD2, and prove whether outer+0x864/0x006CD4D0 is sourced from APOB service 0x9E3B14C (message 0x61, argument 0xFF), native $INV 0x11ED, or another runtime source. Do not follow the concurrent apob_abl_handoff, memory-clock item-0x17, or SMU-selector traces here.
- Updated the owned guide with only the verified edge and missing join; `NOT READY` remains. No other worker report/registry/memory was edited.

## G7 report-log wording correction — 2026-09-21T16:02:00+05:00

The previous action-log result line began `Missing join: Missing join:` because the summary prefix duplicated the report sentence. Its intended reading is one `Missing join:` followed by the outer-object/provider-source boundary. No evidence or finding changes. The deferred final evidence-manifest check was executed: `cd evidence/firmware-audit/20260921-heap-populator-independent-verify-155804-3347325 && sha256sum -c SHA256SUMS.final` returned exit `0`; all 7 entries were `OK`.
