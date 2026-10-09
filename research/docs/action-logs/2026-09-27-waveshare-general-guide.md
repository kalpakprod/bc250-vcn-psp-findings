# Waveshare RP2350B-Plus-W general wiring guide

## Intent

Create a new operator-facing guide for standalone Waveshare RP2350B-Plus-W
bring-up and generic 3.3 V I2C sensor wiring, while separating verified board
facts from unverified BC-250 connector details. Do not edit the historical
TOCTOU wiring guides, the active repository-audit files, firmware, or hardware.
No physical connection or board operation is authorized by this documentation
work.

Target: `docs/guides/waveshare-rp2350b-plus-w-general-wiring.md`

## Intent 2026-09-28 — correct BoardView lookup error and complete guide

Update the operator-facing guide with the verified local CAD mapping for
`I2C_HEADER1`, trace its pull-ups to the boardview rail, and distinguish CAD
design intent from live voltage measurement. Use the official RP2350 datasheet
and the Waveshare product documentation for controller and board details;
cite the community BC-250 documentation only as secondary corroboration.
Append a correction to `MISTAKES.md` because the operator identified a repeat
of the prior BoardView-source lookup mistake. Do not connect hardware, assert
live signal measurements, or modify firmware.

Targets: `MISTAKES.md` and
`docs/guides/waveshare-rp2350b-plus-w-general-wiring.md`.

## Result 2026-09-28

- Rechecked the raw BoardView and connector map: I2C_HEADER1 pin 1 is
  SMB0_DA_ISO/SDA, pin 2 is SMB0_CL_ISO/SCL, and pin 3 is GND.
- Traced R13361/R13360, each 4.7 kOhm, from SDA/SCL to +3.3V_RUN. This is
  static CAD evidence, not a live voltage measurement.
- Opened the official Waveshare pinout page, Raspberry Pi RP2350 datasheet,
  and public BC250 pinout references. The BC250 documentation identifies this
  header as the PMBus interface; no connection or bus operation was performed.
- Added the standalone I2C guide and recorded the repeated source-lookup
  mistake in MISTAKES.md. Existing staged and unstaged repository changes were
  preserved; no commit, hardware, or firmware action occurred.
- `make test` printed all seven contour checks passing and `MAKE_TEST_EXIT=0`.
  The execution wrapper timed out after printing that completed result.
