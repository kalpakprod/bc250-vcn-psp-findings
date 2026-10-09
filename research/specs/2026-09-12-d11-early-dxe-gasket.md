# D11 Early-DXE VCN Gasket

## Title and scope

Extend the hardware-verified D10R early-DXE SMU unlock with only the established
56-write VCN bank-12 gasket program. Exclude VCN power, clocks, donor dataplane,
dom14 requests, PCI-command changes, and VCN MMIO.

## Planning anchor

- D10R boots mode1 and exposes secure Q3 access from Linux.
- The 56-write bank-12 sequence previously completed at runtime and commit read
  back as 1 in a powered experiment.
- Early-DXE timing has not been tested for this sequence.

## Connected groups or observed existing logic

- Reuse D10R immediate SMU unlock and post-unlock readback.
- Call only `ConfigureVcnGasketApertures()` after successful unlock.
- Keep `EnableVcnHardwareUnified()` and `ConfigureVcnDataFabric()` disabled.
- Preserve the existing first-DXE FFS slot and explicit-size LZMA envelope.

## Use cases

1. Test whether VCN bank-12 programming is accepted before later DXE/OS stages.
2. Establish a BIOS-resident gasket baseline for subsequent isolation work.

## Implementation checklist

- [ ] Build a 12,288-byte X64 PE with unlock plus gasket only.
- [ ] Rebase on a fresh D10R chip capture, preserving NVRAM.
- [ ] Verify LZMA header, decompressed invariants, checksums, and extraction.
- [ ] Write only after exact target reconciliation and operator approval.
- [ ] Cold boot mode1; check SMU liveness and secure access before any readback.

## Open questions

- Blocking: whether bank-12 is writable and non-wedging at early DXE timing.
- Blocking for commit claim: safe Linux-side readback after boot.

## Decision log

- 2026-09-12: one-variable step after D10R; no power or MMIO action.
