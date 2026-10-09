# D7 No-op Existing-Slot Control BIOS

## Title and scope

Build a same-slot, same-size no-op DXE control to distinguish reconstructed
LZMA/FV rejection from a hang caused by executing the D6 SMU unlock.

## Planning anchor

- Base: the known-booted `/tmp/d3a_flash/pre_d3b2_retest.bin`.
- Target: existing `Bc250CoreUnlockDxe` PE32 payload, 12,288 bytes.
- D6 used this exact replacement mechanism but did not initialize.

## Connected groups or observed existing logic

- Preserve FFS GUID, Depex, UI, order, sizes, and all non-PE decompressed bytes.
- The D7 PE entry point returns `EFI_SUCCESS` without registering events,
  sending mailbox commands, or touching PCI/SMN/MMIO.

## Use cases

1. D7 boots: LZMA/FV reconstruction is accepted; D6 code/timing caused failure.
2. D7 fails: reconstruction method is rejected; stop rebuilding this capsule.

## Implementation checklist

- [ ] Build RELEASE X64 no-op DXE with a 12,288-byte PE image.
- [ ] Replace the same existing PE32 section.
- [ ] Prove all other decompressed bytes identical.
- [ ] Reparse, extract, hash, and record unrun hardware checks.

## Open questions

- Blocking: cold-boot result after verified SPI readback.

## Decision log

- 2026-09-12: use a no-hardware control before attempting another unlock sequence.
