# AMD BC-250 hash-specific audit report (draft)

**Status:** `DRAFT / INCOMPLETE`. This report separates observed bytes, static analysis, host/emulated results, historical reports, and hardware verification. It does not authorize a firmware or hardware write.

**Generated:** 2026-09-11T05:28:58.956907+00:00

## F1 — Selected baseline and provenance

| Artifact | Path | Size | SHA-256 | Status |
|---|---|---:|---|---|
| Current operator dump | `dump/2.bin` | 16 MiB | `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0` | structural control; no fresh second read yet |
| Archived capture archive | `import/from-windows/Users/kukuruza/tmp_bc250/flash_archive_FULL_20260901-140856.tar` | — | `3b6c5455433285f086899eabd2e35a108b4253525e95faec6484e19b31fc51a5` | historical corroboration |
| Board-view CAD | `import/from-windows/Users/kukuruza/Downloads/AyuGram Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad` | 1,923,019 B | `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8` | CAD-derived wiring |

The archived capture manifests report two matching complete reads per set, and their member hashes were independently rechecked. The current dump differs from the first archived `spi.bin` by 3,071 bytes in 46 ranges confined to the first `0x20000` bytes; PSP/APCB/UEFI firmware regions are byte-identical. This is not a substitute for two fresh reads with current programmer and chip metadata.

## F2 — Outer firmware and extraction

- `scripts/firmware_audit.py` SHA-256: `5ead8605678fc5a13eb0cf49c01b43037560ddc485d8ad2686abf0e9c34d9593`.
- Current report: `evidence/firmware-audit/dump-2-inventory.json`, SHA-256 `151489eccfa56bfdc89a7f7fab10b8ccc6f2d3ffacb486fec8d0ef4192545b8a`.
- Historical stock report: `evidence/firmware-audit/stock-3.00-inventory.json`, SHA-256 `e71ced36d5add5d7c511bb039b01f2ae6062aac76f48715da94838d407b39fcb`.
- The corrected path-parameterized walker handles FV extended headers, 8-byte FFS alignment, UTF-16 UI names, GUID-defined/LZMA sections, freeform subtype sections, and top-level `SECURITY_CORE`.
- Current dump: PSP 19 entries/Fletcher32 pass; BHD 4 entries/Fletcher32 pass; APCB `0xAB1000`, size `0xB70`, checksum `+0x10=0xF2` pass; four FVs with filesystem GUID `8C8CE578-8A3D-4F1C-9935-896185C32DD3`; 234 executable bodies (179 PE32, 55 TE).
- Historical `BC250_3.00.ROM`: 233 executable bodies. Comparison has 233 common GUID/UI/type records and 231 common body hashes; `AMITSE` and `Setup` differ. The dump-only module is `Bc250CoreUnlockDxe`, GUID `2F3D426D-6A54-4A6B-82D0-1207CC5B6D92`, 12,288 B, body SHA-256 `7d22d80284cd4c9c8af997611002f6916b4fa4b0d3ca9e3e34e450abbe885c55`.

## F3 — VCN/PSP/SEC_GASKET observations

- IP discovery payload at `0x981A00`: one die, 38 IP records; VCN HWID 12, version `2.0.3`, harvest `0`, bases `0x7800`, `0x7E00`, `0x02403000`. No dedicated VCN PSP directory entry appears. This is a descriptor, not proof of VCN power, firmware loading, rings, or codec operation.
- PSP type 8 at `0x8FF000`: size `0x40200`, SHA-256 `6a3da1ef6024c3143283fb92468fd71d628e9402a751c4a9799a20f473549ad9`; body matches imported Robin3 PMFW body.
- Current `$PS1` gasket wrapper at `0x982000`, size `0x2E50`, has payload at wrapper offset `0x100`, payload length `0x2C50`, trailing `0x100` bytes. Payload SHA-256 is `d16f7dacfd9b38ea47e3cde8b9754183eeb3a97076244702a0dd980eb53fd52c` and parsed groups match Robin3.
- Current gasket groups: `0x201=1230`, `0x203=31`, `0x210=13`, `0x280=100`, `0x281=31`; no current `0x0900Cxxx` HWID-12 writes. Gasket/policy bytes match Robin3.
- Rejected unsigned VCN gasket artifact adds 56 HWID-12 range writes but is not a signed/current source. The historical Cezanne donor has a different group layout and `0x03E810=0x6`; this remains donor correlation only.
- SEC_GASKET summary: `evidence/firmware-audit/ps1/sec-gasket-summary.json`, SHA-256 `4f65e194236728476789f7b9dc438ca0eed2825a01c28f67586a072da210235d`.

## F4 — Current CoreUnlock binary

- Rizin reports: `evidence/firmware-audit/rizin/`; Rizin `0.9.1`, commit `c3a90e9226d977f58f4e9c75f78fa6b07afe13c7`.
- Corrected summary: `evidence/firmware-audit/rizin/Bc250CoreUnlockDxe.corrected-summary.json`, SHA-256 `446d6b0df325781e7692cfdc545c8633a6ee918ef7ca35278dd714b313662760`.
- `llvm-objdump` corroborates: `evidence/firmware-audit/rizin/Bc250CoreUnlockDxe.llvm-objdump.txt`.
- The exact body reads SMN `0x0115A870`, tests low byte `0xFF`, writes Queue-3 response/argument/command registers `0x03B10A80/0x03B10A88/0x03B10A20`, sends `0x98`, requires response `0x01`, rereads the mask, and calls warm reset.
- It also reads the UEFI `Setup` variable and checks `Setup+0x1C4 == 0x000157C0`; equality skips the Q3 path. Current raw Setup NVAR at `0xD84` has `Setup+0x1C4=0x00011940`, so it does not meet the skip equality.
- The retained `upstream/BC250-DXE-SMU-Core-Unlock/.../Bc250CoreUnlockDxe.c` is only a partial semantic reference. Its exact source revision for the dump body is unresolved; no symbols are present. Current execution remains unverified.

## F5 — Memory/SoC-voltage observations

- `scripts/nvar_audit.py` SHA-256: `16d35db736f5ca0e4423c444ff892b9d2b583bd8efcafda1a5e752ff04cb1160`.
- Current primary NVAR report: `evidence/firmware-audit/dump-2-nvar-primary.json`, SHA-256 `23877f639955c2c15fa040c880065bca69f9c5fdf04d3013916a973d08bdb7ad`.
- `AmdSetup` record: NVAR header at `0x4BB`, body at `0x4CF`, length `0x8B5`, body SHA-256 `6f266c3c78a544d73eae5cea465756dd73e343fe16e2725d2300d08ba176d055`.
- Current observed fields: MemoryClock `+0x316=0xFF`; Tcl `+0x317=0xFF`; UclkDiv1M0 `+0x330=0xFF`; FCLK_DPM `+0x6A3=0x0F`; VDDCR_VDD control/value `+0x6E5=0` / `+0x6E6=0`; DF control/value `+0x703=0xFF` / `+0x704=1000`; CPU frequency `+0x701=3600`; FAST_PPT `88000`; SLOW_PPT `65000`; VRM current `65000`; VRM maximum `95000`.
- Historical IFR field map: `evidence/firmware-audit/amdsetup-ifr-field-map.json`, SHA-256 `ff657447e9070b18773d149bca6e82bbd7c36295172561e5e2a425a6fecab2b7`. The IFR text formatter truncated the high `0x10000` bit in two `Setup+0x1C4` option displays; raw current Setup PE32 restores full values `0x00011940` and `0x000157C0`.
- Four historical OC profile images parse with PSP/BHD/APCB checksums and 233 executable bodies each. Their AmdSetup bodies statically alter MCLK/FCLK/UCLK, SoC-voltage control/value, power limits, and (in one profile) memory power settings. Their DFG/MEMG subgroup body hashes match current, but PSPG/CBSG/APCB sizes differ; they are not current baselines or approved flash candidates.
- OC comparison: `evidence/firmware-audit/oc-profiles/comparison.json`, SHA-256 `8c3c392b7e1e33b38a4051568a76e5d3e68775f2b764d370ab1cda9b4f676fe5`.

## F6 — APCB and candidate preview

- `scripts/apcb_detail.py` SHA-256 `80ea1708836ddee07747c7e507c908af08a7c9dbece197bfb4a6463879914711`; detailed report `evidence/firmware-audit/apcb-detail.json`, SHA-256 `d77ed671b723100c25ccf1e3265362ade799b00904bed621dc9bca9bf0336666`.
- Current DFG has instances 5/6, each 13 token rows. MEMG has instances 7/8/49/80/82/83. Historical OC profiles have the same DFG/MEMG subgroup hashes as current.
- In-memory APCB-only calculation preview: `evidence/firmware-audit/apcb-only-calculation-preview.json`, SHA-256 `d2d109a208acfb70c3b4664ecbb2f241e271e92ebeba95d344123126717bea30`. Proposed values are `0x001FFF00 -> 0x007FFF00` at APCB `+0x130` and `+0x16C`; checksum changes `0xF2 -> 0x32`. Only bytes `+0x132`, `+0x16E`, and checksum `+0x10` change in the current preview.
- This is arithmetic/static evidence only. No full candidate BIOS exists.

## F7 — Cutter/MCP and board-view

- Native MCP fixture evidence: `evidence/firmware-audit/mcp/fixture-true-20260910/manifest.json`, SHA-256 `ae20d7ba4bd91b9395d5a119590003ea5506fba8c942bc466e4835238f46ab3c`. Health, `initialize`, `tools/list`, segments, functions, strings, bounded bytes, disassembly, function detail, and decompile returned HTTP 200 with `isError=false` on `/usr/bin/true`.
- Listener was observed as `127.0.0.1:8000` only. Native mutation tools were not called.
- Module-specific native MCP analysis on BC250 copied modules remains pending; the current Cutter session still reports `/usr/bin/true` at `current_address=0x2560`.
- Normalized board-view map: `evidence/boardview/bc250-connector-map.json`, SHA-256 `fe6314c8098e146d2139da71dbb6dca75222f7bc639326f94061049929fc2379`. J2 is CAD-derived CPU JTAG wiring: TCK pin 2, TMS pin 4, TDO pin 8, TDI via pin 6 -> `N22562912` -> `R19`, TRST# via pin 9 -> `N22563682` -> `R120`; pins 1/19 labelled `+1.8V`, pins 3/5/7/17 GND. J4004 is SPI, J5 UART, TPMS1 LPC/POST, and I2C_HEADER1 SMBus. Physical population/orientation/voltage/debug state remain unverified.

## F8 — Candidate and recovery status

### Proposed VCN/APCB-only candidate

- Source must be two matching fresh full reads of the actual target.
- Only APCB `+0x130`, `+0x16C`, and the checksum byte `+0x10` may change.
- Preserve all PSP entries, signed `$PS1` bytes, BHD, FV/FFS, and unrelated NVRAM.
- A parser/checksum pass does not prove PSP acceptance, bootability, or VCN enablement.

### Memory/SoC-voltage candidate

- No values are approved yet.
- First candidate must isolate one variable or one coupled control/value pair.
- Memory frequency, timings, SoC voltage, power limits, and VCN changes must not be combined in the first test.
- Exact field semantics, units, training behavior, and rail telemetry remain to be established.

### Hardware gates

1. Verify board identity, chip marking, pin-1 orientation, JEDEC ID, capacity/package, voltage, programmer/software, adapter, and connection method.
2. Take two complete reads into separate files and compare them.
3. Validate source/output hashes, changed ranges, format, checksums, compression, alignment, and signature boundaries.
4. Obtain independent review of the actual candidate diff and failure path.
5. Confirm external recovery and rollback procedure.
6. Obtain explicit per-image/per-board approval.
7. Perform post-write full readback and only then test boot, PCI, driver, VCN, clocks, codec, memory training, telemetry, and stability.

No hardware write, programmer write, register write, JTAG target-memory write, DXE injection, or flash was performed for this draft.

## F9 — CoreUnlock native MCP module trial

- Cutter health at module load: HTTP 200, `current_address=0x11037`; listener: `127.0.0.1:8000` only.
- Native MCP `initialize`/`tools/list` passed; 19 tools exposed, 3 mutation-capable and none called.
- Read-only queries for segments, functions, strings, bytes, disassembly, `pd`, decompile, function detail, variables, xrefs, globals, types, current address/function, and entrypoints all returned HTTP 200 with `isError=false`.
- Segments: `.text` `0x1000 -> 0x11000`, size `0x1000`; `.data` `0x2000 -> 0x12000`, size `0x1000`. Functions: `0x11000`/55, `0x11037`/571, `0x11272`/63, `0x112B1`/34, `0x112D3`/33.
- MCP decompile confirms the Setup gate, Q3 command path, mask verification, and reset call; it emits variable-overlap warnings. MCP string filtering misses UTF-16 `Setup`/`SMU` strings seen by raw bytes/Rizin.
- Transcript manifest: `evidence/firmware-audit/mcp/Bc250CoreUnlockDxe-20260911/manifest.json`, SHA-256 `3df026be426c0fda0ebdf6a80ae041f4846f788ee5def841268969cc0d6f3e0a`.

## F10 — Programmer configuration evidence

- Operator supplied CH347T and configured IMSProg profile: `SPI_FLASH`, `WINBOND`, `W25Q128BV`, `16 M`, page `256`, block `64 K`, `3.3 V`, 4-byte address `No`.
- Host read-only metadata: WCH/QinHeng USB `1a86:55db`, `/dev/ttyACM0`, model `USB To UART+SPI+I2C`; installed IMSProg `1.9.1-1`, GPL-3.0-only.
- Preserved screenshot: `evidence/programmer/imsprog-chip-selection.png`, SHA-256 `cd4a135c9cd1e8f9030f98de21a5a06c31deef5c20569c964c2041b804a4639c`. Manifest: `evidence/programmer/imsprog-preflight.json`, SHA-256 `9e56fd4c85169fe6c3ff16a64dcbaf94b72817fc08e6786323d8a8f9845cf13b`.
- No JEDEC command or full programmer read has yet been issued. Chip marking/orientation, clip contact, board power isolation, two fresh read hashes, and exact programmer protocol remain pending.

## F11 — Programmer MCP/CLI evaluation

- No dedicated maintained MCP server for IMSProg/CH347T was found in the bounded local/GitHub repository search. GitHub API rate limiting and unavailable Serper search prevent a universal absence claim.
- IMSProg `1.9.1-1` is a Qt GUI. Its optional `.bin` argument selects a buffer file; it has no documented command-line Detect/Read/Verify operation or MCP endpoint.
- `flashrom 1.8.0-1` is available in Arch metadata. Pinned source commit `90b6b4376c7480a223e7bb5642e7116315ac6d09` implements `ch347_spi` for VID/PID `1a86:55db` (CH347T), 4-byte SPI, and selectable speeds. It is the preferred CLI read-only trial, not yet installed/run.
- Research note: `docs/research/2026-09-11-programmer-cli-evaluation.md`, SHA-256 `27ffa5eb31b341d45613db4fc87da326decb6b0cde76c78ddb43fd00f6d3cc95`.
- Planned first operation after power/orientation confirmation is Detect then two `-r` reads at a conservative SPI speed. No write/erase/status-register-write/Auto operation is planned.

## Q1 — Remaining decisive work

- Stop the fixture server, load the copied `Bc250CoreUnlockDxe` body, restart native MCP on loopback, and save module-specific read-only outputs.
- Reconcile MCP output with Rizin/`llvm-objdump` and exact source/body provenance.
- Complete the VCN map through PSP/TOS, SMU/PMFW, NBIF, UEFI dispatch, driver, MC/coherency, rings, and codec.
- Complete the memory/SoC-voltage map through NVRAM/APCB/PEI/SMU, including field units and training dependencies.
- Obtain programmer/chip metadata and two fresh matching reads.
- Decide whether to build a new APCB-only candidate and/or a separate memory candidate.
- Obtain independent review before any physical write.

## Reproduction commands

```text
python3 scripts/firmware_audit.py dump/2.bin --output evidence/firmware-audit/dump-2-inventory.json --extract-image dump/2.bin --extract-dir evidence/firmware-audit/dump-2-extract
python3 scripts/nvar_audit.py dump/2.bin --output evidence/firmware-audit/dump-2-nvar-primary.json --store-offset 0x0 --store-length 0x10000 --variable AmdSetup
python3 scripts/apcb_detail.py dump/2.bin --offset 0xAB1000 --output evidence/firmware-audit/apcb-detail.json
python3 -m unittest discover -s tests -v
python3 scripts/validate-contour.py
git diff --check
```

## Hash manifest for this draft

- `scripts/firmware_audit.py`: `5ead8605678fc5a13eb0cf49c01b43037560ddc485d8ad2686abf0e9c34d9593`
- `scripts/nvar_audit.py`: `16d35db736f5ca0e4423c444ff892b9d2b583bd8efcafda1a5e752ff04cb1160`
- `scripts/apcb_detail.py`: `80ea1708836ddee07747c7e507c908af08a7c9dbece197bfb4a6463879914711`
- `tests/test_nvar_audit.py`: `689020cc061c9e99c81b24a96fb8abf768d25973a05ec2e7cd2ddbb79bb7a78f`
- `evidence/firmware-audit/rizin/module-triage.json`: `6b43307c93b02b7bfd35b69a31900bda16e941088a2e0481a924a906824ac120`
- `evidence/firmware-audit/rizin/vcn-apcb-static-constant-scan.json`: `066bf18889edef6df8f8daad91721101b62e0f92da863e2168f0ee8868c1fef9`
- `evidence/firmware-audit/rizin/Bc250CoreUnlockDxe.corrected-summary.json`: `446d6b0df325781e7692cfdc545c8633a6ee918ef7ca35278dd714b313662760`
- `evidence/boardview/bc250-connector-map.json`: `fe6314c8098e146d2139da71dbb6dca75222f7bc639326f94061049929fc2379`
- `evidence/firmware-audit/mcp/Bc250CoreUnlockDxe-20260911/manifest.json`: `3df026be426c0fda0ebdf6a80ae041f4846f788ee5def841268969cc0d6f3e0a`
- `evidence/programmer/imsprog-preflight.json`: `9e56fd4c85169fe6c3ff16a64dcbaf94b72817fc08e6786323d8a8f9845cf13b`
- `evidence/programmer/imsprog-chip-selection.png`: `cd4a135c9cd1e8f9030f98de21a5a06c31deef5c20569c964c2041b804a4639c`


## F12 — Fresh CH347T baseline and APCB-only candidate

- Operator confirmed the BC-250 was fully unpowered, with the BIOS battery removed and only the programmer connected. This authorized the bounded read-only operation only.
- Signed Arch package `flashrom 1.8.0-1-x86_64` was verified with `gpgv`; extracted binary SHA-256 `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`.
- `ch347_spi` at `1.875M` found `Winbond W25Q128.V` (`16384 kB`). Probe log: `evidence/programmer/probe-20260911.txt`, SHA-256 `c89588ff0a4889bf03d9ab2f7b12e0c56eb891c5f8746b5793f0664944c7cd1e`.
- Two full reads completed with exit 0. `read-a.bin` and `read-b.bin` are both `16,777,216` bytes, byte-identical, and byte-identical to `dump/2.bin`; common SHA-256 is `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`. Machine-readable provenance: `evidence/programmer/reads/20260911/manifest.json`, SHA-256 `80b34cb2be1706abeac499d95cc4ae1d0c55b05183add75b015ad85780cccb60`.
- Fresh `firmware_audit.py` checks pass for PSP (19 entries/checksum), BHD (4/checksum), APCB (`0xB70`/checksum), and 4 FVs. Fresh extraction found 234 executable modules and all 234 hashes match the existing dump extraction.
- Separate APCB-only candidate: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`. It changes exactly three bytes: `0xAB1010 F2->32`, `0xAB1132 1F->7F`, `0xAB116E 1F->7F`; all other bytes, including PSP/BHD/FV/FFS/NVAR, remain equal to the read baseline.
- Candidate reports: `evidence/candidates/BC250_APCB_DFG_only_v001/apcb-detail.json` SHA-256 `01feebf8bb82ea17d6ef12138445573128eae94d171ee8180608ec0cb72abf9e` and `firmware-audit.json` SHA-256 `0b1b273dd233e3e102cc9df333221eee68b593ac80736e9e38bfb5ee4cb26fac`; build manifest SHA-256 `1a69c72b03d9fc513686c56198e644ffa42f9e2cd986213ae82c0f64d54e61da`.
- Status: `statically-verified-offline-candidate`; no flash, boot test, PSP acceptance test, VCN runtime test, memory training test, or voltage-rail test has run.

## Q2 — Remaining decisive work after fresh baseline

- Complete native MCP read-only calls for pending UEFI modules and reconcile them with Rizin and source.
- Complete the VCN path map through PSP/TOS, SMU/PMFW, NBIF, UEFI dispatch, PCI/driver, MC/coherency/rings, and codec.
- Complete memory/SoC-voltage field semantics, units, consumers, and training dependencies. Do not choose a voltage value from an unproven unit.
- Obtain an independent review of the candidate diff, recovery path, and failure modes.
- No candidate flash is approved.


## F13 — VCN and memory/SoC evidence maps

- VCN evidence map: `evidence/firmware-audit/vcn-evidence-map.json`, SHA-256 `ab683aaacfa77b71ec6404f714cb66b39210f6c57509f457082b5f09bbdc08b5`. It distinguishes IPDS descriptor, PSP/PMFW, `$PS1`, APCB DFG candidate, UEFI/Rizin literals, CoreUnlock MCP, host source, and unresolved runtime/codec edges.
- Memory/SoC-voltage evidence map: `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`, SHA-256 `6dae6540db6944e9a570b60db2293e8d26a3bcb27507c5693102882a00e2c34f`. It records fresh-read AmdSetup/NVAR values, IFR types/options, APCB MEMG/DFG groups, UMC instances, module hashes, and historical OC profile deltas.
- Fresh AmdSetup report: `evidence/programmer/reads/20260911/firmware-audit/read-a-nvar-primary.json`, SHA-256 `d3e769533368d0fcbfad476e6c2b75f510d1b4f80d356c4b8ff72bdfd3673b65`; values match the prior dump report and three tail warnings reproduce.
- The memory and SoC-voltage candidate tracks remain `NOT BUILT`: units, consumers, training dependencies, and live rails are not proven. No voltage was guessed.


## F14 — Separate memory-clock candidate

- Built `candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin` from the matching fresh baseline. SHA-256: `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee`.
- Exact diff: one byte at absolute `0x7E5` (`AmdSetup+0x316`), `FF` (Auto) -> `23` (IFR-labelled 1750MHz). No UCLK/FCLK/voltage/timing/APCB/PSP/`$PS1`/BHD/FV bytes changed.
- Validation: NVAR report `evidence/candidates/BC250_MemoryClock_1750_only_v001/nvar-primary.json` SHA-256 `06710664aa71770881221401da74c1fa1ce224e8eaf1e5940176490a69a927f5`; full firmware report SHA-256 `83b82cd738bc7d668ac90f568066ef451ffc2075af36d2b2fde5bc4e951dcae8`; build manifest SHA-256 `f9c72180e2d67c0eef7c3128456dde87478b89d5b1a06d20f76e63539db4f61f`. All parser/checksum checks pass and only `MemoryClockSpeed` differs from baseline.
- Status: `statically-verified-offline-candidate`. Memory training, live clocks, stability, bootability, and independent review are unrun. This is not a voltage or combined candidate.
- SoC-voltage candidate remains `NOT BUILT`; no voltage value has been guessed or recommended.


## F15 — Independent candidate review

- APCB candidate review: `evidence/candidates/BC250_APCB_DFG_only_v001/independent-review-gemini.md`, SHA-256 `90e15006a3093c8ba484fa702d4dab12225d522878892e6bba01d39666db7905`. Root rechecked the actual artifact and hash.
- Memory candidate review: `evidence/candidates/BC250_MemoryClock_1750_only_v001/independent-review-gemini.md`, SHA-256 `47a9b6a7be4628861ac04031e959a6ea76b1b67bfe7f724c8ba0b66b330123fb`. Root rechecked the actual artifact and hash.
- Both reviews independently PASS the requested static scope: exact source/output hashes, expected diff, parser/checksum results, and unrun limitations.
- Neither candidate is declared safe, signed, bootable, PSP-accepted, runtime-verified, or approved for flash.


## F16 — Historical VCN runtime limitation

- Imported mode-1 log `import/from-windows/Users/kukuruza/tmp_bc250/recon/vcn-probe-mode1_2026-08-26.out` (SHA-256 `920d82c67ddd3b937fba8f5fabc04ec532f0be10e42a9647baac3cca48fc970a`) reports VCN firmware/ring enumeration and then `-110` IB ring-test failures for `vcn_dec`, `vcn_enc0`, and `vcn_enc1`.
- This remains historical evidence. It does not prove the current board state, codec success, or root cause. A fresh stock-boot baseline is required.
- VCN map SHA-256: `7ad5f17b2b75c0e19a57ef3953e69be8c4b78a534e799406b7e2bdc89fbdf421`; memory/SoC map SHA-256: `215aafba73e28cdd5d22b4b328baa24f01db2853abc20cf47488fed0177e1460`.


## F17 — VCN DXE/probe safety classification

- Imported `Bc250VcnUnlockDxe.efi` and `Bc250VcnProbeApp.efi` remain static-only references. Rizin analysis shows Q2/Q3, SMU SRAM, privileged SMN gasket/DF, VCN power/clock, and PCI writes; the probe app can chainload a bootloader.
- They are not approved read-only probes and were not executed. Dxe manifest: `evidence/firmware-audit/rizin/dxe/manifest.json`, SHA-256 `58a4f7bf9aefa04e1f7300ddbb26d104cfc5e424fa3dde09f4afbbf72f5fcebe`.
- VCN map SHA-256: `0dc07ac65ada78a77b47ca68453e2a795468a2d742ee9254f853a926e9b96ec7`.


## F18 — Correction to the earlier programmer status

- Earlier F10/F11 text saying no programmer read had been issued is superseded by F12: after explicit power-isolation confirmation, signed pinned flashrom completed a successful probe and two matching full reads.
- Current readback status is hardware-verified for the SPI capture only. No firmware write or erase occurred.
- Programmer research note current SHA-256: `3e082b56514be95a94011f183b23ccda1dca8a6d4fbd6e7e72ce92030b193d57`.


## F19 — Current synchronized status

- VCN map current SHA-256: `0dc07ac65ada78a77b47ca68453e2a795468a2d742ee9254f853a926e9b96ec7`. Memory/SoC-voltage map current SHA-256: `2d0433c5dae972216bc55a0034724540331b49de4ed14321309012e097a057a8`.
- Both offline candidates have independent Gemini review artifacts rechecked by root.
- SoC-voltage candidate remains unbuilt. No voltage value is selected.
- Flash/write gate remains closed; current hardware evidence is limited to the two matching readback images.


## F20 — Final current evidence snapshot

### Passed

- Hardware readback: two independent 16 MiB CH347T reads match each other and `dump/2.bin`; SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Current-image structure: PSP/BHD/APCB checksums, 4 FV inventory, fresh NVAR/AmdSetup parse, IPDS table sums, and 234-module extraction/hash reconciliation.
- APCB candidate static checks and independent review: candidate SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`; review SHA-256 `90e15006a3093c8ba484fa702d4dab12225d522878892e6bba01d39666db7905`.
- Memory candidate static checks and independent review: candidate SHA-256 `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee`; review SHA-256 `47a9b6a7be4628861ac04031e959a6ea76b1b67bfe7f724c8ba0b66b330123fb`.
- Repository contour, tests, syntax, and diff checks pass. Native MCP server cleanup is complete; no listener remains on port 8000.

### Unrun or incomplete

- Full native MCP transcript for pending modules; GUI control was unavailable in the current Wayland/Orca path, while Rizin coverage remains available.
- PSP signature acceptance, modified-image boot, VCN power/clock/MC/rings/codec behavior, memory training/stability/live clocks, and SoC-voltage rail response.
- SoC-voltage candidate: deliberately not built because units/encoding/consumer/training/telemetry are not proven.
- JTAG attach and any firmware/register/programmer write.

Current maps: VCN `evidence/firmware-audit/vcn-evidence-map.json` SHA-256 `cd5161981c161a060b6ff0a4c30bf05e5b91aa05b11f8c7268744e2eace99bb2`; memory/SoC `evidence/firmware-audit/memory-soc-voltage-evidence-map.json` SHA-256 `2d0433c5dae972216bc55a0034724540331b49de4ed14321309012e097a057a8`.


## F21 — Historical OC/SoC claim correction

- Historical OC documents and builders are retained as static references only. Their `u8/i8` and mV descriptions for `AmdSetup+0x6E6`, safety ranges, and post-profile behavior are not current proof and conflict with the corrected IFR `u32`/control-pair evidence.
- No historical `+35`, `+80`, or `+100` value is recommended. The SoC-voltage candidate remains unbuilt.
- Updated memory/SoC map SHA-256: `d93db2d4d5dd31627d949abc57182434c2e29e993f38496cb5df6527c556f442`.


## F22 — Root SoC-voltage static review

- Root static review: `evidence/firmware-audit/soc-voltage-static-review-root.md`, SHA-256 `d9cfbaca981c33181b04c7f9bc17aed35192cad4e762763ae25a9809f56a341b`.
- PASS: `AmdSetup+0x6E5` control and `+0x6E6` IFR `u32` value are directly located and reproduced from the fresh read.
- INCONCLUSIVE/UNRUN: physical unit/sign/encoding, exact PEI/DXE/SMU consumer, memory-training dependency, and live rail response. Historical mV/safety comments remain unverified.
- Decision: no SoC-voltage candidate or value is generated.


## F23 — Runtime SMU encoding context

- Imported `bc250_smu` sources show distinct mV, VID-step, IEEE-float-offset, and SoC-DPM clock protocols (`api_q3.py` SHA-256 `30464310e6c4f6146322dd0136255e7f6069c2c397509296e92519e0f0cd8c90`, `codec.py` SHA-256 `bb747622598b92ff43f10583ef93803bda4d6ae59b2480e74fc2abf6751db116`, `api_q2.py` SHA-256 `a5da57c58230e4be02204efb8791ff49082fe7d4b78890d838c47439c0ee8f8d`).
- They are write-capable and were not executed. None maps `AmdSetup+0x6E6` to an exact runtime message. This reinforces the no-guessed-voltage decision.
- Current memory/SoC map SHA-256: `5fb17da2fe66dfb2fb350a038894d1c3cdcc79795d47ad701b92bb741f04a9a6`.


## F24 — Derived-artifacts inventory

- Machine-readable inventory of current reads, candidates, parser reports, maps, reviews, specs, and runbooks: `evidence/firmware-audit/derived-artifacts-20260911.json`, SHA-256 `0aef5680451ea1d96ff1ff279872f29762b90b7d3f05e9723f1ca2493630f6ba`.


## F25 — SoC-voltage encoding ambiguity

- Added host-side formula comparison `evidence/firmware-audit/soc-voltage-encoding-comparison.json`, SHA-256 `3576ead3e78ab343cd93727046f2de44e135fb4a4d67024228fee114061823c5`.
- Raw historical values `0x23/0x50/0x64` yield different hypothetical meanings as offset mV, VID codes, or IEEE floats. This confirms that no voltage value can be chosen without tracing the closed consumer.


## F26 — Correction: SMU helper is write-capable

- Static inspection of imported `bc250_smu/api.py`/`transport.py` (hashes `584b135de0796e2b1e5d593b316457f18b5e5120bb3f8b5307acb551c2721185` / `4ec3ba8cc13ff4af8ab2e2e525edd145bb23ffe3c59098231ada36f45b6685a6`) shows PCI `O_RDWR`, SMN selector writes at `0xB8`, and mailbox command/argument writes.
- Query-named helper calls are therefore prohibited in a read-only stock telemetry session. No helper was executed.
- Direct sysfs/kernel/journal reads remain the only first runtime route.


## F27 — APCB candidate byte terminology correction

The independent review's `DFG Value LSB` wording is corrected. The changed bytes at `0xAB1132` and `0xAB116E` are the third byte (`+2`) of each little-endian DFG word; the least-significant byte at each word start is unchanged. The exact word values and three-byte diff are unchanged.


## F28 — Safe stock-runtime collector

- Added `scripts/collect_stock_runtime_readonly.py`, SHA-256 `ea128ffe4f7fb7151fd63575722e570c7920547c6b8251f923227a447d4571a9`. It excludes the write-capable `bc250_smu` transport and only reads allowlisted kernel/sysfs/journal/lspci/modinfo data.
- Synthetic fixture test PASS: `evidence/firmware-audit/collector-fixture-test.json`, SHA-256 `2c83872ef57929fdc5006e41ee67e4fe89db5bcc19137f57505419f1764c59f7`. Real stock boot remains UNRUN.


## F29 — Direct SMU mailbox context

- Bundled Rizin report `evidence/firmware-audit/rizin/AmdNbioSmuV10Dxe.mailbox-context.txt` (SHA-256 `c81b065ee241d336efa5354b38aa44668f3041d3162254152e2563eaf8a4e76c`) shows Q2 command/response/argument addresses passing through a service helper.
- No flow from `AmdSetup+0x6E6` to this mailbox path is identified. It does not justify a voltage value or candidate.


## F30 — Direct APCB DFG consumer context

- Bundled Rizin report `evidence/firmware-audit/rizin/AmdApcbObrDxe.dfg-context.txt` (SHA-256 `fcb666f776d700933878024166c39929147cf06210d85fd9ffbeceac72241201`) shows function `0x119DC` masking DFG token words with `0x001FFF00` and comparing the wildcard marker.
- `0x007FFF00 & 0x001FFF00 == 0x001FFF00`, so the APCB candidate preserves the marker while extending upper bits. The policy recipient and runtime effect remain unverified.


## F31 — Direct NBIO PEI DF context

- `AmdNbioGfxARIPei` forced-little-endian Rizin report `evidence/firmware-audit/rizin/AmdNbioGfxARIPei.df-window-context.txt` (SHA-256 `95ce1c7917dd12789e6af168dbbdfa046d0003ec653116e3f276da6ea74b8c68`) maps generic DF indirect read/write/read-modify-write helpers using `0x405C` and `0x4098`.
- This remains static write-capable context; no AmdSetup VDD or VCN-specific data flow is proven and no register write occurred.


## F32 — CbsBasePei default field context

- `CbsBasePei` direct Rizin context `evidence/firmware-audit/rizin/CbsBasePei-setup-defaults-context.txt` (SHA-256 `04f27d70a345d06a66dfae3f0af07185f5c742dd1049acd4057d167b9f53db2e`) shows a setup-like initializer writing the current defaults for MCLK/UCLK/FCLK, VDDCR_VDD control/value, DF override, and power fields.
- This corroborates layout/default bytes but not the downstream NVAR consumer, SMU application, or memory training behavior.


## F33 — Deterministic audit-state verification

- `scripts/verify_bc250_audit_state.py` (SHA-256 `88ebabef801051fd11ca64fcb02e2a729c475c0ad861cf7ce413f60fb5439d1f`) returned `14/14` pass.
- Evidence: `evidence/firmware-audit/audit-state-verification-20260911.json`, SHA-256 `d25777f9badce31633509f5746f590be0e843969c6bbce9148f2922128a6cc2b`.
- It verifies readback equality, candidate diffs/hashes, parser reports, reviews, and map references. Runtime and write gates remain open.


## F34 — CoreUnlock Setup/PPT correlation remains unresolved

CoreUnlock compares `Setup+0x1C4` with `0x000157C0`; the current generic Setup value is `0x00011940`. The separate `AmdSetup+0x70C FAST_PPT_LIMIT` is also `0x000157C0`. This numeric coincidence is observed but does not prove that the CoreUnlock gate reads the PPT setting or any voltage field.


## F35 — APCB DFG-only SPI write and readback

- The operator approved exact candidate `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`, for board `BC250-01`.
- A new full pre-write dump matched both preserved stock reads byte-for-byte at SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Pinned/signed `flashrom v1.8.0` detected Winbond `W25Q128.V`, wrote the candidate, and returned built-in `VERIFIED`.
- A separate full-chip readback is byte-identical to the candidate. Relative to stock, exactly `0xAB1010`, `0xAB1132`, and `0xAB116E` differ. PSP/BHD/APCB checksum checks pass, four FVs remain valid, and APCB DFG words are `0x007FFF00`.
- Evidence: `evidence/programmer/reads/20260911/apcb-v001-hardware-trial-manifest.json`, SHA-256 `e0488e8cc0d8d99c25b626ae08dec04db496256d20303fcaa03912b907c3e696`.
- Classification: hardware-verified only at SPI programmer write/readback layer. Cold boot, PSP acceptance, video output, VCN rings/codecs, and stability remain UNRUN.


## F36 — First APCB candidate boot produced no display

- Operator reports green/blue indicators and a red indicator between USB and Ethernet, but no display image on the first cold-boot attempt.
- Video-output criterion: FAIL. Boot stage, PSP acceptance, POST, and VCN state: INCONCLUSIVE because no POST/UART/network/Linux evidence was captured.
- The SPI image itself was previously read back byte-identical, so this is not evidence of a programmer transfer mismatch. It may indicate candidate rejection/boot failure, or a separate display/board-state issue.
- Stop repeated candidate boots. The next discriminating test is an exact stock rollback with full-chip readback followed by the same display test.
