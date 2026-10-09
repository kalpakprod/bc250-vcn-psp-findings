# R1: OC baseline identity and feature manifest

## Verdict

Local reconciliation complete; integrated build-baseline selection BLOCKED. The presumed W9 + 8-core + Steam-logo image is not established. Do not choose the current W9-labelled file by name. No image was built, changed or flashed; no live board identity was queried.

## Measured identities (21 images, each 16,777,216 bytes)

| Role                             | Path                                                                 | SHA-256                                                          |
| -------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Read-only control-analysis base  | evidence/donor/retroweb-20260916/BC250_5.00_clv.bin                  | ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8 |
| Current W9-labelled candidate    | candidates/BC250_5.00_clv_VcnUnlock_W9_v001.bin                      | 3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3 |
| Identical W11 readback           | evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin | 3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3 |
| Original W9 readback, NOT equal  | evidence/programmer/reads/20260918/postwrite-vcn-unlock-w9-v001.bin  | 449475563a332a67a594d794cb2e2fbe4d251e0660b65742660b1ff1ce8463fb |
| Steam-logo/core-driver reference | candidates/BC250_5.00_clv_MeiMeiDXE_SteamLogo_StockNVRAM_v002.bin    | 1a0e41ef83b6e2f15676673ee18d7d514e3f4013bd3ded9f86d38e3037995f31 |
| Original board recovery          | evidence/programmer/reads/20260911/read-a.bin                        | 83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0 |
| FirstMarker recovery             | candidates/BC250_5.00_clv_Recovery_FirstMarker.bin                   | 7d420c9f2d46f39131f90827d2dd7b6ee8c7e3558ad8ef8a1d1e2c2a94bccb35 |

Original recovery equals read-b.bin and dump/2.bin. FirstMarker recovery equals FirstMarker_v001 and 20260918/postwrite-first-marker-v001.bin. These are preserved historical recovery artifacts, not a new current-target recovery certification.

## Feature manifest

| Image                              | Injected B6250780 driver                                                                   | MeiMei core driver                                                               | Standard logo FFS                      | Eight-core runtime                                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Plain clv                          | Not found by extraction                                                                    | Not found by extraction                                                          | PNG section present                    | Unverified                                                                                            |
| Current W9-labelled / W11 readback | Present, PE SHA a3f78cfc75dd194dc6702931a5418697528e46884133213a6cc07f94cf752b65           | Absent in main decompressed DXE volume                                           | Absent in main decompressed DXE volume | Unverified for this identity                                                                          |
| SteamLogo StockNVRAM v002          | Absent in main decompressed DXE volume                                                     | Present, PE SHA 2bf4e0ab7de83ce84b089b0487b8c4172379dba258db3556dd62c1dfaa41a91a | JPEG section present                   | Unverified for this identity                                                                          |
| W10 readback                       | Present, different PE SHA 565d23d81401dfdf3d5f3eb403af0d8f931963f443b1d60d35a6f6502d77168e | Not found by extraction                                                          | Not found by extraction                | Retained W10-labelled cpuinfo: 8 cores / 16 processors; exact flash-to-log chain not established here |
| FirstMarker recovery               | Not found by extraction                                                                    | Not found by extraction                                                          | Not found by extraction                | Not established here                                                                                  |

Steam artwork attribution follows the historical candidate provenance; this task fingerprints the JPEG section, not its rendered pixels. Logo display remains UNRUN. Absence of the MeiMei module does not exclude another CPU-unlock implementation. B6250780 presence does not prove VCN operation.

The current W9-labelled file and FirstMarker retain clv's NVRAM, PSP area, APCB area and PEI area byte-for-byte by region hash. Only the DXE FV differs among those named regions. This does not imply that all desired features survived.

## Reproduction and checks

Run `python3 evidence/firmware-audit/20260919-oc-baseline/reproduce.py` in an environment where its adjacent identity.json does not already exist; exclusive output creation intentionally prevents overwriting evidence. The script imports existing scripts/firmware_audit.py and records that parser's hash. No executable bodies, keys or raw variables are emitted.

- PASS: all 21 input sizes, SHA-256 before/after, PSP/BHD/APCB checksums, bounded FV geometry and independent 16-bit FV header checksum sums.
- PASS: candidate/readback and recovery identities reconciled from freshly read bytes.
- PASS: independent direct LZMA-alone decompression of the principal guided DXE section corroborates logo/core-driver GUID absence in W9 and their presence in SteamLogo v002; B6250780 has the opposite presence pattern.
- INCONCLUSIVE: original W9 readback produces only 61 executable records versus 233 for the current W9-labelled image. Structural catalog checks alone do not explain extraction coverage; do not promote that readback as a reusable base without a focused coverage audit.
- UNRUN: full FFS validation, offline signature verification, current chip read, boot, feature execution, clock/voltage measurements and flash. No parser-correctness or hardware-safety claim.

Historical CPU evidence: evidence/runtime/20260919-w10-boot/cpuinfo.txt SHA-256 20f2fa6a8de025309234ac4c0fd3ece2d5fa49772d7198b57937914f9130a2d0. Only processor count and cpu cores fields were extracted; no raw command lines copied.

## Next actions

R2/R3 can proceed read-only against exact clv control code and existing metrics sources. R1 remains blocked for integrated build selection: establish an exact intended feature-complete baseline (or explicitly design and review a new integration), then obtain fresh target identity and recovery evidence before any hardware operation. No arbitrary fallback to plain clv for OC builds.
