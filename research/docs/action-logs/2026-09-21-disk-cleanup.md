# Action log: system-disk cleanup (board /)

Date: 2026-09-21. Actor: root. Context: `/` 98% full (96G/100G, same
partition as /home); operator order: delete trash / redownloadable.

## Intent (before execution)

Board `steammachine@127.0.0.1`. Audit (2026-09-21):

- `~/linux-cachyos-bc250/build/` 28G: compile output of MastaG repo
  clone (origin github.com/MastaG/linux-cachyos-bc250), dated
  2026-08-26, contains only `linux-cachyos-rc` tree, NO .pkg files.
  Git: clean except 3 untracked patch files in `patches/` (OUTSIDE
  build/, untouched). Regenerable via rebuild; superseded by bore-vcn
  7.2.6 built on .74. DELETE build/ only.
- pacman cache 37M: `pacman -Sc --noconfirm` (keeps installed).
- NOT touched (user data, report only): Steam 29G, PS3_GAMES 19G,
  rpcs3 3.2G, PortProton 3.7G, /opt 2G, journal 46M (diagnostic value),
  snapshots (recovery), old kernels rc/vcn (boot entries; small gain).

Expected: 96G → ~68G (~70%). Rollback: rebuild or re-clone
(git origin known); no unique data in build/.

## Result (2026-09-21 ~21:35, PASS with note)

- `build/` deleted (BUILD_GONE), sources kept (LICENSE/MANIFEST/README/
  pacman/patches/scripts intact, incl. 3 untracked local patches).
- pacman cache cleaned (incl. unused sync repos).
- df: 96G → 81G used (83%), 17G free.
- NOTE: only ~15G freed of 28G deleted — remainder pinned by snapper
  snapshots (build/ existed since Aug-26, referenced by all snapshots
  since). Space releases as snapper rotates old snapshots. Today's
  111/112 (bore-vcn install rollback) deliberately kept. Thinning
  pre-September snapshots NOT done (recovery points, needs order).
