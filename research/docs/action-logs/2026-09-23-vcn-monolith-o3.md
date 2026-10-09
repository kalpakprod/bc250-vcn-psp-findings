# Action Log: 2026-09-23 Option O3 Monolithic VCN Candidate Assembly

## Intent

Build the unified monolithic candidate ROM (Option O3) for AMD BC-250:

1. Strip PSP lock carrier entries `0x24` (SEC_GASKET) and `0x45` (TOS_SECURITY_POLICY) from the `$PSP` directory table and recompute Fletcher32 directory checksum (Lane D).
2. Update `Bc250VcnUnlockDxe` to execute autonomously at boot without emulator-induced O6 abort guards, sending domain bitmap permission bit 6 via `0x28`/`0x29` and issuing SMU message `0x1B` full power-up.
3. Inject the driver into the inner FV of the boot-proven community base `BC250_3.00_MeiMeiDXEv3`.

## Inputs

- Base ROM: `evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3`
  - Size: 16,777,216 bytes
  - SHA-256: `606a7a7f9ef8fb1c445d8ccfa9640de0339bfec5ab52969135a9e87d62028182`
- Driver source: `candidates/vcn-unlock-driver-v000-DRAFT/BC250VCNUnlockDxe.c`
- EDK2 workspace: `/tmp/edk2ws`

## Execution

1. Patched `BC250VCNUnlockDxe.c` to remove O6 clock plan abort, compile cleanly with GCC in EDK2 workspace.
2. Built `Bc250VcnUnlockDxe.efi` and generated `Bc250VcnUnlockDxe.ffs` with GenSec/GenFfs.
3. Authored `scripts/build_vcn_o3_candidate.py` and executed assembly.

## Outputs and Hashes

- Driver EFI: `candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.efi`
  - Size: 12,288 bytes
  - SHA-256: `0af4cc43a166abb2040f362c6f264e0d26bc6e2a00abc2983a2197ae63b54023`
- Driver FFS: `candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.ffs`
  - Size: 12,316 bytes
  - SHA-256: `b9b6f8d381233b8fe5830235a7f2f616095ca96209041510efdbc5c3a4a0e978`
- Candidate ROM: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v004.bin`
  - Size: 16,777,216 bytes
  - SHA-256: `2981b2525c4a101af745d3f22d4b78815566ee5445131a1aa0f5578ae97c5638`
- Flash Package: `firmware-flash-pkg/20260923-v004-combined-o3/`
  - Manifest: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v004.build.json`

## Verification

- Fletcher32 update: `0x63fffcc8` -> `0x3d1e03f9` over span `0x8E0008`..`0x8E0140`.
- All 193 original DXE modules intact, 194th module `Bc250VcnUnlockDxe` verified.
- Byte diff strictly bounded to PSP directory `[0x8E0000, 0x8E0140)` and capsule `[0xAE0000, 0xE00000)`.
- All regression and contract tests green (83/83 pytest, 7/7 make test).
