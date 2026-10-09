# USB boot package: 20260923-probe4-usb (a BOOT stick, NOT a flash)

Purpose: run the VCN state probe via the SMU MAILBOX transport after run 1
of probe3 proved the raw SMN window wedges the board at the first read
(SMN 0x0115D000, 2026-09-23 ~21:05). Same target register set, different
transport. The board returns to Linux automatically.

## Contents
- `EFI/BOOT/BOOTX64.EFI` — Bc250VcnProbe4.efi, mailbox-transport probe,
  SHA-256 `706c9ddb818365ec7699ecc1a19f8c3f2717e43b7f490699fd30f3caa5df909a`
- `PROBE2.TXT` — marker; the probe writes its report only to the volume
  that carries this file
- `probe2-out.txt` — created by the probe on the board (not in this package)

## What probe4 does at boot
1. SMU debug unlock (the hardware-proven D9R/D10/d19 sequence: Q2 ring
   writes + DMA table + SRAM fixup). If the secure read is already open,
   the unlock is skipped and reported as such.
2. Reads the same set as probe3 — clock plan 0x0115D000/D004 + VCN
   descriptor window (+0x560, both copies), domain bitmap 0x0000CCB8,
   power status 0x01D80218, request bits 0x0115F95C, clock controller
   0x0115F800..0x0115F974 — but every read is the SMU's own Q3 0x2A
   secure-read service. The raw PCI 0xB8/0xBC window touches ONLY the
   Q2/Q3 mailbox registers (0x03B1xxxx), the proven-safe addresses.
3. Prints a line per phase (unlock stages, each read) so that if anything
   wedges, the LAST LINE ON SCREEN names the transport step and address.
4. Saves the report to `\probe2-out.txt` on this stick, reboots
   (EfiResetCold). One-time boot pick -> Linux boots as usual.

## Honest risk note (NOT read-only, unlike probe3's claim)
The unlock WRITES SMU SRAM. That exact sequence is hardware-proven (it
lived inside the flashed D9R/D10 images, which booted normally; writes
are the measured-safe first touch on this board) and is non-persistent:
the PSP re-applies state at every boot. If the SMU wedges internally
(mailbox stops answering), the app aborts the survey after 3 timeouts,
still saves the partial report and reboots; a wedged board recovers only
by a cold power cycle. Nothing is written to the SPI or the OS disks.

## Capture loop (per run)
1. Agent side: `scripts/probe2.sh fetch` — timer BEFORE the reboot.
2. Operator: reboot the board, pick the USB stick ONCE in the one-time
   boot menu. Do NOT change the boot order.
3. The probe runs (seconds to ~a minute with the unlock), saves, reboots.
4. `fetch` detects the return, pulls `probe2-out.txt` into
   `evidence/runtime/`, prints the descriptor verdict.
