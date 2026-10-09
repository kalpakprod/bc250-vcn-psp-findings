# USB-first controller/diagnostic build

## Intent

Implement the approved plan's first source slice without hardware writes: keep USB/CDC alive before subsystem initialization, expose startup stage/error in STATUS, split DS5Dongle bridge initialization into bounded steps, and keep the existing production RAM-relocation gate.

## Source change

- Added `adapter_startup` stage tracking.
- Added `bridge_boot_begin()` and one-step `bridge_boot_step()` around existing DS5Dongle initialization.
- Main now services TinyUSB and CDC during a bounded early window and while bridge boot steps run.
- USB-only diagnostic mode now also services the CDC dispatcher.
- Watchdog notice no longer blocks USB with a six-cycle sleep loop.

## Artifact

- Path: `reports/waveshare-implementation-20260930/guide/Waveshare-RP2350B-Plus-W-USB-first-controller-diagnostic-TEST.uf2`
- SHA-256: `aba20b1dc0193c6484d93937425b4451df0fbcb9df6ac560fc5040365926bfa3`
- Structural check: PASS (`scripts/check_waveshare_uf2.py`)

## Evidence

- Production build: `cmake --build /home/OWNER/.cache/waveshare-adapter-safe-v001-build -j1`
- RAM relocation assertion: PASS
- Focused tests: 21 passed
- Contract gate: 7 passed
- Hardware write: NOT PERFORMED
- Hardware acceptance: NOT CLAIMED
