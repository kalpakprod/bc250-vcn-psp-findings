# 2026-09-21 AF58 helper-contract correction

## Incorrect model

The first machine helper verifier modeled `LSLS r1,#0x1E` and `LSLS r0,#0x1F` as checking original bit 15 of each halfword. That is wrong: shifts by 30 and 31 move original bits 1 and 0 into bit 31. For `0x5CBE`'s exact output `[u16 2, u16 1]`, both tests pass and `0xFE60` returns `1`, not `0`.

## Corrected result

The failed result and verifier outputs are retained. Re-run the same pinned ABL1 checks with the corrected host model; AF58's static path therefore reaches its three stores at object-relative offsets `0x739`, `0x75F`, and `0x760` after `0xFE60`. This remains static-analysis only; no clock-policy semantics are inferred.

Evidence class: observed-bytes + static-analysis. No hardware/network/ROM/NVRAM/register operation.

## Harness correction

The first rerun wrapper referenced `helper-contract-check.py`, but the original verifier was inline and had no source file. Python exited `2` before a corrected check. This is preserved as a harness error; the wrong 20/20 output remains quarantined. A standalone corrected verifier will be created with the corrected bit model.
