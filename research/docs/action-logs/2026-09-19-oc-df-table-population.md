# Action Log: SMU DF P-State Table (0xCF0C) Population & Host Influence Audit

## Intent — 2026-09-19T23:59:00+05:00

- **Actor**: Code / RE Agent.
- **Goal**: Determine whether SMU DF P-state table at 0xCF0C (0xCEE0 region) is populated from fixed firmware defaults vs host-provided (PPTable/SMU table transfer/mailbox). Trace all writers and table-load handlers.
- **Permissions & Authority**: Read-only tools + logged owned evidence/docs/memory writes only. NO ROM/candidate/builder/probe/hardware/network changes.

## Pinning & Integrity Confirmation

- CLV ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`).
- Robin-5 PMFW body: `import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` (SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`).
- Verified offset `0x8FEF00` in CLV ROM is 100% byte-for-byte identical to `smu_fw_robin_5` (262,400 bytes).

## Findings Summary

1. **DF P-State Table (0xCF0C..0xCFD4)**:
   - Contains 5 rows of 40 bytes each.
   - Initial values in binary image at offset `0xCF0C` are pre-populated with exact float rates (250/225, 250/225, 750/425, 1200/875, 150/125 MHz).
2. **Writer Trace & Bounded Negative**:
   - Traced all 49 literal references to `_DAT_000171ec` (`0xCEE0`).
   - Handler `FUN_0001e038` sets up row pointers at `0xCEE0 + 0x1C..0x28` pointing to `0xCF84, 0xCF5C, 0xCF34, 0xCF0C`.
   - No code path or DMA engine writes new divider or frequency data into `0xCF0C..0xCFD4`.
3. **Host Influence**:
   - Host PPTable transfer (`FUN_0001bc80`) targets `0x7B5C` and `0x13474` only, completely isolated from `0xCEE0`/`0xCF0C`.
   - Host BIOS cannot influence DF P-state table frequencies via Setup NVRAM or PPTables.

## Verification

- Extended verifier `scripts/verify_df_table_population.py` executed: `VERIFIER_RESULT: ALL_CHECKS_PASSED`.
