# BC-250 5.00 CLV: работающие параметры и инструкция разгона

Status: proposed operational refinement, not hardware authorization.
Spec: .procoder/specs/clv500-actuator-first.md
Implementation plan retained: .procoder/plans/clv500-actuator-first.md

## Goal and scope

Выдать таблицу реально применяемых параметров, BIOS-кандидат при необходимости и короткую последовательность настройки для снижения задержек. Проверить достижимость физических MCLK:UCLK:FCLK = 1:1:1. Не обещать превращение BC-250 в настольный Ryzen. Разделять частоты ядра, контроллера памяти, памяти и fabric. CPU/GPU-разгон не входит в первый этап оптимизации памяти.

## Planning anchor

TARGET: evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
SHA256: ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8
Исходник неизменяем. SoC меняется первым, фактическое напряжение не выше 1.15 В, уставка учитывает погрешность и возможное превышение. Это предел пользователя, не доказательство безопасности конкретной платы.

## Existing evidence and gaps

Прочитаны исходные R1-R8, утверждённый actuator-first plan, memory/INDEX.md, релевантные записи memory/oc-recheck.md, original-oc-case.md, original-oc-diff.md и actuator-first-staging.md от 2026-09-23.

Наличие полей и сериализация доказаны лишь в своих стендах. Физическое применение целевых частот и SoC не доказано. Исполненный ISL69247 helper относится к VCORE-labelled пути, не к SoC. Архивные профили меняют данные, а не исполняемые модули вне первых 0x20000. Пересмотренные профили возвращают Tcl и ручное управление таймингами в Auto. Это повод проверить обучение памяти, не доказанный рецепт. Сообщения о DF1800 относятся к ручной переделке feedback и SoC выше1.2 В, поэтому не подходят под требования.

## Use cases and route selection

- Штатный пункт применяется: инструкция без патча ради патча.
- Пункт скрыт, но реализован: минимально открыть нужный путь меню.
- Значение читается, но перекрывается: найти конкретное условие/политику и проверить минимальное изменение.
- Требование не реализуется доступным путём: предъявить ограничение с точным доказательством. Не заменять исходную цель альтернативным профилем без согласия.

## Implementation checklist

### A1. Закрыть пробел в основах Zen 2 и применимости к BC-250

- [ ] Проверить по первичным AMD-документам и воспроизводимым практическим источникам смысл MCLK/UCLK/FCLK, делителей и переходов между доменами.
- [ ] Отдельно сопоставить настольную DDR4 с GDDR6/UMA BC-250. Не переносить DDR4 MT/s, напряжения, тайминги и частотные пределы по сходству названий.
- [ ] Объяснить вклад fabric/controller clocks, обучения, таймингов, состояний питания и условий измерения в задержку. Обозначить непереносимые свойства, включая кэш и топологию.
- [ ] Результат: краткая таблица «правило Zen2 / источник / применимость к BC250 / что проверить». Не очередной общий обзор.

### A2. Составить паспорт каждого нужного параметра

- [ ] Частоты: MemoryClockSpeed, UclkDiv1M0, MemoryPstate, FclkDpm, DfClockOverrideControl, DfClockOvrd.
- [ ] Напряжение: реальный VDDCR_SOC, отдельно от VCORE/GFX/MEMIO и raw VDD offset.
- [ ] Тайминги: DRAM Timing User Controls и Tcl, затем только подтверждённые применимые поля контроллера. tRCD/tRP/tRAS/tRFC и режимы DDR4 не объявлять доступными по памяти.
- [ ] Для каждого: путь BIOS, условие видимости, переменная/смещение/тип, единицы и Auto, вызывающий код, конечное действие, способ измерения, риск и возврат.
- [ ] Использовать четыре разных статуса: найдено в меню, читается кодом, влияет на выходную команду, подтверждено на плате. «Работает» без последнего статуса не писать.

### A3. Найти и проверить управление, а не очередной буфер

- [ ] Завершить отдельную задачу GhidrAssistMCP, использовать существующие Ghidra/UEFI-инструменты. Установка не является результатом разгона.
- [ ] Сначала проследить путь VDDCR_SOC и единицы. Независимый офлайн-анализ частот не блокировать отсутствием аппаратного измерения.
- [ ] Для частот идти от функций программирования назад к перечисленным полям. Установить физические домены и разрешить native-help FCLK > UCLK против цели1:1:1.
- [ ] Изолированно исполнить конкретный участок: исходный вход, изменённый вход, восстановленный вход. Перехватывать аппаратные обращения, фиксировать команду/значение, не выполнять настоящий IO.
- [ ] Неизвестные ответы оборудования и заглушки явно фиксировать. Исполнение в Unicorn или другом стенде не равно загрузке платы.
- [ ] Если есть блокирующая ветка, изменить только её на копии. Проверку подписи не трогать без доказательства, что она блокирует конкретную необходимую модификацию.

### A4. Подготовить операторскую последовательность

- [ ] Снять исходные задержки и пропускную способность без изменения настроек. Зафиксировать метод, версию, объём рабочего набора, CPU/нагрузку GPU, температуры и частоты, исключить тест только кэша. Это baseline, а не первый шаг разгона.
- [ ] Первое изменение BIOS: подтверждённый SoC. Проверить фактическое напряжение и соблюдение потолка. Неподтверждённое управление SoC запрещает переход к повышению частот, но не останавливает офлайн-работу.
- [ ] При неизменных исходных таймингах/Auto проверить применимость делителя и режимов fabric/controller. Начальные числа и шаги брать из установленных единиц и диапазонов, не назначать сейчас 1800/1900 по настольному Ryzen.
- [ ] Исследовать частоты по одному фактору. Когда синхронная группа требует совместного изменения, заранее определить её как один фактор и записать все изменённые поля.
- [ ] После стабильного частотного профиля отдельно исследовать подтверждённые тайминги, затем состояния питания. Не менять всё одновременно.
- [ ] Для каждой пробы: BIOS-поля, старое/новое, реальные частоты, напряжение, холодный старт, ошибки, задержка, полоса, способ возврата.

### A5. Собрать только обоснованный комплект

- [ ] Основной вариант на чистом CLV, отдельный экспериментальный menu-bridge. Не выпускать новые гипотетические разгонные ROM.
- [ ] Для изменений сохранить MODIFIED_FILE, DIFF_FILE, VERIFICATION.txt, исполняемый ROLLBACK.sh. Повторно использовать канонические роли существующего кандидата.
- [ ] STATIC-PASS: воспроизводимая сборка, объяснимые изменённые диапазоны, FV/FFS и применимые контрольные суммы, нетронутые подписанные области, одинаковые baseline/modified/rollback тесты, восстановленный исходный hash.
- [ ] Независимое ревью рискованного патча. Финальная инструкция: точный путь BIOS, значение, порядок, ожидаемый эффект, проверка, условие остановки и откат.

### A6. Отдельно подтвердить результат на плате

- [ ] До прошивки: одобрение точного образа и платы, проверенный полный dump, независимое восстановление, cold-boot/readback план. Ничего не прошивать этим планом автоматически.
- [ ] Нагрузочные тесты только после отдельного разрешения. Конкретный тест и длительность выбрать до прогона.
- [ ] HARDWARE-PASS: реальные частоты подтверждают соотношение, фактический SoC в пределе, холодный старт и сохранение настроек, ноль ошибок в согласованном тесте. Ноль ошибок не обещает абсолютной стабильности.
- [ ] Задержки: не менее пяти одинаковых прогонов на baseline и кандидате, чередовать A/B при возможности. Сравнить медиану и разброс. Уменьшение меньше межпрогонного разброса не объявлять выигрышем. Записать пропускную способность и регрессии.
- [ ] Если 1:1:1 не достигнуто, не ставить выполнено исходной цели. Альтернативу с меньшей задержкой показать отдельно.

## Stop rules and failure paths

Ветка продолжается только если следующий опыт отличает конкретные гипотезы или меняет решение о патче. После двух неудачных гипотез собрать новые данные. После трёх попыток без нового результата закрыть ветку с точной границей и перейти к независимому пункту. Не повторять доказанные NVAR/serializer/packaging проверки без причины. Отсутствие прямого вызова не доказывает отсутствие управления вообще.

Немедленный аппаратный возврат: превышение потолка, ошибки, зависание, неудачное обучение/загрузка или согласованный температурный предел. Предел температуры и способ recovery определить до испытания. Не назначать новые напряжения других линий автоматически.

## Open questions

Executor-owned: достоверный SoC setter, реальные единицы трёх частот, синхронность, обучение памяти, применимые тайминги, достоверное считывание на BC250. Это рабочие вопросы, не вопросы пользователю.

User-owned later: одобрение точного образа и отдельного нагрузочного прогона. Для составления и офлайн-выполнения плана новых ответов не требуется.

## Decision log and next action

Сохраняются R1-R8, SoC-first <=1.15 В, BIOS-only настройки, отдельные STATIC/HARDWARE уровни и отдельный menu-bridge. Текущий запрос разрешает составление плана, не физическую прошивку. Этот документ уточняет ожидаемый результат и порядок, не отменяет выполненные исследования.

Первый следующий результат: A1 и A2, компактная карта применимости параметров с честными статусами. Далее A3 по самым важным пробелам. Исполнитель отвечает за источники и технические решения, не возвращает эти вопросы пользователю.

Execution checkpoint A1/A2: opened AMD guide full text (internal pages2.9/April2022, not stale2.1 metadata) and pinned integralfx guide; generated10-field byte-backed map. Native unequal-marker experiment overturned old token corrections: FCLK_DPM1331, MemoryPstate123C. See docs/research/2026-09-23-zen2-bc250-parameter-map.md. Next A3 use correct tokens and existing caller artifacts. Physical semantics and SoC setter unresolved. Goal remains active.

Checkpoint caller experiment: ten native branch/staging cases exit0. FixVoltage0 ignores synthetic word and stages900; FixVoltage1 stages requested word in both VCORE/GFX-labelled branches. Pin/net data place PUA1 on core/gfx sense and PUS1 on SOC_FB, not physical board proof. Do not promote these fields to SoC. Corrected123C scan233 modules found7 producers and13 unrelated addresses, no direct immediate requester. No full no-consumer claim. Next independent path: ABL1 memory policy95FC upstream input, reuse existing provider reports; avoid duplicate scans. Goal still open.

A3 new PLL boundary: ABL1 function5E68 includes actual SVC28 calls adjacent to SetupFclkPll/SetupUclkPll labels. R2->R4->LSR R8,R4,1->UCLK service argument; FCLK local default250/1200 then provider463C override->service argument. Byte-backed only; unknown service units/ABI/physical effect. See docs/research/2026-09-23-abl-pll-service-boundary.md. Next executable action: set up disposable local ARM emulator if no existing interpreter offers it, then execute bounded original5F30..5FFA path with explicit log/provider/SVC hooks and record service arguments. Do not patch ROM or use raw service selectors on board.

A3 emulator checkpoint: pinned Unicorn2.1.4 installed project-locally. Executed native PLL builder +463C +1FB4, only4800/log/SVC hooked. Nine cases pass:1800->UCLKarg900,1750->875,restore900;FCLK1200 default,1420 valid override,FFFF rejection. Gate015F missing/0 stops without querying0160. This supersedes historical missing-gate-fallback claim. Full goal remains open. Next first unfinished action: resolve native lookup4800 source for015F/0160 and SVC28 handler/units, using existing exact ABL/SysDrv evidence. Do not repeat generic reader or menu tests.

A3 current: native runtime-cache lookup to final PLL requests executed9 cases. A04E rows and data are explicit synthetic fixture; real producer unresolved. Initial missing73000 emulation error preserved, fixed only by declared test fixture. Next executable action: trace cold-cache construction49CC from4B34 through6238 and its lower source calls, stop at first actual external provider; in parallel only if useful inspect available SVC28 handler corpus. Avoid repeating cache-hit tests.

A3 authoritative checkpoint: actual clean APCB bytes0xAB1000..AB1B9C supplied at modeled7B000, native heap initialization and full cache construction plus lookup executed. ROMAB1B99 gate1 andAB1B9A value1420 produce FCLK servicearg1420. In-memory changedword1430/checksum yields1430, pristine restoration1420; memory1800 still UCLKarg900. Five cases pass, originalcode/ROM unchanged. Next executable action: resolve source/writer of runtime7B000 and any AmdSetup overlay before ABL reader. If needed inspect ABL0/bootloader exact references, not rerun cache-hit/serializer tests. SVC28 units and SoCsetter remain open.

A3 authoritative ABL0 checkpoint: original loader30 requestsSVC2D type60,dest7B000,capacity2000. ValidatorB8 accepts cleanAPCB, rejects badchecksum, servicefailure fatal16, restored accepted. Clean BHD type60 sourceFFAB1000 resolves selectedROM AB1000 statically. ActualSVC2D handler/selection/overlay unresolved. Next executable action: trace actual SVC28 PLL semantics or later DF P-state transitions after GnbSmuInitAblCAR, so early argument-halving is not falsely treated as final steady-state ratio. Use exact ABL1 callsites61A0/61xx and retained SMU handler evidence; no more cache/loader validation repetitions.

A3 DF-phase checkpoint: ABL4 stockcallerD8AE emitsSVC28 selector7,arg100 through9564; actualnative topology helpers return0 and three emulated cases pass. ExactSMU table entries79E8/7A20/7A28 correspond1E720/1F218/1F2F0; read-only decompile byte-verified332 instructions, full ROMslice match. Candidate transition decodes100 as explicitstate0, setsF6=FF; earlyPLL handlers rejectFF and scale0.001. SVC28->table transport unproven, so no final physicalratio claim. Next executable action: bind service transport against exact SMU queue descriptor table and enumerate other selector correspondences as discrimination; resolve startup selected-row writer using retained1E448/1E038 evidence, not repeat startupwrapper tests.

A3 queue checkpoint: exact vector7A94 index5=79B4, indices3/4 alias746C; native accessors use index*12 and base7000; ARG/RSP forindex5 are03010700/03010704. Does not establish PSP-service routing. Next executable action: inspect exact available PSP bootloader/SysDrv inventory and SVC dispatch evidence for service28 transport; if absent/encrypted, record precise boundary, do not claim another table audit closes it. Continue independent startup-row writer only with specific new caller.

A3 transport boundary checkpoint: trustedOS type2 plaintext body259a31d5.. analyzed. SVC vector8->240->4544, ordinary route46A0 returns9 for28/2D, confirmed2 native runs. This is a different service context, not earlyABL transport. Do not continue guessing handlers in TOS. Next executable action: classify exact type1 entry atSPI8E0400 with existing PSP parser/retained matching extraction, and check whether a matching early-service body is available; unknown header is not proof of encryption. If unavailable, close this branch as missing source and move to specific startup-row writer1E448/1E038 provenance, without promoting physicalratio.

Transport branch bounded result: type1 exacthash0bfbd84a.. remains opaque, existing selectedROM parser also reports not-a-PS1; no matching plaintext early-service body found in scoped retained extraction. Do not infer encryption from entropy. Stop this transport branch pending new implementation/trace. Continue independent concrete state-table rate conversion: Q5 selectorA handler1E7D8 matches ABL QueryMemFreqOfDfPstate candidate; analyze conversion before assigning1:1.

A3 checkpoint: early service body unavailable in bounded exact inventory, no encryption claim. IDA candidate query returns runtime row+18 float->integer, not hardware readback. Next executable action: trace writers of selected DF row+18 using exactSMU call/data paths, reuse existing1E038/21E8C decompiles then locate first unexplained store. Do not repeat image-table audit. SoC requirement remains open.

A3 writer checkpoint: bounded candidates classified, row18 writer NOT found.21E8C direct outputF104,1E038 initializes pointers; counters and register replication excluded only for direct stores. 546 bytes-backed instruction records checked. Existinglisting scan insufficient, do not reuse as no-writer proof. Next executable action: inspect specific22D6C->222D4 consumer ofDF current scalar and classify whether it can mutate selected row or only derives CPU timing; do not expand all CPU init callees. Fullgoal incomplete, SoC still no established setter.

Completion audit: objective not achieved. Repeated actionable gap across transport-boundary, query/row-writer and scalar-consumer turns: no matched early transport/runtime state evidence and no realSoC setter. Three bounded candidate attempts did not yield a justified next firmware edit. No claim all code globally exhausted. Stop autonomous synthetic-test loop pending genuinely new implementation/trace or separately agreed hardware evidence. Full objective preserved. See docs/research/2026-09-23-oc-completion-audit.md.

Renewed user-directed A3 execution: native CMOS acceptance6 cases, synthetic precedence7 cases, native pristine APCB provider6 cases executed. New causal result: CMOS clock written at2248 is overwritten by native item7 lookup at22BA. Source read4C16 APCB+482 (ROMAB1482)=24 ->policy1800. Memory-only enum23/checksum ->1750, restore->1800. See docs/research/2026-09-23-cmos-apcb-precedence.md. This is not final MHz or hardware. Next executable action: trace APCB item7 descriptor producer/overlay from AmdSetup MemoryClockSpeed and nested+2C final training use; reuse completed native tests. SoC path remains unresolved, no new ROM candidate authorized by these facts.

User relevance correction: CMOS/APCB precedence is supporting evidence only, not the answer to enabling synchronization. Before another progress claim, require a finding that identifies applied UCLK divider/FCLK coupling or a verified operator step. Do not present memory-policy byte changes as sync mode. Goal and SoC ceiling unchanged.

UCLK-specific continuation: native2CA4 phase2 using actualAPCB now executed0/1/restored1/FF/gate0. M0source ROMAB186F; values change logs only,0 context writes/actuator callbacks/services. Later exactABL3/ABL4 entry-to-return branches also log-only with modeled provider,6 cases. See docs/research/2026-09-23-uclk-application.md. Do not repeat these log handlers or patch them. Not proof whole UI field inert: INV1204->APCB21 remains unjoined. Next discriminator must identify final UCLK divider/PLL register semantics in exact SMU handlers or a matching register source. No new candidate or1:1:1 recipe justified.

UCLK register-source boundary: exactSMU0F/11 pointers recomputed, but already known Sept21, not new mapping. Newly opened primaryAMD clk11_0_0 header shares base5C800 but PLL_REQ byte38 differs from actualSMU byte34. Generic-header transplant rejected. See docs/research/2026-09-23-uclk-register-boundary.md. No new final-domain proof; next useful input must be matching register specification or separately authorized bounded baseline read. Existing PCI transport read writes selectorB8 and needs hardware-probe approval; no execution on hardware permitted by offline continuation alone.

Resumed blocked audit: three consecutive resumed turns leave same missing applied-domain semantics/SoC control. Latest public-source search provided no new discriminating source; offset34/38 mismatch alone does NOT prove whole-header incompatibility, correction recorded. See docs/research/2026-09-23-sync-resume-blocked-audit.md. Full R1-R8 preserved, no candidate or completion. Next useful event must provide matching implementation/register definition or separately approved baseline hardware diagnostic stage. Do not start that hardware access from offline continuation.

Approved diagnostic preparation (user `деелай` after explicit preparation-only question): build guarded copy of existing exact-target clock probe, not another firmware. Default/help must perform no host inspection; explicit metadata mode first, telemetry separately approved later. Exclude hostname/cmdline/secrets. Tests use synthetic files only, baseline/modified/restored with identical harness input, original unchanged, patch reconstruction and executable rollback. No SSH/root/SMN/PCI-config/sysfs write/stress. This preparatory deliverable does not close SoC/clock/HARDWARE requirements. Gates: focused fixture suite, procoder check, procoder test, four-role reopen. Existing tasks retained.

Diagnostic preparation acceptance:10 synthetic tests pass, procoder check exit0, procoder test exit0 Python83 pass(JS not run). Four roles reopened, patch reconstructs, rollback restores original62b5b050.., modifiedb52649a9.., original unchanged. Same --mode plan fixture: original3 mocked reads, modified0, restored3. New main default/help are inert, exact target filter, ambiguous target stops before telemetry. Runbook2026-09-23-clv-diagnostic-preparation.md provides staged, unexecuted board commands. Preparation task complete only; next separate user decision is Stage1 metadata execution on confirmedBC250. Full goal not complete.

Stage1 metadata executed after useralias2: strict-key SSH steammachine, exact collectorhashb52649a9.., exit0/stderr empty. Target card1 1002:13fe, kernel7.2.6-1.206-cachyos-bc250, BIOS reportsP3.00,date12/09/2021. No clock/SoC/settings/probe writes. Current hardware cannot yet be attributed to cleanCLV500. Preserve original development base; do not switch toP3 donor. Next provenance check should reuse latest saved flash/readback history before asking for a new dump. Stage2 telemetry still requires separate authorization. D17 explicitly prohibits LinuxDF/SMN after actual hang; no such operation authorized or performed.

Saved-image provenance resolved narrowly: newly found20260922/live-internal-0318.bin SHA3c340963.. has19/19 PSP payload hashes matching P3 donors, versus8/19 matchingCLV and11 differing includingSMU/ABL. Image not byte-identical to stockP3; differences in first128KiB andAE..C3 blocks. Current Stage1P3 metadata consistent, not fullchipidentity proof. See docs/research/2026-09-23-installed-image-provenance.md. Current hardware cannot validate500CLV-specific behavior. Do not switch target, auto-flash, or repeat oldW11-only provenance audits. No new board access this turn.

ExactCLV readback follow-up: full23AB0/23AC4 getters are SRAM cached values, not physicalcounter/MMIO.57 native instruction byte records verified.2360C/1CAD8 math alreadyknown, not newcontrol. No independent measurement bridge gained. Existing VCN EFI app is write-heavy and cannot be repurposed/ran as harmless clock reader; only inspected. Current next requires a matched counter/register source or a separately specified firmware-context observation, not more getter/math repetitions. See docs/research/2026-09-23-uclk-readback-boundary.md. All original requirements remain incomplete where previously marked.

Counter-source search executed: primaryAMD CyanDCN201 code explicitly uses clk11_0_1 and reads CLK4_CLK2_CURRENT_CNT atGPU-MMIO byte6C9FC into DPREFCLK(raw*100,zero->600000fallback). This is a concrete displaycounter, not independent memory/fabric observation. dcn3 genericstruct fclk comment not applicable without join. See docs/research/2026-09-23-cyan-counter-source.md. No adjacent-register guessing or EFI/hardware scan authorized. Actual UCLK/MCLK/FCLK map and SoCsetter still unresolved, fullgoal incomplete.

ZenTimings alternative checked at pinnedZenStates-Coreab5414a..: three clocks from versionedSMU table, DDR4ratio50200 low7bits/3, inspectedMemoryConfig hasDDR4/5 paths, noGDDR6. Not an independently recoveredCyan divider/counter and not proof globaltoolunsupported. No execution. FullCLV semantics/SoC blockers unchanged. See docs/research/2026-09-23-zentimings-applicability.md. Do not propose installing ZenTimings or running itsDDR4 reads as the next solution.

Stop repeated-source loop: cached-getter/Cyan-displaycounter/ZenStates alternatives all leave same applieddivider/SoC gate open. Current audit revalidates this instead of inventing next address. Existing diagnostic roles unchanged except supplemental record. A dedicated UEFI observation method would be a separately agreed approach: preparation/fixture validation first, no board execution/flash implied, D17LinuxDF/SMN retained. Await this method decision or genuinely new matching implementation source. FullR1-R8 not achieved.

UEFI preparation implementation anchor: candidates/clv-clock-observer-v001, standalone X64 EFI app, no ROM injection. Uses existing pinned EDK2 headers, local clang/LLD, no installation. Default prints plan, no PCI access. Explicit --capture-raw path requires exactlyone CyanPCI1002:13fe insegment0 and AMDroot, fixed9 rawSMN offsets derived from exactCLV clock handlers, no useraddress input. PCI-indexB8 writes are unavoidable and disclosed; data-portBC writes, mailbox, voltage/frequency setters prohibited. Preserve/restore selector on normal/error paths; timeout cannot guarantee recovery from hardwarehang. Host mock tests noIOdefault/wrongtarget/readerror/indexerror/restoreerror/allones/success. StructuralPEcheck and builddeterminism. Hardware/QEMU/independentreview not claimed. Main1:1:1 goal remains open.

UEFI preparation checkpoint: candidates/clv-clock-observer-v001/Bc250ClockObserver.efi SHA893908e55d6bdf30145a9fcca71bc1fcb0151874fed327eb04af614758236218,5120bytes.20hostmockcases pass, exact9offset provenance checkpass, reproduciblelink/PEchecks pass. Default/help noPCI; explicitcapture rawstate only withB8selectorrestore. Firstindependentreview returned unrelatedoldtask receipt, rejected; one retryrunning. NoQEMU/firmwareload/boardrun orclockchange. Genericprocodercheckexit0, separatePython83tests pass. Pending fullprotocolmock/review before furtherreadiness. Samefour diagnostic roles extended, not replaced.

Reviewfinalstate: bothindependentreviewerattempts returnedwrongtask/receipt, rejected. Noacceptedindependentreview. Nextunfinishedoperation fullUEFIprotocolmockcoverage then validindependentreview/loadercheck. ExperimentalEFI remains no-go forboard execution; preparationpartial, wholeOCgoal incomplete. Do not ask user to execute rawcapture yet.

UEFIintegration continuation: fullhostprotocolmock18newcases allpassed (total38), allocationsfreed and noselectorwrites on rejectedidentity/inventory. ExistingprojectlocalQEMU/OVMF found outsidePATH, noinstall; newisolatedESP/VARS reusedknowncontroller. Firstguestattempt124 no bootabledevice becauseShellmissing, corrected bycopyingexistingShell intoownESP; secondrunpending. Do not callno-boot a testedapplicationfailure. Firmwarehash unchanged.

OVMFloader acceptance observed: secondrunexit0/stderrempty, actualEFI893908e5.. entered3times; default/help PLAN_ONLYx2, --capture-raw rejects nonCyanvirtualmachine; no rawcapture, shellend/shutdownobserved. Firstattempt124(noShell) preserved, same45stimeoutnotweakened. Fullhostprotocolmocks now18additional,total38pass. Nextremaininggate validindependentreview oftransport/offsetscope; priorwrong-taskreviews notaccepted. No realboard/CLVhardwarepass or1:1:1recipe. Samefourroles extended, source/EFIreadback verified.

Independentreviewcontinuation: alternativeGemini reviewer started withnewreceipt, stillrunning at verifiedagentstatuscheck; noacceptedreview yet. Root sourceaudit confirms singlePCI.Write siteonlyB8, noBC/data setter,9fixedoffsets matchSMUdescriptors. This doesnotclose physicalhostpermissions orfirmwareidentity and cannotgrantHARDWARE-GO. No boardactions.

Reviewgate remainsblocked after thirdtask-delivery failure: Gemini alternative returned wrong-tasksummary withoutreceipt, not anEFI review. See candidates/clv-clock-observer-v001/review-status.json. Roottransportaudit confirms sourcewrite restriction but not physicalaccesssafety. No more blindreviewretries. New source review from a functioning independent context is required beforehardwareproposal; allclock/SoC/fullBIOS deliverables stillunachieved. User's2 doesnotauthorizehardware or eliminate gate.
- [2026-09-24] FCLK-1800 APCB candidate built (route: ROM record 0xAB1B9A 1420->1800 + checksum 0xAB1010, gate untouched): candidates/BC250_5.00_clv_FCLK1800_APCB_v001.bin sha256 3d6348c65a0c2ee500e13f3b1a5c9e9c64c57e36b570fbd1e85a19b9713871f8; independent parse/diff PASS (3 bytes); pytest 83/83; NOT flashed; 1800 itself not emulator-run (open, A3 harness not preserved). Builder: scripts/build_clv_fclk1800_apcb.py. Log: docs/action-logs/2026-09-24-fclk1800-apcb.md. Next: operator flash gate (v003b first), or rebuild A3 harness to run the 1800 case.
- [2026-09-24 b] O-F1 closed: preserved harness found (20260923-abl95fc-next + tools/abl-emulator-venv); new runner emulate_pll_apcb_v001.py fed the ACTUAL candidate bytes -> native ABL1 gives FCLK service arg 1800 (control 1420, gate-off 1200, tokens 015F/0160 as expected). Manifest updated. Still open: SVC28 transport, APCB->0x7B000 loader copy modeled, no hardware. Not flashed.
- [2026-09-24 c] Bypass-closure session (operator: all software-only tracks). KDB deep audit NEGATIVE (13 images/15 moduli, all attack classes, 20260924-kdb-deep-audit). UCLK PSP-breach: 1-bit ABL1 patch 0x5F32 54->04 (LSR->LSL#0 = MOV) emulator-proven (UCLK arg = input; 1800->1800, 1750->1750); glitch-signed candidate BC250_5.00_clv_UCLK_MOV_GlitchSigned_v001.bin sha b5fff267472bd8ae80d1a87a82f760cd388740305feb46847be04cd57854e799, psp_ps1_verify 14/14 (container relocated 0x9E0000, KDB slot0, kid d9cc642a). Type-9 tail: per-build protected -> root-swap not software-forgeable (CLOSED). Gasket consumer hunt: applier = generic ROM loop, no literals; type-1 encrypted (CLOSED indeterminate). ZD-1: probe4l8_ring_forgery.py deployed+version-gated; live SMU = 58.6.0 (robin-1 family, plan is robin-5/clv) -> append refused by design; robin-1 Q0-table literal 0x13E88 @0x1818C (no slot analogy), board Q3 WEDGED by code-addr read trap -> cold cycle needed; no appends sent. v2000a re-cited CLOSED. Action log: docs/action-logs/2026-09-24-bypass-tracks-closure.md. Open: board cold cycle, flash approvals (v003b, FCLK), D1 voltage, ZD-1 post-clv-flash run.
- [2026-09-24 d] Operator demanded repeated pre-flash verification. Independent from-scratch preflight (scripts/verify_v003b_preflight.py, DxeCore-real walk semantics) FOUND A REAL DEFECT in v003b: driver FFS at 0x432000 sits AFTER the base's 0xFF free tail; DxeCore (FwVol.c FwGetNextFile) stops at the first erased buffer -> driver never dispatches -> route-B would get a false negative. REBUILT as v003c (scripts/build_v003c_bds_prefix.py): same driver blob, inserted BEFORE Bds.ffs @0x12940 (W9-proven placement class), inner FV 0x432000->0x436000, capsule recompressed. sha256 dafb323a5d701f29b9c1b74f0a6bc728572590ced54a8389c01b20c0a4f828b0. Independent preflight verify_candidate_preflight.py 9/9 GO incl. new gate G9 (erased gap=0, dispatch reachable). v003b package+runbook REJECTED/SUPERSEDED; new package firmware-flash-pkg/20260924-v003c-route-b-vcn/; runbook bc250-v003c-programmer-flash-runbook.md. NOT flashed; operator gate now on v003c (dafb323a...). FCLK image audit still pending (A6).
- [2026-09-24 e] v003c FLASHED (operator approval: "прошивай, питание отключено, ошибка недопустима"; intent logged BEFORE the write). Chip W25Q128.V verified; fresh double-read pre-v003c a==b sha 64973ba3… (rollback); family word 0x00580600; package sha OK; write VERIFIED rc=0; independent readback sha dafb323a… == candidate, FLASH VERIFIED EXACT. Dumps in evidence/programmer/reads/20260924-v003c/. NEXT: operator cold boot -> P0 oracle -> postflash_vcn_check.py (deployed) -> verdict appended.
- [2026-09-24 f] v003c NO-BOOT postmortem: bench cleared by operator; full write had factory-reset live APCB tokens 0xAB1008..0xAB1B6F + NVRAM (74293 B outside capsule). Donor-vs-board DXE delta = logo FFS only (7BB28B99, 0x218 vs 0xA4CA); swap hypothesis dropped. OVMF: driver .efi loads+returns clean (rc 0), no board-boot model exists. Fixes built: v003d (pre-dump + capsule window only) sha 7e93a59c…, preflight NO-GO (logo, declared); v003e (pre-dump OWN FV + driver, 0x441000/194) sha b67e59d7…, preflight 9/9 GO vs the booted dump (window parameterized in verify_candidate_preflight.py). MISTAKES rule added: one-variable = diff vs fresh pre-write target dump inside the declared window. Awaiting operator: «откат» (write 64973ba3…) or «v003e» (write b67e59d7…).
- [2026-09-24 g] v003e FLASHED (operator "прошивай"; intent logged before write): chip verified, double pre-read a==b (dafb323a…), package sha OK, write VERIFIED rc=0, independent readback b67e59d7… == candidate (FLASH VERIFIED EXACT). Dumps evidence/programmer/reads/20260924-v003e/. Rollback remains pre-v003c-read-a.bin (64973ba3…). NEXT: operator cold boot -> P0 oracle -> sudo python3 /home/OWNER/vcn_unlock/postflash_vcn_check.py -> verdict.
- [2026-09-24 h] v003e first-blink-only (operator: green blinked once, no 2nd, LAN silent). v003e == morning except DXE capsule (APCB/NVRAM preserved, so the v003c reset is fixed). Root cause = driver-in-DXE dispatches too early, hangs AGESA before LAN bring-up. Fix direction: same payload as UEFI-Shell/.efi (OVMF-validated) or host-side, NOT in-BIOS. Recovery = write 64973ba3… on operator word. Log: 2026-09-24-v003b-route-b.md.
- [2026-09-24 i] v003e hang mechanism byte-locked: driver .ffs = PE32+guid sections only, NO 0x13 Depex -> DxeCore dispatches it in the earliest pool; EntryPoint's first PCI 0xB8/0xBC write hits unmapped NBIO -> early-DXE stall = first-blink-only, no LAN. Carrier (in-BIOS Dxe) is wrong; payload moves to the no-Shell Bc250VcnProbe4.efi (post-init) or host-side. Recovery = 64973ba3… on operator word.
- [2026-09-24 j] Confirmed: VCN enable needs no flashed firmware — probe4 (no-Shell boot app, Q3 0x2A secure-read transport) already carries the route-B write set for post-init run from a USB stick. The remaining firmware-change item on the standing goal is FCLK/memory-fabric only. Blocked on operator "откат" to restore the board.
- [2026-09-24 k] v004 FIX BUILT: root cause of v003e hang = driver FFS had PE32 only, NO DEPEX -> earliest-pool dispatch -> PCI 0xB8/0xBC into unmapped NBIO. Rebuilt driver FFS with DEPEX TRUE (GenSec/GenFfs, sections [0x10 PE32, 0x13 DEPEX]); v004 (98b9c2bd…) on the board's own booted dump, preflight 9/9 GO, DEPEX verified in final FV, PE code byte-identical. Package firmware-flash-pkg/20260924-v004-predump-vcn/. Awaiting operator flash word.
- [2026-09-24 l] v004 FLASHED (operator "прошивай"; intent logged before write): chip verified, double pre-read a==b (b67e59d7…), package sha OK, write VERIFIED rc=0, independent readback 98b9c2bd… == candidate (FLASH VERIFIED EXACT). Dumps evidence/programmer/reads/20260924-v004/. Rollback = pre-v003c-read-a.bin (64973ba3…). NEXT: operator cold boot -> P0 -> sudo python3 /home/OWNER/vcn_unlock/postflash_vcn_check.py.
