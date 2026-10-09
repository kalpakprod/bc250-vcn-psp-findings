# D5 SMU-Unlock Lab BIOS

## Title and scope

Build a boot-oriented BC-250 research BIOS that preserves every signed PSP,
SMU, ABL, TOS, SEC_GASKET, and TOS_SECURITY_POLICY byte while adding only an
x86 DXE-stage SMU debug unlocker. The image is a laboratory candidate, not a
claim of VCN enablement or hardware safety.

## Planning anchor

- Baseline: `/tmp/d3a_flash/pre_d3b2_retest.bin`, 16 MiB, SHA-256
  `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- This exact evolving board state previously booted mode1 before the D3-B2
  retest. Its NVRAM drift is therefore intentionally preserved.
- D3-B2 and D4 hard-failed because signed PSP-resident material was changed.
- The Q2 ring-overflow SMU debug unlock and its BIOS-3 offsets were previously
  hardware-verified from Linux. The corresponding type-0x08 PMFW identity was
  byte-correlated with the on-chip image.

## Connected groups or observed existing logic

- Reuse the EDK II package under
  `archives/imported/uefi-source/legacy-tmp-bc250-dxe/Bc250VcnUnlockPkg/`.
- Audit note (2026-09-27): this imported source is historical. Its unlock and mailbox functions do not propagate every write/readback failure; do not reuse them unchanged as an accepted safe path.
- Reuse only `PerformSmuUnlockDxe()` and its recovery/fixup sequence.
- Do not run `EnableVcnHardwareUnified()`, gasket writes, donor dataplane
  writes, dom14 requests, or VCN MMIO reads at boot.
- Publish the existing protocol GUID after a successful unlock so later DXE
  probes can detect the research substrate.
- Inject one FFS into the unsigned x86 DXE FV. Preserve PSP and APCB exactly.

## Use cases

1. Boot Linux with secure SMU access already open for read-only inventory.
2. Test one new SMU/VCN hypothesis at a time from a separate DXE app or Linux
   probe without reflashing the signed firmware regions.
3. Recover to the exact pre-D3-B2 board image if DXE dispatch or unlock fails.

## Implementation checklist

- [ ] Copy the EDK II package to a D5 candidate source directory.
- [ ] Reduce the driver entry point to SMU unlock plus protocol publication.
- [ ] Build RELEASE X64 with the existing local EDK II tree.
- [ ] Validate PE/COFF, FFS, GUID, Depex, and FV structure.
- [ ] Inject into a copy of the exact baseline.
- [ ] Verify size, hashes, changed ranges, PSP/APCB identity, and independent
      extraction of the injected module.
- [ ] Record all unrun runtime and hardware checks.

## Open questions

- Blocking for a bootability claim: actual cold boot and SSH readback.
- Non-blocking for construction: whether the unlock is early enough in DXE to
  persist through the selected Linux boot path.
- Non-blocking for construction: which new isolation/ownership vector should
  be tested first after a clean boot.

## Decision log

- 2026-09-12: choose unlock-only DXE over an automatic VCN bring-up. The latter
  repeats hardware-verified wedge classes and lowers boot probability.
- 2026-09-12: preserve the board's booted pre-D3-B2 NVRAM state instead of
  rebuilding from generic stock.
