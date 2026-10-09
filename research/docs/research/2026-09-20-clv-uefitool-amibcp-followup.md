# Exact-CLV UEFIExtract IFR map and AMIBCP package follow-up

## Conclusion

A native UEFIExtract-produced `CbsSetupDxe` body was decoded with the existing IFR parser. The result independently reproduces the requested six HII questions and VarStore `0x5000` (`AmdSetup`) from the actual UEFIExtract output, not from a relabeled historical parser dump. The native UEFIExtract report also shows the NVAR `AmdSetup` entry under GUID `3A997502-647A-4C82-998E-52EF9486A247`.

No authorized AMIBCP/AMIBCP64 package or archive exists in the searched local attachment/workspace roots. The AMIBCP track remains `NEEDS-EVIDENCE`; no AMIBCP result is claimed.

## Exact native inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Native UEFIExtract dump root: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.dump`
- Native `CbsSetupDxe` PE32 body: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.dump/2 4F1C52D3-D824-4D2A-A2F0-EC40C23C5916/0 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792/0 EE4E5898-3914-4259-9D6E-DC7BD79403CF/1 Volume image section/0 5C60F367-A505-419A-859E-2A4FF6CA6FE5/42 CbsSetupDxe/1 PE32 image section/body.bin`
- Native body size/SHA-256: `264160` / `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`
- UEFIExtract report: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.report.txt`, SHA-256 `41e44c9dcc977bc7bb027b698b91f00c4592f95c026a2cfdfa0e153b61dc3c89`
- Existing parser: `/home/OWNER/orca/projects/bc250/archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py`, SHA-256 `480aa6fc70ed12e8d1dbec2c32dfb45ddadcd7c2f9075ceac6dad6486bc50ebb`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-amibcp-followup/uefitool-native-ifr-map.json`, SHA-256 `a8e77d27777077b4b037ad50be5935a1232d784f12934e37efc3279fbc5dec88`

Read-only native parser result: `PASS`, six selected questions, exact native body hash match. No image, NVRAM, or hardware write occurred.

## Map decoded from the native UEFIExtract body

All rows use VarStore `0x5000` (`AmdSetup`). Values are stored ROM requests at body base `0x4CF`, not applied clocks or training state.

| Control                   | Form / package path                                                                          |      QID | Offset / absolute ROM            | Options/default or bounds                                                              | CLV stored bytes             |
| ------------------------- | -------------------------------------------------------------------------------------------- | -------: | -------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------- |
| Memory Clock Speed        | `0x702C I Accept`; package chain `0x7007 -> 0x7028 -> 0x702A -> 0x702C`                      |  `0x20F` | `+0x316` / `0x7E5`               | `Auto=0xFF`; 23 enum labels `125..2000MHz` with internal codes; no enclosing condition | `24` (`36`, label `1800MHz`) |
| UclkDiv1M0                | `0x702F GDDR6 DRAM Timing Configuration`; `0x7000 -> 0x7008 -> 0x702E -> 0x702F`             |  `0x229` | `+0x330` / `0x7FF`               | `Auto=0xFF`, `Enabled=0x01`                                                            | `01`                         |
| Memory P-state            | `0x7032 DRAM Power Options`; `0x7000 -> 0x7008 -> 0x702E -> 0x7030 -> 0x7032`                |  `0x25E` | `+0x36D` / `0x83C`               | `Auto=0xFF`, `Enabled=0x01`, `Disabled=0x00`                                           | `FF`                         |
| FCLK_DPM                  | `0x703E SMU Features`; package-local parent `0x7009 SMU Debug Options` has no incoming `REF` | `0x7045` | `+0x6A3` / `0xB72`               | `Disabled=0`, `Enabled=1`, default `Auto=0x0F`; callback flag set                      | `0F`                         |
| DF Clock Override Control | `0x703F SMU Debug`; package-local parent `0x7009` has no incoming `REF`                      |  `0x37D` | `+0x703` / `0xBD2`               | `Auto=0xFF`, `Manual=0x01`                                                             | `01`                         |
| DF Clock Override         | same `0x703F SMU Debug`                                                                      |  `0x37E` | `+0x704` u16 LE / `0xBD3..0xBD4` | numeric `[0,2000]`, step `0`; no discrete options                                      | `8C05` LE = `1420`           |

The form paths/QIDs/options above are decoded from the native UEFIExtract PE32 body. They remain static HII metadata; AMIBCP visibility/access behavior and live Setup-browser reachability are not established.

## AMIBCP availability audit

Safe filename-only inventory was performed in:

- `/home/OWNER/orca/projects/bc250`
- `/home/OWNER/Downloads`
- `/home/OWNER/Desktop`
- `/home/OWNER/Documents`

No `AMIBCP*` executable or archive was found. The prior authorized availability audit also searched imported Downloads, standard executable roots, and mounted software storage, finding zero exact AMIBCP files; its machine record is `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-amibcp-availability-luna/availability.json`.

No unknown archive was opened, no secrets were inspected, no package was downloaded, no runtime was installed, and no AMIBCP claim is made.

### One required operator artifact

Please provide **one** of the following:

1. An authorized, licensed AMIBCP for Aptio package containing `AMIBCP.exe` or `AMIBCP64.exe`, with exact version and provenance; **or**
2. If the package cannot be shared, a sanitized Setup-tree/access-settings export from an authorized Windows AMIBCP run against this CLV image.

Until that artifact arrives, AMIBCP menu/access behavior is `UNRUN`; the native UEFIExtract/IFR map must not be mislabeled as AMIBCP output.

## Acceptance

- **PASS:** native UEFIExtract body selected, hashed, parsed, and reconciled with the existing `CbsSetupDxe` census; six requested HII questions and VarStore decoded.
- **PASS:** safe AMIBCP attachment-name audit found no local package.
- **UNRUN:** AMIBCP UI/access export, native Setup browser, NVRAM save/readback, firmware execution, training, clocks, voltage, and hardware behavior.
