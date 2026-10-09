# BC250 repository inventory — complete, directory by directory (2026-09-19)

> Historical inventory. Counts, contract names and plan locations below are
> dated, not current. Use `docs/repository-layout.md` and `docs/CURRENT-CONTEXT.md`.

Written after reading the repository end to end. Companion:
`docs/research/2026-09-19-consolidated-state.md` (the lock, the ledger, the open list).
Read both before starting any task.

## 1. Top level

| path                                                    | files                | role                                                                               |
| ------------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------- |
| `AGENT_CONTRACT.md`                                     | 29 448 B             | source of truth for project instructions                                           |
| `AGENT_CONTRACT_RU.md`                                  | 47 454 B             | Russian contract                                                                   |
| `AGENTS.md` `CLAUDE.md` `EMPRYO.md`                     | 29 448 B each        | byte-identical compatibility copies                                                |
| `docs/research/2026-09-15-independent-unlock-review.md` | 14 674 B             | independent unlock-claim review (mode 600)                                         |
| `README.md`                                             | 1 675 B              | start-here: AGENTS → memory/INDEX → knowledge-sources → skill → immutable original |
| `C:\Users\OWNER\e1_setup_ifr.txt`                         | 291 B                | stray artifact from a Windows-style path on Linux (audit item R-C)                 |
| `.agents/`                                              | 55 files             | 30+ skills, see §8                                                                 |
| `candidates/`                                           | 4 488 files, 848 MB  | 4 260 `.bin`; the D-series trees + named candidates                                |
| `docs/`                                                 | 218 files, 6.4 MB    | action logs, research, reference, runbooks                                         |
| `memory/`                                               | 19 files, 248 KB     | navigation, decisions, state, corpus, tools, questions, instincts, incidents       |
| `scripts/`                                              | 31 files             | 22 promoted scripts                                                                |
| `specs/`                                                | 21 files, 168 KB     | plans + lifecycle contract                                                         |
| `evidence/`                                             | 6 216 files, 1.9 GB  | programmer reads, runtime captures, firmware audit                                 |
| `import/`                                               | 219 275 files, 31 GB | hash-verified staging (4 679 `.md`)                                                |
| `tools/`                                                | 1 589 files, 290 MB  | `tools/cutter/` = pinned Cutter 2.5.0 AppImage + profile + MCP config              |
| `reports/`                                              | 1 file               | audit draft                                                                        |
| `tests/`                                                | 2 files              | `test_nvar_audit.py`                                                               |
| `old/`                                                  | 5 files              | session exports (codex 2.2 MB, prime-agent 13 MB)                                  |
| `Build/`                                                | 347 files, 5 MB      | EDK II build output                                                                |
| `dump/`                                                 | 1 file               | `2.bin`, 16 MiB, sha `83c4e420...`                                                 |

## 2. memory/ — the required entry point

| file                | content                                                                                                                                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `INDEX.md`          | navigation table — **read this first**                                                                                                                                                                           |
| `project-state.md`  | 21 585 B: dated state through 2026-09-17, incl. the C1 chain map                                                                                                                                                 |
| `decisions.md`      | 15 918 B: D1..D26+ with sources                                                                                                                                                                                  |
| `firmware-audit.md` | 142 629 B: the largest file — dump, extraction, module comparison, VCN evidence, G7 corrections                                                                                                                  |
| `open-questions.md` | 4 963 B: OQ1..OQ12; OQ8/OQ9 answered                                                                                                                                                                             |
| `corpus.md`         | import boundary, 218 616 verified records                                                                                                                                                                        |
| `evidence-model.md` | 6 evidence labels                                                                                                                                                                                                |
| `tools.md`          | reuse map + required external stack                                                                                                                                                                              |
| `instincts/*.yaml`  | 7 atomic rules (no-flash-without-recovery 0.99, preserve-stock 0.99, redact-at-source 0.99, verify-reconciliation 0.99, separate-evidence-layers 0.98, pgrep-self-match 0.97, read-evidence-before-verdict 0.95) |
| `incidents/*.md`    | 4 records: q4q1 board wedge, c0a/c08 mods-not-stock, m0 framing, vcn-exclusion misread                                                                                                                           |

## 3. docs/

| path                                                          | content                                                                        |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `action-logs/`                                                | 83 append-only logs, 2026-09-10 … 2026-09-19 (full list in §3.1)               |
| `research/`                                                   | 40 synthesis documents, see §3.2                                               |
| `reference/amd-bc250-docs/`                                   | full local mirror of the community docs site (source + mirror + MANIFEST.json) |
| `reference/verification-table.md`                             | claim → minimum evidence → not sufficient → status vocabulary                  |
| `reference/runbook-template.md`                               | the runbook contract                                                           |
| `runbooks/2026-09-11-bc250-programmer-and-candidate-gates.md` | programmer + candidate gates                                                   |
| `repository-layout.md`                                        | the earlier layout map                                                         |
| `knowledge-sources.md`                                        | evidence registry                                                              |

### 3.1 docs/action-logs/ (83)

Import/bootstrap 09-10 (6); VCN candidates + D-series 09-11/09-12 (24: d5..d20, s2a,
vcn-mode1-probe-audit 63 KB, q0-table-track 36 KB, flash-ladder-audit, deep-re-pass1);
PEI 09-13; donor + transport 09-14 (18); gaming/disks/review 09-15 (10); 4700S campaign
09-16 (11); campaign close-out 09-17 (6); this session 09-19 (2).

### 3.2 docs/research/ (the ones that decide things)

`2026-09-12-unlock-paths-map.md` (P1..P5 with proven/disproven per sub-path),
`2026-09-17-campaign-error-audit.md` (error register L0-L4 + forward tree),
`2026-09-11-vcn-unlock-synthesis.md` (5-layer kill model, E1-E5 exploit inventory),
`2026-09-12-injection-audit.md` (two-lock unified theory, S1-S5 surfaces),
`2026-09-12-nbif-clamp-mechanism.md` (the PEIM token serializer: `+0x1e0/+0x1e1 = 0x3`
clamped, `0x7` full-enabled; tokens `0x10c2/0x10c3` absent from flash),
`2026-09-14-vcn-mmio-map-audit.md` (the historical arbiter used WRONG labels),
`2026-09-15-smu-ipc-d-r1-result.md` (second-core IPC: sender decoded, receiver absent),
`2026-09-17-thelamer-baseline-delta.md` (thread-by-thread: 3 closed with hardware evidence),
`2026-09-17-decode-1-6-verdicts.md` (msg 0x8/0x9 NULL both versions; t28 chain mapped),
`2026-09-12-bios-vuln-inventory.md` (V1..V15), `2026-09-19-zero-day-confirmation.md`,
`2026-09-19-gasket-script-decode.md`, `2026-09-19-consolidated-state.md` (this session),
plus worker reports and stack evaluations.

## 4. import/ — the historical corpus

`import/from-windows/Users/kukuruza/` = `bc250-bios/`, `tmp_bc250/`, `Documents/Codex/`,
downloads, upstream. `import/IMPORT_SUMMARY.md` + `REFERENCE_LAYOUT.md` at the root.

### 4.1 bc250-bios/docs/ — the project's own book

`00-objective.md` · `01-psp-policy-chain.md` (`svc 0x7c(addr,value,4)` = the write
primitive; the consumer of the group-`0x210` records is NOT in the image) ·
`02-gasket-groups.md` (group semantics, stock vs donor, `xx234` family, VCN tail, DF window) ·
`03-d3-patch-status.md` (D3/D3-C/D3-B2 packages + risk per application path) ·
`04-external-repos.md` · `05-open-questions.md` · `06-overclock-timings.md`
(full AmdSetup offset map 0x316-0x39a, 0x700-0x71c, stock limits, no auto-revert exists) ·
`07-gpu-cu-unlock.md` (CU are GC registers, not BIOS carriers; 40 CU via driver/umr) ·
`08-verification-chain.md` · `09-vcn-bios-unlock-plan.md` (DXE+C2P plan; §6 admits
"Zero-Brick 100%" but VCN activation ~50-70% and calls a ~100% claim logically unfounded) ·
`10-runtime-unlock-recipe.md` (the C2P TOS recipe: `0x100B` token, `0x100C` load —
RSA tail NOT checked on this path, `0x1033` apply) · `CPU_MEMORY_OVERCLOCK_ANALYSIS.md`
(Oberon/GDDR6, FCLK 1000 : UCLK 875 : MCLK 1750, measured 140-142 ns).

### 4.2 bc250-bios/docs/source-docs/

`VCN-LOCK-MECHANISM.md` (637 lines — the 5 layers, the exact PSP directory with 19
entries, the `$PS1` signature scheme + key-id map, the full DFG decode §7, the FVMAIN
consumer hunt §7.5), `VCN-ATTACK-PLAN.md` (VULN-A/B/C, the wedging rule, next-PoC order,
feature levers), `VCN-EXPLOIT-SPEC.md`, `VCN-START-SAFE.md`, `VCN-UNLOCK-CORRECT-CHAIN.md`
(gates G0-G9, G5 = blocker), `roadmap_A_results.md` (A1-A6; A2: the t02 RSA verifier calls
`svc #0x63` and returns normally — rejection is not a halt), `unclamp_decode.md`
(prioritized reversible bit-writes), `vuln-1-gasket-runtime-reprogram.md` (VULN-B + the
2026-08-26 56-write PoC + the VULN-C wedge root cause), `vuln-2-unauthenticated-apcb-dfg.md`.

### 4.3 bc250-bios/tools/ + evidence/

`tools/psp-policy/` ~40 `a*` scripts (`a1_tos_policy`, `a26_donor_pairs`,
`a26b_xx234_semantics`, `a3_bank_map`, `c2_blob_builder`, `c2_disasm`, `b1_emul2`, …),
`tools/apcb/`, `tools/uefi/`, `tools/patch-build/`.
`evidence/a26_{STOCK,DONOR}_{24,45}_grp{201,280}_full.txt`, `a26b_xx234_semantics.txt`,
`fv_extract/BC250_3.00.ROM.dump/…` (incl. `21 AmdNbioGfxARIPei`), `c2_runtime_unlock_blob.bin`.

Relocation note (2026-09-27): the `bc250-bios/` headings above describe the original Windows layout. The intact source repository now lives in `archives/imported/historical-bios-repo/legacy-bc250-bios/`. Ten source documents have tracked derivatives under `docs/research/imported/bc250-bios-docs/`; eleven source documents still need individual promotion review. Its tools and firmware evidence remain historical, not implicitly approved for execution or flashing.

### 4.4 tmp_bc250/

| path                                                                                   | content                                                                                                                                                                                                                                                                                                                                                                                                                              |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `specs/2026-08-26-bc250-vcn-unlock-master-plan.md`                                     | **THE master plan** (gates, use cases 1-5, stage table, validation contract)                                                                                                                                                                                                                                                                                                                                                         |
| `specs/2026-08-25-bc250-vcn-2month-progress.md`                                        | 2-month progress                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `specs/2026-08-25-{gasket-diff,trusted-environment-report,community-second-gate-*}.md` | supporting                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `recon/`                                                                               | 82 `.py` + data: `smn_vcn_gasket_unclamp.py`, `smn_full_gasket_replay.py`, `analyze_*`, `audit_live_gasket_state.py`, `bc250_sec_gasket_banks_decoded.json`, `bc250_vs_cezanne_sec_gasket_diff.txt`, `bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.*`, `disasm_AmdNbio*ARIPei.txt`, `SMU-FINDINGS.md`, `SMU-HANDLERS.md`, `SMU_FIRMWARE_OVERVIEW.md`, `tg_2m_progress_digest.md`, thelamer/daveconde/aydencharles/zecoxao READMEs |
| `archives/imported/firmware-campaign/legacy-tmp-bc250-campaign/`                       | `bc250-smu-unlock/` (library + `unlock.py`), `daveconde-bc250-vcn-enable/` (`enable_vcn.py`, `vcn2_register_map.md`), `smn_full_gasket_replay.py`                                                                                                                                                                                                                                                                                    |
| `upstream/`                                                                            | `bc250-smu-unlock`, `daveconde-bc250-vcn-enable`, `amd_smu_reverse_engineering`, `edk2`, `thelamer-bc250-vcn`                                                                                                                                                                                                                                                                                                                        |
| `dxe/`                                                                                 | `Bc250VcnUnlockPkg/` — `Bc250VcnProbeApp.efi` (12 288 B, the zero-flash UEFI Shell vehicle) + `Bc250VcnUnlockDxe.efi` (4 608 B)                                                                                                                                                                                                                                                                                                      |

Relocation note (2026-09-27): the `specs/` rows above describe the original Windows layout; the files now live in `archives/imported/historical-specs/legacy-tmp-bc250-specs/`. The `dxe/` source and binaries now live in `archives/imported/uefi-source/legacy-tmp-bc250-dxe/`. The old EFI sizes in the table are superseded by the preserved 19,168-byte application and 5,984-byte driver. The imported ProbeApp writes SMU/DF state and must not be used as a read-only test.

### 4.5 Documents named but NOT on disk

`trace_sec_gasket_executor.py` (planned, P1.5a — never built),
`compare_sec_gasket_execution_paths.py` (planned),
`2026-08-26-bc250-sec-gasket-executor-workflow.md` (planned),
`0012-bc250-vcn-staged-hardware.patch` (planned).

## 5. candidates/ and evidence/

`candidates/` root: 30 named images (Recovery_FirstMarker `7d420c9f`, FirstMarker
`7d420c9f`, VcnUnlock_W9 `3c50bc9a`, VcnDispatchProbe, VcnSlot v001-v003, VcnTelemetry,
VcnUnlockDxe, MeiMeiDXE ×4, PURE_RECOMPRESS_CONTROL, D3B2/DXE_only/policy_only/
fulltransplant, M2/M2full/M4/M5/M6, T1/O1prep) + 16 D-series trees (each ~250 files,
23-45 MB) + `bc250-vcn-probeapp-v4/` (the live DXE source).

`evidence/`: `programmer/reads/` (1.6 GB, per-date readbacks), `donor/`
(`retroweb-20260916` = BC250 2.00/3.00/3.00CM/5.00/5.00clv + zips; `amd-4700s-20260916`
= C0A zip, `bb2cf51d`; `chat-oc-profiles-20260904`), `runtime/` (per-date captures +
`20260914-board-retrieval/` with the retrieved stage2b/stage4/stage5 scripts and the
`amdgpu` disasm), `firmware-audit/` (29 files + subdirs incl. `20260915-vcn-unlocked/`,
`20260919-zd/`, `ps1/`, `rizin/`, `oc-profiles/`), `boardview/`, `smu-ipc-d-r1/` (53 files).

## 6. specs/ (21)

Campaign/plan: `2026-09-17-vcn-fclk-mem-campaign.md` (**contains the operator's verbatim
completion condition C1/C2/C3**), `2026-09-16-4700s-base-campaign-plan.md`,
`2026-09-13-pei-df-aperture-candidate.md` (§8 = the V1-BLOCKED verdict),
`2026-09-13-q0-quiesced-redesign.md`, `2026-09-11-memory-soc-candidate.md`,
`2026-09-14-te-entry-comparison.md`, `2026-09-16-{m5-native-pei,trackb-t1-memclk}.md`,
`2026-09-11-vcn-d3b2-fresh-baseline.md`, the D5-D13 specs,
`spec-lifecycle/planning_contract.md`.

## 7. scripts/ (22 + caches)

`firmware_audit.py` (20 KB, the read-only inventory/extractor), `nvar_audit.py`,
`kdb_rsa_weakness_audit.py`, `apcb_detail.py`, `trace_te_entry.py`,
`build_vcn_d3b2_candidate.py` + `verify_vcn_d3b2_candidate.py`,
`build_vcn_policy_only_candidate.py`, `build_vcn_dxe_only_candidate.py`,
`build_apcb_dfg_candidate.py`, `build_amdsetup_memory_candidate.py`,
`build_m{2,2full,4,5,6}_*.py`, `collect_stock_runtime_readonly.py`,
`verify_bc250_audit_state.py`, `validate-contour.py`.

## 8. .agents/skills/ (30+)

Domain: `bc250-reverse-engineering`, `firmware-forensics`, `apcb-policy-analysis`,
`uefi-dxe-validation`, `vcn-smu-probing`, `artifact-verification`, `research-provenance`,
`cutter-reverse-engineering`, `external-stack-evaluation`, `spec-planning`.
Reasoning: `universal-critical-thinking`, `six-hats`, `inversion`, `lateral`,
`provocation`, `random-stimulus`, `scamper`, `worst-idea`, `concept-fan`, `analogy`.
Technical: `rsa-attack-techniques` (+ catalog), `symbolic-execution-tools` (+ angr
cookbook), `vm-and-bytecode-reverse`, `code-obfuscation-deobfuscation`, `omarchy`.

## 9. What this inventory changed

Before it, the same decode was re-derived three times (the gasket groups, the PSP key-id
map, the KDF/thread status) because the entry points were never read in order. The
required order is: `memory/INDEX.md` → `memory/firmware-audit.md` (the section named by
the task) → the numbered `bc250-bios/docs/` set → `docs/research/2026-09-12-unlock-paths-map.md`
→ `docs/research/2026-09-19-consolidated-state.md`.
