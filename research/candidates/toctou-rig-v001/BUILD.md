# BC-250 TOCTOU Rig v001 @ 400 MHz

> Статус на 2026-09-27: НЕ ИСПОЛЬЗОВАТЬ ДЛЯ ПОДКЛЮЧЕНИЯ. Документ сохранён как историческая схема. Владелец запретил рез дорожек, поднятие ножек и пайку на BC-250. В коде и схеме есть несогласованности, аппаратная работоспособность не подтверждена.
> Реестр расхождений: `docs/research/2026-09-27-toctou-document-audit.md`.


## Что это
Firmware для Waveshare RP2350B-Plus-W (Pico 2). Перехватывает SPI-чтения
PSP boot ROM к anchor window (0x9DB560..0x9DB6A0, 320 байт KDB root key)
и подменяет данные при первом чтении на оригинальные ключи.

Основан на: [ProjectSomnacin/SomnacinDumper PicoModchip](https://github.com/ProjectSomnacin/SomnacinDumper)

## Стратегия
- На SPI-флешке BC-250 записан патченный образ (наши ключи в KDB)
- PSP читает каждый модуль ДВАЖДЫ
- 1-е чтение (hash-check): Pico отдаёт ОРИГИНАЛЬНЫЕ 320 байт из SRAM
- 2-е чтение (signature verify): Pico пропускает данные с флешки (наши ключи)
- PSP принимает образ как валидный

## Overclock: 400 MHz
- VREG: 1.30V (`VREG_VOLTAGE_1_30`) — выставляется ДО переключения PLL
- PLL: VCO=1200 MHz (FBDIV=100), POSTDIV1=3, POSTDIV2=1 → 400 MHz
- Flash divider: 4 (QMI `m[0].timing.CLKDIV=4` → flash @ 100 MHz, safe for W25Q128)
- PIO timing: при 25 MHz SPI = 16 тактов/бит, при 50 MHz = 8 тактов/бит
- Рекомендуется радиатор на RP2350 при длительной работе

### Отличия от upstream SomnacinDumper
| Параметр | Upstream (RP2040) | Наш (RP2350B) |
|---|---|---|
| Частота | 198 MHz | 400 MHz |
| VREG | default | 1.30V |
| Flash divider | default | 4 (QMI) |
| LPC postcode | да (GPIO4-9) | нет (BC-250 не имеет LPC) |
| Target reset | GPIO16 | нет (ручной cold boot) |
| Режим | dual-flash CS switch | single-flash MISO proxy |

## Сборка
```bash
cd candidates/toctou-rig-v001
mkdir -p build && cd build
PICO_SDK_PATH=~/.cache/pico-sdk cmake -G Ninja -DCMAKE_BUILD_TYPE=Release ..
ninja
```

## Прошивка на Pico
1. Зажми BOOTSEL на Waveshare RP2350B-Plus-W
2. Подключи USB-C — появится диск RPI-RP2
3. Скопируй `build/bc250-toctou-rig.uf2` на диск
4. Pico перезагрузится с новой firmware

## Подключение к BC-250

### Схема: Pico между PSP и SPI-флешкой

```
                    BC-250 Board
  ┌─────────────────────────────────────────┐
  │  AMD PSP/FCH                            │
  │    MOSI ──────────┬─────────────────────┤── J4004.6 (MOSI)
  │    CLK  ──────────┼─────────────────────┤── J4004.4 (SCLK)
  │    CS#  ──────────┼─────────────────────┤── J4004.3 (CS)
  │    MISO ◄─────────┼── РАЗРЫВ ──┐        │   (J4004.5 MISO)
  │                   │            │        │   (J4004.1 VCC 3.3V, J4004.2 GND)
  │  SPI Flash (W25Q128, SOIC-8)   │        │
  │    DO (pin 2) ────┼────────────┼──┐     │
  │    CS# (pin 1) ───┼────────────┼──┼──┐  │
  │    GND (pin 4) ───┼────────────┼──┼──┼──┤── J4004.2 (GND)
  └───────────────────┼────────────┼──┼──┼──┘
                      │            │  │  │
              ┌───────┼────────────┼──┼──┼───────┐
              │  Waveshare RP2350B-Plus-W        │
              │                    │  │  │       │
              │  GP10 (MOSI sniff)─┘  │  │       │  ← left pin 14
              │  GP12 (CLK sniff) ────┘  │       │  ← left pin 16
              │  GP13 (CS# sniff) ───────┘       │  ← left pin 17
              │  GP16 (MISO IN ← flash DO) ──────┘  ← right pin 21
              │  GP17 (CS# OUT → flash CS#) ─────┘  ← right pin 22
              │  GP18 (MISO OUT → PSP) ──────────┐  ← right pin 24
              │  GND ────────────────────────────┤  ← any GND pin
              └──────────────────────────────────┘
                                                 │
                              к разрыву MISO ────┘
```

### Таблица пинов

| Waveshare пин | GPIO | Физ. позиция | Функция | Подключить к |
|---|---|---|---|---|
| GP10 | GPIO10 | Left, pin 14 | MOSI (слушает) | J4004 pin 6 (MOSI) |
| GP12 | GPIO12 | Left, pin 16 | CLK (слушает) | J4004 pin 4 (SCLK) |
| GP13 | GPIO13 | Left, pin 17 | CS# от PSP (слушает) | J4004 pin 3 (CS) |
| GP16 | GPIO16 | Right, pin 21 | MISO вход (от флешки DO) | Flash chip pin 2 (DO) |
| GP17 | GPIO17 | Right, pin 22 | CS# выход (к флешке) | Flash chip pin 1 (CS#) |
| GP18 | GPIO18 | Right, pin 24 | MISO выход (к PSP) | Разрыв MISO → J4004 pin 5 (MISO), сторона PSP |
| GND | — | Left pin 3/8/13/18 | Земля | J4004 pin 2 (GND) |

> J4004 pinout (сверено по фото платы 2026-09-22): pin1=VCC(3.3V), pin2=GND,
> pin3=CS, pin4=SCLK, pin5=MISO, pin6=MOSI, pin7/pin8=не определены (unk).
> НЕ подключать питание (pin1 VCC) к сигнальным GPIO Pico — это сожжёт вход.

### Физическая подготовка BC-250

1. **Найти SPI flash**: SOIC-8 чип (W25Q128.V) рядом с FCH, около J4004
2. **Проверить напряжение**: мультиметром на VCC flash (pin 8). Если 1.8V — нужен level shifter!
   Наш CH347T работает на 3.3V. Если flash 3.3V — подключаем напрямую.
3. **Разрыв MISO**: перерезать дорожку между flash DO (pin 2) и FCH MISO.
   Или: поднять pin 2 flash с платы (отпаять ножку).
   - Flash DO (pin 2) → GP16 Pico (вход)
   - GP18 Pico (выход) → FCH MISO (сторона PSP)
4. **CS# перехват**: flash CS# (pin 1) отключить от FCH, подключить к GP17 Pico.
   FCH CS# → GP13 Pico (вход, слушает).
5. **MOSI и CLK**: параллельно (не разрывать) — Pico только слушает.

### Важно
- **НЕ подавать питание на flash от Pico** — flash питается от платы
- **Общая земля обязательна** — GND Pico к GND платы (J4004 pin 2)
- **USB-C Pico подключить к ноутбуку** для serial monitor: `screen /dev/ttyACM0 115200`
- **Сначала включить Pico** (USB), дождаться `[TOCTOU] Armed.` в serial
- **Затем cold boot BC-250** (подать питание)

## Артефакт
- UF2: `build/bc250-toctou-rig.uf2`
- SHA256: `e4a70729648d1c06fdf0676ddbf99dd275180f5a3c2c338f7e4394571b145954`
- Size: 66560 bytes (130 UF2 blocks), UF2 magic valid
- Основан на: ProjectSomnacin/SomnacinDumper PicoModchip
