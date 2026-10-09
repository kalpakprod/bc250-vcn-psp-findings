# BC-250 public PMIC identification and ISL69247 rail/page gap

Later qualifications: the [VOUT command review](2026-09-21-luna-vout-command-format.md) distinguishes shared Linux software coefficients from unknown device write coefficients and finds no demonstrated bus write on the pinned callback path. The project also has a local primary CAD file named in [current context](../CURRENT-CONTEXT.md); this 2026-09-21 public-source review did not inspect it for rail nets. A local CAD file is not, by itself, a verified page-to-SoC map.

Current: a public BC-250 community board reference identifies PUA1 as an Intersil ISL69247 “Main PMIC” and PUIO1 as an ISL95712 “Core supply PMIC”; no checked public source assigns ISL69247 page 0/1 to CPU, SoC, or GFX. No voltage recommendation.

## Findings

### F1 — Board-specific component identification is available, but is community documentation

The public `mothenjoyer69/bc250-documentation` repository's `hardware.md` contains an “Auxiliary Chip ID” table beside a numbered board image. In the table, row 2 identifies designator `PUIO1` as `Intersil ISL95712` / “Core supply PMIC”; row 3 identifies `PUA11, etc` as `Intersil ISL99360` / “Smart Power Stage (phase controller)”; row 4 identifies `PUA1` as `Intersil ISL69247` / “Main PMIC.” The same file says the I2C header “appears to host PMBUS communications to the Intersil PMICs” and warns that some discrete MOSFETs and voltage regulators are omitted.

This is useful public, BC-250-specific physical-part evidence independent of the firmware PEIM's module name. It is a contributor-maintained identification/photo, not an OEM schematic, BOM, or revision-controlled board netlist. The table and photograph do **not** identify which ISL69247 output/page feeds CPU, SoC, GFX, or another load. “Main PMIC” is not a rail mapping. The repo's GitHub API metadata reports no recognized license (`license: null`), and the pinned tree has no `LICENSE` file.

Exact source/provenance:

- Repository: https://github.com/mothenjoyer69/bc250-documentation
- Path at the file's latest observed commit: `hardware.md`
- Commit: `1cf461b7766d43b22753f136020b304a90d80c61` (commit time `2026-02-25T03:03:41Z`)
- Pinned file URL: https://github.com/mothenjoyer69/bc250-documentation/blob/1cf461b7766d43b22753f136020b304a90d80c61/hardware.md
- Raw file: https://raw.githubusercontent.com/mothenjoyer69/bc250-documentation/1cf461b7766d43b22753f136020b304a90d80c61/hardware.md
- Raw file SHA-256: `23659e162daaac67c07bd9af116e275a6bfab751bbfa3a1fd8831eb21e3f837f`.
- Relevant lines: 35 (qualified PMBus/I2C note); 172–188 (board image, chip table, omitted-component caveat).
- Linked image: https://raw.githubusercontent.com/mothenjoyer69/bc250-documentation/1cf461b7766d43b22753f136020b304a90d80c61/images/annotated-chip-id.jpg; JPEG 3098×1395, SHA-256 `c96660be7407302ebe0c9a79a4659061a1496d0216c8541fb8b18238cd02b4bf`. The visible red marker `4` supplies location annotation only; neither the photo nor its legend draws voltage nets.

### F2 — Checked public index pages do not fill the page-to-rail gap

The public TheRetroWeb BC-250 record (ID `20611`, https://theretroweb.com/motherboards/s/amd-bc-250) identifies the board as AMD BC-250 and shows “Documentation 0.” Its displayed chip list names the chipset, Realtek NIC, processor/SoC, and Nuvoton Super-I/O; it does not identify an ISL69247 or give a VR schematic. This is a board-catalog page, not a manufacturer electrical document. The readback used `https://r.jina.ai/https://theretroweb.com/motherboards/s/amd-bc-250`, captured 11,303 bytes on 2026-09-21; capture SHA-256 `b9002fae6d26851e33fe0ba2cd92020f36a33d63e77017e8d2abc1f65f94d398`.

A pinned public-doc snapshot is already present locally at `docs/reference/amd-bc250-docs/`: repository `elektricM/amd-bc250-docs`, revision `0524002c3be78e9926a3fc6fb9b40415b7b43b1f`, archive SHA-256 `dfc2f2883b64615a11c22781fe31660eb51000c6f37032af1048c7dbff707394`, retrieved 2026-09-10. The relevant `source/docs/hardware/pinouts.md` describes the I2C header as exposing PMBus communications to Intersil PMICs, and attributes its information to the `mothenjoyer69` repository; it does not identify ISL69247 or assign PMBus pages to board rails. A bounded `rg` query of this pinned source/mirror for `ISL69247`, `ISL95712`, `VDDCR_SOC`, `VDDCR_GFX`, `schematic`, `VRM`, `controller`, and `Luna` returned no matches. This is a result about the checked snapshot only, not a claim that no other public material exists.

### F3 — Linux format evidence distinguishes telemetry from a setpoint; it does not map BC-250 rails

The colleague report `docs/research/luna-isl69247-format-current.md` was reopened and its SHA-256 matched the assigned identity `688379f4371a2dba41a4129403c070b11481cf11f1f12e3eab580d773a52dbc3`. I independently fetched the report's exact Linux source files at commit `6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9` and rechecked the source path. File hashes matched its recorded identities: `isl68137.c` `2b0791dd0075d5dd1b5c5b7264ab9cafe783cd58d4b686546c00172cb3ef9c9f` (17,407 bytes) and `pmbus_core.c` `232a430a5950c56bd10aa521cb085fd749ad9412d39b097a4875c7c9a63b9316` (101,262 bytes).

The narrow conclusion is verified at source level:

- `isl68137.c:436` and `:489` map the `isl69247` I2C ID / OF compatible to `raa_dmpvr2_2rail`; probe `:345–373` copies `raa_dmpvr_info`, then selects `pages=2` without replacing VOUT format or coefficients. The common VOUT profile is `direct`, `m=1`, `b=0`, `R=3` (`:222–247`). This is Linux driver static default behavior, not evidence that Linux bound on a BC-250 or that runtime platform data did not override it.
- `PMBUS_READ_VOUT` is the measured-output telemetry path: the driver read callback accepts `PMBUS_READ_VOUT` and reads that command (`isl68137.c:164–178`), while the PMBus sensor map binds `PMBUS_READ_VOUT` to `PSC_VOLTAGE_OUT` (`pmbus_core.c:1955–1965`) and the core applies `direct` conversion (`:907–945`, `:986–1005`, `:1334–1341`).
- `PMBUS_VOUT_COMMAND` is a command/setpoint path, not the sensor measurement: regulator `get_voltage` reads `PMBUS_READ_VOUT`; `set_voltage` converts the requested value and calls the `PMBUS_VOUT_COMMAND` write wrapper (`pmbus_core.c:3320–3376`). The chip-specific write callback handles that command separately (`isl68137.c:188–215`), but the later callback review found no demonstrated fall-through bus write. Under the static default direct coefficients and the driver's default unity divider, a raw output reading of `1150` converts to `1150 mV`; a host request of `1150 mV` may encode as word `1150` when within queried margins. These are software conversions, not an emitted transaction, a physical BC-250 measurement, or a safe/applied voltage claim.
- Neither the two-page count nor Linux page numbers 0/1 identify CPU, SoC, or GFX nets; the Linux I2C/PMBus path is not shown to be the BIOS PEIM's separate Super-I/O/EC mailbox path.

Linux provenance: https://github.com/torvalds/linux/tree/6a5719cc3ef2e4d9857cc4ae18e6db09d59a8cc9; driver path `drivers/hwmon/pmbus/isl68137.c` (`GPL-2.0+`) and core path `drivers/hwmon/pmbus/pmbus_core.c`.

### F4 — Local firmware trace remains static-only and leaves physical rail identity unresolved

The pinned CLV trace `docs/research/2026-09-20-clv-fixed-voltage-consumer.md` reports Setup fields named VCORE/GFX consumed by an `ISL69247` PEIM, and a page-select command `0x00` written with values `0` and `1` along the two code paths. That is a firmware-source trace against donor ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; it does not prove the physical controller's presence on any live board revision, decoded PMBus semantics, the mapping of page 0/1 to a physical rail, or applied voltage. The independent public board annotation in F1 narrows controller identity for the documented board, but still does not join those pages to CPU/SoC/GFX.

## Search route, failures, and coverage boundary

- `agent-reach doctor --json` exited 0. It reported GitHub through `gh CLI` (status `warn` because the doctor deliberately did not run credential-touching `gh auth status`), Exa unavailable, and general web read through Jina. No credential value was read or printed.
- OpenCLI was used read-only as requested. `opencli list` and command help identified public Google/DuckDuckGo search and web-read commands. The first Google request exited 69 with `BROWSER_CONNECT: Multiple Browser Bridge profiles are connected`. After an ephemeral profile was selected without persisting a default, `opencli doctor --verbose` passed; Google search, DuckDuckGo search, and `opencli web read` each exited 1 with `Navigation rejected` before returning page content. Browser profile identifiers are intentionally not recorded.
- Agent Reach's documented GitHub (`gh CLI`) route was used read-only after those OpenCLI failures: `gh search repos 'BC250 schematic' --limit 20` and `gh search code 'ISL69247 BC250' --limit 20` exited 0 with no rows; `gh search code 'ISL69247' --limit 20` located the exact public `hardware.md` source above (and generic driver matches). The source was then fetched at a pinned commit, not relied upon from the search snippet. A read-only repository-tree query of that pinned repository found `hardware.md` and `images/annotated-chip-id.jpg` but no file path named for a schematic, VRM, or regulator.
- No authenticated social platform, board, register, NVRAM, BIOS, ROM, or physical measurement was accessed. No source repo was modified.

## Result and next decisive source

**Public BC-250-specific controller identification: found** (`PUA1` → ISL69247 “Main PMIC”; `PUIO1` → ISL95712 “Core supply PMIC” in a community board annotation). **Public ISL69247 page-to-CPU/SoC/GFX mapping: not found in the checked sources.** Do not label firmware page 0 or 1 as CPU, SoC, or GFX from these records. A decisive mapping requires a board-revision-specific schematic/netlist or a directly traced board net joining the controller output/page to the corresponding rail; none was present in the checked public repo tree or catalog page. Live board revision and runtime/hardware rail identity remain unknown.

Evidence classes: `external-community-source` for the board annotation; `external-primary` for the pinned Linux source's driver semantics (applicability limited to that Linux branch); `observed-bytes` for downloaded file hashes; `static-analysis` for the local donor firmware trace. Hardware verification: **unrun**.
