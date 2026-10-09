# Offline final consumer pass work log

## Intent
Use hash-pinned clv read-only. Reuse scripts/firmware_audit.py Extractor, adding a local subclass only to retain PcdDxe/PcdPeim raw database sections (existing extractor deliberately retains executables only). Retain selected PCD/CBS modules, objdump output, direct-byte assertions and source hashes here. Trace DXE PCD calls, database token identity and Setup writers; test exact formulas. No hardware/network, candidates/builders/input edits. Rollback: remove only this new evidence directory and own research report. Parent intent: docs/action-logs/2026-09-19-oc-final-consumer-pass.md.

## Discovery
Read oc-recheck memory, both requested reports and applicable RE/forensics/provenance/SMU skills. Fresh clv SHA-256 matches ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8. Existing GNU objdump listings and parser available. DXE 0x17dc allocates 0x49c bytes, populates via PCD protocol getters and later passes pointer halves to mailbox messages 0x0e/0x0d; trace now follows this non-serializer route. No claim yet connects these fields to record 0x1364.
