# 2026-09-26 — DXE VCN v002: thunk-only (no gasket, no DF writes)

## Что изменено относительно v001

v001 включал ВСЕ три action class → boot hang (1 LED, no Ethernet).
Root cause: SMU exploit chain + gasket bank-12 writes + DF firewall writes
выполнялись разом в DXE. Те же операции вешали SMU в runtime sessions 8-11.

v002 оставляет ТОЛЬКО:

1. `PerformSmuUnlockDxe()` — SMU Q2 exploit (proven boot-safe в D10)
2. `EnableVcnHardwareUnified()` — Xtensa thunk: пишет 28 байт в SRAM,
   устанавливает handler slot 61, шлёт Q3 msg 0x61 (VCN power/clock bringup)

Отключено (`#if 0`):

- `ConfigureVcnGasketApertures()` — 56 SMN writes в bank-12 (0x0900Cxxx)
- `ConfigureVcnDataFabric()` — 16 SMN writes в DF firewall (0x03A2xxxx, 0x0001Cxxx)
- `SmuWriteSmn32()` — helper для вышеуказанных
- Все data arrays (`mGasketBank12Writes`, `mGasketDataFabricWrites`)

## Гипотеза

Xtensa thunk выполняет VCN power-up sequence на SMU Xtensa core напрямую.
Если VCN island запитается, ядро amdgpu увидит его при enumeration.
Gasket/DF writes нужны только если VCN MMIO routing не настроен — но на
стоковом BIOS routing уже есть (NBIF port 3 = VCN, просто power-gated).

## Сборка

- Source: `candidates/dxe-vcn-enabled-v002/source/`
- EFI: 16384 bytes (no LTO — LLVM 22 vs edk2's LLVM 19 lld incompatibility)
- ROM: `candidates/dxe-vcn-enabled-v002/BC250_P3.00_dxe-vcn-enabled_v002.bin`
- SHA: `77f06767e5ec43ae...`
- PSP region identical to stock: YES
- Build script: `candidates/dxe-vcn-enabled-v002/build_v002.py` (handles PE32 size change)

## Kill criterion

- 0 LED → PSP reject (не должно — PSP region не тронут)
- 1 LED, no Ethernet → Xtensa thunk wedged SMU (маловероятно — SRAM writes safe)
- 2 LED, Ethernet, VCN=0xFFFFFFFF → thunk не достаточен, нужны gasket writes
- 2 LED, Ethernet, VCN visible → SUCCESS

## Ожидает

Программатор CH347 не подключён. Нужно от оператора:

1. Обесточить плату
2. Подключить CH347 + клипсы к SPI
3. Сказать «готово»

Сначала восстановлю сток (v001 на чипе), затем прошью v002.
