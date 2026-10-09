# Old Lamer (@OldLamer) channel digest — 3-month window

Date retrieved: 2026-09-22 (Asia/Almaty). Channel ID `UCUBPEFq09LAzKqqyrejZRdA`.
Method: agent-reach, platform YouTube via backend yt-dlp (OpenCLI browser
path failed: extension not loaded in Chrome, `Navigation rejected`).
Coverage: 13/13 metadata+descriptions, 9/13 full transcripts, 2/13 no
captions exist on YouTube side (P2z-De1gcUU, D_wPDKI0eao), 1/13 music-only
subs (5Sw1SdU9buQ), 2/13 trivial teasers. Raw fetch in `/tmp/oldlamer/`
(per skill workspace rules); this doc carries provenance + findings only.

Evidence class: `external-community-source` (participant reports). Nothing
here is hardware-verified on the operator board. Claims are single-source
until reproduced locally.

## Video ledger (2026-06-21..2026-09-21 window)

| Date       | ID / link                                                 | Duration / views | Content                                                                        | Transcript     |
| ---------- | --------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------ | -------------- |
| 2026-09-18 | `zjHuHKB0kjw` https://www.youtube.com/watch?v=zjHuHKB0kjw | 18:59 / 15683    | 36CU "unlucky" vs Steam Machine; 38CU symmetry proof; FSR4 INT8 via OptiScaler | full           |
| 2026-09-13 | `yuAFxEy8pXI` https://www.youtube.com/watch?v=yuAFxEy8pXI | 9:40 / 11106     | Non-BC250 Dell G5 + RX7600 budget build                                        | full (skimmed) |
| 2026-09-10 | `D_wPDKI0eao` https://www.youtube.com/watch?v=D_wPDKI0eao | 2:55 / 18621     | Steam Box 5 updates, Thermalright SI-100 budget version                        | NONE on YT     |
| 2026-09-07 | `tYmkv2bhkWQ` https://www.youtube.com/watch?v=tYmkv2bhkWQ | 22:31 / 36503    | BC250 Control Center all-in-one + GFX1013 async-compute patch                  | full           |
| 2026-09-05 | `7pVeH7j2Kv8` https://www.youtube.com/watch?v=7pVeH7j2Kv8 | 0:40 / 2209      | Teaser "Guess what will come next"                                             | trivial        |
| 2026-09-03 | `V8T9guS6rm4` https://www.youtube.com/watch?v=V8T9guS6rm4 | 22:38 / 24886    | Steam Box 5 vertical case build (screwless, HP PL28 PSU, P14 exhaust)          | full (skimmed) |
| 2026-08-26 | `x1cLGKcg_jk` https://www.youtube.com/watch?v=x1cLGKcg_jk | 0:45 / 8861      | JF13K case teaser                                                              | trivial        |
| 2026-08-22 | `hfJSzgiWb40` https://www.youtube.com/watch?v=hfJSzgiWb40 | 9:27 / 23632     | JF13K top-blow cooler on BC250, temps, hybrid mount                            | full           |
| 2026-08-18 | `GxRwKQL_GPw` https://www.youtube.com/watch?v=GxRwKQL_GPw | 15:59 / 5687     | ASUS TUF A16 (7435HS+7600S) as Steam Machine alternative, eBay 699 EUR         | full (skimmed) |
| 2026-08-10 | `P2z-De1gcUU` https://www.youtube.com/watch?v=P2z-De1gcUU | 20:53 / 15355    | Round 2: unlocked BC250 (8C/40CU) vs Valve, 7 games + R23 + power              | NONE on YT     |
| 2026-08-05 | `5Sw1SdU9buQ` https://www.youtube.com/watch?v=5Sw1SdU9buQ | 17:25 / 18931    | Valve vs BC250 (8C@4.0/40CU@2.0/Bazzite): BC250 wins 4/7                       | music-only     |
| 2026-08-01 | `ARFOKLBi_Tc` https://www.youtube.com/watch?v=ARFOKLBi_Tc | 18:42 / 33015    | 8-core unlock Part II: modified BIOS flash + 6v8 game benchmarks               | full           |
| 2026-07-30 | `wJpYmd8OwHE` https://www.youtube.com/watch?v=wJpYmd8OwHE | 6:03 / 16092     | 8-core unlock Part I: software script, +30% MT Geekbench                       | full           |

## Key technical findings (participant claims, not project verdicts)

### F1. Permanent 8-core BIOS exists (ARFO, 2026-08-01)

- Author: Forbidden-Darkness. Tool:
  https://github.com/Forbidden-Darkness/AMD-BC-250-UEFI-v2.2-Firmware-Menu-Script
  (this is the same "FD v2.2" family as the project's FD donor `606a7a7f`).
- Ready files (incl. `8coreSteam.rom` + flasher): public Drive folder from
  the video description,
  `https://drive.google.com/drive/folders/19qrh9XYZaH-_4hieWBtCZSJYdISyhlat`
  (retrieved 2026-09-22; contents NOT downloaded or verified here).
- Method: USB stick → boot → EFI shell → backup with `fix64.efi /O` (AFU
  family) → flash with `/P /N` → power cycle → clear CMOS (jumper or
  battery 20–30 s) → CPU Configuration → `Unlock CPU Cores = Enabled` →
  re-apply fan curve + VRAM 512 MB → boot. Rollback = CMOS reset to 6 cores.
- No programmer needed. Author warns: not every APU has 2 functional spare
  cores; test software unlock first; flash at own risk.
- Benchmarks 6v8: HZD Remastered, Cyberpunk 2077, Doom TDA, AC Shadows,
  TW Warhammer III (avg FPS, 1% lows, frametimes, temps — numbers are
  on-screen only, not transcribed).

### F2. Software 8-core unlock (wJpY, 2026-07-30)

- Project: https://github.com/rw-r-r-0644/bc250-core-unlock,
  `bc250-unlock-cores.py`; stop `cyan-skillfish-governor-smu`, run, reboot.
- Claimed ~+30% multi-core (Geekbench). Pre-existing 6-core OC carries over
  to all 8 (crash cause). Does NOT survive cold reset (warm reboot OK).

### F3. CU topology symmetry rule (zjHu, 2026-09-18)

- PS5 APU GPU = 2 shader engines x 20 CU; WGP = 2 CU. Perf scales ONLY with
  balanced SE counts: 18+18=36 works; 20+18="38" shows but adds nothing
  (FurMark-verified on camera: 24→26 no gain, →28 symmetric gain, →30 asym
  no gain, →32 gain; fully-asymmetric 32 = no gain vs 24).
- Rule: enable max EQUAL per-SE count (e.g. 16+16=32 when one SE limited).
- 36CU@2.0 + 8C@3.85 + async patch trades blows with Valve machine; single
  Arctic P12 Pro + PTM7950, fan ≤2000 RPM, ≤220 W in games; 280 W Meanwell
  brick sufficient (not for FurMark+OCCT simultaneously).

### F4. FSR4 INT8 usable on BC250 (zjHu, 2026-09-18)

- Community FSR4 adaptation + OptiScaler client injection across library.
- Install quirk: extract archive into a new `applications` folder and run
  installer from there (path-resolution error otherwise); scan games, patch,
  in-game Insert menu → FSR4. Expedition 33 bridge: FSR2/3 70+ FPS heavy
  shimmer → FSR4 62 FPS (~10% cost), shimmer gone.

### F5. BC250 Control Center + async-compute patch (tYmk, 2026-09-07)

- https://github.com/movacx/bc250-control-center (Bazzite RPM): dependency
  prep (CPU OC tool, cyan-skillfish SMU governor, CU live unlock), CPU OC
  presets + custom (author stable: 3850 MHz @ 1160 mV, 8C, P12 Pro +
  PTM7950; 100 MHz stepwise apply, test, save-for-boot service), GPU
  governor presets (40CU@2GHz; FurMark 70→100+ FPS at 24CU), metrics fix,
  CU unlock with sync/read-back (24→36 balanced: FurMark 100→150 FPS),
  fan curves (revert to BIOS via Automatic), zRAM→zswap migration (16 GB
  file), GPU mem dynamic limit 10–12 GB vs 8 GB default (black-screen fix).
  Mitigations toggle promised next release (manual for now).
- Async patch: https://github.com/DryhoppedIPA/bc250-gfx1013-fix and
  https://github.com/tri3gubki-ops/bc250-async-compute-bazzite ;
  one-click install in CC (dashboard → compatibility), reboot; Cyberpunk
  before/after demo; claimed up to +20% in CPU/GPU-heavy games.

### F6. JF13K air cooling for max OC (hfJS, 2026-08-22)

- Top-blow cooler, 2×120 mm slim fans, cools VRM zone; VRM/chip heatsinks.
- Hybrid mount: NexGen3D back bracket + printed top
  (printables `1574416`, `1554003`-aio-mount), 0.9 mm springs, PTM7950,
  AM4/AM5 brackets, CPU header. Printables: see video description.
- 40CU@2GHz FurMark: 62–63 °C; UE5 games: 49–52 °C; 20-min loop: APU low
  50s, VRM ≤70 °C, sinks ~40–50 °C. Quiet, maintenance-free.
- Side note: Batocera v44 = kernel 7.2 + Mesa 26.2.1 + sound fixes.

### F7. Comparisons vs Valve hardware (5Sw1, P2z, GxRw, yuAF)

- Unlocked BC250 (8C@4.0, 40CU@2.0, Bazzite) beats Valve Steam Machine 4/7
  games at ~40% of the price (5Sw1: BMW, HZD-R, CP2077, AC Shadows, Doom
  TDA, FH6, Returnal). Round 2 adds Halo CE, Avatar, RDR2, Division 2, CS2,
  AC BF Resynced, Metro EE + R23 + wall power (P2z: chapters only).
- Valve favors single-core (CS2); BC250 favors GPU-bound (AC Shadows).
- ASUS TUF A16 2023 (7435HS+7600S Navi33, 95 W) ≈ Steam Machine GPU,
  bought 699 EUR 2024, now on eBay (GxRw). Dell G5+i5-10600K+RX7600 ≈ half
  Valve price (yuAF, non-BC250).

## Project impact (leads, not adoptions)

- I1. Ready-made 8-core BIOS + AFU USB method is a faster route than the
  project's drivers-only CLV rebuild for the operator's "flash and game"
  goal — but base version/board-match of `8coreSteam.rom` is unverified;
  download + hash + structural audit required before any flash talk.
- I2. Async-compute patch + Control Center overlap the project's OC track;
  CachyOS-portability of the Bazzite-oriented pieces is unproven.
- I3. CU-symmetry rule corroborates careful 24/32/36/40 stepping for any
  future CU work; contradicts naive "max CU number" chasing.
- I4. FSR4-INT8-via-OptiScaler corroborates the project's FSR4 fork lead.
- I5. JF13K + PTM7950 + 0.9 mm-spring mount is a concrete air-cooling
  recipe if the operator pushes clocks.

## Gaps

- G1. P2z-De1gcUU and D_wPDKI0eao have no captions on YouTube (verified via
  `--list-subs`); only descriptions+chapters captured.
- G2. 5Sw1SdU9buQ captions are music-only.
- G3. On-screen benchmark numbers were not transcribed (visual only).
- G4. No project-local reproduction of any linked repo/ROM was performed.
