# PROGRAM#/reset route after HOLD exclusion

Owner continuation: «продолжай». Date: 2026-10-08. Scope: read-only static investigation of a possible no-solder DPD preparation route. No hardware operation or change of firmware architecture was authorized by this continuation.

## Input and evidence class

- Raw GenCAD: `evidence/hardware/ASRock AMD BC-250_ISL_X5R r1.00.cad`.
- 1,923,019 bytes; SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`.
- Selected joins freshly extracted from raw `SIGNAL`/`NODE` records, with line numbers in `reset-net-trace.json`. The source contains UTF-8 part text; an initial ASCII decode failed without producing evidence, then UTF-8 decoding succeeded without replacement characters.
- Historical parse used for consistency comparison only: `archives/imported/recon-evidence/legacy-tmp-bc250-recon/boardview-parse.json`. It is NOT an independent board/schematic source.
- Evidence is **observed-bytes/static-analysis**, not **hardware-verified**. The filename's r1.00 does not establish the owner's physical revision or population.

## Newly narrowed route

The raw CAD links programming-header pin 8 to the reset path of the same FCH connected to the BIOS SPI nets:

| Join | Raw CAD evidence |
|---|---|
| J4004.8 → PROGRAM# | line 76281 |
| PROGRAM# → D606.1 | line 76280 |
| D606.2 → RESETCON# | line 75102 |
| RESETCON# → R8721.1 | line 75105 |
| R8721.2 → SYS_RESET# | line 78564 |
| SYS_RESET# → SU1.U4 | line 78565 |

Device records label D606 **LRB751S-40T1G Schottky**, R8721 **0Ω**, and SU1 **AMD Bolton-D2H/A68H, 218-0844029**. PROGRAM# also has R678 **10kΩ** to the named +3.3V_SB rail. RESETCON# joins PANEL1.4, C300, R8728 and the OR93 → RESTCON# → OR46 → SIO_RESTCON#/UIO1.83 path. It is a shared system-reset network, not an isolated flash WP switch.

The named +3.3V_SB net also includes BIOS_A1.8/BIOS_S_A1.8. This is a static supply join, not a measurement that flash power remains correct during reset.

The SPI CS/DI/DO/CLK nets in the same extracted file still join BIOS, J4004 and SU1 directly. PROGRAM# does not introduce a physical break into them.

## What still cannot be concluded

1. Connectivity through D606 is not proof that pulling PROGRAM# low asserts SYS_RESET#. Its exact pin polarity must come from an applicable device datasheet or verified schematic; no polarity is inferred from the name.
2. Even if SYS_RESET# is asserted, there is no established rule that A68H releases CLK/MOSI/CS to high impedance, with timing and glitch-free ownership transfer. A reset label alone does not prove this.
3. CAD does not establish physical board revision/population, electrical voltages, SIO drive mode or behavior when holding reset.
4. Original W25Q128JVSIQ has HOLD disabled; reset tracing does not resurrect HOLD. DPD still requires safe B9 ownership, protection against host ABh wake-up and a full responder rather than the present prepared 4KiB window.
5. The current responder's first-bit timing remains separately inadequate in the documented 25/50MHz scenarios; these frequencies are not measured on BC250.

## Primary-document search and actual obstacle

OmniRoute DuckDuckGo returned no diode datasheet results; OpenCLI Brave failed navigation; OmniRoute Tavily returned 429 with a 300-second retry time. No primary diode polarity/FCH reset-to-SPI tri-state document was obtained. This is a document/access gap, not a claimed server-wide outage or proof that those properties are impossible.

The hardware candidate is now specific: **J4004.8 → D606 → RESETCON# → 0Ω R8721 → A68H SYS_RESET#**. The missing acceptance input is precise: **verified D606 polarity and documented/measured A68H SPI ownership while SYS_RESET# is held**. Until that is obtained, do not issue PROGRAM#/reset/B9/AB or provide an active wiring instruction.

## Unchanged boundary

No connections, GPIO changes, BC250 commands, resets, flash/QE/DPD operations, commits, purchases or deployments occurred. Fixed-false hardware gates remain in place. This investigation narrows the remaining no-solder route; it does not complete PSP/TOCTOU.
