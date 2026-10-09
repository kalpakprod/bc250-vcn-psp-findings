# BC250 data disks: format sda/sdb as btrfs, mount /cusu + /somnabulist

## Intent (BEFORE, 2026-09-15 ~19:07 PKT, actor: root via SSH as steammachine + sudo -n)

User request (2026-09-15): format sda and sdb, mount as `cusu` and `somnabulist`.
Operator answers to the blocking batch: mapping `sdb -> cusu`, `sda -> somnabulist`;
filesystem `btrfs`; mount points `/cusu` + `/somnabulist` with fstab entries.

Exact targets (re-verified 19:06 PKT, no reboot since first probe, both unmounted):
- `/dev/sda` 953.9G `SSD` serial `AA000000000000002119` (USB Ugreen enclosure), sda1 NTFS, no label -> `somnabulist`
- `/dev/sdb` 894.3G `CUSU C200 960GB` serial `YW2SHJTIWDEB2N5AGNAQ` (USB), sdb2 NTFS label `Photos` -> `cusu`
- Untouched: `nvme0n1` (system + /games + /boot). System mounts use UUID=; /games uses /dev path + nofail.

Pre-destruction evidence (read-only `mount -o ro` + `umount`, both OK):
- sda1 and sdb2 each contain only `System Volume Information`, 4.0K total. No user data to preserve.

Reason: provide two large native-Linux data volumes; NTFS volumes are empty and unmounted.
Expected effect: fresh GPT + one btrfs partition per disk (labels `cusu`, `somnabulist`),
mounted at `/cusu`, `/somnabulist`, owned by `steammachine`, persistent via fstab (UUID, nofail).

Rollback: format is irreversible (old NTFS content unrecoverable by normal means; verified
empty beforehand, so accepted). fstab rollback = restore `/etc/fstab.bak-predisks-20260915`.
No SPI/firmware/bootloader change; system disk untouched.

Planned exact commands (remote login shell is fish: everything wrapped in `bash -c "..."`):
1. Guards + repartition:
   `lsblk -d -n -o NAME,SERIAL` serial match per disk, abort otherwise;
   abort if any /dev/sda* or /dev/sdb* in /proc/mounts;
   `sudo -n wipefs -a /dev/sda /dev/sdb`;
   `sudo -n parted -s /dev/sdX mklabel gpt mkpart primary btrfs 1MiB 100%` (x = a, b);
   `sudo -n partprobe`; `lsblk` readback.
2. `sudo -n mkfs.btrfs -L somnabulist -f /dev/sda1`
   `sudo -n mkfs.btrfs -L cusu -f /dev/sdb1`; `lsblk -o NAME,FSTYPE,LABEL,UUID` readback.
3. `sudo -n mkdir -p /cusu /somnabulist`;
   `sudo -n cp /etc/fstab /etc/fstab.bak-predisks-20260915`;
   append `UUID=<uuid> /cusu btrfs defaults,noatime,compress=zstd:1,nofail 0 0`
   and the somnabulist line; `sudo -n mount -a`;
   `sudo -n chown steammachine:steammachine /cusu /somnabulist`.
4. Verify: `lsblk`, `df -h /cusu /somnabulist`, `findmnt --verify`, `btrfs filesystem show`,
   write test as steammachine (touch + rm).

## Result (AFTER, 2026-09-15 ~19:07 PKT)

PASS. All stages executed exactly as planned, with two deviations noted below.

- Stage 1 (guards + GPT): first attempt aborted at the serial guard with
  `SERIAL_MISMATCH_SDA` — root cause was local shell quoting (`\'` inside a
  single-quoted ssh command mangled the grep pattern), NOT a wrong disk. No write
  occurred (abort preceded wipefs). Retry with quoteless guards:
  `GUARDS_PASS`, `wipefs -a` erased dos (sda) / gpt+PMBR (sdb) signatures,
  fresh GPT + one full-disk `btrfs` partition per disk via parted.
- Stage 2 (mkfs): extra `wipefs -a /dev/sda1 /dev/sdb1` added (deviation 1:
  stale NTFS magic survived on sda1 after repartition; erased before mkfs).
  `mkfs.btrfs -L somnabulist -f /dev/sda1` UUID
  `877aea7f-020e-4778-b9a1-a40efedd31d7`; `mkfs.btrfs -L cusu -f /dev/sdb1`
  UUID `06d38a72-d355-4e48-b958-485f3c72ee8d` (btrfs-progs v7.1, single/DUP).
- Stage 3 (fstab + mount): blkid UUID guards passed (`UUIDS_OK`); fstab backed
  up to `/etc/fstab.bak-predisks-20260915`; two lines appended
  (`UUID=... /cusu` and `/somnabulist`, `btrfs
  defaults,noatime,compress=zstd:1,nofail 0 0`); `mount -a`; both roots
  chowned to `steammachine:steammachine`.
- Verify: `df` shows /cusu 895G (893G avail) and /somnabulist 954G (952G
  avail); `lsblk` confirms labels/UUIDs/mountpoints; `btrfs filesystem show`
  lists both single-device filesystems; user write test (`touch`/`rm`
  `.wtest` as steammachine) OK; `systemctl daemon-reload` run (deviation 2:
  required to clear the findmnt "fstab modified" warning); final
  `findmnt --verify`: 0 parse errors, 0 errors, 1 pre-existing benign warning
  (swapfile source line, untouched).
- System disk nvme0n1 untouched; no reboot performed (persistence via fstab
  + daemon-reload; boot-time mount UNRUN — will be proven at next boot).
- Remaining uncertainty: none for current state; next-boot automount is the
  only unverified claim.
