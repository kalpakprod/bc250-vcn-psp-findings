# Waveshare PROGRAM#/SPI reset — 2026-10-08

BC250-76, владелец: «продолжай реверс». Актуальный результат: `reports/waveshare-reset-path-20261008/AMD-SPI-RESULT.md`; первичная выборка27PDFстраниц/хеши и свежие rawCAD joins: `amd-spi-evidence.json` рядом. Основной контекст: `WAVESHARE.md`.

- LRC Rev.A: D606.1 cathode/PROGRAM#, D606.2 anode/RESETCON#. Через R8721 0Ω сеть идёт на SYS_RESET#/SU1.U4 (CAD part Bolton-D2H/A68H). Направление стягивания reset вниз подтверждено документом + CAD, не электрическим тестом.
- AMD51192 Rev3.03: ResetButtonEn разрешает input; UsrRst2Pll останавливает PLL; UsrRstToNBPwrGdEn переключает NB_PwrGD. Нет доказанного high-Z CLK/MOSI/CS. Defaults документа не являются readback платы.
- SpiBridgeDisable — SPI-LPC bridge для MAC, не disable основного master. SpiBusy=0 — idle, не high-Z. PwnSpiBus принудительно тянет перечисленные сигналы вниз в S3/S4/S5 при выключенном IMC. IMC96h/B4h прекращает только IMC fetch.
- Ранее заявленный конфликт W25Q pin2/5 снят: flash2=DO→SB_SPI_DI и flash5=DI→SB_SPI_DO совместимы с host-side naming. A68H ball direction/электрическая распиновка не проверены, не выдавать это за wiring acceptance.
- H1 «PROGRAM# low → high-Z FCH → внешний B9» не доказана. H2 «B9 через opcode/FIFO самого FCH, controlled restart, Waveshare только responder» — новая неиспытанная гипотеза, не согласованная смена архитектуры. Она не требует передачи CLK/MOSI/CS внешнему мастеру для B9, но нуждается в раннем hardware/PSP trace, отсутствии неконтролируемого пробуждения ABh, сохранении flash VCC, полном responder и recovery. Нынешний4KiB override недостаточен.
- Официальный AMD51205 Rev3.00 скачан в `evidence/datasheets/AMD-51205-Bolton-FCH-BIOS-Dev-Guide.pdf`, SHA256 `9441aa9f65e45bd51b0a609fccdfdf7f969e880ee86559ff3b4fa3f6ea2267d1`. Его introduction перечисляет M3/D3/D4/E4, отдельно D2H не подтверждает и отсылает к databooks/NDA/FAE. Avalon AGESA source — не доказательство раннего boot конкретного BC250.

## Firmware-продолжение того же дня

`reports/waveshare-reset-path-20261008/FIRMWARE-SPI-RESULT.md`: exactpublicCLV5.00 SHA256ea578104...; FchPei TE hash08493ca0..., FchDxe PE hash9adfd933...; полный provenance/sections/tables/model в `firmware-spi-evidence.json`,1073selectedinstructions в `firmware-spi-disassembly.txt`.

Entry240h→15A8h→copydefault13CEh/13E1h→reset-tasklauncher3A55h/4D95h→SPIinitializer4C59h. CopiedtemplateMode6/NormSpeed2 означает targetsingle-lane33MHz по initializer + AMD51192, НЕliveчастоту и НЕранний режим PSP. CurrentPIO10cycles требует25ns при400MHzscenario против15.15ns sampledeadline33MHz: softwaretimingblocker конкретизирован без hardware/overclock.

Opcodehelper4762h восстановлен до opcodewrite483Eh/Execute4850h; RDID/status/QEpaths условны, Mode6 QEcheck обходит. WEL/BUSYpolls внутренне не ограничены. DefaultQEtable12entries не содержит WinbondEF4018; не называть это livebug и не подменять ID. ABimmediates2B3Fh/2BD7h в FchDxe идут в I/O550h черезhelperEA4h, не в SPI. Это не исключает ABh из других/ранних stages. Type1PSP rawregion46592bytes не распознан generic$PS1/HeaderFilelayout; не делать encryption/ARMcodeвывод из rawscan. ImmutableROM не идентифицирован.

Стоп: нет применимых pad/reset timing A68H или раннего trace выбранного restart; currentmatchedheaderresponder также не успевает при найденном33MHzdefault. Нет вывода о невозможности no-solder и нет нового требования покупки. Никаких SSH/измерений/подключений/GPIO/MMIO/reset/B9/AB/QE/flash/build/изменений firmware gates в этом исследовании не было. Старые аппаратные задачи открыты.
