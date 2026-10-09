# BC-250 VCN unlock — прогресс за ~2 месяца (2026-06-25 → 2026-08-25)

Источники:
- Telegram MCP: `чат AMD BC-250 community` (`-1002424231195`), 40 query-dumps, **228** релевантных msg
- GitHub: `thelamer/bc250-vcn`, `daveconde/bc250-vcn-enable`, `bc250-collective/*`, `rw-r-r-0644/*`, search `bc250`
- Локальный A1: `tmp_bc250/specs/a1-readonly-report.md`
- Сырьё: `tmp_bc250/recon/tg_2m_progress_digest.md`, `tg_milestones_ranked.txt`, `gh_meta_summary.txt`

---

## Вердикт одной строкой

За 2 месяца community **доказал power domain 6 ON + direct-load FW path**, упёрся в **second gate (clock/reset/isolation)**. Рабочего VAAPI/encode **нет**. TG почти не знает thelamer/daveconde lab notes; публичный чат всё ещё крутит PSP-wall / vibe-скепсис. Наш stock board = community baseline (`VCLK=0`, `DCLK=1111`).

---

## Фазы прогресса

### Phase 0 — до окна / база (до ~2026-06)
Уже было (не VCN, но primitives):
- CPU **6c→8c** via SMU Q3 msg **`0x98`** arbitrary SMN write (`rw-r-r-0644/bc250-core-unlock`, RescueMei DXE variants)
- SMU RE: `bc250-collective/amd_smu_reverse_engineering` (Ghidra, queue tables) — last push **2025-12**, still the map everyone cites
- `bc250-smu-unlock` / `bc250_smu_oc` — userspace SMU access, code exec primitives
- Stock media: **no** skillfish VCN FW, no `/dev/video*`, amdgpu skips VCN on cyan_skillfish

### Phase 1 — late June 2026: «где FW / PSP не пускает»
TG (Jun 25–30):
- ROCm/HIP patches, golden regs, `navi10_gpu_info` symlink black-screen fix (не VCN)
- «прошивку на VCN 2.0.3 откуда взять?»
- PSP driver forks (`Keshas-dev/AMD-BC-250-PSP-Driver`) — side track
- Консенсус: **PSP не даёт просто включить**

### Phase 2 — July 2026: driver path + hang on MMIO (пик TG = 104 msg)
Ключевые claims (TG, доказательные):

| Date | Who | Finding |
|------|-----|---------|
| 07-02 | mirvsilv / community | firmware symlink fixes for boot (gpu_info), not VCN |
| 07-29 | Stas | SMU/PSP «куча дыр закрывали» historically |
| **07-30** | **pan_Rijovich** | **direct-load path exists in `vcn2_0.c`; VCN MMIO hang even status regs; VCN off by default** |
| 07-30 | Stas | SMU cannot tell PSP «skip verify» |
| 07-30 | pan | ABL header/signature offset notes |
| **07-30** | **Stas** | **«включал power management VCN в SMU до чтения регистров?»** ← правильный вопрос, community later answers YES via domain6 |
| 07-30 | pan | tried reverse `VcnPowerUp` in navi10 SMU FW — unclear internal vs external regs |

Июль = **диагноз hang = unpowered island**, не «мертвый silicon». Ещё нет публичного domain6 proof в TG.

### Phase 3 — early–mid August: IP discovery / kernel patch attempts
| Date | Who | Finding |
|------|-----|---------|
| 08-06 | Blank | PS5 needed full VCN+DCN chip narrative |
| 08-10 | Laird | «когда PCIe разблокируют» (другой unlock) |
| **08-12** | Pavel | patch discovery + `amdgpu_ip_blocks` → tries enable VCN → **no cyan_skillfish2 VCN driver** |
| 08-12 | Blank | VCN bins exist under `/lib/firmware/amdgpu` — useless alone |
| 08-12 | pan | «включать должен SMU, у нас не реализовано» |
| 08-12 | Vladislav | without VCN no real 4K stream competitor to Steam box |
| **08-13** | **Blank** | **dmesg IP list: common/gmc/ih/psp/smu/dm/gfx/sdma — NO VCN block** |
| 08-13 | Pavel | discovery patch hits kernel driver wall; brick risk mainly SMU |
| 08-13 | Blank | brick mostly at SMU stage; else black screen |

### Phase 4 — 2026-08-17: AMD official wall (Deucher via Daniel Lima)
Daniel Lima quotes **Alex Deucher** (amdgpu):
- no board-specific VCN FW
- IP reports **2.0.3 placeholder**; 2.0+ chips can use base 2.0.0 (e.g. Steam Deck blob)
- **PSP rejects** non-model-signed FW → «only AMD can sign»

TG reaction: PS5 dump / glitch fantasies; Maxim: bugs in PSP/SMU might help; Pavel: where are SMU/PSP dumps for Ghidra.

**Важно:** Deucher describes the **PSP load path**. Community RE already had **direct-load bypass** in notes — TG almost never connects the two.

### Phase 5 — 2026-08-18…24: lab notes land on GitHub (Discord → public)
**thelamer/bc250-vcn** (2026-08-18, 2 commits, ★5):
- Status: **powered on, held by second gate**
- Proven:
  - VCN 2.0.3 present, **harvest=0**
  - amdgpu skips register on Cyan Skillfish
  - stock telemetry **VCLK=0, DCLK=1111**
  - no `dpm_set_vcn_enable` → driver fake-success → MMIO hard lock
  - SMU 11.8 / PMFW Xtensa **88.6.0**
  - **Domain 6 = VCN power**; `FUN_00023b14(6,1)` works; teardown `FUN_00024764` touches slots **0x16/0x17/0x18** via `FUN_00023744` → `soc_clk_program_slot`
  - Q3 **0x98** SMN write (core unlock primitive)
  - direct-load FW → `device_fw_loading` 0; **placed ≠ executes**
- Ruled out:
  - no PowerUpVcn mailbox msg in SMU 11.8 (don't hunt VCN-named msgs)
  - don't reuse other-family mailbox IDs (0x8/0x9 ≠ VCN here)
  - BAR5/UMR/debugfs SMN MMIO hang
  - PSP type13 ITEM_NOT_FOUND; type64 TEE_SUCCESS **no-op**
  - no BIOS VCN option; PS5 FW arch different
- Open: diff regs pre/post domain6; program slots 0x16–0x18; VCLK/DCLK enable; Renoir/VanGogh dpm steps; only then ring test

**daveconde/bc250-vcn-enable** (2026-08-21…24, 18 commits, ★3):
- Spike: run Discord VCN enable **inside SMU** via `bc250-smu-unlock`
- BIOS **3 / Robin1 / PMFW 0.58.6.0 only** (BIOS5 offsets differ)
- Sequence: unlock → install 20B Xtensa thunk @ SRAM `0x3ff00` → repoint Q3 msg **0x61** → fire → engage slot ENABLE bits → optional `--direct-load` + ring test
- Mirrors teardown: three `call8 0x00023744` for slots 0x16/0x17/0x18
- Self-documented: HARD-WEDGE on unbounded VCLK/DCLK polls; measured wedge vectors; **not a working enable**
- TG (08-25): Aleś link → whiteflower «не рабочая» → Pavel «Discord vibe/Claude»

### Phase 6 — 2026-08-25: TG reaction + our A1
TG Flood:
- 0 successful runs of daveconde
- Pavel: vibe-coding without knowledge
- Parallel noise: 8c unlock BIOS vs soft, decky/lsfg, not media

Our A1 (steammachine, BIOS P3.00 match):
- Kernel `7.2.0-1.1-cachyos-bc250`, GPU `1002:13fe`
- No skillfish `*vcn*` FW; no `/dev/video*`
- `gpu_metrics` v2.2: **cur_vclk=0, cur_dclk=1111, cur_gfxclk=2000** = community stock baseline
- SMU good snapshot earlier (probe_vcn3): ver `0x580600`, features `0xdd602c7d`; later contention → status `0x00` (metrics/watchdog services)

---

## Что реально сдвинулось (измеримо)

| Capability | 2026-06 | 2026-08-25 | Evidence |
|------------|---------|------------|----------|
| Silicon present / not harvested | suspected | **proven harvest=0** | thelamer |
| IP discovery shows VCN 2.0.3 | partial | **confirmed** | thelamer + TG dmesg debates |
| amdgpu registers VCN on skillfish | no | **patched in lab** (not mainline) | thelamer |
| PSP accepts VCN FW | no | **still no** (Deucher + RE) | TG 08-17 + thelamer |
| Direct-load FW into VCN buffer | unknown | **works (load=0)** | thelamer / daveconde path |
| Power domain 6 ON | unknown | **proven** `FUN_00023b14(6,1)` | thelamer |
| Clocks VCLK/DCLK live | no (0/1111) | **still gated** | thelamer + our A1 |
| Clock/reset/isolation clear | no | **blocker** | thelamer open #1–3 |
| Ring test / decode | no | **hangs if forced** | thelamer |
| VAAPI / `/dev/video*` | no | **no** | A1 + TG |
| Public one-click enable | no | **no** (daveconde = instrumented spike) | TG 08-25 + README safety |

---

## Где community vs TG расходятся

| Topic | Lab (thelamer/dave/Discord RE) | TG public |
|-------|--------------------------------|-----------|
| Blocker | second gate after domain6 ON | still «PSP must sign» / «VCN dead» |
| Path | SMU internal FUN_* + slots 0x16–18 | kernel ip_blocks patch, navi10 bin copy |
| daveconde | lab notebook of wedges | «Claude vibe, not working» (correct outcome, wrong depth) |
| thelamer | primary status doc | **0 hits** on search `thelamer` in TG dumps |
| Core unlock | solved, separate | still hot daily traffic (52 msgs tagged) |

TG volume by theme (2m): firmware_blob 63 · core_unlock 52 · smu_power 41 · psp_wall 24 · driver_ip 11 · vibe 5 · daveconde 1 · deucher 1.

---

## GitHub ecosystem (updated in window)

VCN-specific:
- `thelamer/bc250-vcn` — 2026-08-18 notes (canonical status)
- `daveconde/bc250-vcn-enable` — 2026-08-21…24 spike + reg map

Primitives (older, still load-bearing):
- `bc250-collective/amd_smu_reverse_engineering` ★17 — SMU map
- `rw-r-r-0644/bc250-core-unlock`, `bc250-smu-unlock`
- `rpf16rj/bc250-steamos-real-toolkit` ★65 — SMU-HANDLERS, power tooling (active 08-25)
- `MastaG/linux-cachyos-bc250` ★30 — kernel we run (active 08-25)

Not VCN (noise in «bc250» search): SteamOS toolkits, batocera, LLM/ollama, fan/LED, community guides.

---

## Цепочка bring-up (актуальная)

```
IP discover VCN 2.0.3 harvest=0     ✅
Register vcn_v2_0 in amdgpu         ✅ lab patch
PSP FW auth                         ❌ → direct-load workaround ✅
Power domain 6 ON                   ✅ FUN_00023b14(6,1)
Slots 0x16/0x17/0x18 + VCLK/DCLK    ❌ second gate  ← YOU ARE HERE
Clear reset/isolation               ❌
Ring test / FW execute              ❌
VAAPI / encode / apps               ❌
```

---

## Что НЕ прогресс (частые тупики за 2 месяца)

1. Класть `navi10_vcn.bin` / symlinks без power+clocks
2. Искать mailbox `PowerUpVcn` по именам других SMU family
3. Читать VCN MMIO до SMU power → permanent hang
4. Ждать AMD-signed skillfish VCN FW (Deucher: only AMD)
5. PS5 FW drop-in (other arch)
6. BIOS setup VCN toggle (нет)
7. daveconde as «enable button» without reading HARD-WEDGE / no-proof sections
8. Kernel-only ip_blocks without SMU domain/slots

---

## Акторы

| Actor | Role |
|-------|------|
| Discord RE / thelamer notes | farthest on VCN power path |
| daveconde | packaged spike of Discord sequence + wedge catalog |
| pan_Rijovich, Stas (@dantistnfs) | early correct hang/power hypotheses (TG Jul) |
| Blank (@wd2blank) | dmesg IP proof, firmware location |
| Pavel (@pacha416) | driver discovery attempts; anti-vibe filter |
| Daniel Lima | Deucher quote bridge |
| TG majority | core unlock / daily ops; VCN mostly speculation |
| Our board A1 | confirms stock = pre-domain6 baseline |

---

## Импликации для нашего плана (second gate)

1. **Не** начинать с PSP key / signed FW — community already bypassed load via direct-load; blocker is clocks.
2. **Не** гонять daveconde fire blind — BIOS3-only, known wedge on dom6 `0x00` auto-power; use `--verify` / read-only first.
3. Next evidence that moves the needle (matches thelamer open threads):
   - reg diff before/after `FUN_00023b14(6,1)`
   - program slots `0x16/0x17/0x18` via `FUN_00023744`
   - prove VCLK/DCLK leave 0/1111
   - only then ring test
4. Stop SMU-contending services before any mailbox work (A1: metrics/watchdog → status 0x00).
5. Publish back to community only with **measured** VCLK/DCLK or reg deltas — TG needs lab-grade proof, not another enable script.

---

## Артефакты

| Path | What |
|------|------|
| `tmp_bc250/recon/tg_2m_progress_digest.md` | full 228-msg timeline |
| `tmp_bc250/recon/tg_milestones_ranked.txt` | ranked high-signal |
| `tmp_bc250/recon/tg2m/q_*.json` | per-query MCP dumps |
| `tmp_bc250/recon/thelamer-bc250-vcn-README.md` | community status |
| `tmp_bc250/recon/daveconde-README.md` | spike + wedges |
| `tmp_bc250/recon/gh_meta_summary.txt` | commits + repos |
| `tmp_bc250/specs/a1-readonly-report.md` | our board baseline |
| `tmp_bc250/specs/2026-08-25-bc250-vcn-community-second-gate-plan.md` | execution plan |

---

## Bottom line

**2 months of public TG:** mostly diagnosed hang + PSP myth + core-unlock traffic.  
**2 weeks of GitHub lab notes (Aug 18–24):** real step change — domain6 ON, direct-load, second-gate named.  
**Gap:** lab is ahead of TG by one full gate; nobody published cleared clocks or a passing ring test.  
**Our position:** stock board verified; next work = community second-gate track, not PSP keys and not vibe enable scripts.
