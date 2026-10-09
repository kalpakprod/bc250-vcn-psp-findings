# Action log: operator takeover + live read-only baseline (OC/1:1:1 track)

Date: 2026-09-21 (Asia/Almaty). Actor: takeover session (Muse, this chat).
Context: operator ordered full takeover of the BC-250 OC/voltage/1:1:1 task
from the Codex goal thread `01a0bba1…` ("перенять на себя со всех агентов") and
demanded other paths toward a practical BIOS overclock + 1:1:1. A STAND DOWN
message was queued to the goal thread (`01a0c55d…`); a prior steering message
(`01a0c554…`) was queued before the takeover order.

## Intent (before execution)

New method class (G6 pivot): stop static ABL/PSP byte-tracing; go empirical.
The board was UP on 2026-09-21 (gaming observed, bore-kernel boot PASS
~22:00). Collect the missing live baseline that every current guide lists as
UNRUN/unknown:

1. Board reachability, hostname, kernel, cmdline, uptime.
2. BIOS identity/date (DMI, read-only), GPU PCI ID (expect `1002:13fe`).
3. Current NVRAM `AmdSetup` + `Setup` var bodies via efivars (read-only) and
   decode the six clock fields (`+0x316/+0x330/+0x36D/+0x6A3/+0x703/+0x704`)
   plus voltage controls — the "current NVRAM unknown" gap.
4. Committed-state clock readback via amdgpu sysfs (`pp_dpm_*`, metrics) as
   before/after deltas only (known software alias, not physical proof).
5. No writes: no NVRAM/ROM/register/flash/voltage action; no reboot; no
   service restarts. Each SSH command has a short timeout; stop on auth
   failure. No blind /24 sweep (memory G6 rule); targets only: `steammachine`
   alias, then last-known `127.0.0.1`.

Expected effect: a dated live-baseline record under
`evidence/runtime/20260921-takeover-live-baseline/` + a grounded operator
runbook for staged native-menu OC (clock-only, no voltage) reusing
`docs/research/2026-09-20-clv-native-menu-1to1-guide.md` T0–T6.

Rollback: none needed (read-only). If the board is unreachable, report
`HARDWARE_BASELINE_NOT_ESTABLISHED` and stop; do not manufacture state.

## Result (2026-09-21 ~23:55+05:00, all read-only, all PASS)

Board UP via `steammachine` alias (first try, no sweep): `cachyos`,
kernel `7.2.6-1.1-cachyos-bore-vcn-bc250`, cmdline `amdgpu.bc250_vcn_mode=1`

- zswap lz4/25, up 2:15, governor `performance`, 12 threads.

* BIOS (DMI): `P3.00`, date `12/09/2021` — NOT CLV 5.00. All CLV-static menu
  paths are leads until verified live on P3.00.
* GPU: `1002:13fe` confirmed. `vcn_v2_0_probe` in journal (mode1, as expected).
* Live `AmdSetup` efivar: 2233 B raw (attrs `07000000` + body 2229 = `0x8B5`,
  same size as W11 ledger). Body SHA-256
  `6f266c3c78a544d73eae5cea465756dd73e343fe16e2725d2300d08ba176d055`.
* Live clock fields: `MCLK=0xFF Auto / UclkDiv1M0=0xFF Auto /
MemPstate=0xFF Auto / FCLK_DPM=0x0F Auto / DFctl=0xFF Auto / DFval=1000`.
  This equals the 2026-09-11 stock profile, NOT the W11/CLV profile.
* Live voltage offsets: VDD `0/0`, GFX `0/0`. No separate `Setup` varstore
  efivar exposed under that GUID. No voltage change active.
* Committed clocks (software alias, deltas only): `mclk 450MHz*`,
  `sclk 2000MHz* (350/2000/2230)`, `fclk 450MHz*`.
* Tools on board: `amdgpu_top` present; `rocm-smi`/`sysbench` absent;
  `gpu_metrics` 4096 B present.

Evidence: `evidence/runtime/20260921-takeover-live-baseline/`
(`AmdSetup-live-efivar.bin` `bdb03494…`, `.b64` `368f3a0e…`,
`clocks-cmdline.txt` `10ce4c2c…`, `SHA256SUMS`).

G7-grade correction vs today's static track: the "current NVRAM unknown" gap
is now closed by live readback, and the live baseline is all-Auto on P3.00 —
every CLV-byte assumption about installed state was wrong for this board.
No board/ROM/NVRAM/register/flash/voltage write occurred. Next: operator
runbook `docs/guides/bc250-p300-111-operator-runbook.md`.

## Resume (2026-09-22 ~00:35+05:00)

Operator clarified: help Root, do not stop it ("я просил ему помогать").
STAND DOWN cancelled via queued resume `01a0c583…` (5 steering rules kept +
pointers to runbook, live baseline, Old Lamer digest). Parallel helper wave
launched from this session: 12 independent research tracks (8coreSteam.rom
audit, FD v2.2 release, software unlock, async-port, CC-port, CU symmetry,
FSR4, cooling, P3.00-live join, NVRAM safety, latency harness, W10 lineage)

- synthesis; children are repo-read-only, network fetch to `/tmp` only.
  Results: `docs/research/2026-09-22-helper-wave-results.md` (parent-verified
  headlines: 8coreSteam.rom = 3.00 lineage `c99cbca1…`, W10 8-core join weak,
  UclkDiv/DFval likely hidden on P3.00, FD R3 PUNSH gap).

## Measure-first pass (2026-09-22 ~01:25+05:00, operator-approved, read-only)

All green, zero hangs/writes. SMN[0x5A870]=0x77 (cores 3,7 masked; matches
unlock-script stock expectation); MCE clean; idle 63C/77-81W, VDDNB 1287mV,
VCN down (mode1); umr+python3+cc present; driver enumerates 40CU; raw
CC_GC_SHADER_ARRAY_CONFIG=0xFFE00000 / GEN0=0x00FC0001 captured, bit mapping
unresolved (no decode invented; decisive test = symmetric CU ladder).
Evidence: `evidence/runtime/20260922-measure-first/` (`8955b7db…`).
Next gates (need operator): T0 screen photo; software-unlock trial approval
(register write, volatile).

## 8-core BIOS flash package staged (2026-09-22 ~01:40+05:00, operator demand)

Operator demands the 8-core unlock in BIOS (not software). Staged, NOT
flashed: `firmware-flash-pkg/20260922-8core-p300-afu/` — `8_cores_steam.rom`
`c99cbca1…` (16 MiB, 3.00 lineage + `Bc250CoreUnlockDxe` `7d22d802…`),
AFU EFI 5.16.01.0109 `a21bab5c…`, UEFI Shell `8204279f…`, `startup.nsh`
(no auto-flash). All hashes independently re-verified this session; AFU
options pinned from binary strings (/O backup, /P /N flash).
Runbook: `docs/guides/bc250-8core-p300-afu-flash-runbook.md` with
preconditions, exact cmdlines, stop/rollback (AFU backup primary,
programmer backstop). Flash gate open: needs P3.00 re-confirm + exact
contract approval text. No board/ROM/NVRAM write performed here.

## G7 CORRECTION (2026-09-22 ~02:10+05:00): programmer-first, not AFU

Operator rebuke sustained: 20-day history (m0-window, campaign-error-audit,
vcn-policy-only, fd-v22-port, flashing.md) shows ALL project writes used
CH347+flashrom with capture-x2/VERIFIED/readback discipline, zero bricks;
AFU never used here. AFU-first runbook revision was method-without-evidence
(video convenience over project record). Runbook rewritten to
programmer-first with: chip-ID gate (W25Q128.V vs SIO1_R trap), 3.3V rule,
pre-write capture x2 as primary recovery, LED-oracle P0, DP-direct display
rule (09-11 miswiring saga), CMOS procedure, rollback A/B.
Own-byte verification added: 8c ROM PSP zone + APCB + boot block identical
to stock P3.00/board stock (kill locus M0-M6 does not apply); diffs = NVRAM
blocks 0-1 + DXE 0xAE0000-0xC2FFFF. Flash gate still open, same needs.

## Root session fully studied (2026-09-22 ~03:00+05:00)

Codex goal thread `01a0bba1…` read in full per operator plea: 11145 rollout
lines, 63 user messages (verbatim), 295 Root messages (6-reader wave, every
message digested), 304 task events (empty payloads), 97 spawns (briefs
encrypted). Waits: 601 total, 398 timeouts (66%). Session arc: 09-19 Stage1
census + token maps → 09-20 ABL1 tracing + voltage negatives + AMIBCP saga
(UNRUN) + H1330/H1750 + df1400-only spec + G-ACT BLOCKED → 09-20 late
baseline ledgers (all gaps) + goal set → 09-21 Gemini quarantine + joins +
clock observability + matrix DRAFT + verdicts. Final Root verdicts (#295–296):
flash NO-GO (no fresh SPI readback), 0x24 request-only GO, 1:1:1 NO-GO,
SoC 1.15V NO-GO. OC wall = proof wall (no applied-freq evidence, actuator
unjoined, no counters), NOT a build blocker for D-REQ1. My 3 queued msgs
(steer/stand-down/resume) landed 19:13–19:48 UTC; Root acked at 19:49.

## D-REQ1 fixed (2026-09-22 ~02:25+05:00): unified 5.00-CLV 8-core firmware

Operator requirement recorded in `specs/2026-09-22-clv500-8core-unified.md`:
5.00-CLV base + in-firmware 8-core unlock + all community patch classes.
Checklist Q1–Q7 open; build not started. Live state check same night: DMI
P3.00, uptime 4:10, NVRAM == `6f266c3c…` — contradicts operator's "5.00 CLV
installed / just flashed" (Q7 unresolved). No board write performed.
