## USB-only diagnostic candidate (2026-10-01)

Intent: isolate the confirmed post-reboot USB absence from CYW43/BT/audio startup without changing the approved production candidate or flashing hardware.

Change: added compile-time `USB_ONLY_DIAGNOSTIC`; when enabled, `main.c` initializes the board and TinyUSB, then services `tud_task()` indefinitely and does not enter CYW43/bridge initialization. Added the corresponding CMake definition and skipped the production RAM-relocation post-link assertion only for this diagnostic build.

Artifact: `reports/waveshare-implementation-20260930/guide/Waveshare-RP2350B-Plus-W-USB-only-diagnostic-TEST.uf2`
SHA-256: `e7ec04c2938be0a384e2dffe1a4b5c1d88c3591a89778f0837cb9f8ae5c86c14`

Evidence: build completed with `cmake --build ... -j1`; UF2 structural checker passed; focused Waveshare tests passed (6 tests). No hardware write was performed.
