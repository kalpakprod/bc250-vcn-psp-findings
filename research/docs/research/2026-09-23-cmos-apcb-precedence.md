# CLV500: CMOS clock can be overwritten by APCB

Scope: unchanged exact CLV ABL1 native execution, synthetic entry context and CMOS IO. No hardware, firmware patch, flash, or OC candidate. Continues A3 of `.procoder/plans/clv500-overclock-result.md`.

## Sources

- Base `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.
- ABL1 `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.
- Reopened public source https://github.com/fanoush/bc250_memcfg/blob/222420fbaeedadb7894fb0a782bdb61fa7b084af/main.cpp. CMOS layout matches native reader. This source was already catalogued in the September22 community report, not a new discovery. No utility executed or installed.
- New external source reviewed https://github.com/MastaG/linux-cachyos-bc250/blob/79728f68770d9a93a8f9df8fed43910ce548f02d/patches/linux-cachyos/0001-bc250-8core-telemetry-gpu-activity.patch. Its current/average FCLK and UCLK still alias MemclkFrequency. Voltage[0] is labelled CPU in its diagnostic while METRICS_VOLTAGE_VDDSOC still reads that element. This is code evidence against accepting field labels as independent measurement, not proof of physical rail mapping. No kernel installation.

## Observed native path

1. ABL1 77B2 accepts signature APCB or $ABL in context+510. CMOS72:94 checksum,72:96 clock and following timings are read into context+514..52B.
2. Native checksum5534 sums22 bytes. Comparison7D72 sets context+331 to1 for valid data, clears it on bad checksum. Bad checksum stages CHKE to CMOS72:90. Six acceptance cases passed, including invalid signature and checksum.
3. Native221C phase2 at2234 reads flag331 and clock516. Valid non-FFFF clock is written to nested+2C at2248.
4. It then calls1F2C for item7, phase2. A successful enum lookup writes the same nested+2C at22BA. This can overwrite accepted CMOS.
5. Full native1F2C->47D0->49CC cache construction with actual base APCB at modeled7B000 reads enum24 from APCB+482 at native4C16. ROM position is AB1482. Enum24 selects1800.
6. In-memory APCB+482=23 with corrected sum8 at+10 changes the final policy to1750. Restored APCB returns1800. Code remains unchanged.

## Literal final run

Command: `tools/abl-emulator-venv/bin/python evidence/firmware-audit/20260923-cmos-native-acceptance/native_provider.py`

```text
BASELINE: CMOS=1750 valid=1 native_provider=APCB enum=36 writes=[1750, 1800] final_policy=1800
MODIFIED_INPUT: CMOS=1650 valid=1 native_provider=APCB enum=36 writes=[1650, 1800] final_policy=1800
RESTORED_INPUT: CMOS=1750 valid=1 native_provider=APCB enum=36 writes=[1750, 1800] final_policy=1800
INVALID_CMOS: CMOS=1650 valid=0 native_provider=APCB enum=36 writes=[1800] final_policy=1800
MODIFIED_APCB: CMOS=1650 valid=1 native_provider=APCB enum=35 writes=[1650, 1750] final_policy=1750
RESTORED_APCB: CMOS=1650 valid=1 native_provider=APCB enum=36 writes=[1650, 1800] final_policy=1800
PASS 6 native APCB provider cases; APCB+482 overrides CMOS clock; code unchanged
```

Exit0, stderr empty. Earlier synthetic-provider discriminator7 cases retained separately. Restored inputs are not a flashed rollback and not an executable ROM rollback claim.

## Decision and limits

Do not recommend CMOS ClockSpeed as guaranteed controlling source on clean CLV. Candidate construction must account for APCB item7 and any runtime overlay. This explains a concrete mechanism by which a stored value can be ignored. It does not establish that a specific user's live board takes this branch or that native+2C is final physical MHz.

Actual APCB loading/overlay, subsequent training, final MCLK/UCLK/FCLK and actual SoC remain unresolved. Conditional runtime data mapping57100 and pristine APCB7B000 are explicit model assumptions reused from the prior native provider experiment. Logging130C/112A0 intercepted. No low-level hardware access.

Next: trace the newly pinned APCB item7 descriptor producer/overlay against AmdSetup MemoryClockSpeed, and follow nested+2C into final training choice. Do not repeat CMOS validation or promote the result to1:1:1. SoC-first remains a separate unclosed acceptance requirement.
