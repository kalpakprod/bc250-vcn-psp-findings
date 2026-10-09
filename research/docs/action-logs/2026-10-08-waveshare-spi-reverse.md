# BC250-76: продолжение реверса PROGRAM#/reset/SPI

Запросы: «выясняй», «скачай справочник», «продолжай реверс». 2026-10-08.

## Выполнено

- Использованы уже полученные AMD51192, Winbond IQ/JQ RevF, LRC RevA и rawCAD. Дополнительно получен официальный AMD51205 Rev3.00, без установки/исполнения внешнего кода.
- Сопоставлены reset, SPI ROM/bridge/idle, GPIO mux и IMC ROM-ownership поля. Подтверждения high-Z основных SPI-выходов при SYS_RST# не найдено. Defaults не перенесены на liveBC250.
- Исправлен преждевременный вывод о конфликте flash pin2/5: host-side DI/DO naming совместим с Winbond pinout. Обновлён MISTAKES.md.
- Сохранена H2: opcode/FIFO самого FCH для B9 может избежать внешней передачи мастерства именно для этой команды. Это не доказанный hardware workflow, не принятая архитектура и не реализованный full responder.
- Сохранены результат `reports/waveshare-reset-path-20261008/AMD-SPI-RESULT.md`,27выборок страниц и повторный rawCAD trace `amd-spi-evidence.json`, память `memory/waveshare-spi-reset.md`. Обновлены WAVESHARE.md и действующая PSP/TOCTOUspec.

## Доступ и границы

Plane MCP workitem CRUD не обнаружен; штатный `scripts/plane/check.py BC250 --timeout 10` успешно проверил HTTPS workspace/board. Задача создана sharedHTTPSclient без вывода token. Старые задачи не закрыты. BraveSearch MCP не настроен, Tavily429; SearxNG не дал применимого databook. OpenCLI Brave/DDG — Navigation rejected, OpenTabs navigation/read tool не обнаружен. AMD51205 получен напрямую, поэтому общей недоступности AMD или Plane не заявляется.

Копии перед изменением документов: `~/.cache/bc250-spi-reverse-20261008-before/`. Firmware/code/production не менялись. Нет SSH/USB-проверки, подключений, измерений, GPIO/MMIO-записей, reset/B9/AB, QE, прошивки, сборок или покупки.

## Итоговая проверка

`reports/waveshare-reset-path-20261008/validation-20261008.txt`: совпали5хешей/размеров входов,27выборок страниц с оригинальнымиPDF,8CAD-netjoins и цитируемые поля. Графический pinout D606 воспроизводится побайтно из PDF; свежий OCR подтверждает CATHODE/ANODE, направление pin1/pin2 прочитано визуально. Первичная попытка поиска CATHODE в pdftotext не прошла, поскольку diagram графический; источник не изменён, проверка перенесена на исходный rendering/OCR. `make test`:12тестов PASS, exit0. Полный вывод — `contract-gate-20261008.txt` рядом. Firmware/hardwarechecks не выполнялись.

## Продолжение по «продолжай»: exact firmware bytes

Запрос сохранён в открытой BC250-76. Исследован publicCLV5.00ea578104..., nativeUEFIExtract FchPei/FchDxe/FchDxeAux; GNUobjdump2.47, без Cutter/server lifecycle, новых зависимостей и исполнения firmware. Capstone/pypcode отсутствуют; не устанавливались. Для TE использованы настоящие section boundaries, StrippedSize1C0h и adjustment198h, не слепой decode header/data как executable.

Entry/task table доведены до SPIinitializer; copieddefaultMode6/NormSpeed2 даёт targetsingle-lane33MHz. Подтверждён softwaretimingblocker: current10cyclePIOpath25ns при400MHzscenario против15.15ns deadline33MHz. Источник — байты/справочник/model, не liveзамер или overclock. Восстановлены conditionalopcode/FIFO/RDID/status/QEpaths и внутренние unboundedpolls. Два ABimmediates FchDxe доведены до I/O550h, не SPI. DefaultQEtable12entries безEF4018 не выдана за дефект платы; defaultMode6 обходится безQEcheck. Type1PSP genericlayout не распознан и не выдан заARMcode, дешифрование не проводилось.

Сохранены `FIRMWARE-SPI-RESULT.md`, `firmware-spi-evidence.json`, `firmware-spi-disassembly.txt` в `reports/waveshare-reset-path-20261008/`; rootcontext/memory/spec обновлены. До docchanges копии в `~/.cache/bc250-spi-firmware-20261008/before-docs/`. Новая итоговая проверка записана в `firmware-validation-20261008.txt` рядом: pinned16MiBparent и3native modules совпали с fresh projectFV/FFS extraction; section/template/14taskpointer/12QEprofile checks PASS;13instruction anchors вторично decodedLLVM23.1.1; оба pollbackedges иAB-to-I/O550h bytes совпали. CurrentPIO/model hashes иmargin-130/33cycles совпали. `make test`:12PASS, exit0. Полный gate log — `firmware-contract-gate-20261008.txt`. Hardware acceptance не заявлена.

## Точка остановки

Есть точный post-x8633MHzdefault и доказанный modeltimingblocker нынешнего responder. Применимые pad/reset timing A68H для H1 либо earlyhardware/PSP command/reset trace для H2 всё ещё не получены. Наличие ABбайта в I/Oкоде не является flashopcode, отсутствие такого совпадения не доказывает отсутствие AB в immutableROM. Нужны timely/full responder и ранний trace, а не ещё один scanAB. Никаких аппаратных команд, прошивки, clock changes, изменения code/gates или production не было.
