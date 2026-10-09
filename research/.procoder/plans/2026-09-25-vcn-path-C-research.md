# План C: существует ли программный путь к VCN на BC-250 (mirage-free)

Date: 2026-09-25. Operator chose direction C after the SMU-path was proven a
misattribution (see 2026-09-25-second-gate-passthrough.md). Rule: verify every
claim against a firmware STRING or primary message-table name — never a label.
Goal of C: reach a DEFINITIVE go/no-go on "is there ANY software path to power/
un-isolate the VCN island", not endless chasing.

## Verified ground truth (do not re-litigate)
- VCN 2.0.3 present, harvest=0 (live ip_discovery). Not fused.
- SMU 11.8: NO VCN message (primary msg table). 0x0115F600 = GFX deep-sleep DFLL
  (msg 0x19/0x1A), NOT VCN. FUN_0001fc50 = GFX bring-up step, NOT PowerUpVcn.
- route-B/v003b = dead (targets GFX). Do not flash v003b.
- PSP: type-13 VCN fw -> ITEM_NOT_FOUND (rejected). type-64 -> no-op.
- Transports on BC-250 SMU: Q3 0x2A read (safe for 0x0115F/0x0116D/0x01159/
  0x0005A/0x0000C; WEDGES for 0x0900Cxxx, 0x0220FExx, VCN reg-file 0x0007Exxx);
  Q3 0x28/0x29 SMU-local + SMN write; Q3 0x98 arbitrary-SMN-write (core-unlock
  primitive, survives warm reboot); call() arbitrary SMU fn (patched rpc).
- The real VCN island power/isolation is in the PSP/RSMU domain: 0x0900c004 =
  RSMU_COLD_RESETB_VCN (community-written via fw-window, NOT via 0x2A read).

## The real question, decomposed

C1 (static, safe) — REFERENCE: what actually powers the VCN island on a WORKING
   VCN 2.0.x part? Decompile the Navi10/Renoir SMU PowerUpVcn handler (the
   feature-gated PPSMC_MSG_PowerUpVcn, SMU_FEATURE_VCN_PG_BIT) and list EXACTLY
   which SMN registers / PGFSM / isolation bits it drives, before the OS driver.
   Sources: renoir/navi10 SMU fw (community amd_smu_reverse_engineering), the
   daveconde enable_vcn.py notes. Output: the canonical power/iso register set.

C2 (static, safe) — MAP to BC-250: for each C1 register, find its BC-250 SMN
   address (PSP/RSMU/NBIO domain) and its REACHABILITY class (0x2A-read-safe /
   wedge / 0x98-write-only / call-only). Explicitly separate "in the SMU clock
   domain" (mirage class) from "in the PSP/RSMU/NBIO power domain" (real).

C3 (static, safe) — PSP ROLE: does the BC-250 PSP run ANY VCN power sequencing
   at boot (RSMU cold-reset, rail, isolation), and is it triggerable/observable
   from the reachable transports? Check the PSP bootloader/ABL VCN steps.
   Distinguish signed-only (unreachable) from a runtime-triggerable path.

C4 (decision) — GO/NO-GO:
   - If the island power/iso is ONLY behind a signed PSP path or an unreachable
     transport -> NO software path exists. Honest exit (this is the correct,
     evidence-based "triple deadlock", re-derived without the mirage).
   - If a reachable write primitive (0x98 / call()) can drive the C1 register set
     -> design ONE minimal, guarded hardware experiment (operator-gated, at
     button, cold-cycle recovery). Success = VCN reg-file responds non-FF.

## Guards / discipline
- Every SMN-block->IP claim must cite a firmware STRING or primary msg-table name.
- No 0x2A reads of wedge families (0x0900Cxxx/0x0220/VCN reg-file). Use 0x98/call.
- Hardware only after C1-C3 static, operator-authorized, at the button.
- Accept a NO-GO as a valid, valuable result (saves years).

## Status
Plan written. Next execution step = C1 (static decompile of the real VCN
power handler on a working part). Board healthy; SMU wedged from variant-A probe
(cold cycle before any further hardware).

## C1 DONE — reference established (static, primary)
- Working part (renoir, kernel-verified 2026-08-25, daveconde README:502/567):
  VCN island opened by PPSMC_MSG_PowerUpVcn, FEATURE-GATED behind
  SMU_FEATURE_VCN_PG_BIT. Handler drives PGFSM (mmUVD_PGFSM_CONFIG/STATUS
  0x1F800/0x1F804) + island power/iso.
- BC-250: smu_v11_8_ppsmc.h has NO VCN message; 147-handler Q3 table dump has
  NO VCN handler; 2026-09-23-smu-0x3c: NO feature bit triggers VCN power (the
  0x21->0x249DC->0x23B14 lead RETRACTED). => the working mechanism is
  FUNDAMENTALLY ABSENT on BC-250, not merely unreachable.

## Remaining genuinely-open leads (thin) before a NO-GO
- L-a: undocumented gated Q3 group flags=0x206 (msgs 0x71/0x72/0xA7/0xA8,
  accessible post-unlock) — never examined; NO evidence they are VCN (could be
  anything). Static decode of their handlers = cheap next step.
- L-b (C3): PSP/ABL boot-time VCN sequencing — does the on-die PSP run any RSMU
  cold-reset / island power at boot that a reachable primitive could trigger?
  0x0900c004 = RSMU_COLD_RESETB_VCN lives here; reads wedge, write via 0x98/fw-
  window only. Signed-only path = unreachable = NO-GO.

## Honest lean
Evidence leans hard to NO-GO: the SMU lacks the VCN power mechanism entirely, and
the real island power sits in the PSP/RSMU domain that wedges every reachable read
and is likely signed-only. L-a and L-b are the only cheap things left to close
before a defensible "no software path exists" verdict.

## L-a CLOSED (static, primary)
Gated Q3 group handlers: 0x71->0x284B4, 0x72->0x284D4, 0xA7->0x283A8, 0xA8->0x283FC.
robin_5 table labels 0xA7/0xA8 = "cpu_related"; 0x71/0x72 adjacent same secure band.
ZERO VCN signal (no 0x1F800 PGFSM / 0x0900c RSMU reference). => not a VCN path.

## L-b CLOSED (by existing evidence)
PSP-side VCN sequencing is signature-gated by the on-die ROM (consolidated-state
2026-09-19: verifier in ROM; VCN fw rejected). The one reachable write,
0x0900c004 (RSMU_COLD_RESETB_VCN via 0x98/fw-window), was community-written and did
NOT wake VCN — because the SMU-side power that must follow does not exist on BC-250.

## FINAL VERDICT — direction C: NO-GO (no software path to enable VCN on BC-250)
Every candidate closed with primary evidence:
1. SMU VCN power mechanism: FUNDAMENTALLY ABSENT (no message, no feature bit, no
   handler in the 147-handler table). Working part uses feature-gated PowerUpVcn.
2. "route-B / 0x0115F600 / FUN_0001fc50" = MISATTRIBUTED GFX deep-sleep (mirage).
3. Gated Q3 group 0x71/0x72/0xA7/0xA8 = CPU/secure, not VCN.
4. PSP/RSMU island power = signature-gated (on-die ROM); reachable RSMU cold-reset
   write alone does not wake VCN.
5. Direct VCN MMIO/reg-file = wedges every transport (0x2A, host, kernel).
CALIBRATION: not every one of 147 handlers was byte-decompiled; residual
low-probability space = a fully hand-decompiled handler census. But the pattern is
consistent and every examined lead is closed.
CONCLUSION: VCN is present (harvest=0) but there is NO demonstrated software path to
power/un-isolate the island on BC-250. This re-derives the "triple deadlock" WITHOUT
the mirages that made prior sessions/community believe it solvable. Enabling VCN, if
possible at all, needs a hardware/glitch/signed-key path outside software scope.

## CENSUS (alias "2" continuation, 2026-09-25) — closed against the PRIMARY message table

Source: evidence/board-home-20260924/.../amd_smu_reverse_engineering/tables/
known_messages_smu_fw_robin_5.txt (the community RE repo's authoritative
147-handler mailbox table — the same repo that built the message map).

- FULL-TABLE VCN GREP: zero matches for vcn/uvd/vce/jpeg/video/mmhub/codec/
  encode/decode across ALL 4 queues. No VCN message exists at any msgid.
- 0x1A = PPSMC_MSG_SetMaxDeepSleepDfllGfxDiv (handler 0x2B634); 0x19 =
  SetMinDeepSleepGfxclkFreq; 0x1B = PPSMC_MSG_StartTelemetryReporting
  (handler 0x270DC). => the writeup's "0x1A=SetVcnClock / 0x1B=PowerUpVcn"
  (docs/research/2026-09-23-bc250-platform-complete-writeup.md:108-109) is
  FABRICATED on BOTH counts. Confirms and extends the SetVcnClock finding.
- 68 named PPSMC entries: ALL CPU/GFX/DF/telemetry/table-transfer. Full list
  in this session's grep. Zero multimedia.
- 144 novel unnamed handlers (q?_0x* aliases) remain un-named, but: (a) the
  dispatcher FUN_0002A184 was Unicorn-emulated end-to-end (8,865 insns) with
  no VCN path found; (b) the community RE repo itself has ZERO vcn/pgfsm/
  0x1f800 references anywhere; (c) an independent 16 MB ROM scan (daveconde
  README) finds NO register writes into VCN's 0x024xxxxx fabric frame.

## THIRD-PARTY CORROBORATION (daveconde-bc250-vcn-enable README, on-hw 2026-08-25)
- With clocks programmed + enables ON + dom6 gates released, VCN POWER_STATUS
  and the WHOLE register file (incl. static UVD_VERSION) read UNIFORM ALL-ONES,
  board does NOT hang => island CLAMPED AT THE ROOT, not per-cluster gating.
- SMU mem64 window masks target to 20 bits (0x01100000 + arg&0xFFFFF) — can
  NEVER express VCN's 0x024xxxxx fabric address; the 0x1F8xx/0x0111F8xx
  families are measured hard wedges. No CPU-side transport reaches VCN power
  without hanging while the island is dead.
- IP_DISCOVERY: VCN present, v2.0.3, harvest=0, encode+decode enabled
  (revision&0xC0 == 0). "power-gated, not absent" — matches our harvest=0.
- No VCN_INFO table in this BIOS; upstream Linux knows cyan-skillfish and
  DELIBERATELY skips VCN. A third independent party hit the identical wall.

## CENSUS VERDICT: NO-GO holds, now triangulated by 3 independent sources
1. This session's primary decode (0x0115F600=GFX deep-sleep, not VCN).
2. The community RE message table (no VCN message among 147 handlers).
3. daveconde's on-hardware measurement (island clamped at root; no reachable
   transport; no ROM write into the VCN fabric frame).
There is NO software path to power/un-isolate VCN on BC-250. Enabling it needs
a hardware/glitch/signed-key mechanism outside software scope. v003b/v003 must
NOT be flashed (built on the fabricated 0x1A/0x1B mailbox contract).
