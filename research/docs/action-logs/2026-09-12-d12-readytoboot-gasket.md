# D12 ReadyToBoot gasket action log

## Build and hardware-cycle intent (2026-09-12, Asia/Almaty; before writes)

- Actor: root agent; operator direction: `собирай прошивай`.
- Target: authorized BC250-01, currently restored to exact D10R readback
  `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`;
  CH347T clip remains attached and board is unpowered.
- Change: retain immediate verified SMU unlock; move only the 56-write gasket
  program to a one-shot ReadyToBoot callback. No power/clocks/dataplane/dom14/MMIO.
- Expected effect: avoid D11R's early-DXE transaction failure while programming
  the gasket before OS handoff.
- Failure path: splash/no OS means the full gasket is unsafe even at
  ReadyToBoot; restore the current D10R readback and bisect the 56 records.
- Rollback: `evidence/programmer/reads/20260912/d11-rollback/post-rollback-d10r.bin`,
  SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Stop conditions: build/size/invariant failure, wrong target, SPI mismatch,
  parser failure, or extracted-PE mismatch.

## Build result and approved target (2026-09-12, Asia/Almaty; before SPI write)

- PASS: RELEASE build produced 12,288-byte PE, SHA-256 `59a05d72bff74da2cb75dd95f8b3430ce71a16a367aa74faac088995bdbc54fa`.
- PASS: built `candidates/d12-readytoboot-gasket/BC250_D12_READYTOBOOT_GASKET_from_d10r.bin`, size 16 MiB, SHA-256 `aeaa96bc116b2799363b9d6294d1217ed07403b46ec9f1bc03b76f15c851d2eb`.
- PASS: D8/D10R explicit-size LZMA header; decompressed bytes outside replacement PE identical; signed region identical; four FVs; PSP/BHD/APCB checksums; independent PE extraction.
- Operator authorized both construction and immediate write in one instruction (`собирай прошивай`). Exact generated target and hash are recorded here before the SPI write.
- Proceed only if the on-chip state is still byte-identical to the restored D10R rollback image.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: pre-write capture `evidence/programmer/reads/20260912/d12/prewrite-d12.bin` is byte-identical to restored D10R, SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- PASS: CH347T and Winbond `W25Q128.V` detected; flashrom wrote the full image and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d12/postwrite-d12.bin` is byte-identical to D12, SHA-256 `aeaa96bc116b2799363b9d6294d1217ed07403b46ec9f1bc03b76f15c851d2eb`.
- PASS: four FVs and PSP/BHD/APCB checksums; extracted existing-slot PE SHA-256 `59a05d72bff74da2cb75dd95f8b3430ce71a16a367aa74faac088995bdbc54fa` matches the intended build.
- Evidence class: hardware-verified at SPI write/readback only.
- UNRUN: cold boot, ReadyToBoot gasket completion, SMU liveness/secure access, bank-12 commit, and VCN behavior.

## D12 cold-boot result (2026-09-12 20:45-20:46 PKT)

- PARTIAL: Linux itself booted and is reachable: ping 3/3, SSH uptime 1 minute, kernel `7.2.0-1.92-cachyos-vcn-bc250`, mode1 command line.
- FAIL: operator observed the Linux display frozen. `lspci` shows no bound kernel driver for `01:00.0`; system state is `degraded`.
- Direct SMU verification: `alive=False`; secure Q3 `0x2A` to `0x0005A870` timed out. Per the established taxonomy, the SMU mailbox is wedged and requires a cold cycle.
- Kernel evidence: VCN probe descriptor and firmware were found, then `hw_init of IP block <smu> failed -62`, `amdgpu_device_ip_init failed`, `Fatal error during GPU init`, PSP `DESTROY_TMR(0x7)` failed with `0x80000306`, and amdgpu probe ended `-62`. This directly explains the frozen display while the host remains reachable.
- VERDICT: deferring the full 56-write gasket sequence to ReadyToBoot allows x86/Linux release but wedges the SMU before amdgpu initialization. The full sequence is unsafe at both initial DXE (D11R: no OS release) and ReadyToBoot (D12: host alive, GPU/SMU dead).
- Bank-12 commit is INCONCLUSIVE and was not read: once `alive=False`, another mailbox read cannot provide a valid result and only repeats the failed class.
- STOP: do not run mode2, reload amdgpu, probe VCN MMIO, or repeat the same boot. Restore D10R. Next method must bisect the 56-record sequence; timing alone is insufficient.
