# Operator decisions (pending and recorded)

Format: date, question, options, status. Answers recorded here are durable; chat is
ephemeral.

## 2026-09-23 — D1: fate of the SoC ≤1.15 V requirement (after R2)

R2 (Plane #2, closed Done) proved the limitation: +VDDCR_SOC is not controllable
through BIOS/firmware on this board revision (no CBS field, no SMU message, no
digital receiver on PUS1 RT8237E; SVI2 carries only CPU/GFX planes to ISL69247).
Evidence: docs/research/2026-09-23-r2-soc-vddcr-limitation.md.

Question: what happens to the SoC ≤1.15 V requirement of the actuator-first goal?

- O1 (recommended): drop it from the BIOS track; P4 proceeds with clocks/latency
  only, the SoC-voltage line is documented as hardware-only (FB divider change or
  controller swap, separate approval).
- O2: keep it as a hardware-track requirement (soldering on the owned board),
  separate from the BIOS candidate work.
- O3: reject the limitation verdict (name the falsifier you believe in: board
  revision, other firmware, measurement).

Status: pending operator answer.
