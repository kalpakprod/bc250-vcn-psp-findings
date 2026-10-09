# Research: BC250 swap/zram/zswap/VRAM-split tuning (community)

Date: 2026-09-21. Skill: research-provenance. Question: recommended swap
architecture for BC250-01 (7.5G OS RAM, fixed 8G VRAM carveout, 4G GTT cap,
zram 8G lz4 refilling in <30 min) and verdict on the proposed 32G disk
swapfile. Decision impact: zram-vs-zswap architecture + swapfile size.

## Sources

1. `redbeard1083/bc250-toolkit` @ `f8fb098a297b2f9e2eb16b22c58cab7a7cac9da9`
   (2026-09-19). License: NONE in repo (unlicensed; read-only use, no code
   copied). Files: `bc250-toolkit.sh` L554-615 (swap: 16G file default,
   swappiness 60 default, btrfs-aware), L658+ (zram OFF via
   `systemd.zram=0` + mask, zswap ON: lz4, pool 25%), L5365+ (memcfg
   UMA_SIZE, default 512MB; ttm.pages_limit raise, default 12G).
   Class: source code + embedded operator claims.
2. `elektricm/amd-bc250-docs` @ `0524002` (2026-08-13). License: see repo
   LICENSE file (checked: present; terms not line-read). Files:
   `docs/troubleshooting/performance.md` L405-463 (fixed splits 4G/12G
   most games, 6G/10G esports, 8G/8G+ VRAM-heavy; zram→zswap lz4/25%,
   swappiness 180 example), `docs/troubleshooting/stability.md` L331+
   ("ZRAM Conflicts with Dynamic VRAM", RDR2 crash report → fixed 10/6).
   Class: primary documentation + participant reports (single-source).
3. Local dead ends (coverage gaps, not evidence): 4PDA captures
   (`import/.../archives/imported/recon-evidence/legacy-tmp-bc250-recon/4pda_*.txt`, Aug 2026) = MCP error +
   captcha wall; opencli reddit adapter exists but browser profile
   `u4msqzt7` disconnected; Discord not installed; no Telegram adapter.
   No chat mining performed. 4PDA/Telegram/Discord remain unsearched.

## Agreed claims (2 sources)

- Prefer FIXED VRAM split over 512MB dynamic when memory-troubled.
- Prefer ZSWAP (lz4, max_pool_percent=25) over ZRAM for RAM-hungry games.
- Disk swapfile as overflow backing (16G default), swappiness HIGH
  (60 toolkit / 180 docs example) to keep the compressed pool fed.

## Single-source / contested

- "512MB dynamic + ZRAM = crashes/OOM" (docs, participant report). Our
  board is FIXED 8G carveout (sysfs: vram_total 8G, gtt_total 4G via
  ttm.pages_limit=1048576) — the exact combo does NOT apply here.
- Swappiness 180 (docs example, Bazzite+zswap) vs 60 (toolkit) vs ours 20
  (zram model). Value is architecture-dependent; no BC250 A/B measured.
- memcfg UMA default 512 + 12G dynamic ceiling (toolkit) vs our fixed 8G
  - 4G cap. Our game uses 6.4-6.9G VRAM — a 4G carveout would force
    ~2.5G into GTT. No measurement for either on this workload.

## Local reproduction

- zram 8G lz4 refills to 94%+ within 27 min of gaming (observed
  `/proc/swaps`, 2026-09-21). si/so tens of MB/s sustained during play
  (164-sample vmstat capture). Swappiness was 150, now 20 (live +
  `/etc/sysctl.d/99-bc250-gaming.conf`).
- G7 2026-09-21: catastrophic freezes (50→6 FPS + hard lockup) ENDED
  after the operator reseated the SSD (flapping PCIe link under the
  swapfile/game I/O). Swap pressure is real but was the AMPLIFIER, not
  the sole cause. dmesg evidence unavailable (cmdline loglevel=0).

## Sanitized conclusion (ADAPT, not ADOPT)

- Do NOT copy the toolkit verbatim (unlicensed; overlaps our tooling).
- Directionally correct for us: zswap (lz4/25%) over fixed zram (zram
  CLIFFS when full; zswap overflows gracefully), big disk file as
  overflow only, swappiness matched to architecture (60 with zswap).
- 32G swapfile: harmless insurance, not a fix (file never held >2G;
  constraint is speed, not size). Grow at a reboot window, not live
  (swapoff under pressure risks OOM).
- Next: live zswap trial (`/sys/module/zswap` writable), then persist
  via cmdline drop-in if it behaves; keep 8G carveout (game needs it).
