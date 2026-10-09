# Глава 04. Методология реверса прошивок

## Пререквизиты

- [Главы 01–03](01-boot-basics.md) (форматы FFS/FV/PE, UEFITool, OVMF).
- Ghidra или IDA на уровне «открыть бинарь, найти строки, построить граф».
- Linux-хост с flashrom для аппаратных разделов; root-доступ для программаторов.

## 4.1. Пайплайн разбора образа

Порядок один и тот же для любого вендора; меняется только глубина каждого шага.

1. **Инвентаризация**: размер, энтропия, `strings`, сигнатуры (`$PSP`, `$BHD`,
   `$PS1`, `APCB`, `_FVH`, `LZMA`, PE `MZ`). Определить вендора
   (AMI Aptio / Insyde / Phoenix) и класс платформы (Intel / AMD).
   Для AMD сначала смотрят PSP-область ([гл. 06](06-amd-platform.md)),
   затем FV/FFS.
2. **Структура**: UEFITool → дерево FV → список FFS с GUID и именами.
   Извлечь интересующие DXE/PEI через UEFIExtract. Для сжатых томов —
   сначала распаковать, декомпилировать только распакованное.
3. **Идентификация кода**: GUID-база (EDK2, база UEFITool), строки
   (`ASSERT`, пути сборки `c:\...`), DEPEX и вызовы
   `InstallProtocol`/`LocateProtocol` (граф зависимостей, см.
   [гл. 02](../../../../references/DEPENDENCIES.md#unavailable-local-inputs)). Диффинг версий (BinDiff,
   Ghidra Version Tracking) между релизами BIOS — быстрый путь к патчам
   безопасности.
4. **Декомпиляция**: Ghidra, язык `x86:LE:64:default`; для EFI-модулей
   подключить efiSeek (раздел 4.6). Альтернатива — Rizin/Cutter (4.7).
5. **Динамика**: OVMF+QEMU для generic-кода; Unicorn для точечной эмуляции
   функций (4.10). Для вендорного кода — Serial-лог, CHIPSEC-дампы (4.4),
   сравнение версий.

Все «непонятно» фиксируется в журнале (4.11), а не додумывается.

## 4.2. Аппаратное чтение: flashrom, CH341A, CH347

### 4.2.1. Правила безопасности (читать до подключения)

Канонический источник — best-practices гайд LinuxBoot/Heads
(проверен чтением raw-файла, ветка `master`):

- Полностью обесточить плату: снять все батареи включая CMOS, отключить AC,
  подождать 30 секунд. Не цеплять/снимать клипсу при запитанном
  программаторе.
- Подтвердить напряжение питания чипа мультиметром. Не угадывать:
  неверный VCC убивает чип.
- Ориентация клипсы: точка/ключ чипа (pin 1) — к красному проводу
  (для Pomona 5250). Проверять каждый раз.
- Сначала минимум два полных верифицированных бэкапа в разные файлы.
  Без них восстановление невозможно.

### 4.2.2. Распиновка SOIC8 и подключение

Карта пинов SOIC8 (вид сверху, точка/ключ — pin 1), по тому же гайду Heads:

| Pin | Сигнал | Назначение |
|-----|--------|------------|
| 1 | CS / CS# | Chip select |
| 2 | SO / MISO | Данные чип → программатор |
| 3 | WP# | Write protect (обычно NC) |
| 4 | GND | Земля |
| 5 | SI / MOSI | Данные программатор → чип |
| 6 | SCLK / CLK | Тактирование |
| 7 | HOLD# | Hold (обычно NC) |
| 8 | VCC | Питание (3.3 В или 1.8 В — по маркировке чипа!) |

Соответствие проводов клипсы Pomona 5250 программаторам CH341A-стиля
(проверено чтением того же файла): CS — красный, MISO — синий,
MOSI — фиолетовый, CLK — оранжевый, GND — чёрный, VCC — красный;
WP# (коричневый) и HOLD# (белый) — NC.

### 4.2.3. flashrom: программаторы и скорости

Проверено чтением man-страницы flashrom 8 (через jina reader):

- `ch341a_spi` — для SPI-флэша на WCH CH341A. Параметров нет,
  частота SPI фиксирована 2 МГц, используется CS0.
- `ch347_spi` — для SPI-флэша на CH347. Есть опциональный параметр
  `spispeed`, значение по умолчанию — 15 МГц. Синтаксис:
  `flashrom -p ch347_spi:spispeed=value`.
- Также в списке USB-программаторов man-страницы: `ch347_api`
  (для CH347), `serprog`, `ft2232_spi`, `pickit2_spi` и другие.

Замечание по CH347: вендорный репозиторий `WCHSoftGroup/ch347`
(ревизия `4625b40a`, 2026-06-09) документирует у кремния CH347 также
JTAG master mode (TMS, TCK, TDI, TDO, TRST) — см. локальный разбор
`docs/research/2026-09-11-ch347-jtag-bc250.md`. USB-идентификатор
`1a86:55db` и успешная SPI-работа не доказывают, что конкретная плата
программатора разводит JTAG-пины или держит 1.8 В.

### 4.2.4. Проверенная сессия: CH347T + W25Q128BV (локальный факт)

Полностью проверенная read-only сессия из репозитория —
`docs/research/2026-09-11-programmer-cli-evaluation.md`
(прочитана целиком; бинарь и логи захэшированы в самом документе):

- Бинарь: Arch `flashrom 1.8.0-1`, `flashrom v1.8.0 (git:v1.8.0)`,
  SHA-256 бинаря `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`.
- Проба на консервативной скорости (внутрисхемная клипса):

  ```text
  flashrom -p ch347_spi:spispeed=1.875M
  ```

  Детектировано: `Winbond W25Q128.V` (`16384 kB`).
- Два полных чтения разными файлами, только `-r`:

  ```text
  flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-a.bin
  flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-b.bin
  ```

- Оба файла побитово идентичны друг другу и `dump/2.bin`; общий
  SHA-256: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Дальше: `scripts/firmware_audit.py` независимо на каждом чтении,
  сравнение с базовой линией.

Правило тома: в первой сессии запрещены `-w`, erase, смена
write-protection и записи в статус-регистры. Вердикт документа —
`ADOPT` только для этого bounded read-only маршрута с pinned-бинарём;
IMSProg 1.9.1 остаётся `KEEP` как GUI-фолбэк без CLI/MCP.

### 4.2.5. Каноническая форма команд (Heads)

```bash
sudo flashrom --programmer ch341a_spi
sudo flashrom --programmer ch347_spi
sudo flashrom --programmer ch347_spi  # вариант с повышенной частотой — см. гайд
```

Длинная (`--programmer`) и короткая (`-p`) формы эквивалентны;
репозиторий использует короткую. После детекта — чтение, `hexdump -C`
для sanity-check, `--verify`, второе чтение в другой файл и снова
verify. Хэши обоих файлов — в журнал.

## 4.3. UEFITool / UEFIExtract / UEFIFind: сессии разбора

Проверено чтением README репозитория LongSoft/UEFITool (через jina reader)
и usage-строки `UEFIExtract` в исходниках ветки `new_engine`
(файл `UEFIExtract/uefiextract_main.cpp`, функция `print_usage`).

### 4.3.1. Что есть что

- **UEFITool** — кроссплатформенное Qt-приложение на C++: парсит
  UEFI-совместимый образ в дерево, проверяет целостность, даёт GUI для
  навигации. Сборка Qt-версии: компилятор C++ + Qt5/Qt6, `qmake`
  (или CMAKE для Qt6).
- **UEFIExtract** — консольная утилита на том же движке `ffsParser`:
  парсит образ в дерево и рекурсивно сваливает разобранную структуру
  на файловую систему. С деревом-выводом умеет работать утилита `tree`
  Джетро Бикмана (`jethrogb/uefireverse`). Сборка без Qt: компилятор C++
  + CMAKE (или Meson).
- **UEFIFind** — поиск элементов образа по заданному паттерну на том же
  `ffsParser`; написан для проекта UBU (UEFI BIOS Updater).
- **FMMT** (TianoCore, `BaseTools/Source/Python/FMMT`) — официальный
  Python-тулсет для модификации EDK2-образов; IBV-кастомизации
  не поддерживает. Упомянут в README как альтернатива.
- База известных GUID обновляется с каждым релизом; собирается при помощи
  Linux Vendor Firmware Service, актуальный экспорт —
  `https://fwupd.org/lvfs/shards/export/csv`.

Важно: правка образов сейчас возможна только устаревшим
и неподдерживаемым UEFITool 0.28.0 (ветка `old_engine`) и инструментами
на нём (`UEFIReplace`, `UEFIPatch`). Это приоритетный issue #67,
реализуется медленно. Проверено чтением раздела Known issues README.

### 4.3.2. Сессия UEFIExtract (точные режимы из usage)

```text
UEFIExtract imagefile        - generate report and GUID database, then dump only leaf tree items into .dump folder.
UEFIExtract imagefile all    - generate report and GUID database, then dump all tree items into .dump folder.
UEFIExtract imagefile unpack - generate report, then dump all tree items into a single .dump folder (legacy UEFIDump compatibility mode).
UEFIExtract imagefile dump   - only generate dump, no report or GUID database needed.
UEFIExtract imagefile report - only generate report, no dump or GUID database needed.
UEFIExtract imagefile guids  - only generate GUID database, no dump or report needed.
```

Плюс режим дампа только FFS-файлов с заданными GUID (без отчёта и базы).
Рекомендуемый минимум для нового образа:

```bash
UEFIExtract dump.bin report   # быстрый отчёт: FV, FFS, GUID
UEFIExtract dump.bin           # отчёт + база GUID + дамп листьев в .dump
```

Дальше — `grep` по отчёту (имена DXE, GUID), извлечение конкретных тел
драйверов из `.dump` и передача их в Ghidra/Rizin. Сжатые секции
распаковываются до декомпиляции; размер после распаковки фиксируется.

Локальная практика (см. [гл. 07](07-bc250-cases.md) и спецификацию
`specs/2026-09-10-bc250-firmware-audit.md`): из `dump/2.bin` извлекаются
234 исполнимых тела (179 PE32, 55 TE); счётчики вида «193 vs 194
FFS-файла» используются как детектор инъекции.

### 4.3.3. Известные ограничения (из README, не додумано)

- Вендорные файлы обновлений (шифрованные HP, Dell HDR/EXE, часть
  InsydeFlash FD) могут открываться некорректно или не открываться вовсе.
  Позиция автора: проще снять образ с чипа, где он уже расшифрован
  и распакован.
- Редактирование Intel FIT не поддерживается.
- Windows-сборки UEFIExtract/UEFIFind могут упираться в лимит пути
  MAX_PATH 260 байт; лечится long paths + манифест (в UEFIExtract
  манифест есть с версии A67).

## 4.4. CHIPSEC: модули поименно

CHIPSEC — фреймворк оценки безопасности платформ: железо, системная
прошивка (BIOS/UEFI), компоненты платформы. Включает security test suite,
инструменты доступа к низкоуровневым интерфейсам и forensic-возможности.
Работает на Windows, Linux и в UEFI shell. Первая версия вышла в марте
2014 (анонс на CanSecWest 2014). Проверено чтением README ветки
`chipsec2` (raw, начало файла). Внимание: ветка `main` больше
не поддерживается, актуальная — `chipsec2`, для старых Intel-платформ —
`chipsec1`.

Список модулей ниже проверен листингом дерева через GitHub API
на default-ветке (каталог `chipsec/modules`). Назначение каждого модуля
следует из его имени и кода; детали — в `chipsec-manual.pdf`
репозитория.

### 4.4.1. `chipsec/modules/common/` — базовые тесты (28 файлов)

| Модуль | Проверяет |
|--------|-----------|
| `bios_kbrd_buffer.py` | BIOS keyboard buffer |
| `bios_smi.py` | SMI-хендлеры BIOS |
| `bios_ts.py` | BIOS Test Suite / timestamp-состояние |
| `bios_wp.py` | Write-protection BIOS (BIOSWE/BLE/SMM_BWP) |
| `cet.py` | Control-flow Enforcement Technology |
| `debugenabled.py` | Отладочные интерфейсы (DCI и др.) |
| `firmware_info.py` | Сводная информация о прошивке |
| `ia32cfg.py` | IA32_MISC_ENABLE и смежные MSR |
| `me_mfg_mode.py` | Manufacturing mode Intel ME |
| `memconfig.py` | Конфигурация DRAM-параметров |
| `memlock.py` | Блокировки памятей/апертур |
| `remap.py` | Переотображение памяти (REMAPBASE/LIMIT, TOUUD) |
| `rom_armor.py` | Защита ROM-регионов |
| `rtclock.py` | RTC/CMOS |
| `sgx_check.py` | Конфигурация SGX |
| `sgx_check_sidekick.py` | SGX sidekick-проверка |
| `smm.py` | Базовые проверки SMM |
| `smm_addr.py` | Адресное пространство SMRAM |
| `smm_close.py` | Закрытие SMM (SMMLOCK) |
| `smm_code_chk.py` | SMM_Code_Check_En |
| `smm_dma.py` | DMA-защита SMRAM |
| `smm_lock.py` | Блокировки SMM-регистров |
| `smrr.py` | System Management Range Registers |
| `spd_wd.py` | SPD write-disable |
| `spi_access.py` | Доступ к SPI-контроллеру |
| `spi_desc.py` | Дескриптор SPI flash |
| `spi_fdopss.py` | Flash descriptor override / OPMenu |
| `spi_lock.py` | Блокировки SPI (FLOCKDN и др.) |

### 4.4.2. Подкаталоги `common/` и `tools/`

- `common/cpu/`: `cpu_info.py`, `ia_untrusted.py`, `spectre_v2.py`.
- `common/secureboot/`: `variables.py` (переменные Secure Boot).
- `common/uefi/`: `access_uefispec.py`, `s3bootscript.py`.
- `tools/`: `wsmt.py` (Windows SMM Security Mitigations Table).
- `bdw/`, `byt/` — на default-ветке содержат только `__init__.py`
  (legacy-заглушки).

### 4.4.3. `chipsec/modules/utilcmd/` — команды `chipsec_util`

Проверено листингом каталога (36 команд, имена файлов без `_cmd.py`):

`acpi`, `chipset`, `cmos`, `config`, `cpu`, `decode`, `deltas`, `desc`,
`ec`, `hals`, `hob`, `igd`, `interrupts`, `io`, `iommu`, `lock_check`,
`mem`, `mm_msgbus`, `mmcfg_base`, `mmcfg`, `mmio`, `module_id`, `msgbus`,
`msr`, `pci`, `reg`, `smbios`, `smbus`, `spd`, `spi`, `spidesc`, `tpm`,
`txt`, `ucode`, `uefi`, `vmem`, `vmm`.

Для реверса прошивок важнее всего `chipsec_util uefi`: его субкоманды
проверены чтением `chipsec/utilcmd/uefi_cmd.py` (ветка `chipsec2`,
вызовы `add_parser`): `types`, `var-read`, `var-write`, `var-delete`,
`var-list`, `var-list-spi`, `var-find`, `nvram`, `nvram-auth`, `decode`,
`keys`, `tables`, `s3bootscript`, `insert-before`, `insert-after`,
`replace`, `remove`, `assemble`.

### 4.4.4. Типовая сессия

```bash
python3 chipsec_main.py -m common.bios_wp      # один модуль
python3 chipsec_main.py -m common.spi_lock
chipsec_util.py uefi var-list                  # переменные UEFI
chipsec_util.py spi dump rom.bin               # дамп SPI (имя субкоманды — по --help)
```

Оговорка тома: точные CLI-флаги установки и шагов установки драйвера
из manual построчно не проверялись (см. сквозной открытый вопрос 5
в [гл. 00](00-index.md)); перед боевым запуском сверить `--help`
и README конкретной версии. CHIPSEC исторически Intel-центричен;
на default-ветке отдельного каталога AMD-модулей в `modules/` нет —
применение к AMD-платформам проверять по месту.

## 4.5. Binwalk: сигнатуры и энтропия

Binwalk v3 — переписанная на Rust версия классического инструмента
анализа прошивок (проверено чтением README ветки `master`):

- Находит и опционально извлекает файлы и данные, вложенные в другие
  файлы; основной фокус — прошивки, плюс широкий набор типов
  (см. wiki Supported-Signatures).
- Энтропийный анализ помогает находить неизвестное сжатие или шифрование
  (wiki Generating-Entropy-Graphs).
- Установка: Docker-образ, cargo или сборка из исходников (см. wiki).
  Использование: `binwalk <файл>`; детали — `--help` и wiki.

Место в пайплайне: Binwalk идёт после UEFITool, а не вместо него.
UEFI-области разбираются парсером FFS (4.3); Binwalk полезен для
не-UEFI хвостов: padding-объёмы, вендорные блобы, неизвестные сжатые
куски. Для AMD PSP-областей первичны PSPTool/amdfwtool
([гл. 06](06-amd-platform.md)), Binwalk — как второй взгляд.

```bash
binwalk dump.bin            # сигнатуры
binwalk -E dump.bin         # энтропия (флаг — по --help версии)
binwalk -e dump.bin         # извлечение (флаг — по --help версии)
```

Имена флагов `-E`/`-e` здесь приведены как ориентир классического
Binwalk; у v3 синтаксис сверять с `--help` (ОТКРЫТО, см. конец главы).

## 4.6. Ghidra + efiSeek: анализ EFI-модулей

Проверено чтением README репозитория `DSecurity/efiSeek` (ветка `master`,
raw): efiSeek — Ghidra-анализатор, автоматизирующий исследование EFI-файлов.

Возможности (по README):

- Поиск известных EFI GUID.
- Определение протоколов, получаемых через `LOCATE_PROTOCOL`.
- Определение функций, используемых как `NOTIFY`-функции.
- Определение протоколов, устанавливаемых модулем через
  `INSTALL_PROTOCOL_INTERFACE`.
- Определение функций-прерываний: hardware / software / child interrupts.
- Скрипт загрузки EFI-модулей в headless-режиме с сортировкой SMM-модулей
  по мета-информации в папки `SwInterrupts`, `ChildInterrupts`,
  `HwInterrupts`, `UnknownInterrupts`.

Установка (по README): задать переменную окружения `GHIDRA_INSTALL_DIR`
на путь Ghidra, запустить `gradlew.bat`, после сборки скопировать архив
из каталога `dist` в `GHIDRA_HOME_DIR/Extensions/Ghidra/` и включить
расширение в Ghidra. Использование: открыть EFI-файл, анализатор
выбирается автоматически; запуск — клавиша `A` или
`Analysis / Auto Analyze`.

Типовой флоу главы: тело DXE из `.dump` (4.3) → импорт в Ghidra
(`x86:LE:64:default`) → автоанализ с efiSeek → чтение найденных
протоколов и SMI-хендлеров → ручная разметка оставшегося. Точки входа:
`ModuleEntryPoint`, обращения к `gBS`/`gST`/`gDS`.

## 4.7. Rizin / Cutter: консольный и графический флоу

Проверено чтением README обоих проектов (raw):

- **Rizin** — фреймворк реверс-инжиниринга, форк radare2 с фокусом
  на usability, features и cleanliness. Портативен: анализ бинарей,
  дизассемблирование, отладка, forensic, скриптуемый hex-редактор.
  Документация — официальная книга `https://book.rizin.re`.
  Сборка — `meson` (`meson setup build`, `meson compile -C build`,
  `meson install -C build`; требуется meson не старее 0.55.0).
- **Cutter** — свободная open-source RE-платформа на движке Rizin,
  «создана реверсерами для реверсеров», с прицелом на продвинутую
  кастомизацию при удобном UX.

Типовой консольный флоу (канонические команды Rizin; детали — в книге):

```bash
rizin -A driver.efi        # открыть + базовый анализ
[0x...]> iz                # строки
[0x...]> ii                # импорты
[0x...]> aaa               # полный автоанализ
[0x...]> afl               # список функций
[0x...]> pdf @ main        # дизассемблирование функции
[0x...]> px 64 @ entry0    # hex-дамп
```

Локальная практика репозитория: требуемый стек —
Cutter `v2.5.0` с bundled Rizin и `CutterMCP_native v0.1.6`
только на `127.0.0.1` (см. `specs/2026-09-10-bc250-firmware-audit.md`,
раздел Planning anchor; runtime-проба —
`docs/action-logs/2026-09-10-cutter-mcp-runtime-trial.md`).
MCP-прослойка не заменяет ручную верификацию выводов.

## 4.8. NVRAM-парсинг: переменные UEFI

Переменная UEFI — это тройка «имя + GUID + атрибуты» плюс тело
(см. словарь [гл. 00](00-index.md)). Хранилище переменных живёт
в NVRAM-области прошивки; у AMI-стеков записи помечены сигнатурой
`NVAR`.

Инструментальные маршруты:

1. **CHIPSEC** (субкоманды проверены чтением `uefi_cmd.py`, 4.4.3):
   `var-list`, `var-list-spi`, `var-find`, `var-read`, `nvram`,
   `nvram-auth`, `decode`, `keys`, `tables`. Чтение — безопасно;
   `var-write`/`var-delete` — только осознанно, с бэкапом.
2. **Локальный аудит AMI NVAR** — `scripts/nvar_audit.py` (прочитан):
   read-only bounded-аудитор метаданных NVAR и выбранных полей.
   Сигнатура `NVAR_SIGNATURE = b"NVAR"`, дефолтное окно стора —
   offset `0x1000`, длина `0xF000` (параметризуется). Имена,
   похожие на security-материал (`pk`, `kek`, `db`, `dbx`, ключи,
   пароли…), редактируются: тела не выводятся, только факт наличия.
   Пример evidence-derived таблицы полей (`KNOWN_FIELDS`,
   смещения внутри переменной AmdSetup, типы `u8`/`u16`/`u32`):
   `MemoryClockSpeed` 0x316, `Tcl` 0x317, `FclkDpm` 0x6A3,
   `VddcrVddOffset` 0x6E6 (`u32`), `DfClockOvrd` 0x704 (`u16`),
   `FastPpt` 0x70C (`u32`). Эти смещения — факт конкретного
   репозитория и конкретного образа, а не универсальный стандарт;
   для других образов таблицу строить заново.
3. **Ручной разбор**: найти `NVAR`/GUID переменных в дампе,
   распарсить заголовки записей, сверить с выводом CHIPSEC.

## 4.9. SMM-экстракция: поиск SMI-хендлеров

Цель — перечислить SMI-хендлеры образа и их входные условия:
это входные ворота привилегированного кода (контекст —
[гл. 02](../../../../references/DEPENDENCIES.md#unavailable-local-inputs) и [гл. 05](../../../../references/DEPENDENCIES.md#unavailable-local-inputs)).

Шаги:

1. Извлечь все DXE/SMM-драйверы через UEFIExtract (4.3.2).
2. Отобрать SMM-модули: efiSeek headless-скрипт раскладывает их
   в `SwInterrupts` / `ChildInterrupts` / `HwInterrupts` /
   `UnknownInterrupts` (4.6). Дополнительно — поиск GUID
   `EFI_SMM_SW_DISPATCH2_PROTOCOL` и вызовов регистрации хендлеров.
3. Для каждого хендлера зафиксировать: GUID драйвера, тип диспетча
   (Sw/Child/Hw), входные параметры (`EFI_SMM_SW_CONTEXT`,
   `CommBuffer`), вызываемые Boot/Runtime-сервисы.
4. Сверить конфигурацию платформы модулями CHIPSEC `smm*`:
   `smm`, `smm_addr`, `smm_close`, `smm_code_chk`, `smm_dma`,
   `smm_lock`, `smrr` (4.4.1).

Локальный масштаб задачи: 234 исполнимых тела в `dump/2.bin`
(4.3.2) — ручной разбор без сортировки efiSeek не масштабируется.

## 4.10. Эмуляция: QEMU/OVMF и Unicorn

### 4.10.1. QEMU + OVMF (полная виртуальная платформа)

Проверено чтением `OvmfPkg/README` в edk2 (ветка `master`, raw):
OVMF — прошивка для виртуальных машин на кодовой базе edk2.
Заявленные возможности: архитектура X64 (опционально IA32 SEC/PEI);
QEMU версии 1.7.1 и новее; видео, клавиатура, IDE, CD-ROM, serial;
запуск UEFI shell; опционально NIC; загрузка UEFI Linux/Windows.
Сборка — через `OvmfPkg/OvmfPkgX64.dsc` (`TARGET_ARCH` по месту).

Типовой пример запуска (иллюстративный; пути к fd-файлам — по месту):

```bash
qemu-system-x86_64 -machine q35 -cpu qemu64 -m 2G \
  -drive if=pflash,format=raw,unit=0,file=OVMF_CODE.fd,readonly=on \
  -drive if=pflash,format=raw,unit=1,file=OVMF_VARS.fd \
  -serial stdio -display none
```

Применение в реверсе: прогон generic DXE/утилит, отработка протокольных
взаимодействий, снятие Serial-лога. Вендорные DXE, привязанные
к железу, в OVMF обычно не заводятся — для них следующий инструмент.

### 4.10.2. Unicorn (точечная эмуляция функций)

Проверено чтением документации Unicorn (`unicorn-engine.org/docs`,
через jina reader): установка из исходников, из репозиториев
(Homebrew `brew install unicorn` для macOS и др.), дизайн описан
в слайдах BlackHat USA 2015 (`BHUSA2015-unicorn.pdf` на сайте).

Минимальный иллюстративный пример (x86-64, эмуляция `mov rax, 0x2a`):

```python
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64
from unicorn.x86_const import UC_X86_REG_RAX

CODE = b"\x48\xc7\xc0\x2a\x00\x00\x00"  # mov rax, 0x2a
BASE = 0x1000000

mu = Uc(UC_ARCH_X86, UC_MODE_64)
mu.mem_map(BASE, 0x1000)
mu.mem_write(BASE, CODE)
mu.emu_start(BASE, BASE + len(CODE))
assert mu.reg_read(UC_X86_REG_RAX) == 0x2A
```

Применение в реверсе: вырезать из DXE leaf-функцию (декодер,
checksum, распаковщик), замаппить её и входные буферы, прогнать
с хуками на чтение/запись памяти. Сложность — честная эмуляция
вызовов `gBS` (их обычно стабят). Пример выше — именно пример API,
а не готовый харнес под конкретный драйвер.

## 4.11. Журнал реверса (обязательный минимум)

- Хэш исходного образа (SHA-256), источник дампа, дата, инструмент чтения.
- Таблица «GUID → имя → версия → вердикт» для каждого разобранного драйвера.
- Размеры до/после распаковки сжатых секций, контрольные суммы.
- Все «непонятно» — в открытые вопросы, не додумывать.
- Локальный формат вердиктов — по `specs/2026-09-10-bc250-firmware-audit.md`
  и [гл. 07](07-bc250-cases.md).

## 4.12. Упражнения с ответами

**У1. Два чтения.** Вы сняли два чтения SPI-флэша: `a.bin` и `b.bin`
различаются в одном байте. Ваши действия по методологии главы?

*Ответ.* Ничего не прошивать и не анализировать как baseline.
Проверить посадку клипсы, питание платы (должна быть полностью
обесточена), VCC чипа; повторить пару чтений на пониженной скорости
(для `ch347_spi` — `spispeed=1.875M` из проверенной сессии 4.2.4).
Baseline — только два побитово совпадающих чтения с зафиксированными
SHA-256. Причина: одиночный различающийся байт неотличим от плохого
контакта, а решения на битом дампе отравляют весь дальнейший разбор.

**У2. Отчёт без дампа.** Нужен быстрый обзор незнакомого 16 МиБ образа:
список FV/FFS/GUID, без распаковки тел. Какая команда и почему?

*Ответ.* `UEFIExtract dump.bin report` — режим «только отчёт»
из usage 4.3.2: без дампа и базы GUID, быстро. Дальше `grep` по отчёту,
и только для отобранных драйверов — полный `UEFIExtract dump.bin`
с дампом листьев.

**У3. SMM-перепись.** Опишите минимальную воспроизводимую процедуру
перечисления SMI-хендлеров образа средствами главы.

*Ответ.* 1) `UEFIExtract dump.bin` — извлечь все тела. 2) efiSeek
в headless-режиме — разложить SMM-модули по `Sw/Child/Hw/UnknownInterrupts`.
3) Для каждого — GUID, тип диспетча, входной контекст, вызываемые
сервисы — в таблицу журнала. 4) Прогнать CHIPSEC-модули `smm*`
(`smm`, `smm_addr`, `smm_close`, `smm_code_chk`, `smm_dma`, `smm_lock`,
`smrr`) для конфигурации платформы. Всё неклассифицированное —
в `UnknownInterrupts` и в открытые вопросы, а не в «наверное Sw».

**У4. Переменная-кандидат.** В NVRAM найдена переменная с именем,
похожим на `Setup`, но с другим GUID. Что делать до любых выводов?

*Ответ.* Не предполагать, что это «тот самый Setup». Зафиксировать
имя + GUID + атрибуты + хэш тела; прочитать тело через
`chipsec_util uefi var-read` или `nvram`/`decode`; сверить структуру
с известным Setup (смещения полей валидны только для своего образа,
см. 4.8 про `KNOWN_FIELDS`); искать ссылки на этот GUID в DXE-коде.
Вывод «это копия/зеркало Setup» — только при совпадении структуры
и наличии потребителя в коде.

## 4.13. Источники к главе

- [flashrom man 8 (ch341a_spi, ch347_spi)](https://man.archlinux.org/man/flashrom.8)
  (открыто через jina reader; параметры и скорости — оттуда).
- [flashrom — Supported hardware / docs](https://www.flashrom.org/)
  (открыто через jina reader).
- [Heads: SPI Programmer Best Practices](https://github.com/linuxboot/heads-wiki/blob/master/Installing-and-Configuring/Flashing-Guides/SPI-Programmer-Best-Practices.md)
  (прочитан raw-файл ветки `master`: пинауты, wiring, backup-флоу).
- [UEFITool README](https://github.com/LongSoft/UEFITool)
  (прочитан через jina reader; плюс HN-обсуждение:
  [story 29419389](https://news.ycombinator.com/item?id=29419389),
  найдено через HN Algolia API).
- [UEFIExtract usage (`uefiextract_main.cpp`, ветка `new_engine`)](https://github.com/LongSoft/UEFITool/blob/new_engine/UEFIExtract/uefiextract_main.cpp)
  (прочитан raw-файл, режимы — цитата из `print_usage`).
- [CHIPSEC README (ветка `chipsec2`)](https://github.com/chipsec/chipsec/blob/chipsec2/README.md)
  (прочитан raw-файл); листинг `chipsec/modules` и `chipsec/utilcmd` —
  через GitHub API на default-ветке; `uefi_cmd.py` прочитан raw.
- [CHIPSEC manual (PDF)](https://github.com/chipsec/chipsec/raw/7e016af070f1a3ff26c3888e256e174c1274c183/chipsec-manual.pdf)
  (ссылка из [гл. 00](00-index.md); построчно не проверялся — ОТКРЫТО).
- [Binwalk v3 README](https://github.com/ReFirmLabs/binwalk)
  (прочитан raw-файл ветки `master`).
- [efiSeek README](https://github.com/DSecurity/efiSeek)
  (прочитан raw-файл ветки `master`).
- [Rizin README + книга](https://github.com/rizinorg/rizin)
  (`https://book.rizin.re`; прочитан raw-файл ветки `dev`).
- [Cutter README](https://github.com/rizinorg/cutter)
  (прочитан raw-файл ветки `master`).
- [Unicorn docs](https://www.unicorn-engine.org/docs/)
  (открыто через jina reader).
- [OvmfPkg README (edk2)](https://github.com/tianocore/edk2/blob/master/OvmfPkg/README)
  (прочитан raw-файл ветки `master`).
- Локально (прочитаны целиком): `docs/research/2026-09-11-programmer-cli-evaluation.md`
  (сессия CH347T), `docs/research/2026-09-11-ch347-jtag-bc250.md`,
  `scripts/nvar_audit.py` (первые 60 строк + структура),
  `specs/2026-09-10-bc250-firmware-audit.md` (якоря и стек).

## 4.14. Открытые вопросы

- Binwalk v3: точные имена флагов энтропии/извлечения не сверены
  с `--help` v3 (в тексте — ориентир классики, помечен).
- `chipsec_util spi dump`: имя субкоманды приведено как ориентир,
  сверять с `--help` (помечено в тексте).
- CHIPSEC manual: точные CLI установки и шагов установки драйвера
  построчно не проверялись (сквозной вопрос 5).
- QEMU-пример 4.10.1 — иллюстративный; версии QEMU/OVMF и точные
  опции pflash под конкретную задачу сверять по месту.
- Unicorn-пример 4.10.2 — иллюстрация API, не харнес под драйвер;
  стаббинг `gBS` и работа с хуками памяти — за рамками главы.
- yt-dlp: проверено, что у доклада 36c3-10942
  («Uncover, Understand, Own», AMD PSP) субтитров на media.ccc.de нет
  (`yt-dlp --list-subs` → `has no subtitles`); видео-источники в томе
  по транскриптам не цитируются.
- BH-talk page: не открылась (403/404) — детали доклада не излагаются
  (наследовано из прошлой версии главы).
- Реестр H1–H18 не найден; известны только H1/H19
  (см. [гл. 05](../../../../references/DEPENDENCIES.md#unavailable-local-inputs), [гл. 07](07-bc250-cases.md)).

