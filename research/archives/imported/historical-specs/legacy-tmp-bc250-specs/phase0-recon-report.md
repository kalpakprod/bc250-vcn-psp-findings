# Phase 0 Recon — BC-250 VCN unlock

**Дата:** 2026-08-25
**Плата:** `steammachine` (127.0.0.1, WiFi; резерв Ethernet 127.0.0.1), доступ по SSH (`~/.ssh/config` -> `steammachine`)
**Режим:** software-first, read-only (Phase 0)
**Цель (Q2-A):** рабочая VCN видеокодировка/декодировка -> затем чистый unlock (Q3 A->B->C)

---

## 1. Аппарат + ядро

| Параметр | Значение |
|---|---|
| Hostname | `cachyos` (OS user `steammachine`) |
| Ядро | `7.2.0-1.1-cachyos-bc250` (`~/linux-cachyos-bc250`) |
| GPU | Cyan Skillfish [BC-250] `[1002:13fe]`, driver `amdgpu` bound |
| cmdline | `amdgpu.sg_display=0 ttm.pages_limit=1048576 mitigations=off acpi_enforce_resources=lax` |
| amd_psp (модуль ядра) | **НЕ загружен** (`lsmod`) |
| PSP (копроцессор + прошивка) | **АКТИВЕН** — amdgpu грузит `psp_v11_0_8`, SMU 88.6.0 |

> ВАЖНО: `amd_psp` (драiver ядра) != PSP (копроцессор). Модуль ядра может не быть, но
> PSP-прошивка жива и **проверяет подпись VCN-firmware по умолчанию**. Поэтому «без PSP ->
> сразу разблокируем» — ОШИБКА: подпись PSP остается вратарем даже без драйера. Доступ к
> SMU-mailbox — прямой (raw PCI config `0xB8`/`0xBC`), как и у 40CU.

## 2. Три барьера VCN (подтверждены на живой плате)

> Источник: память `6e3fe51d` (live board), Telegram BC-250 chat, msgs 150936/150940-44/155812.
> **Не** включать VCN одним патчем `amdgpu_ip_blocks` и **не** читать VCN-MMIO на живой системе
> (любое чтение -> hard hang). Разлок = снять 3 барьера по порядку.

### Барьер 1 — IP-block topology (драiver не знает про VCN)
- VCN **отсутствует** в списке IP-blocks amdgpu; `amdgpu_firmware_info`: VCN=0/0x0.
- Драiver даже не пытается инициализировать VCN. Нужен мапинг VCN в ip_blocks.

### Барьер 2 — подписанный Cyan/Oberon firmware (ворота PSP)
- `cyan_skillfish*_vcn.bin` **отсутствует** везде (`find /` пуст) — «Barrier 1» из старого отчёта.
- **Чужой VCN 2.0.x blob PSP отклоняет по подписи** (msg 155812). Любая прошивка должна быть
  подписана ключом Cyan/Oberon (PSP), иначе блок её не примет.
- -> просто скопировать blob в `/lib/firmware/amdgpu/` НЕДОСТАТОЧНО. Нужен либо подписанный
  blob, либо обход проверки подписи PSP (0-day).

### Барьер 3 — SMU power-up (неизвестная команда)
- **Неизвестна рабочая SMU-команда VcnPowerUp** (msgs 150940-150944). Без неё блок не
  питается/не пробуждается. Е надо найти/вывести (реверс SMU-протокола).

## 3. Механизм разлока 40CU (образец для повторения)

Разлок — в **userspace**, пакет `bc250-smu-oc` (pipx, Python 3.14), не в ядре.

- API: `bc250_smu.api.Bc250Smu(use_flock=True, allow_queue0=True)`
- Transport: `Bc250PciTransport` -> raw PCI config mailbox (`0000:00:00.0/config`)
- Queue-0 сообщения SMU:
  - `set_core_enable_mask(mask)` = msg `0x2C` (биты 0..7 -> ядра)
  - `get_enabled_smu_features()` = msg `0x3D` -> bitmask фич
  - `query_active_wgp()` = msg `0x1E`, `query_gfxclk()` = msg `0x0F`
- Инициализация: `check_test_message()` (msg `0x01`, queue 3, arg=123 -> ожидает 124)
- 16 systemd-сервисов: `bc250-cpu-oc`, `bc250-cu-layout` (38->40 CU),
  `bc250-cu-live-manager`, `bc250-gpu-fixed`, telemetry, watchdog, fan, netconsole...

> VCN-разлок = тот же паттерн (SMU-вызов + прошивка + фича), НО упирается в барьеры 1-3.

## 4. Логи: dmesg пуст -> netconsole

`dmesg` на плате пуст (ring buffer = 0). Ядро шлёт логи **off-box**:
- `bc250-netconsole.service` — kernel log -> UDP (приёмник на Windows: `127.0.0.1:6666`)
- `bc250-telemetry.sh` — дублирует семплы в `/dev/kmsg` с префиксом `BC250-TELEMETRY`

> Для Phase 1 (наблюдение за загрузкой VCN) нужен UDP-capture логов, а не `dmesg`.
> КЛЮЧЕВОЕ из памяти: краши были ещё на СТОКОВОМ ядре 7.1.8 (за 4 до кастомного) -> причина
> не в кастомном ядре/профиле/напряжении, а в железе/firmware.

## 5. Открытые вопросы (-> Phase 1)

1. **Откуда взять ПОДПИСАННЫЙ `cyan_skillfish2_vcn.bin`** — собрать из Mesa/amd-firmware,
   извлечь из PS5, или мап generic-VCN? (барьер 2, путь Q3-A)
2. **Рабочая SMU VcnPowerUp** — вывести реверсом (барьер 3, путь Q3-C).
3. **Мапинг VCN в ip_blocks amdgpu** — минимальный драйвер-патч (барьер 1, путь Q3-A).
4. **Обход подписи PSP** — если подписанного blob нет: 0-day на PSP (CVE-2021-26315 и др.).

---

## 6. Phase 1 (предложение)

**Путь A (firmware+driver, барьеры 1+2):**
1. Найти/подписать `cyan_skillfish2_vcn.bin` -> `/lib/firmware/amdgpu/`.
2. Мапить VCN в `amdgpu_ip_blocks` (минимальный патч, НЕ на живой системе).
3. Перезагрузить -> смотреть netconsole, загрузился ли VCN.

**Путь B (PSP signature bypass, если blob не подписан):**
4. 0-day на PSP (bootrom) -> отключить проверку подписи VCN.

**Путь C (SMU power-up, барьер 3):**
5. Вывести `VcnPowerUp` -> SMU-вызов включения VCN (аналог `set_core_enable_mask`).

**Q4:** А — прототип на `steammachine`, потом B — в апстрим (Mesa/AMD).
**Q5:** VCN-модуль — отдельно от 40CU, потом рассмотреть единый механизм.
