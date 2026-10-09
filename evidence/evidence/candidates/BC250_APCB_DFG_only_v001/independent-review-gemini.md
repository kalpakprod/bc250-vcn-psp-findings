# Independent Review (Gemini)

## Scope
The following files were reviewed strictly in a read-only manner (no modified candidate or executing hardware tools):
* Candidate: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`
* Evidences:
  * `evidence/programmer/reads/20260911/read-a.bin`
  * `evidence/programmer/reads/20260911/read-b.bin`
  * `evidence/candidates/BC250_APCB_DFG_only_v001/build-manifest.json`
  * `evidence/candidates/BC250_APCB_DFG_only_v001/apcb-detail.json`
  * `evidence/candidates/BC250_APCB_DFG_only_v001/firmware-audit.json`
* Script: `scripts/build_apcb_dfg_candidate.py`
* Logs: `docs/action-logs/2026-09-10-programmer-preflight.md`

## Evidence Paths & Exact Hashes
* **Candidate**: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`
  * Size: 16777216 bytes
  * SHA-256: `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`
* **Read-A**: `evidence/programmer/reads/20260911/read-a.bin`
  * Size: 16777216 bytes
  * SHA-256: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`
* **Read-B**: `evidence/programmer/reads/20260911/read-b.bin`
  * Size: 16777216 bytes
  * SHA-256: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`
* **build-manifest.json**
  * SHA-256: `1a69c72b03d9fc513686c56198e644ffa42f9e2cd986213ae82c0f64d54e61da`
* **apcb-detail.json**
  * SHA-256: `01feebf8bb82ea17d6ef12138445573128eae94d171ee8180608ec0cb72abf9e`
* **firmware-audit.json**
  * SHA-256: `0b1b273dd233e3e102cc9df333221eee68b593ac80736e9e38bfb5ee4cb26fac`

## Verification Findings
* Base firmware Read-A and Read-B are exact matches.
* Candidate image differs from Read-A by precisely 3 bytes.
  * Offset `0xab1010`: Read-A `0xf2`, Candidate `0x32` (APCB Checksum Byte)
  * Offset `0xab1132`: Read-A `0x1f`, Candidate `0x7f` (DFG Value LSB)
  * Offset `0xab116e`: Read-A `0x1f`, Candidate `0x7f` (DFG Value duplicate byte or backup)
* APCB checksum and DFG words matching expectations (old DFG `0x001FFF00` -> new DFG `0x007FFF00`).
* All other ranges remain untouched (0 offsets anywhere else), leaving UEFI FV/FFS, PSP, BHD, and NVRAM structures unimpacted. 

## Action Log review
In `docs/action-logs/2026-09-10-programmer-preflight.md`, the failure and recovery scenarios and mechanisms are stated but we didn't run signatures checks.

## Assessment

* **Exact Hashes & Size Check**: PASS
* **Calculated Changed offsets & values**: PASS
* **APCB Checksum & DFG Words Evaluation**: PASS
* **Parser Reports Match Evidence**: PASS
* **PSP/BHD/FV/FFS/NVAR untouched**: PASS

## Unrun Checks
The following actions were purposely unrun:
* Hardware interactions (`flashrom`, `programmer`, register reads or writes, JTAG)
* Boot checks / Candidate functionality checks
* UEFI validation tests or cryptographic signature verifications

## Risks
* Without cryptographic verification of the signature checks on modified APCB, the platform signature evaluation might fail and lead to unbootable state.
* The changes are isolated but actual behavioral logic triggered by the DFG bit toggle might induce system instability depending on platform state.
