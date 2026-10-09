# Exact-CLV UEFITool native build/run — intent

- Timestamp: 2026-09-20 Asia/Almaty
- Actor: Codex bounded executor (`/root/amibcp_uefitool_map`)
- Target: immutable `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Need: execute the actual preserved official UEFITool family against exact CLV rather than relabeling the Python IFR parser as UEFITool.
- Source: local preserved `LongSoft/UEFITool` repository, remote `https://github.com/LongSoft/UEFITool.git`, pinned commit `dac91b26733ca21cb204e41614c1b8c81cc50860`, version `NE alpha 76`, BSD license (`LICENSE.md` SHA-256 `c7973c703ab625a818957e2603c94d65eff26307d660234832dd3fed072130ffa`).
- Existing capability check: `cmake`, `g++`, `qmake6`, Qt6 Widgets are available; UEFIExtract is a no-Qt console target and UEFITool is a Qt6 GUI target. This is the existing local route; no external release or package install is needed.
- Planned procedure: build out-of-source into a new project-local evidence directory; run `UEFIExtract` on the immutable ROM to generate a structural report/dump; run the built UEFITool GUI on the same ROM via the documented GUI route and capture observed window/application evidence; compare the extracted `CbsSetupDxe` hash and paths against the existing census.
- Expected effect: generated build/output/evidence files only; no ROM, firmware, NVRAM, global install, or hardware write.
- Rollback: remove only this run's build/output/evidence directory and this action-log entry; preserve source, ROM, and prior evidence.

# Exact-CLV UEFITool native build/run — result

- Configure exit `0`; build exit `0`.
- Built UEFITool GUI: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/build/UEFITool/uefitool`, SHA-256 `19a92b8987b29f9e6a22ba6ac58deb64f59771f7310cbeb8e73ad1405cd204cd`.
- Built UEFIExtract: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/build/UEFIExtract/uefiextract`, SHA-256 `cdc9d31d216deb9aa78f0ee69d841f8ab56618176ea16458bb51e32449ed9d83`.
- Native GUI command started: `QT_QPA_PLATFORM=xcb DISPLAY=:0 .../UEFITool/uefitool evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; observed title `UEFITool NE alpha 76 (Sep 20 2026) - BC250_5.00_clv.bin`; process later stopped with Ctrl-C. Native stderr contained repeated TE-base warnings; no image mutation action was invoked.
- Orca computer-use attempt returned exact error `No top-level AT-SPI window is available for uefitool`; no guessed GUI controls were used. Observation JSON: `evidence/firmware-audit/20260920-clv-uefitool-native-run/orca-computer-get-app-state.json`.
- Native UEFIExtract `report` exit `0`, `all` exit `0`, absolute specific FFS extraction exit `0`; report hash `41e44c9dcc977bc7bb027b698b91f00c4592f95c026a2cfdfa0e153b61dc3c89`.
- UEFIExtract full-dump `body.bin` SHA-256 equals the original CLV SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- `CbsSetupDxe` GUID `F639D37E-02A1-4BA8-AD17-5C6C6E5E9322` native PE32 body size `264160`, SHA-256 `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`, exactly matches existing census module.
- First relative-output specific FFS extraction failed with exit `5` and literal `Cannot open file ... cbs-ffs.dump/file.ffs`; corrected absolute-output invocation passed exit `0`. Both outputs/errors retained.
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/native-run-result.json`, SHA-256 `ae6e00c30d480de7bda70e745ef1b1cc0d236cf3410bde28867eaf0d7bd5e06a`.
- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-uefitool-native-run.md`, SHA-256 `91f02a634b79595beff69dd8392ecb5258f107368be82bbec70577f2366ea2b0`.
- Acceptance: native tool build/extraction/hash reconciliation PASS; GUI tree interaction through Orca INCONCLUSIVE due provider AT-SPI limitation; firmware/NVRAM/hardware writes UNRUN.
- Bounded direct GUI capture retained: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uefitool-native-run/uefitool-xcb.stdout` (SHA-256 recorded in `native-run-result.json`), exit `124` only because the resident GUI was bounded by `timeout 3s`; no parse error or mutation occurred before timeout.
- Updated machine result SHA-256: `9db0c12e0209c02b7fa714af75a72990667863c577025474cbb44577d941bee9`.
