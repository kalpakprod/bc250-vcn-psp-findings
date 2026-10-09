# Импорт: внешние каталоги и upstream README

Дата: 2026-09-28. Источники полностью читаются ограниченными пакетами для роли
и ограничений; чтение не означает принятие их технических claims.
Это локальные исторические копии, не проверка нынешнего состояния GitHub,
не установка стека и не аппаратное испытание. Сырые файлы не менялись.
Точные пути, размеры и SHA-256: `reports/repository-audit-20260927/phase35-external-source-dispositions.json`.

## Происхождение

| Локальный репозиторий     | Origin из сохранённого Git-config                        | HEAD                                       |
| ------------------------- | -------------------------------------------------------- | ------------------------------------------ |
| `awesome-bc250`           | `https://github.com/kalpakprod/awesome-bc250.git`        | `1e64c12fd734930e753f95f5b96a47f65647e8b2` |
| `bc250-telemetry`         | `https://github.com/onlinermm/BC250-Telemetry.git`       | `0135511b5ce22eeeacd3119907b4cca4850ea17e` |
| `meimei-smu-patch`        | `https://github.com/RescueMei/BC250-DXEv3-SMU-Patch.git` | `058039a2b33422fc05f04b97292ca1f1b143df35` |
| `rescuemei-dxev3-biosmod` | `https://github.com/RescueMei/BC250-DXEv3-BIOSMOD.git`   | `7b100b011a45761735fb94ea6a4ee0128d294dd0` |

У прочитанных документов содержание совпало с Git-объектами этих commit
после нормализации CRLF в LF. Сами архивные байты отличаются переводами строк,
поэтому для точного цитирования нужен SHA-256 файла, а не только HEAD.
Origin и наличие LICENSE фиксируют происхождение, но не доказывают актуальность,
право на конкретный firmware-asset или безопасность запуска.

## Роль шести прочитанных текстов

- Главный английский `awesome-bc250/README.md` — навигация по community-проектам.
  Цены, FPS, напряжения и мощность в нём не воспроизведены. Графики и советы
  не являются принятыми параметрами этой платы.
- `knowledge/README.md` — руководство по извлечённым community-claims. Само
  предупреждает о возможных ошибках LLM и неуниверсальности чужих наблюдений.
- `knowledge/index.md` — индекс, где слово «verified» сильнее проверенного
  основания. Цитата и реакции не заменяют технический опыт.
- README веб-монитора — документация внешнего сервиса, не разрешение менять
  systemd, запускать его или открывать порт.
- README SMU-патча — описание условного DXE reporting patch, не самостоятельного
  unlock и не доказанного успешного включения ядер.
- README xdelta-патча — историческая сборочная инструкция. Совпадение MD5
  не означает готовность к физической прошивке.

## Узкие проверки и находки

### Knowledge — форма цитат, не истинность фактов

В 12 concept-файлах найдено 10 221 верхнеуровневое fact-буллет с нумерованной
ссылкой. У 8 177 есть следующий `src:`-маркер, у 2 044 его нет в заявленном
формате. Содержимое исходных сообщений и правильность attribution не проверены.
Не называть весь bundle аппаратно или независимо «verified».

Шесть root-переводов README сохранили те же 34 внешних URL, что английская
версия. Позднее все шесть body полностью прочитаны для роли (раздел ниже).
Набор ссылок не доказывает правильность перевода или истинность claims;
связанные переводные handbook-главы этим чтением не закрываются.

### Telemetry — фактический сервер шире README

В `web/server.py` есть GET-обработчики `/api/topology` и `/api/overclock`,
которые вызывают чтение состояния системы/настроек, помимо JSON telemetry.
Сервер создаётся с `TCPServer(("", PORT), Handler)` и wildcard CORS;
это не loopback-only просмотрщик. Сервис, установщик и сервер не запускались.
Перед возможным использованием нужен отдельный разбор доступа и поверхности API.

### SMU DXE — возврат успеха не доказывает patch

Проверены только конкретные ветки сохранённого C, не весь драйвер и не железо:

- `SmuPrivilegedWritesAvailable` отвергает лишь статус `REJECTED_PREREQ`;
  остальные терминальные ответы сами по себе не доказывают доступность записи.
- `ApplySmuPatch` увеличивает `MismatchCount`, но в конце возвращает `EFI_SUCCESS`.
- Entry point получает `Status = ApplySmuPatch(...)`, освобождает страницу
  и возвращает `EFI_SUCCESS`, не распространяя полученную ошибку.

Поэтому лог/readback и точный статус важнее факта загрузки драйвера. Исходник
не исправлялся, драйвер не собирался и не применялся.

### Delta-патч — ошибка переноса строк и предел проверки

Сохранённый `.xdelta` размером 1 383 592 байта совпал с MD5 из README;
его SHA-256 записан отдельно в отчёте. Исходный `ApplyDeltaPatch.sh` имеет CRLF
и `bash -n` завершился с кодом 2. Одноразовая копия, где изменены только CRLF
на LF, прошла **только** синтаксическую проверку. Оригинал неизменён.

В Patch-каталоге нет указанного base ROM и выходного ROM. Скрипт использует
удаление временного файла и принудительную замену output. Он не запускался,
xdelta не применялся. Ни MD5, ни синтаксис не заменяют проектную проверку
образа, recovery и точное разрешение на flash.

## Дальше

Четыре выбранных английских handbook-раздела теперь полностью прочитаны
для роли и границ доказательств, но их советы не приняты как конфигурация.
Шесть root-переводов ресурсного каталога также полностью прочитаны для роли.
Английские hardware/OS главы следующего пакета также прочитаны для роли.
WiFi/Bluetooth и USB/peripherals также прочитаны для роли.
Следующий пакет — cooling, cases и buying. Opaque/private
материалы, связанные переводы и остальной semantic-корпус остаются открытыми. Неполученный SAST-ответ из
предыдущей проверки не выдан за успех.

## Handbook: все четыре выбранных раздела

Полностью прочитаны `00-start-here.md` (141 строка), `03-power-supply.md`
(382 строки), `08-bios.md` (406 строк) и `09-overclock-undervolt.md`
(645 строк). Это документная роль/актуальность, не воспроизведение всех
технических claims. Прочитана также политика firmware mirror.
Пофайловые хеши/диапазоны: `reports/repository-audit-20260927/phase36-handbook-dispositions.json`.

### Запуск — не автоматически принятый сценарий

В beginner path смешаны полезные темы (питание, охлаждение, драйверы) с
конкретными изменениями BIOS, установкой сервисов, разгоном и stress-test.
Они не запускались. Версии дистрибутивов/ядра, рекомендации частот и проценты
FPS остаются датированными community-claims. Упоминание `vainfo` рядом с
отсутствующим аппаратным encoder не задаёт достаточный критерий успешной
графики во всех API. Факт вывода утилиты не заменяет проверку нужного поведения.

### Питание — схема вида и нумерация должны быть явными

Сохранённый CAD/parse повторно сверены по их собственным SHA-256. В нумерации
CAD `J1000` сеть `+12VA` относится к контактам 1/3/5, а текст handbook цитирует
неформальное «1–3 плюс, 4–8 минус». Без отображения вида, защёлки и соответствия
нумераций эти описания нельзя применять как одну карту подключения. CAD —
статическое основание, не измерение текущей платы.

Рекомендации контактов/проводов и обещания «без модификаций», «полярность
гарантирована», допустимости параллельной подачи или питания через конкретный
адаптер не проверены по точной сборке и официальным условиям рейтинга.
Разные 16/18/20 AWG в разных схемах не дают универсального предела. Магнитная
проверка сама по себе не удостоверяет всю электрическую пригодность кабеля.
Рецепты удаления индуктора, обрезки жгута, изменения latch и управления PSU
не являются разрешёнными действиями этого аудита.

Безусловное «включается сразу при 12 V» соседствует с условием `AUTO_PWRON`;
«нет кнопки» — с инструкциями использовать power-button/PWR_SW. Это повод
уточнять конкретную конфигурацию, а не обещать работу Waveshare-контроллера.
Каталог MCU/ESP32/адаптеров сохранён как lead, не как проверенная схема проекта.

### BIOS — имя, контейнер и readback не подменяют друг друга

- Handbook приравнивает имя `Robin3.00` к modded chipset-menu SHA-256
  `48fbe5d366e6a56e2fdffdca848426216ba1f083610dab63db89d2f4e6c940b5`.
  Локальный 16-MiB файл с тем же именем повторно прочитан и имеет другой SHA-256
  `5d659a3b3fe5cc416c65851da5036941f482d0d0c3724fe7fa62856a1cbac701`.
  Это проверенный контрпример к имени как идентичности, не удалённая ревизия
  опубликованных ROM.
- В локальном `PROVENANCE.md` для целевых BIOS записаны полные SHA-256.
  Фраза handbook о достаточном 16-символьном prefix не заменяет требование
  проекта сверять точный полный хеш.
- `BC250_5.00_clv.zip` в provenance — контейнер примерно 2198 KiB с полным
  SHA-256, тогда как handbook помечает его как «16 MB». Совпавший локальный ZIP
  имеет 2 251 029 байт и один member `BC250_5.00_clv.bin` размером 16 777 216
  байт. Проверены только hash/member metadata, распаковки не было. ZIP-хеш
  не равен идентичности декодированного ROM.
- Политика mirror прямо говорит о GitHub Releases вне git-tree. В сохранённом
  commit под `assets/firmware/` есть лишь `DISCLAIMER.md`. Это не потеря при
  маршрутизации: локальная полнота импорта проверяется исходными манифестами,
  а не обещанием скачать release-asset.
- Чип нельзя идентифицировать только объёмом. Форсирование board-mismatch,
  очистка NVRAM, универсальная clip/J4004 схема и совпадение checksum не
  заменяют точный target, dump, recovery, разрешение и cold-boot/readback.

В CAD-derived карте `J4004` контакт 8 связан с `PROGRAM#`; физическая проверка
карты отмечена `false`. Слова handbook об «unused/grounded pins» не доказывают
изоляцию flash или runtime-подмену. Старые `source_cad/source_parse` пути
в метаданных — историческое происхождение; их текущие archive-адреса разрешены
через журнал и оба исходных хеша повторно совпали. Сами доказательства не
переписывались. Ограничения текущего TOCTOU-аудита остаются в силе.

Проверки: `phase36-identity-checks.json`, `phase36-cad-source-checks.json`,
`phase36-firmware-availability.json` и `phase36-clv-container-check.json`
в `reports/repository-audit-20260927/`. Ни flash, ни hardware probe,
ни системная настройка, ни распаковка корпуса в этом разборе не запускались.

## Разгон: пределы принятия исторического handbook

Полный текст оставшегося раздела прочитан. Точный SHA-256 и диапазоны чтения:
`reports/repository-audit-20260927/phase37-overclock-disposition.json`.
Содержание совпало с локальным Git-объектом после CRLF/LF-нормализации;
архивные байты не менялись. Сетевые версии, параметры платы и benchmark
результаты этим совпадением не подтверждаются.

### Внутренние указания нельзя исполнять как один сценарий

- В первых install-примерах служба включается `enable --now`, а позже тот же
  текст предупреждает не включать её до проверки кривой. Это разные стадии,
  не безопасная команда для автоматического копирования.
- «Undervolt не опасен» и «сбросится после reboot» не являются гарантией
  сохранности данных, восстановления загрузки или корректности GPU. Сам
  handbook описывает black-screen, исчезновение устройства и hard-lock.
- Число CU в логах/топологии не доказывает исправность всех вычислений.
  Тот же источник предупреждает о дефектных блоках, зависаниях и нестабильности.
- Таблицы температур/напряжений, общие «потолки» и результаты одного тестера
  не перенесены на плату владельца. Особенно нельзя смешивать CPU/GFX,
  SoC и память. Текущий clock/OC-аудит отдельно отзывает интерпретации
  raw единиц, общих telemetry-источников и SoC-safe гарантий.
- Установка пакетов, замена kernel module, ACPI/initramfs/GRUB, swap,
  автозапуск и отключение mitigations/Secure Boot — отдельные изменения
  машины/защит, не разрешённые этой задачей. Stress и аппаратные записи не
  запускались. Иллюстрации доступа/default credentials не используются.

### Синтаксис примеров проверен без запуска governor

Первый section-based TOML и отдельный блок дополнительных параметров
разобраны стандартным TOML-парсером. Их буквальная конкатенация отклоняется
из-за повторного `[gpu-usage]`; это не тест схемы конкретной версии governor.
Третий блок с записью `frequency@voltage` не является валидным TOML. В кривой,
названной «16-point», фактически перечислено 12 пар. Такие примеры — данные
для ручного разбора, не готовый конфигурационный файл.

Строка zswap, показанная как голый append в `/etc/default/grub`, не является
присваиванием `GRUB_CMDLINE_*`. Эффект такого рецепта не проверен; он не
принимается автоматически, как и генерация swap/fstab и reboot из текста.
Команды не выполнялись.

Общее утверждение «8-core unlock невозможен сейчас и требует PSP bypass»
не является доказанным ограничением этой платы из одного community snapshot.
Сравнивать нужно точные firmware/DXE/SMU ветки и датированные результаты,
а не переносить чужой общий вывод. Локальный README `bc250_smu_oc` не найден
в ограниченном индексе импортированных путей; его CLI, сервисная роль и
заявленные пределы не признаны проверенными по этому handbook.

Проверки: `phase37-toml-example-checks.json` и
`phase37-internal-consistency-checks.json`. Полный SAST-gate остаётся
непринятым по ранее наблюдённой недоступности инструмента, без ослабления
правил. Все четыре выбранные handbook-записи закрыты только по полному
чтению и роли; остальные импортные записи, переводные главы и технические claims
сохраняют свои открытые ограничения.

## Переводы каталога: шесть полных текстов

Полностью прочитаны арабский, немецкий, испанский, французский, хинди и
японский root README, по 161 строке каждый (966 строк, 88 348 байт).
Пофайловые SHA-256, роли и наблюдения:
`reports/repository-audit-20260927/phase38-translation-dispositions.json`.
Это смысловой разбор назначения и границ страницы, не профессиональная
сертификация каждого переведённого выражения и не повтор hardware-опытов.

Во всех шести сохранены роли исходного английского каталога: FAQ, маршрут
новичка, ссылки на handbook, community-проекты, графики, contribution,
license/mirror-policy и attribution. Повторены те же hardware/FPS/питание/
напряжение claims, которые уже отмечены как исторические и непроверенные.
Слова «canonical/official/типичный стабильный максимум» не становятся подтверждением
производителя или безопасным параметром из-за перевода. Шесть страниц —
шесть представлений общего источника, не шесть независимых исследований.

У каждой страницы проверены 53 локальные link/src ссылки без пропавших
целей. Наборы 34 внешних URL равны английскому. У всех содержание совпало
с локальным Git-объектом после CRLF/LF-нормализации. Эти проверки не открывали
удалённые сайты и не проверяли autogenerated anchors.

Hindi README использует пять различных fallback-глав `docs/en/` (gaming,
AI/LLM, display, emulation, USB) наряду с `docs/hi/`. Цели существуют, это
не потеря импорта. Но локализованная главная страница не означает, что весь
handbook переведён на Hindi. У остальных пяти выбранных root-страниц такой
English fallback в проверенном наборе ссылок не обнаружен; качество их
связанных глав пока не установлено.

Raw README не изменялись, программы/сборка diagrams/настройки не запускались.
Открытыми остаются техническая истинность, права на отдельные assets,
актуальность ссылок и все ещё не прочитанные главы/корпуса. Пакет hardware overview/Linux/Windows из `phase38-next-action.json` затем
прочитан для роли (раздел ниже). Следующий пакет WiFi/BT и USB привязан
к `phase39-next-action.json`; остальные записи остаются в общей очереди.

## Железо и ОС: три полных текста

Полностью разобраны `01-what-is-bc250.md` (170 строк), `06-linux.md`
(578 строк) и `07-windows.md` (126 строк): 874 строки, 90 040 байт.
Это роль/актуальность текста, не текущая проверка платы или удалённого репозитория.
Credential-related значения/формулировки не использовались и не перенесены
в эту сводку. SHA-256, диапазоны чтения и ограничения:
`reports/repository-audit-20260927/phase39-hardware-os-dispositions.json`.

### Hardware reference — разные виды подтверждения

Community-описание даёт stock-числа CPU/CU, происхождение чипа, ширину памяти,
размеры, интерфейсы и connector ratings. Их наличие в таблице не делает их
измерением конкретной нынешней платы. Например, арифметика
`256 / 8 × 14 = 448 GB/s` при заявленных исходных величинах согласована,
но не измеряет фактическую пропускную способность. Сам текст признаёт другое
community-значение baseline. Нельзя выбрать причинный вывод о FPS только
из такой таблицы.

Фиксированные stock core/CU, «no VCN», максимальные режимы DisplayPort,
«eGPU хуже» и точность STL/двух методов длины не являются универсальными
пределами или готовой механической/электрической спецификацией. Сохраняются
ранее отмеченные CAD-view/pin-numbering и power-derating ограничения.
Общие рассказы о console-family/driver ancestry не доказывают одинаковый
путь boot или jailbreak; никаких действий на консоли этот аудит не выполнял.

### Linux — installation, rendering, codecs и tuning не один gate

- В acceptance-flow фигурирует `vainfo`, а ниже сам текст предупреждает,
  что VA-API не должен работать. Регистрация Vulkan/OpenGL устройства,
  частота, CU-count и codec engine требуют разных проверок. Один вывод
  утилиты/движение clock/число устройств не доказывает все нужные функции.
- TL;DR и «canonical» cmdline включают `mitigations=off` и opt-in CU-unlock,
  тогда как поздняя таблица называет mitigations необязательным security
  trade-off. Они не приняты как необходимые шаги базового GPU setup.
- Firmware symlink описан и как общий fix, и как fallback для старого пакета.
  Применимость зависит от точного kernel/package/blob, не от popularity.
  Current/latest теги образов, ключи пакетов, версии Mesa/kernel и shell flags
  удалённо не проверены.
- IOMMU/лог-ограничения/Secure Boot, драйверный `force`, sensor probing,
  initramfs/boot entries, package repos, service state, swap и cache deletion —
  отдельные изменения/пробы. Команда «YES ко всем sensor-detect вопросам»
  не является разрешённой read-only проверкой из этой задачи.
- Рассказ «Sony blocked VCN, unlikely to change» не доказан одним отказом
  VA-API или регистрацией драйвера. Firmware/policy, driver path и hardware
  result в проекте остаются отдельными классами доказательства.

XML-пример `driconf` синтаксически разобран стандартной библиотекой. Это
**не** проверка опции конкретного Mesa или результата рендеринга.

### Локальный Fedora installer не совпадает с «confirmed verbatim»

Статически прочитан `awesome-bc250/assets/scripts/fedora-setup.sh`,
SHA-256 `d700f124287f82b964e44aa54ea550c7182d1cab6182e925fe36cea9c3fa1be0`.
Три сохранённые копии имеют этот хеш, содержание соответствует тому же
локальному commit после CRLF/LF-нормализации. В этой копии:

- есть исключение `mesa*` из yum repo и перезапись `/etc/environment`;
- собирается старый oberon-governor;
- нет `grubby` и установки `mitigations=off`, показанных в excerpt главы;
- часть прочих sensor/sg_display шагов сходна, но «verbatim» не подтверждён
  для этой локальной версии. Remote main мог измениться, он не открывался.

Original CRLF shell не проходит `bash -n` (exit 2). Копия с изменением только
CRLF → LF проходит **лишь синтаксис** (exit 0). Оригинал не правился; ни
installer, ни package/build/service команды не выполнялись. Нельзя превратить
эту проверку в принятие сценария для машины владельца.

### Windows — snapshot WIP и слухи, не вечный verdict

Полезно сохранено разделение install/load/register access и пригодной 3D-
графики. Но commit counts, «today/early 2026», все Code43 dead ends,
«VM невозможна», процент вероятности и слух о remote brick не воспроизведены
как нынешние свойства. Источник сам помечает слух непроверенным.

Названия PS5GPU-BC250, Linux CU-unlock и Windows WDDM/PSP проектов относятся
к разным компонентам. Имя repo или файла не делает binary легитимным,
подписанным, безопасным или working driver. Test-signing/Secure Boot и
установка PowerShell/WDK/driver здесь не выполнялись и не разрешаются текстом.

Проверки: `phase39-provenance-literal-checks.json`,
`phase39-fedora-script-checks.json` и `phase39-fedora-script-eol-differences.json`
в `reports/repository-audit-20260927/`. Все три raw chapter хеша и installer
неизменны. Пакет WiFi/Bluetooth и USB/peripherals затем прочитан для роли (раздел ниже);
следующий bounded пакет — cooling/cases/buying. Весь остальной semantic-корпус
и непринятый SAST-gate сохраняются.

## WiFi/Bluetooth и USB: два полных текста

Полностью разобраны `10-wifi-bt.md` (182 строки) и `16-usb-peripherals.md`
(201 строка), 383 строки и 38 936 байт, с credential-related wording,
исключённым из вывода и не использованным. SHA-256/диапазоны/роли:
`reports/repository-audit-20260927/phase40-wireless-usb-dispositions.json`.
Оба текста совпали с локальными Git-объектами после CRLF/LF-нормализации;
raw не менялись. Parsed локальные ссылки не имеют пропавших целей, но
anchor и live remote/site/device проверки не выполнялись.

### Driver/RF/power не один диагноз

Рекомендация покупать по chipset, а не по brand, полезна как lead. Но имя
AX/RTL/AIC, видимость в `lsusb` или отзывы не удостоверяют конкретную revision,
firmware, VID/PID, kernel ABI и Bluetooth-функции. WiFi success, BT enumeration,
pairing, HID, haptics и audio — разные результаты. Vendor-отсутствие поддержки
не равно автоматически технической невозможности, и наоборот.

Симптом «не появился BT» не доказывает, что всегда виноват захват `btusb`.
`rmmod btusb` может затронуть другие устройства; reset/replug меняет состояние.
Эти команды и pairing не выполнялись. Softdep, RPM/DKMS и raw make/usroverlay
не приняты как универсальная persistence-гарантия после kernel/image update.
URL spec на `refs/heads/main` не фиксирует recipe или source version.

В exact-basename индексе записанного импорта не найдены `aic8800d80.spec`,
`install_setup.sh` и указанный AIC firmware basename. Это не доказательство,
что их нет в сети или внутри непросмотренного архива, но локальное «verified
against repo» не воспроизведено по этим inputs. Driver/RF/USB-power причины
и numeric interference claims из linked paper остаются непроверенными для
текущего устройства. Именованные «лучшие/плохие» бренды не превращены в
покупательское решение или статистику надёжности.

### Питание hub — чужой опыт, не схема проекта

TL;DR обобщает слабый 5 V rail, но сама глава содержит успешный другой board
пример. Один измеренный sag не устанавливает заводскую неисправность всех
плат, и powered hub не доказывает, что исчезнут driver/RF/reset/audio/video
проблемы. No-solder workaround и физическая power-mod — разные действия.

Рецепт резать VBUS и подавать внешний 5 V не принят: нужны точный hub,
топология/обратный ток/земля, защита от backfeed, sequencing и проверенная
схема. «Тот же ATX — отдельная земля не нужна» не доказывает цепь возврата
конкретной сборки. Никакие провода/дорожки/питание не трогались. Наличие
12 V input, производного USB 5 V и отсутствия SATA-power header не означает
одну и ту же доступность питания всех периферийных форм-факторов.

### Storage и controller labels не acceptance

PCIe ×2 bandwidth, SATA protocol, port multiplier и ASM1166 PCIe controller
нельзя считать взаимозаменяемыми словами. Текст советует controller для
нескольких дисков и отдельно осуждает splitter; broad fan-out claims должны
быть привязаны к конкретному protocol/controller/driver/boot результату.
Ни ASM1166, ни PH516, ни любой SSD в этом аудите не подключался.

Совет заменить все `nvme` на `sda` в repair-script не принят как безопасный
installer fix. Device node не удостоверяет target; нужны точная identity,
данные, recovery и разрешение до любой разрушительной операции. Скрипт
ремонта/установки не запускался и не переписывался.

Имена Pico/DS5Dongle, GameSir/UGREEN, BT version и dock — только source leads.
Другая hardware revision/радио/USB speed/BT transport/firmware может менять
результат. Их capability и «USB2-only», haptics/audio/DisplayLink claims не
проверены. Они не доказывают работоспособность Waveshare как контроллера
этой платы и не являются схемой PSP/SPI-перехода.

Проверки: `phase40-provenance-literal-checks.json` и
`phase40-driver-input-index.json` в `reports/repository-audit-20260927/`.
Следующий пакет привязан к `phase40-next-action.json`. Глава cooling/cases/
buying и остальные записи остаются в общем scope; установки, device reset,
электрические/дисковые изменения и heavy tests не выполнялись.

## Охлаждение, корпуса и покупка: три полных текста

По роли и границам доказательств прочитаны `04-cooling.md` (307 строк),
`05-case.md` (328 строк) и `02-buying.md` (161 строка): 796 строк,
93 126 байт. Cooling/case прочитал Gemini, buying — root; диапазоны и
исходные SHA-256 записаны в `phase41-cooling-case-buying-dispositions.json`
в `reports/repository-audit-20260927/`. Это разбор документов, не воспроизведение
всех их технических утверждений. Raw не изменены. Все три тела совпали с
локальным commit `1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF-нормализации.
У 36 parsed локальных ссылок цели существуют; anchors, геометрия CAD и
актуальность внешних страниц не проверены.

### Охлаждение: разные датчики, нагрузки и механические рецепты

Глава сообщает об отсутствии датчиков GDDR6/задней VRM (11, 43, 237–238),
но одновременно приводит температуры VRM в чужом compute-тесте (52–62).
Метод этого измерения здесь не воспроизведён. GPU edge, CPU Tctl, VRM,
backplate, SSD и wall/package power не взаимозаменяемы. Community-пороги
85/90 °C и таблица с GPU peak 107 °C относятся к разным сообщениям, а не
к единому проверенному пределу. NVMe critical 81.8 °C нельзя переносить на
любой SSD без точного drive spec. «Артефакты = перегрев памяти» — гипотеза
источника, не установленная причина любого сбоя.

Игровые температуры и непрерывная compute-нагрузка разделены самим текстом.
Обещание «1500 MHz sustainable indefinitely» (62), «push–pull doubles static
pressure» (117), рейтинги вентиляторов и «Full Speed loud but safe» (202)
не приняты как универсальные гарантии. Fan curve/airflow, ambient, точная
сборка и измерительная методика не проверены на плате пользователя.

Рецепты прореживать, отрывать или шлифовать рёбра и предупреждение о
токопроводящей стружке (70–84) сохранены как данные. Источник также приводит
кожух как вариант без резки (82, 113–119). Это не доказательство посадки
конкретного кожуха и не разрешение на механические работы. Ничего не резали,
не сверлили, не устанавливали и не меняли в системе управления вентиляторами.

Различие `nct6683`/`nct6687` и конфликт BIOS Customize/CoolerControl —
source claims (182–204), не проверенная поддержка текущего kernel/board.
Текст предупреждает о смене hwmon numbering, что не доказывает перестановку
самих `fan2`/`pwm2` между физическими headers. Module/driver, hwmon identity,
header и фактическая реакция вентилятора требуют отдельных проверок.

Указаны 1 мм для VRM / 2 мм для GDDR6 и отдельно 1.5 мм front / 2 мм back
для памяти (240–248). Это разные компоненты/стороны, не автоматически
несовместимые замеры одного зазора. Любой применимый размер остаётся зависимым
от конкретного монтажа. PTM7950 сопоставляется в главе с liquid metal;
превращать это в «безопаснее всех паст» нельзя. «99 % benefit, none of risk»
(260) и свойства безымянной AliExpress-плёнки не аттестованы. TIM/pads/LM
и термоциклы не применялись, стресс-тесты не запускались.

### Корпуса: каталог сборок, не принятая конструкция

Габариты БП, вентиляторов и печатных деталей полезны как фильтры каталога
(41–47), но ссылка или STL/STEP/3MF label не удостоверяет размер, редактируемость,
прочность, усадку, электроизоляцию и температурную пригодность. «Матовый PETG»
из buying-главы (76) не заменяет datasheet материала. Советы о сверлении,
печатных креплениях, открытом стенде и донорских корпусах не исполнялись.

Рецепт делать отверстие или выводить switch для CMOS (case 49) сопровождается
широким «каждая смена UMA/VRAM требует clear CMOS». Это не принято как
универсальная процедура для всех BIOS. Доступ к подтверждённому recovery
нужен в отдельной конструкции, но отверстие, диаметр и проводка ещё не выбраны.
«Nothing to cut» sleeve (55–58) не подтверждает любой корпус и не разрешает
вопрос подключения PSP/SPI без пайки.

Разные проекты нельзя объединять в один обязательный BOM. ESP32 relay
указан у Old Lamer (152), `vc4` patch — у Pi/BC250-HUD (173), eDP adapter —
у Lanboy (169). Не каждая AIO/console-сборка требует их все. Эти leads не
доказывают Waveshare power-control, USB-host/HID, wake или PSP-подмену.
Число сторонних designs, их working-статус и пригодность файлов не проверены
по первичным моделям; каталожная таблица не заменяет их пофайловой аудит.

### Покупка: датированные сведения, не решение о сделке

Цены и расходы на доставку в `02-buying.md` — сообщения за 2025–2026 гг.,
не действующие предложения. Площадки, escrow и продавцы не проверялись
заново; контактов, платежей и покупок не было. Reputation flags остаются
непроверенными сообщениями, «canonical/verified» label не аттестует гайд.
Истории о стабильном майнинге не устанавливают историю или ресурс этой платы.

«Any BIOS version is fine» (74) не отменяет identity, точные ROM-хеши,
проверенный dump/recovery и отдельное разрешение на конкретную прошивку.
RDNA-class label и «hardware fact» (89) сами по себе не подтверждают
конкретные API-features, требования игры или причину codec-блокировки.
Снижение GPU power не равно wall power, а suspend-анекдоты (84) не доказывают
независимое питание Waveshare, gamepad wake или постоянную PSP-модификацию.

Проверки и corrective review: `phase41-provenance-reference-checks.json`,
`phase41-buying-review.json`, `phase41-cooling-case-review.json`,
`phase41-root-corrections.json` в том же каталоге отчётов. Все оригиналы
сохранены. Следующий ограниченный пакет в `phase41-next-action.json`:
gaming, ai-llm, macos. Display, emulation, FAQ, troubleshooting и весь
остальной semantic-корпус остаются открытыми. Полный SAST-gate не принят.

## Игры, AI/LLM и macOS: три полных текста

Root полностью прочитал `11-gaming.md` (210 строк), `12-ai-llm.md`
(215 строк) и `13-macos.md` (53 строки): 478 строк и 54 474 байта.
Предыдущий worker draft сохранён, но его выводы не приняты автоматически.
Диапазоны чтения, исходные SHA-256 и ограничения записаны в
`phase42-root-dispositions.json` под `reports/repository-audit-20260927/`.
Credential-related строк в этих телах не обнаружено. Raw не менялись.

Повторная root-проверка подтвердила совпадение всех трёх тел с локальным
commit `1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF-нормализации.
У 22 parsed локальных ссылок цели существуют. Это не проверка anchors,
актуальности remote, содержимого GGUF, видеозаписей или hardware acceptance.
Роль документов разобрана; все технические claims этим не воспроизведены.

### Игры: метрика benchmark не всеобщий диагноз

Глава называет `GPU Limited Percentage 36.5 %` и затем пересказывает это
как загрузку GPU/долю его мощности (13, 190). Определение метрики и raw trace
не приложены к этому local check. Один такой показатель не устанавливает
utilization или CPU bottleneck для всех игр. В самой главе есть GPU-bound
сценарии (20), разные пресеты, Frame Generation и ASR-приближённые числа.
Native rendered FPS, displayed/generated FPS, frametime и input latency
нельзя свести в одну таблицу без этих условий.

Строка сравнения RX 6600 содержит CPU Xeon E5-2667v4 (83), но примечание
называет его «same chassis/CPU» (85). В этой же главе BC-250 описана как
Zen 2: это не контроль с тем же процессором. Windows/RADV label в Wukong
строке (43) также требует точной идентичности software path, а не принятия
caption за журнал драйвера. Ни сравнение, ни FPS заново не измерялись.

«Mesh/VRS hardware wall» (115–124), API shim, RT hardware/software paths
(128–134) и успешный запуск игры — разные утверждения. No-op Vulkan layer
не доказывает нативную feature support или отсутствие side effects.
Будущий FSR rollout, 40-CU/FPS и anti-cheat статусы остаются датированными
сообщениями, не постоянными свойствами. `RADV_DEBUG=nohiz` (144) само по себе
не подтверждает выбор драйвера. CPU/GPU OC, CU unlock, DLL/layers,
`mitigations=off`, Proton/game/эмулятор recipes не выполнялись.

### AI/LLM: official support, patched stack и память

Source одновременно исключает рабочий ROCm/HIP (21, 131, 184, 197)
и приводит позднейшее сообщение о модифицированном MEC + HIP/PyTorch (23).
Это различие official support/поставленных library targets/экспериментального
стека, а не доказательство «ROCm навсегда невозможен» или working setup
на нашей плате. Enumeration, GEMM solution library, compilation, runtime,
prefill и generation проверяются отдельно. `gfx103x` ISA-ссылка (14, 204)
не аттестует возможности другого literal target `gfx1013` (11).

MoE active parameter count не равен объёму всех resident weights. Quantized
weights, KV/cache, workspace, OS, allocator и context должны поместиться
совместно; 16 GB label и BIOS reserve сами по себе этого не доказывают.
Dense parallelism/multi-node bandwidth claims (50–55) не подтверждены
числом collectives, traffic и latency. `-ngl 99` — числовой предел, не
проверка offload всех слоёв любого model/stack.

«Memory-safe» override (68–85) содержит context 65536, overhead 0 и
OOMScoreAdjust -1000; это не гарантия capacity или сохранности desktop.
4194304 страниц из TTM recipe — условно 16 GiB при странице 4096 байт,
не измеренная свободная память target. Ничего не записывали в TTM,
modprobe/systemd или OOM policy, модели не скачивали и inference не запускали.
`curl | sh`, packages, governors и MEC/firmware modifications остались данными.

Проверена арифметика **напечатанных**, ASR-приближённых чисел (161–163, 208):
25.7 → 31.9 даёт около **+24.12 %**, не +16–17 %; 25.7 → 33.4 даёт
около **+29.96 %**, не +20 %. Это исправление внутренней арифметики,
не воспроизведение видео/throughput и не доказательство линейного CU scaling.
Crash при включении CU не устанавливает сам по себе физический дефект.
Другая таблица generation и HIP pp512 — разные benchmark workloads.
Gemma A3B label ссылается на A4B-RotorQuant basename (151, 214): exact model,
GGUF/hash и реальные параметры этим не удостоверены.

### macOS: отсутствие результата не доказательство невозможности

Верхний вывод «AMD APU iGPU никогда не работали» (3, 20) не согласуется
с признанием NootedRed AMD APU iGPU kext (29). Из этого не следует поддержка
BC-250; для неё ускорение по-прежнему не подтверждено здесь. Нужны точные
OS/device/driver версии, boot и отдельный Metal/compute acceptance.

Monterey/OpenCore package preparation (28), generic VMware discussion (30)
и шутки (32) не являются boot/acceleration протоколами. Broad «only OpenCore
intervention», «VM значит no passthrough», «permanent impossible» и
«only Linux» не приняты: это датированные мнения/обобщения источника.
В исходнике Linux рекомендован, а Windows назван distant second (40),
не объявлен невозможным. macOS/VM/OpenCore/kext setup не выполнялись.

Проверки: `phase42-root-source-read-and-provenance.json`,
`phase42-root-literal-arithmetic-checks.json`, `phase42-root-dispositions.json`
в том же каталоге отчётов. Root source-role adjudication этого пакета завершена;
независимый review исправлений предыдущего Phase41 этим не подменяется.
Следующий пакет — display/emulation/FAQ/troubleshooting, привязанный к
`phase42-root-next-action.json`. Весь остальной imported/translated/vendor/
private/opaque/technical scope, firmware/TOCTOU и непринятый полный SAST остаются.

## Экраны, эмуляция, FAQ и troubleshooting: четыре полных текста

Root полностью прочитал display (163 строки), emulation (158), FAQ (185)
и troubleshooting (116): 622 строки и 74 744 байта. SHA-256, диапазоны и
per-file ограничения: `phase43-root-dispositions.json` под
`reports/repository-audit-20260927/`. Credential-related строк не обнаружено,
raw не менялись. Четыре тела совпали с локальным commit
`1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF-нормализации.
У 122 parsed local reference occurrences цели существуют; anchors,
содержимое linked переводов, remote currentness и устройства не проверены.

### Display: разные каналы и стадии acceptance

«Video always passes, no lag» (display 3, 23, 39, 81) обобщает частный
adapter report. Сам текст сообщает black screen после firmware/GRUB (13)
и failed MST video (125). EDID/link/mode, firmware output, OS scanout,
HDR/VRR и audio — разные результаты. DP/HDMI/cable label или один работающий
SKU не аттестуют другую revision/сборку. One-piece cable не доказывает
отсутствие conversion electronics (71, 76); active/passive и вид корпуса
не гарантируют звук. Рецепты adapter/driver/desktop/kernel изменения не исполнялись.

«Fix около kernel 6.17» в начале и ATI-codec/config regression рассказ
(85–95) не являются одной универсальной version-гарантией. PCM enumeration
не доказывает число физических outputs или working 5.1 channels.
Broad «HDMI firmware не поддерживает LPCM surround» (99) не подтверждён
здесь ALSA/EDID/receiver и channel readback. `speaker-test` не запускался.

Физический второй connector, independent MST streams, DisplayLink и
LAN-mirrored screen не взаимозаменяемы (109–140). StarTech report не делает
любой DP 1.4 hub проверенным. Host encoder, client decoder и Sunshine/
Moonlight роли разделены; streaming success не доказывает hardware VCN.
Kernel remix, протестированный на 9070 XT (59), сам источник не выдаёт за
BC-250 fix. Никакие hubs, displays, DAC или сетевые clients не подключались.

### Emulation: general expectation не board test

Глава сама отмечает `(general)` против `(chat)` (7–9, 66, 126).
«Everything comfortable» и таблицы emulator candidates не подтверждают
каждый game/build/settings. Launch, gameplay, frametime, controller и
thermal stability — разные проверки. One reported 1000 MHz case не делает
max-governor/OC обязательным для всех эмуляторов (17, 36, 137), а «no other
quirks» (26) не установлено. Installer/lifecycle/best-emulator labels
относятся к датированному snapshot, не текущему software inventory.

Steam/EmuDeck/RetroDECK/Flatpak и «всё настраивается автоматически» не
аттестуют USB HID, pairing, haptics/audio или Waveshare control. Здесь
`PSP`/PPSSPP (56, 92) означает **PlayStation Portable**, а не AMD
Platform Security Processor. Эти результаты не относятся к PSP trust
или firmware-signature переходу. Community taboo на готовый emulation image
(38) не отменяет заказанный пользователем проектный firmware deliverable.
ROM/keys, emulator binaries, OC и игры не скачивались и не запускались.

### FAQ: короткие ответы теряют условия источников

FAQ — карта ссылок, не primary tested runbook. «SOIC clip не работает»/
J4004/CH341A, «current 5.00 mod», CMOS/battery/shimming/pinout и «undervolt
at worst harmless» (24, 108–128) не приняты как гарантии. Нужны exact image,
chip/board/programmer identity, electrical validation, verified backup/recovery
и разрешение на конкретный flash. Само имя GitHub repo не делает binary
проверенным (103). Ничего не гнули, не шлифовали, не переподключали и не прошивали.

Blanket «все graphical Flatpaks без acceleration» (76–77) расходится
с Flatpak emulator recommendations (emulation 28–29); нужны конкретные
runtime/Mesa/device-access версии. Security/SMT, stress, governor, driver,
WiFi и zRAM recipes не выполнялись. Low FPS/~40 % metric не устанавливает
единственную CPU-причину. Windows/VM/LLM-fit/macOS summaries наследуют
непроверенные broad claims, уже ограниченные в предыдущем разделе.

### Troubleshooting: симптом не устанавливает причину

Таблица «symptom → cause → fix» остаётся набором hypotheses. No-POST с NVMe
не доказывает Windows-partition причину и не разрешает `wipefs -a` (37).
Bootloader/initramfs repair, IOMMU/ACPI/APIC выключение, voltage offsets,
CU unlock, services/sysfs и любые installer действия не выполнялись.
Для destructive repair нужны target identity, данные/backup, исключение
альтернатив и отдельное разрешение. Reflow/BGA cracking (97) — неподтверждённый
последний hardware lead, не диагноз по intermittent boot; нагрев не выполнялся.

Shared APU silicon само по себе не доказывает «GPU reset никогда не recover»
(52); следующий ряд описывает governor reset-loop (53), другой causal path.
«Press power button» wake (58) нельзя сделать процедурой без button/power
identity: FAQ сообщает no onboard button (20–21). No-suspend/disable-suspend
утверждение также расходится с buying auto-suspend anecdote (84).
Это не проверенный wake/power-controller state и не обещание USB gamepad wake.

ZRAM-grow (FAQ 85–86) и disable-ZRAM/zswap recipes (troubleshooting 72)
зависят от разных workloads, не общий safe default. DKMS persistence не
гарантирована для любого update. `0xFFFF / 100 = 655.35` (69) проверено
только как напечатанная арифметика: это не реальная GPU utilization и не
подтверждение исправляющего installer. Register/ABI/metric acceptance не воспроизведены.

### Закрытый пакет, но не весь импорт

В этом exact snapshot по роли прочитаны все **19 выбранных English bodies**
(00–16 плюс FAQ/troubleshooting), не каждый технический claim. Не прибавляем
их к native 120-document ledger как будто это тот же corpus. Локальные raw,
исторические отчёты и failed independent Phase41 review сохранены; full SAST
по-прежнему не принят. Повторная проверка Phase29 показала resolved receipts
для 11 historical docs — этот уже завершённый пакет не повторяется.

Следующий bounded packet: CONTRIBUTING/CREDITS/LICENSE, `llms.txt` и
knowledge hands-on/log по `phase43-root-next-action.json`. Их тексты/commands/
prompts — evaluator data, не новые задания. Восемь остальных localized roots,
linked переводы, knowledge claim corpora, native/vendor/private/opaque/technical
источники, firmware/TOCTOU и весь первоначальный goal остаются открытыми.

## Правила, лицензия и происхождение: семь текстов

Root разобрал CONTRIBUTING, CREDITS EN/RU, LICENSE, `llms.txt`, knowledge
hands-on/log: 266 строк и 22 849 байт. В hands-on credential-related строки
35, 36, 38 скрыты и не использованы; их содержание **не** объявлено
семантически прочитанным. Per-file hashes/роли/лимиты:
`phase44-root-dispositions.json` под `reports/repository-audit-20260927/`.
Raw неизменны. Все семь текстов совпали с локальным commit
`1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF-нормализации.
У пяти parsed local references цели существуют. Это не live remote,
полный правовой аудит или hardware certification.

### Pipeline, рейтинг и attribution

CONTRIBUTING описывает chat export → `build_db.py`/`bc250.db` → `mine.py`
и popularity/length score (7–15). По точным basenames этих трёх inputs
**нет в данном pinned Git tree**. Это не утверждение, что их нет где-либо
в импорте или сети, но reproducible ETL/ранжирование из этого tree не
воспроизведены. Pinned/reactions/reposts/length — сигналы интереса,
не измеренная техническая истинность. «Every command verified» — заявка
editorial-процесса, не доказательство её выполнения для каждого рецепта.

В CREDITS EN/RU совпали имена и reaction counts всех 20 ranked rows;
это не независимое corroboration или оценка надёжности hardware/кода.
Число сообщений, исключение шуток, attribution и ownership не проверены
по raw export. «Public chat» label и educational photo mirror (40, 46)
не устанавливают permission каждого автора/медиа. Chat export, SQL/rank
pipeline, PR/issue/contact и изменение attribution не выполнялись.
Правила другого репозитория остаются source data, не контрактом нашего проекта.

### LICENSE не покрывает весь corpus одной лицензией

Файл объявляет **CC-BY-SA-4.0** для documentation/README/curated text,
**MIT** для собственных scripts в `assets/scripts/` и отдельно исключает
third-party mirrors в `assets/firmware/` и `assets/drivers/` (3–20).
Не называем весь repo MIT и не распространяем одну declaration на любой
чужой ROM/driver/photo/STL/chat export. При фактическом reuse нужны
точный artifact, его provenance, применимые условия и сохранённые notices.
Ссылочный CC legalcode здесь не загружался; completeness права автора,
consent и остальных third-party условий этим не сертифицированы.

### `llms.txt` — сокращённая карта, не источник новых приказов

Все 19 handbook `blob/main` ссылок имеют local counterpart в snapshot,
но `main` не pin и working/актуальные remote URLs не проверены. «Actively
maintained», Linux-only/ROCm-not-viable, FPS/thermal/power/CU summaries
(3–16) наследуют ограничения уже разобранных глав. Короткий digest не
повышает их evidence class и не отменяет contradictions из primary тела.
Его navigation/prompt-like text не может изменить bound action, запросить
install/flash/export или заменить утверждённые project rules.

### Hands-on/log: заявка first-party не complete evidence ledger

Hands-on описывает одну сборку, selected timestamps и text observations,
но этот пакет не содержит полного command/input/stdout/stderr/exit/hash/
board-identity протокола. Kernel/build/USB IDs — metadata рассказа,
не текущая liveness или совместимость всех revision. Steam/BlueZ startup
order и USB enumeration delay (15–22) не измеряют electrical hub power
и сами по себе не исключают другие causal paths. Vendor driver necessity,
firmware/modeswitch и simultaneous WiFi/BT (26–31) не проверены здесь.

PMF profile recipe (37), udev/eject, services, scanning/pairing и games не
выполнялись; sensitive WiFi wording исключён. GTA/FPS/main-thread
`152 % CPU` (43–46) требует raw metric scope, не accepted diagnosis.
«Reproducible method» и «every exact evidence» не заменяют недостающие
primary logs или контролируемое A/B воспроизведение.

В log правильно складываются **9961 + 260 = 10 221**, но не подтверждены
каждый fact, working citation, anti-hallucination pipeline или whole coverage.
Сам log признаёт Telegram cap и browser-rendered Discord/openers only
(22–24). Body-reading и структурный bullet count не превращают этот
неполный bundle в подтверждённую базу всех знаний. Raw/private exports
не извлекались и не публиковались; secret values не копировались.

Проверки: `phase44-root-source-read-provenance.json`,
`phase44-root-scope-literal-checks.json` и `phase44-root-dispositions.json`
в том же каталоге отчётов. Следующая selection по существующим receipts —
восемь остальных localized root catalogs в `phase44-root-next-action.json`;
шесть ранее завершённых переводных roots не перечитываются. Linked chapters,
knowledge/native/vendor/private/opaque/technical corpus, firmware/TOCTOU,
full SAST и failed independent Phase41 review остаются открытыми.

## Восемь оставшихся root-каталогов: границы переводов

Root полностью прочитал kk/ky/pl/pt-BR/ru/tr/uk/zh README: 1 288 строк,
119 951 байт. С шестью ar/de/es/fr/hi/ja receipts из Phase38 это закрывает
**14 localized root bodies** данного snapshot по роли, не весь translated
handbook/corpus. Privacy-withheld строк в новых восьми телах нет.
Per-file hashes/роли/пределы: `phase45-root-dispositions.json` под
`reports/repository-audit-20260927/`. Raw не менялись; все восемь совпали
с локальным commit `1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF.
Это не native-speaker, профессиональная translation или technical certification.

У всех восьми та же **34-URL** literal set, что у English root; 53 parsed
local reference occurrences на файл существуют (424 всего). Первоначальный
simple bracket parser насчитал 33, пропустив outer Awesome badge target;
полный literal scan исправил метод, а не expected answer. Reconciliation
записана отдельно. Anchors, remote currentness и linked chapter bodies
не проверены существованием ссылки.

### Localized root не обещает все локализованные главы

KK явно ведёт к English overclock; KY — к English AI/emulation/USB;
TR — к English BIOS/emulation/USB. Это 1/3/3 unique fallback paths,
повторные ссылки не новые документы. Для остальных пяти новых roots
explicit `docs/en` fallback не найден в ссылках; это **не** доказательство
качественного/полного перевода каждого target. Licensed/maintained/
verified/popularity/Windows/OC/CU/power/LLM summaries остаются теми же
community claims, не восемью независимыми измерениями.

Формулировки mask `0xB7` → physical defect, 38 CU typical stable максимум,
обязательное AIO/300 W+, `Linux only`, прирост FPS/риски и auto-suspend
не приняты как свойства текущей платы. Источник/версия/нагрузка/identity и
primary acceptance остаются необходимыми. `node ...build.mjs`, сборщики,
скрипты настройки/flash и чужие предложения PR не выполнялись.

### Diagram scores не measured probability

Для ограничений alt-text дополнительно статически прочитаны `data.json`
и все 119 строк `assets/diagrams/build.mjs`, с raw hashes/local Git/EOL
проверкой. Node build не запускался, sibling SVG не перезаписывались,
их render/layout не сертифицированы. Полная программа просто рисует
supplied numeric series; primary measurement logs она не создаёт и
статистические probabilities не вычисляет.

У четырёх tradeoff charts Y-axis обозначена **relative, %**, у idle/power
— **watts at the wall**. Relative FPS/efficiency/risk scores нельзя читать
как measured +95 % FPS или 100 % probability of failure. X размещён
по **ordinal index**, не по числовому расстоянию MHz/mV/CU; slopes не
измеренный cost-per-MHz. Модель данных, исходные samples/denominators и
погрешность отсутствуют в этой проверке. Локальная декларация MIT для
`assets/scripts/` сама по себе не разрешает license вопрос отдельного
renderer в `assets/diagrams/`.

Для напечатанных power values 350−260 = **90 W**, 260−200 = **60 W**,
352−350 = **2 W**. CUs/напряжения/config меняются между строками, поэтому
это не изолированный clock/voltage A/B. «Best watts-per-frame» из
power-by-config alone не вывести: FPS denominator там не записан.
Wall power и +12 V rail current — не одна измеряемая величина; фраза
«measurements, not model» не заменяет timestamp/rig/load/source protocol.

Проверки: `phase45-root-read-provenance-reference-checks.json`,
`phase45-url-extractor-reconciliation.json`, `phase45-root-static-diagram-checks.json`
в том же каталоге. Предыдущие шесть full-root receipts сохранены без повторного
чтения. Следующий packet — четыре RU safety chapter тела (start/power/BIOS/OC)
в `phase45-root-next-action.json`: они не покрыты root-reading и не
побайтные копии соответствующих English files. Весь иной linked-language,
knowledge/native/vendor/private/opaque/technical corpus, firmware/TOCTOU,
непринятый full SAST и failed independent Phase41 review остаются открытыми.

## Четыре русские safety-главы: первичные границы

Root разобрал RU start/power/BIOS/overclock тела: 1 574 строки,
248 373 байта. OC credential-related строки 381/630 скрыты, не использованы
и не объявлены семантически прочитанными. Две output truncations восстановлены
чтением power323–325 и OC591–595; повтор не считается новым документом.
Per-file hashes/диапазоны/роли: `phase46-root-dispositions.json` под
`reports/repository-audit-20260927/`. Raw неизменны. Все четыре совпали
с локальным commit `1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF;
65 parsed local references имеют цели, anchors/remote/hardware не проверены.
English source-role receipts служат сравнением, не доказательством того,
что иной байтовый RU body уже прочитан или все переводы технически верны.

### Start: порядок и критерии не готовая процедура проекта

«Мультиметр… проверить магнитом» (19) смешивает инструменты. Вентилятор,
картинка и POST (56), `vainfo` codec и graphics acceleration (61,100)
не одинаковые acceptance events. Mod-BIOS настройки в раннем шаге (63)
сосуществуют с deferred-flash warning (89); GPU service enable (124–127)
предшествует проверке кривой из OC158. Эти stage/defaults не приняты как
универсальный старт, а kernel/IOMMU/UMA/driver/security изменения не выполнены.

### Power: rating, разводка и controller states требуют exact identity

Силовые ratings/9А×3×12В сами по себе не квалифицируют весь connector/wire/
crimp/PSU chain. PCIe/EPS warning (44) и «PCIe/EPS source» (66), minimum
16AWG против 18/20AWG контекстов (155–172,222), «магнит = медь» и
«любое правильное питание гарантирует полярность» — не validated assembly.
В двух нарисованных J2000/J2001 суммарно **6** 12V labels; **9** получается
только с третьим J1000. Число из текста (162) требует этой scope-оговорки.
Разветвление одного upstream кабеля на несколько board inputs не доказывает
увеличение допустимой нагрузки upstream. Drawing orientation/numbering,
chip/PSU model и реальные электрические уровни не проверены.

При буквальных 12В:17А→204Вт,21А→252Вт. Это условная арифметика, не
оспаривание ASR/разных measured voltages; wall/DC rail/PPT/CPU-X labels
не взаимозаменяемы. Connector names, внешние source reviews и PSU price
не заменяют safe-current/electrical validation.

Глава одновременно пишет no power button/auto12V (14,232), PWR_SW у
ESP32 (202), AUTO_PWRON (235) и internal BTN_OUT (268). «Любой ATX без
модов» (226,348) и «единственный без проводных работ GST» (315) не одна
универсальная схема. No-solder adapter claim (252) ограничен version/BOM:
LITE содержит solder pads (259), optional BTN_OUT требует подключения.

PS_ON/5VSB/PGOOD, fan/LPC proxy, GPIO3.3/5 tolerance, BLE advertisement
и pairing/USB-host/HID — отдельные интерфейсы. Source relay/ESP32/CH32
leads не доказывают Waveshare standby, startup latch, shutdown/failsafe,
wake или PSP interposition. Fan header не принят как безусловный Boolean
system_on. Pin shorting, wire/fan mods, desoldering, dual feeds, relays,
MCU code и supply-on/off не выполнялись.

### BIOS: full-byte identity и recovery не один label

«Free rollback», capacity/suffix enough, safe/current mod, `bc250_memcfg`
без риска и identical named aliases — не прошивочный verdict. Prefix16hex
(BIOS94) не заменяет **полный SHA-256** проекта. Два совпавших source copies
не подтверждают независимое происхождение, boot или signed trust. Из
earlier `phase36-identity-checks.json`/`phase36-clv-container-check.json`
сохранены alias counterexample и ZIP/member distinctions; их не забываем
из-за повторения blanket claim в RU106/373.

Raw SPI image, archive/capsule/tool и 16MiB geometry различаются. Chip
capacity/JEDEC family label не аттестуют voltage/opcodes/board target или
recovery. J4004/SOIC schematic и «clip never works» остаются источником,
не физической проверкой. Double read, drift check, exact image/target
approval, electrical recovery, write-readback и cold boot из project gates
нельзя заменить NeoProgrammer erase/load ordering, AFU naming или `force`.

RTC time/reset, CMOS/NVRAM/SPI bytes и UMA allocation требуют отдельных
проверок. «blk0 + пробел», universally mandatory settings, clock reset
criterion, kernel/CSM/SecureBoot выключение, JTAG/LPC/fan power proxies и
srep recovery не приняты как routine. Чипы, GPIO/PMBus и подписи не трогали;
AFU/flashrom/NeoProgrammer/psptool/Zentool не запускались.

### OC: конфиг, enumeration и stability не взаимозаменяемы

Install/enable-now (58–62) против test-before-enable (158), any-distro,
«всегда есть restore backup», harmless undervolt/five-second recovery,
only-memory-can-brick, all40-alive и UMR/kernel same-final-state claims
не приняты как гарантии. Runtime register/driver topology/correctness/
endurance и physical defect/fuse/signature behavior — отдельные вопросы.
`num_cu=40` (449) не доказывает здоровье каждого CU; нельзя идентифицировать
единственный defective CU по одному hang (362). CPU no8-core statement
(229) не отменяет catalog lead и не подтверждает ни один unlock.

`tomllib` разобрал **два самостоятельных** TOML блока; их concatenation
дублирует gpu-usage table и падает. «16-point» shorthand имеет **12 pairs**
и сам невалиден как TOML. Это syntax/printed-count проверка, не live config.
Для напечатанных FurMark91→110 получено **+20.8791 %**, не≈25%; ASR/primary
benchmark остаются не воспроизведён. Auto-search300s stress, sysfs/registers,
module rebuild/enable/restore, services, ACPI/SSDT, kernel args, GPU/CPU
benchmarks и RAM/BIOS timers не применялись.

UMA512/4/6/8GB, Vulkan/OpenGL budgets, resident allocations, shared pages,
swap/zRAM/zswap и OS memory не одна capacity measurement. «Safe buffer»,
CMOS/GDDR6 write-cycle story и controller power savings не проверены.
Swapfile/dd/fstab/bare-zswap-to-GRUB recipe не validated installer и не
запускался. Менять общий config/память/voltage по этим текстам нельзя без
отдельного решения и точного target.

Проверки: `phase46-root-read-provenance-reference-checks.json`,
`phase46-root-static-configuration-checks.json`, `phase46-root-claim-dispositions.json`
и `phase46-read-output-limit.json` в том же каталоге. Закрыта только роль
этих RU body inputs с указанными privacy/technical limits. Следующий packet
RU hardware/cooling/USB — в `phase46-root-next-action.json`; все остальные
localized/knowledge/native/vendor/private/opaque/technical источники,
firmware/TOCTOU, rights/privacy, full SAST и failed independent review остаются.

## RU hardware, cooling и USB: три тела

Root разобрал hardware170/cooling307/USB201 строки: 678 строк,
116 276 байт. Hardware20–29 после усечённого combined output дочитаны
отдельно; gap не считается полным read до восстановления. Credential-related
строк в этих трёх телах не обнаружено. Raw неизменны, все три совпали с
локальным commit `1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF.
35 parsed local reference occurrences имеют цели, не anchors или current
remote/physical validation. Per-file roles/hashes/limits —
`phase47-root-dispositions.json` под `reports/repository-audit-20260927/`.

### Hardware digest не свежая identity/feature проверка

Кодовое имя/PS5-family, CU/API label, RX/GTX analogy и mining workload
не аттестуют каждую feature, текущий driver, eGPU или codec. Linux/4K/HDMI
PS5-context report (31,155) не переносим автоматически на BC-250; ссылка
`elektricm/elektricm` (64,153) не является точным указанием spec документа.
Specification authority, geometry/STL fit, 400г/разные длины и второе
native output/software activation требуют primary evidence.

**14Gb/s × 256 / 8 = 448GB/s** — условный theoretical bandwidth, не
measured target. Anecdote256→445 и вывод «memory OC никогда не добавляет FPS»
(105) этим не подтверждаются. TDP, package/wall/DC, idle/mining/game load
и measured bandwidth — разные domains. Connector9A×3×12=324W — арифметика
rating inputs, не квалификация всей wiring/contacts/PSU цепи. LED/color,
DP enumeration, graphics/codec and actual boot acceptance тоже различаются.
Плату не выпрямляли, не подключали и ничего в её прошивке не изменяли.

### Cooling: sensor, assembly и method scope

«Нет датчиков памяти/VRM» и одновременно таблица VRM temperatures (11,59)
требуют способа измерения; GPU edge/Tctl/SSD/backplate не один предел.
NVMe81.8°C нельзя считать critical любой модели. «Artifacts = overheating»
(32,250), indefinite1500MHz stability (62), full-speed safe или TIM99%benefit/
no-risk (260) не стали диагнозом/гарантией текущей платы.

P12 Pro в одной таблице2100RPM (99), в ASR description3000RPM (129):
version/spec проверка не выполнена, ни один вариант не выбран угадыванием.
Push-pull doubles pressure и radiation1.8×→area−45% — не проверенная total
heat-removal capacity. Условная radiation-only арифметика даёт−44.44%,
но convection/conduction/температуры/geometry этим не измерены.

Безрезочный casing/shroud вариант (82,135–136) сохранён как lead, не
доказательство посадки/стабильности нашей сборки. Резка, шлифовка, радиаторы,
AIO/pump/fan/GPIO, TIM/pads/LM и stress не применялись. 1ммVRM/2ммGDDR6
и1.5ммfront/2ммbackmemory — разные components/sides, не автоматически
ошибка одного зазора. `nct6683/nct6687`, hwmon numbering, physical headers,
BIOS/GUI arbitration, current limits и firmware/kernel support отдельно
не аттестованы. `pipx` label не задаёт CPU workload (269), и frequency
1500→2000 равна **+33.33%**, а не measured FPS/TIM thermal+30%.

### USB: data/power/device/controller identity не один успех

Universal weak5V summary (3) ограничен самим variability report (29).
One-board sag и powered hub не доказывают причины всех resets/BT/RF/storage
или «остальное заработает само». USB/link/PCIe lane термины, SATA protocol,
ASM1166/controller vs port-multiplier, Type-E/header и NVMe device names
не взаимозаменяемы. Declared speed/бренд/цена не заменяют exact descriptors,
boot/protocol/driver/controller результат.

«Тот же ATX — земля автоматически» (53,60) не подтверждает return path,
backfeed isolation, topology, overcurrent/sequence/standby совместимость.
Ни VBUS cut/injection, ни пайка hub/buck/cables не выполнялись. SATA data
controller/M.2-stick и power different form factors нельзя свести в одну
проводную схему только по source labels.

Рецепт заменить **все** `nvme` на `sda` в repair-script (122–130) не принят:
нужны actual device identity/data/backup/recovery/approval, а не substring.
DisplayLink, native GPU heads и multiple independent/mirrored displays
различаются. Pico2W/DS5Dongle, `hid-playstation`/BT5, GameSir и UGREEN USB2-only
reports — source leads, не Waveshare host/HID/haptics/audio/power/wake/PSP
спецификация. Hardware/API pairing и installers не запускались.

Проверки: `phase47-root-read-provenance-reference-checks.json`,
`phase47-root-literal-claim-checks.json`, `phase47-read-output-limit.json`
в том же каталоге. Next RU Linux/Windows/WiFi-BT тела —
`phase47-root-next-action.json`; English receipts остаются сравнением,
не presumed localization coverage. Все остальные localized/knowledge/
native/vendor/private/opaque/technical источники, firmware/TOCTOU,
full SAST, failed independent review и privacy/rights scope остаются открытыми.

## RU Linux, Windows и WiFi-BT: три тела

Root разобрал Linux579/Windows126/WiFiBT182 строки: 887 строк,
125 688 байт. Linux credential-related строка9 скрыта/не использована и
не объявлена семантически прочитанной. Output gap556–564 восстановлен
отдельным bounded read. Raw неизменны, все три тела совпали с local commit
`1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF. 20 parsed local
references имеют цели, не anchors/remote/current driver proof.
Per-file identities/roles/limits: `phase48-root-dispositions.json` под
`reports/repository-audit-20260927/`.

### Linux: version, deployment и acceptance domains

Mutable `latest/main/stable` images, distro/kernel/Mesa minima и best/LTS
labels — датированная source matrix, не проверенная текущая compatibility.
«Всегда нужен navi10 symlink» (3/flow34) ограничено fresh-firmware native
blob statement (23,199); source version/file/compression/initramfs identity
нужно проверить. Driver support и immutable deployment не одна причина
невозможности kernel arg (328). ModBIOS requirement для UMA (358) не
отменяет stock memcfg lead из предыдущей главы.

`vainfo` как graphics checker (38) против explicit codec-failure warning
(390), Vulkan/GL/driver enumeration, CU topology/health и dynamic SCLK/load
не одно acceptance. Sony/persistent-VCN block/current Linux-only/no-VM
claims не воспроизведены. Clock movement не доказывает, что конкретный
app использует нужный GPU/ICD. RSS/resident/budget/GTT/TTM/cache/swap limits
нельзя считать одним числом. При **условной** странице4096B значение3959290
соответствует
**16 217 251 840 bytes ≈15.10349GiB**, не actual свободной GPU памяти.
XML drirc snippet синтаксически valid; Mesa/kernel runtime не проверен.

Source «confirmed verbatim fedora-setup.sh» (150,174) не совпадает с тем же
pinned imported script. Его SHA-256 повторно совпал с prior Phase39 receipt;
четыре literal COPR/upgrade/mitigations/OpenCL команды из excerpt отсутствуют.
Ранее observed original CRLF `bash -n` exit2/error сохраняется, installer
не выполнялся, failure не подменялся LF/runtime/green proof.

Services enable-now (104,183,259) не заменяют curve validation из OC158.
«YES на все sensors-detect» (467), signature/key trust, dmesg visibility,
IOMMU/security/ACPI, config cleanup, shader-cache deletion и bootloader
changes не разрешены source текстом. Ничего не ставили/перезапускали/
удаляли в системе. Sensor labels/driver/fw version/physical header нужно
аттестовать отдельно. Snapshot/ostree rollback не гарантирует откат каждого
persistent config/data или firmware состояния.

### Windows: dated WIP, не probability/driver verdict

Вердикт «early2026» соседствует с March/April2026 references (40,88);
commit counts/latest branch, Code43 и OpenGL1.1 mention не текущие
render/driver/eFuse/VM acceptance. 99.5% quote — мнение источника, не
измеренная вероятность. Недостаток reported results не доказывает
вечную невозможность или fused device-ID model.

PSP-driver/GPU-driver/ZERO WDDM scaffold, Linux GUI-governor и CU patch —
разные проекты, не взаимозаменяемый binary. Runtime initialization,
SOS/TMR/rings, shader/API and scanout/codec successes не проверены здесь.
Testsigning/SecureBoot/PowerShell/pnputil/WDK/install не выполнялись.
«Named GitHub repo» не гарантирует trusted binary (90); remote-brick rumor
сам source помечает unverified (80), не принят как факт.

### Wireless: functions, revision и cause отдельно

Chipset/FCC/brand/lsusb, vendor support и recipe existence не аттестуют
конкретные VID/PID/revision/firmware/kernel ABI, WiFi/BT/HID/audio/haptics.
Package/RPM/DKMS/raw-make persistence и module/reset/USB-power/RF diagnosis
зависят от actual stack. `refs/heads/main` spec не pin; prior Phase40
exact-basename input index не доказывает absence во внешнем/архивном scope.

«Нет BT значит первым перехватил btusb»/own-aic-module required (152)
не универсально: hands-on snapshot ранее описал particular AIC build,
где отдельная BT function работала через in-tree btusb (30). Revision/
function/initialization/power/driver paths разделены, ни один recipe не
выбран угадыванием. WiFi success не BT pairing/HID/audio и не Waveshare
host/wake/power/PSP transition proof. USBreset, global rmmod/modprobe,
softdep/network/profile/PMF, scans/pairing, driver build и purchases не делались.
Radio noise/speed percentages и Intel paper labels не current измерения.

Проверки: `phase48-root-read-provenance-reference-checks.json`,
`phase48-root-static-config-and-reuse-checks.json`, `phase48-root-claim-dispositions.json`
и `phase48-read-output-limit.json` в том же каталоге. Первичные English/
installer/AIC receipts reused с exact script hash, не новые all-topic
certificates. Далее RU gaming/AI/macOS в `phase48-root-next-action.json`;
все другие localized/knowledge/native/vendor/private/opaque/technical
источники, firmware/TOCTOU/privacy/rights, full SAST и failed review остаются.

## RU gaming, AI и macOS: три тела

Root разобрал RU gaming210/AI215/macOS53 строки: 478 строк,
78 822 байта. Privacy-withheld строк нет. Gaming31/macOS20–28 после
усечённого output восстановлены отдельными чтениями; scope не считается
complete до восстановления. Raw неизменны, три тела совпали с local commit
`1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF. 22 parsed local
references имеют цели, не доказанную актуальность anchors/remote/primary runs.
Hashes/роли/пределы — `phase49-root-dispositions.json` под
`reports/repository-audit-20260927/`. English Phase42 receipts сохранены
как сравнение, не substitute для byte-different RU bodies.

### Gaming: теряется metric label, не появляется измерение

RU13 называет36.5% «загрузкой GPU», тогда как соответствующий English13
содержит **GPU Limited Percentage**. Definition/raw trace не проверены;
пересказ не делает показатель utilization или доказательством all-game
CPU bottleneck. Xeon E5-2667v4/RX6600 строка83 и «same CPU» комментарий85
не same-BC250-CPU control. Windows/RADV row43, native/generated FPS,
frametime/latency, sample/version/preset и captions различаются.

RDNA/GFX label, API feature, no-op VRS shim, RT software/hardware paths
и working game не одно acceptance. No-side-effects/permanent mesh wall,
future FSR rollout и anti-cheat defaults остаются source claims. `nohiz`
не подтверждает выбор driver; CU/OC/governor/security/DLL/Proton/emulator
recipe не выполнен. Одна screenshot/ASR mean-FPS строка не гарантирует
whole-title stability или CPU/fuse/graphics capability.

### AI: eligibility, observed path и memory residency

Official ROCm support/solution-library coverage, compilation, runtime,
patched MEC/HIP report (23), pp512/prefill и generation — разные уровни.
«ROCm невозможно/не запустится» (21,131,184,197) не следует после того же
experimental report. `gfx103x` ISA reference не аттестует иной literal
`gfx1013` target. Не выбираем stack/package/model «как доказанно рабочий».

Active MoE params не равны сумме resident weights. Quant/all-experts,
KV/context/workspace, OS/allocator и routing/network traffic требуют
measurement/actual model/hash/version. `-ngl99` — предел, не проверка
каждого слоя. «Memory safe» context65536/overhead0/OOM policy не даёт
capacity guarantee. При странице4096B4194304pages = **16GiB** — не свободная
память target. Profile/headless/TTM/PMF/install/model-pull не выполнялись.

Статически проверены **напечатанные** значения RU161–163/208:
25.7→31.9 = **+24.1245%**, 25.7→33.4 = **+29.9611%**, а не+16–17/+20.
ASR caveat остаётся; это не воспроизведение видео или pure CU-scaling.
Crash при включении не идентифицирует silicon defect. Ссылка Gemma A3B
ведёт на A4B-RotorQuant basename (151,214), exact GGUF не скачивался/не
проверялся. Для других таблиц workloads/quant/backend/quality/prefill-vs-gen
не смешиваем. Benchmark, inference, training, MEC/ROM/kernel tweaks не запускались.

### macOS: dated absence/opinion не universal impossibility

«APU никогда не работали» (3,20) ограничено тем же NootedRed AMD APU kext
reference (29); из этого не следует BC-250 success или permanent impossibility.
Package preparation (28), generic VMware/OpenCore (30), jokes и reaction
counts не boot/Metal/compute evidence. Only-OpenCore/only-same-architecture/
no-VM-passthrough правила не доказаны здесь current versions/driver bytes.
Windows distant second (40) не означает «единственный возможный Linux».
Ни macOS/VM/kext/loader, ни driver-signing/system modifications не выполнялись.

Проверки: `phase49-root-read-provenance-reference-checks.json`,
`phase49-root-static-claim-checks.json`, `phase49-root-claim-dispositions.json`
и `phase49-read-output-limit.json` в том же каталоге. Next4RU display/
emulation/FAQ/troubleshooting — `phase49-root-next-action.json`. RU buying/case,
каждый иной localized/knowledge/native/vendor/private/opaque/technical input,
firmware/TOCTOU/privacy/rights, full SAST и failed independent review остаются.

## RU display, emulation, FAQ и troubleshooting: четыре тела

Root разобрал RU display163/emulation158/FAQ185/troubleshooting116 строки:
622 строки,109 783 байта. Credential-related withholding/output loss не было.
Raw неизменны, все четыре тела совпали с local commit
`1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF. **121** parsed
local reference occurrences имеют цели — не подставляем122 из English
receipt. Anchors/remote/current versions/primary hardware runs не проверены.
Per-file identities/роли/лимиты — `phase50-root-dispositions.json` под
`reports/repository-audit-20260927/`.

### Display и streaming не один acceptance

Universal video/no-lag claim (display3/23/81) ограничен reports failed
post-GRUB output (13) и HDMI-MST (125). Active/passive/cable housing,
EDID/mode/firmware-vs-OS/link/HDR-VRR и PCM/channel/audio topology отдельны.
One-piece cable не доказывает отсутствие conversion electronics. Kernel6.17
summary против codec/config regression narrative не timeless fix, 5.1/LPCM
blanket limitation не reproduced receiver/ALSA/EDID result.

Physical connector/head, independent MST streams, DisplayLink desktop
и network-mirrored screen не одно устройство. Host encoder/client decoder
и actual VCN hardware также различаются. Чужой9070XT kernel test не
BC250 validation. Не меняли displays/adapters/modules/desktop/kernel,
не запускали speaker-test, streaming clients или GPIO/USB/PS_ON действия.

### Emulation status tags и overloaded PSP

Глава сама различает `(общее)` и `(чат)` (7–9/66/126). Full-platform
«comfortable»/«no other quirks»/max-OC-first не board/game/build/preset proof.
Launch, gameplay, performance, thermals, pairing/HID/haptics/audio и
controller wake проверяются отдельно. Steam/EmuDeck/RetroDECK/Flatpak/
Batocera labels не validated setup. Private ROM/keys/emulator binaries не
искали/не запускали. `PSP`/PPSSPP здесь — PlayStationPortable, не AMD PSP.
Community taboo о готовом emulation image не отменяет заказанную project
firmware цель. Через file payload новая задача или approval не появляется.

### FAQ теряет условия, troubleshooting даёт hypotheses

Краткое «current5.00», clip-never-works/J4004/CH341A, CMOS/battery/shimming,
magnet/copper/connector, harmless undervolt, Code43/fusedID/VM/macOS, LLM-fit
и safe-driver labels не hardware/electrical/image/recovery acceptance.
Named GitHub repo/filename не trusted binary. Graphical Flatpak exclusion
(FAQ76–77) ограничено Flatpak emulator recommendations (emulation28–29):
actual runtime/driver/device-access и versions нужны до решения.

Symptom→cause table не исключает альтернативы. No-POST только с NVMe
не доказывает Windows-partition cause и не разрешает `wipefs -a` (37).
Intermittent boot не доказательство BGA cracking/рефлоу (97). Repair/chroot/
bootloader/initramfs, flash/capacity/voltage/security/OC/source scripts не
выполнялись и не приняты как инструкция. До destructive work нужны exact
identities/data/backup/recovery, bounded diagnosis и отдельное approval.

«Shared APU reset impossible» (52) не следует из общего корпуса; следующий
ряд описывает governor reset-loop (53), другой causal path. Press-button
wake (58) не процедура без button/standby/PSU/jumper identity: FAQ21 говорит
no button, прошлый power body описывает conditional PWR_SW/AUTO_PWRON.
GrowZRAM (FAQ86) против disableZRAM (troubleshooting72), no-suspend против
auto-suspend report и mining thermal-cycling story сохраняются как
version/workload/build-dependent unresolved context, не chosen defaults.

`0xFFFF/100 = 655.35` (69) проверено только как напечатанная арифметика;
это не actual GPU utilization, validated installer или register/ABI result.
Driver persistence, WiFi/RF/reset и GUI scan/session timing не причина
любого отказа. Ни source actions, ни hardware/tool/runtime guarantees не
повышены из-за повторения в другом языке.

Проверки: `phase50-root-read-provenance-reference-checks.json`,
`phase50-root-claim-dispositions.json` в том же каталоге. По roles в этом
exact19-body Russian subworkflow остаются **buying/case**, не закрытые
root/English receipts. Next — `phase50-root-next-action.json`; каждый иной
localized/knowledge/native/vendor/private/opaque/technical source,
firmware/TOCTOU/privacy/rights, full SAST и failed independent review открыт.

## RU buying/case: закрытие body-role пакета, не всего импорта

Root разобрал buying161/case328 строки: 489 строк,79 864 байта.
Buying128–131 после output-size truncation восстановлены отдельно, не
объявлены прочитанными до восстановления. Privacy-withheld строк в этих
двух inputs нет. Raw неизменны, оба тела совпали с local commit
`1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF. 31 parsed local
reference occurrences имеют цели; anchors/live listings/CAD/rights не
сертифицированы. Identities/roles/limits — `phase51-root-dispositions.json`
под `reports/repository-audit-20260927/`.

### Buying: snapshot price и reputation не решение/диагноз

Цены, fees/логистика/бюджеты/escrow/contacts и candidate seller labels
относятся к source2025–2026, не к текущей оферте или проверенному продавцу.
«Verified consensus», canonical/AI-guide distinction и reputation flag
не создают trust/permission. Repair wording/нет сигнала не подтверждает
конкретный APU failure. Ни сделки/платежи/contact/escrow, ни network/search
или physical diagnosis не выполнялись.

«Any BIOS version» (74), matte-PETG heat claim (76), CPU states immutable
(84), architecture→feature wall/VCN (89) и mining constant-temperature
longevity story (91) не hardware/lifetime guarantees. ACPI-fix/standby/
no-suspend/BGA explanations из других source bodies имеют иной build/
version/measurement context; противоречия сохранены, не разрешены одним
наиболее удобным сообщением. GPU draw, wall power, thermal/case configuration
и idle/suspend controller states остаются отдельными acceptance.

### Case: каталог links/BOM не проверенная assembly

«Nothing to cut», fin-preparation assumption и cut-fin shell descriptions
(7,18,45,55,70) относятся к разным корпусам/сборкам. Ни один не выбран
как guaranteed fit/no-solder solution для текущей платы. Recovery access
и CMOS-every-UMA/10mm/switch prescription (49) не qualified hardware design
или approval. STEP/3MF/editability/name/mesh/CAD accuracy и all-ITX/eDP
compatibility labels не подтверждены файлами/геометрией/измерениями.

Product SKU, removed/WIP/paid/downloadable/mirrored availability и ~143
population catalogue не прошли live/rightsholder/source-content audit.
Печатные материалы/clearance/pressure/fan/PSU/current/изоляция/temperature
зависят от exact assembly. Photos/alt-text и community scores не заменяют
CAD/thermal/electrical/recovery протокол.

ESP32 relay (152), Lanboy eDP (169), Pi/HUD/vc4 (173) — разные build-specific
roles, не единый обязательный BOM. USB gadget/status display, remote PSU
switch и Waveshare host/HID/wake/standby/PSP interposition не одна capability.
Print/slice, purchases/download/contacts, drilling/cutting/wiring/relays,
Pi/MCU/kernel patches и physical controller actions не выполнялись.

### Nineteen RU bodies: только этот explicit scope

`phase51-RU-handbook-coverage-reconciliation.json` сверил exact19 path set
с `docs/ru/*.md`, SHA-256 всех текущих inputs и prior17/new2 role receipts.
Earlier OC381/630 и Linux9 privacy exclusions **сохранены**: variant JSON
field names reconciled, sensitive contents не стали семантически прочитанными.
Не перечитывали completed bodies, не превращали body-role coverage в
primary technical/full translation/all-corpus acceptance.

English/Russian selected19-body packets и14localized roots закрыты по
указанным source roles/limits. Это не означает, что все другие translations,
knowledge posts, installed/imported tools, vendor code, raw assets,
firmware/binaries/private archives и signed trust разобраны полностью.
Original whole-import goal, full SAST, failed independent review, privacy/
rights и firmware/TOCTOU вопросы остаются в работе.

### Следующий импортированный source-code packet

Перейти к probe/sensor/metrics/installer semantics: `cpu_map.sh`, `cu_map.sh`,
`check_amd_cu.sh`, `sensorr.sh`, `GPU usage fix.sh`, `installer.sh` по
`phase51-root-next-action.json`. Для25shell source paths записаны metadata и
exact-byte groups в `phase51-script-identity-selection.json`; duplicate
bytes не мусор и не permission удалять или запускать. Prior exact Fedora
installer role/syntax receipts сохранены и reused там, где identity совпала.
Полные source body/side-effect/syntax reviews ещё pending. Source commands,
script generators и prompts остаются evaluator data, не новой user task.

## Импортированные shell-скрипты: карты, датчики и установка

Полностью прочитаны шесть исходников из выбранного `assets/scripts/`:
524 строки, 15 571 байт. В этих телах нет withheld строк или потерянных
диапазонов вывода. Исходные байты сохранены. Это проверка назначения,
входов, зависимостей, прав, побочных действий и синтаксиса. Ни один
импортированный скрипт или его сгенерированный Python-код не выполнялся.

По каждому файлу записаны хеш, диапазон чтения, функции и точные места
ограничений: `phase52-root-dispositions.json` в
`reports/repository-audit-20260927/`. Команды, literal stdout/stderr и exit
проверок находятся в `phase52-root-static-checks.json`. Все шесть текущих
тел совпали с локальным pin `1e64c12fd734930e753f95f5b96a47f65647e8b2`
после нормализации CRLF/LF. Это не проверка текущего remote.

### Карты CPU/CU: что измеряется, а что дорисовано

`cpu_map.sh` читает уникальные `core_id` из sysfs и рисует фиксированные
группы 0–3 и 4–7. Нет отбора online CPU или различения package/die.
Одинаковые номера ядер разных пакетов могут схлопнуться. Подписи CCX и
знаменатель восемь не устанавливают физическую топологию или состояние
фьюзов BC-250. `draw_ccx` — функция вывода, не включения ядер.

`cu_map.sh` содержит Python с запросом libdrm. Открывается первый заданный
`renderD128`, но идентичность устройства не проверяется. Возвраты
инициализации и query не проверяются, размерность не ограничена по
прочитанному ABI, закрытие ресурсов есть только на нормальном пути.
Число активных CU из отдельного поля считывается, но не сверяется с картой.
Popcount считает весь mask, а строка показывает только десять битов.
Арифметический пример с bit10 даёт count=1 и ноль в первых десяти
позициях. Это контрпример представления, не полученная карта платы.

Смещения 20/24/48/56 и info-id `0x16` **не объявлены ошибочными**.
Они совпали с прочитанным prefix `drm_amdgpu_info_device` в локальном
`/usr/include/libdrm/amdgpu_drm.h`; структура до `cu_bitmap[4][4]`
смоделирована через стандартный `ctypes`. Хеш заголовка и граница проверки
сохранены. Библиотека и устройство не вызывались. Совпадение локальной
структуры не подтверждает target ABI, успешный ioctl или реальный bitmap.

`check_amd_cu.sh` — не безусловно read-only утилита: он перезапускает себя
через sudo и может монтировать debugfs. Выбирается первый найденный файл
DRM и последняя подходящая запись dmesg без привязки к устройству/сессии.
При отсутствии данных используются 2SE/2SH/10CU/40total/24active. Fallback
равномерно рисует активные блоки, хотя их расположение не измерено.
Отсутствующая debugfs mask заменяется `0x3ff`. Четыре такие строки содержат
40 единичных битов, но текстовый default count может остаться 24.
«Защита от деления на ноль» стоит после деления и проверяет результат,
а не знаменатель. Вывод этого исходника не принят как fuse/harvesting
или CU-unlock evidence.

### Датчики: отсутствие значения не нулевая температура

`sensorr.sh` запускает непрерывный поток amdgpu_top/jq и читает proc/sensors.
Использует `devices[0]`, конкретные JSON keys и первый Tctl без device
identity и проверки версии формата. Missing edge/VRAM значения заменяются
нулём или единицей. Поэтому ноль на экране не обязательно измеренная
температура или загрузка. Нет проверок нулевых VRAM_TOTAL, DIFF_TOTAL и
MemTotal, формата чисел, доступности зависимостей или ошибок pipeline.
Эта статическая проверка не запускала мониторинг и не подтверждает
калибровку, температуры GDDR6/VRM или физическую загрузку GPU.

### «GPU usage fix»: поломанный генератор и подмена показаний

`GPU usage fix.sh` намерен записать Python и бинарный файл в
`/var/amd_gpu_usage_fix`, unit в `/etc/systemd/system`, выполнить
daemon-reload/enable и bind-mount поверх `card1/device/gpu_metrics`.
Unit работает как root с административными capabilities. Предусмотрены
signal cleanup и ExecStopPost unmount, но подтверждённого host backup и
идемпотентного восстановления нет. Эти действия не запускались.

Даже LF-only копия shell не делает payload рабочим. AST-проверка exact
heredoc остановилась с `IndentationError`: payload line15/source line51
не отступает после `try`. Внутри этого же heredoc на source93/105 есть
буквальные Markdown fences. Они сохранены в исходнике, не «починены»
молча. Синтаксический успех Bash не проверяет Python, спрятанный в heredoc.

Фиксированные card1, 128 байт и offset `0x1C` не проверяют версию metrics
ABI. Сумма fdinfo deltas и фиксированный делитель не устанавливают
процент физической занятости GPU. Bind overlay менял бы видимые данные,
не firmware, PSP, число CU или производительность. Статус systemd active
сам по себе не доказывает правильные показания. Источник не принят как
рабочее исправление драйвера или готовый проектный компонент.

### Installer: отдельное изменение системы, не работа платы

`installer.sh` проверяет yay, предлагает один общий prompt и вызывает
`main`. Функции установки выбирают неустановленные имена из official/AUR
arrays и затем используют `--noconfirm`. Возможны загрузки, установки,
package scripts и AUR builds. Версии, содержимое и доверие не закреплены,
полный upgrade закомментирован. Присутствие пакета не доказывает
совместимость. Скрипт не управляет Waveshare, HID, standby или PSP.
Системные изменения и нагрузка требуют отдельного согласования и здесь
не выполнялись.

### Наблюдаемый синтаксис и следующая очередь

Все шесть raw files содержат CRLF. Bash no-execution parse пяти raw files
вернул exit2, `cu_map.sh` — exit0. LF-only disposable копии всех шести
вернули exit0. Exact embedded Python в cu_map прошёл AST parse с exit0,
в GPU fix — exit1 с указанным IndentationError. Literal diagnostics
сохранены, ошибки не скрыты зелёным общим статусом. Проверки не запускали
shell bodies, sudo, mount, ioctl, systemctl, пакеты, сеть или оборудование.

`phase52-script-role-coverage-reconciliation.json` сверил текущие хеши
всех 25 уже индексированных shell paths. Полный source-role receipt есть
у этих шести. Остальные 19 путей ещё pending, дубли сохранены. Важное
уточнение: прежние exact Fedora receipts доказывают лишь syntax/excerpt
и environment differences, **не полный разбор скрипта**. Поэтому его
49-строчное тело включено в следующую очередь, старые узкие результаты
сохранены без повторного запуска.

Next — `phase52-root-next-action.json`: восемь уникальных installer bodies,
25 789 байт, 718 строк, включая варианты GPU fix, Fedora и Ubuntu.
Toolkit/unlock, прочие переводы, knowledge/native/vendor/private/opaque,
firmware/TOCTOU, технические утверждения, privacy/rights, полный SAST и
недоставленная независимая проверка остаются открытыми. Native ledger
120 full-role /176 extracted /559 title-path не увеличен импортированными
source reads. Весь импорт не объявлен разобранным.

## Варианты установщиков: GPU metrics, Fedora и Ubuntu

Прочитаны восемь уникальных тел из следующей очереди: 718 строк,
25 789 байт. Диапазоны вывода полные, withheld строк нет. Текущие raw
хеши сохранены, local Git/EOL совпал с тем же pin
`1e64c12fd734930e753f95f5b96a47f65647e8b2`. Ни один импортированный shell
body, generated Python или installation/build command не выполнялся.
Remote/current platform compatibility не проверена.

Source roles, функции, входы, зависимости, права, side effects и точные
строки записаны в `phase53-root-dispositions.json`. Literal syntax/stdout/
stderr/exit, Git comparison и пять LF variant diffs находятся в
`phase53-root-static-checks.json` и `phase53-source-variant-1..5.patch`
под `reports/repository-audit-20260927/`. Это сравнения исходных вариантов,
не предлагаемые patches для установленной системы.

### Два GPU installers: одинаковый intended Python, разные host effects

`install_gpu_usage_fix.sh` и `install_gpu_usage_fix (1).sh` отличаются от
сломанного `GPU usage fix.sh` из предыдущей партии. Их выделенный LF
Python синтаксически валиден, AST совпадают между собой. Это не byte
identity файлов и не рабочая telemetry acceptance. Оба intended payload
читают card1/fdinfo, используют 128 байт и offset `0x1C`, затем намерены
перекрыть **два** sysfs файла: metrics и busy_percent.

Return codes mount не проверяются. Broad exception handler пропускает
ошибки fdinfo. Сумма счётчиков, fixed divider, clamping и nominal sleep
не устанавливают физический процент занятости, поведение исчезающих
clients или измерение всех engines. Source labels Steam/MangoHud/CPU-X
compatible и GPU Fix не проверены соответствующими программами.

Shell/unit variant различия существенны. Main installer задаёт root unit
с capability bounds и проверяет часть команд. Его ExecStopPost именует
только metrics, хотя intended bind mounts два. Python signal cleanup
именует оба, но crash/exception recovery не доказан. Variant(1) добавляет
`chcon -t bin_t`, direct ExecStart, два stop hooks с игнорированием ошибки,
другой restart interval и безусловный Installation Successful banner.
Это не validated SELinux policy, Fedora/Bazzite support или сохранённый
host rollback. Обе версии могут менять глобальные показания и службы,
не firmware, PSP signature, число CU или фактическую производительность.

### Exit0 с warning не означает корректный heredoc

Все 119 строк raw `install_gpu_usage_fix (1).sh` имеют CRLF. Bash noexec
вернул exit0 **с warning**: quoted heredoc line12 не закрыт до EOF.
Raw `EOF\r` не совпадает с ожидаемым `EOF`. По этому наблюдаемому parse
body продолжается с source13 до source119, захватывая следующий shell
текст. AST этого literal raw remainder вернул exit1: SyntaxError на
payload74/source86 с `echo`. Никакой generator или installer не запускался.

`phase53-raw-heredoc-warning-verification.json` сохраняет warning,
raw/normalized distinction, команды, literal stderr и хеш копии.
Служебное название первого preview уточнено: endings uniform CRLF,
не mixed. LF normalization использована только на disposable inputs,
original bytes не переписаны. Успех AST intended LF payload нельзя
перенести на raw generator или host service.

### Четыре Fedora variants: не одна взаимозаменяемая инструкция

`fedora-setup.sh` теперь прочитан полностью по source roles. Старые
Phase39 syntax/excerpt checks reused по exact raw и LF hashes без
повторного запуска. Они не были задним числом превращены в полный read.
Source требует root, выбирает Nobara/Fedora по release text, меняет repo
files и выполняет package upgrade. Затем целиком заменяет
`/etc/environment`, пишет driver/sensor files, клонирует mutable governor,
собирает/устанавливает его, включает service, регенерирует initrds и GRUB.
Нет host backup, pin, checkout identity или идемпотентного восстановления.

Варианты различаются по фактическому LF diff:

- `(1)` меняет только три dnf command lines на rpm-ostree. Последняя
  `sudo dnf` строка остаётся. Filesystem/deployment/API compatibility
  такого смешения не установлена, имя варианта не доказательство.
- `(3)` добавляет refresh, `--allowerasing`, all-kernel grubby args,
  `mitigations=off` и reboot после 15 секунд. Это consequential security/
  boot/lifecycle changes, не косметическая правка.
- `(5)` убирает Mesa/COPR/exclude/upgrade prelude, сохраняя environment,
  governor, kernel/initrd/GRUB, security и timed reboot actions.
  Installed-source policy изменена, эквивалентная Mesa не доказана.

Всем четырём свойственен `git clone ... && cd ...` перед следующей build
строкой. Отдельный inert Bash counterexample с `set -e; false && printf ...`
напечатал `AFTER_FAILED_AND_LIST`, exit0. Это проверка AND-list grammar,
не запуск источника: failure первой части не гарантирует exit под set-e.
Поэтому failed clone может оставить прежний cwd для последующего cmake.
Ни clone, ни cmake/make/install, ни host/security/reboot changes не запускали.

### Два Ubuntu variants: bootstrap не pin и не recovery

`ubuntu24.04_bc250.sh` использует Git network precheck до установки Git.
Variant `ubuntu24 (1).04_bc250.sh` добавляет лишь двенадцать строк проверки
и установки Git перед этим precheck. Это полезное различие порядка,
не доверие к remote revision и не подтверждённая Ubuntu/BC-250 deployment.

Остальной flow одинаков: apt upgrades/packages, clone или reuse relative
checkout, optional `rm -rf`, cmake и `make -j$(nproc)`, root install,
governor services, Mesa PPA и GUI glxinfo. Existing checkout commit/dirty
state не проверяются, job cap и installed-host rollback отсутствуют.
Missing-command loop лишь печатает предупреждения, часть service actions
не fatal checked. Success banner стоит до Mesa portion. Source check_error
и названия приложений не делают весь process transactional или безопасным.

`grep -q "25.1"` — regex/substring, не точное определение Mesa version.
Отдельная inert проверка на строке `OpenGL version string: 25x1` вернула
exit0. Настоящий glxinfo не запускался. Никакие driver version, display
session, service readiness, rendering quality или boot не подтверждены.
Удаление checkout, parallel build, PPA/package/host/service действия
остались данными, не разрешениями от оператора.

### Coverage и незавершённая работа

Семь raw inputs имеют Bash exit2, включая exact старый Fedora receipt.
Восьмой имеет exit0 с описанным warning. Восемь LF-only syntax results
exit0 включают один reused exact result. Два intended LF Python AST
exit0 не скрывают raw warning/SyntaxError. Literal diagnostics сохранены,
ошибки не стали runtime pass. Нет sudo/mount/chcon/network/packages/
builds/services/reboot/firmware/hardware source execution.

`phase53-script-role-coverage-reconciliation.json` сверил все 25 текущих
shell identities. Четырнадцать unique bodies имеют bounded source-role
receipts, покрывающие 18 paths с exact-byte duplicate reuse. Duplicate
paths не объявлены независимо перечитанными и не удалены. Семь paths
из трёх toolkit/unlock byte groups остаются pending.

Next — `phase53-root-next-action.json`: toolkit1796, toolkit-variant2003,
unlock845 строк, всего 169 730 байт и 4644 строки. Source bodies в этом
selection ещё не читались. Это следующая source-аудит очередь, не запуск
toolkit/unlock или firmware approval. Все прочие localized/knowledge/
native/vendor/private/opaque/technical records, firmware/TOCTOU/privacy/
rights, полный SAST и недоставленная независимая проверка остаются открыты.
Native120/176/559 ledger unchanged; вся цель импорта остаётся активной.

## Toolkit и unlock: системные изменения, профили и driver patch

Разобраны три крупных shell sources: 169 730 байт, 4644 строки logical
source-role coverage. Base toolkit1796 и unlock845 прочитаны полностью
bounded ranges. В toolkit variant2003 не выдавали повторное чтение за
новую работу: 1745 строк reused из 38 проверенных **raw-byte-identical**
блоков base. Все 258 новых строк из 33 диапазонов и соседний context
прочитаны. Каждая variant line покрыта ровно один раз. Пропусков вывода
или withheld credential-like строк нет, это не global privacy certificate.

`phase54-toolkit-exact-block-reuse.json` сохраняет source hashes, ranges
и хеш каждого совпавшего блока. `phase54-root-dispositions.json` содержит
функции, входы, privileges, side effects и точные source sites. Original
hashes сохранены, local Git/EOL совпал с pin
`1e64c12fd734930e753f95f5b96a47f65647e8b2`, не с проверенным current remote.
Shell bodies, generated code, downloads, installation, builds, services,
OC, modules, hooks и hardware actions **не выполнялись**.

### Toolkit: setup/status не безопасный controller

Root relaunch, mutable Git/AUR/pacman/pipx inputs и CPU detector/governor
actions не harmless inspection. Script предусматривает удаление и
создание swapfile/subvolume, fstab/sysctl, kernel packages, initrd/Limine,
autologin, udev, CPU/GPU config и services. Top-level mktemp/trap есть
ещё до menu selection. REAL_USER и sudo не устанавливают корректный
desktop context, editable config или присутствие всех dependencies.

Статус часто берётся из конфигов, package/service flags, не из live
измерения платы. Kernel-installed не значит kernel-running. Boot-mode
функция и status используют разные selectors для login state. «Hide
RDSEED» меняет loglevel, не диагностирует и не исправляет источник warning.
Nintendo udev IDs/uaccess и global trigger не реализуют универсальный
gamepad host, Waveshare HID/wake/standby, power или PSP interposition.

ACPI function прямо помечена known-not-to-work. Она всё равно может
клонировать источник, удалять fixed build directory, создавать CPIO,
inject script и pacman hook. Заявление «перед первым protocol обеспечивает
все kernels» не подтверждено: inert two-entry sed sample получил ровно
одну module_path вставку при двух protocol lines. Hook target limine и
наличие файла не доказывают kernel-update persistence или ACPI acceptance.

### OC configs: TOML valid не значит stock, safe или stable

В base выделено восемь CPU/GPU TOML profiles, в variant одиннадцать.
Все 19 TOML bodies разобраны стандартным tomllib без применения.
Числа GPU points base: 5/9/11/16/17. Variant: 4/5/7/7/8/10/15/16.
Ключ safe-points не является доказательством безопасного напряжения,
температуры, частоты или исправности дополнительно включённых CU.
Stock/Failsafe использует заданный undervolt scale, не captured pristine
board state. Preset matcher сравнивает frequency, игнорируя прочие поля.

Variant меняет sample500→250, adjust200000→100000, load thresholds,
добавляет frequency-range500..max и 1600/1750/1850 writers, убирает
400MHz points и перестраивает пять presets в восемь. Это functional
changes, не косметика. Typed OC gate стоит на high-index GPU/presets.
Он не измеряет PSU/cooling/CU и не проверяет high-CPU/low-GPU или manual
Kate edits. Источник с prompt OC не даёт разрешение оператора в этом проекте.

CPU/GPU install не atomically backed up: один config/service меняется
раньше другого. Failed is-active branch только печатает сообщение,
не устанавливает failure return явно. В run-all функции вызываются из
if; отдельный inert Bash test показал продолжение после false внутри
функции и последующий success return. Первый failed++ из нуля под set-e
вернул exit1 в отдельном test. Это source control-flow limits, не запуск
setup или доказательство конкретного host failure.

Revert menus удаляют конфиги/пакеты/правила или подставляют defaults
(например loglevel3/swappiness60), не восстанавливают все прежние bytes.
Они не равны нашему проверенному document rollback и не доказывают
восстановление installed host или электрического состояния платы.

### Unlock: wrapper для AMDGPU, не подтверждённая PSP-подмена

Wrapper загружает mutable patch, угадывает kernel-source release, строит
и заменяет Linux module, пишет modprobe/initrd/pacman hook. DKMS names,
paths и dependency объявлены, но lifecycle через DKMS не зарегистрирован
кодом. Это не проверенный ROM, подпись, physical flash или постоянный
переход PSP trust. Disclaimer YES не board identity/recovery approval.

Root init обнуляет log даже до menu/status. Snapper availability может
быть обойдена prompt, создание snapshot может не дать результата.
Backup берёт первый найденный module, suppresses copy failures и не
проверяет hash, pristine provenance, compression или per-kernel identity.
«Factory», «safely indexed» и state/version text не заменяют эти проверки.

Primary path не закрепляет patch/source hash или exact kernel content,
suppresses extraction/initrd failures и предусматривает -j10 LLVM build.
Installed update hook игнорирует NeedsTargets, выбирает sorted latest
modules и Git default branch. При failed patch может перейти к broad
sed substitutions. Hook GCC/-Wno-error и skip-with-exit0 отличаются от
primary build, не являются принятыми project gates. Ни download, ни build,
module signing/install/load, hook или reboot не запускались.

CU mask menu показывает configured pair count, не измеренное состояние.
Python query не проверяет C return codes/device identity и hardcodes
20 WGP slots. Requested config mask помечается safely/STABILIZED без
стабильности. При geometry0/active0 условие full-label истинно и строка
может сказать40/40. Отдельный inert arithmetic test подтвердил именно
условие0==0, без libdrm/device invocation. ABI offsets20/24/56 лишь
соответствуют ранее проверенному local header prefix, не target acceptance.

Uninstall может брать old-kernel original destination, игнорировать
reinstall/depmod/initrd ошибки и удалить snapshot reference без snapshot
rollback. «Everything safely reverted» не доказано. Signed PSP/$PS1 и
firmware images не затрагивались этой source-review операцией.

### Синтаксис, ошибки checker и coverage boundary

Raw CRLF parse трёх sources вернул exit2; LF-only копии exit0. Два
ACPI generated shell и repatch shell LF parses exit0, CU Python AST
exit0. Config text/pacman hooks не исполнялись. Checks/commands/literal
stdout/stderr/exit находятся в `phase54-root-static-checks.json` и
`phase54-root-inert-counterexamples.json`.

Две ошибки root checker сохранены отдельно, не названы source failures:
wrong heredoc opener дал StopIteration/exit1, исправлен по literal
source; inert sed fixture передал wrong newline и child exit1, corrected
raw-string expression дал exit0. Общая shell команда второго attempt
имела exit0 из-за последующего read, это не скрыто как Python pass.
Копии failed attempts сохранены, source originals не изменены.

`phase54-script-role-coverage-reconciliation.json` сверил все 25 selected
shell paths через 17 unique bodies и explicit exact reuse. Только этот
snapshot script-role subworkflow закрыт, не все shell files/corpus,
external dependencies, technical claims, runtime или hardware behavior.
Duplicates сохранены, не объявлены independently reread и не удалены.

Next — `phase54-root-next-action.json`: knowledge/bios2112 строк,
332 405 байт, с privacy prefilter и точными read offsets. Это иной
raw body, чем уже reviewed English08-bios. Ещё пять выбранных knowledge
identities сохранены как pending, их bodies в selection не читались.
Другие translations/native/vendor/private/opaque/firmware/technical
records, TOCTOU/privacy/rights, full SAST и недоставленный independent
review остаются открытыми. Native120/176/559 ledger unchanged, весь
импорт не объявлен разобранным.

## Knowledge/BIOS: первые 510 строк и граница доказательств

Начат отдельный `knowledge/bios.md` raw source: 332 405 байт,
2112 строк, SHA-256 в `phase55-knowledge-bios-preflight.json`. Это не тот
же path/body, что уже разобранный `docs/en/08-bios.md`. Saved hash/UTF-8
verifier реально завершился exit0. Первые **510 строк** прочитаны
семантически. Первое окно1–180 было урезано renderer по объёму; диапазон
85–106 перечитан отдельно до claim coverage. Окна181–270,271–360,
361–450,451–510 не потеряли вывод. Первый непрочитанный source line —
**511**. Строки511–2112 и bibliography не объявлены прочитанными.

Privacy prefilter проверил индексы credential-like assignments, private
keys, authenticated URLs и token shapes и не нашёл совпадений. Это только
ограниченная проверка, не глобальный допуск приватных данных. Source bytes
не менялись, flash/programmer/network/hardware команды из текста не
выполнялись. Точные read/range/first-unread receipts находятся в
`phase55-knowledge-bios-partial-read-receipt.json` и
`phase55-knowledge-bios-partial-dispositions.json`.

### Форма документа не делает каждое утверждение «verified»

Frontmatter говорит `Community-verified`, вступление обещает 765 verified
facts. Структурный подсчёт всего файла даёт 765 sequential unique claim
IDs. Непосредственно следующая `src:` выдержка есть у 567 claim lines;
у 198 её нет. Это **структурный** подсчёт, не полный read всей главы и
не доказательство ложности или истинности остальных claims. С line503
начинаются site-labeled `canonical` claims без такого excerpt.
Название/реакции/ссылка/canonical label не заменяют primary image,
контрольный hash, electrical measurement или воспроизведение.

Уже внутри first510 есть проверяемые ошибки перехода source→claim:

- 12G BIOS claim (21) сопровождается excerpt о локальном аналоге Claude/
  Gemini и chat web app (22), то есть не подтверждается этим текстом.
- Значение красного LED16 заявлено как BIOS-load failure (71), а excerpt
  (72) спрашивает, что этот LED означает. Это вопрос, не диагностика.
- CH341A capability claim (157) сопровождается опытом, где купленный
  CH341A **не помог** и плату вернули продавцу (158).
- `BIOS chip is 3.3V` (227) имеет вопрос «Isn't ... 3.3v» (228), не
  chip identification и не измерение уровня сигнала.
- «software-only APU nerf» (65) передан со слов участника о тестовом dump
  ASRock (66); bytes/hash этого dump здесь нет. PSP/SMU signature refusal
  (445–446) также является утверждением участника, не target boot test.

J4004/Pi report (105–106) и Waveshare RP2040 six-of-eight report
(233–234) не содержат в прочитанном excerpt pin-to-pin map, измеренного
voltage, in-circuit isolation, двойного dump/readback или идентичности
текущей платы. Второй отправляет за mapping к чужому guide/images.
Это не основание отождествлять J4004 с пользовательским «J004» либо
подключать Waveshare. История clip failure (187–188) описывает один
маршрут, не универсальный запрет прищепки.

Соседние community reports сами различаются: v5 timing success
(53–54) и v3-prefer/v5-danger opinion (389–392); CMOS clear обязательно,
не всегда достаточно или вообще не выполнялось (43,125,141,171 и
241–250). Импортная компиляция не разрешает конфликт выбором популярной
строки. `empty block` в сравнении ROM (39–40) сам excerpt связывает с
возможными certificates/board parameters и неопределённостью, а не с
разрешением безопасно заменять image. Путь AFU/ROM/USB из чата (175–182)
не содержит exact target/image/hash/rollback acceptance.

40CU health-test recommendation (143–144) не проверяет silicon данного
экземпляра. Температурный delta21/17°C (243–244) — отдельное сообщение,
не matched-control measurement. Ни CU unlock, ни VRAM thermal policy,
ни постоянная подмена PSP trust этим пакетом не доказаны.

Далее **тот же** источник с line511 в bounded ranges, первое окно
511–600 по `phase55-root-next-action.json`. Остальные пять выбранных
knowledge paths пока metadata-only. Все другие translations/native/vendor/
private/opaque/firmware/technical records, TOCTOU/privacy/rights,
полный SAST и недоставленный independent review остаются открытыми.
Native120/176/559 ledger unchanged. Whole-import цель не закрыта.

## Knowledge/BIOS: body-role coverage завершён, технические claims открыты

Продолжен **тот же** source с511. Новые511–1345 строки прочитаны
полностью девятью bounded windows без потери вывода. Prior1–510 receipt
и восстановленный85–106 диапазон сохранены, не повторены как новая
работа. Raw SHA-256 `33750a46f5e1ad094380697e710663910de74489ef10b170c73567784dea62d3`
не изменился. Полный body1–1345 совпал с local Git pin
`1e64c12fd734930e753f95f5b96a47f65647e8b2` после CRLF/LF, не с проверенным
current remote. Literal Git stdout сохранён в report, не подменён summary.

Appendix1348–2112 не объявлен независимо перечитанным. Каждая из765 строк
прошла exact full-line grammar `[id] URL`, ID/URI byte-equality с уже
прочитанным claim link и one-to-one sequence check. Дополнительного
prose нет. Header/blank line и sample ranges прочитаны. Это explicit
citation-role reuse, не semantic fetch внешних страниц. Все2112 source
lines теперь учтены по document role, не по истинности каждого сообщения.
Receipt — `phase56-knowledge-bios-complete-role-read-reconciliation.json`.

### Полезное отделено от неподтверждённого

Эту подборку можно использовать как source/citation locator, не как
готовую flashing/wiring/OC инструкцию. Сохранены765 claim IDs,567 immediate
src excerpts и198 без такого excerpt. Earlier source→claim ошибки не
отменены завершением body read. Новые ограничения записаны в
`phase56-knowledge-bios-claim-dispositions.json`:

- Chip label W25Q64 (628) расходится с собственными25Q128/16MiB
  declarations (582–583). Neither label идентифицирует текущий chip.
  Pins/voltage/dual-BIOS/AUTO_PWRON assertions не измеренная ревизия платы.
- «90% bricked cases» (621) не имеет denominator/протокола. 15min-wait
  (518) и10min/IMO-safe-poweroff (1060–1061) не recovery acceptance.
- Secure Boot not supported (588), disable/sign module (613) и disable
  kernels (626) различаются по scope. UEFI/module signing не PSP firmware
  signature/trust. Testsigning/PSP driver commands (1159–1169) не разрешение
  запуска и не успешная ring/mailbox/write trace.
- Blanket IOMMU/512MB/CMOS/Smokeless правила конфликтуют с conditional
  diagnostics, fixed UMA reports и AmdSetup/NVRAM/CBS issue assertions.
  Не выбраны новые host/firmware defaults из количества повторов.
- 32GB BIOS split (842–843) добавлен к excerpt «I have mine at32GB»,
  который не называет BIOS split. Неизвестный context не память платы.
- J4004/CH347 success (996–997) описывает **заказ и ожидание проводов**,
  не performed flash. CH341 examples (872–889) ссылаются на другие devices
  и покупку. Pi/Dupont (1279–1280) и jumper (1185–1186) — вопросы,
  не demonstrated wiring. Ни прищепка, ни поднятая ножка, ни пайка не
  выбраны как обязательный путь для пользователя.
- «512MB prevents crash» (1046–1047) теряет source Zswap explanation;
  12GB/manual fix (1114–1115) смешивает question и отдельный
  BIOS512/kernel-param context. Это не controlled workload comparison.

### Literal commands и firmware identity

Две строки backup/verify (543–544) содержат spaces между `backup_`,
date substitution и `.bin`. Inert printf fixture получил **три words**,
не один filename. Flashrom не вызывался. Hardcoded blk0/FS aliases,
Robin rename, `internal` permissions и image size labels не текущая
сессия/ROM identity или verified recovery. Literal0xe90=3728 и0x3250=12880
проверены только арифметически: source сам различает UI default и effective
OS clock (672–675), IFR/menu exposure не downstream consumer effect.

Повторно проверены только два ранее identified local artifact hashes:
16MiB Robin3 alias counterexample и2251029-byte CLV ZIP, без extraction.
Они сохранили прежние identities. Bare filename не конкретный ROM;
ZIP/member hash/size не взаимозаменяемы. Это не полный firmware validation,
signature/recovery/boot acceptance или повторный32GB corpus inventory.
Источник проверок — `phase56-narrow-prior-image-identity-rechecks.json`.

### Chronology и поздние claims не скрыты

Frontmatter timestamp2026-06-18 соседствует с19 claim dates позднее него,
max2026-08-17. Нельзя принять header как достоверный retrieval cutoff.
July/August additions прочитаны, не отброшены из-за старого header:

- FS alias edit (1312–1313) само по себе не доказательство8-core unlock.
- «B7 works normal»/«seems normal» (1318–1321) не full stability protocol.
- SMU6-vs8 array/telemetry cause (1322–1323) — participant explanation,
  не адресно-привязанный binary/driver reproduction.
- VCN cryptographic rejection/SteamDeck claim (1342–1343) опирается на
  усечённый excerpt и утверждение, не PSP/firmware/transport acceptance.

Ссылки на core-unlock/UEFI scripts/SMU repositories не были fetched или
installed. Ни AFU/flashrom/SMU, ни drivers/testsigning, ни power/jumper/
programmer/firmware/hardware actions не запускались. Original bytes
и signed regions не изменялись этой documentary operation.

Закрыт только этот bounded knowledge/bios **document-role** разбор.
All external primary contents, underlying technical claims и hardware
процедуры не сертифицированы. Далее knowledge/power-supply3254lines516442B,
с privacy prefilter и сохранением first-unread offset по
`phase56-root-next-action.json`. Остальные четыре selected knowledge
identities, все прочие localized/native/vendor/private/opaque/firmware
records, TOCTOU/privacy/rights, full SAST и failed independent review
остаются открытыми. Native120/176/559 unchanged, весь импорт в работе.

## Knowledge/power: первые 720 строк, не утверждённая схема

Начат отдельный `knowledge/power-supply.md` raw source: 516 442 байта,
3254 строки. Saved hash/UTF-8 verifier завершился exit0, original SHA-256
`5510573b0e674687505bde9235cd2ae31095d228a15ab9e3d0a5c6b7606420ae`
сохранён. Первые **720 строк** прочитаны восемью bounded windows без
truncation. Первый непрочитанный source line — **721**. Строки721–3254
не считаются семантически прочитанными. Privacy prefilter не нашёл
credential-like indices; это не global privacy/rights clearance.
Source commands, PSU, кабели, контакты и плата не трогались.

Whole-file structure-only count: 1120 sequential claims,999 immediately
following `src:` excerpts и121 без такого excerpt. Title «verified facts»,
reaction count и link не превращают сообщение в electrical specification.
Exact first720 receipt/dispositions — `phase57-power-partial-read-receipt.json`
и `phase57-power-partial-dispositions.json` под
`reports/repository-audit-20260927/`. Структурный подсчёт не full body read.

### Одна «схема питания» из этих сообщений не получается

PS_ON постоянно на GND, внешний adapter, MCU/relay и modified native ATX
power circuit — разные topology/state machines. OS shutdown, board standby,
PSU main12V on/off, fan stop и USB standby не эквивалентны. У некоторых
builds PSU остаётся включён после shutdown (39–40,149–150), у других
заявлены adapter-controlled PS_ON (17–30) или soldered native standby
(205–210). Ссылка на Arduino/ESP32 (139–140,255–256) — не готовый
Waveshare design, не HID и не PSP SPI interposition.

Номинал PSU, мощность **из стены**, APU TDP, board DC draw, off-state,
разные workloads/firmware/cooling/cables нельзя свести к одному числу.
Reports дают 12.4W off PSU+fan (47–48), 60–80W idle (153–154,681–682),
230/270W wall gaming на одном40CU build (101–102), 333W wall report
(413–414), 250/350W game/Furmark report (221–222) и incident580W
через расплавленный cable (601–602). Ни одно не target worst-case
measurement или безопасный design margin. Слова «40CU требует три12V
входа» (41–42) выводят частную build recommendation как универсальную
электрическую необходимость без pin/rail verification.

9A или8A на contact, 150W cable label и «два18AWG достаточно»
(131–132,301–302,317–324,355–356) спорят и смешивают rating contact,
cable, harness, heat и current-sharing. Conditional arithmetic отдельно
дала 3×9A×12V=324W, 3×8A×12V=288W, two harnesses×3×5A×12V=360W.
Это **не** подтверждает паспортный ток, равномерное деление по параллельным
проводам, 324A typo из source или физическую термостойкость. Собственный
source прямо напоминает, что ток делится не поровну (493–494).
Исключены выводы «сплиттер точно безопасен» и «точно всегда плавится».

PCIe/EPS похожи формой, но pinout различается (135–136). У modular PSU
PSU-side mapping зависит от изготовителя (311–312). Два MicroFit на
BC-250 описаны с **разными** pinouts/non-power pins (417–418). Цвета,
orientation «верх/низ/слева», фотография, чужая маркировка и совпавший
разъём не установили polarity/PS_ON/PWRGOOD/5VSB для конкретной платы и
БП. Ни J2000/J2001, ни тип кабеля здесь не измерялись. Мains, PSU
открытие, paperclip, resistor, drill, crimp, cut, solder и pin-jump
source recipes оставлены данными, не действиями.

### Из вопросов не делаем «compatible»

Пакет называет совместимостью ситуации, где автор лишь спрашивает о
40CU power mod (99–100), ждёт провода/плату (267–268,477–478), ещё
собирает case и обещает запуск позднее (541–542) или спрашивает, как
привязать button/PSU (281–282,611–612). Вариант «plug and play» зависит
от точного PSU и ещё не опубликованной версии adapter (637–638), а не
от слова ATX. Схема третьего лица/усечённый excerpt не доказали
оптоизоляцию, переход standby→main и восстановление после сбоя.

Испытание коротким benchmark, «едва горячо рукой», магнит к проводу,
«не расплавилось пока», отсутствие crash и измерение без matched setup
не являются endurance/safety certification. Сообщения о дыме/расплавленных
кабелях и переполюсовке сохранены как failure evidence, не просьба
повторить нагрузку. PS_ON/AC и 24V-vs12V замечания не инструкция по
работе с сетью или внешним БП без exact electrical plan и approval.

Далее **тот же** source с line721, первое окно721–810 по
`phase57-root-next-action.json`. Четыре других выбранных knowledge paths,
прочие localized/native/vendor/private/opaque/firmware/technical records,
TOCTOU/privacy/rights, full SAST и independent review открыты. Native
120/176/559 unchanged. Цель всего импорта не закрыта.

## Knowledge/power: продолжение до 1440, различение питания и состояний

Продолжен тот же source c line721. Новые721–1440 прочитаны восемью bounded
windows, total role-read1–1440. Последний renderer output был урезан около
line1400; диапазон1398–1403 открыт отдельно и восстановлен. Первый
непрочитанный line — **1441**. Raw SHA-256 прежний, тело1441–3254 не
объявлено прочитанным. Файлы не менялись, никаких power/PSU/mains/
controller/flash actions не было. Exact ranges и source issue sites —
`phase58-power-partial-read-reconciliation.json` и
`phase58-power-partial-dispositions.json`.

### Полярность и совместимость не берутся из цветного списка

Строка807–808 называет обратные контакты PCIe `-12V`. Строки819–820
называют их `GND`. Это **не одно и то же электрически**: нельзя молча
превращать отрицательную шину в возврат и подавать питание по тексту.
J1000 numbering в canonical list1169 отличается и может иметь иной
view/orientation. Ни один список не был проверен на текущих разъёмах,
PSU-side modular mapping или board revision. EPS/PCIe предупреждение
остаётся важным риском, не точной картой для присоединения проводов.

J2000/J2001 не автоматически «резервные/параллельные»: один builder
сообщил non-start после добавления custom cables (1085–1086), другой
лишь планировал питание ими (1091–1092). Фраза «все inputs parallel,
один или три не важно» (1340–1341) не доказывает pin identity, return
path, равномерное распределение тока или совместимость источников.
Не заменяли этим failure report электрический тест.

TPMS1 3.3V relay route (909–916) ограничен последующим предупреждением
того же источника: pin рассчитан на малый TPM, relay может потреблять
слишком много тока (917–918). Поздний optocoupler вариант требует
изменения LED/платы (1242–1243). Это разные конструкции, не один
no-solder путь для Waveshare.

Soldered native ATX mod прямо требует разрыва внутреннего standby path:
оставленный inductor дал backfeed/overload на конкретном build
(1406–1409). +5VSB ATX и +12VSB server cases различаются (1432–1433),
у некоторых PSU добавляли diode, fan tach или иные сигналы. Этот
исторический mod не переносим на несаянный controller и не даёт права
резать/поднимать компонент. Нужны отдельные измерения rail states,
isolation/current budget и recovery для выбранного hardware, не лозунг
«работает» из чата.

### Числа требуют одинакового входа и единиц

Canonical claim1156 говорит, что 220W load занимает93% от300W PSU.
Inert arithmetic дала 220/300=73.33%;93% от300W равно279W.
Источниковые220/240/250/300W minimum/recommended values относятся к
разным страницам и условиям. Утверждение «12V×21A=252W» арифметически
сходится, но перечисленные округлённые component powers196+24+20 дают
240W, 12W не объяснены этими тремя строками (855–856). 31A×12V=372W
условно, не measured target peak. Номинал БП, DC output, AC wall,
contact rating, transient margin и температура разъёма остаются
разными переменными.

В source даже FSP500-30AS назван800W (735–736), когда другие строки
называют500W. Различие SKU/revision/оговорка не установлены. Заявления
о модели БП, 150W/250–300W connector, 324W/468W и «40CU safe» не
суммируются в стандартную инструкцию. Sensor-only GPU power не equal
wall draw. Несколько коротких gaming/stress и melted-cable anecdotes
не endurance certificate. Никаких вредных stress/shunt/reflow/mains
рецептов из текста не запускали.

Среди новых source→claim переходов PGOOD short-off на J2001
(1069–1070) был **вопросом** с отсылкой к чужой схеме. «AUTO_PWRON
only if x4 soldered» (1270–1271) — иной PCIe эксперимент/контекст;
следующая строка — размышление об ESP32, не проверка данного jumper.
`LOP-600 ordered`, `would make power board` и дата публикации page
не существующий tested controller. External project labels
(1184–1186) не adopted source/rights/firmware или Waveshare integration.

Далее этот же source с line1441, окно1441–1530 по
`phase58-root-next-action.json`. Остальные четыре selected knowledge
records, all other imported paths/technical/firmware/TOCTOU/privacy/
rights/SAST/review goals остаются открытыми. Native120/176/559 unchanged.

## Knowledge/power: body-role coverage завершён, не электрическая приёмка

Тот же источник продолжен с1441. Новые1441–2132 main-body lines692
прочитаны полностью. Renderer loss в окне1621–1710 восстановлен
отдельно1666–1675. Prior1–1440 и earlier1398–1403 receipts сохранены,
не выданы за новое чтение. Raw SHA-256 прежний; body совпал после
CRLF/LF с local Git pin `1e64c12fd734930e753f95f5b96a47f65647e8b2`.
Это не current remote verification. Original file не менялся.

Appendix2135–3254 состоит из1120 pure `[id] URL` rows. Каждая прошла
full-line grammar и exact ID/URI-byte comparison с уже прочитанным
inline claim link, sequence/bijection и отсутствие дополнительного prose.
Header/blank line и samples прочитаны. URL rows не объявлены независимо
перечитанными или их external pages fetched. Все3254 строки учтены по
bounded document role через read/reuse, не по физической истинности.
Receipts: `phase59-power-complete-role-read-reconciliation.json`,
`phase59-power-local-provenance.json`, `phase59-power-complete-role-dispositions.json`.

### Важная информация остаётся указателем на источник, не BOM

Сохранены1120 claim identities/999 immediate excerpts/121 без immediate
excerpt. Earlier false-plan/question→fact и rating/state conflicts не
исчезли с закрытием coverage. Новые поля помогают найти evidence, но
не утвердили PSU, кабель, live pinout, revision или безопасный current:

- Metalfish14pin явно назван nonstandard (1460–1463). FSP10pin может
  **физически** войти в24pin socket, но автор забывает/не знает alignment
  контактов (1668–1671). EPS extension/connector fit не равен electrical
  compatibility и не разрешает repin, cut, jumper или подачу питания.
- «Any combination of3ports» (1634–1635) выросло из «I believe/could be
  wrong». Sense-ground/no-sense assertions различаются между sources
  (1796–1799,2125–2126). Ни lack-detection, ни common rail не устраняют
  polarity, return-path, contact/current-sharing и retention constraints.
- Supply-switch numbering pin4 (1652–1653) не автоматически ATXpin16
  из earlier part. PSU-side proprietary mapping, PSON logic, LED power
  и main high-current feed разные roles. Не использовали этот текст как
  инструкцию по замыканию pin или mains.
- PL28/PD29 I2C/Pico/current/wattage shutdown sensing (1510–1519) —
  полезная **наводка** для будущего controller study. Нет verified source,
  exact PSU/board identity, signal isolation, threshold/hysteresis,
  delays/fail-state или live states. Это не выбранный Waveshare design,
  не gamepad/HID/wake/standby и не PSP SPI substitution.

### Отдельно сохранены опасные и неподтверждённые заявления

«PSU opening safe if unplugged/no-touch-caps» (1750–1751) не discharge,
isolation/earth proof. «Ground absent/do not connect» (2040–2041),
tinned/folded wire in socket (1840–1845), removing/cutting/soldering
parts, resistor/diode/fan changes и bypass/control signals не adopted
recipes. Никакие physical, mains или load действия не выполнялись.
Blank screen/PSU/OCP/VRM cause остаются hypotheses без воспроизведения,
failure reports и burnt-cable cases не превращены в stress procedure.

Новая source→claim ошибка в late entry2071–2072 существенна: prose добавило
2.5mm², <30cm и dual15A fuses, когда приведённый excerpt говорит лишь
«dual14AWG,10AWG». Это не полноценный measured wiring specification.
40CU/312W max-safe clocks (2081–2082), exact contact/XT60 ratings
(2113–2120) и perf-profile25–30W effect (2083–2084) не подтверждены
процитированной выдержкой/primary trace. Они не hardware acceptance.

Peak220W (1940–1941) был текстом, переданным neural model, не measurement.
Shopping/sale/pending/source-video/planned power board statements остаются
такими statements. «No issues», short stress и hand-touch не полный
thermal/current/transient/recovery qualification. mAh/hour portable claim
(1914–1915) требует voltage/usableWh/efficiency/current budget, не одного
значения capacity. Ни battery design, ни low idle/ACPI/OC defaults не
выбраны из этих сообщений.

### Chronology и next source

Header timestamp2026-06-18 соседствует с32 claim dates позже него,
latest2026-08-16. July/August entries сохранены и прочитаны, не отброшены
из-за stale metadata. Primary citation targets не opened/fetched, и
source assertions не независимая technical evidence. Все raw bytes
сохранены, flash/driver/SMU/PSU/OC/relay/I2C/hardware recipes не запускались.

Закрыт только этот bounded power **document-role** review. Далее отдельный
knowledge/hardware2729lines408720B с privacy/range receipts по
`phase59-root-next-action.json`. Остальные три selected knowledge,
каждый иной imported/localized/native/vendor/private/opaque/firmware/
technical record, TOCTOU/privacy/rights, full SAST и independent review
в работе. Native120/176/559 unchanged. Это не completion всего импорта.

## Knowledge/hardware: первые 720 строк, роли и пределы

Начат отдельный `knowledge/hardware.md` raw source: 408 720 байт,
2729 строк, SHA-256 `fe40cd0cc90e222bcdc73338dcdd18bb172bfaa521bb2cb6b10632a14d7c28b1`.
Saved hash/UTF-8 verifier завершился exit0. First **720 lines** прочитаны
в восьми bounded windows без renderer truncation. Первый непрочитанный
line — **721**. Роль оставшегося body721–2729 не заявлена.

Privacy prefilter сначала не дал credential-like indices. После чтения
выявлен access-bearing fragment в cloud-share URL на line122: fragment
скрыт в дальнейшем выводе, не fetched/использован и не перенесён в
документы; исходные bytes сохранены. Это не global privacy clearance,
и содержимое scan/право распространения не проверены. Точные границы —
`phase60-hardware-partial-read-receipt.json`,
`phase60-hardware-privacy-prefilter.json` и
`phase60-hardware-partial-dispositions.json`.

Whole-file **structure-only** count даёт965 claim IDs,784 immediately
following `src:` excerpts и181 без immediate excerpt. Счёт не означает
полное чтение всего body, true facts или проверку external pages.
«Community-verified» и reactions — metadata подборки.

### Что найдено в прочитанной части

- Rear built-in power button (199–200), отдельный soldered momentary
  switch (89–96), adapter PCB `SWITCH/H1/J1` (495–498) и ESP32 BLE beacon
  controller (159–160) — разные проекты/roles. Совпадение слова
  «power» не создаёт готовый Waveshare HID/wake/standby/PSP controller.
  Source157–160 обещает further features, а не проверяет все gamepads.
- TPMS header short уничтожил standby circuit у одного автора
  (99–100). SCL trace cut, сорванные headers/VRM components и попытки
  работы с платой под heatsink — failure evidence. Никакой probe/cut,
  поднятие ножки, пайка, прогрев или работа без охлаждения не делались.
- LED red-as-short-circuit (51–52) — «almost certainly» от комментатора,
  не схема LED/измерение. Red/green load observations и ASCII CU maps
  не дают единого fault code, fuse map или silicon health. Burn-test для
  принудительного green не запускался.
- LPC18-pin/Pico (299–300), TPMS1, J4003, J4004 и J2000/J2001 упомянуты
  в разных threads. J4004 item (619–620) только направляет к чужой GitHub
  странице, а не содержит проверенный pin-to-pin map/current voltage/
  in-circuit isolation/readback текущей платы. J4003 «fan hub»
  (381–382) задан как вопрос. Никакой connector не отождествлён с
  пользовательским «J004» по созвучию.
- «RAM faster than L3» (35–36), «originally Bitcoin mining» (43–44),
  2×4MB cache excerpt (73–74), backside-only VRAM (97–98) — вопрос,
  предположение или несоответствующая выдержка, не primary measurement.
  Stock24-vs28 CU и RDNA1/RDNA2 descriptions расходятся между posts;
  обозначение в чате не заменяет board-specific ABI/firmware evidence.
- Blanket «sleep unsupported» (305–306,341–342), IOMMU prevents VMs
  (525–526) и universal encoder absence из community posts не
  воспроизведены на версии/плате. Existing project firmware/TOCTOU
  questions открыты. Некоторые boards шли с battery/Optane, другие
  без — seller cases не manufacturer universal configuration.

Source user-facing recipes остались данными. Ни батарейка/jumper/
power/USB, ни пайка/тепло, ни stress/GPU/CU, ни firmware/PSP/BIOS
команды не выполнялись. Current board electrical, wake and controller
acceptance не заявлены. Следующий диапазон **721–810** того же source
по `phase60-root-next-action.json`; три другие selected knowledge paths,
прочий imported corpus, TOCTOU/firmware/privacy/rights, full SAST и
failed independent review остаются открытыми. Native120/176/559 unchanged.

## Knowledge/hardware: полный разбор роли документа и границы доказательств

Завершён разбор роли того же `knowledge/hardware.md`, а не проверка
всех его технических утверждений. Исходник: 408 720 байт, 2729 строк,
SHA-256 `fe40cd0cc90e222bcdc73338dcdd18bb172bfaa521bb2cb6b10632a14d7c28b1`.
К прежнему чтению1–720 добавлены721–1762. Уже выполненные721–1350
сохранены без повторного чтения; потеря вывода восстановлена1302–1307.
Возобновление началось с1351, а не с устаревшего cursor721.
Новые1351–1762 прочитаны пятью ограниченными окнами без потери вывода.

После `# Citations`1763 и пустой1764 идут965 строк1765–2729.
Каждая имеет только ID и URI, ID образуют последовательность1–965,
URI побайтно совпадает со ссылкой соответствующего прочитанного claim.
Это явное повторное использование уже прочитанных полей, не независимое
чтение страниц или первичных сообщений. Все2729 строк учтены только
на уровне роли документа. Точные границы и965 совпадений:
`phase61-hardware-complete-role-read-reconciliation.json`.

Локальный blob pinned commit `1e64c12fd734930e753f95f5b96a47f65647e8b2`
совпадает после нормализации CRLF/LF. Текущий remote не проверялся.
Cloud-share fragment на122 скрыт как `#TOKEN`, не запрошен и не
использован. Начальное раскрытие до расширения prefilter не замалчивается
и не повторяется. Это не общая проверка приватности или прав на публикацию.

### Что важно для проекта управления

- Claim1404 обещает беспроводное включение от Xbox360 через RP2040,
  USB-host и CH444G. Выдержка1405 начинается «I maybe figured out» и
  описывает предполагаемую работу. Это **идея, не подтверждённый запуск**.
  Нет полной прошивки, trace передачи USB-приёмника, проверки питания
  в выключенном состоянии или теста HID/wake. К Waveshare и PSP-подмене
  это нельзя приравнять.
- J4004, TPMS1/LPC/I2C/PMBus и debug headers остаются разными
  источниками/интерфейсами. Canonical/issue labels и ссылки на pinout
  не измеряют напряжение, нумерацию, изоляцию и владение шиной текущей
  платы. Пользовательский «J004» не отождествлён с J4004 по написанию.
  JTAG1604–1605 опирается на «вроде», а M.2 POST-card1520–1521 предложена,
  не показана работающей.
- Отдельный wake-by-button report811–812 не согласован с общими
  заявлениями «sleep/standby невозможно». DualSense/BT/USB и WiFi
  observations1636–1637,1702–1703,1731–1732 не проверяют один контроллер,
  радио, драйвер и надёжность включения в одном setup.
- «Sony блокирует VCN»1477 и «SMU activation не реализована»1753–1754
  не являются доказанной причиной. Windows DriverTest/PSP-Driver
  descriptions, физический BAR address и register-offset recipes
  не воспроизведены на target ABI. Это не готовый Windows driver,
  не подписанная прошивка и не переход к BIOS без внешней платы.

### Несогласованность и качество источника

- LED memory/GPU load, boot/reset и Ethernet-color описывают разные
  диоды или догадки. J2000 voltages1306–1307 не имеют однозначного
  reference/state. Цвет, нагрев и keyboard lights не являются POST trace.
- Q11 replacement1364–1365, Q10 symptom1368–1369 и более ранние варианты
  компонента не определяют замену без схемы и маркировки. Samsung RAM
  identification1100–1101 ссылается на Gemini, не на прочитанный чип.
- PCIe lane, bifurcation/BGA/mux bypass/Oculink discussions смешивают
  предположения, план rework и failed-POST/adapter cases. «Infinity fabric»
  1014–1015 содержит «I thought». Отдельные x2/x8/two-slot descriptions
  нельзя свести в один проверенный device context.
- CU/fuse/RT claims расходятся:12 fused-off,16 harvested,24/26/38/40 CU,
  RT отсутствует либо добавляется. ASCII maps и register values не
  доказывают silicon health или устойчивую обработку всеми блоками.
  Успех одного38-CU случая1757–1758 не универсален.
- Eight-GB board claim1614–1615 извлечён из вопроса о system RAM.
  UCLK=MCLK1530–1531 прямо назван непроверяемым. Третья power rail1721–1722
  только «скорее всего V_SOC», по SMU code неясна. Частота80Hz, fault
  diagnoses и benchmark numbers остаются с их исходными units/context,
  не исправляются догадкой и не становятся нашими измерениями.
- Audio/whitelist, seller BOM/размеры, recovery, обязательный минимум
  охлаждения/PSU и оценки производительности имеют неустановленный либо
  единичный контекст. Question/«вроде»/«может быть» и обрезанная выдержка
  не превращаются в гарантированное свойство платы.

Подробные20 групп замечаний: `phase61-hardware-complete-role-dispositions.json`.
Сохранены оригинальные bytes и предыдущие результаты. Никаких source
commands, CMOS short, замены/поднятия ножки, пайки, прогрева, removal caps,
GPU/CU/MMIO/SMU, power/USB/controller, BIOS/PSP/flash действий не было.

Следующий отдельный source — `knowledge/cooling.md` с первой строки,
по `phase61-root-next-action.json`. USB/overclock, весь остальной импорт,
technical/firmware/TOCTOU/privacy/rights, full SAST и независимый review
остаются открытыми. Native120/176/559 не изменён. Разобрана роль одной
подборки; полный аудит репозитория и проект Waveshare не завершены.

## Knowledge/cooling: первые 1080 строк и пределы проверки

Начат отдельный `knowledge/cooling.md`: 739 993 байта, 4667 строк,
SHA-256 `a7180c24442e901a738697cdf7056ad51aa8bafe09b04f91ae2af367d4f28c96`.
Сохранённый hash/UTF-8 verifier выполнен с exit0. Прочитаны строки
**1–1080** в двенадцати ограниченных окнах без потери вывода.
Первый непрочитанный номер — **1081**. Остаток1081–4667, включая
приложение ссылок, не считается содержательно разобранным.

По пяти privacy patterns совпадений нет. Это только ограниченный
предварительный поиск, не проверка всех чувствительных данных и прав.
Структурный подсчёт всего файла:1602 claim IDs,1448 immediate `src:`
и154 без immediate excerpt. Header «verified facts» и реакции сообщества
не подтверждают эти утверждения. Точные границы чтения:
`phase62-cooling-partial-read-receipt.json`; двадцать групп замечаний:
`phase62-cooling-partial-dispositions.json`.

### Что найдено

- **Резать радиатор не объявлено обязательным.** Есть разные сообщения
  о неизменённом радиаторе с blower/воздуховодом61–62, push-pull103–104,
  двумя вентиляторами451–452 и shroud803–804. Это отдельные сборки,
  не готовый выбор для текущей платы. Cross-flow275–278 ещё ждёт теста
  на радиаторе. Противоречащие «без открытия не охладится»599–600
  сохранены как мнения, не правило.
- Прототип, «попробую», «планирую», «проверю завтра» и ожидание поставки
  неоднократно становятся готовым cooling claim. Особенно253–254:
  два60mm fans «достаточны по математике», но автор только обещает
  stress test. Water-block511–512, PS5 fan537–538, AM4 cooler709–710,
  PETG1045–1046 и laptop pad1059–1060 тоже не показаны прошедшими тест.
- Выход из строя после изменения охлаждения107–108, повреждённые
  радиаторы и предупреждения о стружке/изгибе платы сохранены отдельно.
  Даже cut+P12+repaste687–688 оставляет высокие90s. Успешная фотография
  не доказывает безопасность резки или гарантию хорошей температуры.
- Толщины front1/1.5mm, back2mm, copper0.8mm и presumed0.2gap относятся
  к разной геометрии.49g putty361–362 и30–40g603–604 не общий расход.
  Washers, bending/brace и tower support сопоставлены с предупреждением
  о выдавливании putty677–678 и shims805–806. Не выбирались прокладки,
  проставка, давление, крепёж или torque для текущей платы.
- Fan-header claim95–96 и J4003/FnT/FnP379–380 не измеряют pinout:
  автор прямо «I have not done it myself». PWM tie267–268, fan hub509–510
  и отсутствие voltage-control561–562 не заменяют схему/нагрузку.
  **4.32A/stalled fan killed port351–352 — failure report, не допустимый ток.**
  Blade-one shutdown663–664 выключает чужие fans в одной сборке:
  важная зависимость общего охлаждения, не универсальная схема рига.
- Throttle/safe/max85/90/95°C спорят с reported96/100/102°C и смешивают
  sensors/settings/loads. FurMark «definitive»/«don't worry at100°C»,
  cardboard ignition comparison423–424 и hand-touch447–448 не дают
  ни безопасного порога, ни температуры внутри memory chips.
- Claim311 связывает+104/fan problem с CPU, но excerpt312 говорит о GPU.
  Zero sensor541–542 исходно «скорее всего», не доказательство отсутствия.
  При PSU-powered fan1047–1048 zero tach не значит отсутствие обдува.
  FLIR/thermocouple/source measurements — не наши измерения.
- Gaming low60s claim501 и source502 с literal70f не имеют общей
  установленной единицы. Условное преобразование70F даёт21.111111°C,
  60F —15.555556°C, но намерение автора этим не восстановлено.
  3850Hz/2100Hz569 и200MHz703, как и source2125ghz716, не исправлены
  догадкой. Конкретный conversion-command/stdout в
  `phase62-cooling-inert-unit-conversion.json` не запускал нагрузку.
- Scores/температуры сравнивают разные CU, clock/voltage, API, ambient,
  fan curve и duration. Пока нет matched control/repeated protocol.
  PTM supplier/brand/stock-material claims не проверены; неудача
  PTM743–744 сохранена наряду с положительными отчётами.
- APU, VRM/chipset, backside VRAM и SSD — разные cooling roles.
  96mm mounting claim765–766 и LGA/AM4/AM5 adapters не определяют
  geometry/fit текущей платы. Заявление «memory cooling не нужно»967–968
  содержит99% уверенность, не measurement. Claim1017 имеет показанный
  excerpt про GUI/MangoHud, не доказательство названной VRM цепи.
- PSU cover/grill/fan, liquid-metal/nail-polish, immersion, thermal
  glue и heat sharing с корпусом PSU остались исходными рецептами.
  Protection-shutoff не означает отсутствие перегрева или безопасный
  открытый блок питания. Никакие такие действия не разрешались аудитом.

Оригинальные bytes сохранены. Source commands, fan/USB/power/PSU,
режущие инструменты, пайка, pressure/thermal mods, stress/OC/CU,
BIOS/PSP/firmware и hardware операции не выполнялись.
Следующий диапазон того же source — **1081–1170** по
`phase62-root-next-action.json`. USB/overclock и весь прочий импорт,
technical/firmware/TOCTOU/privacy/rights, full SAST и независимый review
остаются открытыми. Native120/176/559 не изменён. Полный аудит не завершён.

## Knowledge/cooling: продолжение до строки 2160

Продолжен тот же raw source, SHA-256
`a7180c24442e901a738697cdf7056ad51aa8bafe09b04f91ae2af367d4f28c96`.
Прежние1–1080 сохранены. Новые **1081–2160** прочитаны двенадцатью
ограниченными окнами без потери вывода. Всего учтены1–2160, первый
непрочитанный номер — **2161**. Последний claim1143 на2160 ещё ждёт
выдержку2161; его полный контекст не заявлен разобранным.
Остаток2161–4667 и приложение ссылок не закрыты.
Exact-hash/UTF-8 preflight завершился exit0; прежний privacy prefilter
переиспользован только после сверки того же raw hash, не как clearance.
Границы: `phase63-cooling-partial-read-reconciliation.json`.

### Новые различия, которые нельзя потерять

- CFM comparison1101–1102 взят из Google AI, не из измерения.
  Main Bazzite box с2D5/9fans1113–1114 не привязан к BC250. HBM/PTM
  joke1257–1258 и «LOP500/600 — cooler для LOP300»1317–1318 не BOM.
  TPM/PTM9750,12mm fan,1275mhz voltage и400 CPU labels не исправлены
  догадкой и не становятся названиями доказанных компонентов.
- Uncut PS5-fan case1661–1662 имеет индивидуальный stress/обычный-use
  report. Plans1147–1148,1489–1490 и temporary push-pull1363–1364
  отделены от него. Reversible printed shroud1461–1462 — оценка автора,
  не наш проверенный вариант без резки. Частный случай не даёт гарантии.
- **OS shutdown не доказан как снятие питания вентилятора.** На1541–1542
  автор спрашивает о fan running после Bazzite-off и другом результате
  от rear button. На1435–1436 питание fan перепаяно отдельно из-за hum
  в off state. Это разные сборки, без ACPI/standby rail trace.
  PSU power + board PWM/RPM1399–1400,1601–1602 и PS3/Arduino fan1515–1516
  не являются прошивкой Waveshare, gamepad-wake или PSP-substitution.
- J4003 five-channel2.54mm1803 и «two4pin headers»1807 не дают одного
  проверенного connector map.3pin spin/tach1207–1208 не подтверждает
  speed control;3fans на1connector1513–1514 не подтверждает допустимый
  ток. Fan2/pwm2/PumpFan и nct6683/nct6687 остаются version/config claims.
- «Read-only monitoring» не означает read-only setup: приведены host
  config writes, force module load, initramfs, install и service enable.
  Literal1828 tokenizes как `sudo`, `modprobe`, `nct6683`, `force`, `=`,
  `true`; сам modprobe не запускался и его результат не заявлен.
  CoolerControl «should be able»1663–1664 и toolkit proposal2056–2057
  не являются готовой интеграцией.
- В canonical block1753–1889 нет immediate excerpts, только ссылки.
  Страницы/код/datasheets и remote revision не проверялись заново.
  «Canonical» не заменяет primary proof, hardware trace или производителя.
  Особо: P12 Max6.9mmH2O1838 против3.27mmH2O1878; safe CPU95°C1770
  против90°C1871; VRAM1/1.5mm1763 против2mm1782/1790 и «memory/VRM2mm»1881.
  Не сливать разные parts/interfaces/contexts в единый рейтинг или BOM.
- Safe/normal/config/default/TJmax/throttle значения смешаны. Нет
  подтверждённого общего порога85/90/95/100/107°C. «Governor can't
  overheat»1549–1550 и fan-off<60°C1723–1724 не доказаны как safeguards.
  «None we have access to yet»1610 не доказывает отсутствия physical
  sensors или всех desktop safety mechanisms1141–1142.
- PWM80 на1859 не объявлен80%. Только если это uint8 scale, он равен
  31.372549%; фактическая шкала не установлена. Min=max frequency1863
  не доказан как bypass package protections. Curve/hysteresis значения
  1910–1911,1976–1979 не проверены в target runtime.
  Static argv/arithmetic stdout: `phase63-cooling-inert-argv-scale-checks.json`.
- Stock washers1379–1380/1395–1396 могут помочь одному автору, но
  printed brace1405–1410 им мешает. «0.2mm more pressure»2048–2049
  описывает displacement, не силу. Spring gauge/Hooke claim2054–2055,
  slots94.5–96.5mm1986–1987 и block<72mm2136–2137 не измеряют die load,
  board strain, torque, actual fit или creep. Guide pads «from memory»1923
  и непроменённые stock pads2059 не дают нового измерения.
- **Burned cables не исчезают за хорошей температурой.** Claim1545
  «месяцами без overheating» имеет excerpt1546 с burned PSU cables.
  Booster report1416 содержит nearly-melted wiring/380W at wall.
  Unnamed component180/300W1443–1444, declared pump500L/h1305–1306,
  AIO300+W1377 и APU350W1972 — не одна power plane или verified rating.
- Fanless/no-screw heating1617–1618, heatpipe heating/puncture1631–1632,
  live paperclip1418, open PSU1419–1420, mains wires1502, liquid metal,
  coolant/material recipes остались опасными исходными данными.
  Слово «safely» не проверяет процедуру. Packaging «3layers»1335–1336,
  generic brand-conductivity1565–1566 и phase-change lifetime claims
  1595–1596 не заменяют SKU/datasheet/подлинность или electrical isolation.
- «25mV —2°C»1367–1368 исходно «in my case», не закон. Peltier report1653–1654
  «час работало, не умерло» и fin ranking1926–1927 «nothing scientific»
  не endurance test. «Would overheat100+»1681–1682 не измерение этого
  сценария. Ring temperature1199 — не идентифицированный thermal sensor.
  Gaming/API/ambient/CU/load comparisons и thresholds не воспроизведены.
- APU, VRM/chipset, backside VRAM/SSD и QFN5V-standby1934–1935 имеют
  разные roles, не один hotspot. External backplate thermocouple2084–2085
  и tREF/48→52/41–42°C claims2076–2095 не доказывают junction temperature,
  memory correctness или что tREF — единственный heat-relevant setting.
  PTM claim1417 имеет показанную выдержку про live PSU, fan-daisychain1501
  про mains terminals: неполный/неподходящий excerpt не подтверждает claim.

Точные20 групп замечаний: `phase63-cooling-partial-dispositions.json`.
Исходные bytes и ранее завершённые результаты сохранены. Никаких
source install/module/config/service, BIOS/PSP/firmware, fan/PSU/wiring,
pressure/cut/heat/LM, stress/OC/CU или hardware операций не выполнялось.
Следующее чтение того же источника **2161–2250**, с незавершённой выдержки,
по `phase63-root-next-action.json`. USB/overclock и весь остальной import,
firmware/TOCTOU/privacy/rights/SAST/independent review остаются открытыми.
Native120/176/559 не изменён. Это не завершение главы или полного аудита.

## Knowledge/cooling: роль документа разобрана полностью

Дочитан тот же source: 739 993 байта, 4667 строк, SHA-256
`a7180c24442e901a738697cdf7056ad51aa8bafe09b04f91ae2af367d4f28c96`.
Новые **2161–3063** прочитаны ограниченными окнами без потери вывода.
Прежние1–2160 сохранены, pending excerpt1143 прочитан на2161.
Основной текст1–3063 разобран на уровне роли документа.

После header3064 и blank3065 идут1602 чистых ID/URI строки3066–4667.
Каждая проверена полной грамматикой и точным совпадением с inline link
прочитанного claim, ID1–1602 взаимно-однозначны. Это **явное повторное
использование полей**, не чтение первичных страниц, сообщений или media.
Все4667 строк учтены только в этом ограниченном смысле.
Receipt: `phase64-cooling-complete-role-read-reconciliation.json`.

Local pinned Git blob `1e64c12fd734930e753f95f5b96a47f65647e8b2` совпадает
после нормализации CRLF/LF. Raw bytes не изменились, current remote не
проверялся. Header18June2026 имеет46 более поздних claim dates,
последний16August2026; нельзя считать timestamp датой всех записей.
Privacy prefilter reused по exact hash, не общий допуск на публикацию.

### Завершающие замечания

- **Управление вентиляторами не равно готовому контроллеру платы.**
  Corsair Commander Duo с внешними thermocouples/OpenLinkHub2228–2235,
  native fan header, host governor, Linux-temperature client idea2961–2962
  и ссылка на control-center3018–3019 имеют разные роли. Нет независимой
  прошивки Waveshare/gamepad-wake/PSP или проверенного fail-safe.
  «System sensor»2230–2231 имеет неизвестное расположение; hear-based
  fan-power-starvation2232–2233 не измеряет напряжение или fault cause.
- Detect pin J4003 «pulled to ground»2364–2365 заканчивается вопросом,
  что делает сама BC250. Grounding procedure не принята. Splitters,
  parallel tach2709–2710, pump/two-fans2627–2628 и25W fan2963–2964
  не устанавливают допустимый ток/распиновку/startup. Автор2628 прямо
  не знает power capacity. Inverted PWM2895–2896 и bent pump pin2976–2977
  не универсальны. OS individual-fan claim3050 не подтверждён excerpt3051,
  где сказано только об общей настройке BIOS.
- No-cut и no-change — разные вещи. Uncut three-fan2164–2165 имеет
  сомнение в contact/LM; tail-server-fan2717–2718 — отдельный report.
  Opening/bending without cutting2893–2894 всё равно меняет радиатор.
  Passive40min BIOS3042–3043 имеет отдельный fan на другом chip и не
  доказывает passive whole-board cooling или игровой режим.
- Good temps не дают stability guarantee. AIO hard-lockups2318–2319,
  low40–50°C crash2392–2393 и cold Doom issue2797–2798 сохранены.
  Gemini suggested VRM overheating2551 — model advice, не fault trace.
  Fan green-transition claim2428 не совпадает с excerpt2429, где автор
  ожидает fan уже при первом red LED. CPU protection2430–2431 сопровождается
  «I think», а не воспроизведением механизма.
- Claim «heatsink non-conductive»2402–2403 не electrical-isolation proof.
  «Conductive glue»2753–2754, insulation cuts2996–2999, backplate/PSU
  drilling2655–2656, disconnect PSU fan2781–2782, foam insulation2899–2900,
  fanless/bare-die heating и pressure/LM/coolant рецепты не approved designs.
  Q11 ripped by shroud2512–2515 и possible NVMe component loss2374–2375
  отмечены как failure evidence. «Обратимый shroud» не означает отсутствие
  механического риска при установке.
- Нулевой benefit PTM/UTP-8 повторной установки2276–2277 и stronger springs
  без улучшения2244–2245 сохранены рядом с обещаниями pressure/temperature.
  Sizes1/1.25/1.5/2/2.15/2.5/3mm смешивают interfaces/revisions/compression.
  «Two revisions(kind of)»2305, doubled/flattened pads, wrong washer side2501
  и burned/no-image cases не разрешают выбрать один universal BOM.
  Finger tight+eighth turn2432–2433 — не измеренный torque или force.
- PSU fan startup2496–2499, board PWM, PS3 negative adapter assertion2677–2678
  и RTX8pin failed hookup2967–2970 — разные circuits. «Все GPU fans как
  обычные»2887–2888 не подтверждено. Из3300rpm at100% не следует calibration
  1500rpm=50%3058–3059. THM_BASE offset2615 — imported repo claim, не ABI/
  MMIO read или доказательство physical sensor access текущей платы.
- Укороченные excerpts добавляют specificity: JF13K2991 — только название,
  54°C2993 — только температура «в стрессе», «тока240»2995 — без protocol.
  NC1002898 и Meanwell2762 заданы как вопросы. Mini-heatsink claim3028
  содержит item IDs, которых нет в показанной выдержке3029. 5090 «не подойдёт»
  3007 и custom plate3046–3049 — разные contexts, без универсального fit.
  CAD-cross3034–3037 и15×25mm3038–3039 не измерялись по actual target/model.
- 2.2mm²H2O2738,960V2848 и36cpu2983 остались с unit/context uncertainty.
  Toy model2791–2792 проверен только арифметикой: h7×ΔT35=245W/m²,
  +radiation15/225 дают260/470W/m² и44.680851% меньшую площадь при тех же
  assumptions. Это не измеренная emissivity/heat-transfer curve и не
  доказательство passive cooling. Literal stdout в
  `phase64-cooling-inert-model-arithmetic.json`.
- Temperature/FPS/voltage/CU/CPU-core/API/ambient/duration, acoustic phone-app
  и datasheet-like ratings остаются отдельными claims. Thermal/power planes,
  chip junction/backplate thermocouple и safe/recommended/config/TJmax limits
  не смешаны. «240/280AIO обязательно», «100%stable» или «fan tolerates»
  не воспроизведены на этой плате. Нельзя пропускать copper/insulation/fan
  safety controls ради красивого числа или чужой успешной фотографии.

Полные границы, исходные различия и завершающие14 групп:
`phase64-cooling-complete-role-dispositions.json`. Ранние Phase62/63
замечания retained, не заменены. Никаких imported recipes, installs,
module/service/config, fan/pump/PSU/pin/wiring, cut/pressure/heat/material,
stress/OC/CU, BIOS/PSP/firmware или hardware операций не выполнялось.

Далее отдельный `knowledge/usb.md` с первой строки по
`phase64-root-next-action.json`, затем оставшийся overclock и весь прочий
импорт. Technical/firmware/TOCTOU/privacy/rights/full SAST/independent review
не закрыты. Native120/176/559 не изменён. Закрыта роль одной подборки,
не весь импорт и не hardware/firmware acceptance.

## Knowledge/usb: роль документа разобрана полностью

Прочитан отдельный `knowledge/usb.md` (USB & storage): 40 439 байт,
272 строки, SHA-256
`34b6b89814a775a128693a296109f76e236902d04d87544a13e37ede6561c78b`.
Весь файл прочитан ограниченными окнами1–90,91–180,181–272 без потери
вывода. Body1–178, header179/blank180 и92 appendix rows181–272 учтены.
Последние92 строки здесь **прочитаны полностью**, не только reused:
дополнительно проверены pure ID/URI grammar и точное соответствие
inline links, ID1–92 взаимно-однозначны.
Receipt: `phase65-usb-complete-role-read-reconciliation.json`.

Hash/UTF-8 verifier exit0. Raw bytes сохранены; pinned Git
`1e64c12fd734930e753f95f5b96a47f65647e8b2` совпадает после CRLF/LF
нормализации. Prefilter без совпадений по пяти patterns не означает
privacy/rights clearance. Header18June2026 имеет один поздний claim,
3August2026. Current remote/primary pages/media не проверялись.
92 «verified facts»/реакции — labels,19 claims без immediate excerpt.

### Различия, важные для управляющего проекта

- **USB device не равен автономному USB host/controller.** Pico audio
  S/PDIF firmware23–24, front hub+button17–18, USB3pin fan65–66 и
  JAMMA/Brooks boards149–150 — разные роли. В показанном Pico excerpt
  нет воспроизведённого BC250/CachyOS test, firmware hash или полного
  gamepad-wake/mux/standby/PSP проекта. Ничего из этого не установлено.
- Power after early boot59–60, shutdown/S5/button/reboot93–96,170–173
  и voltage/current reports не дают одной таблицы VBUS для текущей платы.
  Claim79 «5V active after off» имеет excerpt80 про optocoupler/relay;
  claim127 supply switch относится к **modified True ATX** guide.
  Display2A/500mA61–62 и ports4.3/3.5V139–140 не имеют нашего bound load,
  rail/reference/state measurement. Powered hub «нужен всегда»67–68 и
  blanket poor-voltage43–44 остаются source assertions, не наш verdict.
- Front hub power/data claim53 расходится с excerpt54: **power отдельно**.
  Self-powered hub не равен hub с порезанным VBUS и injected ATX5V75–76/141–142.
  Color/black-ground/5.2V limits33–34 и omitted ground при commonATX76
  не подтверждают pinout, isolation/backfeed/current safety.
  NC100 adapter GND→5V short85–86 сохранён как failure report.
  Никакой cable, VBUS cut/injection или external supply не подключались.
- RF interference, low VBUS, broken port, thicker dongle, driver и
  second-device conflict125–126 — разные hypotheses/conditions.
  Bluetooth adapter starts26 не гарантирует wake from off; hub/extender
  не универсальное лечение и не гарантированная совместимость геймпадов.
  Dark keyboard lights не POST/PSP trace. Claim151 имеет correction152:
  WiFi+Bluetooth **в купленном адаптере**, не штатный Bluetooth платы.
- USB DAC, Pico audio, USB Bluetooth, DisplayLink и DP-altmode не
  взаимозаменяемы. DisplayLink47–48 «could try/even if/drivers» не
  подтверждает готовый multi-display или native DP transport. $10audio
  adapter147–148 задан как вопрос, не solved result. Swapped channels
  162–163 и DP popping/stuttering69–70 сохранены с device/driver uncertainty.

### Storage, команды и качество данных

- USB SSD/HDD/microSD success и failure относятся к разным bridge/OS/
  filesystem/port/workloads. «Only one correct boot port»143–144 основан
  на попытках2maybe3из4, не полной port map. PNY exFAT/FAT32 failure27–28
  не разрешает форматировать диски как универсальную repair. Successful
  external NVMe boot137–138 не доказывает исправность M.2 slot/current board.
- USB3.0 «около1GB/s»101 не согласован с5Gbps47 и mixed USB3.1/PS5
  BIOS inference117–120/one10Gbps port174. Если literal5Gbps, raw ceiling
  **625MB/s до overhead**, а не1GB/s; для10Gbps —1250MB/s. Реальный mode,
  bus tree, controller и rates не измерены.1.96Gbps82 =245MB/s только
  decimal arithmetic, не наш network test.311 units134 в excerpt не
  указаны;30MB/s write168–169 не bus rating и не портовая неисправность.
- FAT32 flashing medium97–100/111,4/8GB installer106–110 и Ventoy129–132
  имеют разные roles. Literal destructive command108 распадается на
  `if`, `=`, filename, `of`, `=`, path и другие отдельные tokens;
  assignment-form source132 иной. Выполнен только **shlex разбор текста**,
  не `dd`, не format и не flash. Literal argv/stdout и conditional
  speed math: `phase65-usb-inert-argv-metric-checks.json`.
- Canonical19 без immediate excerpts, USB counts105, AIC MassStorage/
  usbcore/VID-PID descriptor155–157 и OpenCore/kernel158–161 не проверяют
  current hardware, driver ABI или official firmware support. Suggestion,
  question, «in theory», «almost» и обрезанный snippet не фактическая
  гарантия. Первичные URI и содержимое страниц не fetched.

Подробные13 групп: `phase65-usb-complete-role-dispositions.json`.
Оригинал и предыдущие результаты сохранены. Никаких source commands,
USB pairing/reset/tethering/port writes, driver/install/module/service,
disk/format/recovery/PSU/VBUS/solder, audio/network workloads, BIOS/PSP/
firmware или hardware действий не было.

Далее оставшийся selected `knowledge/overclock.md` с первой строки
по `phase65-root-next-action.json`, затем весь остальной оригинальный
импорт. Firmware/TOCTOU/privacy/rights/full SAST/independent review не
закрыты. Native120/176/559 не изменён. Полный аудит и прошивка Waveshare
не завершены; документ-роль не hardware acceptance.

## Knowledge/overclock: первые 1080 строк и пределы проверки

Начат отдельный `knowledge/overclock.md`: 584 998 байт, 3664 строки,
SHA-256 `d0f7e35969448ce26d30646e188a92eb17c82befae75730a614a098f23a1176a`.
Hash/UTF-8 verifier реально завершился exit0. Прочитаны **1–1080**
двенадцатью ограниченными окнами без потери вывода. Первый непрочитанный
номер — **1081**. Остаток1081–3664 и bibliography не заявлены прочитанными.
Prefilter по шести patterns и полный private-key-block guard совпадений
не дали, это не privacy clearance. Whole-file1268claim/1113immediateSrc/
155withoutSrc — структура, не полная семантическая или technical проверка.
Receipt: `phase66-overclock-partial-read-receipt.json`.

### Что найдено в прочитанной части

- **FurMark/короткий benchmark pass не означает стабильность.** Source995–996
  прошёл FurMark1h+, но hardlocked сразу в CS2;1001–1002 прошёл CPUstress,
  а потом упал в idle.12h run653–654 прямо ещё ждёт game validation.
  Автор969–970 сначала не видел проблем при2100@925, на973–974 нашёл
  subtle white dots. These negative outcomes не замещены словом «stable».
- «All chips stable2000@1000»832/903 и «на mine нельзя ниже1050»529–530
  не одно evidence class. Recommendations1250→1275 идут назад после
  hardlock reports1047–1066. Board-specific clock/voltage/CU/temperature
  tables не выбраны как наши safe points и не применены к плате.
- Tool detect/setup и persistence раздельны: source123–124 прошёл detect,
  установил overclock.conf и потерял OS boot. RAM+150380 не восстановился
  CMOS reset;1950/reflash665–666 и bricked761–762 противоречат простому
  «легко исправить, ведь не BIOS»575–576. GRUBmask215–216 **не тестировался**
  и требует доступного GRUB/правильного unit; recovery guarantee не принят.
  Runtime request, service-at-boot и permanent BIOS — разные состояния.
- Kernel OD_RANGE1000–2000, patch350–2230, GPUhardcoded350–2350 и reports
  2530–2575 — разные interfaces/versions, не один physical limit.
  SMU tool меняет конфигурацию, выбор per-core clock остаётся SMU1063–1064.
  Sysfs/table/UI/telemetry read не доказывает actual rail/clock under load.
  «MCLK inverted450→1750»159–160, UCLK/MMCLK741–744 и disabled-core
  frequencies305–306 требуют code/measurement context, не CPU-core unlock.
- CPUcap1325mV163–164 **software limit**, editable697–698, не manufacturer
  rating.1.4/1.475V reports и potentially destructive4.2GHz636 сохранены.
  OCP «exact1200/1500mV»507–508 смешивает voltage и current/protection;
  1195mV/shuntmod487–488 не разрешение менять safeguard. «No danger»,
  «absolutely safe» и prescribed minimum/max не подтверждены hardware.
- Good temps не подтверждают harness safety.340W12V99–100,410Wwall345–346,
  352Wmax1077–1078 и GPU140–150W451–452 — разные power planes/loads.
  Near-melting cables186, wire hand-touch133 и extra connector593–594
  не certified current/ground/pinout/recovery. Extended-voltage patch659–660
  прямо «DON'T USE THIS»; source shunt/sysfs/restart/install/kernel/mitigation
  recipes остались данными, не действиями этого аудита.
- MoreCU/free performance, pair-disable live/AI/full-access stories и
  clean ASCII maps не proof healthy silicon.40enable/38usable103–104,
  last-pair artifacts405–408 и noSSH/noimage/fans-spinning799–800 сохранены.
  Подмена PSP, USB-gamepad/wake, flashing/firmware behavior отсюда не следуют.
- Memory timing/UMA/refresh sets119–120,663–680 не названы validated BOM
  или TOML только по виду. Leading-zero INI-like поля retained.1875max-safe
  595–596,1950stable671–672 и1950bricked665 — разные reports. «3400memory»611
  не имеет shown device/domain context. Exact BIOS/driver/clock aliases и
  memory correctness/reliability не проверены. DefaultVID/OD_VDDC824/837/
  918mV и board numbers — tool/source metadata, не ADC/healthy-bin proof.
- «25mV fixes», global voltage step6mV, default700minimum против680report965,
  absolute-safe bounds1025/1075/1085/1100/1129/1150 и warning «all boards»
  не образуют единой safe table. Green/black/artifacts/freeze могут иметь
  CPU/GPU/RAM/power/thermal/driver/display context; cable correction706
  не диаграмма причин. Suggested increase/reduce recipe не diagnosis.
- Цена/battery/efficiency claims не переведены в измерения.65Wh/30min65–66
  условно дают **130W ideal average**, не батарейный тест. Report129→172FPS37
  даёт33.333333%, CU24→40 даёт66.666667%, но clock тоже изменился:
  линейный CU speedup отсюда не следует. W/fps и points/W разные metrics.
  «No power meter»188 и software-vs-wall276 сохранены; heat/drop in voltage
  не measured watts. FSR/LSFG/caps, presets, duty/load duration — не контроль.
- Header «verified» не подтверждает facts. Preparing3550 heading71–72,
  rumoredBIOS217–218, addingGUI55–56, havn'ttested216 и question814
  не completed build/result. «Auto-tuned voltage»906 явно содержит `-v1231`.
  SMU/governor/Qt/OS/package labels не отождествлены с firmware bypass.
  Canonical block825–942 содержит118 ссылочных claims без immediate
  excerpts; primary pages/code/config versions не fetched/verified.
- **Literal команды895/900 потеряли redirection.** В shlex result путь
  к `pp_od_clk_voltage` — обычный argument `echo`, нет `>`/pipe/tee.
  Здесь выполнен только parse, не source echo или sysfs write.
  Literal stdout и conditional metric math:
  `phase66-overclock-inert-command-metric-checks.json`.
  Flock update349–350 — cooperative transport claim, не доказанная защита
  от всех concurrent writers/firmware accesses. Bazzite/script/service/kernel
  recipes не установлены, source file instructions не стали нашими задачами.
- 850V/1150V/940v,50Hz boost step,4000hz/2500hz,25mA voltage increment,
  2230mv clock и CPU2300MHz labels оставлены с unit/domain uncertainty,
  не исправлены догадкой и не выданы как безопасные параметры.

Подробные15 групп: `phase66-overclock-partial-dispositions.json`.
Исходные bytes и предыдущие завершённые результаты сохранены. Никаких
source commands, service/install/kernel/sysfs/SMU/CU/voltage/clock/memory,
benchmark/game/load, mitigations/PSU/shunt/solder/reset/BIOS/PSP/firmware
или hardware операций не было. Следующий диапазон того же источника
**1081–1170** по `phase66-root-next-action.json`. Весь остальной оригинальный
импорт/technical/firmware/TOCTOU/privacy/rights/full SAST/independent review
остаётся открытым. Native120/176/559 не изменён, полный аудит не завершён.

## Knowledge/overclock: роль документа разобрана полностью

Дочитан отдельный `knowledge/overclock.md` (584 998 байт,3664 строки,
SHA-256 `d0f7e35969448ce26d30646e188a92eb17c82befae75730a614a098f23a1176a`).
К прежним1–1080 добавлены**1081–2394** в ограниченных окнах без потери
вывода. Body1–2394 теперь полностью разобран по роли.
После `# Citations`2395 и blank2396 идут1268 pure ID/URI rows2397–3664:
каждый ID и URI строго/взаимно-однозначно совпадает с inline claim link.
Это точное повторное использование прочитанных полей, не чтение
первичных страниц/сообщений/media. Все3664 строки учтены только на
уровне роли документа. Receipt:
`phase67-overclock-complete-role-read-reconciliation.json`.

Exact raw hash/UTF-8 сохранён. Local pinned Git
`1e64c12fd734930e753f95f5b96a47f65647e8b2` совпадает после CRLF/LF
нормализации. Текущий remote не проверен. Header18June2026 имеет35
более поздних claim dates/latest14August2026. Повторный prefilter
по тому же hash не clearance приватности/прав.

### Новые критические разграничения

- **Принудительное SMU-задание GPU не является безопасным продолжением
  обычного governor.** Источник1197–1200,1229–1230 прямо предупреждает:
  bypass temperature/current throttles. Его код/пределы не запускались,
  и заявление о всех bypass-эффектах тоже не подтверждено на плате.
  Kernel/sysfs, SMU backend, script/API и отображение clock — разные
  пути. Hardcoded2350 vs >2500 reports остались версия-зависимыми.
- CPU scale/VID formula1241/2343 — напечатанная approximation для clock>=3000,
  не заводская calibration. Только символическая производная по scale:
  5.1375mV за единицу при3500 и7.3mV при4000 по этой формуле;
  voltage/SMU readback не делались. Literal `--temp -95/-90`1168/1174
  сохранён как отрицательный argument. Не подменять положительным числом
  или действительной безопасной температурой без проверки parser.
  Точные inert argv/stdout: `phase67-overclock-inert-argv-formula-checks.json`.
- Memory>1875 bricked/CMOS/reflash у одного автора1090/1513 и V3/1975
  против V5/non-POST у него же1519–1520 — разные board/BIOS/method
  contexts; «в V5 отсутствует watchdog» остаётся предположением, не
  проверенным firmware механиз­мом. Default Phoronix locks even stock1470,
  потому не годится как однозначный тест timing regression.
  tREF/TRFC confusion1270 и название1875 при `ClockSpeed=1850`1497–1498
  retained, не исправлены догадкой. ECC/perf/temperature из single score
  и backplate sensor не выводятся. «Переход на profile назад»1553 не
  восстановил booted performance у автора, поэтому reversal не обещается.
- Benchmarks/idle/cold boot/composite load — разные acceptance gates.
  Source1373–1374 выдержал пять часов burn, затем green в idle;
  source1747–1750 прошёл FurMark+Superposition после прогрева, но падал
  на cold boot. Source2258–2259 прошёл три часа OCCT, browser tabs дали green.
  RAM warm reboot1095–1096 и games после Superposition1795–1798/1823–1824
  отдельно. `bc250-detect` stress1295–1296 может сохранить настройку,
  вызывающую crash через пять секунд. Никакие параметры не названы
  универсально стабильными по одному тесту.
- 40CU/38CU GPU and extra2CPU cores — разные unlocks. Source2308–2309
  говорит «все healthy» в тесте, но один CU row даёт артефакты.
  `cu_map.sh` может не отражать runtime enable2161–2163. New CPU8C16T
  single-source Geekbench/7Zip/OCCT claims2351–2358/2377–2394 не
  про GPU dispatch, hardware fuse health или PSP signing.
- Reported power planes не сливаются: GPU telemetry, CPU/SMU watt,
  wall,12V rail, PSU label и cable temperature. Burning smell2051–2052,
  melted8pin1907–1908 и hardlock с неработающими кнопками1841–1842
  сохранены. Low temperature не сертифицирует connector/провода.
  Suggested voltage/shunt/cap/SMU/OC/thermal limit/PSU wiring edits
  не выполнялись и не приняты как проектный safeguard.
- «All boards», «nothing breaks», «safe at...», CPU/VRM OCP exactmV,
  config/restart recovery и фиксированные 2000/1000 defaults имеют
  противоречащие single-board reports. Lowering load-target решило
  downclocking, но **не дало FPS gain**2095–2096, значит reported
  clock не равно производительности. CPU+GPU race/load/ACPI/Bazzite fork
  и idle behaviour требуют version-specific trace, не универсального рецепта.
- Source усиливает snippet: Q/A, could/suspect/appears/untested,
  truncated logs и service/issue URLs становятся категоричными фактами.
  Например claim2333 «utility manages via successful UMR» показан
  рядом с error `Failed to read ...`. Claim1567 «stable profile» связан
  с вопросом про DP failure. Claim2352 initial benchmarks отсутствовали,
  более поздние claim results требуют отдельной проверки.
- 0.960mV,4000GHz,850v,2000ghz,0.05mv/5mV-for-frequency и другие
  units/context сохранены, не подменены безопасными MHz/mV значениями.
  Stated software max1325mV/thermal-limit setting не измеренные физические
  пределы. Нет актуального показания этой платы, ROM signature/boot trace
  или проверенного recovery от PSP-подмены в этом источнике.

Шесть выбранных `knowledge` глав — bios/power/hardware/cooling/usb/
overclock — сверены **только по роли документа** с сохранёнными receipts:
`phase67-six-knowledge-role-packet-reconciliation.json`. Это не весь
import, не primary source/firmware/board acceptance. Следующие Arabic
chapter paths выбраны **по metadata** и старым physical-routing receipts
«UTF-8 decode only», не названы прочитанными: `phase67-next-source-selection-metadata.json`.

Подробные15 завершающих групп:
`phase67-overclock-complete-role-dispositions.json` плюс прежние15
групп Phase66. Оригинальные bytes и прежние итоги сохранены. Ни один
source command, service/install/rebase/kernel/sysfs/SMU/perf-profile/CU,
clock/voltage/timing/thermal-limit/load/PSU/shunt/firmware/hardware шаг
не выполнялся. Дальше первый Arabic chapter from1 по
`phase67-root-next-action.json`, остальные локализованные/технические/
firmware/private/opaque записи и full SAST/TOCTOU/privacy/rights/
independent review остаются открытыми. Native120/176/559 unchanged.

## Arabic start-here: роль документа разобрана

Прочитана отдельная Arabic `docs/ar/00-start-here.md`: 13 987 байт,
143 строки, SHA-256
`a8138a85c5c8863a2a38b4d93fcfc1155769c8781c4a6e890da3fac256eed1d6`.
Saved hash/UTF-8 verifier exit0. Строки1–90 и91–143 прочитаны полностью
без renderer loss. Privacy prefilter6patterns/private-key block не дал
совпадений; это не global clearance.27 локальных relative link occurrences
разрешаются на существующие файлы, **но их body не подменяет чтение этой
главы и не делает linked claims проверенными**. Raw bytes сохранены;
local pinned Git `1e64c12fd734930e753f95f5b96a47f65647e8b2`
совпадает после CRLF/LF. Remote issue и primary pages не fetched.
Точный receipt: `phase68-arabic-start-complete-role-read-reconciliation.json`.

### Навигация и границы

- Первая строка сама называет главу «community translation» и отсылает
  к English как возможной более свежей. Physical routing Phase33
  классифицировал эту запись как historical-document / UTF-8 decode only,
  **не semantic review**. English/Arabic cross-links проверены на
  существование, не использованы для подтверждения её частных claims.
- «Из коробки до игры», Mermaid flow и60-second checklist — маршрут
  автора, не state trace пользовательской платы. Текст рекомендует
  PCIe8pin12V/~235W, 120mm fan/shroud, DP, Bazzite, firmware symlink,
  governor~2000MHz, WiFi dongle и game. Ни один пункт здесь не был
  физически выполнен и не доказан для текущего BIOS/revision/harness.
- Cooling в главе формулирует резку/разгибание ламелей и FurMark<80°C
  почти как обязательные условия. Уже разобранная cooling-подборка
  содержит отдельные no-cut duct/stock-finstack reports и damage cases.
  Ни одна сборка не сертифицирована для этой платы; разрезать радиатор
  из этого текста не следует. «Fan spinning+picture=POST»58 не
  заменяет PSP/UEFI/OS stage capture или SPI readback.
- No Windows GPU/VCN encoder, HDMI-black, IOMMU broken, ROCm dead end,
  exact Mesa/kernel blacklist и `aic8800d80` preference — dated or
  environment-specific source assertions. Нельзя превратить их в
  свойства текущей платы/драйвера без version, primary bytes и runtime
  evidence. `vainfo`/`dmesg` alone не доказывают игровой GPU/VCN.
- **Risky next steps are only quoted content:** cut/sand, PSU pinout,
  BIOS VRAM/CMOS, IOMMU disable, `nomodeset`/grub/rpm-ostree, COPR/dnf,
  service enable/reboot, config/governor/OC и `RADV_DEBUG=nohiz`.
  Они не были запущены, не стали workflow и не являются одобрением
  hardware/firmware change. `2000MHz≈+30%FPS` без game/preset/baseline
  не принят как benchmark. Static6/10GB VRAM workaround for two games
  не generic crash/PSP fix. BIOS mod на91 прямо назван non-starter и
  требует отдельного recovery; full image/target approval отсутствует.
- Pico/USB/wake/PSP controller, gamepad support и J004/J4004 connector
  не выводятся из этой introductory главы. В ней нет firmware/USB host
  implementation или подписи, которую можно подменить.

Подробные10 source-role групп:
`phase68-arabic-start-complete-role-dispositions.json`. Ни Mermaid/
source shell, ни PSU/USB/driver/game/CU/OC/BIOS/PSP/hardware действия
не выполнялись. Следующая отдельная Arabic power глава по
`phase68-root-next-action.json`, затем Arabic BIOS/OC и весь остальной
импорт. Technical/TOCTOU/privacy/rights/full SAST/independent review
не закрыты. Native120/176/559 unchanged.

## Arabic power-supply: роль документа разобрана

Прочитана отдельная Arabic `docs/ar/03-power-supply.md`: 64 764 байта,
402 строки, SHA-256
`cb0487b2a53899d9218ed38c808dc1be65510b6d86d2c7e5fb64d20d5e9d7fdc`.
Saved hash/UTF-8 verifier exit0. Пять ограниченных окон1–90,
91–180,181–270,271–360,361–402 прочитаны без renderer loss.
Шесть privacy patterns/private-key block не дали совпадений, не clearance.
Пять относительных file references существуют, но anchors, linked bodies,
public pages, video и datasheets не проверены. Raw bytes сохранены,
local pinned Git `1e64c12fd734930e753f95f5b96a47f65647e8b2` совпал
после CRLF/LF. Receipt:
`phase69-arabic-power-complete-role-read-reconciliation.json`.
Community translation на первой строке считает English первичным и
возможно более свежим; перевод не разрешает электрических действий.

### Критические противоречия

- **Сам документ конфликтует по разъёму.** Строки62–68 предупреждают,
  что PCIe8pin и CPU/EPS8pin имеют разную полярность и смешение может
  повредить плату. Строка86 разрешает формулировкой «PCIe8-pin / EPS»
  оба класса. Нельзя выбирать кабель по этому переводу. Обещание, что
  внешний ATX кабель «гарантированно» имеет правильную полярность,
  не является измерением J1000/current board.
- Абсолютное «нет кнопки и плата всегда запускается от12V»5/16 не
  согласовано с `AUTO_PWRON`255, PWR_SW/relay222 и самим разделом
  PS_ON/кнопок250–288. Earlier hardware collection имеет rear-button
  report. Board button, PSU switch, auto-power jumper, OS shutdown,
  5VSB и полностью снятое AC — разные состояния, не один проверенный
  power-cycle transition для Waveshare.
- Арифметика не равна электрическому рейтингу. `235/12=19.583333 A`,
  `3×9×12=324 W` условны. Clamp report17A→204W, а глава пишет≈190W;
  21A→252W против≈240–250W. Значения могут быть округлёнными/из разных
  условий, но точная calibration, reference и raw video не проверены.
  GST280→«252W usable» не выводится из одного nameplate: разница28W
  никак не объяснена. `CPU-X`/wall/12V rail/PSU rating — разные planes.
- J2000+J2001 имеют **6** позиций12V по показанной схеме, **9** только
  вместе с J1000. «Подай питание и на J2000, разделив тот же PCIe cable»
  166 не добавляет независимый upstream cable/current capacity. Parallel
  feed не гарантирует равного тока по контактам; автор192 сам это
  оговаривает. PGD/LED, J2000/J2001 orientation, Molex Micro-Fit BMI/
  3.0/JST и quoted part numbers не проверены на текущем board revision.
- 16AWG как минимум5/96/175/372, но Micro-Fit section178 называет
  18AWG recommended/20AWG acceptable, а40CU example190 использует18AWG.
  Это разные wire/branch/load claims, не universal безопасная BOM.
  Magnet test78 может выявить ферромагнитную сердцевину, не подтверждает
  полную медь/CCA, сопротивление, состояние кримпа и нагрев контакта.
- GST280A12-C6P с заводским6pin +8pin180adapter323/335 назван
  «единственный без проводки», но таблица210/246 даёт штатный ATX
  8pin без доработки. Ни точная распиновка адаптера, ни 6pin contact
  rating/current/temp под BC250 не квалифицированы. Нельзя превращать
  рекламу «без пайки» в разрешение питать плату этим переходником.

### Что документ даёт только как направления исследования

- ESP32 BLE/Xbox/PWR_SW/accessory relay222, CH32V003259,
  mosfet.party adapter263–290 и modified-ATX iamdarkyoshi292–308 —
  **разные проекты**. Здесь нет проверенной прошивки Waveshare, USB host
  для геймпадов, надёжного wake/power state или PSP SPI handoff.
  `system_on` с fan header,3sec delay,5VSB и GPIO labels не проверены
  voltage/direction/fail-safe/current-board trace. «Без пайки»272 не
  распространяется на PCB LITE279, BTN_OUT288 или physical modification306.
- HP server bridge/resistor216–218, open Mean Well terminals230–232,
  paperclip PS_ON246, wire cutting257, PSU fan rewiring258, connector
  shaving179, crimp/solder181, backplate/inductor modification306,
  direct PCB solder354 — source recipes, **не действия**. 24V caution
  важен как риск, но не означает проверенный board input-protection map.
  PSU/seller/geographic/price/fan-noise/nameplate claims датированы и
  должны проверяться по точной модели и текущей схеме, не по реакции чата.
- Таблицы «выбери PSU» и строения с фото — examples, не pinout/readback/
  cold boot/EMI/overcurrent measurements. Частное сообщение VS450
  overheat355 не доказывает универсально «multi rail is bad».
  Приведённые URL и библиография376–400 — provenance pointers,
  не независимое подтверждение текста.

Подробные13 групп: `phase69-arabic-power-complete-role-dispositions.json`.
Оригинал, прежние receipts и чужие workspace drifts сохранены.
Никаких source PSU/relay/PS_ON/мультиметр/wiring/crimp/solder/fan/
cut/mains/firmware/hardware действий не выполнялось.
Далее отдельная Arabic BIOS глава с первой строки по
`phase69-root-next-action.json`, затем Arabic OC и весь оставшийся
import/firmware/TOCTOU/privacy/rights/SAST/independent review.
Native120/176/559 не изменён; общий аудит и Waveshare дизайн открыты.

## Arabic BIOS: роль документа разобрана

Прочитана отдельная Arabic `docs/ar/08-bios.md`: 46 255 байт,
409 строк, SHA-256
`528a128ce59a29ca3f23ead23092c5b23d01645f0bef4b945a30677cc00ab050`.
Saved hash/UTF-8 verifier exit0. Окна1–90,91–180,181–270,
271–360,361–409 прочитаны полностью без renderer loss. Prefilter
по6 patterns/private-key block без совпадений, не clearance.
11 локальных relative references указывают на существующие файлы,
но linked bodies/anchors/public pages/video/datasheets не проверены.
Raw bytes сохранены, local pinned Git
`1e64c12fd734930e753f95f5b96a47f65647e8b2` совпал после CRLF/LF.
Receipt: `phase70-arabic-bios-complete-role-read-reconciliation.json`.
Первая строка называет главу community translation и предупреждает,
что английская версия может быть новее.

### Что найдено

- **«J4004 — единственный надёжный способ восстановления» и
  «SOIC-прищепка не работает» — утверждения источника, не gate для нашей
  платы.** На183 цитата фактически «почти не работает», а не «никогда».
  Пользователь ранее сообщил, что уже прошивал через своё F1-соединение;
  перевод не опровергает этот опыт, но и не квалифицирует независимый
  recovery. Нужны exact image/target, полный verified dump, отдельный
  recovery path и план coldboot/readback до любого физического flash.
- Нарисованный J4004 2×4 содержит семь подписанных/один пустой контакт,
  а numbering1–8/резисторы10k на207 взяты из другой ссылки. Orientation,
  реальные VCC/GND/CS/SCLK/MISO/MOSI, bus ownership и питание платы
  здесь не измерены. 16MiB BIOS против512KiB SuperIO важно различать,
  но auto-detect/capacity/суффикс маркировки не доказывают, что кабель
  подключён к `BIOS_A1`; part `MX25L4005` на244 и `MX25L4006E` в
  table327 тоже не совпадают. Никакого programmer connection не было.
- **Хеш ≠ доказательство нужной прошивки.** Таблица104–108 содержит
  заявленные SHA-256 исторических имён, но не проверена по ROM bytes
  текущего imported source. Prefix16hex на98 слабее full digest.
  Две копии одного `P5.00_clv` с равным hash без независимой provenance
  не подтверждают официальный origin. Сам текст49 говорит «нет public
  hash»; на377 перечисляет mirror ZIP без проверенной ROM identity.
  В `assets/firmware/` **именно этого импортного репозитория** фактически
  есть только `DISCLAIMER.md`; указанных ROM/ZIP/tar файлов там нет.
  Это не утверждение, что образов нет в остальных папках проекта.
  Формула «все известные BIOS-файлы ровно16MiB» на100 не относится
  автоматически к ZIP-архивам и инструментам в списке377–384.
- Software AFU `/P /N` меняет NVRAM, а `flashrom internal:boardmismatch=force`
  обходит предупреждение. `Flash.nsh` с переименованием mod ROM в
  `Robin5.00` имеет риск перепутать его с packaged stock под тем же
  именем. У NeoProgrammer порядок «стереть → открыть файл → записать»
  не содержит двух до-записи чтений или независимого readback.
  External flashrom snippet предлагает два чтения, но не показывает
  команду точного byte diff, затем post-coldboot check. Печать
  синтаксиса, список действий и «подожди15 минут» не равны observed
  безопасному programmer run. Ничего не запускалось.
- CMOS clock becoming wrong162 — слабый proxy для reset, не проверка
  всех NVRAM/UMA states. С одной стороны, после flash CMOS может быть
  нужен; с другой, плохие настройки могли не восстановиться через
  CMOS по source5. 512MB dynamic/Forces/UMA_SPECIFIED и история Cyberpunk
  60→66→76FPS смешивают OC/FSR/видео/версию: это не измеренный эффект
  одной UMA-переменной. «Нет flashing риска» у runtime memcfg22 тоже
  не превращает другие host writes в гарантию безопасности.
- `Smokeless_UMAF`, `Zentool`, `psptool`, DXE/SMU и `srep` указаны
  как внешние инструменты/идеи. `srep`353 прямо не работал — это не
  самовосстановление. `psptool -X -d 0 -e 1` не проверен на конкретном
  ROM/entry как extraction SMU. Secure Boot disable, CSM/IOMMU settings
  и kernel recommendations не приняты как глобальная boot policy.
- TPMS1, J2 JTAG, I2C/PMBus, J4003 и 3V system-on pin282 — pinout
  claims из внешнего page, не live-board trace или разрешённый вход
  Waveshare. UI x1x1x1x1 option не подтверждает работу bifurcation,
  3600 default field не actual clock. Это не F1/J004 identity,
  не gamepad/wake controller и не PSP signature substitution.

Подробные12 групп:
`phase70-arabic-bios-complete-role-dispositions.json`. В частности,
приложение390–409 — provenance pointers, не independent validation.
Никаких source AFU/flashrom/NeoProgrammer, USB boot, chip erase/write,
CMOS short, driver/config/PSP/firmware/hardware действий не выполнялось.
Далее Arabic overclock body с первой строки по
`phase70-root-next-action.json`; остальные original corpus/firmware/
TOCTOU/privacy/rights/SAST/independent review задачи остаются открытыми.
Native120/176/559 не изменён; весь импорт не разобран.

## Arabic overclock-undervolt: роль документа разобрана

Отдельная переведённая глава `docs/ar/09-overclock-undervolt.md`
прочитана целиком: 98 721 байт, 647 строк, SHA-256
`d6d26a260c1e2ee41c7050487064d9454a13d8e602877cbe3df8fb15dc06e0b6`.
Диапазоны 1–90, 91–180, 181–270, 271–360, 361–450, 451–540,
541–647 не дали потерь вывода. Local pinned Git blob совпал после EOL
нормализации; это не проверка текущего upstream. 25 относительных
ссылок ведут к существующим файлам, но их тела и внешние ссылки в этом
проходе не проверялись. Read receipt, provenance и 12 подробных групп:
`phase71-arabic-overclock-complete-role-*.json`.

- Строки 60–64 предлагают сразу включать governor, а 156–160 называют
  SMU вариант намеренно отключённым до проверки кривой. Сервис не
  включали. TT, SMU, sysfs, ACPI, GUI и CPU OC относятся к разным
  поверхностям; конфиг, запрос или UI не равны реальным тактам/напряжению
  на текущей плате.
- Строка 231 категорически закрывает вопрос двух CPU-ядер. Поздние
  английские обсуждения экспериментируют с этим, но ни запрет, ни успех
  не доказаны на целевой плате. Не смешивать CPU cores с 24→40 GPU CU.
- Строка 335 обещает безвредность чрезмерного undervolt и быстрое
  восстановление; ранее зафиксированы no-boot и неудачный CMOS recovery.
  Утверждения о безопасности, температурах и процентах выигрыша не
  выдерживают универсального переноса на другую плату.
- Строки 343–455 смешивают kernel patch и runtime CU mapping.
  Эквивалентность конечного CU состояния и надёжность `cu_map.sh`
  не установлены; советы установить модуль, изменить initramfs и
  перезагрузиться не выполнялись. Бенчмарки и thermal anecdotes из
  источника не являются наблюдением этого экземпляра.
- Строки 490–538 называют UMA safe-for-all, но смешивают BIOS/UMA,
  swap, загрузчик и службы. Это разные изменения состояния, не
  разрешённый план. Показатели игр и LLM не воспроизведены в
  контролируемом сравнении.
- Строки 540–559 предупреждают о риске GDDR6 timings/CMOS,
  приводя противоположные исходы на разных платах. Их числовые
  частоты и задержки не являются безопасными значениями для цели.
  Независимый recovery path не подтверждён.
- Строка 594 внутренне расходится по времени появления/переименования
  governor. Датированные ссылки требуют сверки с первичными ревизиями.
  Библиография 621–645 не заменяет проверки самих Telegram, Reddit,
  GitHub и 4PDA источников. Ни F1/J004/Waveshare controller, ни PSP
  signature substitution этой главой не доказываются.

Privacy incident: первоначальный фильтр не распознал арабскую строку
383 с учётными данными; ранний ограниченный вывод показал фрагмент.
Значение не повторяется и не переносится в документацию. Фильтр
расширен, эта строка скрыта; строка 632 скрыта консервативно. Это не
полная проверка приватности всего корпуса. Исходные байты не менялись.
Никаких OC/SMU/CU/UMA/GDDR6, host, firmware, PSP или аппаратных
действий не было. Следующая отдельная непрочитанная глава — Arabic
`04-cooling.md`; весь исходный импорт, технические проверки, права,
приватность, SAST и независимый review остаются открытыми.
Native 120/176/559 не изменён.

## Arabic cooling: роль документа разобрана

Отдельная Arabic `docs/ar/04-cooling.md` прочитана полностью: 50 232
байта, 308 строк, SHA-256
`064ee4fdf770d783ac0391dc9b86c3a9d3ef5fcfba87101441892c94cf2055d1`.
Диапазоны 1–90, 91–180, 181–270, 271–308 без renderer loss. Local
pinned Git blob совпал после EOL нормализации, не проверяя текущий
upstream. Шесть относительных ссылок ведут к существующим файлам; их
тела и внешние источники не подтверждены. Privacy prefilter не нашёл
совпадений по пяти patterns, но это не общий clearance. Receipt,
provenance и 13 групп ограничений сохранены в
`phase72-arabic-cooling-*.json`.

- Строки 5–7 и 282–288 выставляют thinning/cutting рёбер как базовый
  этап, но 84 допускает похожий эффект от хорошего кожуха, а 137–138
  описывают **неразрезанный штатный радиатор** с push-pull и камерами
  давления. Это прямое опровержение «обязательно резать», но пока лишь
  один чужой результат. Для нашей платы не измерены геометрия,
  посадка, длительная нагрузка и обратимость. Ничего не резали.
- Температурная таблица 19–32 смешивает GPU edge, CPU Tctl, backside
  memory и SSD. Глава одновременно говорит, что у задней GDDR6 нет
  датчика, но даёт ей температурные цели; метод измерения не указан.
  Точное критическое число для одного SSD не распространяется на
  любой NVMe. Эпизод 54–64 под 40 CU/2GHz дал 107 °C peak GPU и 100 °C
  CPU в чужом десятиминутном прогоне; «устойчиво бесконечно» на
  1500 MHz этим не доказано.
- Таблица 100–101 называет P12 Pro максимум 2100 RPM, тогда как
  описание 131 даёт 600–3000 RPM. Сравнения pressure/airflow/noise,
  удвоение давления двух вентиляторов, выигрыш от отдельного выхлопа
  и радиационный коэффициент анодирования не являются результатом
  контролируемого опыта с этим кожухом и экземпляром платы.
- Shroud/STL/zip-tie и uncut case — кандидаты для проверки fit/flow,
  не готовая сборочная инструкция. AIO и custom loop с числами
  350–400 W от розетки не подтверждают допустимый ток разъёмов.
  Заявление о помпе и пяти вентиляторах от board control не содержит
  измеренного budget; сама глава приводит leak и pump-stall failures.
- `nct6683` как чтение и внешний `nct6687` с `force=true` как запись
  PWM имеют разные риски. `fan2/pwm2`, chip-ID, проводка разъёма,
  разделение BIOS/OS PWM ownership и фактическая скорость на нашей
  плате не подтверждены. Никаких модулей, сервисов или PWM-записей.
- Рецепты paste/PTM и pad толщин относятся к разным сборкам.
  26×30 mm и 40×80×0.25 mm нельзя объявлять взаимозаменяемым
  размером без проверки поверхности; видео само предупреждает о
  неточном автотексте. VRM 1 mm/GDDR6 2 mm и фронтальные 1.5 mm
  относятся к разным зазорам. Pixel artifacts не доказывают именно
  перегрев VRAM, а уменьшение UMA не доказано как охлаждение GDDR6.
- «Проверенный» Furmark+CPU/OC прогон 266–276 — инструкция из источника,
  а не выполненное испытание. Ни установка, ни стресс, ни разгон, ни
  работа с термоинтерфейсом, радиатором, питанием или жидкостью не
  выполнялись. Внешние Telegram/Reddit/YouTube/Printables ссылки
  остались provenance leads, не первичным подтверждением или
  проверкой прав на медиа.

Следующая отдельная непрочитанная глава — Arabic `05-case.md`. Весь
исходный импорт, board-specific thermal/электрические проверки,
приватность, права, SAST и независимый review остаются открытыми.
Native 120/176/559 не изменён.

## Arabic case: роль документа разобрана

Отдельная Arabic `docs/ar/05-case.md` прочитана целиком: 45 816 байт,
345 строк, SHA-256
`fc75fbda2c9797f6cf2a354b1b5a5860dfd269e55b7271e3d532c82e20277cf2`.
Диапазоны 1–90, 91–180, 181–270, 271–345 без renderer loss. Local
pinned Git blob совпал после EOL нормализации, но текущий upstream не
проверялся.19 relative targets существуют; их тела и внешние модели
не проверены. Privacy prefilter5patterns без совпадений, но не общий
clearance. Read receipt, provenance, exact-name check и13 issuegroups:
`phase73-arabic-case-*.json`.

- Каталог 5–11 говорит, что «почти все» печатают корпус и советует
  конкретную накладку, а 321 допускает открытую плату/переделку
  старого корпуса. Значит, корпус не является обязательным условием
  работы. Ссылка на ~143 модели и оценки «лучшая» — исторический
  срез/популярность, не проверенная текущая доступность или fit.
- Строка 47 говорит, что большинство корпусов предполагают уже
  обработанные рёбра, но 9 и 55–62 предлагают **friction-fit sleeve
  без резки и без винтов в плату**. Чужой отчёт ~70 °C/150 W не
  подтверждает геометрию, контакт, материал, питание или длительное
  охлаждение нашей платы. Это полезный вариант для последующего
  выбора, но не инструкция к изготовлению.
- Пункт 51 категорически требует clear CMOS после каждого изменения
  UMA и предлагает отверстие/трёхпозиционный переключатель. Нет
  board-specific идентификации контактов, полярности, изоляции и
  проверенного восстановления. Сверлить или подключать ничего
  не разрешено и не делалось.
- Family LOP/Flex/SFX/HP, fan aperture и «любой PSU» — фильтры
  каталога, не электрические допуски и не точный fit/strain relief.
  Звёзды, фотографии, список материалов и продажи не заменяют
  CAD/печать/измерения. Для Steam Cube 159–170 сам источник честно
  пишет: параметрическая концепция не напечатана, не собрана и не
  испытана, а положение ядра выведено из bounding box.
- Строки 154–155 показывают пример ESP32 relay для дистанционного
  включения чужой сборки. Это не схема Waveshare для gamepad/power/SPI,
  не J004/F1 и не путь подмены PSP-записи. Pi Zero 2 HUD 188–190
  обслуживает экран состояния через USB gadget с отдельной vc4
  правкой; показание сна по напряжению вентилятора не становится
  управлением платой или геймпадом. Код этих проектов не проверялся.
- В импортной `assets/stl/` метаданными обнаружена61 запись.
  Восемь выбранных точных названий есть; у трёх точных названий
  chat-marked архивов/составных моделей из таблицы 210–244 в этом
  каталоге совпадений нет. Сокращённые placeholders не засчитаны как
  отсутствующие файлы. Строки 210/345 о «всех mirrored» поэтому
  нельзя подтвердить для этой папки; это не поиск по всему архиву.
  Наличие STL/3MF/STEP по имени не доказывает геометрию, лицензии,
  печатаемость или соответствие текущей плате.
- «Generic ITX mount для любого ITX-корпуса» на201 опирается на одну
  DeepCool сборку без захваченной первичной ссылки, не универсальный
  тест. Истории eDP, Xbox-donor цен, wood/metal/backplate paste и
  температур на чужих сборках остаются отдельными leads. Ни одну
  модель не скачивали, не распаковывали, не печатали, не покупали и
  не устанавливали. Внешние ссылки и права на медиа не проверены.

Следующая отдельная непрочитанная глава — Arabic
`16-usb-peripherals.md`, затем весь остальной исходный импорт,
приватность, права, SAST и независимый review. Native120/176/559
не изменён.

## Arabic USB/peripherals: роль документа разобрана

Отдельная Arabic `docs/ar/16-usb-peripherals.md` прочитана целиком:
28 982 байта, 203 строки, SHA-256
`a59b2fcc389d5eeef39e22f9a43c17bc2b7a64c16953be1e02aef3ecb8821853`.
Диапазоны 1–90, 91–180, 181–203 без renderer loss. Local pinned
Git blob совпал после EOL нормализации, но это не текущий upstream.
Десять относительных ссылок ведут к существующим файлам; их тела и
внешние источники не проверены. Privacy prefilter5patterns без
совпадений, но не clearance всего корпуса. Receipt, provenance и
13групп ограничений: `phase74-arabic-usb-*.json`.

- Глава заявляет четыре rear USB порта и отсутствие штатного переднего
  header, но «USB3 электрически x2» на15 — двусмысленное слово одного
  участника, не lane map или замер скорости. Отчёт одного владельца
  25–27 о 4.3 V и 2.3–3.2 V под нагрузкой соседствует с владельцем
  31, у которого много устройств работают на пассивном hub. Ни
  состояние 5 V, ни ток, ни причина сбоя на нашей плате не измерялись.
- **Активный hub с отдельным питанием** на35–43 — без пайки и потому
  полезная гипотеза для поздней проверки геймпадов. Это ещё не
  одобренное устройство: обратная подача VBUS, общая земля,
  standby/sequence и лимиты питания не изучены. «Иначе сожжёшь
  порт» и «навсегда привяжешься к hub» не следуют из цитат.
- Строки 49–79 дают cut/inject VBUS рецепт одного пользователя.
  Совпадение источника ATX не доказывает безопасный return path,
  отсутствие backfeed, токовый лимит или порядок включения.
  Это **не** требование для Waveshare и не разрешение резать провод,
  паять или питать разъём. Ничего подобного не делалось.
- Type-E/Key-A/Type-A обозначения 95–102 требуют pinout/fit; сам
  источник подтверждает только USB2, а USB3 в той сборке ещё ждал
  проверки. Никакие кабели не соединялись и не резались.
- M.2 PCIe2 ×2, прямой M.2 SATA stick и активная ASM1166 карта
  106–116 — разные режимы. Число PCIe линий само не опровергает
  активный SATA контроллер и не доказывает SATA mode в текущем
  разъёме. PH516 fail описан по двум сообщениям, не по всему классу.
  «На плате только 12 V» на120 смешивает отсутствие SATA power header
  с признанным выше генератором USB 5 V. Buck/USB-to-SATA supply
  не квалифицированы по земле, нагрузке или контакту.
- Глобальная замена `nvme`→`sda` в repair script 124–132 — частный
  workaround с риском направить установщик не на тот диск. Скрипт и
  диски не менялись. Один DisplayLink dock без видео не доказывает
  невозможность видео у любого dock.
- DS5Dongle/Pico2W, GameSir 2.4 GHz и UGREEN/USB2 на156–162 —
  пути и отзывы отдельных пользователей. Программная, аудио и BT
  совместимость не подтверждены здесь. Это не схема постоянно
  подключённой Waveshare, не доказательство питания/опроса всех
  геймпадов и не доступ к PSP/SPI. Код и железо не испытывались.
  Telegram/4PDA/video ссылки остаются leads, не первичной
  board-specific верификацией или проверкой прав.

Следующая отдельная непрочитанная глава — Arabic `10-wifi-bt.md`,
затем весь остальной импорт, технические, privacy/rights/SAST и
независимый review задачи. Native120/176/559 не изменён.

## Arabic WiFi/BT: роль документа разобрана

Отдельная Arabic `docs/ar/10-wifi-bt.md` прочитана целиком: 23 062
байта, 185 строк, SHA-256
`3087718af55cf3cb83a7a1a61f79b6ce9e4e0cf6df77513f2457c5ee603ef972`.
Диапазоны 1–90, 91–180, 181–185 без renderer loss. Local pinned
Git blob совпал после EOL нормализации, текущий upstream не
проверялся. Единственная относительная English ссылка существует,
её тело не проверено; external repos/issues/видео не открывались.
Privacy prefilter5patterns без совпадений, но не clearance всего
корпуса. Receipt, provenance и13 issuegroups:
`phase75-arabic-wifi-*.json`.

- «Почти каждое отключение от двух причин» на15–20 не следует даже
  из самой главы: позже названы RF-помеха USB3, BT coexistence,
  firmware и kernel-version/build проблемы. Семнадцатиминутное
  отключение чужого донгла не изолирует причину. Чужой USB5V
  отчёт из соседней главы не становится измерением нашей платы.
- `aic8800d80` назван «самым надёжным», но строки 94–97 ссылаются на
  собственные issue cases: отсутствующий firmware blob, сбой сборки
  на некоторых ядрах и отказ WiFi в Debian. BT идёт отдельной
  веткой. Bazzite RPM и raw `make` маршруты 46–90 содержат
  загрузку внешнего кода, overlay, kernel module install и reboot.
  Версия main не зафиксирована, code/signature/rollback не
  проверены. Ничего не скачивали, не компилировали, не ставили и
  не перезапускали.
- `rtw88` на RTL8821/8822 содержит утверждение о mainline fix в
  6.13–6.14, но раздел 117 признаёт остаточные обрывы и разницу
  throughput. `biglinux/rtl8831` на RTL8851BU не был показан на
  BC-250 в самом чате. У одного TP-Link vendor BT/Linux не
  поддерживается; это не автоматическая проверка WiFi Linux или
  любого UGreen с похожим маркетинговым именем.
- `lsusb`/FCC ID и название чипсета — старт для exact device-ID,
  но не фиксируют revision, firmware и binding. Список покупок
  159–168 и общие отзывы про RTL8111 Ethernet не подменяют
  инвентаризацию и тест нашего экземпляра.
- USB3→2.4GHz RF документы дают механизм, но «20 dB» на146 не
  измерены на этой раскладке. USB2/удлинитель — проверяемая
  гипотеза, не гарантия. 150/190 Mbit при BT on/off — один замер.
  Рецепт `rmmod btusb`/`softdep` на155 мог бы затронуть чужие BT
  устройства; отсутствие Bluetooth не доказывает единственную
  причину. Никаких USB reset, модулей и конфигурации не меняли.
- WiFi/BT донгл нужен только как возможная транспортная часть
  геймпадов. Эта глава не описывает управляющую Waveshare,
  power-on/off, J004/F1, SPI handoff или PSP signature substitution.
  Ни один из перечисленных сторонних репозиториев не был принят
  как компонент проекта без отдельной проверки.

Следующая отдельная непрочитанная глава — Arabic `11-gaming.md`,
затем весь остальной импорт, privacy/rights/SAST, технический
и независимый review. Native120/176/559 не изменён.

## Arabic gaming: роль документа разобрана

Отдельная Arabic `docs/ar/11-gaming.md` прочитана полностью: 34 418
байт, 212 строк, SHA-256
`b4f71b4e9611c121f4bbcf29fcc882707730c9b1a7d2a542abc0ed6446ebd013`.
Диапазоны 1–90, 91–180, 181–212 без renderer loss. Local pinned
Git blob совпал после EOL нормализации, текущий upstream не
проверялся. Девять относительных ссылок ведут к существующим
файлам, но их тела и внешние видео/таблицы/код не проверены.
Privacy prefilter5patterns без совпадений, не clearance всего
корпуса. Receipt, provenance и13 issuegroups:
`phase76-arabic-gaming-*.json`.

- Одна сцена с 38 FPS и метрикой GPU36.5% на15 не доказывает, что
  CPU ограничивает **большинство** игр, или что 1440p «бесплатны».
  Результаты зависят от версии игры, нагрузки, ОС, CU, тактов,
  UMA, драйвера и frame-time. В таблице 43–85 смешаны Windows/Linux,
  FSR, frame generation, RT, video/ASR и разные конфигурации.
  Wukong45 содержит смешанные метки Windows/RADV, требующие
  проверки оригинала; RX6600+Xeon85 прямо **не BC-250**.
- «Разгоняй сначала», GPU2000MHz, 40CU, memory clock и UMA
  22–35 — чужие сборки, не профиль нашей платы. +30% FPS относится
  к некоторым GPU-limited сценам, не ко всем играм. Список
  включает Elden Ring ~60, но ниже сохраняет 30 FPS даже 720p
  low; обе истории нельзя усреднить. 40CU/Doom и RT данные
  зависят от версии/patch, не подтверждают boot или firmware.
- FSR/LSFG «почти удваивает FPS» меняет показываемые кадры, не
  обязательно native simulation/input latency. FSR4 на RDNA2
  через DP4a назван экспериментом, а «официально к началу2027»
  — прогноз на момент источника, не подтверждённая нынешняя
  возможность. `mitigations=off` на35 снимает защитные меры
  ради противоречивого/неизолированного FPS-эффекта; ничего в
  host boot policy не менялось.
- Жёсткие заявления 115–126 о mesh/VRS не проверены feature query
  конкретной платы и версией игр. Внешняя NullVRS layer описана
  как обход одного launch-gate, но «без побочных эффектов» не
  доказано и не связано с PSP/BIOS подписью. Hardware RT, Mesa
  software RT path и игровой preset нельзя подменять друг другом.
  Сами игры и внешний layer не запускались.
- Anti-cheat/Proton/эммуляторские таблицы и «список работающих
  PS-портов» историчны и не гарантируют нынешний запуск.
  `RADV_DEBUG`, Proton GE, UMA/GTT и zswap советы — инструкции
  источника, не применённые настройки. Видео и Google Sheet
  не проверены на происхождение/права. Эта глава не содержит
  проверки геймпадов или схемы Waveshare-power-SPI.

Следующая отдельная непрочитанная глава — Arabic `12-ai-llm.md`,
затем весь остальной исходный импорт, privacy/rights/SAST,
технический и независимый review. Native120/176/559 не изменён.

## Arabic AI/LLM: роль документа разобрана

Отдельная Arabic `docs/ar/12-ai-llm.md` прочитана целиком: 29 463
байта, 217 строк, SHA-256
`ff7294919f5141346fc3ae567200ffaae570c5a734e7275f01084cde3289002e`.
Диапазоны 1–90, 91–180, 181–217 без renderer loss. Local pinned
Git blob совпал после EOL нормализации, текущий upstream не
проверялся. Девять relative link occurrences ведут к существующим
файлам, но linked/remote code, models, Discord и тесты не проверены.
Privacy prefilter5patterns без совпадений, не clearance всего корпуса.
Receipt, provenance, inert numeric/name check и13 issuegroups:
`phase77-arabic-ai-*.json`.

- Эта глава на13 называет `gfx1013` RDNA-1.x/Navi10-подобной, а
  предыдущая Arabic gaming на13 называла тот же `GFX1013` RDNA2/PS5.
  Противоречие остаётся до независимой идентификации IP/ISA.
  Отсутствие официальных ROCm userspace math solutions не равно
  физической невозможности: сама глава после «никто не запустил»
  приводит25 сообщение о HIP/PyTorch после MEC firmware/BIOS/rebuild.
  Этот эксперимент не даёт нам образ, signed-region diff, recovery
  или право переносить его на плату. Ни MEC/PSP/BIOS не менялись.
- Общие 16GB делят CPU, GPU, OS, модель и KV-cache; число параметров
  и MoE-активных экспертов не доказывают размещение всех весов в
  памяти. BIOS VRAM, TTM, headless и OOM — разные изменения.
  Установка `curl | sh`, systemd override/restart и sysfs writes
  65–98 не выполнялись. `OOMScoreAdjust=-1000` мог бы защитить
  Ollama ценой остальных процессов, а `OLLAMA_GPU_OVERHEAD=0`
  не оставляет явного запаса. При 4KiB pages значение4194304
  соответствует16GiB, почти всему общему объёму, не «безопасной»
  универсальной настройке.
- Таблица ~30–40 tok/s и поздние 66–87 tok/s используют разные
  backend/модели/CU/метрики; HIP `pp512` — prefill, не generation.
  Не смешивать их в единый benchmark. Источник ошибается в простой
  арифметике видео: 25.7→31.9 это **+24.12%**, не16–17%;
  25.7→33.4 это **+29.96%**, не~20%. Два MoE ряда 66.1→87.5
  и59.5→78.7 действительно около+32%, но лишь в тех опытах.
- Модельные подписи тоже не строго совпадают: ссылка для
  библиография отдельно упоминает Qwen3.5 и Qwen3.6; не
  объединять их в один проверенный результат. Gemma A3B ведёт к
  имени файла A4B. GGUF, hashes, versions, prompts и модели не
  скачаны. Jan AI web/MCP и внешние frontend/repos не приняты
  без отдельного review. Экспериментальные CU/ROCm/LLM слова
  не являются доказательством PSP-signature substitution.

Следующая отдельная непрочитанная глава — Arabic `13-macos.md`,
затем весь остальной исходный импорт, privacy/rights/SAST,
технический и независимый review. Native120/176/559 не изменён.

## Arabic macOS: роль документа разобрана

Отдельная Arabic `docs/ar/13-macos.md` прочитана целиком: 8 590
байт, 55 строк, SHA-256
`e6e2a46e39b9d805fd58e5b15db813a35d6f1d2ebaccc0231babf9f3328775ac`.
Один диапазон 1–55 без renderer loss. Local pinned Git blob совпал
после EOL нормализации, текущий upstream не проверялся. Семь
relative link occurrences ведут к существующим файлам; их тела,
внешние bootloader/kext/forum и ZIP не проверены. Privacy
prefilter5patterns без совпадений, не clearance всего корпуса.
Receipt, provenance и9 issuegroups: `phase78-arabic-macos-*.json`.

- «Никто не сообщал об ускоренном macOS» — отсутствие результата
  в выбранной беседе до даты источника, не доказательство
  физической невозможности и не нынешний поиск по всему миру.
  `gfx1013`/GPU ID, native driver table, firmware and target board
  не были независимо сверены. macOS не загружали.
- Строки 15–21 описывают OpenCore как единственный pre-OS путь
  вмешательства и подмену ID только внутри одной архитектуры.
  Это упрощение: совместимость зависит также от бинарных драйверов,
  инициализации и hardware IP, а не от одного ID. Никакой
  bootloader/kext не применялся.
- Внутри главы есть прямое противоречие: строка22 утверждает, что
  Ryzen iGPU «никогда не работала», а31 сама называет NootedRed
  для AMD APU Vega/Renoir. Это **не** доказывает поддержку BC-250,
  но снимает категоричность общего тезиса.
- Архив Monterey recovery+OpenCore, упомянутый30, свидетельствует
  лишь о подготовке/публикации, не об успешной загрузке и тем
  более не о Metal acceleration. Форумный VMware/OpenCore пример
  — общий Ryzen, не BC-250. Шутки из чата не результаты.
  Советы Linux/Windows/macOS не заменяют сравнение на текущей
  плате. Архив не открывался, не устанавливался и не запускался.

Следующая отдельная непрочитанная глава — Arabic `14-display.md`,
затем весь остальной исходный импорт, privacy/rights/SAST,
технический и независимый review. Native120/176/559 не изменён.

## Arabic display: роль документа разобрана

Отдельная Arabic `docs/ar/14-display.md` прочитана целиком: 26 443
байта, 165 строк, SHA-256
`e49dc88d2c3095a48c009ec55b02f3535ac3ffda97132943558e50d694382cde`.
Диапазоны 1–90, 91–165 без renderer loss. Local pinned Git blob
совпал после EOL нормализации, не проверяя нынешний upstream.
Десять relative link occurrences ведут к существующим файлам;
linked/remote bodies не валидированы. Privacy prefilter5patterns
без совпадений, не clearance всего корпуса. Receipt, provenance
и11 issuegroups: `phase79-arabic-display-*.json`.

- «DP→HDMI видео всегда, без задержки» на5 противоречит самому
  источнику: 15 описывает изображение до GRUB, затем чёрный экран
  в ОС; 82 — сбой на 4K-мониторе; 127 — HDMI MST без видео.
  Коннектор, кабель, EDID, адаптер и драйвер имеют значение.
  DP1.4/4K120/HDR10 и предел кабеля — ссылки, не измеренный
  link-training нашей платы.
- Путь «нет картинки → сброс BIOS/перепрошивка» на16 не даёт
  точного образа, verified dump, независимого recovery или readback.
  Несколько не показывающих карт не доказывают firmware root cause.
  Ничего не сбрасывали и не прошивали. После-входа чёрный экран
  тоже не всегда Wayland; менять GDM, Mesa, `nomodeset` или
  стороннюю Bazzite image без target diagnosis не разрешалось.
  Упомянутый remix HDMI2.1 испытывался на9070XT, не BC-250.
- Раздел DP audio 69–83 содержит взаимно ограничивающие
  советы: «пассивный надёжнее», «активный для 4K/HDR», затем
  «тип сам не предсказывает звук; зависит от адаптера».
  Вывод про всегда искажаемый DP-звук и никогда не работающие
  HDMI 5.1 требует target ALSA/ELD/codec проверки. Открытие
  обещает fix в kernel6.17, а87 говорит, что 6.17 сломало
  default configuration и нужен custom codec build. Ничего
  не собирали и не тестировали.
- «Второго физического вывода нет/он не припаян» на113–116
  нельзя смешивать с двумя **логическими** мониторами через
  один DP MST. StarTech MST report120–129 относится к одному
  splitter, не к нашей плате. DisplayLink video 131 —
  другой путь; Arabic USB глава ранее приводит один dock
  без видео. Ни тот ни другой исход не универсален.
- Steam/Sunshine/Moonlight 135–142 — чужие сетевые опыты,
  не доказательство текущего VCN hardware encode, latency,
  gamepad forwarding или управления питанием. Вся глава
  не определяет Waveshare/PSP-SPI путь. Дисплей, аудио,
  поток и firmware на нашей плате не трогали.

Следующая отдельная непрочитанная глава — Arabic `15-emulation.md`,
затем весь остальной исходный импорт, privacy/rights/SAST,
технический и независимый review. Native120/176/559 не изменён.

## Arabic emulation: роль документа разобрана

Отдельная Arabic `docs/ar/15-emulation.md` прочитана полностью:
28 370 байт, 160 строк, SHA-256
`1a9177ab5ea1f5302ef7f22c984f061bc94f35572bb8d128315a90708369baec`.
Диапазоны 1–90, 91–160 без renderer loss. Local pinned Git blob
совпал после EOL нормализации, текущий upstream не проверялся.
Двенадцать relative link occurrences ведут к существующим файлам;
linked/remote emulator/OS/rights bodies не проверены. Privacy
prefilter5patterns без совпадений, не clearance всего корпуса.
Receipt, provenance и11 issuegroups: `phase80-arabic-emulation-*.json`.

- Здесь **PSP — PlayStation Portable, эмулируемая PPSSPP**, а не
  AMD Platform Security Processor. Чужой отчёт о 4× internal
  resolution не свидетельствует ни о PSP-подписи BIOS, ни о
  SPI-handoff, ни о загрузочной цепочке.
- Глава честно отличает результаты участников от общих оценок
  для Zen2/RDNA2, однако общие **непроверенные на BC-250**
  строки всё равно окрашены зелёной галочкой и названы
  «тривиальными»/«98%». Это не поигровая проверка платы.
  PS4 Bloodborne/DriveClub и PS3 Uncharted — отдельные
  датированные случаи; Xenia в одном случае показывает меню
  и получает ввод контроллера, но не выводит игру.
- Один случай GPU1000MHz в эмуляторе не делает OC2000–2250MHz,
  CPU4GHz и обработку радиатора обязательными для всех систем.
  Прямо здесь простые эмуляторы — другой класс нагрузки.
  Ни контроллер, ни тепловой режим, ни такты нашей платы не
  измерялись. Никаких OC/cut/thermal действий.
- EmuDeck/RetroDECK/RetroArch/Batocera и Steam overlay — внешние
  установщики/ОС и опыт настройки; «EmuDeck привязывает
  геймпад» не проверяет Waveshare, F1/J004, включение платы
  или PSP SPI. Ни один пакет/образ не запускался.
- ROMs, консольные ключи, BIOS и бинарники эмуляторов имеют
  отдельные права. Слова выбранной беседы о «запрете готовой
  сборки» не определяют все правовые условия. Ничего не
  скачивали и не распространяли. External guide сам отмечен
  как неверно считающий CPU cores; здесь RDNA2 тоже не
  снимает противоречия с Arabic AI `gfx1013` RDNA1.x.

Следующая отдельная непрочитанная глава — Arabic
`01-what-is-bc250.md`, затем оставшиеся Arabic и весь исходный
импорт, privacy/rights/SAST, технический и независимый review.
Native120/176/559 не изменён.

## Arabic identity: роль документа разобрана

Отдельная Arabic `docs/ar/01-what-is-bc250.md` прочитана полностью:
26 266 байт, 172 строки, SHA-256
`ae39f027332928e6c4ebeedef70e84ea693ff3c9ae037c3e46b14de6d1dc2c56`.
Диапазоны 1–90, 91–172 без renderer loss. Local pinned Git blob
совпал после EOL нормализации, текущий upstream не проверялся.
22 relative link occurrences ведут к существующим файлам;
linked/remote technical bodies не приняты. Privacy prefilter5patterns
без совпадений, не clearance всего корпуса. Receipt, provenance,
inert arithmetic и14 issuegroups: `phase81-arabic-identity-*.json`.

- Вступление5 говорит «нет обычного x86 BIOS», но та же глава
  обсуждает BIOS3.00 UMA и BIOS reset, а предыдущая Arabic BIOS
  — AMI/UEFI и прошивку. Для нашей платы решают exact ROM bytes,
  а не вводный лозунг. «PS5 surplus silicon», blockchain origin,
  4700S/4800S родство и «Linux как взлом PS5» — разные
  community/press версии происхождения, не die provenance.
- Здесь `gfx1013` зовётся RDNA2, тогда как Arabic AI называла
  его RDNA1.x. Пока не сверены target IP/ISA и первичные источники,
  не превращать сходство с PS5/SteamDeck в точную GPU/VCN/PSP
  карту. «VCN нет» на53/101 не отличает неработающий штатный
  encoder path от физического отсутствия блока. Цель проекта
  по VCN остаётся открытой.
- «Нет никаких официальных драйверов» на51 шире, чем «нет
  board-specific поддержанного пакета»: generic amdgpu/Mesa
  и чужие скрипты — разные вещи. «Многим нужен CMOS reset
  перед POST» — один тип анекдота, не диагностика нашего экземпляра
  или разрешение сбрасывать/прошивать. LED red/green map
  также не проверен live logic trace. История «выпрямить
  плату бумагой» не даёт безопасной процедуры; усилие может
  повредить PCB/BGA. Никаких физических действий.
- Pinout J1000/J2000/J2001, PGD5V, polarity и Micro-Fit
  на118–139 заимствованы из внешних pages, а не измерены на
  этой плате. **3×9A×12V=324W** — верная арифметика,
  но не допуск разъёма/провода/дорожек/PSU и не указатель
  ориентации pin1. Нельзя по этой картинке подключать питание
  или Waveshare.
- Табличное **256bit×14Gbps÷8=448GB/s** — номинальное
  вычисление, не замер. Рассказ о «stock256→OC445GB/s»
  не может описывать тот же default state; сама глава
  признаёт расхождение. Варианты размеров 340/310mm,
  M.2/SATA, DP1.4/8K60, second DP и 220W TDP не
  проверены на конкретной плате, а physical second port
  и один DP с MST нельзя смешивать.

Следующая отдельная непрочитанная глава — Arabic `02-buying.md`,
затем оставшиеся Arabic и весь исходный импорт,
privacy/rights/SAST, технический и независимый review.
Native120/176/559 не изменён.

## Arabic buying: роль документа разобрана

Отдельная Arabic `docs/ar/02-buying.md` прочитана полностью:
30 276 байт, 163 строки, SHA-256
`ed0365127536adf18a7c4a0c6275e1f425735bace65dd1dc6f40db9420d70817`.
Диапазоны 1–90, 91–163 без renderer loss. Local pinned Git blob
совпал после EOL нормализации, не проверяя нынешний upstream.
16 relative link occurrences ведут к существующим файлам;
внешние объявления/цены/отзывы не проверялись. Privacy
prefilter6patterns без совпадений, но не clearance всего корпуса.
Личные контакты и непроверенные обвинения в active docs не
переносились. Receipt, provenance и13 issuegroups:
`phase82-arabic-buying-*.json`.

- Диапазоны цен, комиссии и доставки относятся к разным датам,
  странам, валютам и комплектациям. Цена мёртвого донора,
  голой рабочей платы и собранного ПК несопоставима без
  нормализации. Старая ссылка на объявление не подтверждает
  сегодняшнюю цену, продавца, гарантию или наличие. Ничего
  не покупали, никому не писали и не платили.
- Описанный путь через посредника с переводом на частную
  карту/чатный escrow — не проверенная защита покупателя.
  Неподтверждённые репутационные жалобы не приняты как факт
  и имена не повторяются. Фото, надпись «работает» или
  установленная ОС не доказывают exact board/chip/ROM identity,
  recovery или долговременную исправность.
- Масса «голой платы ~0.86kg» здесь расходится с ~0.4kg
  «с радиатором» в предыдущей Arabic identity главе.
  Возможно, разные методы/упаковка, но это не замер
  нашего экземпляра и не надёжный расчёт пересылки.
- «Любой BIOS годится, все перешьёшь» на76 не учитывает
  точный image/target, signed PSP, полный verified dump,
  независимый recovery и явное согласование конкретной
  прошивки. Этот совет не заменяет очередь прошивки.
  «Разница рёбер не влияет на охлаждение» расходится с
  Arabic cooling вариантами и остаётся непроверенным.
- Wall idle, GPU, CPU и GDDR6 числа на86 взяты из разных
  контекстов; источник сам признаёт большой разброс.
  «Auto-suspend ~10W» не является доказательством wake/power
  контроллера Waveshare на нашей плате. Постоянный mining
  temperature не гарантирует долговечность BGA/PCB.
  Mesh/VRS и VCN заявления здесь не заменяют feature query
  или точную PSP/SMU политику; прежняя gaming глава
  приводит частный VRS launch workaround.

Следующая отдельная непрочитанная глава — Arabic `06-linux.md`,
затем оставшиеся Arabic и весь исходный импорт,
privacy/rights/SAST, технический и независимый review.
Native120/176/559 не изменён.

## Arabic Linux: роль документа разобрана

Отдельная Arabic `docs/ar/06-linux.md` прочитана целиком:
71 727 байт, 581 строка, SHA-256
`e545a8e5e3fe0a0174189d8db7d949dc223a573d0ac0332527dd56ec886847d2`.
Диапазоны 1–90, 91–180, 181–270, 271–360, 361–450,
451–540, 541–581 без renderer loss. Local pinned Git blob совпал
после EOL нормализации, но текущий upstream не проверялся.
Тринадцать относительных ссылок ведут к существующим файлам;
их тела и внешние images/scripts/issues не проверены. Privacy
prefilter6patterns без совпадений, но не clearance всего корпуса.
Receipt, provenance и17 issuegroups: `phase83-arabic-linux-*.json`.

- В начале firmware symlink navi10 показан как обязательный.
  Позже сама глава говорит, что современный `linux-firmware`
  уже содержит `cyan_skillfish_gpu_info.bin`, а symlink нужен
  лишь при конкретной ошибке загрузки. Нельзя применять
  старую инструкцию без текущих версий/файлов/dmesg.
  Аналогично Fedora43 названа не нуждающейся в Mesa COPR,
  но скопированный `fedora-setup.sh` всё ещё включает старый
  COPR и меняет Mesa. Arch official `extra` назван достаточным,
  но предыдущий блок предлагает Chaotic-AUR и git Mesa.
- Stock Bazzite+governor и чужая BC250 patched image —
  разные состояния. Образ `latest` не закреплён digest/source
  review. Важнее: источник сам предупреждает, что встроенная
  40CU-правка на некоторых установках ломает **fan control
  и Xbox controller**. Другая community kernel только
  предполагаемый workaround, не гарантия. Для цели Waveshare
  нельзя считать rebase или 40CU изменением без риска для
  охлаждения и геймпадов. Ни образ, ни kernel не ставились.
- `mitigations=off` в начальной «необходимой» строке, а ниже
  объявлен необязательным с ценой потери защиты. Blanket
  «выключи IOMMU в BIOS один раз» не следует из доказательства
  именно нашей платы и ухудшает isolation. TTM/GTT почти на
  весь общий объём RAM, 512MB UMA, zswap32GB и отказ от ZRAM
  — разные системные компромиссы, не universal safe baseline.
  Никаких BIOS, bootargs, swap или security changes.
- CoreOS `umr` boot register writes и injected ACPI AML
  не документационная мелочь, а реальные live GPU/boot
  действия. `dmesg_restrict=0` ослабляет приватность логов;
  `sensors-detect` YES-all, Nuvoton `force=true` и внешний
  `nct6687` могут получить PWM write authority без target
  chip/pin/current map. Ничего не запускалось.
- `vulkaninfo`, RADV label, dmesg CU, hwmon и debugfs
  частично наблюдают систему, но по отдельности не доказывают
  app GPU rendering, exact CU map, VCN или coldboot.
  `vainfo` failure и software fallback — shipping-path факт
  из отчётов, не «VCN нет навсегда». Source cache deletion
  через `rm -rf`, service masks/restarts, kernel downgrade
  и bootloader rebuild оставлены **невыполненными**.

Следующая отдельная непрочитанная глава — Arabic `07-windows.md`,
затем оставшиеся Arabic и весь исходный импорт,
privacy/rights/SAST, технический и независимый review.
Native120/176/559 не изменён.

## Arabic Windows: роль документа разобрана

Отдельная Arabic `docs/ar/07-windows.md` прочитана целиком:
18 748 байт, 128 строк, SHA-256
`0650d687768f87ea7de191eec6f4559a86f0f6d80145675030b72a7999348ee3`.
Диапазоны 1–90, 91–128 без renderer loss. Local pinned Git blob
совпал после EOL нормализации; current upstream/driver releases
не проверялись. Девять relative link occurrences ведут к
существующим файлам, их тела и внешние repo/7z/issue не
проверены. Privacy prefilter6patterns без совпадений, не
clearance всего корпуса. Receipt, provenance и13 issuegroups:
`phase84-arabic-windows-*.json`.

- Code43, PCI `1002:13FE` и неудачные `.inf` на15–21 —
  исторические отчёты, не текущее PCI readback нашей платы.
  Одна неудачная правка BIOS Device ID не доказывает eFuse
  или физическую неизменяемость ID. «Никто не играет в
  Windows» привязано к времени выбранного корпуса, не к
  сегодняшним всем Windows-разработкам.
- Keshas PSP-driver по ссылкам заявляет SOS/BAR5/NBIO
  register access, но сам отмечает отсутствующие GPCOM ring,
  GPU firmware upload и TMR. README/commits не были
  независимо собраны/запущены на нашей плате. **Windows
  драйвер PSP — не подмена PSP-подписи в SPI** и не
  доказательство, что модифицированный ROM загрузится без платы.
  Ранняя 7z-сборка не открывалась и не принималась.
- ZEROAESQUERDA WDDM2 test с D3D9 DDI без shader compiler/
  command processor/современных API — образовательный
  каркас, не игровой драйвер. PS5GPU-BC250 и duggasco40CU
  в source resource lists названы неверно: это Linux
  governor/kernel patch, не Windows driver.
- `testsigning on`, отключение Secure Boot и PowerShell/
  pnputil установка снижали бы доверие к загрузке и меняли
  kernel drivers. У нас нет exact release/hash/signer/
  восстановления для принятия этих команд. Шутка с
  «NVIDIA driver», переименованный Adrenalin exe и
  malware-истории — повод проверять provenance; GitHub
  сам по себе не знак безопасности. Unverified remote-brick
  rumor не принят как факт. Ни ОС, ни драйвер, ни SPI/ROM
  не менялись.

Следующая отдельная непрочитанная глава — Arabic `faq.md`,
затем `troubleshooting.md` и весь исходный импорт,
privacy/rights/SAST, технический и независимый review.
Native120/176/559 не изменён.

## Arabic FAQ: роль документа разобрана

Отдельная Arabic `docs/ar/faq.md` прочитана целиком: 24 432
байта, 187 строк, SHA-256
`57a07f61527778a26e243ee90f555674d85d700b8463b510f207edb3c831b620`.
Диапазоны 1–90, 91–180, 181–187 без renderer loss. Local pinned
Git blob совпал после EOL нормализации; current upstream не
проверялся.49 relative link occurrences ведут к существующим
файлам, большинство из Arabic FAQ в English главы; linked bodies
не проверены. Privacy prefilter6patterns без совпадений, не
clearance всего корпуса. Receipt, provenance и16 issuegroups:
`phase85-arabic-faq-*.json`.

- Краткий ответ «нет кнопки, включается при 12V» расходится
  с более подробными power состояниями AUTO_PWRON/PWR_SW/PS_ON.
  «Нет POST → сброс CMOS или выпрямить плату бумагой»
  не является безопасной диагностикой. «EPS всегда с обратной
  полярностью» и «дым кабеля почти наверняка фальшивая медь»
  упрощают не измеренные pinout, crimp, contact и токи;
  магнит не обнаруживает алюминий или плохое медное соединение.
  Никакого подключения/выпрямления/CMOS действия.
- FAQ снова предлагает резать/шлифовать рёбра как минимальный
  путь, хотя Arabic cooling/case содержат no-cut shroud.
  Требуемая толщина pad зависит от реального зазора.
  Furmark под разгоном и универсальные 85/90°C пределы
  не были проверены на нашей плате.
- FAQ требует старый firmware symlink как решение почти
  каждого чёрного экрана, но подробная Linux глава говорит,
  что новый firmware package уже содержит собственный blob,
  а symlink условен. «Все графические Flatpak ломают Mesa»
  и «любой Wayland заменяй X11» шире исходных случаев.
  zRAM32GB здесь **прямо расходится** с подробным Linux/OC
  советом отключить ZRAM ради zswap+file swap. Ничего
  из host boot/memory настроек не менялось.
- `mitigations=off`/`nosmt=force` снимают safeguards/SMT
  ради неповторённой игровой метрики. «Слишком сильный
  undervolt безопасен и за секунды исправим» противоречит
  ранее сохранённым no-boot/неудачному CMOS recovery.
  40CU на чужой сборке не доказывают состояние нашей,
  и patched OS image ранее сообщал fan/gamepad regressions.
- «Восстановление только CH341A/J4004, SOIC clip не
  работает» нельзя принять для текущей платы: оператор
  сообщил, что уже прошивал через F1. Это не подтверждает
  независимый путь recovery, но опровергает слово «только».
  VCN shipping encode недоступен — не доказательство
  физического отсутствия. Windows/macOS/цены/FPS/AI
  краткие ответы тоже относятся к своим датам и источникам.

Следующая отдельная непрочитанная глава — Arabic
`troubleshooting.md`, затем весь остальной исходный импорт,
privacy/rights/SAST, технический и независимый review.
Native120/176/559 не изменён.

## Arabic troubleshooting: роль документа разобрана

Отдельная Arabic `docs/ar/troubleshooting.md` прочитана полностью:
22 175 байт, 114 строк, SHA-256
`af06066f5bc05ee311c81fb1d147d08b73c72ba879ffe2e046a7bd4f8661a27b`.
Диапазоны 1–90, 91–114 без renderer loss. Local pinned Git blob
совпал после EOL нормализации; current upstream не проверялся.
53 relative link occurrences ведут к существующим файлам,
преимущественно English главам; linked/remote bodies не проверены.
Privacy prefilter6patterns без совпадений, не clearance всего
корпуса. Receipt, provenance и14 issuegroups:
`phase86-arabic-troubleshooting-*.json`.

- Таблица «симптом → причина → исправление» сводит чёрный
  экран, llvmpipe и случайные падения к одной-двум причинам
  без target POST/log/voltage evidence. Отключать IOMMU,
  менять Wayland/GRUB/initramfs, поднимать напряжение на
  25–50mV или трогать BIOS по такой строке нельзя.
  No-cut охлаждение и no-boot undervolt случаи остаются.
- Самая опасная строка38: отсутствие POST только с NVMe
  приписано Windows EFI-разделам, после чего предлагается
  `wipefs -a` на другом ПК. Это уничтожение данных без
  идентификации точного диска, backup и доказательства,
  что firmware вообще дошла до загрузчика. Ничего не
  стирали.
- Suspend «не работает, отключи» на59 противоречит
  Arabic buying совету auto-suspend около10W. Ни один
  источник не доказывает wake/power state текущей платы
  или пригодность для контроллера Waveshare. Stock24CU
  на66 — ожидаемое состояние, а не поломка; 40CU image
  ранее сопровождался fan/gamepad regressions.
- J4004/CH341A как единственный recovery и «SOIC clip
  никогда» на97 не согласуется с сообщением оператора
  об успешной прошивке через F1. При этом F1 ещё не
  независимый восстановительный gate. Источник сам на100
  допускает Pi Pico, что тоже рушит слово «только».
  3.3V на питании программатора не доказывает уровни
  сигнала/изоляцию шины. «Память не грузится» не
  доказывает изменение ROM bytes; строка101 даже говорит
  об «USB update» в контексте BIOS настроек. Ни read/write,
  ни CMOS/flash действий не выполнялось.

Полный отдельный machine receipt
`phase86-arabic-md-cohort-reconciliation.json` сверил **19 из19**
Markdown файлов **только этой Arabic docs/ar папки**: raw hashes
совпадают, строки документной роли учтены, исходные байты
не менялись. Первый проход cohort check exit1 из-за различия
схемы Phase68 (`new_renderer_truncation` вместо
`renderer_truncation`); исправленная проверка прошла. Это
не проверка всех импортных записей, linked primary sources,
media, firmware, приватности, прав или hardware.
Следующий отдельный источник — English `docs/en/00-start-here.md`;
весь остальной импорт, privacy/rights/SAST и независимый review
остаются открытыми. Native120/176/559 не изменён.

## English start-here: роль документа разобрана

Отдельная English primary `docs/en/00-start-here.md` прочитана
целиком: 9 555 байт, 141 строка, SHA-256
`35d2bc7781a85a3b2afe2bae266302d8785261554f63fbec38756ea0bac1ded9`.
Диапазоны 1–90, 91–141 без renderer loss. Local pinned Git blob
совпал после EOL нормализации; current upstream не проверялся.
27 relative links ведут к существующим файлам, их тела
не проверены. Privacy prefilter6patterns без совпадений,
не clearance всего корпуса. Receipt, provenance и11 issuegroups:
`phase87-english-start-*.json`. Arabic перевод ранее разобран
отдельно; его чтение не подменяло English source.

- Линейная схема «power → срезать рёбра → Linux → OC →
  WiFi → игра» описывает **одну** сборку. No-cut shroud уже
  встречался в импортных источниках; проводная сеть, штатная
  частота и открытая плата возможны как отдельные состояния.
  Это не повод резать, паять или разгонять текущую плату.
- 235W/8pin/copper и нарисованный порядок сборки не дают
  target polarity, current/connector/harness rating. Картинка
  и вращение вентилятора — слабые признаки POST, не
  verified ROM, coldboot или input-control proof.
- Схема делает navi10 firmware symlink типовым шагом,
  хотя подробная Linux глава говорит: новый firmware package
  уже может содержать Cyan Skillfish blob, symlink условен.
  «Проверь GPU через `vainfo`» противоречит той же Linux
  главе, где `vainfo` может закономерно не работать из-за
  недоступного VCN. VA-API decode и RADV рендеринг —
  разные проверки. Никаких OS/driver команд не запускалось.
- BIOS VRAM512, IOMMU off и CMOS after every USB flash
  не приняты как board-specific boot policy. Нет exact
  image/dump/recovery. 2000MHz/+30%FPS — условная игровая
  метрика, не цель для всех нагрузок. «ROCm dead end»
  сильнее предыдущего экспериментального modified-MEC HIP
  отчёта и не разрешает PSP/VCN выводов.
- «Все строки checklist закрыты → готово» означает
  onboarding сценарий автора, не аудит всего импорта,
  не Waveshare/gamepad/power design и не hardware acceptance.

Следующий отдельный непрочитанный источник — English
`docs/en/01-what-is-bc250.md`; весь остальной импорт,
privacy/rights/SAST и независимый review остаются открытыми.
Native120/176/559 не изменён.

## English identity: роль документа разобрана

Отдельная English primary `docs/en/01-what-is-bc250.md`
прочитана целиком: 19 126 байт, 170 строк, SHA-256
`b90ad77c50b3fbbf1b778ef8248e0a07bc1de319200919f53493441a57c1f7b7`.
Диапазоны 1–90, 91–170 без renderer loss. Local pinned Git blob
совпал после EOL нормализации, нынешний upstream не проверялся.
21 relative link ведёт к существующему файлу, но linked
technical bodies/remote pages не проверены. Privacy
prefilter6patterns без совпадений, не clearance всего корпуса.
Receipt, provenance и10 issuegroups:
`phase88-english-identity-*.json`. Arabic перевод разбирался
отдельно, но его receipt не заменяет английский source.

- English original сам пишет «no x86 BIOS you know», но далее
  говорит о BIOS3.00 UMA и reset. Точная UEFI/ROM-структура
  должна выводиться из байт, не из вводной метафоры.
  Сходство с PS5 и история leftover silicon/«jailbreak
  same way» — provenance гипотезы из сообщества, не
  модель PSP-авторитета на этой плате.
- `gfx1013` здесь назван RDNA2, Arabic AI назвала RDNA1.x.
  Нужна независимая IP/ISA идентификация. «VCN None»
  — известная недоступность штатного encode path, не
  доказательство, что физического блока нет. Generic
  amdgpu/Mesa и отсутствие официального board-specific
  Windows драйвера/даташита тоже разные утверждения.
- В таблице **256bit×14Gbps÷8=448GB/s** — номинальная
  арифметика. Она не согласуется с рассказом «stock256→
  OC445GB/s» как с тем же default state. TDP220W, mining
  draw67–85W, размеры 340/310mm, DP1.4/second port и
  eGPU/LED окраска получены из разных источников и
  не замерены на нашем экземпляре.
- J1000/J2000/J2001/PGD diagrams заимствованы из
  внешнего `hardware.md`. Фраза **«324W safely»**
  выходит за пределы умножения3×9A×12V: нет проверки
  derating, проводов, контактов, платы, PSU и ориентации.
  Это не разрешение питать плату или Waveshare.
  Paper-shimming bent board не становится безопасным
  ремонтом из-за одного рассказа. Никаких pin/power/
  firmware/board действий.

Следующая отдельная непрочитанная глава — English
`02-buying.md`; весь оставшийся импорт, privacy/rights/SAST
и независимый review открыты. Native120/176/559 не изменён.

## English buying: роль документа разобрана

Отдельная English primary `docs/en/02-buying.md` учтена целиком:
21 842 байта, 161 строка, SHA-256
`f887ba67f27c7fb9979847448cee4320f2beee74690bbb9524d91e57d471ce01`.
Диапазоны 1–90, 91–161 без renderer loss. Шесть строк с
контактами/непроверенной репутацией рассматривались только
в санитизированном виде; имена/контакты в active docs не
перенесены. Исходные байты сохранены. Local pinned Git blob
совпал после EOL нормализации; нынешние объявления/upstream
не проверялись.15 relative links ведут к существующим файлам,
их тела не проверены. Privacy prefilter8patterns — не
clearance всего корпуса. Receipt, provenance и11 issuegroups:
`phase89-english-buying-*.json`. Arabic перевод ранее
разбирался отдельно, но не заменил English primary.

- Цены/комиссии/валюты/поставки из2025–2026 — исторические
  снимки. Дохлая донорская плата, голая рабочая плата и
  готовая система — разные комплектации. Старый URL не
  подтверждает продавца или гарантию сегодня. Путь
  перевода денег на частную карту/чатный escrow не
  проверенная защита покупателя. Ни контакта, ни платежа,
  ни покупки.
- Масса «bare0.86kg» не согласована с «0.4kg with heatsink»
  в translated identity. Нет физического взвешивания
  или надёжной цифры для доставки. Фото объявления,
  установленная ОС и mod BIOS не доказывают ROM/chip/PSU
  identity и coldboot.
- «Любой P2–P5 BIOS можно перешить в community mod»
  не допускается как flash gate: нужны exact image/target,
  полный проверенный dump, независимое восстановление
  и согласование. Слова «fin variations не влияют»
  расходятся с cooling главой; idle/suspend10W не
  доказывают power/wake схему Waveshare и противоречат
  troubleshooting совету отключить suspend.
- Mesh/VRS/VCN/надежность шахтёрского оборудования
  сведены из сообщества, не target feature query,
  signed-PSP/SMU trace или статистика отказов. Непроверенные
  обвинения продавцов не повторялись и не принимались
  как факт.

Следующий отдельный непрочитанный источник — English
`03-power-supply.md`; весь остальной импорт, privacy/rights/SAST
и независимый review остаются открытыми. Native120/176/559
не изменён.

## English power-supply: роль документа разобрана

Отдельная English primary `docs/en/03-power-supply.md` прочитана
целиком: 45 272 байта, 382 строки, SHA-256
`04b890f321abc50e00d4c2696a79da98f3c3c116ac9a5fcd415747276bb20da9`.
Диапазоны 1–90, 91–180, 181–270, 271–360, 361–382 без
renderer loss. Local pinned Git blob совпал после EOL
нормализации; current upstream не проверялся. Четыре relative
links ведут к существующим файлам, но внешние hardware,
PSU datasheet, repos и видео не валидированы. Privacy
prefilter6patterns без совпадений, не clearance всего корпуса.
Receipt, provenance, inert arithmetic и16 issuegroups:
`phase90-english-power-*.json`. Arabic перевод читался
отдельно, но не заменял English original.

- Вводное «нет кнопки; 12V сразу включает» не охватывает
  описанные здесь AUTO_PWRON, PWR_SW, PSU PS_ON, fan-header
  `system_on` и OS shutdown. Это разные управляющие состояния,
  а не готовая схема Waveshare. Ни один pin/voltage/current
  текущей платы не измерен.
- PCIe nominal150W, три контакта×9A×12V=324W, запас
  PSU300W и wall/rail draw — разные пределы. «324W safely»
  из умножения не следует. Подписи видео приблизительны:
  при12V 17A=204W, не~190W;21A=252W, не~240W.
  Ничего из этого не квалифицирует жгут, rail, контакт
  или плату.
- J1000/J2000/J2001/PGD/LED pinouts и ориентация
  заимствованы из внешних документов. Разветвление **одного**
  PCIe кабеля на соседние разъёмы не повышает upstream
  пропускную способность. Соседние рекомендации >=16AWG
  и «18/20AWG acceptable», срезать защёлку и заменить
  обжим пайкой — не единая безопасная спецификация.
  Никакой harness/cut/crimp/solder работы.
- Для будущей роли controller источник даёт два разных
  **непроверенных** lead: ESP32 пассивно видит Bluetooth
  advertisement Xbox и замыкает PWR_SW, при этом HID
  pairing остаётся у ПК; коммерческий no-solder adapter
  следит за fan-header `system_on` и держит PS_ON ещё
  несколько секунд. Ни один не демонстрирует Waveshare
  gamepad forwarding, точное питание/отключение BC-250,
  standby/fault timing, J004/F1 или PSP SPI substitution.
  Их схемы/код/сигналы не проверены.
- True-ATX mod снимает дроссель и меняет плату — это
  необратимый путь, не выбранный пользователем. GST280
  6pin→8 adapter выглядит без пайки, но оставляет
  два обратных контакта незаполненными; current return,
  ключи и ~280→252W «usable» без вывода не проверены.
  HP startup/MeanWell terminals/ATX paperclip — разные
  опасные рецепты, не выполнялись. Не покупали и не
  подключали PSU.

Следующая отдельная непрочитанная глава — English
`04-cooling.md`; весь остальной импорт, privacy/rights/SAST
и независимый review остаются открытыми. Native120/176/559
не изменён.

## English cooling: роль документа разобрана

Отдельная English primary `docs/en/04-cooling.md` прочитана
целиком: 36 591 байт, 307 строк, SHA-256
`7762ef3ca5154c95987d9d36f39d7f67ba70f936d06e2eac5fc0deff63114bc8`.
Диапазоны 1–90, 91–180, 181–270, 271–307 без renderer
loss. Local pinned Git blob совпал после EOL нормализации;
current upstream не проверялся. Пять relative links ведут
к существующим файлам, linked/remote thermal/model bodies
не подтверждены. Privacy prefilter6patterns без совпадений,
не clearance всего корпуса. Receipt, provenance и13
issuegroups: `phase91-english-cooling-*.json`. Arabic перевод
читался отдельно, не вместо English original.

- Главный для пользователя вывод **из самого English source**:
  вступление и «minimum» предлагают шлифовать рёбра,
  но82 говорит, что хороший кожух даёт схожий выигрыш
  без удаления, а135–136 описывают case с исходными
  **нетронутыми рёбрами** и push-pull. Это не
  target-board тест, но снимает «резать обязательно».
  Никакой резки, шлифовки или монтажа не было.
- На11 сказано «у GDDR6 сзади нет сенсора», а таблица
  17–26 даёт температуры памяти без метода измерения.
  SSD81.8°C — предел конкретного диска, не всех NVMe.
  Pixel artifacts и freezes могут иметь разные причины.
  Десятиминутный чужой 40CU/2GHz compute report
  достиг107°C GPU/100°C CPU; из него не следует
  «1500MHz устойчиво бесконечно» для каждого экземпляра.
- P12 Pro имеет max2100RPM в таблице99 и 600–3000RPM
  в строке129. Серийные вентиляторы не гарантируют
  буквального удвоения давления, а коэффициент
  излучения анодирования не обосновывает сокращение
  всей площади радиатора на45%. Все числа из разных
  builds/video, не наш стенд.
- AIO/custom loop и профили350–400W от розетки
  не квалифицируют PSU, connector и pump-failure риск.
  Фраза «board fan control может вести помпу+~5 fans»
  не даёт rating разъёма. `nct6683` наблюдение и
  forced `nct6687` PWM write — разные полномочия;
  chip/fan2 mapping и BIOS/OS ownership не проверены.
- PTM/pad размеры и зазоры отличаются по сборке:
  26×30 и40×80×0.25 не являются одним точным cut.
  VRM1mm/GDDR6 2mm и front-memory1.5mm/back2mm
  не заменяют измерение прижима/изоляции. Принимать
  LM, монтаж, стресс в Furmark или OC из источника
  как действие не разрешено; ничего не запускалось.

Следующий отдельный непрочитанный источник — English
`05-case.md`; весь остальной импорт, privacy/rights/SAST
и независимый review остаются открытыми. Native120/176/559
не изменён.

## English case: роль документа разобрана

Отдельная English primary `docs/en/05-case.md` прочитана целиком:
34 693 байта, 328 строк, SHA-256
`f29a4043ea1ed271f93704912b08e80ad098d9610ed591b1b71ed8e826275b67`.
Диапазоны 1–90, 91–180, 181–270, 271–328 без renderer
loss. Local pinned Git blob совпал после EOL нормализации;
current upstream не проверялся.16 relative links ведут к
существующим файлам, linked/remote model bodies не проверены.
Privacy prefilter7patterns без совпадений, не clearance всего
корпуса. Receipt, provenance, exact-name stat и13 issuegroups:
`phase92-english-case-*.json`.

- English source сам предлагает **friction-fit cooling sleeve без
  резки и винтов в плату** (строки7,53–60), несмотря на
  «большинство корпусов предполагают обработанные рёбра»
  на45. Чужой70°C/150W отчёт не доказывает тепловой режим
  нашего экземпляра, но «резать обязательно» неверно даже
  в собственной книге. Ничего не резали и не печатали.
- Каталог PSU-family/вентиляторов — фильтр механики,
  не электрическая квалификация. «Любой PSU в sleeve»
  значит прорезь под провод, не совместимость напряжения,
  контактов или автоматики питания. Access hole и
  трёхпозиционный CMOS switch — не проверенный pinout/
  безопасная операция. Популярность, фото и внешние STLs
  не доказывают fit или cooling.
- Видео «Steam Machine Pro» показывает ESP32 relay для
  удалённой подачи питания, но не Waveshare, HID gamepad
  forwarding или PSP SPI. Pi Zero 2 HUD через USB gadget
  показывает состояние и имеет свой vc4 patch; чтение
  напряжения вентилятора для dimming — не verified
  wake/power control. Generic ITX «любой корпус»
  основан на одном DeepCool примере.
- В импортной `assets/stl/` метаданными сейчас61 запись.
  Exact-name scan chat-tagged таблицы не нашёл в **этой
  директории** три несокращённых имени archive/composite
  моделей; остальные выбранные точные имена присутствуют.
  Сокращённые placeholders не объявлялись отсутствующими.
  «All chat hosted files mirrored» поэтому не подтверждено
  для указанной папки; это не глобальный поиск по архиву
  и не проверка геометрии/прав.
- Cross-language structural receipt показывает важное:
  Arabic case345 строк содержит **Steam Cube** как явно
  ненапечатанный CAD concept, а English primary328 строк
  этого раздела не имеет. Нельзя автоматически считать,
  что English версия включает все сведения перевода.
  Ни модель, ни плата не тестировались и не покупались.

Следующий отдельный непрочитанный источник — English
`06-linux.md`; весь остальной импорт, privacy/rights/SAST
и независимый review остаются открытыми. Native120/176/559
не изменён.

## English Linux: роль документа разобрана

Отдельная English primary `docs/en/06-linux.md` учтена целиком:
56 692 байта, 578 строк, SHA-256
`e540f2251f41fb8ff640c1f49a28c77c06fe1133eb5bb7027fcd68a84288cb8f`.
Диапазоны 1–90, 91–180, 181–270, 271–360, 361–450,
451–540, 541–578 без renderer loss. Одна строка с общим
объяснением `sudo` рассмотрена санитизированно; никаких
значений доступа там не было и не переносилось. Local pinned
Git blob совпал после EOL нормализации, current upstream
не проверялся.12 relative targets существуют, linked/remote
scripts/images/issue bodies не проверены. Privacy
prefilter6patterns не whole clearance. Receipt, provenance
и16 issuegroups: `phase93-english-linux-*.json`.

- English primary сам противоречит обязательному navi10
  symlink во вступлении: позже говорит, что современный
  firmware package уже содержит Cyan Skillfish blob, а
  ссылка нужна лишь при конкретной ошибке. Fedora43
  названа не нуждающейся в Mesa COPR, но скопированный
  setup script его включает; Arch official Mesa достаточно,
  но выше дана старая Chaotic/TKG цепочка. Это
  разные версии/source trust, не инструкции к исполнению.
- Bazzite patched image под `latest` не pinned release.
  Важно для проекта: сама English глава признаёт, что
  40CU образ на части сборок ломает **вентилятор и Xbox
  gamepad**. Чужой custom kernel не гарантированное
  исправление. Нельзя перенести этот OS rung в будущий
  Waveshare controller plan без отдельной проверки.
- `mitigations=off` в начале подан как нужный, затем
  назван optional/security tradeoff. IOMMU disabled
  blanket не доказан для нашей платы и ослабляет
  isolation. TTM/GTT/UMA/zswap настройка почти всей
  общей памяти тоже не universal safe profile.
  CoreOS UMR register writes и ACPI AML override —
  live boot/hardware-facing действия. Ничего не писали.
- Flowchart предлагает `vainfo` для GPU acceleration,
  позднее глава ожидает его сбоя из-за VA-API/VCN.
  Video decode и RADV rendering разные каналы.
  `vulkaninfo`, dmesg, debugfs clock и `pp_dpm_sclk`
  по одному не доказывают загрузку конкретной игры, CU map
  или VCN. Нет target-board readback.
- `dmesg_restrict=0` раскрывает kernel logs; Nuvoton
  `force=true`, `sensors-detect YES-all` и `nct6687`
  дают риск неверной привязки и право PWM write без
  карты контактов. Историческая kernel matrix не current
  target boot. Source `rm -rf` shader caches/остановка
  служб/изменение bootloader оставлены невыполненными.

Следующая отдельная непрочитанная глава — English
`07-windows.md`; весь остальной импорт, privacy/rights/SAST
и независимый review остаются открытыми. Native120/176/559
не изменён.

## English Windows: роль документа разобрана

Отдельная English primary `docs/en/07-windows.md` прочитана
целиком: 14 222 байта, 126 строк, SHA-256
`2cdad9d548736c08fa0d8d757986f26f140cd5205e57e53f6186ecc35d85cd7d`.
Диапазоны 1–90, 91–126 без renderer loss. Local pinned Git
blob совпал после EOL нормализации, current upstream/release
не проверялся. Восемь relative links существуют, linked
remote drivers/7z/commits не проверены. Privacy
prefilter6patterns без совпадений, не clearance всего корпуса.
Receipt, provenance и12 issuegroups: `phase94-english-windows-*.json`.
Arabic перевод был отдельной записью, не замена English.

- Code43, PCI `1002:13FE` и отсутствие игрового Windows
  драйвера на начало2026 — исторический срез, не
  сегодняшний PCI readback или обзор всех текущих
  выпусков. Одна BIOS DeviceID попытка не доказывает
  eFuse/невозможность другого перехода. VM/IOMMU
  «не выйдет никогда» тоже не испытано на target.
- Keshas PSP-driver описывает SOS/BAR5/NBIO MMIO,
  но сам признаёт отсутствующие GPCOM/TMR/GPU firmware
  этапы. Это **не** подмена PSP-подписи SPI-записи и
  не загрузка изменённого BIOS без платы. English
  00.00.01.7z и код внешних repos не скачивались,
  не собирались и не запускались.
- Другой WDDM2/D3D9 каркас без shader compiler/CP
  microcode/современных API — не игровой драйвер.
  Source resource list ошибочно зовёт Linux governor
  и Linux 40CU kernel patch Windows средствами.
- Testsigning, SecureBoot off, PowerShell/pnputil
  installer снижают boot trust и требуют точного
  бинарника/подписи/recovery, которых здесь нет.
  Remote-brick leak story сам source называет слухом;
  фальшивые exe/April-Fools — повод проверять
  происхождение, а не разрешение запускать GitHub
  бинарники. ОС/BIOS/driver не менялись.

Следующая отдельная непрочитанная глава — English
`08-bios.md`; весь остальной импорт, privacy/rights/SAST
и независимый review остаются открытыми. Native120/176/559
не изменён.

## English BIOS: роль документа разобрана

Отдельная English primary `docs/en/08-bios.md` учтена целиком:
35 682 байта, 406 строк, SHA-256
`cb79667db26943d608137ef8212e0400a24df5001f862f0fac18fc5c45530b80`.
Диапазоны 1–90, 91–180, 181–270, 271–360, 361–406
без renderer loss. После первого вывода социального ника
фильтр расширен; строки34/162/349 далее рассматривались
санитизированно, ники не перенесены в active docs.
Исходные байты не менялись. Local pinned Git blob совпал
после EOL нормализации, current upstream не проверялся.
Десять relative links существуют, linked/remote bodies
не валидированы. Privacy prefilter7patterns не clearance.
Receipt, provenance, exact-name stat и18 issuegroups:
`phase95-english-bios-*.json`.

- «Единственный надёжный J4004, SOIC clip не работает»
  — сильнее имеющихся доказательств. Ты сообщал об уже
  успешной прошивке через F1; это не даёт независимый
  recovery gate, но опровергает слово «единственный».
  J4004 2×4 рисунок, шесть signal labels/два residual
  контакта, ориентация и part variants не измерены на
  целевой плате. Никакого wiring/programmer run.
- Исторические SHA из guide не сопоставлены с actual
  target ROM bytes. Prefix16 слабее полного SHA, а два
  одинаковых `P5.00_clv` без независимой provenance не
  доказывают origin. P3 «safe default» не делает
  открытые timing/voltage поля безопасными.
- Таблица говорит «files mirrored under assets/firmware»,
  но в **этом импортном репозитории** папка сейчас
  содержит только `DISCLAIMER.md`:0 из11 точных названий
  ROM/ZIP/tool таблицы там нет. Это не утверждение
  об отсутствии где-либо ещё. ZIP size не raw ROM size.
- AFU `/N` меняет NVRAM; `Flash.nsh` с именем
  `Robin5.00` путает bundled stock и renamed mod.
  Internal flashrom `boardmismatch=force` снимает
  предупреждение. NeoProgrammer erase-before-open
  не имеет двойного backup/readback; external flashrom
  snippet не показывает точный diff двух чтений и
  post-coldboot контроль. Ни одна команда не исполнялась.
- Неправильные CMOS часы — слабый proxy для reset;
  Cyberpunk UMA 60→66→76 смешивает OC/FSR/settings.
  `srep` автооткат **не заработал**. `psptool` presumed
  SMU entry, низкоуровневые TPMS1/J2/I2C/PGD/пин9
  и blanket SecureBoot/IOMMU советы не выводят
  безопасный Waveshare/J004 или PSP-signature transition.
  Ни BIOS, ни CMOS, ни PSP/firmware/hardware записи.

Следующая отдельная непрочитанная глава — English
`09-overclock-undervolt.md`; весь остальной импорт,
privacy/rights/SAST и независимый review открыты.
Native120/176/559 не изменён.

## English overclock-undervolt: роль документа разобрана

Отдельная English primary `docs/en/09-overclock-undervolt.md`
учтена целиком: 75 030 байт, 645 строк, SHA-256
`833ffc560568cfa8992da339dda72f15b148cabad1411eda7c27dda47baee2f4`.
Диапазоны 1–90, 91–180, 181–270, 271–360, 361–450,
451–540, 541–630, 631–645 без renderer loss. Строки381/630
с access credential скрыты; первое чтение выпустило фрагмент
из630 до расширения фильтра для `pwd`. Значение здесь
не повторено и в active docs не перенесено. `$(pwd)` на418/419
— shell working-directory, не credential. Raw source
сохранён. Local pinned Git blob совпал после EOL
нормализации, current upstream не проверялся.24 relative
links существуют, linked/remote bodies не валидированы.
Privacy prefilter8patterns не clearance. Receipt, provenance,
inert arithmetic и18 issuegroups: `phase96-english-oc-*.json`.
Arabic перевод разбирался отдельно.

- Ранние строки55–65 советуют сразу `enable --now` SMU
  governor, но158 говорит, что он намеренно поставляется
  отключённым до проверки кривой из-за boot black-screen.
  Service running, requested clocks и реальные частоты/
  напряжения на target — разные события. Ничего не
  устанавливалось/включалось.
- «CPU8 cores нельзя, нужен PSP signature bypass+SMU
  microcode» на229 — community вывод, не fuse/readback
  или доказанный маршрут подписи. GPU CU unlock — другое.
  Название GPU регистров `SPI_PG_ENABLE_STATIC_WGP_MASK`
  относится к shader/power-gating, **не** к serial SPI
  с BIOS или PSP signed-entry подмене.
- Kernel patch при init и runtime UMR CC/SPI/RLC после
  загрузки драйвера не доказаны эквивалентными.
  `cu_map.sh`/health manager/40CU benchmark не
  проверялись на нашей плате; source сам предупреждает
  о scattered harvest и hard-lock при плохом CU.
  Измерение FurMark91→110 равно **+20.88%**, не указанным
  ~25%. Superposition4647→6863 даёт~47.69%, но это
  один чужой прогон, не стабильность.
- «Слишком сильный undervolt безвреден и очищается
  за5секунд» на333 расходится с сохранёнными no-boot/
  неудачным CMOS recovery историями. CPU4GHz/voltage
  советы сами показывают quick-pass→game crash и разные
  1300/1325mV limits. Электрической безопасности
  чисел нет. 40CU2GHz достиг107°C GPU/100°C CPU за
  10мин в чужом опыте, а J2000/J2001 power wiring
  не квалифицировано.
- UMA «safe, everyone do it» рядом с играми, которые
  зависают/падают на маленьком split, и несовместимыми
  ZRAM/zswap/TTM командами — не target memory policy.
  GDDR6 clock/timing через BIOS может не дать POST,
  CMOS не гарантирует восстановления. Заявление о
  14.75GB для LLM почти исчерпывает общий pool.
  Никаких SMU/CU/clock/voltage/stress/host/BIOS/
  firmware/hardware операций не выполнялось.

Следующий отдельный непрочитанный источник — English
`10-wifi-bt.md`; весь остальной импорт, privacy/rights/SAST
и независимый review открыты. Native120/176/559 не изменён.

## English WiFi/Bluetooth: роль документа разобрана

Отдельная English primary `docs/en/10-wifi-bt.md` учтена целиком: 17 701 байт, 182 строки, SHA-256 `19d21ee5d8f97647e1aeef926b219ec2f55c0899d69863ebf10fce4e7a46e416`. Диапазоны 1–65, 66–125, 126–182 без renderer loss. Широкий фильтр отметил строку 111 по `PWD`; ручная проверка установила, что это shell working-directory в неприменённом DKMS-рецепте, не пароль. Исходные байты сохранены, local pinned Git blob совпал после EOL-нормализации. Локальных относительных ссылок в главе нет; удалённые Telegram/GitHub/магазин/Intel/TP-Link страницы не открывались и не подтверждались. Privacy prefilter не является clearance. Receipt и десять групп замечаний: `phase97-english-wifi-*.json`.

- Списки aic8800d80/Digma/Realtek основаны на отдельных сообщениях и этикетках; без USB VID:PID, ревизии чипа, ядра и Bluetooth-пути это не подтверждённый выбор для нашей платы. «Самый надёжный» и «работает сразу» не общая гарантия.
- Сбои соединения могут идти от драйвера, питания USB или радиоусловий. Источник смешивает эти гипотезы; общие сообщения о RTL8111/8168 не подтверждают отказ onboard NIC именно здесь. На RTL8821/8822 даже после `rtw88` один отзыв сохраняет сбои.
- `biglinux/rtl8831` для AX900 источник сам помечает непроверенным на BC-250. Для TP-Link TX10UB Nano заявлен сторонний WiFi-драйвер, но Bluetooth самим изготовителем для Linux не поддерживается. Это не проверка пары WiFi+BT.
- RPM/DKMS, `rpm-ostree`, remote `curl`, `git clone`, `make install`, reboot, `rmmod`/`modprobe`, MOK, `usbreset` и persistent modprobe-конфигурация в тексте — рецепты изменения хоста, не выполненные здесь. Версионные предупреждения kernel 7.x/Debian и ветка BT ограничивают обещание повторяемости.
- Замер 150 против 190 Mbit, USB3 RF-white-paper и перестановка порта не являются измерением нашей платы или доказательством подключения геймпада. Эта глава вообще не задаёт Waveshare как контроллер питания/геймпадов и не содержит пути подмены PSP/SPI BIOS.

Следующая отдельная непрочитанная глава — English `11-gaming.md`; весь остальной импорт, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён. Никаких драйверов, модулей, сетевых, USB, BIOS или физических действий не было.

## English gaming: роль документа разобрана

Отдельная English primary `docs/en/11-gaming.md` учтена целиком: 26 574 байта, 210 строк, SHA-256 `bee34e9da8d0e661dcb374af32f73c87084babcd91b55d09a7dfd496f1831fd3`. Диапазоны 1–70, 71–140, 141–210 без renderer loss и совпадений privacy prefilter; это не полное privacy clearance. Исходные байты сохранены, local pinned Git blob совпал после EOL-нормализации. Восемь относительных ссылок существуют, их тела и удалённые Telegram/Reddit/YouTube/Sheet/драйверные источники здесь не проверялись. Receipt, provenance и двенадцать групп замечаний: `phase98-english-gaming-*.json`.

- Число `GPU Limited Percentage 36.5%` в одном benchmark не является прямым замером занятости GPU на 36.5%; вывод «GPU простаивает на две трети» и универсальный CPU bottleneck из него не следует. Смешанная таблица FPS включает разные игры, системы, драйверы, частоты, пресеты, FSR/FG и автосубтитры. Строка RX6600 прямо не относится к BC-250; «Windows, RADV» и минимум 3 при среднем 70 требуют проверки происхождения.
- Совет сразу разогнать 1500→2000MHz и открыть 40CU не является установкой безопасного профиля. +33.3% частоты не гарантируют +30% FPS, а один отчёт о Doom не доказывает широкий прирост, исправность вентилятора/геймпада или холодный старт. Обязательность резать/менять охлаждение из этого источника тоже не следует.
- FSR, frame generation, LSFG и экспериментальные DP4a/FSR4 пути нельзя складывать как нативный FPS или подтверждение задержки. Обещание официальной RDNA2 FSR4 к 2027 году — прогноз внешнего источника, не проверенный результат.
- UMA 512MB/4GB, GTT, zswap и `mitigations=off` имеют разные риски и противоречащие по играм эффекты. Источник сам описывает llvmpipe, артефакты, зависания и спорный выигрыш от отключения защит. Ничего в boot/kernel/host не менялось.
- Категорические «не запустится» для античита, mesh/VRS и «Vulkan_NullVRS без побочных эффектов» зависят от версии игры и требуют отдельного воспроизведения. Таблица RT смешивает аппаратный RT с помеченным software path. Эмуляторные результаты и совет компенсировать предполагаемый RPCS3 GPU1000MHz разгоном CPU не являются диагностикой нашей платы.
- Глава не тестирует Waveshare, геймпады, VCN, питание или подмену подписанной PSP-записи в SPI BIOS. Никакие игры, драйверы, настройки ОС, разгон, прошивки или железо не запускались/изменялись.

Следующая отдельная непрочитанная глава — English `12-ai-llm.md`; весь остальной импорт, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## English AI/LLM: роль документа разобрана

Отдельная English primary `docs/en/12-ai-llm.md` учтена целиком: 21 673 байта, 215 строк, SHA-256 `c849e9396925de6335025f54118b195c2cf4ef8aa5e4eacc19aec7e1a0b7b13b`. Диапазоны 1–75, 76–150, 151–215 без renderer loss. Первоначальный широкий фильтр скрыл строки 51/140/157/176 по слову `token`; отдельная проверка установила, что речь о токенах модели/скорости, не учётных данных. Privacy prefilter не является глобальным clearance. Raw bytes сохранены, local pinned Git blob совпал после EOL-нормализации; восемь относительных ссылок существуют, их тела и удалённые GitHub/Discord/Telegram/YouTube/Hugging Face источники не проверены. Receipt, provenance, условная арифметика и 14 групп замечаний: `phase99-english-ai-*.json`.

- В этой главе `gfx1013` назван RDNA-1.x, тогда как English gaming называл ту же метку RDNA2. Ссылка на ISA `gfx1030` не определяет точно нашу плату. Первое категорическое «ROCm/HIP здесь не работает» и запрет HIP-сборки противоречат более позднему сообщению о HIP/PyTorch после изменения MEC firmware. Поздний рассказ не содержит независимого target dump/boot/readback и **не** разрешает вмешательство в PSP/SPI или прошивку.
- 16GB — общий пул OS+GPU, не 16GB выделенной видеопамяти. Указания `vram=12`, 65 536 контекста, `GPU_OVERHEAD=0`, TTM и длинного KV-cache не образуют проверенный безопасный профиль: сам источник сообщает OOM и гибель рабочего стола. При условных 4KiB-страницах `4194304` страниц равны 16GiB, то есть всему физическому пулу до расходов ОС; реальную единицу и текущий лимит надо проверять отдельно.
- `curl | sh`, AUR/apt/source build, systemd override/restart, `OOMScoreAdjust=-1000`, sysfs/modprobe, governor и модельные загрузки — рецепты изменения хоста, а не действия этого аудита. Защита Ollama от OOM-killer может перенести отказ на остальные процессы; обещание «memory-safe» не доказано.
- Разные 30–40, 59.5/66.1 и 78.7/87.5 tok/s получены на разных моделях, квантах, рантаймах и CU. Это не единый baseline нашей платы. Для видео с авто-субтитрами указанное 25.7→31.9 вычисляется как **+24.125%**, не 16–17%; 25.7→33.4 как **+29.961%**, не ~20% суммарно. Числа условные, видео не воспроизводилось. 66.1→87.5 даёт +32.375%, 59.5→78.7 — +32.269%, согласуется с округлёнными 32% в источнике, но не подтверждает стабильность 40CU.
- Отчёт о плате, падающей при CU сверх 36, ограничивает совет «разблокировать 40CU». Прирост от governor не бесплатный по теплу/питанию. Hackaday MTP и замечания про стабильность дистрибутивов оставлены как непроверенные сообщения, а не решение по нашей машине.
- Глава не содержит доказательства Waveshare/gamepad/power-controller пути или подмены PSP-подписи. Никакие пакеты, службы, лимиты памяти, модели, CU, ROCm/HIP, прошивки или железо не запускались/изменялись.

Следующая отдельная непрочитанная глава — English `13-macos.md`; весь остальной импорт, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## English macOS: роль документа разобрана

Отдельная English primary `docs/en/13-macos.md` учтена целиком: 6 227 байт, 53 строки, SHA-256 `fb98d8d219549094bb760f9925319fe340a0eb3d378ab5aba7c785f74152e1b0`. Диапазон 1–53 без renderer loss и совпадений privacy prefilter; это не глобальный privacy clearance. Raw bytes сохранены, local pinned Git blob совпал после EOL-нормализации. Шесть относительных ссылок существуют; их содержимое, Telegram/форум/GitHub/Dortania и актуальные списки поддержки не проверялись. Receipt, provenance и десять групп замечаний: `phase100-english-macos-*.json`. Arabic macOS глава была отдельным источником, не подменена этой.

- «Никто не сообщил об ускоренном macOS» в указанном сообществе — отсутствие отчёта, не доказательство невозможности во всех версиях. Глава не показывает и успешной загрузки macOS **без** GPU на нашей BC-250. Monterey recovery + OpenCore ZIP подтверждает подготовку архива, но не загрузку, Metal или восстановление.
- Утверждения «драйвер определяется только device ID» и «вмешаться можно только OpenCore» слишком абсолютны: совместимость архитектуры, функций и драйвера тоже важна, а сама глава позже приводит NootedRed как kext-путь для **других** AMD APU. Её же «ни один Ryzen iGPU никогда не работал» противоречит этому упоминанию. Это не делает NootedRed применимым к BC-250; текущие списки поддержки не проверены.
- «Нет поддерживаемого близнеца», история годового spoofing, прогноз интереса разработчиков и запрет VM passthrough — утверждения/оценки из внешних сообщений, не замеры платы. Identity `gfx1013` здесь классифицирован документом, без повторного PCI/ROM/driver-probe.
- Ссылки на OpenCore/FakePCIID/NootedRed/AMD-OSX оставлены библиографией, не инструкцией к установке. Не менялись ОС, разделы, bootloader, kext, драйверы, BIOS или железо. Глава не содержит пути Waveshare/gamepad/power-controller или подмены PSP-подписи.

Следующая отдельная непрочитанная глава — English `14-display.md`; весь остальной импорт, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## English display: роль документа разобрана

Отдельная English primary `docs/en/14-display.md` учтена целиком: 19 755 байт, 163 строки, SHA-256 `adf8d98201253fd3f21cf7655c0e0d0d7af2ff4181f907ee4da7ba6984e50f16`. Диапазоны 1–60, 61–120, 121–163 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, local pinned Git blob совпал после EOL-нормализации. Девять относительных ссылок существуют; их тела и удалённые Telegram/Reddit/GitHub/товарные источники не проверялись. Receipt, provenance и 12 групп замечаний: `phase101-english-display-*.json`. Arabic display учитывался отдельно.

- «Чёрный экран» не указывает однозначно на HDMI, кабель, драйвер или BIOS. Шаг «сбросить BIOS/перепрошить known-good» на строке14 выведен из чужого группового случая и **не** преодолевает наши dump/recovery/exact-image/readback gate. Ничего не сбрасывалось и не прошивалось.
- «DP→HDMI всегда передаёт видео без задержки» расходится с этой же главой: адаптер показывал картинку до GRUB, затем чёрный экран, а generic HDMI MST не давал видео вовсе. DP1.4/4K120/HDR10, таблица разрешений и кабелей не заменяют живую проверку линка, EDID, ОС и конкретного дисплея.
- Аудио-советы внутри главы не сводятся к «простой кабель всегда работает»: один проверенный адаптер, молчащие/меняющие тон другие, спор passive-vs-active и собственный вывод о chipset dependence. 5.1-«не работает» получено из внешнего обсуждения, не из ELD/ALSA/receiver измерения нашей платы.
- В начале «исправление приходит примерно с kernel6.17», ниже — «kernel6.17 изменил путь и сломал стандартный конфиг»; причинность и версия требуют отдельного kernel/config/ALSA доказательства. Custom kernel, Wayland/GDM, Mesa, Bazzite remix и USB DAC здесь не устанавливались. Remix проверялся автором на 9070XT, не на BC-250.
- Неприпаянный второй выход и две картинки через один DP MST hub — разные вещи. Поздний отчёт о StarTech MST не подтверждает второй физический GPU head и не гарантирует любой hub. DisplayLink и LAN streaming тоже не являются вторым нативным выходом; успешная передача игры на ноутбук не доказывает работу VCN encoder, геймпада через Waveshare или его питание.

Отдельный hash/UTF8 preflight сначала успешно записался в старый путь AI из-за ошибочного output аргумента checkpoint. Эти байты сохранены, старый AI preflight восстановлен прежней командой, display preflight повторён в верном пути; оба исправительных запуска exit0. Событие и исходный checkpoint: `phase101-display-dispatch-correction.json`. Исходные документы не менялись.

Следующая отдельная непрочитанная глава — English `15-emulation.md`; весь остальной импорт, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## English emulation: роль документа разобрана

Отдельная English primary `docs/en/15-emulation.md` учтена целиком: 20 954 байта, 158 строк, SHA-256 `3d5c2ff07f4e0d4d9524790161b2a389dd074c53c2c26e9e0e7dbc8068a08104`. Диапазоны 1–55, 56–110, 111–158 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, local pinned Git blob совпал после EOL-нормализации. Одиннадцать относительных ссылок существуют; их тела и удалённые Telegram/Reddit/видео/проекты не проверялись. Receipt, provenance, 11 групп замечаний и механический census таблицы: `phase102-english-emulation-*.json`. Arabic emulation учитывалась отдельно.

- **PSP здесь означает PlayStation Portable** и PPSSPP, а не AMD Platform Security Processor с подписанными компонентами BIOS. Отчёт о PSP в 4× разрешении не относится к подмене PSP-подписи.
- «Сначала разогнать до 2000MHz, возможно CPU4GHz, перед любой эмуляцией» выведено из одного рассказа о 1000MHz в Switch и расходится с самой главой, где retro названо лёгким, а PPSSPP работал без throttling. Это не безопасный профиль нашей платы и не основание резать/менять охлаждение. Разгон, governor и стресс не запускались.
- Таблица имеет 33 строки платформ: 24 помечены **общим ожиданием**, 8 — **сообщениями участников чата**, одна (Wii U) — вопросом без подтверждения. У 22 из 24 общих ожиданий стоит зелёная галочка; визуально их нельзя принимать за проверенные результаты BC-250. PS2/GameCube/Wii здесь не имеют отдельного замера на нашей плате.
- Switch/PS3/PS4 и Bloodborne/Drive Club/Uncharted — сообщения о конкретных играх/версиях, часто без точного конфигурационного следа. Stock Xenia «низкая скорость» и Canary «меню с геймпадом, игра чёрная» — разные варианты. Последнее подтверждает только чужой PC-ввод, **не** подключение геймпада через Waveshare.
- EmuDeck/RetroDECK/Steam input/Batocera, установочные пакеты, ОС-образы и эмуляторные ключи здесь не ставились и не загружались. Правовой и источник происхождения ROM/ключей остаются за оператором; фраза «искать binaries and keys» не поручение. RDNA2/gfx1013 классификация расходится с импортной AI-главой, где написано RDNA-1.x; это не новый аппаратный замер.

Следующая отдельная непрочитанная глава — English `16-usb-peripherals.md`; весь остальной импорт, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## English USB/peripherals: роль документа разобрана

Отдельная English primary `docs/en/16-usb-peripherals.md` учтена целиком: 21 235 байт, 201 строка, SHA-256 `bf4a52edabb07b5f3fb58f4d1d07a08466e28e0b5bca16283a8dc64d42ecca7f`. Диапазоны 1–70, 71–140, 141–201 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, local pinned Git blob совпал после EOL-нормализации. Девять относительных ссылок существуют; их тела и удалённые Telegram/4PDA/видео/товарные источники не проверены. Receipt, provenance и 13 групп замечаний: `phase103-english-usb-*.json`. Arabic USB учитывалась отдельно.

- Четыре задних порта и «нет внутренних headers» перенесены из внешнего справочника, не пересчитаны на нашей ревизии. «USB3 порт фактически x2» не имеет ясной электрической единицы и не равно двум PCIe-линиям M.2. Просадка 5V до 4.3/2.3–3.2V описывает одну проблемную плату; та же глава приводит другую, где bus-powered hub работает. Это не доказательство слабого питания каждой BC-250 или риска «сжечь порт».
- **Отдельно питаемый USB-хаб** — обратимый вариант без пайки, заслуживающий проверки перед любым изменением проводки. Но его питание, защита от обратной подачи VBUS и обнаружение устройств на нашей плате не измерены; покупка и подключение не выполнялись.
- Предложенная в источнике **резка VBUS и подача 5V от ATX** меняет топологию питания. Утверждение «общий БП автоматически избавляет от проверки земли» не заменяет проверку возвратного пути данных, ограничения тока, обратной подачи, порядка включения и защиты. Один успешный чужой хаб не даёт разрешения резать провод, паять или включать плату.
- Раздел хранилища одновременно называет M.2 только PCIe2.0×2 и уверяет, что SATA-протокольный M.2 SSD ставится прямо в слот. Поддержка SATA не следует из PCIe-линий; wiring слота здесь не проверен. ASM1166/PH516 — сообщения о разных контроллерах, не проверка нашего загрузочного пути. 5V питания SATA-диска и SATA-данные — разные контуры; buck-подключение взято из пересказа видео, без электрической квалификации.
- Замена всех `nvme` на `sda` в SteamOS repair script может выбрать чужой диск и не является универсальным исправлением. Никакие диски, разделы или скрипты не менялись. Вывод «dock video невозможно из-за лимита GPU» не согласуется с отдельным USB DisplayLink-путём в display-главе; единичный сбой дока не устанавливает причину.
- DS5Dongle использует **Raspberry Pi Pico 2W**, GameSir — собственный USB-приёмник. Ни это, ни рассказ о DualSense/UGREEN в USB2 не доказывают, что **Waveshare** управляет геймпадами, включением BC-250 или PSP/SPI BIOS. Bluetooth≥5 и портовые ограничения не подтверждены на нашем железе.

Следующие отдельные непрочитанные English primary источники — `faq.md` и `troubleshooting.md`; весь остальной импорт, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён. Ни USB/PSU/хаб, ни проводка, ОС, BIOS или железо не тронуты.

## English FAQ: роль документа разобрана

Отдельная English primary `docs/en/faq.md` учтена целиком: 16 536 байт, 185 строк, SHA-256 `b4b52d7cb1024dfe60dc322194822f36881c63ef7bd91e62e77afb18e4f8367f`. Диапазоны 1–65, 66–130, 131–185 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, local pinned Git blob совпал после EOL-нормализации. Все **48** относительных ссылок существуют; их техническое содержание и удалённые источники не перевалидированы этой проверкой. Receipt, provenance и 15 групп замечаний: `phase104-english-faq-*.json`. Arabic FAQ оставлен отдельной ролью. FAQ — карта предыдущих глав, не новое независимое измерение платы.

- Короткие ответы усиливают чужие сообщения до абсолютов: «нет кнопки, включается сразу от 12V» смешивает AUTO_PWRON/PWR_SW/PS_ON, «CMOS reset и бумажная прокладка при no-POST» не диагностика, а «VCN недоступен, значит всегда software encoder» не доказывает отсутствие кремния или фактический путь кодирования Sunshine.
- PSU≥300W/single-rail, EPS/PCIe распиновка, дымящийся кабель=«фальшивая медь», термопрокладки и 85/90°C пороги нельзя переносить на электрическую/тепловую безопасность нашей платы без измерений. Совет **стончать/резать стоковые рёбра как самый дешёвый путь** расходится с сохранённым в cooling-главах вариантом без резки. Никаких проводов, рёбер, PSU или стресс-тестов не трогали.
- FAQ повторяет устаревающие команды Bazzite/Fedora/COPR, обязательный firmware symlink, запрет всех Flatpak, универсальный X11, `mitigations=off`, `nosmt=force` и zRAM32 как быстрые решения. Они зависят от версии и несут системные/защитные последствия; ОС/boot/kernel не менялись.
- «Нет Windows-драйвера» — датированный статус, не закон кремния. «J4004 только, SOIC clip не работает» расходится с сообщённым оператором F1-прошиванием и само по себе не закрывает double-read, независимый recovery, точный образ и coldboot/readback gate. CMOS и чужой 5.00 hash не разрешают прошивку.
- 2000MHz/CPU4GHz/1.325V/«все 40CU», «слишком сильный undervolt безвреден» и 12GB VRAM — чужие настройки, а не безопасный профиль; undervolt абсолют расходится с сохранёнными no-boot/CMOS проблемами. DP→HDMI/audio, WiFi-драйверы, FPS/«CPU-bound», Mac-невозможность и цены также краткие исторические выводы, не target проверки.
- Ничего в FAQ не подтверждает управление BC-250 через Waveshare, вход геймпадов, PSP-подпись, F1/J004/SPI recovery или VCN. Ни аппаратные, ни firmware/host действия не выполнялись.

Следующая отдельная непрочитанная English primary — `troubleshooting.md`; затем English handbook cohort можно сверить по hash/line receipt, но это **не** завершение всего импорта. Privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## English troubleshooting: роль документа разобрана

Отдельная English primary `docs/en/troubleshooting.md` учтена целиком: 17 499 байт, 116 строк, SHA-256 `4a4cacb38f54227a7b62830734b165097de2a1d61697dce78107fcef48c41a98`. Диапазоны 1–60, 61–116 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, local pinned Git blob совпал после EOL-нормализации. Все 54 относительные ссылки существуют; их технические тела и удалённые GitHub/4PDA/Reddit/видео источники не валидированы. Receipt, provenance и 13 групп замечаний: `phase105-english-troubleshooting-*.json`. Arabic troubleshooting — отдельная роль. Таблица «симптом→вероятная причина→решение» не является доказанным диагнозом нашей платы.

- «Нет POST только с NVMe» не доказывает, что виноваты Windows-разделы. `wipefs -a` уничтожил бы метаданные диска; совет источника **не выполнялся**. Black screen сам по себе не подтверждает IOMMU, KWin, firmware symlink, kernel regression, CMOS/GRUB/initramfs или конкретную электрическую неисправность.
- Резка стоковых рёбер, фиксированные 80/90°C, +50/+25mV и ≥700mV — чужие условия, не безопасная рекомендация для нашей платы. «GPU crash всегда валит весь APU» и «ACPI error→acpi=off/noapic→перепрошить» слишком сильные переходы без target trace. «Нажать power button для wake» также расходится с FAQ «кнопки нет»; suspend-состояние требует отдельной проверки.
- 24CU в stock — не симптом поломки, требующий 40CU unlock. MangoHud 655%/`gpu_metrics`, governor, patch clocks, CPU-bound, headless glmark2 и swap/UMA рецепты относятся к разным слоям telemetry/driver/OS; не доказаны текущими частотами, напряжением, рендерером или памятью платы. Никакие скрипты, службы, boot flags, настройки BIOS или kernel не менялись.
- «J4004 только, clip не работает» противоречит сообщённому оператором F1-прошиванию и не заменяет double-read, независимый recovery, точный образ, coldboot/readback. Программатор 5V/не тот чип, CMOS «2–3 очистки» и чужая версия 5.00 не установлены как причина. No-POST после GDDR6 timings не доказывает, что испорчены именно **ROM-байты**, а не настройки.
- Предполагаемая BGA-трещина и reflow — спекулятивный и разрушительный «последний способ», не проведённый диагноз и не поручение на нагрев платы. WiFi/ISP/Windows/driver ответы датированы и не являются universal fixes. Ни дисков, проводки, ОС, напряжения, CMOS, прошивки или железа не касались.

**Сверка English handbook cohort:** все 19 отдельных Markdown-файлов `docs/en/` сошлись с live raw SHA-256, размерами, числом строк и собственными document-role receipts: суммарно 516 859 байт и 4 727 строк. Это **учёт ролей**, не повторное чтение linked bodies, не независимая проверка всех технических утверждений и не завершение импорта. Двенадцать строк по ролям ранее скрывались/санитизировались, включая не-секретные false positives и чувствительные фрагменты; privacy clearance нет. Машинная сверка: `phase105-english-cohort-role-reconciliation.json`. Следующий отдельный непрочитанный языковой источник — Russian primary `docs/ru/00-start-here.md`, ранее прошёл только hash/UTF8 preflight. Все остальные локали, исходники, binaries, native документы, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian start-here: роль документа разобрана

Отдельная Russian primary `docs/ru/00-start-here.md` учтена целиком: 13 754 байта, 141 строка, SHA-256 `0e2906b6bf4a1b95c5d1aa452dd6d8ec7e0f32d79ebaff1dbbe833633d2b8ec6`. Диапазоны 1–75, 76–141 без renderer loss и совпадений privacy prefilter (включая русские credential-слова); это не глобальный clearance. Raw bytes сохранены, prior phase46 hash/UTF8 preflight и local pinned Git blob совпали после EOL-нормализации. Все 27 относительных ссылок существуют; linked/remote тела не валидированы. Receipt, provenance, 12 групп замечаний и EN/RU структурная сверка: `phase106-russian-start-*.json`. Заголовки RU и English start-here стоят на одинаковых 18 позициях, но blobs имеют разные размеры/хеши; содержание не объявлено эквивалентным.

- Прямой маршрут «питание→обязательно проредить рёбра→Bazzite→fix firmware→2000MHz→WiFi→игра» — вариант сборки из источника, **не** список обязательных действий на нашей плате. No-cut stock-fin варианты сохранены отдельно. Чужие 235W, пин-аут, температурные цели и «есть картинка/крутится вентилятор значит POST» не устанавливают электрическую безопасность или cold-boot/readback. Никакой резки, проводки или нагрузки.
- Bazzite/Fedora43, Mesa, firmware symlink, COPR, kernel versions и `cyan-skillfish-governor-smu` зависят от версии и текущего драйверного состояния. Обязательный navi10→Cyan symlink не учитывает собственный firmware blob в нынешних сборках; `vainfo` относится к video API и сам не доказывает весь RADV rendering. Встроенные `dnf`, service enable, GRUB edit и reboot **не выполнялись**.
- VRAM512 dynamic, IOMMU Disabled, CMOS после flash и `nomodeset` — чужие OS/BIOS советы, а не target policy; IOMMU off имеет последствия для защиты/VM, CMOS не восстанавливает ROM. Раннее `enable --now` governor расходится с OC-главой, где он намеренно отключён до проверки кривой из-за риска чёрного экрана. 2000MHz/+30%FPS, 40CU и 700mV не являются безопасными пределами. Никаких BIOS/OC/CU/voltage изменений.
- «Нет аппаратного video encoder» сильнее установленной недоступности VCN через текущий firmware/driver путь. 16GB — общая GDDR6-память, не выделенные 16GB VRAM; «ROCm тупик» расходится с более поздним чужим HIP/MEC сообщением без независимого target proof. WiFi-донгл и игровая цепочка не подтверждают Waveshare/gamepad/power/PSP путь.

Следующая отдельная непрочитанная Russian primary — `docs/ru/01-what-is-bc250.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian identity: роль документа разобрана

Отдельная Russian primary `docs/ru/01-what-is-bc250.md` учтена целиком: 28 933 байта, 170 строк, SHA-256 `0323d361380c699dbb737a5eda9d06005417585c08e21c614c59150014a9f7ae`. Диапазоны 1–60, 61–120, 121–170 без renderer loss и совпадений privacy prefilter, включая русские credential-слова; это не глобальный clearance. Raw bytes сохранены, prior phase47 preflight и local pinned Git blob совпали после EOL-нормализации. Двадцать Markdown-ссылок и один HTML `img src` разрешаются локально, но тела ссылок, фото и 3D-модели не оценивались. Receipt, provenance, 13 групп замечаний, инертная арифметика и структурная EN/RU сверка: `phase107-russian-identity-*.json`. Русская и английская главы имеют одинаковые позиции девяти заголовков, но разные bytes/hash; содержание не объявлено эквивалентным.

- «Оставшийся кремний PS5», Cyan Skillfish/Oberon/Ariel, 6/12 и 24CU/RDNA2 — классификация документа и сообщества, не повторный die/PCI/ROM probe нашей платы. RDNA2 здесь расходится с импортной AI-главой, где `gfx1013` назван RDNA-1.x. Фраза «нет привычного BIOS» не равна отсутствию UEFI/BIOS вообще. Родственные 4700S/4800S не становятся донорами прошивки по аналогии, а «Linux завели как на PS5» не доказывает PSP-цепочку.
- 16GB GDDR6 — общий пул, не 16GB выделенной VRAM; выбор 12GB в BIOS3.00+ не признан безопасным для ОС/модели. «Нет аппаратного кодировщика» сильнее установленной недоступности VCN в текущем firmware/driver пути. Чужие FPS, сравнение с RX6600/GTX1660Ti, mining draw, eGPU и красный/зелёный LED не измерены на нашей плате.
- При 256 битах и 14 Гбит/с номинальная арифметика даёт **448GB/s**. Источник сам отмечает, что история «разгон с 256 до 445GB/s» противоречит этому stock ориентиру. Ни одно число не является нашим измерением пропускной способности или FPS. Габариты 340/310мм и ~400г зависят от способа измерения; популярность поста и ссылки на STL не подтверждают геометрию для корпуса.
- `J1000`: расчёт трёх контактов × 9A × 12V даёт **324W** условной контактной арифметики, но не гарантирует безопасную подачу на плату с конкретным кабелем, возвратными контактами, нагревом и БП. Распиновку и полярность не подтверждали независимой прозвонкой. `J2000/J2001` различаются LED/PGD по источнику; упоминание 5V PGD в стеллаже не разрешает подачать его на сигнальный вывод. Никакие разъёмы, питание или GPIO не трогали.
- Указанные DP1.4/4K120/8K60, «второй DP включается программно» и M.2 `PCIe2.0×2 или SATA III` — ссылки на внешние описания, не живые EDID/MST/slot-wiring проверки. Последнее не снимает разногласие с USB-главой, где слот описан как PCIe-only. Плата, дисплей, накопитель и прошивка не менялись.

Следующая отдельная непрочитанная Russian primary — `docs/ru/02-buying.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian buying: роль документа учтена с приватными строками

Отдельная Russian primary `docs/ru/02-buying.md` учтена по всем 161 строкам: 33 028 байт, SHA-256 `efcbc3cc9cf5ca26faa76190611c8bff54a87b7893c734a063eb10dfccbd31e8`. Диапазоны 1–55, 56–110, 111–161 без renderer loss; **28 строк** с прямыми контактами, платёжными маршрутами или неподтверждённой репутацией скрыты целиком. Значения не переносились в активные документы. Это не privacy clearance. Raw bytes сохранены, прежний phase51 preflight и local pinned Git blob совпали после EOL-нормализации. Тринадцать Markdown-ссылок и два HTML-ассета существуют, но их тела не проверялись. Receipt, privacy, provenance, 13 групп замечаний и EN/RU структура: `phase108-russian-buying-*.json`. Десять позиций заголовков совпадают с English buying при той же длине 161 строка; разные размеры/хеши не позволяют объединить содержимое.

- Цены из 2025–2026 смешивают валюты, страны, комиссии, «мёртвую» и рабочую плату, голую плату и готовые сборки с БП/SSD/ОС/охлаждением. Это исторические слепки, не текущая оценка сделки. Контакты продавцов, репутационные обвинения и брокерские способы оплаты не рекомендованы и не воспроизведены. Никаких покупок, контактов, гарантов или переводов.
- Масса **≈0,86кг для «голой» платы** расходится с identity-главой **≈0,4кг «с радиатором»**; измерения здесь не было. «Любая BIOS-версия прошивается на мод» не проходит exact-image, полный dump, независимый recovery, PSP-подпись и coldboot/readback gates. Комплектация в объявлении не доказывает состояние firmware или платы.
- Потребление от розетки 100–125W в простое, GPU29W и автоусыпление≈10W взяты из разных чужих сборок, не измерены на нашей. Совет «автоусыпление решит» расходится с troubleshooting, где suspend назван неподдерживаемым/псевдозависшим. Невозможность управлять CPU power states не доказана для целевого BIOS/OS.
- «Постоянная майнинговая температура означает надёжность и BGA почти не страдает» — гипотеза сообщества, не прогноз срока службы; обратное предположение о BGA-трещине и reflow также не доказано. Нет видеоэнкодера/VRS/mesh по источнику не означает все соответствующие кремниевые блоки отсутствуют или что VCN никогда не включить. SSD под горячим потоком, цена 3D-печати и матовый PETG не проверены на конкретном корпусе.
- Глава не даёт проверенной платы Waveshare, gamepad/power wiring, PSP-signature перехода, F1/J004/SPI recovery или разрешения на flash. Ни продажи, покупки, BIOS, питание, корпус, ОС или железо не трогались.

Следующий отдельный непрочитанный Russian primary — `docs/ru/03-power-supply.md`; остальные локали, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian power-supply: роль документа разобрана

Отдельная Russian primary `docs/ru/03-power-supply.md` учтена целиком: 70 033 байта, 382 строки, SHA-256 `bbdbc757292a01936a94b322d264003c18abb1932f9589415f19342ad5067869`. Диапазоны 1–80, 81–160, 161–240, 241–320, 321–382 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase46 preflight и local pinned Git blob совпали после EOL-нормализации. Три Markdown-ссылки и один HTML-ассет существуют, но linked/remote тела и фото не валидировались. Receipt, provenance, 16 групп замечаний, инертная арифметика и EN/RU структура: `phase109-russian-power-*.json`. У Russian/English power одинаковые позиции 23 заголовков при разных размерах/хешах; тела не объявлены эквивалентными.

- «Нет кнопки, включается сразу от 12V» смешивает **PS_ON БП**, `AUTO_PWRON` платы, `PWR_SW` и `system_on` с разъёма вентилятора. Это разные состояния/сигналы, а не один готовый интерфейс управления для Waveshare. Чужие 220–235W, «нужна единая линия≥300W» и список PSU не являются замером или допуском нашей плате.
- Документ одновременно цитирует стандарт **PCIe 8-pin 150W** и объявляет J1000 «безопасным до324W/468W» по контактам. `3×9A×12V=324W` — условная арифметика контактов, **не** разрешённая мощность платы/кабеля/БП с тепловыми и возвратными ограничениями. В видео 17A при условных12V дают **204W**, не подпись ~190W; 21A дают252W, близко к ~240–250W с погрешностью субтитров. Wall-power, вход платы и отдельный 8-pin не одна плоскость измерения.
- J1000/PCIe-versus-EPS предупреждение важно, но точная ориентация и текущий кабель не прозванивались. J2000 имеет LED1/LED2, J2001 — PGD по источнику; 5V PGD в стойке **сигнал**, не вход для подачи напряжения. Разветвление J1000 и Micro-Fit **от одного исходного PCIe-кабеля** не увеличивает допустимый ток исходного провода и БП. Противоречивые 16AWG/2.5мм²/18–20AWG, срезание защёлки, пайка вместо обжимки и обещание «>400W безопасно» не квалифицированы. Никакой проводки, пайки или измерения живой платы.
- HP start pins/резистор, открытые клеммы Mean Well, PS3/LED-strip блоки, модульные `PS_ON` выводы и скрепка — модельно-зависимые электрические рецепты. Суффикс `LOP-300-24` действительно обозначает иную категорию выходного напряжения, но ни один PSU не покупался/включался. «Штатный ATX PCIe-кабель просто безопасен» требует совместимости конкретного родного кабеля БП.
- **Два разных lead на управление без пайки:** коммерческий адаптер PS_ON, читающий `system_on` с fan header, и ESP32 BLE-сканер Xbox с реле PWR_SW/питания периферии. Ни один не является Waveshare-дизайном или доказанным подключением геймпада к BC-250. `system_on`, standby draw, fan-header ownership, PSU shutdown timing и уровни GPIO не проверены. Удаление дросселя ради «настоящего ATX» — необратимая аппаратная переделка, не выполнялась.
- «GST280 с 6→8 адаптером — единственный путь без пайки» расходится с собственным ATX/SFX native8pin и FSP plug-and-play вариантами. Заводской 6-pin/возвратные контакты, unexplained 280→252W и пределы при разгоне не проверены. Ни GST280, ни другой адаптер не признан готовым к включению.

Следующая отдельная непрочитанная Russian primary — `docs/ru/04-cooling.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian cooling: роль документа разобрана

Отдельная Russian primary `docs/ru/04-cooling.md` учтена целиком: 55 676 байт, 307 строк, SHA-256 `9cd3b998219f1b204cfdc0e98aa4581ba0e369adf11c9e0f0279191cb354b875`. Диапазоны 1–80, 81–160, 161–240, 241–307 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase47 preflight и local pinned Git blob совпали после EOL-нормализации. Три Markdown-ссылки и два HTML-изображения существуют, но linked/remote тела, STL и фото не проверялись. Receipt, provenance, 16 групп замечаний, условная арифметика и EN/RU структура: `phase110-russian-cooling-*.json`. Русская/английская cooling главы имеют одинаковые позиции 21 заголовка при разных размерах/хешах; тела не объявлены эквивалентными.

- В начале и в «минимальном» комплекте источник требует **прорезать/шлифовать рёбра стокового радиатора**. Ниже он сам сохраняет **корпус с продувом push–pull без резки рёбер**, а текст оценивает эффект хорошего шрауда как похожий. Это важная no-cut альтернатива для пользователя, но её механическая посадка, качество 3D-модели, зазоры и температура **на нашей плате** не проверены. Никакой резки, подъёма рёбер или металлической стружки.
- Температурные таблицы GPU/CPU/SSD и особенно оборотная GDDR6/VRM без собственного датчика собраны из разных наблюдений; их нельзя объявлять текущими target показаниями. Пик **107°C GPU/100°C CPU** за чужие 10 минут 40CU/2GHz не доказывает «можно сколько угодно» при другом лимите 1500MHz. Артефакты не всегда означают перегрев VRAM. Ни stress, ни compute, ни термометрию платы не запускали.
- Таблица Arctic P12 Pro даёт максимум **2100rpm**, а другой фрагмент из автосубтитров — диапазон **600–3000rpm**; точная модель/ревизия и fan curve не сверены. «Push–pull удваивает статическое давление», 1,8× излучение чёрного радиатора/−45% площади рёбер, 100°C VRM и −3…−5°C от вытяжки — разные чужие условия, не расчёт нашего корпуса. STL/STEP/FreeCAD упоминания — ссылки, не геометрическая и лицензионная проверка.
- AIO-профили с **350–400W от розетки**, насос, вентиляторы и водоблоки не квалифицированы относительно J1000/БП, fan-header current, прижима, шлангов или защиты от протечки. Источник сам сообщает о лопнувшем шланге и отказавшей помпе. Башенные AM4-крепления также могут перекрыть M.2 и по-разному давить на кристалл. Никакой AIO, помпы, жидкости, кронштейна или аппаратной переделки.
- `nct6683` read-only и out-of-tree `nct6687` c `force=true`/PWM — **разные** режимы. Нумерация hwmon, Super I/O, `fan2/pwm2`, владение вентилятором BIOS/ОС и допустимый ток не измерены на нашей плате. Ни DKMS, ни CoolerControl, ни sysfs/PWM записей.
- PTM7950 **26×30мм на кристалл** и **40×80×0,25мм лист в видео** не дают одной подтверждённой выкройки; 1мм VRM/2мм задней GDDR6 и 1,5мм лицевой памяти относятся к разным зазорам. Жидкий металл проводящий; его не применяли. Установка TIM и требование FurMark+CPU нагрузки под 2000MHz — рецепты источника, **не** разрешённая нам серия стресс-тестов. `1500→2000MHz` означает **+33,33% частоты**, не гарантированные +30% FPS.

Следующая отдельная непрочитанная Russian primary — `docs/ru/05-case.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian case: роль документа разобрана

Отдельная Russian primary `docs/ru/05-case.md` учтена целиком: 46 836 байт, 328 строк, SHA-256 `321c2193fb099b2eef3bd029b33650ac5608764814cf1a25bed528a0777b3c01`. Диапазоны 1–85, 86–170, 171–255, 256–328 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase51 preflight и local pinned Git blob совпали после EOL-нормализации. Двенадцать Markdown-ссылок и четыре HTML-изображения существуют; содержимое ссылок, фото и STL не проверялось. Receipt, provenance, 14 групп замечаний, выбранные exact asset names и EN/RU структура: `phase111-russian-case-*.json`. Русская и английская case главы имеют одинаковые позиции 29 заголовков и 328 строк, но разные bytes/hash; тела не объявлены эквивалентными. Arabic Steam Cube concept учитывался отдельно и здесь не обнаружен по структуре заголовков.

- Минимальный **двухчастный рукав охлаждения** в этой главе заявлен как вариант **без распила рёбер**. Его нельзя смешивать с более крупным Shell Case того же сообщества, где показаны **прорезанные** рёбра. Другая no-cut ветка — stock-fin push–pull корпус из cooling-главы. Около70°C при150W — отчёт отдельной сборки, не измерение нашего экземпляра. Ни печати, ни примерки, ни проверки давлений/зазоров.
- Обещание, что «все чатовые STL/STEP/3MF зеркалируются в `assets/stl/`», не подтверждено буквально: в этом imported каталоге 61 файл; девять из десяти выбранных точных имён присутствуют, а `BC250 korpus исправленный.rar` здесь **не найден**. Это ограничено одним каталогом, не глобальный поиск и не оценка содержимого архива. Плейсхолдеры и составные названия в таблице нельзя выдавать за точные имена файлов.
- Подбор корпуса зависит от **точного БП, вентилятора, разъёмов, крепления и охлаждения**, а не числа реакций на фото. «Любой ITX-корпус» для печатного переходника подтверждён только одной названной сборкой; CAD-модель с подписью accurate не была размерно сверена. Встроенный AIO, LOP/ATX/HP PSU, реле, экраны и eDP-переходники требуют своих проверок питания, fan/pump current, зазоров, изоляции, пожарной и тепловой стойкости материала.
- Совет сделать отверстие или внешний переключатель CMOS опирается на чрезмерное «сбрасывать после каждой смены UMA» и добавляет невалидированную электрическую цепь. ESP32 сетевое реле для БП и Raspberry Pi Zero 2 HUD с MangoHud — **разные проекты**, не Waveshare-контроллер геймпадов/питания и не доказательство VCN. Никаких GPIO, кнопок, PSU или прошивки не подключали.
- Каталог ~143 моделей, платные/бесплатные печатные файлы, фото, температуры и ссылки на магазины — исторические внешние lead. Доступность, права на печать/перераспространение, геометрию, лицензии и результаты **на нашей** плате не проверяли. Открытый стенд/переделка чужого корпуса не равны готовому безопасному изделию.

Следующая отдельная непрочитанная Russian primary — `docs/ru/06-linux.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian Linux: роль документа учтена с одной скрытой строкой

Отдельная Russian primary `docs/ru/06-linux.md` учтена по всем 579 строкам: 78 555 байт, SHA-256 `b795a9903513a4f1a146391cd590d78bb991c5e424f1d3c43db6d3ed81d01dc7`. Диапазоны 1–85, 86–170, 171–255, 256–340, 341–425, 426–510, 511–579 без renderer loss; строка9 с широким совпадением по credential-слову скрыта целиком и не перенесена в активные документы. Это не глобальный privacy clearance. Raw bytes сохранены, прежний phase48 preflight и local pinned Git blob совпали после EOL-нормализации. Все 12 относительных ссылок существуют; linked/remote тела, пакеты и образа не проверялись. Receipt, provenance, 17 групп замечаний, условная арифметика памяти и EN/RU структура: `phase112-russian-linux-*.json`. Русская версия имеет 579 строк против 578 English; после первых трёх заголовков все остальные 29 позиции сдвинуты на одну строку. Тела не объявлены эквивалентными.

- Открывающая схема требует `navi10`→`cyan_skillfish` symlink, а дальше сам источник говорит: актуальный `linux-firmware` **уже поставляет свой** `cyan_skillfish_gpu_info.bin`, и новые Arch/CachyOS гайды симлинк не делают. Это старый условный workaround при доказанном missing-blob, не обязательный шаг. Fedora43 якобы имеет Mesa в основных репах, но B2 всё ещё включает старый COPR `mixaill`; Arch official Mesa рядом со старым Chaotic/AUR/TKG рецептом. Датированные kernel/Mesa/image tags не проверялись как текущие. Ни симлинка, пакетов, rebase, initramfs или bootloader edits.
- Источник предупреждает, что 40CU-образ Bazzite у части владельцев ломал **управление вентилятором и Xbox controller**. Упоминание альтернативного kernel image — не доказанный фикс для нашей платы и не Waveshare gamepad route. Немедленное `systemctl enable --now` governor расходится с OC-главой, где он намеренно выключен до проверки кривой из-за black-screen. Service running, requested GPU clocks и реальные частоты/rail — разные события.
- `mitigations=off`, обязательное BIOS IOMMU Disabled и `kernel.dmesg_restrict=0` ослабляют разные границы безопасности; ни один не принят как target repair. `amdgpu.bc250_cc_write_mode=3`, TTM/GTT и UMA512 затрагивают CU/общую 16GB память и OOM. При условной странице4KiB лимит `3959290` равен **≈15,10GiB**; `gttsize=14750` при MiB-единице равен **≈14,40GiB**, не «добавленным» RAM. Никаких boot/BIOS/CU/swap изменений.
- CoreOS `umr` записи `mmSPI_PG_ENABLE_STATIC_WGP_MASK` относятся к GPU shader/power gating, **не** к serial SPI BIOS и не к подмене подписи PSP. ACPI SSDT/AML override — отдельное изменение pre-OS/boot, не применялось.
- RADV/Vulkan/OpenGL renderer, CU log, `vainfo`/VA-API и sensor hwmon — разные проверки. Сбой VA-API не опровергает RADV rendering и не доказывает отсутствия VCN silicon. Forced `nct6683` read-only vs out-of-tree `nct6687` PWM требует отдельной проверки Super I/O/header ownership. Команды удаления shader caches, запись `/etc`, service restart, DKMS и `rm -rf` из источника не исполнялись.

Следующая отдельная непрочитанная Russian primary — `docs/ru/07-windows.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian Windows: роль документа разобрана

Отдельная Russian primary `docs/ru/07-windows.md` учтена целиком: 22 031 байт, 126 строк, SHA-256 `43c2b57536452064ba76e93b44a468a072e96d750dfeef672c2df18a52d7c06e`. Диапазоны 1–65, 66–126 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase48 preflight и local pinned Git blob совпали после EOL-нормализации. Все восемь относительных ссылок существуют; их содержимое и актуальное состояние удалённых GitHub/Telegram/AMD источников не проверены. Receipt, provenance, 13 групп замечаний и EN/RU структура: `phase113-russian-windows-*.json`. Russian/English Windows главы имеют одинаковые позиции 12 заголовков и 126 строк, но разные bytes/hash; тела не объявлены эквивалентными.

- «Нет рабочего Windows GPU-драйвера» — **датированный статус на начало 2026**, не доказательство навсегда. Code43 после W5700 `.inf` и одной BIOS DeviceID правки не доказывает, что ID неизменно закреплён eFuse или что все возможные драйверные пути исчерпаны. Проброс GPU/IOMMU «невозможен» — обобщение без свежего target trace.
- Keshas PSP kernel driver по описанию загружает SOS, читает/пишет BAR5 MMIO и служит прокси GPU-регистров. Это **не** возможность подменить AMD PSP-подпись или подписанную запись в SPI ROM. Сам источник оставляет GPCOM/TOS ring, загрузку GPU firmware и TMR незавершёнными; установка драйвера и OpenGL1.1 milestone не равны игровому рендерингу. Образовательный WDDM/D3D9 DDI каркас другой команды также не даёт D3D11/12/Vulkan/VCN или рабочего GPU.
- `PS5GPU-BC250` здесь исправлен как Linux governor, а `duggasco` 40CU скрипт — Linux `amdgpu`, не Windows. Неверный ярлык в списке ресурсов не становится доказательством Windows-реализации.
- Тестовая подпись, отключение Secure Boot, PowerShell/`pnputil` установка, архив `00.00.01.7z` и псевдо-драйверные `.exe` — риск для доверенной загрузки/хоста, **не выполнялись**. Предупреждение о поддельных бинарниках оставлено; GitHub-адрес сам по себе не гарантирует их безопасность. Слух о «удалённом кирпиче за слив» источник сам не подтвердил, и как факт он не принят.
- Эти рассказы не дают ни Waveshare/gamepad/power маршрута, ни подписанной PSP-подмены, ни F1/J004/SPI recovery, ни VCN acceptance. Ни Windows, драйверы, test-signing, Secure Boot, BIOS, прошивка или плата не тронуты.

Следующая отдельная непрочитанная Russian primary — `docs/ru/08-bios.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian BIOS: роль документа учтена с приватными строками

Отдельная Russian primary `docs/ru/08-bios.md` учтена по всем 406 строкам: 51 240 байт, SHA-256 `1d6788e40c865695a68ac9f53cb720f6420aea4185c231445b805b5e973dea40`. Диапазоны 1–80, 81–160, 161–240, 241–320, 321–406 без renderer loss; строки 34/162/349/378 с прямыми social/contact совпадениями скрыты целиком, значения не перенесены в активные документы. Это не privacy clearance. Raw bytes сохранены, прежний phase46 preflight и local pinned Git blob совпали после EOL-нормализации. Все десять относительных ссылок существуют; linked/remote тела, образы и программаторы не проверялись. Receipt, provenance, 18 групп замечаний, EN/RU структура и ограниченная проверка зеркала: `phase114-russian-bios-*.json`. RU/EN BIOS имеют те же позиции 17 заголовков и 406 строк, но разные bytes/hash и разное число скрытых строк; тела не объявлены эквивалентными.

- BIOS P3/P5 stock, death setup-menu mods и `P5.00_clv` — разные байтовые образы. Открытие меню **не** подменяет подписанную PSP-запись или её доверенный ключ. «P3 безопасный дефолт» и «P5 текущий» — советы сообщества, не approved image для целевой платы. Для `P5.00_clv` источник признаёт отсутствие публичного полного хеша; две совпавшие копии не заменяют независимую provenance.
- 16 hex-символов префикса — слабее полного независимо сверенного SHA-256. Размер 16MiB и чужие хеши не доказывают, что конкретный staged ROM сохранил подписанные области и имеет полный dump, независимый recovery, точный target, cold-boot/readback план. В **этом** импортированном `assets/firmware/` найден только `DISCLAIMER.md`: ни одного из 11 названий таблицы здесь нет. Это не отсутствие файлов во всём корпусе. ZIP-размер не является размером распакованного ROM. Никакой образ не извлекался и не прошивался.
- AFU `/P /N` затрагивает BIOS/NVRAM; `Flash.nsh` с именем `Robin5.00` рядом со stock-файлом того же имени и `blk0:` против `fs0:` оставляет риск подмены цели. Внутренний `flashrom boardmismatch=force` снимает защиту. NeoProgrammer-рецепт **стирает до открытия файла** и не содержит двойного чтения/независимого readback. Внешний flashrom текст предлагает два чтения, но буквальный список команд не делает их `diff`/hash, coldboot и отдельное подтверждение восстановления. Ни одна команда не запускалась.
- Категорическое «только J4004, SOIC clip не работает» противоречит собственному более узкому «почти не работает» и **сообщённому оператором F1-прошиванию**. F1-запись подтверждает возможный маршрут записи, но сама по себе не доказывает независимое восстановление, корректный целевой чип и холодную загрузку. Pinout J4004/CH341A 3.3V data lines, `BIOS_A1` 16MiB против `SIO1_R` 512KiB — исходные fixture-сведения, не измеренная текущая плата. Ничего не подключалось.
- CMOS может влиять на настройки, но не восстанавливает испорченные ROM-байты/PSP подпись. Чужая история 512MB UMA с Cyberpunk меняла также часы и FSR; прирост нельзя приписать одному UMA. `srep` описан как эксперимент без готового результата. Secure Boot/CSM Disabled меняют trust/boot режимы; не применялись как универсальное предусловие. PSPTool извлекает объекты для анализа, **не** создаёт действительную PSP-подпись.

Следующая отдельная непрочитанная Russian primary — `docs/ru/09-overclock-undervolt.md`; все остальные локали/исходники/binaries/native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён. Никаких CMOS, AFU, CH341A, SPI, PSP, UEFI, hardware или firmware действий не было.

## Russian overclock-undervolt: роль документа учтена с приватными строками

Отдельная Russian primary `docs/ru/09-overclock-undervolt.md` учтена по всем 645 строкам: 113 346 байт, SHA-256 `5ac15ff19007bbb5614e0916394a0e68115ebc0bce93747c2f3fadd241ea8635`. Диапазоны 1–80, 81–160, 161–240, 241–320, 321–400, 401–480, 481–560, 561–645 без renderer loss. Строки381/630 с credential-bearing содержимым скрыты целиком без повторения значений; широкое `pwd` совпадение на418/419 оказалось только shell `$(pwd)` (рабочая директория), эти строки проверены отдельно. Это не глобальный privacy clearance. Raw bytes сохранены, прежний phase46 preflight и local pinned Git blob совпали после EOL-нормализации. 16 Markdown-ссылок и восемь HTML-ассетов существуют, но linked/remote тела не проверены. Receipt, provenance, 18 групп замечаний, инертная арифметика и EN/RU структура: `phase115-russian-oc-*.json`. RU/EN OC имеют одинаковые позиции30 заголовков и645 строк, но разные bytes/hash; тела не слиты.

- В начале инструкция сразу делает `systemctl enable --now` SMU-governor, а позже говорит, что автор **умышленно поставляет его выключенным**, пока кривая не проверена из-за риска чёрного экрана на загрузке. Service state, запрошенный VID/clock, телеметрия и физические rail/частота — разные вещи. Никакой governor, SMU/sysfs или напряжение не изменялись. Пределы 700/1129mV и чужая кривая на воздухе до1150mV не образуют безопасного профиля нашей платы.
- `4GHz@1275mV` как рекомендация расходится с таблицей, где4GHz уже троттлили, и видео, где короткий тест прошёл, а игра падала. 1300mV из автосубтитров против1325mV в README — не подтверждённый электрический потолок. «Два дополнительных CPU-ядра требуют обхода PSP-подписи» — объяснение сообщества, **не** target fuse/readback или демонстрация замены подписанного SMU микрокода. Разблок GPU CU — другая задача.
- `CC_GC_SHADER_ARRAY_CONFIG` и **`SPI_PG_ENABLE_STATIC_WGP_MASK`** — GPU shader/power-gating регистры. `SPI_PG` здесь **не serial SPI BIOS** и не путь подмены PSP-записи. Kernel-init patch и runtime UMR после загрузки драйвера не доказаны эквивалентными состояниями; scattered/дефектные CU могут повесить плату. Источник сам допускает36/38/40 стабильных CU и пик107°C GPU/100°C CPU за чужой десятиминутный 40CU тест. Совет добавить питание J2000/J2001 не прошёл электрическую квалификацию. Ни CU, UMR, BIOS или второй БП не трогали.
- FurMark91→110 — **+20,879%**, не заявленные около25%; Superposition4647→6863 — **+47,687%**, согласуется с округлёнными48%, но это один чужой прогон. Частота1500→2000MHz повышается на33,33%, не гарантирует такой же FPS. Эти цифры не подтверждают gamepad/VCN, физическую стабильность или состояние нашей платы. Никаких бенчмарков/нагрузок.
- «Слишком сильный undervolt безвреден и проходит за пять секунд» расходится с сохранёнными no-boot/failed CMOS recovery случаями. UMA512MB «безопасно всем» рядом с llvmpipe/зависаниями и играми, требующими4–8GB, zRAM/zswap/TTM-рецептами — не target memory policy. GDDR6 clocks/timings могут не дать POST, а CMOS не гарантирует восстановления ROM. Предложение отдать ~14.75GB общего16GB пула под модель почти не оставляет ресурса ОС/KV-кэшу. Ни OS swap, ни GDDR6, ни настройки памяти не менялись.

Следующая отдельная непрочитанная Russian primary — `docs/ru/10-wifi-bt.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian WiFi/Bluetooth: роль документа разобрана

Отдельная Russian primary `docs/ru/10-wifi-bt.md` учтена целиком: 25 102 байта, 182 строки, SHA-256 `0d10da5f8f7ec96185c485366c7e8f5c2527bc09428f653f4df6c6b5620b018c`. Диапазоны 1–70, 71–140, 141–182 без renderer loss. Широкое совпадение фильтра на111 оказалось shell **`$PWD`** (рабочая директория в неприменённом DKMS-рецепте), не паролем; скрытых credential-значений здесь не обнаружено, но глобального privacy clearance нет. Raw bytes сохранены, прежний phase48 preflight и local pinned Git blob совпали после EOL-нормализации. Локальных относительных ссылок нет; удалённые Telegram/GitHub/магазин/Intel/TP-Link страницы не открывались. Receipt, provenance,12 групп замечаний и EN/RU структура: `phase116-russian-wifi-*.json`. RU/EN WiFi имеют одинаковые позиции12 заголовков и182 строки, но разные bytes/hash; тела не слиты.

- «Самый надёжный» aic8800d80 и Digma «работает из коробки» — отдельные отзывы, не target USB VID:PID, ревизия чипа, ядро или BT-профиль. Brand-label не гарантирует чипсет; таблица RTL8821/8822/8851 требует точной идентификации. `biglinux/rtl8831` сам источник помечает **не проверенным на BC-250**. У TP-Link TX10UB Nano Linux WiFi заявлен через сторонний драйвер, а BT вендором для Linux **не поддерживается**; комбинированную работу нельзя обещать.
- Отвал под нагрузкой может исходить от драйвера, USB-питания/root-hub либо RF-помех — один симптом не различает причины. Общелинуксовые сообщения о `r8169`/RTL8111 не доказывают неисправности onboard NIC нашей платы. USB3→2.4GHz белая книга и единичный замер 150 против190Mbit — внешний контекст, не измерение на BC-250.
- RPM/DKMS, remote `curl` spec, `rpm-ostree usroverlay`, `git clone`, `make install`, reboot, `rmmod`/`modprobe`, MOK, `usbreset` и persistent modprobe softdep — **host/device изменения**, не выполненные здесь. Источник сам предупреждает о проблемах ядра7.x/Debian и что raw `make` может не пережить перезагрузку; даже с `rtw88` сохранялись редкие отвалы.
- Bluetooth-донгл для геймпада — это **не** встроенный Waveshare-контроллер включения/выключения, самостоятельного сопряжения геймпадов или PSP/SPI BIOS. Ни радио/USB, ни драйверы, модули, покупки, firmware или hardware действия не выполнялись.

Следующая отдельная непрочитанная Russian primary — `docs/ru/11-gaming.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian gaming: роль документа разобрана

Отдельная Russian primary `docs/ru/11-gaming.md` учтена целиком: 37 294 байта, 210 строк, SHA-256 `b7ad9834e338cdc92817b72489e108bcc280a6bf2b0e3fa49a0f1083eca66728`. Диапазоны 1–75, 76–145, 146–210 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase49 preflight и local pinned Git blob совпали после EOL-нормализации. Восемь относительных ссылок существуют, их тела и удалённые Telegram/Reddit/YouTube/таблицы не проверены. Receipt, provenance,14 групп замечаний, условная арифметика и EN/RU структура: `phase117-russian-gaming-*.json`. RU/EN gaming имеют одинаковые позиции13 заголовков и210 строк, но разные bytes/hash; содержание не слито.

- `GPU Limited Percentage 36,5%` в одном benchmark переведено как «загрузка GPU всего36,5%». Это не прямой измеритель utilization, поэтому вывод «GPU простаивает на две трети» и универсальный CPU bottleneck из одной метрики не следует. `1500→2000MHz` — **+33,33% частоты**, не гарантия +30% FPS, особенно когда сама глава говорит об упоре в CPU. Один 40CU Doom-отчёт не доказывает широкий прирост, стабильность вентилятора/геймпада или необходимость резать охлаждение.
- FPS-таблица смешивает ОС, драйверы, частоты, пресеты, FSR и frame generation. Строка с **RX6600/Xeon не BC-250**, а подпись «Windows, RADV» требует сверки происхождения. Минимум около3 при среднем70 не описывает стабильный игровой процесс. Видео с ASR и «играбельно» не превращены в целевой бенчмарк.
- FSR, FG/LSFG, DP4a/FSR4 и XeSS — разные программные пути. Сгенерированный/показанный FPS нельзя приравнивать к нативной симуляции или задержке ввода; официальный FSR4 для RDNA2 «к2027» — прогноз внешнего источника. UMA512MB/4GB/8GB и GTT зависят от игры; текст сам описывает llvmpipe/зависания. `mitigations=off` снижает защиту и даёт спорный эффект; никаких boot/host настроек не меняли.
- Категорические «не запускается» для античита, mesh/VRS и «Vulkan_NullVRS без побочных эффектов» зависят от версии игры и точных GPU-функций, не проверенных на нашей плате. RT-таблица смешивает заявленный аппаратный RT с отдельно помеченным **software path** Portal2 RTX. RPCS3 GPU1000MHz и совет «компенсировать разгоном CPU» — чужой случай, не диагностика наших частот.
- Глава не тестирует Waveshare, геймпады, VCN, питание или PSP/SPI BIOS. Никакие игры, эмуляторы, Proton, драйверы, CU, разгон, ОС, прошивка или hardware операции не выполнялись.

Следующая отдельная непрочитанная Russian primary — `docs/ru/12-ai-llm.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian AI/LLM: роль документа разобрана

Отдельная Russian primary `docs/ru/12-ai-llm.md` учтена целиком: 32 334 байта, 215 строк, SHA-256 `efcd099e3b67e5b3bd3b98ea9149699450c18288e77e1a56168bd5d0cb58c03a`. Диапазоны 1–75, 76–150, 151–215 без renderer loss. Широкий privacy-фильтр отметил строки51/157 по слову «токен»; отдельная проверка установила, что это **токены модели/скорость генерации**, а не доступ или пароль. Глобального privacy clearance нет. Raw bytes сохранены, прежний phase49 preflight и local pinned Git blob совпали после EOL-нормализации. Восемь относительных ссылок существуют; linked/remote GitHub/Discord/Telegram/YouTube/Hugging Face тела не валидированы. Receipt, provenance,15 групп замечаний, условная арифметика и EN/RU структура: `phase118-russian-ai-*.json`. RU/EN AI главы имеют одинаковые позиции11 заголовков и215 строк, но разные bytes/hash; содержание не слито.

- Здесь `gfx1013` назван RDNA-1.x, тогда как gaming-глава называет его RDNA2. Ссылка на ISA `gfx1030` не разрешает расхождение для нашей платы. Раннее категорическое «ROCm/HIP не работает» противоречит позднему сообщению о HIP/PyTorch после изменения **MEC firmware**, BIOS и пересборки стека. Поздний рассказ не содержит независимого target dump/boot/readback и **не** разрешает подписанную PSP/SPI подмену.
- 16GB — общий пул CPU+GPU+ОС+KV-кэш, не выделенная 16GB видеокарта. `vram=12`, контекст65536, `OLLAMA_GPU_OVERHEAD=0`, TTM и `OOMScoreAdjust=-1000` не образуют проверенный «безопасный по памяти» профиль: источник сам описывает OOM и смерть десктопа, а защита Ollama от OOM-killer может переложить отказ на другие процессы. При условных4KiB страницах `4194304` — **16GiB**, весь физический пул до расходов ОС. Никаких BIOS/TTM/service записей.
- `curl | sh`, AUR/apt, source build, systemd restart, `ollama run` и governor — host/model рецепты, **не исполнялись**. Отчётные 30–40, 59.5/66.1 и 78.7/87.5 ток/с относятся к разным моделям, квантам, рантаймам и числу CU; это не единый baseline нашей BC-250. Для видео с автосубтитрами 25.7→31.9 означает **+24,125%**, не 16–17%, а 25.7→33.4 — **+29,961%**, не ~20% суммарно. 66.1→87.5 даёт+32,375%, 59.5→78.7 —+32,269%, согласуется с округлёнными32%, но не доказывает стабильность 40CU. Один чужой экземпляр срывался сверх36CU.
- MoE/многоплатный bandwidth, качество квантованных моделей, Ubuntu-vs-Fedora, обучать/не обучать и web/MCP возможности фронтендов — контекст/оценки, не принятые как test/лицензия/приватность target. Глава не даёт Waveshare gamepad/power route, F1/J004 recovery, VCN или PSP signature transition. Никаких моделей, драйверов, пакетов, CU, прошивок или железа не запускалось.

Следующая отдельная непрочитанная Russian primary — `docs/ru/13-macos.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian macOS: роль документа разобрана

Отдельная Russian primary `docs/ru/13-macos.md` учтена целиком: 9 194 байта, 53 строки, SHA-256 `58ec70ea8b62cba12dc6414645fa81a0c6a421db52267cc53ee7e2a8196becfd`. Диапазон 1–53 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase49 preflight и local pinned Git blob совпали после EOL-нормализации. Шесть относительных ссылок существуют; их тела и удалённые Telegram/форум/GitHub/Dortania списки поддержки не проверялись. Receipt, provenance,11 групп замечаний и EN/RU структура: `phase119-russian-macos-*.json`. RU/EN macOS имеют одинаковые позиции пяти заголовков и53 строки, но разные bytes/hash; тела не объявлены эквивалентными.

- «Никто в сообществе не сообщил об ускоренной macOS» — отсутствие отчёта в данном корпусе, не доказательство невозможности навсегда. Глава **не показывает и успешную загрузку CPU-only macOS** на нашей BC-250. Пакет Monterey recovery + OpenCore — намерение/упаковка, а не boot, Metal или recovery test; ZIP не извлекался.
- «Драйвер определяется только device ID» и «вмешаться можно только через OpenCore» — упрощение. Идентификатор не заменяет совместимость архитектуры, функций, питания и драйвера. Собственный список главы позже приводит **NootedRed kext** для других AMD APU, что делает абсолют «никакой Ryzen iGPU никогда не работал» слишком широким. Это **не** означает, что NootedRed поддерживает BC-250; актуальный список кристаллов не проверяли.
- «Нет поддерживаемого близнеца», история годового spoofing и прогноз, что разработчики не займутся чипом, — атрибутированные выводы/предсказания, не новый target PCI/ROM/driver trace. Generic VMware/OpenCore ссылка также не доказывает ни Metal на BC-250, ни «VM всегда без passthrough». Датированный консенсус 2025-06→2026-03 не обновлён здесь до текущего состояния.
- Ссылки на OpenCore, FakePCIID, NootedRed, AMD-OSX и Linux оставлены библиографией, не инструкцией к установке. Ни macOS, VM, bootloader, kext, ОС, BIOS, firmware или железо не тронуты. Глава не содержит Waveshare/gamepad/power или PSP-signature transition.

Следующая отдельная непрочитанная Russian primary — `docs/ru/14-display.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian display: роль документа разобрана

Отдельная Russian primary `docs/ru/14-display.md` учтена целиком: 29 042 байта, 163 строки, SHA-256 `6a3c243539c443ef827f568472a19ea6a1f2314b82d2234f8b0a8e34a4c29f85`. Диапазоны 1–60, 61–120, 121–163 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase50 preflight и local pinned Git blob совпали после EOL-нормализации. Девять относительных ссылок существуют; их тела и удалённые Telegram/Reddit/GitHub/товарные источники не проверены. Receipt, provenance,13 групп замечаний и EN/RU структура: `phase120-russian-display-*.json`. RU/EN display имеют те же позиции11 заголовков и163 строки, но разные bytes/hash; тела не слиты.

- «Нет картинки» не диагностирует однозначно HDMI, кабель, драйвер, PSU или BIOS. Совет «сбросить/перешить known-good» после группового случая **не** преодолевает наши dump/recovery/exact-image/readback gates и не выполнялся. «DP→HDMI видео всегда без задержки» расходится с собственными сообщениями об изображении до GRUB, чёрном экране после ОС и generic HDMI MST без видео. DP1.4/4K120/HDR10 таблица не заменяет target EDID/link/дисплей тест.
- Аудио-советы внутри главы противоречат простому выбору «пассивный/активный»: есть успешный адаптер, молчащие и меняющие высоту звука другие, а итог сам говорит о **chipset конкретного адаптера**. «Цельный кабель убирает чипсет» не установлено. 5.1-«никогда» взято из треда, не из ELD/ALSA/receiver измерений нашей платы. Ничего не подключали.
- В начале «kernel6.17 приносит исправление», ниже — «6.17 изменил путь и сломал штатную конфигурацию», причинность и версия не сверены по точному build/config/ALSA. Custom kernel, GDM/Wayland и Bazzite remix не ставились; последний автор испытывал VRR на Radeon9070XT, не на BC-250.
- Неприпаянный второй физический output/head, два MST-потока по **одному** DP1.4 хабу, USB DisplayLink desktop и LAN streaming — четыре разные реализации. Один StarTech hub-report не создаёт второй GPU head, а Sunshine/Steam поток на ноутбук не доказывает аппаратный VCN encoder или Waveshare/gamepad input. Никакой MST, DisplayLink или stream не запускался.

Следующая отдельная непрочитанная Russian primary — `docs/ru/15-emulation.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian emulation: роль документа разобрана

Отдельная Russian primary `docs/ru/15-emulation.md` учтена целиком: 30 547 байт, 158 строк, SHA-256 `06f2803506f4d5e2a69b394401ab21f10ee31cdb80bdfb5e5f5f03a86c00905f`. Диапазоны 1–55, 56–110, 111–158 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase50 preflight и local pinned Git blob совпали после EOL-нормализации. Одиннадцать относительных ссылок существуют, linked/remote Telegram/Reddit/видео/проекты не открывались. Receipt, provenance,12 групп замечаний, census таблицы и EN/RU структура: `phase121-russian-emulation-*.json`. RU/EN emulation имеют одинаковые позиции13 заголовков и158 строк, но разные bytes/hash; содержание не слито.

- **PSP в этой главе — портативная консоль PlayStation Portable**, которую запускает PPSSPP, а не AMD Platform Security Processor в подписанной прошивке BIOS. Отчёт о4× разрешении не относится к PSP-подписи или ROM.
- Текст делает «сначала разгон2000MHz/CPU4GHz и охлаждение» обязательным для эмуляции на основании одного Switch-случая GPU1000MHz. При этом сам относит retro/PPSSPP к лёгким задачам без такого требования. Ни одна частота не признана безопасной настройкой нашей платы; разгон, governor и охлаждение не выполнялись.
- Механический census таблицы: **33 строки платформ**, из них **24 — общие ожидания по классу железа**, **8 — сообщения участников чата**, **одна Wii U — только вопрос без подтверждения**. У22 общих ожиданий стоит зелёная галочка; её нельзя читать как first-hand BC-250 test. PS2/GameCube/Wii здесь не измерены на нашей плате.
- Switch/PS3/PS4 — рассказы о конкретных играх/версиях, часто без полного следа clock/renderer/конфига. Stock Xenia «низкая скорость» и Canary «меню отвечает на геймпад, игра чёрная» — разные варианты. Отклик геймпада подтверждает только чужой host input, **не** Waveshare pairing/power controller. EmuDeck/Steam input/Batocera — host/OS установки, не проверенные здесь. ROM, BIOS и ключи не скачивались; их законное происхождение и права остаются отдельным условием, а «искать ключи» не поручение.
- RDNA2/gfx1013 словарь главы расходится с импортной AI-главой RDNA-1.x; это provenance gap, не новый ISA probe. Никакой эмулятор, ОС, бинарник, ROM, игра, драйвер, firmware или hardware действие не выполнялось.

Следующая отдельная непрочитанная Russian primary — `docs/ru/16-usb-peripherals.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian USB/peripherals: роль документа разобрана

Отдельная Russian primary `docs/ru/16-usb-peripherals.md` учтена целиком: 31 667 байт, 201 строка, SHA-256 `27ff689db163a3e5d32490ed2b7ec8e62dc6c455fa9788bd23c5cd1d810736b4`. Диапазоны 1–70, 71–140, 141–201 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase47 preflight и local pinned Git blob совпали после EOL-нормализации. Девять относительных ссылок существуют; linked/remote Telegram/4PDA/видео/магазины не проверялись. Receipt, provenance,14 групп замечаний и EN/RU структура: `phase122-russian-usb-*.json`. RU/EN USB главы имеют одинаковые позиции15 заголовков и201 строку, но разные bytes/hash; тела не слиты.

- Четыре задних USB-порта и отсутствие внутренних headers взяты из внешнего справочника, не пересчитаны на целевой ревизии. «USB3 фактически x2» не имеет понятной электрической единицы и **не** равно двум PCIe-линиям M.2. Просадка5V до4.3/2.3–3.2V описана на **одной проблемной плате**; сам текст приводит другую с работающим bus-powered hub. Ни универсальная слабость USB-рельса, ни риск «сжечь порт» так не доказаны.
- Отдельно питаемый USB-хаб — **обратимый lead без пайки**, но supply rating, защита от обратной подачи VBUS и перечисление устройств на нашей плате ещё не проверены. Резка upstream VBUS и подача5V от ATX меняют топологию питания; «земля общая автоматически» не заменяет проверку возвратного пути данных, sequencing, ограничения тока и защиты. Один успешный чужой хаб не разрешает резать дорожку/провод, паять или включать нашу плату.
- Раздел называет M.2 **PCIe2.0×2** и одновременно обещает прямую работу **SATA-протокольного** M.2 SSD. SATA-support не следует из PCIe-линий; identity-глава формулирует «PCIe или SATA», exact slot wiring не измерен. ASM1166/PH516 — ограниченные сообщения о вариантах контроллера. SATA-данные и отдельные5V питания диска — разные цепи; buck wiring взято из пересказа видео без целевой электрической квалификации.
- Слепая замена всех `nvme` на `sda` в SteamOS repair script может указать на **другой диск** и повредить данные; это не универсальный фикс. Не трогались диски/разделы/инсталлятор. Один DisplayLink dock без видео, приписанный TPM/BIOS, не доказывает лимит native GPU outputs: USB DisplayLink — отдельный путь, уже указан в display-главе.
- DS5Dongle на **Raspberry Pi Pico2W**, GameSir со своим2.4GHz приёмником и отзыв об UGREEN в USB2 — **не** постоянно подключённый Waveshare-контроллер питания/геймпадов. Утверждение BT≥5 для `hid-playstation` и Direct-mode audio не проверены на нашем хосте. Ни USB/BT, драйверы, реле, Waveshare, BIOS, PSU или hardware операции не выполнялись.

Следующие отдельные непрочитанные Russian primary — `docs/ru/faq.md` и `troubleshooting.md`; остальные локали и большой корпус импорта, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian FAQ: роль документа разобрана

Отдельная Russian primary `docs/ru/faq.md` учтена целиком: 25 679 байт, 185 строк, SHA-256 `1fbb41e0e150f889e261840d8fd9d026321b3a4d9c1574553b65075bb41f4b01`. Диапазоны 1–65, 66–130, 131–185 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase50 preflight и local pinned Git blob совпали после EOL-нормализации. Все 48 относительных ссылок существуют; их техническое содержание и удалённые источники не перевалидированы. Receipt, provenance,16 групп замечаний и EN/RU структура: `phase123-russian-faq-*.json`. RU/EN FAQ имеют одинаковые позиции12 заголовков и185 строк, но разные bytes/hash; тела не слиты. FAQ — карта глав, не новое измерение платы.

- Короткие ответы превращают условные рассказы в абсолюты: «нет кнопки, сразу от12V» смешивает `AUTO_PWRON`/`PWR_SW`/`PS_ON`; «CMOS и бумажная прокладка при no-POST» не диагностика; «VCN недоступен ⇒ всегда CPU encoder» не доказывает отсутствия кремния или фактический режим Sunshine.
- PSU≥300W/single-rail, EPS/PCIe ориентация, дымящийся кабель=«поддельная медь», thermal pads и 85/90°C пороги нельзя переносить на target safety без измерений. FAQ требует **прореживать рёбра радиатора** как самый дешёвый путь, тогда как полные cooling/case главы сохраняют **варианты без резки**. Никакой проводки, резки или stress.
- Bazzite/Fedora COPR, обязательный navi10 symlink, «любой Flatpak без GPU», Wayland→X11, `mitigations=off`, `nosmt=force`, zRAM32 и kernel rollback зависят от версии и меняют хост/защиту. Датированный Windows Code43/IOMMU статус не является постоянным законом железа. ОС и службы не менялись.
- «J4004 только, clip не работает» расходится с **сообщённым оператором F1-прошиванием** и не закрывает exact image/full dump/independent recovery/coldboot/readback. 2000MHz/CPU4GHz/«все40CU», 1.325V, «слишком сильный undervolt безвреден» и12GB VRAM — чужие настройки, а последний абсолют противоречит сохранённым no-boot/failed-CMOS случаям. Ни BIOS/CMOS, ни OC, ни драйверы не тронуты.
- DP→HDMI audio/video, WiFi fixes, FPS/CPU-bound, цена и «Mac GPU никогда» остаются краткими датированными выводами соответствующих глав, не target-проверкой. Ни один FAQ-ответ не подтверждает Waveshare/gamepad/power, signed PSP substitution или VCN acceptance.

Следующая отдельная непрочитанная Russian primary — `docs/ru/troubleshooting.md`; затем русскую когорту Markdown можно сверить по hash/line receipts, **не** объявляя весь import завершённым. Privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## Russian troubleshooting: роль документа разобрана

Отдельная Russian primary `docs/ru/troubleshooting.md` учтена целиком: 24 515 байт, 116 строк, SHA-256 `534e39c8fefa79b32a6d4c3134c8e96d738992bff042057b9fc531b5180c1b6b`. Диапазоны 1–60, 61–116 без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw bytes сохранены, прежний phase50 preflight и local pinned Git blob совпали после EOL-нормализации. Все53 относительные ссылки существуют, но их технические тела и удалённые GitHub/4PDA/Reddit/видео источники не проверены. Receipt, provenance,14 групп замечаний и EN/RU структура: `phase124-russian-troubleshooting-*.json`. RU/EN troubleshooting имеют одинаковые позиции9 заголовков и116 строк, разные bytes/hash. Таблица «симптом→причина→фикс» — указатель к расследованию, не целевой диагноз.

- «Нет POST только с NVMe» не доказывает, что виноваты Windows EFI-разделы. `wipefs -a` уничтожил бы метаданные диска; совет **не выполнялся**. Чёрный экран не указывает однозначно на IOMMU, KWin, symlink, kernel regression, CMOS или кабель. Ни один такой shortcut не разрешает BIOS flash.
- Резка стоковых рёбер, 80/90°C пороги, +50/+25mV и ≥700mV — чужие условия, не безопасный профиль нашей платы. «GPU reset всегда валит весь APU» и «ошибка ACPI→`acpi=off noapic`→перешить» слишком сильные причинные переходы без target trace. «Нажми кнопку для пробуждения» расходится с FAQ «кнопки нет» и buying-советом auto-suspend≈10W. Никакого OC/stress/OS/CMOS.
- Stock24CU — **не поломка**, требующая 40CU unlock. MangoHud655%, governor, clock patch, headless glmark, CPU-bound и zRAM/zswap/UMA относятся к разным слоям driver/telemetry/memory; нужны точные показания target, а не одна таблица решений. Не запускались `umr`, install-скрипты, драйверы, службы или swap/BIOS-правки.
- «J4004 только, clip не работает» противоречит сообщённому оператором F1-прошиванию и не заменяет double-read, независимый recovery, exact image, coldboot/readback. No-POST после GDDR6 timings не доказывает испорченные **ROM bytes** вместо настроек. Предполагаемая BGA-трещина и reflow — опасная гипотеза из сообщества, не диагностика и не поручение греть плату. Никакого диска/PSU/programmer/flash/rework.

**Сверка Russian handbook cohort:** все19 отдельных Markdown-файлов `docs/ru/` сошлись с live raw SHA-256, размерами, числом строк и своими document-role receipts: суммарно **758 806 байт и 4 728 строк**. Это учёт ролей, не повторное чтение linked bodies и не проверка всех технических утверждений. **35 строк по ролям** ранее скрывались по privacy/contact/credential фильтрам; global privacy/rights clearance нет. Машинная сверка: `phase124-russian-cohort-role-reconciliation.json`. После English/Arabic/Russian handbook cohorts большой корпус импорта, остальные локали, queued native next20, SAST и независимый review остаются открытыми. Следующий отдельный непрочитанный языковой источник — German primary `docs/de/00-start-here.md`. Native120/176/559 не изменён.

## German start-here: роль документа разобрана

Отдельная немецкая onboarding-глава `docs/de/00-start-here.md` учтена целиком: 11 061 байт, 143 строки, SHA-256 `65924a1c04819d99d73891f4a3f9185f6bbbdae04e4496d0481c592c4d108356`. Диапазоны 1–75 и 76–143 прочитаны без потери вывода; privacy prefilter совпадений не дал, но это не глобальный clearance. Исходные байты сохранены, local pinned Git blob совпал после EOL-нормализации. Все 27 относительных ссылок существуют, 25 ведут в English и две в German FAQ/troubleshooting; тела ссылок и внешние источники этой проверкой не валидированы. Receipt, provenance, 11 групп замечаний и EN/DE структура: `phase125-german-start-*.json`. Немецкий текст прямо объявляет English основным; 18 Markdown-заголовков стоят на две строки ниже английских из-за вводного предупреждения, но хэши и тексты различны. Это не доказательство точности перевода.

- Маршрут «питание → проредить рёбра → Bazzite → firmware symlink → OC → Wi-Fi» является импортным onboarding, а не обязательной спецификацией нашего экземпляра. Резка рёбер в схеме и checklist конфликтует с ранее сохранёнными вариантами охлаждения без резки. Чужой порог FurMark не является тестом платы; ничего не резали и не нагружали.
- PCIe8-pin/235W, pinout, провод и «вентилятор вращается/есть видео ⇒ POST» требуют целевой электрической проверки, а не переноса с перевода. `navi10_gpu_info.bin` symlink может устаревать относительно `cyan_skillfish`; `vainfo` проверяет VA-API video, а не всю RADV graphics acceleration. Путь card0 и версии kernel/Mesa/image зависят от хоста. ОС, прошивку GPU и питание не меняли.
- VRAM512 dynamic, IOMMU Disabled, `nomodeset`, CMOS после flash и дальнейшая рекомендация 10GB/6GB fixed — советы источника, не policy нашего BIOS. Отключение IOMMU меняет защиту и виртуализацию; CMOS не восстанавливает ROM. Никакого BIOS/CMOS/flash/boot изменения.
- Глава называет `oberon-governor` стандартным, но её команды ставят и включают `cyan-skillfish-governor-smu`. Автоматический старт до настройки кривой расходится с отдельной OC-главой. 2000MHz/+30% FPS, 40CU и undervolt не подтверждены на цели. Команды установки, systemd, GRUB и reboot прочитаны как данные, не исполнены.
- «Нет hardware video encoding», «16GB VRAM» и категорическое «ROCm тупик» не заменяют разделения VCN driver/firmware, общей памяти и позднего modified-MEC/HIP отчёта. Глава не подтверждает Waveshare gamepad/power, F1/J004/SPI recovery или замену подписанного AMD PSP. Никакого hardware/firmware/host действия.

Следующий отдельный немецкий документ — `docs/de/01-what-is-bc250.md`; весь оставшийся корпус, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German identity: роль документа разобрана

Отдельная German primary `docs/de/01-what-is-bc250.md` учтена целиком: 21 341 байт, 172 строки, SHA-256 `4979545a2e01f3f32c1d18b79e499f83b1fde731c3865431f5079bd3c3458b9a`. Диапазоны 1–85 и 86–172 прочитаны без renderer loss; privacy prefilter совпадений не дал, но это не глобальный clearance. Исходные байты сохранены, local pinned Git blob совпал после EOL-нормализации. Все 22 относительные Markdown/HTML-ссылки существуют; их тела и внешние GitHub/Telegram/Reddit/производительские источники этой проверкой не подтверждены. Receipt, provenance,11 групп замечаний и EN/DE структура: `phase126-german-identity-*.json`. Немецкое предупреждение называет English основным; девять Markdown-заголовков стоят на две строки ниже английских, но хэши и тексты отличаются. Совпадение структуры не доказывает точность перевода.

- «Нет x86-BIOS», происхождение от отбракованного PS5 кристалла, Cyan Skillfish/Oberon/Ariel, RDNA2 при `gfx1013` и сравнение с 4700S/4800S — импортное описание, не установленная идентичность нашей платы. Linux на BC-250 не тождественен взлому PS5. Нужны целевые ROM/CPUID/PCI/firmware evidence для сильных выводов.
- 16 GB GDDR6 в этой главе **общий пул**, не отдельные 16 GB VRAM. BIOS 12 GB allocation не одобрена для цели. «VCN отсутствует/только software encode» сильнее имеющегося наблюдения о недоступном firmware/driver/runtime пути. Игровые FPS, частоты, 4K HDMI, USB, LLM и eGPU «медленнее» смешивают чужие конфигурации и вывод из ограниченной PCIe-полосы, не target benchmark.
- «Кулер обязательно модифицировать» конфликтует с ранее сохранёнными no-cut airflow вариантами. BIOS-reset, бумажная прокладка и двухцветная NIC LED — частные сообщения, не диагноз. Утверждение GDDR6 «256→445 GB/s без выигрыша FPS» противоречит же заявленным штатным 448 GB/s и не доказано сравнительным тестом. Размеры 340/310 mm и «точные» STL нельзя переносить в наш корпус без замера.
- Таблица смешивает **TDP 220 W**, чужое типичное потребление 67–85 W и арифметические **324 W** для трёх контактов J1000 по 9 A × 12 V. Это разные величины; последнее **не является безопасным бюджетом питания всей сборки** без derating контактов, провода, PSU, ориентации и ревизии платы. Диаграмма pinout не проверена на нашей плате и не использовалась для подключения. J2000 LED1/LED2 и J2001 PGD названы разными, но PGD=5V и их wiring не измерялись.
- «PCIe2.0×2 или SATA III» не доказывает прямую SATA-проводку M.2. DP1.4/4K120/8K60 и звук через любой DP→HDMI не являются результатом EDID/адаптерной проверки; программное включение незапаянного второго DP не создаёт физический разъём. Спецификации перечислены как community provenance, не hardware acceptance.
- Эта глава не разрешает питание, резку, правку BIOS/OS, flash или recovery. Она не доказывает операторский F1-путь, J004/clip, постоянно подключённый Waveshare для питания и геймпадов, подмену подписанного AMD PSP или разблокировку VCN. Exact image, full dump, независимое восстановление и readback/coldboot остаются обязательными воротами. Никаких команд источника, электрических или firmware действий не выполнялось.

Следующий отдельный German primary — `docs/de/02-buying.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German buying: роль документа разобрана

Отдельная German primary `docs/de/02-buying.md` учтена по ролям всех 163 строк: 24 741 байт, SHA-256 `0091b59fa77740d9bd9b454d4da8e757a12e680e1f41b4765c2b5fdb62ad4c78`. Диапазоны 1–80 и 81–163 прочитаны без renderer loss; четыре строки с контактным Telegram-handle (51,61,133,155) показаны только с редактированием handle, не опубликованы целиком. Остальной privacy prefilter совпадений не дал; глобального privacy/rights clearance нет. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Все 16 относительных Markdown/HTML-ссылок существуют; linked bodies и внешние торговые/Telegram/4PDA/Reddit страницы не проверялись. Receipt, provenance,10 групп замечаний и EN/DE структура: `phase127-german-buying-*.json`. Немецкая глава явно вторична к English; десять Markdown-заголовков расположены на две строки ниже, но хэши/тексты разные. Совпадение структуры не подтверждает точность перевода.

- eBay, AliExpress, Ozon, Avito, OLX, hand-to-hand и пересылка — **датированные чужие каналы**, не сегодняшнее наличие, законность импорта или рекомендация продавца. Приведённые USD/RUB/UAH/EUR суммы относятся к разным лотам, комплектациям, датам, доставке и курсам; $630 за готовую единицу нельзя напрямую сравнивать с $70–130 за голую плату. Никакой live-оценки или предела покупки не установлено.
- Маршрут «переведи деньги посреднику и жди месяц» несёт необратимый финансовый риск. Чатовый поручитель/эскроу и контакт не верифицированы; адреса/handles не переносились в активные документы. Не было платежа, переписки, заказа или проверки текущих объявлений. Названные в источнике репутационные претензии к продавцам остаются **непроверенными чужими сообщениями**, не обвинениями проекта.
- «Любую версию BIOS можно прошить community mod» не проходит наши exact-image, подписанный PSP, полный dump, независимый recovery, coldboot/readback gates. Готовый build, modified BIOS, LOP300/другой PSU, охлаждение и OS в лоте не подтверждают его состояние, питание или безопасность. Советы «сначала купи плату», PETG/печать и обязательный cooling mod не становятся требованиями нашей сборки без замера и согласования.
- Указанная масса «голой платы ≈0,86 kg» не согласована с прошлой identity-главой «≈0,4 kg с радиатором»; определения/источники требуют выяснения. Idle 100–125/70/35–45 W, GPU ≈30 W и suspend ≈10 W смешивают чужие стенды и точки измерения. `_CPC`, GDDR6 и governor не измерены на нашей плате; auto-suspend не заменяет проектирование постоянно подключённого Waveshare-контроллера питания.
- Отсутствие Mesh/VRS и hardware encode/decode нельзя объявлять полностью доказанным по обзорной таблице; нужно разделять кремний, firmware и driver. «Майнинг при постоянной температуре ⇒ BGA надёжен» — недоказанный причинный переход. «Нет сигнала ⇒ повреждена APU» тоже не диагноз. Горячая зона M.2 и USB-SATA обход зависят от конкретного корпуса. Маркировка чужих guides как «проверенных» не подтверждает их wiring/flash команды.

Глава не подтверждает F1/J004/clip recovery, Waveshare gamepad/power, подмену подписанного PSP, VCN unlock или готовность полной прошивки. Никаких денег, контактов, покупок, ОС, BIOS, прошивки или hardware действий. Следующий German primary — `docs/de/03-power-supply.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German power: роль документа разобрана

Отдельная German primary `docs/de/03-power-supply.md` учтена целиком: 53 799 байт, 402 строки, SHA-256 `0debb250b95c4dba486c5a484fd338bbc8a65751951e5a21d0ac3b89efd9f8ae`. Диапазоны 1–80, 81–160, 161–240, 241–320 и 321–402 прочитаны без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Пять относительных Markdown/HTML-ссылок существуют; их тела и внешние GitHub/Telegram/4PDA/Reddit/видео/производительские источники этой проверкой не валидированы. Receipt, provenance,12 групп замечаний и EN/DE структура: `phase128-german-power-*.json`. **German не просто та же English-глава плюс вводные две строки:** в German есть отдельный раздел физики на строках 40–57. Поэтому 24 заголовка/402 строки против English 23/382; после этого места сопоставимые заголовки сдвинуты на 20 строк. Точность перевода и электрических сведений из структуры не следует.

- Исходник смешивает оценку потребления платы, сообщения о токе с амперметра/автосубтитров, мощность **на стене**, паспорт БП, номинал PCIe-разъёма и арифметику `3×9 A×12 V=324 W` вплоть до 468 W для других контактов. Это разные границы измерения. **324/468 W не являются проверенной безопасной мощностью J1000, кабеля или всей сборки.** Предложение заводского 6-pin через 8-pin адаптер без пайки также не прошло электрическую квалификацию; 6-pin/8-pin нельзя объявить взаимозаменяемыми по форме.
- Формулы `P=U·I`, `I²R` и `IR` сами по себе корректны, но из них не следуют «16 AWG всегда холоден при 20 A», единый безопасный провод для любого разъёма или «магнит удостоверяет чистую медь». Магнит не обнаружит меднённый алюминий, а токи параллельных жил могут распределяться неравномерно. Внутри главы рекомендации 16 AWG против 18/20 AWG для Micro-Fit и 18 AWG для triple-output зависят от разных сценариев и не образуют проверенный harness.
- Предупреждение не путать PCIe и EPS существенно, но рисунок J1000 и ориентация pin1 не сверены с целевой ревизией; фраза об «EPS-class source» рядом с запретом EPS-штекера дополнительно неоднозначна. J2000 и J2001 имеют разные signal-позиции, а заявленные PGD/LED напряжения, точное сопряжение Micro-Fit и топология рельсов не измерялись. Текст одновременно требует один PSU/одну шину для второй подачи и ссылается на rack с другим PSU. **Разветвление одного исходного PCIe-кабеля на дополнительные входы платы не увеличивает допустимый ток исходного кабеля/БП.** Не брали источник как wiring-инструкцию.
- Рецепты запуска server PSU, открытые AC-клеммы Mean Well, перемычка PS_ON, перепиновка, обрезка проводов, снятие защёлки, замена crimp пайкой, 40CU/FurMark и прямой обход разъёма — чужие рискованные операции. «Вставить обычный ATX PCIe и замкнуть PS_ON скрепкой» не является буквально нулевым вмешательством или доказанно безопасной процедурой для нашей платы. `-12`/`-24` различают номинальное выходное напряжение конкретной серии, но не заменяют паспорт и целевые измерения. Никакого PSU/кабель/AC/OC действия.
- **Важные leads для задачи Waveshare, не готовое решение:** импорт описывает чужую ESP32-схему, которая видит BLE-рекламу геймпада и включает питание, и отдельный no-solder ATX PS_ON latch-adapter, использующий `system_on` с fan header. Это разные устройства и не Waveshare-интеграция. «Нет кнопки, boot при 12 V» здесь сосуществует с `AUTO_PWRON`, `PWR_SW`, shutdown/suspend и `system_on`; состояния нельзя свести к простому разрыву питания. Нужно на самой ревизии подтвердить сигнал header, дежурное питание MCU, изоляцию входов, PS_ON совместимость БП, сопряжение геймпада, fail-safe off и последовательность питания периферии. LOP без enable требует иного переключения; утверждение о почти нулевом потреблении 5VSB не измерено.
- Описанная «true-ATX» модификация со снятием индуктивности/отбором standby5V разрушительна и противоречит предпочтению оператора **без пайки и подъёма ножек**. Она не разрешена. Датированные рекомендации моделей БП, цены, шум/вентиляторы, фото сборок и приписанная надёжность не являются target approval или правом на перепубликацию.

Ни один источник не доказал операторский F1/J004/clip recovery, надёжную постоянно подключённую Waveshare для power/gamepad, подмену подписанного AMD PSP или готовность полной прошивки. Никаких источниковых команд, проводки, включения питания, BIOS, firmware или hardware действий не выполнялось. Следующий German primary — `docs/de/04-cooling.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German cooling: роль документа разобрана

Отдельная German primary `docs/de/04-cooling.md` учтена целиком: 41 250 байт, 308 строк, SHA-256 `0ad9aafc1010c319bd7004a92ea7f56406965bd70ad69fe477a348c3ab5c8ee5`. Диапазоны 1–80, 81–160, 161–240 и 241–308 прочитаны без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Шесть относительных Markdown/HTML-ссылок существуют; их тела и внешние GitHub/Telegram/4PDA/Reddit/видео/торговые источники не валидированы. Receipt, provenance,9 групп замечаний и EN/DE структура: `phase129-german-cooling-*.json`. У German 308 строк, English 307; 21 настоящий Markdown-заголовок имеет тот же уровень и позицию +2 из-за вводного предупреждения. Два `#` внутри shell-кода не заголовки. Совпадение структуры не доказывает перевод/термические утверждения.

- Начало и «минимальная» таблица предлагают **необратимо проредить штатные рёбра**. Но эта же глава явно сохраняет вариант **без резки**: штатные рёбра, push-pull и разделённый воздушный канал. Это соответствует предпочтению оператора не пилить/не паять; чужой результат при разогнанном CPU/GPU — **lead для проверки геометрии и температуры**, не гарантия для нашей ревизии. Удаление рёбер, шлифовка и металлическая пыль несут риск для основания/кристалла/платы; ничего не резали.
- GPU edge, CPU Tctl, наружные VRM/GDDR6/SSD точки, package и wall power — разные метрики. Источник одновременно говорит «у GDDR6/backplate нет датчика» и приводит температурную таблицу: измерение с внешним датчиком нельзя молча считать hwmon. Пороги 85/90/95/100/107 °C и 81,8 °C для SSD не являются универсальными пределами нашей платы и накопителя. Чужой 40CU/2GHz непрерывный прогон на двух вентиляторах достиг высоких температур/троттлинга; заявление о бесконечной работе при 1500 MHz не target endurance proof.
- Пиксельные артефакты и сбои через 30–60 минут **не** доказывают именно перегрев VRAM. Совет менять BIOS VRAM split не подтверждён как thermal fix. 1500→2000 MHz означает +33,3 % частоты, но не гарантированные +30 % FPS. Одновременные FurMark/CPU stress и долгие compute-прогоны могут тяжело нагрузить эту машину/плату; не запускались.
- Давление/CFM/RPM вентилятора, «push-pull удваивает давление», выигрыш 3–5 °C от вытяжки и положение центра — смесь паспортов, отдельных сборок и автосубтитров. Результат зависит от ламелей, shroud, backplate и корпуса. AIO, custom-loop и tower-bracket добавляют риски утечки, усилия крепления, перекрытия M.2 и оставленных без обдува VRM/GDDR6. OC- и температурные цифры других сборок нельзя переносить в нашу. Никаких печатных деталей, жидкости или крепления не применяли.
- Импорт противопоставляет встроенный `nct6683 force=true` для наблюдения и внешний `nct6687 force=true` для PWM. Точный Super-I/O, header, fan2/pwm2 и права записи не подтверждены на целевой ревизии; hwmon-нумерация плавает. BIOS Customize и CoolerControl могут спорить за PWM. Никакие DKMS/modprobe/службы/ручные записи вентилятора не выполнялись. Fan header как возможный `system_on` для Waveshare из прошлой главы пока также **не измерен**.
- TIM/PTM7950, putty, пасты, backplate и pad выигрыши — чужие условия. Толщины pad различаются по зонам и сборкам; ошибочный gap может ухудшить контакт die или давить на компоненты. «Сенсоров нет ⇒ обязательно такие pads» не доказано. Жидкий металл электропроводен и в этом контуре не применялся. Не меняли пасту, прокладки, BIOS или железо.

Глава не подтверждает управление Waveshare, F1/J004/clip recovery, подписанный PSP, VCN или полную прошивку. Следующий German primary — `docs/de/05-case.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German case: роль документа разобрана

Отдельная German primary `docs/de/05-case.md` учтена целиком: 39 962 байта, 345 строк, SHA-256 `358499faa1bdd7fbb6f9fe36b7d25f763b09ba1523da8ea69068bd13a8b4dc8f`. Диапазоны 1–80, 81–160, 161–240 и 241–345 прочитаны без renderer loss и совпадений privacy prefilter; это не глобальный privacy/rights clearance. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Девятнадцать относительных Markdown/HTML-ссылок существуют; linked bodies и внешние GitHub/Telegram/Printables/MakerWorld/4PDA/Reddit/магазины не перевалидированы. Receipt, provenance,9 групп замечаний, EN/DE структура и проверка локальных asset-имён: `phase130-german-case-*.json`.

**German/English не идентичны:** German 345 строк/30 заголовков, English 328/29. В German добавлен раздел про параметрический Steam Cube на строке159; сам источник признаёт его **не напечатанным, не собранным и термически не испытанным**. До вставки заголовки сдвинуты на две строки, после — на 17. Размеры корпуса и температурные цели этого концепта не являются проверенной посадкой или benchmark.

- Вводная часть сохраняет конкретный **безрезовый минимальный sleeve** с одним вентилятором и локально присутствующими `BC-250-FanSleeves.3mf`/`bc-250-body.step`. Это не то же самое, что более поздний Shell Case с изображёнными прореженными рёбрами. Наличие 3MF/STEP и чужие 70 °C при150 W доказывают файл/сообщение, не fit, давление защёлок, PSU clearance или температуру нашей платы. Большинство других моделей учитывают уже изменённые ламели, поэтому не подходят по умолчанию под требование «не резать». Ничего не печатали.
- Выбор корпуса зависит от конкретной семьи БП, вентилятора, версии радиатора и воздушного пути. Фото, название STL или метка «проверенный» не подтверждают безопасную геометрию, доступ к разъёмам и поведение охлаждения. Совет вывести CMOS-clear наружным переключателем — новая электрическая/механическая модификация; CMOS не заменяет восстановление ROM. Не сверлили, не подключали и не переключали.
- Отдельные сборки с AIO, ATX, экраном, eDP, USB-HUD и ESP32-реле — каталог чужих систем, не тест Waveshare. Relay remote-power — только lead; Pi Zero HUD отвечает за индикацию, не доказанное управление геймпадами/питанием. Водоблок, открытый PSU, крепёж и 40CU/OC цифры требуют отдельной проверки нагрузки, зазоров, утечек и электрической защиты. Личные фото/никнеймы и внешние файлы не переносятся в проект без provenance/rights.
- Проверены **имена** 13 строк таблицы с пометкой `chat` против локальной `assets/stl/`: 61 файл в этом каталоге (48 STL, 11 3MF, 2 STEP). У двух точно названных package-файлов `.rar`/`.zip` из строк217/219 **нет точного имени в локальной папке**; сокращённые групповые названия не считались отсутствующими. Это не доказательство, что геометрии вообще нет: близкая 3MF может быть производной, но byte/content equivalence не проверялась. Подсказка таблицы «chat-файлы зеркалированы» для этих package-имён не подтверждена. Машинная проверка: `phase130-german-case-local-asset-name-check.json`; бинарные файлы, архивы, лицензии и печать не открывали.
- Заявленный внешний каталог ~143 дизайнов, текущая доступность, цена и права скачивания/перепубликации не проверены. Открытый стенд или переиспользованный корпус — также не автоматическое безопасное решение. Ни один дизайн не доказывает постоянно подключённый Waveshare, F1/J004/clip recovery, подписанный PSP, VCN или готовую полную прошивку.

Следующий German primary — `docs/de/06-linux.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German Linux: роль документа разобрана

Отдельная German primary `docs/de/06-linux.md` учтена по ролям всех 581 строк: 61 581 байт, SHA-256 `5d8243c735a0d9ef246b00211f78fba1d9d526b83022217275eee574cdc7f435`. Диапазоны 1–80, 81–160, 161–240, 241–320, 321–400, 401–480 и 481–581 прочитаны без renderer loss. Строка11 содержит **общую инструкцию о вводе sudo-пароля**, не значение секрета; она разобрана с замаскированным словом и не опубликована целиком. Иных совпадений privacy prefilter нет, глобального clearance нет. Raw source сохранён; local pinned Git blob совпал после EOL-нормализации. Тринадцать относительных ссылок существуют, тела и внешние upstream/Telegram/Reddit/видео страницы этой проверкой не валидированы. Receipt, provenance,13 групп замечаний и EN/DE структура: `phase131-german-linux-*.json`. У German 581 строк, English 578; 32 настоящих заголовка совпадают по уровням, первые30 стоят на +2, последние два на +3. Структура не подтверждает точность перевода или версии инструкций.

- TL;DR/схема делают `navi10`→`cyan_skillfish` symlink будто обязательным. Далее сам документ говорит, что современные firmware-пакеты уже содержат `cyan_skillfish_gpu_info.bin` и symlink — **условный старый workaround**, лишь после диагностики недостающего файла. Ни symlink, ни initramfs не меняли. Fedora/Bazzite/Arch/Alpine/SteamOS, версии Mesa/kernel и «лучший» LTS — датированные срезы, не состояние нашего хоста. Одно чужое сравнение дистрибутивов по FPS/температуре не контролировало конфигурацию целевой платы.
- Bazzite rebase на `latest`, COPR/AUR/сторонние setup scripts, `rpm-ostree` pin/rollback, Fedora GRUB/dracut, Arch keyring и пакетные источники меняют boot/доверие/службы. В тексте Fedora43 mainline Mesa уже достаточна, но приведён старый сценарий patched COPR. Активация SMU-governor до проверки кривой и card0/card1 — не безопасный дефолт. Источник сам передаёт сообщения, что 40CU unlock ломал **вентилятор и Xbox-контроллер** в некоторых установках; это особенно важно для будущего Waveshare, но не доказано на нашей плате. Никаких пакетов, сервисов, ребейзов, bootloader-правок или запусков скриптов.
- `mitigations=off` отключает CPU-защиту ради чужого FPS-числа; это **не условие загрузки GPU**. «IOMMU всегда выключить», VRAM512, ACPI-SSDT, zswap/32GB Btrfs swap и CoreOS `umr`-записи в GPU-регистры — отдельные security/firmware/runtime решения, не универсальный fix. `3 959 290` страниц при 4 KiB = **15,1035 GiB**, а `gttsize=14750 MiB` ≈ **14,404 GiB**: три лимита нельзя свести к одной «14,5–14,75 GB» оценке. Runtime 40CU через `umr` не эквивалентен проверенному kernel/image пути и несёт wedge-риск. Ничего не записывали.
- В начальной схеме `vainfo` подан как проверка ускорения GPU; ниже глава ожидает его **ошибку** из-за VA-API/VCN. RADV Vulkan/OpenGL, VA-API video и число CU — разные проверки. Два Vulkan-device entry не доказывают два физических GPU, двигающийся debugfs clock не доказывает, что конкретная игра рендерится на GPU. «VCN от Sony закрыт и никогда не заработает» сильнее доступных сведений; отсутствие VA-API не доказательство отсутствия кремния. Никаких target GPU/VCN результатов эта глава не добавила.
- `RADV_DEBUG` и cache/driver overrides зависят от Mesa и приложения. Удаление Mesa/Steam shader cache, глобальная перемена окружения, `kernel.dmesg_restrict=0`, downgrade/versionlock и ACPI override — вмешательства в хост или защиту, а не безвредная диагностика. `nct6683 force=true` для чтения против внешнего `nct6687 force=true` для PWM требует проверки точного Super-I/O/header и исключения конфликтующих модулей; hwmon/card индексы меняются. Никаких DKMS, modprobe, fan-PWM или удаления cache.

Глава не устанавливает Waveshare power/gamepad architecture, F1/J004/clip recovery, подмену подписанного PSP, VCN unlock или готовность полной прошивки. Следующий German primary — `docs/de/07-windows.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German Windows: роль документа разобрана

Отдельная German primary `docs/de/07-windows.md` учтена целиком: 16 300 байт, 128 строк, SHA-256 `ac9f259fc468891d9db4885dfb7ee7ca0e3c3f90ad75fa0713f3244d2a6d77e2`. Диапазоны 1–70 и 71–128 прочитаны без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Девять относительных ссылок существуют; их тела и внешние GitHub/Telegram/AMD/форум-источники здесь не проверены на текущий статус. Receipt, provenance,8 групп замечаний и EN/DE структура: `phase132-german-windows-*.json`. German 128 строк/12 заголовков, English 126/12: заголовки сдвинуты на +2, но хэши/тексты различны. Это не доказательство точности перевода или нынешней поддержки Windows.

- «Code 43, нет игровых Windows-драйверов» — датированный **началом 2026** статус и чужие отчёты, не результат на нашей плате и не проверка текущих GitHub-ревизий. Неудачный `.inf`/device-ID эксперимент не доказывает, что ID «физически приварен» или что любой VM/IOMMU-passthrough невозможен навсегда. Ни Windows, ни BIOS не трогали.
- Два описанных WIP-пути различны. Отчёт о Keshas Windows PSP-драйвере с SOS, BAR5/MMIO и NBIO register-proxy — **host-driver reverse-engineering**, а не право записать свой подписанный AMD PSP в ROM и не доказательство готовой GPU-инициализации. Отдельная WDDM-2.0 reference implementation описана как без работающего shader/современного D3D/Vulkan/VCN; она не игровой драйвер. У этого автора Linux-governor repo и Windows-test repo не следует смешивать. Текущие исходники/коммиты в этом проходе не открывались.
- Test-signing Windows и отключение Secure Boot понижают доверие загрузки; PowerShell/PNP driver install может нарушить хост. Файлы `00.00.01`/переименованный installer, мошеннические «драйверы» и слух о **дистанционном brick из-за утечки** не являются проверенным firmware-механизмом. GitHub-адрес сам по себе не доказывает безопасность бинарника. Ничего не скачивали, не запускали и не устанавливали.
- Упомянутый `duggasco` 40CU unlock в этой главе отнесён к **Linux/amdgpu**, не к Windows. Это исправление классификации источника, не проверка текущего upstream и не безопасный runtime unlock. Ни один из Windows-отчётов не подтверждает F1/J004/clip recovery, Waveshare power/gamepad, signed PSP substitution, VCN или полную прошивку.

Следующий German primary — `docs/de/08-bios.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German BIOS: роль документа разобрана

Отдельная German primary `docs/de/08-bios.md` учтена по ролям всех 409 строк: 39 627 байт, SHA-256 `d76d928f236ff92970b7c3ed48aebca9fca696841a0f9ea2a6581dd33622afb1`. Диапазоны 1–85, 86–170, 171–255, 256–340 и 341–409 прочитаны без renderer loss; строки38/166/353 с контактными handles разобраны только после редактирования, не опубликованы целиком. Остальной privacy prefilter чист, но глобального clearance нет. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Все 11 относительных файлов-ссылок существуют; один фрагмент `06-linux.md#sensors--fan-control` ведёт в немецкий файл с **немецким** заголовком и не совпадает с ним. Receipt, provenance,12 групп замечаний, EN/DE структура и локальный firmware-catalog check: `phase133-german-bios-*.json`. German 409 строк/19 заголовков против English 406/19: первые два заголовка +2, остальные +4; сходство структуры не доказывает эквивалентность рецептов.

- Stock P2/P3/P4/P5, community P3 menu-mod, P5 mod и `P5.00_clv` — **разные образы и полномочия**. «P3 — безопасный стандарт» означает чужой относительный опыт, не одобрение для нашего exact image. Открытие AMI/AMD меню не подменяет подпись PSP и не доказывает загрузку модифицированного подписанного PSP. Плохие GDDR6/UMA/voltage настройки могут дать no-POST; CMOS не обязан исправлять это и не восстанавливает ROM bytes. `bc250_memcfg` — отдельный runtime lead, не «нулевой риск».
- Глава приводит полные SHA-256, но одновременно допускает сверку лишь первых16 hex-символов. Префикс и совпадение двух копий из одного непроверенного канала не доказывают происхождение/доверие и не заменяют полный hash конкретного образа. `Robin5.00` в таблице — **stock P5**, а пример скрипта предлагает назвать им модифицированный ROM: это опасная потеря идентичности файла. AFU `/P /N` меняет и NVRAM, internal flashrom `boardmismatch=force` отключает проверку платы. Ни один рецепт не содержит все ворота нашего exact image/full dump/independent recovery/approval/coldboot/readback. Ничего не прошивали.
- Внешний раздел утверждает «только J4004, SOIC clip не работает»; это **противоречит сообщённому оператором успешному F1-прошиванию** и не закрывает конкретное соединение нашего программатора. NeoProgrammer-порядок «стереть, потом открыть файл» вообще не сохраняет double read до стирания. Вариант flashrom с двумя чтениями и readback — полезная дисциплина, но не доказательство target chip ID или восстановления. BIOS_A1 16 MiB против SIO1_R 512 KiB, CH341A 3,3-V VCC против возможных 5-V data-lines и pin1/rail — критические ограничения, не проверенные на плате. Не подключали программатор и не стирали чип.
- TPMS1 «3V только при system-on», J4003 DET, fan header и прочие pinout/BOM записи могут быть **leads для будущего контроллера Waveshare**, но напряжение/доступность/изоляция не измерены. «J2 — единственный reset/debug» слишком сильный абсолют. `psptool` может извлечь компонент для анализа, но не подписать новый PSP. `srep` auto-reset у источника **не заработал**; его нельзя считать recovery. Secure Boot/CSM и IOMMU/UMA советы меняют boot/security policy, не применялись.
- Локальная копия `awesome-bc250/assets/firmware/` содержит только `DISCLAIMER.md`; сам disclaimer и `assets/PROVENANCE.md` относят firmware к **GitHub Releases, вне git-дерева**. Поэтому фраза главы «образы зеркалированы под `assets/firmware/`» неверна для этой локальной папки. `PROVENANCE.md` содержит полные SHA-256 как **метаданные**, но байты релизов не открывались и не сверялись. Особенно таблица называет `.zip` пакет `BC250_5.00_clv.zip` 16 MB, а provenance сообщает **2198 KB**; другой `bc250_3.00_clv1.zip` там **2201 KB**, тоже не raw 16-MiB SPI. Это не означает, что внутри ZIP нет 16-MiB ROM: архивы не извлекались. Машинная проверка: `phase133-german-bios-local-firmware-catalog-check.json`. Первичная локальная проверка ошибочно ожидала отсутствия второго ZIP в provenance и завершилась exit1; строка проверена заново, assertion исправлен, ошибка сохранена в `phase133-root-prep-first-attempt-error.json` до изменения документов.

Глава не подтверждает Waveshare power/gamepad, F1/J004/clip recovery, signed PSP replacement, VCN unlock или полную прошивку. Следующий German primary — `docs/de/09-overclock-undervolt.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German OC: роль документа разобрана

Отдельная German primary `docs/de/09-overclock-undervolt.md` учтена по ролям всех 647 строк: 81 925 байт, SHA-256 `40add5e7486fa4a8b48dcfcb83b423e7ec909d050db59d821075d7e8a00512a4`. Диапазоны 1–80, 81–160, 161–240, 241–320, 321–400, 401–480, 481–560 и 561–647 прочитаны без renderer loss. Строки383/632 содержат значение источниковой учётной записи и **не воспроизводятся**; строки420/421 совпали по `pwd`, но это shell current-directory, не секрет. Privacy/rights clearance в целом нет. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Все 25 относительных Markdown/HTML-ссылок существуют; linked bodies и внешние GitHub/Telegram/Reddit/форум/видео источники здесь не валидированы. Receipt, provenance,12 групп замечаний, EN/DE структура и арифметика: `phase134-german-oc-*.json`. У German 647 строк, English 645, 30 настоящих заголовков имеют одинаковые уровни: 29 позиций +2, один schema-заголовок +4. Похожая структура не делает источниковые напряжения/методы безопасными.

- В установочных командах SMU-governor предлагается **немедленно включить службу**, а ниже сам источник говорит, что автор поставляет её отключённой до проверки кривой из-за boot-black-screen. Это конфликт порядка, не инструкция нам пробовать. SMU, TT, старый Oberon, GUI и CPU SMU service могут управлять пересекающимися состояниями; card0/card1, TOML-схема, пределы 700/1129 mV и «2700 MHz» не проверены для цели. Экспериментальная воздушная кривая пересекает собственные консервативные границы главы. Не ставили governor и не писали напряжение.
- «4 GHz @ 1275 mV рекомендуем» расходится с собственным примером, где 4 GHz прошли короткий тест, но упали в игре, и с таблицей троттлинга. Источники расходятся также по CPU Vid ceiling 1300/1325 mV; запрос Vid не является измеренной rail voltage. История о двух отключённых CPU-ядрах, eFuse и необходимости обойти PSP-проверку — **сообщение сообщества**, не результат target fuse/ABL/SMU анализа и не путь к подмене подписанной PSP-записи. ACPI SSDT/cpufreq и idle-W цифры не целевые измерения.
- 40CU-направление описывает разные механизмы: патч amdgpu **при ранней инициализации** и runtime `umr` **после** загрузки драйвера. «Одинаковый конечный результат» не доказывает эквивалентность очередности, топологии, сброса или риска зависания. `SPI_PG_*` в таблице — **GPU shader/power-gating register, не серийная SPI-память BIOS**. Стабильные 36/38/40 CU различаются по кристаллу; мгновенный lockup при плохой CU не является безопасным диагностическим методом без recovery. Скрипты сборки kernel-модуля, постоянный systemd/boot arg, live manager и mask/health test не запускались.
- Арифметика отделена от рекламных процентов: FurMark **91→110 = +20,879 %**, не заявленные около25 %; Superposition **4647→6863 = +47,687 %**, что согласуется с «около48 %», но это чужой тест. 1500→2000 MHz = +33,33 % частоты, не автоматические +30 % FPS. Игры/разрешения/FSR/CU/OC и данные из авто-субтитров нельзя объединять в target benchmark. Длительные FurMark/OCCT, совместная CPU+GPU нагрузка и CU-перебор запрещены без разрешения на тяжёлую нагрузку; не выполнялись. На чужом 40CU/2GHz dual-fan опыте пик 107 °C GPU/100 °C CPU и падение throughput не обосновывают безопасный no-cut режим или дополнительную проводку J2000/J2001.
- «Слишком сильный undervolt безвреден, проходит за пять секунд» конфликтует с описанными blackscreen/hard-reboot, нестабильностью игр и возможным no-POST после memory-настроек. VRAM512/UMA split и `bc250_memcfg` зависят от workload; отсутствие SPI flash не делает изменение platform state нулевым риском. ZRAM→zswap/16-GB swapfile/fstab/GRUB и GTT/TTM лимиты — серьёзные host/disk изменения, не применялись. GDDR6 timing/frequency и bad-CMOS/ROM механизм не доказан без целевого readback; чужие 1800/1875/1950 MHz не безопасные пороги.
- В исходном тексте две строки с источниковым credential **скрыты** в артефактах. Во время первичного просмотра одна из них ошибочно появилась в кратковременном выводе инструмента; значение не повторено и не сохранено в проектных файлах. Санитизированное событие записано в privacy receipt/action log. Отдельный первоначальный EN/DE assert требовал +2 для всех заголовков и завершился exit1; реальная структура 29×+2/1×+4 проверена, assertion исправлен до изменения документов, ошибка сохранена в `phase134-root-prep-first-attempt-error.json`.

Глава не доказывает Waveshare power/gamepad, операторский F1 recovery, signed PSP substitution, VCN unlock или готовность полной прошивки. Последняя фраза вновь делает работу с рёбрами обязательной, хотя отдельная cooling-глава сохраняет вариант **без резки**. Следующий German primary — `docs/de/10-wifi-bt.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German WiFi: роль документа разобрана

Отдельная German primary `docs/de/10-wifi-bt.md` учтена по ролям всех 185 строк: 20 152 байта, SHA-256 `08b46e1849ede6d533dad097800a5ef433ea3e98cf0d0232367b9bcf7557f052`. Диапазоны 1–95 и 96–185 прочитаны без renderer loss. Строка113 совпала с широким privacy-фильтром из-за shell-переменной `$PWD` (текущий каталог), не пароля; показана с маской, секретного значения нет. Глобальный privacy/rights clearance этим не доказан. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Одна относительная ссылка (на English original) существует; внешние driver GitHub/Telegram/Intel/USB-IF/магазины и их нынешний статус не открывались. Receipt, provenance,8 групп замечаний и EN/DE структура: `phase135-german-wifi-*.json`. German 185 строк, English 182; 12 настоящих заголовков одинакового уровня: первые10 +2, последние два +3. Это не проверка точности перевода или драйверов.

- Список aic8800d80, Digma, RTL8821/8822/8851BU и старого `r8169` — смесь чужих опытов, generic Linux reports и датированных версий kernel. Название бренда не идентифицирует кристалл; `lsusb` даёт VID:PID, но само по себе не доказывает качество питания, radio coexistence или стабильность драйвера на нашей плате. Отдельно источник отмечает: для конкретного RTL8851BU WiFi-драйвер является сторонним, а Bluetooth у производителя **не заявлен для Linux**. Не покупать его как гарантированный WiFi+BT. Никакого нашего VID:PID/радио-теста не было.
- Обрывы при скачивании нельзя заранее списать на Realtek, USB5V, root hub или помеху USB3 в 2,4 GHz: это разные причины, требующие раздельного измерения. Перестановка в USB2/короткий удлинитель — обратимый lead, но чужое «~20 dB и никакой фильтр» не target RF-замер. `usbreset` и удаление системного `btusb` могут обесточить/отключить **другие** BT-устройства и геймпады; эти рецепты не выполнялись. Одна оценка WiFi 150 Mbit с BT против190 без BT не измеряет задержку/надёжность наших контроллеров.
- RPM/spec с moving `main`, `spectool` download, DKMS/`make install`, `rpm-ostree usroverlay`, USB fake-CDROM mode switch, `mokutil`/Secure Boot и Bluetooth branch меняют supply-chain/host/USB state. «RPM сохраняется через обновления» и «backport починил большинство» не универсальные обещания: сам текст приводит ошибки новых kernel/Debian и случаи обрывов после backport. Ничего не загружали, не собирали, не устанавливали, USB не сбрасывали.
- Краткий shopping-list и ссылка на объявление — не текущая доступность, цена или рекомендация продавца. WiFi/BT dongle **не** постоянно подключённый Waveshare-контроллер питания/геймпадов и не подтверждает F1/J004/SPI recovery, signed PSP replacement, VCN или готовность полной прошивки.

Следующий German primary — `docs/de/11-gaming.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German gaming: роль документа разобрана

Отдельная German primary `docs/de/11-gaming.md` учтена целиком: 28 562 байта, 212 строк, SHA-256 `55fc1e65678726531f0278594c14333a7bd636db6d12ece8f812d76dfbba2c7e`. Диапазоны 1–75, 76–150 и 151–212 прочитаны без renderer loss и совпадений privacy prefilter; глобального clearance нет. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Девять относительных ссылок существуют, их тела и внешние видео/таблицы/Reddit/Telegram/производительские источники не перевалидированы. Receipt, provenance,9 групп замечаний, EN/DE структура и табличный census: `phase136-german-gaming-*.json`. German 212 строк/13 заголовков, English 210/13, позиции +2; похожая структура не доказывает точность перевода или FPS.

- **GPU Limited Percentage 36,5 %** в одном игровом тесте не равно 36,5 % загрузки видеокарты и не доказывает универсальный CPU bottleneck. CPU simulation/render, GPU time, средний FPS, OC, разрешение и FSR — разные метрики. 1500→2000 MHz даёт +33,33 % **частоты**, не обещание +30 % FPS. «Сначала разгоняй» и обязательная работа с рёбрами расходятся с уже сохранённым обратимым no-cut путём. Ни игр, ни ОС, ни разгона не запускали.
- В основной таблице **41** строка результатов: **одна RX 6600 + Xeon не является BC-250**, десять явно помечены как числа из автосубтитров, четыре включают FG-маркер (категории могут пересекаться). Строки смешивают Linux/Windows, часы, CU, RT, FSR/FG, пресеты и «играбельно» без числа FPS. Строка «Windows + RADV» требует отдельного platform provenance — RADV-метка сама по себе не описывает нативный Windows-драйвер. Это не head-to-head и не target benchmark.
- FSR/LSFG generated frames не равны native FPS и добавляют задержку; планы FSR4 для RDNA2 и заявленные проценты — версионные/будущие утверждения. Один Doom после 40CU и workaround не подтверждает «40CU обязательны для игр». Anti-cheat, FF7 mesh и Doom VRS категорические блоки зависят от версии игры/driver/layer; NullVRS может пройти gate запуска, но «никаких побочных эффектов» не проверено. Hardware RT и Mesa software RT следует различать (сама таблица помечает Portal RTX как software path).
- `RADV_DEBUG=nohiz` может менять HiZ-ветку драйвера, но **не выбирает RADV** как Vulkan ICD. Proton/GameMode, `mitigations=off`, zswap и BIOS VRAM split — per-host/per-game решения; последнее отключает CPU-защиты. Эмуляторные Switch/PS3/PS4/Xenia данные — чужие истории, не тест controller/Waveshare; «подними CPU OC, чтобы компенсировать RPCS3 clock» не безопасный универсальный фикс. Права на видео/Google Sheet и реальные версии игр не проверены.

Игровая глава не доказывает Waveshare power/gamepad, F1/J004 recovery, signed PSP substitution, VCN или готовность полной прошивки. Следующий German primary — `docs/de/12-ai-llm.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German AI: роль документа разобрана

Отдельная German primary `docs/de/12-ai-llm.md` учтена целиком: 23 905 байт, 216 строк, SHA-256 `cbe2825bb899504bd21bb88e3875c12a85facb81b137660770ba48c2bd18ae38`. Диапазоны 1–80, 81–160 и 161–216 прочитаны без renderer loss и совпадений privacy prefilter; глобального clearance нет. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Девять относительных ссылок существуют; linked bodies и внешние GitHub/HuggingFace/Discord/видео-источники не перевалидированы. Receipt, provenance,7 групп замечаний, EN/DE структура и арифметика: `phase137-german-ai-*.json`. German216 строк/11 заголовков против English215/11; первые два заголовка +2, остальные +1. Первичная структурная JSON-запись ошибочно поместила число строк в `en.bytes`; до изменения живых документов оно исправлено на действительное число байт, а поправка записана в `phase137-root-prep-correction.json`.

- Эта AI-глава называет `gfx1013` RDNA-1.x, тогда как игровая глава называет то же устройство RDNA2. Без целевого ISA/firmware/driver анализа это не единый строгий словарь. Отсутствие **официальной** ROCm/rocBLAS поддержки и `gfx1013` kernels — одно ограничение; сам текст далее сообщает об экспериментальном **modified-MEC/HIP/PyTorch** пути. После этого категорическое «ROCm/HIP — невозможный тупик» в заключении уже не верно как абсолют. Но чужой отчёт тоже не доказывает безопасную прошивку MEC, подпись PSP или работу на нашей плате. Ничего в firmware не меняли.
- 16 GB GDDR6 — **общая память CPU/GPU**, не отдельные 16 GB VRAM. BIOS carve-out12GB может оставить мало ОС и KV-cache; MoE активирует мало параметров за токен, но все квантованные веса, router, KV-cache и runtime всё равно требуют место. Фраза о «минимальной сетевой стоимости» распределения экспертов не подтверждена на BC-250-кластере. OOM/падение рабочего стола — риск, не просто медленная генерация.
- Рецепт с `curl | sh`, systemd override/restart и загрузкой модели — действия на хосте и в сети. При 4-KiB страницах `ttm.pages_limit=4194304` соответствует **16 GiB**, всему номинальному общему пулу, а не гарантированному безопасно выделяемому объёму. `OOMScoreAdjust=-1000` защищает модель ценой возможного убийства других процессов; context65536 и GPU overhead0 добавляют давление на память. Ни один параметр не применяли, модели не запускали. `-ngl 99` — запрошенное число слоёв, не доказательство, что все слои оказались на нужном устройстве.
- Числа из одного видео пересчитаны: **25,7→31,9 tok/s = +24,125 %**, не заявленные 16–17 %; **25,7→33,4 = +29,961 %**, не «около20 %». MoE-пары 66,1→87,5 и59,5→78,7 действительно дают около32 %, но runtime/quant/context/CU и Ollama против llama.cpp отличаются; это не единый target benchmark. Участник видео остановился на36 CU после crash при дополнительных ядрах — 40CU не универсальный стабильный режим. Тяжёлую GPU/LLM нагрузку не запускали.

Глава не подтверждает Waveshare power/gamepad, F1/J004/SPI recovery, signed PSP substitution, VCN или полную прошивку. Следующий German primary — `docs/de/13-macos.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German macOS: роль документа разобрана

Отдельная German primary `docs/de/13-macos.md` учтена целиком: 7 226 байт, 55 строк, SHA-256 `8464368818742ea35280443586bba9b0445d75fe39d674211cebdc96e218f4cd`. Один диапазон 1–55 прочитан без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Семь относительных ссылок существуют, но linked bodies и внешние OpenCore/NootedRed/Dortania/форум/Telegram источники не перевалидированы. Receipt, provenance,5 групп замечаний и EN/DE структура: `phase138-german-macos-*.json`. German55 строк/5 заголовков, English53/5, позиции +2; разные bytes/hash, не техническая эквивалентность.

- «К началу 2026 никто не сообщил об ускоренном macOS на BC-250» — **отсутствие отчёта**, не доказательство универсальной невозможности. «Вероятно загрузится CPU-only» тоже не подкреплено наблюдённой загрузкой целевой платы. Пакет Monterey recovery + OpenCore означает только подготовленный архив, не boot, Metal или рабочий GPU. Общий AMD-Ryzen VM/Hackintosh thread не является BC-250 GPU passthrough-тестом.
- Объяснение «macOS только сверяет device ID, OpenCore единственное место вмешательства» упрощает драйверный стек. «Ни одна AMD-APU iGPU никогда не работала» расходится с упомянутым самой главой **NootedRed** для других APU: это сужает абсолют, но **не** даёт поддержку `gfx1013`/BC-250. Заключение о том, что разработчики OpenCore не возьмутся за плату из-за коммерческого мотива, — предположение об их намерениях, не hardware evidence. Текущие compatibility-листы не открывались.
- Шуточные сообщения/реакции не отчёты о работе. Образы, bootloader и kext не скачивали, не ставили; права на сторонние архивы не проверены. Глава не подтверждает Waveshare power/gamepad, F1/J004/clip recovery, signed PSP replacement, VCN или готовую полную прошивку.

Следующий German primary — `docs/de/14-display.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German display: роль документа разобрана

Отдельная German primary `docs/de/14-display.md` учтена целиком: 22 079 байт, 165 строк, SHA-256 `e7ebbd5f56e168e0a9ccafdb4dd22f97c4f5f18964f54e78b5152a84d8cec1d9`. Диапазоны 1–85 и 86–165 прочитаны без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Десять относительных ссылок существуют; их тела и внешние GitHub/Telegram/Reddit/адаптерные источники не проверены здесь. Receipt, provenance,6 групп замечаний и EN/DE структура: `phase139-german-display-*.json`. German165 строк/11 заголовков, English163/11, позиции +2; разные body/hash, не доказательство эквивалентности рекомендаций.

- «Нет изображения» разделено на питание/POST, кабель/DP/HDMI, firmware, driver, Wayland/session и адаптер. Чёрный HDMI или экран после GRUB **не равен** испорченному ROM. Предложение после нескольких чужих плат сразу «сбрось BIOS/перепрошей» не прошло наши target dump, recovery и exact-image ворота. Никакой flash/CMOS/power-cycle/перестановки железа не выполняли.
- Утверждение «DP→HDMI всегда даёт видео без задержки» противоречит собственным примерам чёрного экрана после загрузки ОС, разных разрешений и неудачных MST/HDMI hub. DP1.4,4K120,HDR10/VRR и предел кабеля требуют EDID/link/адаптер/driver результата на цели. Сторонний Bazzite HDMI2.1 remix испытан на другой Radeon, не BC-250. Адаптер и монитор не проверялись.
- По аудио глава приводит несовместимые абсолюты: прямой DP искажён, адаптер «надёжно исправляет», но пассивные/активные варианты могут быть немыми или менять pitch; заключение честнее — **модель адаптера и приёмник важны**. В списке источников пассивный адаптер даже назван необходимым для HDR, тогда как основной текст требует активный. Kernel6.17 codec-путь — custom build на чужой конфигурации, не готовый target fix. «5.1 HDMI никогда» — пересказ thread, без нашего ALSA/EDID/AVR теста. ОС/аудио не меняли.
- Незаселённый второй физический разъём, число GPU display heads, два независимых потока по **одному DP через MST**, USB DisplayLink и LAN-streaming — разные механизмы. Один MST-hub, сообщённый как работающий, не создаёт второй разъём; другие зеркалили или не работали. DisplayLink с CPU-compression и Sunshine/Steam через LAN не доказывают native GPU head, hardware VCN encode или управление Waveshare. Никаких streaming/DisplayLink опытов.

Глава не подтверждает F1/J004 recovery, signed PSP substitution, Waveshare power/gamepad, VCN unlock или готовую полную прошивку. Следующий German primary — `docs/de/15-emulation.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German emulation: роль документа разобрана

Отдельная German primary `docs/de/15-emulation.md` учтена целиком: 23 262 байта, 160 строк, SHA-256 `e44bf65b1fef5b8a5191d7d639eb0a62c867609da4b514c44906f4888707f983`. Диапазоны 1–80 и 81–160 прочитаны без renderer loss и совпадений privacy prefilter; глобального clearance нет. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Двенадцать относительных ссылок существуют; linked bodies и внешние Telegram/Reddit/emulator/ROM/keys источники не проверены. Receipt, provenance,6 групп замечаний, EN/DE структура и table census: `phase140-german-emulation-*.json`. German160 строк/13 заголовков, English158/13, позиции +2; разные bytes/hash не доказывают точность перевода.

- В таблице **33 платформенные строки**: **8** опираются на чат-отчёты о BC-250, **24** являются общей оценкой класса Zen2/GPU без теста платы, **1** — вопрос без подтверждения. **22 зелёные галочки стоят именно на общих оценках**, поэтому превращать их в «BC-250 проверена на этих системах» нельзя. Xbox 360/Xenia, PS3/RPCS3, PS4/shadPS4 и Switch/Eden — отдельные game/version anecdotes; один общий результат не равен совместимости всего каталога.
- **PSP в PPSSPP — портативная консоль Sony, не AMD Platform Security Processor.** Похвала PPSSPP на 4× разрешении не относится к подписанной PSP-записи BIOS или обходу подписи. То, что в меню Xenia реагировал геймпад, также не проверяет постоянно подключённый Waveshare-контроллер.
- Один Switch-случай с GPU на1000 MHz не превращает GPU2000/CPU4GHz, прошивку BIOS и резку рёбер в обязательные предпосылки **всей** эмуляции: собственный текст относит Retro/PPSSPP к лёгкой зоне и cooling-глава сохраняет no-cut path. Статус эмуляторов/форков и юридические права на ROM/ключи меняются; никаких бинарников, ROM, ключей, EmuDeck/Batocera/OS не загружали и не устанавливали.

Глава не подтверждает Waveshare power/gamepad, F1/J004 recovery, signed PSP substitution, VCN или полную прошивку. Следующий German primary — `docs/de/16-usb-peripherals.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German USB: роль документа разобрана

Отдельная German primary `docs/de/16-usb-peripherals.md` учтена целиком: 24 136 байт, 203 строки, SHA-256 `f18d15a5d82b9d3a3c5d3c5083eef5e6a64d9e342afbcc5426dccf3094a2f22b`. Диапазоны 1–80, 81–160 и 161–203 прочитаны без renderer loss и совпадений privacy prefilter; глобального clearance нет. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Десять относительных ссылок существуют, linked bodies и внешние Telegram/4PDA/видео/магазины не проверены. Receipt, provenance,9 групп замечаний и EN/DE структура: `phase141-german-usb-*.json`. German203 строки/17 заголовков, English201/17, позиции +2; разные bytes/hash, не электрическая эквивалентность.

- Четыре задних USB-порта и отсутствие распаянного front-header взяты из чужой аппаратной карты, не пересчитаны на целевой ревизии. «USB3 фактически x2» не задаёт понятной USB-единицы и **не** равно двум PCIe-линиям M.2. Просадка 5V до4,3/2,3–3,2V была на **одной проблемной плате**; сам текст приводит другую с работающим bus-powered hub. Универсальная слабость USB-рельса и риск «сжечь порт» этим не доказаны.
- Отдельно питаемый USB-хаб — **обратимый lead без пайки**, подходящий предпочтению оператора. Но rating его блока, защита от обратной подачи VBUS, current limiting и перечисление нашей периферии/геймпадов не проверены. Разрезать upstream VBUS и подать 5V от ATX — другая, необратимая электрическая топология. «Земля общая автоматически» не заменяет проверки return path, sequencing, обратного питания и предохранения; не резали, не паяли, не подавали питание.
- M.2 назван **PCIe2.0×2**, но рядом утверждается прямая работа **SATA-протокольного** M.2 без переходника. Это возможно лишь при подтверждённой разводке/переключении протокола, которого глава не показывает. ASM1166/PH516 — ограниченные сообщения о конкретных контроллерах, не target qualification. SATA-данные и отдельные 5V питания диска — разные цепи; buck-рецепт из видео не применяли. Слепая замена всех `nvme` на `sda` в SteamOS repair script может попасть **не в тот диск** и повредить данные; диски/разделы не трогали.
- Один DisplayLink-dock без видео не доказывает лимит native GPU outputs: USB DisplayLink — отдельный путь. Pico2W DS5Dongle для DualSense, GameSir со своим 2,4-GHz приёмником и USB2/BT-анекдоты **не** постоянно подключённый Waveshare-контроллер питания и геймпадов. Версию BT, Direct-mode audio, 5V-нагрузку и latency на нашей плате не проверяли.

Глава не подтверждает F1/J004/clip recovery, signed PSP substitution, VCN или полную прошивку. Следующий German primary — `docs/de/faq.md`; весь остальной original corpus, queued native next20, privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.

## German FAQ: роль документа разобрана

Отдельная German primary `docs/de/faq.md` учтена целиком: 19 455 байт, 187 строк, SHA-256 `274d0bb3b0404d669e7090e4c6eff21ddc6fa056f44070f2b816c9ac6afc2726`. Диапазоны 1–70, 71–140 и 141–187 прочитаны без renderer loss и совпадений privacy prefilter; это не глобальный clearance. Raw source сохранён, local pinned Git blob совпал после EOL-нормализации. Все **49** относительных файлов-ссылок существуют: **47 ведут в English, одна в German, одна вне локалей**. Значит немецкая FAQ не является самостоятельным полным немецким handbook; существование ссылок не повторно проверяет тела глав или внешние URL. Receipt, provenance,10 групп замечаний, EN/DE структура и routing: `phase142-german-faq-*.json`. German187 строк/12 заголовков, English185/12, позиции +2, разные bytes/hash. FAQ — указатель к главам, не новое измерение платы.

- Короткие ответы делают условные истории абсолютами: «нет кнопки, сразу 12V» смешивает AUTO_PWRON/PWR_SW/PS_ON; CMOS и бумажная прокладка при no-POST не диагностика; «VCN недоступен ⇒ всегда software encoder» не доказывает отсутствия кремния или фактический Sunshine codec. Не включали и не трогали плату.
- PSU≥300W/single rail, PCIe/EPS, «дымящий кабель ⇒ фальшивая медь», магнетический тест, thermal pads и 85/90°C пороги не переносятся на target safety без измерений. FAQ требует **прореживать рёбра** как дешёвое решение, тогда как полные cooling/case главы сохраняют **безрезовый** путь. Никакой проводки, резки или совместного stress.
- Bazzite/Fedora/COPR, обязательный `navi10` symlink, «любой графический Flatpak теряет GPU», Wayland→X11, `mitigations=off`, `nosmt=force`, zRAM32 и kernel rollback зависят от версии и меняют хост/защиту. Полная Linux/AI главы обсуждают другой путь zswap, поэтому краткий FAQ не задаёт универсальную swap-policy. Датированные Windows Code43/IOMMU/VM ответы не постоянный закон платы. ОС и драйверы не менялись.
- «J4004 только, SOIC clip не работает» противоречит **сообщённому оператором F1-прошиванию** и не закрывает exact image/full dump/double read/independent recovery/coldboot/readback. P5 mod, 40CU, CPU4GHz, 955mV, «слишком сильный undervolt безвреден» и CMOS-after-flash — чужие условия; последний абсолют расходится с сохранёнными blackscreen/no-boot случаями. Не прошивали и не разгоняли.
- DP→HDMI audio/video, радио/usbreset, CPU-bound/FPS, AI12GB BIOS, цены и «Mac GPU никогда» — сокращения соответствующих глав, не target-проверка. Никакой FAQ-ответ не подтверждает Waveshare gamepad/power, signed PSP substitution или VCN acceptance.

Следующий отдельный German primary — `docs/de/troubleshooting.md`; затем можно сверить немецкую Markdown-когорту по hash/line-role receipts, **не** объявляя весь import завершённым. Privacy/rights/SAST и независимый review открыты. Native120/176/559 не изменён.
