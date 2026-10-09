# 2026-09-26 — DXE VCN Unlock v001 flashed

## Что собрано

- Взят готовый D10 edk2-пакет (`candidates/d10-early-dxe-smu-unlock/source/
Bc250VcnUnlockPkg`), скопирован в `candidates/dxe-vcn-enabled-v001/source/`.
- Один edit в `Bc250VcnUnlockDxe.c` (line 387):
  `mEnableVcnActions = FALSE` → `TRUE`.
  → включает вызовы `EnableVcnHardwareUnified()` + `ConfigureVcnGasketApertures()`
  - `ConfigureVcnDataFabric()` после `PerformSmuUnlockDxe()`.
- Пересобран через edk2 (WORKSPACE = импортированный `edk2-bc250-capture`),
  target: `Bc250VcnUnlockDxe.efi` — 12288 байт, sha `a3f78cfc75dd194d…`.
- Разница со стоковым D10 EFI: 3885 байт (компилятор пересчитал ветки под
  константой TRUE, весь блок вошёл в execution path).
- Вставлен в SPI через `build_d10.py` (замена PE32 payload'а в существующем
  `Bc250CoreUnlockDxe` FFS in-place, LZMA-recompress, FFS checksum пересчитан).

## Свойства образа

- `candidates/dxe-vcn-enabled-v001/BC250_P3.00_dxe-vcn-enabled_v001.bin`,
  SHA `a61c988d9af6db250a27f90bdc6447c50e37a4101fcc1565f516057b24f33fb8`.
- **Signed PSP region (0x8E0000..0xAE0000) идентичен стоку** —
  подпись AMD не тронута.
- Diff bytes: 1 333 650, все внутри DXE FV `0xAE0000..0xE00000`
  (пересжатие LZMA перекомпоновывает bit-stream).
- Manifest: `candidates/dxe-vcn-enabled-v001/build-manifest.json`
  подтверждает `signed_psp_region_...identical=True` и
  `decompressed_bytes_outside_target_pe32_identical=True`.

## Flash

- Pre-flash SHA `83c4e420…` = STOCK P3.00 (проверено).
- Write: `flashrom -p ch347_spi -c W25Q128.V -w …dxe-vcn-enabled_v001.bin`
  → **VERIFIED**.
- Post-flash SHA `a61c988d…` = **bit-perfect** совпадает с candidate.
- Артефакты:
  - `evidence/programmer/reads/20260926-dxe-vcn-enabled/pre-flash-20260926-071459.bin`
  - `evidence/programmer/reads/20260926-dxe-vcn-enabled/post-flash-20260926-071459.bin`

## Почему это должно загрузиться

- Signed PSP payload'ы (IPL/ABL/TOS/SEC_GASKET) не тронуты → PSP boot-ROM
  и ABL0/1 отработают как на стоке (первый зелёный LED, потом второй).
- Замена — только PE32 payload'а внутри `Bc250CoreUnlockDxe` FFS, размер
  сохранён, GUID сохранён (`6d423d2f-...`), FFS header checksum пересчитан.
- Original D10 candidate (с `mEnableVcnActions=FALSE`) уже был hardware-tested
  в session 3-4 — грузится, publishes protocol → значит наш путь через
  тот же FFS slot валиден.
- Изменена ТОЛЬКО одна константа (FALSE→TRUE) → выполняется gasket+DF+SMU
  sequence из того же D10 driver'а, который до этого проходил boot-safe.

## Kill criterion

- Если нет ни одного LED → PSP каким-то образом валидирует DXE FV или
  outer FV header changed (не должно — build_d10.py специально сохраняет).
  Восстановить сток из
  `evidence/programmer/reads/20260926/pre-flash-p300-absence.bin`.
- Если LED проходят, но зависание до BDS → DF firewall write повесил
  fabric. Recovery: тот же rollback на сток.
- Если BDS загружается → `lspci -k | grep -A3 VCN` и `dmesg | grep amdgpu`;
  ожидаемо VCN появится как powered device.

## Дальше — cold boot оператором.

## Cold boot result: PARTIAL — first LED only, no Ethernet

- Первый зелёный LED мигнул один раз, второго LED нет.
- Ethernet не поднимается → OS не грузится → BDS не достигнут.
- Первый LED = PSP boot-ROM + IPL + ABL0/1 отработали (сток P3.00 signed
  region цел, что и подтверждено).
- Отсутствие второго LED = DXE dispatch либо ранний PEI зависли.

## Root cause (гипотеза)

`Bc250VcnUnlockDxe` (наш модифицированный) выполняет:

1. `PerformSmuUnlockDxe()` — Q2 msg 0x23 spam (30 итераций) → msg 0x0A →
   Q2 msg 0x23 spam (28+1 итераций) → msg 0x0A с key=0x37.
   Это SMU RPC exploit, дающий arbitrary write на Xtensa SMU SRAM.

2. `EnableVcnHardwareUnified()` — заливает 28-байтовый Xtensa thunk через
   SmuWriteSram32 (12 итераций), пишет handler slot 61, шлёт Q3 msg 0x61.

3. `ConfigureVcnGasketApertures()` — 56 SMN writes в bank-12 через Q3 msg 0x2C
   (privileged SMN write через SMU mailbox).

4. `ConfigureVcnDataFabric()` — 12 firewall writes через тот же Q3 msg 0x2C.

**В live-session 3-11 эта же цепочка (запускаемая из userspace через bc250-smu-unlock)
ВЕШАЛА SMU** — задокументировано в MISTAKES.md (session 8: sec_smn_read32
0x1FDxxxx wedges SMU; session 10: FN_DAG.14 wedges; session 11:
enable_smu_features(VCN_PG) hard hang).

Прошивая эту цепочку в DXE, мы получили ТУ ЖЕ проблему в UEFI-фазе.
SMU wedge в DXE = SMU не отвечает на PEI's next request после DXE hand-off =
DXE dispatcher blocks = второй LED не зажигается.

## Урок

`mEnableVcnActions = FALSE` в D10 стоял НЕ случайно. Комментарий в коде:

> «Deliberately false in D10. Later candidates can enable one action class
> only after early-unlock boot safety is established.»

Мы включили всё разом. Правильный путь — enum action classes по одному:
first только `EnableVcnHardwareUnified` (Xtensa thunk без gasket writes),
потом только `ConfigureVcnGasketApertures` (без Xtensa), потом только
`ConfigureVcnDataFabric` (без gasket) — bisect который из трёх вешает.

Но каждый эксперимент = flash + cold boot + возможный wedge → recovery flash.
Не быстро.

## Immediate action

Восстановить сток. Программатор CH347 разъединился (штатное поведение при
питаемой плате — ток от VCC-3.3 пробивает через клипсы, USB-hub на хосте
переключает shared line). Требуется от оператора:

1. Полностью обесточить плату (unplug PSU).
2. Отсоединить программаторные клипсы от SPI чипа.
3. Отключить CH347 от USB хоста, подождать 5с, подключить обратно.
4. Подсоединить клипсы к SPI чипу заново (без питания платы).
5. Сказать «CH347 подключён» — я запущу restore.

Кандидат `dxe-vcn-enabled-v001` — **тупиковый**. Не прошивать снова.

## Следующая гипотеза после rollback

Собрать `dxe-vcn-enabled-v002` со следующими правками:

1. `mEnableVcnActions = TRUE`, НО:
2. `EnableVcnHardwareUnified()`: закомментировать (Xtensa thunk — слишком
   агрессивно на cold boot, вероятно ломает SMU state machine).
3. `ConfigureVcnGasketApertures()`: только последние 3 writes — те, что
   реально «enable+lock» (без пересборки всей bank-12 таблицы, потому что
   на стоке она уже загружена ABL1).
4. `ConfigureVcnDataFabric()`: закомментировать полностью (fabric firewall
   writes — самый рискованный класс, вешают в 100% случаев на этой плате).

Одно изменение за раз. Если v002 boot-safe, но VCN не появился — добавляем
DataFabric в v003.
