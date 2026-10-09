# Exact-CLV BIOS menu map: AMIBCP and UEFITool boundaries

## Conclusion

The exact CLV image contains all requested controls in HII/IFR. The practical local route is the existing Python IFR parser over the extracted `CbsSetupDxe` module; it reproduced the five questions with `PASS` and `60,721` IFR bytes walked. No AMIBCP executable and no runnable UEFITool/UEFIExtract binary is installed on this Linux host. A preserved UEFIExtract A75 Windows executable and UEFITool NE alpha-76 source are inventory-only.

**UEFITool can structurally open/extract FV/FFS/PE32 sections (and the preserved source has structural tree/rebuild interfaces), but it does not produce this HII question-to-`AmdSetup` map or provide AMIBCP-style Setup/NVRAM field editing.** AMIBCP would be the Windows-side candidate for a vendor-aware Setup/NVRAM UI, but its availability and behavior are unverified here. No image or NVRAM was modified.

## Pinned input and parser evidence

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Size: `16,777,216` bytes
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact extracted module: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin`
- Module SHA-256: `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`
- Existing parser: `/home/OWNER/orca/projects/bc250/archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py`
- Parser SHA-256: `480aa6fc70ed12e8d1dbec2c32dfb45ddadcd7c2f9075ceac6dad6486bc50ebb`
- Exact verifier reused: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-df-init-route/menu-verify.py`
- Verifier reproduction: copied to a disposable `/tmp` directory and run with `python3 -B`; exit status `0`, stderr empty, status `PASS`.
- Existing exact menu result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-df-init-route/menu-result.json`
- Tool inventory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-menu-map-amibcp-uefitool/tool-inventory.json`

The ROM hash was identical before and after the parser run. The persisted `AmdSetup` body base used below is `0x4CF`; offsets are relative to that body. Absolute offsets are included for reproducibility.

## Practical menu map

All five questions use VarStore `0x5000` (`AmdSetup`), are editable, have IFR flags `0x10` (`RESET_REQUIRED`, not callback, not read-only), and have no enclosing conditional scope in the exact package unless noted. Values shown as “current” are ROM-stored requests, not applied clocks or training results.

| Control                       | Package-local form path                                                                                                                                   |      QID | `AmdSetup` offset | Absolute ROM offset | Current stored value          | Default and options                                                                                                                                                                                                                                                                                       | Local edit/extract result                                                                                                                          |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------: | ----------------: | ------------------: | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Memory Clock Speed**        | `0x7007 UMC Common Options` → `0x7028 GDDR6 Common Options` → `0x702A DRAM Timing Configuration` → `0x702C I Accept`                                      |  `0x20F` |     `+0x316` (u8) |             `0x7E5` | `0x24` = 36 (`1800MHz` label) | Default `Auto=0xFF`; `125=0x02`, `225=0x04`, `250=0x05`, `400=0x08`, `450=0x09`, `500=0x0A`, `750=0x0F`, `850=0x11`, `1000=0x14`, `1250=0x19`, `1330=0x1A`, `1375=0x1B`, `1500=0x1E`, `1600=0x20`, `1650=0x21`, `1700=0x22`, `1750=0x23`, `1800=0x24`, `1850=0x25`, `1900=0x26`, `1950=0x27`, `2000=0x28` | Existing IFR parser extracts all options. UEFITool can extract the containing module/section but not decode this field itself.                     |
| **UclkDiv1M0**                | `0x7000 AMD CBS` → `0x7008 UMC Debug Options` → `0x702E GDDR6 Debug Options` → `0x702F GDDR6 DRAM Timing Configuration`                                   |  `0x229` |     `+0x330` (u8) |             `0x7FF` | `0x01` (`Enabled`)            | Default `Auto=0xFF`; `Enabled=0x01`                                                                                                                                                                                                                                                                       | Existing IFR parser extracts it. `Enabled` is an enum label, not a decoded divider ratio.                                                          |
| **Memory P-state**            | `0x7000 AMD CBS` → `0x7008 UMC Debug Options` → `0x702E GDDR6 Debug Options` → `0x7030 GDDR6 DRAM Controller Configuration` → `0x7032 DRAM Power Options` |  `0x25E` |     `+0x36D` (u8) |             `0x83C` | `0xFF` (`Auto`)               | Default `Auto=0xFF`; `Enabled=0x01`; `Disabled=0x00`                                                                                                                                                                                                                                                      | Exact supplemental verifier: `9864/9864 PASS`; package-local path is unconditional. No training/application claim follows.                         |
| **FCLK_DPM**                  | `0x7009 SMU Debug Options` → `0x703E SMU Features`; `0x7009` has no incoming `REF` in this package                                                        | `0x7045` |     `+0x6A3` (u8) |             `0xB72` | `0x0F` (`Auto`)               | Default `Auto=0x0F`; `Disabled=0x00`; `Enabled=0x01`                                                                                                                                                                                                                                                      | Existing IFR parser extracts it. Flag `0x14` includes reset-required + callback. Package-local presence is not proof of live browser reachability. |
| **DF Clock Override Control** | `0x7009 SMU Debug Options` → `0x703F SMU Debug`; `0x7009` has no incoming `REF` in this package                                                           |  `0x37D` |     `+0x703` (u8) |             `0xBD2` | `0x01` (`Manual`)             | Default `Auto=0xFF`; `Manual=0x01`                                                                                                                                                                                                                                                                        | Existing IFR parser extracts it. It controls the separate numeric request below in the UI model.                                                   |
| **DF Clock Override (Value)** | same `0x7009` → `0x703F` path                                                                                                                             |  `0x37E` | `+0x704` (u16 LE) |             `0xBD3` | `0x058C` LE = 1420            | Numeric bounds `[0, 2000]`, step `0`; no discrete option list and no IFR option/default opcode                                                                                                                                                                                                            | Existing IFR parser extracts bounds. UEFITool does not provide semantic NVRAM editing for this numeric question.                                   |

### Reachability qualification

The `0x7000` CBS chain to `0x7008` is unconditional in the package. `0x7007` (UMC Common Options) and `0x7009` (SMU Debug Options) are present in the package, but the exact package has no incoming `REF` for either form. AMITSE/external registration or dynamic links may still expose them; this was not run on hardware or in a live Setup browser. “No local conditional scope” therefore means only that the question is not nested under a decoded `SUPPRESS_IF`, `GRAY_OUT_IF`, or `DISABLE_IF` in this module.

## Capability comparison

| Tool/route                                 | Available locally                                             | Can extract the relevant object?                                                       | Can map/edit these individual Setup fields?                                                                       | Evidence boundary                                           |
| ------------------------------------------ | ------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Existing `e1_ifr_dump.py` + exact verifier | Yes                                                           | Yes, via existing extracted `CbsSetupDxe`                                              | **Map: yes** (form/QID/VarStore/offset/options/defaults/bounds); **edit: no**                                     | Reproduced exact CLV HII statically; no browser/NVRAM write |
| UEFITool NE                                | Source only: preserved `NE alpha 76`; no executable in `PATH` | **Yes, structurally**: FV/FFS/section tree and extraction                              | **No HII-aware field edit**; binary module replacement/rebuild is a separate structural operation and was not run | Source/README inventory only; no local binary execution     |
| UEFIExtract A75 / UEFIFind A75             | Windows PE32+ binaries only; not run                          | **Yes, structurally/pattern search** if run on Windows/Wine, subject to target support | **No Setup-field editor**                                                                                         | Hashes and `file(1)` observed; execution unrun              |
| AMIBCP / AMIBCP64                          | **Unavailable** (`command -v` empty; no local file)           | Unrun                                                                                  | AMIBCP-specific NVRAM/IFR UI editing and extraction **unverified**                                                | Do not infer behavior from historical tool names or reports |

## What this map does not prove

- IFR labels such as `1800MHz` and numeric bounds `[0,2000]` are UI encodings; they do not prove physical frequency units, GDDR6 conversion, a clock domain, training acceptance, or `MCLK=UCLK=FCLK`.
- `UclkDiv1M0=Enabled` is not a decoded divider factor.
- The DF help text says “make sure FCLK > UCLK and Memory P-state is disabled”; this is UI guidance, not hardware proof.
- `RESET_REQUIRED` and `CALLBACK` are IFR metadata, not evidence of a successful save, reset, browser callback, or clock application.
- No AMIBCP run, live Setup-browser run, NVRAM save/readback, firmware execution, hardware clock measurement, voltage measurement, or flash occurred.

## Status

- **PASS:** pinned image identity, immutable input hash, exact HII/IFR parser run, requested QIDs/forms/offsets/options/defaults/bounds, current stored bytes, and structural tool inventory.
- **UNRUN:** UEFITool executable run, UEFIExtract run, AMIBCP run, live browser path, NVRAM write/readback, firmware training, and hardware behavior.
- **Rollback:** no image or hardware write occurred; remove only the new report, machine inventory, and action-log entry if rejected.
