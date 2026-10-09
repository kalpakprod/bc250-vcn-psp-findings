# Waveshare: интеграция существующего recorder/watchdog

> Scope correction07.10 after owner objection: input12V measurement, an INA3221 purchase and a required external measurement module are agent proposals, not confirmed mandatory requirements. Their absence is NOT a blocker for the whole approved adapter scope. Earlier physical-voltage wording below describes an inferred implementation, not a verbatim owner requirement. Existing code/build/hardware gaps remain; this correction does not mark acceptance passed. Source distinction and correction: WAVESHARE.md, MISTAKES.md. No firmware/hardware change.

## 1. Scope
Продолжить единый финальный образ. Текущая доступная программная работа: реально включить recorder/watchdog, HOST_ALIVE и выгрузку событий. Не добавлять выдуманный измерительный канал, не прошивать и не менять BC250. Это не сужение конечной цели: физические напряжения и аппаратная приёмка остаются открыты.

## 2. Anchor
Владелец: «Работай до результата или конкретного препятствия». BC250-70. Источники/полная цель: WAVESHARE.md, планы 30 сентября и 3 октября. Бэкап: waveshare-recorder-integration-before-20261007.zip.

## 3. Existing logic
Существующие recorder/watchdog не связаны с main/CMake/CDC. HOST_ALIVE сейчас обновляет лишь freshness Linux-метрик. Main обслуживает USB, controller/network и диагностику. HTTP уже имеет авторизацию. Использовать эти пути без второго scheduler/USB stack.

## 4. Use cases
- До первого HOST_ALIVE отсутствие отправителя означает unknown, не heartbeat_lost.
- После первого HOST_ALIVE тишина >=5с пишет одно heartbeat_lost; возвращение пишет recovered. Не называть это доказанным kernel hang.
- Потеря host heartbeat не перезапускает Waveshare или AMD. Сам watchdog Waveshare питается завершёнными проходами обслуживаемых задач, не HOST_ALIVE.
- В штатном цикле watchdog требует USB/recorder и controller/network только при успешной инициализации wireless. До завершения startup его не включать: длительность ранних SDK init ещё не принята на аппаратуре.
- События доступны через bounded cursor API в CDC и существующую защищённую HTTP-службу; unknown value сериализуется null. Кольцо не является долговременным хранилищем.

## 5. Checklist
- [x] Include modules, shared recorder, runtime heartbeat/watchdog wiring.
- [x] CDC RECORDER_STATUS / RECORDER_READ cursor, authenticated HTTP /api/recorder and /api/recorder?cursor=N.
- [x] Native behavior test: loss/recovery/readout, and self-watchdog progress versus lost external host. An isolated disabled heartbeat-loss state is rejected.
- [x] Existing affected tests + contract gate + scoped procoder executed. Firmware compilation, RAM relocation and UF2 structure passed. Hardware/flash acceptance pending.

Results: Waveshare suite 90/91; pre-existing SPI textual gate expects diagnostic-only while unchanged implementation also permits monitor. Contract fails because AGENTS.md lacks expected project text map. Procoder fails formatting/SDK include context/pytest collection. No checks weakened. Artifacts and logs: reports/waveshare-recorder-integration-20261007/. No final readiness claimed.

## 6. Questions/blockers
Fresh BOOTSEL info/save -p -v confirmed RP2350A4 and installed historical5c1d program (841512bytes, SHA2562636b11a6e6f588f01dbfdddf31998eb9c6eef470b294e6c6617fae19deee9ff). USB absence is no longer a blocker; installed application's VERSION/STATUS previously returned no recognized reply. No firmware was loaded, erased or rebooted by tooling.

Owner confirms only Waveshare and wires. Physical sensor and validated solderless input12V tap are absent. AdafruitINA3221/product6062 is a sourced candidate for voltage-only measurement, not a finalized wiring plan and not a series power path for BC250. Cable, power tap and independent supply still need physical confirmation. PMBus capability is not denied, but live addresses/rail mapping and safe shared-bus sampling are unproven. Evidence: reports/waveshare-voltage-equipment-20261007/RESULT.md. Full firmware/hardware acceptance, voltage history and durable storage remain pending; unavailable hardware does not complete remaining software work.

## 7. Decisions
Use the existing 16-event ring and no flash-per-sample writes. Watchdog only resets the RP MCU, never BC250. Shared static recorder follows existing singleton metric state. Add no external dependencies. Rollback is the scoped snapshot above, plus removal of newly created test/spec only after copying them if needed.
