# Глава 06. Платформа AMD: PSP, AGESA, ABL, APCB, SMU

## Пререквизиты

- [Главы 01–05](01-boot-basics.md) (фазы PI, DXE-инъекция как идея, классы уязвимостей).
- [Глава 04](04-re-methodology.md) (UEFIExtract, парсинг бинарей, журнал).
- Готовность: спецификация PSP доступна только под NDA (это прямо сказано
  в документации coreboot, см. 6.4); часть знаний — из комьюнити-тулзов
  и открытых заголовков coreboot. Всё, что не проверено, — в открытых
  вопросах, выдуманных ID и адресов в главе нет.

Нотация: все структуры ниже — little-endian, смещения в байтах от начала
структуры. Первоисточник байтовых раскладок — открытые заголовки coreboot
(`src/vendorcode/amd/psp/*.h`, прочитаны raw с ветки `main`); в их
комментариях указан документ AMD #55758 как нормативная спецификация
(сам документ под NDA, в томе не цитируется).

## 6.1. EFS и PSP-директория побайтово

### 6.1.1. EFS (Embedded Firmware Structure)

Точка входа всей AMD-разборки: PSP ROM ищет EFS по сигнатуре.
Структура `embedded_firmware` из `psp_efs.h` (выравнивание 16):

| Смещение | Поле | Значение / смысл |
|----------|------|------------------|
| 0x00 | `signature` | `0x55AA55AA` |
| 0x04 | `imc_entry` | Точка входа IMC |
| 0x08 | `gec_entry` | Точка входа GEC |
| 0x0C | `xhci_entry` | Точка входа xHCI FW |
| 0x10 | `psp_directory` | Указатель PSP-директории (он же combo) |
| 0x14 | `new_psp_directory` | Указатель новой PSP-директории |
| 0x18–0x20 | `bios0/1/2_entry` | Точки входа BIOS |
| 0x24 | `efs_gen` / `multi_gen_efs` | Поколение EFS (client / server) |
| 0x28 | `bios3_entry` | Точка входа BIOS3 |
| 0x2C | `psp_bak_directory` | Резервная PSP-директория |
| 0x30–0x38 | `promontory*_fw_ptr` | Указатели FW Promontory |
| 0x3C | `reserved_3Ch` | Резерв |
| 0x40–0x4B | `spi_readmode/fast_speed/...` | Параметры SPI по семействам (f15, f17 mod 00–2f / 30–3f) |
| 0x4C | `vendor_id` | u16 |
| 0x4E | `board_id` | u16 |
| 0x50–0x53 | `espi0/1_config0/1` | Конфигурация eSPI |
| 0x54 | `ubu_table` | Таблица UBU |
| 0x58 | `bios_size` | Размер BIOS |

Практический приём: `grep` сигнатуры `AA 55 AA 55` по образу даёт
кандидатов в EFS; дальше читаются `psp_directory` и BIOS-указатели.

### 6.1.2. Заголовок PSP-директории (16 байт)

Структура `psp_directory_header` из `psp_directory.h`:

| Смещение | Поле | Смысл |
|----------|------|-------|
| 0x0 | `cookie` | `0x50535024` (`PSP$`) для L1; `0x324C5024` (`2LP$`) для L2 |
| 0x4 | `checksum` | Контрольная сумма директории |
| 0x8 | `num_entries` | Число записей |
| 0xC | `additional_info` | Битовые поля (версия 0 или 1, см. ниже) |

Версия 0 (`version` = 0): `dir_size:10` (в блоках 4K),
`spi_block_size:4`, `base_addr:15` (биты [26:12] базового адреса),
`address_mode:2`, `version:1`.
Версия 1 (`version` = 1): `dir_size:16` (в блоках 4K),
`spi_block_size:4` (`4K << (1 << value)`), `dir_hdr_size:4`
(в блоках 1K), `address_mode:2`, `reserved:5`, `version:1`.

Режимы адресации (`enum amd_addr_mode`, тот же заголовок):
`AMD_ADDR_PHYSICAL` = 0 (физический адрес),
`AMD_ADDR_REL_BIOS` (от начала образа), `AMD_ADDR_REL_TAB`
(от таблицы), `AMD_ADDR_REL_SLOT` (от слота), `AMD_ADDR_AUTO`.

### 6.1.3. Запись PSP-директории (16 байт)

Структура `psp_directory_entry`:

| Смещение | Поле | Смысл |
|----------|------|-------|
| 0x0 | `type` (u8) | Тип FW (таблица 6.2) |
| 0x1 | `subprog` (u8) | Подпрограмма |
| 0x2 | `rsvd` (u16) | Биты: `rom_id:2`, `writable:1`, `inst:4`, резерв |
| 0x4 | `size` (u32) | Размер тела |
| 0x8 | `addr:62` + `address_mode:2` (u64) | Адрес (или значение) + режим |

Двухуровневость: запись типа `0x40` (`AMD_FW_PSP_L2_PTR`) указывает
на L2-таблицу с кукой `2LP$`. Максимальные размеры по `amdfwtool.h`:
`MAX_PSP_ENTRIES 0xFF`, `MAX_BIOS_ENTRIES 0x2F`; выравнивания:
таблицы — `0x1000`, блобы — `0x100`.

### 6.1.4. BIOS-директория (L1/L2)

Структура `bios_directory_hdr` из `bios_directory.h` повторяет раскладку
PSP-заголовка (кука, checksum, число записей, `additional_info` v0/v1):
куки `0x44484224` (`$BHD` в порядке байтов образа — см. примечание ниже)
для L1 и `0x324C4224` (`2LB$`) для L2.

Запись `bios_directory_entry` — 24 байта:

| Смещение | Поле | Смысл |
|----------|------|-------|
| 0x0 | `type` (u8) | Тип BIOS-записи (6.2.2) |
| 0x1 | `region_type` (u8) | Тип региона |
| 0x2 | биты | `reset:1`, `copy:1`, `ro:1`, `compressed:1`, `inst:4` |
| 0x3 | биты | `subprog:3`, `romid:2`, `writable:1`, `rsvd:2` |
| 0x4 | `size` (u32) | Размер |
| 0x8 | `source:62` + `address_mode:2` (u64) | Источник |
| 0x10 | `dest` (u64) | Назначение |

Примечание о порядке байтов: константа `BHD_COOKIE 0x44484224`
в дампе читается как ASCII `$BHD` (байты `24 42 48 44`); в локальных
материалах репозитория якорь так и записан — `$BHD` на `0xAB0000`
(см. 6.8). Аналогично `PSP_COOKIE 0x50535024` — это `PSP$` в дампе.

## 6.2. PSP trust chain и типы записей

### 6.2.1. Модель загрузки

Platform Security Processor (в новых материалах — AMD Secure Processor,
ASP) — отдельное ARM-ядро на кристалле, стартующее до x86 и проверяющее
подписи ранних стадий. Документация coreboot (Family 17h, прочитана
через jina reader) фиксирует: роль PSP в инициализации системы —
центральная; спецификация PSP — только под NDA; coreboot полагается
на `util/amdfwtool` для сборки структур образа; дизайн PSP для Family 17h
добавил BIOS Directory Table по образцу PSP Directory Table.

Вывод для практики (наследован из прошлой версии главы, верен
и сейчас): тела PSP без приватных ключей AMD не подменить — точка
инъекции смещается в неподписанные области (DXE, APCB, NVRAM).
Проверка подписей `$PS1`-контейнеров (RSA PSS / SHA-256) — скриптами
верификации по месту; готового рецепта в томе нет (ОТКРЫТО).

### 6.2.2. Типы записей PSP-директории (из `enum amd_fw_type`)

Ключевые для реверса (полный enum — в заголовке coreboot, значения —
u8 в смещении 0x0 записи):

| Type | Имя | Роль |
|------|-----|------|
| 0x00 | `PSP_PUBKEY` | Публичный ключ PSP |
| 0x01 | `PSP_BOOTLOADER` | Загрузчик PSP |
| 0x02 | `PSP_SECURED_OS` | Защищённая ОС PSP (TOS) |
| 0x03 | `PSP_RECOVERY` | Recovery-образ |
| 0x04 | `PSP_NVRAM` | NVRAM PSP |
| 0x05 | `PSP_RTM_PUBKEY` | Ключ RTM |
| 0x08 | `PSP_SMU_FIRMWARE` | Прошивка SMU (PMFW), слот 1 |
| 0x0A | `PSP_ABL_PUBKEY` | Ключ ABL |
| 0x0C/0x0D | `PSP_TRUSTLETS/TRUSTLETKEY` | Трастлеты и их ключи |
| 0x12 | `PSP_SMU_FIRMWARE2` | Прошивка SMU, слот 2 |
| 0x1A–0x1F | `SEV/BOOT/SOC/DEBUG/INTERFACE_DRIVER` | Драйверы PSP |
| 0x20 | `PSP_HW_IPCFG` | Конфигурация HW IP |
| 0x22 | `PSP_TOKEN_UNLOCK` | Токен разблокировки |
| 0x24 | `PSP_SEC_GASKET` | SEC GASKET (политика изоляции IP) |
| 0x25 | `PSP_MP2_FW` | Прошивка MP2 |
| 0x2A | `PSP_MP5` | MP5 |
| 0x30–0x37 | `PSP_ABL0..ABL7` | AGESA Boot Loader, стадии 0–7 |
| 0x38/0x39 | `PSP_SEV_DATA/SEV_CODE` | SEV данные/код |
| 0x40 | `PSP_L2_PTR` | Указатель L2-таблицы |
| 0x42 | `PSP_DXIO` | DXIO FW |
| 0x45 | `PSP_TOS_SEC_POLICY` | Security policy TOS |
| 0x47 | `PSP_DRTM_TA` | DRTM trusted app |
| 0x48/0x4A | `RECOVERYAB_A/B` | A/B recovery |
| 0x49 | `PSP_BIOS_TABLE` | Указатель BIOS-таблицы |
| 0x52/0x53 | `VERSTAGE/VERSTAGE_SIG` | Verstage и подпись |
| 0x5C | `PSP_SPIROM_CFG` | Конфигурация SPI ROM |
| 0x5F | `PSP_TPMLITE` (17h/19h) | fTPM |

Остальные значения (0x50/0x51 KEYDB, 0x54 RPMC_NVRAM, 0x55 SPL,
0x58/0x59 DMCU, 0x5A MSMU, 0x5D MPIO, 0x64+ RAS/SPDM/DPE, 0x71 DMCUB,
0x73 BOOTLOADER_AB, 0x76 RIB и далее) — по заголовку; в главе
не разворачиваются.

Типы записей BIOS-директории (`enum amd_bios_type`): `0x05 RTM_PUBKEY`,
`0x07 SIG`, **`0x60 APCB`**, `0x61 APOB`, `0x62 BIN`, `0x63 APOB_NV`,
`0x64 PMUI`, `0x65 PMUD`, `0x66 UCODE` (микрокод), `0x68 APCB_BK`
(бэкап APCB), `0x69 EARLY_VGA`, `0x6A MP2_CFG`,
`0x6B PSP_SHARED_MEM`, `0x6D NV_ST`, `0x70 L2_PTR`.

### 6.2.3. Сессия PSPTool

PSPTool — «швейцарский нож» для прошивок AMD Secure Processor:
парсит, извлекает и заменяет AMD FW внутри UEFI-образов
(проверено чтением README; репозиторий переехал
`cwerling/psptool` → `PSPReverse/PSPTool`). Ключевой факт
из README: все AMD-блобы лежат в padding-объёмах, которые UEFITool
не парсит, — поэтому PSPTool complementary к UEFITool, а не замена.
Установка: `pip3 install psptool` (PyPI) или из GitHub.
HN-покрытие (найдено через HN Algolia API): story 20106060
(«PSPTool Is a Swiss Army Knife…», 172 points, 42 комментария),
Show HN 20102425 и новость 20123863.

```bash
pip3 install psptool
psptool image.bin        # список FW-записей ROM (пример 1 из README)
```

Исследовательский контекст из README (TU Berlin): faulTPM (2023),
«One Glitch to Rule Them All» (2021, fault injection против SEV),
доклады 36c3-2019 «Uncover, Understand, Own» и «Dissecting the AMD PSP»,
BlackHat US 2023 про Tesla. Это карта первоисточников для углубления;
сами работы в томе не пересказываются.

### 6.2.4. Сессия amdfwtool (coreboot)

Usage-строка проверена чтением `util/amdfwtool/opts.c`:

```text
Usage: amdfwtool [options] --config <file> --flashsize <size> --output <filename>
```

`--output` обязателен; также проверены `--output-manifest`
(манифест версий блобов), `--signed-output`, `--apob-base`
(назначение для AGESA PSP output block). Поддерживаемые платформы
(`enum platform` в `amdfwtool.h`, прочитаны): Mullins, Carrizo,
StoneyRidge, Raven, Picasso, Renoir, Cezanne, Mendocino, Lucienne,
Phoenix, Strix, Genoa, Krackan2E, StrixHalo, Turin, StrixKrackan.
Отдельной платформы для BC250/Ariel в списке нет (см. открытые вопросы).

## 6.3. ABL-цепочка

ABL (AGESA Boot Loader) — ранние загрузчики, исполняющиеся под контролем
PSP до передачи управления x86. Факты, на которых стоит раздел:

- Типы записей `0x30–0x37` = `AMD_FW_PSP_ABL0..ABL7` (проверено чтением
  `enum amd_fw_type` в `psp_directory.h`).
- Локальный инвентарь BC250 (`docs/research/2026-09-12-bios-vuln-inventory.md`,
  строка 23, прочитана): записи PSP-директории 9–13, типы `0x30–0x34` =
  `AGESA_BOOT_LOADER_0..4`, причём `0x31` = ABL1 размером 48,848 B
  со смещения `0x99F700+`; все подписанные (`signed`).
- Извлечение тел ABL — через PSPTool (6.2.3); упаковка обратно в образ —
  через amdfwtool (6.2.4).

Что отсюда следует для реверса: ABL-стадии — подписанный код PSP-стороны,
поэтому менять поведение через их тела нельзя; рабочая поверхность —
данные, которые они потребляют (APCB, NVRAM). Утверждение «ABL1 читает
APCB» в этой редакции тома считается неподтверждённым по месту
(ОТКРЫТО): в изолированной копии нет разбора, который бы это показывал
(step-точка для читателя — упражнение У2). Порядок и семантика стадий
ABL0–ABL7 нормированы документом AMD #55758 (упомянут в заголовках
coreboot); сам документ под NDA.

## 6.4. AGESA и PI-фазы

AGESA (AMD Generic Encapsulated Software Architecture) — референсный код
инициализации платформы: включение DRAM, конфигурация проприетарной
core-логики, помощь в генерации ACPI-таблиц и другие функции
(проверено чтением документации coreboot «AMD Family 17h in coreboot»
через jina reader). Из того же документа:

- Начиная с Family 17h (Zen) AMD сменила парадигму инициализации —
  поток исполнения coreboot пришлось серьёзно менять; документ описывает
  новый boot flow, вызовы и компромиссы.
- AGESA для продуктов старше Family 17h известна как v5 или Arch2008;
  в coreboot сосуществуют открытая AGESA и закрытые реализации (binaryPI).
- Первое устройство Family 17h, портированное в coreboot, — Picasso
  (`soc/amd/picasso`).

### 6.4.1. Точки входа AGESA Arch2008 (проверены по спецификации)

Проверено чтением полного текста спецификации «AGESA Interface
Specification for Arch2008» (документ AMD #44065, зеркало 15h.org,
PDF → текст через jina reader, 508 КБ текста). В документе присутствуют
следующие точки входа (имена — цитата, grep по тексту):

`AmdInitReset`, `AmdInitResetPPI`, `AmdInitEarly`, `AmdInitEarlyPPI`,
`AmdInitPost`, `AmdInitPostPeim`, `AmdInitPostPPI`, `AmdInitEnv`,
`AmdInitMid`, `AmdInitLate`, `AmdInitResume`, `AmdInitRtb`,
`AmdS3LateRestore`, `AmdS3FinalRestore`,
`AmdLateRunApTask`.

Конвенциональное отображение на PI-фазы (проверяется по той же
спецификации, раздел вызовов): `Reset`/`Early` — ранний PEI;
`Post` — мост PEI→DXE; `Env`/`Mid`/`Late` — DXE-сторона;
`Resume`/`S3*Restore` — путь S3-resume. Точные предусловия каждого
вызова (доступная память, состояние HOB, требования к вызывателю)
в главе не фиксируются — читаются в документе #44065 по месту вызова.

Практическое правило тома (без изменений): менять поведение через
APCB/NVRAM, а не через подписанные тела AGESA/ABL.

## 6.5. APCB-парсинг

APCB (AGESA PSP Customization Block) — конфигурационные данные для AGESA:
тайминги DRAM, фабрика, лимиты. В BIOS-директории APCB — тип `0x60`,
бэкап — `0x68` (проверено чтением `enum amd_bios_type`, 6.2.2).

### 6.5.1. Модель данных (проверена чтением UTK README)

Проект UTK (`ragebone/utk`, файл `UtkAmd/psp/firmware/apcb/README.md`,
прочитан raw с веток `main` и `master` — содержимое совпало) фиксирует:

```text
APCB -> Group -> Type -> Data?
```

APCB содержат группы, группы — типы, типы — данные. Одна из форм данных —
токены: простые пары «ключ → значение». Значения ключей и их смысл
в прошлом не были открытым знанием; UTK ссылается на открытый список
токенов APCB V3 из openSIL (см. 6.5.2). Там же — пример практического
применения: модификации APCB для ASUS ROG Ally при апгрейде памяти
(репозиторий `95JakeHex/APCB_ROG_Ally`, упомянут в README).

### 6.5.2. Проверенные инструменты и таблицы токенов

- **apcbtool** (`Tim---/apcbtool`): «Tool to parse and build AMD APCB
  data» (прочитан README ветки `main`). Парсинг и сборка APCB.
- **openSIL AGCL-R**: заголовок `ApcbV3TokenUid.h`
  (`AgesaPkg/Addendum/GenoaSp5Rdimm/Apcb/Inc/Genoa/`, пин `0a60473`):
  по ссылке из UTK README отдаёт HTTP 200, размер 213,110 байт
  (проверено 2026-09-24). Исчерпывающий список UID токенов APCB V3
  для Genoa — сверять покрытие под свой SoC.
- **oxidecomputer/amd-apcb** (Rust): упомянут в UTK README как один
  из APCB-инструментов; сам репозиторий в этой редакции не открывался
  (ОТКРЫТО, см. конец главы).
- **PSPTool + amdfwtool** — извлечение области APCB из образа
  (6.2.3–6.2.4), далее разбор токенов инструментами выше.

Сквозной открытый вопрос 10 («отдельный APCB-парсер не найден»)
этой главой частично закрывается: apcbtool существует и проверен
на уровне README; глубина его покрытия под BC250 — отдельный вопрос
(см. конец главы).

### 6.5.3. Локальный факт: APCB в BC250

Якоря из `specs/2026-09-10-bc250-firmware-audit.md` (прочитаны):
APCB на `0xAB1000`, размер `0xB70`, контрольная сумма в `+0x10`.
Скрипт `scripts/apcb_detail.py` (прочитан, первые строки + структура)
реализует read-only аудит: проверка магии `b"APCB"`, проверка размера
(`size >= 0x20`, внутри образа), пересчёт checksum-байта формулой

```python
(-(sum(data[offset:offset + size]) - data[offset + 0x10])) & 0xFF
```

и построчное сканирование тела токенами (`body_offset`, `u8_0`, `u8_1`,
`u16_le`). Точный CLI скрипта — по его `--help`; в главе не фиксируется.
Вывод аудита — только метаданные, без публикации сырых тел.

Связь с прошлым результатом репозитория: неподписанный APCB
(только байтная checksum) — доказанно загружаемая поверхность
для кандидатов (`docs/research/2026-09-12-bios-vuln-inventory.md`):
«V3 — Unsigned APCB (byte checksum only). PROVEN bootable».
Это и есть рабочая точка инъекции из 6.2.1.

## 6.6. SMU mailbox-протокол

System Management Unit управляет питанием и частотами; прошивки SMU
(PMFW) подписаны (типы PSP-записей `0x08` и `0x12`, см. 6.2.2).
OS-уровень общается с SMU через mailbox в SMN-адресном пространстве.
Раздел стоит на исходниках драйвера `ryzen_smu` (`leogx9r/ryzen_smu`,
GitHub — read-only mirror основной GitLab-копии; README, `smu.h`
и `smu.c` прочитаны raw с ветки `master`).

### 6.6.1. Транспорт: PCI-конфигурация → SMN → mailbox

Проверено чтением `smu.h`/`smu.c`:

- Доступ к SMN идёт через PCI config-регистры корневого устройства:
  `SMU_PCI_ADDR_REG 0xC4` (адрес), `SMU_PCI_DATA_REG 0xC8` (данные).
  В комментарии заголовка отмечено: регистры `[0x60, 0x64]` и `[0xB4, 0xB8]`
  тоже работают, но это может быть arch-specific.
- Два mailbox: MP1 (обязательный) и RSMU (опциональный); у каждого —
  тройка адресов `cmd` / `rsp` / `args` в SMN-пространстве.
- Версии MP1-интерфейса: `IF_VERSION_9` … `IF_VERSION_13`.
- Команда SMU несёт до 6 32-битных аргументов (`SMU_REQ_MAX_ARGS 6`,
  структура `smu_req_args_t`).
- Детект CPU — по CPUID family/model (`0x17`, `0x19` и модели внутри),
  для каждого codename — своя тройка адресов mailbox.

Примеры адресов mailbox из `smu.c` (факт кода; привязку каждой тройки
к codename смотреть в самом файле, в главе не фиксируется):
MP1 `cmd/rsp/args` вида `0x3B10528/0x3B10564/0x3B10598`,
`0x3B10528/0x3B10564/0x3B10998`, `0x3B10530/0x3B1057C/0x3B109C4`;
RSMU вида `0x3B10524/0x3B10570/0x3B10A40`. Протокол опроса:
писать args → писать cmd → поллить rsp до кода возврата
(повторы `SMU_RETRIES_MIN 500` … `SMU_RETRIES_MAX 32768`).

### 6.6.2. Коды возврата (цитата из `smu.h`)

| Код | Имя | Смысл |
|-----|-----|-------|
| 0x01 | `SMU_Return_OK` | Успех |
| 0xFF | `SMU_Return_Failed` | Ошибка |
| 0xFE | `SMU_Return_UnknownCmd` | Неизвестная команда |
| 0xFD | `SMU_Return_CmdRejectedPrereq` | Отклонено: предусловия |
| 0xFC | `SMU_Return_CmdRejectedBusy` | Отклонено: занят |

Остальные коды (`0xFB…0xF6`) — внутренние коды самого драйвера
(таймаут, невалидный аргумент, неподдерживаемая функция и т.д.),
а не ответы SMU.

### 6.6.3. Поддерживаемые коднеймы (по README)

Colfax, Renoir, Picasso, Matisse, Castle Peak, Raven Ridge
(+2), Summit Ridge, Pinnacle Ridge, Rembrandt, Vermeer, Vangogh,
Cezanne и далее (список в README длиннее; BC250/Ariel в нём нет —
см. открытые вопросы). PM-таблица (телеметрия через DRAM):
драйвер работает с версией таблицы `0x240903` (`PM_TABLE_SUPPORTED_VERSION`
в `userspace/monitor_cpu.c`, файл прочитан, 25,979 байт).

### 6.6.4. Статус msg-id для BC250

Покомандных msg-id под SoC BC250 в открытых источниках этой главы нет —
и в главе их нет (выдумки запрещены). Что есть:

- Механизм отправки произвольного msg-id полностью описан выше (6.6.1):
  имея кандидата в ID, его можно послать и классифицировать ответ
  по 6.6.2 (`OK` / `UnknownCmd` / …). Это и есть легальный путь
  перебора с живым железом.
- Локальный observed-bytes факт (`docs/research/2026-09-17-t8-smu-msgtable-workerB.md`,
  прочитан): в SMU-теле разобран селектор `0x03220038`
  (стабилен в SRAM-адресации между старым и новым телом; декод —
  pypcode 4.0.0 Xtensa:LE:32, 128/128 и 100% валидация таблиц после
  поправки load-delta). Это наблюдение за внутренней таблицей PMFW,
  а не готовый OS-уровневый msg-id — не смешивать.
- PMFW-блоб BC250: тип PSP-записи 8 на `0x8FF000`, размер `0x40200`
  (якоря спецификации, см. 6.8).

## 6.7. HVB: статус разбора (ОТКРЫТО)

HVB вынесен в отдельный раздел требованием плана главы, но честный
статус такой: **расшифровка и детали в этой редакции не верифицированы**.

След верификации (все шаги выполнены 2026-09-24, всё мимо):

- Поиск по дереву изолированной копии (`docs/`, `specs/`, `scripts/`,
  `evidence/`, регистронезависимо): совпадений `hvb` нет.
- Исходники PSPTool (`entry.py`, default-ветка `master`): `hvb` нет.
- Текущий coreboot (`gh api search/code`, authenticated):
  `CONFIG_HVB` — 0 совпадений; символ удалён вместе со старым AGESA-кодом.
- Старый coreboot 4.1–4.4: `src/southbridge/amd/agesa/hudson/Kconfig`
  существует (6,316 байт), но `HVB` в нём нет; каталога
  `src/southbridge/amd/pi/avalon/` на теге 4.3 нет.
- Полный текст AGESA Arch2008 (#44065, 508 КБ): `HVB` нет.
- Поисковая выдача указывает на тред coreboot-gerrit 2014 года
  (Steppe Eagle / Avalon southbridge, опция `CONFIG_HVB=Bypass/HVB`),
  но сам тред как источник не открывался и не цитируется.

Рабочая гипотеза (не факт): HVB = Hardware Validated Boot, опция
southbridge эпохи Kabini/Steppe Eagle. До подтверждения по первоисточнику
никакие утверждения о семантике HVB в томе не делаются.

## 6.8. Карта регистров и якорей BC250

### 6.8.1. Якоря образа (локальные факты)

Из `specs/2026-09-10-bc250-firmware-audit.md` (прочитаны), baseline
`dump/2.bin`, 16 МиБ, SHA-256
`83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`:

| Якорь | Смещение | Размер / примечание |
|-------|----------|---------------------|
| `$PSP` | `0x8E0000` | 19 записей |
| `$BHD` | `0xAB0000` | BIOS-директория L1 |
| APCB | `0xAB1000` | `0xB70`, checksum `+0x10` |
| `$PS1` gasket | `0x982000` | `0x2E50` |
| `$PS1` policy | `0x9CA400` | `0x6E0` |
| IP discovery payload | `0x981A00` | Обнаружение HW IP |
| SMU/PMFW (type 8) | `0x8FF000` | `0x40200` |
| ABL0–ABL4 (types 0x30–0x34) | `0x99F700+` | ABL1 = 48,848 B, signed |

### 6.8.2. VCN MMIO: сверка с VCN2 (локальный факт)

Из `docs/action-logs/2026-09-14-vcn-mmio-map-audit.md` (прочитан):
сверка с публичным заголовком Linux v6.8
`drivers/gpu/drm/amd/include/asic_reg/vcn/vcn_2_0_0_offset.h`
(забирался 2026-09-14): `VERSION=0x5C9`, `POWER_STATUS=4`,
`STATUS=0x26F`, `SCRATCH9=0x1D`, все `BASE_IDX=1`. При записанном
`base1=0x7E00` (в двойных словах) байтовые адреса: `VERSION=0x20F24`,
`POWER_STATUS=0x1F810`, `STATUS=0x201BC`, `SCRATCH9=0x1F874`.
Вывод аудита: короткие метки исторического скрипта (`base0=0x7800`
плюс смещения `0xCA/0xBC/0xBD/0xC9`) конфликтуют с VCN2 —
в частности, `0x1E328` не является VERSION в этом интерфейсе.
Историческая полная лестница `enable_vcn.py` использует `base1=0x7E00`
и записывает all-ones; свежие бортовые проверки не запускались.

### 6.8.3. Комьюнити-разбор BC250 (внешний факт)

Документ `docs/vcn-registers.md` репозитория
`simpmix/bc250-encoding-decoding-fix` (прочитан raw с `HEAD`):
BC250 — «Cyan Skillfish» / APU PS5 «Oberon»; блок VCN 2.0.3
присутствует на кристалле (`UVD_VERSION = 0x0002001B` в PSP IP
Discovery), но заблокирован ранней boot-цепочкой:

- Таблица `SEC_GASKET` (`0x24` в PSP-таблице): подписанный набор
  из 926 пар `(address, value)`, исполняемый шифрованным `PSP_BL`
  до снятия reset с x86.
- ~816 записей программируют Data Fabric ACL (диапазон `0x09xxxxxx`),
  отрезая не-PSP мастеров от VCN-апертуры: записи host CPU через
  PCI config (`0xB8/0xBC`) молча дропаются, чтения отдают `0xFFFFFFFF`;
  доступ через SMU mailbox вешает mailbox (таймаут 5 с).
- Аппаратный harvesting-latch: `CC_UVD_HARVESTING = 0x3`
  по SMN `0x1f81c` и запись `[0x1f820] = 0x00185103`
  (запись политики, отсутствующая на рабочих VCN-устройствах
  вроде Steam Deck).

Это комьюнити-выводы, а не заявления AMD; приводятся как карта
для собственного воспроизведения, дословно по прочитанному файлу.
Связь с 6.6: «зависание mailbox» — именно тот класс поведения,
который виден через коды 6.6.2 на живом железе.

## 6.9. Класс проблем: пример Sinkclose (NVD-факт)

Владельцем уязвимостей в томе является [гл. 05](../../../../references/DEPENDENCIES.md#unavailable-local-inputs);
здесь — один платформенный пример с проверкой через NVD API
(`services.nvd.nist.gov/rest/json/cves/2.0?cveId=...`, прочитано):

- **CVE-2023-31315** (Sinkclose), опубликовано NVD 2024-08-12:
  «Improper validation in a model specific register (MSR) could allow
  a malicious program with ring0 access to modify SMM configuration
  while SMI lock is enabled, potentially leading to arbitrary code
  execution.»

Релевантность разделу: атака бьёт в конфигурацию SMM через MSR —
то самое состояние, которое на Intel-стороне проверяют модули CHIPSEC
`smm*`/`smrr` из [гл. 04](04-re-methodology.md), а на AMD-стороне
упирается в PSP/SMU-инициализацию из настоящей главы.

## 6.10. Упражнения с ответами

**У1. Кука-директория.** В дампе по смещению `0x8E0000` прочитаны байты
`24 50 53 50`. Что это и какие два поля читать дальше?

*Ответ.* Это кука PSP-директории L1: u32 little-endian `0x50535024`
(`PSP$`, см. 6.1.2). Дальше читать u32 `checksum` (+0x4) и u32
`num_entries` (+0x8), затем `additional_info` (+0xC) для версии
и режима адресации. Если вместо этого `24 42 48 44` — это `$BHD`
(BIOS-директория, 6.1.4).

**У2. ABL1 и APCB.** Предложите воспроизводимый путь проверки гипотезы
«ABL1 читает APCB» средствами глав 04 и 06.

*Ответ.* 1) Извлечь тело ABL1 (тип `0x31`) через PSPTool из образа
(6.2.3); сверить размер с инвентарём (BC250: 48,848 B).
2) Открыть в Ghidra/Rizin, найти обращения к области APCB
(адрес из BIOS-записи типа `0x60`, на BC250 — `0xAB1000`).
3) Подтверждением считается найденный кодовый путь чтения
с разбором Group/Type (6.5.1), а не соседство смещений.
Отрицательный результат тоже фиксируется в журнале. До выполнения —
гипотеза, а не факт (см. 6.3).

**У3. Диагностика SMU.** Посланный в MP1 mailbox msg-id вернулся
с `rsp = 0xFE`. Что это значит и что делать дальше?

*Ответ.* `0xFE` = `SMU_Return_UnknownCmd` (6.6.2): SMU жив
и отвечает, но такого msg-id не знает. Выводы: транспорт (PCI 0xC4/0xC8,
адреса mailbox) корректен; кандидат в ID отбрасывается, перебор
продолжается. Если бы вернулся `0xFC` (Busy) — повторить позже;
`0xFD` (Prereq) — искать предусловие; таймаут/зависание — сверять
с классом поведения из 6.8.3.

**У4. APCB-чек.** Опишите минимальную проверку целостности APCB
перед любыми выводами о токенах.

*Ответ.* По образцу `scripts/apcb_detail.py` (6.5.3): магия `APCB`
по ожидаемому смещению; размер `>= 0x20` и внутри образа; пересчёт
checksum-байта `+0x10` формулой из скрипта и сравнение с хранимым.
Только после прохождения всех трёх — разбор Group/Type/Token
(apcbtool, таблица openSIL). Несовпадение checksum — стоп и журнал,
а не «правка одного байта».

## 6.11. Источники к главе

- [coreboot `psp_efs.h`](https://github.com/coreboot/coreboot/blob/main/src/vendorcode/amd/psp/psp_efs.h)
  (прочитан raw: EFS, `0x55AA55AA`, doc #55758).
- [coreboot `psp_directory.h`](https://github.com/coreboot/coreboot/blob/main/src/vendorcode/amd/psp/psp_directory.h)
  (прочитан raw: заголовок/запись, куки, `amd_fw_type` incl. ABL0–7).
- [coreboot `bios_directory.h`](https://github.com/coreboot/coreboot/blob/main/src/vendorcode/amd/psp/bios_directory.h)
  (прочитан raw: BIOS-запись 24 байта, `amd_bios_type` incl. APCB `0x60`).
- [coreboot `amdfwtool.h` / `opts.c`](https://github.com/coreboot/coreboot/tree/main/util/amdfwtool)
  (прочитаны raw: usage, платформы, выравнивания, лимиты записей).
- [coreboot docs: AMD Family 17h](https://doc.coreboot.org/soc/amd/family17h.html)
  (открыто через jina reader: PSP под NDA, AGESA, Picasso, v5/Arch2008).
- [PSPTool README](https://github.com/PSPReverse/PSPTool)
  (прочитано через jina reader; HN: [story 20106060](https://news.ycombinator.com/item?id=20106060)
  (172/42), [Show HN 20102425](https://news.ycombinator.com/item?id=20102425),
  [story 20123863](https://news.ycombinator.com/item?id=20123863) —
  через HN Algolia API).
- [AGESA Arch2008 #44065 (зеркало 15h.org)](https://15h.org/images/f/f7/44065_Arch2008.pdf)
  (полный текст через jina reader, 508 КБ; точки входа — grep).
- [UTK APCB README](https://github.com/ragebone/utk/blob/main/UtkAmd/psp/firmware/apcb/README.md)
  (прочитан raw с `main` и `master`: модель Group/Type/Token).
- [apcbtool](https://github.com/Tim---/apcbtool/tree/main)
  (прочитан README ветки `main`).
- [openSIL `ApcbV3TokenUid.h` (пин `0a60473`)](https://github.com/openSIL/AGCL-R/blob/0a60473007604550bd0fb708cc1a820240d1bc51/AgesaPkg/Addendum/GenoaSp5Rdimm/Apcb/Inc/Genoa/ApcbV3TokenUid.h)
  (проверено: HTTP 200, 213,110 байт).
- [ryzen_smu README / `smu.h` / `smu.c`](https://github.com/leogx9r/ryzen_smu)
  (прочитаны raw с `master`: транспорт, mailbox-адреса, коды возврата).
- [simpmix BC250 VCN registers](https://github.com/simpmix/bc250-encoding-decoding-fix/blob/HEAD/docs/vcn-registers.md)
  (прочитан raw: SEC_GASKET, DF ACL, `0x1f81c`/`0x1f820`).
- [NVD CVE-2023-31315](https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2023-31315)
  (прочитана JSON-запись API: Sinkclose, 2024-08-12).
- Локально (прочитаны): `specs/2026-09-10-bc250-firmware-audit.md` (якоря),
  `docs/research/2026-09-12-bios-vuln-inventory.md` (ABL/APCB-строки),
  `docs/research/2026-09-17-t8-smu-msgtable-workerB.md` (селектор),
  `docs/action-logs/2026-09-14-vcn-mmio-map-audit.md` (VCN2-сверка),
  `scripts/apcb_detail.py` (checksum/скан).

## 6.12. Открытые вопросы

- HVB: расшифровка и семантика не верифицированы; след поисков —
  в 6.7. Рабочая гипотеза (не факт): Hardware Validated Boot эпохи
  Kabini/Steppe Eagle.
- «ABL1 читает APCB»: в изолированной копии не подтверждено (6.3, У2).
- Покомандные SMU msg-id под SoC BC250: открытой таблицы нет;
  путь — перебор через механизм 6.6.1 с классификацией по 6.6.2
  на живом железе. Локальный селектор `0x03220038` — наблюдение
  за внутренней таблицей PMFW, не OS msg-id.
- `oxidecomputer/amd-apcb`: упомянут в UTK README, сам репозиторий
  не открывался.
- Глубина покрытия apcbtool под BC250: проверен только README;
  прогон на `0xAB1000` — за рамками главы.
- amdfwtool: платформы BC250/Ariel в `enum platform` нет; сборка
  образа под BC250 этим инструментом не проверялась.
- PSP ROM/криптодеривация ключей, детали `$PS1`-верификации —
  вне открытых источников тома (наследовано).
- TRM неоднозначна — принята трактовка DRTM/TXT; перепроверить
  по первоисточнику (наследовано из прошлой версии главы).

