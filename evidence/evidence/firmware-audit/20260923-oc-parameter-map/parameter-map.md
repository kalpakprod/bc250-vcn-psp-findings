# CLV500: проверяемая карта параметров

Значения ниже прочитаны из чистого ROM. Это не рекомендации и не измерения платы.

| Поле | AmdSetup | Значение в ROM | INV token | Путь внутри CBS | Применение на плате |
|---|---|---|---|---|---|
| Memory Clock Speed | 0x316 / 1 B | 1800MHz (36) | 0x11ed | UMC Common Options → GDDR6 Common Options → DRAM Timing Configuration → I Accept (вход из CBS не доказан) | NOT TESTED |
| DRAM Timing User Controls | 0x32f / 1 B | Manual (1) | 0x1203 | AMD CBS → UMC Debug Options → GDDR6 Debug Options → GDDR6 DRAM Timing Configuration | NOT TESTED |
| UclkDiv1M0 | 0x330 / 1 B | Enabled (1) | 0x1204 | AMD CBS → UMC Debug Options → GDDR6 Debug Options → GDDR6 DRAM Timing Configuration | NOT TESTED |
| FCLK_DPM | 0x6a3 / 1 B | Auto (15) | 0x1331 | SMU Debug Options → SMU Features (вход из CBS не доказан) | NOT TESTED |
| VDDCR_VDD Voltage Offset Control | 0x6e5 / 1 B | Auto (0) | 0x1363 | SMU Debug Options → SMU Debug (вход из CBS не доказан) | NOT TESTED |
| VDDCR_VDD Voltage Offset | 0x6e6 / 4 B | 0 (0) | 0x1364 | SMU Debug Options → SMU Debug (вход из CBS не доказан) | NOT TESTED |
| DF Clock Override Control | 0x703 / 1 B | Manual (1) | 0x1373 | SMU Debug Options → SMU Debug (вход из CBS не доказан) | NOT TESTED |
| DF Clock Override | 0x704 / 2 B | 1420 (1420) | 0x1374 | SMU Debug Options → SMU Debug (вход из CBS не доказан) | NOT TESTED |
| Tcl | 0x317 / 1 B | Auto (255) | 0x11ee | UMC Common Options → GDDR6 Common Options → DRAM Timing Configuration → I Accept (вход из CBS не доказан) | NOT TESTED |
| Memory P-state | 0x36d / 1 B | Auto (255) | 0x123c | AMD CBS → UMC Debug Options → GDDR6 Debug Options → GDDR6 DRAM Controller Configuration → DRAM Power Options | NOT TESTED |

VDDCR_SOC: подтверждённый BIOS setter пока не найден. VDDCR_VDD offset не переименовывать в SoC.
FCLK_DPM: +0x6A3 → 0x1331. Memory P-state: +0x36D → 0x123C. Исправлены старые отчёты, связывавшие поле со следующим record ID.
DF help требует FCLK > UCLK и Memory P-state Disabled. Это текст интерфейса, не доказательство аппаратного ограничения и не готовый рецепт 1:1:1.
Числа в MHz на экране не устанавливают физическую семантику GDDR6/делителей.
