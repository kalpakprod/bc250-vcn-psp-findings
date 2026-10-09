# External UEFI/firmware security sources — registration note

Date: 2026-09-23. Operator supplied: https://github.com/river-li/awesome-uefi-security
("this repo will help you break the BIOS from all sides"). Fetched 2026-09-23. Status: a
curated LINK LIST (tools, exploits, papers, talks); no code executed, nothing adopted.
Adoption of any component below goes through the `external-stack-evaluation` skill first.

## Mapped onto active BC250 lanes

| Source from the list                                                                           | Relevance here                | Verdict for our lanes                                                                                                                                        |
| ---------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| amd-sp-glitch / AMD PSP EMFI work (Razer/Cure53 lineage)                                       | V7 EMFI lane                  | CONFIRMS our existing lane; already incorporated (glitch candidate built)                                                                                    |
| S3 boot script hunting (SentinelOne "Hunt for the S3 Boot Script")                             | V6                            | Lane already CLOSED-NEGATIVE with own root evidence (no NVRAM persistence markers; script rebuilt in RAM; AMD table signature-checked)                       |
| Binarly "Breaking Firmware Trust From Pre-EFI" (AMD PSP early boot), Binarly parse-bug hunting | V2/V2b                        | Method matches our V2b (unsigned tail carrier); their class of bugs lives in native verify code we lean ROM on — keep V2b consumer hunt as the open question |
| efiXplorer / uefi-firmware-parser / UEFITool NE                                                | F4 platform map, DXE analysis | Optional tooling; we already have Ghidra headless + own parsers; evaluate before install if used                                                             |
| chipsec                                                                                        | runtime SPI/SMI checks        | Useful AFTER a working boot for audit, not for the breach itself                                                                                             |
| qiling / efi_fuzz / tsffs                                                                      | fuzzing DXE/SMI               | Our SMM surface closed as dead code (lane B); DXE fuzzing is a later F4-quality lane, not the crux                                                           |
| LogoFAIL-class image parser bugs                                                               | n/a                           | We ALREADY run unsigned x86 code (MeiMei lineage); a parser bug in unsigned FV adds nothing for PSP trust                                                    |
| Sinkclose (AMD ring-2 persistence)                                                             | n/a                           | Exploits SMM bugs on running systems; our goal is PSP trust root, not OS-side persistence                                                                    |

## Net effect

No new lane opened: the list independently corroborates two conclusions we reached with
own evidence (S3 script dead, EMFI is the residual hardware lane) and gives method
references for the two open lanes (V2b consumer/parse-bug hunting; V8 if reopened). The
crux stays unchanged: the single bit "does PSP accept our key" (V3/V4 flash pair).
