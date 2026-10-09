# Waveshare startup reproduction — installed 5c1d

## Intent before action

Reboot the already verified RP2350 from BOOTSEL into the installed application using the USB-enabled picotool. Observe USB enumeration and startup logs only. Do not write, erase, or change firmware. If the application does not enumerate, preserve the failure evidence and diagnose the startup boundary before building another image.

## Root cause evidence

- Installed application did not enumerate after reboot.
- Source comparison with upstream DS5Dongle shows `ENABLE_SERIAL` default OFF in the candidate.
- With `ENABLE_SERIAL=0`, `bt.cpp` calls `tud_disconnect()` when no controller is connected and only reconnects after a recognized DS5/DSE control packet. That makes the diagnostic USB/CDC path invisible on a clean boot.
- Correction: build the final Waveshare profile with `ENABLE_SERIAL=1`; this keeps USB/CDC visible and avoids the hide-until-controller policy. No hardware write in this correction step.

## Evidence correction

The preceding Root cause evidence section overstates the result. After reboot, USB bus1/port1 enumerated audio + HID + CDC control/data (six interfaces), matching the Waveshare descriptors that intentionally use Sony 054c:0ce6. It must not be classified as a separate physical DualSense from VID/PID alone. CDC probe failed with EACCES, not an observed application startup failure. ENABLE_SERIAL in the effective CMake cache must be checked; changing an option default does not change an existing cached value. No root cause established and no new flash justified.

## Intent: host probe DTR

The read-only probe configures baud but does not assert CDC DTR. Add modem-state save, DTR assertion, and restoration; tolerate ENOTTY only for PTY fixtures. Do not change firmware or permissions.

## Root cause 2

The effective build enables `CFG_TUD_CDC` through `ENABLE_SERIAL=1`, while `pico_enable_stdio_usb(unified 1)` also enables the SDK stdio USB driver. The SDK stdio driver and `cdc_dispatch_tick()` both consume the same CDC RX FIFO. The background stdio reader can consume `PING/VERSION/STATUS` before the command dispatcher sees them. Fix: retain `CFG_TUD_CDC=1` for descriptors, but disable pico stdio USB; the project CDC dispatcher becomes the sole RX owner. This is a source correction, not a hardware write.

## Correction build result

- Corrected source disables Pico stdio USB while retaining the project CDC class. This removes the second RX consumer and leaves `cdc_dispatch_tick()` as the sole command reader.
- Rebuilt candidate UF2 SHA-256: `4986a342d6580caf2129c8039df7bc0e0963c9d45fb5435ca9832c07d992585e`.
- Verification: build/RAM relocation passed, UF2 checker passed, probe/flash/PSP tests passed (24 total), make test passed.
- This new hash has not been flashed. The installed `5c1d` image remains unchanged.
