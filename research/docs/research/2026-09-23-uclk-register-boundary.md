# UCLK actuator register boundary

Goal remains the original CLV500 BIOS candidate/instruction and verified1:1:1, not a register inventory.

## Executed result

Read-only Ghidra command executed exactSMU1F2F0 from newest matching controller template df-scalar-leaf-command.json, exit0. Output: evidence/firmware-audit/20260923-abl95fc-next/uclk-final-actuator-next.txt. Entire loaded memory equals pinned Robin5. That handler was already known; this rerun is not new actuation evidence.

Fresh independent arithmetic from the exactSMU source agrees with the September21 register map:

| domain | program  | poll     |
| ------ | -------- | -------- |
| 0E     | 0115C0FC | 0115C120 |
| 0F     | 0115C8FC | 0115C920 |
| 10     | 0115C924 | 0115C948 |
| 11     | 0116C0FC | 0116C120 |
| 12     | 0116C124 | 0116C148 |

These remain inferred candidate FCLK/UCLK paths, not independent physical names. The early PSP SVC28->SMU queue join remains unproven. No hardware operations performed.

## New source discrimination

Primary upstream AMD-authored Linux header:
https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/include/asic_reg/clk/clk_11_0_0_offset.h

Fetched matching sh_mask header too. Header block base5C800 matches the SMU group3 base, BUT its PLL_REQ is dword offset0E, byte offset38. ExactSMU2379C descriptor resolves writer to byte offset34. A shared base is therefore not sufficient evidence that this register map applies.

Compared additional primary headers clk10_0_2,clk11_0_1,clk11_5_0 via GitHub contents API at commit fe2ec83746e501645709761605c2464a44fd2929. They do not provide the required demonstrated BC250 MCLK/UCLK/FCLK relationship. Raw-download429 errors retained in action log, API fallback succeeded. First clk11_0_0 pair fetched at master, not claimed commit-pinned; exact file hashes preserved.

Literal host verifier output:

```text
PASS exact descriptor pointer arithmetic for5 domains
REJECT map equivalence: CLV writer=0x5c834; Linux clk11_0_0 PLL_REQ=0x5c838
No hardware operation, no new divider mapping
```

Result: evidence/firmware-audit/20260923-uclk-register-boundary/result.json.

## Decision

Do not transplant generic clock-register masks/offsets into a CLV patch. No synchronization setting or new OC candidate justified by this turn. No physical-clock measurement obtained.

Useful next independent evidence: a revision-matched clock-register specification or separately approved baseline hardware register observation. Hardware observation is not a flash or an overclock; it would need board identity, bounded address list, access-race handling and explicit driver-probe approval before execution. Existing transport.read_smu_reg writes the PCI selector atB8 before readingBC, and flock does not coordinate with kernel users. Do not call this write-free or unconditionally safe. No hardware reader was launched.

## Follow-up qualification: offsets34/38 do not prove different silicon

The earlier comparison only disproves assigning the exact writer to the particular published PLL_REQ offset without another link. It does NOT prove that the entire header is incompatible:34 and38 could denote two different registers in the same block. This alternative was checked against additional opened sources but neither established nor refuted.

Executed searches: gh code queries for CLK_PLL_REQ in coreboot and CLK_PLL_FREQ_REQ returned empty results (exit0). Exa searches did not yield a matching BC250 register definition. Opened AMD-authored smu_8_0_d.h and smu_8_0_sh_mask.h via GitHub contents API (exit0), neither supplied the needed clock mapping in the inspected definitions. A ps4gentoo repository-path query returned404; that failure is not evidence of content absence elsewhere. Do not claim exhaustive public-source coverage.

Result remains: no independently established register-to-physical-domain mapping, no applied1:1:1, no SoC BIOS setter. Avoid repeating these empty searches or treating another header hash as progress.
