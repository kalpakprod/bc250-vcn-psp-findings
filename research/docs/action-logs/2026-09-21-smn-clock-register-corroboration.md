# 2026-09-21 SMN clock register corroboration — action log

Date: 2026-09-21 (Asia/Almaty, +05:00)  
Actor: `/root/clock_observability`  
Status: intent recorded before evidence/report creation; result pending.

## Intent

- **Target/evidence:** completed exact-CLV SMU-domain selector result `evidence/firmware-audit/20260921-smu-domain-selector/selector-result.json` and local register headers `recon/gc_10_1_0_offset.h`, `gc_10_1_0_sh_mask.h`, `gmc_10_0_0_offset.h`, `gmc_10_0_0_sh_mask.h`, `smu_v11_8_pmfw.h`.
- **Procedure:** use only the completed report's accepted example (index 11, domain ID `0x18`, Group 6) and named addresses `0x0116D150` program / `0x0116D174` poll; run one bounded local verification that checks exact, base-stripped, and low-word register-address spellings against the existing local header files and confirms their hashes. Do not rerun Ghidra, disassembly, the selector reconstruction, GoldenTSC/ATOM work, a probe, or any hardware/network operation.
- **Rationale:** determine whether the exact selector-derived SMN addresses have independent names/definitions in the project's existing register-header set. A hit can corroborate an address name; a miss is only a bounded source gap and cannot prove an undocumented/computed physical function.
- **Expected effect:** record literal match/no-match and its limited meaning, while keeping CLV `AmdSetup+0x316=0x24` untouched and not promoting Group 6/domain `0x18` to MCLK/UCLK/FCLK.
- **Rollback:** no source or input changes; remove only the new report, this log, and its unique evidence directory if invalidated.
- **Acceptance event:** one verifier process exits and records stdout/stderr/status/result and readback hashes.

## Observed result (2026-09-21T16:40+05:00)

- **Command:** `python3 -B evidence/firmware-audit/20260921-smn-clock-register-corroboration/smn_header_match_test.py`
- **Observed stdout:** `{"checks": {"failed": 0, "passed": 4, "total": 4}, "domain_id": "0x18", "domain_symbols": 31, "header_count": 5, "literal_matches": 0, "output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smn-clock-register-corroboration/smn-header-match-result.json", "poll": "0x0116D174", "program": "0x0116D150", "status": "PASS", "verdict": "NO_DIRECT_HEADER_MATCH"}`
- **Exit/status:** `0`; stderr empty (`0` bytes); checks `4/4` PASS.
- **Address readback:** selector index `11`, array entry `10`, target slot `0x140B0`, domain ID `0x18`, Group `6`, program `0x0116D150`, poll `0x0116D174`; literal header matches `0`.
- **Result:** local headers contain no direct name/address definition that independently identifies these addresses as MCLK/UCLK/FCLK/DF/UMC or divider/crossing registers. This is a bounded source gap, not an absence proof.
- **Evidence:** result JSON SHA-256 `81755d70ce15276265fdf3c31393293baae4d5782e09fa717e2d35c87d276a49`; verifier SHA-256 `322530cba29114e43ce215e1e58d250d7a6c539ff7ab04c87e41725c7bfab148`; `SHA256SUMS.final` verifies `5/5 OK`. Report SHA-256 `050a089a78106da40a4d618db9e64c32b04b06f246b1a75d8ad936ea3ba1524f`.
- **No hardware/network/repeat:** no board, sysfs, network, register, firmware, NVRAM, ROM, install, GoldenTSC/ATOM, or selector-disassembly action occurred; only the completed selector JSON was read.

## Completion status

Address corroboration is complete. The exact meaning of Group 6/domain `0x18` and SMN `0x0116D150/0x0116D174` remains unresolved; no MCLK/UCLK/FCLK identity or synchronization claim is promoted.

## G7 correction: final report readback assertion spelling

A first final readback assertion exited `1` because it searched for the exact combined phrase `MCLK/UCLK/FCLK identity`, while the report intentionally separates the terms in prose/table text. The corrected assertion searched for the stable substring `MCLK/UCLK/FCLK` and reran with exit `0`, emitting `PASS result=4/4 program=0x0116D150 poll=0x0116D174 literal_matches=0 physical_clock_identity=unresolved`. No artifact or input changed.
