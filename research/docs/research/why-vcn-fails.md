# Почему ~100 BIOS не завели VCN (диагноз 2026-09-24)

Сводка трёх отчётов-исследователей (таблица провалов, стек драйвер/FW/power,
механика DXE-вставки) + прямые проверки писателя. Каждый пункт привязан
к артефакту: sha12 образа, файл, кейс. Непроверенное — в конце.

## 1. Классы причин (с доказательствами)

### K1. LZMA-контейнер unknown-size — дважды (закрыт gate G10)

PEI-декодер отвергает капсулу без явного outsize: DXE не грузится,
диагноз «молчание». D5 `dec17ca8` (bulk-FV, неприписываемо) → D6 `bd7689d6`
(вилка LZMA-vs-код) → D7 `dccd8914` (no-op всё равно молчит) → виноват
контейнер; D8 `e7c8223b` с explicit `0x420010` — BOOT
(`docs/research/uefi-tome/07-bc250-cases.md`, кейсы 1–4).
Тот же провал повторён через 12 дней: v003e `b67e59d7` + v004 `98b9c2bd`
(FLASHED, 1 блинк идентично) — урок жил в прозе, не в gate; preflight 9/9 GO
пропустил. Добавлен gate G10 `lzma_explicit_size`
(`docs/action-logs/2026-09-24-v003b-route-b.md`, `MISTAKES.md` 09-24).

### K2. Клин от доступа в неподаный домен: транспорт/контекст, не значения

Самый массовый класс. D11R–D19: бисекция 56→14→7→3 записей, итог —
`C234←0` и `C830←донор` КАЖДАЯ достаточна для клина SMU (`alive=False`,
`hw_init −62`), при присутствовавшем DFG-гранте → виноват транспорт/контекст
(запись в неподаный остров в RTB), не грант (кейсы 7, 11).
Сюда же: S2-A (59/59 gasket принято, bring-up верифицирован, арбитр
все-единицы — мост не открылся); probe3 (raw SMN-чтение вешает с первого);
dfprobe (read-only insmod → hard hang, ping 100% loss); Q4-batch (wedge,
виновник UNKNOWN); sweep 29 clamp-регистров → hard wedge; v005/v007
(клин в коде драйвера при валидном томе). G6-breach: класс надо было менять
после D14, gasket тянули до D19.

### K3. Пейлоад, не механика: STUB грузится, FULL клинит

Механика вставки доказано работает: STUB (тот же FFS/FV/LZMA, entry заменён
на `33 C0 C3` = xor eax,eax; ret, + PE CheckSum —
`scripts/build_STUB_no_hw_ops_early_slot.py:10-14`) ЗАГРУЖАЕТСЯ в Linux
в обеих позициях: early-slot `0x12940` (v006r `6500bea5`) и appended-at-end
(v007r `0133a34b`). FULL с `DEPEX=TRUE` диспетчер запускает безусловно
в TRUE-пуле до PciBus/GOP/LAN/AGESA, а при entry драйвер сразу делает
запрещённое: raw-чтения SMN `0x0115D560+` через окно `0xB8/0xBC` + десятки
Q3-транзакций со Stall-поллами (`BC250VCNUnlockDxe.c:335,354-359,87-90`).
Итог: FULL виснет и в early-slot (v005 `2fadb173`, 2 блинка), и appended
(v007 `9d249397`, 1 блинк) — позиция не спасает. H19 WINS: код клинит только
против инициализированного SMU. Готовое лечение собрано, не прошито: v008
`c935e3ec` (secure, без сырых чтений), v009 `56df6244` (RTB-дефер, entry
только регистрирует one-shot ReadyToBoot).

### K4. Драйверный слой Linux: пустой case, нет FW, нет power/clock

`amdgpu_discovery.c:~2909`: `case IP_VERSION(2,0,3): break` — пустой,
IP-блок не регистрируется (слой 2 замка). FW обязан грузиться через PSP
(`amdgpu_vcn.c:1347-1359` `psp_execute_ip_fw_load`, `UCODE_ID_VCN0/1_RAM`),
но родного `vcn_2_0_3.bin` не существует (AMD/Sony его не создали;
донор — `renoir_vcn.bin`). Power обязан подниматься (`start_dpg_mode`:
`PG_EN`, `CLK_EN`, снять `SOFT_RESET`), но dom6 `enable=0`, секвенсор
`0x0006D1xx` пишет только SMU, кандидаты Q3 `0x61/0x3C` недоказаны.
Clock загейчен: probe4l4 — все PLL prog/poll readback `0x00000000` при живом
канале `sanity_5a870=0xff` (`evidence/runtime/20260924-001510-probe4l4-pll.json`).
Дифференциал mode1/mode2: mode1 PASS (9 блоков, probe-only), mode2 клин
в `vcn_v2_0_hw_init` без VCN-строк (watchdog CPU4) — клин на первом
HW-доступе VCN (кейс 9).

### K5. Fabric-изоляция двух носителей + hardware-lock

Гаскет `0x24` применяется раньше `TOS_POLICY 0x45` (last-writer-wins), оба
несут kill-значения; фабрик-регистры после записи hardware-lock до холодного
рестарта, хостовые записи дропаются; `DEBUG_UNLOCK 0x13` требует RSA AMD
(`VCN-LOCK-MECHANISM.md` §1, §11). Кросс-таблица Robin↔Cezanne (слой 3):
`0x03E810=0` против 6, DF-окна `0x87FF/0x00000000`, VCN-банк `0x0900Cxxx`
отсутствует целиком. S2-A поверх полного донорского датаплана перехода
не дал — фаворитная модель: PSP лочит матрицы трансляции при
`DRIVER_ENTRIES` (boot-time-only).

### K6. Методологические классы (повторяющиеся)

1. Stale-источник вместо живой проверки: база `af531026` (silent-on-boot)
   для v001; «плата мертва» по 6-дневному коммиту; `read-a` NOT stock;
   «Cezanne» из памяти (`MISTAKES.md` 09-23, третий повтор → скилл
   `board-liveness`).
2. Diff не против той пары: v003c `dafb323a` (zero-blink) сбросил живые
   APCB `0xAB1008..0xAB1B6F` + NVRAM к donor values — diff'али vs donor,
   не vs booted dump.
3. Нарушение одно-переменности: D5 (1.3МБ diff), governor (2 vars), uma8g.
4. Наблюдение без канала: пять no-video 09-11 (включая сток!) — miswiring
   дисплея оператором, все non-discriminating; M6-механизм unresolved;
   mode2 zero journal 23:21–23:50.
5. «Парсится ≠ принимается»: сторонние парсеры vs PEI-декодер; OVMF-load
   vs board-boot.
6. Поздняя смена класса (G6): bulk-FV, gasket до D19 вместо D14.
7. Статика за доказательство: «W9-proven placement» falsified (W9 append
   `@0x3FCE08`, не insert-before-Bds; 8-core datum = W10-era);FurMark-PASS
   с мёртвой нагрузкой.
8. Live-действия без revert: governor enable → hard hang (конкурентные
   SMU-писатели).

## 2. Что закрыто железом (отрицательные результаты — тоже результаты)

- DXE-time gasket: `C234←0`, `C830←донор` — клин SMU, класс закрыт.
- DF/SMN из Linux: запрещены даже read-only (dfprobe, probe3, clamp-sweep);
  OS-зондирование припарковано (D17).
- Bulk-FV / whole-FV graft: E1 закрыл 1.3МБ-переписывание; `af531026`
  (clv+MeiMeiDXEv3+8c+omarchy) — single green blink → только surgical injection.
- V14 Secure-OS body swap: CLOSED-NEGATIVE (14/14 `$PS1` RSA PASS).
- KDB-edit-only: невозможен (anchor `39bfc192` — silicon ROM constant).
- R2 SoC-voltage limitation: proven 52/52. R3 1:1:1: structural negative
  (UCLK делит MEMCLK; OS-путь FCLK/UCLK закрыт).
- M-лесенка 4700S: kill-locus = C0A PSP-регион (M0/M2full/M4/M5/M6 silent,
  T1 BOOT но revert `0x7E5 0x23→0xFF`); APCB-гипотеза disproven (M2full).
- PEI V1: BLOCKED (stock→VCN seg-3 delta = 0, target list EMPTY).
- OC firmware wall ~2200–2230 (путь — governors, не pp_od); voltage NO-GO
  (rail/encoding UNRUN, vdd80 withdrawn).

## 3. Главный подозреваемый сейчас

Fabric-изоляция двух носителей (`0x24`+`0x45`) + отсутствие VCN в SMU PMFW
`88.6.0` (поднять power/clock некому: дескриптор пуст, PLL gated — это
следствие, не причина) + отсутствие подписанного VCN FW. Драйверный слой
обходим (патч пустого case), питание/клок частично трогаем (S2-A), но мост
не открывается ни значениями маршрутизации, ни полным донорским датапланом.
Ближайший эмпирический вопрос — механизм клина v005/v007 (U4): raw reads
vs gasket writes vs race с SMU boot sequencing; v008/v009 staged, не прошиты.

Открытое противоречие: локальный discovery `harvest=0`/HARV пустая (железо
есть) vs simpmix `CC_UVD_HARVESTING=0x3` latch от гаскета — чтение `0x1f81c`
с хоста вешает fabric, сверить нечем без UEFI-Shell зонда.

## 4. План: 3 следующих шага

1. **Прошить staged v008** (secure, без сырых чтений) → вердикт U4; если
   клин — v009 (RTB-дефер). Строго из очереди (имя+sha256, Plane-статус,
   INTENT до записи) — см. скиллы `flash-queue`, `flash-run`.
2. **Канал наблюдения**: J5 UART + TPMS1 POST + таблица кодов из
   `AmdStatusCodeDxe` (`docs/reference/`). Без него запрещены все вердикты
   о молчании (instrument-first, anti-G6); разблокирует U1 (M6-механизм),
   U2 (mode2, первая инструкция), аномалию v007 (1 блинк при валидном томе).
3. **UEFI-Shell живой зонд DF/SMN**: сначала доказать загрузку Shell.efi
   с USB без перешивки (D17-гейт), затем инкрементальная карта
   «адрес → читается/виснет» по одному адресу с логом и холодным циклом
   как штатным исходом. Единственный разрешённый живой путь к DF/SMN.

## 5. Неразрешённое (U1–U13, кратко)

U1 M6-механизм (нет канала); U2 первая инструкция mode2 (только граница
фазы); U3 виновное Q4-сообщение (нужен one-at-a-time перепрогон); U4 клин
v005/v007 (ждут v008/v009); U5 SoC-voltage units/rail (NO-GO); U6 1:1:1
на стоке (negative только на разобранных путях); U7 T1-revert `0x7E5`
(OQ-T1d); U8 ORPHAN/UNKNOWN образы `VERSIONS.md` (U-C2, ~47 без исхода);
U9 атрибуция dfprobe/clamp (dmesg потерян); U10 история W9/W10/W11
(нет manifest W11); U11 PSP entry-absence/root-swap/type44 UNRUN, glitch
ждёт rig; U12 C834-only контроль не делан; U13 reset reason parity error
(стабильность 3900/-35+2200/1015 не доказана).
