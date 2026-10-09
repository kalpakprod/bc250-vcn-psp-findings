# PSP/TOCTOU implementation

## 1. Scope

Implement the PSP/TOCTOU path as a bounded, reproducible offline pipeline and preserve the separate RP2350 runtime boundary. The offline path must pin exact stock/candidate image hashes, use an explicit transaction index and address window table, reject substituted images and malformed reads, and produce the existing serve-map. No claim of hardware TOCTOU is made until the bus, reset, chip-select, MISO timing and recovery are independently accepted.

## 2. Planning anchor

Owner directive 2026-10-07: «PSP/TOCTOU реализовать обязательно». Existing anchors: `.procoder/plans/20260928-single-flash-emulator.md`, `candidates/single-flash-emulator-v001/`, `candidates/waveshare-adapter-safe-v001/src/adapter_toctou*.c/.h/.pio`, and the exact stock/candidate images used by `scripts/build_toctou_serve_map.py`.

## 3. Connected existing logic

- The existing experimental `src/rig/rig.c` and `src/rig/spi_toctou.pio` can be compiled with `ENABLE_TOCTOU_RIG=ON` (default OFF). The option checks compilation only: no runtime caller exists, and the linker can discard the unreferenced module. It does not put a working MISO responder into the delivered image.
- The PIO source now retains the count outside the captured ISR, obtains the first payload word before enabling DO, and releases DO before `/HOLD`. These corrections do not establish electrical safety or first-bit timing.
- RAM-only window staging is integrated into CDC (`RIG_BEGIN`, `RIG_LOAD`, `RIG_COMMIT`, `RIG_CLEAR`, `RIG_STATUS`). `rig_transfer.py` checks both pinned full-image hashes and extracts the selected window; the firmware checks sequential transfer bounds and payload SHA-256 using `pico_sha256`. This proves transfer integrity only, not PSP signatures or firmware-side image membership. It leases the existing SPI capture scratch in FLASH mode, releases on clear, digest failure, CDC disconnect or mode exit, and never opens a flash transport.
- `RIG_PREPARE <read_index>` binds a verified staging lease to a bounded rig payload descriptor: 0x03/address mark, exact byte length, clock count, and explicit read index. The experimental DMA backend consumes this descriptor instead of a duplicate 4KiB buffer. This is payload preparation, not activation or device-side full-image membership verification.
- `RIG_INIT` and `RIG_ARM` still return `ERR rig-hardware-unverified`. The C `rig_arm` API also refuses activation with a fixed false hardware gate. Read-index selection is NOT implemented in PIO; retaining the index does not enforce it. No physical bus/readback test has run.
- `rig_override_model.py` executes the actual override tail after header match/payload preload. It verifies normal release ordering and one-shot completion, and reproduces that early CS and stalled CLK leave DO driven/HOLD asserted. It is not a DMA/autopull, header, timing or electrical simulator.
- `rig_abort.c/.h` adds a dormant independent guard: hardware timer deadline plus CS rising raw IRQ, with GPIO pad overrides releasing DO before deasserting HOLD without waiting for SPI clocks or cooperative code. The guard is initialized only by the experimental backend, and `hardware_accepted` remains false. It bounds recovery attempts but does not prove interrupt latency, pad electrical behavior, or first-bit timing on hardware.

- `image_pack.py` provides lossless sparse 4KiB storage and random reads.
- `spi_model.py` provides bounded `0x03` reads and per-read `ReadRule` selection.
- `pio_selector_model.py` traces the older selector ordering but does not serve data.
- `build_toctou_serve_map.py` compares exact 16MiB stock/candidate bytes and identifies anchor-sensitive changed ranges.
- Unified firmware contains a separately gated TOCTOU state/runtime path. `ADAPTER_TOCTOU_WIRING_CONFIRMED` is intentionally not enabled by default; unconfirmed physical wiring must not be armed.

## 4. Use cases

1. Pack either exact 16MiB image without changing source bytes.
2. Read any valid range through synthetic `0x03`; reject unsupported opcode, short header, overflow and out-of-range address.
3. Select stock/candidate only from an explicit `read_index + address window + image` table. Never infer order from filenames.
4. Reject a plan if either supplied image hash or capacity differs from the pinned identity.
5. Export hardware state as disconnected, untested and unauthorized until a separate physical gate is completed.

## 5. Implementation checklist

- [x] Add `candidates/single-flash-emulator-v001/toctou_plan.py` with pinned identities, explicit windows, non-overlap validation, image verification, model construction and safe JSON export.
- [x] Add tests for explicit order, hash substitution rejection and overlapping-window rejection.
- [x] Run the existing serve-map builder against the exact pinned stock/candidate files.
- [x] Add a bounded C read-only reader for the existing sparse container; compile and exercise it against a Python-produced container.
- [x] Assemble the experimental PIO and compile its driver using the unified RP2350 toolchain (not runtime integration).
- [x] Connect host sparse image/window selection to bounded RAM staging, verify payload SHA-256, and reject hardware activation.
- [x] Bind verified staging to the experimental backend payload descriptor without GPIO activation or an additional large buffer.
- [x] Model the actual override tail for complete, early-CS and stalled-clock transactions; preserve the reproduced unsafe aborts as blockers.
- [x] Add a dormant clock-independent abort guard with deadline and CS-rise paths; test the real C guard with fake SDK peripherals and fault injection.
- [ ] Enforce cryptographic image/window membership and read-order selection on device, validate abort latency/pad behavior and first-bit/FIFO timing, and authorize the arm API. Preparation is not this completed gate.
- [ ] Hardware acceptance: synthetic PIO timing, electrical levels, stock flash release, readback and recovery.

## 6. Open questions

Concrete timing blocker (source analysis 2026-10-08): `rig_timing.py` traces the current matched PIO path from the final header CLK-falling WAIT to the first payload OUT. The optimistic lower bound is 10 PIO cycles, excluding GPIO synchronization, FIFO stalls, HOLD delay and output setup. At hypothetical 400MHz PIO this already misses the first mode-0 sample at 25MHz SPI by 2 cycles and at 50MHz by 6. At 20MHz there is zero setup margin. These SPI frequencies are scenarios, NOT measurements of BC250. The older selector timing model does not establish the responder's first-bit behavior.

A passing build cannot repair this path. The responder needs a timing architecture change, informed by actual CLK/CS traces and flash release behavior. Full read-index selection is still absent in PIO; staging indices remain available as metadata, not silently restricted to index zero.

Confirmed route blocker 2026-10-08: owner identified `25Q128JVSQ`; official Winbond Rev F marking table maps it to W25Q128JVSIQ. Q has fixed QE=1 and HOLD disabled (§11 footnote 5, §7.1.4). Pin7 is IO3; the HOLD/MISO rig must not be enabled for this chip. Device identity remains owner-reported, not live readback. Primary evidence and hash: `docs/research/2026-10-08-w25q128jvsq.md`.

Blocking hardware: exact PSP transaction order on the live BC-250, J4004 ownership and CS/MISO isolation, reset/DPD behavior, first-bit timing, and recovery. DPD requires safe FCH/SPI ownership and ABh handling; the current 4KiB window backend is not a full responder. These do not block offline work, but HOLD is no longer an available isolation assumption for the identified variant.

2026-10-08 reset-route narrowing: freshly parsed GenCAD joins J4004.8/PROGRAM# through D606 to RESETCON#, then 0Ω R8721 to SYS_RESET#/SU1.U4 (A68H FCH). This is a concrete candidate, not proven control/tri-state behavior. D606 polarity was initially missing and is now documented by LRC Rev.A: pin1 cathode/PROGRAM#, pin2 anode/RESETCON#. FCH SPI ownership during reset remains unverified; reset is shared with PANEL/SIO and does not physically isolate flash nets. Evidence: `reports/waveshare-reset-path-20261008/RESULT.md` and the subsequent `AMD-SPI-RESULT.md`.

BC250-76 document follow-up: AMD51192 reset/PLL controls, SPI idle/ROM-enable and bridge-disable fields do not document high-Z of the main SPI outputs. PwnSpiBus drives listed signals low in S3/S4/S5 rather than releasing them; IMC96h/B4h stops only IMC fetch. A separate untested hypothesis uses the FCH's documented alternate opcode method to issue B9h before a controlled restart, avoiding external-master transfer for that command. This is not an adopted architecture or permission to execute: early FCH/PSP command trace (including ABh), retained flash VCC, full responder and recovery remain unproved. The current4KiB override is insufficient. RawCAD pin2→SB_SPI_DI/pin5→SB_SPI_DO is compatible with host-side naming; the earlier claim of a Winbond numbering conflict is not established.

BC250-76 firmware continuation: exactCLV5.00 FchPei entry/task table resolves to initializer4C59h and a copied templateMode6/NormSpeed2, targeting single-lane33MHz by AMD51192. This is not a measured live/early-PSP mode. Existing10-cycle matched-header path already needs25ns at400MHzscenario versus15.15ns sampledeadline33MHz (margin-130/33cycles), grounding the timing blocker in a named firmware default. RDID/status/QE routines are conditional; defaultMode6 skips QEcheck. FchDxe ABimmediates map to I/Oport550h, not flash wake-up. The default12-entry QEtable lacks EF4018, but no live defect or ID-spoofing solution is inferred. Early type1PSP generic layout is unresolved and immutableROM/earliest command trace remains uncovered. Source hashes/RVAs/model: `reports/waveshare-reset-path-20261008/FIRMWARE-SPI-RESULT.md` and `firmware-spi-evidence.json`. No code, architecture, hardware or arm gate changed.

Non-blocking for this software result: absolute wall-clock time and external voltage measurement. Neither is required by this implementation.

## 7. Decision log

- 2026-10-07: owner made PSP/TOCTOU mandatory. Implement offline pipeline now; do not silently convert unverified electrical assumptions into an armed firmware feature.
- 2026-10-07: exact image identity is enforced by SHA-256. A passing host model/build is not hardware success.
- 2026-10-07: no BC250 connection, BIOS write, firmware flash, reset control or purchase performed.
- 2026-10-08: owner-confirmed 25Q128JVSQ maps to a fixed-QE Q variant with HOLD disabled. Exclude HOLD-based activation; do not silently substitute QE writes/DPD/reset for a proved isolation plan. No physical action performed.
