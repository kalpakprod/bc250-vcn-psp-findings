# Intent

Build a standalone HII form prototype with three REF3 links to existing exact-CLV native forms. Not a complete DXE/ROM, not a voltage unlock. No board access. Keep source ROM unchanged. Test compile and decode for baseline/modified/rollback, plus byte-exact reconstruction.

# Result

Compile and REF3 decode PASS: baseline 0 links, modified 3 links, rollback 0 links. Patch reconstructs source exactly. Original ROM hash unchanged. No physical behavior tested.

# DXE build intent

Compile navigation-only DXE using existing EDK II in separate workspace. Package list carries forms and strings, registers HII only. No SetVariable, SMU, ports or voltage writes. Do not inject into ROM. Existing four roles preserved.

# DXE result

GCCNOLTO build exit0, PE32+ X64 subsystem11, 2752 bytes, SHA256 c102be23d68d886ac657a49386717492b56ee5f337f98920124e65e87a774595. Embedded HII forms/strings/end package validated with existing decoder. Host mock verifies registration and error/unload paths. VFR BASELINE/MODIFIED/ROLLBACK recompiled: 0/3/0 REF3, exits0. No ROM injection, UI execution, voltage unlock, or hardware acceptance.

# FFS intent

Package existing navigation DXE into FFS with HII database DEPEX. Audit available space in exact CLV only, no ROM mutation. Recheck RT8237E datasheet and GenCAD independently.

# Integration intent

Create a NEW exact-CLV copy with navigation driver, a Setup reference to it, preserved NBIO access, and canonical FALSE expressions in the existing voltage form. Do not add any voltage setter or alter NVRAM/clock/voltage defaults. RT8237E direct digital setpoint is unsupported by official pinout; do not label this a SoC voltage unlock. Keep original ROM, S3, donor firmware untouched. Build and validate standalone FFS, re-compression, original ranges, and reversible patch before any report. No physical flash.

# Integration result

Experimental MENU_ONLY exact-CLV copy built: 476076f280ca6385024db1bf643e042629153afff8bab2f9a52cc61c221e411e. Original source hash unchanged. 187->188 FFS, same FV size, one Setup body change plus navigation driver. All bytes outside AE0000..E00000 unchanged including NVRAM/PSP/APCB. Two malformed FALSE expressions normalized; voltage enable gates retained. Independent extraction resolves all 5 native targets. ROM delta reconstructs exactly, rollback restores original hash. Firmware-audit BASELINE/MODIFIED/ROLLBACK exits0. VFR 0/5/0 REF3, compiler exits0. No boot/UI/clock/voltage proof.

# UEFI smoke-test environment intent

System QEMU/OVMF absent. Fetch distro packages into project-local disposable test environment only, verify package signatures before extraction/execution. No system install, service, network listener, or hardware access. OVMF can verify loading/HII registration, not native AMD/AMI boot or clock/voltage behavior.

# OVMF result

QEMU exit0. Exact ROM-extracted driver e7d6957c3929bc3bed76282f38c131db03b1190a970e867aec5124d06e75c5ad loaded/started/unloaded in OVMF: HII count 0 -> 1 -> 0. Verified package signatures, project-local binaries only. No system install or board access. AMI Setup display/clock/voltage not verified.

# Final evidence ledger update

ROM_VERIFICATION now binds exact source/candidate absolute paths and acceptance status. QEMU smoke log reopened and still shows BASELINE 0 -> MODIFIED 1 -> ROLLBACK 0. No hardware flash.

# VDD80 lineage integration intent

Build a second candidate from the operator's voltage-unlocked CLV lineage `candidates/BC250_5.00_clv_OC_sync1750_vdd80_v001.bin` (hash verified separately). Preserve its exact NVRAM requests (`MemoryClock=1750`, `UclkDiv1M0=Enabled`, `FclkDpm=Disabled`, `DF=1750`, `VddcrVddOffsetControl=Manual`, raw offset=80), while adding only the already validated navigation DXE, Setup REF and canonical FALSE UI corrections. This is a reportable experimental candidate, not a voltage-safety claim or flash authorization. Original CLV and voltage-unlocked source remain unchanged.

# Operator scope correction — offline CLV first

Intent: record the operator's explicit correction, withdraw unsupported vdd80 attribution and application instructions, preserve all binaries.
Result: active target is pristine BC250_5.00_clv.bin, ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8. User will flash after analysis. Missing current SPI reads do not block offline work. VDD80 is a historical project-generated candidate, NOT established as a user-provided voltage-unlocked baseline. Prior instructions to retain raw80 and treat 1750/1750/Enabled as an applicable profile are withdrawn. No voltage ceiling compliance was proven. The vdd80 instruction/runbook are superseded by this correction and must not be used to authorize a flash.
