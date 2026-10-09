# Action log: ppfeaturemask OD bit for bore-vcn-mode1

Date: 2026-09-22. Actor: root. Context: operator chose the clean OC
route. All pp_od_clk_voltage writes rejected (Invalid argument):
OD bit 0x4000 is OFF in current mask 0xfff7bfff. Fix: OR the bit
-> 0xfff7ffff via cmdline (takes effect at next reboot; zero impact
on the running A/B session).

## Intent (before execution)

Board `steammachine@127.0.0.1`. Same two-place pattern as zswap:

1. Append ` amdgpu.ppfeaturemask=0xfff7ffff` to
   KERNEL_CMDLINE[linux-cachyos-bore-vcn-bc250-mode1] in
   /etc/limine-entry-tool.d/91-bore-vcn-probe.conf
   (backup .bak-20260922-ppmask).
2. Same append to the live (non-snapshot) mode1 cmdline in
   /boot/limine.conf (backup .bak-20260922-ppmask).
3. Verify: grep both; diff shows exactly 1 line each; fallback +
   snapshots untouched. Rollback: restore backups (effective next
   boot); live system unaffected either way.

## Result (2026-09-22 ~00:15, PASS)

- Snippet: exactly 1 line (diff 2c2). limine.conf: exactly 1 live
  mode1 cmdline (grep-confirmed). Backups kept. Fallback +
  snapshots untouched. Takes effect at next boot; running A/B
  session unaffected (mask is read at amdgpu init).

## Part 2 (2026-09-22): isolation + iommu + cstates (operator answers)

Topology: sibling pairs (0,1)(2,3)(4,5)(6,7)(8,9)(10,11); core_ids
0,1,2,4,5,6 (core 3 fused off); CCX0 = cpus 0-5, CCX1 = cpus 6-11.
Isolate last 2 cores of CCX1 (cores 5,6 = cpus 8-11, one L3 slice):
`isolcpus=8-11 nohz_full=8-11 rcu_nocbs=8-11` + `iommu=pt` +
`processor.max_cstate=1`. Game pinned via Steam launch option
`taskset -c 8-11 %command%` (operator applies at next launch).
UKSM: no operator order (answered neither) — NOT in pkgrel3 scope.
Same two-place pattern + backups; verify by grep; effect next boot.
Rollback: restore backups. IRQ affinity left unmanaged (follow-up
only if 1% lows still noisy after A/B).
