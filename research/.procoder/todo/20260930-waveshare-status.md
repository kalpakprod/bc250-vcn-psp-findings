
# Waveshare context recovery — 2026-09-30

Type: directive (recover chat evidence) + consultation (recommend next steps). Size: medium, read-only research.
- [ ] Recover last confirmed Waveshare firmware status from relevant chats and local artifacts.
- [ ] Distinguish TOCTOU, DS5 Dongle and other integration plans from implemented/tested features.
- [ ] Report next steps and remaining blockers, without flashing or changing firmware.
Earlier audit, TOCTOU and other tasks remain open. Plane synchronization pending: connector unavailable; REST endpoint not yet verified.

## Observed result
Reviewed relevant Claude chats in bc250 (0b9aa6d9…) and eltex (871664a9…), firmware source and build artifacts, Cycle 1 progress ledger and header draft. Phase 1 unified artifact exists for Waveshare; earlier chat reports upload of an earlier build, but the later full-CDC build remained waiting for BOOTSEL. No current hardware acceptance inferred. Firmware dispatch currently has only controller/rig active paths; monitor is reserved and power-control path absent. Cycle 1 ledger closes Task 1 only; Tasks 2–5 are not recorded complete. Header draft contains unverified/prospective statuses and conflicting connector assumptions; not an approved wiring guide.
- [x] Recover last confirmed Waveshare firmware status from relevant chats and local artifacts.
- [x] Distinguish TOCTOU, DS5 Dongle and other integration plans from implemented/tested features.
- [x] Prepare next steps and blockers for report, without flashing or modifying firmware.
Plane synchronization remains pending. Earlier open tasks unchanged.

## Connected Waveshare inspection
Directive; size: simple initial read-only device inspection.
- [ ] Identify the user-connected Waveshare on this computer and inspect exposed firmware identity/status if available without changing device state.
Initial lsusb: no identifiable RP2350/Waveshare/DS5 composite device; /dev/serial/by-id and by-path absent; lsblk shows no removable USB storage. Earlier open tasks retained. Plane synchronization still unavailable.

Inspection result: Waveshare not currently visible in USB inventory; no CDC serial node or USB storage. Kernel log records USB 1-2.4 disconnect at 09:22:30, device 16, without identity established by that line. Firmware cannot be identified until device is enumerated. Await user confirmation of physical connection to this computer; do not reset or flash. Task stays open.

Additional evidence: disconnected USB device 16 was Generic USB2.0-CRW (Realtek card reader), not evidence of Waveshare detection. Current sysfs product inventory also has no Waveshare/DS5/RP2350 identity.

User observation: LED1 blinks. Consultation/diagnostic continuation, simple. Determine what blinking establishes; keep device-identification task open. No new hardware action authorized.

New live result: USB 054c:0ce6 appeared with CDC /dev/ttyACM0 named Sony DualSense Wireless Controller. This is consistent with the DS5 bridge descriptor, not proof of physical device identity or exact firmware version. Local bridge source blinks wireless LED during Bluetooth inquiry and low battery; LED1 labeling not independently established. VERSION/STATUS query not executed on device: pyserial missing; corrected standard-library command failed opening CDC with PermissionError errno13. No permissions changed, no firmware reset/flash/mode switch. Firmware identity remains pending.

Continuation: user says далее. Directive, simple. ACTIVE_OBJECT=connected DS5-labelled Waveshare candidate; LAST_CONFIRMED_RESULT=CDC identity appears, ordinary open denied errno13; NEXT_EXECUTABLE_ACTION=read-only VERSION/STATUS via existing noninteractive privilege if available; INPUT_PATHS=/dev/ttyACM0 and existing firmware dispatcher source; ACCEPTANCE_EVENT=literal firmware reply or concrete access error. Preserve earlier tasks; do not alter permissions, reset, flash or change mode.

Observed continuation command: exit=1; stdout=''; stderr='sudo: a password is required\n'.

## Omarchy sudo invocation
Directive, simple: read Omarchy skill and determine correct interactive sudo execution. Preserve all earlier open tasks. User ACL command failed exit1: fingerprint verification timed out, sudo requires a terminal for password. Device-access task remains open.
- [ ] Read Omarchy guidance for interactive sudo and apply supported invocation if applicable.

- [x] Read Omarchy guidance: visible interactive terminal → sudo; agent/background without usable terminal → pkexec and system authentication dialog. Applied to recommendation; no privileged action started by this lookup-only request. Device inspection remains open. Correction recorded in MISTAKES.md.

User reports interactive sudo ACL command returned without error. Directive continuation, simple: retry read-only firmware VERSION/STATUS; retain earlier open tasks, no flash/reset/mode change.

Live CDC observed (exit0): VERSION replied "VERSION c1e7627 2026-09-28T21:32:39Z MODE controller" then "OK". STATUS returned recognized "OK" only, no STATE line observed. Firmware version and controller mode now confirmed by device reply; no proof of gameplay, Bluetooth pairing or TOCTOU operation.
- [x] Identify connected firmware version/current mode via read-only CDC query.

## Approved full adapter implementation
Directive; hard execution, interview already completed: full adapter, software fallback permitted, no solder, no unconditional TOCTOU/VCN claim.
- [ ] A: preserve source/build provenance, establish recoverable installed baseline and powered-hub acceptance.
- [ ] B: hardware acceptance of paired DualSense inputs, audio, feedback and reconnects.
- [ ] C: concurrent runtime services and safe mode handling.
- [ ] D: verified monitoring sources and safe power state machine; Linux/HA fallback explicitly marked.
- [ ] E: authenticated web/MQTT/Decky, shared fresh metrics.
- [ ] F: passive firmware/UART diagnostics only after electrical verification.
- [ ] Final: cross-family review, rollback, hardware acceptance and observation.
First executable slice: snapshot existing source/build artifacts and read-only host acceptance probe. Stage A installed-image restoration unproven; no flashing or later hardware writes authorized. Plane sync pending.

User hardware observation: DualSense switched on but not connected; controller LED blinking. Simple diagnostic continuation within stage B: establish pairing without flashing, clearing keys or switching modes. Earlier tasks retained.

Execution constraint from user: NO SUBAGENTS; root performs all work. Directive, simple. Worker waveshare_host_probe interrupted. Independent cross-family review is pending unless the user later permits it; no review claimed.
Live read-only recheck: VERSION c1e7627 2026-09-28T21:32:39Z MODE controller; STATUS MODE controller then OK. Correction: earlier parsing omitted legacy MODE lines; STATUS was not bare OK. Existing tracker observations retained with this correction.

User says pairing sequence complete. Simple stage B verification: read-only host enumeration/CDC check, then actual gamepad events if present. Completion of button sequence is not pairing acceptance until host evidence. Earlier tasks retained.

User confirms DualSense still blinking after pairing sequence. Pairing remains unconfirmed. Read-only sysfs: HID driver not bound, no gamepad event node. Current kernel record 0003:054C:0CE6.0064: expected pairing feature length20, got1; driver probe error -22. Do not conflate host USB initialization failure with Bluetooth pairing failure. Next collect sanitized Bluetooth event evidence.

Executed slice: source snapshot and on-disk UF2/bin/ELF preserved (not installed readback). Added read-only scripts/waveshare_probe.py supporting legacy MODE replies and modern STATE, bounded VERSION/STATUS only, selected USB ancestry and explicit no-hardware-acceptance field. 17 stdlib unittest checks and make test passed; scoped procoder check exit0 after formatting correction, nonblocking broad findings retained. Four roles created/reopened; BASELINE missing collector exit2, MODIFIED fixture parser exit0, ROLLBACK missing collector exit2; rollback archive SHA equals pristine, patch reconstruction matches modified. Existing firmware source/binary bytes unchanged.
Existing picotool lacked USB; locally built same v2.3.1 source with libusb at low priority/single job, no install. USB save command now available. Awaiting user BOOTSEL for two installed-flash reads; not asking to upload/erase. All full-plan stages remain open.

Final owned-import cleanup completed and regression/contour rerun exit0. Same four role paths reopened; final BASELINE/MODIFIED/ROLLBACK fixture commands exit2/0/2, final patch/archive reconstruct byte-identically, rollback restores pristine archive. Hardware pairing still blinking and no gamepad input node; next action remains user BOOTSEL then two bounded private flash reads with freshly verified USB-capable picotool. No full-plan completion claimed.

User reports successful pairing. Directive continuation, simple: verify registered gamepad and read-only status. Previous blinking observation is historical, not current state. Defer requested BOOTSEL backup while checking this working connection; firmware recovery and other full-plan tasks remain open.

Post-pairing read-only device checks: VERSION and legacy MODE STATUS still controller; no host gamepad event node. User pairing observation retained separately from USB input acceptance. No firmware change, reset or BOOTSEL requested during this check. Same four artifacts reopened; original host tool transaction remains BASELINE absent2 / MODIFIED fixture parser0 / ROLLBACK absent2.

## Approved replacement plan implementation
Directive; hard, interview already completed and user approved. Root only, existing equipment, no solder/cuts/purchases, no PSP bypass.
- [ ] A: corrected interface registry from CAD/vendor sources; facts vs specimen checks.
- [ ] B: two installed Waveshare flash reads and verified recovery; exact image approval before upload.
- [ ] C: staged firmware USB initialization repair, persistent/read-only status, safe runtime modes; offline checks and build.
- [ ] D: safe monitoring/control interfaces, Linux/HA fallback explicitly distinguished; inaccessible electrical paths disabled.
- [ ] E: shared fresh state/read-only panel/authorized controls; no arbitrary commands.
- [ ] F: fully illustrated offline HTML tied to candidate, verified rendering, tests, restore assets.
- [ ] G: actual AMD hookup/hardware acceptance after user follows guide.
All prior tasks remain open. Earlier cross-family review requirement superseded by explicit no-subagents instruction; no independent review claimed. Plane sync pending.

User reports starting Waveshare with BOOT held. Simple approved recovery-read step: identify sole RP2350 BOOTSEL USB and perform two read-only whole-flash saves; no load/erase/reboot. Retain every unfinished task.

Recovery step observed: two verified full installed flash reads exit0, 16MiB each, hashes identical, dumps private under ~/.cache/waveshare-recovery-20260930. Restoring by upload not tested and no upload performed. Candidate source staged as candidates/waveshare-adapter-safe-v001; originals remain unchanged. Next fix early USB identity enumeration and unsafe mode fall-through in this copy, excluding active injection from the safe target.

Candidate first build failed at link: pre-existing bt_is_connected declaration had no definition. Retained literal build logs. Added truthful two-channel connection predicate in candidate only, then rebuilt; no evaluator/test weakening. Stage C still hardware-unverified.

Stage C candidate rebuilt exit0 after unresolved pre-existing declaration fixed on copy. Offline C++ USB readiness and bounded copy test PASS; CDC C harness with partial TX, long-input overflow and rejected ARM/RESET/toctou PASS. nm confirms no rig_init/rig_arm/spi_toctou symbols in safe ELF. No image upload yet; exact image authorization pending. Corrected CAD registry includes external USB and all diagnostic/power connectors with unavailable status until electrical acceptance.

User decision: first final image with all functions, then flash. Directive constraint update, simple. No permission to upload the controller-only candidate. Keep staged test image unflashed; do not present it as final. Continue offline full-adapter software and documentation, keep unavailable physical/PSP functions explicit and hardware acceptance pending. Existing earlier tasks retained.

Review caught a security gate on the synthetic test token literal (not a real credential). Test now creates ephemeral random fixture tokens instead of embedding a token-like constant; validations unchanged, no scan suppression. Mobile guide QA caught overflowing inline action container and mobile hover-vs-touch mismatch; CSS fixed, native hover/touch retested. Full source/firmware tests remain distinct from hardware acceptance.

UF2 validation first failed on mixed absolute/program block families. Primary picotool source showed its exact RP2350-E10 ignore marker, separate from program pages, and pico SDK declared its ignore extension. Added strict pattern-specific recognition, not blanket exemption: malformed markers and all real program pages in private sectors still fail. Validation exit0; marker hardware-ignore behavior explicitly unverified. No upload.

Patch reconstruction initially failed on a board header; first suspected line-ending normalization was incorrect. Byte comparison showed missing EOF newline caused next patch header to concatenate. Corrected generator emits standard "No newline at end of file" markers. Third corrected command passed byte-for-byte reconstruction; all original bytes preserved. No source normalization or weakened comparison.

Decky read-only backend/frontend staged from verified template API, no root/install hooks. First typecheck failed: @decky/api imports react-router types not declared transitively. Added exact @types/react-router 5.1.20 matching installed API source metadata, without skipLibCheck or weakened checks. Build output alone not accepted until types pass. No installation on AMD.
HA power-on helper added with fixed documented target, exclusive-supply confirmation, fresh off-state gate, explicit execution flag and no off/reset routes; tested exclusively with fake API, no HA calls performed.

## Executed offline progress, not final-image completion
- [x] Two full installed Waveshare flash reads, verified equal; private backups preserved. Restore writing not tested.
- [x] CAD-grounded connector registry corrected, 18 items; unsafe/unaccepted GPIO stays unavailable.
- [x] Candidate copy compiles with controller identity-ready USB retry, bounded HID reports/input and controller-only dispatch; originals untouched, active rig excluded.
- [x] Async WiFi, private CRC/bounded provisioning slot, authenticated read-only HTTP and telemetry-only MQTT compile.
- [x] Fresh Linux hwmon metrics/BC250 heartbeat bridge; missing/stale stays null/unknown; no I2C/SMN writes.
- [x] Fixed owned-topic nonretained MQTT PS read helper and HA power-on helper with exclusive-supply confirmation, independent physical/HA OFF agreement, explicit execution flag; fake APIs only.
- [x] Read-only Decky source/typecheck/build passed using pinned verified API/template, no root/install hooks. Actual installation pending.
- [x] Offline illustrated HTML draft generated from CAD and checked desktop/mobile with actual hover/touch; no JS errors/network requests/page overflow. Intermediate UF2 download disabled per user decision.
- [x] Relevant host tests, candidate symbol/size gate, strict UF2 checks, contour and scoped host gate passed. Literal callback BASELINE returned63/overwrote53, MODIFIED returned10/overwrote0, actual ROLLBACK returned63/overwrote53 on same host input, all exit0; this is not hardware behavior.
- [x] Same four role paths extended, reopened; host baseline2/modified0/rollback2 and native archives/patches/source restore hashes verified. No original pico-bc250 edits, no firmware upload or AMD/system changes.
- [ ] Final-image function closure: GPIO/UART/BIOS diagnostic electrical viability, live AMD integration, powered-hub/exclusive supply evidence, actual HA/Decky installation/configuration, device/runtime/audio/feedback/reconnect acceptance.
Firmware upload remains prohibited until final image; do not ask to flash partial builds. Full objective remains open, not complete. User need not reconnect AMD yet. No subagents.

## Active goal continuation — 2026-09-30
Directive continuation; implementation hard, prior interview/approved scope reused. Previous turn classified progress: source/candidate/host companions/QA and rollback changed authoritative state. Goal remains full plan, root only; no intermediate upload. Next safe slice: prevent historical MQTT status from triggering PS power-on, fix actual MQTT ring capacity, add default-disabled input-only UART diagnostics and tests; finish safe diagnostic software without claiming electrical/hardware acceptance.

Goal continuation implemented: MQTT freshness test first reproduced accepting missing age; strict age/historical validation now passes. MQTT ring expanded from actual default256 to1024; queued records carry original age. Added explicit default-disabled UART1 RX GP9, no TX pin and TX enable bit cleared, no automatic raw publication; C fixture proved bounded64-byte loop, 8KiB ring overflow and no GPIO calls without confirmation. Disabled stock UART stdio to avoid driving GP0. Offline BIOS integrity helper prints no bytes/offsets or signing material and does not assert signed-region preservation. HTTP large buffers moved out of measured2KiB main stack; abort callbacks return ERR_ABRT. All runtime/electrical acceptance still pending; no flash or board writes.

Goal continuation evidence: recent PS rising-edge persists short taps, boot nonce and owner-only event dedup prevent held-state/queue replay; MQTT can use private credentials and hard packet deadlines. Added native PS wraparound test and default-disabled RX-only UART fixture. Safe existing BIOS audit reused project parser on dump/2.bin: PSP directory checksum/bounds passed, BHD has one out-of-image reference; no assertion of signature or boot acceptance, no keys/offsets emitted. Goal still active; final integration/hardware and final illustrated connection acceptance not proven. No new permission to upload.

Goal continuation: previous turn is progress, not a wait; immutable original/device no-upload restrictions retained. Start readiness matrix and verify vendor pinout asset for the final illustrated instructions, then close missing graceful-shutdown software path (fake executor only). Goal is not narrowed to the compiled subset.

Readiness audit preserved the full goal: 17 requirement groups mapped to authoritative evidence/missing hardware facts in readiness-matrix.json and READINESS.md. No passing narrow gate is treated as full completion. Official vendor pinout inspected: GP9 UART1 RX is physical left header12, adjacent GND is13 with USB-C up; added conditional two-wire RX illustration, power/TX wires excluded until measurement acceptance. Added graceful local shutdown helper with DMI+explicit execute guards, fake-executor baseline failure then tests pass; no shutdown or relay-off actually requested. Goal remains active.

Goal continuation: previous turn is progress (vendor instructions/readiness/shutdown), not a wait. Integration phase now tests real MQTT socket framing against a controlled fake broker and replaces firmware English placeholder with bounded Russian read-only dashboard. Preserve full plan and no intermediate upload; no live broker/HA/board operation.

Integration audit found actual BC250 SuperIO hwmon name is nct6686 under both driver variants, not just module names nct6683/nct6687. Fixture first failed, then collector and Decky source allowlists corrected; no inference that read-only driver supports control. Firmware HTTP/Russian embedded UI tests and real source mock callbacks now verify auth/routes/response/abort, one HTTP session reserves a PCB for MQTT. No actual host driver installation/fan operation or broker actuation.

Controlled integration progress: socketpair MQTT byte exchange and urllib HA request fixtures pass; no real endpoint contacted. Exact staged HTTP C source tested with mock lwIP/SDK for auth/routes/copied buffers/abort contract and bounded connection accounting. Russian embedded firmware dashboard replaces English placeholder, clears stale values on failed/malformed replies, byte limit checked against unchanged TCP window; desktop/mobile browser fixtures pass. Actual BC250 nct6686 source name regression fixed in collector/Decky. Still no firmware upload, final readiness/hardware acceptance unproven.

Goal continuation: previous turn progress, no live job assumed. Close portable preconnection bundle with helpers/compiled Decky/docs and per-file hashes, excluding private dumps/credentials/node_modules. Documented owned env assignment names checked without emitting values; preparation helper tested with synthetic files only, never configures a device. Provisioning now requires an exact expected source/version reply before credential bytes; PTY test proved old/wrong version receives VERSION only. Hardware/full-plan closure remains pending, no upload permission inferred.

Package/boot closure: actual source-shape names match private profile helper aliases; no values copied, no secret profile generated from real credentials. Added portable source/compiled-plugin/UF2/HTML bundle and tested extraction plus packaged validators/parser independently, no private data included. SDK stdout default could block 500ms with a connected unread CDC: explicit nonblocking log/no-host-wait flags added, fixture baseline failed then config tests passed. Build warning audit found contradictory CYW43_LWIP definitions from legacy WoL switch versus always-network SDK; redundant definition removed, no macro precedence ambiguity. Source fingerprint now normalizes its own GIT_HASH slot and includes build configuration. Original source and board state preserved; no intermediate upload.

Current preconnection package sealed and extracted independently: 31 explicit assets, no private profiles/dumps/env/cache, exact per-file hashes and packaged UF2/ROM helpers pass. Current program/source/compile flags association verified against actual binary and compile_commands: stdout/connect/mutex wait0 and one CYW43_LWIP=1. Device remains BOOTSEL, no upload/HA/power/AMD service action. Package is explicitly draft because electrical/live/deployment/full-function acceptance remains unproven; full objective retained, not marked complete.

Full-goal impasse audit: software/package checks complete their respective offline scope, but the same electrical/runtime/no-upload blocker remains across at least the last three goal continuations. Read-only picotool info freshly confirms BOOTSEL, not running candidate; no intermediate upload permission. Cannot derive measured levels, actual cable/board fit, installed AMD services, controller/audio/feedback/cold-boot/restoration results from documentation or fixtures. No further fixture/report polishing can satisfy those requirements. BLOCKED-AUDIT.json preserves full objective and exact missing external observations; no scope reduced, no completion claimed.

User constraint update: no multimeter available; requests skipping its checks as unnecessary. Directive, medium scope/safety decision, prior full-plan interview retained. Do not weaken acceptance gates or mark unmeasured GPIO safe. Preserve all earlier unfinished tasks. Need distinguish functions that genuinely require electrical evidence from standard USB/software paths which can proceed without it; no signal wiring or image upload authorized by this message.

## Уточнение заказчика: порядок подключения и живых проверок
Тип: директива. Размер: сложная задача, уточнение уже согласованного плана; интервью по исходной цели сохранено, новых вариантов цели не вводить.
- [ ] Сохранить полный объём адаптера; USB/Linux/HA не подменяют требуемую интеграцию с разъёмами AMD.
- [ ] Довести подготовку прошивки и иллюстрированной инструкции до этапа, когда осталось физическое подключение: точный разъём, контакт, кабель, направление, ограничения по подтверждённым источникам. Не выбирать J4/J204/MS/LPC по оговоркам пользователя.
- [ ] После подключения пользователем выполнить живой сбор метрик и диагностику доступных сигналов; отличать отсутствующий сигнал от доказательства неправильного подключения. Программная диагностика не доказывает напряжение/безопасность всех проводов.
- [ ] Не требовать мультиметр как действие пользователя. Неподтверждённые электрические свойства оставить явно открытыми; исследовать документальное подтверждение/доступный безопасный способ, не выдумывать результат.
- [ ] Не включать, не выключать, не перезапускать AMD и не прерывать игру до согласованного этапа подключения и отдельного разрешения на конкретную операцию. Наличие доступа не равно разрешению сейчас.
- [ ] Сохранить запрет промежуточной прошивки, прежние открытые задачи и проверки. Не объявлять полный образ готовым без реализации и доказательств.

UART preparation progress: full CAD trace contradicts draft pin3 transmit assumption. Diagram withdrawn, actual four nets recorded in uart-net-trace.json. Next: confirm UIO1 NCT6686D pins33/34 direction and I/O voltage from authoritative documentation before assigning data wire. No electrical/hardware acceptance claimed.

## Уточнение: прошивка входит в работу исполнителя
Директива, средний размер: уточнение порядка уже согласованной сложной задачи.
- [ ] Довести полный образ, затем самому прошить Waveshare; не ограничиваться подготовкой файла. Указание не разрешает выдавать нынешний тестовый образ за финальный. Перед записью привязать точный образ/хеш/устройство и проверить условия восстановления.
- [ ] Выдать цветную схему конкретных проводов и контактов, не перекладывать на пользователя измерения мультиметром.
- [ ] После физического подключения проверять реальные сигналы; отсутствие сигнала разбирать при наблюдённой ошибке, не считать заранее аппаратную проверку выполненной.
- [ ] Не нарушать текущую игру: питание AMD/перезапуск остаются отложены до согласованного подключения. Ранее открытые задачи сохранить.

[x] UART direction confirmed by official Nuvoton section4.4: J5.4 U_RX → R9558(0ohm) → UIO1.34 SOUTA output; J5.3 U_TX → R9557 → UIO1.33 SINA input. Guide corrected with blue data/black ground preparation diagram. Voltage legend O12p3=3.3V conflicts with electrical-table heading 5V; resolve using supply net/independent vendor evidence, no multimeter action requested. Earlier open tasks retained.

## Запрос: доступность браузера и обороты вентиляторов
Тип: директива + фактический вопрос. Размер: средний.
- [ ] Сообщить точные ошибки доступности Chrome/IAB в cua, отличать от рабочего OpenTabs. Причину глубже сообщения инструмента не выдумывать.
- [ ] Проверить существующие BC250 источники/скрипты тахометра и управления вентиляторами; не смешивать UART с tach/PWM. Сохранить все ранее открытые задачи.

Fan forwarding progress: Linux collector already reads RPM; previously firmware bridge forwarded only temperatures/power. Now forwards nct fan1/fan2 indices to explicit fan1_rpm/fan2_rpm, no assumption CPU/PUMP mapping, no PWM writes. Native fan1 regression failed before implementation exit134 then passed exit0, rejects negative and returns null after5s. Live old-IP probe pingDOWN/SSH no-route exit255 is reachability failure, not power-off proof. New build not sealed for release; fingerprint/manifest need regeneration before upload.

Fan CDC closure: exact dispatcher+metrics C test and real PTY host byte exchange pass. Updated build ID d5a12b0c5f99; source ID found in binary, actual wait/LWIP flags checked, strict UF2 parser and candidate symbol gates pass. No device upload. Final panel RPM display and full-plan hardware/deployment acceptance still open; no narrowing.

Panel fan display added: fan1/fan2 RPM with scale1 (temps/power scale1000); absent/error clears data. Regression first failed, actual JS VM caught typo in error text, corrected and reran. TCP2920 limit retained. Compiled source association must be refreshed after last text fix before output release; no upload.

UART design-level voltage resolved from CAD power pins1/46/85 and vendor O12p3 legend: documented3.3V output J5.4; no specimen measurement/acceptance claim. Multimeter demands removed from own draft. Old immutable preconnection bundles carry superseded pin3 assumption and must not be used for wiring; corrected bundle to be packaged. Full outstanding implementation/hardware requirements retained.

Full source audit: all70 host checks pass but do not prove missing features. mode_load currently always controller; isolated selectable diagnostic mode requested by plan is not implemented. Passive external SPI BIOS acquisition also not implemented (offline file audit is not equivalent). Next implement passive diagnostic isolation without enabling active rig/PSP bypass; retain external SPI and hardware tasks open.

Diagnostic isolation implemented: explicit MODE diagnostic, IDs0-4 unchanged, new5, RAM-only boot defaultscontroller. Legacy active modes remain rejected; UART reset on mode change, RX still explicit. Bridge stops audio/HID output/wake/controller actions in diagnostic; resume waits fresh BT input and rebaselines heldPS without changing monotonic sequence. Capture helper enters diagnostic, disablesRX and restores original mode with acknowledged outcomes. Native mode+CDC tests pass, helper mock/PTY file fixture passes; not hardware proof. Passive external BIOS acquisition remains open.

SPI acquisition audit: J4004.5 is MISO (flash pin2 SO), J4004.6 MOSI (flash pin5 SI), confirmed CAD+Macronix mirrored datasheet; pin names use FCH viewpoint. PROGRAM# couples reset through diode, no isolated master bus proven. External read not executed. Two exposed IOs cannot prove full quad/QPI capture. Available USB inventory has RP2350BOOTSEL and no recognized CH341/347. Next select passive evidence capture coverage from actual supported modes; never run live master SPI/PROGRAM# during gameplay.

Passive SPI waveform engine compiled: explicit diagnostic-only verified scheme command, dynamically claimed PIO+DMA, input-only GP10-13, finite2048words/16384samples at existing clk_sys, timeout1s, bounded32word localCDC read, mode/off clears buffer. No master commands, reset, pin output, network raw export or PSP bypass. Source/PIO contract and exact CDC dispatcher with sampler stubs pass; actual sampler hardware not exercised. 133MHz/quad/full-ROM coverage remains unproven and not claimed. Next host private trace capture helper needed.

Actual sampler C compiled against mock SDK: controller/unchecked start rejects beforeGPIO, PIO/DMA resource failures leave pins untouched,2048word completion clips reads32, timeout/off/modechange invalidate trace. PIO assembler and ARM firmware build pass, new sourceID f7bf62990131; real pins/DMA/clock capture unverified. No claim full-ROM acquisition.

Private SPI host helper implemented: version/diagnostic+scheme gate, fixed CDC commands, new600 file, bounded metadata/frame parsing,64x32words exact transfer, disarm/originalmode outcomes. Parser rejects oversized/short/duplicate/malformed frames; successful mock exchange writes8192bytes and timeout restores mode. Package whitelist extended with helper, no private capture included. Waveform remains not full-ROM acquisition.

## Новая директива: активный отладчик Waveshare/AMD
Размер: сложная задача, расширение ранее согласованного пассивного плана. До реализации активных функций требуется интервью/фиксация границ.
- [ ] Спроектировать активный режим отладки, а не только захват входов: команды SPI памяти и управление подтверждёнными линиями AMD.
- [ ] Составить матрицу всех реально доступных функций платы: чтение/запись памяти, управление/сброс, UART, LPC/POST, SMBus, возможный JTAG; для каждого отдельные ограничения, протокол, необходимые контакты/оборудование, проверка и восстановление. Возможность не считать доказанной по наличию разъёма.
- [ ] Уточнить допустимость активных действий по памяти BIOS: чтение/идентификация отдельно от erase/program; все активные действия только при доказанном владении общей шиной, не одновременно с работающим FCH.
- [ ] Сохранить прежние незавершённые функции, финальный образ/прошивку/цветную инструкцию и запрет прерывать текущую игру. «Максимум» не означает подключить неподтверждённые линии или разрешить команды сейчас.
- [ ] Старое исключение автономного обхода PSP не отменять без конкретной постановки; активная отладка не обещает универсального доступа или обхода защит.

Continuation before active-debug scope decision: finish already-observed sampler overrun/timing fix rather than silently implementing erase/program. New AGENTS Plane path accepted; configured MCP search (corrected unsupported per_page parameter) and BC250 project list succeeded, no Waveshare item found in20listed tasks; no unrelated task selected or mutated. Full active-debug request retained; BIOS-write boundary interview answer remains pending. Rebuild association after actual sampler changes: finite PIO self-stop, RXSTALL rejection, rateclk_sys/2.

Sampler timing fix verified: native overrun regression exit134 before change then exit0; finite PIO stop prevents post-completion RXSTALL and runtimeRXSTALL invalidates data. Accurate rate clk_sys/2; rehashed source a18a9736bcbe. Active-debug scope expansion retained separately, awaiting BIOS-write boundary answer; no active AMD operations.

[x] Active-debug capability matrix created and reopened:9function groups covering SPI read/write, UART, LPC, SMBus, JTAG, power/reset, fan and retained controller/network. Explicit implementation gaps and1.8V/JTAG/unpopulated/2mm/shared-bus constraints recorded; not substituted with Linux metrics. BIOS erase/program boundary answer still pending. No hardware actions. Earlier tasks remain open.

[x] Reuse audit checked current Pico SDK revision079c6f39023649b154152db30f1d781e884879bc: UART raw TX blocks without local deadline; SPI init defaultsmaster, read generates clock/output. Reuse existing UART1/ring, but active TX requires boundedqueue/gates. Ordinary SPI command driver can use SDK without legacy injection rig; exclusive bus before init required. Active implementation not started pending shared-understanding interview; erase/program choice remains unanswered.

## Новый запрос: человеческий пост BC250 Gaming
Директива, средний размер: переписать предоставленный пост под живой Reddit-подобный стиль, пригласить к совместной работе без выдуманных результатов.
- [ ] Найти useful.software.md и перечисленные humanizer-инструменты/скиллы.
- [ ] Посмотреть публичные stars lildebil0 на GitHub, определить относящиеся humanizer материалы, не запускать сторонний код.
- [ ] Посмотреть реальные посты Reddit BC250 через доступный браузер, сохранить стиль/цель без публикации.
- [ ] Выдать готовый русский пост для темы BC250 Gaming, различить текущие результаты и планы; подмена PSP не доказана и не обещается как рабочий способ.
Все предыдущие задачи прошивки и открытый вопрос erase/program сохранить; этот запрос не разрешает флеш, питание, публикацию или отправку поста.

Post task result: found registry useful-software.md, inspected relevant prose rules from registry and public lildebil0stars (ten repositories, no third-party install/execution). Russian draft created/reopened in cache, local installed scanner via alreadycached deps exit0,100/100 (not authorship proof). Real Reddit examples not read: both browser paths disconnected, OpenCLI exit69. Draft deliver now with explicit research limitation, no publication. Firmware tasks and unanswered active BIOS-write boundary unchanged.

## Уточнение поста: английский для Reddit
Директива, простой размер: адаптировать уже согласованный русский черновик на естественный английский для Reddit. Публикация ещё не выполнена; конкретный subreddit/URL не указан. Не публиковать в произвольно выбранном сообществе. Все задачи прошивки и открытые решения сохраняются.

Active-scope impasse: same unanswered BIOS erase/program inclusion gate recorded across sampler closure, matrix, SDK reuse and current revalidation. Those preparation steps are complete; no live process remains. Current diagnostics check passes but is no new active-debug progress. Full implementation/flash/connection/acceptance remain open. English post delivered, publication waits unspecified subreddit. Goal blocked audit ready; not marked complete.

Feedback: «claude работает лучше». Simple evaluation, no new directive, no agent handoff authorization. Revalidated prior work: many offline/source/report increments, but requested final device image/flash/connection outcome still not delivered. Do not claim complete or replace result with repetitive green checks. All earlier tasks retained.

Blocked audit committed: active scope boundary still unanswered, gate process exit2. Same condition repeated in recorded sampler/matrix/reuse/current continuations; no remaining preparation changes substitute for the requested active implementation. Stop automatic goal churn; retain full objective, previous artifacts and unfinished tasks. Need owner scope decision to proceed under plan. No flash/power/publication.

## Ответ заказчика: А, включить стирание и запись BIOS
Директива, средний размер: решение уже заданного интервью, не новая цель. Включить обычные функции чтения/стирания/записи/проверки BIOS в проект активного отладчика. Физическая запись отдельно после подтверждённой резервной копии, восстановления и разрешения на точный образ/чип. Ответ А не разрешает запись сейчас, подмену PSP, гонки/инъекции, сброс AMD во время игры или публикацию Reddit. Сохранить все прежние открытые задачи.

A scope accepted, gate resolved. First active-debug implementation: pure conventional NOR command builder supports ID/status/read128/pageprogram256/4KiB erase/write-enable, exact bound checks and default-deny bus/write guards. Native regression missing-module baseline compileexit1 then implementationexit0. This builds frames only, not a physical SPI backend; GPIO/bus ownership/chip validation/readback/image approval enforcement still pending. No hardware write.

Active conventional NOR operation engine implemented on staged copy: WREN→WEL/status check→program/sector erase→busy poll→full requested-range readback comparison;5s deadline, ownershiploss abort beforetransport, no generic commands. Actual engine C compiled against emulated NOR; program/erase/verification mismatch/timeout/gate cases pass. Physical SPI transport/CS backend and exact-image authority binding remain incomplete; no device commands. New native-engine project regression compiled/executed successfully.

## Новая директива: немедленная схема подключения и аппаратные тесты
Тип: директива. Размер: средний, уточнение уже согласованной интеграции.
- [ ] Сейчас выдать точные пины/тип DuPont, без пайки, для уже подтверждённых интерфейсов; не выдавать неготовый activeSPI за рабочий программатор.
- [ ] Учитывать новое разрешение на аппаратные тесты и перезагрузку через принадлежащую розетку; прежнее ограничение «пока играю» снято этим сообщением. Не выполнять действие на неподтверждённой розетке/машине.
- [ ] Сначала установить наличие готовых контактов/колодок и ориентацию экземпляра; не требовать мультиметра, не предлагать пайку. Если механика неизвестна, обозначить условие и попросить фото, а не выдумывать наличие штырей.
- [ ] Точное разрешение физической прошивки BIOS и образ по-прежнему отдельно; «карт-бланш на тесты» не называет образ и не доказывает восстановление.
Сохранить все незавершённые active-debug/финальная прошивка/инструкция/приёмка задачи.

Physical SPI transport implemented in source, defaultdisabled: diagnostic+wiring+isolated-bus confirmations before pins/SPIinit, fixed10SCK/11MOSI/12MISO/13CS,100kHz, FIFO budget64,1s transferdeadline/10s sessionlease, explicit normal-opcode allowlist, timeout/mode loss deinit toinputs. Passive trace normalized to same four wires (CS bit3), mutual exclusion added; no SPI wiring has been issued to owner. Exact transport mockSDK and actual-engine emulator tests pass; actual board/electrical timing untested. Operator booleans are not isolation proof. No CDC active command endpoint/image authority binding yet. No live operation or flash.

## Исправленная транскрипция: консоль свободна, разрешены аппаратные тесты
Директива, простой размер: уточнение разрешения, не смена цели. Заказчик больше не играет; BC250 свободна для тестов, включая перезапуск через принадлежащую умную розетку при зависании. Может подключить провода к указанным разъёмам. Прежний запрет прерывать игру больше не действует. Не спрашивать повторно разрешение на обычные тесты/перезапуск. Сначала подтвердить точную машину и розетку; не считать неизвестное питание/изоляцию подтверждёнными. Неподтверждённые контакты не назначать по догадке. Ограничение без пайки/мультиметра сохраняется. Физическая прошивка требует точного образа/цели, полной копии и подтверждённого восстановления по проектному контракту; общий допуск к тестам этих фактов не создаёт. Все прежние задачи сохранить.

User provided192.168.1.245 as current address in BC250 reachability context. Simple directive; bind as BC250 HOST for read-only identity check, not socket address. Earlier .118 failure is stale-address reachability, not board death. Preserve prior tasks/approval constraints.

[x] Actual BC250 reachability/identity at owner-supplied192.168.1.245 confirmed ping+SSH+DMI. Installed reportedP3.00 and current customkernel observed, not exact-ROM hash proof. Real readings GPU57C/CPU64.625C/fan2 2312RPM collected without writes. Previous192.168.1.118 unreachable was wrong/stale endpoint; do not repeat offline-board claim. Socket readON, no reset executed.

## Новый запрос: единый сайт-инструкция и полная ясность по разъёмам
Директива + вопросы, средний размер: развить уже согласованный HTML-артефакт, не менять цель/добавлять новые интерфейсы по догадке.
- [ ] Выдать именно удобный сайт-инструкцию с цветными проводами, двумя платами, пошаговым подключением для новичка.
- [ ] Явно показать число разъёмов, пинов и проводов для текущего этапа отдельно от полного проектного расширения.
- [ ] Объяснить TPMS1/LPC и остальные разъёмы: что реализовано, что планируется, какой шаг/кабель, почему нельзя обещать готовность неподтверждённого интерфейса.
- [ ] Дать честный ответ по UART: документально установлены направления J5, входRX реализован; реальный журнал/скорость/включение отладкиAMD ещё не доказаны.
- [ ] Никакого объявления частичного UART-подключения всей выполненной задачей. Сохранить activeSPI erase/program и все прежние открытые пункты.

Site instruction updated with first-stage2UART wires/counts, colored embedded diagram and official pinout, full connector tableTPMS/LPC2mm, SPI5wirefuture mapping, SMBus/JTAG/fan readiness and honest UART observed-vs-doc status. Not all-connectors ready claim. Local identify/read service compiled, not physically executed; destructive commands not exposed until preflight complete. Real Linux collector ran on192.168.1.245, no serial device/Waveshare found in AMD USB snapshot.

Actual service+engine+authority regression exposed ID→READ bug: previous engine abort callback deinitialized newly-enabled SPI. First test abortedexit134, fixed ordering by stopping old engine before enabling new transaction, test passes. Native tests now cover identified-supportedID, readbounds, modegeneration, USBdisconnect, leaseexpiry, unsupportedID and transportfailure. ExactCDC fixture checks guardedopen/read/data/invalid args and rejects destructive commands. Active destructive integration and PSP signedregion preflight remain open, not narrowed out. No hardware commands.

Host protected-region preflight implemented: root/checksum/bounded PSP reference graph and conservative prefix unchanged, unbounded refs/unmappedPS1 rejected; no byte/key/offset output. Native plan regression first failed ValueError notraised for modifiedPSP, after implementation3tests pass. Owned original dump/2.bin self-check passes scoped byte preservation, signature validation notperformed/fullsignedscope false. Packaging whitelist includes helper. No physical write authorization inferred; destructive service remains to bind/implement, full goal retained.

Destructive service source API bound to current adaptertag/JEDEC/modegeneration + exact approved digest/matchingbackup hashes/recovery+protected-scope host attestations. Immutable4096sector copy, exactpagebyte match before SPI; normal erase/program retains independent readback, mismatch revokespermit. Actual service+engine+authority tested with emulatedNOR including erase/program/mutatedpayload/badtarget/missingpreflight. Host attestations not signature/hardware proof; no destructive USB command exposed yet. No physicalwrite.

Feedback repeated: «claude работает лучше!!!». Simple feedback, no new task. Root cause remains overlong iterative scope and failure to deliver final flashed hardware result. Record for correction, preserve all open tasks; do not claim complete.

Framed localUSB writer implemented; actual CDC→CRC→service→NOR emulator tested erase+16page program+readback and corruptframe revocation. ARM linker exposed RAM overflow2832bytes, so NO new firmware image accepted. Three failed attempts to drop duplicated immutable sector cache were stopped; prior verified service/authority restored from same MODIFIED_FILE and nativeE2E passes again. Next changed design: reuse inactive passive capture scratch for incoming frame, preserving both immutable sector copies and explicit mutual exclusion; do not repeat broken pointer/cache optimization. Full goal remains open, no device flash or power action.

ARM RAM closure succeeded by restoring audio stack32KiB and leasing existing passive8KiB sample buffer for framed flash input; mutual exclusion prevents simultaneous sampler/flash. New framed CDC E2E emulator and87 tests pass, buildRAM relocation exit0. No new intermediate upload; source ID refresh pending final build.

## Feedback: использовать существующий GitHub-стек, не переписывать всё
Тип: консультация/корректировка направления, простой размер. Зафиксировано требование: явно отделять собственный glue-код от заимствованных DS5Dongle/Pico SDK/BTstack/TinyUSB/lwIP и существующих BC250 host tools; искать и переиспользовать доступные upstream компоненты прежде чем писать новое. Ошибка текущего шага: /dev/ttyACM0 оказался DualSense 054c:0ce6, probe получил PermissionError, это не Waveshare и не доказательство отсутствия прошивки. Не запускать probe на этом узле повторно как на Waveshare. Все предыдущие задачи сохранить.

## Новая директива: исследовать GitHub/Trends и переиспользовать готовые решения
Тип: директива, сложный размер. Не писать новые подсистемы до аудита существующих репозиториев.
- [ ] Провести read-only поиск GitHub repositories/code/releases/trending по BC250, PSP/VCN, DS5Dongle, RP2350 SPI programmers, NCT6686/LPC/POST/SMBus.
- [ ] Для каждого кандидата записать URL, revision/date/license, relevant files, capabilities, compatibility, security/data risks, maintenance and rollback; distinguish upstream code from claims.
- [ ] Compare candidates against current staged source; adopt/adapt only components that are actually reusable and authorized.
- [ ] Do not clone/execute/install unreviewed third-party code, do not post, flash or write AMD. Preserve prior open tasks and final artifact requirement.

GitHub reuse audit completed read-only: DS5Dongle confirmed adaptable base; official/community BC250 docs and BIOS recovery repos retained as references; 40CU/UMR/control-center host writers deferred; Shalasere and bot VCN research separated direct driver-load evidence from unresolved SMU gate; simpmix encoding repo NEEDS-EVIDENCE, not adopted. No clone/install/execute/hardware mutation. Audit at docs/research/2026-09-30-github-reuse-audit.md.

[x] Independent preconnection package/audit refreshed after GitHub reuse and framed writer changes. Package includes current helpers; final gap audit explicitly separates offline source proof from missing hardware/product acceptance. Goal remains active and not complete.

Continuation: Waveshare remains absent from USB; ttyACM0 is DualSense. No valid live Waveshare action available, so no duplicate probe or report churn. Next action remains identify exact Waveshare CDC after physical connection.

Owner: «подключил». Simple directive/status: revalidate connected device now, run only bounded read-only identity probe on target-correlated CDC; do not infer GPIO wiring/isolation or exact-image flash approval. Earlier firmware and hardware tasks retained. Note: Sony VID alone cannot exclude Waveshare because DS5Dongle deliberately emulates Sony and addsCDC.

[x] Waveshare physically connected and live CDC confirmed: /dev/ttyACM0 Sony-emulation VID054c/PID0ce6, recognized DS5Dongle bridge VERSION c1e7627/build2026-09-28T21:32:39Z/MODE controller; STATUS recognized. This is the old installed firmware, not current candidate. Read-only probe passed; no upload/reset/BIOS command.

Current target revalidated: /dev/ttyACM0 bus1/dev11 VID054c/PID0ce6 Sony-emulation bridge, VERSION c1e7627; stale BOOTSEL address8 no device. Candidate remains NOT_FINAL, no flash.

Reuse correction: source-level pinned audit found existing pico-serprog variants and installed flashrom1.8.0. Standard flashrom/serprog preferred over adding new homemade host programmer; standalone code defaults SPI outputsON/blocks I/O and lacks RP2350/composite proof, so must adapt not flash unchanged. No upstream code executed/installed or physical operation. New-source handoff/reuse evidence written; preserve all current prototype and incomplete tasks.

[x] Actual upstream reuse feasibility: pinned pico-serprog builds unchanged for RP2350/pico2 using existing SDK, strict UF2 structure checked, no hardware upload. Existing flashrom host can replace custom host programmer work. Upstream GPIOsdefault1/2/3/4 + masterON, fixedPIO/stdio blocking require adaptation; do not flash standalone into combined adapter. All original full-plan gaps remain open.

Вопрос заказчика «какая причина»: объяснить единственную причину блокировки простыми словами, без новой разработки или действия.

Уточнение заказчика: «почему нет доступа к плате?!». Исправить формулировку: доступ к AMD BC250 и Waveshare есть; блокировка не по доступу, а по финальному образу/приёмке. Ничего не запускать.

## Уточнение заказчика: выбрать тестовый UF2 и прекратить повторные запросы
Директива, простой размер: заказчик явно просит назвать образ для теста и принимает, что он не полностью проверен. Выбран тестовый кандидат Waveshare-RP2350B-Plus-W-DualSense-WiFi-MQTT-LinuxMetrics-TEST.uf2, SHA256 6c5b4a321b2c79a63b9b0af8cf76c307405364db00a112486e5b454c18705b2a, target RP2350B-Plus-W. Это согласие на тестовый кандидат, но не отменяет жёсткий запрет физической прошивки без полной копии/восстановления и плана readback. Не повторять общий вопрос о выборе образа; перейти к конкретному preflight и затем действию.

## Явное разрешение на тестовую прошивку
Директива: владелец разрешил прошить выбранный TEST UF2 `6c5b4a321b2c79a63b9b0af8cf76c307405364db00a112486e5b454c18705b2a` на Waveshare RP2350B-Plus-W. Разрешение записано; физическая запись начинается только после наблюдения RP2350 BOOTSEL и проверки устройства. Текущий USB всё ещё Sony-emulation bridge, не BOOTSEL. Требуется действие владельца: удерживать BOOT, нажать RESET, отпустить BOOT. Не использовать DualSense ttyACM0 и не подавать UF2 в работающую CDC.

[x] Owner-authorized exact TEST UF2 flashed to verified RP2350 target: fresh double16MiB backups matched d3dec91f..., picotool load verify100% and reboot exit0. Postflash app USB not yet enumerated; VERSION/STATUS unavailable, hardware acceptance pending. Recovery via saved backups/BOOTSEL retained. Do not infer app crash until reconnect/retry.

[x] Owner explicitly approved rebuilt USB-survival TEST UF2 SHA e822a65145dbe23cef60a22cf098223707cccef2db9f7ef2bcdbd62a9444ecaa. Current USB check shows no RP2350/CDC, so write cannot start until owner reconnects in BOOTSEL.

- 2026-10-01 continuation: operator reports BOOTSEL reconnect complete; execute approved UF2 load for exact hash e822a65145dbe23cef60a22cf098223707cccef2db9f7ef2bcdbd62a9444ecaa.

- 2026-10-01 blocker audit: repeated live USB discovery confirms BOOTSEL absent. Approved e822 UF2 loaded and picotool verification passed, but application did not enumerate. Readback requires physical BOOTSEL reconnection. No live process is waiting.

- 2026-10-01 resumed continuation: operator reports BOOTSEL reconnect complete; perform pending independent flash readback for approved e822 image.
- 2026-10-01 result: approved image read back from BOOTSEL and `picotool verify` returned OK. Static startup audit found missing `board_init()` before TinyUSB; minimal candidate-only fix added `board_init()` and `board_init_after_tusb()`. New UF2 built and startup/format tests passed. New image requires separate explicit approval before hardware write.

- 2026-10-01 directive (medium): operator explicitly authorizes flashing USB-init-fix UF2 SHA-256 4ffac696aee995d250b6c0762e05d599811892de348e7111aa50159d236d8d13. Keep earlier authorization and readback records.

- 2026-10-01 continuation: BOOTSEL reconnect reported; retry already-authorized USB-init-fix UF2 load, exact SHA-256 4ffac696aee995d250b6c0762e05d599811892de348e7111aa50159d236d8d13.

- Hardware check: approved 4ffac696 image verified in flash; application still absent. USB startup fault remains open. Next: instrument startup phases before further hardware experiments, not blind reflash.

- 2026-10-01T00:27:20+06:00: user confirmed Waveshare connected; resume read-only VERSION/STATUS action.

- 2026-10-01T00:30:43+06:00: user requested immediate Waveshare USB/BOOTSEL check.

- 2026-10-01T00:34:11+06:00: user completed BOOTSEL exit; check application enumeration and VERSION/STATUS.

- 2026-10-01 result: after BOOTSEL exit, application still did not enumerate. Built a USB-only diagnostic candidate from the existing TinyUSB/DS5Dongle stack; exact SHA-256 e7ec04c2938be0a384e2dffe1a4b5c1d88c3591a89778f0837cb9f8ae5c86c14. No flash authorization for this new image yet.

- 2026-10-01T00:52:03+06:00: directive (simple): owner approved USB-only diagnostic UF2 e7ec04c2938be0a384e2dffe1a4b5c1d88c3591a89778f0837cb9f8ae5c86c14; preflight and write exact image if RP2350 BOOTSEL is present.

- 2026-10-01T00:53:01+06:00: user reports RP2350 BOOTSEL ready; perform approved USB-only diagnostic UF2 write.

- 2026-10-01 result: approved USB-only diagnostic UF2 e7ec04c2938be0a384e2dffe1a4b5c1d88c3591a89778f0837cb9f8ae5c86c14 copied to RP2350 BOOTSEL; reboot/unmount observed after 2s; `/dev/ttyACM0` appeared as root:uucp. USB enumeration is now hardware-observed. VERSION/STATUS read is pending because current user is not in uucp and noninteractive sudo requested a password; no permissions changed.

- 2026-10-01T00:56:05+06:00: directive (simple): user requested omarchy skill guidance for the pending device-access command.

- 2026-10-01: simple troubleshooting: user ACL command used /dev/ttyACM without numeric suffix; check actual device path before correction. Earlier tasks retained.

- 2026-10-01T01:06:15+06:00: user applied ACL to /dev/ttyACM0; run read-only VERSION/STATUS now.

- 2026-10-01 result: ACL applied; VERSION/STATUS writes reached `/dev/ttyACM0` and exited 0, but no reply because USB-only diagnostic intentionally omits cdc_dispatch_tick. USB enumeration is hardware-verified; next candidate must retain USB-first startup and run CDC dispatcher before subsystem initialization.

- 2026-10-01T01:09:23+06:00: directive (hard): audit all firmware-build mistakes and produce a decision-complete plan ending with Waveshare flash and BC250 installation; retain earlier tasks.

- 2026-10-01T01:23:55+06:00: directive (hard): implement the approved USB-first Waveshare/BC250 plan; keep prior open tasks and preserve recovery artifacts.

- 2026-10-01 implementation result: USB-first source slice built from existing DS5Dongle/TinyUSB/BTstack path. Added startup stage/error reporting, bounded CDC servicing before CYW43 and between bridge init steps, and nonblocking watchdog notice. Production RAM relocation passed; focused tests 21 passed; make test 7 passed. Candidate: reports/waveshare-implementation-20260930/guide/Waveshare-RP2350B-Plus-W-USB-first-controller-diagnostic-TEST.uf2 SHA-256 aba20b1dc0193c6484d93937425b4451df0fbcb9df6ac560fc5040365926bfa3. Hardware write not performed; exact image requires separate approval.
- 2026-10-01 correction: repaired the build action log after an unquoted heredoc stripped code/path substitutions; artifact and source were unaffected. Log now records exact path/hash and PASS evidence.

- 2026-10-01T02:15:48+06:00: directive (hard): owner approved exact USB-first UF2 aba20b1dc0193c6484d93937425b4451df0fbcb9df6ac560fc5040365926bfa3; BOOTSEL reported ready; perform preflight and one write.

- 2026-10-01 flash result: exact approved USB-first UF2 aba20b1dc0193c6484d93937425b4451df0fbcb9df6ac560fc5040365926bfa3 copied to RP2350 BOOTSEL; reboot observed after 2s; post-write USB enumerated as Sony-emulation `054c:0ce6`; `/dev/ttyACM0` exists. Image write is hardware-observed. Read-only VERSION/STATUS pending because recreated tty node has root:uucp and no ACL.

- 2026-10-01T02:19:18+06:00: user applied ACL to recreated /dev/ttyACM0; execute read-only PING/VERSION/STATUS/HELP probe on flashed USB-first candidate.

- 2026-10-01 result: after ACL, PING/VERSION/STATUS/HELP writes exited 0 but returned no bytes. USB enumerates; command acceptance is not yet proven. Fresh reset + immediate early-window probe is the next discriminator; do not claim CYW43 root cause yet.

- 2026-10-01T02:35:01+06:00: directive (hard): deep research existing BC250/Waveshare/DS5 software stacks and repositories; retain firmware recovery and prior implementation tasks.

- Research continuation (directive, existing hard task; no new interview needed): falsified broad CDC/audio incompatibility and automatic double-TinyUSB-init claims using official cdc_uac2 and actual compiler preprocessing. TLV persistence failure remains a scoped hypothesis, not CDC root cause. See docs/research/2026-10-01-waveshare-upstream-claim-corrections.md. Earlier firmware/installation requirements remain open, not replaced by separate products.

- 2026-10-01 discriminator: `lsusb -v` on the flashed image shows valid 6-interface HID/UAC/CDC composite (`wTotalLength=0x012d`, CDC interfaces 4/5, endpoints 0x85/0x06/0x86). A read-only host probe asserted DTR/RTS and sent PING/VERSION/STATUS; zero bytes returned. Descriptor malformation and missing DTR are not established causes; runtime startup/CDC service remains the open boundary.

- 2026-10-01 TinyUSB cross-check: official cdc_uac2 example confirms CDC+UAC2 is supported in principle but warns same VID/PID with different interface layouts can cause host errors; static descriptor, class-map PID and fixed endpoint mapping are used. Dynamic Sony composite remains unproven for our layout.

- 2026-10-01 UART research correction: current CMake has `pico_enable_stdio_uart(unified 0)` and ELF lacks stdio_uart symbols; upstream DS5Dongle/Linux Bridge enable UART0 GP0 115200 and disable USB stdio. Existing flashed candidate therefore cannot provide the promised upstream-style GP0 boot log. This is source evidence, not a hardware root-cause claim.

- 2026-10-01 probe research: official TinyUSB CDC app gates RX on `tud_cdc_connected()`/DTR; existing waveshare_probe.py does not assert DTR. Manual DTR/RTS discriminator still got zero bytes from current flashed image, so this is a host-tool compatibility gap, not a proven current root cause.

- 2026-10-01 SDK research: Pico SDK already has CDC magic-baud reset (default 1200) to BOOTSEL via rom_reset_usb_boot_extra. Current CMake disables both baud and vendor reset paths. A debug candidate could enable baud reset without adding a vendor interface; descriptor/callback compatibility remains to validate.
