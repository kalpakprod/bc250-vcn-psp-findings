# 2026-09-24 — STUB early-slot BOOTS: verdict and knowledge

## Verdict (hardware, live-checked)

- Image on chip: `BC250_vcn-driver-STUB_no-hw-ops_early-slot.bin` (`6500bea5…`).
- Operator cold boot 2026-09-24 ~19:37: board passed init, reached Linux.
- Live check (`scripts/board_liveness.sh` + SSH as `steammachine`, key auth):
  ping UP, booted 19:37:14, uptime 1 min at check, kernel
  `7.2.6-1.206-cachyos-bc250`, host `cachyos`, BIOS P3.00.
- GPU: `lspci` shows `1002:13fe` Cyan Skillfish; `/dev/dri/card1` +
  `renderD128` present; dmesg (via `sudo -n`): SMU fw `88.6.0`, Display Core
  v3.2.384 on DCN 2.0.1, `amdgpu 3.64.0` initialized, fb0 up. No VCN lines
  (expected: the STUB executes zero HW ops).
- SSH note: direct `ssh 127.0.0.1` as `kukuruza` fails; the working path
  is `steammachine@` + `~/.ssh/id_ed25519`, `sudo -n` for `/boot` and dmesg.

## Knowledge gained (what the boot taught)

1. DXE completes with our driver FFS inserted in the FIRST TRUE-pool slot.
   The FV insertion surgery is innocent.
2. Therefore the FULL early-slot hang (2 blinks, no LAN/video) is caused by
   the driver's own code (route-B sequence), not by placement/surgery.
3. The ladder's next variable is dispatch position: FULL-appended is NEXT.
4. STUB-appended branch is now fallback-only (kept staged, not next).
5. Board software baseline for VCN judging: two kernels installed,
   `7.2.6-1.206-cachyos-bc250` (current) and
   `7.2.6-1.3-cachyos-bore-vcn-bc250` with Limine modes 0/1/2
   (`amdgpu.bc250_vcn_mode=0/1/2`); one vmlinuz+initramfs per kernel, modes
   differ by cmdline only. Kernel packages + sources live on the board
   (`~/kernel-1.3`, `~/linux-cachyos-bc250`, `~/vcn-work`, `~/vcn_unlock`).

## Recorded in

- `scripts/gen_versions_registry.py` OVERRIDES + regenerated
  `candidates/VERSIONS.md` (STUB → `FLASHED-OK`, FULL-appended → `NEXT`).
- `candidates/BC250_vcn-driver-STUB_no-hw-ops_early-slot.txt` (verdict lines).
- `memory/project-state.md` (2026-09-24 status section).
- Plane BC250: #7 Done (this verdict), #8 Todo (flash FULL-appended, needs
  operator approval), #9 In Progress (pull board work, publish kernels).
