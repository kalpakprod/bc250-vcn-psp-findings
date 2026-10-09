# CLV phase-2 CBS PPI ownership/caller lifecycle — intent

Timestamp: 2026-09-20T06:02:00+05:00 (+05:00)
Actor: sync_stage2_consumer executor
Target: exact `CbsBasePei` interface GUID `04126c85-5c4e-458f-abc1-29f1f7da365e`, its entrypoint InstallPpi descriptor/interface ownership, and target-specific direct GUID/pointer references across the retained 233-module exact-clv census.

Next executable action: run `evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-owner/cbs_ppi_owner_verify.py`; decode the Cbs descriptor from the actual entrypoint push, map its GUID/interface pointers, and classify direct caller/registration joins without another generic token scan.

Inputs: pinned clv ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; Cbs/SMU exact bodies; retained 233-module census; prior six-call LocatePpi result reused read-only.

Expected effect: own CBS PPI ownership/caller evidence/report/log only. No firmware, ROM, hardware, shared plan/memory, Ghidra/Cutter/MCP, candidate, installation, voltage or settings changes.

Rollback: remove only this unique evidence directory, report and action log.
