# BC-250 VCN: верная цепочка разблокировки (корневой реверс-отчёт)

Дата: 2026-08-29. Роль: профессиональный RE. Задача: собрать максимальную информацию
и построить ВЕРНЦЕПОЧКУ включения VCN без повторения чужих ошибок и без зависания платы.
Источники: our `vuln-1-gasket-runtime-reprogram.md`, `VCN-ATTACK-PLAN.md`,
`thelamer/bc250-vcn` README, `daveconde/bc250-vcn-enable` (static+README),
внутренняя сессия команды (`empryo-session…md`, ~6760 строк, фаза A1→O3),
локальный RE: bank-diff `bc250_vs_cezanne_sec_gasket_diff.txt`,
`disasm_AmdNbioGfxARIPei.txt`, decoded SEC_GASKET banks.

Приёмка (как в O3/`emprio-session` L537): V2 `UVD_VERSION@0x05C9 != 0xFFFF_FFFF` →
VA-API H.264 decode 1080p60 ×3 0 hang → encode (если IP/fw даёт) → apps (mpv/Jellyfin/FF).
Все шаги обратимы: boot-entry / pacman / service-mask / power-cycle.

---
## 0. Вердикт (TL;DR)
Кремень физически присутствует, harvest=0, питание и клоки включены, микрокод положен в VRAM,
драйверный probe-path собран. **Финальный барьер — апаратный фаервол Data Fabric / NBIF Gasket Clamp**,
зафиксированный PSP на ранней загрузке (DRIVER_ENTRIES → SEC_GASKET Type 0x24) и locked до холодного reset.
Поэтому **все чтения VCN-MMIO дают `0xFFFF_FFFF` (master-abort)** и driver-патчи его не берутся.
Программный runtime-выход есть **только через trusted PSP-контекст** (secure-world exploit или подписанный
debug-token) либо **через модификацию подписанного SEC_GASKET в SPI ROM**. Слепых записей из Linux/SMU/UEFI — нет.

---
## 1. Кому мы обязаны (кто остановился)
- **thelamer/bc250-vcn**: power-domain 6 ВКЛ (`FUN_00023b14(6,1)`); уперлись во «второе врато»
  clock/reset/isolation (слоты `0x16/0x17/0x18` через `FUN_00023744`→`soc_clk_program_slot`); ring=hang.
  ⚠️ их «triple deadlock / dead silicon» устарел: питание уже есть.
- **daveconde/bc250-vcn-enable**: smu-thunk spike; catalog wedge-путей; **не готовый enable**
  (designed no-op, isolation all-ones). Ценность = offset'ы + `--verify`/`--dom6-dump`/`--msg-table` + negative results.
- **Внутренняя сессия команды (emprio)**: полный P0–P9 roadmap; после P4 (fw placed) stuck;
  **финальная цель = runtime trusted transition**; mode1/2 = изолированные probe-ядра (mode1 НЕ анлок, проверено).

Наша плата = их tip по power+clock, но дальше — свой gate: NBIF/Fabric clamp.

---
## 2. Полная цепочка по слоям (gate → статус → доказательство)
```
G0  SMU unlock (Q2 0x23 overflow)        ✅ DONE   0x7B3C=0xFD->0x0; persist; unlock.py
G1  Power Domain 6 ON                    ✅ DONE   FUN_00023b14(6,1); status=0x01010101
G2  Clocks (VCLK/DCLK + slots 16/17/18)  ✅ DONE   VCLK 0->625MHz; DCLK 1111MHz; enable=0x01 READY
G3  VRAM staging + fw (navi10_vcn.bin)   ✅ DONE   fw_size=404544; VCPU BO=1064960; FB 0xf400000000
G4  Driver register path (probe)         ✅ DONE   mode0/mode1 kernels; vcn_v2_0.c patch; /dev/dri up
G5  NBIF/Fabric bridge open              ❌ BLOCKER  см. §3 (hardware firewall lock)
G6  Direct-load + decoder ring smoke      ⬜ NEXT     mmUVD_SCRATCH9: CAFEDEAD->DEADBEEF
G7  VA-API H.264 dec 1080p60 x3           ⬜          -> V2/O1
G8  Encode (H.264, if caps)               ⬜          -> O3
G9  Apps (mpv/Jellyfin/Chromium VAAPI)    ⬜          -> O3 apps
```
`UVD_VERSION@0x05C9` — маркер прохода G5: станет != 0xFFFF_FFFF, только когда мост открыт.

---
## 3. Финальный блокер: WHY 0xFFFF_FFFF (три пути в одну точку)
### 3.1 Что зафиксировано
- `SEC_GASKET` (Type 0x24, body 11344B, ver B.51.0.16) читается PSP из SPI ROM на раннем `DRIVER_ENTRIES`.
  Группы: `0x201` (51 SMN-письмо периф. мостов `0x0900C000..`), `0x280/0x281` (фаервол Data Fabric
  `0x03A2011C..`/`0x09300234..`), `0x210` (binding диапазонов VCN/UVD `0x0003E810..`).
- Применяет → **hardware-lock матрицы трансляции Fabric** до cold reset. Ни SMU, ни x86 CPU не имеют
  прав снять lock-bit во время работы ОС.
- **Robin omit-full VCN bank (HWID 12, `0x0900C000..0x0900CFFF`)**: Cezanne (рабочий сосед) несёт
  51-write VCN-банковку в `0x201` + 0x280-recommit-tail; Robin её не включает.
  Локально: `bc250_vs_cezanne_sec_gasket_diff.txt` (BC 1230 vs CZ 900 writes; 158 diff-регистров;
  в `0x09018934/38` NBIO-адреса `0x13b103f8`/`0x13b10fff` vs `0x13b10400`/`0x13b10bff`).

### 3.2 Почему SMU/Q3 0x98 и 56-write unclamp НЕ открывают мост
- SMU пишет конечные регистры (`0x0900C234: 0->1`), но Data-Fabric фаервол (группа `0x280`) уже от PSP,
  поэтому host-трафик к апертуре VCN `0x02403000` отбрасывается → `0xFFFF_FFFF`.
- PSP C2P-Mailbox API из UEFI (`AmdPspPeiV2`) даёт только `0x01/0x07/0x0B/0x18/0x19`:
  **без** команд динамической перенастройки апертур/сброса фаервола.

### 3.3 Два врата к G5 (путь A/B/C)
1. **Путь A — Live SMN Un-clamp (рекомендуется, без flash BIOS):**
   Reverse NBIF-register гаскета из `AmdNbioGfxARIPei` → запись «на лету» через SMU Q3 **`0x98`**
   (тот же arbitrary-SMN-write примитив, что раскрывал 8 ядер CPU) → проверить `mmUVD_POWER_STATUS`,
   затем direct-load + ring smoke.
   - PEIM подтверждён (disasm 25K instr.): `Init Config Struct 0x23a0-0x2460`,
     `MOV [ECX+0x1e0],0x3` / `MOV [EDX+0x1e1],0x3` (GPU-порты = `0x07` Full-Enabled);
     сериализация `0x7340-0x7380` → APCB-токены **`0x10c2` NBIF_VCN_PORT_CONFIG** /
     **`0x10c3` NBIF_VCN_BRIDGE_ENABLE**. Значение `0x03` = Port-Disconnected / Clamped.
   -candidates NBIO-регистров (early AmdNbioGfxInit через helpers 0x72d/0x75b/0x6a3):
     `0x13b1005c`, `0x13b10060`, `0x13b00084`, `0x13b0004c`.
   - ⚠️ команда в emprio сначала назвала `0x10c2/0x10c3` регистрами, потом **отклонила** (это AGESA
     IDS NV ID из `$INV`): значит точные регистры NBIF всё ещё **нужно доказать**, а не верить на слово.
2. **Путь B — DXE-модуль в BIOS** (по аналогии с `BC250-DXE-SMU-Core-Unlock`): снять NBIF изоляцию
   до старта Linux ядра.
3. **Путь C — Kernel Patch `amdgpu`** (`cyan_skillfish_ppt.c`/`vcn_v2_0.c`): встроить инициализацию VCN;
   только после G5; guard — не вешаться на пустой `dpm_set_vcn_enable`.

### 3.3.1 Альтернатива без flash BIOS = trusted PSP-контекст
- **`DEBUG_UNLOCK` Type 0x13**: протокол `Svc_GetDebugUnlockInfo → UnlockNegotiation → SecureUnlock`,
  одноразовый челлендж, проверка токена по `SEC_DBG_PUBLIC_KEY~0x9` (RSA-2048, kid **6c5f…**),
  закрытый ключ AMD → токен нельзя воспроизвести/подделать.
- Итого: **для штатного устойчивого анлока, вероятнее всего, нужна модификация подписанного
  SEC_GASKET в SPI ROM** (добавить HWID-12 VCN bank), иначе — secure-world exploit или подписанный
  debug-token (рабочего пути пока нет).

---
## 4. Наша классификация уязвостей (VULN-A/B/C) в контексте сообщества
- **VULN-A** = SMU unlock (Q2 `0x23` ring-overflow). Фундамент всего; transport = PCI config
  `0xB8`/`0xBC`, root-only; safe-очереди Q2 `0x03B10528..` и Q3 `0x03B10A20..` (OC-tool uses them).
  = thelamer/daveconde `unlock()` + emprio «domain6 persist after UEFI chainload».
- **VULN-B** = runtime reprogram SEC_GASKET через Q3 `0x98` (register-space). Работает на уровне
  SMN (56 писем приняты + readback), **но не открывает Fabric-мост** (см. §3.2). Это и есть
  «второе врато» сообщества на уровне bridge.
- **VULN-C** = native-domain6 bring-up (`enable_vcn.py`, 204 KB): 20B секвенция → SRAM `0x3ff00`,
  repoint msg-`0x61` @`0x776c`, `call8 0x00023744` ×3 слоты `0x16/17/18` (`soc_clk_program_slot @0x2362c`)
  → `--direct-load` (navi10_vcn в VRAM, ring-test `mmUVD_SCRATCH9` CAFEDEAD→DEADBEEF, doorbell BAR2).

## 5. Главная причина наших зависаний (чтобы НЕ повторить)
**Читать VCN-MMIO (`rd()`), пока домен power-gated / мост зажат = bus-wedge.**
Сегодня `full` gasket-replay повесил плату: netconsole живы до ~04:02, последняя строка
`usb 7-2: USB disconnect`, тишина; ping 100%, SSH No-route. Recover = **manual power-cycle**
(cmdline `nowatchdog`, reboot-скрипт для работы needs SSH).
**FIX (WRITE-FIRST):** включить домен (unlock→install→fire msg `0x61`→engage) → ТОЛЬКО потом MMIO-read.
`--verify` = safe read-only first contact.

## 6. Безопасный порядок следующих шагов (для продолжения с платы)
```
S1  --verify        (read-only dom6/slot state; safe first contact)
S2  --no-fire       (unlock + install + repoint; disarm on exit)
S3  fire            (msg 0x61 -> domain6 clock; NOT the blocker fix)
S4  Live SMN un-clamp  ← ГЛАВНЫЙ ХОД (Путь A)
    - read-only: снять значения NBIO-регистров `0x13b1005c/.60`/`0x13b00084/.4c` и
      APCB `0x10c2/0x10c3` (включая проверку, что это IDS-NV-ID, как emprio отклонили);
    - ОДНА обратимая bit-write (bit-write + readback);
    - проверить `mmUVD_POWER_STATUS`: уйти с 0xFFFF_FFFF;
S5  --direct-load   (ring smoke CAFEDEAD->DEADBEEF)
S6  vainfo/amdgpu_pm_info (V3/V5); cold-reboot reproducibility (V6)
```
Хранится/развёртывается через `recon/vcn_safe_run.sh`, `vcn_watch.sh`, `vcn_deploy.sh`, `VCN-START-SAFE.md`.

## 7. Что уже локально (артефакты для продолжения)
- `robin3_uefi/` (BIOS.bin, dump, guids, AmdNbioGfxARIPei), `robin3_psp_bodies/` (SEC_GASKET,
  DEBUG_UNLOCK, ABL1-4, DRIVER_ENTRIES), `disasm_*`, `bc250_smu/`, `upstream/{bc250-smu-unlock,daveconde-bc250-vcn-enable}`.
- `recon/VCN-ATTACK-PLAN.md`, `vuln-1-gasket-runtime-reprogram.md`, `specs/` (12 файлов roadmap).

## 8. Open questions (куда копать дальше)
- Точно ли NBIO-регистры = `0x13b1005c/.60`/`0x13b00084/.4c`, или `0x1e0/0x1e1`→`0x10c2/0x10c3`?
  (нужно read-only + reversible write, как в S4).
- Есть ли у Robin отдельный Fabric-«bridge-enable» регистр vs Cezanne (diff показывает расхождения)?
- Подписанный debug-token / secure-world exploit для `DEBUG_UNLOCK` (Type 0x13) — единственный
  non-flash путь; рабочего PoC нет.
