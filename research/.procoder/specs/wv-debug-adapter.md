# wv-debug-adapter

Status: complete
Author: bc250 session, 2026-09-29
Related repo: `~/pico-bc250/` (peer eltex-65 sessions maintain the firmware)

## Problem

Стационарная домашняя BC-250 (Cyan Skillfish, PS5-derived APU, Bazzite/CachyOS
на gfx1013) закрыта на нескольких поверхностях: аппаратный VCN-декодер запретил
PSP-firewall (msg 0x1B mailbox — фабрикация, все SMN-адреса семейств
0x0900Cxxx, 0x0902Fxxx, 0x1FDxxxx стабильно вешают SMU на read и на write),
метрики питания и температуры не видно без Linux-агента внутри системы,
питание коммутируется физической кнопкой на корпусе или отдельной MQTT-розеткой
Eltex, DualSense требует проприетарного Sony-адаптера для передачи адаптивных
триггеров и haptic-v2, а джиг для одноразового изучения BIOS собирается на коленке
для каждой попытки. Существующие точечные проекты (BC250-Telemetry,
cyan-skillfish-governor, Decky-плагины) решают части задач, но не собраны в
единую железку, постоянно подключённую к плате. Владельцу нужен один
универсальный отладочный адаптер на Waveshare RP2350B-Plus-W, который висит
на плате навсегда через USB-Hub с внешней БП и одновременно: заменяет
Sony-Dongle для геймпада, включает и выключает консоль по кнопке PS,
выполняет TOCTOU-подмену BIOS каждый холодный boot (пока persistent
модифицированная BIOS не готова), снимает PMBus-метрики с наружной шины
I2C_HEADER1 и служит стеком для дальнейшей отладки (SPI-программатор, UART,
диагностика TPM/LPC/JTAG).

## Users

- **Владелец BC-250**: включает консоль кнопкой PS, играет, смотрит метрики
  в браузере телефона или в Steam Big Picture через Decky-плагин.
- **Агент-разработчик** (Claude/Codex/peer-сессии): читает UART-логи, снимает
  BIOS-снимки, программирует flash, arm-ит TOCTOU-подмену, обновляет
  прошивку коробочки через BOOTSEL или CDC.
- **Существующие клиенты Linux-стороны** (MangoHud, CoolerControl): бонусом
  получают температуру и ватты, потому что коробочка эмулирует формат вывода
  BC250-Telemetry.

## In scope

- [S-1] Страница-справочник в `docs/hardware/` — карта каждого распаянного
  header'а на плате BC-250 (имя, тип разъёма, пин→сигнал, уровень,
  рекомендация «использовать для…» или «не использовать»), основанная на
  локальном CAD, BoardView и фото платы владельца.
- [S-2] Расширение прошивки `~/pico-bc250/` — добавление двух режимов
  `MODE_MONITOR` и `MODE_POWER_CTRL` рядом с существующими
  `MODE_CONTROLLER` и `MODE_TOCTOU`; unified.uf2 продолжает быть одним
  образом с CDC-переключением.
- [S-3] BT-хост на BTstack как в DS5Dongle-WoL: одна постоянная пара с
  DualSense через MAC-whitelist в flash-TLV, PS-нажатие на выключенной
  консоли будит её через GPIO на Power-header.
- [S-4] TOCTOU-подмена BIOS-байтов каждый холодный boot через клипсу SOIC-8
  на BIOS-flash (первый выбор). Fallback — пины прямо в разъём J4004, если
  клипса физически не помещается в корпус. Рабочая последовательность
  SPI-снифер → mark → payload.
- [S-5] SPI-программатор через J4004 — CDC-команды `PROGRAM`, `VERIFY`,
  `SNAPSHOT`; автоматический weekly-snapshot BIOS образа на host-диск.
  Снифер использует PIO0 SM0, программатор — PIO0 SM1 (разные state
  machines на одном PIO-блоке, совместимы одновременно).
- [S-6] UART-отладчик на debug-header консоли (если распаян по данным S-1) —
  CDC/MQTT-мост, ring-буфер последних 8 КБ строк для команды `UART_LOG`.
- [S-7] I2C-снятие PMBus @ 0x60 через `I2C_HEADER1 → TPMS1 pins 4/6` каждые
  700ms; двойной формат публикации в MQTT — свой компактный для веб-панели и
  ключ-в-ключ-совместимый с BC250-Telemetry для существующих потребителей.
- [S-8] Диагностика TPM/LPC/JTAG-кандидатов на плате — фиксируется в карте
  header'ов из S-1 отметками «распаян и используется», «распаян не используется»,
  «не распаян».
- [S-9] Веб-панель на WV в домашнем Wi-Fi (`http://<wv-ip>/`) — секции
  Питание, Метрики, VCN-статус, DS5-инфо, «Расширенное» под чекбоксом;
  референс стиля — Decky-плагины LSFG.
- [S-10] Decky-плагин на самой BC-250 (TypeScript+React frontend, Python
  backend с MQTT-клиентом), подписан на метрики коробочки, показывает
  температуру и частоты в Quick Access Steam Big Picture. Исходники плагина
  живут sub-tree внутри `~/pico-bc250/tools/decky-plugin/`.
- [S-11] MQTT-эмуляция формата BC250-Telemetry — тонкий bridge на BC-250
  systemd-юнитом пишет `/run/bc250/*.json` из MQTT-топиков коробочки, чтобы
  MangoHud и CoolerControl видели метрики без изменений в них.

## Out of scope

- Управление разгоном (`cyan-skillfish-governor` внутри Linux BC-250 остаётся
  единственным контуром OC — коробочка не пишет в SMU и не крутит governor).
- Persistent модифицированная BIOS, при которой TOCTOU-rig можно вынуть из
  цепи (это отдельный research-трек через открытые planы `psp-breach`,
  `vcn-verifier-first`, `20260928-single-flash-emulator`).
- «Умный личный агент» уровня Hermes — исполнение `pcsh`-команд, LLM-логика
  на самой коробочке или на её backend — оставлено как future work за
  пределами этой спеки.
- Декодирование 11-байтовой структуры Sony adaptive-trigger FFB для
  генерации собственных эффектов на стороне коробочки (pass-through работает
  без декодирования; собственные эффекты не требуются в этой спеке).
- Пайка на плату BC-250 (только клипсы, пиновые разъёмы, DuPont).
- Розетка Eltex как канал включения консоли (остаётся только для замера ватт).
- Работа в поездке, AP-режим Wi-Fi без домашней сети (консоль стационарная,
  всегда дома).
- Поддержка более одной пары DualSense одновременно.
- Прямые SMN-writes к VCN-адресам (класс `0x0900Cxxx`, `0x0902Fxxx`,
  `0x1FDxxxx`, `0x101xxxxx` — все запрещены; см. MISTAKES 2026-09-25).

## Constraints

- Питание WV: строго USB-C от внешнего активного USB-Hub с собственной БП;
  никакой отдельной силовой линии, никакой пайки, никакого питания от BC-250.
- Никакой пайки на плату BC-250 (только клипсы, пиновые разъёмы, DuPont).
- Никакого прямого SMU-доступа через SMN-mailbox из коробочки —
  все известные пути к VCN-регистрам вешают SMU (см. MISTAKES).
- Никаких изменений в signed PSP-регионах (IPL, ABL1, SEC_GASKET, TOS) без
  явной карты границ подписи; таких карт у нас нет.
- Прошивка BC-250 никогда не пишется без свежего верифицированного дампа,
  подтверждённого способа восстановления и явного «да» владельца на
  конкретный образ и целевую плату.
- MQTT-брокер локальный (`127.0.0.1:1883` в HAOS), коробочка публикует туда.
- Один DualSense спарен навсегда — MAC-whitelist сохраняется в flash-TLV.
- Клипса SOIC-8 — первый выбор для доступа к BIOS-flash; переключение на
  пины J4004 разрешено только при доказанной физической невозможности
  клипсы в корпусе (документируется в action-log).
- Прошивка pico-bc250 продолжает собираться под Pico SDK 2.3.1 + TinyUSB 0.20.0,
  cpu-clock 400 MHz (те же constraint, что в Phase 1).
- BT-стек — BTstack (`pico_btstack_classic` + `pico_btstack_cyw43`), уже
  linked в текущем `CMakeLists.txt` pico-bc250; свой BT-стек не пишется.

## Interfaces

- **CDC-консоль коробочки** — команды: `PING`, `VERSION`, `STATUS`, `MODE`,
  `HELP`, `SELFTEST`, `LOAD`, `DUMP`, `SET`, `ARM`, `DISARM`, `LOADCLEAR`,
  `RESET`, `SNAPSHOT`, `PROGRAM`, `VERIFY`, `UART_LOG`, `POWER_ON`,
  `POWER_OFF`, `POWER_TOGGLE`.
- **MQTT publish** от коробочки: `bc250/pmbus/{vin,vout,iout,pout,temp}`,
  `bc250/uart/log`, `bc250/vcn/status`, `bc250/power/{state,event}`,
  `bc250/ds5/{connected,mac,battery}`, `bc250/wv/{uptime,rssi,mode}`.
- **MQTT emulation слой** на BC-250 (тонкий systemd-юнит) — подписывается на
  вышеперечисленные топики, пишет ключ-в-ключ формат BC250-Telemetry в
  `/run/bc250/cpu_vrm_temp`, `/run/bc250/gpu_vrm_pout`,
  `/run/apu_telemetry.json` каждые 700ms.
- **HTTP** — веб-панель коробочки на `http://<wv-ip>/`, статические HTML/JS/CSS
  из flash, WebSocket на `/ws` для стрима метрик.
- **BT (CYW43 + BTstack)** — коробочка как central, пара с одним DualSense,
  MAC-whitelist в flash-TLV (тег 0x424C434B 'BLCK', как в текущем
  pico-bc250 pairing-модуле).
- **USB Device (composite)** — HID (интерфейсы 0-1, эмуляция DualSense для
  BC-250), UAC1 (2-3), CDC (4-5).
- **GPIO Power-header** — 1 GPIO через опто-развязку на front-panel Power
  контакт BC-250; логика: пульс 200ms по PS-нажатию, если консоль не
  отвечает на I2C.
- **SPI (PIO0)** — клипса на BIOS-flash или J4004-пины, GP10/11/12 для
  снифера на SM0, GP16 для DO-override, GP20 для /HOLD на BC-250 flash;
  SM1 используется программатором в `SNAPSHOT`/`PROGRAM` циклах.
- **I2C (bit-bang или PIO)** — I2C_HEADER1 GP пины (уточняются в S-1),
  PMBus @ адрес 0x60.
- **Decky-плагин** — стандартный `plugin.json` + Python backend с
  `paho-mqtt` подпиской + React UI из TypeScript.

## Data

- **MAC-whitelist DualSense**: TLV flash-tag `0x424C434B` ('BLCK'),
  offset в flash уже занят в pico-bc250, реиспользуется.
- **Config коробочки** (mode, wifi-креды, mqtt-broker): flash offset
  `0xFFF000`, CRC-32 (унаследовано из Phase 1).
- **Weekly BIOS-snapshot**: `~/snapshots/bc250-bios-YYYY-MM-DD-<sha8>.bin` на
  host-диск владельца (не в WV flash — образ 32 МБ не помещается).
  Каталог создаётся владельцем однократно с mode 700.
- **Header-map**: страница в `docs/hardware/` в bc250-репо (создаётся по S-1,
  одна страница-справочник для всех агентов и для владельца).
- **Metrics history**: в коробочке не хранится, только RAM ring-buffer 60
  последних сэмплов; исторический график ведёт MQTT-клиент HAOS или свой
  файл-логгер на BC-250 (не в scope этой спеки).
- **UART ring-buffer**: 8 КБ последних строк, круговой, в RAM коробочки.
- **Wi-Fi креды и MQTT-broker**: `~/.config/pico-bc250/net.env` на host-стороне
  владельца, mode 600; заливаются в WV однократно через BOOTSEL при первой
  прошивке (не через MQTT-топик).

## Edge cases

- Консоль включили руками с корпуса (не через PS-геймпад) — коробочка
  детектирует по появлению I2C-response, переходит в MONITOR-режим без
  дополнительного щелчка Power-GPIO и без TOCTOU-arming (если TOCTOU уже
  сработал в первую миллисекунду boot).
- BT-connect от неспаренного DualSense (гость, соседский геймпад) — отказ
  по MAC-whitelist, лог в UART.
- Клипса ослабла или провод оборвался — TOCTOU промахивается, PSP отклоняет
  boot, зажигается только первый green blink. Коробочка детектирует по
  отсутствию ожидаемого READ на SPI-шине за 500ms и публикует
  `bc250/vcn/status=RIG_LOST`.
- MQTT-брокер лежит (HAOS перезагружается) — коробочка держит локальный
  буфер последних 60 сэмплов, публикует их когда broker поднимется.
- I2C_HEADER1 занята LPC-контроллером (NCT-чип) — коробочка использует
  arbitration lock: читает только в свободные окна (детект по SDA idle
  > 500µs), при коллизии откладывает попытку.
- USB-Hub выключен — коробочка мертва, консоль стартует без TOCTOU,
  VCN не активен, ни одна из функций не работает. Владелец видит это по
  отсутствию сигнала DualSense через коробочку — резервный вариант — Sony
  Dongle напрямую.
- Weekly-snapshot нашёл дифф от предыдущего snapshot'а — тревога, публикуется
  `bc250/vcn/status=BIOS_DRIFT`, следующий snapshot откладывается до
  расследования (защита от петли «плохой TOCTOU затер BIOS»).
- BT-стек CYW43 виснет — коробочка сбрасывается через watchdog каждые 30 сек
  простоя без событий; после ресета MAC-whitelist сохранён (в flash-TLV).
- DualSense не поддерживает адаптивные триггеры (старая fw) — pass-through
  вибрации всё равно работает; для триггеров игра шлёт FFB, устройство
  игнорирует.

## Failure modes

- Пропала совместимость с форматом BC250-Telemetry (изменилось имя ключа
  на их стороне) — MangoHud/CoolerControl молча читают старые данные, но
  наша веб-панель продолжает показывать актуальные через собственный формат.
- Decky-плагин не устанавливается (Decky Loader сломан обновлением SteamOS
  или Bazzite поменял пути) — веб-панель WV остаётся единственным UI.
- UART debug-header не распаян на плате BC-250 (обнаруживается в S-1) —
  S-6 недоступен; логи из BC-250 приходят только через тонкий MQTT-агент
  внутри Linux (`journalctl` → MQTT), это отдельная работа вне этой спеки.
- Клипса SOIC-8 не влезает в корпус BC-250 (физика) — путь S-4 переключается
  на пины J4004, что тоже требует физического доступа к разъёму; если и
  J4004 в корпусе закрыт — TOCTOU невозможен без снятия крышки для каждого
  boot, что противоречит «навсегда подключена» — вариант выносится в
  research-трек.
- I2C-конфликт с LPC-контроллером выше допустимого — падает частота
  PMBus-опроса до 3 сек вместо 700ms; веб-панель показывает stale.
- Прошивка WV окирпичена битым unified.uf2 — восстанавливается BOOTSEL и
  повторной заливкой предыдущей версии; MAC-whitelist в flash-TLV
  переживает.
- Wi-Fi CYW43 не поднимает домашний SSID (сменились креды) — веб-панель
  недоступна, но CDC-консоль по USB остаётся, метрики публикуются по MQTT
  только если broker в той же сети что и WV (не публикуются, если WV
  без сети).

## Acceptance criteria

- [ ] [S-1] `procoder check` — `TestHeadersMapCompleteness` fails if `docs/hardware/bc250-headers-map.md` is missing, any header row lacks name/connector/pin-map/status, or status is outside {"распаян и используется", "распаян не используется", "не распаян"}.
- [ ] [S-2] `procoder check` — `TestUnifiedSymbols` fails if `nm` on the freshly built `unified.elf` does not list both `monitor_init` and `power_ctrl_init`.
- [ ] [S-2] `procoder check` — `TestCdcModeAcceptsMonitor` fails if CDC `MODE monitor` returns anything other than `OK\r\n` within 200 ms.
- [ ] [S-3] `procoder check` — `TestBtWhitelistSurvivesColdCycle` fails if after a watchdog reset the paired DualSense does not auto-reconnect within 5 s or the BLCK TLV in flash is empty.
- [ ] [S-3] `procoder check` — `TestPsPressPulsesPowerGpio` fails if Power-GPIO pulse is absent, shorter than 180 ms, longer than 220 ms, or arrives later than 500 ms after PS press on a bench.
- [ ] [S-4] `procoder check` — `TestVcnStatusOkOverThreeColdBoots` fails if `bc250/vcn/status` MQTT topic does not read `OK` on all three consecutive cold boots or any read times out after 30 s.
- [ ] [S-4] `procoder check` — `TestRigLostPublishedOnMissingSpiRead` fails if the box does not publish `bc250/vcn/status=RIG_LOST` within 700 ms when the SPI clip is disconnected before boot.
- [ ] [S-5] `procoder check` — `TestSnapshotIntegrity` fails if CDC `SNAPSHOT` does not produce `~/snapshots/bc250-bios-<date>-<sha8>.bin` of exactly 32 MiB, or the sha256 prefix does not match `<sha8>` in the filename.
- [ ] [S-5] `procoder check` — `TestWeeklyTimerActiveAndRecent` fails if `systemctl status bc250-bios-snapshot.timer` is inactive or the last recorded run in `docs/action-logs/bc250-bios-snapshots.md` is older than 8 days.
- [ ] [S-6] `procoder check` — `TestUartLogReturnsBoundedLines` fails if CDC `UART_LOG 50` returns zero lines under active UART traffic, or returns more than 50 lines.
- [ ] [S-7] `procoder check` — `TestPmbusTopicFrequency` fails if the median interval between 20 consecutive `bc250/pmbus/vin` updates lies outside 650–750 ms.
- [ ] [S-7] `procoder check` — `TestPmbusMatchesBc250Telemetry` fails if delta between `bc250/pmbus/vin` and same-instant `/run/apu_telemetry.json` on BC-250 exceeds 0.05 V, or the `iout` delta exceeds 0.2 A.
- [ ] [S-8] `procoder check` — `TestTpmLpcJtagStatusesResolved` fails if any TPM/LPC/JTAG row in `docs/hardware/bc250-headers-map.md` lacks a status from S-1 or a non-empty CAD/photo justification.
- [ ] [S-9] `procoder check` — `TestWebPanelLayoutAt360Px` fails, in headless-Chromium at viewport 360×800 against `http://<wv-ip>/`, if "Питание", "Метрики", "VCN", "DS5" have `getBoundingClientRect().bottom` above 800 px or are absent from the DOM.
- [ ] [S-10] `procoder check` — `TestDeckyPluginManifestValid` fails if `~/pico-bc250/tools/decky-plugin/plugin.json` is missing or does not parse against Decky Loader schema (required: `name`, `author`, `api_version`, `publish`); manual "плагин в Quick Access, 700 ms" is logged in `docs/action-logs/<date>-decky-plugin-install.md`.
- [ ] [S-11] `procoder check` — `TestMqttBridgeUpdatesRunBc250` fails if publishing on `bc250/pmbus/temp` and reading `/run/bc250/cpu_vrm_temp` on BC-250 one second later does not show the same value (rounded to whole millidegrees).

## Open questions

<!-- All frontier questions from the 2026-09-29 grilling session were
     closed as decisions and moved into the appropriate section above.
     Physical facts that need the S-1 inventory pass are recorded there
     as acceptance criteria driven by that inventory, not as OPEN items:
     the inventory closes them by producing evidence, not by asking the
     user again. -->
