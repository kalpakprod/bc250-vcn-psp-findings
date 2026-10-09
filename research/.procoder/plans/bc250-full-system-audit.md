# Полный системный аудит BC-250

Status: scope corrected, maintenance-window decision pending.
User correction: нужен не обзор графики/конфигов, а максимально полный учёт системы.

## Проверяемый результат
- Карта всех смонтированных постоянных файловых систем и точные границы обхода.
- Реестр файлов и ссылок: путь, тип, размер, владелец, права, время, пакетное происхождение. Отдельные счётчики ошибок/недоступных путей. Обход без перехода по symlink и без исполнения файлов.
- Пакетные файлы: проверка наличия/прав/контрольных сумм по доступным пакетным эталонам. Не путать локальную БД пакетов с независимым доверенным эталоном.
- Непакетные исполняемые файлы, библиотеки, конфиги, загрузчики, hooks, автозапуски: назначение, ссылки, активность и восстановление происхождения, где возможно. Не утверждать неизвестное происхождение как вредоносность.
- Все обнаруженные механизмы постоянного запуска: system/user units и зависимости, timers/cron, shell/session env, XDG, udev, modprobe/initramfs/boot, sudo/polkit metadata, containers/Flatpak/пользовательские менеджеры при наличии.
- Сопоставление установленного с реально используемым: process executable/maps, открытые удалённые файлы, активные overrides, конфликты и дубликаты.
- Матрица оставить/исправить/карантин/неизвестно с обоснованиями. Никаких автоматических удалений.
- Отчёт о покрытии: число файлов, объём реально прочитанных байтов, проверенные эталоны, ошибки и остаток.

## Ограничения
Не раскрывать и не копировать секреты. Содержимое ключей, токенов, паролей, приватных пользовательских данных не читать для общей инвентаризации. /proc,/sys,/dev обходить только целевыми read-only запросами, не хешировать виртуальные файлы. Сохранения не удалять. Игровые архивы/медиаданные учитывать в реестре; полная checksum-проверка требует отдельного учёта объёма, не означает понимание содержания. Сетевые/съёмные чужие носители не включать без подтверждения принадлежности.

## Этапы
1. Согласовать окно нагрузки. Получить карту дисков и размеров без полного чтения содержимого.
2. Ограниченный по I/O и CPU однопоточный файловый реестр, пакетное происхождение.
3. Контрольные суммы и независимые эталоны для системного кода, классификация изменений.
4. Полная карта активации/влияния. Отдельный независимый review при переходе к рискованной очистке.
5. Согласовать конкретные изменения и перезапуск. Снимок, обратимый карантин/исправления, проверка запуска и игры.

Не завершено: этапы 1–5. Предыдущие отчёты являются входными данными, не заменяют эти этапы. Проблема Spider-Man и возврат FOV остаются открытыми.

User approved execution and maintenance-window proposal. Begin low-priority inventory now. No cleanup or restart approval inferred.

Checkpoint: full metadata traversal completed exit0, 5,615,530 entries / 0 errors, including snapshots and all mounted local volumes. Full pacmanQkk completed exit1,1463packages421278entries,9packageswithdeviations. Classification1563unowned regular systemfiles. Report docs/research/2026-09-23-full-system-audit.md. Stage2 complete for metadata/localownership,stage3localmtreecomplete butindependentarchivespending. Stage4 semantic/provenance review incomplete. No cleanup. NEXT: nativeACPIoverride semantics/provenance and remaining activecustomscripts, thenexactnormalizationplan.

Checkpoint continuation2: iasldecode2/2exit0, nativeidleC2/C3andPSS3200..800matchedsysfs. BootAE_NOT_FOUNDrecorded, attributionunresolved. Staticreviewfoundcombo/transientfalsePASSpath, netconsolefalseONLINE, inactiveCPU/GPUwritersandCUmgr. nftemptyrulesetexit0. NewF29–F36appended. NEXT: user-levelpersistentlaunchers/SteamProtonper-gameoverrides + independentpackageetalonofsecurityrelevantdeviations. No cleanup.

Checkpoint continuation3: userlaunchandSteamtoolmappingverified. libutempterfalsepositiveexplainedbyownedtmpfilespolicyandindependentlydownloadedmatchingbinary. ActualDRMdebug0supersedesconfig-onlyassumption. ReportF37–F40. NEXT: captureindependentverificationremainingalteredpackageobjectsandpersistentuserhooks, consolidateactionablecleanupmatrix. No cleanup.

Checkpoint continuation4: remainingQkkdeviationsclassifiedbyownedhooks/tmpfiles/FAT. Signedhandheld/hooksverified. NewDeckyvariabletypo,danglingly/dmemlinks, OptionalTrustAllrepo, persistentVCNmenu-generator profiles. AMDmicrocodedownloadwasdifferentversion, comparisonrejected, exactoldversionindependentcheckopen. NEXT: consolidatecoverage/exceptionsandcleanupmanifest, verifyallremainingunownedactiveconfigrefs. No remotechanges.

Checkpoint continuation5: realunitWants/RequiredBychecked, cleanupmanifestA1–A8createdandvalidated8/8sections. Path docs/research/2026-09-23-system-cleanup-manifest.md. No mutations. Audit deliversfullmetadata+packagechecks+identifiedactivationchains, unresolvedsemantic/independentetalonlimitsretained. Nextrequireddecision: approveexactreversibleA1Vulkanoverridequarantineandgraphicalsessionrestart; othergroupsnotblanketauthorized. FurtherauditcanpursueACPIprovenancewithoutrestart.

Checkpoint continuation6: exactliveACPI hashesmatchinstalled, snapshots126–135same, filenamesourcecensusnoDSLmatches. No moreequivalentACPIhashchecks. A1 restart awaitingexplicitapproval (alias2 notapproval by usercontract). Remainingresearch: differentlynamedsourceprovenance/independentoldmicrocode optional, notcleanupblocker. NEXT actionable: approvedA1execution, otherwise finish auditwithdeclaredunknowns.

Checkpoint continuation7 FINAL_READONLY_AUDIT: remaininglocaljournal/referencechecksfoundnoACPIauthor/sourceandnoexactoldmicrocodecache. Final audit conclusion docs/research/2026-09-23-audit-conclusion.md, coverage/unknownsclear. STOP equivalent scans. Auditdeliverycompletewithlimits;cleanupnotexecuted,gameissueopen. Await explicit authorization of exactA1 session interruption, no repeated approval prompts.

A1APPLIED with explicituserapproval"дазкарывай": twooverridefilesrenamed.disabled-a1-20260923. FirstDMrestartfailedruntimeacceptance(oldenvpersisted); correctedfullusermanager/DMcycle succeeded13:04:14. NewSteam123545envclean, gamescope-wl123305maps/usr/lib/libvulkan_radeon.so. OC/fanpreserved. Rollbackscript executedoncopyhashmatches. NoFPSacceptance. RemainingA2–A8unapplied, FOVopen.

A1followup: gamePID131192 actualmapsconfirmssystemRADV, noOptiScaler. Newlog13:08:54. Nextacceptance: same-sceneperformance, notdriveridentityrechecks. A2–A8notapplied,FOVpendingclosedgame.
