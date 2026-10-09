# Action log: UMA 6G via memcfg (BIOS menu did not stick)

Date: 2026-09-22. Actor: root. Operator set 6G in BIOS menu; reboot
showed vram_total still 512M (536870912), RAM 14G.

## Intent (before execution)

CMOS readback shows UMA_SIZE=0512 — firmware reads memcfg's CMOS
block (0x90-0xAB + checksum), which the BIOS menu option did not
modify. Same approved value (6G/6144), other writer: run
`./bc250memcfg UMA_SIZE 6144`, read back CMOS, reboot, verify
vram_total=6442450944 + gamescope alive + game test.
Rollback: memcfg UMA_SIZE 512 (or 8192) + reboot.

## Result

PASS. After memcfg write + reboot: vram_total=6442450944 (6G),
RAM 9.4G, gamescope alive (2 procs), uptime fresh. Operator's BIOS
menu change to 6G demonstrably did not touch CMOS (readback stayed
0512 after his reboot); memcfg write was the applier. Note: my
reboot+verify command was cancelled mid-flight, but the reboot had
already been issued; state re-verified clean afterwards.

## Game test 05:24+ (AC Black Flag Resynced, AppID 3751950)

- Launch Completed, reaper+proton+wineserver alive, wineserver ~12%
  CPU; prefix initializing (Fonts writes). No game window yet:
  gamescope focus=steam, 0 surfaces, GPU 0%, no flip errors, no new
  coredumps — 6G holds so far, no 512-style crash.
- Fossilize shader-cache mkdir errors on /cusu path are
  container-scoped (host mkdir works) and non-fatal by design.
- Remote screenshot: FAILED x3 (grim: no screencopy protocol;
  kmsgrab: VRAM BO unmappable EPERM; uinput F12: EINVAL). Operator
  asked to press F12 for a Steam-side capture.

## Ubisoft activation error (05:25/05:35, launcher_log.txt)

- On-screen "Unable to start game / cannot be activated" =
  launcher WARNING PlayGame.cpp:2089 "Unable to activate game".
- Cause lines: JobHttp.cpp:605 "Http status code is no content" for
  public-ubiservices.ubi.com playsession?productId=66088 (HTTP 204,
  no session issued) + StoreProductsGet "timed out".
- Board side verified healthy: clock synced (NTP yes, RTC match),
  DNS resolves, public-ubiservices answers 404 in 0.94s,
  connect.ubisoft.com 301 in 0.72s.
- Verdict: backend/account-side refusal (no session for product),
  NOT board/network/Proton/VRAM. Fix is user-side: Ubisoft Connect
  login, Steam-account link, library entitlement, server status,
  retry later.

## "Worked yesterday" verification (operator challenge)

- CONFIRMED: Sep 21 sessions ran 30+ min (start + 5.5-min updates,
  clean delete). "Unable to activate" first-ever occurrence today
  05:23/05:25/05:35 (3x total in log spanning Aug 26-Sep 22).
- Same Ubisoft profile id across all history (no account switch).
  Launcher binaries untouched since Sep 3 (only logs fresh).
  This boot: only known DAL boot noise, no GPU/OOM/MCE errors, no
  new coredumps; game exits cleanly in 4-5s (Steam "process
  removed", no crash).
- Correlation admitted: last board change (memcfg 6G + reboot
  ~05:18) immediately precedes first failure (05:23). No causal
  path: split cannot alter server HTTP 204; store endpoint (board-
  independent) times out simultaneously. Decisive test offered:
  retry launch unchanged now (transient backend?) before any
  revert; yesterday's split was 8G per earlier sysfs read.

## Goal: activation root cause (operator-set)

- Window narrowed: last good heartbeat today 03:37:31, first
  failure 05:23:54. Retry 05:42 same signature (3rd identical).
- Net: all ubi endpoints <1.2s (API 404-alive, CDNs alive);
  public IP 92.46.179.141 ZEN_CLEAN; clock synced.
- Launcher dir: only file changed in window = options .save;
  no cache dir; ownership files absent at depth<=2; login token
  works (sessions start OK). "Launch attributes" warning new
  today (4x, likely post-failure noise). Web threads = SEO spam.
- Pending discriminator: PROTON_LOG=1 (user sets launch option,
  launches; root reads ~/steam-3751950.log) — wine crash vs
  clean DRM exit. 8G revert held as fallback if log implicates
  board side.
- PROTON_LOG via GE tool-dir user_settings.py WORKED (fresh
  2.6MB log 06:03): NO wine crash (only handled faults), NO D3D
  device created (count 0), game exits cleanly pre-render. DRM
  refusal confirmed at app layer. Broken user launch options
  live in cmdline (duplicated command) but postdate first
  failures (05:23/05:25/05:35/05:42 had clean options).
- Gap 03:37-05:23: sessions STARTED ok 03:46/03:47/04:04/04:45
  (died by board crashes before validation?) — DRM refusal may
  predate 05:23, masked by display crashes. 6G correlation possibly
  coincidental (6G unmasked it). Alternate hypothesis: Ubisoft
  throttling after 10+ session starts in 2.5h (204 + store
  timeouts fit). Store timeout chronic since Aug (not a signal).
- Intent (8G causation test): memcfg UMA_SIZE 8192 + readback +
  reboot + verify vram_total + NO launch until user cleans
  launch options in UI (avoid confound + throttle deepening).
  Rollback: memcfg 6144 + reboot.
- 8G revert DONE 06:07: CMOS UMA_SIZE=8192, vram_total=8589934592,
  RAM 7.5G, Steam up. No test launch yet (awaiting UI options
  cleanup to avoid confound; also doubles as throttle cooldown).
- 06:12: chattr +i held clean LaunchOptions across reboot (Steam
  healthy). 06:23 CLI test launch on 8G: session started, NO
  refusal (Unable count stays 9), D3D12 device created, GPU 100%,
  focus=3751950, heartbeat updated 06:29:23, flip errors 0.
  GAME RESTORED TO WORKING STATE.
- Verdict: activation refusals (GNM Code 10 + HTTP 204, 9x
  05:23-06:02) were Ubisoft-side transient (backend incident or
  throttle after 18 rapid starts); board config exonerated —
  PROTON_LOG showed clean pre-D3D exit, no wine crash. 6G-vs-8G
  role unresolved (non-monotonic: 512@03:37 OK, 6G failed,
  8G OK) — 6G retest deferred to avoid re-breaking. Hygiene
  pending: chattr -i after user re-types same string in UI
  (push clean value to Cloud); keep user_settings.py until
  stability confirmed, then remove.
- Operator order: restore 6G, everything must work on 6G.
  Intent: memcfg UMA_SIZE 6144 + readback + reboot + verify
  vram_total=6442450944 + SINGLE CLI test launch + verify
  (no refusal + D3D + heartbeat). Rollback: memcfg 8192.
  chattr +i and user_settings.py stay (still needed).
- 6G retest: FAIL 2/2 (06:38, 06:40, same 2-3s signature, count
  now 11). Scoreboard: 6G fails 11/11 (05:23-06:40, 3 boots);
  8G works (Sep 21 + 06:23); 00:00-03:37 sessions OK on UNKNOWN
  split. Split-correlated unless backend incident window
  05:23-06:40 with one lucky 06:23 success (p~3% at 90% fail).
  Launches PAUSED (throttle-deepening risk). Pending: operator
  states WHEN 512 was set (before/after 03:37?) — decides
  between split-causal vs transient.
- Operator order: try 7G (bisect: 7G-works => 6G-specific;
  7G-fails => not-8G issue). Intent: memcfg UMA_SIZE 7168 +
  readback + reboot + verify vram_total=7516192768 + SINGLE
  CLI test launch + read outcome. Rollback: memcfg 8192.
- New goal (operator): full self-serve — fix everything, restore
  game to working state. GNM Code 10 is 1:1 with refusals, first
  ever 05:23:54. Aug-30 had 9 starts/hour without refusal —
  throttle hypothesis weakened but alive (18 starts today).
- Intent (self-serve options fix): write LaunchOptions
  `PROTON_NO_NTSYNC=1 %command%` to localconfig.vdf + chattr +i
  (beats Cloud revert) + reboot + verify value persisted and
  Steam healthy + SINGLE CLI test launch on 8G + read outcome.
  Rollback: chattr -i + restore value + reboot. user_settings.py
  (PROTON_LOG) stays for instrumentation; remove after.
- 05:52: `steam -applaunch 3751950` via SSH WORKS (ActionID 5,
  same 204 signature, 5th identical). Self-serve launch loop open.
- Operator: "can't you write it yourself?" — yes, with reboot:
  running Steam holds localconfig in memory, file edit needs
  Steam restart to apply. Intent: backup localconfig.vdf, exact
  replace LaunchOptions to
  `PROTON_NO_NTSYNC=1 PROTON_LOG=1 %command%`, verify, reboot,
  verify Steam back, CLI-launch, read fresh proton log.
  Rollback: restore localconfig backup + reboot (or UI edit).
- 7G result (read by new session 06:47, read-only): vram_total=
  7516192768 confirmed. 06:45:36 session started, 06:45:38
  "Unable to activate game", process ended — same 2-3s signature.
  Refusal count now 12. d3d12_device_create count=1 in
  ~/steam-3751950.log (not yet checked whether that line is from
  this run or a stale log). Scoreboard: 6G 11/11 fail, 7G 1/1 fail,
  8G 1/1 OK today (06:23). Board left at 7G, no further launches.

## Root-cause analysis 06:50-07:05 (new session, read-only on board)

- G7 correction: HTTP 204 is NOT the refusal cause. In every failed
  run the order is: session started -> game process never connects
  to launcher API -> "GNM error Code 10" + "Unable to activate game"
  - "Game process ended" (same second) -> THEN 204 on the session
    delete/update call. The 204 is a consequence, not the trigger.
- 8G success 06:23 vs 7G fail 06:45: identical launcher sequence up
  to session start; success shows "Game with process id N connected"
  at +5s, fail shows GNM Code 10 at +2s. Proton log (7G run): game
  process 05d8 loads dbdata.dll + uplay_aux_r164.dll at 172.56-172.57
  and ends there; no wine crash, no D3D device of its own.
- Launcher "RAM: N MB" vs outcome, all 27 launches Sep 21-22:
  7652/7651 (8G) OK, 15199 (512M) OK, 9655 (6G) FAIL 11/11,
  8647 (7G) FAIL 1/1. 100% separation by RAM value.
- 6G itself is not incompatible: Sep 15-16, RAM 9659 MB, 3/3 runs
  started and connected.
- First-seen RAM values: 15199 new at 03:45, 7651 new at 04:04,
  9655 new at 05:23, 8647 new at 06:45. Values first seen before
  05:23 work; values first seen at/after 05:23 fail.
- Hypothesis (inferred, not verified): per-hardware license/
  activation in the game; every new RAM size is a new hardware
  fingerprint; several fingerprint changes in ~2h hit an activation
  limit, so new configs are refused (GNM Code 10) while already
  activated configs still run. Which DRM, the meaning of Code 10 and
  the window length are unknown.
- Falsifying test: no new split sizes; one launch on the target split
  after a cooldown (>=24h after 05:23). Fails again => hypothesis wrong.

## 08:40 Intent: restore 8G to play (operator: "fix my game")

- Target: steammachine@127.0.0.1, CMOS UMA_SIZE 7168 -> 8192 via
  `sudo ~/bc250_memcfg/bc250memcfg UMA_SIZE 8192`, readback, reboot,
  verify vram_total=8589934592, one CLI launch `steam -applaunch 3751950`,
  read launcher log. Reason: 8G RAM value (7651/7652) is the only split
  that activated today (06:23 OK). One variable: split only; LaunchOptions
  and localconfig immutable flag left as at 06:23.
- Rollback: memcfg UMA_SIZE 7168 (or 6144) + reboot.
- 08:40 result: memcfg 7168->8192 readback OK; reboot; vram_total=8589934592.
- 08:43 launch (steam -applaunch 3751950): launcher RAM 7651 MB (same value
  as the 06:23 success), session started 08:43:53, GNM Code 10 +
  "Unable to activate game" 08:43:56. FAIL. Refusal count 13.
- G7 correction: the "new RAM value = new fingerprint, old values still
  activate" hypothesis is FALSIFIED. Identical RAM value, LaunchOptions,
  "Test/dev args file present" line and command line as the 06:23 success;
  outcome differs. Refusal is now config-independent on this side.
  Remaining explanation (inferred): activation refused upstream (account-
  or hardware-level), not caused by the local split. No local change
  tested so far discriminates it.
- Fan noise 08:44: CPU Tctl 80C during launcher start, curve raised blower
  to ~3150 rpm; falling after. Idle 75 W at pinned 2000 MHz sclk is the
  standing baseline since 2026-09-20 (telemetry), not new.
- Left: UMA 8192, launcher processes stopped, no further launches.

## 11:0x systematic debug of activation refusal (read-only)

- 11:01 launch: same refusal (GNM Code 10 at 11:01:03). Game proc 04d8 loads
  dbdata.dll + uplay_aux_r164.dll, opens UplayService pipe 11:01:01, exits.
  06:23 success instead shows ApiProcessConnection "Game ... connected".
- Excluded (observed): network/servers (ubiservices 404/301 in <1s, clock
  synced); CPU count (16 threads already at 06:11 boot, ananicy topology);
  kernel cmdline, packages (none since 06:30), game files, prefix files
  (unchanged since 06:24); Steam session (LogOn OK 06:19 and 10:58); Steam
  launch task chain identical; ownership (appmanifest LastOwner = logged-in
  account, not family-borrowed); UMA (8G at 06:23 and 08:43/11:01).
- Remaining variable: the Ubisoft activation answer itself. Web search for
  "GNM error Code 10" found no specific documentation.
- GPU OC test T1 (single writer 2200@1112-1118 mV, 60 s idle) passed; auto
  revert fired 11:03:36 -> 2000@999.

## 11:3x activation debug continued

- Relogin (11:27:31) did NOT help: 11:29:15 GNM Code 10 again. Excluded: region/IP (KZ Kazakhtelecom, same as Sep 3), pending game update (Fully Installed, TargetBuildID 0, only shader-cache updates).
- Test T2 (intent): disable ACBlackFlagFix mod by renaming version.dll -> version.dll.bc250-off (ASI loader; mod patches exe memory 1 s before activation). One launch. Rollback: rename back.
- T2 result: mod disabled, 11:31:36 GNM Code 10 again -> mod EXCLUDED. version.dll restored.
- 11:4x prefix backup search (operator goal "restore the prefix"): NO activated
  copy exists. Board: all fs searched (/, /home [@home not in snapper],
  /cusu, /somnabulist, /games); only /cusu/steamapps-archived/compatdata/
  3751950.failed-fresh-20260830-003806 (files 2026-08-30 00:34-00:37, never
  activated). kukuruza-pc (.74): no Steam games, no Ubisoft Connect. Laptop:
  librarycache only. DRM circumvention refused (scope). Prepared
  ~/.local/bin/ac4-backup-prefix.sh (rsync to /cusu/backups) for the first
  successful launch; drafted Ubisoft support request for a lockout reset.

## UMA 8G -> 6G for Spider-Man — INTENT (operator "да", ~17:5x PKT)

Evidence: Spider-Man.exe RSS 2.1G + 1.17G swapped, 54 major faults/s,
GTT 1.27G, VRAM 5.8/8G used, system 7.5G. Target: memcfg UMA_SIZE 6144,
CMOS readback, reboot, verify vram_total=6G. Denuvo/AC4 risk accepted by
operator. Rollback: `bc250memcfg UMA_SIZE 8192` + reboot.
RESULT 17:51 PKT: CMOS UMA_SIZE=6144 readback, reboot: vram_total=6144 MiB,
MemTotal 9.4 GiB, swap 0. Boot-time OC verified in the same boot:
bc250-smu-oc "Applying 4000 MHz @ Scale -35", governor TestMode 2200/1015,
40 CU, CPU 3992 MHz.
17:56 vm.swappiness 150 -> 10 (/etc/sysctl.d/99-bc250-swappiness.conf): disk swapfile + zswap, game pages swapped with 4 GB available. Rollback: delete file, sysctl vm.swappiness=150.
19:43 FurMark-start hang reproduced at GPU 2000@960 (not OC). Suspect UMA 6G (17:51) vs MastaG Mesa. Test: memcfg UMA 8192 + reboot + FurMark start at 2200@1015.
