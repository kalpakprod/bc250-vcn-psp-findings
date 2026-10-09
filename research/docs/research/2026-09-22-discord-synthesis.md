# Discord synthesis: BC250 community history vs our project (2026-09-22)

Root synthesis from the 2026-09-22 Discord wave (STOP-ordered mid-run for account safety).
No Discord API calls were made for this document; all mining below is local files only.

## 1. Provenance (research-provenance)

- Guild: BC250 Community Discord `1315924807128449065` (6923 members, owner TG2/realderyn).
- Complete worker artifacts (read-only, verified receipts): T1 (500 msgs, Sep 20-21 2026),
  T2 (836 msgs, 20 terms), T3 (986 msgs, 29 help threads), T6 (346 msgs, 11 terms),
  T10 (rules/announce/faq/flex/pins), T11 (guild ctx + operator history).
  Paths: `/tmp/discord-track-{01,02,03,06,10,11}-*.md`, raw `/tmp/discord-raw-*/` (374 JSON).
- Partial: T7 draft (147 lines, V1-V12 voltage/OC), T4/T5/T8/T12 raw fragments.
- Local bulk export `/tmp/discord_bc250_pre0322.jsonl` (113,309 msgs, 2025-09-22 -> 2026-03-21,
  bc250-chat/offtopic/flex/faq/announce) + `/tmp/discord_export_state.json` — pulled during
  our own wave by a worker script; used here as local data only.
- NOT covered: DMs (T9 blocked 2x429, retry cancelled by STOP), in-progress/dynolog/
  moderator-only (50001 Missing Access), forum offset-deep pages, Mar-Jun 2026 gap between
  export end and search windows, attachments (filenames only).
- Evidence class: ALL chat quotes below are trust-class-6 participant reports, NOT proof.
  IDs are `msg_id` in guild `1315924807128449065` unless noted.

## 2. Community unlock lineage (timeline)

- Nov-Dec 2025: `pp_od` **`vc`-path recipes** (FilippoR 1438914981667012738, 1438915509948252230,
  1440801600737120306; Dec 18 recipe 1451248701745135626): stop governor,
  `echo vc 0 <CLOCK> <VOLTAGE> > pp_od_clk_voltage`, `echo c`. NOTE: `vc`, not `s`.
- Dec 2025: dantistnfs 1437810290879365201 — SMU sleep-state msgs point to stubs; PSP signing wall.
- Mar 2026: consensus "P3.00 + chipset menu" (popsicle 1477761133061603657); modded 5.00 =
  dangerous, brick-risk options (essdee 1481305223489392832, popsicle 1477760444193308732).
- Apr 2026: angablade SMU register/REP/Feature tables (1490964063310839909, 1490964088744972328).
- Jul 2026: ded811 AmdSetup EFI-variable route, no BIOS mod needed (1523465147845443828...);
  essdee hijacks hidden Setup:0x1C4; rescuemei plans NVRAM-configured DXE v2.
- Aug 10 2026: **essdee DXE breakthrough** — custom DXE + VFR/HII adds own menus + varstore
  (1536306207663464528, 1536427524706271373); rescuemei: "much much easier" (1541564263691321345).
- Aug 24 2026: rescuemei documents lineage — FF-only SMU bug -> arbitrary protected writes,
  BIOS mod = C port of rw's scripts + rw's SMU fw patch (1541561432108310650, 1541562254271455273);
  core-unlock repo `github.com/rw-r-r-0644/bc250-core-unlock`.
- Sep 2026: FD `Forbidden-Darkness/AMD-BC-250-UEFI-v2.2-Firmware-Menu-Script` is the standard
  recommendation (B3/B4); janusz_62029 P3.00-unlocked v0.2 bundles all MeiMei patches
  (1550021247990235227). Current newbie path (T10): 3.00 CHIPSETMENU -> Linux ->
  `WinnieLV/bc250-cu-live-manager` -> optional DXEv2/FD BIOS -> governors.

## 3. Direct answers

### 3.1 Why is our project slow (the original question)

Branches we burned months on were already closed WITH CAUSE by the community:

1. **P5.00/CLV as a base**: community consensus since Nov 2025 = no benefit, dangerous
   options, fan-control bugs (holde 1495315348977881088), ReBAR breaks USB2, PXE netboot
   default. Our whole-FV graft af531026 failed P0; drivers-only 0968a70c still unflashed.
2. **VCN via policy/patch**: dantistnfs (Nov 2025) + popsicle (Mar 2026) + our own S2-A/S4
   all converge: bridge/PSP-signing wall, no working recipe anywhere. Months spent after
   the wall was already characterized.
3. **pp_od max-first via `s`-path**: peer reports EINVAL on `s 0 2200 1129`, but community
   recipes use the **`vc` path**. The `s` failure does not close the `vc` question (open Q below).
4. **4700S Frankenstein**: C0A PSP kill locus; no community success either.
   Meanwhile the working stack (FD/RescueMei/janusz BIOS + governors + live-manager) was never
   tried as-is on our board: our live chip ALREADY runs MeiMeiDXEv3-XL with the menu present
   but Disabled in NVRAM — enablement needs a Setup visit, not a flash.

### 3.2 maymay/FD menu: why his works

FD ships 6 coherent DXE drivers on the 3.00 base they were built for; Menu_Driver installs
its own HII FormSet (ACPI/SMU/CoreUnlock/per-core). essdee's Aug-10 breakthrough is the
documented technique; rescuemei confirms DXE-menu > Setup-hijack. Our graft failed at
boot/dispatch on a foreign 5.00 base; our clean drivers-only build never booted. Not a
menu race we lost — an experiment we never ran on hardware.

### 3.3 pp_od peer claim: correction

Peer (soft session) claimed "39k msgs, zero pp_od recipes" and max-first impossible. Local
export proves `vc`-path recipes existed Nov-Dec 2025 (FilippoR x3 + Dec-18 recipe). Peer
tested `manual`/`s`/`c` only. OPEN Q: does `echo vc 0 <clk> <volt>` + `c` still work on
7.2.6-1.2? One careful read-first retest decides it. Until then "pp_od dead" = overstated.

### 3.4 Old Lamer

A YouTuber, not a Discord tech lead: step-by-step SMU OC video (froginasock 1484539716761292811),
BIOS+Bazzite install guide (cliff_86 1444487247188721747), OC video (Strykur 1459541042327191583),
Honeywell-PSU case build. Community-respected guides. His SMU OC video transcript is the
single highest-value unwatched artifact (yt-dlp fetch status: check session).

### 3.5 Operator's own footprint

4 messages total, all 2026-06-17: asked for P5.00_clv, T.Sharp warned against v5
("no benefits, downsides"), operator noted CH340A programmer intent. No reply after.
Our work history is NOT in the operator's posts — it is in community threads.

## 4. Tech facts worth promoting (all single-source until reproduced)

- VDDCR: zero hits guild-wide; LLC: no load-line discussion (T7 true negatives).
- FCLK/MCLK: fixed 450 MHz, no SMU control known; "MCLK inverted in driver, 450 means 1750"
  (dantistnfs 1492554062518947962); golden 1:1:1 rule cited, mem OC breaks it (Dznuts).
- Safe voltage ~1275 mV (Lord Antares 1550104341384536155); uncapped-VID brick warning
  (Yrouel 1548088539051327550 — bricked a board).
- 36CU ~= 38CU perf; valid steps 40/36/32/28/24 (zerosumpr 1549240138914332743, d0c T1).
- CMOS-clear vs NVRAM: CONFLICT preserved (essdee: BIOS clears NVRAM vs hexxeh: SPI survives).
- GDDR6 1750->1650 MHz boot fix (brain_cylinder T01, Dream-Cypher script).
- 5V-logic CH341A fries non-flash ICs — use programmer-first with verified 3.3V (T20).
- ACPI fix implicated in green screens; two users clean without it (T24).

## 5. Gaps and next decisive tests

1. `vc`-path retest on 7.2.6-1.2 (closes 3.3). 2. Setup visit: enable MeiMei SMU+CoreUnlock
   on the live XL image (no flash). 3. Old Lamer SMU-OC transcript. 4. DMs only on explicit
   order. 5. Mar-Jun 2026 history gap. 6. T4/T5/T8 partial raws minable locally anytime.
