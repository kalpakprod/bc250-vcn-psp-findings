# Helper wave results — 12 parallel tracks (2026-09-22)

Parent-verified synthesis. Children were repo-read-only, fetch to `/tmp/wf-*/`.
Root-verification (this session, direct): `8_cores_steam.rom` re-hashed
`c99cbca1…50449`, AGESA string `RBNBDK-BL5 46.1.2.211126` at file `0xEB996D`;
live AmdSetup body (2229 B) found byte-identical in `dump/2.bin` at `0x4CF`.

## Verdicts per track

- rom-audit: `8_cores_steam.rom` (16 MiB, `c99cbca1…`) is stock-3.00 lineage:
  MB01-09/MB13-15 identical to `BC250_3.00.bin`, diffs only NVRAM + DXE FV;
  inner FV 182/187 files = 3.00 vs 175 = 5.00 / 174 = CLV. Adds
  `Bc250CoreUnlockDxe` (12288 B, `7d22d802…` = repo-known module: SMN
  0x115A870 read, SMU msg 0x98, warm reset) + AMITSE/Setup/NVRAM/logo
  changes. Lighter `bc250-Steam/bc250.rom` = logo+AMITSE+CbsSetupDxe IFR
  flag only, no unlock driver. Flasher AMI AFU EFI 5.16.01.0109.
  Status: base question CLOSED (3.00, not 5.00). Unresolved: exact AFU
  cmdline, Secure Flash/ROMID behavior, boot proof.
- fd-release: v0.5.0 (`05cca622…`, 2026-08-24): "atop modded v3.00";
  `menu.nsh` flash switches `/P /B /N /K /RLC:E /CLRCFG`; 16 firmware
  images; **menu R3 references missing `BC250_3.00_MeiMeiDXEv3-PUNSH`**
  (flash via R3 would fail). Unresolved: image internals, BOOTX64 dump.
- sw-unlock: `bc250-core-unlock` writes only `0xFF` to SMN `0x5A870` via SMU
  Q3 msg `0x98` (PCI config window, root, stop governor, verify, no-retry
  on timeout). Volatile, warm-reboot survives, cold clears. Unresolved:
  msg presence on operator board (needs live mask read), per-core health.
- async-port: Bazzite RADV `0001` is kernel-free ONLY on OGC kernels;
  bore 7.2.6 needs upstream v33 kernel half (apply-cleanly unknown); Mesa
  26.1.6 vs 26.2.x hunk drift untested; mesh/task stays disabled (GPU hang).
  Portable: fdinfo/journal/hwmon probes + Vulkan tests.
- cc-port: Control Center mechanisms mapped (SMU OC helper+service, Cyan
  TOML governor, CU live-manager+service, NCT fan pwm, zswap paths incl.
  CachyOS path, metrics fix incl. `amdgpu.cs_legacy_8core_metrics=1`).
  CachyOS no-GUI reuse plausible (helpers are GUI-free, Arch scripts exist).
  Unresolved: vendored SMU-opcode blob unaudited, UMR WGP semantics.
- cu-symmetry: repo corroborates mechanism shape (2SE×2SH×5WGP=40CU, stock
  CC `0xFFF80000`=24CU, "shows but adds nothing" precedents, live-manager
  per-SE/SH table as test tool) but symmetry rule stays single-source
  (video); operator harvest unknown (`cu_map.sh` never run).
- fsr4-track: `daniel-h-0/bc250-fsr4-fork` (FSR 4.1.1 INT8 DLL) + OptiScaler
  Client route; author numbers recorded; reversible per-game trial fits
  stock driver + GE-Proton (11-6 tested vs operator 11-3). Unresolved:
  gamescope/MangoHud interaction, slot exposure per owned game.
- cooling-fit: JF13K recipe plausible (265W top-down, 92mm height) but
  operator heatsink/fan/RPM/VRM-sensor/clearance all unknown; printables
  BOM not fetched. Measure-first before parts.
- p300-live-join: live = stock-Auto confirmed; stock IFR marks UclkDiv1M0
  (0x229) and DF value (0x37E) HIDDEN (SUPPRESS_IF) while CLV lists them
  editable → **T2/T6 likely UNREACHABLE on P3.00**; DF-visibility doc
  conflict must be arbitrated by live T0 photo. T1 revert risk stands.
- nvram-safety: procedure hardened (efivar readback commands, CMOS
  jumper-or-battery 20–30s, programmer escalation with pinned flashrom).
  Gaps: P3.00 CMOS jumper unphotographed, no current full-SPI recovery
  image, no Setup-efivar live path, no independent clock counters.
- latency-harness: no-install path exists (`measure_bc250_perf.py` stdlib,
  amdgpu_top, gpu_metrics, pp_dpm deltas); python3/cc presence on board
  unchecked; W4 workload scene unrecorded; no run authorized yet.
- w10-lineage: W10 cpuinfo = 8 cores / DMI P5.00, but **flash-to-log join
  has no transcript/manifest**; W11 boot unverified (empty dir); unlock
  causality (B6250780?) unproven. No CLV + working-unlock image exists
  (af531026 P0-fail, drivers-only 0968a70c unflashed).

## Action order (parent synthesis)

1. Measure-first on live board: SMN 0x5A870 mask, active_wgp, `cu_map.sh`
   harvest, per-core mprime/MCE, sensor inventory (one SSH pass).
2. T0 screen photo to arbitrate hidden controls (UclkDiv/DFval).
3. Software 8-core unlock trial (volatile, CMOS-safe) before any flash talk.
4. Cooling/governor + CU symmetric stepping (24→28→32→36) via live-manager.
5. Async-port: v33 kernel-hunk dry-apply vs bore sources + Mesa 0001 dry-apply.
6. FSR4 per-game reversible trial (DLL route, owned game with upscaler slot).
7. Flash LAST: only with fresh full-SPI recovery + exact approval; PUNSH gap
   blocks FD-menu R3 path as-is.
