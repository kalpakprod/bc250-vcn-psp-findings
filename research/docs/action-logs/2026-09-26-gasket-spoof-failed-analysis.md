# 2026-09-26 — Gasket-spoof v001 FAILED — full attack-surface audit

## Result

Прошивка `BC250_P3.00_gasket-spoof-vcn_v001.bin` (SHA `6a7feaae…`)
не даёт инициализации на cold boot (нет ни одного LED). Стоковый
образ P3.00 (`83c4e420…`) восстановлен bit-perfect, verify через
readback — pass.

## Root-cause анализ (честный)

Два независимых кандидата провалились одинаково — не даёт первый
LED:

1. `BC250_P3.00_NO_GASKET_v001.bin` (1 байт: удаление entry 0x24 из
   $PSP directory) — reject на уровне PSP boot-ROM после того, как
   ROM обходит directory и не находит ожидаемый type.
2. `BC250_P3.00_gasket-spoof-vcn_v001.bin` (подмена tail SEC_GASKET
   после signed header 0x100 байт) — reject тоже до первого LED.

**Вывод (гипотеза):** SEC_GASKET подпись покрывает **больше чем
первые 0x100 байт**. Возможно signed region = весь body, а поле
signature находится в trailer или отдельно в directory. Моё
допущение «первые 0x100 = signed header, rest = free-form policy»
было неверным.

## Что это меняет

- Runtime-атака (через SMU 0x23 exploit из bc250-smu-unlock) —
  единственный подтверждённый вектор на этой карте. Не требует
  прошивки, работает поверх стока, обратимая.
- Все прошивочные варианты, которые ТРОГАЮТ подписанные регионы
  (IPL, ABL1, SEC_GASKET body, TOS, PSP directory) без валидной
  RSA-подписи AMD — reject на PSP.
- Прошивочные варианты, которые НЕ трогают signed regions —
  ограничены изменениями в:
  - Non-PSP регион SPI (BIOS_DIR entries: PEI, DXE, RAW blobs без
    signature).
  - APCB tokens (fletcher-checksummed, но не RSA-signed).
  - NVRAM / NVAR variables.
  - MeiMei DXE payload (custom — не подписан AMD).

## Attack surface — переоценка

### A. Runtime (не требует прошивки) — ПРИОРИТЕТ

- **A1**: `bc250-smu-unlock` Q2 msg 0x23 — уже работает, получает
  RPC на Xtensa SMU. Проверено на живом железе в session 3/7.
- **A2**: userspace VCN staging (`enable_vcn.py --direct-load`) —
  загружает VCN firmware из VRAM, программирует регистры как ядро.
  Требует, чтобы VCN power domain был поднят (это то, что A1 делает).
- **A3**: обход dom6-clamp через PLL power set + clock ungate
  (SMU RPC `FN_PLL_POWER_SET(6, 1)` + `FN_CLK_DOMAIN_UNGATE(...)`).

### B. Прошивочная (unsigned regions) — не тронуто

- **B1**: MeiMei DXE payload (не подписан AMD, живёт в BIOS_DIR).
  Можно внедрить DXE driver, который на ReadyToBoot делает то же
  что A1+A2 — но в UEFI фазе, до загрузки ОС. Уже есть попытки:
  `candidates/d10-early-dxe-smu-unlock`, `d17-gasket-control-only`.
- **B2**: APCB tokens — можно изменить memory training / clock
  scaling параметры (fletcher-checksum, не RSA). Не открывает VCN.
- **B3**: DXE «gasket» driver, регистрирующий свой protocol на
  gEfiEndOfDxeEventGuid и выполняющий SMU RPC перед BdsDxe. Тот же
  подход что B1, но в другую фазу.

### C. Signed regions (BLOCKED) — не пытаться без RSA-эксплойта

- IPL (type 0x01) — RSA-signed, полностью зашифрован. Без CBC-key
  или reference plaintext атака невозможна.
- ABL1 (type 0x30/0x31) — RSA-signed.
- SEC_GASKET (type 0x24) — **весь body подписан** (гипотеза
  подтверждается двумя reject'ами).
- TOS (type 0x02) — RSA-signed.
- PSP directory — не RSA-signed, но fletcher32 покрывает всё, а
  reject на удалении entry 0x24 показывает, что PSP валидирует
  ожидаемый layout независимо.

## Рекомендация оператору

**НЕ прошивать больше прошивки, которые трогают signed regions.**

Вместо этого:

1. Cold boot на стоке (уже прошит) — плата поднимется.
2. Через SSH выполнить `enable_vcn.py --direct-load` (A1+A2).
3. Если runtime-путь не работает — писать B1 (unsigned DXE driver
   в MeiMei payload), не C (взлом RSA).

## Kill list (закрытые треки)

- ❌ SEC_GASKET entry removal (0x24) — PSP reject
- ❌ SEC_GASKET body substitution (spoofed $PS1) — PSP reject
- ❌ 5.00 CLV base flash (never boot-tested) — PSP reject
- ❌ PEI immediate flip 0x03→0x07 — boot hang (NBIF link training
  на выключенный VCN)
- ✓ Stock P3.00 — работает, VCN gated, но SMU alive → runtime unlock
  доступен

## Артефакты этой сессии

- `evidence/programmer/reads/20260926-gasket-spoof/pre-flash-20260926-065349.bin` — что было на чипе до gasket-spoof (= NO_GASKET_v001)
- `evidence/programmer/reads/20260926-gasket-spoof/post-flash-20260926-065349.bin` — gasket-spoof v001 после прошивки (bit-perfect)
- `evidence/programmer/reads/20260926-gasket-spoof/post-restore-*.bin` — сток восстановлен (SHA `83c4e420…`)
- `candidates/psp-ipl-cbc-bitflip-v001/BC250_P3.00_gasket-spoof-vcn_v001.bin` — сохранён для post-mortem, НЕ прошивать
- `exploits/psp-cbc-bitflip-v001/build_exploit.py` — билдер, оставлен для reference
