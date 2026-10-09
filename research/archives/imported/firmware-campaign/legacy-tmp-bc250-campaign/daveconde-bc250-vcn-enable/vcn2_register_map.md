# VCN 2.0 register address table (BC250 / VCN 2.0.3)

Source: `drivers/gpu/drm/amd/include/asic_reg/vcn/vcn_2_0_0_offset.h` (VCN 2.0.x;
re-verified 2026-08-25 against the kernel tree in `linux/` — all **467**
registers cross-checked: offset, BASE_IDX, and computed MMIO byte address
below are header-exact; `--direct-load`'s 53 R_* constants and every bit mask
were verified the same way, as were the doorbell/C2PMSG/GB_ADDR_CONFIG/
BIF_MMSCH0 spellings and the whole `vcn_v2_0_start`/`mc_resume`/ring-test/stop
sequence it replays).

**MMIO byte address** (the `amdgpu_regs`/BAR5 register-file route; formula from
`RREG32_SOC15(VCN, inst, reg)` in `soc15_common.h`) — this is what the table's
"MM byte addr" column holds:

    MM dword = base_address[reg_BASE_IDX] + mmREG
    MM byte  = MM dword * 4
    e.g. UVD_POWER_STATUS (0x0004, base_idx 1) -> MMIO 0x1F810

CPU reads of the VCN segment HANG the board while the island is dead (July,
measured via userspace BAR5, UMR, and kernel debugfs). **MEASURED 2026-08-25
(post-clock-work: slots programmed + enables ON + gates released): all-ones
and NO hang** — `--direct-load`'s 11-register segment ladder (both segments,
incl. the static `UVD_VERSION` constant at MMIO `0x20F24`) read uniform
`0xffffffff`: the whole register file is clamped at the root while the SMU
dom6 sequencer reports the domain UP. The July hang was a pre-clock-work
behavior; all-ones is the closed-island behavior when clocks run. Ladder
spellings (all kernel-exact): PGFSM_CONFIG `0x1F800`, PGFSM_STATUS `0x1F804`,
POWER_STATUS `0x1F810`, HARVESTING `0x1F81C`, JPEG_POWER_STATUS `0x1F828`,
MASTINT_EN `0x20000`, UVD_STATUS `0x201BC`, **UVD_VERSION `0x20F24`** (the
liveness key — a static constant that only decodes if the file's periphery
is powered), NO_OP `0x20EFC` (SEG1); JPEG_CNTL `0x1E200`, JRBC_STATUS
`0x1E424` (SEG0).

**MMIO offsets are NOT SMN addresses** (kernel-verified counter-example, model
v3): every IP's registers exist at SEVERAL spellings whose numerics are
unrelated. The kernel talks to this card's MP1 (SMU) at MMIO 0x058A08 =
(MP1_BASE__INST0_SEG0 0x16000 + mmMP1_SMN_C2PMSG_66 0x282 dwords) x 4 — while
the same PMFW's mailbox queues live at SMN 0x03B10A20 (the bc250-smu-unlock
library's transport, hardware-proven). Same block, two unrelated frames. In
each IP's discovery `base_address[]` list only the SMALL values (<= 0x10400
dwords) are MMIO spellings.

**SMN fabric frame `0x024xxxxx`** (model v3, 2026-08-25): the discovery
`base_address[2] = 0x02403000` entry is REAL — identical to renoir's
`UVD0_BASE__INST0_SEG2` in the kernel's `renoir_ip_offset.h` (navi12/navi14
carry the same SEG2 too) — but:

- **No VCN 2.0 register uses BASE_IDX 2** (checked: all 467 entries in
  `vcn_2_0_0_offset.h` are BASE_IDX 0 or 1). The kernel derives no address
  from SEG2 on ANY ASIC — the value exists in the tables because the hardware
  maps a window there, not because any driver register needs it.
- **The frame holds a small per-IP slice for (nearly) every IP** (full
  ROM-verified map below) — typically 1-2 KB. GC's slice (0x02402C00, 1 KB)
  cannot hold GC's ~35 KB MMIO register file, so the slices are NOT
  register-file mirrors. Slice contents are UNKNOWN for every IP, VCN
  included.
- **The 16 MB BIOS ROM contains no register writes into the frame**: a full
  scan for little-endian dwords in 0x02400000-0x0243FFFF finds 80 hits — all
  either inside the discovery table itself (0x981A9C-0x981D60) or coincidental
  byte patterns in code/data. The earlier "the BIOS GNB table programs THM/CLK
  config through their slices" claim is RETRACTED.
- The old morning formula "`SMN = 0x02403000 + mmREG*4`" remains unsupported:
  it would place mmUVD_POWER_STATUS at the 5th dword of the slice — a guess,
  not a mapping (and it placed its "GC anchor" 0x02407B78 inside VCN's
  slice). `--vcn-power-regs` dumps the slice and lets the values speak.

**SMU SRAM access contract** (source-verified 2026-08-25,
`bc250_smu/primitives.py`): `smu_read(addr, n)` reads **at most 18 words**
per call (the library's own `window_read`/`dump_sram` chunk at 18);
`smu_write32` writes one word. The first `--msg-table` run violated the cap
(32-word chunks) and received 0x80-periodic session residue — every bulk
read in this repo now chunks at ≤ 18. The same file documents the library's
~60 live Q3 message ids (api_q3.py) — incl. msgs 0x28-0x2C (the secure
cluster this tool rides) and 0x3C/0x3D (enable/disable SMU features,
bitmask — renoir's PowerUpVcn is feature-gated the same way).

**Q3 handler table (SRAM 0x746C, stride 8 — dumped 2026-08-25, premise
validated: 147 handlers):** entry = {handler_ptr, flags_dword}. Flags:
`0x6` = normal, `0x201` = gated secure cluster (msgs 0x27–0x2F; bit 0x200 =
needs the unlock), `0x206` = a SECOND gated group (msgs 0x71/0x72/0xA7/0xA8
— undocumented, accessible post-unlock). Undocumented secure siblings
0x27/0x2D/0x2E/0x2F sit interleaved with the mem64-window family (handlers
0x27C94–0x27E18) — likely more window primitives. The #1 power-message
suspect is **msg 0x21 → handler 0x249DC** (0x319 bytes past the fw's dom7
power-up caller 0x246C3, in the power-code band 0x23370–0x246C3); msg 0x8F
→ 0x2326C and 0xAE → 0x2522C are adjacent to the band. Note: the kernel
MP1 C2PMSG mailbox (PPSMC numbering) and the PMFW Q3 queues are different
message spaces — the kernel list's lack of a VCN message never constrained
Q3.

**SMU windows** (the fw's own register access, decoded from FUN_000235c8): the
fw masks every target to 20 bits and accesses it at SMU-local
0x01100000 + (target & 0xFFFFF). **RESOLVED 2026-08-25 (route P step 0, on
hardware): the window maps to the SMN LOW frame — fw-window offset X == SMN
0x000X.** Evidence: the dom6 sequencer's four registers (cmd/rail/status/ctrl
at window offsets 0x6D1xx) match live at SMN 0x0006D1xx (status=0x01010101,
ctrl=0x02 — distinctive) while the NBIO spellings 0x0116D1xx read dead-zero.
The core mask read 0x77 at BOTH spellings (0x0115A870 / 0x0005A870) —
ambiguous on its own (alias or coincidence). The mask still makes the window
structurally unable to express 0x024xxxxx, and it cannot reach the PMFW
mailbox frame 0x03B1xxxx either (measured stall, 2026-08-20). The 2026-08-24
"0x02403010 fast 0" mem64 read was the masked alias → SMN 0x00003010 → dead →
zero (dead reads return 0x00000000 on this box — measured). The 0x1F8xx arg
family (→ SMN 0x0001F8xx) is the documented hard wedge.

**PCI-config SMN window** (root `00:00.0`, config `0xB8/0xBC`) — the library's
transport (`Bc250PciTransport.read_smu_reg` / `write_smu_reg(reg, value)`,
both source-verified), proven live at SMN 0x03B10A20 (every mailbox send).
Full 32-bit SMN addressing, no masking. **MEASURED 2026-08-25:** dead reads
return clean 0x00000000 on this box (THM/GC slice anchors, 0x0116D1xx) — not
the 0xffffffff July #5 suggested; the 0x024 frame reads dead-zero even on
live IPs (THM, GC), so the fabric-slice probe carries no information here.
**MEASURED 2026-08-25 — read/write asymmetry on the dom6 block (SMN
0x0006D1xx):** config READS are live (all four sequencer values match the
fw-window reads; the slot 0x17 clock/enable registers — changed post-boot —
read identically through both paths), but config WRITES to the sequencer
(ctrl 0x0006D0F8, cmd 0x0006D17C, rail 0x0006D184) are IGNORED: a
correctly-issued ctrl 0x02→0x00 store read back 0x02 immediately, with no
side effects on cmd/rail/status. The block is fabric-READABLE but
host-fabric-write-protected. The fw-window debug-write path (SMU-executed,
msgs 0x28/0x29 over the same transport) provably lands on this whole block:
the engage's slot enable 0→1 persisted across processes, and MEASURED
2026-08-25 the sequencer ctrl store LANDED too (0x02→0x00, re-read 0x00 by a
later process; night-1's "sat dirty" evidence was vacuous — the old
bit0-only clear wrote 0x02 over 0x02). The cmd/rail stores in the same run
are landed-by-inference with vacuous read-backs (one-shot/self-clear
semantics; favored reading: taken on an already-up rail). A cold boot
restores the factory ctrl=0x02. The dom6 sequencer registers
(config-readable) and the VCN MMIO read are the power-state arbiters.

Discovery `base_address[]` for VCN instance 0 (dwords), ROM-verified 2026-08-24
(BC250_3.00_CHIPSETMENU.ROM @0x981d10, die-0 record 34; identical to renoir's
UVD0_BASE):
    [0] = 0x00007800   (0x0001E000 bytes)
    [1] = 0x00007E00   (0x0001F800 bytes)  <- uvd0 power/PG/harvest cluster
    [2] = 0x02403000   (SMN fabric slice base; slice is <= 2 KB, contents unknown)

Verified against enable_vcn.py: UVD_PGFSM_CONFIG 0x1F800, UVD_PGFSM_STATUS 0x1F804,
UVD_POWER_STATUS 0x1F810, CC_UVD_HARVESTING 0x1F81C.

## The 0x024 fabric frame — full ROM-verified slice map

Parsed from the IP_DISCOVERY die-0 records (38 IPs, 2026-08-25). "max size" is
bounded by the next slice above (1 KB allocation granularity); it is an upper
bound, not a measured size. hw_id names follow `soc15_hw_ip.h`. Useful for
reading `--vcn-power-regs` dumps: what neighbors to expect around each probe.

| slice base | hw_id | IP | version | MMIO SEG0 (dwords) | other bases | max size |
|------------|-------|-----|---------|--------------------|-------------|----------|
| 0x02400C00 | 3 | THM | 11.0.1 | 0x16600 | - | 1 KB |
| 0x02401000 | 4 | SMUIO | 11.0.8 | 0x16800, 0x16A00 | 0x00440000 | 1 KB |
| 0x02401400 | 5 | FUSE | 11.0.1 | 0x17400 | - | 1 KB |
| 0x02401800 | 6 | CLKA inst0 | 11.0.1 | 0x16C00 | - | 1 KB |
| 0x02401C00 | 6 | CLKA inst1 | 11.0.1 | 0x16E00 | - | 1 KB |
| 0x02402000 | 6 | CLKA inst2 | 11.0.1 | 0x17000 | - | 12 KB |
| 0x02402C00 | 11 | **GC** | 10.1.3 | 0x1260, 0xA000 | - | 1 KB |
| 0x02403000 | 12 | **VCN** | 2.0.3 | 0x7800, 0x7E00 | - | 2 KB |
| 0x02403800 | 14 | ACP | 4.0.0 | 0x480000 | - | 1 KB |
| 0x02403C00 | 271 | DMU | 2.0.3 | 0x12, 0xC0, 0x34C0, 0x9000 | - | 1 KB |
| 0x02404000 | 272 | DIO | 127.127.63 | - | - | 2 KB |
| 0x02404800 | 274 | DAZ | 127.127.63 | 0x4C0000 | - | 24 KB |
| 0x02406000 | 24 | IOHC | 0.0.0 | 0x10000 | 0x04EC0000 | 4 KB |
| 0x02407000 | 28 | L2IMU | 0.0.0 | 0x7DC0 | 0x900000, 0x4FC0000, 0x55C0000 | 6 KB |
| 0x02408800 | 34 | **MMHUB** | 2.0.3 | 0x1A000 | - | 1 KB |
| 0x02408C00 | 35 | ATHUB | 2.0.3 | 0xC00 | - | 2 KB |
| 0x02409400 | 37 | DFX | 2.0.0 | 0x580 | - | 3 KB |
| 0x0240A000 | 40 | OSSSYS | 5.0.1 | 0x10A0 | - | 1 KB |
| 0x0240A400 | 41 | HDP | 5.0.1 | 0xF20 | - | 5 KB |
| 0x0240B800 | 46 | DF | 3.5.0 | 0x7000 | - | 1 KB |
| 0x0240BC00 | 47 | CLKB | 11.0.1 | 0x17E00 | - | 2 KB |
| 0x0240C400 | 49 | DFX_DAP | 2.0.0 | 0x5A0 | 0xB80000 | 19 KB |
| 0x02411000 | 0 | (unmapped hw_id 0) | 11.0.1 | 0x1B800 | 0x1440000, 0x1480000, 0x14C0000 | 1 KB |
| 0x02411400 | 0 | (unmapped hw_id 0) inst1 | 11.0.1 | 0x1BA00 | 0x1500000, 0x1540000, 0x1580000 | 1 KB |
| 0x02411800 | 70 | SDMA2 | 4.2.0 | - | 0x04440000 | 2 KB |
| 0x02414000 | 80 | SDMA3 | 3.6.0 | - | 0x04680000 | 28 KB |
| 0x0241B000 | 108 | **NBIF/NBIO** | 2.1.1 | 0x0, 0x14, 0xD20, 0x10400 | 0x04040000 | 20 KB |
| 0x02420000 | 128 | OSSSYS2 | 2.1.0 | 0xEA0 | 0x500000 | 22 KB |
| 0x02425800 | 150 | UMC inst0 | 8.1.1 | 0x14000 | - | 1 KB |
| 0x02425C00 | 150 | UMC inst1 | 8.1.1 | 0x54000 | - | 1 KB |
| 0x0242A800 | 170 | PCIE inst0 | 4.5.0 | - | 0x05B00000 | 1 KB |
| 0x0242AC00 | 170 | PCIE inst1 | 4.5.0 | - | 0x05B80000 | 1 KB |
| 0x0243FC00 | 255 / 1 | **MP0 / MP1** | 11.0.8 | 0x16000 (shared) | 0xDC0000, 0xE00000, 0xE40000 | 1 KB |

Notes:
- The two MP0/MP1 records carry IDENTICAL base lists in the ROM (the kernel's
  renoir table gives MP1 a different SEG1 = 0x02400400 — the ROM is this
  card's truth). The kernel's `cyan_skillfish_ip_offset.h` lists only 4 of
  the NBIF record's 6 bases (it drops 0x0241B000 and 0x04040000) — the
  kernel's static tables are pruned copies of the discovery data, another
  reason a SEG value's absence there means nothing.
- DBGU_NBIO (hw_id 36) and DBGU_IO (hw_id 45) are the only IPs with NO 0x024
  slice.
- The kernel's MP1 SMU-messaging path on this card class is
  `SOC15_REG_OFFSET(MP1, 0, mmMP1_SMN_C2PMSG_66)` — the MMIO spelling at
  0x058A08 — a THIRD mailbox view besides the PMFW's 0x03B10xxx queues.

| register | off | base_idx | MM byte addr |
|----------|-----|----------|--------------|
| mmUVD_JPEG_CNTL | 0x0080 | 0 | 0x1e200 |
| mmUVD_JPEG_RB_BASE | 0x0081 | 0 | 0x1e204 |
| mmUVD_JPEG_RB_WPTR | 0x0082 | 0 | 0x1e208 |
| mmUVD_JPEG_RB_RPTR | 0x0083 | 0 | 0x1e20c |
| mmUVD_JPEG_RB_SIZE | 0x0084 | 0 | 0x1e210 |
| mmUVD_JPEG_DEC_SCRATCH0 | 0x0089 | 0 | 0x1e224 |
| mmUVD_JPEG_INT_EN | 0x008a | 0 | 0x1e228 |
| mmUVD_JPEG_INT_STAT | 0x008b | 0 | 0x1e22c |
| mmUVD_JPEG_PITCH | 0x009f | 0 | 0x1e27c |
| mmUVD_JPEG_UV_PITCH | 0x00a0 | 0 | 0x1e280 |
| mmJPEG_DEC_Y_GFX8_TILING_SURFACE | 0x00a1 | 0 | 0x1e284 |
| mmJPEG_DEC_UV_GFX8_TILING_SURFACE | 0x00a2 | 0 | 0x1e288 |
| mmJPEG_DEC_GFX8_ADDR_CONFIG | 0x00a3 | 0 | 0x1e28c |
| mmJPEG_DEC_Y_GFX10_TILING_SURFACE | 0x00a4 | 0 | 0x1e290 |
| mmJPEG_DEC_UV_GFX10_TILING_SURFACE | 0x00a5 | 0 | 0x1e294 |
| mmJPEG_DEC_GFX10_ADDR_CONFIG | 0x00a6 | 0 | 0x1e298 |
| mmJPEG_DEC_ADDR_MODE | 0x00a7 | 0 | 0x1e29c |
| mmUVD_JPEG_GPCOM_CMD | 0x00a9 | 0 | 0x1e2a4 |
| mmUVD_JPEG_GPCOM_DATA0 | 0x00aa | 0 | 0x1e2a8 |
| mmUVD_JPEG_GPCOM_DATA1 | 0x00ab | 0 | 0x1e2ac |
| mmUVD_JPEG_SCRATCH1 | 0x00ae | 0 | 0x1e2b8 |
| mmUVD_JPEG_DEC_SOFT_RST | 0x00af | 0 | 0x1e2bc |
| mmUVD_JPEG_ENC_INT_EN | 0x00c1 | 0 | 0x1e304 |
| mmUVD_JPEG_ENC_INT_STATUS | 0x00c2 | 0 | 0x1e308 |
| mmUVD_JPEG_ENC_ENGINE_CNTL | 0x00c5 | 0 | 0x1e314 |
| mmUVD_JPEG_ENC_SCRATCH1 | 0x00ce | 0 | 0x1e338 |
| mmUVD_JPEG_ENC_STATUS | 0x00e5 | 0 | 0x1e394 |
| mmUVD_JPEG_ENC_PITCH | 0x00e6 | 0 | 0x1e398 |
| mmUVD_JPEG_ENC_LUMA_BASE | 0x00e7 | 0 | 0x1e39c |
| mmUVD_JPEG_ENC_CHROMAU_BASE | 0x00e8 | 0 | 0x1e3a0 |
| mmUVD_JPEG_ENC_CHROMAV_BASE | 0x00e9 | 0 | 0x1e3a4 |
| mmJPEG_ENC_Y_GFX10_TILING_SURFACE | 0x00ea | 0 | 0x1e3a8 |
| mmJPEG_ENC_UV_GFX10_TILING_SURFACE | 0x00eb | 0 | 0x1e3ac |
| mmJPEG_ENC_GFX10_ADDR_CONFIG | 0x00ec | 0 | 0x1e3b0 |
| mmJPEG_ENC_ADDR_MODE | 0x00ed | 0 | 0x1e3b4 |
| mmUVD_JPEG_ENC_GPCOM_CMD | 0x00ee | 0 | 0x1e3b8 |
| mmUVD_JPEG_ENC_GPCOM_DATA0 | 0x00ef | 0 | 0x1e3bc |
| mmUVD_JPEG_ENC_GPCOM_DATA1 | 0x00f0 | 0 | 0x1e3c0 |
| mmUVD_JPEG_ENC_CGC_CNTL | 0x00f5 | 0 | 0x1e3d4 |
| mmUVD_JPEG_ENC_SCRATCH0 | 0x00f6 | 0 | 0x1e3d8 |
| mmUVD_JPEG_ENC_SOFT_RST | 0x00f7 | 0 | 0x1e3dc |
| mmUVD_JRBC_RB_WPTR | 0x0100 | 0 | 0x1e400 |
| mmUVD_JRBC_RB_CNTL | 0x0101 | 0 | 0x1e404 |
| mmUVD_JRBC_IB_SIZE | 0x0102 | 0 | 0x1e408 |
| mmUVD_JRBC_URGENT_CNTL | 0x0103 | 0 | 0x1e40c |
| mmUVD_JRBC_RB_REF_DATA | 0x0104 | 0 | 0x1e410 |
| mmUVD_JRBC_RB_COND_RD_TIMER | 0x0105 | 0 | 0x1e414 |
| mmUVD_JRBC_SOFT_RESET | 0x0108 | 0 | 0x1e420 |
| mmUVD_JRBC_STATUS | 0x0109 | 0 | 0x1e424 |
| mmUVD_JRBC_RB_RPTR | 0x010a | 0 | 0x1e428 |
| mmUVD_JRBC_RB_BUF_STATUS | 0x010b | 0 | 0x1e42c |
| mmUVD_JRBC_IB_BUF_STATUS | 0x010c | 0 | 0x1e430 |
| mmUVD_JRBC_IB_SIZE_UPDATE | 0x010d | 0 | 0x1e434 |
| mmUVD_JRBC_IB_COND_RD_TIMER | 0x010e | 0 | 0x1e438 |
| mmUVD_JRBC_IB_REF_DATA | 0x010f | 0 | 0x1e43c |
| mmUVD_JPEG_PREEMPT_CMD | 0x0110 | 0 | 0x1e440 |
| mmUVD_JPEG_PREEMPT_FENCE_DATA0 | 0x0111 | 0 | 0x1e444 |
| mmUVD_JPEG_PREEMPT_FENCE_DATA1 | 0x0112 | 0 | 0x1e448 |
| mmUVD_JRBC_RB_SIZE | 0x0113 | 0 | 0x1e44c |
| mmUVD_JRBC_SCRATCH0 | 0x0114 | 0 | 0x1e450 |
| mmUVD_JRBC_ENC_RB_WPTR | 0x0120 | 0 | 0x1e480 |
| mmUVD_JRBC_ENC_RB_CNTL | 0x0121 | 0 | 0x1e484 |
| mmUVD_JRBC_ENC_IB_SIZE | 0x0122 | 0 | 0x1e488 |
| mmUVD_JRBC_ENC_URGENT_CNTL | 0x0123 | 0 | 0x1e48c |
| mmUVD_JRBC_ENC_RB_REF_DATA | 0x0124 | 0 | 0x1e490 |
| mmUVD_JRBC_ENC_RB_COND_RD_TIMER | 0x0125 | 0 | 0x1e494 |
| mmUVD_JRBC_ENC_SOFT_RESET | 0x0128 | 0 | 0x1e4a0 |
| mmUVD_JRBC_ENC_STATUS | 0x0129 | 0 | 0x1e4a4 |
| mmUVD_JRBC_ENC_RB_RPTR | 0x012a | 0 | 0x1e4a8 |
| mmUVD_JRBC_ENC_RB_BUF_STATUS | 0x012b | 0 | 0x1e4ac |
| mmUVD_JRBC_ENC_IB_BUF_STATUS | 0x012c | 0 | 0x1e4b0 |
| mmUVD_JRBC_ENC_IB_SIZE_UPDATE | 0x012d | 0 | 0x1e4b4 |
| mmUVD_JRBC_ENC_IB_COND_RD_TIMER | 0x012e | 0 | 0x1e4b8 |
| mmUVD_JRBC_ENC_IB_REF_DATA | 0x012f | 0 | 0x1e4bc |
| mmUVD_JPEG_ENC_PREEMPT_CMD | 0x0130 | 0 | 0x1e4c0 |
| mmUVD_JPEG_ENC_PREEMPT_FENCE_DATA0 | 0x0131 | 0 | 0x1e4c4 |
| mmUVD_JPEG_ENC_PREEMPT_FENCE_DATA1 | 0x0132 | 0 | 0x1e4c8 |
| mmUVD_JRBC_ENC_RB_SIZE | 0x0133 | 0 | 0x1e4cc |
| mmUVD_JRBC_ENC_SCRATCH0 | 0x0134 | 0 | 0x1e4d0 |
| mmUVD_JMI_CTRL | 0x0145 | 0 | 0x1e514 |
| mmUVD_LMI_JRBC_CTRL | 0x0146 | 0 | 0x1e518 |
| mmUVD_LMI_JPEG_CTRL | 0x0147 | 0 | 0x1e51c |
| mmUVD_JMI_EJRBC_CTRL | 0x0148 | 0 | 0x1e520 |
| mmUVD_LMI_EJPEG_CTRL | 0x0149 | 0 | 0x1e524 |
| mmUVD_LMI_JRBC_IB_VMID | 0x014f | 0 | 0x1e53c |
| mmUVD_LMI_JRBC_RB_VMID | 0x0150 | 0 | 0x1e540 |
| mmUVD_LMI_JPEG_VMID | 0x0151 | 0 | 0x1e544 |
| mmUVD_JMI_ENC_JRBC_IB_VMID | 0x0152 | 0 | 0x1e548 |
| mmUVD_JMI_ENC_JRBC_RB_VMID | 0x0153 | 0 | 0x1e54c |
| mmUVD_JMI_ENC_JPEG_VMID | 0x0154 | 0 | 0x1e550 |
| mmUVD_JMI_PERFMON_CTRL | 0x015c | 0 | 0x1e570 |
| mmUVD_JMI_PERFMON_COUNT_LO | 0x015d | 0 | 0x1e574 |
| mmUVD_JMI_PERFMON_COUNT_HI | 0x015e | 0 | 0x1e578 |
| mmUVD_LMI_JPEG_READ_64BIT_BAR_LOW | 0x0160 | 0 | 0x1e580 |
| mmUVD_LMI_JPEG_READ_64BIT_BAR_HIGH | 0x0161 | 0 | 0x1e584 |
| mmUVD_LMI_JPEG_WRITE_64BIT_BAR_LOW | 0x0162 | 0 | 0x1e588 |
| mmUVD_LMI_JPEG_WRITE_64BIT_BAR_HIGH | 0x0163 | 0 | 0x1e58c |
| mmUVD_LMI_JPEG_PREEMPT_FENCE_64BIT_BAR_LOW | 0x0164 | 0 | 0x1e590 |
| mmUVD_LMI_JPEG_PREEMPT_FENCE_64BIT_BAR_HIGH | 0x0165 | 0 | 0x1e594 |
| mmUVD_LMI_JRBC_RB_64BIT_BAR_LOW | 0x0166 | 0 | 0x1e598 |
| mmUVD_LMI_JRBC_RB_64BIT_BAR_HIGH | 0x0167 | 0 | 0x1e59c |
| mmUVD_LMI_JRBC_IB_64BIT_BAR_LOW | 0x0168 | 0 | 0x1e5a0 |
| mmUVD_LMI_JRBC_IB_64BIT_BAR_HIGH | 0x0169 | 0 | 0x1e5a4 |
| mmUVD_LMI_JRBC_RB_MEM_WR_64BIT_BAR_LOW | 0x016a | 0 | 0x1e5a8 |
| mmUVD_LMI_JRBC_RB_MEM_WR_64BIT_BAR_HIGH | 0x016b | 0 | 0x1e5ac |
| mmUVD_LMI_JRBC_RB_MEM_RD_64BIT_BAR_LOW | 0x016c | 0 | 0x1e5b0 |
| mmUVD_LMI_JRBC_RB_MEM_RD_64BIT_BAR_HIGH | 0x016d | 0 | 0x1e5b4 |
| mmUVD_LMI_JRBC_IB_MEM_WR_64BIT_BAR_LOW | 0x016e | 0 | 0x1e5b8 |
| mmUVD_LMI_JRBC_IB_MEM_WR_64BIT_BAR_HIGH | 0x016f | 0 | 0x1e5bc |
| mmUVD_LMI_JRBC_IB_MEM_RD_64BIT_BAR_LOW | 0x0170 | 0 | 0x1e5c0 |
| mmUVD_LMI_JRBC_IB_MEM_RD_64BIT_BAR_HIGH | 0x0171 | 0 | 0x1e5c4 |
| mmUVD_LMI_EJPEG_PREEMPT_FENCE_64BIT_BAR_LOW | 0x017a | 0 | 0x1e5e8 |
| mmUVD_LMI_EJPEG_PREEMPT_FENCE_64BIT_BAR_HIGH | 0x017b | 0 | 0x1e5ec |
| mmUVD_LMI_EJRBC_RB_64BIT_BAR_LOW | 0x017c | 0 | 0x1e5f0 |
| mmUVD_LMI_EJRBC_RB_64BIT_BAR_HIGH | 0x017d | 0 | 0x1e5f4 |
| mmUVD_LMI_EJRBC_IB_64BIT_BAR_LOW | 0x017e | 0 | 0x1e5f8 |
| mmUVD_LMI_EJRBC_IB_64BIT_BAR_HIGH | 0x017f | 0 | 0x1e5fc |
| mmUVD_LMI_EJRBC_RB_MEM_WR_64BIT_BAR_LOW | 0x0180 | 0 | 0x1e600 |
| mmUVD_LMI_EJRBC_RB_MEM_WR_64BIT_BAR_HIGH | 0x0181 | 0 | 0x1e604 |
| mmUVD_LMI_EJRBC_RB_MEM_RD_64BIT_BAR_LOW | 0x0182 | 0 | 0x1e608 |
| mmUVD_LMI_EJRBC_RB_MEM_RD_64BIT_BAR_HIGH | 0x0183 | 0 | 0x1e60c |
| mmUVD_LMI_EJRBC_IB_MEM_WR_64BIT_BAR_LOW | 0x0184 | 0 | 0x1e610 |
| mmUVD_LMI_EJRBC_IB_MEM_WR_64BIT_BAR_HIGH | 0x0185 | 0 | 0x1e614 |
| mmUVD_LMI_EJRBC_IB_MEM_RD_64BIT_BAR_LOW | 0x0186 | 0 | 0x1e618 |
| mmUVD_LMI_EJRBC_IB_MEM_RD_64BIT_BAR_HIGH | 0x0187 | 0 | 0x1e61c |
| mmUVD_LMI_JPEG_PREEMPT_VMID | 0x0188 | 0 | 0x1e620 |
| mmUVD_LMI_ENC_JPEG_PREEMPT_VMID | 0x0189 | 0 | 0x1e624 |
| mmUVD_LMI_JPEG2_VMID | 0x018a | 0 | 0x1e628 |
| mmUVD_LMI_JPEG2_READ_64BIT_BAR_LOW | 0x018b | 0 | 0x1e62c |
| mmUVD_LMI_JPEG2_READ_64BIT_BAR_HIGH | 0x018c | 0 | 0x1e630 |
| mmUVD_LMI_JPEG2_WRITE_64BIT_BAR_LOW | 0x018d | 0 | 0x1e634 |
| mmUVD_LMI_JPEG2_WRITE_64BIT_BAR_HIGH | 0x018e | 0 | 0x1e638 |
| mmUVD_LMI_JPEG_CTRL2 | 0x018f | 0 | 0x1e63c |
| mmUVD_JMI_DEC_SWAP_CNTL | 0x0190 | 0 | 0x1e640 |
| mmUVD_JMI_ENC_SWAP_CNTL | 0x0191 | 0 | 0x1e644 |
| mmUVD_JMI_CNTL | 0x0192 | 0 | 0x1e648 |
| mmUVD_JMI_HUFF_FENCE_64BIT_BAR_LOW | 0x019a | 0 | 0x1e668 |
| mmUVD_JMI_HUFF_FENCE_64BIT_BAR_HIGH | 0x019b | 0 | 0x1e66c |
| mmUVD_JMI_DEC_SWAP_CNTL2 | 0x019c | 0 | 0x1e670 |
| mmJPEG_SOFT_RESET_STATUS | 0x01c0 | 0 | 0x1e700 |
| mmJPEG_SYS_INT_EN | 0x01c1 | 0 | 0x1e704 |
| mmJPEG_SYS_INT_STATUS | 0x01c2 | 0 | 0x1e708 |
| mmJPEG_SYS_INT_ACK | 0x01c3 | 0 | 0x1e70c |
| mmJPEG_MASTINT_EN | 0x01c8 | 0 | 0x1e720 |
| mmJPEG_IH_CTRL | 0x01c9 | 0 | 0x1e724 |
| mmJRBBM_ARB_CTRL | 0x01cb | 0 | 0x1e72c |
| mmJPEG_CGC_GATE | 0x01e0 | 0 | 0x1e780 |
| mmJPEG_CGC_CTRL | 0x01e1 | 0 | 0x1e784 |
| mmJPEG_CGC_STATUS | 0x01e2 | 0 | 0x1e788 |
| mmJPEG_COMN_CGC_MEM_CTRL | 0x01e3 | 0 | 0x1e78c |
| mmJPEG_DEC_CGC_MEM_CTRL | 0x01e4 | 0 | 0x1e790 |
| mmJPEG2_DEC_CGC_MEM_CTRL | 0x01e5 | 0 | 0x1e794 |
| mmJPEG_ENC_CGC_MEM_CTRL | 0x01e6 | 0 | 0x1e798 |
| mmJPEG_SOFT_RESET2 | 0x01e7 | 0 | 0x1e79c |
| mmJPEG_PERF_BANK_CONF | 0x01e8 | 0 | 0x1e7a0 |
| mmJPEG_PERF_BANK_EVENT_SEL | 0x01e9 | 0 | 0x1e7a4 |
| mmJPEG_PERF_BANK_COUNT0 | 0x01ea | 0 | 0x1e7a8 |
| mmJPEG_PERF_BANK_COUNT1 | 0x01eb | 0 | 0x1e7ac |
| mmJPEG_PERF_BANK_COUNT2 | 0x01ec | 0 | 0x1e7b0 |
| mmJPEG_PERF_BANK_COUNT3 | 0x01ed | 0 | 0x1e7b4 |
| mmUVD_PGFSM_CONFIG | 0x0000 | 1 | 0x1f800 |
| mmUVD_PGFSM_STATUS | 0x0001 | 1 | 0x1f804 |
| mmUVD_POWER_STATUS | 0x0004 | 1 | 0x1f810 |
| mmUVD_PG_IND_INDEX | 0x0005 | 1 | 0x1f814 |
| mmUVD_PG_IND_DATA | 0x0006 | 1 | 0x1f818 |
| mmCC_UVD_HARVESTING | 0x0007 | 1 | 0x1f81c |
| mmUVD_JPEG_POWER_STATUS | 0x000a | 1 | 0x1f828 |
| mmUVD_DPG_LMA_CTL | 0x0011 | 1 | 0x1f844 |
| mmUVD_DPG_LMA_DATA | 0x0012 | 1 | 0x1f848 |
| mmUVD_DPG_LMA_MASK | 0x0013 | 1 | 0x1f84c |
| mmUVD_DPG_PAUSE | 0x0014 | 1 | 0x1f850 |
| mmUVD_SCRATCH1 | 0x0015 | 1 | 0x1f854 |
| mmUVD_SCRATCH2 | 0x0016 | 1 | 0x1f858 |
| mmUVD_SCRATCH3 | 0x0017 | 1 | 0x1f85c |
| mmUVD_SCRATCH4 | 0x0018 | 1 | 0x1f860 |
| mmUVD_SCRATCH5 | 0x0019 | 1 | 0x1f864 |
| mmUVD_SCRATCH6 | 0x001a | 1 | 0x1f868 |
| mmUVD_SCRATCH7 | 0x001b | 1 | 0x1f86c |
| mmUVD_SCRATCH8 | 0x001c | 1 | 0x1f870 |
| mmUVD_SCRATCH9 | 0x001d | 1 | 0x1f874 |
| mmUVD_SCRATCH10 | 0x001e | 1 | 0x1f878 |
| mmUVD_SCRATCH11 | 0x001f | 1 | 0x1f87c |
| mmUVD_SCRATCH12 | 0x0020 | 1 | 0x1f880 |
| mmUVD_SCRATCH13 | 0x0021 | 1 | 0x1f884 |
| mmUVD_SCRATCH14 | 0x0022 | 1 | 0x1f888 |
| mmUVD_FREE_COUNTER_REG | 0x0024 | 1 | 0x1f890 |
| mmUVD_DPG_LMI_VCPU_CACHE_64BIT_BAR_LOW | 0x0025 | 1 | 0x1f894 |
| mmUVD_DPG_LMI_VCPU_CACHE_64BIT_BAR_HIGH | 0x0026 | 1 | 0x1f898 |
| mmUVD_DPG_VCPU_CACHE_OFFSET0 | 0x0027 | 1 | 0x1f89c |
| mmUVD_DPG_LMI_VCPU_CACHE_VMID | 0x0028 | 1 | 0x1f8a0 |
| mmUVD_PF_STATUS | 0x0039 | 1 | 0x1f8e4 |
| mmUVD_DPG_CLK_EN_VCPU_REPORT | 0x003c | 1 | 0x1f8f0 |
| mmUVD_GFX8_ADDR_CONFIG | 0x0049 | 1 | 0x1f924 |
| mmUVD_GFX10_ADDR_CONFIG | 0x004a | 1 | 0x1f928 |
| mmUVD_GPCNT2_CNTL | 0x004b | 1 | 0x1f92c |
| mmUVD_GPCNT2_TARGET_LOWER | 0x004c | 1 | 0x1f930 |
| mmUVD_GPCNT2_STATUS_LOWER | 0x004d | 1 | 0x1f934 |
| mmUVD_GPCNT2_TARGET_UPPER | 0x004e | 1 | 0x1f938 |
| mmUVD_GPCNT2_STATUS_UPPER | 0x004f | 1 | 0x1f93c |
| mmUVD_GPCNT3_CNTL | 0x0050 | 1 | 0x1f940 |
| mmUVD_GPCNT3_TARGET_LOWER | 0x0051 | 1 | 0x1f944 |
| mmUVD_GPCNT3_STATUS_LOWER | 0x0052 | 1 | 0x1f948 |
| mmUVD_GPCNT3_TARGET_UPPER | 0x0053 | 1 | 0x1f94c |
| mmUVD_GPCNT3_STATUS_UPPER | 0x0054 | 1 | 0x1f950 |
| mmUVD_TSC_LOWER | 0x0057 | 1 | 0x1f95c |
| mmUVD_TSC_UPPER | 0x0058 | 1 | 0x1f960 |
| mmUVD_SEMA_CNTL | 0x01c0 | 1 | 0x1ff00 |
| mmUVD_RB_RPTR3 | 0x01db | 1 | 0x1ff6c |
| mmUVD_RB_WPTR3 | 0x01dc | 1 | 0x1ff70 |
| mmUVD_RB_BASE_LO3 | 0x01dd | 1 | 0x1ff74 |
| mmUVD_RB_BASE_HI3 | 0x01de | 1 | 0x1ff78 |
| mmUVD_RB_SIZE3 | 0x01df | 1 | 0x1ff7c |
| mmUVD_RB_ARB_CTRL | 0x01e0 | 1 | 0x1ff80 |
| mmUVD_LMI_LAT_CTRL | 0x01e2 | 1 | 0x1ff88 |
| mmUVD_LMI_LAT_CNTR | 0x01e3 | 1 | 0x1ff8c |
| mmUVD_LMI_AVG_LAT_CNTR | 0x01e4 | 1 | 0x1ff90 |
| mmUVD_SOFT_RESET2 | 0x01e6 | 1 | 0x1ff98 |
| mmUVD_LMI_SPH | 0x01e7 | 1 | 0x1ff9c |
| mmUVD_CTX_INDEX | 0x01e8 | 1 | 0x1ffa0 |
| mmUVD_CTX_DATA | 0x01e9 | 1 | 0x1ffa4 |
| mmUVD_CGC_GATE | 0x01ea | 1 | 0x1ffa8 |
| mmUVD_CGC_STATUS | 0x01eb | 1 | 0x1ffac |
| mmUVD_CGC_CTRL | 0x01ec | 1 | 0x1ffb0 |
| mmUVD_CGC_UDEC_STATUS | 0x01ed | 1 | 0x1ffb4 |
| mmUVD_CXW_WR_INT_ID | 0x01ee | 1 | 0x1ffb8 |
| mmUVD_CXW_WR_INT_CTX_ID | 0x01ef | 1 | 0x1ffbc |
| mmUVD_VCPU_INT_ROUTE | 0x01f3 | 1 | 0x1ffcc |
| mmUVD_GP_SCRATCH0 | 0x01f4 | 1 | 0x1ffd0 |
| mmUVD_GP_SCRATCH1 | 0x01f5 | 1 | 0x1ffd4 |
| mmUVD_GP_SCRATCH2 | 0x01f6 | 1 | 0x1ffd8 |
| mmUVD_GP_SCRATCH3 | 0x01f7 | 1 | 0x1ffdc |
| mmUVD_GP_SCRATCH4 | 0x01f8 | 1 | 0x1ffe0 |
| mmUVD_GP_SCRATCH5 | 0x01f9 | 1 | 0x1ffe4 |
| mmUVD_GP_SCRATCH6 | 0x01fa | 1 | 0x1ffe8 |
| mmUVD_GP_SCRATCH7 | 0x01fb | 1 | 0x1ffec |
| mmUVD_LMI_VCPU_CACHE_VMID | 0x01fc | 1 | 0x1fff0 |
| mmUVD_LMI_CTRL2 | 0x01fd | 1 | 0x1fff4 |
| mmUVD_MASTINT_EN | 0x0200 | 1 | 0x20000 |
| mmUVD_SYS_INT_EN | 0x0201 | 1 | 0x20004 |
| mmUVD_SYS_INT_STATUS | 0x0202 | 1 | 0x20008 |
| mmUVD_SYS_INT_ACK | 0x0203 | 1 | 0x2000c |
| mmUVD_VCPU_INT_EN | 0x0204 | 1 | 0x20010 |
| mmUVD_VCPU_INT_ACK | 0x0206 | 1 | 0x20018 |
| mmUVD_TOP_CTRL | 0x0207 | 1 | 0x2001c |
| mmUVD_ENC_VCPU_INT_EN | 0x021f | 1 | 0x2007c |
| mmUVD_ENC_VCPU_INT_ACK | 0x0221 | 1 | 0x20084 |
| mmUVD_LMI_VCPU_CACHE_VMIDS_MULTI | 0x0222 | 1 | 0x20088 |
| mmUVD_LMI_VCPU_NC_VMIDS_MULTI | 0x0223 | 1 | 0x2008c |
| mmUVD_LMI_URGENT_CTRL | 0x0224 | 1 | 0x20090 |
| mmUVD_LMI_CTRL | 0x0226 | 1 | 0x20098 |
| mmUVD_LMI_STATUS | 0x0227 | 1 | 0x2009c |
| mmUVD_LMI_VM_CTRL | 0x0228 | 1 | 0x200a0 |
| mmUVD_LMI_PERFMON_CTRL | 0x022a | 1 | 0x200a8 |
| mmUVD_LMI_PERFMON_COUNT_LO | 0x022b | 1 | 0x200ac |
| mmUVD_LMI_PERFMON_COUNT_HI | 0x022c | 1 | 0x200b0 |
| mmUVD_LMI_SWAP_CNTL | 0x022d | 1 | 0x200b4 |
| mmUVD_UDEC_ADR | 0x022e | 1 | 0x200b8 |
| mmUVD_MP_SWAP_CNTL | 0x022f | 1 | 0x200bc |
| mmUVD_MPC_LUMA_SRCH | 0x0231 | 1 | 0x200c4 |
| mmUVD_MPC_LUMA_HIT | 0x0232 | 1 | 0x200c8 |
| mmUVD_MPC_LUMA_HITPEND | 0x0233 | 1 | 0x200cc |
| mmUVD_MPC_CHROMA_SRCH | 0x0234 | 1 | 0x200d0 |
| mmUVD_MPC_CHROMA_HIT | 0x0235 | 1 | 0x200d4 |
| mmUVD_MPC_CHROMA_HITPEND | 0x0236 | 1 | 0x200d8 |
| mmUVD_MPC_CNTL | 0x0237 | 1 | 0x200dc |
| mmUVD_MPC_PITCH | 0x0238 | 1 | 0x200e0 |
| mmUVD_MPC_SET_MUXA0 | 0x0239 | 1 | 0x200e4 |
| mmUVD_MPC_SET_MUXA1 | 0x023a | 1 | 0x200e8 |
| mmUVD_MPC_SET_MUXB0 | 0x023b | 1 | 0x200ec |
| mmUVD_MPC_SET_MUXB1 | 0x023c | 1 | 0x200f0 |
| mmUVD_MPC_SET_MUX | 0x023d | 1 | 0x200f4 |
| mmUVD_MPC_SET_ALU | 0x023e | 1 | 0x200f8 |
| mmUVD_GPCOM_SYS_CMD | 0x023f | 1 | 0x200fc |
| mmUVD_GPCOM_SYS_DATA0 | 0x0240 | 1 | 0x20100 |
| mmUVD_GPCOM_SYS_DATA1 | 0x0241 | 1 | 0x20104 |
| mmUVD_VCPU_CACHE_OFFSET0 | 0x0242 | 1 | 0x20108 |
| mmUVD_VCPU_CACHE_SIZE0 | 0x0243 | 1 | 0x2010c |
| mmUVD_VCPU_CACHE_OFFSET1 | 0x0244 | 1 | 0x20110 |
| mmUVD_VCPU_CACHE_SIZE1 | 0x0245 | 1 | 0x20114 |
| mmUVD_VCPU_CACHE_OFFSET2 | 0x0246 | 1 | 0x20118 |
| mmUVD_VCPU_CACHE_SIZE2 | 0x0247 | 1 | 0x2011c |
| mmUVD_VCPU_CACHE_OFFSET3 | 0x0248 | 1 | 0x20120 |
| mmUVD_VCPU_CACHE_SIZE3 | 0x0249 | 1 | 0x20124 |
| mmUVD_VCPU_CACHE_OFFSET4 | 0x024a | 1 | 0x20128 |
| mmUVD_VCPU_CACHE_SIZE4 | 0x024b | 1 | 0x2012c |
| mmUVD_VCPU_CACHE_OFFSET5 | 0x024c | 1 | 0x20130 |
| mmUVD_VCPU_CACHE_SIZE5 | 0x024d | 1 | 0x20134 |
| mmUVD_VCPU_CACHE_OFFSET6 | 0x024e | 1 | 0x20138 |
| mmUVD_VCPU_CACHE_SIZE6 | 0x024f | 1 | 0x2013c |
| mmUVD_VCPU_CACHE_OFFSET7 | 0x0250 | 1 | 0x20140 |
| mmUVD_VCPU_CACHE_SIZE7 | 0x0251 | 1 | 0x20144 |
| mmUVD_VCPU_CACHE_OFFSET8 | 0x0252 | 1 | 0x20148 |
| mmUVD_VCPU_CACHE_SIZE8 | 0x0253 | 1 | 0x2014c |
| mmUVD_VCPU_NONCACHE_OFFSET0 | 0x0254 | 1 | 0x20150 |
| mmUVD_VCPU_NONCACHE_SIZE0 | 0x0255 | 1 | 0x20154 |
| mmUVD_VCPU_NONCACHE_OFFSET1 | 0x0256 | 1 | 0x20158 |
| mmUVD_VCPU_NONCACHE_SIZE1 | 0x0257 | 1 | 0x2015c |
| mmUVD_VCPU_CNTL | 0x0258 | 1 | 0x20160 |
| mmUVD_VCPU_PRID | 0x0259 | 1 | 0x20164 |
| mmUVD_VCPU_TRCE | 0x025a | 1 | 0x20168 |
| mmUVD_VCPU_TRCE_RD | 0x025b | 1 | 0x2016c |
| mmUVD_MPC_PERF0 | 0x025c | 1 | 0x20170 |
| mmUVD_MPC_PERF1 | 0x025d | 1 | 0x20174 |
| mmUVD_CXW_WR | 0x025f | 1 | 0x2017c |
| mmUVD_SOFT_RESET | 0x0260 | 1 | 0x20180 |
| mmUVD_LMI_RBC_IB_VMID | 0x0261 | 1 | 0x20184 |
| mmUVD_RBC_IB_SIZE | 0x0262 | 1 | 0x20188 |
| mmUVD_LMI_RBC_RB_VMID | 0x0263 | 1 | 0x2018c |
| mmUVD_RBC_RB_RPTR | 0x0264 | 1 | 0x20190 |
| mmUVD_RBC_RB_WPTR | 0x0265 | 1 | 0x20194 |
| mmUVD_RBC_RB_WPTR_CNTL | 0x0266 | 1 | 0x20198 |
| mmUVD_RBC_READ_REQ_URGENT_CNTL | 0x0267 | 1 | 0x2019c |
| mmUVD_RBC_WPTR_STATUS | 0x0268 | 1 | 0x201a0 |
| mmUVD_RBC_RB_CNTL | 0x0269 | 1 | 0x201a4 |
| mmUVD_RBC_RB_RPTR_ADDR | 0x026a | 1 | 0x201a8 |
| mmUVD_JOB_START | 0x026d | 1 | 0x201b4 |
| mmUVD_JOB_DONE | 0x026e | 1 | 0x201b8 |
| mmUVD_STATUS | 0x026f | 1 | 0x201bc |
| mmUVD_SEMA_TIMEOUT_STATUS | 0x0270 | 1 | 0x201c0 |
| mmUVD_SEMA_WAIT_INCOMPLETE_TIMEOUT_CNTL | 0x0271 | 1 | 0x201c4 |
| mmUVD_SEMA_WAIT_FAULT_TIMEOUT_CNTL | 0x0272 | 1 | 0x201c8 |
| mmUVD_SEMA_SIGNAL_INCOMPLETE_TIMEOUT_CNTL | 0x0273 | 1 | 0x201cc |
| mmUVD_CXW_EN | 0x0274 | 1 | 0x201d0 |
| mmUVD_CXW_SE | 0x0275 | 1 | 0x201d4 |
| mmUVD_CXW_FINISHED | 0x0276 | 1 | 0x201d8 |
| mmUVD_CXW_SHIFT_FINISHED | 0x0277 | 1 | 0x201dc |
| mmUVD_CXW_START | 0x0278 | 1 | 0x201e0 |
| mmUVD_CXW_BLOCK_STATUS | 0x0279 | 1 | 0x201e4 |
| mmUVD_STOP_CONTEXT | 0x027a | 1 | 0x201e8 |
| mmUVD_CXW_SAVE_AREA_ADDR | 0x027b | 1 | 0x201ec |
| mmUVD_CBUF_ID | 0x027c | 1 | 0x201f0 |
| mmUVD_CONTEXT_ID | 0x027d | 1 | 0x201f4 |
| mmUVD_CXW_SAVE_AREA_SIZE | 0x027e | 1 | 0x201f8 |
| mmUVD_CONTEXT_ID2 | 0x027f | 1 | 0x201fc |
| mmUVD_CXW_CNTL | 0x0280 | 1 | 0x20200 |
| mmUVD_CXW_EVENT | 0x0281 | 1 | 0x20204 |
| mmUVD_CXW_SCAN_AREA_OFFSET | 0x0282 | 1 | 0x20208 |
| mmUVD_CXW_SHIFT_CNTL | 0x0283 | 1 | 0x2020c |
| mmUVD_RBC_CAM_EN | 0x0286 | 1 | 0x20218 |
| mmUVD_RBC_CAM_INDEX | 0x0287 | 1 | 0x2021c |
| mmUVD_RBC_CAM_DATA | 0x0288 | 1 | 0x20220 |
| mmUVD_RBC_VCPU_ACCESS | 0x0289 | 1 | 0x20224 |
| mmUVD_CXW_INT_ID | 0x0293 | 1 | 0x2024c |
| mmUVD_LMI_CRC0 | 0x0294 | 1 | 0x20250 |
| mmUVD_LMI_CRC1 | 0x0295 | 1 | 0x20254 |
| mmUVD_LMI_CRC2 | 0x0296 | 1 | 0x20258 |
| mmUVD_LMI_CRC3 | 0x0297 | 1 | 0x2025c |
| mmUVD_RBC_WPTR_POLL_CNTL | 0x0298 | 1 | 0x20260 |
| mmUVD_RBC_WPTR_POLL_ADDR | 0x0299 | 1 | 0x20264 |
| mmUVD_RB_BASE_LO4 | 0x029f | 1 | 0x2027c |
| mmUVD_RB_BASE_HI4 | 0x02a0 | 1 | 0x20280 |
| mmUVD_RB_SIZE4 | 0x02a1 | 1 | 0x20284 |
| mmUVD_RB_RPTR4 | 0x02a2 | 1 | 0x20288 |
| mmUVD_LMI_MC_CREDITS | 0x02a3 | 1 | 0x2028c |
| mmUVD_RBC_BUF_STATUS | 0x02b0 | 1 | 0x202c0 |
| mmUVD_RBC_IB_SIZE_UPDATE | 0x02b1 | 1 | 0x202c4 |
| mmUVD_RBC_BDM_PRE | 0x02b2 | 1 | 0x202c8 |
| mmCG_TIMESTAMP_LOW | 0x02b5 | 1 | 0x202d4 |
| mmCG_TIMESTAMP_HIGH | 0x02b6 | 1 | 0x202d8 |
| mmUVD_UMC_UVD_CTL_CMD | 0x02b7 | 1 | 0x202dc |
| mmUVD_UMC_UVD_BLOCK_REQ | 0x02b8 | 1 | 0x202e0 |
| mmUVD_RBC_CXW_RELEASE | 0x02b9 | 1 | 0x202e4 |
| mmUVD_YBASE | 0x02ba | 1 | 0x202e8 |
| mmUVD_UVBASE | 0x02bb | 1 | 0x202ec |
| mmUVD_PITCH | 0x02bc | 1 | 0x202f0 |
| mmUVD_WIDTH | 0x02bd | 1 | 0x202f4 |
| mmUVD_HEIGHT | 0x02be | 1 | 0x202f8 |
| mmUVD_PICCOUNT | 0x02bf | 1 | 0x202fc |
| mmUVD_SEMA_ADDR_LOW | 0x0580 | 1 | 0x20e00 |
| mmUVD_SEMA_ADDR_HIGH | 0x0581 | 1 | 0x20e04 |
| mmUVD_SEMA_CMD | 0x0582 | 1 | 0x20e08 |
| mmUVD_GPCOM_VCPU_CMD | 0x0583 | 1 | 0x20e0c |
| mmUVD_GPCOM_VCPU_DATA0 | 0x0584 | 1 | 0x20e10 |
| mmUVD_GPCOM_VCPU_DATA1 | 0x0585 | 1 | 0x20e14 |
| mmUVD_ENGINE_CNTL | 0x0586 | 1 | 0x20e18 |
| mmUVD_SUVD_CGC_GATE | 0x05a4 | 1 | 0x20e90 |
| mmUVD_SUVD_CGC_STATUS | 0x05a5 | 1 | 0x20e94 |
| mmUVD_SUVD_CGC_CTRL | 0x05a6 | 1 | 0x20e98 |
| mmUVD_LMI_VCPU_CACHE1_64BIT_BAR_LOW | 0x05ac | 1 | 0x20eb0 |
| mmUVD_LMI_VCPU_CACHE1_64BIT_BAR_HIGH | 0x05ad | 1 | 0x20eb4 |
| mmUVD_LMI_VCPU_CACHE8_64BIT_BAR_LOW | 0x05ae | 1 | 0x20eb8 |
| mmUVD_LMI_VCPU_CACHE8_64BIT_BAR_HIGH | 0x05af | 1 | 0x20ebc |
| mmUVD_LMI_VCPU_CACHE2_64BIT_BAR_LOW | 0x05b0 | 1 | 0x20ec0 |
| mmUVD_LMI_VCPU_CACHE2_64BIT_BAR_HIGH | 0x05b1 | 1 | 0x20ec4 |
| mmUVD_LMI_VCPU_CACHE3_64BIT_BAR_LOW | 0x05b2 | 1 | 0x20ec8 |
| mmUVD_LMI_VCPU_CACHE3_64BIT_BAR_HIGH | 0x05b3 | 1 | 0x20ecc |
| mmUVD_LMI_VCPU_CACHE4_64BIT_BAR_LOW | 0x05b4 | 1 | 0x20ed0 |
| mmUVD_LMI_VCPU_CACHE4_64BIT_BAR_HIGH | 0x05b5 | 1 | 0x20ed4 |
| mmUVD_LMI_VCPU_CACHE5_64BIT_BAR_LOW | 0x05b6 | 1 | 0x20ed8 |
| mmUVD_LMI_VCPU_CACHE5_64BIT_BAR_HIGH | 0x05b7 | 1 | 0x20edc |
| mmUVD_LMI_VCPU_CACHE6_64BIT_BAR_LOW | 0x05b8 | 1 | 0x20ee0 |
| mmUVD_LMI_VCPU_CACHE6_64BIT_BAR_HIGH | 0x05b9 | 1 | 0x20ee4 |
| mmUVD_LMI_VCPU_CACHE7_64BIT_BAR_LOW | 0x05ba | 1 | 0x20ee8 |
| mmUVD_LMI_VCPU_CACHE7_64BIT_BAR_HIGH | 0x05bb | 1 | 0x20eec |
| mmUVD_SCRATCH_NP | 0x05bc | 1 | 0x20ef0 |
| mmUVD_NO_OP | 0x05bf | 1 | 0x20efc |
| mmMDM_DMA_CMD | 0x05c0 | 1 | 0x20f00 |
| mmMDM_DMA_STATUS | 0x05c1 | 1 | 0x20f04 |
| mmMDM_DMA_CTL | 0x05c2 | 1 | 0x20f08 |
| mmMDM_ENC_PIPE_BUSY | 0x05c3 | 1 | 0x20f0c |
| mmMDM_WIG_PIPE_BUSY | 0x05c5 | 1 | 0x20f14 |
| mmUVD_VERSION | 0x05c9 | 1 | 0x20f24 |
| mmUVD_GP_SCRATCH8 | 0x05ca | 1 | 0x20f28 |
| mmUVD_GP_SCRATCH9 | 0x05cb | 1 | 0x20f2c |
| mmUVD_GP_SCRATCH10 | 0x05cc | 1 | 0x20f30 |
| mmUVD_GP_SCRATCH11 | 0x05cd | 1 | 0x20f34 |
| mmUVD_GP_SCRATCH12 | 0x05ce | 1 | 0x20f38 |
| mmUVD_GP_SCRATCH13 | 0x05cf | 1 | 0x20f3c |
| mmUVD_GP_SCRATCH14 | 0x05d0 | 1 | 0x20f40 |
| mmUVD_GP_SCRATCH15 | 0x05d1 | 1 | 0x20f44 |
| mmUVD_GP_SCRATCH16 | 0x05d2 | 1 | 0x20f48 |
| mmUVD_GP_SCRATCH17 | 0x05d3 | 1 | 0x20f4c |
| mmUVD_GP_SCRATCH18 | 0x05d4 | 1 | 0x20f50 |
| mmUVD_GP_SCRATCH19 | 0x05d5 | 1 | 0x20f54 |
| mmUVD_GP_SCRATCH20 | 0x05d6 | 1 | 0x20f58 |
| mmUVD_GP_SCRATCH21 | 0x05d7 | 1 | 0x20f5c |
| mmUVD_GP_SCRATCH22 | 0x05d8 | 1 | 0x20f60 |
| mmUVD_GP_SCRATCH23 | 0x05d9 | 1 | 0x20f64 |
| mmUVD_ENC_REG_INDEX | 0x05da | 1 | 0x20f68 |
| mmUVD_ENC_REG_DATA | 0x05db | 1 | 0x20f6c |
| mmUVD_OUT_RB_BASE_LO | 0x05dc | 1 | 0x20f70 |
| mmUVD_OUT_RB_BASE_HI | 0x05dd | 1 | 0x20f74 |
| mmUVD_OUT_RB_SIZE | 0x05de | 1 | 0x20f78 |
| mmUVD_OUT_RB_RPTR | 0x05df | 1 | 0x20f7c |
| mmUVD_OUT_RB_WPTR | 0x05e0 | 1 | 0x20f80 |
| mmUVD_RB_BASE_LO2 | 0x05e1 | 1 | 0x20f84 |
| mmUVD_RB_BASE_HI2 | 0x05e2 | 1 | 0x20f88 |
| mmUVD_RB_SIZE2 | 0x05e3 | 1 | 0x20f8c |
| mmUVD_RB_RPTR2 | 0x05e4 | 1 | 0x20f90 |
| mmUVD_RB_WPTR2 | 0x05e5 | 1 | 0x20f94 |
| mmUVD_RB_BASE_LO | 0x05e6 | 1 | 0x20f98 |
| mmUVD_RB_BASE_HI | 0x05e7 | 1 | 0x20f9c |
| mmUVD_RB_SIZE | 0x05e8 | 1 | 0x20fa0 |
| mmUVD_RB_RPTR | 0x05e9 | 1 | 0x20fa4 |
| mmUVD_RB_WPTR | 0x05ea | 1 | 0x20fa8 |
| mmUVD_ENC_PIPE_BUSY | 0x05eb | 1 | 0x20fac |
| mmUVD_RB_WPTR4 | 0x0616 | 1 | 0x21058 |
| mmUVD_LMI_VCPU_CACHE_64BIT_BAR_HIGH | 0x061e | 1 | 0x21078 |
| mmUVD_LMI_VCPU_CACHE_64BIT_BAR_LOW | 0x061f | 1 | 0x2107c |
| mmUVD_LMI_VCPU_NC1_64BIT_BAR_HIGH | 0x0620 | 1 | 0x21080 |
| mmUVD_LMI_VCPU_NC1_64BIT_BAR_LOW | 0x0621 | 1 | 0x21084 |
| mmUVD_LMI_VCPU_NC0_64BIT_BAR_HIGH | 0x0622 | 1 | 0x21088 |
| mmUVD_LMI_VCPU_NC0_64BIT_BAR_LOW | 0x0623 | 1 | 0x2108c |
| mmUVD_LMI_RBC_IB_64BIT_BAR_HIGH | 0x0626 | 1 | 0x21098 |
| mmUVD_LMI_RBC_IB_64BIT_BAR_LOW | 0x0627 | 1 | 0x2109c |
| mmUVD_LMI_RBC_RB_64BIT_BAR_HIGH | 0x0628 | 1 | 0x210a0 |
| mmUVD_LMI_RBC_RB_64BIT_BAR_LOW | 0x0629 | 1 | 0x210a4 |
| mmUVD_LMI_MMSCH_NC0_64BIT_BAR_LOW | 0x0640 | 1 | 0x21100 |
| mmUVD_LMI_MMSCH_NC0_64BIT_BAR_HIGH | 0x0641 | 1 | 0x21104 |
| mmUVD_LMI_MMSCH_NC1_64BIT_BAR_LOW | 0x0642 | 1 | 0x21108 |
| mmUVD_LMI_MMSCH_NC1_64BIT_BAR_HIGH | 0x0643 | 1 | 0x2110c |
| mmUVD_LMI_MMSCH_NC2_64BIT_BAR_LOW | 0x0644 | 1 | 0x21110 |
| mmUVD_LMI_MMSCH_NC2_64BIT_BAR_HIGH | 0x0645 | 1 | 0x21114 |
| mmUVD_LMI_MMSCH_NC3_64BIT_BAR_LOW | 0x0646 | 1 | 0x21118 |
| mmUVD_LMI_MMSCH_NC3_64BIT_BAR_HIGH | 0x0647 | 1 | 0x2111c |
| mmUVD_LMI_MMSCH_NC4_64BIT_BAR_LOW | 0x0648 | 1 | 0x21120 |
| mmUVD_LMI_MMSCH_NC4_64BIT_BAR_HIGH | 0x0649 | 1 | 0x21124 |
| mmUVD_LMI_MMSCH_NC5_64BIT_BAR_LOW | 0x064a | 1 | 0x21128 |
| mmUVD_LMI_MMSCH_NC5_64BIT_BAR_HIGH | 0x064b | 1 | 0x2112c |
| mmUVD_LMI_MMSCH_NC6_64BIT_BAR_LOW | 0x064c | 1 | 0x21130 |
| mmUVD_LMI_MMSCH_NC6_64BIT_BAR_HIGH | 0x064d | 1 | 0x21134 |
| mmUVD_LMI_MMSCH_NC7_64BIT_BAR_LOW | 0x064e | 1 | 0x21138 |
| mmUVD_LMI_MMSCH_NC7_64BIT_BAR_HIGH | 0x064f | 1 | 0x2113c |
| mmUVD_LMI_MMSCH_NC_VMID | 0x0651 | 1 | 0x21144 |
| mmUVD_LMI_MMSCH_CTRL | 0x0652 | 1 | 0x21148 |
| mmUVD_MMSCH_SOFT_RESET | 0x0654 | 1 | 0x21150 |
| mmUVD_LMI_ARB_CTRL2 | 0x0662 | 1 | 0x21188 |
