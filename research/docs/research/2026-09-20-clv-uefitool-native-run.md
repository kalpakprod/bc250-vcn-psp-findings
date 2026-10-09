# Exact-CLV native UEFITool run

## Conclusion

The preserved official `LongSoft/UEFITool` source was buildable with the existing local Qt6/CMake toolchain. A real UEFITool NE alpha 76 GUI process opened and parsed the exact CLV ROM; its native UEFIExtract sibling produced a full structural report/dump with exit `0`. The extracted `CbsSetupDxe` PE32 body is byte-identical to the existing census module (`7ff717d51c9a...`), so the prior IFR map is now tied to an actual UEFITool-family extraction rather than only a Python parser.

No firmware write, image replacement, UEFITool Save/Rebuild/Replace action, NVRAM write, or hardware action occurred.

## Provenance and build

- Source: `/home/OWNER/orca/projects/bc250/archives/imported/codex-workspaces/legacy-Documents-Codex/2026-08-30/x20/bc250-uefi-capture/third_party/UEFITool`
- Remote: `https://github.com/LongSoft/UEFITool.git`
- Pinned commit: `dac91b26733ca21cb204e41614c1b8c81cc50860`
- Version: `NE alpha 76`
- License: BSD license; `LICENSE.md` SHA-256 `c7973c703ab625a818957e2603c94d65eff26307d660234832dd3fed072130ffa`
- Build: `cmake -S <source> -B evidence/firmware-audit/20260920-clv-uefitool-native-run/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=<run>/install`; `cmake --build <run>/build --target UEFIExtract UEFITool -j2`
- Configure exit: `0`; build exit: `0`.
- Built UEFITool GUI: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/build/UEFITool/uefitool`, SHA-256 `19a92b8987b29f9e6a22ba6ac58deb64f59771f7310cbeb8e73ad1405cd204cd`.
- Built UEFIExtract: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/build/UEFIExtract/uefiextract`, SHA-256 `cdc9d31d216deb9aa78f0ee69d841f8ab56618176ea16458bb51e32449ed9d83`.
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/native-run-result.json`.

## Exact input

- Source ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Size: `16,777,216` bytes.
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Extraction used a project-local copy `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin` with the same SHA-256. The source ROM remained unchanged.

## Native UEFITool GUI event

Command:

```text
QT_QPA_PLATFORM=xcb DISPLAY=:0 evidence/firmware-audit/20260920-clv-uefitool-native-run/build/UEFITool/uefitool evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
```

Observed X11 window title:

```text
UEFITool NE alpha 76 (Sep 20 2026) - BC250_5.00_clv.bin
```

Observation record: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/uefitool-window-observation.txt`.

The process stayed resident after opening the image and emitted repeated native parser warnings:
`checkTeImageBase: TE image base is neither zero, nor original, nor adjusted, nor top-swapped`.
These warnings concern TE image-base interpretation; they did not prevent the UEFITool GUI from opening the image or UEFIExtract from completing report/full extraction.

The required `orca computer` GUI observation was attempted without guessing controls. This session's provider returned:
`No top-level AT-SPI window is available for uefitool`.
Record: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/orca-computer-get-app-state.json`.
Thus no GUI tree click, Save, Replace, Rebuild, or other mutation was attempted.

## Native UEFIExtract results

Commands used the built sibling from the same pinned source:

```text
uefiextract BC250_5.00_clv.bin report
uefiextract BC250_5.00_clv.bin all
uefiextract BC250_5.00_clv.bin F639D37E-02A1-4BA8-AD17-5C6C6E5E9322 -o <absolute-output-dir> -m file -t FF
```

Results:

- `report`: exit `0`, report `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.report.txt`, SHA-256 `41e44c9dcc977bc7bb027b698b91f00c4592f95c026a2cfdfa0e153b61dc3c89`.
- `all`: exit `0`; full dump `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.dump` (3,858 files observed).
- Whole dump `body.bin` SHA-256 equals the input ROM SHA-256.
- Absolute specific-FFS extraction: exit `0`; `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/cbs-ffs-absolute/file.ffs`, size `264,378` bytes.
- A first relative-output specific-FFS attempt exited `5` because the extractor changes directory while resolving a relative output path; this was corrected by using an absolute output path. Both attempts and their literal errors are retained in the run directory.

## `CbsSetupDxe` reconciliation

UEFIExtract report identifies:

```text
F639D37E-02A1-4BA8-AD17-5C6C6E5E9322 | CbsSetupDxe
```

Native full-dump PE32 body:

`/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.dump/2 4F1C52D3-D824-4D2A-A2F0-EC40C23C5916/0 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792/0 EE4E5898-3914-4259-9D6E-DC7BD79403CF/1 Volume image section/0 5C60F367-A505-419A-859E-2A4FF6CA6FE5/42 CbsSetupDxe/1 PE32 image section/body.bin`

- Size: `264,160` bytes.
- SHA-256: `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`.
- Existing census module: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin`.
- Existing census SHA-256: identical `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`.

This is the requested actual-tool extraction/hash comparison. The five-field IFR map can now cite the native UEFITool-family extraction as its module source; UEFITool itself remains a structural parser, not an AMIBCP-style semantic Setup editor.

## Acceptance status

- **PASS:** pinned source provenance/license/commit; local build; actual UEFITool GUI open/parse event; UEFIExtract report and full dump; absolute specific FFS extraction; exact CLV hash preservation; `CbsSetupDxe` size/hash match.
- **UNRUN:** AMIBCP track, live Setup browser, semantic IFR editing through UEFITool, firmware/NVRAM write, hardware execution, and clock/training acceptance.
- **INCONCLUSIVE:** interactive GUI tree inspection through Orca due to provider limitation; no GUI mutation was attempted.
