# Action Log: 2026-09-19 OC Clock Application & Telemetry Discrimination

## Intent

Transition method from repetitive voltage telemetry loops to clock control tracing and independent telemetry discrimination. Trace discriminating SMU commands for DF/FCLK/UCLK and record driver aliasing.

## Results

- Evaluated SMU message tables (`known_messages_robin5.txt` and `SMU-HANDLERS.md`):
  - Located `PPSMC_MSG_QueryDfPstate` (Queue 0 msg `0x13`, handler `0x0001E988`) and `PPSMC_MSG_QueryVddcrSocClock` (Queue 0 msg `0x11`, handler `0x0002EA74`).
  - Located DFLL divider command `SetMaxDeepSleepDfllGfxDiv` (Queue 0 msg `0x1A`, handler `0x0002B634` in Robin 5).
- Annotated `scripts/probe_bc250_clocks_readonly.py` to prevent treating aliased `pp_dpm_*` readings as independent measurements.
- Added stock verification profile support in `scripts/build_clv_oc_candidate.py`.
- Updated plan `specs/2026-09-19-oc-sync-recovery-plan.md` checklist item R2.
