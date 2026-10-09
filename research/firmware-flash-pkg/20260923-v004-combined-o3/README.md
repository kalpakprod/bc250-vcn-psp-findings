# Flash Package: 20260923-v004-combined-o3

## Artifacts
- `BC250_3.00_MeiMeiDXEv3_vcn_v004.bin`: 16,777,216 bytes, SHA-256 `2981b2525c4a101af745d3f22d4b78815566ee5445131a1aa0f5578ae97c5638`
- `SHA256SUMS`: Verification hashes

## Description
Monolithic Option O3 image:
1. Removal of PSP lock carriers (entry 0x24 SEC_GASKET, entry 0x45 TOS_SECURITY_POLICY) with refreshed Fletcher32 checksum (0x63fffcc8 -> 0x3d1e03f9).
2. Autonomous `Bc250VcnUnlockDxe` pre-OS driver injected into inner FV (GUID `B6250780-7E00-4203-900C-23443B1413FE`, 193 -> 194 modules), executing SMN domain bitmap write and SMU full power-up message 0x1B at boot.

## Runbook
Step-by-step flashing instructions and verification:
`docs/guides/bc250-v004-monolith-o3-flash-runbook.md`
