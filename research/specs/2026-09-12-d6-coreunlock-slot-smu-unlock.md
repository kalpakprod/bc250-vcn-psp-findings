# D6 Existing-CoreUnlock-Slot SMU Unlock BIOS

## Title and scope

Build a BC-250 research BIOS that replaces only the PE32 payload of the
existing `Bc250CoreUnlockDxe` FFS with the same-size D5 SMU-unlock DXE. Do not
add an FFS, change dispatch order, resize the inner FV, or modify signed
PSP-side firmware.

## Planning anchor

- Baseline: `/tmp/d3a_flash/pre_d3b2_retest.bin`, the exact 16 MiB state that
  previously booted mode1; SHA-256
  `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Existing FFS: UI `Bc250CoreUnlockDxe`, GUID
  `2F3D426D-6A54-4A6B-82D0-1207CC5B6D92`, type 7, PE32 payload size 12,288.
- Replacement: D5 `Bc250SmuUnlockDxe.efi`, PE32 payload size 12,288.
- D5 added a new FFS and changed inner-FV layout; D6 removes that variable.

## Connected groups or observed existing logic

- Preserve the original FFS header, GUID, Depex, UI section, ordering, and
  size. Replace only its PE32 section contents.
- Preserve every other decompressed FV byte exactly, then rebuild only the
  enclosing LZMA transport envelope required to store the changed payload.
- Preserve all PSP, BHD, APCB, SMU, ABL, TOS, SEC_GASKET, and policy bytes.

## Use cases

1. Test whether a known-dispatched DXE slot can host the SMU unlock without
   changing FV topology.
2. If it boots, use the unlocked SMU state as the substrate for separately
   controlled BIOS-resident probes.
3. If it fails, separate DXE payload behavior from FFS insertion/layout as a
   cause of D5 failure.

## Implementation checklist

- [ ] Identify the existing FFS and its exact PE32 section in the decompressed FV.
- [ ] Require the source and replacement PE payload sizes to match.
- [ ] Replace only the PE payload; assert all other decompressed bytes match.
- [ ] Recompress and rebuild the enclosing FFS without changing outer FV size.
- [ ] Parse the result and independently extract the replacement payload.
- [ ] Verify hashes, changed ranges, signed-region identity, and checksums.
- [ ] Record unrun cold-boot and SMU-unlock checks.

## Open questions

- Blocking for a bootability claim: cold boot with SPI readback already proven.
- Non-blocking: whether the existing CoreUnlock FFS dispatch timing is suitable
  for the ReadyToBoot registration used by the replacement.
- Non-blocking: which new BIOS-resident probe to enable after D6 boot success.

## Decision log

- 2026-09-12: change method class from adding an FFS to same-size PE payload
  replacement in an existing, historically booted DXE slot.
- 2026-09-12: keep VCN power/gasket/dom14/MMIO actions disabled until the base
  unlock BIOS itself is hardware-verified.
