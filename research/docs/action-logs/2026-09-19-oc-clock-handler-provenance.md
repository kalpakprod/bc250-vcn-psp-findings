# Clock Handler Provenance Action Log

## Intent — 2026-09-19T22:35:00+05:00

Actor: code / RE agent.
Task: OFFLINE BC250 exact clock provenance investigation. Root retains scope/integration/hardware decisions.
Model limitation: Configured default model family/model/effort requested, effective identity UNKNOWN unless runtime discloses; no effort override supported.
Permissions: local reads/existing tooling, new evidence/report/log writes only. NO hardware/network/flash/ROM/candidate/builder/probe edits.

## Hashes Verified

- ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, 16,777,216 bytes).
- SMU: `import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` (SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, 262,400 bytes).
- SMU body matches ROM offset `0x8FEF00` byte-for-byte.

## Execution & Artifacts

- Ran Ghidra analyzeHeadless with `-readOnly -noanalysis` using `OcConsumerRead.java` over handlers `0x2ea74`, `0x1e988`, `0x2e788`, `0x2e9dc`, `0x2ea0c`, `0x1e720`, `0x1e090`, `0x2b634`.
- Created deterministic verification tool `evidence/firmware-audit/20260919-oc-clock-provenance/verify-clock-handlers.py` and generated `clock-handlers-verification.json`.
- Archived decompilations and instruction listings in `evidence/firmware-audit/20260919-oc-clock-provenance/ghidra-decompiles.txt`.
- Deliverable report: `docs/research/oc-clock-handler-provenance.md`.
