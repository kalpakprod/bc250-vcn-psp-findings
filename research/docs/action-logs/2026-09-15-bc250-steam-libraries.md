# BC250: register /cusu + /somnabulist as Steam library folders

## Intent (BEFORE, 2026-09-15 ~19:2x PKT, actor: root via SSH as steammachine)

User request: add the two new disks to Steam. Operator approved stopping the
running Steam client for the edit (blocking-question answer 2026-09-15).

Current state (read-only recon 19:2x PKT):
- Native Steam `/home/OWNER/.local/share/Steam`, client RUNNING (main PID
  observed 1297, deck-mode `steam.sh -srt-logger-opened -steamdeck -steamos3
  -steampal -steamdeck -gamepadui` under gamescope autologin session).
- Live VDF: `steamapps/libraryfolders.vdf` with libs "0" (default, 4 apps) and
  "1" (`/games/SteamLibrary`, 6 apps incl. 3751950). A second
  `config/libraryfolders.vdf` exists (expected legacy mirror; diff at runtime).
- No game process observed (client only); a game guard re-checks before shutdown.
- `/cusu` + `/somnabulist`: btrfs, mounted, empty, owned by steammachine.

Reason: make the 893G + 952G volumes selectable for Steam installs.
Expected effect: VDF gains "2" -> /cusu (label `cusu`) and "3" ->
/somnabulist (label `somnabulist`), each with empty `apps{}`; Steam populates
metadata and per-library `steamapps/libraryfolder.vdf` on next launch.

Rollback: restore `steamapps/libraryfolders.vdf` from
`steamapps/libraryfolders.vdf.bak-20260915`; remove library entries via Steam
GUI (Settings -> Storage) if adopted; `rmdir` the new steamapps dirs if empty.
No game data touched (libs "0"/"1" byte-compared after edit).

Planned exact steps:
1. Guards: abort if a game .exe (excluding steamwebhelper/xalia/crashpad) or
   steam-launch-wrapper/reaper process runs; capture steam.sh cmdline + client
   env (DISPLAY/WAYLAND_DISPLAY/XDG_RUNTIME_DIR/DBUS) for relaunch.
2. `steam -shutdown` (fallback: `bash steam.sh -shutdown`); poll main PID from
   `~/.steam/steam.pid` up to 60 s; abort path if it survives (report, no SIGKILL).
   Confirm gamescope compositor still alive.
3. `mkdir -p /cusu/steamapps /somnabulist/steamapps` (as steammachine);
   backup both VDFs; apply VDF edit via scp'd python3 script
   (`/tmp/steam_add_libs.py`, strict parse + assert existing libs "0"/"1" paths,
   append minimal "2"/"3" entries, re-serialize); remove script; diff vs backup.
4. Relaunch: poll 30 s for session auto-relaunch first; if absent, `setsid`
   relaunch of the captured steam.sh cmdline with captured env; poll for new
   main PID (must differ) up to 60 s.
5. Verify: new client alive; VDF still contains /cusu + /somnabulist with
   entries "0"/"1" unchanged; adoption signal =
   `/cusu/steamapps/libraryfolder.vdf` + `/somnabulist/...` created by Steam.
6. Fallback if relaunch fails: report; machine fully usable over SSH; operator
   reboots or restarts the console session (no auto-reboot without approval).

G3 note: no repo script manages Steam libraries; stopped-client VDF edit is the
standard headless route (GUI alternative declined by operator choice).
G9 criterion: adopted libraries observed in the rewritten VDF after client
restart, old apps intact.

## Method change (BEFORE edit, 2026-09-15 ~19:35 PKT, G6)

`steam -shutdown` cycled the client (1297 -> 44309) but a supervisor relaunched
it within seconds; `systemctl --user stop steam-launcher.service` likewise left a
live client (56167) — no stable stopped window. Suspected relauncher:
plasmalogin-helper autologin supervision (DM = plasmalogin.service,
`display-manager.service` symlink). New method: `sudo systemctl stop
display-manager` (whole console stack down, SSH unaffected) -> edit VDF while
provably down -> `sudo systemctl start display-manager` -> autologin session
boots Steam on the edited VDF. Operator-approved outcome unchanged (brief dark
console, now ~2 min instead of ~30 s). Rollback unchanged (VDF .bak files);
DM start failure would be diagnosed over SSH, worst case operator reboots.

## Result (AFTER, 2026-09-15 ~19:37 PKT)

PASS. Both disks are live Steam libraries; old libraries untouched.

- Edit: `STEAM_DOWN_CONFIRMED` (DM stopped, no client), `EDIT_OK
  libs=['0','1','2','3']`; VDF backups at
  `steamapps/libraryfolders.vdf.bak-20260915` + config mirror; steamapps dirs
  created owned by steammachine; helper script removed after verify.
- Restart: `start display-manager` -> autologin -> new client PID 76802.
  `verify`: libs "0"/"1" paths + full apps dicts byte-equal to backup;
  libs "2" (`/cusu`, label cusu) + "3" (`/somnabulist`) present, 0 apps.
- Adoption (hardware-observed): Steam rewrote the VDF at 19:35:28, enriching
  both entries with generated contentids + correct totalsizes (960195723264,
  1024208142336). Stronger: Steam placed app 1174180 (downloading/) onto
  /somnabulist at 19:35-19:36 (appmanifest + common/ dirs) — operator-side
  install to the new library observed live. No libraryfolder.vdf written;
  evidently not required for adoption.
- G7 correction: two bogus "client still up" verdicts were pgrep -f
  self-matches (patterns `ubuntu12_32/steam ` and `.exe` matched the wrapper
  cmdlines / `libexec`). Rule added: `memory/instincts/pgrep-self-match.yaml`.
  Also corrected: `steam -shutdown` and user-unit stop DO cycle the client;
  the relaunch is plasmalogin-supervised; DM stop/start is the deterministic
  window. `config/libraryfolders.vdf` was byte-identical to the canonical
  steamapps one and was edited identically.
- Remaining uncertainty: none for registration; per-game install behavior is
  operator-side from here.
