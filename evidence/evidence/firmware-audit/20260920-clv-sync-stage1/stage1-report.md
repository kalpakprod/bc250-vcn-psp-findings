# Stage 1 — Historical CLV/SYNC reconciliation (offline)

## Conclusion
The three loose `SYNC` images and their archived revisions are NVRAM/default-store variants, not executable/APCB code variants. Their selected `AmdSetup` values request different memory/DF/divider/voltage/PPT states, but no physical clock synchronization is established. The ZIP DFG variants are APCB-only two-byte experiments; four uncorrected variants fail the local additive APCB checksum, while the duplicate `ckfix` pair adds an unknown APCB byte (`+0x14 = 0x1E`) and passes that checksum calculation. No image was modified or executed.

## Pinned inputs
- Baseline: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Baseline SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Chat source: `/home/OWNER/Downloads/AyuGram Desktop/ChatExport_2026-09-20`
- Machine report: `stage1-report.json`

## Archive coverage
`files.zip`, `oc_profiles.rar`, `oc_profiles (1).rar`, and `03_BC250_ULTIMATE_LOW_LATENCY_StockCPU.rar` were inventoried by `bsdtar -tvf` before bounded extraction. Only `README.md` and `.bin` members were extracted as data; no member was run. Inventory reports and archive hashes are in this directory.

Attachment IDs (sanitized metadata): ZIP `771991`; loose DFG duplicates `771994`, `771998`; loose SYNC 01/02/03 `772078`/`772079`/`772080`; `oc_profiles.rar` `772084`; ULTIMATE RAR `772120`; `oc_profiles (1).rar` `772176`. These IDs do not prove that a file was flashed.

## Structural attribution
| Family | Bytes vs pinned CLV | Changed region | Result |
|---|---:|---|---|
| Loose SYNC 01/02/03 | 3019/3018/3020 | only `0x000000..0x01FFFF` first FV/NVRAM | PSP/BHD/APCB pass; UEFI module bodies unchanged |
| `oc_profiles (1).rar` SYNC 01/02/03 | same NVRAM family | same first FV/NVRAM region | each changes loose copy only at `AmdSetup` Tcl and DRAM Timing fields |
| ULTIMATE RAR | 3022 | first FV/NVRAM region | no UEFI code/APCB changes |
| ZIP DFG variants | 2 each | paired DFG fields at `0xAB112A/0xAB1166` or `0xAB112E/0xAB116A` | no NVRAM/code changes |
| ZIP `ckfix` duplicate pair | 3 | DFG pair + `0xAB1014` | byte-identical duplicates; APCB checksum calculation passes |

All images are 16 MiB and retain four outer FVs. Donor, SYNC03, and ULTIMATE each extract 233 executable module bodies; ordered body hashes are identical. This is static/host evidence only.

## Decoded AmdSetup values
The parser was `scripts/nvar_audit.py` with bounded store `offset=0x0`, `length=0x20000`; raw variable bodies were not emitted.

| Revision | MCLK token | UclkDiv1M0 | FCLK_DPM | VDD offset control/value | DF override control/value | CPU | Fast/Slow PPT | Vrm current/max | Tcl / DRAM |
|---|---:|---:|---:|---|---|---:|---|---|---|
| SYNC 01 loose | 35 | 0 | 0 | 0 / 0 | 1 / 875 | 3600 | 105000 / 85000 | 75000 / 100000 | 18 / 1 |
| SYNC 02 loose | 26 | 1 | 0 | 1 / 35 | 1 / 1333 | 3600 | 120000 / 95000 | 80000 / 110000 | 14 / 1 |
| SYNC 03 loose | 35 | 1 | 0 | 1 / 80 | 1 / 1750 | 3600 | 130000 / 105000 | 90000 / 120000 | 16 / 1 |
| SYNC 01/02/03 archived later | same profile values | | | | | | | | Tcl=`0xFF`, DRAM=`0xFF` |
| ULTIMATE archived later | 35 | 0 | 0 | 1 / 100 | 1 / 1400 | 3600 | 130000 / 105000 | 95000 / 120000 | Tcl=`0xFF`, DRAM=`0xFF`; PhyPowerSaving=0; MemoryPstate=0 |

The ULTIMATE `VDD` offset value is historical data and is not a project recipe; voltage semantics/rail identity remain unresolved and the current ceiling is not a validated safety rating.

## APCB/checksum finding
`apcb_detail.py` and `firmware_audit.py` report stored APCB checksum byte `+0x10 = 0xC0` for all variants. Uncorrected DFG values calculate to `0xFA`, `0x82`, `0xDE`, and `0xA2` (FAIL). The `ckfix` pair changes byte `0xAB1014` from `0x00` to `0x1E` and calculates `0xC0` (PASS). The role of `+0x14` beyond checksum balancing is unknown. This is not PSP acceptance proof.

## Verification ledger
- `scripts/firmware_audit.py` on 14 image entries / 13 unique SHA-256 contents: exit `0`; PSP/BHD/APCB/FV structure captured.
- `scripts/apcb_detail.py` on 14 image entries / 13 unique SHA-256 contents: exit `0`; `failed=false`.
- `scripts/firmware_audit.py --extract-image`: donor/SYNC03/ULTIMATE each exit `0`; 233 modules each; donor-vs-candidate ordered module hashes equal.
- `scripts/psp_ps1_verify.py`: exit `1` on baseline and every candidate because 14 containers pass while two externally keyed records remain unresolved; no new candidate-only failure observed.
- Historical imported `rom_scan.py`: partial, exit `1` after useful scan output because its hard-coded Windows output path is absent; this is not used as the completed structural check.

## Phase 2 consumer target
Trace the native `AmdSetup` serializer and consuming divider/clock/training path for body offsets `0x316`, `0x330`, `0x6A3`, `0x703`, and `0x704` through `CbsSetupDxe`/`AmdFabricAriPei`. Resolve units, precedence, and whether any setting selects synchronous crossing. Do not carry the historical DFG byte variants forward without a verified checksum/consumer rationale.

## Unrun / unresolved
Hardware boot, training, physical MCLK/UCLK/FCLK observation, PSP acceptance of modified APCB, voltage/rail measurement, performance, and flash acceptance are unrun. Archive-to-flash associations remain historical and ambiguous; photos 7/9/16 are prior report evidence, not fresh tests. Three opaque later NVAR records in SYNC images remain parser warnings outside the decoded `AmdSetup` record.
