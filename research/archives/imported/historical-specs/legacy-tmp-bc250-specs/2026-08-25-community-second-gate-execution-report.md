# BC-250 VCN — Community continuation: clock gate cleared, root isolation remains

**Date:** 2026-08-25  
**Board:** `steammachine` / BIOS `P3.00` / PMFW `0x580600` / kernel `7.2.0-1.1-cachyos-bc250`  
**Mode:** volatile SMU SRAM/register experiments. Cold power-cycle restores factory state.

## Verified outcome

Community clock work reproduced and extended:

- SMU secure debug cluster opened successfully.
- Domain-6 control register `0x06d0f8` changed `0x02 -> 0x00` and persisted in the SMU session.
- Slots `0x16`, `0x17`, `0x18` were reprogrammed through `FUN_00023744` and enabled (`+0x08 = 1`).
- Slot `0x17` changed from clock value `0` to `32`.
- `gpu_metrics` changed from `VCLK=0` to **`VCLK=625 MHz`**; `DCLK=1111 MHz` remained active.
- SMU remained alive and responsive throughout.

This clears the **clock portion** of the community's second gate. It does not clear the final VCN register-file isolation.

## Native domain-6 power transition

The full live PMFW SRAM was dumped and disassembled. Cross-domain descriptor evidence resolves the state semantics:

- Domain descriptors 0–6 use state byte `1` and powered status pattern `0x01010101`.
- Domain 7 uses state byte `0` and the down pattern.
- Therefore `FUN_00023b14(domain, 1)` is the native ON transition; `FUN_00023b14(domain, 0)` is OFF.
- `FUN_00024764` is the domain-6 teardown wrapper: it programs slots `0x16`–`0x18`, then calls `FUN_00023b14(6,0)`. It is not a power-up wrapper.

To bypass the firmware's early return, the domain-6 state byte was temporarily forced `1 -> 0`, then a verified Xtensa thunk called `FUN_00023b14(6,1)`:

```text
state_before=0x00010101
state_forced=0x00010100
fire=FUN_00023b14(6,1)
smu_alive_after=true
state_after=0x00010101
transition=1->1
cleanup=ok
```

Result: the complete native PMFW ON path executed and restored state `1`, without wedging the SMU.

Evidence: `tmp_bc250/recon/force_native_domain6_on_2026-08-25.out`.

## Direct-load result

After the real native ON transition:

- `navi10_vcn.bin` was parsed and stripped to 404288 bytes of ucode.
- A clean 1052 KiB VRAM span was found at offset `0x00e00000`.
- Firmware and `fw_shared` were staged and read-back verified at MC address `0x00f400e00000`.
- The corrected identity check verified the BC-250 debugfs BDF and live 8 GiB FB range `0x00f400000000..0x00f5ffffffff`.

Before any VCN register writes or ring submission, the guarded MMIO ladder returned uniform `0xffffffff`:

```text
UVD_PGFSM_CONFIG      0xffffffff
UVD_PGFSM_STATUS      0xffffffff
UVD_POWER_STATUS      0xffffffff
CC_UVD_HARVESTING     0xffffffff
UVD_STATUS            0xffffffff
UVD_VERSION           0xffffffff
UVD_JPEG_CNTL         0xffffffff
UVD_JRBC_STATUS       0xffffffff
```

The tool aborted safely. No VCN register programming, VCPU reset release, doorbell write, or ring test occurred.

Evidence: `tmp_bc250/recon/direct_load_after_real_native_2026-08-25.out`.

## Current blocker

The remaining blocker is no longer power-domain state or media clocks:

```text
IP discovery / harvest=0             confirmed
SMU debug access                      working
Domain-6 native ON transition         executed
VCLK / DCLK                           625 / 1111 MHz
Slots 0x16–0x18                       enabled and READY
VCN firmware staged in VRAM           verified
VCN MMIO register file                root-clamped (all 0xffffffff)
VCPU boot / decoder ring              not reached
```

The evidence now points outside the replicated domain-6 PMFW sequence: NBIO/PSP-side isolation, fabric firewall/routing, or another platform handoff not represented by the domain-6 descriptor and clock slots.

## Cold-boot replay and NBIO hypothesis check

After a physical cold power-cycle, the complete sequence was replayed from stock state:

- stock `VCLK=0`, `DCLK=1111`, secure debug closed;
- slot-clock thunk restored slot `0x17` from `0` to `32` and all three slot enables to `1`;
- `--manual-powerup` changed domain control `0x06d0f8: 0x00000002 -> 0x00000000` and the change persisted;
- `VCLK=625`, `DCLK=1111`, SMU test message and version remained healthy;
- guarded direct-load staged and verified `navi10_vcn.bin`, then again observed uniform `0xffffffff` across both VCN MMIO segments, including `UVD_VERSION`;
- the staged VRAM spans were zeroed and read-back verified after the abort.

The proposed `AmdNbioGfxInit` replay is now rejected as a no-op. Before and after the VCN clock/power work, the live NBIO destinations already equal the boot firmware sources:

```text
0x13b1005c = 0x00008000    0x0006a140 = 0x00008000
0x13b10060 = 0x0000ffff    0x0006a144 = 0x0000ffff
0x13b0004c = 0x00800000    0x0006a148 = 0x00800000
                              0x0006a14c = 0x00000008
                              0x000033e0 = 0x00003820  (bits 1/2 already clear)
```

Therefore those AGESA copies/RMWs were already applied by BIOS P3.00 and cannot explain or release the VCN clamp. No redundant NBIO writes were issued.

Evidence:

- `tmp_bc250/recon/read_nbio_safe_targets_after_coldboot_2026-08-25.out`
- `tmp_bc250/recon/read_nbio_safe_targets_after_vcn_clock_2026-08-25.out`
- `tmp_bc250/recon/clock_enable_direct_load_after_coldboot_2026-08-25.out`

## Decisive PMFW experiment: true electrical OFF -> ON

The corrected native cycle executed successfully:

```text
before:    state=0x00010101 ctrl=0 status=0x01010101 clocks=18/32/20
after OFF: state=0x00010100 ctrl=7 status=0x01011010 clocks=0/0/0
after ON:  state=0x00010101 ctrl=0 status=0x01010101 clocks=18/32/20
```

SMU remained alive. Final `VCLK/DCLK=625/1111 MHz`. A fresh guarded MMIO ladder still returned uniform `0xffffffff` across both VCN segments, including static `UVD_VERSION`.

This closes the PMFW power-edge hypothesis: neither software-state forcing nor a genuine firmware-owned electrical OFF -> ON releases the VCN register file.

Evidence:

- `tmp_bc250/recon/native_domain6_cycle_2026-08-25.out`
- `tmp_bc250/recon/vcn_mmio_liveness_after_native_cycle_2026-08-25.out`
- `tmp_bc250/specs/2026-08-25-bc250-vcn-trusted-environment-report.md`

## Circuit breaker

Three independent approaches reached the same root clamp:

1. host-bounded manual domain-6 sequence;
2. slot-clock thunk + enable writes;
3. forced real `FUN_00023b14(6,1)` native transition.

Blind register mutation remains prohibited. PMFW power sequencing is closed. Work now moves exclusively to trusted-policy identification, a working sibling comparison, or cryptographically authorized secure debug.

## Restored state

All stopped board services were restarted and verified active:

- `bc250-metrics`
- `bc250-gpu-watchdog`
- `bc250-pwrwatch`
- `bc250-telemetry`
- `bc250-dpwatch`
- `bc250-fan`
- `bc250-netconsole`

Final live checks: board online, SMU test message OK, version `0x580600`, WGP 12, `VCLK=625`, `DCLK=1111`; all seven services active.
