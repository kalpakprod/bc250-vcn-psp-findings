# D13 ReadyToBoot Gasket First-Half Slice

## Title and scope

Bisect the D12 56-write gasket failure by executing only records 0 through 27
at ReadyToBoot after the hardware-verified D10R early SMU unlock. Do not issue
the remaining records, lock/unlock tail, commit, power, dom14, or VCN MMIO.

## Planning anchor

- D10R boots with early SMU unlock.
- D11R full 56 writes at initial DXE prevents OS release.
- D12 full 56 writes at ReadyToBoot releases Linux but wedges SMU before
  amdgpu initialization.
- D13 changes only the executed gasket record count from 56 to 28.

## Connected groups or observed existing logic

- Records 0..27 include the initial programming write `0x0900C234 <- 0`,
  masks/requester fields, and the first four aperture descriptors through
  `0x0900C9D4 <- 0x307`.
- They exclude `0x0900CB80` lock writes and every `0x0900C234 <- 1` commit.
- Retain immediate unlock plus one-shot ReadyToBoot callback.

## Use cases

1. If D13 boots with live SMU, the failing record is in 28..55 or requires
   commit/finalization.
2. If D13 wedges, bisect 0..27 into 0..13 and 14..27 using the same method.

## Implementation checklist

- [ ] Define and enforce an executed-record count of 28.
- [ ] Build a 12,288-byte PE and replace the existing CoreUnlock-slot PE.
- [ ] Preserve explicit-size LZMA and all non-PE decompressed bytes.
- [ ] Reparse and independently extract.
- [ ] Before flash, restore/capture D10R and rebase current NVRAM.

## Open questions

- Blocking: which half contains the SMU-wedging operation.

## Decision log

- 2026-09-12: select first-half binary slice; exclude all commit/lock tail
  operations to minimize irreversible/compound behavior.
