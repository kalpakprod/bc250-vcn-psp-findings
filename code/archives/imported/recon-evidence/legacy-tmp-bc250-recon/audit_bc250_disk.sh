#!/usr/bin/env bash
set -u

section() { printf '\n===== %s =====\n' "$1"; }

section 'FILESYSTEM'
df -hT / /home /tmp
sudo btrfs filesystem usage -T / 2>/dev/null || true

section 'TOP LEVEL'
sudo du -x -h -d 1 / 2>/dev/null | sort -h

section 'HOME DEPTH 2'
du -x -h -d 2 /home/OWNER 2>/dev/null | sort -h | tail -60

section 'VAR DEPTH 2'
sudo du -x -h -d 2 /var 2>/dev/null | sort -h | tail -50

section 'LARGE FILES OVER 500M'
sudo find / -xdev -type f -size +500M \
  -not -path '/proc/*' -not -path '/sys/*' -not -path '/dev/*' \
  -printf '%s %p\n' 2>/dev/null | sort -n | tail -60

section 'PACMAN CACHE'
sudo du -sh /var/cache/pacman/pkg 2>/dev/null || true
sudo find /var/cache/pacman/pkg -maxdepth 1 -type f 2>/dev/null | wc -l
paccache -d 2>/dev/null | tail -20 || true

section 'JOURNAL AND LOGS'
sudo journalctl --disk-usage 2>/dev/null || true
sudo du -sh /var/log /var/lib/systemd/coredump 2>/dev/null || true
sudo find /var/lib/systemd/coredump -type f -printf '%s %p\n' 2>/dev/null | sort -n | tail -20

section 'BTRFS SNAPSHOTS'
sudo btrfs subvolume list -s / 2>/dev/null | tail -40 || true
sudo du -sh /.snapshots 2>/dev/null || true
for dir in /.snapshots/*/snapshot; do
  [[ -d "$dir" ]] || continue
  sudo btrfs filesystem du -s "$dir" 2>/dev/null | tail -1
done | tail -40

section 'USER CACHES AND TRASH'
du -sh /home/OWNER/.cache /home/OWNER/.local/share/Trash \
  /home/OWNER/.config/rpcs3 /home/OWNER/Загрузки 2>/dev/null || true
du -h -d 1 /home/OWNER/.cache 2>/dev/null | sort -h | tail -30

section 'BUILD TREES'
du -sh /home/OWNER/linux-cachyos-bc250/build/* \
  /home/OWNER/src/* 2>/dev/null | sort -h | tail -40

section 'TEMP'
du -sh /tmp/* 2>/dev/null | sort -h | tail -30

section 'POSSIBLE DUPLICATE GAME TREES'
du -sh /home/OWNER/relocated-games/* /home/OWNER/Games/* \
  /home/OWNER/gtavcne 2>/dev/null | sort -h | tail -40

section 'INSTALLED ORPHANS'
pacman -Qtdq 2>/dev/null | head -100 || true
