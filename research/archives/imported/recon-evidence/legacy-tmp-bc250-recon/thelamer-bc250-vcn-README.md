# BC250 VCN Unlock — Findings & Resources

Working notes for bringing up the **VCN 2.0.3** media/decode block on the AMD
**BC250 "Cyan Skillfish"** blade under Linux. Silicon is present and **not
harvested**; AMD/Sony just never wired up the platform software to power and init
it. Same group already unlocked the extra CPU cores (6c → 8c) and GPU CUs via an
SMU-mailbox write primitive — VCN is next.

This is a scratch organizing doc to stop people repeating dead ends. It is
speculation + a findings list + link-outs, not a finished writeup.

---

## Current status: powered on, held by a second gate

The VCN **power domain has been switched on** from the SMU —
`FUN_00023b14(6, 1)` on **power domain 6** (SMU v3). Register state and operating
frequency confirm it; the SMU survives its hardware-acknowledge poll, so domain 6
physically acknowledged the transition. The block is now held down by a **second
gate** (clock / reset / isolation): *"VCN is gated by something else."*

> ⚠️ The earlier "triple deadlock / dead silicon" verdict is **obsolete**. That was
> before the domain-6 power-on. Power is no longer the blocker.

### Bring-up chain

| Stage | State |
|-------|-------|
| IP discovery exposes VCN 2.0.3 (harvest=0) | ✅ confirmed |
| Register `vcn_v2_0` IP block in amdgpu (Linux skips it by default) | ✅ patched |
| Get firmware past PSP (PSP rejects it, `0xffff0008`/`ITEM_NOT_FOUND`) | ⚠️ worked around via direct-load into VCN buffer |
| **Power VCN domain on** — `FUN_00023b14(6, 1)`, domain 6 | ✅ **done (new)** |
| Clear clock / reset / isolation (the "second gate") | ❌ **current blocker** |
| Decoder ring test / decode | ❌ blocked above (first ring op hangs board) |

---

## Key findings (proven & ruled out — don't repeat these)

**Proven / confirmed**
- VCN 2.0.3 is physically present, **harvest = 0** (not fused off).
- Linux `amdgpu` deliberately skips registering VCN 2.0.3 on Cyan Skillfish.
- Stock telemetry before intervention: **VCN powered down, VCLK = 0, DCLK = 1111**.
- Cyan Skillfish has **no `dpm_set_vcn_enable` callback**; generic
  `amdgpu_dpm_enable_vcn()` returns success when it's absent, so the driver *thinks*
  power-up worked and walks into VCN MMIO → hard lock.
- SMU is **SMU 11.8**, resident PMFW is **Xtensa, version 88.6.0** (extracted from
  BIOS). Central mailbox dispatcher + response ABI are reversed.
- **Domain 6 = VCN power domain** (drives VCLK/DCLK + one unknown clock); powering
  it via `FUN_00023b14(6, 1)` works. Teardown reference: `FUN_00024764` (SMU v3
  `0x00024764`) tears down domain 6 and touches slots `0x16`/`0x17`/`0x18` via
  `FUN_00023744` → `FUN_0002362c` (`soc_clk_program_slot`).
- SMU Queues 1–4 are host-reachable via PCI config `0xB8`/`0xBC`. Queue 3 msg
  **`0x98`** is an ungated SMU-privileged **arbitrary SMN write** (writes `0x00FF`
  to any SMN address) — the primitive behind the CPU core unlock; survives warm reboot.
- Direct-load firmware patch bypasses PSP auth and reaches `vcn_v2_0_hw_init()`
  (`device_fw_loading` returns 0). Proves firmware is *placed*, **not** that it *executes*.

**Ruled out — do not chase again**
- **No `PowerUpVcn`/`PowerDownVcn` message exists** in SMU 11.8. Full Ghidra
  decompile shows **zero VCN-named messages across all 7 SMU queues**. Stop looking
  for a VCN mailbox message — the working path was an SMU *internal function*, not a message.
- **Don't reuse mailbox IDs from other SMU families.** `0x8`/`0x9` = PowerDown/Up
  Vcn on SMU 11.5, but on Cyan Skillfish `0x09` is a no-op (q0/q1/q3), DRAM-table
  related (q2), or memory-controller related (q5) — **not** the VCN switch.
- Direct VCN MMIO via BAR5, UMR, and kernel SMN-via-debugfs all **hang the board**.
- PSP path is a dead end for firmware: type 13 (VCN) → `ITEM_NOT_FOUND`; type 64 →
  `TEE_SUCCESS` but a confirmed **no-op**. AMD-signed TAs *do* load (fail-open), but
  no VCN power-on was achieved through them. Hence the direct-load workaround.
- No VCN option exists in the BIOS setup / IFR; PS5 firmware is a different
  architecture and doesn't help.

## Open threads (next tests, highest-priority first)

1. **Diff VCN power/clock/reset/isolation registers before vs. after
   `FUN_00023b14(6, 1)`** — name the exact gate still asserted.
2. Check whether slots `0x16`/`0x17`/`0x18` need programming
   (`FUN_00023744` → `FUN_0002362c`) as a power-up prerequisite.
3. Trace the VCLK/DCLK enable routine; confirm clocks move from 0 after power-on.
4. Cross-reference Renoir / Van Gogh `*_dpm_set_vcn_enable` reset/isolation steps
   we haven't replicated.
5. Only after the gate clears: re-run the decoder ring test to see if firmware executes.

### Debug setup (avoids losing dmesg on hard hang)

Blacklist the driver at boot (`modprobe.blacklist=amdgpu loglevel=7 ignore_loglevel`;
Limine: `/boot/limine.conf`), SSH in, run `sudo dmesg -wH` in one session, then
`sudo modprobe amdgpu` (patched) in another and watch live. A hard hang needs a
physical reboot and won't appear in `journalctl -b -1 -k`.

> ⚠️ SMU power-domain and VCN MMIO tests can wedge the APU — only run on a box you
> can physically power-cycle.

---

## External resources

### BC250-specific — SMU / core unlock (most relevant)
| Link | Why it matters |
|------|----------------|
| [bc250-collective/amd_smu_reverse_engineering](https://github.com/bc250-collective/amd_smu_reverse_engineering) | Full Ghidra decompile of the BC250 SMU (Xtensa). All 7 queue tables. Source of the `FUN_*` addresses above. |
| [rw-r-r-0644/bc250-core-unlock](https://github.com/rw-r-r-0644/bc250-core-unlock) | CPU 6c→8c unlock; reveals Queue 3 msg `0x98` arbitrary SMN write primitive. |
| [rw-r-r-0644/bc250-smu-unlock](https://github.com/rw-r-r-0644/bc250-smu-unlock) | Arbitrary r/w + code execution on the BC250 SMU. Access/testing mechanism. |
| [rpf16rj SMU-HANDLERS.md](https://github.com/rpf16rj/bc250-steamos-real-toolkit/blob/main/external/bc250-steamos/bc250-power/SMU-HANDLERS.md) | Decoded SMU handlers Q0/Q2/Q3; feature framework (Q2_0x05, 64 feature bits w/ callbacks); Queue 2 mailbox addrs. |
| [bc250-collective/bc250_smu_oc](https://github.com/bc250-collective/bc250_smu_oc) | Userspace OC tool using Queue 3 via PCI config `0xB8`/`0xBC` — confirms queue accessibility. |
| [RescueMei/BC250-DXE-SMU-Core-Unlock](https://github.com/RescueMei/BC250-DXE-SMU-Core-Unlock) | Alternative core-unlock impl, same `0x98` primitive. |
| [leogx9r/ryzen_smu](https://github.com/leogx9r/ryzen_smu) ([GitLab](https://gitlab.com/leogx9r/ryzen_smu)) | SMU access kernel driver — **lacks Cyan Skillfish support**, would need adding. |

### BC250 BIOS / firmware / docs
| Link | Why it matters |
|------|----------------|
| [elektricm AMD BC250 docs — BIOS flashing](https://elektricm.github.io/amd-bc250-docs/bios/flashing/) | BIOS variants, flashing, verified hashes. |
| [katzzero community guide — BIOS & firmware](https://github.com/katzzero/bc250-unofficial-community-guide/blob/main/02-bios-and-firmware.md) | All BIOS variants, flashing methods, community projects. |
| [MrrZed0/bc-250-bios](https://github.com/MrrZed0/bc-250-bios) | BC250 BIOS resources. |
| [amd/firmware_binaries](https://github.com/amd/firmware_binaries) · [v2000a](https://github.com/amd/firmware_binaries/tree/main/v2000a) | v2000a is the closest relative APU vBIOS/PSP — check its VCN power-up chain. |

### AMD SMU / PSP reference
| Link | Why it matters |
|------|----------------|
| [smu_v11_8_pmfw.h (feature bits)](https://codebrowser.dev/linux/linux/drivers/gpu/drm/amd/pm/swsmu/inc/pmfw_if/smu_v11_8_pmfw.h.html) | All 64 SMU 11.8 feature bits (`FEATURE_DS_SMNCLK_BIT 14`, etc.). |
| [Dayzerosec: Reversing the AMD PSP (2023)](https://dayzerosec.com/blog/2023/04/17/reversing-the-amd-secure-processor-psp.html) | PSP SMN/Syshub slot mechanism (`MapSmn()`), ABL boot order — explains why unmapped SMN frames hang. |
| [PSPReverse](https://github.com/PSPReverse) · [AMD-SP-Loader](https://github.com/dayzerosec/AMD-SP-Loader) | PSP emulator/headers/talks; Binary Ninja loader for PSP blobs. |
| [Buhren — All You Ever Wanted to Know About the AMD PSP (BlackHat 2020, PDF)](https://i.blackhat.com/USA-20/Wednesday/us-20-Buhren-All-You-Ever-Wanted-To-Know-About-The-AMD-Platform-Security-Processor-And-Were-Afraid-To-Emulate.pdf) | PSP internals; SuperIO/UART slide. |
| [Coreboot PSP integration](https://doc.coreboot.org/soc/amd/psp_integration.html) · [bl_syscall_public.h](https://github.com/sameershaik/coreboot_beagle-xM/blob/ab8cc142a727c917aa58bd3ff1e3097332ee2610/src/vendorcode/amd/fsp/cezanne/include/bl_uapp/bl_syscall_public.h) · [bl_errorcodes.h](https://review.coreboot.org/plugins/gitiles/amd_blobs/+/53c000991a5e896bb107e816ff6e422d5c25d3c7/picasso/PSP/bl_errorcodes.h.txt) | PSP FET/directory format, bootloader syscalls, POST/error codes. |
| [ARM Cortex-A5 TRM](https://documentation-service.arm.com/static/5e8e2aacfd977155116a6e48) | The PSP's CPU core specs. |
