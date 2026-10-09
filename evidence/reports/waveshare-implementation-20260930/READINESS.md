# Полный план: завершение НЕ доказано

Аудит сохраняет весь объём; готовый пакет не заменяет аппаратную приёмку.

| Требование | Статус | Доказательство / недостающее |
|---|---|---|
| Сохранить установленную Waveshare и возможность возврата | PARTIAL | installed-recovery-status.json: два чтения совпали, запись восстановления не испытана |
| Одна сборка, прежние исходники и настройки не перезаписаны | OFFLINE_PROVEN | VERIFICATION.txt original_pico_source_unchanged, manifests/source hashes |
| DualSense: ввод, звук, микрофон, haptics, triggers, reconnect | CODE_BUILT_HARDWARE_PENDING | candidate-tests и literal-callback/native tests: не доказывают игровой результат |
| Одновременная работа контроллера, сети, мониторинга | CODE_BUILT_HARDWARE_PENDING | goal-last-build, polling loop: нагрузка/радиосовместимость требуют платы |
| Wi-Fi, авторизованный HTTP, MQTT, сбои/свежесть | OFFLINE_PROVEN_RUNTIME_PENDING | goal native/host tests, MQTT age regression, CRC/token/private config, no live credentials; exact native HTTP source mocked, socketpair MQTT wire transport tests and browser Russian panel fixtures now pass; no live deployment |
| Достоверные метрики, единицы, источник, stale/null | OFFLINE_PROVEN_AMD_PENDING | host metrics tests, firmware metrics harness, DMI gate; реальная AMD не опрошена; actual SuperIO nct6686 name regression reproduced and fixed, module name is not control capability |
| PS включает через разрешённый канал, без повтора/старых событий | OFFLINE_PROVEN_RUNTIME_PENDING | PS gate/MQTT/HA fake API tests; реальные HA/relay не вызывались |
| Штатное выключение Linux без аварийного отключения | OFFLINE_PROVEN_RUNTIME_PENDING | test_waveshare_shutdown.py fake executor; wrong DMI/dry run do not act; no real shutdown |
| Общая телеметрия Decky и панели | BUILD_PROVEN_INSTALL_PENDING | Decky typecheck/build, backend freshness/source tests; не установлен на AMD |
| UART RX, журнал, без записи в AMD | CODE_PROVEN_ELECTRICAL_PENDING | uart_test и capture protocol tests; GP9 physical12/GND13 vendor evidence, J5 CAD; J5.4 выход подтверждён CAD+Nuvoton, проектный уровень3.3V; приёмка экземпляра не выполнена, мультиметр не требуется |
| Снимки/диагностика BIOS, сохранность подписанных регионов | PARTIAL_EXTERNAL_READ_UNPROVEN | offline file audit/source intact; живое чтение SPI и signed-region acceptance не выполнены |
| Все полезные доступные разъёмы и электрическая безопасность | EVIDENCE_PARTIAL | CAD registry18 + vendor pins; кабели, уровни, колодки экземпляра не приняты |
| Подробная офлайн HTML инструкция, две платы, кабели, проверки | DRAFT_RENDER_PROVEN_FINAL_PENDING | CONNECT.html desktop/mobile native hover/touch QA, vendor image and conditional RX diagram; не финальное разрешение на проводку |
| Патч, проверка, самодостаточный откат с наблюдёнными тремя состояниями | OFFLINE_PROVEN | same four roles plus firmware pristine delta/archive, actual restored callback test |
| Только финальный точный образ, затем аппаратная проверка | NOT_AUTHORIZED | user declined intermediate upload; physical device remains BOOTSEL |
| Холодные старты, ввод/звук, игровая сессия, сутки наблюдения | NOT_RUN | No post-upload/AMD hardware observations |
| Анализ PSP без автономного обхода защиты | STATIC_ONLY_APPROVED_EXCLUSION | PSP/BHD summary; PSP bypass excluded from approved plan, never implemented |

Current source/build ID: 0e663124e005; candidate SHA256: ddde4aa06c6d8ea2ccb6f2fb346a8c2d35dd44f3a9bfc4cc8ea753408f2d2655. Fan1/fan2 host→CDC→firmware→panel code verified with native/PTY/VM checks, not live device. MODE diagnostic isolation and passive external BIOS acquisition remain source closure gaps, not satisfied by file audit.
