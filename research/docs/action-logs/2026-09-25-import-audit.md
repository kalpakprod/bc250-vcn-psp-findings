# Аудит import/ (31 ГБ) — 2026-09-25

## Цель

Найти артефакты в `import/from-windows/` (миграция с Windows), которые:

1. Не перенесены в основной репо и нужны для VCN-задачи
2. Содержат секреты (для удаления/защиты)
3. Дублируют то, что уже в `evidence/`

## Структура import/ (31 ГБ)

| Область         | Размер | Содержание                                                                              |
| --------------- | ------ | --------------------------------------------------------------------------------------- |
| Documents/Codex | 21 ГБ  | Codex-сессии: x20 (UEFI capture, Discord dump 14 ГБ media, PSP analysis, awesome-bc250) |
| tmp_bc250       | 5.9 ГБ | Основная рабочая директория: recon/, campaign/, bc250_smu/, 4700S ROM, PSP entries      |
| AppData         | 2.5 ГБ | OpenSIL checkout (NBIO reference code!), finalizer audits, Temp                         |
| .agent-reach    | 811 МБ | ShadPS4/game scripts (не VCN)                                                           |
| bc250-bios      | 73 МБ  | Старый репо: 7 VCN docs, 74 evidence файла, gasket RE                                   |
| Downloads       | 44 МБ  | AyuGram (Telegram) пакеты: VCN test package, async-compute, CAD схема, BIOS zip         |
| WorkBuddy AI    | 9 МБ   | PSP attack surface doc, VCN контекст, UEFI menu script                                  |
| .claude/.codex  | 132 КБ | Память сессий: VCN second gate hunt, PSP vuln analysis (blocked)                        |

## НЕ ПЕРЕНЕСЕНО (критичное для VCN)

### F1: VCN документация из bc250-bios (7 файлов)

```
import/.../bc250-bios/docs/source-docs/
  VCN-LOCK-MECHANISM.md      — полный RE: 5 слоёв блокировки, PSP chain, gasket decode
  VCN-UNLOCK-CORRECT-CHAIN.md — верная цепочка G0-G9, вердикт: G5 NBIF/Fabric = BLOCKER
  VCN-ATTACK-PLAN.md          — exploit spec: VULN-A/B/C, PoC plan, rollback
  VCN-EXPLOIT-SPEC.md         — own exploit: bank-12 replay, method rules
  VCN-START-SAFE.md           — safe ordering (WRITE-FIRST)
  unclamp_decode.md           — gasket decode details
  roadmap_A_results.md        — roadmap A results
```

**Статус:** NOT FOUND в docs/ основного репо. Это самые ценные VCN-документы проекта.

### F2: 74 evidence файла из bc250-bios

```
import/.../bc250-bios/evidence/a26_*, a30_*, b1_*, c1_*, e1_*, f1_*, g1_*
```

PSP disasm, gasket diff, APCB groups, RSA analysis, IFR strings, setup decode.
**Статус:** NOT FOUND в evidence/ основного репо.

### F3: 4700S BIOS ROM (16 МБ)

```
import/.../tmp_bc250/bc250_firmware/4700S/C0A/C0A
sha256: bb2cf51df4099a4c4a01c9959c13cfa186f5e59abd2eb04de731670febca8243
```

Полный 16 МБ ROM от ASRock 4700S Desktop Kit. Нужен для diff SEC_GASKET (VCN bank).
**Статус:** Частичный анализ в evidence/firmware-audit/20260914-4700s/, но сам ROM NOT FOUND.

### F4: lorek123 PSP decompiled (ABL1/3/4 + DRIVER_ENTRIES)

```
import/.../tmp_bc250/recon/lorek123_psp/
  ABL1_decompiled.c, ABL3_decompiled.c, ABL4_decompiled.c
  d00_e07_DRIVER_ENTRIES_0x28_0.1C.0.3_decompiled.c  — 669 functions, ARM 32-bit
```

Декомпилированный PSP bootloader. DRIVER_ENTRIES — это код, применяющий SEC_GASKET.
**Статус:** NOT FOUND в evidence/.

### F5: OpenSIL reference code (NBIO/DF/SMU)

```
import/.../AppData/Local/Temp/bc250-opensil-632b976/
  xUSL/NBIO/IOD/ — NbifepfncfgReg.h, NbifmmReg.h, NbifrccfgReg.h, GnbRegisters.h
  xUSL/DF/, xUSL/SMU/
```

AMD OpenSIL: reference NBIO register definitions. Может содержать gasket/firewall register names.
**Статус:** NOT FOUND в evidence/.

### F6: PSP entries (extracted, Robin1 + Robin5)

```
import/.../tmp_bc250/recon/robin1_sec_gasket/  — 22 PSP blobs (ABL0-4, APCB, DRIVER_ENTRIES, SEC_GASKET, SMU, TOS)
import/.../tmp_bc250/recon/robin5_sec_gasket/  — 22 PSP blobs (newer versions)
import/.../tmp_bc250/bc250_firmware/psp_entries/8_cores_Steam/  — 15+ extracted entries
```

**Статус:** NOT FOUND в evidence/ (только JSON analysis results есть).

### F7: Discord «BC250 Community» полный дамп (14 ГБ)

```
import/.../discord-in/dce/guild/
  json/ — 12 каналов exported (bc250-chat, in-progress, dynolog, faq-suggestions...)
  media/ — 14 ГБ attachments (photos, videos)
  data/ — channels.json (24), threads.json (100)
```

**Статус:** NOT FOUND в evidence/. JSON каналов — ценный research source.

### F8: AyuGram (Telegram) пакеты

```
import/.../Downloads/AyuGram Desktop/
  BC250_VCN_test_package_v2.zip
  bc250-async-compute-0.1.0.tar.zst / 0.2.0
  ASRock AMD BC-250_ISL_X5R r1.00.cad  — PCB schematic!
  bc250_3.00_clv1.zip
  bc250-bios-main.zip
```

**Статус:** NOT FOUND. CAD-схема платы особенно ценна.

### F9: Reference BIOSes (forbidden-darkness-drive)

```
import/.../recon/forbidden-darkness-drive/
  8_cores_steam.rom, bc250-Steam.rom, bc250.rom
```

Три варианта ROM (stock, Steam, 8-core). Нужны для diff.
**Статус:** NOT FOUND в evidence/.

### F10: Kernel driver diffs (vcn-patch-base/new, vcn-probe-base/new)

```
import/.../recon/vcn-patch-{base,new}/drivers/gpu/drm/amd/amdgpu/
import/.../recon/vcn-probe-{base,new}/drivers/gpu/drm/amd/amdgpu/
import/.../recon/vcn-source-context/ (includes .rej files — failed patches)
```

**Статус:** NOT FOUND.

## УЖЕ ПЕРЕНЕСЕНО (дубли)

| Артефакт             | import/                                | evidence/                                            |
| -------------------- | -------------------------------------- | ---------------------------------------------------- |
| campaign scripts (5) | tmp_bc250/bc250_firmware/campaign/*.py | evidence/board-home-20260924/home/OWNER/        |
| campaign JSON (3)    | campaign/*.json                        | evidence/board-home-20260924/home/OWNER/        |
| BC250_2.00.bin       | recon/theretroweb/                     | evidence/donor/retroweb-20260916/                    |
| bc250_smu library    | tmp_bc250/bc250_smu/                   | evidence/board-home-20260924/home/OWNER/share/pipx/ |

## СЕКРЕТЫ (требуют защиты)

### S1: Discord token

```
import/.../discord-in/token.txt
import/.../discord-in/extract_token.py
```

Discord auth token в открытом виде. Файл в .gitignore (import/ не в git), но при любом
копировании/архивировании должен быть исключён.

## F11: PS5 retail kernel (kernel_retail_250.elf)

```
/home/OWNER/Downloads/kernel_retail_250.7z
  kernel_retail_250.elf     — 56 МБ, ELF64 x86-64 FreeBSD (Orbis)
  kernel_retail_250.elf.i64 — 121 МБ, IDA Pro database
Build: W:\Build\J01329826, Oberon C0 (PS5 APU)
```

Ключевые находки:

- **VCNFW 71.15.51** встроен в ядро (тег `[ATI LIB=VCNFW,71.15.51]` @ 0x23aa880)
- **PPSMC таблица: 37 сообщений** — полная Q0/Q1 таблица PS5 SMU. **НЕТ PowerUpVcn** — подтверждает census
- **SMU mailbox адреса идентичны BC-250**: Q2 0x03B10528, Q3 0x03B10A20 — тот же SMU 11.8
- **Oberon golden settings** упоминаются (C0, B0, A0 варианты)
- **a53mm** — Sony multimedia module (VCN controller), 74 уникальных строки: ring management, suspend/resume, context save
- **avcntl_ih_kc/lock** — VCN interrupt handler kernel context
- **UVD_PGFSM_CONFIG (0x1f800)**: 27 ссылок — VCN power gating FSM активно используется
- _*Gasket адреса (0x0900c*): NOT FOUND_* — PS5 kernel не программирует gasket напрямую (это делает PSP/ABL)
- **DF firewall 0x03220124**: 1 hit — единственная ссылка на Data Fabric firewall
- **IDA database (.i64)** — готовый для анализа, 127 МБ

Значение для VCN-задачи:

- PS5 kernel подтверждает: VCN power management идёт через PGFSM, не через PPSMC messages
- Gasket программируется PSP при загрузке, не ядром — значит ответ в PSP firmware (SEC_GASKET/ABL)
- a53mm module содержит полную логику VCN ring management — reference для нашего direct-load
- IDA database позволяет декомпилировать a53mm и найти точную последовательность VCN power-up

## Рекомендации

### Перенести (по приоритету для VCN)

1. **F1** (7 VCN docs) → `docs/research/imported/` — основа всей VCN RE работы
2. **F3** (4700S ROM 16 МБ) → `evidence/donor/4700s-c0a/` — SEC_GASKET diff
3. **F4** (lorek123 PSP decompiled) → `evidence/psp-decompiled/` — DRIVER_ENTRIES = gasket applier
4. **F5** (OpenSIL NBIO headers) → `evidence/reference/opensil-nbio/` — register names
5. **F6** (Robin1/5 PSP blobs) → `evidence/psp-extracted/` — SEC_GASKET binary для diff
6. **F8 CAD** → `evidence/hardware/` — PCB schematic
7. **F9** (forbidden-darkness ROMs) → `evidence/donor/` — reference ROMs для diff
8. **F11** (PS5 kernel + IDA db) → `evidence/ps5-kernel/` — a53mm VCN module, VCNFW 71.15.51
9. **Discord JSON** (F7, ~50 МБ без media) → `evidence/community/discord-bc250/`

### НЕ переносить

- Discord media (14 ГБ видео/фото) — bulk, не VCN-relevant
- .agent-reach (811 МБ) — ShadPS4/game scripts
- pyc файлы, .git dirs
- Codex session outputs (52 МБ dialogue exports) — архивные

### Защитить

- **S1** Discord token (`discord-in/token.txt`) — при любом копировании исключить
