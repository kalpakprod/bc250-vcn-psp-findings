# Waveshare UF2 readback — 5c1d0677

- Target: RP2350 BOOTSEL, USB `2e8a:000f`, RP2350 A4, 16 MiB flash.
- Readback tool: locally rebuilt picotool v2.3.1 with libusb support under `~/.cache/waveshare-readback/`.
- `picotool info -a`: boot type `bootsel`, chipid observed, flash size 16384K.
- `picotool save -p -v`: wrote 841512 bytes to `/home/OWNER/.cache/waveshare-readback/installed-program.bin`.
- Independent `picotool verify` against the exact approved UF2: `OK` through 100%.
- Readback SHA-256: `2636b11a6e6f588f01dbfdddf31998eb9c6eef470b294e6c6617fae19deee9ff`.
- No write, erase, or BC250 BIOS/SPI operation performed in this readback.
