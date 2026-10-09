# USB-only diagnostic UF2 flash

- Target: Waveshare RP2350B-Plus-W (RP2350 BOOTSEL)
- Image: reports/waveshare-implementation-20260930/guide/Waveshare-RP2350B-Plus-W-USB-only-diagnostic-TEST.uf2
- SHA-256: e7ec04c2938be0a384e2dffe1a4b5c1d88c3591a89778f0837cb9f8ae5c86c14
- Approval: explicit owner approval: да
- Purpose: isolate USB enumeration from CYW43/BT/audio startup.
- Recovery: two matching 16 MiB pre-flash dumps retained at /home/OWNER/.cache/waveshare-recovery-current-20260930/; hash d3dec91fadd5a86982f6a6d80090cc431dcf539fdeebe220de1b83de503b8379.
- Stop conditions: absent BOOTSEL, hash mismatch, copy error, or no post-write reboot event.
- Procedure: verify hash, confirm INFO_UF2.TXT, copy UF2, sync, observe reboot/re-enumeration. No AMD or SPI writes.

## Result

- Exact SHA-256 preflight: matched.
- BOOTSEL identity: RP2350 Bootloader v1.1, Board-ID RP2350.
- UF2 copy: OK.
- Reboot/unmount event: observed after 2 seconds.
- Post-write device: `/dev/ttyACM0` appeared as `root:uucp`.
- Hardware result: USB CDC enumeration is now observed for the USB-only diagnostic image.
- VERSION/STATUS: pending read-only query; current user lacks direct `uucp` access and noninteractive sudo will be tested without changing permissions.

## CDC query result

- ACL applied by operator to `/dev/ttyACM0`.
- `VERSION` and `STATUS` were transmitted successfully with exit status 0.
- No reply was returned. This is expected for the current USB-only diagnostic: it intentionally runs only `tud_task()` and does not run `cdc_dispatch_tick()` or the command handlers.
- Conclusion: USB enumeration is hardware-verified; command protocol is not tested by this image.
