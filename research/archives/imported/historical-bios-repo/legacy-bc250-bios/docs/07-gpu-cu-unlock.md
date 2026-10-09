# Включение вычислительных блоков GPU (CU/SE/SH) на BC-250

## Вердикт

- BIOS-патч для поднятия числа активных CU невозможен и не нужен: ни один BIOS-носитель не несёт CU-маску, а рабочее и подтверждённое сообществом включение идёт записью GC-регистров на живой системе.
- CU-конфиг применяет SMU/PSP-стек в рантайме в регистры GC; они перезаписываемы, и комьюнити уже включает 40 CU на BC-250 (драйверный параметр `amdgpu.ps5_cu_unlock=3` или umr-утилита `bc250-cu-live-manager`).
- Ответ на вопрос 1: это не «жёсткий фьюз» целиком, не APCB-токен и не гаскет-группа; это конфиг в GC-регистрах, инициализируемых firmware, с частично read-only фьюз-битами.

## Что за чип на самом деле

- GC-таблица IP-discovery блоба в сток-ROM (PSP-запись типа 0x20 @0x981900, блоб @0x981A00, GC-таблица @0x981D60, версия 1.1) описывает полный диз: `gc_num_se=2`, `gc_num_wgp0_per_sa=3`, `gc_num_wgp1_per_sa=2`, `gc_num_sa_per_se=2` — 2 SE × 2 SH × 5 WGP = 40 CU.
- Форма 2×2×10 CU — это Navi-класс (кремний PS5/Oberon), не Cezanne: донор-Cezanne несёт собственный discovery с GC-таблицей v2 «1 SE × 8 CU» (Vega 8).
- Запись GC в IP-discovery стока помечена `harvest=0`, harvest-таблица «HARV» пуста: discovery-носитель уже содержит полный 40-CU конфиг, патчить в нём нечего.
- Дамп: `evidence/f1_gc_info.txt`, инструмент `tools/uefi/f1_gc_info.py`.

## Почему BIOS-носителей нет (вопрос 2)

### Гаскет/политики PSP

- Полные дампы групп 0x201/0x280 стока и донора не содержат ни одной пары в GC/NBIF-GFX пространстве: все 0x03-адреса — это DF-фабрика (0x03A2xxxx, 0x03D2xxxx), остальные — NBIF/VCN 0x09xxxxxx.
- Диф сток/донор по 0x03-пространству: только DF-окно (0x03A2011C: сток 0x87FF, донор 0x107FF) — GFX-адресов ноль.
- Механизм, на котором работает VCN-анлок (гаскет 0x24 + политика 0x45), физически не может выразить изменение CU/WGP: записывать GC-регистры через svc 0x7c политиками не умеет ни сток, ни донор.
- Дамп: `evidence/f1_gasket_gfx_diff.txt`, инструмент `tools/psp-policy/f1_gasket_gfx_diff.py`.

### APCB

- APCB стока @0xAB1000 (группы: PSPG, DFG, MEMG, FCHG, CBSG) не содержит GFX-группы вообще; донор-Cezanne имеет группу GNBG, но это 4 нулевых UMA-класс токена (0x0102, 0x0103, 0x0106, 0x0107) — CU-маски там нет.
- Дамп: `evidence/f1_apcb_groups.txt`, `evidence/f1_apcb_gfx_scan.txt`, инструмент `tools/apcb/f1_apcb_groups.py`.

### VBIOS

- В сток-ROM и в донор-BIOS нет ATOM-образа: нет валидного заголовка 0x55AA→ATOM, нет строк ATOM/ATOMBIOS/PowerPlayInfo/DispDevicePathInfo.
- VBIOS-носителя (PowerPlay, DispDevicePath, GPIO) в этом стеке просто не существует; на CU-маску он не влияет по определению.
- Дамп: `evidence/f1_atom_scan.txt`, инструмент `tools/uefi/f1_atom_scan.py`.

### AGESA (AmdNbioGfxARIPei)

- Модуль сериализует конфиг-структуру в TLV-блоб «$INV» (магия 0x564E4924) с идентификаторами токенов 0x1000–0x101B; совпадение ID 0x100F/0x1010 со смещениями mmCC_GC_SHADER_ARRAY_CONFIG/mmGC_USER_SHADER_ARRAY_CONFIG — последовательность ID, а не записи GC-регистров.
- Прямых доказательств, что AmdNbioGfx читает/пишет CU-маску, нет; строковый реестр модуля пуст («AmdNbioGfxInit Entry/Exit»).
- Выдержка дизасма: `tmp_bc250\recon\f1_nbgiogfx_4e00_5150.txt`.

## Как реально включаются CU (вопрос 3)

### Носитель и значения

- Активная CU-маска на SH вычисляется как `~(config | efuse | user)` в `gfx_v10_0_get_wgp_active_bitmap_per_sh` (`linux-kiq-diff\gfx_v10_0-rc7.c`): `mmCC_GC_SHADER_ARRAY_CONFIG` (0x100F, фьюз-стрэп), `mmGC_USER_SHADER_ARRAY_CONFIG` (0x1010, рантайм-оверрайд).
- Сток на BC-250: CC = 0xFFF80000 на каждом SE/SH (INACTIVE_WGPS = 0xFFF8 → активны WGP0–2 = 24 CU), SPI_PG_ENABLE_STATIC_WGP_MASK = 0x07.
- Включение — три записи на каждый инстанс SE/SH (через gfx_v10_0_select_se_sh): `mmCC_GC_SHADER_ARRAY_CONFIG = 0` (биты WGP3/4 реально очищаются, readback 0xFFE00000), `mmSPI_PG_ENABLE_STATIC_WGP_MASK = 0x1F`, `mmRLC_PG_ALWAYS_ON_WGP_MASK = 0x1F` → 40 CU.
- Комментарий в патче: «CC alone updates enumeration but SPI still dispatches only to enabled WGPs; both writes are required (verified empirically on BC-250)».

### Инструменты

- Драйвер: параметр модуля `amdgpu.ps5_cu_unlock` (0=off, 1=probe SE0/SH0, 2=SE0/SH0, 3=all SE/SH, 4=probe-all), патч в `tmp_bc250\recon\linux.patch`, hunk gfx_v10_0_get_cu_info.
- Юзерспейс: umr-утилита `WinnieLV/bc250-cu-live-manager` (дайджест TG описывает и её, и ошибки «Failed to read cyan_skillfish.gfx1013.mmSPI_PG_ENABLE_STATIC_WGP_MASK»).
- Живые логи: `tmp_bc250\recon\vcn-probe-mode{0,1}_2026-08-26.out` — «bc250-40cu-enable: mode=3 ... CC=0xfff80000->0xffe00000 SPI=0x00000007->0x0000001f» на всех четырёх SE/SH.

## Лимиты и риски

- Частично жёсткий харвест: старшие биты поля INACTIVE_WGPS в CC read-only (запись 0 читается обратно как 0xFFE00000), то есть фьюз-стрэп присутствует; перезаписываемы только реально существующие WGP-биты.
- Биннинг: кремний BC-250 харвестится по дефектам; в TG-дайджесте есть случай «38/40 CU, два CU дают крапинки на экране» — полный анлок не гарантирован стабилен на каждой плате.
- BIOS-патч всё равно бы не персистил: SMU/PMFW применяет конфиг заново при GFX power-up, порядок «политики PSP → инициализация GFX» такой, что гаскет-пары затираются; подтверждённого SMN-отображения GRBM-инстансов CC-регистра нет.
- Питание: пользователи гоняют 40 CU на 2000–2200 МГц; вопрос запаса ББ/PCIe-питания поднимался в TG («то есть если делать 8 ядер, 40CU — нужно подавать питание не только на 8 pin?»).
- Драйвер/ОС: amdgpu подхватывает анлок автоматически (CU-число идёт из регистров, а discovery уже несёт 40-CU конфиг); Windows-стек не тестирован.
- Детекция: PCI-ID/ATOM не меняются (ATOM-таблиц нет), PSP-аттестация эти регистры не покрывает; поверхность детекции — изменившееся CU-перечисление в sysfs/ROCm/профайлерах, видимое любому античиту или бенчмарку.

## Открытые вопросы

- Кто именно пишет CC/SPI_PG/RLC_PG при GFX power-up (MP1 PMFW или PSP-блоб) — по дизасму TOS/ABL не установлено.
- Является ли сток-значение 24 CU следствием фьюза или выбором SKU-конфига PMFW (для BC-250 как майнинг-платы) — на живой плате отличимо только дампом фьюз-блока MP0/MP1.
