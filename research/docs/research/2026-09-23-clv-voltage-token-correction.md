# Исправление карты CBS voltage-токенов CLV

Дата: 2026-09-23

## Проверенный исходник

`evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`  
SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`

## Что исправлено

В прежнем тексте `0x1364` был назван `VDDCR_GFX_OFFSET`. IFR и producer-map exact CLV показывают другое:

| CBS `$INV` token | AmdSetup offset | Поле                               |
| ---------------- | --------------: | ---------------------------------- |
| `0x1363`         |        `+0x6E5` | `VDDCR_VDD Voltage Offset Control` |
| `0x1364`         |        `+0x6E6` | `VDDCR_VDD Voltage Offset`         |
| `0x1365`         |        `+0x6EA` | `VDDCR_GFX Voltage Offset Control` |
| `0x1366`         |        `+0x6EB` | `VDDCR_GFX Voltage Offset`         |

Следовательно, старое описание `0x1364 = GFX` отозвано. Оно не должно использоваться для выбора значения.

## Что фактически доказано

`verify_inv_token_ownership.py` на pinned 233-module extraction завершился кодом `0`. Для обоих токенов:

- ровно семь producer-модулей;
- по одному producer-сайту на модуль;
- ноль immediate request sites;
- ROM occurrences соответствуют producer sites;
- положительные control-токены находятся там, где ожидается запрос.

Это доказывает отсутствие **прямого immediate `$INV`-request** для `0x1363/0x1364` в проверенном UEFI corpus. Это не доказывает невозможность вычисляемого или закрытого consumer-path в SMU/PSP.

## Решение для разгона

`0x1363/0x1364` не переводятся в `1.15 В`. В основной или экспериментальный BIOS нельзя записывать raw voltage value по этим полям. Фактический SoC-путь остаётся не найден. `HARDWARE-PASS` не запускался.

Fresh raw-ROM verification command: `python3 scripts/verify_clv_voltage_token_map.py` -> `PASS`, exit `0`.

The new check pins the ROM hash, checks 28 producer windows (seven per field), verifies token and payload-store bytes and runs fresh i386 objdump decoding. Evidence: `evidence/firmware-audit/20260923-clv-voltage-map/result.json`, `stderr.txt`, `exit.txt`. It does not prove runtime execution or identify the physical rail. Initial failed script: full operands were incorrectly compared with bare token; exit 1. Fixed verifier result: exit 0, empty stderr.

## Косвенный путь, который удалось закрыть

В `AmdNbioSmuV10Pei` найден и проверен отдельный heap-lookup путь. Он передаёт handle `0xA019` в lookup, проверяет заголовок возвращённого объекта `0xDB1099CC` и возвращает указатель на его поля. Это не запрос `$INV`, не NVTB parser и не voltage actuator. Проверено 114 строк инструкций побайтно против тела модуля, плюс 13 независимых byte anchors и два прямых call-edge. Evidence: `evidence/firmware-audit/20260923-smu-pei-heap/result.json`, exit `0`.

Это сужает неизвестное: этот конкретный SMU PEI heap path не является доказанным потребителем `0x1363/0x1364`. Полный arbitrary computed/pointer-flow аудит всё ещё не закрыт.

## Caller of the A019 lookup

`AmdIdsDebugPrintDxe` directly passes `0xA019` into the lookup, accepts the object only after checking `0xDB1099CC`, then reads object offset `+0x18` and returns it to an IDS/debug-print path. Ten independent PE32 byte anchors verify this route, exit `0`. It contains no voltage token and no SMU voltage-register write. Evidence: `evidence/firmware-audit/20260923-smu-pei-heap/ids-debug-path.json`.
