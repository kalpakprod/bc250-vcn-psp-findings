# Live-железо: VCN harvest=0 (фьюз исключён) — прямой замер по SSH

Date: 2026-09-25. Actor: root (laptop) → root@bc250 по SSH. Evidence class:
observed-bytes с ЖИВОГО железа (sysfs ip_discovery, безопасное чтение, без MMIO).

## Контекст доступа

- Плата загружена в Debian (kernel `7.1.5-bc250r2`) с флешки, которую делали ранее.
- IP платы: **127.0.0.1** (DHCP; hostname `bc250`). SSH root по ключу
  `~/.ssh/id_ed25519` (`IdentitiesOnly=no`, ключ уже авторизован на плате).
- Подтверждение железа: `lspci` → `01:00.0 ... Cyan Skillfish [BC-250] [1002:13fe]`,
  `AMD BC-250`, amdgpu, SMU fw `0x00580600` (88.6.0).

## Ключевой замер (безопасный sysfs, без wedge-класса)

`/sys/class/drm/card0/device/ip_discovery/die/0/12/0/` (hw_id 12 = VCN):

```
hw_id              = 12
major.minor.rev    = 2.0.3
base_addr          = 0x00007800 / 0x00007E00 / 0x02403000
num_base_addresses = 3
harvest            = 0x0      <-- НЕ harvested, фьюза нет
num_instance       = 0
```

## Выводы

- **VCN 2.0.3 присутствует, harvest = 0x0** — прямое доказательство с ЭТОЙ платы,
  что VCN НЕ выжжен фьюзом. Опровергает single-source заявление simpmix
  «VCN permanently eFused off» ([[firmware-audit]] уже фиксировал harvest=0 из ROM;
  теперь подтверждено живым кремнием).
- amdgpu на стоковом `bc250r2` **не регистрирует** VCN (в `detected ip block`
  его нет; UVD/VCE firmware version = 0x0) → блок пропускается драйвером.
- Замок = ПРОГРАММНЫЙ слой (драйвер + SMU/PSP power/gating), не кремний.

## Границы (не закрыто этим замером)

- harvest=0 отвечает ТОЛЬКО на «фьюз?» — нет. «Второй gate» (сможет ли SMU/PSP
  подать питание и снять изоляцию VCN) остаётся firmware/power-вопросом
  ([[open-questions]]), не фьюзовым. Опасные MMIO/SMN-чтения из Linux
  по-прежнему под запретом (D13/D17, вешают плату) — этот замер их не трогал.

## Побочно (serial-трек, закрыт)

- J5 UART: плата пишет в `/dev/ttyS0` (0x3f8) нормально (`WROTE_OK`), но
  DuPont-контакт на нераспаянном J5 не проходит до ноута (0 байт на приёме).
  cmdline `console=tty0` (не serial), BIOS без redirect → firmware/boot-консоли
  на J5 нет. Для доступа к плате serial не нужен: есть SSH root.
