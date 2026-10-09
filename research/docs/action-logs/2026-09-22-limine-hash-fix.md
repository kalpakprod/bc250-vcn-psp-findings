# Action log: fix stale blake2b hashes in Limine bore-vcn mode entries

Date: 2026-09-22. Actor: root (this session). Trigger: board reboot into
default entry `bore-vcn-mode1` (7.2.6-1.2) ended in a Limine panic:
blake2b hash mismatch + stack trace. Board recovered on fallback
7.2.0-1.1-cachyos-bc250 by the operator.

## Root cause (measured, not guessed)

Limine verifies every `path:`/`module_path:` against the `#<blake2b>`
suffix in limine.conf before loading. pkgrel2 install (01:32) replaced
vmlinuz+initramfs in the shared dir `linux-cachyos-bore-vcn-bc250/` and
rehashed only the BASE entry. The mode0/mode1/mode2 entries (same files,
extra cmdline) kept pkgrel1 hashes:

- claimed initramfs `6bc3a199...0bb0b1302` vs file `b8e51170...0c6991655`
- claimed vmlinuz `36ef7816...4982490a5d` vs file `87e3b839...5d669b`
- stale `6bc3a199...` == b2sum of the 1.1-era history copy
  `limine_history/initramfs_sha256_177d31b2...` (proof of staleness)

Base entry (line 632) has correct hashes; mode0/1/2 (lines 641-667) do
not. btrfs device stats are all-zero: disk is innocent. pstore empty
(panic is Limine-side, before Linux).

## Intent (before execution)

Target: `/boot/limine.conf` top-level mode0/mode1/mode2 blocks ONLY
(lines 641-667). Replace the two stale `#hash` values with the current
file b2sums (6 substitutions). Non-bore `vcn-bc250` entries checked
separately; snapshot-submenu entries left untouched (their mode
sub-entries are stale the same way — documented, not booted).

Procedure: `cp limine.conf limine.conf.bak-20260922-bootfix`, then
`sed -i '641,667 s/<stale>/<current>/'` x2, then re-read the three
blocks + programmatic b2sum compare. Rollback: restore the .bak file.
Fallback entry (7.2.0) untouched throughout; worst case = mode1 still
panics exactly as now. Reboot test by operator afterwards.

## Result

Executed 2026-09-22 ~02:2x+05: BACKUP_OK
(`/boot/limine.conf.bak-20260922-bootfix`), 6 lines changed (3 entries
x vmlinuz+initramfs). Programmatic verify: mode0/mode1/mode2 all MATCH
live file b2sums. Non-bore vcn entries verified healthy (untouched).
Fallback 7.2.0 untouched. Reboot test: operator (mode1 default).
Lesson: every future kernel pkg install MUST re-verify mode-entry
hashes — limine-entry-tool rehashes only the base entry.
Reboot test 02:20+05 PASSED: board booted 7.2.6-1.2 mode1, full new
cmdline active, zswap Y/lz4/25 live, Vulkan 26.2.3 (mesa unpin
effective).
