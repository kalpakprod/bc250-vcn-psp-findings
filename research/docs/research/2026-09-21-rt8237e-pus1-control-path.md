# PUS1 RT8237E: official interface and BC-250 net-path review

Current: the imported BC-250 GenCAD maps `PUS1` to Richtek `RT8237EZQW(2)` and to the named `VDDCR_SOC` path. The matching official Richtek documentation describes a single-phase analog-feedback buck PWM controller, not an SVI/PMBus-programmable voltage regulator. The boardview shows feedback and power-sequencing nets, but neither it nor the checked BIOS reports demonstrates a BIOS command that sets the SoC voltage to 1.15 V. The boardview's physical revision match and any indirect BIOS control path remain unknown.

## Scope and boundary

Question: determine what the exact `PUS1` part/documented control interface and its boardview-listed feedback/enable nets show, then bound whether current local BIOS evidence establishes a SoC setpoint path. This is read-only research. No BIOS, NVRAM, board, register, or hardware operation occurred. No resistor values, feedback ratio calculation, solder instruction, or modification recipe is included.

## Sources and provenance

### Local boardview

- Preserved source: `archives/imported/boardview-and-downloads/legacy-AyuGram-Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad`, 1,923,019 bytes, SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`.
- Header: `GENCAD 1.4`, `DRAWING X`, `REVISION "NA"` (the filename's `r1.00` is not evidence of actual PCB revision).
- Existing parsed map: `archives/imported/recon-evidence/legacy-tmp-bc250-recon/boardview-parse.json`, 294,507 bytes, SHA-256 `cf11baa257b81ae26b6288162b49f436d50fe0f4ad1a59c2c9703b4527fa8caf`; 2,163 device records and 1,437 signal records.
- The boardview part text at line 68456 is `PWM CONTROLLER RT8237EZQW(2) RICHTEK/WDFN-10L(3*3)/COT`.

The public host was already reconciled in `docs/research/2026-09-21-voltage-mapping-source-followup.md`: its GenCAD body equals the local source plus one trailing LF. It is not an independent netlist or a board-revision match.

### Official Richtek documentation

- Manufacturer product page: <https://www.richtek.com/en/Products/Switching%20Regulators/Single-Phase%20Step-Down%20Controller/RT8237E>, retrieved through Agent Reach/Jina on 2026-09-21; rendered capture SHA-256 `7284e9565092209ef21e9673a163ab403c12f09d2044e8c8ecd07cd523c76d19` (20,264 bytes).
- Official PDF: <https://www.richtek.com/assets/product_file/RT8237E/DS8237E-02.pdf>, downloaded directly from that Richtek URL on 2026-09-21 without authentication; 228,343 bytes; SHA-256 `5ee3a420be490bbab3feab0895b8b47b2a604df8107ac642012d4bad998cfb90`.
- Richtek's product page lists exact orderable part `RT8237EZQW(2)`, package `WDFN3x3-10`, output-adjust method “Resistor,” output range `0.7–3.3 V`, and datasheet version `V2.0`, last update `2020/11/02`. PDF metadata/title is `DS8237E-02.pmd`; it is 18 pages and dates to October/November 2020. This matches the CAD's part string/package, but does not prove which silicon is physically populated on the operator's board.
- The official PDF was text-extracted (`pdftotext -layout`) and the pinout (printed p. 2), typical application circuit (p. 8), and output-feedback section (p. 15) were rendered and visually checked. The complete function list and diagram agree with the text extraction.

## Finding F1 — exact PUS1 pin-name join

A temporary read-only parser read the local GenCAD `SIGNAL`/`NODE` records and asserted that all eleven boardview PUS1 pins match the official device pin numbering; result: **11/11 PASS**. The existing parse JSON's PUS1 part, `SOC_EN`, and `+VDDCR_SOC` entries matched those raw-source joins.

|         PUS1 pin | Richtek RT8237E function (official datasheet p. 2) | Boardview net name |
| ---------------: | -------------------------------------------------- | ------------------ |
|                1 | PGOOD                                              | `VDDCR_SOC_RUN_PG` |
|                2 | CS                                                 | `SOC_OCSET`        |
|                3 | EN                                                 | `SOC_EN`           |
|                4 | FB                                                 | `SOC_FB`           |
|                5 | RF                                                 | `SOC_RF`           |
|                6 | LGATE                                              | `SOC_LG`           |
|                7 | VCC                                                | `SOC_VCC`          |
|                8 | PHASE                                              | `SOC_PHASE`        |
|                9 | UGATE                                              | `SOC_HG`           |
|               10 | BOOT                                               | `SOC_BST`          |
| 11 / exposed pad | GND                                                | `GND`              |

Relevant source anchors in the preserved GenCAD: PUS1 part at lines 68455–68456; `+VDDCR_SOC` at line 74993; `SOC_EN` 77618; `SOC_PHASE` 77627; `SOC_FB` 77647; `VDDCR_SOC_RUN_PG` 77769; `APU_VMEMIO_SUS_PG` 77773; `+VMEMIO_PGOOD` 77478; `MAIN_PWR_EN` 77757; `VMEMP_PWRGD` 77992; `SOC_RF` 78095; `SOC_FB_R` 78099; `APU_VDDCR_SOC_RUN_FB_H` 78108; `SOC_OCSET` 78113. Low-side sense label `APU_VDDCR_SOC_RUN_FB_L` is at line 76699.

### Boardview-listed output and feedback topology

- `SOC_PHASE` joins PUS1 pin 8 to inductor `PLS1` pin 1 and the listed switch-device nodes; `+VDDCR_SOC` joins `PLS1` pin 2 to the `U25` SoC power pins. `VDDCR_SOC_RUN_PG` is PUS1 pin 1. This is static GenCAD connectivity, not a live measurement.
- PUS1 pin 4 lands on `SOC_FB`. The boardview routes the feedback/sense network through `PRS14`/`PRS15`, `SOC_FB_R`, `PRS16`/`PRS17`, and `APU_VDDCR_SOC_RUN_FB_H/L`; the high sense net includes `U25.BC20`, and the low-side sense chain joins the boardview-labelled `SOC_VSS_SENSE2` / `U25.BD20` via `NS9`. The CAD therefore documents a board-level analog feedback/remote-sense network. This does not reveal measured voltage or establish the physical board revision.
- PUS1 pin 5 (`SOC_RF`) is connected to a resistor-strap network; pin 2 (`SOC_OCSET`) is connected to a current-limit network. The Richtek datasheet defines RF as frequency/mode selection by external resistance and CS as a current-limit setting input. These are board-design configuration nets, not documented BIOS voltage commands. Component values and any rework instructions are intentionally omitted.
- PUS1 pin 3 (`SOC_EN`) lands on `SOC_EN`, which the GenCAD joins to a +3.3V-run pull-up path (`PRS4`), `APU_VMEMIO_SUS_PG` (`PRS19`), `VMEMP_PWRGD` (`PRS20`), and a capacitor (`PCS3`). The `APU_VMEMIO_SUS_PG` net also joins a PUIO1 `+VMEMIO_PGOOD` route and a `MAIN_PWR_EN` diode path; `VMEMP_PWRGD` originates at a separate boardview-listed controller `PUM1` pin 1. This shows power-sequencing dependencies as represented in the CAD. It does **not** identify firmware ownership of those signals or prove that BIOS can force them.

## Finding F2 — interface type and BIOS boundary

The official RT8237E pinout contains PGOOD, CS, EN, FB, RF, LGATE, VCC, PHASE, UGATE, BOOT, and GND; no SDA/SCL, SVC/SVD/SVT, or other digital voltage-command pins are documented. Its pin descriptions call FB an analog VOUT-feedback input connected to an external divider; Richtek's product table explicitly says output-adjust method “Resistor.” The datasheet's typical application circuit shows an EN input and passive FB/RF/CS components. A bounded text scan of the full 18-page official datasheet found no SVI/SVID, PMBus, SMBus, I2C, SVC/SVD/SVT, or serial-interface terms. The complete pin table plus documented analog feedback is the relevant evidence; the string scan is only corroborative.

**Conclusion at the controller layer:** there is no published RT8237E SVI/PMBus digital setpoint interface. The datasheet describes analog FB control, a separate enable, and resistor-selected frequency/mode/current-limit configuration. Its generic 0.7–3.3 V output range includes 1.15 V, but that range is not a board-specific support or safety claim and does not make 1.15 V BIOS-programmable.

**BIOS control is not established, not ruled impossible.** Existing exact-CLV static traces document fixed-voltage PEI consumers for `ISL69247` VCORE/GFX and `ISL95712` MEMIO, not this PUS1 RT8237E device (`docs/research/2026-09-20-clv-fixed-voltage-consumer.md`, SHA-256 `6bb851ec32ec8fe963bf50e4070563944bf98c2657a703d2fd696ce960bb3791`; independent decode `docs/research/2026-09-20-fixed-voltage-independent-decode.md`, SHA-256 `a3b3cb0f90a392cb3be97a305a310ed3b23d5c3405ecfdc99d7cda810f071edd`). The existing integration report says `VDDCR_SOC` fields are telemetry-calibration fields, and unresolved `VDDCR_VDD` offset fields do not yet establish a final actuator or physical SoC mapping (`docs/research/2026-09-21-voltage-evidence-integration.md`, SHA-256 `9dda181dc478400d8e06313296674572fdb00bebb50dfedc4d2bee8703b91d36`). These are bounded source findings, not a whole-firmware proof that no indirect GPIO/power-sequencing route exists.

The boardview suggests that BIOS might affect _whether_ a prerequisite rail/power-good is present through some independent route, but it does not expose an addressable voltage setting for `PUS1`. No `SOC_EN` GPIO consumer, feedback-network actuator, or other BIOS-controlled analog setpoint path was traced in this task. Do not translate `SOC_EN`, `VDDCR_VDD`, or the generic RT8237E range into a `1.15 V` BIOS setting. The 1.15 V target remains unsupported by the checked evidence; no safety limit or actual output voltage was measured.

## Evidence class, limits, and next decisive offline step

- `observed-bytes`: local GenCAD/CAD parse hashes and official Richtek PDF hash.
- `static-analysis`: PUS1 pin-to-net joins and component topology as represented in the imported GenCAD; official vendor pin/function table and application figures.
- `external-primary`: official Richtek product page and datasheet (applicability is to RT8237E, not physical board identity).
- `hardware-verified`: **none**. No board revision was inspected, no probe/measurement was performed, and no voltage or safety claim follows.

The immediate offline follow-up, if required, is to trace only documented exact-CLV writers/readers for the boardview-labelled `SOC_EN` prerequisites and candidate voltage-offset producer/consumer paths. A negative string search is insufficient; require a bounded call/data-flow boundary and preserve unknown indirect paths. Physical rail identity, actual output voltage, and the board's populated revision still require revision-matched electrical evidence and, if separately approved, measurement. No modification/rework instructions are included.
