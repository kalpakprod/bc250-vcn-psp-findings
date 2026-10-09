# Parallel lanes inventory — 2026-09-25 (AUTO)

## Задача

Оператор: «идти всеми путями одновременно», начиная с PSP-блока. Собрать
факты, что уже сделано и что ещё имеет смысл делать, без импровизации.

## Сколько BIOS-кандидатов уже собрано (evidence)

- 63 root-images в `candidates/` (полные 16 MiB прошивки).
- 15 DXE-injection кандидатов d5..d19: все через один и тот же вектор
  `OUTER_FV=0xAE0000`, `CAPSULE_FFS=0xAE0078`, GUID CoreUnlock
  `6d423d2f-546a-6b4a-82d0-1207cc5b6d92`, замена одной PE32-секции same-size.
- 4 «vcn-первого-класса»: `VCN_D3B2_combined`, `APCB_DFG_only`,
  `VCN_policy_only`, `MemoryClock_1750_only`. Из них 3 flashed на BC250-01.
- 1 в разработке: `vcn-unlock-driver-v000-DRAFT` (`BC250VCNUnlockDxe.c`,
  `_rtb.c`, `_secure.c` — три варианта: сразу, ready-to-boot, secure-only).

## Что уже железно опровергнуто (не повторять)

1. **Модифицированные $PS1-carrier PSP-entries** (D3-B2 combined + policy-only +
   APCB-DFG-only). 3 write-verified flash, 3 no-display, SSH-at-t+90s
   FAIL (12 probes) — PSP RSA-2048 halt на stale 0x100 signature tail.
   Источник: `docs/action-logs/2026-09-11-vcn-policy-only-candidate.md:114`,
   `docs/action-logs/2026-09-12-vcn-mode1-probe-audit.md:389-390`.
2. **SMU firmware body edit** (D4: 1 байт в zero-padding SMU payload).
   Тот же halt → SMU $PS1 верифицируется on-die ROM. **SMU is NOT patchable
   in BIOS.** Источник: `docs/action-logs/2026-09-12-vcn-mode1-probe-audit.md:406`.
3. **KDB signature bypass** (замена modulus в KDB). `39bfc192` byte-identical
   через 5 BC250 BIOS + 4700S C0A — это shipped platform constant в on-die ROM,
   не image-local. `96ea7cfe` (SEC_GASKET/policy signer) — BC250-family
   (byte-identical в 5 стоках, отсутствует в 4700S), но это тоже not-forgeable.
   Источник: `docs/action-logs/2026-09-19-kdb-crossimage-anchor-test.md:63-78`.
4. **Runtime NBIF/DF firewall unclamp** (S1..S4 через Q3 0x98). Session 3-5
   на живом железе: 7 writes landed, VCN всё равно `0xFFFFFFFF`.
   Гипотеза owner/commit подтверждена: PSP-owned finalization обязателен.
   Источник: `docs/action-logs/2026-09-25-vcn-live-session.md`.
5. **DXE ReadyToBoot 0x2A/2C gasket writes (d11-d19)**: single write
   `0x0900C234 <- 0` или `0x0900C830 <- 0x00FFFFFB` **wedges SMU до Linux
   verification** (SMU alive=False, PSP DESTROY_TMR 0x80000306, amdgpu probe
   -62). D17/D19 разделяют: каждый по-отдельности достаточен для wedge.
   Источник: `docs/action-logs/2026-09-12-d17-gasket-control-only.md:40`,
   `docs/action-logs/2026-09-12-d19-gasket-c830-only.md:46`.
6. **Domain-14/15/17 power-up transaction** (5 experiments S2-L5b..L10).
   Denial complete: fw path, direct host path, config path, mode1, mode2, все
   всегда wedges на dom14 request doorbell. Isolation живёт ПОД SMU firmware
   на power-controller/fabric level.
   Источник: `docs/action-logs/2026-09-12-vcn-mode1-probe-audit.md:287-288`.
7. **NBIF routing candidates** `0x13b1005c/60/0x13b00084/4c` (chain report S4).
   Read-only capture: `0x8000/0xffff/0x108/0x800000` — не carry `0x3`
   port-config pattern. Chain report сам говорил «точные регистры NBIF ещё
   нужно доказать» — доказано что это НЕ те.
   Источник: `docs/action-logs/2026-09-12-s2a-runtime-donor-aperture.md:170-175`.
8. **APCB in-place `0x10c2/0x10c3` flip** (NBIF_VCN_PORT_CONFIG /
   NBIF_VCN_BRIDGE_ENABLE). Токены ОТСУТСТВУЮТ в flash APCB Robin —
   PEIM инжектит `0x3` в RAM. Нечего flip'ать.
   Источник: `docs/action-logs/2026-09-12-s2a-runtime-donor-aperture.md:197-199`.

## Что открыто и имеет смысл (offline, no board risk)

### Lane A — P1.5a: SEC_GASKET executor RE (никогда не построен)

- Скрипт `trace_sec_gasket_executor.py` **planned since 2026-08-26, never built**
  (`docs/repository-inventory.md:136`).
- Есть все нужные ABL/PSP bodies:
  - `evidence/psp-bodies-import/ABL1~0x31_21.11.26.0.body` (48336 B, ARM Thumb-2)
  - `evidence/psp-bodies-import/SEC_GASKET~0x24_B.51.0.16.body` (11344 B, policy blob)
  - `evidence/psp-bodies-import/PSP_FW_TRUSTED_OS~0x2_0.1C.0.2.body` (82256 B, TOS)
  - `evidence/psp-bodies-import/DRIVER_ENTRIES~0x28_0.1C.0.2.body` (107888 B)
- Уже декодировано в `docs/research/imported/bc250-bios-docs/01-psp-policy-chain.md`:
  loader fn@0x13468, register fn@0x1167c, интерпретаторы fn@0x2178 и fn@0xfeac,
  секвенсер fn@0x20d4 (типы 0x201/0x205/0x203/0x20A/0x20B/0x210).
- **Что не декодировано:** group 0x280/0x281 применяется ТОЛЬКО через fn@0xfeac,
  но вызывающий fn@0xfeac ВНУТРИ контейнера ОТСУТСТВУЕТ — значит либо снаружи,
  либо не выполняется вовсе. Это open question, влияющая на всё.

### Lane B — P1.5b: NBIF token engine (частично)

- 5 stages декодировано в `docs/research/2026-09-12-nbif-clamp-mechanism.md`:
  defaults → serializer → APCB RAM merge → token engine → NBIF SMN RMWs.
- **Не декодировано:** где token engine (consumer loop), какие ИСТИННЫЕ NBIF
  registers writes'ит для token 0x10c2/0x10c3. Кандидатные регистры
  `0x6A140..0x6A1B4` captured (live values), но какой из них — VCN port —
  неизвестно.

### Lane C — Zen2/Renoir/Cezanne PSP CE (glitch/CVE)

- Не исследовано. AMD PSP имел ряд опубликованных CVE:
  - MasterKey (CVE-2018-8930), Chimera, EPYC key extraction (2020),
    voltage/EM glitch fault injection.
- Требует внешних инструментов (glitch board, PMBus), не software-only.
- НЕ рекомендую как первый шаг: user не разрешил hardware modding сверх
  programmer flash.

### Lane D — DXE injection с исправлением root cause d11-d19 wedge

- Все 9 gasket-DXE кандидатов (d11-d19) wedge SMU на первом же
  0x0900C234/C830/C834 write из ReadyToBoot.
- **Гипотеза (не проверенная):** ReadyToBoot запускается ПОСЛЕ того как PSP
  SEC_GASKET уже применил свою политику и hardware-lock'нул fabric matrices.
  Значит поздние DXE writes виснут на том же fabric wedge, что и runtime.
- **Смена стратегии:** нужен DXE, работающий В PEI phase (до PSP finalize),
  или SEC phase (до DXE dispatch). НО в UEFI PEI-модуль тоже подписан?
  Не изучено — надо проверить какие модули НЕ подписаны и куда можно вставить.
- Альтернатива: DXE, который заменяет собой **типовой AMD PEI/DXE-модуль
  подписи-not-required класса** — например, custom NVRAM handler, ACPI
  init hook.

## Ranked next actions

1. **Lane A** (offline, primary, blocked с 2026-08-26): собрать
   `trace_sec_gasket_executor.py` на `SEC_GASKET~0x24_B.51.0.16.body` +
   `ABL1~0x31_21.11.26.0.body`. Найти где именно fn@0xfeac (интерпретатор
   group 0x280) вызывается — снаружи container'а. Это ключ к тому кто
   commit'ит fabric matrices и когда lock'ит.
2. **Lane B** (offline): декодировать consumer loop token engine (сравнение
   AGESA source ↔ import evidence в `recon/disasm_AmdNbioGfxARIPei.txt`).
3. **Lane D** (offline pre-build): аудит UEFI firmware volumes на предмет
   PEI/SEC модулей, не покрытых PSP $PS1 подписью. Оценить возможность
   инжекта в PEI phase.

## Blockers → нужно от оператора

- Ничего до Lane A/B/D завершения. Live-сессия SMU wedged (session 5).
- Cold power-cycle НЕ требуется прямо сейчас: следующий полезный шаг
  offline, не трогает плату.

## Session 5 → Lane A initial run (2026-09-25 evening)

Собран `scripts/trace_sec_gasket_executor.py`. Прогон на
`SEC_GASKET~0x24_B.51.0.16.body` (11344 B, sha256 `d16f7dac...`) и
`ABL1~0x31_21.11.26.0.body` (48336 B, sha256 `e33acd49...`).

### Результат (объективный)

- **Policy blob parse: PASS.** Все 5 групп совпали с 02-gasket-groups.md
  counts (0x201:1230, 0x203:31, 0x210:13, 0x280:100, 0x281:31), pairs_parsed
  == count для всех. Table start = 0x40 (не 0x100 как думалось раньше).
- **Body в ABL1 body ≠ ARM Thumb from doc:** первые 32 байта — ARM (`10 40
2d e9 04 20 9f e5`), не Thumb. Это ARM32 code, а Thumb prologues
  разбросаны редко (46 занятых `2d e9`, 16 `10 b5`).
- **Все callers = 0 для fn@0x13468/0x1167c/0x2178/0xfeac и т.д.** Значит:
  адреса fn@ из `01-psp-policy-chain.md` относятся к **другому** body — почти
  наверняка к `PSP_FW_TRUSTED_OS~0x2` (82256 B, где живёт t02/t28-код,
  фактически описанный в decode). ABL1 — это отдельный container с ARM
  entrypoint по offset 0.
- SVC counts в ABL1: топ = svc 40/39/38 (по 6-7), svc 6/10/28 (по 3),
  svc 0x7c ОТСУТСТВУЕТ. Значит **fn@0xfeac и svc 0x7c живут НЕ в ABL1**,
  а в TOS (`type 0x28`) или PSP FW TRUSTED OS (`type 0x2`).

### Что нужно исправить в Lane A

1. Переключиться на правильные body для интерпретаторов:
   - fn@0x13468 (loader $PS1) и fn@0xfeac (interp 0x280) — в TOS/PSP2.
   - `PSP_FW_TRUSTED_OS~0x2_0.1C.0.2.body` (82256 B) — это тот блоб t02
     из `01-psp-policy-chain.md`, где живёт весь policy-executor.
2. Учитывать что body может иметь загрузочный header (base ≠ 0).
   `01-psp-policy-chain.md:10` говорит: код t02 начинается со смещения
   0x100 от body. Значит base = 0x100 (или E00000-relative VA).
3. VA-модель: в `2026-09-23-clv-t28-vcn-gate-disasm.md:222+` VA = body_off +
   0x985000 (load base 0xE00000 = t28 body @ FILE 0x985000). Для t02
   надо аналогично найти load base.

### Обновлённый ranked

- **Lane A шаг 2:** переключить `trace_sec_gasket_executor.py` на `PSP2` body,
  base=0x100, декодировать fn@0xfeac callers и svc 0x7c argument origins.
- Оставшиеся lanes B, C, D — без изменений в приоритете.

Executor JSON output: `evidence/firmware-audit/20260925-sec-gasket-executor/
executor-map.json` (пока с zero-caller данными — это негативный результат,
не баг).

## Session 5 → Lane A шаг 2 (PSP2 TOS body): ПРОРЫВ

Прогон переключен на `PSP_FW_TRUSTED_OS~0x2_0.1C.0.2.body` (82256 B,
sha256 `19f091de...`), code base +0x100 из `01-psp-policy-chain.md`.

### Ключевой факт (новый, никогда не был найден):

- **fn@0xfeac (интерпретатор group 0x280/0x281) вызывается ИЗНУТРИ TOS
  из ОДНОЙ точки: 0x11aae** (относительно code base +0x100).
- Doc сказал «вызывающий fn@0xfeac ВНУТРИ контейнера ОТСУТСТВУЕТ» — это
  было НЕ ТАК, доc'ные grep'ы шли не в тот body. Есть ровно один caller.
- **SVC 0x7c: 11 occurrences** в PSP2 code (это SMN write primitive). Значит
  весь fabric-firewall apply идёт через эти 11 SVC 0x7c call-sites, и
  минимум один из них — из fn@0xfeac.

### Что это даёт для VCN unlock

- **0x11aae — единственная точка, через которую применяются group 0x280 (100
  pairs) + 0x281 (31 pairs).** Именно эти группы содержат dom14/VCN gasket
  policy (VCN bank 12 addresses 0x0900Cxxx). Если эта точка вызывается
  условно (по гейту), появится вариант обойти условие через runtime SRAM
  patch того гейта.
- **LockDFReg 0x1b — надо найти где applier делает финальный «lock»
  transaction после apply.** Это следующий шаг: декодировать 0x11aae, найти
  как оно вызывает fn@0xfeac, а после — какой финальный SVC/store делает
  hardware-lock fabric matrices.
- Прежний вердикт «hardware-lock после apply» ОСТАЁТСЯ, но теперь есть
  адрес call-site (0x11aae) и точка, куда включать патч (SRAM byte-flag
  или сам body-patch с обходом check).

### Обновлённые lanes

- **Lane A шаг 3:** декодировать 0x11aae в PSP2 body — arm/prologue,
  локальный контекст, гейты. Извлечь arg passing к fn@0xfeac.
- **Lane A шаг 4:** трассировать 11 SVC 0x7c call-sites — какой из них
  выставляет LockDFReg 0x1b (иначе — какое store делает hardware-lock).
- **Lane B/D/C:** без изменений.

## Итог сессии AUTO

Progress:

- Инвентарь всех предыдущих BIOS-попыток (63 root images, 15 DXE, все PSP)
  зафиксирован с явными причинами провала — 8 закрытых лейнов.
- Собран и запущен **никогда не построенный** `trace_sec_gasket_executor.py`
  (P1.5a, planned since 2026-08-26).
- **Найдена ранее unknown call-site fn@0xfeac @0x11aae в PSP2 TOS body** —
  это первая известная точка apply group 0x280/0x281 (VCN gasket policy).
  Опровергает предыдущий вывод «no caller inside container».
- SVC 0x7c call-site count: 11. Локация LockDFReg apply — следующий шаг.

Артефакты (все reversible, static-only):

- `scripts/trace_sec_gasket_executor.py` (229 lines)
- `evidence/psp-bodies-import/` (5 PSP bodies из import)
- `evidence/firmware-audit/20260925-sec-gasket-executor/executor-map.json`
- Этот файл.

Blocker: **нет.** Плата не нужна для следующих 3 шагов (декодирование 0x11aae,
SVC 0x7c trace, LockDFReg apply site). Live-сессия начнётся когда будет
готов конкретный runtime-patch (SRAM byte или fw-code hook).
