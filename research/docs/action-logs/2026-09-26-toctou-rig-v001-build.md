# TOCTOU Rig v001 — build log

## Intent

Собрать firmware для Waveshare RP2350B-Plus-W (Pico 2) для TOCTOU-атаки на PSP boot chain BC-250.
Основа: SomnacinDumper PicoModchip (PIO programs: spi_inject, spi_trigger, spi_reader).
Адаптация: single-flash, MISO substitution на anchor window 0x9DB560..0x9DB6A0 (320 байт).

## Toolchain

- arm-none-eabi-gcc 16.2.0 (Arch extra)
- cmake 4.4.3, ninja 1.13.2
- Pico SDK 2.x (git, ~/.cache/pico-sdk) + tinyusb submodule
- SomnacinDumper (git, ~/.cache/SomnacinDumper)

## Result

- UF2: `candidates/toctou-rig-v001/build/bc250-toctou-rig.uf2`
- SHA256: `79dc8bddbad390189e8fed8782c9bac530746ded5fe968ecfa90967908e57410`
- Size: 64512 bytes (126 UF2 blocks)
- UF2 magic: 0x0A324655 (valid)
- Build: clean, zero warnings on main.c/spihack.c

## Anchor data

- Source: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` @ 0x9DB560
- 320 bytes, SHA256: `de87b7db4cbcafee1b2ecfdab44c7524c4957ad1b2699361e0f1a9442852d1fc`
- First 16 bytes: `39bfc1922fa14ef285d9ae87e696d2b2` (kid 39BF = root key anchor)

## Дальше

- Прошить UF2 на Pico (BOOTSEL + drag-drop)
- Прошить патченный образ `91de01eb` на SPI-флешку BC-250 через CH347T
- Подключить Pico между PSP и флешкой (разрыв MISO)
- Cold boot, наблюдать через USB serial (screen /dev/ttyACM0 115200)

## Rebuild v001.1 — overclock + miso_proxy PIO

### Changes

1. **Overclock 300 MHz** — `set_sys_clock_khz(300000, true)` в main.c перед stdio_init.
   При 25 МГц SPI = 12 PIO-тактов на бит, при 50 МГц = 6 тактов. Достаточно.
   На стоковых 150 МГц при 50 МГц SPI = 3 такта — недостаточно для proxy.

2. **miso_proxy.pio** — новая PIO-программа для single-flash режима.
   Проблема: spi_inject.pio рассчитан на dual-flash CE switching.
   В passthrough он просто переключает CS между двумя чипами.
   Для single-flash нужен MISO proxy: читает DO с флешки → выдаёт на MISO к PSP.
   В inject-режиме выдаёт данные из FIFO вместо flash DO.

### Архитектурная проблема (найдена при анализе)

spi_inject.pio в passthrough-режиме опускает CS# второго чипа — данные идут
напрямую с флешки на PSP. В single-flash режиме это означает bus contention:
и флешка, и GPIO18 Pico пытаются управлять MISO одновременно.
miso_proxy.pio решает это: Pico ВСЕГДА управляет MISO к PSP (GPIO18),
а флешку читает через отдельный GPIO16. Линия MISO между чипом и FCH разорвана.

### Артефакт

a61944074f1e2d55373360b931d0503a2fb65962d980fdbeb83d15ff42841f7d candidates/toctou-rig-v001/build/bc250-toctou-rig.uf2
