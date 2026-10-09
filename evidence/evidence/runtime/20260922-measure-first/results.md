# Measure-first results (2026-09-22 ~01:25+05:00, read-only SSH)

Board `cachyos`, up 3:28, load <1. All commands with 10–15 s timeouts; zero
hangs, zero writes.

## Observed

- CPU online: 12 threads (6C/12T as before).
- MCE: single journal line is benign (`In-kernel MCE decoding enabled`);
  no machine-check/hardware-error records.
- SMN[0x5A870] = `0x00000077` (single PCI-CFG window read): physical cores
  3 and 7 masked, 0-2/4-6 active. Matches `bc250-core-unlock` expected
  stock mask exactly (refuses non-0x77 without -f).
- Temps/power (idle-ish): GPU 63C, k10temp 63.6C, NVMe 49.9C; pm_info:
  MCLK 450 / SCLK 2000 / VDDGFX 999mV / VDDNB 1287mV / SoC 77-81W /
  GPU 0% / VCN powered down (mode1 as expected).
- hwmon: nvme, amdgpu, k10temp, nct6686 (fan-control capable Super-I/O).
- Tooling on board: `umr` v1.0.0, python3, cc/gcc all present.
- UMR blocks: cyan_skillfish (df350, mp0/mp1 11.0.8 = SMU, umc811 x2,
  gfx1013 10.1.3, vcn203, clkb/clka clock blocks, ...).
- Driver boot line: `SE 2, SH per SE 2, CU per SH 10, active_cu_number 40`
  (enumerated count; dispatch mask below is the separate question).
- Raw harvest/config: `CC_GC_SHADER_ARRAY_CONFIG = 0xFFE00000`
  (INACTIVE_WGPS[16:31] = 0xFFE0),
  `..._GEN0 = 0x00FC0001` (GEN0_INACTIVE_CU = 0xFC).
- Driver config caps: max_cu_per_sh=10, max_sh_per_se=2 (full die 40CU).

## Not established

Bit-to-WGP mapping of the CC/GEN0 values (naive decodes contradict the
known-stock 24CU dispatch and the enumerated 40; no mapping invented here).
Decisive test: symmetric WGP ladder via live-manager with FPS readback
(zjHu method), optionally cross-checked by SMU active_wgp query.

## Gaps closed / opened

- Closed: SMN mask (0x77), MCE clean, sensor/tool inventory, python3+cc
  present (latency-harness Q), UMR usable with `-i 1`, driver CU line.
- Open: CU dispatch ground truth, VRM temp path, per-core masked-core
  health (needs unlock trial + stress), T0 screen photo (operator).
