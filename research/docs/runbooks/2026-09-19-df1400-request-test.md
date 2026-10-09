# DF1400 stored-request discriminator — NOT FLASH APPROVED

Candidate: candidates/BC250_5.00_clv_DF1400_REQUEST_ONLY_v003.bin
SHA-256: 4811e1bdc95fa96a74fc7d6e688d6d44aa2cc306c52803c89c635d81917df841
Base: evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
SHA-256: ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8
Both 16777216 bytes. Only byte 0xBD3 changes 8C -> 78; AmdSetup+0x704 u16 request 1420 -> 1400. Voltage, divider, timings and other clocks unchanged. This is not 1:1:1, not a demonstrated overclock and not proof of a lower physical frequency.

Hypothesis: this stored DF request is retained and reaches an active clock control. First discriminator is retention after boot; physical application needs an independent DF clock source, not the known aliased gpu_metrics field. Without that source, a booting image permits only a retention verdict, not a clock-application verdict.

## Gates before execution

- Independent artifact/failure-path review is INCOMPLETE: selected reviewer model unavailable. Do not flash on the basis of this document.
- Confirm exact board/chip, isolated programmer procedure, fresh full-chip matching reads and known recovery image. Earlier recovery copies do not replace current preflight.
- Capture clv baseline and define stock recovery procedure, instrumentation, boot timeout and stop conditions before trial. Obtain separate approval for this exact candidate hash and target.
- Do not use unreviewed SMN/DF reads to measure clocks. No manual rail changes.

## Trial after gates are satisfied

1. Baseline: same kernel, cooling and workload, capture boot/training/errors and validated measurement sources.
2. Operator-approved programmer write and independent full-chip readback must exactly match the candidate.
3. One cold boot, maximum 120 seconds for normal boot; stop on no progress, training loop, loss of video, machine-check, unexpected voltage or thermal alarm. Do not keep retrying a failing profile.
4. Read back retained AmdSetup with the correct bounded store (0..0x20000). Record revert/retained/inconclusive separately from measured DF behavior.
5. If no independent DF measurement exists, stop at retention result; do not optimize further from aliased telemetry. Do not combine voltage changes in this trial.
6. On failure, power down and restore verified recovery through the recorded programmer procedure; independently verify full-chip readback, then cold boot control. Never flash with clip/board power conflicts.

## Checks already performed

11 unittest checks passed (7 builder, 4 existing NVAR parser). Exact full-image comparison and existing firmware_audit PSP/BHD/APCB checks pass. Firmware outside NVRAM is byte-identical to source. Hardware, stability, effective voltage/frequencies and independent review remain UNRUN/INCOMPLETE.
