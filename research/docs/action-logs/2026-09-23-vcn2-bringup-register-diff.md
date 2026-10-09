# VCN 2.0 bring-up register sequence vs. BC-250 community replay — static diff

Date: 2026-09-23. Scope: read-only source analysis. No hardware touched, no flashing.
Purpose: name the concrete _untested_ steps between what a working VCN 2.0 (Navi10-class,
the same IP the BC-250 aliases via `navi10_vcn.bin`) does at power-up and what the BC-250
community has already replayed. This is source analysis, not proof of hardware behaviour.

## Sources (all local, byte-exact kernel copies)

- `drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c` — modern copy (2212 lines, `amdgpu_vcn_inst`-era):
  `/home/OWNER/orca/projects/bc250/import/from-windows/Users/kukuruza/tmp_bc250/recon/vcn-source-context/drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c`
- `vcn/vcn_2_0_0_offset.h`, `vcn/vcn_2_0_0_sh_mask.h`, `mmhub/mmhub_2_0_0_offset.h` (linux-v5.10):
  `/home/OWNER/orca/projects/projector/firmware-analysis/forum-1117702-2026-09-20/runs/kernel_patch_research_20260920T193000Z/linux-v5.10/drivers/gpu/drm/amd/include/asic_reg/`
- `amdgpu_discovery.c` upstream-era copy: `.../recon/amdgpu_discovery.c` (VCN switch at :2886-2900,
  Cyan Skillfish chip case at :3281-3312). Community-patched copy: `.../recon/vcn-probe-new/drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c`
  (:2667-2688) and `.../vcn-probe-new/.../amdgpu_vcn.c` (`amdgpu_vcn_fw_is_psp`, :102-111).
- `mmhub_v2_0.c` (linux-v5.10, same tree as the headers) for the MMHUB VM-context functions.
- Community data (treated as data, not verified): `memory/firmware-audit.md` L1640-1660 (dmoraza PS5 flow, rxl replay).

## Address conventions used below

Every VCN register is written as `NAME (seg-off, BASE_IDX) -> abs`:

- `seg-off` = the `#define mmNAME` value in `vcn_2_0_0_offset.h`. This is what the driver adds to
  `adev->reg_offset[VCN_HWIP][0][BASE_IDX]` (macro `SOC15_REG_OFFSET`). **Authoritative.**
- `abs` = register-space **dword** index derived from the header's `// base address:` addressBlock
  comment: `abs = block_base + (seg-off - first_seg_off_in_block)`. Three blocks matter:
  `uvd0_uvd_pg_dec` base `0x1f800` (first off `0x0000`), `uvd0_uvddec` base `0x1ff00` (first off
  `0x01c0`), `uvd0_uvdnpdec` base `0x20700` (first off `0x0580`). Byte address = `abs * 4`.
- The full SMN address on the BC-250 = `VCN0_SMN_base + abs`. `VCN0_SMN_base` comes from IP
  discovery at runtime (Navi-class has no static table in `nv.c`), so it is **not resolvable
  statically**. It is a constant the community already has if any VCN SMN read ever returned
  non-`0xffffffff`; treat `abs` as the offset to add.

Everything below is executed by `vcn_v2_0_start()` (non-DPG path, `vcn_v2_0.c:1006`) and the
helpers it calls. The BC-250 has no `AMD_PG_SUPPORT_VCN_DPG`, so the DPG (`start_dpg_mode`)
path is not the relevant one.

## 1. Ordered working-card sequence (vcn_v2_0_start, non-DPG)

### (0) Pre-VCN: SMU/DPM and doorbell (outside VCN MMIO)

| #   | Action                                                                                      | Where                  | Register                                         |
| --- | ------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------ |
| 0.1 | `amdgpu_dpm_enable_vcn(adev, true, 0)` — ask SMU to power the VCN domain / ungate VCLK+DCLK | `vcn_v2_0_start:1015`  | SMU message (PowerUpVcn), **not** a VCN MMIO reg |
| 0.2 | `nbio->vcn_doorbell_range(adev, use_doorbell, doorbell_index, 0)`                           | `vcn_v2_0_hw_init:293` | NBIO doorbell-range reg (nbio_v2_3 on Navi10)    |

0.1 is the _precondition_ for everything below. Without it, the PGFSM writes in (a) are to a
block whose rails/clocks are off and the reads return `0xffffffff`.

### (a) Static power-gating disable — `vcn_v2_0_disable_static_power_gating` (:765)

Executed only when `pg_flags & AMD_PG_SUPPORT_VCN`. Navi10 sets that flag, so the `if` branch is
the working-card path.

| #   | Write | Register (seg-off, IDX) -> abs              | Value / mask                                                                                                            |
| --- | ----- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| a.1 | W     | `UVD_PGFSM_CONFIG` (0x0000, 1) -> `0x1f800` | UVDM=1, UVDU=1, UVDF/UVDC/UVDB/UVDIL/UVDIR/UVDTD/UVDTE/UVDE = 2 (2-bit fields, per-tile: 1 = power-up, 2 = leave gated) |
| a.2 | poll  | `UVD_PGFSM_STATUS` (0x0001, 1) -> `0x1f801` | wait until masked value == `UVD_PGFSM_STATUS__UVDM_UVDU_PWR_ON_2_0`, mask `0xFFFFF`                                     |
| a.3 | RMW   | `UVD_POWER_STATUS` (0x0004, 1) -> `0x1f804` | `data &= ~0x103` (clears `UVD_POWER_STATUS[1:0]` and `UVD_PG_EN` bit8), then `\|= UVDM_UVDU_PWR_ON \| UVD_PG_EN_MASK`   |

`UVD_POWER_STATUS` field map (`sh_mask.h:1510-1523`): `UVD_POWER_STATUS[1:0]` bit0-1 (0 = powered
on), `UVD_PG_MODE` bit2, `UVD_CG_MODE` [5:4], `UVD_PG_EN` bit8, `RBC_SNOOP_DIS` bit9,
`SW_RB_SNOOP_DIS` bit11, `STALL_DPG_POWER_UP` bit31.

### (b) Busy flag + clock-gating disable

| #    | Write | Register -> abs                              | Value                                                                                                   |
| ---- | ----- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| b.1  | RMW   | `UVD_STATUS` (0x026f, 1) -> `0x1ffaf`        | `\|= UVD_STATUS__UVD_BUSY` (`vcn_v2_0_start:1024`)                                                      |
| b.2  | RMW   | `UVD_CGC_CTRL` (0x01ec, 1) -> `0x1ff2c`      | set `DYN_CLOCK_MODE` (if MGCG) , `CLK_GATE_DLY_TIMER=1`, `CLK_OFF_DELAY=4` (`disable_clock_gating:557`) |
| b.3  | RMW   | `UVD_CGC_GATE` (0x01ea, 1) -> `0x1ff2a`      | clear SYS/UDEC/MPEG2/REGS/RBC/LMI_MC/LMI_UMC/IDCT/MPRD/MPC/LBSI/LRBBM/UDEC_RE/CM/IT/DB/MP/WCB/VCPU/SCPU |
| b.4  | RMW   | `UVD_CGC_CTRL` -> `0x1ff2c`                  | clear all `*_MODE` bits (same list)                                                                     |
| b.5  | RMW   | `UVD_SUVD_CGC_GATE` (0x05a4, 1) -> `0x20724` | **set** SRE/SIT/SMP/SCM/SDB/…/IME_HEVC                                                                  |
| b.6  | RMW   | `UVD_SUVD_CGC_CTRL` (0x05a6, 1) -> `0x20726` | clear SRE/SIT/SMP/SCM/SDB/SCLR/UVD_SC/ENT/IME/SITE `_MODE`                                              |
| b.7  | RMW   | `UVD_VCPU_CNTL` (0x0258, 1) -> `0x1ff98`     | `\|= CLK_EN` (`:1031`)                                                                                  |
| b.8  | RMW   | `UVD_MASTINT_EN` (0x0200, 1) -> `0x1ff40`    | `&= ~VCPU_EN` (`:1035`)                                                                                 |
| b.9  | RMW   | `UVD_LMI_CTRL` (0x0226, 1) -> `0x1ff66`      | `\|= WRITE_CLEAN_TIMER_EN \| MASK_MC_URGENT \| DATA_COHERENCY_EN \| VCPU_DATA_COHERENCY_EN` (`:1039`)   |
| b.10 | RMW   | `UVD_MPC_CNTL` (0x0237, 1) -> `0x1ff77`      | `REPLACEMENT_MODE=2` (`:1047`)                                                                          |
| b.11 | W     | `UVD_MPC_SET_MUXA0`, `MUXB0`, `MPC_SET_MUX`  | VARA/VARB 1..4, SET 0/1/2 (`:1053-1071`)                                                                |

### (c) MC / firmware window programming — `vcn_v2_0_mc_resume` (:386)

PSP-load (working-card/PS5) branch shown. All `BASE_IDX 1`. **BC-250 divergence:** the
community patch's `amdgpu_vcn_fw_is_psp()` returns `false` for device `0x13fe` in PROBE/HARDWARE
mode, so on the BC-250 `mc_resume` takes the _`else`_ branch instead: `CACHE_64BIT_BAR` <-
`vcn.inst->gpu_addr` (a GTT/VRAM BO, not the PSP TMR) and `VCPU_CACHE_OFFSET0` <-
`AMDGPU_UVD_FIRMWARE_OFFSET >> 3` (see section 5).

| #   | Register -> abs                                                                                                      | Value                                                      |
| --- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| c.1 | `UVD_LMI_VCPU_CACHE_64BIT_BAR_LOW/HIGH` (0x061f/0x061e) -> `0x2079f/0x2079e` (note: HIGH sits one dword _below_ LOW) | `ucode[VCN].tmr_mc_addr_lo/hi` (PSP TMR address of VCN fw) |
| c.2 | `UVD_VCPU_CACHE_OFFSET0` (0x0242) -> `0x1ff82`                                                                       | 0                                                          |
| c.3 | `UVD_VCPU_CACHE_SIZE0` (0x0243) -> `0x1ff83`                                                                         | page-aligned fw size + 4                                   |
| c.4 | `UVD_LMI_VCPU_CACHE1_64BIT_BAR_LOW/HIGH`, `CACHE_OFFSET1`=0, `CACHE_SIZE1`=`AMDGPU_VCN_STACK_SIZE`                   | stack window                                               |
| c.5 | `UVD_LMI_VCPU_CACHE2_64BIT_BAR_LOW/HIGH`, `CACHE_OFFSET2`=0, `CACHE_SIZE2`=`AMDGPU_VCN_CONTEXT_SIZE`                 | context window                                             |
| c.6 | `UVD_LMI_VCPU_NC0_64BIT_BAR_LOW/HIGH`, `VCPU_NONCACHE_OFFSET0`=0, `VCPU_NONCACHE_SIZE0`=sizeof(fw_shared)            | fw_shared non-cache window                                 |
| c.7 | `UVD_GFX10_ADDR_CONFIG` (0x004a, 1) -> `0x1f84a`                                                                     | `gb_addr_config`                                           |

### (d) VCPU release / LMI soft-reset — `vcn_v2_0_start` :1075-1093

| #   | Write | Register -> abs                              | Value                                                                                      |
| --- | ----- | -------------------------------------------- | ------------------------------------------------------------------------------------------ |
| d.1 | RMW   | `UVD_SOFT_RESET` (0x0260, 1) -> `0x1ffa0`    | `&= ~VCPU_SOFT_RESET` (release VCPU to boot)                                               |
| d.2 | RMW   | `UVD_LMI_CTRL2` (0x01fd, 1) -> `0x1ff3d`     | `&= ~STALL_ARB_UMC` (enable LMI MC/UMC channels)                                           |
| d.3 | RMW   | `UVD_SOFT_RESET` -> `0x1ffa0`                | `&= ~(LMI_SOFT_RESET \| LMI_UMC_SOFT_RESET)`                                               |
| d.4 | W     | `UVD_LMI_SWAP_CNTL` (0x022d, 1) -> `0x1ff6d` | 0                                                                                          |
| d.5 | poll  | `UVD_STATUS` -> `0x1ffaf`                    | wait `bit1` set (VCPU booted). 10×100×10 ms; on timeout toggle `VCPU_SOFT_RESET` and retry |

Note: no **cold** reset appears anywhere in `vcn_v2_0.c`. The only reset the driver touches is
`UVD_SOFT_RESET` (block-internal). The PSP/SMU is assumed to have already deasserted the RSMU
cold reset and powered the rail before the driver runs — this is the step dmoraza's
`0x0900c004<-1` (`RSMU_COLD_RESETB_VCN`) corresponds to, and it is _below_ the driver.

### (e) MMHUB / VM side

`vcn_v2_0.c` itself performs **no** MMHUB writes. What it does do:

- `ring->vm_hub = AMDGPU_MMHUB0(0)` for dec and both enc rings (`sw_init:177, :208`) — the VCN is
  an MMHUB0 client.
- `UVD_LMI_RBC_RB_VMID` (0x0263, 1) -> `0x1ffa3` = 0 (`:1133`) — ring VMID 0.
- `UVD_LMI_VCPU_CACHE_VMID` (0x01fc, 1) -> `0x1ff3c` — only in the DPG path.

The MMHUB side that a working card must already have done (in `gmc_v10_0_hw_init` ->
`mmhub_v2_0_gart_enable`, called _before_ the VCN IP block's hw_init in the SOC15 ip-block order):

| Function                                       | Registers (mmhub_2_0_0_offset.h, all BASE_IDX 0)                                                                                                                  |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mmhub_v2_0_init_gart_aperture_regs`           | `MMVM_CONTEXT0_PAGE_TABLE_BASE_ADDR_LO32/HI32` (0x072b/0x072c), `..._START_ADDR_LO32/HI32` (0x074b/…), `..._END_ADDR_*`                                           |
| `mmhub_v2_0_init_system_aperture_regs`         | `MMMC_VM_AGP_BASE/BOT/TOP`, `MMMC_VM_SYSTEM_APERTURE_LOW/HIGH_ADDR`, `MMMC_VM_SYSTEM_APERTURE_DEFAULT_ADDR_LSB/MSB`, `MMMC_VM_L2_PROTECTION_FAULT_DEFAULT_ADDR_*` |
| `mmhub_v2_0_init_tlb_regs` / `init_cache_regs` | `MMMC_VM_MX_L1_TLB_CNTL`, `MMVM_L2_CNTL..CNTL5`                                                                                                                   |
| `mmhub_v2_0_enable_system_domain`              | `MMVM_CONTEXT0_CNTL` (0x06c0) <- `ENABLE_CONTEXT=1, PAGE_TABLE_DEPTH=0, RETRY_PERMISSION_OR_INVALID_PAGE_FAULT=0`                                                 |
| `mmhub_v2_0_setup_vmid_config`                 | `MMVM_CONTEXT1..15_CNTL` (0x06c1…), `..._PAGE_TABLE_START/END/BASE_ADDR_*` per VMID                                                                               |
| `mmhub_v2_0_program_invalidation`              | `MMVM_INVALIDATE_ENG0..17_ADDR_RANGE_LO32/HI32`                                                                                                                   |

"MMHUB VM activation x2" in the dmoraza trace is most plausibly the pair
`enable_system_domain` (context 0) + `setup_vmid_config` (contexts 1..15), i.e. two
`MMVM_CONTEXTn_CNTL` enable writes. `MMVM_CONTEXTS_DISABLE` (0x06d0) is the global gate.

### (f) Status / interrupt

| #   | Write | Register -> abs               | Value                                                 |
| --- | ----- | ----------------------------- | ----------------------------------------------------- |
| f.1 | RMW   | `UVD_MASTINT_EN` -> `0x1ff40` | `\|= VCPU_EN` (`:1123`)                               |
| f.2 | RMW   | `UVD_STATUS` -> `0x1ffaf`     | `&= ~(2 << VCPU_REPORT_SHIFT)` — clear busy (`:1128`) |

### (g) Ring / doorbell init (`:1133-1182`)

| #   | Register -> abs                                                                           | Value                                                                             |
| --- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| g.1 | `UVD_LMI_RBC_RB_VMID` (0x0263) -> `0x1ffa3`                                               | 0                                                                                 |
| g.2 | `UVD_RBC_RB_CNTL` (0x0269) -> `0x1ffa9`                                                   | `RB_BUFSZ=log2(size), RB_BLKSZ=1, RB_NO_FETCH=1, RB_NO_UPDATE=1, RB_RPTR_WR_EN=1` |
| g.3 | `UVD_LMI_RBC_RB_64BIT_BAR_LOW/HIGH` (0x0629/0x0628) -> `0x207a9/0x207a8` (HIGH below LOW) | dec ring GPU VA                                                                   |
| g.4 | `UVD_RBC_RB_RPTR` (0x0264) -> `0x1ffa4`                                                   | 0 ; `UVD_RBC_RB_WPTR` (0x0265) -> `0x1ffa5` = rptr                                |
| g.5 | `UVD_RB_RPTR/WPTR/BASE_LO/BASE_HI/SIZE`                                                   | enc ring 0                                                                        |
| g.6 | `UVD_RB_RPTR2/WPTR2/BASE_LO2/BASE_HI2/SIZE2`                                              | enc ring 1                                                                        |
| g.7 | final `RREG32 UVD_STATUS`                                                                 | read-back fence                                                                   |

Doorbell path: `WDOORBELL32(ring->doorbell_index, wptr)` (`dec_ring_set_wptr:1471`) — this is the
NBIO doorbell BAR, enabled by (0.2), not a VCN register.

## 2. What is "0x7fec"?

Community trace: after "MMHUB VM activation x2" -> _read `0x7fec`, clear bit 0_ -> VCN_INIT
(`UVD_POWER_STATUS`, `UVD_STATUS`, `SOFT_RESET`, fw/MC, rings).

Three decodes were tested against `vcn_2_0_0_offset.h`:

| Interpretation                                  | Result                                                                                                                                                                                                                                                                                                                                                                                             | Plausibility                                                   |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| byte offset -> dword `0x1ffb` (= `0x7fec >> 2`) | `0x1ffb` lands in `uvd0_uvddec` at seg-off `0x1c0 + 0xfb = 0x02bb` = **`mmUVD_UVBASE`** (`offset.h:790`) — a decode-surface chroma base register                                                                                                                                                                                                                                                   | **Implausible** as an enable gate; its bit0 is an address bit. |
| dword offset `0x7fec`                           | no VCN, MMHUB(1.0/2.0), GC or MP register defined at `0x7fec`; only DCE/DCN hits at `0x1ffb` (`FMT2_CRC`, `DP_AUX6`)                                                                                                                                                                                                                                                                               | no                                                             |
| `UVD_POWER_STATUS` alias                        | functionally exact: bit0 of `UVD_POWER_STATUS` (abs `0x1f804`, byte `0x7e010`) is `UVD_POWER_STATUS[1:0]`'s LSB, and `disable_static_power_gating` does `data &= ~0x103` — literally "clear bit 0 (and 1 and 8)" as the first thing after PGFSM power-on and immediately before the `UVD_STATUS`/`SOFT_RESET`/MC/ring block. Numerically **`0x7fec != 0x7e010`** and no VCN0 base makes them meet. | Semantics match, address does not                              |

**Most plausible reading:** `0x7fec` is _not_ a register in the VCN UVD register file at all. It
is a small SMN-relative address in the same low aperture family as the other non-VCN strobes in
the trace (`0x0001f8a4`, `0x1f8c4..0x1f8d4` — the SMU per-domain program; `0x0900c004` — RSMU
cold reset). Its position (after the MMHUB VM contexts are enabled, before any VCN MMIO is
touched, and the VCN aperture is dead until it is done) and its shape (read, clear one bit,
write back) fit an **isolation / clamp-release or "aperture enable" bit** on the SMU/RSMU or
NBIO side, the same class as `RSMU_COLD_RESETB_VCN`. If it were the `UVD_POWER_STATUS` RMW, it
would be part of the driver's own sequence and would be reachable through the aperture — which
is exactly what the trace says is _not yet_ true at that point.

Honest statement: the numeric identity of `0x7fec` cannot be resolved from the public
`vcn_2_0_0` / `mmhub_2_0_0` headers. It needs either the PS5 trace's address-space annotation or
an SMN read on a working Navi10/Cyan-Skillfish part. Do not assume it is `UVD_POWER_STATUS`.

## 3. rxl's replay vs the working-card sequence

### What rxl did (community data)

1. `0x0900c004 = 1` via SMU fw-window — `RSMU_COLD_RESETB_VCN` deassert. Corresponds to the
   _pre-driver_ cold-reset release (section 1(d) note). Correctly placed.
2. Five SMN writes `{0x0902F914=0x1FFF, 0x0902F920=0x107, 0x0902F92C=0x2FF, 0x0902F930=0x36,
0x0902F934=0x00}` from table @`0x00e188d8`.

### What the 0x0902F9xx table most plausibly is

- Aperture: `0x0902_xxxx` is a sibling of `0x0900_xxxx` (RSMU). These are **not** UVD
  register-file addresses (`0x1e200..0x211ff` dword / `0x78800..0x847ff` byte + VCN0 base) —
  they are in the RSMU/power-controller aperture.
- Value shapes: `0x1FFF` (13 bits set), `0x107`, `0x2FF`, `0x36`, `0x00` — bit-vectors of
  per-tile enables, the same shape as `UVD_PGFSM_CONFIG`'s ten 2-bit tile fields and the per-domain
  program the PSP t28 body runs (`memory/firmware-audit.md`: write 1 -> `0x1F8A4`, then five
  regs `0x1F8C4/C8/CC/D0/D4`). The two decodes (t28 = `0x1F8xx`, rxl = `0x0902F9xx`) are the same
  5-entry table read through two different base assumptions; the project has not reconciled
  which base is correct.
- Functional slot: this is the **SMU/RSMU-side equivalent of section 1(a)** (static
  power-gating disable / PGFSM tile power-on) plus the SMU `PowerUpVcn` of step 0.1 — the part of
  the sequence that a working card's PSP does before the OS driver ever runs.

So rxl covered: **step 0.1 (SMU-side power) and the pre-driver cold-reset release, and the
SMU-side analogue of 1(a).** He did **not** cover anything from 1(e) onward, and specifically not
the two items the working trace inserts _between_ the power-domain table and `VCN_INIT`.

### Untested steps (working card does, BC-250 has not)

| #   | Step                                                                                                                                                                              | Working-card source                                                   | Status on BC-250                                                                 |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| U1  | MMHUB VM activation ×2 — enable `MMVM_CONTEXT0_CNTL` (0x06c0) + `MMVM_CONTEXT1..15_CNTL` for the VCN's MMHUB0, with page-table base/start/end and `MMVM_CONTEXTS_DISABLE` cleared | `mmhub_v2_0_gart_enable` (gmc_v10_0_hw_init), runs before vcn hw_init | **untested**                                                                     |
| U2  | read `0x7fec`, clear bit 0                                                                                                                                                        | not in `vcn_v2_0.c`; PS5-trace only                                   | **untested**                                                                     |
| U3  | `UVD_PGFSM_CONFIG` <- tile config, poll `UVD_PGFSM_STATUS` (1(a).1-2)                                                                                                             | `disable_static_power_gating`                                         | untested via VCN MMIO (rxl's table may be the RSMU-side equivalent — unverified) |
| U4  | `UVD_POWER_STATUS` RMW `&= ~0x103; \|= PWR_ON \| PG_EN` (1(a).3)                                                                                                                  | same                                                                  | untested                                                                         |
| U5  | `UVD_STATUS \|= BUSY`, CGC/SUVD CGC disable, `VCPU_CNTL.CLK_EN`, `MASTINT_EN` off, `LMI_CTRL`, `MPC_*` (1(b))                                                                     | `disable_clock_gating` + `start`                                      | untested                                                                         |
| U6  | MC windows: `VCPU_CACHE*`, `NC0`, `GFX10_ADDR_CONFIG` (1(c))                                                                                                                      | `mc_resume`                                                           | untested                                                                         |
| U7  | `SOFT_RESET` release VCPU, `LMI_CTRL2` unstall, `LMI_SWAP_CNTL`, poll `UVD_STATUS` bit1 (1(d))                                                                                    | `start`                                                               | untested                                                                         |
| U8  | `MASTINT_EN` on, `UVD_STATUS` clear-busy, ring regs (1(f)-(g))                                                                                                                    | `start`                                                               | untested                                                                         |
| U9  | NBIO `vcn_doorbell_range` (0.2)                                                                                                                                                   | `hw_init`                                                             | untested                                                                         |

U3-U9 are all the _driver-side_ sequence and are all blocked by the aperture (`0xffffffff`).
U1 and U2 are the only two steps that (per the trace) happen _before_ the aperture is usable
and are therefore the candidate "second gate".

## 4. Reachability of each untested step from the SMN side

Only write primitive: SMU-privileged arbitrary SMN write (Q3 msg `0x98` / fw-window
`smn_write32`, 20-bit-limited on the PMFW path). VCN MMIO/UMR/debugfs hang; host PCI-config SMN
hangs.

| Step                         | Register class                                           | SMN-reachable without the VCN aperture?                                                                                                                                                                                                                                                                | Notes                                                                                                                                                                                                      |
| ---------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| U1 MMHUB VM contexts         | MMHUB0 register file (`MMVM_*`, `MMMC_VM_*`, BASE_IDX 0) | **Yes, plausibly.** MMHUB is a separate IP with its own SMN aperture; it is live (the GPU renders, so MMHUB0 GART is up for GFX). The question is only whether the _VCN client's_ VMID contexts / `MMVM_CONTEXTS_DISABLE` need touching, not whether MMHUB responds.                                   | 20-bit limit: MMHUB SMN base on Navi is above `0xFFFFF` in byte terms, so the PMFW-path write may not reach it; the `0x98` message path (if truly 32-bit) would. **First thing to try from the SMU side.** |
| U2 `0x7fec` bit0             | unknown; low SMN address                                 | **Yes** — `0x7fec` is within 20 bits, so even the limited PMFW path reaches it. Read-modify-write is possible only if the SMU path also offers a read (fw-window read is available per rxl's "read 0x1F8A4").                                                                                          | Highest-value single test: it is cheap, reachable, and is the one step in the trace immediately preceding "VCN aperture responds".                                                                         |
| U3 `UVD_PGFSM_CONFIG/STATUS` | VCN register file (`0x1f800/1`)                          | **Only if the SMN view of the VCN register file responds when the MMIO view does not.** Same block — if MMIO is `0xffffffff` because the block is isolated, SMN gets the same. If MMIO is `0xffffffff` because the _host BAR aperture_ is masked (NBIO/PSP-side), SMN could still work. Unknown which. | Test by SMN-reading `0x1f804` (`UVD_POWER_STATUS`, + VCN0 base): non-`0xffffffff` ⇒ the gate is on the host BAR, not the block. Diagnostic, not a fix.                                                     |
| U4 `UVD_POWER_STATUS`        | same                                                     | same as U3                                                                                                                                                                                                                                                                                             |                                                                                                                                                                                                            |
| U5-U8 driver init            | same                                                     | same as U3 — and in practice pointless by SMN (hundreds of writes, polls) once the aperture is open the driver does it.                                                                                                                                                                                | Chicken-and-egg: the _goal_ is to make these reachable via MMIO.                                                                                                                                           |
| U9 NBIO doorbell range       | NBIO register file                                       | **Yes** (NBIO is live). Irrelevant until the block boots.                                                                                                                                                                                                                                              | Not a gate.                                                                                                                                                                                                |
| 0.1 SMU `PowerUpVcn`         | SMU message                                              | Yes — the `0x0902F9xx` table / `msg 0x60` wedge is this.                                                                                                                                                                                                                                               | Already attempted; rxl's wedges on `msg 0x60` and feature bit17 are the SMU refusing this.                                                                                                                 |

**Flagged as doable from the SMU side, no aperture needed:** U2 (`0x7fec` bit0 clear) and U1
(MMHUB VM context enables), in that order of cost. Both should be preceded by a diagnostic SMN
read of `VCN0_base + 0x1f804` to learn whether the block or the BAR is what is gated.

## 5. Upstream vs community kernel: what actually instantiates VCN on the BC-250

This was not in the task brief but fell out of resolving the Cyan Skillfish binding, and it
matters for the "software lock" thesis.

**Upstream amdgpu adds no VCN IP block for Cyan Skillfish.** In
`amdgpu_discovery.c` (`amdgpu_discovery_set_mm_ip_blocks`, `switch (vcn_version)`):

```c
case IP_VERSION(2, 0, 0):
case IP_VERSION(2, 0, 2):
case IP_VERSION(2, 2, 0):
        amdgpu_device_ip_block_add(adev, &vcn_v2_0_ip_block);   /* + jpeg_v2_0 */
        break;
case IP_VERSION(2, 0, 3):
        break;                                                  /* Cyan Skillfish: nothing */
```

So on a stock kernel `vcn_v2_0_start()` never runs on this chip — the driver opts out before
touching a single VCN register. This is a _policy_ decision in the OS driver, not evidence of a
fuse. The same file's `CHIP_CYAN_SKILLFISH` case sets `ip_versions[UVD_HWIP][0] = IP_VERSION(2,0,3)`
(:3310) and, for the `AMD_APU_IS_CYAN_SKILLFISH2` variant, uses `amdgpu_discovery_reg_base_init`
(runtime IP discovery); the non-2 variant calls `cyan_skillfish_reg_base_init()` (static table —
the local `recon/cyan_skillfish.c` copy is 0 bytes, so its VCN base was not recoverable here).

**The community kernel adds it back behind a BC-250-only switch** (patched
`amdgpu_discovery.c:2667-2688`): for `pdev->device == 0x13fe` a module parameter
`amdgpu_bc250_vcn_mode` selects `OFF` / `PROBE` (`vcn_v2_0_probe_ip_block`) / `HARDWARE`
(`vcn_v2_0_ip_block` + `jpeg_v2_0_ip_block`). In PROBE/HARDWARE mode `amdgpu_vcn_fw_is_psp()`
returns `false` (patched `amdgpu_vcn.c:102-111`), forcing **direct (non-PSP) firmware load**.

Consequences for the diff:

- "BC-250 aliases `navi10_vcn.bin`" is a property of the community patch, not of upstream.
- With non-PSP load, the working card's PSP-TMR path in section 1(c) is _not_ what the BC-250
  runs; it programs the VCPU cache BARs to a driver-allocated BO. On Navi10/PS5 the PSP both
  authenticates the VCN fw and, more importantly here, has already done the RSMU cold-reset /
  rail power-up (`0x0900c004`, `0x1f8a4`, the 5-table) before the OS driver starts. The BC-250
  community kernel therefore enters `vcn_v2_0_start()` with **none** of the pre-driver steps
  done, which is exactly the state in which every VCN read returns `0xffffffff`.
- This strengthens the reading in section 3: the SMU/PSP-side pre-steps are the whole gate, and
  rxl's replay reproduced the first two of them (cold reset + power table) but not the two that
  follow (U1, U2).

## 6. Ambiguities and Navi10-vs-Cyan-Skillfish caveats

1. **No cold reset in the driver.** `vcn_v2_0.c` never touches an RSMU or cold-reset register;
   the only resets are `UVD_SOFT_RESET` bits. The PSP/SMU owns cold reset and rail power on every
   VCN 2.x part. Therefore the diff between "driver sequence" and "PS5 trace" is expected to
   contain PSP-only steps (`0x0900c004`, `0x1f8a4`, the 5-table, `0x7fec`), and their absence
   from `vcn_v2_0.c` is not evidence that they are Cyan-Skillfish-specific.
2. **`0x7fec` unresolved** (section 2). The byte-offset decode gives `UVD_UVBASE`, which is
   almost certainly wrong; the functional decode gives `UVD_POWER_STATUS`, which is numerically
   wrong. Treat it as an unknown low-SMN gate.
3. **VCN0 SMN base is not resolvable here.** For the `AMD_APU_IS_CYAN_SKILLFISH2` variant
   `reg_offset[VCN_HWIP]` comes from runtime IP discovery; for the other variant it comes from
   `cyan_skillfish_reg_base_init()`, whose local copy (`recon/cyan_skillfish.c`) is empty. Every
   `abs` above therefore needs `+ VCN0_base`. The header `// base address` comments (`0x1f800`
   etc.) are the canonical register-space dwords and were used for `abs`; they are consistent
   with the three-block model but the model itself is inferred from the header layout, not
   from a discovery dump.
4. **Cyan Skillfish is VCN 2.0.3, header is 2.0.0, and the binding is a patch.** Upstream
   adds no VCN block for 2.0.3 (section 5). The community patch binds it to `vcn_v2_0_ip_block`
   and `navi10_vcn.bin`, so the _register program_ is the one in section 1 — but with the
   non-PSP `mc_resume` branch. The per-tile PGFSM layout and `pg_flags` may still differ (the
   APU may not set `AMD_PG_SUPPORT_VCN`, which would select the `else` branch of
   `disable_static_power_gating`: all tiles `=1`, poll `PGFSM_STATUS == 0`). The BC-250
   firmware's VCN harvest/disable choice is not visible in this source.
   4b. **`UVD_PGFSM_STATUS__UVDM_UVDU_PWR_ON_2_0`** is the poll target used at
   `disable_static_power_gating:788`, but its `#define` was not found in any local header or
   `vcn_v2_0.h` copy; its numeric value is therefore not stated here.
5. **The 5-entry table decode is unreconciled.** rxl's `0x0902F9xx` and the t28 `0x1F8xx` decode
   are the same table under different bases. Which one the hardware actually decodes is not
   established; the values (`0x1FFF,0x107,0x2FF,0x36,0x00`) are only _shaped like_ PGFSM/domain
   masks. This document does not assert they are `UVD_PGFSM_CONFIG`.
6. **"MMHUB VM activation x2" is an inference.** `vcn_v2_0.c` has no MMHUB writes; the ×2 was
   mapped to `enable_system_domain` + `setup_vmid_config` because those are the two
   `MMVM_CONTEXTn_CNTL` enable sites in `mmhub_v2_0_gart_enable`. The trace may mean two
   invalidation engines or two hubs instead.
7. **20-bit PMFW write limit** (rukkusireland) may exclude MMHUB and VCN register-file SMN
   addresses; only `0x7fec` and the `0x1f8xx` family are certainly inside it. Whether the `0x98`
   message path is truly 32-bit is a community claim, not verified here.
8. **Static analysis only.** Nothing here demonstrates hardware behaviour. The strongest
   claim this document supports is: the two steps in the working trace that rxl skipped (MMHUB VM
   activation, `0x7fec` bit0 clear) are both plausibly SMN-reachable without the VCN aperture, and
   are the correct next tests.
