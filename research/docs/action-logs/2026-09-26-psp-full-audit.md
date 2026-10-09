# 2026-09-26 — Полный PSP / BIOS audit (после двух reject'ов)

## Что реально узнали про PSP

**19 записей в $PSP directory** (P3.00 stock, `83c4e420…`). Все имеют
0x100-байтовый header + payload + 0x100-байтовый tail. Tail высокоэнтропийный
(entropy ~250/256 значащих байт), не совпадает ни с одним SHA-256 от подписанных
регионов → это **RSA-signature block**, а не hash-fingerprint.

Layout header (проверено на 17 из 19 записей):

- `0x14`: `size_signed` (u32) — сколько байт payload'а покрыто подписью.
- `0x18`: `enc_opt` — bit0 = encrypted.
- `0x48`: `sig_opt` — bit0 = signed (но это FLAG в header'е, не реальный
  gate PSP; PSP всегда валидирует по типу записи).
- `0x60`: `security_patch_level` — SPL/build tag.
- `0x84`: `size_image` (total).
- `0x88`: `unsigned_size` (0 для всех).

**Все 17 нормальных записей** имеют `body_size - (0x100 + signed_len) == 0x100`
= tail exactly = RSA-2048 signature. `Свободной` unsigned области НЕТ.

Исключения:

| Тип      | signed_len                       | Body   | Tail                        | Комментарий                 |
| -------- | -------------------------------- | ------ | --------------------------- | --------------------------- |
| 0x01 IPL | 0x30f3d743 (garbage — encrypted) | 0xa800 | encrypted header            | AES-CBC, key в fuses        |
| 0x09     | 0xd4acc8ff (garbage — enc)       | 0x440  | enc                         | encrypted PSP L2 pointer    |
| 0x44 KDB | 0x10 (только 16 байт signed)     | 0x6610 | 0x6500 self-verified merkle | TLV policy, self-hash chain |

## Что заблокировано

1. **RSA-подписанные payload'ы**: 0x02, 0x08, 0x12, 0x13, 0x20, 0x24, 0x28,
   0x30-0x34, 0x45, 0x4f, 0x50, 0x51 — всё покрыто подписью, spoof невозможен
   без ключа AMD.
2. **AES-encrypted payload'ы**: 0x01, 0x09 — без AES-key в fuses ничего не сделать.
3. **KDB (0x44)**: cert chain, self-verifying, RSA-key at root — тоже unforgeable
   без ключа.
4. **$PSP directory**: fletcher32 — обходится, но payload'ы всё равно
   подписаны, spoof pointer'а в attacker-controlled region бесполезен.

**Вывод**: PSP-side без AMD key ИЛИ hardware fault-injection закрыт.

## Что открыто: BIOS side (DXE FV @ 0xAE0000)

Разжал LZMA (guided section) FV @0xae0000: **4.2 MiB DXE volume, 169 модулей**.

Ни один DXE модуль в SPI **не подписан AMD**. Их integrity проверяется только
BIOS'ом самим себя (обычно нет проверки, DXE core просто исполняет то, что в FV).

**Ключевая находка**: `Bc250CoreUnlockDxe` (0x3046 байт, GUID
`6d423d2f-546a-6b4a-82d0-1207cc5b6d92`) — factory-shipped custom DXE от вендора.
Пишет в SMN block `0x03B10A20/80/88/8C` (NBIO NB_TOP_ARB unlock) и PCI cfg
port `0x0FEF0CF8`. Не трогает VCN.

Из 169 модулей **ни один не пишет в VCN MMIO** (`0x1FCxxxxx-0x1FFxxxxx`),
только этот один пишет в NBIO SMN. Vendor unlock — только CPU cores.

Inventory: `evidence/firmware-audit/20260926-dxe-audit/dxe-inventory.json`.

## Единственный жизнеспособный путь

**Расширить `Bc250CoreUnlockDxe`** — добавить в него VCN unlock sequence
(тот же SMU RPC path, что пытались в runtime, но выполненный в DXE фазе
до BdsDxe). Плюсы:

- DXE не подписан → можно менять без RSA ключа.
- Один модуль уже есть — cкорее всего активен → его выполнение
  гарантированно происходит.
- Ограничение размера мягкое: PE32 сейчас 12 KiB (`.text` 4 KiB + `.data` 4 KiB
  - headers), можно раздуть до 32 KiB без перекомпоновки FV (много tail padding
    в этом FV).

Минусы:

- Нужно построить PE32 с новой логикой, вставить UI-section, пересчитать
  checksum FFS header, пересобрать guided section с LZMA, поместить обратно в SPI.
- Без reference (edk2 source для Bc250CoreUnlockPkg у нас нет), придётся
  писать unlock-код с нуля на C и собирать через edk2-stable202508.

## Kill list (обновлён после этого аудита)

- ❌ Любая модификация PSP payload'а (RSA sig on everything)
- ❌ Spoof PSP directory (payload sig всё равно проверяется)
- ❌ NO_GASKET (removal of entry 0x24) — hardcoded expected layout в ROM
- ❌ Gasket body substitution — signed region покрывает всё payload'а
- ❌ Runtime SMU RPC — не работает (session log 3-11 подтвердили wedge)
- ✓ Extended Bc250CoreUnlockDxe с VCN unlock — не пробовали, ЕДИНСТВЕННЫЙ
  открытый вектор

## Артефакты

- `evidence/firmware-audit/20260926-dxe-audit/dxe-inventory.json` — 169 DXE
- `/tmp/Bc250CoreUnlockDxe.efi` — extracted vendor unlock DXE (12 KiB PE)
- `/tmp/Bc250CoreUnlockDxe.text.bin` — .text section с immediate SMN writes
- `/tmp/dxe_uncompressed.bin` — расжатый DXE FV (4.2 MiB)

## Дальше

1. Не прошивать больше вслепую.
2. Сток восстановлен bit-perfect (SHA `83c4e420…`) → cold boot заведётся.
3. План: собрать `Bc250CoreUnlockDxeVcn.efi` с дополнением к vendor unlock,
   заменить оригинальный FFS in-place, пересжать guided section с LZMA,
   переспаять SPI.
4. Перед прошивкой требуется: edk2 toolchain + подтверждение оператора.

## Исправление 2026-09-27: структура type-0x09

Историческая строка выше «encrypted PSP L2 pointer» неверна для восстановленного stock P3.00. Raw directory parser нашёл type-0x09 в `0x93F200`, 0x440 B; независимый byte check: version 1, известный kid, e=65537, 2048-bit LE modulus; carriers 0x50/0x51 ссылаются на этот kid. Поля `$PS1` header к этому raw record неприменимы. ROM hash anchor и загрузка изменённого ключа не проверены. Подробности: `docs/research/2026-09-27-autonomous-firmware-gaps.md` G2.
