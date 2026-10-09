# Action log: GPU 2200 MHz via cyan-skillfish-governor-smu (max voltage first)

Date: 2026-09-22. Actor: root. Operator order: max 2200 at MAX voltage; if it
fails at max voltage, voltage is not the limit. Operator picks the test game.

## Intent (before execution)

- Target: steammachine@127.0.0.1, /etc/cyan-skillfish-governor-smu/config.toml
  (governor 0.4.12, set-method smu). Kernel 7.2.6-1.2 (0007: 350-2230).
- Change: frequency-range min 2000->500, max 2000->2200; safe-point 2200 1050->1129 mV,
  2230 1085->1129 mV (1129 = OD_RANGE VDDC max, firmware abs-max). Enable + start
  cyan-skillfish-governor-smu.service.
- Expected: idle clock drops toward 500, load ramps to 2200 @1129 mV.
- Stop: temp >85C, artifacts/crash, FPS below 2000 MHz baseline.
- Rollback: `systemctl disable --now cyan-skillfish-governor-smu`, restore
  config.toml.bak.20260922-oc2200 (clock returns to stock).

## Result

- `enable --now` executed; board hard-hung within seconds (display lost, ssh
  timeout, ping 100% loss). Unit is ENABLED on disk. Recovery: operator power
  cycle + one-shot `systemd.mask=cyan-skillfish-governor-smu.service` at Limine;
  then disable unit + restore config backup + read `journalctl -b -1`.
- 10:58 recovered after operator power cycle: ssh loop ran `disable` + `stop`
  - config restore at uptime 0 min. Now: governor disabled/inactive, config
    2000/2000 restored, bc250-gpu-fixed + bc250-gpu-watchdog + telemetry active.
- Journal -b -1 (observed): governor start 10:54:53.227 triggered
  Conflicts= stop of bc250-gpu-fixed (ExecStop `bc250-gpu-fixed.sh fallback`
  wrote "1500 MHz @ 906 mV -> 2000 MHz @ 956 mV" at 10:54:53.814) and of
  bc250-gpu-watchdog, while the governor began SMU writes; 8x amdgpu
  "Unsupported clock type" at .313/.815; last journal line 10:54:54.256.
- Inferred cause (not proven): two SMU writers at once (fixed.sh fallback +
  governor, telemetry polling too) -> SMU/GPU hang. Matches guide note on SMU
  concurrency crashes. Not yet separated from "2200@1129 itself".

## Debug phase 1-3 (systematic-debugging)

- Board tools (2026-08-21/24): bc250-gpu-set.py (Bc250Smu force_gfx_vid/freq,
  use_flock=True, readback check, bounds 350-2230/700-1129), driven by
  bc250-gpu-fixed.service from /etc/bc250-gpu-fixed.conf (2000@1013, fallback
  2000@960); watchdog rollback at 100C; bc250-smu-oc (CPU 4000 MHz, scale -28,
  same flock). Governor (Rust) does not take that flock.
- Hypothesis H1: hang = unserialized concurrent SMU writes (governor vs
  fixed.sh fallback), not 2200@1129 itself.
- Test T1 (intent): pre-arm `systemd-run --on-active=180 --unit=bc250-oc-revert
/usr/local/libexec/bc250-gpu-fixed.sh apply`; then single writer
  `bc250-gpu-set.py 2200 1129` at idle; sample pp_od/temp/power 60 s.
  Nothing persistent (conf unchanged; reboot = 2000@1013).
  H1 falsified if the board hangs with a single serialized writer.

## Switch to governor, serialized — INTENT (2026-09-22, operator order)

Operator: turn off bc250-gpu-fixed, turn on the governor. Order fixes the
earlier hang cause (two concurrent SMU writers): `disable --now`
bc250-gpu-fixed first, wait until inactive and no `bc250-gpu-*` /
`bc250-smu*` process remains, only then `enable --now`
cyan-skillfish-governor-smu. Config unchanged (range 2000-2000).
Rollback: `disable --now` governor, then `enable --now` bc250-gpu-fixed.

## Switch to governor — RESULT (06:49:49Z, PASS)

bc250-gpu-fixed disabled+inactive; no other SMU writer found (first two
checks aborted on a self-matching pgrep pattern, nothing written to SMU by
them). Governor enabled+active, "SMU communication verified", range
2000..=2000. Board alive 15 s after start. Idle readback 1500 MHz @ 893-906 mV
(level left by the fixed service's ExecStop fallback), governor has not
written a new level at idle yet. Unit is enabled for boot.

## Governor 2200 @ 1129 mV — INTENT (operator: "ставь 2200")

Target /etc/cyan-skillfish-governor-smu/config.toml: backup to
config.toml.bak.<ts>-pre2200; frequency-range max 2000 -> 2200 (min stays
2000); safe-point 2200 voltage 1050 -> 1129, safe-point 2230 1085 -> 1129
(keep the curve monotonic). Restart governor only (single SMU writer,
bc250-gpu-fixed stays disabled). Rollback: restore backup + restart.

## Governor 2200 — RESULT (FAIL: board reset)

- Config edited (diff: max 2000->2200, V2200 1050->1129, V2230 1085->1129).
- `systemctl restart` at 12:02:03.49 PKT ("Stopping Cyan Skillfish GPU
  Governor..."); last journal line of boot -1 is 12:02:04.47; new boot
  12:02:33. Reset, not hang. Journal does not show whether the new
  instance ever started: the failure is at the stop/start transition,
  not proven to be the 2200 level itself.
- Also seen: governor ran 11:49-12:02 but never moved the clock off 1500
  MHz (telemetry gfreq 1500 throughout).
- After reboot: bc250-gpu-fixed came back ACTIVE although disabled —
  it is pulled in by bc250-telemetry and bc250-gpu-watchdog (reverse deps);
  governor lost the Conflicts= race and stayed inactive.
- Recovery: config restored from config.toml.bak.20260922-120203-pre2200
  (max 2000); governor `disable`d so the next boot cannot race two SMU
  writers. Board: 2000 MHz @ 999 mV via bc250-gpu-fixed.
- Hypothesis (untested): telemetry polls SMU metrics every 1 s; if it does
  not take the Bc250Smu flock, it collides with the governor on stop/start.

## Governor, restart-free — INTENT (operator: "настрой губернатор")

Source read (filippor/cyan-skillfish-governor smu @aaed425, v0.4.12 on board):

- start: check_test_message, set_gpu_max_temperature(80), unforce freq+vid;
  stop: unforce freq+vid. Both crashes (10:54 start, 12:02 restart) sit on
  these transitions. Board tools' flock covers a single 4-byte config op,
  not the 0xB8/0xBC index+data pair -> two userspace clients can interleave.
- change_freq only fires when the target changes; range 2000..2000 never
  changes -> explains 1500 MHz (SMU default after unforce) for 13 min.
- D-Bus Range.Max / set_range change limits live, no restart.
  Steps: mask bc250-gpu-fixed (telemetry Wants / watchdog Requires pull it
  at boot; watchdog stops with it, governor keeps its own 85 C throttle);
  stop gpu-fixed (its fallback write runs while nothing else writes); verify
  no SMU client; config: min 2000 max 2000 on disk + safe-points 2200/2230 at
  1129; enable --now governor (same start that survived at 11:49); then
  D-Bus Range.Max=2200 live. Never restart the governor live.
  Rollback: disable --now governor; unmask + enable --now gpu-fixed.

## Reset to upstream governor scheme — INTENT (operator: "сбрось разгон, сделай нормально")

Partial state before: gpu-fixed stopped (fallback write ran), mask failed
(unit file lives in /etc), governor not started.

- Retire home-made GPU units: stop bc250-gpu-watchdog; move
  /etc/systemd/system/bc250-gpu-{fixed,watchdog}.service to
  /etc/systemd/bc250-oc-retired/; daemon-reload.
- Governor config = package default-config.toml (upstream @aaed425) with
  range 1000..2200 and safe-points extended 2050/980 2100/1000 2125/1020
  2150/1035 2200/1129. Old config kept as config.toml.bak.<ts>-prereset.
- Per upstream README: manual `systemctl start`, load test, enable only after.
  Rollback: move units back, daemon-reload, restore config backup.

## Reset to upstream scheme — RESULT (07:09:11Z start, board alive)

Units bc250-gpu-{fixed,watchdog} moved to /etc/systemd/bc250-oc-retired/,
both inactive; no other GPU writer. Config = upstream default + 1000..2200,
2200@1129. Governor started manually (NOT enabled, per upstream README),
"SMU communication verified", range 1000..=2200, metrics fix on. Idle
readback 1400 MHz @ 874 mV, 61 C. Load test pending; enable after it passes.

## RDR2 crash 12:11:55 + constant max voltage — INTENT

Crash under RDR2 (vsync off, 60 fps cap removed). Last telemetry of boot -1:
gfxclk 1100 MHz, gvolt 806 mV, 57 C, 69 W -> died at LOW clock/voltage on a
load step, not at 2200. Operator order: voltage max, constant. Config: every
safe-point voltage -> 1129 (range stays 1000..2200); start governor once.
RESULT: 13/13 safe-points at 1129; governor active (manual start, not
enabled); readback 1000 MHz @ 1.12 V, 53 C, 80 W. Game test pending.

## Governor per MastaG docs, 2200@1129 top, pollers off — INTENT

Sources: MastaG/linux-cachyos-bc250 README @cf86483 "cyan-skillfish-governor
recommendations" (set-method kernel, method kernel, fix-metrics/fix-freq
false, temp-read sysfs on >=0.4.13); katzzero guide 06 (min >=1000, curve);
reddit r/BC250Gaming 1w89ggy (SMU governor hard freeze = weak WGP at low V).
Operator order: top point 2200 @ 1129 mV, fit the rest, disable pollers.
Curve: 1000/800 1500/900 2000/1013 2100/1060 2150/1095 2200/1129, range
1000..2200. Pollers disabled: bc250-telemetry (2 s), bc250-metrics (1 s),
bc250-pwrwatch (0.2 s). Kept: bc250-fan (needed), dpwatch (DP status only).
Script: scratchpad apply-gov.sh (evidence -> pollers off -> config -> start).
Governor started manually; enable at boot only after the RDR2 test.

## Governor per MastaG docs — RESULT (07:25:45Z)

- Crash #2 evidence (boot -1, 12:18:30): 1000 MHz @ 1125 mV, 58 C, 79 W.
  Both governor crashes happened at 1000-1100 MHz on a load step, at 806 mV
  and at 1125 mV -> voltage is not the trigger; low clock + smu method is.
- Pollers telemetry/metrics/pwrwatch disabled+inactive.
- Governor 0.4.12 (0.4.13 not in sync repos; temp-read stays drm).
- Journal: "GPU usage method: kernel set method: kernel", range 1000..=2200.
- min raised 1000 -> 1500 (config + live D-Bus SetRange 1500 2200, no
  restart): readback 1500 MHz @ 893 mV, 48 C, 70 W. Governor enabled at boot.
- Pending: RDR2 load test with uncapped fps.

## Strictly per docs — INTENT (operator: no own deviations, update governor)

- Upgrade cyan-skillfish-governor-smu 0.4.12 -> 0.4.13-1 from AUR (paru),
  as MastaG README says for temp-read.
- Config: MastaG block verbatim (fix-metrics/fix-freq false, method kernel,
  temp-read "sysfs", set-method kernel); rest = package default except the
  operator's orders: max 2200, top point 2200@1129. min back to default 1000.
  Safe-points = katzzero guide "Recommended Config" (1000/700 1500/900
  2000/1000 2100/1025 2175/1050) + 2200/1129.
- Restart the service once after editing (per both READMEs); verify
  "temperature read: sysfs" in the journal.

## Strictly per docs — RESULT (08:40:52Z)

- Crash #3 at 12:29:27 PKT: during `paru` pacman transaction (rust makedep)
  while RDR2 was loading; pollers were off -> no telemetry, cause unproven.
  Stale db.lck removed (no pacman proc, `pacman -Dk` clean, rust 0 altered).
- Governor 0.4.13-1 built on the laptop (AUR PKGBUILD). First build used
  the laptop's target-cpu=native (6649 zmm/AVX-512 insns) -> SIGILL on Zen2,
  crash-looped, stopped. Rebuilt with -march/target-cpu=znver2: 0 zmm.
- Config = 0.4.13 default + MastaG block verbatim + max 2200 + guide
  safe-points + 2200/1129. Journal: "GPU usage method: kernel set method:
  kernel temperature read: sysfs". Idle 1000 MHz @ 699 mV, 49 C.
- Governor enabled; pollers disabled. Pending: RDR2 test.

## Crash #4 + operator curve +50 mV (applied under running game, operator order)

- Crash #4 13:51:50 PKT: game 2668510 launching, governor at 1000 MHz
  ~700 mV, 49 W (DPWATCH HB) -> same pattern: low clock/low V + load step.
- Operator order: +50 mV per point: 1000/850 1500/950 2000/1050 2100/1075
  2175/1100 2200/1129 (cap = OD_RANGE VDDC 1129). Rest of config unchanged.

## Crash #5 + community two-point curve (09:18:14Z)

- Crash #5: governor start under running game 2668510 with +50 curve.
- 2000 MHz after boot 14:15 was set by the governor in its 6 s before my
  stop (only writer; bc250-gpu-fixed unit absent).
- Community (TG dump ids 131508, 154858, 157135/157165, 157361): per-chip
  safe-points; more points = more chances of an under-volted point; hang =
  load drop -> lower clock -> too little V. Practice: few points, min 1000,
  two states, tune from max down. Discord extracts (/tmp/discord-track-*):
  min >=1000, governor black screens on link training (V4).
- CPU OC 4000 MHz scale -28 unchanged since 2026-08-30 (not touched).
- Applied: MastaG block + two safe-points 1000/950, 2200/1129 (anything
  > 1000 gets 1129 by the next-higher-point rule). Enabled + active,
  > readback 1000 MHz @ 943 mV, 56 C, 49 W.

## Crash #6 -> fixed clock, operator choice O1: 2150 @ 1129 — INTENT

Governor disabled. New unit bc250-gpu-clock (oneshot, kernel OD write
"vc 0 2150 1129" + "c", Conflicts= governor), conf /etc/bc250-gpu-clock.conf.
Rollback: disable unit, reboot (stock 1500).
RESULT 14:23 PKT: governor inactive+disabled; bc250-gpu-clock enabled+active;
readback 2150 MHz @ 1118 mV (asked 1129, SMU rounds), 61 C, ~112 W idle.
Game test pending.
2050@1040 via gpu-fixed (operator order, 14:52)
2050@1090 (operator: +50 mV, 14:53)
crash #9 14:53:30 at 2050@1090 (147 W, no game), parity error. Now booted stock 7.2.6-1.206; gpu-fixed back to 2000@1013 (14:55)

## RESET to MastaG canon — INTENT (operator order ~15:20 PKT)

Disable+retire: bc250-smu-oc (CPU 4000/-28), bc250-gpu-fixed, bc250-cu-layout,
bc250-cu-live-manager, bc250-cpu-performance, bc250-telemetry, bc250-pwrwatch,
bc250-dpwatch, bc250-userlog, bc250-netconsole. Keep bc250-fan; enable
bc250-metrics (throttle status). 40 CU via MastaG modprobe drop-in
bc250_cc_write_mode=3 + mkinitcpio -P. default_entry -> stock
linux-cachyos-bc250 7.2.6-1.206. Governor 0.4.13 per MastaG README, points
1000/800 1500/900 2000/960 2050/1030, max 2050, hard cap 1050 (operator).
Reboot by operator. Rollback: units in /etc/systemd/bc250-oc-retired/,
limine.conf.bak-20260922-reset, drop-in removable.

## OC ladder harness — INTENT (goal: CPU ~4 GHz + GPU 2200, 40 CU)

/usr/local/libexec/oc-step.sh <mhz> <mv> <min> [cpu]: governor TestMode
SetTestMode (README), furmark-vk 1080p + stress-ng cpu16 combined, 5 s
samples (sclk, mV, temps, W, throttle bits from bc250-metrics) to
/tmp/oc-<f>-<v>.log, kmsg marks. Method per community: FurMark/OCCT-style
combined load, ladder from known-good up, ~10 min per step, 30+ min final.
Ladder: GPU at stock CPU 2000/960 -> 2100/1000 -> 2200/1015 -> +15 mV
(cap 1050). Then CPU via bc250-detect 3800/1150 -> 3900/1200 -> 4000/1250
with GPU at best point, combined. Reboot into stock 7.2.6-1.206 + 40 CU.

## OC ladder results so far (stock 7.2.6-1.206, 40 CU, CPU 3200 stock)

GPU combined (furmark-vk 1080p + stress-ng 16) 10 min each, all PASS:
2000/960 (66C, 158W), 2100/1000 (65C, 121W), 2200/1015 (65C, 175W).
bc250-cpu-performance restored (detect needs performance governor).
bc250-detect: -v1250 -> 3600 (throttle at 3700), -v1275 -> 3500 (Tctl 89C
vs t 90), -v1175 -> 3600 scale -13 (throttle 3700, Tctl 83C).
Operator: t_max 100, fan 85% manual (bc250-fan stopped, pwm2=217) for tests.

## Combined + CPU undervolt results (stock 7.2.6-1.206, 40 CU, fan 100%)

- Combined 10 min CPU 4000/-28 + GPU 2200@1015: PASS (GPU 71C, Tctl 97C, 207W).
- Fan fixed 100% persistent: bc250-fan-max.service (Conflicts bc250-fan).
- CPU 4000 undervolt, stress-ng --verify 120 s + 7z b: -20 -30 -35 -40 -45
  all 0 failures, 7z 72.8-73.3k (no clock stretching), Tctl 101/97/93/88/85.
  -50 (tool min): HARD HANG, next boot "parity error" = same signature as
  game crashes -> parity error = voltage-margin instability class.
- Chosen: -35 (10 steps margin). Final combined 30 min running.

## FINAL (synthetic) — CPU 4000/-35 + GPU 2200@1015, 40 CU: 30 min PASS 17:22

Combined furmark-vk + stress-ng 16, 30 min: GPU 69C, Tctl 92C, 204 W peak.
Persisted as tested: bc250-smu-oc restored with 4000/-35/100; governor
drop-in 20-fixed-2200.conf ExecStartPost SetTestMode 2200 1015; fan-max,
cpu-performance, metrics enabled; default kernel stock 7.2.6-1.206.
Not proven: real-game stability (community: synthetic can pass while games
crash after hours) -> operator RDR2 1-2 h is the acceptance test.
17:56 fan back to auto: bc250-fan-max disabled, bc250-fan (curve) enabled (operator: too loud).
18:01 crash 17:59:28 on texture switch in Spider-Man: parity error, throttle=0x0, gfx 73C, p_gfx 55W. All today's parity crashes share CPU 4000 + undervolt. CPU scale -35 -> -20 (live + /etc/bc250-smu-oc.conf). GPU 2200/1015 unchanged.
18:03 operator: revert, keep as was -> CPU scale back to -35 (live + conf).
19:34 transient test 19:24-19:34: INVALID. Started while a Steam game process was running (check printed GAME_RUNNING but did not abort: missing exit). FurMark segfaulted at start -> only CPU pulses ran (80 W, GPU 60 C). No crash.
19:54 bisect: disabled bc250-smu-oc + governor 20-fixed-2200 dropin, reboot to stock runtime, then FurMark start test.

## FurMark-start hang: bisect result (19:36-19:57)

Instant hard hang (<1 s after furmark launch, parity error) reproduced in
every variant: CPU -35 / -28, GPU 2200@1015 / 2200@1040 / 2000@960, UMA 6G / 8G,
MastaG Mesa / stock cachyos Mesa, 1080p / 640x480, --no-gpumon, and fully
stock runtime (no CPU OC, no GPU pin, governor at 1000 MHz). vkcube runs fine.
FurMark only starts on gamescope Xwayland after `xrdb` sets Xft.dpi (it
segfaulted otherwise since 16:52). Conclusion: current FurMark launch path is
itself fatal and independent of the OC -> all post-16:52 "test" results void.
Valid evidence remains 15:15-16:09 runs. Restored operator config (smu-oc
4000/-35 enabled, governor 2200/1015 dropin). Mesa now stock cachyos 26.2.3-1,
UMA 8G (FSR4 needs MastaG Mesa; 6G reverted during bisect).
20:19 combo glmark2-4k+cpu pulses at 4000/-35 + 2200/1015: HANG at ~7 min (20:18), parity error, GPU V droop 987-1006, Tctl 88.8. Next: 2200/1040 same CPU.
20:36 combo 15 min PASS: CPU 3800/-35 + GPU 2200/1015 (590 pulses, 156 W peak, 72 C). 2200/1040 + 4000/-35 hung <1 min (more V = faster hang -> shared current/power limit). Next: 3900/-35.
20:51 combo 15 min PASS 3900/-35 + 2200/1015. Persisted /etc/bc250-smu-oc.conf frequency 3900 (was 4000). Final 30 min running.

## FINAL — CPU 3900/-35 + GPU 2200@1015, 40 CU: 30 min combined PASS (21:22)

Load: glmark2 terrain 3840x2160 offscreen (GPU 65-90% busy) + stress-ng cpu16
pulsed 0.5 s on/off, 1179 pulses, glmark2 alive throughout, peak 195 W,
GPU 70-71 C, GPU V droop to 968 mV, no hang. Ladder at GPU 2200/1015:
4000 hung @7 min, 3900 PASS 15+30 min, 3800 PASS 15 min. More GPU V (1040)
hung faster -> shared current/power limit, not V deficit. Persisted:
/etc/bc250-smu-oc.conf 3900/-35/100 (enabled), governor dropin SetTestMode
2200 1015. Stock cachyos Mesa, UMA 8G at this point.
