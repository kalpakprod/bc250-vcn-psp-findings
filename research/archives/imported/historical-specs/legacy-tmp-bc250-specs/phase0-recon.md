# Phase 0 — Recon (spec-driven)

**Цель:** собрать все факты о прошивке/драйвере BC-250 (gfx1013 / Cyan Skillfish),
которые нужны, чтобы спроектировать эксплойт активации VCN. Recon = read-only,
software-first (hardware на плате `tunika`, доступ по ssh).

**Контекст:**
- Барьеры активации VCN (из брифа): IP Topology → SMU Power/Clock Gating → PSP Signature.
- Дайджест CVE AMD PSP/SMU/VCN: 61 CVE, ~18 NO FIX (0-день на практике).
  Основа: CVE-2024-36319 (VCN FW debug), CVE-2021-26335/29951 (PSP boot loader),
  CVE-2024-36346 (PMFW/SMU).
- Дайджест драйвера: 40-CU unlock (duggasco, CC+SPI+RLC, PCI 0x13FE) + compute queue
  (Mesa/RADV) уже встроены в ядро MastaG/linux-cachyos-bc250. VCN пока не тронут.

## Критерии приёмки (acceptance)

Фаза 0 считается закрытой, когда для каждого из 3 барьеров есть хотя бы один
**подтверждённый факт** (команда/файл/регистр с доказательством), а не предположение:

- [ ] **B1 (Topology):** в `soc15.c` для gfx1013 (IP_VERSION 10,1,3) VCN либо
       отсутствует в `amdgpu_ip_blocks`, либо закомментирован. Точное место + diff
       относительно рабочего блока ( Renoir/green_sardine_vcn).
- [ ] **B2 (Power/SMU):** найден ID команды `VcnPowerUp` в SMU-прошивке или в
       `smu_v13_0` драйвера; зафиксирован текущий `enabled_features`
       (0xdd602c7d) и то, что Queue-3 сообщения VCN возвращают status 0x00
       (уже есть в probe_vcn3.out — нужно подтвердить на свежем дампе).
- [ ] **B3 (Signature):** определена версия PSP-тайла для Cyan Skillfish
       (psp_13_0_11_ta / psp_13_0_12_sos и т.п.), описан поток проверки подписи
       (заголовок → RSA-2048/SHA-256 → OTP), и для каждого VCN-блоба указано,
       есть ли рядом ADS-контейнер / подпись.
- [ ] **VCN-блоб:** подтверждено отсутствие `cyan_skillfish_vcn.bin`; найден
       источник (linux-firmware / ADS-контейнер) и размер замены.
- [ ] **CVE → gfx1013:** для CVE-2024-36319 / 26335 / 29951 / 36346 подтверждено,
       применимы ли к gfx1013 (не только EPYC). Источник: AMD-SB-6024 / 1027 / 4013 / 6018.
- [ ] **SMU-прошивка:** найден и (по возможности) дампирован файл SMU-прошивки,
       из которого можно искать VcnPowerUp.

## Ограничения (out of scope для Фазы 0)

- Не паяем, не глитчим SPI (это Фаза 1+ с hardware).
- Не компилируем драйвер, не правим код (это Фаза 1+).
- Не требуем hardware от пользователя: всё — на `tunika` + публичные источники.

## Метод (как добываем факты)

1. **Live-дамп с tunika** (ssh, sudo): SMU-команды (VcnPowerUp probe),
   `firmware_info`, `ip_blocks`, `gpu_metrics`, дамп SMU-прошивки, список
   `/lib/firmware/amdgpu` (VCN + psp_блобы).
2. **Драйвер**: `soc15.c` / `amdgpu_discovery.c` для gfx1013 — где VCN в ip_blocks;
   `smu_v13_0.c` — ID VcnPowerUp; `vcn_v2_0*` — структура VCN.
3. **CVE**: уже есть `cve_results.json` (61 CVE) + `cve_target.json` (7 целевых).
   Дополнить проверкой применимости к gfx1013 через AMD-SB.
4. **linux-firmware**: найти `cyan_skillfish_vcn.bin` / ADS-контейнер.

## Артефакты (куда пишем)

- `tmp_bc250/recon/barrier_map.md` — барьер → факт → доказательство.
- `tmp_bc250/recon/smu_firmware.md` — VcnPowerUp + Queue-3.
- `tmp_bc250/recon/psp_signature.md` — PSP-тайл + поток подписи + VCN-блобы/ADS.
- `tmp_bc250/recon/cve_gfx1013.md` — применимость CVE к gfx1013.
- `tmp_bc250/recon/README.md` — индекс + статус приёмки (чек-лист).

## Выход

Покрытие критериев приёмки ≥ 80% → Фаза 0 закрыта, переход к Фазе 1 (дизайн/exploit).
Непокрытые пункты → формулируются как гипотезы для Фазы 1 (hardware-верификация).
