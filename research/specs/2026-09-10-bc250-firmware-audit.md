# BC-250 firmware audit and two-track BIOS plan

## Title and scope

Conduct a reproducible, evidence-bounded audit of the authorized AMD BC-250 firmware corpus and maintain two separate technical tracks:

1. **VCN unlock / initialization track**: determine which combination of IP discovery, signed `$PS1`/SEC GASKET policy, PSP/TOS, SMU/PMFW, UEFI modules, PCI discovery, and host driver behavior is required for VCN operation.
2. **Memory performance / SoC-voltage track**: determine where MCLK/UCLK/FCLK, memory-controller policy, training parameters, and SoC-voltage controls are represented and what dependencies and safe limits apply.

The tracks share provenance, parser, Cutter, MCP, and recovery gates, but their candidate artifacts and experiments remain separate. The word `VCM` in the request is treated as `VCN`, because the current corpus and all existing evidence identify the video block as VCN. If `VCM` means a different IP block, stop and rename the track before patching.

This is an analysis and specification plan. It does **not** authorize firmware writes, register writes, programmer writes, DXE injection, flashing, or hardware mutation.

## Planning anchor

- Project: `/home/OWNER/orca/projects/bc250`.
- Primary structural baseline: `dump/2.bin`, 16 MiB, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Known firmware anchors in that baseline:
  - `$PSP` at `0x8E0000`, 19 entries;
  - `$BHD` at `0xAB0000`;
  - APCB at `0xAB1000`, size `0xB70`, checksum at `+0x10`;
  - `$PS1` gasket at `0x982000`, size `0x2E50`;
  - `$PS1` policy at `0x9CA400`, size `0x6E0`;
  - hardware IP discovery payload at `0x981A00`;
  - PSP type-8 SMU/PMFW blob at `0x8FF000`, size `0x40200`.
- Required reverse-engineering stack: Cutter `v2.5.0`, bundled Rizin, adapted `reverse-skill` methodology, and `CutterMCP_native v0.1.6` on `127.0.0.1` only.
- Current extraction output: 234 executable bodies from `dump/2.bin` (179 PE32, 55 TE), under `evidence/firmware-audit/dump-2-extract/`.
- Current evidence class is primarily `observed-bytes` and `static-analysis`. No current-board VCN, memory-clock, boot, PSP-acceptance, codec, or flash result exists.

## Current verified state

- PSP, BHD, and APCB structural checks pass on the named baseline.
- The current dump is not identical to historical `BC250_3.00.ROM`: 233 common module records, 231 common body hashes, differing `AMITSE` and `Setup`, and one dump-only `Bc250CoreUnlockDxe` body.
- The exact dump-only `Bc250CoreUnlockDxe` body statically reads SMN `0x0115A870`, tests low byte `0xFF`, sends Q3 registers `0x03B10A20/0x03B10A80/0x03B10A88` with command `0x98` and mask address, checks response `0x01`, rereads the mask, and requests a warm reset. It also reads `Setup` and skips this path when `Setup+0x1C4 == 0x157C0`. The retained `Bc250CoreUnlockDxe.c` is only a partial semantic reference because it lacks that guard. This is not proof that the target board executed it.
- IP discovery reports one die and 38 records; VCN HWID 12 has version `2.0.3`, harvest `0`, and bases `0x7800`, `0x7E00`, `0x02403000`. A descriptor is not proof of a powered or functional codec.
- The type-8 PMFW body and the current gasket/policy match the imported Robin3 baseline. Current static policy evidence shows `0x03E810=0`, clamped DF values, and no HWID-12 `0x0900Cxxx` writes.
- APCB DFG words at `+0x130` and `+0x16C` are `0x001FFF00`. The previously considered APCB-only change to `0x007FFF00` remains a **proposal**, not a built or accepted candidate.
- Four archived capture sets report two matching reads each, but the required current procedure still lacks two fresh matching reads with complete programmer/chip/voltage metadata.

## Connected groups and observed logic

### Shared evidence and tooling

- Preserve imported material and `dump/2.bin` as immutable provenance.
- Use existing parsers and reports first. New outputs go under `evidence/`, `reports/`, or `candidates/` with source/output hashes.
- Use copied executable module bodies for Cutter and MCP. Do not open the sole original dump in a write-capable analysis session.
- Native MCP read-only triage tools include health, initialize, tools/list, segments, functions, strings, bounded bytes, imports/exports, disassembly, decompilation, function detail, and xrefs. Mutation tools remain unused unless separately approved per call.
- Every claim record must contain: claim, artifact and SHA-256, byte/function address, command/tool, evidence class, independent check, status, uncertainty, and next discriminating test.

### VCN track anchors

1. IP discovery and PSP directory: HWID 12, VCN base addresses, harvest bits, table presence, and absence/presence of a dedicated VCN PSP entry.
2. `$PS1` SEC GASKET and policy: group order, register writes, DF/NBIF aperture, VCN/HWID-12 banks, `0x03E810`, signature boundary, checksum/hash fields, and donor-versus-current deltas.
3. UEFI dispatch path: `AmdNbioGfxARIPei`, `AmdNbioPcieARIPei`, `AmdNbioSmuV10Pei`, `AmdNbioBaseARIPei`, `AmdFabricAriDxe`, `AmdNbioGfxARIDxe`, `AmdNbioSmuV10Dxe`, `AmdPspPeiV2`, `AmdPspDxeV2`, `AmdApcbObrDxe`, `AmiApcbLibInterface`, `CbsSetupDxe`, and `Bc250CoreUnlockDxe`.
4. SMU/TOS/PMFW path: queue and C2P/mailbox interfaces, message identifiers, response checks, reset behavior, power and clock requests, and closed-code boundaries.
5. Hardware/driver handoff: PCI discovery, firmware names, MMIO aperture, VCN MC/coherency, rings, interrupts, power domains, and user-visible VA-API/codec behavior.

### Memory and SoC-voltage track anchors

1. APCB MEMG: all six subgroups, record headers, `0x6D6` values, checksum, ordering, duplicate records, and relationship to DFG.
2. UEFI setup/NVRAM: exact `Setup`/`AmdSetup` variable stores, field offsets, encodings, units, defaults, Auto/manual selectors, and whether active extended-CMOS values are outside SPI.
3. PEI and SMU consumers: `AmdMemAm4Pei`, `CbsBasePei`, `CbsSetupDxe`, NBIO/SMU modules, and any readers/writers of memory-controller or SoC-voltage policy.
4. Clock relation: MCLK, UCLK, FCLK, divider/mode controls, training dependencies, UMA split, and telemetry interpretation. Historical `UCLK=450`/`FCLK=450` is not live synchronization proof.
5. Voltage path: identify whether SoC voltage is represented in APCB, NVRAM, SMU policy, a signed `$PS1` group, board VRM programming, or only runtime firmware. Never infer a safe voltage from a string or one donor image.

## Use cases

1. Reproduce the current dump inventory and all provenance hashes.
2. Explain the smallest evidence-backed VCN initialization path without claiming hardware enablement.
3. Determine whether APCB DFG changes are sufficient, necessary, or only correlated with VCN discovery.
4. Determine whether the existing `Bc250CoreUnlockDxe` path is dispatchable and what it does statically.
5. Identify memory-control and SoC-voltage fields and their dependencies without selecting unsafe values by guesswork.
6. Produce separate, reviewable VCN and memory candidate specifications.
7. Preserve stock controls, recovery procedures, stopping conditions, and rollback before any future board test.

## Phased action plan

### Phase 0 — Baseline and session safety (partly complete)

- [x] Hash and preserve `dump/2.bin`, historical images, and archived capture sets.
- [x] Reconcile the imported corpus and classify excluded/secret-like material at the source.
- [x] Validate PSP/BHD/APCB and extract the UEFI FV/FFS tree using the path-parameterized parser.
- [x] Record Cutter/Rizin/MCP versions, hashes, loopback binding policy, and known Plus/native limitations.
- [ ] Obtain exact BC-250 revision, board identifier, programmer model/software/version, chip marking and JEDEC ID, capacity/package, voltage, adapter, and connection method.
- [ ] Obtain two new complete 16 MiB reads in separate files. Stop if they differ or chip identity/voltage is unclear.

### Phase 1 — Native Cutter MCP fixture and module triage (next action)

The user may first open `/usr/bin/true` only as a harmless MCP fixture. After health and handshake pass, use copied extracted modules, not the original image.

- [ ] Confirm Cutter's load dialog with default analysis settings.
- [ ] Open **Windows -> Plugins -> CutterMCPDock** and verify `Host: 127.0.0.1`.
- [ ] Start the server and verify `ss -ltnp` exposes only `127.0.0.1:8000`.
- [ ] Run MCP `initialize`, `tools/list`, and one bounded read-only query before any other call.
- [ ] Query the exact copied `Bc250CoreUnlockDxe` body, then the selected VCN/PSP/SMU/APCB/setup/memory modules.
- [ ] Save raw bounded outputs and request/response metadata under `evidence/firmware-audit/mcp/`; hash reports, not secrets.
- [ ] Compare MCP segments/functions/strings/disassembly/decompile results with Rizin and source. Record disagreement instead of choosing silently.
- [ ] Stop the server when the controlled trial ends.

### Phase 2 — VCN static evidence map

- [ ] Build a call/data-flow table with callers, callees, function offsets, constants, reads, writes, response checks, and unknown closed boundaries.
- [ ] Correlate the IPDS descriptor with `$PS1`, PSP entries, UEFI modules, PMFW, and host driver expectations.
- [ ] Locate all static references to HWID 12, `0x02403000`, `0x0900Cxxx`, `0x03E810`, SMN accessors, Queue 3, C2P, and VCN firmware/ring names.
- [ ] Separate three hypotheses: discovery-only, power/clock initialization, and full MC/coherency/ring/codec bring-up.
- [ ] Classify each link as `observed-bytes`, `static-analysis`, `emulated-or-host-tested`, `historical-report`, or `hardware-verified`.
- [ ] Mark the exact signature span and PSP acceptance behavior as unknown unless independently established.

### Phase 3 — Memory and SoC-voltage static evidence map

- [ ] Parse and inventory every MEMG subgroup and relevant APCB record with offsets, lengths, values, ordering, and checksum.
- [ ] Identify exact `Setup`/`AmdSetup` variable stores and map frequency, divider, timing, and voltage fields to consumers.
- [ ] Trace `AmdMemAm4Pei`, `CbsBasePei`, `CbsSetupDxe`, NBIO, and SMU readers/writers using MCP plus independent Rizin/source checks.
- [ ] Determine whether each setting is a boot-time policy, a signed supervisor policy, an SMU runtime input, board VRM control, or an unverified historical label.
- [ ] Define one falsifiable host-side test for each uncertain field. Do not combine memory frequency, divider, timing, and SoC voltage in the first test.
- [ ] Document training failure signals, safe rollback, and the minimum telemetry required before any future hardware test.

### Phase 4 — Host-side and emulated validation

- [ ] Re-run parsers on stock, current, and any derived copies, including malformed/offset/alignment fixtures where applicable.
- [ ] Use UEFI/QEMU or a disposable test environment only for components that can execute without BC-250-only hardware; label hardware-specific paths untestable there.
- [ ] Validate config encoding, PE/COFF/TE/FFS structure, checksums, and changed ranges independently.
- [ ] Use historical Linux driver/ring logs only as `historical-report` or `emulated-or-host-tested`; do not promote them to hardware proof.
- [ ] Preserve negative results, timeouts, and cleanups.

### Phase 5 — Candidate specifications, no flash

#### VCN/APCB-only specification (provisional)

If, and only if, the static evidence still supports it after Phases 1–4 and a fresh matching baseline exists:

- Source: the selected fresh read, never a historical donor or rejected candidate.
- New output: `candidates/BC250_APCB_DFG_only_v001.bin` or a dated equivalent; never overwrite the source.
- Allowed structured changes only:
  - `APCB+0x130`: little-endian `0x001FFF00` -> `0x007FFF00`;
  - `APCB+0x16C`: little-endian `0x001FFF00` -> `0x007FFF00`;
  - APCB checksum at `APCB+0x10`: recalculate and independently verify the expected change from the current dump's `0xF2` (the exact fresh-baseline result must be recomputed).
- Preserve all PSP entries, signed `$PS1` gasket/policy bytes, BHD, FV/FFS modules, and all unrelated NVRAM bytes.
- Reject the candidate if any byte outside the two DFG words and the APCB checksum changes, if the source is not a matching fresh read, or if signature boundaries/PSP acceptance are unresolved for the intended claim.
- This candidate would be `statically verified` only. It would not be called signed, safe, bootable, VCN-enabled, or hardware-accepted.

#### Memory/SoC-voltage specification (not yet parameterized)

- Do not choose frequency, timing, or voltage values until the exact field, unit, consumer, allowed range, and dependency are established.
- Keep memory-only, SoC-voltage-only, and combined candidates as separate outputs. The combined variant is not the first test.
- Any NVRAM/APCB change must have a new source/output hash, changed-range report, variable/APCB checksum validation, independent parser result, and review of training/recovery failure paths.
- If SoC voltage is enforced by signed `$PS1`, PSP/TOS, PMFW, or board VRM logic, an unsigned field edit is not a valid candidate merely because a host parser accepts it.

### Phase 6 — Independent review and hardware gates (future, not authorized now)

Before any physical write or runtime mutation:

1. Complete the two fresh matching reads and record board/chip/programmer metadata.
2. Verify candidate source/output hashes, exact changed ranges, format/checksum/signature boundaries, and independent parser results.
3. Obtain an independent review of the actual candidate diff, evidence, failure path, and rollback plan. Prefer a different model family; a worker dispatch is not a review.
4. Confirm recovery programmer, compatible voltage/adapter, verified full dump, rollback image, power procedure, and post-write readback method.
5. Obtain explicit approval in this exact form:
   `Подтверждаю запись файла <точный путь> SHA-256: <точный hash> на плату <идентификатор>`.
6. Test the smallest candidate first, with one changed variable and a stock control. Stop on readback mismatch, failed identity, training loop, no POST, loss of recovery access, or unexpected device state.
7. After an approved write only, verify cold boot, BIOS, PCI ID `1002:13fe`, `amdgpu`, VCN firmware/rings, clocks, `vainfo`, and a simple codec workload. For memory candidates also verify POST/training, telemetry, stability, and rollback.
8. Never infer VCN enablement or memory synchronization from a clean checksum, module enumeration, or successful build.

## Implementation checklist and completion criteria

### Shared

- [x] Corpus inventory and provenance snapshot.
- [x] Current dump hash and outer-structure validation.
- [x] Corrected UEFI extraction with independent 234-body count.
- [x] Native MCP loopback fixture trial and Rizin reports.
- [ ] Native MCP read-only analysis of the selected BC-250 modules with saved outputs.
- [ ] Reconciled evidence map with exact addresses and contradictory findings.
- [ ] Fresh programmer metadata and two matching reads.
- [ ] Independent review of candidate specifications.

### VCN track

- [ ] Static map from IPDS/HWID 12 through gasket/TOS, PSP mailbox, SMU/PMFW, NBIF/VCN, UEFI dispatch, driver, MC/coherency, and codec.
- [ ] Clear separation of discovery, power/clock, and user-visible codec claims.
- [ ] Decision whether an APCB-only candidate remains justified.

### Memory/SoC-voltage track

- [ ] MEMG/DFG/APCB inventory and checksum map.
- [ ] Setup/NVRAM field and unit map.
- [ ] PEI/SMU consumer map and dependency matrix.
- [ ] Separate, bounded candidate specification or a documented no-go decision.

The audit is complete only when every checklist item needed for the requested claim is passed or explicitly marked inconclusive/unrun, all remaining unknowns have a decisive next test, and no hardware mutation has been implied by static evidence.

## Open questions

### Blocking

- What exact closed PSP/TOS signature span and acceptance transform covers the relevant `$PS1` data?
- Does the target PMFW power and clock VCN after any policy/discovery change?
- Which exact UEFI/SMU path performs VCN MC/coherency/ring bring-up?
- Which exact fields encode MCLK/UCLK/FCLK, memory timing, and SoC voltage, and what are their units and dependencies?
- What board/chip/programmer/recovery facts are required for any future candidate test?

### Non-blocking for static mapping

- Does `VCM` refer to VCN in the user's terminology?
- Which Linux firmware and driver versions are expected after hardware discovery?
- Which historical telemetry values were captured from the current board versus a donor or another configuration?

Each question needs a named artifact, baseline, one-variable test, expected signal, timeout/stopping condition, and evidence class.

## Decision log

- **D-A1**: Preserve `dump/2.bin`, stock images, donor images, and imported source as immutable controls.
- **D-A2**: Use Cutter v2.5.0, bundled Rizin, and native MCP on loopback; Plus remains comparison/reference.
- **D-A3**: Use read-only MCP and static/host-side checks before any hardware operation.
- **D-A4**: Treat the current dump's `Bc250CoreUnlockDxe` as a static finding, not proof of execution.
- **D-A5**: Keep VCN and memory/SoC-voltage candidate artifacts separate; never combine changes in the first test.
- **D-A6**: The first possible VCN policy candidate remains APCB-only DFG, with exactly two DFG words plus the APCB checksum allowed to change.
- **D-A7**: No candidate is flash-ready merely because it parses, has a valid checksum, or resembles a historical donor.
- **D-A8**: All hardware writes remain blocked until recovery gates and explicit per-file/per-board approval pass.
- **D-A9**: The user's persistent-goal preference is stored in the continual harness: do not add a token budget unless explicitly requested; do not treat a host limit as completion.

## Programmer, board-view, and optional JTAG track

The operator reports that a programmer is connected, can take a fresh dump before any flash, and can attach JTAG for live debugging. These are permissions and setup reports, not yet verified electrical facts.

- Candidate BIOS/DXE builds are allowed in new, clearly named files. Every build remains a candidate until independent structural, hash, diff, signature-boundary, and recovery review passes.
- Programmer operations begin with identification and read-only capture. Record programmer model/software, chip marking, JEDEC ID, capacity/package, voltage, adapter, connection method, and two complete read hashes. Stop on any mismatch or identity/voltage uncertainty.
- The imported board-view source is a wiring lead only. Its report identifies `J4004` as the SPI header, `J5` as UART (`U_TX`/`U_RX`), `TPMS1` as an LPC/POST debug header, `I2C_HEADER1` as an SMBus header, and `J2` as a CPU-JTAG/debug header. The parsed J2 nets are `CPU_TCK` pin 2, `CPU_TMS` pin 4, `CPU_TDO` pin 8, and a TDI path through J2 pin 6 -> `N22562912` -> `R19` -> `CPU_TDI`; `CPU_TRST#` is traced through J2 pin 9 -> `N22563682` -> `R120` -> `CPU_TRST#`. The CAD labels J2 pins 1/19 as `+1.8V` and pins 3/5/7/17 as GND. `J4004` remains SPI and `TPMS1` remains LPC/POST, not JTAG.
- JTAG is read-only by default. Before attaching, independently verify J2 population, pin-1/orientation, live +1.8 V, reset behavior, debug security state, protocol, and safe attach sequence. Target-memory or register writes require separate explicit per-call approval, an action log, timeout, cleanup, and readback.
- If the board is powered for a read-only debug session, capture a stock baseline first and stop on unexpected reset, thermal/power behavior, or loss of recovery access.
- Board-view evidence paths and hashes are recorded in `docs/action-logs/2026-09-10-bc250-full-audit.md`; physical chip marking and pin-1 orientation still need operator verification.

## Verification, rollback, and evidence record

Every derived artifact receives:

- source path and SHA-256;
- output path and SHA-256;
- exact tool versions and command/procedure;
- structured transformations and changed ranges;
- checksum, compression, alignment, PE/TE/FFS, and signature-boundary checks;
- independent byte-level/parser comparison;
- evidence class and unrun checks;
- rollback and remaining uncertainty.

The source/output and experiment records belong in `docs/action-logs/` and the corresponding `memory/` file. No credential, token, private key, raw security material, or unredacted private export may enter these records.


## Status update — fresh baseline and first candidate (2026-09-11T06:35:58.525422+00:00)

- Read-only programmer gate passed for the bounded capture: operator confirmed the board was fully unpowered, the BIOS battery was removed, and only CH347T was connected.
- Pinned flashrom `v1.8.0` was signature-verified and run through `ch347_spi` at `1.875M`. Probe found Winbond `W25Q128.V` / `16384 kB`; expected database mapping is W25Q128BV (`EF 40 18`).
- Two independent full reads are byte-identical and each matches `dump/2.bin`: SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`. Read manifest: `evidence/programmer/reads/20260911/manifest.json`.
- Fresh parser checks pass for both reads: PSP 19/checksum, BHD 4/checksum, APCB `0xB70`/checksum, and 4 FVs. Fresh extraction yields 234 modules and all 234 module hashes match the prior dump extraction.
- First separate candidate built from `read-a.bin`: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`. It changes only APCB absolute bytes `0xAB1010`, `0xAB1132`, and `0xAB116E`; DFG words `0x001FFF00 -> 0x007FFF00`; checksum `0xF2 -> 0x32`.
- Candidate static checks pass: independent byte diff, APCB parser, full firmware parser, PSP/BHD/APCB checksums, and 4 FV discovery.
- Candidate status remains `statically-verified-offline-candidate`, not flash-ready. Independent review, signed-region acceptance, bootability, VCN runtime, memory training, voltage telemetry, and exact per-image/per-board approval remain open.

## Updated next actions

- Preserve the two-read baseline and stop using the old `F10`/`Q1` pending wording as current status; the historical entries remain for provenance.
- Complete native MCP read-only analysis for the pending modules and reconcile the VCN and memory/SoC maps.
- Investigate and document the exact semantics and units of memory/SoC fields before creating a memory/voltage candidate. Do not guess a voltage.
- Obtain an independent review of the actual candidate diff and failure/recovery path.
- Do not flash any candidate.
