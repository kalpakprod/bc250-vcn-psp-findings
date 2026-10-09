# Waveshare UF2 flash — 5c1d0677

## INTENT before write

- Target: Waveshare RP2350B-Plus-W in RP2350 BOOTSEL, mounted at `/run/media/kukuruza/RP2350`.
- Image: `reports/waveshare-implementation-20261001/final/Waveshare-RP2350B-Plus-W-BC250-DS5-TOCTOU-SPI-UART-LPC-FLASH-FINAL.uf2`.
- Expected SHA-256: `5c1d0677070d0dbc32de936957b80243c70b0ffc3749e6f2a6e4ceac62686465`.
- Approval: explicit user approval in chat for this exact SHA.
- Recovery: matching Waveshare recovery dumps retained at `/home/OWNER/.cache/waveshare-recovery-current-20260930/`.
- Procedure: verify hash and INFO_UF2, copy UF2 to mounted BOOTSEL volume, sync, observe reboot/unmount, then independently verify application USB and readback if available.
- STOP conditions: hash mismatch, missing BOOTSEL/INFO_UF2, copy error, no reboot event, or target changes before write.
- Scope: Waveshare UF2 only. No BC250 BIOS/SPI write.

## RESULT observed

- Hash preflight: PASS, exact SHA matched.
- INFO_UF2: PASS, UF2 Bootloader v1.1 / Raspberry Pi RP2350 / Board-ID RP2350.
- Copy and sync: command completed without reported copy error.
- BOOTSEL mount: disappeared after copy, indicating reboot/unmount event.
- Post-write USB: no RP2350 application device observed; only DualSense `054c:0ce6` appeared.
- Independent application CDC/readback: NOT AVAILABLE because the application did not enumerate.
- BC250 BIOS/SPI: untouched.
