# BC-250 plain CLV 5.00 flash decision (2026-09-22)

**Decision: NO-GO to flash now.** This is a readiness decision for one fixed image, not a finding that the image is defective. No flash, erase, NVRAM/register write, voltage change, or board probe was performed for this decision.

## Bound target

- Candidate/reference only: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Size: `16,777,216` bytes.
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Provenance: the local donor manifest identifies a RetroWeb community redistribution for BC-250 board page 20611; uploader is unknown. This is not an authenticated current-board dump or project flash authorization.

## Why the decision is NO-GO

1. **No exact flash authorization is present.** The task requires separate approval before flashing. A research request, selection of a target image, prior flash, or old approval does not authorize a new write today.
2. **No fresh pre-write full-chip readback exists in the reviewed record.** The latest preserved full-chip readback is the 2026-09-19 W11-labelled snapshot, `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin`, SHA-256 `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`. It is a different CLV-derived image, not this donor and not a current 2026-09-22 chip read.
3. **The later live board record is partial, not a SPI identity read.** On 2026-09-21 the board-side read-only baseline observed DMI BIOS `P3.00 12/09/2021`, GPU PCI ID `1002:13fe`, and live `AmdSetup` values all-Auto (body SHA-256 `6f266c3c78a544d73eae5cea465756dd73e343fe16e2725d2300d08ba176d055`). It does not contain a full SPI dump/hash, exact BIOS image identity, or a physical board serial/revision. The retained report also records the operator's unspecified “да менял” response after W11. Thus the dated P3.00/runtime observation is stronger than treating W11 as current, but it does not establish the board's present full-chip contents.
4. **Recovery exists as historical evidence, not a newly certified recovery transaction.** Matching 16 MiB capture pairs are preserved (paths and hashes below), but they predate later board changes and have not been re-read or recovery-tested against the present physical chip/clip setup. Their existence must not be inflated into a current recovery guarantee.
5. **The intended P0 check is not a tuning result.** The older campaign plans define P0 differently (POST+video in the 4700S plan; any sign of life in the M5 plan), and neither definition is CLV-specific. For a future, separately authorized CLV trial, use baseline-only P0: POST plus video is the pass signal; LED/LAN/serial may be recorded as diagnostics. No benchmark, extra clock/voltage change, or 1:1:1 claim belongs in P0. The raw CLV NVAR contains MCLK request `AmdSetup+0x316=0x24` (static HII label `1800MHz`), `UclkDiv1M0=0x01` (`Enabled`), Memory P-state `Auto`, FCLK_DPM `Auto`, and DF override `Manual/1420`. These are saved request bytes, not measured clocks; the image is **not proven to be an all-Auto/no-OC profile**. Do not call a P0 observation proof of a safe clock profile, synchronization, SoC voltage, or performance gain.

The NO-GO is therefore based on missing exact approval and current write/recovery preflight—not on an unsupported claim that the board is running a particular GitHub image or that plain CLV cannot boot. A prior historical CLV readback is positive evidence of an earlier board state, but it is not current authorization or current-state proof.

## Evidence ledger: what is actually established

| Fact | Primary source | Date / identity | What it confirms; limit |
|---|---|---|---|
| Fixed plain CLV donor | `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` | Retrieved 2026-09-16; 16 MiB; `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` | Donor bytes and provenance; not current board firmware, boot acceptance, or authorization. |
| Historical plain-CLV board readback | `evidence/programmer/reads/20260917/postwrite-pure-clv.bin` | 2026-09-17; 16 MiB; same full-image hash `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` | At that capture, the saved board readback was byte-identical to the donor. It does not establish later/current SPI contents or boot behavior. |
| Latest retained full SPI snapshot | `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin` | 2026-09-19; 16 MiB; `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3` | Historical W11-labelled CLV-derived bytes. A 2026-09-21 lineage report notes the W11-specific directory lacks a same-date flashrom transcript/manifest; do not treat this as current. |
| Latest retained live Setup/runtime baseline | `evidence/runtime/20260921-takeover-live-baseline/` and `docs/action-logs/2026-09-21-takeover-live-baseline.md` | 2026-09-21; board project label `BC250-01`, DMI `P3.00`, PCI `1002:13fe` | Live DMI/PCI/NVAR snapshot and software clock exports. It is not a complete SPI readback; software MCLK/FCLK exports are not independent physical clock proof. |
| Original stock recovery pair | `evidence/programmer/reads/20260911/read-a.bin`, `read-b.bin`, and `dump/2.bin` | 2026-09-11; each 16 MiB; all `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0` | Two matching historical board reads and the retained dump; historical Winbond `W25Q128.V` probe. No fresh identification/read today. |
| Pre-M0 recovery/control pair | `evidence/programmer/reads/20260916/pre-m0-read-a.bin`, `pre-m0-read-b.bin` | 2026-09-16; each 16 MiB; both `3f836668bc194cfaef230de3ea842828e665608b96f9f50c7d3960615fbea5fd` | Matching historical board capture before the cross-flash ladder. It is not pristine stock (DFG `0x007FFF00`) and not the CLV donor. |

The donor, 2026-09-17 readback, 2026-09-19 W11 readback, and 2026-09-21 live DMI/NVAR observation are distinct evidence objects. Do not merge them into a single “current BIOS” claim.

## Minimum conditions before reconsidering the flash

1. Freshly identify the physical target board and SPI chip in the intended write session (record board identifier/revision as actually observed, package/JEDEC marking and orientation). `BC250-01` is a project label; old `W25Q128.V` is a historical probe.
2. With the board isolated per the existing programmer runbook, capture **two new** complete 16 MiB read-only SPI dumps to new paths; save the exact pinned `flashrom --version`, chip-probe output, command stdout/stderr/status, SHA-256 values, and `cmp` result. Require both reads to match before any write. Preserve the pre-write dump untouched.
3. Select and re-verify one exact recovery image for the intended rollback. Compare it to the current target and to the desired known bootable baseline; record its hash and independent recovery method. Do not silently treat either historical pair as a present recovery certification.
4. Define the bounded P0 observation and stop condition before any future operation. P0 only tests startup/sign-of-life; no sync, voltage, latency, or performance acceptance is bundled into it.
5. Obtain a new exact, image-hash-and-target-specific operator approval. The existing project programmer runbook requires the exact text form below. This guide does not itself satisfy it.

### Exact approval form for a future, separately gated action

Fill every bracket from a fresh verified capture; while any bracket is blank, this is **not** an approval:

> Подтверждаю запись файла `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` на плату `[observed physical board identifier/revision and verified SPI-chip identity]`. Текущий pre-write полный дамп: `[absolute path]`, SHA-256 `[full hash]`, 16 MiB; два чтения совпали. Recovery image: `[absolute path]`, SHA-256 `[full hash]`; проверенный recovery route: `[exact method]`. Разрешена только эта одна запись указанного образа; без изменений NVRAM, регистров, напряжения и других настроек. После записи требуется независимое полное чтение и совпадение SHA-256 с утверждённым образом; при несовпадении остановиться и не загружать плату.

The historical recovery choices to review—not pre-approved write sources—are:

- Original stock set: `/home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/read-a.bin` (corroborators `read-b.bin` and `/home/OWNER/orca/projects/bc250/dump/2.bin`), SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Pre-M0 set: `/home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260916/pre-m0-read-a.bin` (corroborator `pre-m0-read-b.bin`), SHA-256 `3f836668bc194cfaef230de3ea842828e665608b96f9f50c7d3960615fbea5fd`.

Neither set should be selected without an explicit recovery decision and current preflight. The second is not pristine stock. Existing read-only/write-gate procedure: `docs/runbooks/2026-09-11-bc250-programmer-and-candidate-gates.md`.

## Scope and stop boundary

- **Passed at saved-artifact layer:** exact donor and historical readback hash equality; historical recovery pair identities as recorded above.
- **Hardware-verified, but dated:** 2026-09-21 P3.00 DMI, PCI `1002:13fe`, live all-Auto clock NVAR body. This is not a current 2026-09-22 chip readback.
- **Unrun:** current physical board/chip identity; fresh two-read SPI backup; current exact image; current recovery verification; new exact approval; any CLV P0; CLV bootability on today's target; memory training; physical `MCLK:UCLK:FCLK`; SoC `1.15 V`; stability; latency/bandwidth/FPS comparison.
- **Not implied by flashing plain CLV:** physical `1:1:1`, a SoC setpoint or safe rating, preserved physical memory speed, or a measurable performance improvement.

Do not flash, erase, change NVRAM/registers, apply voltage, or make a board modification under this NO-GO. Reopen this decision only after the missing pre-write evidence and exact operator approval exist. For later delegated work, the control target is at most 7 active agents; after waits, list and collect results, retire terminal agents, and do not claim API closure where no close primitive exists.

## Sources reused

- `docs/guides/bc250-clv-111-decision-matrix.md` — existing CLV request/semantic boundary; recorded final linter result `38/38 PASS`, SHA-256 `fee0e7d2177b1f929879cbf6a9951568d50d1818c0aa7bbe214e65ed8b5b04c3`.
- `docs/research/2026-09-21-baseline-rom-ledger.md` — donor vs historical readback/recovery distinctions.
- `docs/research/2026-09-21-baseline-nvram-ledger.md` — saved request bytes and current-vs-historical distinction.
- `docs/research/2026-09-21-hardware-baseline-consolidated.md` — board/runtime status boundaries.
- `docs/research/2026-09-21-post-w11-change-timeline.md` — unspecified operator-reported post-W11 change; bounded record coverage.
- `docs/action-logs/2026-09-10-programmer-preflight.md` — original two-read baseline and historical chip probe.
- `docs/action-logs/2026-09-16-m0-window.md` — pre-M0 pair and its use/limits.
- `specs/2026-09-16-4700s-base-campaign-plan.md` §4 and `specs/2026-09-16-m5-native-pei.md` §4 — prior campaign-specific P0 definitions.
- `docs/runbooks/2026-09-11-bc250-programmer-and-candidate-gates.md` — exact approval, pre-write and post-write gate.
