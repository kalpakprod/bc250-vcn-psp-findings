# Exact-clv executable extraction and pre-memory coverage audit

## Conclusion

The existing exact-clv extraction is **complete for the retained x86 PE32/TE executable-section census**, not incomplete because a named pre-memory module is absent:

- `233` executable records are present: `178 PE32` and `55 TE`.
- `178` records came through guided/nested/freeform extraction paths; `54` are outer TE records; one security-core-origin record is separately classified.
- The existing extractor is recursive and supports FV, PE32/TE, compression, guided, freeform and nested FV paths; the census records the resulting provenance and hashes.
- Relevant pre-memory candidates are present as named, hashed TE modules: `MemDetect`, `AmdMemAm4Pei`, `AmdMemoryHobInfoPeim`, `PlatformMemoryConfigurationPei`, `CbsBasePei`, `AmdFabricAriPei`, `AmdNbioSmuV10Pei`, `AmdNbioGfxARIPei`, `AmdNbioBaseARIPei`, `AmdNbioPcieARIPei`, `AmdSocBl5AriPei`, `GnbPei`, `NbPei`, and `AmiAgesaPei`.
- The relevant memory-init candidates (`MemDetect`, `AmdMemAm4Pei`, `AmdMemoryHobInfoPeim`, `PlatformMemoryConfigurationPei`) are present but have no direct selected clock-field/token hits in the retained instruction records. This is a bounded source-map result, not proof that they cannot consume indirect data.
- `CbsBasePei` and the AMD NBIO/Fabric PEI serializers are present with direct field/token hits. Extraction coverage therefore does not explain the remaining semantic gap; the unresolved link is downstream dataflow/consumer ownership.

A real coverage boundary remains: this census stores x86 PE32/TE executable sections. Raw PSP/ABL/SMU/non-x86 payloads, non-executable data sections, runtime-computed pointers, DMA, and arbitrary indirect targets require their separate evidence paths and are not silently promoted into the 233-module result.

## Pinned provenance

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Census: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/census.json`
- Census input SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Census extractor SHA-256: `5ead8605678fc5a13eb0cf49c01b43037560ddc485d8ad2686abf0e9c34d9593`
- Disassembler: GNU `objdump 2.47`
- Coverage metadata: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/coverage.json`
- Own result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-extraction-coverage/extraction-coverage-result.json`

## Existing extraction scope

`scripts/firmware_audit.py` is the existing standard route. It parses the outer PSP/BHD/APCB/FV layout and recursively walks FV/FFS sections. Its executable promotion path saves PE32/TE sections; compressed, guided, freeform and nested FV payloads are recursively walked when they decode to further sections. The census records outer/nested provenance, module body hashes, type, section offsets, and instruction metadata.

Coverage result: `evidence/firmware-audit/20260920-clv-sync-extraction-coverage/extraction-coverage-result.json`, `8/8` checks passed. The audit reused existing census/provenance files and did not create a new firmware parser.

## Relevant pre-memory source map

| Module                             | Format/origin | SHA-256           | Coverage interpretation                                                               |
| ---------------------------------- | ------------- | ----------------- | ------------------------------------------------------------------------------------- |
| `MemDetect`                        | TE / outer    | `6ba86d23491b...` | named pre-memory candidate; no selected field/token hit in retained instructions      |
| `AmdMemAm4Pei`                     | TE / outer    | `1ef4e7b94467...` | named memory-init candidate; no selected field/token hit in retained instructions     |
| `AmdMemoryHobInfoPeim`             | TE / outer    | `aad3f828ccef...` | named memory-HOB candidate; no selected field/token hit in retained instructions      |
| `PlatformMemoryConfigurationPei`   | TE / outer    | `6a1ab7fe72ad...` | named platform-memory candidate; no selected field/token hit in retained instructions |
| `CbsBasePei`                       | TE / outer    | `6ff112922ad8...` | exact Setup serializer/default source; direct field/token evidence present            |
| `AmdFabricAriPei`                  | TE / outer    | `c5b99650a442...` | exact `$INV` reader boundary and serializer-related evidence present                  |
| `AmdNbioSmuV10Pei`                 | TE / outer    | `905b8be68afd...` | exact Setup serializer and PEI lifecycle evidence present                             |
| `AmdNbioGfxARIPei`                 | TE / outer    | `63413be2ac29...` | exact serializer builder evidence present                                             |
| `AmdNbioBaseARIPei`                | TE / outer    | `51d96c1e5a5e...` | related PEI executable present; indirect semantics remain bounded                     |
| `AmdNbioPcieARIPei`                | TE / outer    | `62b1398c4ba9...` | related PEI executable present; indirect semantics remain bounded                     |
| `AmdSocBl5AriPei`                  | TE / outer    | `79e13211d5ae...` | related PEI executable present; indirect semantics remain bounded                     |
| `GnbPei` / `NbPei` / `AmiAgesaPei` | TE / outer    | census-pinned     | named pre-memory/platform candidates; no extraction gap inferred                      |

The shortened hashes above are labels; the machine result carries the full values.

## Limits and next interpretation

- **PASS:** exact pinned input, 233-record census, PE32/TE counts, nested/origin representation, relevant module presence and hashes, existing extractor scope.
- **STATIC ONLY:** direct selected field/token hits in relevant modules.
- **OPEN:** actual memory training consumer, indirect/computed dispatch, data ownership across PEI/HOB/SMU, and physical clock application.
- **OUTSIDE THIS CENSUS:** raw PSP/ABL/SMU payload semantics, arbitrary runtime/DMA/computed targets, and hardware behavior.

No module should be called the actual MCLK/UCLK/FCLK consumer solely because it is extracted or named. The coverage result directs follow-up to dataflow/consumer ownership rather than another extraction sweep.
