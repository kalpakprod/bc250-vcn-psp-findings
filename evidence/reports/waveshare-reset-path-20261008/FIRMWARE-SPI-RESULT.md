# SPI после reset: разбор байтов BC250 CLV5.00

2026-10-08, продолжение BC250-76 по запросу «продолжай». Предыдущий документальный этап: `AMD-SPI-RESULT.md`.

## Главный новый результат

В конкретном FchPei найден шаблон **Mode=6, NormSpeed=2** и код его применения. По AMD51192 это обычное однолинейное SPI-чтение с целевой частотой **33MHz**. Это значение из исследуемого образа, **не замер и не readback текущей платы**.

Для этой частоты существующий matched-header PIO-path опаздывает уже в оптимистичной модели: **25ns до первого output против 15.15ns до sample**, даже при сценарии 400MHz PIO и без задержек GPIO/FIFO/flash release. Новая привязка — к найденному firmware default, а не к прежним произвольным 25/50MHz сценариям. Это не измерение RP2350 и не разрешение разгона.

## Входы и инструменты

- Public baseline: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Исходные native UEFIExtract bodies: `evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.dump/`. Точные пути/секционные границы/хеши в `firmware-spi-evidence.json`.
- FchPei: IA32 TE,26568bytes, SHA-256 `08493ca078e74b050ffa85c9b80c50fb67b6f5fae6c467f9cb581af072f5fa08`.
- FchDxe: X64 PE,49024bytes, SHA-256 `9adfd93323dfee12f87b7f6740a5ba5b51b000495155e181a86aa827f815ffe1`.
- FchDxeAux3040bytes просмотрен при первоначальном разборе секций, не принят как свидетельство ранних команд.
- GNU objdump2.47 для ограниченного disassembly исполняемых секций. TE mapping: `file_offset=RVA-(StrippedSize-40)`, StrippedSize=1C0h, delta=198h. Адреса ниже — **module RVA**, не live адреса платы.
- Выборка1073строк: `firmware-spi-disassembly.txt`. Полная цепочка источников, таблицы и timing-model output: `firmware-spi-evidence.json`. Входы не модифицировались. Cutter/MCP не запускались, capstone/pypcode отсутствуют, зависимости не устанавливались.

## 1. Как найден реальный SPI initializer

Цепочка внутри FchPei:

1. Entry240h →15A8h через13C9h.
2. 15EDh вызывает13CEh, где13E1h копирует128байт default-шаблона из link-time pointer09E39918h. Шаблон: RVA6350h, TE-file61B8h.
3. Поля: template[0Ch]=6, template[17h]=2, template[0Ah]=0, template[76h]=0.
4. 164Ch →3A55h →task launcher4D95h с таблицей09E39998h. Третий указатель в таблице, TE-file6240h, ведёт на SPI initializer4C59h. Launcher читает указатель и делает indirect call4DAFh; это не только найденный мёртвый helper.
5. 4C9Dh читает config[17h];4CAAh уменьшает значение на1;4CABh сдвигает на12 и записывает NormSpeed bits13:12. Для2 получается01b. AMD51192, стр.4-499:01b=33MHz.
6. 4CF7h читает Mode=config[0Ch]. Для6 ветка4D18h..4D34h устанавливает SPI read-mode bits в110b. AMD51192, стр.4-498: Normal read до66MHz по normal-speed register.

В checked template это не quad mode. Частота до этой PEI-инициализации и ранние hardware/PSP reads не восстановлены этим путём. Другой installed image, конфигурация или более поздняя настройка не исключаются.

## 2. Opcode/FIFO-путь и условные требования к responder

FchPei4762h — общий alternate SPI transaction helper:

- 4837h берёт opcode из аргумента[ebp+0Ch].
- 483Eh пишет opcode вFEC10000h.
- 484Bh пишет TX/RX counters вFEC10001h.
- 4850h устанавливает Execute bit16;46D9h ждёт очищения80010000h (busy/execute), FIFO находится поFEC1000Ch.

Восстановлены условные paths, не объявленные фактическим wire trace:

| RVA | Действие |
|---|---|
| 492Bh..4957h | Helper RDID9Fh с возвратом3байт через FIFO. |
| 470Bh..4735h | Read05h и повтор доWEL(bit1)=1, внутреннего timeout нет. |
| 4736h..4761h | Read05h и повтор, покаBUSY(bit0)=1, внутреннего timeout нет. |
| 4958h..4A05h | Проверка QE по opcode/длине/mask из profile. Для двухбайтового profile дополнительно читает05h и второй регистр. |
| 4A06h..4A3Ah | Если QE не подтверждён: pre-op06h и table-selected status write, затем poll. |
| 4C19h..4C58h | Может пропустить detection при config[76h]!=0; иначе RDID и profile lookup. |

**Не переносить эти вызовы безусловно на default-mode6:** mode6 идёт по прямой read-mode ветке; QE-check вызывается для других mode values или auto mode. Возврат FFh/00h не является универсально корректным status response: на активированной WEL/BUSY-poll ветке он способен оставить firmware в бесконечном ожидании. Наличие outer retry счётчика не ограничивает внутренний poll.

Default QE table имеет12records, stride19h, terminator0, RVA6450h/file62B8h. В ней есть WinbondEF4015/16/17, read35h/write01h/two-status-bytes/mask0200h. **EF4018 в этой таблице нет.** WinbondRevF §8.1.1 определяет именноEF4018 дляW25Q128JV-IQ/JQ. Это ограничение default fallback table, не доказанный дефект работы платы: есть mode6 и bypass, реальная конфигурация не прочитана. Не подменять ID меньшей микросхемы ради прохождения lookup.

## 3. Два найденных ABh — не команда пробуждения flash

В FchDxe найдено два byte-immediateABh: RVA2B3Fh и2BD7h. Data flow в обоих случаях:

`byteABh на stack → r8=указатель → edx=550h → helperEA4h → EE0h/EE3h: OUT DX,AL`.

Это запись индекса в I/O port550h; соседние обращения используют551h. Это **не** найденный opcode write в SPI controller/FIFO. Два совпадения AB не приняты за доказательство пробуждения оригинальной flash.

Обратное также не доказано: эта выборка FchPei/FchDxe не исключает ABh из on-die ROM, другого firmware component, динамической команды или ранней аппаратной логики.

## 4. First-bit budget для найденного default

Повторно использована существующая модель `candidates/single-flash-emulator-v001/rig_timing.py` на текущем `src/rig/spi_toctou.pio`, без правки исходника.10PIOcycles после final-header CLK falling до первого OUT; optimistic400MHz даёт25ns. SPI33MHz даёт15.1515ns до следующего sample. Margin=-130/33PIOcycles, то есть опоздание≈9.85ns ещё до физических задержек.

`src/rig/rig.c` содержит функцию400MHz overclock и clkdiv1, но она здесь не запускалась. Даже этот заложенный сценарий не исправляет latency первого бита. Скорость steady-state loop не доказывает своевременность первого output. HOLD по-прежнему отключён для владельцем названного Q-чипа; timing-model не подтверждает его release.

## Ранняя граница и следующая обязанность

В точном PSP directory отдельно выделен type1 region8E0400h,46592bytes. Типовой $PS1/HeaderFile layout не распознан: magic check/bounded rom-size не подходят. Не выдан ciphertext/неизвестный wrapper за ARM executable; не сделан вывод об encryption только по этим несовпадениям. Ключи/IV/signatures не экспортировались, дешифрование не запускалось.

Применимый образ неизменяемого PSP ROM не идентифицирован в просмотренных областях корпуса. Поэтому **первые SPI-команды после нужного reset, положение ABh и фактическое повторение требуемых PSP reads остаются неизвестны**. Повторный scan байтаAB эту границу не закрывает.

Для H2 найден положительный input: post-x86 FchPei default — single-lane33MHz, а не обязательный quad. Найден и отрицательный input: нынешний matched-header responder не успевает при33MHz. До аппаратного arm нужны ранний trace/reset qualification и иной своевременный/full responder. Архитектура не менялась, firmware gates сохранены. Исследование не закрывает mandatory PSP/TOCTOU и не требует покупки нового измерительного оборудования.

Итог происхождения/байтов, вторичный LLVM decode и gate записываются в `firmware-validation-20261008.txt`. Hardware tests, SSH, USB-проверка, clock changes, reset/B9/AB, прошивка, сборка и изменения production не выполнялись.
