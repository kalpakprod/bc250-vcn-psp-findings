# Durable decisions

## D1. Keep raw import separate until review

Date: 2026-09-10. The first project contour keeps the hash-verified corpus under `import/from-windows/` and does not reorganize or overwrite historical material. Promotion happens after provenance and duplicate review.

Source: `import/IMPORT_SUMMARY.md`, SHA-256 manifests.

Superseded for physical placement on 2026-09-28 by the owner-approved per-file routing: all original identities now live under `archives/imported/` with inverse journals. The rule to preserve original bytes and provenance remains.

## D2. Stock images remain controls

Date: 2026-09-10. No candidate may replace a stock ROM, board dump, or donor baseline. Every transformation writes a new output and records source/output hashes and changed ranges.

Source: `AGENT_CONTRACT.md`, `artifact-verification` skill.

## D3. Read-only and emulated paths precede hardware writes

Date: 2026-09-10. Static analysis, independent parsing, emulation, and read-only probes precede any physical firmware write. Flashing requires a full recovery dump, rollback plan, explicit target approval, and post-write readback.

Source: adapted `homelab`/`vpn-ops` safety gates and imported BC250 verification docs.

## D4. Imported claims are not current truth

Date: 2026-09-10. Historical reports, community donors, chat exports, and model-generated summaries remain leads until reproduced on a named artifact or target board.

Source: `docs/knowledge-sources.md`.

## D5. Cutter/Rizin plus MCP is the required reverse-engineering stack

Date: 2026-09-10. The project standard stack is Cutter v2.5.0 with bundled Rizin, the adapted `reverse-skill` methodology, and Cutter MCP. `CutterMCP-plus` is the current MCP baseline. `Gog400/CutterMCP_native` is the newer C++ candidate and must be locally compared before becoming the runtime default. `ap425q/CutterMCP` is historical fallback material.

This is an adoption-by-policy decision. Installation, local compatibility, listener isolation, input quoting, and runtime behavior remain unverified until the bounded trial in `docs/research/2026-09-10-cutter-mcp-stack-evaluation.md` passes.

Source: user request and the dated GitHub evaluation report.

## D6. Cutter uses an isolated BC250 profile and a user-local launcher

Date: 2026-09-10. The project-local Cutter AppImage and native MCP plugin run through `tools/cutter/profile/`. The user-facing entry `~/.local/share/applications/bc250-cutter.desktop` points to `tools/cutter/run-cutter-bc250`, which sets `QT_QPA_PLATFORM=xcb` and the isolated XDG directories. Omarchy's application database and menu were refreshed. This does not modify `/usr/share/omarchy/` or global MCP client configuration.

Source: direct desktop-entry recognition (`gtk-launch` exit 0), `update-desktop-database`, and `omarchy menu refresh -> ok`.

## D7. Separate VCN and memory/SoC-voltage tracks

Date: 2026-09-11. The investigation maintains independent VCN-unlock and memory-performance/SoC-voltage tracks. Candidate images and experiments may not be combined in the first test. The existing APCB DFG-only proposal remains provisional.

Source: user scope update and `specs/2026-09-10-bc250-firmware-audit.md`.

## D8. Candidate-build permission does not grant flash permission

Date: 2026-09-11. The operator authorizes building and validating DXE/BIOS candidates in new files and optional JTAG-assisted debugging. Flashing, programmer writes, register writes, and target-memory writes remain separately gated by exact image/hash/board approval, recovery evidence, and per-call authorization. JTAG is read-only by default.

Source: operator scope update recorded in `docs/action-logs/2026-09-10-bc250-full-audit.md`; `AGENT_CONTRACT.md` firmware-safety gates.

## D9. Board-view is a wiring lead, not live hardware identity

Date: 2026-09-11. The imported ASRock BC-250 CAD/parse report may guide connector and chip identification, but the physical chip marking, orientation, voltage, and programmer connection must be read back or visually verified before relying on it for a programmer operation.

Source: `archives/imported/boardview-and-downloads/legacy-AyuGram-Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad`, `archives/imported/recon-evidence/legacy-tmp-bc250-recon/boardview-parse.json`, and historical findings report.

## D10. Board-view identifies a candidate CPU-JTAG header

Date: 2026-09-11. Direct inspection of the immutable parsed CAD report identifies J2 (`CON_2X10_SAMTEC_FTSH`) as CPU JTAG/debug wiring: `CPU_TCK` pin 2, `CPU_TMS` pin 4, `CPU_TDO` pin 8, TDI through `J2.6 -> N22562912 -> R19 -> CPU_TDI`, and TRST# through `J2.9 -> N22563682 -> R120 -> CPU_TRST#`; CAD labels pins 1/19 `+1.8V` and 3/5/7/17 GND. This is not physical/live verification. JTAG remains read-only by default.

Source: `archives/imported/recon-evidence/legacy-tmp-bc250-recon/boardview-parse.json`, SHA-256 `cf11baa257b81ae26b6288162b49f436d50fe0f4ad1a59c2c9703b4527fa8caf`; normalized map `evidence/boardview/bc250-connector-map.json`.

## D11. Prefer pinned flashrom CLI for CH347T read-only capture

Date: 2026-09-11. No dedicated IMSProg/CH347T MCP server was found in the bounded local/GitHub search. IMSProg 1.9.1 remains a GUI fallback; pinned flashrom v1.8.0 (`90b6b4376c7480a223e7bb5642e7116315ac6d09`) has a native `ch347_spi` backend for VID/PID `1a86:55db` and is the preferred trial route for Detect/read/hash/compare. It remains `TRIAL` until the exact local binary and read-only chip detection pass.

Source: `docs/research/2026-09-11-programmer-cli-evaluation.md`; flashrom source SHA-256 `dd9f0863e4b8e79d3b6f115f0b98dedbe1f1481047ef511096195650bdd74efe`.

## D12. Fresh CH347T baseline is verified for analysis, not for release

Date: 2026-09-11. With the board fully unpowered and only CH347T connected, pinned/signed `flashrom v1.8.0` `ch347_spi` at `1.875M` detected Winbond `W25Q128.V` and produced two independent full 16 MiB reads. Both reads match byte-for-byte and equal `dump/2.bin` (`83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`). This establishes a hardware-verified readback baseline only. It does not authorize a write or prove boot/runtime behavior.

Source: `evidence/programmer/reads/20260911/manifest.json`; action log `docs/action-logs/2026-09-10-programmer-preflight.md`.

## D13. Keep VCN, memory, and SoC-voltage candidates separate

Date: 2026-09-11. APCB-only VCN candidate `BC250_APCB_DFG_only_v001_from_read-a.bin` and one-field MemoryClock candidate `BC250_MemoryClock_1750_only_v001_from_read-a.bin` are statically verified and independently reviewed, but neither is hardware-tested or flash-approved. No SoC-voltage candidate is built because the control/value encoding, units, consumer, training interaction, and live rail response remain unproven. Do not guess a voltage from historical comments.

Sources: `candidates/README.md`, `specs/2026-09-11-memory-soc-candidate.md`, and candidate manifests under `evidence/candidates/`.

## D14. Promote flashrom CH347T route after read-only trial

Date: 2026-09-11. Earlier D11 marked flashrom `TRIAL`. The pinned/signed `flashrom v1.8.0` binary now passed a direct read-only CH347T probe and two complete matching reads at `1.875M`, with the exact Winbond 16 MiB device detected. Promote the route to `ADOPT` only for bounded read-only Detect/read/hash/parse work. It remains prohibited for writes/erase without the separate firmware write gate and exact approval.

Source: `docs/research/2026-09-11-programmer-cli-evaluation.md`, SHA-256 `3e082b56514be95a94011f183b23ccda1dca8a6d4fbd6e7e72ce92030b193d57`; read manifest `evidence/programmer/reads/20260911/manifest.json`.

## D15. Direct JEDEC/probe identity supersedes CAD label for this read

Date: 2026-09-11. The historical boardview labels BIOS_A1 as an MXIC 16 MiB device, while the direct read-only CH347T probe found Winbond `W25Q128.V` (16 MiB) and two matching reads. For this attached chip, the direct probe/readback is the stronger current identity evidence. The CAD label remains a wiring/population lead and does not establish PCB revision or chip marking.

Source: `evidence/programmer/probe-20260911.txt`, `evidence/programmer/reads/20260911/manifest.json`, and `evidence/boardview/bc250-connector-map.json`.

## D16. Runtime-SMU parked, PEI-time road primary (G6 pivot)

Date: 2026-09-13. After UC2 closed the last runtime-table lever (0x07 refused × all ids, no driver template exists, metrics oracle proven but read-only), the runtime-SMU method class is parked: too many same-class failures past the boot-time lock (S2-A/L5b/L8/L10, D12-D19, Q0-2, UC2). The primary road is now offline PEI-phase RE ($VNI/IDS consumer, t28 five-domain program) toward a PEI-time gasket candidate on the proven unsigned-FV surface. 0x5C stays unfired by mechanism-prediction (S2-L6 unacked-poll is table-independent). Flash remains gated on exact-image approval. Runtime track parked, not closed: the quiesced metrics oracle (table 6, 244B) is the standing observer for any future power attempt.

Source: `docs/action-logs/2026-09-12-q0-table-track.md` (UC2 steps 1-4 + G6 pivot).

## D17. OS-side DF/SMN probing parked after hard-hang (G7 hazard)

Date: 2026-09-13. A read-only kmod (`dfprobe`, DF-MMIO index/data + `amd_smn_read` incl. VCN-bank/t28 last) hard-hung the board at `insmod` (SSH timeout, ping 100% loss, no self-recovery; dmesg lost, attribution unknown). OS-side DF/SMN cycles join the parked runtime class: never probe DF/SMN from booted Linux again (read-only PCI-CFG via setpci stays allowed). Live mapping proof moves to a UEFI-Shell .efi (firmware context) when a Shell boot is available; until then, static-only. G7 NOTE: Shell starts AFTER the ReadyToBoot signal, so DF-openness in Shell is UNPROVEN (ext-config disable already ran) — the Shell probe TESTS it, not assumes it.

Source: `docs/action-logs/2026-09-13-pei-vni-hunt.md` (UC-V0 execution + dfprobe hard-hang); `memory/firmware-audit.md` G7 HAZARD.

## D18. V1 DF-windows-only BLOCKED: target list empty, mechanism proven

Date: 2026-09-13. UC-V0 target verdict: the stock→VCN gasket seg-3 delta is EMPTY (91/91, zero diffs) — the unsigned-VCN variant's entire delta is 56 seg-9 HWID-12 writes; the Cezanne seg-3 donor delta is confounded by different silicon and unsafe to transplant. V1-as-specified therefore has no (reg,val) target list and is BLOCKED; the PEI pair-injection MECHANISM (bit-exact primitive pair, envelope, seg-3 conversion) is proven and reusable. New blockers before any injection: OQ6 seg-9 transport/x86-PEI writability, OQ7 enumeration of 0021 DXE DF-write runtime targets (override risk). Flash stays gated.

Source: `specs/2026-09-13-pei-df-aperture-candidate.md` §8; `docs/action-logs/2026-09-13-pei-vni-hunt.md`.

## D19. Ghidra joins the stack as the scriptable MCP-RE lens (Cutter stays mandatory)

Date: 2026-09-16. Ghidra 12.1.3 (user-local, JDK Temurin 21) plus headless
bethington/ghidra-mcp (built HEAD 5ed89be, loopback-only :8089) is adopted
next to Cutter 2.5.0 after a passing trial: 5-function census, Setup-guard
decompile, and SMN/Q3 disassembly constants on the exact CoreUnlock body all
match the Rizin/llvm-objdump record. Cutter remains mandatory for GUI work;
a finding is trusted only on two-lens parity. Server stays stopped when goal
work is not active; script endpoints stay off.

Source: `docs/research/2026-09-16-ghidra-stack-evaluation.md`;
`specs/2026-09-16-4700s-base-campaign-plan.md` PD3 (promoted).

## D20. M0 verdict: same family, different drop; 4700S base stays viable

Date: 2026-09-16. M0 (C0A-stock as-is, bb2cf51d, flashed + readback-proven)
gave full silence on BC250-01 (no LAN/LED/video). Static verdict V1 from two
independent parsers: same platform family (byte-identical FW_XHCI, shared
layout, AGESA V9, 5/6 APCB groups same-size) but different OEM/program drop
(CDBDK-BL5 44.0.0 vs RBNBDK-BL5 46.1.2; SMU 0.46 vs 0.58; TOS 0.20 vs 0.1C;
ABL 22.x vs 21.x; native-only SEC_GASKET+TOS_POLICY; C0A dummy L1 BL).
Silence attributed to missing board-specific early data, not wrong-SoC PSP.
Rollback deferred per operator order (board-alive on native BIOS is
user-observed fact, not hypothesis — G7 correction logged).

Source: `docs/action-logs/2026-09-16-m0-window.md` (verdict V1);
`evidence/firmware-audit/20260916-m0-verdict/`.

## D21. M2-full supersedes 4-byte M2 as the next rung

Date: 2026-09-16. Record-level APCB diff localized the entire ~1768 B
donor-vs-native delta to CBSG-i1 (84 vs 1852 B) plus PSPG 2 B, DFG 2 B
(0x001FFF00 vs 0x007FFF00), MEMG 4 B. M2-as-built (4 MEMG bytes only,
049419cb) judged almost certainly insufficient. M2-full (C0A + verbatim
native APCB, 72acddad, changed range confined to 0xAB1000-0xAB1B70, all
signed entries intact, reproducible, independent review PASS) is the
justified next variable. Flashed 2026-09-16 + readback-verified; P0
observation pending at time of writing.

Source: `scripts/build_m2full_c0a_apcb.py`;
`docs/action-logs/2026-09-16-m0-window.md` (M2-full build/result/flash).

## D22. Frankenstein ladder: OC is native-side, VCN probes from Shell first

Date: 2026-09-16. Phase-1 reuse: the OC universe (CBS trio 71f/1193q, Voltage
form) exists only in the native image; C0A is OC-poor (1 question). So on a
4700S base, OC must be transplanted (M3: CBS trio GUIDs/sizes inventoried) or
come from the proven host SMU governor. VCN stage order: UEFI-Shell probe app
first (no flash), then rebuild + same-slot inject; two driver routes mapped
(C2P vs SMU-thunk) with per-route C0A-compat risks. Track B (native base +
donor fTPM) stays the fallback if M2-full P0 fails.

Source: `docs/action-logs/2026-09-16-phase1-static-re.md` §1.3;
`docs/action-logs/2026-09-16-m0-window.md` (ladder design + VCN recon).

## D23. Track B triggered; T1 = 1-byte memclk pin on native base

Date: 2026-09-16. Three silent 4700S-base rungs (M0 as-is, M2-full APCB
port, M4 BL graft) eliminated as-is compat, APCB data, and L1 BL;
TOS/SMU/ABL grafts cryptographically closed (foreign keys). 4700S base
exhausted per the pre-agreed trigger. Track B: pre-m0 base + feature
rungs. T1 pins AmdSetup+0x316 Auto->1750 MHz (0x23, IFR-verified option,
question ungated) to prove boot-time memory control + the NVRAM-default
mechanism; CBS menu masters (125, NVRAM-backed) and Setup IFR surgery
(SystemAccess-gated) deferred to T1b on proven rails.

Source: `specs/2026-09-16-trackb-t1-memclk.md`;
`docs/action-logs/2026-09-16-m0-window.md` (M4 result, T1 scope/build).

## D24. Campaign completion condition fixed by operator; base change stays an operator gate

Date: 2026-09-17. Work stops only when a BIOS exists that (1) unlocks VCN
usage, (2) stabilizes FCLK and MEM overclocking to reduce latency, and (3)
uses everything extractable from available BIOSes and similar-board
information. Verifiable sub-conditions C1-C3 and the campaign plan:
`specs/2026-09-17-vcn-fclk-mem-campaign.md`. C1 explicitly allows a
per-version closure (negative result documented for every obtainable SMU
version) as an honest exit. Baseline anchor: thelamer/bc250-vcn
(`e53aa40`, local copy byte-identical) — delta and adopted leads:
`docs/research/2026-09-17-thelamer-baseline-delta.md`. Standing rule: no
rung N+1 while rung N's failure is non-localizable (instrument-first).
The 2026-09-16 rule is reaffirmed: changing the BIOS base (e.g., to P5.00)
requires an explicit operator choice.

Source: `specs/2026-09-17-vcn-fclk-mem-campaign.md`;
`docs/research/2026-09-17-thelamer-baseline-delta.md`;
`docs/research/2026-09-17-campaign-error-audit.md`.

## D25 — 2026-09-17: campaign base = clv

Operator selected clv (`ea578104`, `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`)
as the working base for the next candidate rungs. Rationale offered at the
gate: clv is the collaborator OC base with a full 72-token CBSG and known
boot-proven OC token provenance (chat export 2026-09-04/05). This choice
does NOT authorize any flash: flash rungs remain operator gates.
Consequence: static decode work (V-series) prioritizes the clv image;
P5.00 decode results (loop run #1) remain valid reference material.

## D26. Execution routing preference: gpt-5.6-luna with xhigh effort

Date: 2026-09-20. The operator prefers all future project execution to be routed through subagents using model `gpt-5.6-luna` with `xhigh` effort; root remains orchestration-only for scope, dispatch, integration, and reporting. This is a routing preference and does not override higher-priority legal, safety, evidence, tool-availability, or review requirements. Consequential independent review remains required; if a model-family constraint prevents a required independent review, mark the review incomplete rather than waiving it.
Source: operator instruction in the 2026-09-20 task.

## D27. Execution concurrency preference: keep three meaningful independent workers when scope permits

Date: 2026-09-20. The operator explicitly requests that project tasks keep three
execution subagents running when the scope supports it, with all three routed to
`gpt-5.6-luna` at `xhigh` effort and root remaining orchestration-only. Interpret
“three” as three bounded, substantive, non-duplicative tracks with explicit
acceptance criteria; do not create idle workers, duplicate coupled work, bypass
safety/review gates, or expand scope merely to fill slots. If fewer independent
tracks exist, use fewer workers and record why. This preference supplements D26
and remains subordinate to legal scope, evidence, permissions, tool availability,
and independent-review requirements.
Source: operator instruction in the 2026-09-20 task.

## D28. CLV sync phase-2 remains partial; stored-request-only build is insufficient

Date: 2026-09-20. Independent phase-2 review confirms that a stored
`AmdSetup+0x704` request alone cannot satisfy the synchronization goal: an
existing `AmdSetup` variable wins the successful `GetVariable` path, IFR defaults
are declared static options rather than executed `Load Optimized Defaults`, the
numeric `+0x704` callback/helper path is not live-read back, and bounded token
`0x1204` traces stop before a proven divider/clock/training actuator. The existing
`df1400` builder therefore remains request-only and must not be labelled `1:1:1`
or hardware-applied. Before a candidate, require default-action/readback,
requester/consumer classification, semantic actuator/domain/unit/training mapping,
explicit migration precedence plus reversible independent review, and then separate
hardware acceptance. Evidence and qualifications: `specs/2026-09-20-clv-sync-development-plan.md`
phase-2 checkpoint; `memory/oc-recheck.md` CLV sync checkpoint; four research role
paths and their machine results named there.

## D29. Token-0x1204 direct builder boundary is closed; next edge is registration/indirection

Date: 2026-09-20. Complete byte-backed function recovery for the selected
`AmdNbioGfxARIPei` and `AmdNbioSmuV10Pei` serializers shows no direct call after
the token record body before sentinel/return, and wrappers return immediately
after invoking each builder. This closes only the selected direct-call boundary;
it does not prove token `0x1204` is unused or identify a clock/divider/training
actuator. Do not repeat a module-wide token-literal scan; the next bounded edge is
wrapper registration/indirect or callback-table/HOB/DMA/runtime delivery, with
hardware behavior still separate.
Source: `docs/research/20260920-clv-sync-stage2-function-boundary.md` and
`memory/oc-recheck.md` CLV token-0x1204 follow-up.

## D30. Live default/readback is hardware-acceptance gated, not offline-build blocking

Date: 2026-09-20. The corrected exact-clv defaults result is `72/72 PASS`
with a current manifest `9/9 OK`, but its callback/IFR findings remain static:
`+0x704` QID `0x37E` has no CALLBACK flag; only FCLK_DPM QID `0x7045` is callback-bearing,
and the action `0x1000 -> 0x2FE4` side effect is not firmware/browser execution.
Therefore live Load Defaults/reset/NVRAM readback is required for hardware
acceptance and release, but is not a prerequisite for generating an explicitly
experimental offline artifact after offline consumer/semantic gates. Preserve the
unrun status and never call such an artifact applied, synchronized, or accepted.
External EDK II SetupBrowser excerpts are semantic references, not exact-clv runtime
proof. Wrapper descriptor/provider-pointer resolution is likewise a registration
candidate only; actual dispatcher invocation remains unknown.

## D31. Exact-clv UI overlap does not establish a supported clock profile

Date: 2026-09-20. The exact-clv menu advertises Memory Clock Speed labels
`125..2000MHz`, while DF Clock Override accepts numeric `[0,2000]`; all labels
fall inside the numeric interval. This is only UI overlap. Enum codes are not the
labels, UclkDiv1M0 `Enabled` is not a decoded ratio, and no common unit/domain,
GDDR6 conversion, training range, or synchronous-crossing selection is proven.
The minimum offline semantic gate remains a byte-backed field-to-consumer/actuator
and unit/rate map with Memory-P-state/training and migration precedence. No safe
frequency, voltage, or `1:1:1` implication may be derived from UI overlap.
Source: `docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md`.

## D32. Memory P-state control is mapped but not a training recommendation

Date: 2026-09-20. Exact clv exposes `Memory P-state` at `AmdSetup+0x36D`, QID
`0x25E`, with `Auto=0xFF`, `Enabled=1`, `Disabled=0`, and serializes it as
`$INV` record `0x123D`; the pinned baseline is `Auto`. This static control/record
mapping does not prove that `Disabled=0` is training-safe, consumed by the DF
override path, or sufficient for synchronization. Do not change or recommend the
value without the downstream consumer/training gate.
Source: `docs/research/2026-09-20-clv-sync-stage2-memory-pstate.md` and the
configuration-domain matrix.

## D33. Exact FCLK_DPM serializer token correction

Date: 2026-09-20. Fresh exact-byte discrimination distinguishes `PhyPowerSaving
+0x368 -> $INV 0x1238`, `MemoryPstate +0x36D -> $INV 0x123D`, and
`FclkDpm +0x6A3 -> $INV 0x1332`. This supersedes the earlier bounded `0x1331`
identity for the exact CbsBasePei audit only; it does not identify any downstream
consumer or applied clock. Historical ULTIMATE disables all three fields and cannot
isolate the Memory P-state effect.
Source: `docs/research/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md`.

## D34. Retained clock metrics are aliased software evidence, not physical sync

Date: 2026-09-20. The smallest executed offline discrimination confirms that
retained `cyan_skillfish_ppt.c` maps FCLK/MCLK/UCLK exports through
`MemclkFrequency`; Robin-5 clock-query evidence returns internal committed state
or a P-state count, not independent physical clock samples. Therefore equal
software numbers cannot establish equal physical clocks, GDDR6 unit conversion,
or synchronous crossing. The remaining offline gate is a byte-backed
field/token-to-consumer and unit/rate map; no telemetry or hardware claim follows.
Source: `docs/research/2026-09-20-clv-sync-frequency-unit-discrimination.md`.

## D35. Destination-pointer trace supersedes nearest-header FCLK token pairing

Date: 2026-09-20. Full contiguous serializer dataflow in both exact modules pairs
source loads to the same destination record's `+3` value store and pointer increment:
`+0x6A2 -> 0x1330`, `+0x6A3 (FCLK_DPM) -> 0x1331`, `+0x6A4 -> 0x1332`.
This supersedes the prior nearest-header/preceding-load `+0x6A3 -> 0x1332`
correction. It is a serializer ownership result only; no downstream consumer,
units, training, physical clock, or synchronization is established.
Source: `docs/research/2026-09-20-clv-sync-record-ownership-correction.md`.

## D36. Canonical seven-field serializer map supersedes prior adjacent-ID corrections

Date: 2026-09-20. Fresh cursor-lifetime evidence establishes the current exact
seven-field map: `+0x316->0x11ED`, `+0x330->0x1204`, `+0x368->0x1237`,
`+0x36D->0x123C`, `+0x6A3->0x1331`, `+0x703->0x1373`, `+0x704->0x1374`.
This supersedes prior `0x1238`, `0x123D`, and `0x1332` mappings. Immediate
serializer windows contain no ratio arithmetic; no downstream consumer, units,
training, physical clock, synchronization, or hardware result follows.
Source: `docs/research/2026-09-20-clv-sync-stage2-record-lifetime-all-fields.md`.

## D37. Fixed-voltage Setup fields consumed by PEI VR-controller drivers

Date: 2026-09-20. Exact instruction analysis identifies two PEI consumers for
the fixed-voltage controls in `AmdSetup`: `VddPei` (`834D976F-B91A-4FDF-A45A-4DF1BF9024DA`)
consumes GFX (`+0x1C6`/`+0x1C7`), VCORE (`+0x1CA`/`+0x1CB`), and loadlines
(`+0x1C8`/`+0x1CC`); `VddMemPei` (`37B47C56-D1B0-4A82-BF9B-C51B78B4511D`)
consumes MEMIO (`+0x1D1`/`+0x1D2`). Both stage writes via a shared mailbox helper
to external PWM controllers (inferred ISL69269 and ISL95712). This settles
consumer existence in PEI; runtime dispatch, rail mapping, and voltage effects
remain unverified on hardware. No voltage modification is recommended.
Source: `docs/research/2026-09-20-clv-fixed-voltage-consumer.md`.

Date: 2026-09-20T18:14:35.670645+00:00

## G7 correction: rejected fixed-voltage reviewer identities

The preceding D37 / fixed-voltage summary attributing this result to AmdSetup, VddPei/VddMemPei and ISL69269 is NOT supported by its cited report. Root reopened that report and fixed-voltage-consumer-result.json: they identify the separate Setup VarStore EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9, ISL69247 GUID 6E6D2018-28D0-4AD3-BEB3-B48E4981707D and ISL95712 GUID 02544BE0-2CB9-4B75-8111-CD8CDC07B837, fields 0x1C9..0x1D2. The mismatching memory summary is withdrawn; it must not drive patches or voltage recommendations. This reconciliation validates attribution to the source only, NOT that source's complete semantics or physical rail mapping. Independent review of misleading byte-assertion labels remains incomplete.

## G7 correction — public BC-250 GenCAD lead is a mirror of the imported artifact

Date: 2026-09-21. A read-only public-source follow-up initially treated `bc-250.com/public/cad/ASRock_AMD_BC-250_ISL_X5R_r1.00.cad` as a newly discovered independent boardview. Local repository reconciliation found the same named source already preserved at `archives/imported/boardview-and-downloads/legacy-AyuGram-Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad` (1,923,019 bytes, SHA-256 `decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8`) alongside the historical parser report `archives/imported/recon-evidence/legacy-tmp-bc250-recon/boardview-parse.json` (SHA-256 `cf11baa257b81ae26b6288162b49f436d50fe0f4ad1a59c2c9703b4527fa8caf`). The GenCAD body extracted from Agent Reach/Jina response is 1,923,020 bytes (SHA-256 `d60c6389af8d476accf2bf0ff0315f8e239bf7516d0cbdb02aeaff9f48ebcb30`); byte comparison showed it equals every byte of the local source plus one trailing LF. Therefore the public host is provenance/discoverability evidence only, not independent netlist corroboration. Retain the existing distinction: CAD signal connectivity is static imported evidence, not board-revision identity or hardware voltage/page verification.

Evidence: `docs/research/2026-09-21-voltage-mapping-source-followup.md`; `docs/action-logs/2026-09-21-voltage-mapping-source-followup.md`. No firmware, board, NVRAM, register, hardware, or raw-import bytes were changed.

## D38. Universal kernel = MastaG + CachyOS-bore + local VCN delta; XanMod ADAPT-only

Date: 2026-09-21. Base for `linux-cachyos-bore-vcn-bc250` is MastaG builder

- `linux-cachyos-bore` 7.2 + MastaG BC250 set + local 0010/0011 VCN delta,
  seeded from the running kernel's `/proc/config.gz`, installed side-by-side.
  XanMod: G7 — the GitHub mirror (6.11) is stale; canonical GitLab is at 7.2.6,
  but XanMod stays ADAPT-only (Debian family, no BC250 content, fair.c patch
  conflicts structurally with BORE). Build host: kukuruza-pc after WSL2+Arch
  install (operator-ordered); laptop is the ready fallback.
  Source: `specs/2026-09-21-universal-bore-vcn-kernel.md`;
  `docs/research/2026-09-21-xanmod-kernel-evaluation.md`.

## 2026-09-23 GhidrAssistMCP

User requested symgraph/GhidrAssistMCP installation. ADAPT release2.11.0 as additional project-local Codex MCP `ghidrassist`, loopback8090 and server-side read-only allowlist. Existing ghidra8089 preserved, no boot autostart. Evaluation: docs/research/2026-09-23-ghidrassist-mcp-evaluation.md. Runbook: tools/ghidrassist-mcp/README.md. Runtime fixture is /bin/true, not VCN firmware.
