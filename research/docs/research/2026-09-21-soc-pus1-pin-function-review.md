# PUS1 RT8237E pin and control-net review

Date: 2026-09-21 (Asia/Almaty). Scope: PUS1/RT8237EZQW and the named SoC enable/mode/feedback/power-good nets in the preserved GenCAD only. The official Richtek PDF was **not refetched**; its pinned identity and pin-function table are reused from the completed source-fetch report. Evidence class: `observed-bytes` for the CAD and `static-analysis` for selected net connectivity; `external-primary` for the previously pinned vendor datasheet. No board or modification action occurred.

## Verdict

**No explicit EC/GPIO/DAC endpoint appears in the bounded PUS1 control/feedback nets.** The CAD shows:

- `SOC_FB`/remote sense as an analog feedback network;
- `SOC_RF` and `SOC_OCSET` as resistor-connected configuration/current-limit nets;
- `SOC_EN` as a passive/power-sequencing net combining a +3.3V-run pull-up, VMEMIO/PUM1 power-good dependencies, and a capacitor;
- `VDDCR_SOC_RUN_PG` as a PUS1 PGOOD net.

This supports “no EC/GPIO/DAC endpoint identified in this bounded net slice,” **not** “no software control exists.” The unresolved source/ownership is the upstream path at the named passive/power-good nodes, especially `PRS4`/`+3.3V_RUN`, `PRS19`/`APU_VMEMIO_SUS_PG`, and `PRS20`/`VMEMP_PWRGD`; the CAD slice does not prove who drives those rails/signals.

## Pinned vendor evidence reused, not refetched

Prior source-fetch report: `docs/research/2026-09-21-rt8237e-pus1-control-path.md`, SHA-256 `54ea41f7df003de07613f8605dc882b92e6182b9b483d4ce4583bcf76a61f387`. It records the official Richtek PDF URL, size `228,343` bytes, SHA-256 `5ee3a420be490bbab3feab0895b8b47b2a604df8107ac642012d4bad998cfb90`, 18 pages, and the pin/function table. This review intentionally did not refetch or duplicate that source-fetch work.

The reused table maps PUS1 pins to RT8237E functions: pin 1 PGOOD; 2 CS; 3 EN; 4 FB; 5 RF; 6 LGATE; 7 VCC; 8 PHASE; 9 UGATE; 10 BOOT; 11 GND. The prior report states the vendor device uses analog FB and resistor output adjustment, with no documented SVI/PMBus digital voltage-setpoint interface. Those vendor claims are not promoted beyond that pinned source report.

## Independent CAD-side parse

Exact source: `/home/OWNER/orca/projects/bc250/archives/imported/boardview-and-downloads/legacy-AyuGram-Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad`, size `1,923,019` bytes, SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`. Header is `GENCAD 1.4`, `DRAWING X`, `REVISION "NA"`; filename `r1.00` does not establish board revision.

A targeted raw line parse (no use of `boardview-parse.json` for this decision) found all ten signal-bearing PUS1 pins and the GND-block PUS1 pin 11. The device label is `RT8237EZQW(2)` at CAD lines 68455–68456.

### PUS1 control and feedback nets

- **EN, pin 3:** `SOC_EN` at lines 77618–77623 joins PUS1 pin 3, capacitor `PCS3` pin 1, `PRS19` pin 2, `PRS20` pin 2, and `PRS4` pin 2. The opposite endpoints are represented in selected named nets as follows:
  - `PRS4` pin 1 is on `+3.3V_RUN` (line 74164; this is a pull-up path, not an identified EC/GPIO/DAC endpoint).
  - `PRS19` pin 1 is on `APU_VMEMIO_SUS_PG` (77773–77779), a power-good/sequencing net.
  - `PRS20` pin 1 is on `VMEMP_PWRGD` (77992–77996), which includes separate controller `PUM1` pin 1.
  - `APU_VMEMIO_SUS_PG` includes `PRIO25` pin 1; `+VMEMIO_PGOOD` includes `PRIO25` pin 2 and `PUIO1` pin 23 (77478–77482), so the bounded path reaches a separate ISL95712 power-good endpoint through passives/controllers, not a named EC/GPIO/DAC.
- **FB, pin 4:** `SOC_FB` (77647–77651) joins passives `PCS9`, `PRS14`, `PRS15`; `SOC_FB_R` (78099–78103) joins `PRS11`, `PRS13`, `PRS14`, `PRS16`; high remote-sense `APU_VDDCR_SOC_RUN_FB_H` (78108–78112) reaches U25 pin `BC20`; low remote-sense `APU_VDDCR_SOC_RUN_FB_L` (76699–76702) and `SOC_VSS_SENSE2` (76687–76692) reach U25 pin `BD20` through passive/short components. No EC/GPIO/DAC designator appears in these selected feedback blocks.
- **RF/mode, pin 5:** `SOC_RF` (78095–78098) contains `PRS1` and `PRS2` plus PUS1 pin 5. The bounded CAD evidence identifies a resistor/strap network only; it does not identify a software or digital mode endpoint.
- **CS/OCSET, pin 2:** `SOC_OCSET` (78113–78115) contains `PRS3` and PUS1 pin 2. This is a passive current-limit network in the bounded file slice, not a voltage-setpoint interface.
- **PGOOD, pin 1:** `VDDCR_SOC_RUN_PG` (77769–77772) contains `PDA3`, `PRM20`, and PUS1 pin 1. It is a power-good return/status net, not a documented digital voltage command.
- **Power stage pins:** `SOC_PHASE` (77627–77640) routes PUS1 pin 8 through `PLS1` and switching-device nodes; `SOC_VCC`, `SOC_LG`, `SOC_HG`, and `SOC_BST` map to their named supply/driver nets. These are power-stage connections, not EC/GPIO/DAC control endpoints.

## Claim decisions

- **ACCEPT:** The RT8237E pin-function table aligns with the PUS1 boardview labels used in the prior pinned report; the new CAD parse independently reproduces the relevant PUS1 net joins.
- **ACCEPT, qualified:** `SOC_EN` has an upstream power-sequencing path involving +3.3V pull-up and PUIO1/PUM1 power-good signals through passives/controllers.
- **REJECT:** calling that path an identified EC/GPIO/DAC control path; no such endpoint is present in the bounded named nets.
- **REJECT:** calling the analog FB/RF/OCSET networks a BIOS-addressable 1.15 V setpoint.
- **UNRESOLVED:** ownership/firmware origin of `+3.3V_RUN`, `APU_VMEMIO_SUS_PG`, `VMEMP_PWRGD`, and any untraced upstream side of the passive network; boardview revision fidelity; actual voltage and safety; and any indirect BIOS/software path.

No resistor values, resistor changes, solder/rework, GPIO writes, BIOS writes, or hardware probes are provided or performed.
