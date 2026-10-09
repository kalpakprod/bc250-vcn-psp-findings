# Corpus synthesis: what the BC-250 project has established (2026-09-22)

Actor: root (no workers; the W1-W7 fan-out was stopped unread). Sources read
directly: memory/project-state.md (full), memory/open-questions.md,
memory/decisions.md outline D1-D38, docs/research/2026-09-17-campaign-error-audit.md,
2026-09-21-workflow-reset.md, 2026-09-22-{discord,uma512,helper-wave}-synthesis,
2026-09-22 action-log verdicts. Evidence class: synthesis of recorded findings;
no new measurement. Chat-sourced items are participant reports (trust class 6).

## F1. Closed routes (evidence-backed negatives)

- VCN power grant: every software-reachable route closed (2026-09-12 verdict,
  D3-A/D3-B2; loop#2 C3: needs SMU-side PowerUpVcn, NULL on BC250, or a PSP
  release block). Community (Nov 2025, Mar 2026) independently hit the same
  PSP-signing wall. No working recipe exists anywhere.
- 4700S base: C0A PSP region is the kill locus (M0..M6 silent; M6 = native +
  C0A PSP only, still silent).
- Whole-FV CLV graft af531026: P0 fail (single green blink, no LAN/video).
- pp_od `s`-path live OC: SMU rejects (EINVAL, `Invalid sclk`). 3000 MHz is
  above the firmware wall; community 40CU wall ~2200.
- Naive NVRAM memclk pin (T1): firmware reverts it (OQ-T1d).
- UMA 512 + gamescope + AAA game: flip ENOMEM -> SIGABRT (matches drm/amd#3704).
- Manual CPU pinning: lowered FPS.

## F2. Working / proven

- Native 3.00 lineage boots; recovery chain intact; all writes readback-verified.
- Kernel cmdline work (sclk ceiling, ppfeaturemask, limine hash fix): PASS.
- UMA 8G + ttm 15G: game runs. sg_display=-1 boots clean.
- Memory OC via host SMU governor (1500->2230 MHz) reported proven earlier.

## F3. Unused levers already in hand (highest value, lowest risk)

- Live chip already carries MeiMeiDXEv3-XL with SMU/Core unlock present but
  Disabled in NVRAM (factory mask 0x77 = 6 cores). Enable = Setup visit, no flash.
- Volatile software core unlock (`bc250-core-unlock`, SMN 0x5A870 via SMU msg 0x98),
  cleared on cold boot.
- GPU OC route = userspace governor (filippor/cyan-skillfish-governor); `vc`-path
  pp_od retest on 7.2.6 is the one open OC question.
- Drivers-only CLV candidate 0968a70c: built, never flashed.

## F4. Process diagnosis (why progress was slow)

- No boot-observation channel ever populated (J5 UART, TPMS1 LPC/POST, J2 JTAG);
  every silent flash was a 1-bit coin flip (audit M-A).
- Base choice not mapped to goals before flashing (S1); bisection from wrong end (M-B).
- G6 breaker stated but not enforced; worker claims entered decisions unverified.
- Months spent on branches the community had already closed with cause.
- Large uncommitted state and parallel worker waves with stale receipts.

## F5. Game issue (separate track)

- 6G/7G failures separate 100% by launcher-reported RAM value; the earlier
  "backend 204" verdict was withdrawn (G7). Leading hypothesis (inferred):
  per-hardware activation limit after repeated split changes. Working
  configs: 8G, 512M-era. Not a firmware problem.

## Recommended order

1. Setup visit: enable MeiMei SMU + Core unlock on the live image (no flash);
   measure cores, MCE, temps.
2. `vc`-path pp_od read-first retest; otherwise governor-based OC.
3. Populate one observation channel (UART J5 or POST) before any further flash.
4. Any flash only after fresh full-SPI dump + exact approval; drivers-only
   0968a70c is the only reasoned candidate.
5. Stop VCN work unless a new PSP-side fact appears.
