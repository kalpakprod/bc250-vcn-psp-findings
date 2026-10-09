# BC-250 — PSP & NBIO Firmware Extraction & Root Isolation Audit

**Date:** 2026-08-25  
**Target:** AMD BC-250 BIOS **Robin 3.00** (`Robin3.00.ROM`, 16 MiB)  
**Tools Employed:** `PSPTool` (TU Berlin), `UEFIExtract A75` (LongSoft), `pypcode` (SLEIGH Xtensa)

---

## 1. Сводка результатов экстракции

В соответствии с правилом исключения слепых записей на плату, мы перешли к полному статическому аудиту подсистем безопасности PSP (Platform Security Processor), ABL (AGESA Boot Loader) и UEFI PEI/DXE:

1. **Экстракция каталогов PSP / BHD (`psptool`):**
   - Извлечены 22 уникальных системных блоба (`tmp_bc250/recon/robin3_psp_unique/`).
   - Для всех упакованных компонентов выполнен стриппинг $PS1-заголовков и zlib-декомпрессия (`tmp_bc250/recon/robin3_psp_bodies/`).
   - Ключевые компоненты:
     - `HARDWARE_IP_CONFIG` (Type `0x20`): 1104 байта дескрипторов IP-блоков кристалла.
     - `SEC_GASKET` (Type `0x24`): 11344 байта конфигурации аппаратных гаскетов безопасности.
     - `ABL0`–`ABL4` (Types `0x30`–`0x34`): ранние стадии инициализации кремния AGESA.
     - `PSP_FW_TRUSTED_OS` (Type `0x02`) & `DRIVER_ENTRIES` (Type `0x28`): доверенная ОС процессора PSP.

2. **Декомпозиция UEFI PEI/DXE (`UEFIExtract A75`):**
   - Распакован том BIOS (`tmp_bc250/recon/robin3_uefi/BIOS.bin.dump/`).
   - Идентифицированы ключевые PEIM инициализации шины и графического ядра:
     - `AmdNbioGfxARIPei` (`D0FF5E04-1D07-491D-970E-E220A3B79611`)
     - `AmdNbioBaseARIPei` (`6CFDBB02-DB4B-4C87-BE13-B4E79E68CE51`)
     - `AmdNbioPcieARIPei` (`2B9E5A05-686F-4E72-AF0A-2D7BAA61E918`)
     - `AmdNbioSmuV10Pei` (`7307BD0F-8B7A-4BA5-9AF6-3997D1E32786`)
     - `AmdPspPeiV2` (`27 AmdPspPeiV2`)
     - `AmdFabricAriPei` (`17 AmdFabricAriPei`)

---

## 2. Ключевые архитектурные находки

1. **Аппаратная топология в `HARDWARE_IP_CONFIG`:**
   - Подтверждены базовые адреса аппаратных шин:
     - **VCN Fabric Base:** `0x02403000`
     - **GC (Graphics Core) Fabric Base:** `0x02402C00`
     - **THM (Thermal) Fabric Base:** `0x02400C00`
   - Сегмент VCN 2.0 зафиксирован на смещениях `0x7800` (BAR5 base) и `0x7E00`.

2. **Связь ABL с SMU/PSP:**
   - `ABL1` содержит процедуры низкоуровневой настройки шины SMN (`~SMN R [0x%0x]`, `~SMN W [0x%0x] = 0x%0x`) и специфические сообщения управления питанием (`PSPSMC_MSG_ConfigSocRail`, `PSPSMC_MSG_ChangeGfxMode`).
   - В `SEC_GASKET` зашита матрица изоляции портов доступа между Host CPU, PSP и периферийными контроллерами (включая UVD/VCN).

3. **Локализация изоляции ("Root Isolation"):**
   - Поскольку SMU Domain 6 физически запитан и клоки VCLK/DCLK активны (625/1111 MHz), возврат `0xffffffff` на уровне BAR5 обусловлен **NBIF/Fabric Gasket Clamp** — отключением моста на уровне `AmdNbioGfxARIPei` / `SEC_GASKET`, а не силовой блокировкой в SMU.

---

## 3. Артефакты и результаты

| Путь к файлу | Описание |
|---|---|
| `tmp_bc250/recon/robin3_psptool.json` | Полная таблица директорий PSP и метаданных |
| `tmp_bc250/recon/robin3_psp_unique/` | 22 извлечённых блоба прошивки |
| `tmp_bc250/recon/robin3_psp_bodies/` | Декомпрессированные исполняемые тела PSP/ABL |
| `tmp_bc250/recon/robin3_uefi/` | Полный дамп декомпозиции PEI/DXE модулей UEFI |
| `tmp_bc250/recon/robin3_psp_body_scan.json` | Карта перекрёстных ссылок литералов и строк |
