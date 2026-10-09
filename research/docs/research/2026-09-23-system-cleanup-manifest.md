# BC250: перечень нормализации после аудита

Статус: ПОДГОТОВЛЕН, НЕ ПРИМЕНЁН. Авторизация аудита не является разрешением закрыть сеанс или удалить файлы.

## Обязательные правила исполнения

Перед каждой группой: свежая проверка состояния, архив только точных изменяемых несекретных файлов с правами/владельцами/хешами, журнал намерения, обратимый патч/карантин, проверка, откат на копии. Никаких rm-rf, удаления сохранений, префиксов, snapshots, ключей или всех старых пакетов. Не запускать тесты разгона. Закрытие Steam/сеанса отдельно согласуется.
Не менять CPU3900/-35, GPU2200/1015, fan curve,40CU, BIOS в рамках этой нормализации.

## A1. Выбор Vulkan — первым

Точные источники:
/etc/environment.d/60-bc250-gfx1013.conf
/home/OWNER/.config/environment.d/60-bc250-gfx1013.conf
Действие: перенести эти два override в именованный резервный каталог, не удалять /opt/bc250-gfx1013. Убедиться, что ранее отключённый profile.d не активирован.
Применение: согласованный полный выход/вход графического сеанса, НЕrestart GPU governor.
Приёмка: окружение нового Steam не содержит старого/optICD; контейнерныйICD и /proc/новыйигровойPID/maps указывают системнуюMesa. Проверить64/32bitмаршруты. Отдельныйsame-scene FPS/frame-time прогон.
Откат: вернутьобаoverride, новыйсеанс. Старыйдрайверсохранён.

## A2. Политика памяти — отдельное сравнение

/etc/sysctl.d/99-bc250-gaming.conf
/etc/sysctl.d/99-bc250-swappiness.conf
/etc/sysctl.d/99-swappiness.conf
/etc/sysctl.d/99-zzz-bc250-zram.conf
Действие: убратьдублирование, подготовитьединственныйпрофильдляфайловогоswap. Начальнаяконсервативнаягипотезаswappiness60, не«доказаннолучшее». Остальныеполяzramпрофилянепереноситьслепо.
Неswapoff, небезусловныйsysctl--system, незапускzram.
Приёмка: одинwriterкаждогополя, фактическоезначение, PSI/swapI/Oвтойжесцене; rollbackточныхпредыдущихзначений.

## A3. Кастомный потолок dmem

/etc/systemd/system/dmem-app-ceiling.service
/etc/systemd/system/multi-user.target.wants/dmem-app-ceiling.path (битаяссылка)
/usr/local/bin/dmem-wait-appslice.sh
Действие: после проверки reverse-deps убратькастомныйдополнительныйпотолокизавтозапуска, оставитьпакетныйdmemcg-booster. Скриптсохранитьвкарантин.
Приёмка: actualapp.slice dmem.max/low/current, нетпротиворечияlow>max, играбезрегрессии. НеобещатьисправлениеFPS.

## A4. Диагностика, а не вечный аварийный режим

/etc/systemd/system/bc250-metrics.service
/etc/systemd/system/bc250-boot-forensics.service
/etc/systemd/system/bc250-netconsole.service
/etc/modules-load.d/bc250-netconsole.conf
/etc/modprobe.d/netconsole.conf
/usr/local/libexec/bc250-netconsole.sh
/etc/sysctl.d/99-bc250-printk.conf
/etc/sysctl.d/99-bc250-verbose.conf
/etc/modprobe.d/99-bc250-drm-debug.conf
Действие: выбрать отдельный отключаемый диагностическийпрофиль; устранитьWantsnetconsoleиздвухunitsилисначалаисправитьегоисделатьреальнуюпроверкуприёмника. Неотправлятьсетевыепробынастарыйадресбезподтвержденияадресата.
Приёмка: отсутствие скрытоговключения, ошибкинепревращаютсявONLINE, диагностиканевозвращаетсяпослерестарта.
Watchdogнеудалятьвэтойгруппе: требуетотдельногорешенияобаппаратнойзащите.

## A5. Битые ссылки и helpers

/etc/systemd/system/multi-user.target.wants/ly@tty2.service
/etc/systemd/system/multi-user.target.wants/dmem-app-ceiling.path
gamescope-xbindkeys.service,ibus-gamescope.service,steam-notif-daemon.service
Действие: битыеlocalsymlinksвкарантин. Длятрёхпакетныхhelpersвыбратьвосстановлениезависимостейлибоявноеотключениененужнойфункции; неустанавливатьпакетыбезсогласования.
Приёмка: целевыеслужбыбольшенедают203/EXEC, остальныефункциисеансасохранены.

## A6. Proton и Spider-Man

/usr/share/steam/compatibilitytools.d/protonge-latest-bc250/bc250-fsr4-launch.py
ПереоформитьсегодняшнееисключениеOptiScalerвверсионированныйпакетилиподдерживаемыйper-gameнастройкойвариант; неоставлятьмолчаливуюправку/usr.
Сохранитьтребованиепользователя: собственныйFSRпуть, безOptiScaler.
ВернутьслучайноизменённыйFOVCorrection0кпредыдущему1250взакрытойигре, снезависимымreadback. НеобъявлятьNativeAAапскейлингом.
Приёмка: nextprocessenv+maps, settingslog, измеренныйframetime. Одногоfpsизжурналанедостаточно.

## A7. Архивировать инструменты экспериментов, не исполнять

/usr/local/libexec/combo.sh,transient.sh,oc-step.sh,cpu-step.sh,cpu-uv.sh,
/usr/local/libexec/bc250-psu-stress.sh,bc250-psu-soak.sh,bc250-vram-stress.sh,
/usr/local/bin/bc250-cu-live-manager,/usr/local/libexec/bc250-cpu-oc.py
Действие: послеполнойпроверкиреференсовобратимыйкарантиннеиспользуемыхtools, отдельныеREADMEобопасностизапуска. combo/transientнепригодныкакавтоматическийPASSgateбезисправления.
НеархивироватьактивныйfanиactualCPU/GPUcontrol.

## A8. Не чистить без отдельной проверки

SSDT-CST/PST: действующиеACPIметоды, требуетсясравнениебезнихсrecoveryиоднойпеременной.
91-bore-vcn-probe.conf: сначалаисточникгенерациииактивныйbootloader,потомсогласованноеудалениеэкспериментальныхменю,срабочимзапаснымядром.
SigLevelOptionalTrustAll,NOPASSWD,Sunshinecapabilities,SSH: отдельнаяполитикабезопасности, ненеобдуманноеотключениеудалённогодоступа.
Backups/Protons/snapshots/DKMS: определитьпотребителейидопустимыйсрокхранения.
utempter,Plymouth,VLC,journalpermissions: штатныепакетныеполитики, оставить.

## Открытые пределы аудита

Всефайлыметаданныхучтены, неносячийназвание«полныйаудит»неозначаетсемантическогопониманиякаждогоигровогоархиваилиотсутствиявредоносности.
Точныйстарыйamd-ucodeподписанныйархивнеполучен, совпадениеслокальнымmtreeесть.
ПубличноеавторствоACPIнеустановлено. Полнаясемантикавсехпользовательскихпрограммнеизучалась.
Очисткаиустранение10FPSНЕвыполнены. Готовапроверяемаяпоследовательность, несертификатбезопасности.
