# D12 ReadyToBoot VCN Gasket

## Title and scope

Keep the hardware-verified D10R immediate SMU unlock, but defer only the
56-write VCN bank-12 gasket sequence to `ReadyToBoot`. Exclude VCN power,
clocks, donor dataplane, dom14, PCI-command changes, and VCN MMIO.

## Planning anchor

- D10R immediate unlock boots and persists into Linux.
- D11R immediate unlock plus immediate gasket reaches splash but blocks OS.
- The discriminating variable is gasket timing, not its record set.
- Current chip was restored and independently read back as D10R, SHA-256
  `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.

## Connected groups or observed existing logic

- Run `PerformSmuUnlockDxe()` immediately at DXE entry.
- Register one ReadyToBoot callback only after unlock verification succeeds.
- Callback executes `ConfigureVcnGasketApertures()` once and closes its event.
- Publish the unlock protocol at entry; do not perform any VCN MMIO readback.

## Use cases

1. Determine whether the full bank-12 program is safe after DXE initialization.
2. If Linux boots, verify SMU liveness/secure access before a bounded commit read.

## Implementation checklist

- [ ] Build a same-size 12,288-byte PE.
- [ ] Replace only the existing CoreUnlock-slot PE.
- [ ] Preserve the D8 explicit-size LZMA header.
- [ ] Verify decompressed and signed-region invariants.
- [ ] Write only after exact hash approval; verify/read back independently.
- [ ] Cold boot mode1; never use mode2 for this experiment.

## Open questions

- Blocking: whether the ReadyToBoot callback completes without wedging later boot.
- Blocking for effect: whether bank-12 commit survives into Linux.

## Decision log

- 2026-09-12: change only timing after D11R early-gasket failure.
