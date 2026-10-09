# VCN START — SAFE PROCEDURE (BC-250)

WHY: on 2026-08-29 a full gasket replay read VCN-MMIO while the domain was still power-gated -> **bus wedge**,
board dead (ping 100%, SSH No-route) until **cold power-cycle**. Root cause = read-MMIO-before-enable.
This package makes the run SAFE + WATCHED so it cannot wedge the same way.

## Safe order (WRITE-FIRST)
1. `--verify`      — read-only dom6/slot state. SAFEST first contact. (no writes)
2. `--no-fire`     — unlock + install + repoint; **disarms on exit** (handler slot->0, thunk wiped).
3. `fire`          — install + fire Q3 msg **0x61** -> firmware enables domain-6 (VCN) clock. (the domain ENABLE point)
4. `--direct-load` — stage navi10_vcn in VRAM + ring-test. Reads MMIO *after* the domain is enabled.
   Success marker: `mmUVD_SCRATCH9 0xCAFEDEAD -> 0xDEADBEEF` in directload.log.

## Run (on board, one command)
```
ssh steammachine@127.0.0.1 'bash ~/vcn_unlock/vcn_safe_run.sh'
# optional second terminal: watch for wedge
ssh steammachine@127.0.0.1 'bash ~/vcn_unlock/vcn_watch.sh'
```
Logs: `~/vcn_unlock/vcn_safe_run/{verify,ofire,fire,directload}.log main.log heartbeat.log watch.log`.
Watchdog: if heartbeat stops advancing >90s -> WEDGE (process stuck). Since these runs happen on the live OS,
first check the OS still answers SSH; if the whole board is dead -> cold power-cycle (recovery is documented).

## Wedge playbook (if something wedges)
- If board OS still SSH-reachable: `~/.venv`-safe; just `~/vcn_unlock/vcn_safe_run.sh` again from --verify.
- If board DEAD (ping 100%, SSH no-route): **manual power-cycle** (cmdline has `nowatchdog`, no auto-reboot).
  enable_vcn disarms on normal exit; a hard-wedged process may need SIGTERM/power-cycle.

## Rollback / reversibility
- Power-cycle restores stock PSP-applied gasket at boot. No flash writes.
- limine already trimmed (stock default=fallback, BOOTX64.EFI fallback). `rebc250-rollback.sh` for limine.

Files: vcn_safe_run.sh (runner) · vcn_watch.sh (wedge detector) · vcn_deploy.sh (scp to board).
Sources: enable_vcn.py, bc250-smu-unlock/ (unlock.py Q2 0x23, bc250_smu/).
