# A1 Read-only recon — BC-250 VCN

**Дата:** 2026-08-25  
**Плата:** `steammachine` / `127.0.0.1` (SSH OK, `sudo -n` OK)  
**Режим:** только чтение. Без MMIO VCN, без SMU write, без установки firmware, без kernel rebuild.  
**Артефакты:** `tmp_bc250/recon/a1_*.out`, `a1_part*.sh`

---

## 1. Вердикт A1

На этой плате **VCN userspace-путь мёртв**: нет `cyan*vcn` firmware, нет `/dev/video*`, `vainfo` нет, sysfs media/clock для VCN не отдаёт данных.  
Ядро **содержит** generic VCN-код и cyan_skillfish2 marker, но **локальные патчи 7.2 не регистрируют/не включают VCN**.  
SMU mailbox userspace (`bc250-smu-oc`) жив как API, **VCN-методов в пакете нет**.  
**Stock media clocks подтверждены:** `cur_vclk=0`, `cur_dclk=1111` (gpu_metrics_v2_2) — 1:1 с community baseline «VCN powered down».  
Сообщество (`thelamer/bc250-vcn`, 2026-08-24): domain 6 power уже брали; **их блокер = clock/reset/isolation**. У нас даже pre-power stock.

---

## 2. Живая конфигурация

| Поле | Значение |
|---|---|
| Kernel | `7.2.0-1.1-cachyos-bc250` |
| GPU | `1002:13fe` Cyan Skillfish, `amdgpu` bound, rev `0x00` |
| Audio func | `1002:13ff` |
| BAR0 / BAR2 | 256 MiB pref / 2 MiB pref |
| PCIe | 16.0 GT/s ×16 |
| VRAM / GTT | 8 GiB / 4 GiB (`mem_info_*`) |
| DRM | `/dev/dri/card1`, `renderD128` only |
| Media nodes | **нет** `/dev/video*`, `/dev/media*` |
| `vainfo` | absent |
| `amd_psp` module | **not loaded**, no modinfo |
| GPU fixed | `FREQUENCY_MHZ=2000`, `VOLTAGE_MV=1013`, thermal 100°C |
| CU path | `bc250-cu-layout` **active** (stable 38-CU) |
| Netconsole | `bc250-netconsole` active |
| Governor SMU | `cyan-skillfish-governor-smu` **inactive** |
| Packaging tree | `~/linux-cachyos-bc250` = **patches/scripts only**, not full kernel sources |
| Netconsole sink | `127.0.0.1:6666` (`bc250-netconsole.sh`) |
| `ip_block_mask` | `0xffffffff` (all bits; VCN still not exposed as /dev/video) |
| debugfs dri | **not mounted/readable** |

Cmdline (relevant): `amdgpu.sg_display=0 ttm.pages_limit=1048576 loglevel=0 mitigations=off acpi_enforce_resources=lax`

---

## 3. Firmware

**Cyan Skillfish2 present:**  
`ce me mec mec2 pfp rlc sdma sdma1` under `/lib/firmware/amdgpu/cyan_skillfish2_*.bin.zst`

**Absent (confirmed `find`):**  
- `cyan_skillfish*_vcn*`  
- `*skillfish*vcn*`  
- `*cyan*vcn*`

Other families’ `*_vcn.bin.zst` лежат в дереве (navi10, beige_goby, vcn_4_*, …) — **не skillfish**, symlink/copy сам по себе VCN не поднимет (PSP `ITEM_NOT_FOUND` / signature path в community notes).

---

## 4. Sysfs / telemetry hazards (важно)

| Node | Результат |
|---|---|
| `mem_info_*`, link speed/width | OK, быстро |
| `pp_dpm_sclk/mclk/fclk/socclk` | **READ HANG** (процесс клинит; убит) |
| `pp_dpm_vclk/dclk` | не дошли / missing после hang |
| `firmware_info` / `ip_blocks` | **missing** |
| `gpu_metrics` | **readable** (128 B, fmt 2.2); concurrent readers (`bc250-metrics`) → D-state / restart storm |
| hwmon `amdgpu` | name есть; temp/freq/power sysfs часто пустые |
| debugfs `/sys/kernel/debug/dri` | no_debugfs |

**Правило:** не читать `pp_dpm_*` unguarded. `gpu_metrics` — только с timeout; metrics service уже держит его.

dmesg/journal локально почти пусты (`loglevel=0`) → netconsole `127.0.0.1:6666`.

### 4.1 gpu_metrics_v2_2 (probe_vcn3 hexdump, layout = `bc250-metrics.py`)

| Field | Value | Note |
|---|---|---|
| size/fmt/cont | 128 / 2 / 2 | matches sampler |
| `cur_gfxclk` | **2000** | = GPU fixed |
| `cur_socclk` | 1254 | |
| `cur_uclk` / `cur_fclk` | 450 / 450 | |
| **`cur_vclk`** | **0** | stock VCN clock off |
| **`cur_dclk`** | **1111** | community baseline same |
| `avg_vclk` / `avg_dclk` | 0 / 1111 | |
| `act_mm` | 0xFFFF (invalid) | no media activity |

`bc250-metrics.py` **парсит** `cur_vclk`/`cur_dclk`, но **не эмитит** их в kmsg (только gfx/soc/u/fclk). Off-box сейчас **не** видит VCLK без правки sampler или разового parse.

---

## 5. SMU userspace (`bc250-smu-oc`)

- Package: pipx venv Python 3.14, transport PCI config `0000:00:00.0`
- Queues 0..4 mailbox addrs in `api.py` (`DEFAULT_QUEUE_ADDRS`)
- **60 public methods** — CPU/GPU OC, features enable/disable, gfx force freq/vid, soft min/max cclk, temps…
- **Ноль** методов/строк с `VCN` / `VcnPowerUp` / `vclk` enable в site-packages
- Есть `raw_send(queue, msg_id, arg)` — общий примитив (как 40CU path)

**Read results:**

| Когда | Результат |
|---|---|
| `probe_vcn3.out` (sudo, earlier boot window) | `test_message OK`, `smu_version=0x580600` (**88.6.0** = community PMFW), `enabled_features=0xdd602c7d`, `active_wgp=0xc` (12 WGP), `core_pstate0=0x5` |
| A1 part6/7/8 now | **all** known-safe msgs → `status 0x00` even with `use_flock=True` + 5 retries |
| q3 `0x98` / `0x27` / `0x2a` / `0x2b` (probe_vcn3) | status 0x00 — not a usable VCN path from host msg table |

**Concurrent SMU/sysfs consumers (part8):**
- `bc250-metrics.service` — **NRestarts=214**, `python3 bc250-metrics.py` often **D** (blocked on `gpu_metrics`)
- `bc250-pwrwatch`, `bc250-gpu-watchdog` (heavy D time), `bc250-telemetry`, fan, dpwatch
- metrics **не** ходит в SMU mailbox (только `gpu_metrics` sysfs); contention mailbox = другие writers/readers (watchdog/gpu-fixed path/amdgpu)

**API surface vs community:**
- `raw_send` / `raw_read` / `send_message` — есть
- queues 0–4 PCI config addrs — есть
- **ноль** VCN/PowerUp/domain helpers в package (grep empty)
- community: **нет** host `PowerUpVcn` msg в SMU 11.8; path = internal `FUN_00023b14(6,1)`; q3 `0x98` = ungated SMN write (core unlock primitive), not VCN power

---

## 6. Kernel / patches on board

`patches/kernel-7.2/` (installed line):

- 0001 telemetry / gpu activity (cyan_skillfish_ppt metrics; **печатает vclk/dclk fields** из SMU metrics struct)
- 0003 nct6687d hwmon  
- 0004 gfx1013 pasid TLB  
- 0005 compute gfxoff guard  
- 0006 kfd flush TLB  
- 0007 ttm null page guard  

**Нет** patch «register vcn_v2_0 for cyan skillfish».  
Mesa patches: compute queue / mesh / radv gfx103 — **не VCN/VAAPI**.

`amdgpu.ko.zst` strings (установленный модуль) содержат среди прочего:

- `AMD_APU_IS_CYAN_SKILLFISH2`
- `amdgpu_discovery_get_vcn_info`
- `amdgpu_vcn_is_disabled_vcn`
- полный набор `amdgpu_vcn_*` ring/fw/debugfs symbols
- `AMDGPU_PP_SENSOR_VCN_POWER_STATE`, `VCLK` metrics IDs

→ драйвер **умеет** VCN framework; платформенный bring-up для skillfish **не активирован** в этой сборке.

---

## 7. Сверка с `thelamer/bc250-vcn` (upstream notes)

Полный README: `tmp_bc250/recon/thelamer-bc250-vcn-README.md` (repo = только README).

| Стадия community | У нас A1 |
|---|---|
| IP discovery VCN 2.0.3 harvest=0 | **не подтверждено** (ip_discovery/ip_blocks sysfs missing; debugfs absent) |
| Register `vcn_v2_0` | **нет** в 7.2 patches |
| FW past PSP / direct-load | skillfish VCN blob **absent**; not tried |
| Power domain 6 ON | **not done** (write). Community: internal `FUN_00023b14(6,1)` |
| Second gate clock/reset/isolation slots `0x16/0x17/0x18` | community **current blocker**; we are pre-power |
| Ring / MMIO | hang risk — **not touched** |
| Stock VCLK=0 DCLK=1111 | **confirmed** on this board via gpu_metrics |
| SMU 11.8 / PMFW 88.6.0 | **confirmed** (`0x580600`) |
| No PowerUpVcn mailbox msg | package surface agrees (no VCN msgs) |
| Don't poke BAR5/UMR/SMN-debugfs | respected in A1 |
| PSP type13 ITEM_NOT_FOUND / type64 no-op | not re-tested; community ruled out |

**Ruled out by community (do not repeat):** host VCN mailbox IDs from other SMU families (`0x8`/`0x9`); PSP as power path; BIOS IFR VCN option; PS5 FW architecture.

**Community open threads (post-power):** diff regs before/after domain6; program clock slots; VCLK move from 0; Renoir/VanGogh `dpm_set_vcn_enable` isolation steps; only then ring test.

---

## 8. Gap vs цель «включить VCN»

| # | Gap | Evidence | Next (не A1) |
|---|---|---|---|
| G1 | Нет skillfish VCN firmware | find empty | direct-load notes / blob hunt — **не** navi symlink |
| G2 | Driver не register VCN IP | no patch; no /dev/video | patch **after** power+clock plan |
| G3 | Нет host PowerUpVcn msg | package + community Ghidra | internal domain-6 only w/ safety |
| G4 | Second gate post-power | community | slots 0x16/17/18 **before** MMIO |
| G5 | Observability | loglevel=0; metrics omits vclk | netconsole + emit vclk/dclk in sampler |
| G6 | SMU mailbox unusable under load | status 0x00 + NRestarts=214 | serialize: pause metrics/watchdog window **(service stop = change, needs OK)** |
| G7 | metrics D-state on gpu_metrics | part8 ps | don't pile concurrent gpu_metrics readers |

---

## 9. Явно не делали (и не надо без OK)

- VCN BAR/MMIO / UMR / ring test  
- SMU writes / domain power  
- firmware install / PSP signature bypass / key extract  
- kernel rebuild  

---

## 10. Рекомендуемый следующий шаг

**A2 safety-plan** (черновик, без применения):

1. Baseline freeze: 38 CU, 2000/1013, VCLK=0/DCLK=1111, netconsole `127.0.0.1:6666`, boot rollback entry.  
2. Hard bans: `pp_dpm_*` unguarded, VCN BAR/MMIO/UMR, concurrent SMU writers, q3 `0x98` without explicit plan.  
3. Done in this follow-up: VCLK/DCLK parse, community README diff, raw_send surface, metrics unit map.  
4. Remaining A1-class only with OK: short **stop** metrics+watchdog window → re-snapshot SMU features (still read-only msgs).  
5. After A2 OK, community order: domain-6 power → clock/reset slots → (optional) driver register/direct-load → ring. **Not** PSP key hunt.

---

## 11. Файлы

- `tmp_bc250/recon/a1_readonly.sh` + `a1_part2..10.sh` / `.out`  
- `tmp_bc250/recon/probe_vcn3.out` — last good SMU snapshot  
- `tmp_bc250/recon/parse_gpu_metrics.py` — offline VCLK/DCLK decode  
- `tmp_bc250/recon/thelamer-bc250-vcn-README.md`  
- Board: `/usr/local/libexec/bc250-metrics.py` (layout source)  
- Upstream: https://github.com/thelamer/bc250-vcn  
