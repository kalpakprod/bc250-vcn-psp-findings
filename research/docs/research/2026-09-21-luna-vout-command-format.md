# ISL69247 VOUT_COMMAND format: Linux implementation vs PMBus device semantics

Date: 2026-09-21 (Asia/Almaty)
Scope: determine whether the exact Linux `isl69247` profile encodes `VOUT_COMMAND` with the same direct coefficients it uses for `READ_VOUT`; account for `VOUT_MODE` and optional platform-data coefficient handling; independently review the narrow claims in `luna-bc250-rail-evidence-current.md`.

## Conclusion

There are two different answers at two evidence layers:

1. **Linux software path — yes, one shared profile.** The `isl69247` I2C and OF matches select `raa_dmpvr2_2rail`. That branch copies `raa_dmpvr_info`, whose `PSC_VOLTAGE_OUT` fields are `format=direct, m=1, b=0, R=3`. In the pinned core, regulator `get_voltage()` reads `READ_VOUT` with class `PSC_VOLTAGE_OUT`; `set_voltage()` builds the same class, converts through the same class-level `pmbus_data2reg()` coefficient array, and passes the result to `VOUT_COMMAND`. The driver struct explicitly stores one m/b/R set per sensor class. Thus the **Linux arithmetic path** reuses the same class profile for read and set.
2. **Exact ISL69247 command coefficients — unresolved.** The official PMBus specification says the coefficients for setting and reading a parameter such as output voltage _may differ_. Its `COEFFICIENTS` command distinguishes command code and read-vs-write direction. The optional Linux coefficient loader requests only the `READ_VOUT` read coefficients and stores them into the single shared `PSC_VOLTAGE_OUT` set; it does not request `VOUT_COMMAND` write coefficients. Renesas's public page for this part returned 404, and its exact-part Datasheets search returned no ISL69247 datasheet. Therefore source code and the checked public docs do not prove that the physical controller's `VOUT_COMMAND` write coefficients equal its `READ_VOUT` coefficients.

`VOUT_MODE` selects/validates the broad output-voltage data format (e.g. Direct), not the direct m/b/R coefficients. The mode is shared for output-voltage-related commands under the PMBus specification, but that does not force identical encode/decode coefficients.

A further source-level limitation: for this two-rail variant the pinned driver installs a custom `write_word_data` callback. Linux's callback contract says a successful write callback returns zero, while this driver's VOUT callback returns the computed positive clamped word and does not call `pmbus_write_word_data()`. The core returns any callback result other than `-ENODATA` without falling through to the default bus write. So the inspected code does **not** demonstrate a resulting VOUT_COMMAND bus transaction; this is a static callback-contract discrepancy to review, not a hardware observation.

No page-to-SoC/core/GFX mapping, BIOS-to-PMBus equivalence, applied voltage, or safe voltage is established. No voltage is recommended.

## Pinned Linux source and exact trace

Read-only Agent Reach GitHub (`gh` CLI) fetch, pinned to Torvalds Linux commit `6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9`, commit time `2026-09-20T18:21:10Z`:

- [`drivers/hwmon/pmbus/isl68137.c`](https://github.com/torvalds/linux/blob/6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9/drivers/hwmon/pmbus/isl68137.c), SHA-256 `2b0791dd0075d5dd1b5c5b7264ab9cafe783cd58d4b686546c00172cb3ef9c9f`, 17,407 B.
- [`drivers/hwmon/pmbus/pmbus_core.c`](https://github.com/torvalds/linux/blob/6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9/drivers/hwmon/pmbus/pmbus_core.c), SHA-256 `232a430a5950c56bd10aa521cb085fd749ad9412d39b097a4875c7c9a63b9316`, 101,262 B.
- [`drivers/hwmon/pmbus/pmbus.h`](https://github.com/torvalds/linux/blob/6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9/drivers/hwmon/pmbus/pmbus.h), SHA-256 `e893b3ea228675253e34b41b0a6b4d21a0441690b76b7d575e29673109ee33cb`.
- [`include/linux/pmbus.h`](https://github.com/torvalds/linux/blob/6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9/include/linux/pmbus.h), SHA-256 `5c5394059c0820d8fa8f20f677fc3e5119cedc34e31e01a28c9d079f836cb9ab`.

Relevant exact lines:

- `isl68137.c:222-247`: `raa_dmpvr_info` sets `PSC_VOLTAGE_OUT` to direct / `m=1,b=0,R=3`.
- `isl68137.c:325-408, 436, 489`: probe copies that struct; I2C ID `isl69247` and OF compatible `renesas,isl69247` select `raa_dmpvr2_2rail`; its arm sets two pages and installs callbacks without changing those coefficients.
- `pmbus_core.c:1929-1966, 2642-2668`: `READ_VOUT` is the voltage-out sensor attribute and sole `PSC_VOLTAGE_OUT` coefficient source in this attribute class.
- `pmbus_core.c:907-945, 986-1005`: `READ_VOUT` conversion uses `info->m/b/R[PSC_VOLTAGE_OUT]` via `pmbus_reg2data()`.
- `pmbus_core.c:3319-3377`: `get_voltage()` uses `READ_VOUT`; `set_voltage()` uses `PSC_VOLTAGE_OUT`, calls `pmbus_data2reg()`, and passes the result with register `PMBUS_VOUT_COMMAND`.
- `pmbus_core.c:1143-1176, 1204-1222`: the direct write-side arithmetic also indexes the same `info->m/b/R[sensor->class]` array.
- `drivers/hwmon/pmbus/pmbus.h:440-467`: the core data structure documents one coefficient set per sensor type and documents write callbacks as returning zero on success.
- `pmbus_core.c:334-355`: `_pmbus_write_word_data()` returns any callback result other than `-ENODATA`, without calling the default `pmbus_write_word_data()`.
- `isl68137.c:188-215`: `raa_dmpvr2_write_word_data()` handles `PMBUS_VOUT_COMMAND` by scaling the provided word by `Rout/Rtotal`, assigning the clamped result to its return value; the function contains no `pmbus_write_word_data()` call. `isl68137.c:369-373` installs this callback for `raa_dmpvr2_2rail`.

### VOUT_MODE behavior

At `pmbus_core.c:2743-2780`, `pmbus_identify_common()` reads `PMBUS_VOUT_MODE` when the byte register is supported. For a valid non-`0xFF` response it checks the top three mode bits against the driver's preselected format: ULINEAR16 must match `linear`, VID must match `vid`, Direct must match `direct`, and IEEE-754 must match `ieee754`; mismatch returns `-ENODEV`. A missing/failed check or `0xFF` skips this validation. For Direct mode, the code does not derive or update m/b/R from the low parameter bits. It therefore validates the configured format; it does not establish chip-specific write coefficients. The core also does not validate the Direct-mode low five parameter bits against the PMBus requirement of zero.

### Optional COEFFICIENTS override

- `pmbus_core.c:3856-3903` copies `pmbus_platform_data.flags` into `data->flags` when platform data is present.
- `include/linux/pmbus.h:69-74` defines `PMBUS_USE_COEFFICIENTS_CMD`.
- `pmbus_core.c:2972-2980` invokes `pmbus_init_coefficients()` only when this flag is set.
- `pmbus_core.c:2673-2705` sends `attr->reg` with direction byte `0x01` and stores the returned m/b/R in that attribute's sensor class; `pmbus_core.c:2709-2737` selects the first attribute in each direct-mode class.
- For `PSC_VOLTAGE_OUT`, the matching attribute is `PMBUS_READ_VOUT` (`:1955-1965`). The Linux override therefore asks for READ_VOUT/read coefficients (direction `0x01`) and places that single result into the shared class array. It does not request `PMBUS_VOUT_COMMAND` write coefficients (direction `0x00`). Whether BC-250 platform data enables this flag is unknown; no running kernel or platform-data object was queried.

## Official protocol documentation and chip-specific documentation search

Official PMBus standards-site archive:

- Archive page: https://pmbus.org/specification-archives/; Jina capture SHA-256 `865301aebb11c028526d33854106882dccfcddaf06a3af0fc3948168040ce9c1`.
- Public archived specification: [PMBus Specification Rev. 1.3.1 Part II](https://pmbusprod.wpenginepowered.com/wp-content/uploads/2022/01/PMBus-Specification-Rev-1-3-1-Part-II-20150313.pdf), 121 pages, PDF SHA-256 `1717c59615032ea66bf867316e4be076bfa10bf983dab9aff9b7ed4aed2c7ec6` (678,599 B). The current-specifications page says revision 1.5 is current and available by request/registered adopter access; this check used the publicly archived 1.3.1 text and makes no claim to have retrieved revision 1.5.
- Section 7.4.3, p. 24: host must know m/b/R for Direct operations; manufacturer literature may supply them; for one parameter (such as output voltage), encode and decode coefficients “may not be the same.”
- Section 8.3, pp. 27-28: `VOUT_MODE` selects the mode/parameter for output-voltage-related commands. Section 8.4.3, p. 30: Direct-format `VOUT_COMMAND` uses m/b/R to encode its transmitted value.
- Section 14.1, p. 72: `COEFFICIENTS` request includes the command code plus direction (`0x01` for coefficients to decode a read, `0x00` for coefficients to encode a write).
- Section 18.4, p. 98: `READ_VOUT` is actual measured—not commanded—output voltage, in the mode selected by `VOUT_MODE`.

Renesas official-site checks (retrieved 2026-09-21 via Jina Reader):

- `https://www.renesas.com/en/products/isl69247` returned a 404 capture (807 B, SHA-256 `650639657939aba0db94b2d2d53f37992c21916762c0c9201d899fdd272781ca`).
- Official search `https://www.renesas.com/us/en/search?keywords=ISL69247&docType%5B0%5D=Datasheets&page=1` returned four Datasheet-filtered results; none is ISL69247 (the listed parts include ISL69147, ISL69144, and ISL6209). Capture: 21,440 B, SHA-256 `ab6198f3c285cd01f457f2394d57244be657cfc482489af568cb65878289b047`.
- This is a bounded search result, not proof no exact datasheet is available through another catalog or channel. No neighboring-part datasheet is substituted for ISL69247 evidence.

## Independent review of the existing BC-250 rail-evidence report

Reviewed only the focused report and its cited identifying source, not the larger firmware corpus:

- `docs/research/luna-bc250-rail-evidence-current.md` SHA-256 `482de15b75c9ee139611ff4e737c05e225133b49b28adcd1e059b1b259803bf3` was reopened. Its F1 source was independently fetched at commit `1cf461b7766d43b22753f136020b304a90d80c61`: `mothenjoyer69/bc250-documentation/hardware.md` SHA-256 `23659e162daaac67c07bd9af116e275a6bfab751bbfa3a1fd8831eb21e3f837f` (lines 35, 172-188). The source labels PUA1 “ISL69247 / Main PMIC” and PUIO1 “ISL95712 / Core supply PMIC,” while saying I2C appears to host PMBus communications; it provides no PMBus page/net-to-SoC mapping. The pinned annotated board image hash `c96660be7407302ebe0c9a79a4659061a1496d0216c8541fb8b18238cd02b4bf` was independently retrieved and viewed: it marks chip locations, not voltage nets or PMBus pages. This supports controller-identification provenance but not a physical rail mapping.
- The rail report's F3 summary and prior `docs/research/luna-isl69247-format-current.md` (SHA-256 `688379f4371a2dba41a4129403c070b11481cf11f1f12e3eab580d773a52dbc3`) are accurate about the Linux shared-class arithmetic path. Add the qualification established here: shared Linux coefficients do not prove identical device-level write/read coefficients, and the source-level callback path does not demonstrate an emitted VOUT_COMMAND I2C transaction.
- The rail report's F4 summary cites the exact-clv fixed-voltage consumer report. That report's own boundary says firmware mailbox identity, PMBus semantics, physical rail identity, and applied voltage are unverified. The observed firmware writes described as command/register `0x00` with values `0` and `1` are static staged bytes; without controller/mailbox identity and PMBus semantics they cannot be equated to Linux PMBus `PAGE` or to ISL69247 pages 0/1. The page-to-SoC/core/GFX gap remains open.

The independent rail-review conclusion is unchanged: the checked community evidence supports “PUA1 is identified as ISL69247 Main PMIC,” not which output/page drives SoC. No exact device write coefficients, physical rail mapping, BIOS/PMBus bridge, runtime binding, physical voltage, or safety limit is established.

## Reproduction and acceptance ledger

Read-only checks executed:

```sh
agent-reach doctor --json
gh api "repos/torvalds/linux/contents/drivers/hwmon/pmbus/isl68137.c?ref=6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9"
gh api "repos/torvalds/linux/contents/drivers/hwmon/pmbus/pmbus_core.c?ref=6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9"
gh api "repos/torvalds/linux/contents/drivers/hwmon/pmbus/pmbus.h?ref=6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9"
gh api "repos/torvalds/linux/contents/include/linux/pmbus.h?ref=6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9"
gh api "repos/mothenjoyer69/bc250-documentation/contents/hardware.md?ref=1cf461b7766d43b22753f136020b304a90d80c61"
curl -fsSL "https://r.jina.ai/https://pmbus.org/specification-archives/"
curl -fsSL "https://r.jina.ai/https://pmbus.org/current-specifications/"
curl -fsSL "https://r.jina.ai/https://www.renesas.com/us/en/search?keywords=ISL69247&docType%5B0%5D=Datasheets&page=1"
curl -fsSL "https://pmbusprod.wpenginepowered.com/wp-content/uploads/2022/01/PMBus-Specification-Rev-1-3-1-Part-II-20150313.pdf"
pdfinfo /tmp/pdfs/luna-pmbus-1.3.1-part2.pdf
pdftotext -layout /tmp/pdfs/luna-pmbus-1.3.1-part2.pdf /tmp/pdfs/luna-pmbus-1.3.1-part2.txt
```

A GitHub Contents API attempt to retrieve the >1 MB board image yielded an empty `content` field; the API-provided pinned `download_url` was then fetched successfully and its hash matched the report. A first guessed Renesas product URL returned 404; the official site search page was then checked. No live I2C/SMBus/bus command, board access, ROM/NVRAM/register write, or voltage measurement was performed.

- Passed: pinned Linux source identity/fresh fetch; exact match/probe-to-shared-coefficient trace; VOUT_MODE and platform-data branches; official PMBus clauses; independent hash/readback of cited BC-250 identification source/image.
- Unresolved/unrun: exact ISL69247 `VOUT_COMMAND` write coefficients; active BC-250 platform-data flag and running Linux binding; emitted PMBus command transaction; PMBus page-to-physical-rail mapping; BIOS/PEIM-to-PMBus correspondence; any applied voltage or safety assessment.
