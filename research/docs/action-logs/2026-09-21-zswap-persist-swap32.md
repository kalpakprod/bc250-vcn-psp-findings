# Action log: persist zswap cmdline + second 16G swapfile

Date: 2026-09-21. Actor: root. Context: zswap live trial PASS
(`docs/action-logs/2026-09-21-zswap-trial.md`); user asked to persist
("допиши") and reach >=32G disk swap.

## Intent (before execution)

Board `steammachine@127.0.0.1`.

A. zswap cmdline persist for default entry
`CachyOS/linux-cachyos-bore-vcn-bc250-mode1` (CONFIG_ZSWAP=y built-in,
default zstd — override needed):

- Source of truth: append
  ` zswap.enabled=1 zswap.compressor=lz4 zswap.max_pool_percent=25`
  to `KERNEL_CMDLINE[linux-cachyos-bore-vcn-bc250-mode1]` in
  `/etc/limine-entry-tool.d/91-bore-vcn-probe.conf`.
- Immediate effect: same append to the live (non-snapshot) mode1
  `cmdline:` in `/boot/limine.conf` (entries are auto-generated;
  snippet preserves it across regenerations).
- Backups: `*.bak-20260921-zswap` of both files. mode0/mode2 and the
  fallback entry untouched (minimal change).
- Rollback: restore backups; no boot until user reboots anyway.
- Takes effect at next boot (user's reboot window for kernel test).

B. Second 16G swapfile (16G existing + 16G new = 32G disk swap).
`/` is 98% full (2.4G free) — no room there. Placement:
`/games/swapfile2` on /dev/nvme0n1p1, SAME internal SSD, ext4, 233G
free (satisfies "internal SSD only"; avoids btrfs nocow handling).

- `fallocate -l 16G`, `chmod 600`, `mkswap`, `swapon` (live, no
  swapoff of the existing file — zero downtime, zero OOM risk).
- fstab append (backup first):
  `/games/swapfile2 none swap defaults,nofail 0 0`
  (`/games` already `nofail` and ordered before swap lines.)
- Rollback: `swapoff /games/swapfile2`, remove fstab line, delete file.

## Result (2026-09-21 ~21:15, PASS)

A. zswap cmdline persisted for default bore-vcn-mode1 entry:

- Snippet `91-bore-vcn-probe.conf`: diff confirms exactly 1 line
  changed (mode1 KERNEL_CMDLINE += zswap.enabled=1,
  zswap.compressor=lz4, zswap.max_pool_percent=25). A first sed attempt
  wrote an empty expansion (nested-quote bug) and was corrected via
  python; backup `*.bak-20260921-zswap` kept.
- `/boot/limine.conf`: exactly 1 live mode1 cmdline patched
  (non-snapshot; snapshot entries and fallback untouched). Backup kept.
- Takes effect at next boot.

B. Disk swap now 32G: `/games/swapfile2` 16G created (fallocate, 600,
mkswap UUID 0407c7da-...), SWAPON_OK, live in /proc/swaps
(16G file + 8G zram + 16G file2), fstab line appended with nofail
(backup `/etc/fstab.bak-20260921-swap32`). /games: 217G free left.
`/` untouched (98% full — cleanup is a separate task, not started).
