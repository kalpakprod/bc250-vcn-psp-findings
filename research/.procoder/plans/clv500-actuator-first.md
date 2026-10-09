# CLV 5.00 — от аппаратной записи к BIOS-профилю

Status: in progress
Spec: .procoder/specs/clv500-actuator-first.md

## Goal

Выполнить исходные R1–R8: воспроизводимый BIOS-кандидат на чистом CLV и инструкция для снижения задержек с проверкой 1:1:1, SoC первым и не выше 1.15 В. Офлайн-доказательства и аппаратная приёмка раздельны. Ни меню, ни гипотетические частоты не заменяют результат.

## Planning anchor

TARGET: evidence/donor/retroweb-20260916/BC250_5.00_clv.bin.
SHA-256: ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.

Прочитаны текущий tracker, исходный goal, MISTAKES.md, отчёт O11, локальные lateral/concept-fan и procoder, ранее полученный drunk-claude SKILL.md. Пользователь просит применить оба подхода и построить план. Новые аппаратные действия не разрешены. Пользователь одобрил выполнение сообщением «делай» после выдачи плана. Выполнение начато, аппаратные действия по-прежнему отдельно согласуются.

## Architecture

Два технических направления: источник настройки до обучения памяти и фактическое программирование частот/напряжения. Соединять их только доказанными вызовами и потоком данных. APOB сначала классифицировать по коду: результат/описание состояния или вход управления. Не назначать ему роль потребителя $INV заранее.

## Constraints

- Чистый CLV неизменен. BIOS3.00, vdd80 и архивные профили — не рабочая база.
- SoC-first и потолок1.15 В сохраняются. Более низкая частота не заменяет цель1:1:1.
- Не выпускать новые NO_VOLTAGE/1TO1 варианты до найденного механизма применения.
- Экспериментальный menu-bridge остаётся отдельным образом, не voltage unlock.
- Не менять подписанные области, CMOS/reset-защиты или контрольные суммы вслепую.
- Неизвестный аппаратный ответ в тесте — явный неизвестный вход/остановка, не молчаливый ноль.
- Фотографии и свежие SPI-read не являются условием офлайн-анализа.
- Никакой прошивки, тяжёлой нагрузки, установки глобальных инструментов или изменения платы без соответствующего отдельного разрешения.

## Connected logic and existing evidence

- Native NVAR/CBS acquisition, fallback, serializer и generic reader уже исполнены в ограниченных стендах. Не повторять без изменения, влияющего на их корректность.
- $INV содержит запросы, но доказанный stock requester нужных clock tokens не найден.
- O11: CD9 перебирает записи каталогов. BHD type61 содержит destination0x04000000. Это не доказанная команда SMU.
- Отчёт O11 смешивает CD9 с B09. Не переносить эту неточность в архитектуру: отдельно проследить аргументы/возвращённые адреса CD9 и роль B09.
- Сценарий сообщества включает ручное изменение feedback и SoC выше1.2 В. Это не допустимый рецепт для данного задания.
- Модульная сборка menu-only, ссылки, откат и воспроизводимость уже проверены в своих ограничениях.

## Creative pass: drunk-claude + lateral/concept-fan

Текущий путь: разобрать очередной буфер. Первый подъём: определить, что реально управляет частотой. Второй: получить воспроизводимую аппаратную конфигурацию и меньшую задержку.

На уровне управления рассмотрены: поиск от входных полей, обратная трассировка от записей, контрфактические изменения источников. На уровне результата: доказанный native-рецепт, минимальный патч действующей политики, либо обоснованное ограничение конкретного требования. Последнее не объявлять достижением1:1:1.

- O8: «BIOS выдаёт свои записи». Собрать адрес/значение/стек вызовов реальной функции программирования в офлайн-исполнении. Сначала использовать существующий стенд, затем оценить, нужен ли эмулятор другой ISA.
- O9: «Источники намеренно спорят». Разные помеченные значения в NVRAM и другом подтверждённом входе. Смотреть только на выбранную политику или команду программирования, не на очередной сериализованный буфер.
- O7: «Убить подозреваемый вход». Испортить одну копию входных данных в памяти и сравнить достигнутый выходной путь. Работает только после найденного потребителя. Отсутствие эффекта не доказывает глобальную ненужность.
- O10: сравнение реализаций того же пункта с подтверждённым рабочим эталоном. Запасная ветка, пока такого эталона нет.

Отброшены: новые имена для старых тестов, ещё один принудительный запрос generic reader, случайный перебор напряжения, повторные hashes вместо причинного эксперимента, подмена1:1:1 обычным уменьшением задержки.

Вывод: проблема не в отсутствии ещё одного поля меню. Проверяется причинная цепь от доступного пользователю значения до аппаратной команды. У неё должны быть оба конца.

## Use cases

U1: штатный пункт действительно управляет нужной линией/частотой — выпустить инструкцию без лишнего патча.
U2: пункт читается, но значение перекрывает другая политика — минимально исправить доказанное место выбора на копии.
U3: нужной команды нет в доступном интерфейсе — документировать точное ограничение и отличать неизвестное от невозможного.
U4: найден офлайн-кандидат — передать отдельный пакет для последующей согласованной аппаратной приёмки, не объявлять её пройденной.

## Task 1: P1 — исправить карту загрузки и роли APOB/APCB

Files: docs/research/2026-09-23-amdmemam4-directory-lookup.md, evidence/firmware-audit/20260919-inv-token-consumers/AmdMemAm4Pei-1ef4e7b94467.bin (read-only), evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin (read-only).
Interfaces: CD9 entry type61, BHD destination0x04000000, APOB signature check and subsequent reads.

- [x] Разделить directory lookup, получение адреса, чтение данных и отладочный вывод. Исправить смешение B09/CD9.
- [ ] Установить, кто читает/пишет APOB и в какой фазе. Не выводить хронологию только из названия модуля.
- [ ] Выдать небольшую карту доказанных связей с адресами и неизвестными границами.

Gate: каждое направление стрелки подтверждено аргументами, инструкцией чтения/записи или точным внешним контрактом. Если APOB — выход, запретить дальнейший поиск «команды настройки» в его потребителях без нового основания.

## Task 2: P2 — найти программирование, затем идти назад

Files: existing extracted ABL/SMU/PEI modules, docs/research/2026-09-21-memory-clock-units-next.md, docs/research/2026-09-21-df-consumer-next.md, docs/research/2026-09-21-rt8237e-pus1-control-path.md (read-only inputs). New focused evidence stays under evidence/firmware-audit/.
Interfaces: конкретные команды/регистры UMC/DF и регулятора питания, если они установлены.

- [x] Для MCLK/UCLK/FCLK составить список кандидатов функций записи по инструкциям и вызывающему коду, не по сходству названий. — SMU-сторона закрыта 2026-09-23: единственный движок записи частотных доменов = FUN_00023890(domain, code) → FUN_000235c8 → SMN-окно 0x010FFE00+0x200 (+IPC-ветка для доменов 3/4). Домены: FCLK 0x0E → SMN 0x0115C0FC, UCLK 0x0F/0x11 → 0x0115C8FC/0x0116C0FC, производные 0x10/0x12 → 0x0115C924/0x0116C124; селекторы q3 0x1D доменов 0x0E–0x12 не достигают (массив из образа). См. docs/research/2026-09-23-r3-clock-actuator-map.md, verify_r3.py 46/46.
- [x] Producer-цепочки закрыты (2026-09-23, проход 2): Setup-поля не доходят до бутовых частот. UCLK-таблица 0x5F1E-0x5F9A мертва (слот [sp,#4] перезатирается дефолтом FCLK на 0x5FA8), живой аргумент = безусловный LSR#1; строки прошивки называют сервисы (SetupFclkPll/SetupUclkPll/ConfigSocRail). MCLK = APCB item 7 (+0x482, 0x24=1800), CMOS игнорируется (census CLOSED-NEGATIVE). UclkDiv1M0 — сирота на обеих поверхностях (NVTB 0x1204 без читателя; APCB token 21 без читателя). Эмпирика: 4 SYNC-профиля оператора (обе попытки 1:1:1) правят только NVRAM, APCB побайтово идентичен донору — моста Setup→APCB нет. Фальсификатор (a) закрыт. verify_r3b.py PASS; док §4a.
- [x] Для SoC отделить уставку от telemetry calibration и VDD/GFX/MEMIO. Проверить путь до исполнительного узла, единицы и знак. — RESOLVED 2026-09-23 как доказанное ограничение: SoC-уставки в прошивке нет (полный свип обработчиков robin_5: только домены CPU/GFX), приёмника на плате нет (PUS1 RT8237E аналоговый, SVI2 ведёт только на ISL69247). См. docs/research/2026-09-23-r2-soc-vddcr-limitation.md, verify_r2.py 52/52.
- [ ] Проследить операнд выбранной записи назад к источнику политики. Назначение неизвестного регистра оставить неизвестным.

Gate: для каждого результата указаны source -> conversion/condition -> command/write и недоказанные связи. Для SoC обязательна привязка к нужной линии. Список адресов без назначения не считается готовым setter.

## Task 3: P3 — причинный тест, а не демонстрация парсера

Files: existing native harnesses reused when their ISA/path fits; new isolated harness only for a named missing edge. Original firmware files read-only.
Interfaces: один входной параметр, заданная среда, трасса конкретного выхода из P2.

- [ ] Сначала зафиксировать baseline и ожидаемые различающиеся исходы двух гипотез.
- [ ] Изменить один вход только в памяти стенда. Проверить, изменяется ли вывод на границе реального управления.
- [ ] Добавить отрицательный контроль: неправильный namespace/token либо отключённый control при неизменном payload.
- [ ] Вернуть исходный вход и подтвердить исходную трассу.

Gate: изменение выхода обусловлено входом, проверены тип/единицы, версия кода и все подставленные ответы. Прямой вызов generic reader с нужным токеном не доказывает stock reachability. Копирование байта не доказывает clock actuation.

## Task 4: P4 — выбрать обоснованный BIOS-профиль

Files: docs/guides/bc250-clv500-memory-1-1-1-instruction.md and the existing acceptance matrix.
Interfaces: точный путь меню -> значение -> эффект -> проверка -> откат.

- [ ] Сначала подтвердить управление SoC, выбрать уставку с учётом потолка1.15 В и погрешности. Не присваивать напряжение raw35/80/100.
- [ ] Согласовать единицы трёх доменов. 1330 и1333 не объявлять равными без доказанной кодировки.
- [ ] Выбрать исходный профиль из проверенных зависимостей и ограничений обучения памяти. Не выбирать его из красивого имени архива.
- [ ] Если для шага нет доказательств, оставить его невыполненным. Альтернативный режим обозначить отдельно.

Gate: таблица исходное/предлагаемое/подтверждённое без скрытых предположений. Порядок реального изменения: SoC, подтверждение напряжения, затем частоты.

## Task 5: P5 — минимальная сборка и независимая проверка

Files: выбранный канонический комплект MODIFIED_FILE/DIFF_FILE/VERIFICATION.txt/ROLLBACK.sh, existing menu-bridge integration, tests/ only when required by actual implementation.
Interfaces: clean CLV -> reproducible transform -> candidate; separate experimental menu variant.

- [ ] До правки записать baseline/hash и минимальный изменяемый символ/поле.
- [ ] Только после P2–P4 выполнить минимальную обоснованную правку на копии. Не добавлять фиктивный voltage setter.
- [ ] Проверить восстановление из патча, все изменённые диапазоны, FV/FFS/checksums, сохранность PSP/$PS1/APCB вне согласованных изменений.
- [ ] Выполнить одинаковые baseline/modified/rollback проверки и совпадение восстановленного хеша.
- [ ] Получить независимое ревью рискованного diff без передачи собственных выводов как доказанного факта.

Gate: полный R5, а не один успешный firmware_audit. `procoder check` по фактически изменённым файлам и `procoder test` дополняют firmware-specific проверки, не заменяют их.

## Task 6: P6 — аппаратная приёмка отдельным этапом

Files: существующий операторский runbook и инструкция, без автоматического выполнения команд на плате.
Interfaces: точный хеш утверждённого образа, recovery dump, независимый способ восстановления.

- [ ] Подготовить cold-boot/readback и проверку доступности/сохранения пунктов.
- [ ] Подготовить метод проверки фактического SoC, трёх частот и ошибок памяти. Проверить пригодность инструмента для BC-250.
- [ ] Сравнить задержки до/после при одинаковой методике и условиях. Конкретные нагрузочные тесты запускать только после отдельного разрешения.

Gate: HARDWARE-PASS только по наблюдениям. Этот план не разрешает прошивку. Недостаток аппаратных данных не блокирует независимые P1–P5.

## Stop and decision rules

- Каждый шаг обязан изменить решение о следующем действии. Повторная зелёная проверка без изменения входов — не новый результат.
- После двух неудачных гипотез — новые данные. После трёх попыток без новой информации — закончить эту ветку, записать границу и перейти к следующей независимой ветке, если она есть.
- Не переписывать тест под ожидаемое число. Исправление неверного gate должно содержать независимое обоснование и исходную ошибку.
- Не создавать новые меню/ROM-варианты ради количества артефактов.
- Доказанные SoC setter и единицы/применение частот — обязательны для практического рецепта. Их отсутствие не маскировать объявлением цели выполненной.

## Open questions

Technical, executor-owned: boot-time writer of APOB; true source of ABL clock policy; final UCLK ratio semantics; whether changing policy requires reset/training/next boot. Закрыто 2026-09-23: real SoC programming path — не существует (доказанное ограничение, R2).

User-owned, deferred until a concrete package exists: exact image/target flash approval, hardware tests and any new paid tool/service. No new question is required merely to deliver this plan.

## Decision log

- User: use drunk-claude + lateral, then make plan.
- Existing user decisions remain: clean5.00 CLV, BIOS-only setup, goal1:1:1 and lower latency, SoC first <=1.15 V, separate experimental bridge, static/hardware acceptance split.
- Recommendation within those decisions: complete O11 by correcting source/output direction, then O8 reverse tracing. O9/O7 only after an output-side path exists.
- Pre-mortem: wrong architecture causes endless tracing -> P1 gate; test stubs manufacture success -> P3 explicit assumptions; unsafe numeric substitution -> P2/P4 rail/unit gate; document proliferation -> stop rules.

## Plan validation

Read back this file and compare every R1–R8 with the copied original specification. Run `procoder plan check clv500-actuator-first` for plan structure. Passing that check validates planning structure only, not feasibility or firmware.

## Execution checkpoint

P1 partial: CD9 directory and APOB read-side corrected, B09 debug-message path distinguished. Producer/boot timing remains open. P2 started: exact ISL69247 write helper6ED stages word bytes into70/71 with command register21. Three instrumented process tests0123->0456->0123 confirm causal output and restore. This is VCORE-labelled, NOT SoC, no actual IO. Next: actual caller enable predicate and destination-rail classification, plus independent clock-write branch. Evidence: docs/research/2026-09-23-actuator-first-staging.md.

Execution correction after user feedback: enforce existing stop rules, no renewed generic-reader or packaging tests as functional progress. Next BIOS evidence must advance the actual clock/SoC programming path or eliminate a specific hypothesis. Tool integration remains a separate task, not a firmware outcome.

R2 checkpoint 2026-09-23 (Plane #2): SoC-актюатор — доказанное ограничение. Полный свип почтовых обработчиков robin_5 (очереди 0/1/2/3/5, ~120 функций) + GenCAD-трассировка: SVI2-порт платы несёт только плоскости CPU/GFX на ISL69247, PUS1 (RT8237E, +VDDCR_SOC) не имеет цифрового интерфейса, SOC_EN аппаратно-последовательностный, в CBS нет SoC-полей (VDDCR_SOC = калибровка телеметрии). Следствие: SoC ≤1.15 В через BIOS недостижимо на этой ревизии платы — решение оператора (убрать требование или перевести в hardware-трек) требуется для P4. Слова телеметрии 1275/912 мВ — друп-калибровки CPU/GFX, не SoC. Доказательства: docs/research/2026-09-23-r2-soc-vddcr-limitation.md; evidence/firmware-audit/20260923-r2-svi-census/ (verify_r2.py 52/52). Хеш robin_5 выверен: канонический cae8617c…3268b39e59f37, 63-символьный «вариант» прошлой сессии не существует ни в одном файле репозитория.
