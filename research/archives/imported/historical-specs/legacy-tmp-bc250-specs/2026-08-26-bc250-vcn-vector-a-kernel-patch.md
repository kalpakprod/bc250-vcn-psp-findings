# BC-250 VCN Vector A: reversible kernel opt-in

**Status:** superseded forward plan. Preserve its measured kernel evidence; use `2026-08-26-bc250-vcn-unlock-master-plan.md` for all remaining work.  
**Date:** 2026-08-26  
**Target:** `steammachine`, AMD BC-250 `1002:13fe`, CachyOS Linux `7.2-rc7` test variant  
**Patch:** `tmp_bc250/recon/0009-bc250-vcn-safe-direct-load.patch`

## Scope

The patch exposes the existing upstream VCN 2.0 driver path for Cyan Skillfish IP version `2.0.3`, but only when explicitly enabled:

```text
amdgpu.bc250_vcn=1
```

Default remains `0`, so the patched kernel preserves stock BC-250 behavior unless the test boot entry opts in.

The patch changes four AMDGPU files:

1. `amdgpu.h`: declares the internal opt-in flag.
2. `amdgpu_drv.c`: defines read-only module parameter `bc250_vcn`, default false.
3. `amdgpu_discovery.c`: maps `1002:13fe`, VCN `2.0.3`, to existing `vcn_v2_0` and `jpeg_v2_0` IP blocks only when opted in.
4. `amdgpu_ucode.c`: maps VCN `2.0.3` to existing `amdgpu/navi10_vcn.bin` legacy firmware name.

No new driver implementation or dependency is added.

## Rejected global direct-firmware test mode

The historical test entry used:

```text
amdgpu.bc250_vcn=1 amdgpu.fw_load_type=0
```

This is no longer an accepted VCN test. Preserved stable-kernel boots show a strong experimental association between global `fw_load_type=0` and GFX KIQ failure even when the stock module ignores `bc250_vcn`; they do not establish the internal failure mechanism. Any future direct-load work must be VCN-specific and must leave global AMDGPU firmware policy unchanged.

## Safety and rollback

- Stock/default boot entry omits both parameters.
- Existing installed kernel is not replaced.
- Experimental kernel will be installed under a distinct `linux-cachyos-rc-bc250` package/kernel name.
- Rollback: boot the current `linux-cachyos-bc250` entry or remove the two parameters.
- Cold power cycle remains the recovery path for a fabric/VCN hard hang.
- `tmp_bc250/recon/install_vcn_test_kernel.sh` installs only the co-installable RC kernel and adds the parameters through a kernel-specific Limine drop-in.
- `tmp_bc250/recon/rollback_vcn_test_kernel.sh` refuses to remove the package while that test kernel is running, then removes the package and test entry from a known-good boot.

The first draft contained an `mmUVD_NO_OP` read as a supposed guard. It was removed: blocked VCN MMIO reads can themselves hang the fabric, so a CPU MMIO read cannot be treated as a safe preflight.

## Verification completed

1. Applied patches `0001`, `0003` through `0007` to a fresh CachyOS `7.2-rc7` source extraction.
2. `patch --dry-run -Np1` for `0009` passed.
3. Real application of `0009` passed.
4. Confirmed no `BC-250: VCN MMIO` probe remains in `vcn_v2_0.c`.
5. Clang/LLVM targeted compilation passed for:
   - `amdgpu_drv.o`
   - `amdgpu_discovery.o`
   - `amdgpu_ucode.o`
6. The complete AMDGPU object linked as `amdgpu.o`, SHA-256 `c160534ffd3d938b13d25003bfd3dd544bb411aa92822896716dc956c15e041d`.
7. `llvm-nm amdgpu.o` confirms:
   - `__param_bc250_vcn`
   - `__param_str_bc250_vcn`
   - `amdgpu_bc250_vcn`
8. Standalone `amdgpu.ko` modpost reached the final module stage. It failed only because the disposable partial-kernel tree has no top-level `Module.symvers`, producing unrelated unresolved core-kernel symbols. No compile or link error came from the VCN patch.

## Live A/B results

The co-installable `7.2.0-rc7-1.90-cachyos-rc-bc250` package was built, installed, and booted. It registered VCN `2.0.3` and selected `navi10_vcn.bin`, but AMDGPU failed earlier during GFX initialization:

```text
ring kiq_0.2.1.0 test failed (-110)
KCQ enable failed
hw_init of IP block <gfx_v10_0> failed -110
```

Runtime reloads performed after a failed global-direct boot did not isolate a clean control because they reused hardware state from that boot. Preserved cold-boot evidence shows:

- RC7 with `bc250_vcn=1 fw_load_type=0` failed GFX KIQ.
- Packaged stable with unknown `bc250_vcn` ignored but `fw_load_type=0` still failed GFX KIQ.
- Packaged stable without experimental arguments initialized AMDGPU and `/dev/dri` normally.

Therefore UEFI bring-up, 40CU, and VCN registration are not required for the observed KIQ failure. Global direct firmware mode is the isolated experimental trigger in the preserved boots, not a mechanism-level causal proof. RC7 itself was never clean-booted with `fw_load_type=-1`, so the claim that RC7 is unsuitable is withdrawn. The discovery-offset backport was tested under the confounded global-direct condition and is not a valid RC7 verdict.

## Stable-final module experiments

A stable-final overlay with matching vermagic was built. Loading that experimental overlay after PCI unbind reset or hard-hung the board even with `bc250_vcn=0`. This makes the overlay/reload experiment unusable, but does not prove that every AMDGPU reload is inherently unsafe or identify the experimental VCN code as the cause.

The compiled VCN-only direct-load draft is also incomplete: it changed PSP registration, payload copy, and cache-window selection but left `amdgpu_vcn_sw_init` sizing the VCPU BO as PSP-only. A VCN payload copy would overrun the allocated firmware region. Compile success is not acceptance.

The board and all stable/RC command lines, stable initramfs, and module overlays were restored. The authoritative next plan is `2026-08-26-bc250-vcn-evidence-reassessment-and-safe-next-slice.md`.
