# Action log: FD v2.2 functionality port onto clv (5.00-lineage) base

Date: 2026-09-20. Actor: root (operator request "right now").
Base: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (16 MiB, ea578104).
Donor: Forbidden-Darkness AMD-BC-250-UEFI-v2.2-Firmware-Menu-Script, 3.00-based
variants preserved in `import/` (fd-menu-audit 16 variants + ext/fd_repo +
upstream RescueMei sources/xdelta).

## Intent (BEFORE writes)

Operator request: take the functionality the FD developer made and port ALL of
it onto BIOS version 5. G3 check: the Sep-17 whole-FV graft
(`candidates/BC250_clv_MeiMeiDXEv3_8c_omarchy_v001.bin`, af531026) already tried
the whole-FV method class and produced single-green-blink / no-LAN / no-video on
BC250-01, so a duplicate whole-FV graft is REJECTED. New method class: surgical
FFS injection of the 6 MeiMeiDXEv3 DXE drivers into clv's OWN DXE volume,
keeping all 187 native clv modules (anti-G6: different method after a
non-localizable failure).

FD functionality inventory (from RescueMei READMEs + preserved images):

1. Core-Unlock DXE driver (arbitrary core selection, CCX rules).
2. SMU-Unlock DXE driver (early Q3 0x98 exploit).
3. SMU-Patch DXE driver (8-core reporting; OS-side fix still needed).
4. Cold-Boot DXE driver (learn factory core mask).
5. ACPI DXE driver (inject power-management tables).
6. Menu DXE driver (MeiMeiDXEv3 Menu under Advanced, PXE preserved).
7. CHIPSETMENU base (Setup unhide) + logo variants (branding only).
8. menu.nsh (UEFI Shell backup/flash helper; runs from USB, no BIOS port needed).

Scope of THIS build: items 1-6 (driver FFS injection). Item 7 Setup-unhide is a
separate byte-patch class, inventoried but deferred. Item 8 is copied as-is for
operator USB use.

Procedure:

1. Read-only: verify donor hash, diff FD inner FV vs stock-3.00 inner FV to
   isolate the added driver FFS set; measure free tail in clv inner FV.
2. Build new file `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin`
   - `.build.json` (new files only; no baseline touched).
3. Validate: firmware_audit.py + independent re-scan (PSP/APCB/BHD identity,
   FV/FFS checksums, LZMA round-trip, module inventory).
4. NO flash in this run. Flash needs independent review + exact operator
   approval + fresh chip identity + recovery (chip currently holds W11 3c50bc9a;
   board unreachable at .118 as of this writing).

Expected effect: offline candidate only. Rollback: delete the two new files.
Remaining uncertainty: DXE-dispatch compatibility of 3.00-built drivers on the
5.00-lineage base; DEPEX satisfaction; no boot proof without hardware.

## Result (AFTER writes) — 2026-09-20, offline build only, no flash

Output:

- `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin`, 16 MiB,
  sha256 `0968a70c4d6fbb51f43d3e0fb5e4b3783dec41e881246356a75c66dc5f19c554`
- `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.build.json`
- Builder: `scripts/build_fd_drivers_clv.py` (reuses d-series LZMA params +
  FFS checksum routine; full structural self-validation inside)

Observed bytes: 6 MeiMei FFS appended to clv's own inner FV (187 -> 193
files); inner FV 0x41C000 -> 0x437000 (NumBlocks 0x41C -> 0x437, checksum
recomputed); capsule 0x14550F -> 0x148ECE; changed range 0xAE0088-0xC28F45;
outside 0xAE0000-0xE00000 byte-identical to clv. Donor hash re-verified
606a7a7f (matches Sep-17 record).

Validation (two-parser): firmware_audit.py PSP Fletcher32 0x17AA38B9 match /
19 entries identical / BHD match / APCB 0xC0 match on candidate and clv;
independent re-scan: 4 outer FVs checksum PASS, capsule FFS checksum PASS,
LZMA round-trip OK, inner FV checksum PASS, all 193 FFS header checksums
valid, 6/6 driver bodies byte-exact vs donor. DEPEX static: 63/64 FD GUIDs
present in clv; the single missing one (e1d5c3a7) is produced intra-set by
SMU_Unlock and consumed by Core_Unlock/SMU_Patch.

Deferred (not in this candidate): FD-modified files 899407D7 (same-size Setup
patch, CHIPSETMENU unhide class), B1DA0ADF (+0x27), logo 7BB28B99 (branding);
menu.nsh reused as-is from
`import/.../tmp_bc250/ext/fd_repo/menu.nsh` (UEFI Shell, no BIOS port needed).

Unrun: repo pytest suite (no pytest module on host); independent second-family
review (REQUIRED before any flash per review policy); hardware acceptance
(boot/dispatch/8-core/menu). Chip still holds W11 3c50bc9a; board unreachable
(.118, 100% loss) at last check. Rollback: delete the 3 new files.
Status: BUILT_OFFLINE_STATIC_VERIFIED, hardware_written=false.
