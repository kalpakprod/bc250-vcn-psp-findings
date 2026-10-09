# Action Log: 2026-09-23 Option O2 Pure PSP Entry Absence Candidate Assembly

## Intent

Build the clean Option O2 candidate ROM for AMD BC-250 (Lane D single-variable discriminator):

1. Strip PSP lock carrier entries `0x24` (SEC_GASKET) and `0x45` (TOS_SECURITY_POLICY) from the `$PSP` directory table.
2. Refresh Fletcher32 directory checksum (`0x63fffcc8` -> `0x3d1e03f9`).
3. Keep all other bytes intact, including inner FV and DXE modules on the boot-proven `BC250_3.00_MeiMeiDXEv3` base.

## Inputs

- Base ROM: `evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3`
  - Size: 16,777,216 bytes
  - SHA-256: `606a7a7f9ef8fb1c445d8ccfa9640de0339bfec5ab52969135a9e87d62028182`
- Tool: `scripts/build_psp_entry_absence_candidate.py`

## Execution

- Invoked `scripts/build_psp_entry_absence_candidate.py` targeting candidate path `candidates/BC250_3.00_MeiMeiDXEv3_PSP-entry-absence_0x24-0x45_v001.bin`.
- Verified 34 bytes changed strictly within `0x8E0000..0x8E0140`.

## Outputs and Hashes

- Candidate ROM: `candidates/BC250_3.00_MeiMeiDXEv3_PSP-entry-absence_0x24-0x45_v001.bin`
  - Size: 16,777,216 bytes
  - SHA-256: `28cc548decbae0c6d2a5c5ef528c5c9a4ba407e1c381db0eca59c8c74100498e`
- Flash Package: `firmware-flash-pkg/20260923-v005-absence-o2/`
  - Manifest: `candidates/BC250_3.00_MeiMeiDXEv3_PSP-entry-absence_0x24-0x45_v001.build.json`

## Verification

- Stored vs calculated Fletcher32: `0x3D1E03F9` (PASS).
- `psp_ps1_verify.py`: 5/5 valid containers pass, 0 failed, 2 non-containers intact.
- `firmware_audit.py`: PSP and BHD checksum matches true, 17 active entries.
- Diff confinement: exactly 34 bytes changed, 0 bytes modified outside PSP directory header/entries.
