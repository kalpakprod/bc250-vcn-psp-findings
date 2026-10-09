# SoC feedback: bounded endpoint audit

Source: pinned GenCAD SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`.

## Observed connectivity

PUS1.4 -> SOC_FB -> PRS14 -> SOC_FB_R.

SOC_FB_R branches:

- PRS11 -> SOC_VSEN_LOC+ -> NSS1 -> +VDDCR_SOC.
- PRS16 -> APU_VDDCR_SOC_RUN_FB_H -> U25.BC20, TP4 and R775.
- PRS13 -> N46990603 -> PCS9 -> SOC_FB (RC branch).

SOC_FB -> PRS15 -> N46990718 branches:

- PRS12 -> SOC_VSEN_LOC- -> NSS2 -> GND.
- PRS17 -> APU_VDDCR_SOC_RUN_FB_L -> NS9 -> SOC_VSS_SENSE2 -> U25.BD20.

R775 joins the high/low remote-sense nets. SOC_VSS_SENSE2 also connects NS10/NS11 and TP18. These other sense branches have not been followed through their full circuits.

## Result and consequence

Nine exact net endpoint sets and two rail boundary connections pass against raw GenCAD. The inspected feedback nets list resistor/capacitor/jumper/sense endpoints, not a separate DAC, digital potentiometer or switched transistor providing a BIOS-addressable setpoint. Together with RT8237E's published analog FB interface, this is evidence against treating an arbitrary BIOS VDD offset as a SoC voltage control.

This does NOT prove the APU sense pads can never influence voltage. Physical board revision and fitted components remain unverified. Placeholder parts in the CAD are not proof of populated components. No nominal or safe voltage is inferred from resistor values. No hardware changes are recommended.

R2 is still unresolved. No 1.15 V BIOS recipe can be issued from these facts. Further firmware work needs a specific actuator hypothesis tied to these endpoints, not another search for voltage labels. R3 clock semantics and R4/R5 candidate checks remain independent offline work.

## Reproduction

`python3 evidence/firmware-audit/20260923-soc-feedback/verify.py`

Observed stdout: `PASS 9 complete feedback/sense nets and 2 local rail boundary connections`

Exit: `0`. Stderr empty. Evidence: `evidence/firmware-audit/20260923-soc-feedback/result.json`.
