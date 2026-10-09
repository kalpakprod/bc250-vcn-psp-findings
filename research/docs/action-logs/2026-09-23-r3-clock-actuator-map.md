# 2026-09-23 — R3: clock-domain actuator map + 1:1:1 structural negative (Plane issue #3)

## Intent

Work Plane board «BC250» issue #3 (R3, id `a204c671-4eeb-4027-bb28-a65050ee6a63`),
following the corpus's own next-step directive (close the 22D6C transitive link and the
clock actuator). Offline only; no firmware image, board, bus, or hardware state
modified. Inputs read-only: pinned donor ROM, pinned robin_5 slice, existing
20260923-abl95fc-next artifacts.

## Procedure

1. Read the R3 corpus: `docs/research/2026-09-21-smu-domain-selector.md`,
   `docs/research/2026-09-23-zen2-bc250-parameter-map.md`,
   `docs/research/2026-09-23-abl-pll-service-boundary.md`,
   `.procoder/specs/clv500-goal-final.md` (R3 text), plus the
   `20260923-abl95fc-next` row-writer/transition artifacts.
2. Wrote and ran `evidence/firmware-audit/20260923-r3-clock-actuator/DfCensus.java`
   (Ghidra 12.1.3 headless, existing `OCConsumer` project, `-noanalysis`):
   clock-domain setter family decompiles (0x23890/0x2379c/0x23ab0/0x23ac4/0x23cb8/
   0x23c78/0x23c40/0x231a8/0x2360c/0x2ec94/0x24410/0x2445c/0x235c8/0x1e448/0x1e7d8/
   0x1e720), DF-structure/row/descriptor hexdumps, reference census of the DF-base
   slot `0x171ec`, and a transitive closure of `FUN_00022d6c` (depth 3, 49 functions).
   Output: `df-census-out.txt` (3016 lines).
3. Recomputed domain table, DF rows, and the q3 0x1D selector array directly from the
   pinned image bytes (Python).
4. Wrote the result doc + deterministic verifier; ran gates.

## Result

- **Clock-domain actuator engine byte-proven**: `FUN_00023890(domain, code)` →
  descriptor `[0xF568 + domain*0x1C + 0x254]` (raw offset) → `FUN_000235c8` →
  SMN window `0x010FFE00+0x200`, poll `+0x24` bit 0x10000; IPC transport branch for
  raws inside `(0x5AFFF, 0x5B7FF]` (domains 3/4). Nine domain SMN addresses mapped,
  including FCLK 0x0115C0FC, UCLK 0x0115C8FC (+mirror 0x0116C0FC), derived
  0x0115C924/0x0116C124; domain 0x18 cross-check matches the independent 2026-09-21
  decode.
- **OS route closed for FCLK/UCLK**: the q3 0x1D selector→domain array (20 entries,
  image bytes) contains no domain 0x0E–0x12; the PLL domains are programmable only by
  the early ABL1 boot services.
- **DF pstate table decoded**: rows 0xCF0C.. (0x28 stride), row+0x18 floats
  450/450/850/1750/250 with derived halves at +0x10 and /16 at +0x14; row pointer
  array at DF+0x1C is zero in the image (runtime-initialized). No row+0x18 writer in
  the 22D6C closure (49 functions) — the extended bounded negative says the DF
  pstate frequencies are firmware constants.
- **1:1:1 structural negative**: UCLK's only found programming path divides the
  memory word by two (`LSR #1`, executed + emulated earlier); no `UclkDiv1M0`
  consumer found; default FCLK 1420 > UCLK 900 matches the native help. Static
  verdict: 1:1:1 is not reachable through stock firmware on the analyzed paths;
  falsifiers named (UclkDiv1M0 consumer elsewhere, second UCLK path, units, revision).
- `verify_r3.py`: **PASS, 46/46 checks**.
- Gates: `pytest tests/` 83 passed; `make test` 7/7 (results below in the session
  report).

## Writes

New files only (no existing file modified except plan/memory updates recorded below):

- `docs/research/2026-09-23-r3-clock-actuator-map.md`
- `evidence/firmware-audit/20260923-r3-clock-actuator/{DfCensus.java,df-census-out.txt,df-census-err.txt,verify_r3.py}`
- `.procoder/plans/clv500-actuator-first.md` (P2 clock sub-items, checkpoint)
- `memory/oc-recheck.md` (dated entry)
- Plane #3 progress comment (issue stays In Progress: the ABL/AGESA consumer edges
  for the six Setup fields and the units remain open)

No firmware image, board, bus, mailbox, NVRAM, or hardware state was touched.

## Pass 2 (same day): producer chains closed

Intent: close the remaining R3 consumer/producer edges — the ABL1 UCLK-argument
branch (0x5F1E..0x5FAE), the UclkDiv1M0 consumer search, the MemoryClockSpeed
producer, and the DfClockOverride→APCB link.

What was done (read-only analysis + new files):

- Full decode of ABL1 0x5E68..0x601A against the pinned ABL1
  (af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a):
  the value-table+clamp block 0x5F1E..0x5F9A is DEAD (its result slot [sp,#4] is
  overwritten by the FCLK default at 0x5FA8 before any read); the live UCLK
  argument is the unconditional LSR #1 at 0x5F30. Firmware strings name the
  services: GnbSmuInitAblCAR (function identity), PSPSMC_MSG_SetupFclkPll,
  PSPSMC_MSG_SetupUclkPll, PSPSMC_MSG_ConfigSocRail (ID 9; no voltage value —
  an R2-relevant observation).
- Corpus census reuse (20260919-inv-token-consumers, 517 byte-verified checks):
  the 7 target NVTB tokens are written by 7 PEIM modules at 49 sites; the only
  direct readers are 4 call sites (0x10FF/0x1104/0x1000/0x1001) — none of ours.
  UclkDiv1M0 (0x1204) has no consumer in the extracted corpus.
- ABL1 provider census: 0x463C has exactly one call site (0x5FAE, ID 0x0F =
  the FCLK override); APCB token 21 ("UclkDiv", +0x86E..0x872, value 01) is
  never read. Census artifacts (writer-census, emulation) from the same day
  were re-cited and re-asserted.
- Empirical diff: the operator's four SYNC OC profiles (incl. both 1:1:1
  attempts) are byte-identical to the clean donor in the entire APCB
  (0xAB1000, 2972 B) and differ only in the NVRAM store at ROM 0x0
  (EFI_SYSTEM_NV_DATA_FV): MCLK enum 0x24→0x23 (1800→1750; profile 02 → 0x1A),
  DfClockOverride 1420→875/1333/1750, UclkDiv-region 01→03. The Setup→clock
  bridge does not exist on the analyzed surface; the operator's 1:1:1 mods
  were structurally inert. 2.bin (board pre-flash BIOS) has a 2928-byte APCB
  without the 015F/0160 pair (different layout; boundary noted in the doc).

Writes (new files only; no existing evidence modified):

- `evidence/firmware-audit/20260923-r3-producer-chains/verify_r3b.py` — PASS
  (all assertions).
- `docs/research/2026-09-23-r3-clock-actuator-map.md` — updated: §2 refinement
  (dead table, service strings), new §4a (producer chains), §6 falsifier (a)
  closed, §7 open edges rewritten, Evidence section extended.
- `.procoder/plans/clv500-actuator-first.md` — producer-edges checkpoint.
- `memory/oc-recheck.md` — dated entry (append).

No firmware image, board, bus, mailbox, NVRAM, or hardware state was touched.

## Pass 3 (same day, ~21:00): 0x123C route correction, 2.bin answers, probe2 push

Intent: close the remaining §7 open edges while the probe2 fetch watcher waits for
the operator's reboot. Read-only evidence work plus one sanctioned USB-stick write
(probe2 payload); no firmware image, board, or hardware state modified.

Findings and fixes:

- **MemoryPstate 0x123C correction**: it IS serialized by the same 7 modules via
  the standard pattern (`mov edx,0x123c; mov eax,[ebp-0x8]; mov [eax],dx`), 1 site
  each (AmdFabricAriPei 0xDD21, AmdNbioBaseARIPei 0xEB31, AmdNbioGfxARIPei 0xBEF1,
  AmdNbioPcieARIPei 0xF641, AmdNbioSmuV10Pei 0xC841, AmdSocBl5AriPei 0xC581,
  CbsBasePei 0xA7C1). The 20260919 census simply never targeted 0x123C, so the
  doc's "different serialization route" wording was a filter artifact — corrected
  in §7; serializer total = 56 sites across 8 clock-token IDs, all reader-orphans.
- **2.bin APCB answered at the row level** (apcb_detail.py + row diff): group
  skeleton identical to donor except CBSG (44 bytes smaller: inst13 68 vs 72,
  inst15 1768 vs 1808 = 11 rows). Board tail row **(0, 0, 1000)** vs donor
  (0, 1, 1420): the structural override slot exists with **gate byte 0**
  (disabled) and a 1000 value → under donor-chain semantics its boot takes the
  FCLK default (1200 emulated); its own parser/default unverified (see next).
- **2.bin is a different firmware build**: donor SMU body (robin_5, 0x8FEF00,
  262,400 B, cae8617c…) agrees with 2.bin's same-offset region at only 39.3%
  and appears nowhere in the dump (3×64-byte probes). The doc's falsifier (d)
  "all five analyzed images agree on the chain semantics" was WRONG for 2.bin
  and is withdrawn; reframed: the running chain is the flashed donor-derived
  v001 (readback-verified), the profiles share donor bytes outside NVRAM, and
  2.bin's own semantics are unverified/moot.
- **probe2 unblocked and running**: stick enumerated (Phison 28.9G, sdc; archiso
  install stick, vfat = sdc2 23M). Fixed a probe2.sh bug (lsblk PATH is absolute;
  callers prepend /dev/ → /dev//dev/sdc2 mount failure; switched find_stick_dev
  to lsblk NAME). Payload pushed: EFI/BOOT/BOOTX64.EFI (c281d5d8…) + PROBE2.TXT
  onto the auto-mounted sdc2 (replaced archiso's own bootloader; ISO data on
  sdc1 untouched). Fetch watcher started; first window timed out (600 s, board
  never went down); restarted with a fresh window.

Gates: verify_r3b.py PASS (extended: +7 sites 0x123C, 2.bin tail rows, CBSG
sizes, SMU build-difference), verify_r3.py PASS, pytest 83 passed, make test 7 OK.

Writes: `scripts/probe2.sh` (bug fix), `verify_r3b.py` (extension), doc §4a/§6(d)/§7
updates, this log, memory entry. Board/flash/NVRAM untouched; only the USB stick
received the probe payload (sanctioned probe2 plan).
