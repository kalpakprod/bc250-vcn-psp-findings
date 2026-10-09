# Live-system check battery (2026-09-13T00:29-00:35+05:00, D10R/mode1)

Goal driver: session goal `выполни все проверки которые можешь выполнить
в рабочей системе`. All checks below are read-only or previously
proven-safe; SMU mailbox stayed alive throughout (verified before/after
each SMU step). Transports: SSH + `sudo -n` file reads + `Bc250Smu`
query messages only.

## A. Host / driver / firmware (board)

- A1 boot identity: PASS. uptime 18 min (same D20-verified boot), kernel
  `7.2.0-1.92-cachyos-vcn-bc250`, cmdline `amdgpu.bc250_vcn_mode=1`,
  param `/sys/module/amdgpu/parameters/bc250_vcn_mode` = `1`.
- A2 PCI/GPU: PASS. `01:00.0 VGA [1002:13fe] Cyan Skillfish [BC-250]`;
  `card1`, `card1-DP-1/2`, `renderD128` present; amdgpu IP blocks 0-7
  (common/gmc/ih/psp/smu/dce/gfx/sdma) + block 8 `vcn_v2_0_0
  (vcn_v2_0_probe)`; MMIO base `0xFE800000` size 512K.
- A3 VCN firmware: PASS. `[VCN instance 0] Found VCN firmware Version
  ENC: 1.24 DEC: 8 VEP: 0 Revision: 9` (green_sardine loads in probe).
- A4 SMU driver handshake: PASS. `smu driver if version = 0x8, smu fw if
  version = 0x8, smu fw version = 0x00580600 (88.6.0)`, `SMU is
  initialized successfully!` — second independent route confirming the
  Q0-1 version read (`0x580600`).
- A5 probe WARN triage: PASS (explained, non-blocking). Two WARNs in
  display HPD/IRQ init (`dal_irq_service_dummy_ack: called for
  non-implemented irq source, src_id=0, ext_id=0`, irq_service.c:169,
  and :129 during `dm_hw_init`). Display path only; DP outputs present;
  unrelated to VCN/SMU. Taint `[W]` expected from it.
- A6 KFD/GPU node: PASS. `/dev/kfd` exists; kfd 1 node; `Topology: Add
  GPU node [0x1002:0x13fe]` (virtual CRAT). GPU compute exposed; only
  VCN is probe-held. Firmware-CRAT flag encoding closed as MOOT (driver
  builds virtual CRAT; 1 web search found no kfd reference — G6, not
  pursued).

## B. SMU read-only

- B1 alive: PASS (`true` before and after every step this session).
- B2 Q0 versions (re-run): PASS. `0x02 -> 0x580600`, `0x03 -> 0x8`
  (stable across runs).
- B3 Q0 queries (first-ever): PASS, all answered, no wedge.
  `gfxclk(0x0F)=0x7D0`, `gfx_freq(0x37)=0x7D0` (2000 MHz, two routes
  agree), `active_wgp(0x1E)=0xC` (12), `core_pstate0(0x0C)=0x6`,
  `df_pstate(0x13): st=1 ret=0x3`.
- B4 domain statuses (`domain_status2.py`, statuses-only): PASS.
  dom6 `0x0` (gated, expected), dom7 `0x0`, dom14 `0x41`, dom15 `0x0`,
  dom17 `0x80000002` (bit31 marker present again). alive_after=true.

## C. Offline chain (host)

- C1 D20 evidence re-verify: PASS. `postwrite-d10r.bin` = `addef288...`
  OK; `prewrite-d19.bin` = `67f6ede7...` OK (`sha256sum -c`).
- C2 MCP sessions: PASS. 8001/8002/8003/8004 all answer `cutter_health`.

## D. VCN function

- UNRUN (by design): needs domain enable + bridge; no MMIO-before-enable
  attempted (Aug-29 wedge rule holds).

## E. Gated (NOT run; each needs explicit per-run approval)

- Q0-2 table READ (`0x04/0x05` + `0x06` into DMA buffer) — design ready
  to draft; nonzero DMA-target risk.
- Q0-3 staged-table write (`0x07`) + `0x5C` fire — new state change.
- Slave-SMU IPC `0xfe` — decoded, never tried.
- DF-space SMN reads — PROHIBITED (S2-A wedge class), not proposed.
- Flash writes — moratorium holds.

## Slave-IPC recon (read-only file reads, no mailbox contact)

- Board healthy (up 20 min, same D20 boot).
- Q4 mixin mapped: alias of Q3 table (`0x04-0x11`, `0x27`), never tried.
  Q1 mixin: mostly unexamined (`0x08`, `0x10`, `0x68-secure`).
- CORRECTION to the track premise: there is NO decoded host->slave
  message. `0xFE` appears as (a) the RETURN STATUS of stub handlers Q3
  `0x47`/`0x48` (`q3_0x47_return_status_0xfe`, 5-line wrappers), and (b)
  the fw-internal master->slave IPC number from the `0x233e8` RE
  (`0x5afff..` via `0x1b514`). The Q3 handler table covers `0x01..0xC0`
  only. The slave core is reachable, if at all, via master forward
  (`0x5afff`-range SMN — DF-space class, gated, NOT attempted).
- Consequence: the slave track is redefined as (i) Q4-alias read-only
  queries (same risk class as Q0-1, needs approval), then (ii) a designed
  `0x5afff`-range probe (separate design + approval, DF hazard noted).

## Live-vs-donor IP-discovery diff (new check, observed)

- Fetched live `amdgpu_discovery` blob (10240 B, sha
  `698d22a6...`) via read-only debugfs+base64; compared against corpus
  donor `discovery_robin.bin` (same size).
- VCN entry (bases `0x7800/0x7E00/0x02403000` at file `0x318/0x31C/0x320`)
  byte-identical; HARV table (`@0x3C4`) empty in both.
- ALL bytes `0x000-0x44F` (header + full IP table + VCN + HARV) are
  IDENTICAL between live BC-250 (D10R/mode1) and the Robin donor.
  2615 differing bytes live only in `0x450+` high-entropy tail
  (uninterpreted — not parsed, not claimed).
- Conclusion (static-analysis, corroborated): the VCN descriptor is
  stock-healthy on this board; the delta vs a working VCN system is NOT
  in discovery/harvest. Consistent with the driver skip (`2.0.3`) +
  power/isolation layers. This check never existed before.

## Methods/notes

- Exact working assess form: `cd ~/vcn_unlock && sudo -n env
  PYTHONPATH=$HOME/vcn_unlock/bc250-smu-unlock timeout N python3 <script>`.
- `domain_status2.py` header documents the 0x10FFExx read-wedge class;
  statuses-only v2 used — no cmd reads, no writes, no fw messages.
- One web search (CRAT flags) returned no reference; resolved locally
  instead via driver behavior (virtual CRAT). URL list: none retained.

## 2026-09-12 ~00:40 UTC+6 — PP/DPM + firmware_info + error scan (read-only SSH)
- `pp_dpm_sclk`: 1000/1500/**2000 MHz active** — matches Q0-1 gfxclk 0x7D0=2000 (route 3). `pp_dpm_mclk`: 450. `power_dpm_state=performance`, level=auto.
- `amdgpu_firmware_info`: **VCN feature 0, firmware version 0x08118009** (non-zero — driver attempted/recorded a VCN FW load despite HARVEST empty list); UVD 0/0 (expected, no UVD block).
- `journalctl -k -b0 -p err`: ONLY RDSEED-unreliable lines; zero amdgpu error lines.
- No vcn/uvd/jpeg/decode/encode entries in card1/device sysfs. Board uptime 23 min. No writes; approval-gated items still pending.

## 2026-09-12 ~00:50 UTC+6 — driver boot sequence + VCN probe lines (read-only SSH)
- Kernel `7.2.0-1.92-cachyos-vcn-bc250`, cmdline carries `amdgpu.bc250_vcn_mode=1` (mode1 path confirmed from live boot).
- amdgpu probe: CYAN_SKILLFISH 0x1002:0x13FE, MMIO base 0xFE800000 size 512K; IP blocks incl `psp_v11_0_8`, `smu_v11_0_0`, and **`vcn_v2_0_0 (vcn_v2_0_probe)` as block 8**.
- `[VCN instance 0] Found VCN firmware Version ENC: 1.24 DEC: 8 VEP: 0 Revision: 9` — matches firmware_info 0x08118009 (DEC 8 / rev 9). Driver located a VCN FW for instance 0 despite HARVEST empty discovery.
- `smu driver if 0x8 == smu fw if 0x8, program 0, version 0x00580600 (88.6.0)` — matches Q0-1 0x580600 (route 4).
- Only amdgpu error: `*ERROR* Failed to clear hpd(rx) source=3 on init` (display-side) + 2 dal_irq WARNs. No VCN/SMU/PSP errors.
- hwmon0 path absent under card1/device (sensors via different hwmon index; not pursued — display/health side detail).
- No writes. vcn-smu-probing skill loaded in preparation for gated Q0-2/Q4/Q1 checks.

## 2026-09-12 ~01:00 UTC+6 — full firmware table + live mode param + memory (read-only SSH)
- Full `amdgpu_firmware_info`: ME/PFP/CE/MEC feat 32, SDMA0/1 feat 50, **SMC prog 0 fw 0x00580600 (88.6.0)** = route 5 for Q0-1, VCN 0/0x08118009, VCE/UVD/MC zero. **SOS/ASD/TA-* all zero** — PSP secure-OS/TA firmwares not reported loaded under mode1 (consistent with skipped PSP TA path; PSP v11.0.8 IP itself probed OK per dmesg).
- `/sys/module/amdgpu/parameters/bc250_vcn_mode` = **1** live.
- VRAM 6442450944 total / 479997952 used; GTT 4294967296. hwmon index is hwmon1: temp 58C, power ~80.1W, sclk 2.0GHz (route 6 for gfxclk).
- No writes. Read-only surface on the working system is now exhausted except hwmon1 sensors + gated Q0-2/Q4/Q1.

## 2026-09-12 ~01:10 UTC+6 — goal marked BLOCKED (awaiting operator approval)
- Read-only surface exhausted: SMU Q0-1/discovery/PCIE/TOS/versions, PP/DPM, firmware_info, driver seq, VFCT, error scans, VRAM/GTT, sensors — all captured, no writes made.
- Remaining 3%: Q0-2 DMA READ 0x04/0x05+0x06 and Q4/Q1 read-only queries — require explicit bundled approval (no volatile runtime without per-run approval per standing constraint). Same gate repeated 6 consecutive goal turns with no operator answer.
- Unblock action: operator approves the bundled probe batch; vcn-smu-probing skill already loaded for execution.
