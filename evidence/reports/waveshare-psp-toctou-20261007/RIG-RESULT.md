# RP2350 TOCTOU responder milestone

Date: 2026-10-07

## Done

- Corrected `candidates/waveshare-adapter-safe-v001/src/rig/spi_toctou.pio` so the saved clock count is not overwritten by header capture.
- Added the missing first payload `pull` before DO is enabled.
- Releases the Waveshare DO pin before releasing BC-250 `/HOLD`.
- Corrected DMA word byte order in `src/rig/rig.c` with byte-swap so RAM bytes are shifted MSB-first on the SPI wire.
- Added a CMake option `ENABLE_TOCTOU_RIG`, default OFF, so the experimental module can be compiled without silently enabling it.

## Verification

The explicit RP2350 toolchain build was run with `-DENABLE_TOCTOU_RIG=ON`:

- `cmake --build ... --target unified --parallel 1`: PASS
- generated PIO assembly: PASS
- RAM relocation linker gate: PASS

The build output is retained at:

- `~/.cache/waveshare-rig-source-20261007/build.log`
- `~/.cache/waveshare-psp-reader-20261007/rig-build/`

`procoder check` was run against the changed rig sources and did not pass: it reports the generated `spi_toctou.pio.h` as unavailable to its standalone clang pass, plus pre-existing repository findings. This is recorded, not hidden.

## Concrete blocker

This is not yet the mandatory integrated PSP/TOCTOU result. A CDC RAM-only window transfer path now exists, but the unified firmware still has no runtime caller that:

1. enforces stock/candidate image membership and transaction order on device,
2. runs the prepared payload through PIO/DMA with safe aborts and proven timing,
3. arms the responder under an explicit hardware-confirmed mode.

## RAM staging continuation

- Added `adapter_toctou_stage.c/.h` and `rig_transfer.py`. Host verifies both full-image hashes from the explicit plan and extracts one selected window, bounded to 4096 bytes. It emits commands only, with no serial I/O or arm.
- CDC supports `RIG_BEGIN address length sha256`, sequential `RIG_LOAD offset hex`, `RIG_COMMIT`, `RIG_CLEAR`, and `RIG_STATUS`. RP2350 verifies the entire staged payload through `pico_sha256`; invalid chunks are rejected before modifying bytes.
- Reused the existing SPI capture scratch lease in FLASH mode after an extra staging array caused linker RAM overflow. No capture capacity, controller/audio feature, heap or stack reservation was reduced to obtain a passing build.
- Lease is released on explicit clear, digest mismatch, CDC disconnect and mode exit. SPI stop does not wipe an active scratch lease. Digest success proves transfer integrity only; host image pins and PSP validation remain separate.
- `RIG_INIT` / `RIG_ARM` are explicitly blocked; `RIG_STATUS` reports `hardware=blocked`. No new hardware caller was enabled.

## Approved boundary continuation

Owner approved the software-only continuation with «да» after the proposal to bind staging to the rig while retaining blocked activation.

- Added `src/rig/rig_payload.c/.h`: verified staging is bound to the backend's exact 0x03/address mark and bit count, with retained `read_index`, bounds, 4-byte DMA alignment and zeroed final-word padding. The payload is borrowed from the existing scratch lease, not copied into another 4KiB allocation.
- Added `RIG_PREPARE <read_index>` and prepared/index status. Host commands derive this index from the selected plan window, not filenames or guessed order. Releasing staging clears the descriptor before releasing scratch.
- Experimental `rig_arm` consumes that descriptor and refuses activation through a fixed false hardware gate. Direct C `rig_init` also returns -3 before clocks/pins/PIO are touched. ARM object disassembly confirms init returns immediately and arm only reads the RAM descriptor then returns false. CDC init/arm remains blocked even when `ENABLE_TOCTOU_RIG=ON`. Read index is metadata only: PIO does not yet count/select transactions, so this is NOT an accepted order-sensitive responder.
- Corrected disarm so it does not restart the SM or re-trigger payload DMA; it stops SM/DMA, releases DO before HOLD, and clears the FIFO. Shutdown clears the descriptor and releases program memory. This is source/build evidence, not physical acceptance.
- Added `rig_override_model.py`, an interpreter of the actual override tail after match/prefetch. Normal completion sends the expected bits, releases DO before HOLD and stops one-shot. Early CS and stalled CLK reproduce a concrete hazard: the SM remains waiting with DO driven and HOLD asserted. Tests intentionally identify this blocker, not assert successful emergency recovery.
- Model excludes header capture, FIFO/DMA/autopull timing, synchronization and electrical behavior; first-bit timing remains unproved. No GPIO, clip or board operations were performed.
- Verification: default-OFF and experimental-ON RP2350 builds PASS with RAM relocation gate; candidate **29/29**, Waveshare **91/91**. `procoder check` is recorded separately and is not assumed passed. Different-family review is still outstanding.
- Boundary rollback copy: `~/.cache/waveshare-rig-boundary-20261007/before.zip`; logs in that directory. No commit, merge or flash performed.

## Abort guard continuation

Owner approved the next software step with «делай».

- Added dormant `rig_abort.c/.h`: an independent hardware timer deadline and CS rising raw GPIO IRQ. It uses pad overrides to release DO first and drive HOLD high without waiting for SPI clocks, PIO progress, DMA completion or the main loop.
- The guard is initialized only after the fixed-false hardware gate would be passed; normal firmware still does not touch these resources. `rig_init` returns before GPIO/PIO/clock changes while the gate is false.
- `rig_arm` now requires a bounded explicit timeout and refuses a second arm. The backend stops before cleanup and clears the descriptor only after disarm.
- C test `test_rig_abort.py` compiles the real `rig_abort.c` against fake SDK peripherals, checks CS and deadline paths, resource exhaustion, missed deadlines and re-arm rules. Fault injection removed the DO release from the source and produced the expected red result; the untouched source returned green. This demonstrates the test catches the intended regression, not just setup.
- Final candidate suite **31/31**, Waveshare regression **91/91**. Experimental ON and default OFF RP2350 builds PASS with RAM relocation gate. A fresh OFF build directory first rejected configuration because fixed `BUILD_DATE` was absent; OFF was subsequently built successfully using the already sealed-date build cache. No build gate was weakened.
- `procoder check` remains non-passing because standalone clang lacks Pico/generated headers and reports broad hygiene findings. Different-family review is still outstanding.
- This guard depends on IRQ delivery on its owning RP2350 core, a functioning timer/CPU and SDK helper execution; RAM-marked entries do not prove every transitive helper is RAM-resident. Interrupt latency, electrical pad release, recovery with real DMA and first-bit timing remain unmeasured. Host peripheral fakes are not hardware acceptance.
- Rollback: `~/.cache/waveshare-rig-abort-20261007/before.zip`. Final logs: `tests-final.log`, `regression-final.log`, `build-on-final.log`, `build-off-retry.log`, `fault-injection.log`, and `procoder.log` in that directory. No commit, merge, flash, BC250 command or physical connection occurred.

## Exact first-bit timing blocker (2026-10-08)

Continuation request: «Работай до результата или конкретного препятствия».

Added `candidates/single-flash-emulator-v001/rig_timing.py`, tracing the actual matched responder instructions rather than reusing the older selector timing estimate. The path from final header falling WAIT to first OUT is:

`WAIT -> JMP -> MOV -> JMP -> IRQ -> MOV -> PULL -> NOP -> SET -> WAIT -> OUT`

Even with zero input synchronization/HOLD delay and a ready payload FIFO, OUT is 10 PIO cycles after that falling edge. At hypothetical 400MHz PIO:

| Assumed SPI clock | Optimistic first-bit margin |
|---|---:|
| 10MHz | +10 cycles |
| 20MHz | 0 cycles, no setup margin |
| 25MHz | -2 cycles |
| 50MHz | -6 cycles |

These are analytical scenarios, not BC250 measurements. Real synchronization, FIFO and flash release delays can only worsen them. The older 7-cycle selector estimate does not prove this responder's first bit. The rig source's historical comment that 400MHz is comfortably enough is not acceptance evidence.

This is a concrete algorithmic blocker, not a missing optional polish check: at 25/50MHz this implementation cannot provide the first bit before the first sample, even in the optimistic model. Do not enable it or disguise the gap by restricting host staging to read_index zero. PIO read-order enforcement also remains unimplemented; host staging/metadata still accepts explicit later indices.

The needed inputs for selecting a replacement timing architecture are actual BC250 CLK/CS transaction traces and confirmed flash release behavior. Neither was obtained in this work, and no commands/connections were authorized or performed.

Verification: candidate **33/33** and Waveshare **91/91**, including timing bound and rejection of an unaccounted instruction delay. No tests were weakened. New logs and rollback are in `~/.cache/waveshare-rig-timing-20261008/`. Hardware activation remains blocked; the artifact remains `INCOMPLETE_NOT_FOR_FLASH`.

## Identified flash rules out HOLD (2026-10-08)

Owner confirmed `25Q128JVSQ`. Official Winbond W25Q128JV Rev F §11.1 maps this to W25Q128JVSIQ. §11 says Q has fixed QE=1, footnote 5 explicitly disables HOLD; §7.1.4 confirms IO3 instead of HOLD. Thus the current HOLD-based backend is not applicable to the identified chip. DO/HOLD pad-order tests are not evidence of original-flash isolation. No attempt to change QE, send B9/AB, assert reset, connect or enable the backend was made.

Primary PDF and exact hash/quotes are preserved in `docs/research/2026-10-08-w25q128jvsq.md`. DPD still requires proven FCH/SPI ownership, host ABh handling and a full responder, none established here. The 4KiB prepared-window backend is not sufficient for that route.

The next software blockers are transaction-index enforcement and a first-bit-safe timing architecture. The concrete delivery blocker is safe no-solder original-flash isolation: HOLD is unavailable on this variant. Measured IRQ/pad latency and physical flash ownership remain prerequisites; hardware gate remains fixed-false. The artifact stays `INCOMPLETE_NOT_FOR_FLASH`.
- Earlier staging-only baseline: verified unified RP2350 build with RAM relocation gate; candidate suite **27/27** including actual C staging roundtrip and corrupt/incomplete transfer rejection; Waveshare regression **91/91**. The C tests do not emulate the hardware SHA peripheral, CDC lease lifecycle or electrical behavior.
- `procoder check` remains FAIL, with missing Pico SDK/generated headers in its standalone clang pass and repository-wide findings. It is not counted as a pass.
- Logs: `~/.cache/waveshare-toctou-stage-20261007/{build-final.log,tests.log,regression.log,procoder.log}`.

The physical blocker is still original flash bus ownership through a clip on a soldered part: the exact flash marking/QE/HOLD behavior and a safe method to suppress its MISO response are unconfirmed. A clip is not isolation. No wiring or command to silence that flash is authorized by these source/build results.

There is also no physical bus/readback evidence. The current artifact remains `INCOMPLETE_NOT_FOR_FLASH`. No BC-250 connection, command, reset, flash, or hardware write was performed.
