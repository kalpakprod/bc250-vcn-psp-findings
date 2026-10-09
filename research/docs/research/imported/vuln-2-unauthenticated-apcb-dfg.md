# VULN-BC250-002 — unauthenticated data-fabric gate via APCB (no key)

## Находка (ground-truth с ROM `AMD_4700S_C0A.rom`)
- `$BHD`(BIOS-dir) содержит **APCB @0xab1000** и **APCB_COPY @0xab3000**. `$PS1`-подписей во всей
  области APCB = **0**. Целостность APCB = **32-бит аддитивный checksum** (`0x24ed` в заголовке,
  поле +0x0c), НЕ крипто-подпись → **пересчитываемый**.
- Внутри APCB лежат таблицы, из которых PSP строит гейт: `PSPG`@0xab109c, **`DFG`@0xab10f4**, `MEMG`@0xab117f.
  Структура = группы `03 17 <n> <sz>` + строки `<grp> <sub> <perm> <00>`.
  Разрешения: базовый `03`; расширенные `0x63`,`0x23`,`0x67` (bit extra = open grant).
- Подписанный SEC_GASKET (0x24) = **потребитель** этого конфига; сам **вход гейта = неаутентифицирован**.

## Суть уязвимости
Решение PSP «разрешить x86 доступ к VCN-апертуре» принимается из таблицы, защищённой лишь аддитивным
checksum (не подписью). = checksum-as-authentication на security-входе. = класс «unverified input»
(аналог published CVE-2023-20521 TOCTOU-after-verify, но сильнее: тут вообще нет верификации, только сумма).

## Эксплойт (developable, БЕЗ robin3-ключа, без глитча)
1. В APCB-таблице DFG добавить/поправить строку grant x86-мастер → VCN-блок (perm по образцу уже-открытых
   блоков, формат `01 <vcn_sub> <perm> 00`); в заголовке группы поднять `<n>`.
2. Пересчитать аддитивный checksum APCB.
3. Записать APCB-регион (AFU пишет unsigned-регионы; подписанные не трогаем → ключ не нужен).
4. Cold boot → PSP строит гейт из изменённого-but-valid-APCB → VCN-апертура открыта → V2..V6.
5. Rollback = вернуть APCB-регион + reboot (без ключа).

## Чем отличается от WorkBuddy C1
WorkBuddy: правим **подписанный** SEC_GASKET → нужен ключ/TOCTOU («эксплойт меняет исполнителя, не результат»).
Мой lever: правим **несигнатурный, checksum-only вход гейта (APCB DFG)** → результат меняется, ключ не нужен.

## Открыто / надо домержать (не board-зависимо, это parse)
- точный sub-index DFG = VCN (bank 12 runtime → APCB sub) — сопоставить с DFG-группой;
- точный алгоритм APCB checksum (мой byte-sum ≠ 0x24ed → алго иной, подбирать span/полином);
- принимает ли парсер PSP добавление строки (или правку существующей с «secure»-perm на open-perm).
Runtime-развилка (gate-write) закрыта RE как тупик — путь = boot-config (APCB), не runtime.
