# Linux callback versus BIOS direct-writer distinction

Date: 2026-09-21 (Asia/Almaty). Evidence class: `static-analysis` / `observed-bytes` for the re-opened Linux source copies; `historical-report` for the prior BIOS and AMD reports. No new ROM bytes were decoded, and no firmware write, BIOS command, or hardware operation was performed.

## Verdict

**The Linux callback anomaly must not be transferred to the BIOS direct-writer path, and AMD's extracted generic `1.1 V` guidance must not be transferred to a custom BC-250 SoC/GDDR6 setting.** The two boundaries are separate and both remain qualified static evidence.

## Claim decisions

### A1 — ACCEPT: Linux positive return is from `write_word_data`, not `read_word_data`

`docs/research/2026-09-21-luna-vout-write-callback-verification.md:8,29,31-39` explicitly traces `isl69247` to the `raa_dmpvr2_2rail` probe arm and the `raa_dmpvr2_write_word_data()` `PMBUS_VOUT_COMMAND` case. The pinned Linux source copies are:

- `/tmp/luna-isl68137.c`, SHA-256 `2b0791dd0075d5dd1b5c5b7264ab9cafe783cd58d4b686546c00172cb3ef9c9f`;
- `/tmp/luna-pmbus_core.c`, SHA-256 `232a430a5950c56bd10aa521cb085fd749ad9412d39b097a4875c7c9a63b9316`;
- `/tmp/luna-callback-pmbus.h`, SHA-256 `e893b3ea228675253e34b41b0a6b4d21a0441690b76b7d575e29673109ee33cb`.

The report's `PASS 14/14` source assertions and exit `0` are accepted as the already recorded static reproduction.

### A2 — ACCEPT: the Linux result is a callback-contract anomaly, not an observed PMBus write

The reviewed report lines `10`, `34-39`, and `53-55` correctly state that the write callback returns a positive clamped value, the core returns any non-`-ENODATA` callback result before fallback, and the callback itself contains no low-level `pmbus_write_word_data()` call. The report correctly refuses to claim a PMBus command, bus transaction, physical voltage, or runtime failure.

### A3 — ACCEPT: BIOS direct-writer evidence is a distinct static route

Existing pinned CLV reports identify two PEI modules reading the Setup variable and staging EC-window transactions: `docs/research/2026-09-20-clv-fixed-voltage-consumer.md:7-26,73-119`; the board-writer inventory independently records exactly two complete EC-window writer modules: `docs/research/2026-09-20-bc250-board-voltage-sources.md:42-78,107-128`. This route uses PEI Setup reads, x86 port I/O (`0x2E/0x2F`, `0xA20/0xA21/0xA22`) and mailbox staging (`0x65/0x66/0x70/0x71/0x63/0x60`), not the Linux `pmbus_core` callback API. I accept this route distinction at the report boundary; this review did not re-decode the ROM bytes, per the no-repeat instruction.

The BIOS report's own boundary is accepted: physical rail identity, PMBus/register semantics, PEI dispatch, applied voltage, and hardware behavior remain unverified. Thus “static direct-writer route exists” is accepted; “BIOS successfully writes a physical voltage” is not accepted.

### R1 — REJECT: transfer of the Linux callback anomaly to BIOS

The Linux positive-return mismatch is a kernel callback/API-contract fact in `isl68137.c` + `pmbus_core.c`; it does not imply that the BIOS PEIM's EC/mailbox path is broken, returns the same status, or emits no transaction. Although both sources use the `ISL69247` label, that name alone is not a caller/callee or transport join: the Linux host driver callback and BIOS PEI mailbox writer are distinct code paths. Conversely, the prior BIOS report cannot repair or falsify the Linux callback-contract mismatch. Any statement that the BIOS writer “inherits” the Linux positive-return bug is rejected as a layer error.

### R2 — REJECT: relabeling BIOS VCORE/GFX/MEMIO fields as SoC from these records

The BIOS report labels fields/actions as VCORE, GFX, and MEMIO (`docs/research/2026-09-20-clv-fixed-voltage-consumer.md:11-14,75-102`) but explicitly says physical rail identity and register semantics are unverified (`:115-119`). These labels are not a proven SoC mapping. The Linux `PSC_VOLTAGE_OUT` class and `VOUT_COMMAND` conversion likewise do not identify a BC-250 SoC rail or page. Such a cross-label is rejected.

### R3 — REJECT: transferring AMD generic 1.1 V guidance to BC-250

`docs/research/2026-09-21-amd-guidance-boundary.md:20-24,35-40` scopes the extracted `1.1 V` text to Ryzen 3000-Series memory/fabric overclocking and the surrounding DDR4 discussion; it explicitly rejects a BC-250/GDDR6 prescription. The PDF recheck further qualifies the evidence: `docs/research/2026-09-21-amd-guide-pdf-recheck.md:7-19,28-34` records that the original PDF was unavailable, the extracted text says `CLDP VDDG`, and the extraction does not establish a VDDG/SoC equality or electrical relationship. Therefore neither a universal manual SoC `1.1 V` nor `1.15 V` recommendation for BC-250 follows.

## Scoped conclusion

Accepted: the Linux source finding is a static `write_word_data` callback anomaly; the BIOS evidence is a separate static PEI/EC mailbox writer path; AMD's extracted DDR4/Ryzen-3000 starting-value text is context-limited. Rejected: any conclusion that the Linux anomaly proves BIOS failure, that BIOS VCORE/GFX/MEMIO labels prove SoC identity, or that generic `1.1 V` guidance is a BC-250/GDDR6/BIOS target.

No new runtime or hardware evidence was produced. The next decisive checks would be different-layer tests (kernel/mock PMBus path for Linux; PEI dispatch/EC readback or board measurement for BIOS), but none is run or requested by this review.
