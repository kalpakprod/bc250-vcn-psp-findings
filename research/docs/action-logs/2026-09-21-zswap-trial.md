# Action log: live zswap trial on BC250-01

Date: 2026-09-21. Actor: root. Context:
`docs/research/2026-09-21-bc250-swap-tuning.md` (community: zswap lz4/25%
over fixed zram).

## Intent (before execution)

Trial zswap ON TOP of the live full zram (swapoff impossible live: 7.9G
used, nowhere to go). All writes instantly reversible, no reboot.

Writes (board `steammachine@127.0.0.1`):

1. `/sys/module/zswap/parameters/compressor` = lz4
2. `/sys/module/zswap/parameters/max_pool_percent` = 25
3. `/sys/module/zswap/parameters/enabled` = Y
4. `vm.swappiness` 20 → 60 live + `/etc/sysctl.d/99-bc250-gaming.conf`
   (zswap needs swap flow to function; 20 starves it)

Expected: new swap-outs land in zswap pool (~1.9G cap, self-limiting via
writeback); old pages stay in zram; disk spill slows; no OOM (pool
shrinks under pressure). Watch 3-5 min under game load: pool_total_size,
stored_pages, written_back_pages, reject counters, free, si/so.

Abort (any of): free <50MB sustained, OOM kills, new hard freezes:
`echo N > .../enabled`, swappiness back to 20, record.

## Result (2026-09-21 ~21:00, PASS)

Enabled live 20:53, measured under game load 20:53-20:57 + counters 21:00.
No abort triggered (no OOM, no new freezes reported, free stable).

zswap pool (~7 min live): pool_total_size 367MB of ~1.9G cap (19%),
stored_pages 157079 (~615MB uncompressed, lz4 ratio ~1.68x),
written_back_pages 22960 (~90MB overflow, normal),
pool_limit_hit 0, all reject_* 0 — pool healthy.
RAM: free 124→122MB, available 231→253MB (stable-or-better).
zram eased: mem_used_total 4586→3511MB (pages faulted back under
swappiness 60, fresh evictions now land in zswap first).
vmstat si/so quiet at end of window.

Verdict: zswap lz4/25% absorbing fresh evictions as designed on top of
full zram. No regression. Next: persist via kernel cmdline
(zswap.enabled=1 zswap.compressor=lz4 zswap.max_pool_percent=25) on the
bore-vcn-mode1 limine entry + grow /var/swap/swapfile to 32G.
