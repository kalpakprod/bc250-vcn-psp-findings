# Independent BC-250 SoC/core/GFX net-path review

Date: 2026-09-21 (Asia/Almaty). Scope: only the cited preserved GenCAD artifact and the named PUS1/PLS1/SoC and PUA1/core/GFX signals. Evidence class: `observed-bytes` for the local source identity and `static-analysis` for targeted `SIGNAL`/`NODE` connectivity; the source is a community boardview, not a hardware measurement.

## Verdict

**Accept at the file/netlist level:** this GenCAD labels `PUS1` as an RT8237EZQW controller on a named `+VDDCR_SOC` path through `PLS1`; it labels `PUA1` as an ISL69247 whose PWM pins connect to separate core and GFX power-stage paths. The file does not show PUS1 as PUA1 or map PUA1's PMBus `PAGE=0/1` to CORE/GFX. This does not prove the file matches the operator's board revision, that the nets are physically implemented as drawn, or that any voltage is applied/safe.

## Source identity and board labels

- Exact source reopened: `/home/OWNER/orca/projects/bc250/archives/imported/boardview-and-downloads/legacy-AyuGram-Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad`.
- Size `1,923,019` bytes; SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`. It has `80,812` CRLF line endings and no bare LF/CR.
- The raw header (lines 1–9) says `GENCAD 1.4`, `USER "NA"`, `DRAWING X`, `REVISION "NA"`, and `ATTRIBUTE HEADER_1 "NA"`. The filename's `r1.00` is not proof of board revision; no revision-matched operator-board identity follows.
- Device labels: `PUA1` is `PWM CON. ISL69247IRAZ-T-C51 RENESAS/QFN52/AMD/4+2` (lines 68427–68428); `PUS1` is `PWM CONTROLLER RT8237EZQW(2) RICHTEK/WDFN-10L(3*3)/COT` (68455–68456); `PLS1` is labeled `INDUCTOR 0.33UH/60A ...` (67979–67980); `U25` is labeled `CPU 100-000000656 BL5R2 AMD ROBIN` (69627–69628). These are boardview labels, not fresh physical part markings.

## Targeted independent `SIGNAL`/`NODE` parse

The parser read the preserved raw CAD directly and selected only the signals named below; it did not read or rely on the pre-existing `boardview-parse.json` result.

### PUS1 / SoC

- `SOC_PHASE` (signal begins at line 77627) joins `PUS1` pin `8` (line 77640) to `PLS1` pin `1` (77629).
- `+VDDCR_SOC` (74993) joins `PLS1` pin `2` (75018) to the U25 CPU package pins (75020–75051; e.g. U25 `AR15` through `AU35`).
- `VDDCR_SOC_RUN_PG` (77769) connects to `PUS1` pin `1` (77772).
- Together, these named records show a PUS1 → `SOC_PHASE` → PLS1 → `+VDDCR_SOC` → U25 netlist path, separate from the PUA1 PWM nets. This is the requested SoC path within this file only.

### PUA1 / core

- `+VDDCR_CORE_PWM1` (78164) joins `PUA1` pin `48` to `PUA11` pin `28` (78165–78166); `+VDDCR_CORE_PWM2` (78167) joins `PUA1` pin `49` to `PUA12` pin `28` (78168–78169).
- `CORE_SW1` (77792) joins `PUA11` pin `9` to `PLA11` pin `1` (77793–77794); `CORE_SW2` (77795) joins `PUA12` pin `9` to `PLA12` pin `1` (77796–77797).
- `APU_VDDCR_CORE_RUN` (72904) joins `PLA11`/`PLA12` pin `2` (72942–72943) to the U25 CPU package pins (72945–73048).

### PUA1 / GFX

- `+VDDCR_GFX_PWM1` through `PWM4` (78155–78172) join `PUA1` pins `3,2,1,52`, respectively, to `PUA21`–`PUA24` pin `28`.
- `GFX_SW1`–`SW4` (77798–77809) join `PUA21`–`PUA24` pin `9` to `PLA21`–`PLA24` pin `1`.
- `APU_VDDCR_GFX_RUN` (74508) joins `PLA21`–`PLA24` pin `2` (74585–74588) to U25 CPU package pins (74591–74830).

## Mirror identity qualification and remaining limit

The Jina-extracted public body `/tmp/bc250-genccad-source.cad` is `1,923,020` bytes with SHA-256 `d60c6389af8d476accf2bf0ff0315f8e239bf7516d0cbdb02aeaff9f48ebcb30`. The raw local file and extracted body are **not byte-identical**: the local bytes match the entire body prefix, but the Jina body has one additional bare LF after the local file's `$ENDSIGNALS`; hashes and sizes differ. This is not independent corroboration. Do not describe line-ending-normalized or final-LF-trimmed equality as byte identity.

## Accepted, rejected, unresolved

- **Accept:** within this GenCAD, PUS1/PLS1 feed the named `+VDDCR_SOC` U25 net; PUA1 controller pins feed distinct named core and GFX stage/inductor/output nets.
- **Reject:** PUA1 as the source of the named `+VDDCR_SOC` connection in this file; the parsed SoC path uses PUS1/PLS1.
- **Reject:** calling the public Jina body byte-identical to the local source or independent netlist corroboration.
- **Unresolved:** actual board revision/fidelity, electrical operation, output voltage/safety, exact PUA1 PMBus `PAGE` to CORE/GFX mapping, BIOS/runtime behavior, and hardware verification.
- No board, net, ROM, firmware, NVRAM, register, or hardware operation was performed; no voltage value is recommended.
