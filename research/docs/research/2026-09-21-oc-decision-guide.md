# BC-250 OC decision guide: memory 1800, SoC target, and voltage evidence

Date: 2026-09-21 (Asia/Almaty)  
Scope: consolidate current local evidence only. No BIOS/NVRAM/ROM/board/hardware change and no fresh firmware scan.

## Decision

1. **Preserve the user's memory baseline as the exact CLV request `AmdSetup+0x316 = 0x24`.** The exact HII label for code `0x24` is `1800MHz`. Keep this request unchanged. It is a stored UI request, not proof of physical 1800 MHz, training, or current NVRAM.
2. **Do not describe any equal-number profile as `1:1:1`, synchronized, or physically applied.** Historical profiles and requests that use equal or numerically overlapping Memory/DF values remain unproven clock synchronization. UI ranges, enum labels, and aliased driver metrics do not establish a common clock unit or crossing.
3. **Treat SoC `1.15 V` as the user's target constraint only.** No checked BIOS field, PMIC page, or boardview path translates that target into a safe or applied voltage. No electrical conversion or value recommendation is proposed.
4. **Keep CPU/core and GFX examples separate from the SoC target.** The boardview's latest PUS1 finding places the named `+VDDCR_SOC` path on a separate Richtek RT8237E controller; PUA1/ISL69247 core/GFX stages are not evidence that the SoC rail is controlled by the same page or field.
5. **Current voltage decision: no manual voltage change is supported.** The BIOS fields and PEI code paths are useful static leads only; live Setup visibility, PEI dispatch, controller protocol, physical net identity, output voltage, and electrical limits remain unverified.

## Exact statically proven menu paths

These are package-local HII paths and stored bytes in the pinned CLV image. They are not claims that a live board displays or applies them.

| Control            | Exact static path                                                                                                                                                     | Field and pinned request                                                              | Boundary                                                                                                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Memory Clock Speed | `UMC Common Options -> GDDR6 Common Options -> DRAM Timing Configuration -> I Accept` (`0x7007 -> 0x7028 -> 0x702A -> 0x702C`)                                        | QID `0x20F`, `AmdSetup+0x316`, `0x24` (`1800MHz`)                                     | Display label/request only; physical rate, GDDR6 conversion, training and NVRAM state are unverified.                                                                       |
| UclkDiv1M0         | `AMD CBS -> UMC Debug Options -> GDDR6 Debug Options -> GDDR6 DRAM Timing Configuration` (`0x7000 -> 0x7008 -> 0x702E -> 0x702F`)                                     | QID `0x229`, `AmdSetup+0x330`, `0x01` (`Enabled`); default `Auto=0xFF`                | `Enabled` is not a decoded divider ratio and does not prove synchronous crossing.                                                                                           |
| Memory P-state     | `AMD CBS -> UMC Debug Options -> GDDR6 Debug Options -> GDDR6 DRAM Controller Configuration -> DRAM Power Options` (`0x7000 -> 0x7008 -> 0x702E -> 0x7030 -> 0x7032`) | QID `0x25E`, `AmdSetup+0x36D`, `0xFF` (`Auto`); options `Enabled=1`, `Disabled=0`     | This is the corrected **DRAM Power Options** path, not DRAM Timing Configuration. Serializer edge exists; final consumer/training effect is unresolved.                     |
| FCLK_DPM           | `SMU Debug Options -> SMU Features` (`0x7009 -> 0x703E`)                                                                                                              | QID `0x7045`, `AmdSetup+0x6A3`, `0x0F` (`Auto`)                                       | Static callback/serializer metadata does not prove clock application.                                                                                                       |
| DF Clock Override  | `SMU Debug Options -> SMU Debug` (`0x7009 -> 0x703F`)                                                                                                                 | QID `0x37D/+0x37E`, `AmdSetup+0x703=1`, `+0x704=1420`                                 | Numeric `[0,2000]` overlap with Memory labels is not semantic support or synchronization.                                                                                   |
| Fixed-voltage form | `Setup -> Advanced -> Voltage Configuration` (`0x2710 -> 0x2712 -> 0x28EA`)                                                                                           | Separate `Setup` VarStore: VCORE QIDs `0x73/0x74`, GFX `0x76/0x77`, MEMIO `0x79/0x7A` | Parent REF is under a static `FALSE` suppress expression. VCORE/GFX numeric fields have QID-enable predicates; MEMIO scope is noncanonical. Live browser behavior is unrun. |

The exact HII parser's `HIDDEN`/`GRAY` labels reflect lexical scope membership and do not by themselves establish live visibility. AMIBCP visibility, if available, would likewise not prove Setup Browser evaluation, save/reset, or PEI application.

## SoC controller finding: PUS1 is distinct from PUA1

The latest preserved GenCAD review identifies, within that file only:

- `PUS1` as Richtek `RT8237EZQW(2)` (`RT8237E` family), with `SOC_PHASE -> PLS1 -> +VDDCR_SOC -> U25` and `VDDCR_SOC_RUN_PG` on PUS1 PGOOD. The official Richtek documentation describes analog FB regulation, resistor output adjustment, enable, current-limit and frequency/mode pins; it does not document SVI/PMBus/I²C voltage programming.
- `PUA1` as ISL69247 with separate core and GFX PWM nets through their power stages and inductors to `APU_VDDCR_CORE_RUN` and `APU_VDDCR_GFX_RUN`.

This separates the **SoC target** from CPU/core and GFX examples. The CAD header says `REVISION "NA"`; the filename `r1.00` is not a verified PCB revision, and the file's applicability to the operator's physical board is unknown. The generic RT8237E output range is not a board-specific limit and does not provide a BIOS `1.15 V` setting. No resistor, feedback, solder, or electrical conversion method is proposed.

## CPU/GFX firmware examples are not SoC evidence

The exact CLV fixed-voltage PEIM trace statically shows named VCORE/GFX Setup fields staged through the ISL69247-labelled path and MEMIO fields staged through the ISL95712-labelled path. The exact source/dependency audit shows both PEIMs require two PPIs, including unresolved GUID `01F34D25-4DE2-23AD-3FF3-36353FF323F1`; dispatch is therefore not established. Their static page/target payloads do not prove PMBus page semantics, board rail identity, or output voltage.

The VCORE/GFX advertised `700..1250 mV` fields, MEMIO enum labels `1.20..1.45 V`, and other UI bounds are syntax/options only. They must not be repurposed as SoC limits, recommended values, or evidence that `1.15 V` is safe. The CBS `VDDCR_VDD`/`VDDCR_GFX` offsets and `VDDCR_SOC` telemetry calibration names likewise do not provide a proven absolute SoC setpoint path.

## Supersession of equal-number profiles

The following interpretation is superseded for user-facing decisions:

> “Memory and DF values are equal or numerically close, therefore MCLK=UCLK=FCLK / `1:1:1` is applied.”

The current evidence supports only that certain bytes/options and numeric ranges coexist in one HII package. It does not establish a shared unit, GDDR6 data-rate conversion, divider/crossing state, training acceptance, physical clocks, or stable latency improvement. Existing driver exports can alias one `MemclkFrequency` source, so equal displayed software numbers are not independent measurements. Preserve the 1800 request as a baseline; do not combine it with a voltage change or market it as synchronized operation.

## Minimum missing operator information

No electrical `1.15 V` method is invented here. The minimum inputs needed before a physical voltage or applied-clock claim can be considered are:

1. **Board identity:** a clear operator-board model/revision and PUS1/PUA1 package marking, sufficient to establish whether the imported GenCAD applies. The CAD itself reports revision `NA`.
2. **Revision-matched electrical mapping:** a schematic/boardview/netlist or equivalent authoritative trace for the operator's revision. It must join the named controller/output/net to the requested physical rail; for PUA1 it must also resolve any `PAGE` value to core/GFX. The current CAD does not provide the PUA1 page-value mapping and does not prove live-board fidelity.
3. **Current firmware state:** an authorized current NVRAM/Setup capture if the operator wants to claim the board is at the 1800 request or any menu value. The donor ROM byte is not current NVRAM readback.
4. **Application evidence:** exact PEI PPI/depex dispatch and controller-command semantics, followed by an independent voltage readback, before claiming any field is applied. No current report supplies that runtime chain.
5. **Clock/latency evidence:** independent physical or domain-specific clock observation and controlled baseline/candidate measurements before claiming synchronization or latency benefit. No numerical latency expectation is supported now.

These are information gates, not permission to modify or flash. Until they are supplied and verified, retain the 1800 request unchanged and make no voltage change.

## Evidence ledger and reopened manifests

Pinned donor:

- `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` — SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.

Latest PUS1/CAD and decision sources reopened by content:

- `docs/research/2026-09-21-rt8237e-pus1-control-path.md` — `54ea41f7df003de07613f8605dc882b92e6182b9b483d4ce4583bcf76a61f387`.
- `docs/research/2026-09-21-soc-net-independent-review.md` — `cfe1355d96a2179b55467d489c41c10297068f1d2120418254950eae9030e0e6`.
- `docs/research/2026-09-21-manual-voltage-safety-matrix.md` — `e43bb1d0108bb58ab8a81bb87bb5768e76ccf42d1b958424540c111a9926cb9d`.
- `docs/research/2026-09-21-voltage-mapping-source-followup.md` — `79c4f512d11bd8819bfbd9bccb7c0e35290c88c0f851c163c4bc0efa64cebe82`.
- `docs/research/2026-09-21-luna-fixed-rail-conditions-current.md` — `a62b77e80e13a1b61b97986b83bc23eeca02284b99ecc45a6f85bc86439df2b2`.
- `docs/research/2026-09-21-voltage-evidence-integration.md` — `9dda181dc478400d8e06313296674572fdb00bebb50dfedc4d2bee8703b91d36`.
- `docs/research/2026-09-21-clv-fixed-voltage-hii-reachability.md` — `e19daea30331751d9bff94b823167c1ad8eb9b2e282c862096c8a38d4edad02e`.

Reopened manifests (all checks passed):

- `evidence/firmware-audit/20260920-clv-voltage-control-inventory/SHA256SUMS.final` — SHA-256 `07636ad369a548050a3c851e5769b45ae39660f76607f81920adebf2d4e799d8`, `2/2 OK`.
- `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/SHA256SUMS.final` — SHA-256 `c35a3b79076001487a440605c0d3694ae043141b4b7728833be6c75c4f447bba`, `11/11 OK`.
- `evidence/firmware-audit/20260921-luna-fixed-rail-conditions/SHA256SUMS.final` — SHA-256 `df6459d59cf7de5fca61806de2dbdda07a2ab5c8f716297b25ed672b495a1e06`, `8/8 OK`.

Evidence class: `observed-bytes` for pinned hashes/manifest readback; `static-analysis` for exact HII, PEIM and boardview traces; `external-primary` for the qualified Richtek documentation; `external-community-source` for the GenCAD provenance. No `hardware-verified` voltage, clock, synchronization, or latency result exists. This guide is a decision/evidence boundary, not a candidate or hardware procedure.
