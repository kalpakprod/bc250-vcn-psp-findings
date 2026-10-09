# D10 Early-DXE SMU Unlock

## Title and scope

Move the D9R hardware-verified SMU debug unlock from `ReadyToBoot` to the
entry point of the existing first CoreUnlock DXE slot. Do not perform any VCN,
gasket, dom14, fabric, PCI-command, or MMIO operation.

## Planning anchor

- D9R hardware state: mode1 boots and secure Q3 `0x2A` returns status `0x01`.
- D9R executes the unlock at `ReadyToBoot`.
- D8 proved the required LZMA-alone explicit decoded-size field `0x420010`.
- Existing dispatch slot: `Bc250CoreUnlockDxe`, GUID
  `2F3D426D-6A54-4A6B-82D0-1207CC5B6D92`, first module in the inner DXE FV.

## Connected groups or observed existing logic

- Reuse the exact D9R unlock and fixup implementation.
- Replace event registration with a direct call from the DXE entry point.
- Publish the existing protocol only after the post-unlock secure readback
  succeeds.
- Preserve the existing FFS metadata and all other decompressed FV bytes.

## Use cases

1. Determine whether secure SMU access can be opened at initial DXE dispatch.
2. Establish an earlier BIOS-resident substrate for subsequent single-variable
   VCN isolation experiments.

## Implementation checklist

- [ ] Copy the D9R source into a new candidate source directory.
- [ ] Call `PerformSmuUnlockDxe()` directly from the entry point.
- [ ] Keep all VCN actions behind a false gate.
- [ ] Build RELEASE X64 and require a 12,288-byte PE32 replacement.
- [ ] Rebase into the existing slot with explicit LZMA size `0x420010`.
- [ ] Verify all decompressed bytes outside the PE replacement are identical.
- [ ] Reparse checksums/FVs and independently extract the PE.

## Open questions

- Blocking for progression: cold boot and secure-SMN readback.
- Non-blocking: the exact point during DXE dispatch at which PSP/SMU policy
  becomes immutable.

## Decision log

- 2026-09-12: choose early unlock alone; defer gasket and VCN actions until
  early-unlock boot safety is hardware-verified.
