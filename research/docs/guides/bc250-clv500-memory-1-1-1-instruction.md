# BC-250 5.00 CLV: профиль памяти и проверка 1:1:1

Статус документа: офлайн-инструкция, `HARDWARE-PASS = NOT TESTED`.

## База

Рабочая база:

`/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`

SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`

Эталон для основного кандидата, НЕ готовый оптимизированный BIOS: `/home/OWNER/orca/projects/bc250/candidates/clv-native-menu-bridge-v001/integration/BC250_5.00_clv_MAIN_NATIVE_BASE.bin`. Это побайтная копия чистого CLV, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. Наличие native-полей не доказывает их доступность или действие на плате. Экспериментальный образ с меню-мостом отделён от основного:

`/home/OWNER/orca/projects/bc250/candidates/clv-native-menu-bridge-v001/integration/BC250_5.00_clv_MENU_ONLY_EXPERIMENTAL.bin`

SHA-256: `476076f280ca6385024db1bf643e042629153afff8bab2f9a52cc61c221e411e`

Он не содержит SoC-voltage unlock и не доказывает появление меню в реальном AMI Setup.

## Обязательный порядок

1. Сначала подтвердить фактическое `+VDDCR_SOC` и его BIOS-путь.
2. Только после этого менять частоты памяти.
3. Фактическое SoC не должно превышать `1.15 В`.
4. В текущем CLV-пакете действующий числовой SoC-setpoint не найден. Поля `VDDCR_VDD Voltage Offset` (`AmdSetup+0x6E5/+0x6E6`) являются неподтверждённым offset-путём и не переводятся в `1.15 В`. Не выставлять их наугад.
5. Поэтому до доказательства управления SoC и подтверждения фактического напряжения переход к разгону не подготовлен. Одного измерения без управления недостаточно. Это не ошибка инструкции, а safety-gate.

## Native BIOS paths

### MCLK

`UMC Common Options -> GDDR6 Common Options -> DRAM Timing Configuration -> I Accept -> Memory Clock Speed`

- QID `0x20F`
- `AmdSetup +0x316`
- значение CLV: `0x24`, label `1800MHz`
- предлагаемое значение пока не выбрано. `1800MHz` является сохранённой настройкой, не измерением.

### UCLK

`AMD CBS -> UMC Debug Options -> GDDR6 Debug Options -> GDDR6 DRAM Timing Configuration -> UclkDiv1M0`

- QID `0x229`
- `AmdSetup +0x330`
- `Enabled = 0x01`, `Auto = 0xFF`
- `Enabled` не является доказательством физического делителя `/1`. Назначение требует трассировки, рекомендация изменения пока отсутствует.

### Memory P-state

`AMD CBS -> UMC Debug Options -> GDDR6 Debug Options -> GDDR6 DRAM Controller Configuration -> DRAM Power Options -> Memory P-state`

- QID `0x25E`
- `AmdSetup +0x36D`
- `Auto = 0xFF`, `Enabled = 1`, `Disabled = 0`
- `Disabled` указан как требование native-help для DF override, не как уже проверенная рекомендация.

### FCLK

`AMD CBS -> SMU Debug Options -> SMU Features -> FCLK_DPM`

- QID `0x7045`
- `AmdSetup +0x6A3`
- `Auto = 0x0F`, `Enabled = 1`, `Disabled = 0`
- до подтверждения физической схемы оставить `Auto`; не считать это установленным FCLK.

### DF/FCLK override

`AMD CBS -> SMU Debug Options -> SMU Debug -> DF Clock Override Control / DF Clock Override`

- QID `0x37D/+0x703`, `0x37E/+0x704`
- CLV: `Manual`, `1420`
- native help требует `FCLK > UCLK` и отключённый Memory P-state.
- help рекомендует `FCLK > UCLK`, но проверенные окна кода не содержат сравнения этих частот. Это не доказывает ни запрет равенства, ни его допустимость. Способ установки 1:1:1 через DF override пока не подтверждён.

## Приёмка

### STATIC-PASS

Полный STATIC-PASS пока не присвоен. Перечисленные проверки меню и структуры являются лишь частью R5 исходного задания. Необходимо проверить все изменённые диапазоны, зависимости и воспроизводимость.

### HARDWARE-PASS

Остаётся `NOT TESTED`, пока на плате не подтверждены cold boot, сохранение настроек, фактический SoC `<=1.15 В`, реальные MCLK/UCLK/FCLK, отсутствие ошибок памяти и воспроизводимая задержка на одинаковом тесте.

## Откат

Для экспериментального образа использовать:

`/home/OWNER/orca/projects/bc250/candidates/clv-native-menu-bridge-v001/integration/ROM_ROLLBACK.sh`

Исходный ROM не перезаписывать. Физическая прошивка не входит в этот этап.

## Граница доказательств частот: повторная проверка 2026-09-23

- MCLK: enum `0x24` соответствует политике `1800` в отдельном ABL1-пути. Связь его token `7` с конкретным `AmdSetup+0x316` пока не доказана. Это не измеренные 1800 MHz.
- UCLK: `Enabled=1` копируется в `$INV 0x1204`. Физический делитель за этим значением не установлен.
- FCLK: поля `+0x703/+0x704` сериализуются в `$INV 0x1373/0x1374`. В ABL1 список `0x015F, 0x0160, 0` означает последовательные варианты поиска, а не пару «тип/значение» и не частоты.
- Проверенный путь ABL1: `0x1FB4 -> 0x4800 -> 0x49CC`. Связь этого пути с `$INV 0x1373/0x1374` и физическим генератором не доказана.
- Поэтому значения `1800/1800/1800` не являются готовым BIOS-рецептом. Соотношение 1:1:1 остаётся целью, а не результатом.

Команды и буквальные результаты трёх свежих проверок: `evidence/firmware-audit/20260923-clock-reconciliation/runs.json`. Все три завершились с кодом 0. PASS относится к ограниченным статическим проверкам, не к разгону.

## Первая чистая CLV-гипотеза без изменения напряжения

Для офлайн-проверки создан отдельный кандидат, повторяющий non-voltage часть архивного low-latency профиля:

`/home/OWNER/orca/projects/bc250/candidates/clv-native-menu-bridge-v001/integration/BC250_5.00_clv_LOW_LATENCY_HYPOTHESIS_NO_VOLTAGE.bin`

SHA-256: `cbb31e70d8e78c24da6f3f238f2dda52f5d0dc4fdacb7db93aad53b341b113e1`

Изменены только девять native request-полей: MCLK `1750`, Tcl Auto, DRAM Timing User Controls Auto, UclkDiv1M0 `0`, BankGroupSwap Disabled, PhyPowerSaving Disabled, Memory P-state Disabled, FCLK_DPM Disabled, DF `1400`. VDDCR_VDD, GFX, PPT и VRM-поля оставлены байт-в-байт чистыми.

Это диагностический кандидат, а не рекомендация и не доказательство `1:1:1`. Напряжение SoC в нём не повышается.

## Ближайшая к 1:1:1 статическая гипотеза

Отдельный кандидат на базе чистого CLV, без voltage/PPT/VRM изменений:

`/home/OWNER/orca/projects/bc250/candidates/clv-native-menu-bridge-v001/integration/BC250_5.00_clv_1TO1_HYPOTHESIS_1333_NO_VOLTAGE.bin`

SHA-256: `121c4d278df21e1eba63d3a02a3cd3f6f91ab8ea0cd1409722d36bd2863dfc30`

Поля: MCLK `1330` label, UclkDiv1M0 `Enabled`, DF `1333`, Tcl/DRAM User Controls Auto, BankGroupSwap/PhyPowerSaving/Memory P-state/FCLK_DPM Disabled. Это наиболее близкая к заявленному `1:1:1` гипотеза из архивного профиля 02. Физическое равенство частот не доказано.

### Ограничение новых гипотез

Оба NO_VOLTAGE образа являются только офлайн-образцами для сравнения байтов. Они не выполняют требование «сначала установить SoC», не являются выбранным основным кандидатом и не предназначены к прошивке по этой инструкции. Называть 1330/1333 «ближайшим 1:1:1» без установленных единиц некорректно. Физическая эквивалентность отсутствует. Не создавать дополнительные варианты, пока не определён проверяемый механизм применения полей. Порядок реальной настройки остаётся прежним: подтверждённое управление SoC и его напряжение, затем частоты.
