# Runtime audit: 1.92 kernel mode1 (VCN probe) boot (2026-09-12, SSH read-only)

- Access: steammachine@127.0.0.1, key `~/.ssh/id_ed25519`, passwordless sudo OK. All commands read-only (uname, cat, uptime, ls, journalctl -k, dmesg).
- Audit time 2026-09-12 02:26 PKT; uptime 2:35, so boot occurred 2026-09-11 23:51 PKT.
- SPI image on board: APCB-only candidate `BC250_APCB_DFG_only_v001` SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70` (unchanged since verified readback).
- Running kernel: `7.2.0-1.92-cachyos-vcn-bc250`; cmdline ends with `amdgpu.bc250_vcn_mode=1` — operator selected the mode1 (probe) limine entry.

## VCN probe result (hardware-verified runtime journal)

- amdgpu bound at `0000:01:00.0` (1002:13fe). IP blocks detected: 9 (`detected ip block number 0..8`): common, gmc, ih, psp, smu, dm, gfx, sdma, and `number 8 <vcn_v2_0_0> (vcn_v2_0_probe)`. Stock mode0 boot had 8 blocks with no VCN; the +1 is the probe block.
- `[VCN instance 0] Found VCN firmware Version ENC: 1.24 DEC: 8 VEP: 0 Revision: 9`.
- `VCN probe: fw_version=0x08118009 fw_size=404544 vcpu_bo_size=1064960`. fw_size equals `green_sardine_vcn.bin` (404,544 B) staged in /lib/firmware.
- Matches the historical mode1 PASS (2026-08-28: vcn_v2_0_probe block 8, VCN fw ENC 1.24 DEC 8). This is fresh reproduction on the current APCB-only image.
- No ring-test lines appear in this boot journal (historical mode1 log had vcn ring setup + `-110` timeouts). Treat ring exercise as UNRUN for this boot.
- SMU 88.6.0 initialized successfully; display core DCN 2.0.1 up; DP-1 connected. Non-fatal `dal_irq_service` WARN/ERROR lines identical to the 2026-09-11 audit.
- Live telemetry (BC250-METRICS): gfxclk=2000, socclk=1254, uclk=450, fclk=450 MHz; DP connected.

## Evidence class

- `hardware-verified` for: board boots Linux on APCB-only candidate; mode1 VCN probe block attaches; VCN firmware header is discovered and read.
- UNRUN / not claimed: VCN hardware block attach and initialization, ring bring-up, MMIO decode, encode/decode function. These require mode2 (`amdgpu.bc250_vcn_mode=2`).

## Evidence files

- Journal extract: `evidence/runtime/20260912-mode1-probe-boot-journal.txt`, 157 lines, SHA-256 `c165345b0ec05f12f4939a88b6f315b8e97fcac7bf183ef0bd6ef85c99e2004a`.

## Next decisive step

- Operator reboots from local console and selects limine entry `linux-cachyos-vcn-bc250-mode2` (`amdgpu.bc250_vcn_mode=2`, hardware block). Then repeat the read-only SSH audit: expected signal is a real `vcn_v2_0` hardware ip_block line, VCN ring/IRQ init, and absence of firmware-load errors. Failure modes to record: firmware load error, GPU hang/reset, or missing block.
