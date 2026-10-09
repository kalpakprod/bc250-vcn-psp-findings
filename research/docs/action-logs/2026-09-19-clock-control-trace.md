# R2 clock-control and telemetry trace

## Intent — 2026-09-19T17:34:41+05:00

Root owns the coupled local trace and evidence; no delegation. Scope: hash-pinned clv firmware and retained driver source, no board operations. Reuse firmware_audit.Extractor for selected CBS/SMU executables; inspect code with local disassembly where applicable. Existing IFR map is historical and not a consumer proof.
Targets: evidence/firmware-audit/20260919-clock-trace/ (selected module copies, test harness and JSON report), docs/research/2026-09-19-clock-control-trace.md, append memory/oc-recheck.md, update plan/task status.
Input: evidence/donor/retroweb-20260916/BC250_5.00_clv.bin expected SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8; little-endian 16 MiB SPI. Retained cyan_skillfish_ppt.c is a source snapshot, not certified identical to the installed kernel.
Procedure: verify input hash and selected NVAR fields; extract selected CBS/SMU executable bodies with existing walker; capture exact source assignments and execute a small C harness generated from those assignments against distinct synthetic clock values. Search control-consumer offsets in selected executable disassembly; preserve unknown links rather than infer them from IFR labels.
Expected effect: reproducible measurement-provenance verdict and bounded firmware consumer map. Rollback: remove only newly generated reports/copies if requested. Original images and source remain unchanged. No new dependency, candidate, flash or runtime register access.

## Result

PASS: pinned clv hash and 16 MiB size; five selected modules extracted using existing parser. Ten load/serialization windows validated directly against TE file bytes; all five record IDs agree in CbsBasePei and AmdNbioSmuV10Pei. trace.json SHA-256 140a9867cd9025bcaff9d4d02b1f7e0918b9a284a9b7bb6b92e7ba109410414c; serialization.json SHA-256 66fc967e825f6776a4093e8c6430d66ad4a4e13a0b199bc5f7bc9ec9bb630ed7.
PASS: GCC 16.2.1 compiled telemetry-alias.c with -Wall -Wextra -Werror; exact copied source assignments produce duplicate UCLK/FCLK outputs for Current=1750 and Average=1333. Harness SHA-256 4208e3720f8e9d464f8e3acff8bbfd429155d8e7c58efb24f5e1b9c7dcc472e4.
Tool limitation: system Python capstone import failed (module absent). Used installed GNU objdump 2.47 instead, no installation. PE flag warnings IMAGE_SCN_MEM_NOT_PAGED were emitted; they do not constitute runtime verification. TE code extracted by section raw pointer minus StrippedSize-40, disassembled with -D -b binary -m i386 -M intel and section RVA adjustment. Offset-leads and full selected-module listings retained.
PARTIAL: first serialization stage located; caller provenance, downstream receiver/hardware writers and independent telemetry not yet established. R2 remains in progress, not falsely completed. No current-board or synchronous-clock claim. All hardware tests UNRUN; no firmware or production-code changes. Findings: docs/research/2026-09-19-clock-control-trace.md; durable result appended to memory/oc-recheck.md.
