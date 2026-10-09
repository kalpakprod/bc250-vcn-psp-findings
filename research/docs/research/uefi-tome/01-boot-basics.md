# Глава 01. Основы загрузки: SPI flash, программаторы, карта 16 МБ BC250, reset vector, BIOS vs UEFI

> Статус: рабочий черновик. Правило главы: любое утверждение либо подкреплено
> открытой ссылкой из раздела «Источники» (каждая ссылка открыта и проверена
> автором главы), либо файлом evidence проекта, либо явно вынесено в раздел
> «Открытые вопросы». Выдумки запрещены.

## 0. Как читать главу и как проверять утверждения

Глава покрывает самый нижний слой platform bring-up: микросхему SPI NOR flash,
внешнее чтение программатором (CH341A/CH347), побайтовую карту эталонного дампа
BC250 размером 16 МиБ, точку входа процессора после RESET (reset vector) и
разницу Legacy BIOS/CSM и native UEFI — с привязкой к конкретным смещениям дампа.

Принятые обозначения:

- `dump/2.bin` — эталонный операторский дамп BC250, 16777216 байт,
  SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`
  (зафиксировано в `docs/action-logs/2026-09-10-programmer-preflight.md`).
- Все смещения — в байтах от начала SPI-файла, hex.
- `PA(X)` — физический адрес при отображении flash в верх 4 ГБ:
  `PA(X) = 0x100000000 − 0x1000000 + X = 0xFF000000 + X` для 16-МиБ чипа.

Минимальный набор для воспроизведения: Linux-хост, `flashrom 1.8.0`,
`sha256sum`, `cmp`, `xxd`, `dd`, `python3`, скрипты `scripts/firmware_audit.py`
и `scripts/nvar_audit.py` из корня проекта.

## 1. SPI flash: протокол

### 1.1. Сигналы и топология шины

SPI NOR flash 25-й серии (корпус SOIC-8) — 8 выводов. Логические сигналы:

| Сигнал | Направление (со стороны flash) | Назначение |
|---|---|---|
| `/CS` (chip select) | вход | выбор кристалла, активный низкий; каждый пакет начинается с falling edge |
| `CLK` (SCLK) | вход | такты; данные стробируются по фронту (режим 0/3) |
| `DI` / `MOSI` / `IO0` | вход | данные master → flash (команда, адрес, полезная нагрузка записи) |
| `DO` / `MISO` / `IO1` | выход | данные flash → master (статус, JEDEC ID, читаемые данные) |
| `/WP` / `IO2` | вход | защита от записи (в single-SPI); старший бит в quad-режиме |
| `/HOLD` (или `/RESET`) / `IO3` | вход | пауза транзакции (в single-SPI); старший бит в quad-режиме |
| `VCC` | питание | 2.7–3.6 В для W25Q128 (см. п. 1.2) |
| `GND` | земля | общий провод |

Шина shared: в штатном режиме мастером является SoC/PCH через встроенный
SPI-контроллер (аппаратный sequencer + memory-mapped окно чтения), вне штатного
режима мастером становится внешний программатор. Два мастера одновременно
недопустимы — отсюда жёсткое требование полностью обесточить плату перед
подключением прищепки (п. 2.2).

### 1.2. SOIC-8 распиновка W25Q128 и питание

Распиновка W25Q128 (нумерация против часовой от ключа/точки pin 1),
по datasheet Winbond (PDF открыт и проверен, см. Источники):

| Pin | Имя | Pin | Имя |
|---|---|---|---|
| 1 | `/CS` | 8 | `VCC` |
| 2 | `DO` (`IO1`) | 7 | `/HOLD` (`IO3`) |
| 3 | `/WP` (`IO2`) | 6 | `CLK` |
| 4 | `GND` | 5 | `DI` (`IO0`) |

Питание: диапазон 2.7–3.6 В (запись `W25Q128.V` в `flashchips/winbond.c`
pinned-исходника flashrom v1.8.0; профиль IMSProg оператора: `3.3 V`).
Страница программирования 256 байт, стирание секторами 4 КБ / блоками
32/64 КБ — те же значения показывает скриншот выбора чипа
(`page 256 / block 64 K`). 4-байтная адресация для 16-МиБ кристалла
не нужна (`4byte No`): 24-битного адреса хватает ровно на 16 МиБ.

### 1.3. Опкоды: минимальный рабочий набор

Формат транзакции: `/CS` вниз → 1 байт команды → адрес/данные → `/CS` вверх.
Таблица стандартных опкодов SPI NOR (сверка — раздел Instruction Set
datasheet W25Q128JV и исходник `flashchips/winbond.c`):

| Опкод | Мнемоника | Назначение |
|---|---|---|
| `0x06` | WREN | Write Enable, взводит бит WEL; обязателен перед Program/Erase/WRSR |
| `0x04` | WRDI | Write Disable, сбрасывает WEL |
| `0x05` | RDSR1 | чтение Status Register 1 |
| `0x35` | RDSR2 | чтение Status Register 2 |
| `0x01` | WRSR | запись Status Register 1 (+2) |
| `0x03` | READ | чтение данных, 24-битный адрес, без dummy-циклов |
| `0x0B` | Fast Read | чтение с dummy-байтом, выше допустимая частота CLK |
| `0x02` | Page Program | запись до 256 байт в пределах одной страницы |
| `0x20` | Sector Erase | стирание сектора 4 КБ (в `0xFF`) |
| `0x52` | Block Erase | стирание блока 32 КБ |
| `0xD8` | Block Erase | стирание блока 64 КБ |
| `0xC7` / `0x60` | Chip Erase | стирание всего кристалла |
| `0x9F` | RDID (JEDEC ID) | чтение 3-байтного идентификатора |
| `0x90` | REMS | чтение Manufacturer/Device ID (legacy) |
| `0xAB` / `0xB9` | Release Power-down / Deep Power-down | управление питанием |

Правило проекта: в рамках данной главы и всех текущих работ разрешён
только путь чтения (`READ`/`Fast Read`/`RDID` через `flashrom -r`).
Опкоды стирания/записи приведены для понимания протокола и распознавания
чужих логов, выполнять их запрещено действующими гейтами (см. п. 2.2).

### 1.4. JEDEC ID (RDID): разбор ответа `EF 40 18`

Ответ на `0x9F` — 3 байта:

- Byte 0 — Manufacturer ID: `0xEF` = Winbond.
- Byte 1 — Memory Type: `0x40` (семейство SPI NOR).
- Byte 2 — Capacity code: `0x18` = 24 → ёмкость `2^24` байт = 16 МиБ.

Именно `EF 40 18` ожидался по pinned-базе flashrom, и probe проекта
(`flashrom -p ch347_spi:spispeed=1.875M`) нашёл чип `Winbond W25Q128.V`
(`16384 kB, SPI`) — зафиксировано в
`docs/research/2026-09-11-programmer-cli-evaluation.md` и в action log
preflight. Любой другой ID при повторных чтениях — стоп-условие
(не тот чип, плохой контакт прищепки, неверная ориентация).

### 1.5. Защита от записи: Status Register

Status Register 1 (младший байт, читается `0x05`), типовой состав:

- `S0 BUSY` — идёт Program/Erase/Write, остальные команды игнорируются;
- `S1 WEL` — Write Enable Latch, взводится `WREN`, сбрасывается после операции;
- `S2–S4 BP0–BP2` — Block Protect: задают размер защищённой от записи области;
- `S5 TB` — Top/Bottom: защищённая область считается сверху или снизу;
- `S6 SEC` — защита в единицах секторов 4 КБ (если поддержан);
- `S7 SRP0` — Status Register Protect (совместно с `/WP` даёт hardware lock).

Практический вывод: битовая карта защиты читается, а не угадывается —
`flashrom` показывает её при probe/verbose. Любые операции, меняющие
статус-регистры, в проекте запрещены до отдельного аппрува.

## 2. Подключение программаторов: CH341A и CH347

### 2.1. CH341A: дешёвый маршрут и его ловушки

CH341A — USB-мост WCH (UART/SPI/I2C), массовые чёрные/зелёные платы
с ZIF-панелью. В flashrom поддерживается бэкендом `ch341a_spi`
(задокументирован в man-странице flashrom и на странице поддерживаемых
программаторов — обе открыты, см. Источники).

Базовая разводка «плата CH341A → SOIC-8 flash» (имена со стороны flash, п. 1.2):

| SOIC-8 pin | Сигнал flash | Куда на программаторе |
|---|---|---|
| 1 | `/CS` | `CS` |
| 2 | `DO`/`MISO` | `MISO` |
| 5 | `DI`/`MOSI` | `MOSI` |
| 6 | `CLK` | `CLK`/`SCK` |
| 8 | `VCC` | `3.3V` (только!) |
| 4 | `GND` | `GND` |
| 3 `/WP`, 7 `/HOLD` | подтяжка | к `VCC 3.3V` (на многих переходниках/прищепках уже разведено) |

Подключение к запаянному чипу — прищепкой SOIC-8 (Pomona-стиль) с короткими
проводами; альтернатива — выпаивание чипа в панель программатора
(надёжнее электрически, но с риском повредить плату).

Известная проблема части дешёвых плат: при заявленных 3.3 В на сигнальных
линиях фактически 5 В (питание CH341A от 5 В USB без сдвига уровней).
Правило: перед первым касанием платы проверить мультиметром уровни `VCC`
и `MOSI`/`CLK`/`CS` относительно `GND`; при 5 В — доработать плату
(мод 3.3 В) или не использовать её. Утверждение о конкретной ревизии платы
оператора не проверено и вынесено в Открытые вопросы; боевой маршрут
проекта — CH347T (п. 2.2), а не CH341A.

Типовая read-only сессия (после всех проверок питания и ориентации pin 1):

```sh
flashrom -p ch341a_spi
flashrom -p ch341a_spi -r read-a.bin
flashrom -p ch341a_spi -r read-b.bin
sha256sum read-a.bin read-b.bin && cmp read-a.bin read-b.bin
```

Первая команда без `-r`/`-w` — только probe (опрос JEDEC ID).
Два чтения в разные файлы + сравнение — обязательный минимум:
расхождение означает плохой контакт, а не «вариант прошивки».

### 2.2. CH347T: боевой маршрут проекта BC250

Аппарат: WCH CH347 (вариант T), USB VID:PID `1a86:55db`
(`QinHeng Electronics USB To UART+SPI+I2C`), на хосте виден как
`/dev/ttyACM0`. Вендорский репозиторий WCH (открыт, см. Источники)
документирует для семейства CH347 режимы SPI и JTAG-master;
важно: факт USB-идентификатора и рабочей SPI-операции ничего не говорит
о разводке JTAG на конкретной плате программатора и о допустимых 1.8 В —
подробности в `docs/research/2026-09-11-ch347-jtag-bc250.md`.

Софт: `flashrom 1.8.0` с нативным бэкендом `ch347_spi`
(проверен pinned-исходник по коммиту `90b6b4376c7480a223e7bb5642e7116315ac6d09`:
SPI interface 2, endpoints `0x06/0x86`, 4-байтный SPI, скорости
`60M/30M/15M/7.5M/3.75M/1.875M/937.5K/468.75K`, default 15 МГц).
Проект использует консервативные 1.875 МГц для прищепки в цепи.

Точные команды проекта (read-only, выполнены с результатом, см. action log
preflight и `docs/research/2026-09-11-programmer-cli-evaluation.md`):

```sh
flashrom -p ch347_spi:spispeed=1.875M
flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-a.bin
flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-b.bin
```

Предусловия (все зафиксированы как выполненные): плата полностью
обесточена (нет `+3.3V_SB`), батарея BIOS снята, подключён только CH347T,
ориентация pin 1 проверена. Результат: probe нашёл `Winbond W25Q128.V`
(`16384 kB`); оба чтения завершились с exit 0, размер 16777216 байт,
побайтово идентичны друг другу и `dump/2.bin`
(SHA-256 `83c4e420…f8ee0`).

GUI-фолбэк: IMSProg 1.9.1 (Qt, synopsis только `IMSProg`, CLI-операций
чтения/Detect нет — проверено по man-странице и исходнику `main.cpp`
в рамках evaluation). Профиль выбора чипа: `SPI_FLASH / WINBOND /
W25Q128BV / 16 M / page 256 / block 64 K / 3.3 V / 4byte No`.
Статус решения: IMSProg — `KEEP` как ручной фолбэк, flashrom — `ADOPT`
для read-only маршрута с pinned-бинарником.

Категорически запрещено в первом и текущих заходах: `flashrom -w`,
любые erase-опции, изменение status-регистров и write-protection,
режим `Auto` в GUI. Запись — только по отдельной per-image/per-board
процедуре с явным аппрувом (runbook
`docs/runbooks/2026-09-11-bc250-programmer-and-candidate-gates.md`
в родительской копии).

### 2.3. Стоп-условия прищепного чтения

Остановиться и чинить контакт/питание/выбор чипа (а не «читать дальше»):

- нестабильный или неожиданный JEDEC ID (не `EF 40 18` для W25Q128);
- два чтения расходятся хотя бы в одном байте;
- ошибки USB/claim интерфейса, обрывы на середине чтения;
- нагрев чипа/прищепки, запах — немедленно снять питание;
- любое сомнение, что плата обесточена (светодиоды standby, вентиляторы).

## 3. Карта 16 МБ BC250 (по evidence проекта)

### 3.1. Эталон и его хэш

`dump/2.bin`: 16777216 байт (ровно `0x1000000`),
SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
Два свежих чтения через CH347T (`read-a.bin`, `read-b.bin`) побайтово
совпали с ним (`cmp` exit 0 в обе стороны). Парсер `firmware_audit.py`
на свежих чтениях: PSP 19 entries/checksum match, BHD 4 entries/checksum
match, APCB size `0xB70`/checksum match, 4 firmware volumes, 234 модуля
на экстракции — `234/234` имён и хэшей равны с разбором `dump/2.bin`.

### 3.2. Таблица регионов

Смещения — от начала SPI-файла. Источник каждой строки — action log
preflight (наблюдённые байты) и указанные отчёты.

| Смещение | Размер / структура | Что лежит |
|---|---|---|
| `0x000000` | `0x10000` (первые 64 КБ) | NVAR store: 683 записи; `AmdSetup` rel `0x4BB`, body `0x8B5`, body SHA-256 `6f266c3c…d055`; три хвостовых warning `unterminated NVAR name` (воспроизводятся на всех чтениях) |
| `0x0007E5` | 1 байт | `AmdSetup+0x316` = `MemoryClockSpeed` (`FF`=Auto в стоке; IFR-опция `0x23`=1750 МГц — см. memory-кандидат в preflight) |
| `0x8E0000` | `$PSP` directory | 19 entries; Fletcher32 `0x63FFFCC8` сошёлся |
| `0x981A00` | `0x450` байт | IPDS hardware-IP-config: declared `0x44C`, IPDS v2, 1 die, 38 IP-записей; VCN: HWID 12, v2.0.3, harvest 0, bases `0x7800/0x7E00/0x02403000` |
| `0x982000` | `$PS1` gasket metadata | total `0x2E50`, 5 групп (`0x201/0x203/0x210/0x280/0x281`) |
| `0x9CA400` | `$PS1` policy metadata | total `0x6E0`, 4 группы (`0x210/0x211/0x280/0x281`) |
| `0xAB0000` | `$BHD` directory | 4 entries; Fletcher32 `0xECE7B2E6` сошёлся |
| `0xAB1000` | APCB `0xB70` | checksum-байт `@+0x10` (`0xF2` в стоке); DFG-слова `@+0x130` и `@+0x16C` (`00 FF 1F 00` = LE `0x001FFF00` в стоке) |
| (по всему файлу) | 4 шт. | Firmware Volumes (`_FVH`), детали форматов — глава 02 |
| `0xFFFFF0` | 16 байт | reset vector (конец файла = `0xFFFFFFFF`), см. раздел 4 |

ASCII-схема (масштаб условный, порядок и смещения точные):

```text
0x000000 +------------------ NVAR store (64K, AmdSetup@rel 0x4BB)
         |  ... FV/данные (границы — в inventory.json, см. Открытые вопросы)
0x8E0000 +------------------ $PSP directory (19 entries)
0x981A00 +-- IPDS hw-ip-config (0x450) / $PS1 gasket @0x982000
0x9CA400 +------------------ $PS1 policy (0x6E0)
0xAB0000 +------------------ $BHD (4 entries) + APCB @0xAB1000 (0xB70)
         |  ... FV/данные
0xFFFFF0 +------------------ Reset Vector (16 байт) → PA 0xFFFFFFF0
0x1000000 (конец файла = PA 0xFFFFFFFF)
```

### 3.3. Точечные правки как примеры (значения из evidence)

- APCB DFG-кандидат: `@+0x130` и `@+0x16C`: `00 FF 1F 00` → `00 FF 7F 00`,
  checksum `@+0x10`: `0xF2` → `0x32`; всего 3 изменённых байта
  (`0xAB1010`, `0xAB1132`, `0xAB116E`). Арифметика checksum — упражнение 4.
- MemoryClock-кандидат: `0x7E5`: `FF` → `0x23`; ровно 1 изменённый байт,
  NVAR-контрольных сумм эта правка не затрагивает (по отчёту валидации).

### 3.4. Чем смотреть дамп (только чтение)

```sh
xxd -s 0xFFFFF0 -l 16 dump/2.bin        # reset vector
xxd -s 0xAB1000 -l 32 dump/2.bin        # заголовок APCB
dd if=dump/2.bin of=/tmp/apcb.bin bs=1 skip=$((0xAB1000)) count=$((0xB70))
python3 scripts/firmware_audit.py dump/2.bin --output /tmp/inventory.json
python3 scripts/nvar_audit.py dump/2.bin --output /tmp/nvar.json \
  --store-offset 0x0 --store-length 0x10000 --variable AmdSetup
```

`--store-offset/--store-length/--variable` — по фактическому вызову из preflight.
Сторонние просмотрщики FV/FFS (UEFITool, uefi-firmware-parser) — рабочий
инструмент для главы 02; pinned-версии в проекте не зафиксированы
(см. Открытые вопросы).

## 4. Reset vector: первая инструкция процессора

### 4.1. Аппаратный факт

После снятия RESET x86-процессор стартует в 16-битном real mode
со скрытой базой `CS = 0xFFFF0000` и `IP = 0xFFF0`, то есть первая
инструкция выбирается по физическому адресу `0xFFFFFFF0` — за 16 байт
до верха 32-битного адресного пространства (`4G − 16`).
Доступных байт всего 16, поэтому там обычно лежит ближний/дальний `jmp`
в настоящую точку входа SEC (фаза SEC — глава 02).

SPI-контроллер чипсета отображает flash в память (memory-mapped,
через hardware sequencer): конец 16-МиБ файла проецируется на
`0xFFFFFFFF`, а смещение файла `0xFFFFF0` — ровно на `0xFFFFFFF0`
(формула `PA(X)` из раздела 0).

### 4.2. VTF: как это выглядит в прошивке EDK2

Проверено чтением исходника EDK2 `UefiCpuPkg/ResetVector/Vtf0/Ia16/ResetVectorVtf0.nasm.inc`
(шапка: «First code executed by processor after resetting»):

- файл собирается так, чтобы лежать «just below `0x100000000` (4GB)» —
  конец образа (метка `fourGigabytes`) совпадает с верхом 4 ГБ;
- по `0xFFFFFFEC` — сигнатура VTF: байты `'V','T','F',0`
  (`vtfSignature`; VTF-0 = Volume Top File без fixup'ов);
- по `0xFFFFFFF0` (`resetVector`) — «This is where the processor
  will begin execution»: `nop; nop; jmp EarlyBspInitReal16`.

Сборка: модуль `UefiCpuPkg/ResetVector/Vtf0/Vtf0.inf`
(`FILE_GUID 1BA0062E-C779-4582-8566-336AE8F78F09`, проверено чтением
`.inf`) подключается в FDF правилом `[Rule.Common.SEC.RESET_VECTOR]`
как `FILE RAW`. Сам VTF — последний файл последнего FV образа.

Практический вывод для реверса: конец любого UEFI-образа ищите так —
`xxd -s 0xFFFFF0 -l 16` покажет `jmp` на SEC; строкой `VTF` по
`0xFFFFFFEC` можно якорить разбор хвоста дампа.

AMD-оговорка: на AMD-платформах (включая BC250) до/вокруг x86-старта
работает PSP (см. `$PSP`-регион в п. 3.2). Точный порядок
«PSP-first vs x86-first» для BC250 в проекте не подтверждён —
см. Открытые вопросы; раздел выше описывает x86-часть, общую для
платформ UEFI PI.

## 5. Legacy BIOS и UEFI, CSM — с привязкой к дампам

### 5.1. Legacy BIOS: как грузились раньше

Классический путь: POST → `INT 0x19` (bootstrap) → первый сектор
загрузочного диска по `0x7C00`, сигнатура `0x55AA` в последних двух
байтах сектора → передача управления. Видео и диски — через 16-битные
Option ROM (`0xC0000…`, сигнатура `0x55AA`, заголовок с длиной и entry
`INIT`). Всё в real mode, жёсткие ограничения (MBR ≤ 2 ТиБ на диск,
нет драйверной модели, нет namespaces).

### 5.2. Native UEFI: как грузятся сейчас

- Boot manager читает NVRAM-переменные `Boot####` + `BootOrder`;
- fallback — `\EFI\BOOT\BOOTX64.EFI` на ESP (FAT32-раздел);
- образы — PE32+ (или TE), выполняются с Boot Services
  (`HandleProtocol`, `LoadImage`, `StartImage`);
- Secure Boot (базы `PK/KEK/db/dbx`, проверка подписей) — отдельная тема,
  в этой главе только фиксируем, что цепочка начинается с SEC/PEI,
  а не с MBR.

### 5.3. CSM: мост между мирами

Compatibility Support Module — UEFI-драйвер, эмулирующий Legacy:
`INT 19h/13h`, BDA/EBDA, теневые Option ROM, запуск MBR/`0x7C00`.
Признаки CSM в дампе (проверяемые, без гаданий):

- FFS-секция типа `EFI_SECTION_COMPATIBILITY16 = 0x16`
  (значение подтверждено чтением `MdePkg/Include/Pi/PiFirmwareFile.h`,
  см. главу 02);
- 16-битный код и строки вида `Compatibility16`, `LegacyBIOS`,
  `CsmVideo`, `INT19`, `0x7C00` в `strings`-выводе;
- в project-парсере — тип секции `0x16` в отчёте по файлам FV.

SeaBIOS и coreboot-payload'ы — альтернативные реализации legacy-пути
вне EDK2-экосистемы; упоминаются для ориентировки, в дампе BC250
их наличие не проверялось (см. Открытые вопросы).

### 5.4. Что смотреть в дампах: сводная процедура

Для `dump/2.bin` (и любого SPI-дампа UEFI-платы), только чтение:

```sh
# 1. Хвост: reset vector
xxd -s 0xFFFFF0 -l 16 dump/2.bin
# 2. Головы FV (в BC250 их 4 — найти все вхождения)
grep -aob '_FVH' dump/2.bin
# 3. Legacy-признаки (ожидание для чистой UEFI-платы: пусто)
grep -aob -E 'Compatibility16|LegacyBIOS|CsmVideo|SeaBIOS' dump/2.bin | head
# 4. MBR-сигнатура 0x55AA в конце секторов 512 Б (поиск-грубо)
python3 -c "
data = open('dump/2.bin','rb').read()
hits = [hex(o) for o in range(0, len(data), 512)
        if data[o+510:o+512] == b'\x55\xaa']
print(len(hits), 'sectors end with 55AA:', hits[:10])"
# 5. Структурный разбор проектным парсером
python3 scripts/firmware_audit.py dump/2.bin --output /tmp/inventory.json
```

Интерпретация: `jmp` в хвосте + `_FVH` + отсутствие legacy-строк =
типичная native-UEFI картина. Любой `Compatibility16` — повод открывать
главу 02 и разбирать FFS-файл целиком.

## 6. Практикум: эталонная read-only сессия целиком

```sh
# 0. Плата обесточена, батарея снята, pin 1 сверен, подключён только CH347T
flashrom --version                       # ожидаем v1.8.0 (pinned)
flashrom -p ch347_spi:spispeed=1.875M    # probe: ждём W25Q128.V 16384 kB
# 1. Два независимых чтения
flashrom -p ch347_spi:spispeed=1.875M -r read-a.bin
flashrom -p ch347_spi:spispeed=1.875M -r read-b.bin
# 2. Сверка
sha256sum read-a.bin read-b.bin
cmp read-a.bin read-b.bin && echo IDENTICAL
cmp read-a.bin dump/2.bin && echo MATCHES-GOLDEN
# 3. Структурные проверки каждого чтения отдельно
python3 scripts/firmware_audit.py read-a.bin --output /tmp/a.json
python3 scripts/firmware_audit.py read-b.bin --output /tmp/b.json
# 4. Быстрый осмотр ключевых точек
xxd -s 0x8E0000 -l 16 read-a.bin         # $PSP
xxd -s 0xAB0000 -l 16 read-a.bin         # $BHD
xxd -s 0xAB1000 -l 32 read-a.bin         # APCB
xxd -s 0xFFFFF0 -l 16 read-a.bin         # reset vector
```

## 7. Упражнения с ответами

### Упражнение 1. Разбор JEDEC ID

Probe вернул `EF 40 18`. Определите производителя, тип памяти и ёмкость
кристалла в мегабайтах. Покажите расчёт.

<details><summary>Ответ</summary>

- `0xEF` — Manufacturer ID = Winbond;
- `0x40` — Memory Type (семейство SPI NOR);
- `0x18` = 24 — Capacity code: ёмкость `2^24` байт = 16777216 байт = 16 МиБ.
- Вывод: Winbond 128-Мбит (16-МиБайт) SPI NOR, соответствует `W25Q128*`.
  Проверка в проекте: `flashrom` опознал чип как `W25Q128.V (16384 kB)`.
</details>

### Упражнение 2. Смещение reset vector в файле

SPI-дамп ровно 16 МиБ (`0x1000000` байт). По какому файловому смещению
лежит первый байт reset vector и какому физическому адресу он
соответствует при top-of-4G mapping?

<details><summary>Ответ</summary>

- Reset vector — последние 16 байт образа: `0x1000000 − 0x10 = 0xFFFFF0`.
- Команда: `xxd -s 0xFFFFF0 -l 16 dump/2.bin`.
- Физический адрес: `PA(0xFFFFF0) = 0xFF000000 + 0xFFFFF0 = 0xFFFFFFF0`.
- Контроль: конец файла `0x1000000` (exclusive) соответствует `0xFFFFFFFF`.
</details>

### Упражнение 3. Прозвонка прищепки CH341A

Вы подключаете прищепку к запаянному W25Q128. Перечислите 6 обязательных
соединений (pin SOIC-8 → сигнал программатора) и два дополнительных
условия по `/WP` и `/HOLD`. Что измеряете мультиметром до подключения?

<details><summary>Ответ</summary>

- 1 `/CS` → `CS`; 2 `DO` → `MISO`; 5 `DI` → `MOSI`; 6 `CLK` → `CLK`;
  8 `VCC` → `3.3V`; 4 `GND` → `GND`.
- `/WP` (pin 3) и `/HOLD` (pin 7) должны быть подтянуты к `VCC 3.3V`
  (иначе чип может игнорировать команды или висеть в hold).
- До подключения: напряжение `VCC` программатора (= 3.3 В, не 5 В)
  и уровни `MOSI/CLK/CS` в простое; отсутствие `+3.3V_SB` на плате
  (плата обесточена, батарея снята); pin 1 по ключу на корпусе.
</details>

### Упражнение 4. Арифметика APCB checksum

Стоковый APCB: DFG-слова по `@+0x130` и `@+0x16C` равны
`00 FF 1F 00`, checksum-байт `@+0x10` равен `0xF2`. После замены обоих
слов на `00 FF 7F 00` checksum стал `0x32`. Объясните, почему новое
значение именно `0x32`, если checksum — это байт, дополняющий сумму
всех байт региона до нуля по модулю 256.

<details><summary>Ответ</summary>

- В каждом из двух слов изменился один байт: `0x1F → 0x7F`,
  прирост `+0x60` на слово, суммарно `+0xC0` к сумме региона.
- Пусть `S` — старая сумма (mod 256), `C = (−S) mod 256 = 0xF2`.
- Новая сумма `S' = S + 0xC0`, новый checksum
  `C' = (−S') mod 256 = (C − 0xC0) mod 256 = 0xF2 − 0xC0 = 0x32`.
- Совпадает с наблюдённым в evidence (`0xF2 → 0x32`), всего 3 байта
  различий (`0xAB1010`, `0xAB1132`, `0xAB116E`).
</details>

### Упражнение 5 (бонус). Физический адрес региона

Вычислите физические адреса начала `$PSP` (`0x8E0000`), APCB
(`0xAB1000`) и сигнатуры VTF (`0xFFFFEC`) при top-of-4G mapping
16-МиБ чипа.

<details><summary>Ответ</summary>

- Формула: `PA(X) = 0xFF000000 + X`.
- `$PSP`: `0xFF8E0000`. APCB: `0xFFAB1000`. VTF: `0xFFFFFFEC`.
- Проверка VTF: `0xFFFFFFEC + 4 = 0xFFFFFFF0` — сразу за сигнатурой
  идёт reset vector, что совпадает с исходником
  `ResetVectorVtf0.nasm.inc` (сигнатура, затем `resetVector:`).
</details>

## 8. Источники

Все внешние ссылки открыты автором главы (статус на момент написания):

1. flashrom — официальный сайт и страница поддерживаемых программаторов
   (`ch341a_spi`, `ch347_spi`): <https://www.flashrom.org/>,
   <https://www.flashrom.org/supported_hw/supported_prog/index.html>
   (HTTP 200; вторая — финал редиректа со `Supported_programmers`).
2. Man-страница flashrom (документирован `ch341a_spi` и `-r`):
   <https://manpages.debian.org/unstable/flashrom/flashrom.8.en.html>
   (HTTP 200, раздел `ch341a_spi programmer` на месте).
3. WCH CH347 — вендорский репозиторий (SPI/JTAG семейства CH347):
   <https://github.com/WCHSoftGroup/ch347> (HTTP 200; pinned README
   с SHA-256 зафиксирован в `docs/research/2026-09-11-ch347-jtag-bc250.md`).
4. Winbond W25Q128JV — datasheet (распиновка SOIC-8, Instruction Set,
   питание 2.7–3.6 В):
   <https://www.winbond.com/resource-files/w25q128jv%20dtr%20revb%2011042016.pdf>
   (HTTP 200, ~1.9 МБ).
5. flashrom v1.8.0, pinned-исходник `flashchips/winbond.c`
   (запись `W25Q128.V`, 16 МиБ/256-байт страницы, RDID-probe):
   <https://raw.githubusercontent.com/flashrom/flashrom/90b6b4376c7480a223e7bb5642e7116315ac6d09/flashchips/winbond.c>
   (HTTP 200; SHA-256 файла зафиксирован в evaluation-отчёте).
6. EDK2 Reset Vector: каталог `UefiCpuPkg/ResetVector/Vtf0`
   (проверен листингом через `gh api`: `Vtf0.inf`, `Vtf0.nasmb`,
   `Ia16/Ia32/X64`), исходник точки входа
   `Ia16/ResetVectorVtf0.nasm.inc` (прочитан: сигнатура `VTF`
   по `0xFFFFFFEC`, метка `resetVector`, `jmp EarlyBspInitReal16`):
   <https://github.com/tianocore/edk2/tree/master/UefiCpuPkg/ResetVector/Vtf0>.
7. UEFI Forum — страница спецификаций (хаб: UEFI, PI 1.8/1.9/1.10, ACPI):
   <https://uefi.org/specifications> (прямой curl — 403 от бот-фильтра;
   содержимое открыто через jina reader: перечислены PI Specification
   вплоть до Version 1.10, июль 2026).

Локальные файлы проекта (пути от корня репозитория, прочитаны целиком):

- `docs/action-logs/2026-09-10-programmer-preflight.md` — эталон `dump/2.bin`,
  смещения `$PSP/$BHD/APCB/$PS1`, два свежих чтения, точечные кандидаты;
- `docs/research/2026-09-11-programmer-cli-evaluation.md` — CH347T/flashrom
  evaluation, probe `W25Q128.V`, решение `ADOPT`/`KEEP`;
- `docs/research/2026-09-11-ch347-jtag-bc250.md` — границы применимости CH347.

## 9. Открытые вопросы главы

1. Ревизия платы CH341A у оператора и фактические уровни сигналов (5 В
   на линиях?) — не измерено; боевой маршрут использует CH347T.
2. Точные границы 4 firmware volumes в `dump/2.bin` (смещения/длины) —
   взять из `evidence/programmer/reads/20260911/firmware-audit/inventory.json`
   родительской копии (в данной изолированной копии каталога `evidence`
   с разборами нет).
3. Наличие/отсутствие CSM в BC250 (секции `0x16`, строки `CsmVideo`/
   `LegacyBIOS`) — поиск по дампу не выполнялся; процедура дана в п. 5.4.
4. Порядок старта на BC250 (PSP-first vs x86-first, роль `$PSP`-региона
   до reset vector) — не подтверждён для данной платы.
5. Pinned-версии сторонних просмотрщиков (UEFITool, uefi-firmware-parser)
   в проекте не зафиксированы; воспроизводимость их вывода не проверена.
6. HN Algolia API опрошен (`UEFI firmware reverse engineering`, есть
   релевантный хит SentinelOne — использован в главе 02); отдельные
   HN-треды по CH341A/CH347 в главу не цитировались.
7. Видео/транскрипты (yt-dlp доступен, `gh` доступен): видеоисточники
   для данной главы не цитировались — необходимости не возникло.


