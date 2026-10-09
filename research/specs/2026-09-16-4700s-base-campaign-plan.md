# 4700S-base campaign plan: take, dissect, modify, flash, verify

Date: 2026-09-16. Actor: root. Status: PROPOSED (no flash, no candidate build
under this plan yet). Operator order: 4700S-first; BC250-native P5.00 stays the
armed fallback. Tone rule for this campaign: forward-only language — every
blocker ships with its next action, owner, and unblock check.

## 1. Title and scope
Take AMD 4700S-stock BIOS (C0A-stock `bb2cf51d...` in hand; C06-C09 stocks
sought) as the base for a BC250 board image; reverse-engineer it with
Ghidra/Ghidra-MCP + Cutter/Rizin/MCP; modify it through a staged ladder;
flash each stage to BC250-01 with full recovery; climb the success ladder to
a working image (boot -> video -> Linux -> overclocking -> VCN -> TPM).
Out of scope: PS5 system software as a base (reference only, H2 confirmed);
coreboot/OVMF as a base (H3 out); flashing MOD packs (banned, G7).

## 2. Planning anchor
Exact starting artifact: `evidence/donor/amd-4700s-20260916/c0a.zip`
(pack `6df2317d...`) -> inner `C0A/C0A` (`bb2cf51d...`, 16 MiB, PSP-18 no
0x24/0x45, 4 FVs, 245 modules, APCB 0x488 stock DFG, AGESA V9, fTPM present,
no GOP/VBIOS). Target board: BC250-01 (last seen UP 2026-09-15; on-chip image
disputed `c0f5f1c5` vs `addef288` -> fresh capture mandatory before any write).
Recovery anchor: stock `read-a.bin` (`83c4e420...`) + proven CH347T/flashrom
1.8 `ch347_spi` 1.875M write+VERIFIED+readback flow.

## 3. Connected groups and observed existing logic
- 09-14 donor audit already compared corpus C0A vs BC250 dump: identical
  GfxPEIM entry skeleton, byte-identical SMU helpers, same PCD GUID, PCD token
  0x55-vs-0x68 delta (zero-initialized, no proven setter delta), t28
  equivalent svc sequences with zero tables, no hidden VCN carrier. Build on
  it; do not redo it. (`docs/action-logs/2026-09-14-donor-bios-4700s.md`.)
- D5-D19 campaign proved the unsigned-FV DXE surface: explicit-size LZMA
  envelope required (`0x420010`), same-slot replacement works, ReadyToBoot
  gasket writes wedge SMU (closed class). Any DXE-time change reuses the D8
  envelope + same-slot method.
- D3-B2/D3-A proved: PSP rejects relocated/stale-signature 0x24/0x45 carriers
  (fatal halt); APCB-only edits boot. 4700S HAS no 0x24/0x45 at all — the
  cross-flash tests whether Ariel boots BC250 with zero policy carriers.
- OC surfaces known: BC250 AmdSetup map (`evidence/firmware-audit/
  amdsetup-ifr-field-map.json`), donor Setup = AMIBCP-hide bytes only.
- Tooling baseline (inventoried 2026-09-16): Cutter 2.5.0 AppImage + isolated
  profile/launcher present; CutterMCP-native v0.1.6 read-only trial PASSED on
  fixture; Rizin 0.9.1 via Cutter bundle; Ghidra ABSENT, Java 17 present;
  UEFITool/CHIPSEC absent; no MCP listeners besides OpenCLI :19825.

## 4. Use cases (success ladder, each with signal + rollback)
- P0 POST+video: board initializes, display shows output. Signal: photo + UART
  if available. Rollback: stock reflash, 1 cycle.
- P1 Linux: boots to SSH on installed kernel. Signal: `uptime` + `lspci` GPU
  node. Rollback: same.
- P2 Overclocking: MemClk/GFX controls move clocks (SMU metrics oracle).
  Signal: metric delta one variable at a time. Rollback: previous stage image.
- P3 VCN: `vcn_v2_0` hardware attach + ring init + codec job. Signal: dmesg +
  working encode/decode. Rollback: previous stage image.
- P4 TPM: fTPM visible and functional (or dTPM via TPMS1). Signal: kernel TPM
  node + quote test. Rollback: previous stage image.
- Track B trigger: if P0 fails on 3 consecutive stages with distinct,
  documented causes, pivot to P5.00-native base + donor transplants (fTPM
  modules, OC defaults) instead of a 4th blind 4700S variant.

## 5. Implementation checklist
### Phase 0 — RE tooling stand-up — DONE 2026-09-16 (records in §5 of plan file history)
### Phase 1 — Static RE — DONE 2026-09-16 (`docs/action-logs/2026-09-16-phase1-static-re.md`)
- [x] 1.1 Census 85/128/31/20; P5.00-vs-dump 9 bodies + CoreUnlock-only-dump.
- [x] 1.2 Boot map: identical PEI order; AGESA drops CDBDK-44.0.0 vs RBNBDK-46.1.2.
- [x] 1.3 IFR: donor 40f/323q ONE OC question; CBS 71f/1193q BC250-only.
- [x] 1.4 fTPM stack complete on donor (PEI logic strings, no versions).
- [x] 1.5 Video: no GOP/VBIOS/GUID anywhere (symmetric unknown, OQ-N5).
### Phase 2 — Board-diff risks — DONE 2026-09-16 (`docs/action-logs/2026-09-16-phase2-board-diff.md`)
- [x] 2.1 FCH config identical; chip part = operator handoff (non-blocking).
- [x] 2.2 APCB map: UNKN/DFG/FCHG same; PSPG-i2, MEMG-i7/i8 (4 B), CBSG size split.
- [x] 2.3 MEMG delta = 2 bits (subgroup+0x94 `00000000` vs `00010020`); M2 surface.
- [x] 2.4 PCIe/GPIO/SIO/VRM risk list recorded.
- [x] 2.5 M0 GO memo (analytic GO, procedural gates listed).
### Phase 3 — Modification ladder — IN PROGRESS (M0/M1/M2 ready, M3 scoped)
- [x] M0 = C0A-stock as-is `bb2cf51d` (zero edits; analytically GO, gate pends).
- [x] M1 collapsed: no NVRAM edit (factory-empty stock); post-flash observation.
- [x] M2 built `049419cb` (4 MEMG bytes + checksum), verified + reproducible;
      review INCOMPLETE -> not flash-approved yet.
- [ ] M3 DXE/Setup adaptation design (CBS transplant scope; after M0/M2 signal).
### Phase 0 — RE tooling stand-up (no firmware writes) — DONE 2026-09-16
- [x] 0.1 Ghidra 12.1.3 + Temurin JDK 21 user-local; headless smoke PASSED.
- [x] 0.2 ghidra-mcp HEAD built, loopback :8089; CoreUnlock trial PASSED
      (5 fns + Setup guard + SMN/Q3 constants match the record).
- [x] 0.3 Parity via Rizin 0.9.1 (AppImage extract): identical census.
      CutterMCP-native GUI re-run skipped (needs dock click); 3-lens parity
      holds via Ghidra+Rizin+historical MCP record.
- [x] 0.4 UEFITool not needed; CHIPSEC DEFERRED.
- [x] 0.5 Recorded: `docs/research/2026-09-16-ghidra-stack-evaluation.md`,
      D19, `docs/action-logs/2026-09-16-phase0-re-tooling.md`.
### Phase 1 — Static RE of C0A-stock (read-only, /tmp + evidence/)
- [ ] 1.1 Module census 245 vs BC250 233/234: added/removed/same-GUID-diff-body
      table with per-body hashes (reuse `scripts/firmware_audit.py`).
- [ ] 1.2 Boot-path map: PEI order, memory-training entry (`AmdMemAm4Pei`?),
      FCH init, GPIO/SIO tables, NVRAM defaults consumed at PEI.
- [ ] 1.3 Setup IFR full decode (donor) vs BC250 map; list every OC-relevant
      form/field + default + visibility condition.
- [ ] 1.4 fTPM stack review (FtpmDxe/Pei + PSP dependencies) as the R4 carrier.
- [ ] 1.5 Video-path verdict: how each board gets pixels with no GOP/VBIOS in
      image (dGPU OpROM vs iGPU path vs GOP-in-DXE).
### Phase 2 — Board-diff risk closure (analysis + read-only probes)
- [ ] 2.1 Identify BC250 FCH part (visual + PCI + docs) vs Cardinal A77E.
- [ ] 2.2 APCB 0x488-vs-0xB70 token map: which ~1768 bytes are missing and who
      consumes them (apcb-policy-analysis).
- [ ] 2.3 Memory topology: GDDR6 SKU options, training-table board deltas,
      6C-vs-8C cause (downcore vs fused).
- [ ] 2.4 PCIe/GPIO/SIO expectation tables per board; misdrive risk list.
- [ ] 2.5 Go/no-go memo for M0 with residual risks ranked.
### Phase 3 — Modification ladder (new files only, reviewed diffs)
- [ ] M0 C0A-stock as-is (no byte changed): the pure cross-flash probe.
- [ ] M1 NVRAM-default adaptation (board-specific defaults only, documented).
- [ ] M2 APCB adaptation (token adds with recomputed checksum, nothing else).
- [ ] M3 DXE/Setup adaptation (same-slot + D8 envelope + IFR-correct edits).
- [ ] Each stage: source/output hashes, changed-range report, parser PASS,
      independent review PASS, then and only then flash candidacy.
### Phase 4 — Flash-and-verify ladder (per stage; G4 logged before+after)
- [ ] Fresh pre-write capture (2 matching reads) + chip identity + NVRAM-drift
      note; stock recovery re-verified.
- [ ] Exact operator approval in the form: `Подтверждаю запись файла <exact
      path> SHA-256: <exact hash> на плату <identifier>`.
- [ ] Write + flashrom VERIFIED + independent full-chip readback identical.
- [ ] Cold boot through P0->P4 signals in order; first failure stops the climb,
      evidence preserved, rollback flashed + readback-verified.
- [ ] Result recorded in `memory/` + action log with evidence class per claim.

## 6. Open questions (blocking vs non-blocking)
Blocking (must close before M0 flash):
- OQ-B1: current on-chip image identity (fresh capture settles it).
- OQ-B2: BC250 FCH part + SIO/GPIO population (misdrive can damage hardware).
- OQ-B3: memory-training board deltas (no-train = no-boot, safe but blind).
Non-blocking (close in parallel, needed for M1+):
- OQ-N1: numeric AGESA/SMU/ABL per image (string/PE review).
- OQ-N2: P5.00-vs-P3.00 VCN-policy delta (Track B readiness).
- OQ-N3: `clv` variant meaning (custom mod? whose?).
- OQ-N4: TPU-Renoir vs press-Ariel taxonomy (naming only, no byte impact).

## 7. Decision log (plan-local; durable ones get promoted to memory/decisions.md)
- PD1 2026-09-16: 4700S-first order accepted (operator); P5.00-native armed as
  Track B with an explicit trigger (3 distinct P0 failures), not as drift.
- PD2 2026-09-16: MOD packs (`e8fa745b`, `26863de9`) are reference-only, never
  flashed (G7 record stands).
- PD3 2026-09-16 (proposed): Ghidra + Ghidra-MCP joins the stack as the primary
  MCP-RE lens next to Cutter (operator-named); Cutter remains mandatory for
  GUI work; parity required before trusting either alone. Promote to
  decisions.md after Phase 0 trials pass.
- PD4 2026-09-16: M0 goes as-is (zero bytes changed) so the first result is a
  clean board-compatibility discriminator, not a compound edit.
