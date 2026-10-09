# UEFI-том: учебная программа от первокурсника до эксперта

Язык: русский. Термины и код — как есть (без перевода).
Формат: curriculum — 10 глав + индекс. Каждая глава:
пререквизиты, теория, практика, источники, открытые вопросы.

Как том собран: единственный писатель свёл пять отчётов-исследователей
в единый текст, проверил кросс-ссылки, унифицировал словарь терминов
(см. ниже) и вынес всё непроверенное в «Открытые вопросы».
Приоритетные отчёты несли главы 01–02, 03–04, 05, 06–07, 08–10;
слабых мест, требующих дописки с нуля, не осталось — все главы
имеют проверенные источники (список «Плохие отчёты» пуст).

## Как пользоваться

- Порядок чтения — строго 01 → 10. Каждая глава опирается на предыдущие.
- Уровень: 01–02 — freshman (первый курс, базовый C и Linux);
  03–05 — middle (сборка EDK2, статический анализ);
  06–07 — advanced (AMD PSP/AGESA, кейсы BC250);
  08–10 — expert (frontier, аудит, пробелы).
- Правило источников: каждое крупное утверждение снабжено ссылкой.
  Если источник не открылся при подготовке (403/404/таймаут) —
  это явно помечено как ОТКРЫТО, данные не выдумываются.

## Карта глав и зависимости

| Глава | Тема | Уровень | Опирается на |
|---|---|---|---|
| [01](01-boot-basics.md) | Основы загрузки: BIOS vs UEFI, reset vector, SPI flash | freshman | — |
| [02](../../../../references/DEPENDENCIES.md#unavailable-local-inputs) | UEFI/PI: фазы SEC/PEI/DXE/BDS, драйверы, SMM | freshman+ | 01 |
| [03](../../../../references/DEPENDENCIES.md#unavailable-local-inputs) | Тулчейн: EDK2, сборка, OVMF, прошивальщики, отладка | middle | 01–02 |
| [04](04-re-methodology.md) | Методология реверса прошивок | middle | 01–03 |
| [05](../../../../references/DEPENDENCIES.md#unavailable-local-inputs) | Ландшафт уязвимостей: 9 разборов + SMM/SPI (Sinkclose, ThinkPwn) | middle+ | 01–04 |
| [06](06-amd-platform.md) | Платформа AMD: PSP, AGESA, ABL, APCB, SMU | advanced | 01–05 |
| [07](07-bc250-cases.md) | Кейсы BC250: разборы из репозитория | advanced | 01–06 |
| [08](../../../../references/DEPENDENCIES.md#unavailable-local-inputs) | Frontier: measured boot, DRTM, memory safety, supply chain | expert | 01–07 |
| [09](../../../../references/DEPENDENCIES.md#unavailable-local-inputs) | Чек-лист программного аудита прошивки | expert | 01–08 |
| [10](10-skill-gaps.md) | Карта пробелов и план закрытия | expert | 01–09 |

Сквозные цепочки: reset vector (01 → 02 → 07) · DXE-инъекция
(02 → 04 → 06 → 07) · SMM/SMI (02 → 05 → 09) · PixieFAIL
(05 → 09 → 10) · PSP trust chain (06 → 07 → 09) · CHIPSEC/FWTS
(03 → 09 → 10).

## Единый словарь терминов

Пишется так везде по тому; варианты в скобках не употреблять.

- SPI NOR flash — микросхема прошивки (не «флэшка», не «SPI-флэш»).
- reset vector — `0xFFFFFFF0`, x86 real mode (не «вектор сброса» в коде).
- Firmware Volume (FV), Firmware File System (FFS), GUID — контейнеры PI.
- PE/COFF, `.efi`, TE — исполняемые форматы; DXE-драйвер — через дефис.
- SEC, PEI (PEIM, PPI, HOB), DXE (диспетчер, DEPEX), BDS — фазы PI.
- Boot Services (`gBS`), Runtime Services — сервисы UEFI.
- SMM, SMRAM, SMI-хендлер (не «SMI handler», не «SMI-обработчик» вперемешку).
- NVRAM, переменная UEFI (имя + GUID + атрибуты), `dbx`, Secure Boot.
- OVMF, EDK2, QEMU — тулчейн; UEFITool/UEFIExtract, flashrom, CH341A.
- PSP, `$PS1`, PSP-директория; AGESA, ABL0–ABL4; APCB-токен; SMU (PMFW, mailbox).
- Капсула обновления, anti-rollback, measured boot, SRTM/DRTM, TPM PCR.
- Finding — единичный результат аудита ([гл. 09](../../../../references/DEPENDENCIES.md#unavailable-local-inputs)).

## Сквозные открытые вопросы (статус — open, не выдумывать)

1. uefi.org PDF спеки (UEFI/PI/ACPI): 403/404 при подготовке — прямые ссылки
   не верифицированы; пользоваться HTML-зеркалом PI 1.8 и GitHub Tianocore.
2. BH-talk page, бюллетени AMI/Insyde/Lenovo: 403/404 — номера CVE/версий
   патчей сверять вручную, в том не фиксируются.
3. Intel BootGuard: официальная страница не открылась — детали не излагаются.
4. UDK Debugger manual + детали JTAG/XDP: не открывались — распиновку
   и процедуры не выдумывать.
5. CHIPSEC: точные CLI установки и шаги установки драйвера из manual
   построчно не проверялись (manual только PDF, wiki не открылась).
6. FWTS wiki (`wiki.ubuntu.com/FirmwareTestSuite`): jina timeout —
   пользоваться README с GitHub проекта FWTS.
7. CH347: подтверждён только факт `CONFIG_CH347_SPI`; wiring-гайд
   не проверен — для практики использовать CH341A.
8. PixieFAIL-видео: субтитров/проверенного транскрипта нет — цитируется
   только статья Eclypsium; yt-dlp URL не проверен.
9. TRM неоднозначна — в томе принята трактовка DRTM/TXT; требует
   перепроверки по первоисточнику.
10. Отдельный APCB-парсер не найден; покрытие — PSPTool + amdfwtool.
11. Реестр H1–H18 не найден; известны только H1/H19.
12. BC250: D7 вердикт только косвенный (D8 intent); cold-boot раздела нет.
13. BC250: 0b fill, живые FCLK, D1 SoC, аппрув v003b — open.
14. probe4l4 JSON проверен чтением (см. [гл. 07](07-bc250-cases.md)); остальные слоты
    (`probe4l`, `probe4l2/3/5/6/7`) — сверять по месту в `evidence/runtime/`.
15. BIOS-моддинг топ-тредами на HN почти не представлен — отдельного
    HN-источника в томе нет.

## Волна 3 (2026-09-24): углубление до учебника, ~370 КБ

- Закрыты п. 7 (CH347T-маршрут по проверенной сессии: `1a86:55db`,
  `ch347_spi`, 1.875M, точные команды — гл. 01/04), п. 15 (HN-треды:
  PSPTool, UEFITool, BlackLotus, Sinkclose, PKfail, PixieFAIL, LogoFAIL —
  с пермалинками), пробел гл. 07 (кейс 14: лесенка v004–v009, H1/H19,
  probe1–4, probe4l4 «gated clocks»).
- Уточнён п. 11: реестра H2–H18 как документа нет — в проекте
  использовались только метки H1 и H19 (см. кейс 14 гл. 07).
- Новые открытые (из глав волны 3):
- 16. HVB semantics unverified (гл. 06 §6.7 — задокументирован
  негативный поиск, только гипотеза).
- 17. Per-SoC SMU msg-id таблицы BC250 в открытых источниках нет
  (механизм + коды возврата верифицированы).
- 18. `oxidecomputer/amd-apcb` не открывался; покрытие apcbtool под
  BC250 шире README не тестировалось.
- 19. Наличие CSM (section `0x16`) в BC250 не подтверждено; точные
  границы FV в `dump/2.bin` требуют inventory родительской копии.
- 20. Binwalk v3 флаги, имя `chipsec_util spi dump`, версии QEMU
  в примерах — ориентиры, сверять с `--help`.

Детализация — в разделах «Открытые вопросы» каждой главы.

## Базовые источники (сквозные)

- Спецификации UEFI/PI на сайте UEFI Forum: [uefi.org/specifications](https://uefi.org/specifications)
  (ОТКРЫТО: при подготовке прямые ссылки на PDF отдавали 403/404;
  рабочие зеркала — HTML-версия PI 1.8:
  [Boot Paths](https://uefi.org/specs/PI/1.8/V1_Boot_Paths.html)).
- PI FAQ от Tianocore: [uefi_pi_faq.md](https://github.com/tianocore/tianocore-wiki.github.io/blob/HEAD/reference/faqs-glossaries/uefi_pi_faq.md).
- Исходники и доки EDK2: [tianocore/edk2](https://github.com/tianocore/edk2).
- CHIPSEC manual (PDF в репозитории): [chipsec-manual.pdf](https://github.com/chipsec/chipsec/raw/7e016af070f1a3ff26c3888e256e174c1274c183/chipsec-manual.pdf);
  код: [chipsec/chipsec](https://github.com/chipsec/chipsec).
- UEFITool: [LongSoft/UEFITool](https://github.com/LongSoft/UEFITool/tree/0.28.0),
  [README](https://github.com/longsoft/uefitool/blob/HEAD/README.md).
- PixieFAIL разбор: [Eclypsium: Understanding & Detecting PixieFail](https://eclypsium.com/blog/understanding-detecting-pixiefail-uefi-vulnerabilities/).
- Топ-5 векторов атак на прошивки: [Eclypsium](https://eclypsium.com/blog/the-top-5-firmware-and-hardware-attack-vectors/).
- Введение в UEFI для начинающих: [uefi-beginner.md](https://github.com/harkeryx/martins3.github.io/blob/HEAD/docs/uefi/uefi-beginner.md).
- Форум OSDev про написание своего UEFI: [osdev.org](https://forum.osdev.org/viewtopic.php?t=32645).
- Локальный writeup BC250: `docs/research/2026-09-23-bc250-platform-complete-writeup.md`
  (проверено чтением: §Executive Summary, §1–2, §4).
- Локальный замер PLL: `evidence/runtime/20260924-001510-probe4l4-pll.json`
  (проверено чтением).

## Соглашения тома

- Пути вида `docs/research/...`, `evidence/...`, `specs/...` — относительно корня
  репозитория bc250.
- «Проверено чтением» = автор тома открыл файл/страницу и подтверждает содержимое.
- «ОТКРЫТО» = источник недоступен или не проверен; утверждение не делается.
- Кросс-ссылки между главами — относительные (`[гл. 02](../../../../references/DEPENDENCIES.md#unavailable-local-inputs)`);
  якоря на разделы не используются (хрупко при правках).
