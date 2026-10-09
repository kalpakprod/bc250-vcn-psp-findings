#!/usr/bin/env bash
set -Eeuo pipefail

if pgrep -x shadps4 >/dev/null 2>&1 || pgrep -x shadPS4 >/dev/null 2>&1; then
  echo "shadPS4 is running; refusing removal" >&2
  exit 1
fi

user_paths=(
  /home/OWNER/src/shadps4
  /home/OWNER/src/shadps4-bc250-clean
  /home/OWNER/shadps4-git
  /home/OWNER/.local/share/shadPS4
  /home/OWNER/.local/share/shadps4
  /home/OWNER/.config/shadps4
  /home/OWNER/.config/shadPS4
  /home/OWNER/.local/bin/shadps4-console
  /home/OWNER/.local/bin/bloodborne
  /home/OWNER/.local/bin/ratchet-clank
  /home/OWNER/.local/share/applications/shadps4-console.desktop
  /home/OWNER/.local/share/applications/bloodborne.desktop
  /home/OWNER/.local/share/applications/ratchet-clank.desktop
  /games/.shadps4-src-d316ff1
  /games/.shadps4-build-d316ff1
  /games/PS4_GAMES
)
root_paths=(
  /opt/shadps4-bc250
  /opt/shadps4-prerelease
)

echo '=== BEFORE ==='
df -h / /games
for path in "${user_paths[@]}" "${root_paths[@]}"; do
  [[ -e "$path" || -L "$path" ]] || continue
  du -sh "$path" 2>/dev/null || true
done

rm -rf -- "${user_paths[@]}"
sudo rm -rf -- "${root_paths[@]}"

if pacman -Qq shadps4-bin >/dev/null 2>&1; then
  sudo pacman -R --noconfirm shadps4-bin
fi

command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database /home/OWNER/.local/share/applications || true
sudo btrfs filesystem sync / || true
sync

echo '=== AFTER ==='
df -h / /games
failed=0
for path in "${user_paths[@]}" "${root_paths[@]}"; do
  if [[ -e "$path" || -L "$path" ]]; then
    echo "still exists: $path" >&2
    failed=1
  fi
done
if pacman -Qq shadps4-bin >/dev/null 2>&1; then
  echo 'package still installed: shadps4-bin' >&2
  failed=1
fi

find /home/OWNER /games /opt -maxdepth 4 \
  \( -iname '*shadps4*' -o -iname 'CUSA01073' -o -iname 'CUSA03173' \) \
  -print 2>/dev/null | head -100

exit "$failed"
