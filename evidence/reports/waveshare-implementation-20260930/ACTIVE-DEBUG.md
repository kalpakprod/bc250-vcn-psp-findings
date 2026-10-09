# Активный отладчик: функции и реальные ограничения

Полная цель сохранена. Наличие разъёма не означает готовую функцию или доступ к CPU/PSP. Никаких команд AMD не выполнено. Решение о включении стирания/записи BIOS пока не получено.

## SPI memory identify/read
Разъём/путь: J4004. Статус: DESIGN_PENDING_BUS_OWNERSHIP.
Уже реализовано: bounded input-only waveform observer only
Запрошено: active memory commands including full read
- shared FCH/flash bus
- PROGRAM# reset coupling is not proven isolation
- actual installed chip identity must be established
- no master commands during running AMD
Приёмка: exclusive bus ownership independently confirmed; two full reads equal; chip ID/size bound; no write side effects

## SPI erase/program/verify
Разъём/путь: J4004. Статус: SCOPE_DECISION_PENDING.
Уже реализовано: False
Запрошено: active debugger expansion; erase/program choice pending
- explicit write-scope decision outstanding
- verified pristine dump, recovery and exact-image approval before physical write
- preserve signed PSP regions; no bypass or race injection
Приёмка: offline allowlist/bounds/write protect tests; approved chip write and independent readback; recovery check

## UART receive/transmit
Разъём/путь: J5. Статус: RX_BUILT_TX_NOT_IMPLEMENTED.
Уже реализовано: 115200 8N1 RX GP9, explicit diagnostic/wiring confirmation, private capture
Запрошено: bidirectional serial debugging
- CAD/vendor direction: J5.4 board TX, J5.3 board RX
- documented3.3V; connector orientation not observed
- no presumed PSP console/protocol
Приёмка: real receive capture; benign documented TX exchange only after operator integration approval

## LPC POST observation
Разъём/путь: TPMS1. Статус: NOT_IMPLEMENTED.
Уже реализовано: False
Запрошено: POST observation and protocol diagnostics
- 2mm header not standard2.54mm cable
- 33MHz community clock claim is not measured unit clock
- must not drive shared LAD/frame/clock during observation
- not generic arbitrary LPC master
Приёмка: passive capture resource/bandwidth proof; known POST decoder fixtures and actual board capture

## SMBus/PMBus diagnostics
Разъём/путь: I2C_HEADER1. Статус: NOT_IMPLEMENTED.
Уже реализовано: Linux sensor collection is separate, not external SMBus implementation
Запрошено: documented peripheral reads and justified control
- CAD pin1 SDA/pin2 SCL; public orientation disagreement
- shared open-drain bus and pull-up voltage need evidence
- no blind scans/writes to power controllers while gaming
- device/register meanings and limits required before writes
Приёмка: connector/device identity and bus ownership evidence; read-only known-register fixture then live checked read

## JTAG/HDT CPU debug
Разъём/путь: J2. Статус: HARDWARE_ACCESS_UNPROVEN.
Уже реализовано: False
Запрошено: maximum accessible CPU debugging
- CAD supplies1.8V; Waveshare GPIO3.3V not direct compatible
- community describes unpopulated1.27mm footprint
- no solder/buy constraint retained; existing level conversion/connector availability unproven
- security/debug access may be restricted; no bypass promise
Приёмка: compatible connection/level conversion established; supported documented authenticated debug path

## Power/reset controls
Разъём/путь: existing HA + documented board controls. Статус: HA_BUILT_PHYSICAL_CONTROLS_PENDING.
Уже реализовано: gated HA power-on and local graceful shutdown helpers
Запрошено: physical control and reset in debugger
- access is not present permission to interrupt gameplay
- pin role/output topology must be proven for any physical control
- PROGRAM# is not general safe isolation
- no autonomous destructive reset loop
Приёмка: owned target/supply confirmed; one explicitly approved action and actual resulting state

## Fan RPM/PWM
Разъём/путь: CPU_FAN1/J4003 and NCT6686D Linux hwmon. Статус: RPM_BUILT_PWM_NOT_IMPLEMENTED.
Уже реализовано: nct sensors/collector, fresh fan1/fan2 forwarding and panel; Decky all available sensors
Запрошено: fan speed monitoring and documented control
- placement-only parsed facts do not prove all pin mappings
- Linux module names versus actual nct6686 sensor name differ
- PWM and tach are separate, fan power12V not Waveshare supply
- no changes to current cooling while gaming
Приёмка: actual channel/physical fan association; bounded approved PWM change with restore/current controller exclusivity

## DualSense/network/telemetry
Разъём/путь: USB/Bluetooth/WiFi. Статус: CODE_BUILT_RUNTIME_PENDING.
Уже реализовано: HID/audio/feedback source, WiFi/auth HTTP/MQTT, metrics and Decky
Запрошено: retain concurrently with normal operation
- diagnostic isolation intentionally stops controller output
- physical game/audio/reconnect/load acceptance not yet run
Приёмка: final-image flash with readback; input/audio/feedback/reconnect, gameplay and observation phases


## Проверка повторного использования
Используется уже связанный Pico SDK, а не новый внешний стек. UART raw TX API блокируется в ожиданииFIFO, поэтому будущая передача требует ограниченной очереди и бюджета. SPI init включает ведущий режим по умолчанию; даже READ генерирует тактирование/выходные биты, поэтому запуск только после подтверждения исключительного владения шиной. Чтение не равно пассивному наблюдению. Обычные команды памяти не требуют включения исторического rig/подмены PSP. См. active-debug-reuse.json для точной ревизии и хешей. Стирание/запись остаются решением заказчика, реализации пока нет.
