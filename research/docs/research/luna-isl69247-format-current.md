# ISL69247 VOUT format applicability in the current Linux PMBus driver

Later source-boundary update: the [VOUT command review](2026-09-21-luna-vout-command-format.md) found that shared Linux read/write arithmetic does not establish identical device coefficients. Its [callback verification](2026-09-21-luna-vout-write-callback-verification.md) found no demonstrated fall-through bus write on the pinned regulator-set path. Statements below about a setter writing `VOUT_COMMAND` describe the core's intended call path, not an observed emitted transaction or applied voltage.

Date: 2026-09-21 (Asia/Almaty)
Scope: verify whether the Linux `isl68137` driver's `raa_dmpvr_info` VOUT direct coefficients are selected for `isl69247`, trace the two distinct VOUT read/setpoint paths, and state what this does not establish for BC-250 BIOS OC.

## Finding

**Yes, the source-level `isl69247` match selects the `raa_dmpvr2_2rail` probe branch, which starts from `raa_dmpvr_info` and retains its VOUT `format=direct, m=1, b=0, R=3` defaults.** That is the driver's static default profile for this chip ID; it is not merely an unrelated struct occurrence.

This is conditional source evidence, not proof that a particular BC-250 Linux kernel bound this driver, which PMBus page is SoC, or which coefficients were active at runtime. The PMBus core can replace direct coefficients if platform data enables `PMBUS_USE_COEFFICIENTS_CMD`; no target runtime/platform-data state was inspected. The Linux PMBus path is also not shown to be the BIOS PEIM's separate EC/Super-I/O mailbox protocol.

## Exact source and provenance

Retrieved read-only via Agent Reach's GitHub route (`gh` CLI; OpenCLI help was inspected first) from Torvalds' Linux repository, pinned to commit `6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9` (commit time `2026-09-20T18:21:10Z`):

- Driver: `https://github.com/torvalds/linux/blob/6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9/drivers/hwmon/pmbus/isl68137.c`
  - SHA-256 `2b0791dd0075d5dd1b5c5b7264ab9cafe783cd58d4b686546c00172cb3ef9c9f`, 17,407 bytes.
  - Relevant lines: 222-247 (default coefficients); 325-408 (probe initialization and variants); 436 (I2C ID mapping); 489 (OF compatible mapping); 151-185 (read callback); 188-215 (write callback); 264-305 (optional divider configuration).
  - Preserved local copy `/tmp/bc250-isl68137.c` has the same size and hash; `cmp` against the pinned copy exited `0`.
- PMBus core: `https://github.com/torvalds/linux/blob/6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9/drivers/hwmon/pmbus/pmbus_core.c`
  - SHA-256 `232a430a5950c56bd10aa521cb085fd749ad9412d39b097a4875c7c9a63b9316`, 101,262 bytes.
  - Relevant lines: 907-945 and 986-1005 (direct register-to-sensor conversion); 1143-1176 and 1204-1222 (sensor-to-register conversion); 1955-1965 (READ_VOUT is PSC_VOLTAGE_OUT); 1334-1341 (sensor read then conversion); 3320-3376 (regulator get/set path); 2972-2980 and 3891-3903 (optional coefficient-command/platform-data path).
- Driver SPDX header: `GPL-2.0+`.

## Source trace: match to selected coefficients

1. The I2C ID table maps `.name = "isl69247"` to `raa_dmpvr2_2rail` (`isl68137.c:436`). The OF table independently maps `.compatible = "renesas,isl69247"` to the same variant (`:489`).
2. `isl68137_probe()` initializes the channel-divider state, copies `raa_dmpvr_info` into per-device `data->info` (`:336-347`), then switches on the matched variant (`:348`).
3. The common struct declares `PSC_VOLTAGE_OUT` as `direct`, `m=1`, `b=0`, `R=3` (`:222-247`). The `raa_dmpvr2_2rail` arm sets `pages=2` and installs read/write callbacks (`:369-373`); it does not replace those VOUT format/coefficient fields. Thus the profile does reach the `isl69247` branch.
4. The distinct `raa_dmpvr2_2rail_pmbus` arm changes formats to `linear` (`:374-384`), but `isl69247` is not mapped to that variant. The high-voltage arm changes VOUT to `m=2,R=2` (`:389-399`), also not selected for `isl69247`.

## READ_VOUT telemetry versus VOUT_COMMAND setpoint

- **`PMBUS_READ_VOUT` is measured-output telemetry.** The sensor map assigns it to `PSC_VOLTAGE_OUT` (`pmbus_core.c:1955-1965`). The chip-specific read callback handles `PMBUS_READ_VOUT` by reading that command (`isl68137.c:164-178`) and, when configured, scaling the returned raw word by the channel's `Rtotal/Rout` divider ratio. The core then converts the raw result using direct-mode `m,b,R` (`pmbus_core.c:907-945, 986-1005, 1334-1341`). For `m=1,b=0,R=3`, the core's voltage-to-milli-unit path leaves the raw word numerically in mV; e.g. code `1150` converts to `1150 mV` before any channel divider correction. This is a software format conversion, not a physical reading reproduced here.
- **`PMBUS_VOUT_COMMAND` is a setpoint command, not the measured output.** The regulator setter converts a requested value in mV to the direct-format register word, then calls the `PMBUS_VOUT_COMMAND` write wrapper (`pmbus_core.c:3341-3376`). The chip-specific write callback handles that command and applies the inverse channel-divider ratio, `Rout/Rtotal`, but the later callback review found no demonstrated fall-through bus write (`isl68137.c:188-215`). Under the static default `m=1,b=0,R=3` and a 1:1 channel ratio, if 1150 mV is within the queried low/high margins, the host-side request maps to word `1150`; that is software setpoint encoding, not evidence of an emitted command or safe/applied 1.15 V rail.
- The driver's AVS helper also reads an existing `PMBUS_VOUT_COMMAND` and writes the same command back before switching AVS control (`isl68137.c:68-106`). That is preservation of a setpoint command, not a `READ_VOUT` measurement.
- A device-tree `vout-voltage-divider` can alter both read and write scaling (`isl68137.c:264-305`). The driver initializes default numerator and denominator fields identically (`:336-343`), so its default ratio is unity; no BC-250 device-tree setting was checked.

## Applicability and safety boundary

- The direct coefficient is established for the Linux driver branch's static default. `pmbus_core.c` only calls `pmbus_init_coefficients()` when `data->flags & PMBUS_USE_COEFFICIENTS_CMD` (`:2972-2980`); `pmbus_do_probe()` sources those flags from optional platform data (`:3856-3903`). Such a flag can replace direct coefficients from device-reported values. Whether any BC-250 host supplies it is **unknown**.
- Neither the I2C ID nor the OF compatible entry proves that the BC-250's actual VR controller is this chip or that the driver is bound. Linux page numbers 0/1 are not identified as SoC/core rails by this driver source.
- This driver speaks PMBus/I2C. Existing BC-250 firmware notes describe a separate PEI mailbox/Super-I/O path; this source does not bridge that protocol to BIOS Setup fields or establish that BIOS writes use the same units, register, page, or conversion.
- Keep the requested memory baseline `1800` unchanged for this OC track. Treat SoC `1.15 V` only as the operator's target boundary, not a proven safe ceiling or recommended setpoint. Nothing in this source establishes board-specific voltage limits, silicon margin, thermal/current margin, rail identity, BIOS applicability, or physical voltage.

## Reproduction and checks

Agent Reach discovery and read-only source retrieval:

```sh
agent-reach doctor --json
opencli --help
opencli github --help -f yaml
opencli gh --help
gh api repos/torvalds/linux/commits/master --jq .sha
# Output: 6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9
REV=6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9
gh api "repos/torvalds/linux/contents/drivers/hwmon/pmbus/isl68137.c?ref=$REV" --jq .content | tr -d '\n' | base64 -d > /tmp/luna-isl68137.c
gh api "repos/torvalds/linux/contents/drivers/hwmon/pmbus/pmbus_core.c?ref=$REV" --jq .content | tr -d '\n' | base64 -d > /tmp/luna-pmbus_core.c
sha256sum /tmp/luna-isl68137.c /tmp/luna-pmbus_core.c
cmp -s /tmp/bc250-isl68137.c /tmp/luna-isl68137.c
```

Observed source retrieval: driver `17,407` bytes, hash above; core `101,262` bytes, hash above; local-vs-pinned driver `cmp` exit `0`. Initial API request used the guessed path `drivers/hwmon/isl68137.c` and returned HTTP 404 (`base64: invalid input`); the actual source path is under `drivers/hwmon/pmbus/`. The corrected fetch succeeded.

Checks: source identity/pinned fetch **passed**; I2C/OF match-to-variant and variant-to-default-coefficient trace **passed**; distinction between READ_VOUT and VOUT_COMMAND **passed at source level**; runtime driver binding, active coefficient override, BC-250 page/rail mapping, BIOS/hardware behavior, and voltage safety **unrun/unknown**. No ROM, NVRAM, bus, register, candidate, or hardware operation was performed.
