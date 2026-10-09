# USB boot package: 20260923-probe2-usb (a BOOT stick, NOT a flash)

Purpose: run the read-only VCN state probe (probe3) at boot and return the
board to Linux automatically. No firmware flashing, no register writes, no
mailbox messages.

## Contents
- `EFI/BOOT/BOOTX64.EFI` — Bc250VcnProbe3.efi, read-only SMN probe,
  SHA-256 `c281d5d8a70656ba26422229f0bf8fed4147fc3aa585db4cd44313e01140dc48`
- `PROBE2.TXT` — marker; the probe writes its report only to the volume
  that carries this file
- `probe2-out.txt` — created by the probe on the board (not in this package)

## What probe3 does at boot
1. Reads via PCI config 0xB8/0xBC (root 00:00.0 SMN index/data):
   clock plan 0x0115D000/D004, VCN descriptor window (+0x560, both copies),
   domain bitmap 0x0000CCB8, power status 0x01D80218, request bits
   0x0115F95C, clock controller 0x0115F800..0x0115F974. Read-only.
2. Saves the report to `\probe2-out.txt` on this stick.
3. Reboots the board (EfiResetCold). With a one-time boot pick the firmware
   then boots Linux as usual.

## Prepare the stick (once)
FAT32 stick; files at the root exactly as in this folder
(`EFI/BOOT/BOOTX64.EFI`, `PROBE2.TXT`). Two ways:
- A) stick plugged into the BC-250 host: `scripts/probe2.sh push`
  (writes the payload over SSH and prints the next steps), or
- B) from any machine: copy this folder's contents to the stick root.

## Capture loop (per run)
1. Agent side: `scripts/probe2.sh fetch` — starts the timer BEFORE the reboot.
2. Operator: reboot the board and pick the USB stick ONCE in the one-time
   boot menu. Do NOT change the boot order: the probe reboots the board and
   it must go back to Linux, not loop into the stick again.
3. The probe runs for a few seconds, writes the report, reboots.
4. `fetch` detects the return, mounts the stick read-only on the board,
   copies `probe2-out.txt` to `evidence/runtime/<timestamp>-probe2-out.txt`
   and prints the descriptor verdict (populated / EMPTY).

## Risk note (honest)
First-contact SMN reads at this late boot phase carry a measured hang risk
(the 2026-09-12 wedge class). If the board does not return within the
timeout: cold power cycle. It boots the current P3.00 image; nothing was
written anywhere except this stick.
