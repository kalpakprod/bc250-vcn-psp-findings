# Разгон и тайминги BC-250: механика, носители, патчи

Фаза E. Образцы: сток `BC250_3.00.ROM`, CHIPSETMENU, dump 5.00, моды; извлечение `evidence/fv_extract/`. Инструменты: `tools/apcb/e1_apcb_dump.py`, `tools/uefi/e1_ifr_dump.py`, `tools/uefi/e1_recovery_scan.py`, `tools/uefi/e1_fv_decompress.py`, `tools/uefi/e1_gddr6_table.py`, `tools/uefi/e1_limits_dump.py`.

## TL;DR — ответы на четыре вопроса

1. **Почему нет автоотката при плохих таймингах.** Обучение GDDR6 идёт в PEI (AGESA, `AmdMemAm4Pei`/`AmiAgesaPei`) до запуска DXE/BDS; вся recovery-инфраструктура (`BootFlow`, `LastBoot`, `LastBootFailed`, fail-safe defaults в AMITSE/Bds) живёт в DXE/BDS и до PEI не выполняется. Код-обработчик «тренировка упала → откат NVRAM» в прошивке отсутствует вовсе (строковых и логических следов нет ни в одном модуле). Откат возможен только патчем PEI-обёртки AGESA; «простого» переключателя нет.
2. **Где живут тайминги.** В NVRAM-переменной `AmdSetup` (GUID `3A997502-647A-4C82-998E-52EF9486A247`, размер 0x8B5), смещения 0x316–0x39a; вопросы определены в HII-формсете CBS (`B04535E3-3004-4946-9EB7-149428983053`, модуль CbsSetupDxe); дефолты — NVAR «4 AmdSetup» (2229 байт) + APCB-группы MEMG/DFG/CBSG @0xAB1000.
3. **Что патчится напрямую.** Тайминги — да (байты в AmdSetup; в стоке половина пунктов HIDDEN — снимается правкой IFR/NVRAM). MCLK — да (AmdSetup+0x316, 125–2000 МГц). FCLK/UCLK — косвенно (DF Clock Override 0x704, UclkDiv 0x330..0x333, SMU runtime). Лимиты PPT/TDC/EDC/fast — да, это видимые NUMERIC-поля SMU Debug (0x70c–0x71c) + runtime SMU-mailbox (bc250-smu-oc).
4. **Зашитые лимиты и сток-значения.** Ядро (cyan_skillfish): SCLK 1000–2000 МГц, VDDC 700–1129 мВ; NVRAM-сток: FAST_PPT 88000, SLOW_PPT 65000, VRM_CUR 65000, VRM_MAX 95000, TctlMax 100 °C, CPU 3600 МГц, FCLK 1000 МГц; PMFW содержит фичи-ограничители PPT/TDC/EDC/STAPM/PROCHOT/UMC/DF (битовая карта, `smu_v11_8_pmfw.h`).

## 1. Почему нет автоотката при неудачных таймингах

### Где механизм отсутствует

- Обучение GDDR6 выполняется в PEI: `AmdMemAm4Pei` — тонкая (5 КБ) обёртка APOB, логики повторов/отката не содержит; `AmiAgesaPei` — обёртка AGESA.
- Recovery-механизм AMI живёт в DXE/BDS и срабатывает только ПОСЛЕ успешной инициализации памяти:
  - Bds: переменные `BootFlow`, `LastBoot`, `LastBootFailed`, `BootNext` (UTF-16, район 0xd720 в Bds);
  - AMITSE: `BootNowCount`, `SetUpdateCountVar`, `EvaluateDefaults4FirstBoot`, «Load Fail-Safe Defaults» — последний только вручную (F-клавиша), автоматического триггера нет;
  - `EvaluateDefaults4FirstBoot`/`ConstructDefaults4FirstBoot` выполняются только при первом старте (пустой NVRAM).
- Сканирование всей прошивки (`e1_recovery_scan.py`, `evidence/e1_recovery_scan.txt`): строк «clear CMOS on training fail», watchdog-retry, fallback-по-неудаче-памяти нет нигде — ни в PEI, ни в DXE.
- Итог: неудачная тренировка → сброс/зависание в PEI → следующая загрузка читает те же значения из `AmdSetup` → бесконечный цикл; единственный выход — ручное обнуление CMOS (джампер/батарейка), NVRAM при этом очищается и дефолты восстанавливаются из NVAR-образа.

### Можно ли добавить

- Да, но только патчем PEI (до/вокруг вызова AGESA mem-init): в `CbsBasePei`/`AmdMemAm4Pei` завести счётчик неудач (байт в CMOS/NVAR) и по N-й неудаче записать AmdSetup+0x316..=0xFF (Auto) либо погасить переменную — тогда сработает штатный путь восстановления дефолтов.
- Альтернатива без правки кода — не найдена: runtime-пути нет (машина до загрузки ОС не доходит), BootFlow-переменные в PEI недоступны.
- Сложность высокая: PEI-модули пересобирать/переподписывать; подписная цепочка PSP — см. вердикт фазы C (`docs/08-verification-chain.md`).

## 2. Где физически живут параметры таймингов

### Цепочка носителей

- HII-вопросы (формсет CBS `B04535E3-…`, CbsSetupDxe) → varstore `AmdSetup` (GUID `3A997502-647A-4C82-998E-52EF9486A247`, size 0x8B5).
- Пользовательское значение — байт в NVRAM-переменной `AmdSetup` по смещению вопроса.
- Дефолты: NVAR «4 AmdSetup» (внешние дефолты, 2229 байт) — все тайминги = 0xFF (Auto); плюс копии значений в APCB (группы MEMG 0x1704 / CBSG 0x1707 @0xAB1000) как board-level источник.
- Потребитель: CbsSetupDxe → структуры AGESA/CBS → UMC/PHY.

### Карта смещений AmdSetup (из `evidence/e1_setup_ifr.txt`, формы «I Accept»/«GDDR6 DRAM Timing Configuration»/«DRAM Power Options»)

| Параметр | Смещение | Опции/диапазон | Сток-дефолт | Скрыт |
|---|---|---|---|---|
| Memory Clock Speed (MCLK) | 0x316 | Auto=0xFF; 125–2000 МГц (сток-пункт 1750 МГц = 0x23; макс 2000 = 0x28) | 0xFF (Auto) | нет |
| Tcl | 0x317 | 8–0x21 Clk, Auto | 0xFF | нет |
| Tras | 0x318 | Clk, Auto | 0xFF | нет |
| Trcdrd / Trcdwr | 0x319 / 0x31a | Clk, Auto | 0xFF | нет |
| TrpAb / TrpPb | 0x31b / 0x31c | Clk, Auto | 0xFF | нет |
| TrcAb / TrcPb | 0x31d / 0x31e | Clk, Auto | 0xFF | нет |
| TrrdL / TrrdS | 0x31f / 0x320 | Clk, Auto | 0xFF | нет |
| Trtp / TFaw | 0x321 / 0x322 | Clk, Auto | 0xFF | нет |
| Tref Control / Tref | 0x323 / 0x324 | Manual/Auto; значение | 0 | Tref HIDDEN |
| TrfcPb Control / TrfcPb | 0x326 / 0x327 | Manual/Auto; значение | 0/1 | TrfcPb HIDDEN |
| Trfc Control / Trfc | 0x329 / 0x32a | Manual/Auto; значение | — | HIDDEN |
| BankGroupSwap / Address Hash Bank | 0x32d / 0x32e | Enable/Disable/Auto | — | нет |
| DRAM Timing User Controls (мастер-рубильник) | 0x32f | Auto=0xFF / Manual=1 | 0xFF | нет |
| UclkDiv1M0..M3 (UCLK, mem-pstate 0–3) | 0x330–0x333 | Auto=0xFF / Enabled=1 | 0xFF | HIDDEN |
| Trdwr / Twrrd | 0x334 / 0x335 | 1–0x1F Clk, Auto | 0xFF | HIDDEN |
| TwtrL / TwtrS | 0x336 / 0x337 | Clk, Auto | 0xFF | HIDDEN |
| TwrwrSc/Sd/Dd | 0x338–0x33a | Clk, Auto | 0xFF | HIDDEN |
| TrdrdSc/Sd/Dd | 0x33b–0x33d | Clk, Auto | 0xFF | HIDDEN |
| Tcksrx Control / Tcksrx | 0x33e / 0x33f | Manual/Auto; значение | 0xFF | HIDDEN |
| Tcksre Control / Tcksre | 0x341 / 0x342 | Manual/Auto; значение | 0xFF | HIDDEN |
| Tpd Control / Tpd | 0x343 / 0x344 | Manual/Auto; значение | 0xFF | HIDDEN |
| Cmd2T / Gear Down Mode / Data Scramble | 0x346 / 0x34c / 0x35b | Enable/Disable/Auto | 0xFF | нет |
| Memory P-state | 0x36d | Auto / Enable / Disable | 0xFF | нет |
| VMEMP Voltage Control | 0x37c | Manual/Auto | — | нет |
| APUDFE Training Control | 0x37d | Manual/Auto | — | нет |

Точный список пунктов: `evidence/e1_gddr6_questions.txt` (174 вопроса CBS, включая дерево форм 0x7000–0x7071); границы/дефолты: `evidence/e1_stock_limits.txt`.

### APCB (@0xAB1000, группы из `evidence/e1_apcb_groups.txt`)

- Заголовок группы 0x10 байт; подгруппы {gid u16, inst u16, size u32(incl 8)}; строки токенов 4 байта {u8,u8,u16}.
- 6 групп: UNKN 0x0b07, PSPG 0x1701, DFG 0x1703, MEMG 0x1704, FCHG 0x1706, CBSG 0x1707.
- MEMG 0x1704: конфигурация GDDR6 — таблицы типов токенов (inst 7/8), voltage-strapped строки, частоты (0x6D6 = 1750 = сток-частота GDDR6), тренировочные шаблоны (пары u32, маски 0x5555/0x3FFF/…).
- DFG 0x1703: «дикие карты» доступа — слова 0x001FFF00 по +0x130/+0x16C; во ВСЕХ локальных образах (сток, CHIPSETMENU, 5.00, моды, чип-дамп) тело APCB байт-в-байт одинаково; отличается только CBSG-размер у robin5.00. Вывод: APCB — не канал модов сообщества; правка DFG-масок (0x001FFF00 → 0x007FFF00, checksum-only, без подписи) — самостоятельный, но малоисследованный рычаг (см. D3-пакет `docs/03-d3-patch-status.md`).
- CBSG 0x1707: копия CBS-значений (у robin5.00 раздута до 0x730) — второй кандидат на «где лежат значения».

### Скрытость (HIDDEN)

- В стоке половина пунктов (UclkDiv, Trdwr, Twtr*, Trdrr*, Tcksrx/re, Tpd, Tref, Trfc, TctlMax, VID-offsets, FAST/SLOW_PPT и пр.) закрыта SUPPRESS_IF; CHIPSETMENU-разблокировка — это правка IFR Setup-модуля: REF «GFX Configuration» в форме 0x2713 переведён с внутренней заглушки 0x285b на CBS-форму 0x7005, заглушка удалена, SUPPRESS_IF подправлены (дифф `evidence/e1_setup_ifr_stock_dec.txt` vs `evidence/e1_setup_ifr_chip_dec.txt`, район 0x1175CA, 57 байт).

## 3. Что патчится напрямую (таблица «параметр → носитель → патч»)

| Параметр | Носитель | Как патчить |
|---|---|---|
| Тайминги GDDR6 (Tcl, Tras, Trcd, Trp, Trc, Trrd, Trtp, TFaw, Tref, Trfc, Trdwr/Tw*, UclkDiv…) | байты AmdSetup +0x316–0x39a (NVRAM, GUID 3A997502-…) | (а) unlocked-меню (CHIPSETMENU-патч REF 0x285b→0x7005) и запись через Setup; (б) прямая запись NVRAM (Setup-переменная) или правка NVAR-дефолтов в образе; (в) снять SUPPRESS_IF в IFR (CbsSetupDxe) для скрытых пунктов |
| MCLK (частота GDDR6) | AmdSetup+0x316 | ONE_OF: 125–2000 МГц; патч = значение пункта (0x23=1750 сток, 0x28=2000 макс); или правка опций ONE_OF в IFR для расширения диапазона |
| FCLK | AmdSetup+0x703/0x704 (DF Clock Override; дефолт 1000 МГц) + FCLK_DPM фича 0x6a3 | видимый пункт «DF Clock Override» (Manual → значение); runtime — SMU |
| UCLK | AmdSetup+0x330–0x333 (UclkDiv1M0..M3, HIDDEN) | снять SUPPRESS_IF + Manual; делители на mem-pstate |
| Лимиты PPT/TDC/EDC (fast/slow) | AmdSetup: FAST_PPT_LIMIT +0x70c (u32), SLOW_PPT_LIMIT +0x710, SLOW_PPT_TIME_CONSTANT +0x714, VRM_CURRENT_LIMIT +0x718, VRM_MAXIMUM_CURRENT_LIMIT +0x71c; тумблеры фич: TDC +0x6b9, EDC +0x6bc, PPT +0x6bf, STAPM +0x6c0 (0=off/1=on/0xF=Auto) | ВИДИМЫЕ NUMERIC-поля формы SMU Debug (min=0, max=0xFFFFFFFF) — патчатся прямо из меню после разблокировки входа в CBS; дефолты можно менять в NVAR-образе |
| VDDCR_VDD / VDDCR_GFX offset | AmdSetup+0x6e5/0x6e6 и +0x6ea/0x6eb | Control=Manual → значение; runtime-вариант — SMU VID-offset (0x49/0x4A ±5, 0x4D/0x4E ±200 мВ) |
| TctlMax / PROCHOT | AmdSetup+0x6c3, +0x6cb | HIDDEN NUMERIC; снять SUPPRESS_IF |
| CPU-частота | AmdSetup+0x700/0x701 «Force CPU Frequency» (max 4000) | HIDDEN; Manual → МГц; runtime — SMU per-core OC clk (q3/0x25/0x26) |
| GFX SCLK / VDDC (runtime, без перепрошивки) | SMU-почтовые ящики (MMIO 0x03B10Axx/0x03B105xx), сообщения RequestGfxclk/ForceGfxVid/UnforceGfxVid; ядро cyan_skillfish | Linux: разгон через sysfs (SCLK 1000–2000, VDDC 700–1129 мВ); сообщество (bc250-smu-oc) — расширенный API (см. ниже) |
| APCB-уровень (board-level) | APCB @0xAB1000: DFG-маски, MEMG-таблицы, CBSG-значения | правка слов + пересчёт контрольной суммы APCB (checksum-only, без PSP-подписи) — `tools/apcb/apcb_cks_brute.py` |

Runtime SMU (bc250-smu-oc, очереди 0–4): set CPU/GFX VID q3/0x0F (unforce 0x10); OC-частота по ядрам q3/0x25 (сброс 0x26); max temp q3/0x20 (0–100 °C); VID-offsets q3/0x49/0x4A (±5) и q3/0x4D/0x4E (±0.2 В); scaling f-VID-кривой q3/0x50; clock-stretch коэф. q3/0x52/0x53; enable/disable фич-масок q2/0x05/0x06 (64-бит маска — туда попадают биты PPT=34, TDC=27, EDC=30, STAPM=35, UMC_THROTTLE=23, DF_THROTTLE=24, PROCHOT=21, FCLK_DPM=5, GFX_DPM=6 из `smu_v11_8_pmfw.h`); чтение «power limit settings» q2/0x2C.

## 4. Зашитые лимиты и сток-значения

### Зашито в коде (не в NVRAM)

- Ядро cyan_skillfish (mainline): SCLK 1000–2000 МГц, VDDC 700–1129 мВ, magic VID 0x13FE (unforce); это диапазоны OD-интерфейса ядра, не прошивки.
- PMFW (Cyan Skillfish, v11.8): фичи-ограничители существуют как биты: TDC=27, EDC=30, PPT=34, STAPM=35, FCLK_DPM=5, GFX_DPM=6, SOC_DPM=13, UMC_THROTTLE=23, DF_THROTTLE=24, PROCHOT=21, FP-throttling и др. (`tmp_bc250/upstream/smu_v11_8_pmfw.h`). Числовые значения лимитов лежат в таблицах PMFW (perfprofiletable, SMU q3/0x41 / q3/0x1E), в NVRAM их копии — см. ниже.
- Меню MCLK: максимум 2000 МГц (пункт 0x28) — граница списка ONE_OF в IFR; расширение = правка IFR.

### Сток-значения из NVAR-дефолтов «4 AmdSetup» (`evidence/e1_stock_limits.txt`)

| Лимит | Смещение | Сток-значение | Примечание |
|---|---|---|---|
| FAST_PPT_LIMIT | 0x70c | 88000 (0x157C0) | предположительно мВт = 88 Вт |
| SLOW_PPT_LIMIT | 0x710 | 65000 (0xFDE8) | предположительно мВт = 65 Вт |
| SLOW_PPT_TIME_CONSTANT | 0x714 | 5 | постоянная времени slow-PPT |
| VRM_CURRENT_LIMIT | 0x718 | 65000 | предположительно мА; согласуется с SLOW_PPT (65 А × ~1 В ≈ 65 Вт) |
| VRM_MAXIMUM_CURRENT_LIMIT | 0x71c | 95000 (0x17318) | предположительно мА = 95 А |
| TctlMax_Core / TctlMax_Gfx | 0x6c7 / 0x6c9 | 100 / 100 | °C; TctlMax (0x6c3) = 0 |
| Force CPU Frequency | 0x701 | 3600 (0x0E10) | МГц, дефолт скрытого пункта |
| DF Clock Override (FCLK) | 0x704 | 1000 (0x3E8) | МГц |
| Memory Clock Speed | 0x316 | 0xFF = Auto → 1750 МГц (сток-режим 14 Гбит/с; APCB MEMG содержит 0x6D6=1750) | |
| Все тайминги | 0x316–0x39a | 0xFF = Auto | AGESA сам вычисляет по JEDEC/тренировке |
| Фичи TDC/EDC/PPT/STAPM/FCLK_DPM | 0x6b9/0x6bc/0x6bf/0x6c0/0x6a3 | 0x0F = Auto (включено) | 0=off, 1=on |
| VDDCR offsets | 0x6e6/0x6eb | 0 | |

### Пробелы

- Точные единицы FAST/SLOW_PPT/VRM-лимитов (мВт/мА против внутренних единиц SMU) — не подтверждены дизассемблированием CbsSetupDxe; версия «мВт/мА» согласуется перекрёстно.
- Семантика слов DFG-масок APCB (0x001FFF00) на уровне полей не декодирована.
- Полный дизассемблер-разбор потребления AmdSetup в AGESA (какие смещения реально читает mem-init) не выполнен; карта смещений выведена из IFR (один-к-одному varstore).

## Инструменты и доказательства фазы E

- `tools/apcb/e1_apcb_dump.py` → `evidence/e1_apcb_groups.txt`, `evidence/e1_apcb_diff.txt` — группы/токены APCB, 8-образный дифф.
- `tools/uefi/e1_ifr_dump.py` → `evidence/e1_setup_ifr.txt` (+ строки, + stock/chip диффы) — полный декод HII/IFR CBS.
- `tools/uefi/e1_recovery_scan.py` → `evidence/e1_recovery_scan.txt` — скан recovery-логики.
- `tools/uefi/e1_fv_decompress.py` → `evidence/fv_extract/STOCK_FV.dec`, `CHIPSETMENU_FV.dec` — распаковка LZMA-областей.
- `tools/uefi/e1_gddr6_table.py` → `evidence/e1_gddr6_questions.txt` — дедуп-таблица CBS-вопросов.
- `tools/uefi/e1_limits_dump.py` → `evidence/e1_stock_limits.txt` — границы IFR + сток-значения NVRAM.
- `tools/patch-build/build_oc_profiles.py` → генератор 3 калиброванных версий BIOS (Sync FclkUclk 875, Full Sync 1333/+35mV, Full Sync 1750/+80mV, все с Tcl Auto и CPU сток 3600) в `C:\Users\OWNER\tmp_bc250\recon\oc_profiles`.

