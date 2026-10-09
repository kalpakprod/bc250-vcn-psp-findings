# PUS1 EN versus FB: board-file-scoped distinction

Date: 2026-09-21 (Asia/Almaty). Scope: exact imported PUS1 GenCAD object and only the named EN/FB/RF/OCSET/PGOOD nets. Evidence class: `observed-bytes` plus targeted `static-analysis`; official pin semantics are reused from the pinned Richtek source report. No broader power-tree scan, hardware action, resistor change, ROM change, or BIOS write occurred.

## Result

**The CAD separates an enable/sequencing path from the analog feedback path.** With the previously pinned official RT8237E function table (`pin 3 = EN`, `pin 4 = FB`, `pin 5 = RF`, `pin 2 = CS`, `pin 1 = PGOOD`), the targeted CAD check passed `12/12`.

- `SOC_EN` / PUS1 pin 3 joins `PCS3`, `PRS19`, `PRS20`, and `PRS4`.
- `PRS4` leads to `+3.3V_RUN`; `PRS19` leads to `APU_VMEMIO_SUS_PG`; `PRS20` leads to `VMEMP_PWRGD`.
- The selected sequencing branch reaches `+VMEMIO_PGOOD`/PUIO1 pin 23 through `PRIO25` and PUM1 pin 1 through `VMEMP_PWRGD`.
- `SOC_FB` / PUS1 pin 4 and its high/low remote-sense blocks are separate: they contain the feedback passives and U25 sense pins, with no shared component/pin endpoint with the selected EN/RF/OCSET blocks.
- `SOC_RF` / pin 5 and `SOC_OCSET` / pin 2 are resistor/strap and current-limit networks in this file slice.

Therefore, in this board file, EN/power-good can be discussed as **rail enable/sequencing**, not as a demonstrated steady-state voltage setpoint. A `1.15 V` output would require the analog FB network or an independently proven regulator-control mechanism; EN alone does not establish that setpoint.

## Direct verification

Input: `/home/OWNER/orca/projects/bc250/archives/imported/boardview-and-downloads/legacy-AyuGram-Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad`, size `1,923,019`, SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`.

Targeted check output (exit `0`):

```text
PASS SOC_EN PUS1 pin: PUS1 pin 3 present in SOC_EN block at line 77618
PASS SOC_FB PUS1 pin: PUS1 pin 4 present in SOC_FB block at line 77647
PASS SOC_RF PUS1 pin: PUS1 pin 5 present in SOC_RF block at line 78095
PASS SOC_OCSET PUS1 pin: PUS1 pin 2 present in SOC_OCSET block at line 78113
PASS VDDCR_SOC_RUN_PG PUS1 pin: PUS1 pin 1 present in VDDCR_SOC_RUN_PG block at line 77769
PASS PRS4 upstream: SOC_EN PUS1-side PRS4 pin2; PRS4 pin1 on +3.3V_RUN
PASS PRS19 upstream: SOC_EN PRS19 pin2; PRS19 pin1 on APU_VMEMIO_SUS_PG
PASS PRS20 upstream: SOC_EN PRS20 pin2; PRS20 pin1 on VMEMP_PWRGD
PASS PUIO1 PGOOD branch: PRIO25 bridges APU_VMEMIO_SUS_PG to +VMEMIO_PGOOD/PUIO1 pin23
PASS PUM1 PGOOD branch: PUM1 pin1 present on VMEMP_PWRGD
PASS EN/FB endpoint separation: common component/pin refs=[]
PASS No named EC/GPIO/DAC in selected control nets: selected node designators contain no EC/GPIO/DAC token
SUMMARY: 12/12 PASS
```

## Official pin-function provenance

The prior source-fetch report `docs/research/2026-09-21-rt8237e-pus1-control-path.md` (SHA-256 `54ea41f7df003de07613f8605dc882b92e6182b9b483d4ce4583bcf76a61f387`) pins the official Richtek PDF URL and PDF SHA-256 `5ee3a420be490bbab3feab0895b8b47b2a604df8107ac642012d4bad998cfb90`; it records the datasheet pin table and analog FB/resistor-output semantics. This task did not refetch that PDF. The present result is an independent CAD-side endpoint check against that pinned table.

## Exact missing physical identity and limits

The CAD header is `GENCAD 1.4`, `DRAWING X`, `REVISION "NA"`; the filename `ASRock AMD BC-250_ISL_X5R r1.00.cad` does not prove the populated operator-board revision. Thus the result applies to this imported board file, not automatically to the live board. Still missing are revision-matched physical confirmation, upstream ownership of `+3.3V_RUN`/`APU_VMEMIO_SUS_PG`/`VMEMP_PWRGD`, any indirect firmware/GPIO path, actual output voltage, and safety.

No universal impossibility claim follows, and no `1.15 V` recommendation follows. No resistor values or modification instructions are included.
