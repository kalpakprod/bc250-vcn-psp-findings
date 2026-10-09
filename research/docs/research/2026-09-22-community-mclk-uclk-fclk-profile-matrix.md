# Community MCLK/UCLK/FCLK profile matrix — BC-250

Date: 2026-09-22
Status: report-only, static comparison. No ROM, NVRAM or hardware write.

## Scope and source classes

The comparison uses:

- local Discord exports and search receipts: `/tmp/discord-track-07-search-B.md`, `/tmp/discord-track-01-chat-history.md`, `/tmp/discord-track-02-chat-mining.md`, `docs/research/2026-09-22-discord-synthesis.md`;
- local Telegram corpus: `/tmp/bc250_6mo.jsonl`, `docs/research/telegram-bc250-6mo/`;
- public repositories retrieved on 2026-09-22: `fanoush/bc250_memcfg`, `Dream-Cypher/bc250-memory-timing-boot-fix`, `NexGen-3D-Printing/SteamMachine`, `cachenetics/project-ariel`, `elektricM/amd-bc250-docs`, `katzzero/bc250-unofficial-community-guide`, and `bc250-collective/amd_smu_reverse_engineering`.

Community reports are participant evidence, not physical proof on BC250-01. GitHub source is code/document evidence. The exact CLV bytes are observed-byte evidence.

## Evidence-led conclusions

1. Community consensus is that BC-250's shared GDDR6 gives high CPU-visible memory latency. Reports commonly place it above 100 ns, but methods differ.
2. Discord repeats the Zen 2-style `1:1:1` rule and reports that memory overclocking usually breaks that relationship. No public community recipe proves a physical `MCLK=UCLK=FCLK` state on BC-250.
3. Community SMU notes say FCLK/MCLK control is not exposed through a proven ordinary SMU path. Driver values around 450 MHz are treated as an inverted or aliased representation of the GDDR6 clock, not as a direct physical counter.
4. `fanoush/bc250_memcfg` and the community timing file support CMOS memory-clock/timing edits, but report little confirmed latency gain from timings and warn about stability.
5. `Dream-Cypher/bc250-memory-timing-boot-fix` provides the strongest current external hardware result: on one board 1650 and 1600 MHz booted repeatedly, while 1750 was intermittent and 1700/1740/1500/1000 failed training. This establishes a memory/ABL stability control, not synchronization.
6. `cachenetics/project-ariel` treats `UclkDiv1M0` as an advanced full-clock control and recommends Auto. Its benchmark path separates bandwidth, random access, pointer-chase latency and integrity, which is the right validation shape for this task.
7. Community voltage numbers are not a revision-matched SoC setpoint proof. The operator ceiling `1.15 V` is retained as a hard experiment policy, but no BIOS value is assigned to it.

## Exact CLV fields

Source: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.

`AmdSetup` body base is `0x4CF`.

| Field                  | Body offset |     ROM offset |              Observed CLV value |
| ---------------------- | ----------: | -------------: | ------------------------------: |
| MemoryClockSpeed       |     `0x316` |        `0x7E5` | `0x24` (36, IFR label 1800 MHz) |
| UclkDiv1M0             |     `0x330` |        `0x7FF` |                          `0x01` |
| FclkDpm                |     `0x6A3` |        `0xB72` |                   `0x0F` (Auto) |
| DfClockOverrideControl |     `0x703` |        `0xBD2` |                 `0x01` (Manual) |
| DfClockOvrd            |     `0x704` | `0xBD3..0xBD4` |              `0x058C` LE (1420) |
| MemoryPstate           |     `0x36D` |        `0x83C` |                   `0xFF` (Auto) |

These bytes are requests and persistence values. They are not physical clock readbacks.

## Minimal comparison matrix

The values below are a test matrix, not a flash authorization and not a claim of 1:1:1.

| State                         |       MemoryClockSpeed |     UclkDiv1M0 |     FclkDpm |       DF control/value | Memory P-state | Voltage   |
| ----------------------------- | ---------------------: | -------------: | ----------: | ---------------------: | -------------: | --------- |
| C0 observed native CLV        |    `0x24` / 1800 label |         `0x01` |      `0x0F` |          `0x01` / 1420 |         `0xFF` | unchanged |
| C1 native lower-clock control |    `0x1A` / 1330 label |    `0xFF` Auto | `0x0F` Auto | `0xFF` / 1000 fallback |    `0xFF` Auto | unchanged |
| C2 native UCLK comparison     |    `0x23` / 1750 label | `0x01` Enabled | `0x0F` Auto | `0xFF` / 1000 fallback |    `0xFF` Auto | unchanged |
| P3 CMOS stability control     | CMOS `ClockSpeed=1650` |      unchanged |   unchanged |              unchanged |      unchanged | unchanged |

C1 and C2 are native AmdSetup comparison states. P3 is a separate CMOS control from the Dream-Cypher/fanoush path and is not an AmdSetup BIOS field. Do not combine them in one write.

## Why no SoC voltage value is included

The 1.15 V ceiling is an operator requirement. The current evidence does not identify a revision-matched BIOS field whose stored value is an absolute SoC voltage, nor does it prove the rail/controller/net mapping. Historical `VDD offset` values `80` and `100` are unresolved encodings. They must not be labelled 1.14 V or 1.15 V.

## Acceptance checks before any live trial

For each state, if separately approved later:

1. preserve a fresh full-chip dump and recovery path;
2. change one logical state only;
3. read back NVRAM after save/reset;
4. cold-boot repeatedly and capture POST/training outcome;
5. run CPU pointer-chase latency, GPU memory latency, bandwidth and integrity checks;
6. capture UMC registers and all available clock fields;
7. reject the claim `1:1:1` unless independent MCLK, UCLK and FCLK observations agree within a predeclared tolerance;
8. stop on training failure, no POST, unexpected voltage or data-integrity error.

## Machine-readable result

`/tmp/profile_matrix_20260922/result.json` records the exact CLV hash, field bytes, profile values and the hard voltage policy. It is intentionally outside the repository because it is a disposable generated result.

## Validation

- Source size check: 16 MiB, passed.
- Source SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Profile matrix generation: exit 0.
- Firmware modification: none.
- Hardware/NVRAM execution: not run.
