# Independent Review (Gemini) - BC250 MemoryClock Candidate

## Scope
The following files were reviewed in a strictly read-only manner:
* Candidate: `candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin`
* Evidences:
  * `evidence/programmer/reads/20260911/read-a.bin`
  * `evidence/candidates/BC250_MemoryClock_1750_only_v001/build-manifest.json`
  * `evidence/candidates/BC250_MemoryClock_1750_only_v001/nvar-primary.json`
  * `evidence/candidates/BC250_MemoryClock_1750_only_v001/firmware-audit.json`
* Script: `scripts/build_amdsetup_memory_candidate.py`

## Exact Source Evidence Paths & Hashes
* **Candidate**: `candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin`
  * Size: 16777216 bytes
  * SHA-256: `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee`
* **Read-A**: `evidence/programmer/reads/20260911/read-a.bin`
  * Size: 16777216 bytes
  * SHA-256: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`
* **build-manifest.json**: SHA-256: `f9c72180e2d67c0eef7c3128456dde87478b89d5b1a06d20f76e63539db4f61f`
* **nvar-primary.json**: SHA-256: `06710664aa71770881221401da74c1fa1ce224e8eaf1e5940176490a69a927f5`
* **firmware-audit.json**: SHA-256: `83b82cd738bc7d668ac90f568066ef451ffc2075af36d2b2fde5bc4e951dcae8`
* **build_amdsetup_memory_candidate.py**: SHA-256: `3d015676c4e2d8bc5fbee235aaea18802fb93332d1b4bab0610ab4f20dd0ea36`

## Findings
* The baseline read-a hash matched expectations.
* The independent byte-by-byte comparison between Candidate and Read-A identified exactly one altered byte.
* The single modified byte is situated precisely at `0x7E5` where it transitioned from `0xFF` to `0x23` (1750MHz IFR option for MemoryClockSpeed setup field).
* All external parsers output checks and validations align identically with these modifications, identifying zero unintended changes over remaining portions inside NVAR variables or the outer UEFI boundaries.
* APCB, PSP, BHD, FFS and UEFI volumes remained exactly unmodified as expected.

## Assessment (PASS/FAIL/INCONCLUSIVE)
* **Exact specific change at 0x7E5**: PASS
* **No other selected field changes (1 byte changed total)**: PASS
* **Parsers alignment (NVAR/Audit)**: PASS
* **Read-only limitation maintained**: PASS

## Unrun Checks and Limitations
* **Hardware Operations Unrun**: No interaction occurred with physical programmers, SPI headers, JTAG controllers, flashrom software, I/O memory reads or any forms of live platform registration.
* **Boot/Training unverified**: We can only claim static offsets matching manifest targets. The review possesses limitations regarding runtime execution. Any claim on memory training success, functional platform boot or safe UEFI driver phase execution is fundamentally prohibited under this verification constraint. 
