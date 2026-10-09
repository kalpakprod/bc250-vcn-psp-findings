# BC250 CLV500: подготовленная диагностика, запуск не разрешён

## Объект и границы

Цель остаётся BIOS500CLV, реальныйSoC первым и<=1.15В, физическоеMCLK:UCLK:FCLK1:1:1 и уменьшение задержки. Этот комплект только подготавливает аппаратный этап. Он не является BIOS-кандидатом или доказательством разгона.

Пользователь одобрил подготовку без запуска на плате. SSH, переустановка, перезагрузка, прошивка, изменение напряжений/частот, SMN/PCI-config и нагрузка не выполнялись.

Повторно использован `scripts/probe_bc250_clocks_readonly.py`, оригинал сохранён. Исправленная копия: `evidence/firmware-audit/20260923-diagnostic-preparation/MODIFIED_FILE.py`.

## Почему изменён старый сборщик

Старый main игнорировал аргументы: даже --help запускал сбор. Во время подготовки это вызвало чтение метаданных рабочей станции, неBC250; target cards=[] и другаяGPU была пропущена. Это ошибка подготовки, не аппаратный результат. Новая копия проверена на запрет чтения при default/--help. Полные командная строка ядра, имя машины и журналы не собираются.

## Этап0: только проверка плана

Уже выполнено локально. Никаких чтений sysfs/оборудования в этом режиме:

```sh
python3 evidence/firmware-audit/20260923-diagnostic-preparation/MODIFIED_FILE.py
```

Ожидается PLAN_ONLY, exit0. `--help` также не запускает сбор. Неизвестный аргумент даёт exit2 до чтения.

## Этап1: метаданные после отдельного разрешения

Цель: подтвердить, что команду выполняют на нужной плате, определить сообщаемые BIOS/kernel. Только cached sysfs vendor/device и BIOS version/date. Нет датчиков, gpu_metrics, mailbox и регистров. Жёсткий фильтр1002:13fe не меняется окружением. При двух подходящихGPU остановка до телеметрии.

Ниже команда подготовлена, НЕ запущена на плате. Запускать в согласованной сессии именноBC250, не на рабочей станции. Перед запуском: программатор/клипса сняты, штатное питание/охлаждение. Образ на плате должен быть отдельно идентифицирован; строкаP5.00 не доказывает SHA исходногоCLV.

```sh
umask 077
mkdir -p "$HOME/.cache/bc250"
capture_dir=$(mktemp -d "$HOME/.cache/bc250/baseline-XXXXXX") || exit 1
timeout --signal=TERM --kill-after=2s 15s python3 \
  evidence/firmware-audit/20260923-diagnostic-preparation/MODIFIED_FILE.py \
  --mode metadata > "$capture_dir/metadata.json" 2> "$capture_dir/metadata.stderr"
rc=$?
printf '%s\n' "$rc" > "$capture_dir/metadata.exit"
printf 'capture=%s exit=%s\n' "$capture_dir" "$rc"
```

Никакой root не требуется самим скриптом. Если доступ запрещён, не обходить права. UNKNOWN/missing BIOS сохраняется как null. ПроверкаPCI — фильтр кандидата, не полное доказательство ревизии/собственности.

## Этап2: ограниченная телеметрия, отдельное разрешение

После проверки этапа1 можно отдельно согласовать тот же сбор с `--mode telemetry`: только pp_dpm_mclk/fclk/socclk/sclk и rawgpu_metrics. Пока не запускался. Чтения sysfs могут вызвать обращения драйвера к железу, поэтому они не называются безусловно безопасными или аппаратно инертными. Длительность ограничивается внешним timeout, но он не гарантирует выход из зависшего kernelIO.

Результат показывает то, что сообщает драйвер. Равные MCLK/FCLK могут быть алиасом одного поля. Отображаемое VDDSOC не принимается как измерение физическогоSoC. Никакие частоты/напряжения не менять на основании одного такого отчёта.

## Этап3: прямые регистры и физическийSoC — пока не готов к запуску

Не включены в исполняемый сборщик. Существующий транспорт read_smu_reg пишет PCI-селекторB8, затем читаетBC; flock не защищает от конкурирующего обращения ядра. Нет проверенного доступа и независимо установленной карты трёх физических доменов. Список найденных SMU-адресов не является разрешением на чтение/запись. Требуются отдельный проверенный метод, согласованный риск и точная плата.

ФизическийSoC и аппаратная приёмка1:1:1 остаются открытыми. Не давать указания касаться неизвестных точек платы. Сначала подтвердить измерительный путь/ревизию, затем согласовать отдельное измерение. Пользовательский потолок1.15В не объявляется универсально безопасным.

## Коды и остановка

- 0: PLAN_ONLY, METADATA_ONLY или KERNEL_TELEMETRY_ONLY. Ни один не означает HARDWARE-PASS.
- 2: ошибка аргументов.
- 3: NO_TARGET, нужнаяGPU не обнаружена/identity недоступна.
- 4: PARTIAL_TELEMETRY, отсутствует/недоступен/слишком велик хотя бы один источник. Не выдавать за полный замер.
- 5: AMBIGUOUS_TARGET, несколько совпадений, телеметрия не читается.
- timeout/другой код: остановка, сохранить stdout/stderr/exit. Не повторять автоматически.

Откат настроек не требуется: сборщик их не пишет. ROLLBACK.sh откатывает только переданную копию скрипта к старому коду; это НЕ восстановлениеBIOS. Новую копию и старый сборщик не запускать в телеметрическом режиме без согласования.

## Офлайн-проверки и следующие решения

Тесты покрывают default/help безIO, неверные аргументы, отсутствие/несколькоGPU, точный фильтр, многозначный номерcard, отсутствие датчиков вmetadata, rawhash, неполные/слишком большие данные, выход symlink заfixture-root и неизменностьfixture.

Все аппаратные результаты ещё отсутствуют. Следующее решение пользователя: отдельный запуск Этапа1 на подтверждённойBC250. После его результата выбрать безопасный следующий наблюдаемый шаг, не обещать, что обычная телеметрия докажет1:1:1.

## Stage1 executed after alias2 authorization

2026-09-23T07:31:54Z: metadata-only collector piped over existing steammachine SSH alias with strict existing host-key checking, one connection attempt, client25s/remote15s timeout. Exit0,stderr empty. One matching card1 PCI1002:13fe. Kernel7.2.6-1.206-cachyos-bc250. Reported BIOSP3.00,date12/09/2021. This does NOT identify fullROM hash or prove cleanCLV500 is executing. No telemetry, settings, SMN, PCI-config, voltage or clock operation.

Additional binding recovered from memory/decisions.md D17: Linux DF/SMN probing was explicitly parked after a prior hard hang. Stage3 is not merely pending ordinary approval; it must not run through Linux under existing D17. Keep proposed direct-register work offline/UEFI-path review unless user explicitly lifts the named restriction for a concrete action. Current metadata collection did not use that path.

Evidence extends the same four roles: stage1-command.json and stage1-metadata.json, referenced in VERIFICATION.txt. First priority before attributing hardware behavior to500CLV is installed-image provenance. Do not infer installed image hash from a version string or require a new dump to continue unrelated offline work.
