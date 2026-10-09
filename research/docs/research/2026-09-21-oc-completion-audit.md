# OC completion audit: practical 1.15 V + physical 1:1:1 status

Date: 2026-09-21 (Asia/Almaty)  
Scope: latest PUS1/CAD control-net finding plus current CLV OC evidence. Read-only completion assessment; no scan, patch, firmware/NVRAM, board, or hardware action.

## Verdict

**The practical user outcome is not supplied.** Current evidence does not provide either:

- a BIOS-controlled, board-mapped SoC `1.15 V` setpoint or a safe 1.15 V limit; or
- a physical `MCLK=UCLK=FCLK` / `1:1:1` result.

The latest PUS1 review strengthens the boundary: `SOC_EN`, `SOC_FB`, `SOC_RF`, `SOC_OCSET`, and `VDDCR_SOC_RUN_PG` are passive/power-sequencing/analog feedback nets in the bounded GenCAD slice. No explicit EC/GPIO/DAC endpoint is identified, but this does **not** prove that no upstream software path exists. Its ownership is unresolved. The official RT8237E evidence describes analog feedback/resistor adjustment, not a documented digital voltage-setpoint interface.

## Requirement-by-requirement status

| Requested outcome           | Status                                          | Exact evidence / reason                                                                                                                                                   |
| --------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Preserve memory 1800        | **PASS, static request only**                   | Pinned CLV `AmdSetup+0x316=0x24`, exact HII option label `1800MHz`. Current board NVRAM and physical clock are unrun.                                                     |
| BIOS SoC 1.15 V             | **FAIL as an evidence-supported claim**         | No field-to-SoC actuator/unit/page map. PUS1 is an analog RT8237E path in the CAD; fixed VCORE/GFX/MEMIO fields and unresolved CBS offsets are not a proven SoC setpoint. |
| Safe 1.15 V boundary        | **UNRUN / unsupported**                         | No revision-matched electrical rating, live readback, thermal/current margin, or silicon limit. Do not infer from menu bounds or generic RT8237E range.                   |
| Physical 1:1:1              | **UNRUN; equal-number interpretation rejected** | No independent MCLK/UCLK/FCLK measurements, divider/crossing state, common-unit conversion, or training result. Equal UI values/driver metrics are insufficient.          |
| Latency improvement         | **UNRUN**                                       | The reviewed protocol defines future A/B measurements only; no board benchmark exists.                                                                                    |
| Runtime voltage application | **UNRUN**                                       | PEI modules require two PPIs; runtime dispatch, mailbox semantics, board revision, and output readback are unresolved.                                                    |

## CPU/GFX versus SoC distinction

The CAD finding separates PUS1 from PUA1:

- PUS1/RT8237E: `SOC_PHASE -> PLS1 -> +VDDCR_SOC -> U25`; `SOC_EN` includes `+3.3V_RUN` and VMEMIO/PUM1 power-good dependencies. This is a boardview net path, not a BIOS voltage command.
- PUA1/ISL69247: separate core and GFX PWM/power-stage paths to `APU_VDDCR_CORE_RUN` and `APU_VDDCR_GFX_RUN`. Static CLV VCORE/GFX examples therefore cannot be relabelled as SoC control.

The GenCAD header reports `REVISION "NA"`; `r1.00` in the filename is not a verified physical-board revision. Thus even the static PUS1 path awaits applicability to the operator's board.

## Superseded interpretation

Prior equal-number or numerically overlapping profiles must remain labelled **request-only / synchronization unproven**. No six-field profile should be applied merely to test this conclusion. In particular, preserving the 1800 request does not authorize changing UclkDiv1M0, Memory P-state, FCLK_DPM, DF override, voltage, or timing fields.

## Smallest necessary operator input

The smallest useful bundle is a **read-only identity-and-state capture**, not a candidate profile:

1. board model/revision markings and PUS1/PUA1 package markings, establishing whether the imported CAD applies; and
2. current BIOS image hash plus current NVRAM/Setup readback showing the existing Memory Clock request (to verify the B1800 control).

No profile application is requested. A later physical voltage/synchronization claim additionally needs a revision-matched electrical output/net mapping and independently measured voltage/clock evidence; this audit does not invent a 1.15 V electrical method.

## Offline next step

After the bounded `SOC_EN`/feedback-net distinction, there is **no productive offline step that can close the practical 1.15 V + physical 1:1:1 requirement** without the identity/state bundle above or new board-specific evidence. Continuing generic BIOS string scans or creating more equal-number profiles would not resolve the missing physical links. Stop this track pending that operator input; do not create filler experiments.

## Reopened source ledger

- Donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` — `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Latest PUS1 pin review `docs/research/2026-09-21-soc-pus1-pin-function-review.md` — `2c4bd39250c87f0ed0aa0e1ead5f428a86df810b564ee499f8527ce571ba217c`.
- PUS1 RT8237E source report `docs/research/2026-09-21-rt8237e-pus1-control-path.md` — `54ea41f7df003de07613f8605dc882b92e6182b9b483d4ce4583bcf76a61f387`.
- Independent SoC net review `docs/research/2026-09-21-soc-net-independent-review.md` — `cfe1355d96a2179b55467d489c41c10297068f1d2120418254950eae9030e0e6`.
- Consolidated guide `docs/research/2026-09-21-oc-decision-guide.md` — `7862a581010c206a58390d7a8150bfe3b3c566aa1fd5ac28145ab8a56e9c0d58`.
- Latency protocol `docs/research/2026-09-21-latency-protocol-reviewed.md` — `11d15b3a2158c71290e917ee0339bfc000bf2a74655b94fe0e4979f7d75ebcfb`.
- Voltage safety matrix `docs/research/2026-09-21-manual-voltage-safety-matrix.md` — `e43bb1d0108bb58ab8a81bb87bb5768e76ccf42d1b958424540c111a9926cb9d`.
- PEI applicability `docs/research/2026-09-21-luna-fixed-rail-conditions-current.md` — `a62b77e80e13a1b61b97986b83bc23eeca02284b99ecc45a6f85bc86439df2b2`.

Evidence classes: observed-bytes and static-analysis only, plus external-primary Richtek documentation as qualified in the cited report. Hardware voltage, clock synchronization, training, latency and rollback are not verified.
