# Baseline delta: thelamer/bc250-vcn vs current project state

Date: 2026-09-17. Actor: root. Question: taking
https://github.com/thelamer/bc250-vcn as the initial state, has the project
genuinely advanced the VCN unlock, or drifted?

## Provenance record (per research-provenance)

- Source: https://github.com/thelamer/bc250-vcn, single commit HEAD
  `e53aa40d8a51c11a1a0fa939928164938924c4b0` ("initial notes", 2026-08-18).
- License: none in the repository. Working notes only (participant report /
  secondary source summarizing primary community repos). Reference-only;
  no code copied.
- Local copy: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/
thelamer-bc250-vcn/README.md` — byte-IDENTICAL to GitHub HEAD (diff
  empty, verified 2026-09-17). The imported corpus therefore already
  contains this exact baseline; no new external fetch needed.
- Related repos from its resource list, already local under `upstream/`:
  `amd_smu_reverse_engineering` (bc250-collective, full Ghidra SMU
  decompile), `bc250-smu-unlock` (rw-r-r-0644), `BC250-DXE-SMU-Core-Unlock`
  (RescueMei), `daveconde-bc250-vcn-enable` (enable_vcn.py — the parser
  whose header offsets were G7-corrected 2026-09-14), `PSPTool`, `edk2`.
- Additional mirror: `docs/reference/amd-bc250-docs/` (elektricm docs incl.
  `system/8core-unlock.md`).

## Baseline state (2026-08-18) — open threads

1. Diff power/clock/reset/isolation registers before vs. after dom6
   power-on; name the exact second gate.
2. Check whether slots 0x16/0x17/0x18 need programming as a prerequisite.
3. Trace the VCLK/DCLK enable routine; confirm clocks move after power-on.
4. Cross-reference Renoir/Van Gogh `*_dpm_set_vcn_enable` reset/isolation
   steps not yet replicated.
5. Only after the gate clears: decoder ring test.

## Current project state — thread-by-thread

| Baseline thread                 | Status now                                                                                                                                                                                                                                                                                                                                                                           | Evidence                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| 1. Name the second gate         | **CLOSED (named, runtime scope)**: not the gasket — donor aperture `0x03E810=6`/`0x03A2011C=0x107FF`/`0x03A20124=0x10FFF` + 56 bank-12 records latch (59/59 accepted, commit=1), full donor dataplane 15/15 accepted, island STILL isolated; the dom14-cluster power transaction never completes from ANY runtime path (fw polls and host-side doorbell); NBIF bridge stays all-ones | S2-A, stage5, S2-L8/L9/L10 (hardware-verified 2026-09-12) |
| 2. Slots 0x16/0x17/0x18         | **DONE** — clock-enable landed, slots ON/READY, up-ack                                                                                                                                                                                                                                                                                                                               | S2-A (hardware-verified)                                  |
| 3. VCLK/DCLK trace              | **DONE (static)** — metrics producer `0x29AEC`; slots 22/23 = VCLK/DCLK under the interface-v8 header; source-mode fields decoded                                                                                                                                                                                                                                                    | 2026-09-14 metrics-producer records                       |
| 4. Other-family reset/ISO steps | **PARTIAL** — v6.8 `vcn_v2_0_start` sequence decoded (PGFSM before POWER_STATUS); cyan_skillfish ppt has no `dpm_set_vcn_enable` (public-driver success is a no-op); NBIF/NBIO surface covered by PEIM/DXE decodes (S4 candidates disproven, `$VNI` table built at runtime)                                                                                                          | 2026-09-14 driver-start-contract; 2026-09-12 deep-re pass |
| 5. Ring test                    | **STILL BLOCKED — now with cause**: first VCN MMIO wedges while the domain is gated (controlled differential probe); firmware placement proven ≠ execution                                                                                                                                                                                                                           | mode2 controlled probe 2026-09-12                         |

## Beyond the baseline (new verified results)

- Per-version exhaustion verdict for SMU 0.58.6.0: five runtime experiments
  across modes 0/1/2 — the dom14 power transaction never completes; the
  isolation sits below every runtime-reachable register.
- Boot-time PSP policy carriers: signature-fatal (svc#6 ROM verifier halt,
  D3-B2 discriminator); APCB (unsigned) proven boot-safe by flash tests.
- BIOS-resident SMU-unlock substrate: D9R/D10R boot + unlock PASS
  (early-DXE, persists into Linux); its verification literally reads the
  8-core mask register `0x115A870` = `0x77` (stock 6C) — the unlock
  substrate runs on this board.
- Wedge taxonomy (safe/unsafe transport matrix) incl. SMU-mailbox wedges
  from reads of side-effect/dead SMN blocks.
- Key/policy map: `$KDB` 8+3 RSA-2048 keys, OEM policy key 96EA native-only
  -> native 0x24/0x45 carriers cannot verify under foreign key sets.
- Base/BOIS axis: C0A 4700S base dead (M0-M6, oracle-confirmed); P5.00
  newer SMU (`13c93c08`) identified — never decoded or probed; campaign
  plan `specs/2026-09-17-vcn-fclk-mem-campaign.md` targets it (V1-V4).

## Verdict on the question asked

Measured against this baseline the project has NOT drifted into wasted
motion on the unlock track: all five baseline threads are addressed (three
closed with hardware evidence), the blocker moved from "unknown second
gate" to a named mechanism with a version-scoped closure verdict, and the
next unprobed surface (P5.00 SMU) is pinned. The one detour relative to
this baseline was the 4700S BIOS-base flash campaign (M0-M6) — it served
the Frankenstein goal, not the unlock; its cost and lessons are recorded in
`docs/research/2026-09-17-campaign-error-audit.md`.

## Leads adopted from the baseline into the campaign checklist (C3)

- **v2000a** (amd/firmware_binaries, closest APU relative): compare its VCN
  power-up chain (PSP type-13 handling, ABL steps) against BC250 — unmined.
- **8c CPU unlock on BC250-01**: community-proven (GabriWar tool +
  Forbidden-Darkness DXE + mendesrr ACPI tables); our substrate verified
  (mask `0x77` readable via Q3 0x2A); the `0x98` write of `0xFF` was never
  applied on this board. Runtime candidate (reversible, cold cycle), needs
  matching ACPI tables for a clean OS view (mendesrr rebuild — FV graft on
  the unsigned surface).
- **Feature-bit naming**: apply `smu_v11_8_pmfw.h` names to the 64-bit
  feature framework decode (features 4/21 already mapped) for the ISO/
  reset hunt.
- **bc250-collective Ghidra project** (local): reuse as the lens/method
  template for the P5.00 SMU decode (V1) instead of starting from zero.
