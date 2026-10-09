# ISL69247 write callback: exact pinned source path

Date: 2026-09-21 (Asia/Almaty)
Scope: independently verify whether the earlier positive result belongs to `write_word_data` or `read_word_data`; trace the `isl69247` match through the full probe switch and the core callback/fallback for `VOUT_COMMAND`. This is exact source inspection only; no bus/hardware execution.

## Result

**The positive result is returned by the assigned `write_word_data` callback, not the `read_word_data` callback.** The `isl69247` I2C and OF match entries both select `raa_dmpvr2_2rail`; that probe arm installs both distinct callbacks. In `pmbus_regulator_set_voltage()`, Linux first computes a voltage-out-class register value and then calls `_pmbus_write_word_data(..., PMBUS_VOUT_COMMAND, ...)`. That wrapper invokes the assigned write callback, and the driver's `PMBUS_VOUT_COMMAND` case returns its positive clamped divider-adjusted word.

**Correction/limit:** pinned core source short-circuits on any callback result other than `-ENODATA`; the core's documented callback contract is zero on successful write. The callback body does not call `pmbus_write_word_data()` or a low-level write. Consequently, for this exact regulator-set path, the source does not show a fall-through/default PMBus write after the positive return. This is a static callback-contract discrepancy, not proof of a runtime driver failure, physical chip behavior, or board voltage. No bus transaction was attempted.

## Match and complete probe switch

Pinned driver: [`drivers/hwmon/pmbus/isl68137.c`](https://github.com/torvalds/linux/blob/6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9/drivers/hwmon/pmbus/isl68137.c), commit `6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9`, SHA-256 `2b0791dd0075d5dd1b5c5b7264ab9cafe783cd58d4b686546c00172cb3ef9c9f` (17,407 bytes). The file is byte-identical to the already pinned source capture. Its I2C ID line 436 and OF compatible line 489 both map `isl69247` to `raa_dmpvr2_2rail`.

At `isl68137_probe()` lines 325-408 the code copies `raa_dmpvr_info` to the per-device structure before the switch, then handles every variant as follows:

| Switch arm               | Result before `pmbus_do_probe()`                                                                                                             |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `raa_dmpvr1_2rail`       | 2 pages; adjusts VIN exponent and functionality; installs `raa_dmpvr2_read_word_data` and `raa_dmpvr2_write_word_data`; adds AVS sysfs group |
| `raa_dmpvr2_1rail`       | 1 page; installs the read and write callbacks                                                                                                |
| `raa_dmpvr2_2rail_nontc` | clears `PMBUS_HAVE_TEMP3` for pages 0/1, then falls through                                                                                  |
| `raa_dmpvr2_2rail`       | 2 pages; installs the read and write callbacks; does not override VOUT `format/m/b/R`                                                        |
| `raa_dmpvr2_2rail_pmbus` | changes IN/OUT voltage, current, power, and temperature formats to `linear`; 2 pages; installs both callbacks                                |
| `raa_dmpvr2_3rail`       | retains its three-page base; installs both callbacks                                                                                         |
| `raa_dmpvr2_hv`          | 1 page; changes VIN `R`, VOUT `m=2,R=2`, IIN `m=2`, and power `m=2,R=-1`; installs both callbacks                                            |
| `default`                | immediately returns `-ENODEV`; no `pmbus_do_probe()` call                                                                                    |

All successful switch cases then parse any device-tree divider data and call `pmbus_do_probe()` (`:404-408`). This verifies that the selected `isl69247` variant actually installs `write_word_data=raa_dmpvr2_write_word_data`; it is not a `read_word_data` result mislabeled by the previous report.

## Exact `VOUT_COMMAND` callback and core fallback

- Driver `raa_dmpvr2_read_word_data()` is a separate function (`isl68137.c:151-185`). Its `READ_VOUT` case reads the command with `pmbus_read_word_data()` and applies the configured `Rtotal/Rout` read divider (`:164-178`).
- Driver `raa_dmpvr2_write_word_data()` is separately declared (`:188-215`). Its switch explicitly includes `PMBUS_VOUT_COMMAND` (`:196-203`) and computes the reverse divider `Rout/Rtotal`; it returns `clamp_val(temp, 0, 0xffff)` (`:210-214`). That function contains no `pmbus_write_word_data()` call.
- For regulator writes, `pmbus_core.c:334-355` defines `_pmbus_write_word_data()`: call `info->write_word_data` when present; return its result immediately unless the result is exactly `-ENODATA`; only otherwise reach the normal `pmbus_write_word_data()` fallback. The exact positive result from the driver therefore does not reach that fallback in this source path.
- `drivers/hwmon/pmbus/pmbus.h:450-467` says the mapping callbacks return a register value for reads or **zero for a successful write**. The driver write callback's positive return is inconsistent with that documented contract; this is the bounded mismatch.
- `pmbus_core.c:3319-3377` distinguishes the two regulator methods: `get_voltage()` reads `PMBUS_READ_VOUT`; `set_voltage()` uses a `PSC_VOLTAGE_OUT` sensor, converts with `pmbus_data2reg()`, and passes the result to `_pmbus_write_word_data(..., PMBUS_VOUT_COMMAND, ...)`.

This precisely settles the source question: the positive integer originates in a write callback for `VOUT_COMMAND`, but the pinned core interprets it as the callback's handled status, not as a replacement word to be written. Do not claim that a PMBus command was emitted from this static source trace.

## Coefficient scope retained from the prior report

The same pinned driver maps `isl69247` to the `raa_dmpvr2_2rail` arm, which inherits `raa_dmpvr_info`'s VOUT `direct, m=1,b=0,R=3` profile (`isl68137.c:222-247, 345-373, 436, 489`). The pinned core has one coefficient array per sensor class and regulator `set_voltage()` uses `PSC_VOLTAGE_OUT`. Therefore the Linux _software conversion_ uses the same class-level values as `READ_VOUT`; this does not prove distinct device-level write/read coefficients, successful bus transfer, PMBus page identity, or actual board voltage. The earlier full qualification, official PMBus spec result, VOUT_MODE and platform-data caveats remain in `docs/research/2026-09-21-luna-vout-command-format.md`.

## Reproduction and verification

Inputs:

- `/tmp/luna-isl68137.c`, SHA-256 `2b0791dd0075d5dd1b5c5b7264ab9cafe783cd58d4b686546c00172cb3ef9c9f`.
- `/tmp/luna-pmbus_core.c`, SHA-256 `232a430a5950c56bd10aa521cb085fd749ad9412d39b097a4875c7c9a63b9316`.
- `/tmp/luna-callback-pmbus.h`, freshly fetched at the same pinned commit; SHA-256 `e893b3ea228675253e34b41b0a6b4d21a0441690b76b7d575e29673109ee33cb`.

Executed read-only command sequence: hash the driver/core copies; fetch only `drivers/hwmon/pmbus/pmbus.h` from the pinned GitHub Contents API into `/tmp`; run an inline Python source assertion check for both ID mappings, both callback assignments, inherited coefficient fields, the `PMBUS_VOUT_COMMAND` case, positive clamp/return and no in-callback I/O call, the core callback-first/`-ENODATA` fallback order, the documented callback return contract, and the regulator setter's class/command path. Literal output: `PASS 14/14`, then 14 named `PASS` lines. Command exited `0`.

Evidence class: `static-analysis` of pinned upstream source plus byte hashes. No mock I2C transaction, driver build, live bus, board access, register operation, NVRAM/firmware write, or voltage measurement was performed. Remaining unknowns: whether this code path is exercised at runtime, actual part coefficients, active platform data, actual PMBus transfer, and physical output/rail identity.
