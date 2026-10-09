# Action log: remove CPU isolation from boot cmdline + reboot

Date: 2026-09-22. Actor: root (this session). Operator order: remove the
pinning/isolation mess, reboot with a sane config. Game saved by operator.

## Intent (before execution)

Board `steammachine@127.0.0.1` on 7.2.6-1.2 mode1. Problem: cmdline
carries `isolcpus=8-11 nohz_full=8-11 rcu_nocbs=8-11`, which idles 2 of 6
physical cores for normal scheduling and breaks load balancing for any
task allowed there (observed live: 44 game threads piled on cpu8, FPS
collapse). No project evidence ever justified it (local docs: zero
mentions). Manual taskset games on top made it worse.

Target: `/boot/limine.conf`, TOP-LEVEL cmdline lines only (2-space
indent; snapshot-submenu lines untouched). Remove the three tokens
`isolcpus=8-11`, `nohz_full=8-11`, `rcu_nocbs=8-11` wherever present.
Keep everything else byte-identical (zswap, ppfeaturemask, iommu,
cstates, vcn_mode, hashes).

Procedure: backup to `limine.conf.bak-20260922-deisolate`, python edit
(top-level cmdlines only), diff must show ONLY cmdline token removals,
then `sudo reboot` (operator-authorized). Expected: board returns on
7.2.6-1.2 mode1, `/sys/devices/system/cpu/isolated` EMPTY, all 12 CPUs
balanced. Rollback: restore .bak + reboot (fallback 7.2.0 untouched).

## Result

Executed 02:5x+05: backup OK, line-657-only diff (3 tokens removed),
top-level clean. Reboot OK first try: board on 7.2.6-1.2 mode1,
`/sys/devices/system/cpu/isolated` EMPTY, all 12 CPUs in balancing.
Durable rule from operator rebuke:
`memory/instincts/no-unexplained-tuning.yaml` — no perf tweak without
mechanism + evidence + revert.
