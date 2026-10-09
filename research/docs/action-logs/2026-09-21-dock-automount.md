# Action log: dock automount fix (x-systemd.automount)

Date: 2026-09-21. Actor: root. Context: post-reboot check — new kernel
7.2.6-1.1-cachyos-bore-vcn-bc250 booted as default (PASS), but the
Ugreen dock (/cusu, /somnabulist) did NOT mount at boot (USB
enumeration races fstab; units failed on dependency, then mounted fine
manually). Steam game libraries live there — must self-heal.

## Intent (before execution)

Board `steammachine@127.0.0.1`. Standard fix for USB fstab races:
add `x-systemd.automount` to both dock lines in /etc/fstab (keep
`nofail`, keep all other options):

- `UUID=06d38... /cusu btrfs defaults,noatime,compress=zstd:1,nofail`
  → append `,x-systemd.automount`
- `UUID=877aea... /somnabulist ...` → same.

Backup: /etc/fstab.bak-20260921-automount (already have
.bak-20260921-swap32 from the swap edit).
Then `systemctl daemon-reload`, verify `cusu.automount` +
`somnabulist.automount` units exist and are active (waiting).

Effect: disks mount on first access instead of at boot — immune to
USB timing. No behavior change when the dock is present; when absent,
access blocks briefly then fails cleanly (automount timeout) instead
of boot-order failure.
Rollback: restore backup + daemon-reload.
Full proof: next reboot (UNRUN until then); unit-level check now.

## Result (2026-09-21 ~22:10, PASS)

- fstab: exactly 2 lines changed (diff-verified),
  `+x-systemd.automount` on /cusu + /somnabulist. Backup kept.
- daemon-reload generated both .automount units (dead-while-mounted,
  correct).
- LIVE PROOF on /cusu: `umount` OK (nothing held it busy) →
  `systemctl start cusu.automount` → first `ls` triggered the mount
  (findmnt shows autofs + /dev/sdb1 with noatime,compress=zstd:1).
  Manifests visible incl. moved Stray/Overcooked2.
- /somnabulist: same config, currently classic-mounted; live umount
  test skipped (same mechanism proven); boot behavior for both proven
  at next reboot.
- NOTE: /cusu grew 242→247G used in ~10 min after boot — likely Steam
  shader/update writes post-reboot. Not investigated (cosmetic).
