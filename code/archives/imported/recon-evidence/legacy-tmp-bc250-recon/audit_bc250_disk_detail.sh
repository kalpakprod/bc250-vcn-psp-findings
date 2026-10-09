#!/usr/bin/env bash
set -u

section() { printf '\n===== %s =====\n' "$1"; }

section '.LOCAL SHARE DEPTH 2'
du -x -h -d 2 /home/OWNER/.local/share 2>/dev/null | sort -h | tail -50

section 'RPCS3 CONFIG DEPTH 3'
du -x -h -d 3 /home/OWNER/.config/rpcs3 2>/dev/null | sort -h | tail -50

section 'SHADPS4 TREES'
du -x -h -d 2 /home/OWNER/src/shadps4 /home/OWNER/src/shadps4-bc250-clean 2>/dev/null | sort -h | tail -50
for dir in /home/OWNER/src/shadps4 /home/OWNER/src/shadps4-bc250-clean; do
  printf '%s branch=' "$dir"
  git -C "$dir" branch --show-current 2>/dev/null || true
  git -C "$dir" status --short 2>/dev/null | head -20 || true
done

section 'SNAPSHOT EXCLUSIVE/SHARED'
for dir in /.snapshots/*/snapshot /@home-golden-20260816; do
  [[ -e "$dir" ]] || continue
  printf '%s\n' "$dir"
  sudo btrfs filesystem du -s "$dir" 2>/dev/null || true
done

section 'BTRFS QGROUPS'
sudo btrfs qgroup show -reF / 2>/dev/null | tail -40 || true

section 'BUILD SUBDIRS'
sudo du -x -h -d 2 /home/OWNER/linux-cachyos-bc250/build/linux-cachyos-rc 2>/dev/null | sort -h | tail -30

section 'CURRENT BUILD'
systemctl --user status bc250-vcn-build --no-pager -l 2>/dev/null | head -40 || true
