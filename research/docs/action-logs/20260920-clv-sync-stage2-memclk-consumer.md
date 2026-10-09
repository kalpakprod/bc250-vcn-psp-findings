## PEI service-table result

Executed `pei_service_verify.py`; exit `0`, `16/16` checks passed. Local `PiPeiCis.h` slot mapping binds `[PeiServices+0x4C]` to `AllocatePool`, `[PeiServices+0x18]` to `InstallPpi`, and `[PeiServices+0x44]` to `InstallPeiMemory`. Exact `AmdMemAm4Pei` dataflow receives the PeiServices pointer from `[ESP+8]`, allocates two structures, and calls InstallPpi; no InstallPeiMemory call appears in main `0x2F6..0x434`. The helper path validates APOB/PSP/BHD data. GUID/interface identity and downstream AGESA consumer remain unresolved.

Own manifest check exited `0` with all files `OK`.

## Superseding pointer-provenance correction

A reviewer correction identified that `EFI_PEI_SERVICES` is not directly at `ESI`: the PEIM entry receives a pointer-to-pointer. The report/result now state the exact chain `[ESP+8] -> EAX -> ESI`, then `[ESI] -> EFI_PEI_SERVICES table`; calls are `[[ESI]+0x4C]` (`AllocatePool`) and `[[ESI]+0x18]` (`InstallPpi`), with no `[[ESI]+0x44]` (`InstallPeiMemory`) call. Earlier wording is superseded; no training claim was made.

Rerun: `pei_service_verify.py` exit `0`, `16/16` PASS. Evidence manifest rerun from its directory exit `0`, all files `OK`.
