# PSP/TOCTOU reader continuation, 2026-10-07

Implemented `candidates/single-flash-emulator-v001/src/sparse_reader.c/.h`.

It validates the existing `image_pack.py` container header, page map, payload bounds and duplicate indexes; it clears stale state on failed open; it serves bounded read-only ranges and returns erased-page bytes as `0xFF`. It does not write flash and does not drive GPIO/MISO.

Verification: `python3 -m unittest discover -s candidates/single-flash-emulator-v001/tests -p 'test_*.py'` — **25/25 PASS**. The new test compiles the C reader with `cc -std=c11 -Wall -Wextra -Werror -pedantic` and tests a real Python-produced container, cross-page read, erased-page read, out-of-range read, truncated reopen and duplicate map rejection.

This closes the storage-reader part of the software path. It does not close the RP2350 SPI slave/MISO responder or the hardware gate. The existing single-flash target is still an input-only PIO capture prototype; no BC250 connection, reset, HOLD/DPD command, trace intervention or flash was performed.
