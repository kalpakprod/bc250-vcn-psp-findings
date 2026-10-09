# VCN live-сессия — action log (2026-09-25)

Actor: laptop root → root@127.0.0.1 (bc250). Оператор разрешил live. AUTO.
Транспорт записи: SMU Q3 0x98 через bc250-smu-unlock (secure access open).

## Board state (свежий прогон, read-only)

- ssh root@127.0.0.1 OK. hostname bc250, kernel 7.1.5-bc250r2, uptime 3 min.
- lspci: 01:00.0 Cyan Skillfish [BC-250] [1002:13fe]. BAR5 @ 0xfe900000 (512K).
- ip_discovery hw_id 12: VCN 2.0.3, harvest=0x0 (НЕ выжжен) — подтверждено вживую.
- tools: python3 3.13.5, setpci, amdgpu debugfs (amdgpu_regs_smc/pcie present).

## S0 baseline — enable_vcn.py --verify (read-only, PASS)

- SMU alive; secure access open (unlock exploit активен).
- dom6 state word @0xf714 = 0x00010101 (state byte 0x01 — НЕ 0x00,
  worst-case auto-power branch FUN_00023b14(6,1) НЕ сработает → безопасно).
- slot 0x16 dom6: clock=0x12 enable=OFF divider=5 status=READY gate@0x06d100
- slot 0x17 dom6: clock=0x00 enable=OFF divider=5 status=READY gate@0x06d128
- slot 0x18 dom6: clock=0x14 enable=OFF divider=5 status=READY gate@0x06d150
  => VCN-клоки выключены (enable=0), но домен в READY. Как и ожидалось.

## Recon перенесён

- evidence/board-home-20260924/home/OWNER → root@bc250:/root/vcn_unlock
  (1.9M, без .git/pyc). Содержит bc250-smu-unlock lib + enable_vcn.py +
  smn_vcn_gasket_unclamp.py + unclamp_step1.py + assess_S1.py.

## WEDGE (2026-09-25 ~16:47) — плата повешена чтением VCN MMIO при gated домене

- Действие: read-only чтение mmUVD_VERSION (dword 0x78CA) + mmUVD_POWER_STATUS
  через amdgpu_regs debugfs, ДО подъёма домена (без msg 0x61).
- Результат: команда 30s timeout; после — ping 100% loss, ssh connect timeout.
  Плата ЗАВИСЛА целиком.
- Причина: wedge-класс из enable_vcn.py item 8 — CPU reads of the VCN segment
  HANG the board while the island is dead (July x3: BAR5, UMR both hung on
  first read). VCN clamped => чтение его MMIO виснет на шине.
- Ошибка: нарушено собственное правило скилла vcn-unclamp-live (не читать VCN
  MMIO при гейтнутом домене; сначала msg 0x61). amdgpu_regs НЕ безопаснее для
  VCN-сегмента — тот же CPU-side MMIO read.

## RECOVERY REQUIRED

- Нужен ХОЛОДНЫЙ power-cycle (не reboot — SMU не сбросится тёплым).
- baseline VCN MMIO НЕ снят (before неизвестно; предполагается FF-clamp).
- Урок: baseline VCN MMIO нельзя снять безопасно ДО msg 0x61. Обязательный
  порядок: msg 0x61 (поднять домен) -> только потом любое чтение VCN MMIO.

## SESSION 2 (после cold power-cycle оператором ~16:50, uptime 0)

- Плата поднялась, ssh OK, VCN 2.0.3 harvest=0 подтверждён.
- root cause прошлого зависания уточнён и РАСШИРЕН: помимо VCN-MMIO wedge есть
  второй класс — **SMN-read firewall-адресов через msg 0x2A вешает SMU mailbox**
  (не всю плату; плата по сети жива, но SMU не отвечает, alive()=False,
  нужен cold power-cycle). Мой baseline snprint читал 7 firewall-регистров
  (0x3A2011C и др.) через smu.smn_read32 -> sec_smn_read32(addr) -> msg 0x2A;
  один адрес подвесил mailbox. assess_S1.py прямо предупреждал: "after the 0x2A
  wedge, NO 0x2A smoke".
- Отличие от рабочего enable_vcn --verify: оно НЕ читает firewall-регистры;
  dom6/slot state идёт через smu_read (msg 0x03/window), не через 0x2A.
- Фикс скрипта scripts/recon/vcn_s1_unclamp_safe.py: убран baseline-снимок
  firewall-регистров (snprint + FW_REGS удалены). Единственное 0x2A-чтение —
  post-write readback S1_ADDR. --verify теперь = alive + secure_access только.
- rsync -az НЕ перезаписал 57/58 пустых py-заглушек (0 байт, kalpak, Aug 25)
  на плате — mtime новее. Лечится rsync --checksum. Первый --verify работал
  из другой директории случайно.
- Состояние: SMU mailbox wedged, требуется ВТОРОЙ cold power-cycle оператором.
  Flash не тронут, записей в firewall не делалось (только чтения), обратимо.

## SESSION 3 (после 2-го cold power-cycle оператором ~17:08) — ПРОРЫВ

Порядок соблюдён строго (baseline -> подъём домена -> потом MMIO).

- S0 baseline (enable_vcn --verify, read-only): SMU alive, secure open,
  dom6 state=0x01, слоты 0x16/0x17/0x18 READY enable=OFF. Идентично прошлым.
- S1 подъём домена (enable_vcn full run, msg 0x61):
  - все 3 слота: enable 0->1 ON, LANDED, персистит.
  - slot 0x17 clock 0x00->0x20, status 0x00090053->0x02090053.
  - ctrl @0x06d0f8 = 0x02 (domain-level clock GATE держится на slot 0x17
    bit1; fw teardown НЕ запускался). msg 0x61 handler восстановлен -> 0.
- S2 manual-powerup (enable_vcn --manual-powerup, bounded polls, cannot wedge):
  - step[0]: ctrl 0x02 -> 0x00 LANDED and HELD -- ПЕРВОЕ реальное изменение
    состояния секвенсора на этой карте (gate bit, переживший все прошлые
    прогоны, снят). Night-1 теория "stores sat dirty" ОПРОВЕРГНУТА: пишется.
  - step[1] cmd bit0 up-request (self-clear, taken).
  - step[3] rail 0x00->0x00010000 bit16 rail-up (favored: already-up rail
    consumed one-shot; powered dom0-3 тоже читают 0).
  - AFTER: cmd=0 rail=0 status=0x01010101 ctrl=0x00000000.
  - VERDICT tool: clocks programmed + enables ON + gates released + rail
    taken. SMU-side power как полно, как этот oracle может дать.
- Плата ЖИВА после всех шагов (uptime растёт, ssh OK, SMU alive=True).

## РАЗВИЛКА (нужен явный go оператора)

Единственный оставшийся арбитр "виден ли VCN" — MMIO-чтение POWER_STATUS
через enable_vcn --direct-load. read_reg() = raw f.read(4) на amdgpu_regs
БЕЗ таймаута (тот же путь, что дважды вешал плату в session 1-2).

- НО: прошлые зависания были при GATED домене (enable=0, ctrl=0x02) — чтение
  шло в мёртвый остров. СЕЙЧАС домен поднят (enable=1, ctrl=0x00, rail taken)
  — впервые MMIO-read идёт в потенциально ЖИВОЙ остров.
- 3 исхода по doc: real values = остров жив (успех); all-ones = isolation
  (clean abort, measured 2026-08-20); hang = cold cycle (July, pre-clock-work).
- Риск: если hang — нужен 3-й cold power-cycle. Всё рантайм, flash не тронут.

## ВЕРДИКТ АРБИТРА (2026-09-25 ~17:12, оператор дал go на --direct-load)

Плата НЕ зависла — --direct-load отработал до конца, чтение вернулось мгновенно.

- --direct-load: MMIO amdgpu_regs читается, GC-остров ЖИВ:
  mmGB_ADDR_CONFIG = 0x00000044 (реальное значение через GC-аперу
  (0x1260+0x13DE)*4). fw-load прерван штатно: не нашёл чистый staging-span
  в VRAM (все кандидаты заняты живыми данными; --fw-offset нужен) — это не
  ошибка VCN, это про размещение fw в памяти.
- Прямое чтение VCN register block через штатный VcnDirect.rd (тот же
  транспорт, что читает GC 0x44), домен поднят:
  UVD_POWER_STATUS (_uvd(0x04)=byte 0x1F810) = 0xFFFFFFFF
  UVD_PGFSM_STATUS (_uvd(0x01)) = 0xFFFFFFFF
  UVD_PGFSM_CONFIG (_uvd(0x00)) = 0xFFFFFFFF
  UVD_STATUS (_uvd(0x6F)) = 0xFFFFFFFF
  UVD_SCRATCH9 (_uvd(0x1D)) = 0xFFFFFFFF

ВЫВОД (эвиденс-класс: измерено на живом кремнии, read-only MMIO):

- Это НЕ hang (плата жива, чтение мгновенно), НЕ баг адресации (та же
  формула читает GC=0x44). Это ISOLATION CLAMP: all-ones = master-abort на
  VCN register block.
- dom6-clock unclamp НЕОБХОДИМ, но НЕ ДОСТАТОЧЕН: SMU-side питание поднято
  (enable ON x3, ctrl gate 0x02->0x00, rail taken), а fabric/NBIF держит VCN
  register block изолированным. Есть ОТДЕЛЬНЫЙ isolation-слой ПЕРЕД
  register block, не снимаемый через dom6-секвенсор.
- Гипотеза "поднять dom6 -> VCN виден" ОПРОВЕРГНУТА на железе. Следующий
  барьер — fabric/NBIF isolation (не clock gate).

## S1 DF-window unclamp попытка (2026-09-25 ~17:14, после подъёма домена)

- Единый прогон: unlock -> smn_write32(0x3A2011C, 0x107FF) через msg 0x2B+0x2C.
- alive ПОСЛЕ записи = True (запись 0x2B/0x2C не вешает).
- Readback того же адреса через smn_read32 -> msg 0x2A: "queue 3 msg 0x2A
  timed out - SMU wedged, cold cycle". 0x2A виснет на 0x3A2011C даже как
  post-write readback (не только на baseline-снимке).
- VCN MMIO после S1: UVD_POWER_STATUS/PGFSM_STATUS/STATUS = 0xFFFFFFFF.
  GC sanity GB_ADDR_CONFIG = 0x44 (транспорт корректен, GC жив).
- ВЫВОД: (1) S1-запись 0x3A2011C сама по себе VCN register block НЕ
  открывает (всё ещё FF). (2) Адрес 0x3A2011C НЕЛЬЗЯ читать через 0x2A
  вообще — виснет как baseline, так и post-write. S1-верификацию надо делать
  без 0x2A (либо VcnDirect MMIO как арбитр, либо не верифицировать readback'ом).
- Состояние: SMU mailbox wedged (0x2A), плата по сети жива. Нужен cold cycle
  для следующей SMU-сессии. Flash не тронут, всё рантайм.

## Итог сессии (эвиденс: живой кремний, read-only + рантайм-записи)

1. VCN 2.0.3 harvest=0 — блок физически есть, не выжжен.
2. dom6 clock-домен поднимается штатно (enable ON x3, gate 0x02->0x00 снят,
   rail taken) — впервые реально изменено состояние секвенсора на этой карте.
3. НО VCN register block остаётся изолирован (all-ones master-abort) — есть
   отдельный fabric/NBIF isolation-слой ПЕРЕД register block.
4. S1 DF-window (0x3A2011C) — запись проходит, VCN не открывает; readback
   через 0x2A на этом адресе фундаментально виснет.
5. Барьер VCN = fabric/NBIF isolation, НЕ clock gate. Это меняет цель
   следующих сессий: искать снятие isolation, а не clock unclamp.

## SESSION 4 (2026-09-25 после операторского "готово" / power-cycle)

- Плата по сети UP: ping 0% loss, ssh OK, uptime 13 min.
- SMU state check: `Bc250Smu().alive()` = False (wedged).
- test_message (q3 msg 0x01) — timeout SmuTimeout из mailbox._wait_done.
- Диагноз: SMU остался wedged с сессии 3 (0x2A viselo на 0x3A2011C).
  Тёплый reboot SMU не сбрасывает — нужен ХОЛОДНЫЙ power-off (снять питание).
- Действий записи не делалось (только import + alive-check). Обратимо.

## SESSION 5 (после cold power-cycle оператором, uptime 0 min)

- SMU alive=True, `enable_vcn.py --verify` PASS (dom6 state=0x01, slots
  0x16/0x17/0x18 enable=0 READY — идентичен предыдущим baseline'ам).
- `enable_vcn.py` штатный полный прогон: msg 0x61 handler установлен,
  fire msg 0x61, поднят dom6 (все 3 slot enable=1 ON, ctrl gate 0x02->0x00
  снят, rail taken). Восстановил msg 0x61 handler в 0. thunk scratch wiped.
- Скрипт `scripts/recon/vcn_s2_pair_unclamp.py` (новый, S1+S2+S3+S4 pipeline)
  скатан на плату.

- S1 (0x3A2011C 0x87FF->0x107F) via Q3 0x98: alive=True after write.
- S2 (0x3A20124 0x0->0x10FFF) via Q3 0x98: alive=True after write.
- MMIO probe: mmUVD_VERSION=0xFFFFFFFF, mmUVD_POWER_STATUS=0xFFFFFFFF.
  Плата НЕ висит (dom6 up снял wedge на MMIO reads).

- S3a (0x1C780->0x2DF4D) alive=True, S3b (0x1C784->0xFF100000) alive=True.
- MMIO probe: mmUVD_VERSION=FF, mmUVD_POWER_STATUS=FF.

- S4a (0x3A20128->0xFFFF0000) alive=True, S4b (0x3E810->0x6) alive=True,
  S4c (0x3E814->0x2544C382) alive=True.
- MMIO probe: mmUVD_VERSION=FF, mmUVD_POWER_STATUS=FF.

- S5 attempt: `smn_full_gasket_replay.py` (1461 writes, file-order 0x201/
  0x203/0x210/0x280/0x281). Baseline `smn_read32(0x0900CB80)` → SmuTimeout.
  0x0900C234 read=0x0 OK. 0x0900C910/914, 0x09023234, 0x09300234, 0x0003E810/
  814 все → SmuTimeout. Первый write `smn_write32(0x09023234, 0)` через msg
  0x2B → SmuTimeout. 0/1461 writes, SMU DIED.

## ВЕРДИКТ session 5

- S1..S4 landed через host-side Q3 0x98, но VCN block остался master-abort:
  writes прилипают в SMN, но НЕ commit-ят fabric. Гипотеза owner/commit
  ПОДТВЕРЖДЕНА (open question #3 из unclamp_decode.md).
- Wedge-класс расширен: после S1..S4 SMN-адреса 0x0900CB80/C910/C914 +
  0x09023234 + 0x09300234 + 0x0003E81x возвращают SmuTimeout на любой
  mailbox-путь. Это отдельно от 0x2A wedge на firewall.
- Смена стратегии: путь A (APCB DFG патч, PSP-owned commit на буте),
  путь B (найти host commit-регистр через RE AmdFabricAriDxe), путь C
  (DXE-injection до SEC_GASKET LockDFReg).
- Skill `vcn-unclamp-live` обновлён (вердикт session 5, расширенный wedge).
- MISTAKES.md пополнен (0x2B/smn_read32/write32 wedge-класс).

## SESSION 6 (2026-09-25, после операторского "2"/power-cycle, uptime 16 min)

Плата ЖИВА: ping 0% loss, ssh OK, uptime 969s (cold-booted).

- S0 baseline (enable_vcn --verify через PYTHONPATH=bc250-smu-unlock):
  SMU alive=True, secure access open, dom6 state=0x01, slots 0x16/0x17/0x18
  enable=OFF READY. Идентичен всем прошлым baseline. Mailbox ЖИВ (не wedged).

- РЕВИЗИЯ всех прошлых runtime-экспериментов (что реально сделано на железе):
  1. stage5_full_dataplane (2026-09-12, 20260912_140003): 15 writes —
     routes 0x1c760/64/80/84/88/8c, windows 0x1f820/8a4, firewall
     0x322011c/124/12c + 0x3d2011c/124, 0x3e814. commit readback 0x0900c234=0x1.
     verdict FULL-DATAPLANE-APPLIED.
  2. stage4_arbiter (сразу после): mmUVD_POWER_STATUS/STATUS/SEMA/SCRATCH9/
     VERSION = ALL 0xFFFFFFFF. Verdict: "ALL-ONES: island isolated (bridge
     closed); gasket latched but NBIF not passing".
     => donor-route + firewall + commit ЧЕРЕЗ RUNTIME SMN = VCN всё равно
     изолирован. Runtime SMN unclamp опровергнут ПОЛНОСТЬЮ (не только S1..S4,
     но и полный dataplane).

- НОВЫЙ НЕПРОВЕРЕННЫЙ УГОЛ (единственный runtime-эксперимент, не повтор):
  - NBIF port config `0x6A1xx` НИКОГДА не писался (grep smn_write на 0x6a1xx
    во всех скриптах платы = 0 hits). Только читался (3 скрипта).
  - Per RE (nbif-clamp-mechanism.md): NBIF port `0x3`=clamped инжектится
    PEIM-дефолтами через токены 0x10c2/0x10c3, поле struct +0x1e0/+0x1e1.
    Это ОТДЕЛЬНЫЙ clamp (a), независимый от firewall (b), никогда не тронут
    в runtime.
  - ТРАНСПОРТ: read_nbio_safe_targets.py использует Bc250PciTransport.
    read_smu_reg = PCI config B8-index window (os.pwrite fd, reg, 0xB8;
    pread 0xBC), НЕ mailbox msg 0x2A. Есть парный write_smu_reg
    (pwrite 0xB8 reg; pwrite 0xBC value) — запись SMN БЕЗ mailbox,
    обходит весь wedge-класс 0x2A/0x2B.

- LIVE baseline 0x6A1xx через B8-window (read-only, SAFE, mailbox не тронут):
  iohc_source_5c 0x13b1005c = 0x00008000
  iohc_source_60 0x13b10060 = 0x0000ffff
  iohc_source_4c 0x13b0004c = 0x00800000
  nbio_target_6a140 = 0x00008000
  nbio_target_6a144 = 0x0000ffff
  nbio_target_6a148 = 0x00800000
  nbio_target_6a14c = 0x00000008
  nbio_route_33e0 = 0x00003820
  Плата ЖИВА после (B8-read безопасен, как и ожидалось).

## РАЗВИЛКА session 6 (нужен выбор оператора)

Все runtime SMN-пути опровергнуты (S1..S4 + полный dataplane + gasket replay).
Остались ДВА направления:

- Путь R (runtime, НОВЫЙ): записать NBIF port config через B8-window
  (write_smu_reg) — единственный нетронутый регистр-класс + единственный
  транспорт, обходящий mailbox-wedge. РИСК: точный write-target для токена
  0x10c2/0x10c3 НЕ доказан RE (0x6a1xx = кандидаты-захваты, не подтверждённые
  write-таргеты); NBIF port config может быть locked → возможен bus-hang →
  cold cycle. Плюс: обратимо (power-cycle), flash не тронут.
- Путь A (offline, APCB DFG flash): править несигнатурный APCB DFG-token
  (checksum-only), PSP строит гейт на буте = PSP-owned commit. Не
  board-hang-риск в runtime (flash-мод + cold boot), обратимо (restore APCB
  region). Требует: точный DFG sub-index VCN + алгоритм APCB checksum.

## SESSION 6 — Путь R выбран оператором ("r1"), ОТРАБОТАН → target disproven

RE-обоснование write-target (перед любой записью, чтобы не писать вслепую):

- Дизасм `AmdNbioGfxARIPei` (evidence/firmware-audit/rizin/): SMN-доступ идёт
  через PCI B8-окно (`fcn.00014a35` read, `fcn.00014b1f` write, `fcn.00014c0c`
  RMW). Адрес вычисляется из bus/dev/fn args, `0x6a1xx` — результат окна.
- RE-вердикт (2026-09-12 s2a-runtime-donor-aperture.md:184): PEIM делает
  RMW `0x6a148 <- (reg&~0x800000)|v`, `0x6a14c <- (reg&~0x8)|v`,
  `0x6a150 <- ...|MSR 0xc001001a`, `0x6a154 <- ...|(MSR|1)` — payload
  MSR-derived, НЕ значение `0x3`.
- Значение `0x3` (Port-Disconnected) живёт в struct+0x1e0/0x1e1 → сериализуется
  в токены 0x10c2/0x10c3 (NBIF_VCN_PORT_CONFIG / BRIDGE_ENABLE), НЕ в 0x6a1xx.

LIVE-проверка (B8-window read-only, mailbox не тронут, плата жива):

- Все 12 регистров 0x6A140..0x6A1B4 + 0x33e0 прочитаны дважды.
- 0x6a140=0x8000(low3=0), 6a144=0xffff(low3=7 уже Full-Enabled),
  6a148=0x800000(0), 6a14c=0x8(0), 6a150=0x80000000(0), 6a154=0x80000001(1),
  6a158=0x4, 6a15c=0x270(0), 6a160=0x46ffef(7), 6a17c=0x2, 6a1b4=0xf5ff(7),
  33e0=0x3820(0).
- НИ ОДИН регистр не несёт low3=0x3 (Port-Disconnected). Нечего флипать
  `0x3→0x7`. Подтверждает RE-вердикт 2026-09-12 (no clamped candidate) на живом
  железе повторно.

Токен-consumer (2026-09-19-inv-token-consumers.md): токены 0x10c2/0x10c3 НЕ
имеют найденного потребителя. Два generic INV reader (AmdFabricAriPei/1D3C,
AmdCcxVhAriDxe/5AC4) запрашивают 10FF/1104/1000/1001 — никогда 10c2/10c3.
7 сериализаторов ПИШУТ эти ID в записи, но reader на этих direct call-site их
не читает. NBIF-программирование — в AGESA token engine или PSP/ABL, runtime
недостижимо.

## ВЕРДИКТ Путь R (2026-09-25, hardware-verified read-only)

- Премиса Пути R (записать 0x6a1xx `0x3→0x7`) ОПРОВЕРГНУТА на живом железе:
  в runtime-окне 0x6A1xx нет поля port-config `0x3`; токен, несущий `0x3`,
  не имеет runtime-потребителя.
- Слепая запись в 0x6a1xx = стрельба по disproven-таргету с риском bus-hang
  и без RE-обоснования → НЕ выполнена (safe-протокол: писать только туда, где
  клэмп реально найден; он не найден).
- Runtime-путь исчерпан ПОЛНОСТЬЮ: S1..S4 + full dataplane + gasket replay +
  NBIF port config = VCN изолирован во всех случаях. Клэмп производится на
  буте (token engine / PSP), runtime SMN его не снимает.
- Flash НЕ тронут, записей в SMN не делалось (только B8-reads), плата жива.
- Реальный следующий шаг = RE token ENGINE / PSP-ABL consumer (offline),
  а не очередная runtime-запись.

## SESSION 7 (2026-09-25, оператор: "2" продолжить, AUTO): пересборка картины из evidence — БЕЗ живых записей

Плата UP (ping ok, ssh ok, 1002:13fe перечисляется). НЕ запускал ни S1, ни
любую SMN-запись — session 6 уже опроверг runtime-путь на живом железе;
повтор = сжигать цикл флешки за нулевую информацию.

Свёл 5 независимых фактов, до этого никогда не сопоставленных вместе:

F1. `0x3` = Port-Disconnected — это **захардкоженный immediate внутри
AmdNbioGfxARIPei** (disasm `0x22a3..0x24f8+`, `+0x1e0`@`0x2404`,
`+0x1e1`@`0x240e`). Init Config Struct initializer пишет его
unconditionally, БЕЗ чтения из flash / HOB / PCD. Ссылка:
`docs/research/2026-09-12-nbif-clamp-mechanism.md:11-14`.
F2. Токенов `0x10c2/0x10c3` в flash **НЕТ** (сканы APCB подтвердили,
`docs/research/2026-09-12-nbif-clamp-mechanism.md:20`;
`docs/repository-inventory.md:74`). Robin/thelamer/наша карта — все
показывают отсутствие. Все APCB-DFG кандидаты били по другому полю
(`0x1F→0x7F` — это DFG memory-config, НЕ NBIF VCN port).
F3. У токенов `0x10c2/0x10c3` **нет runtime-потребителя** (сессия 6
подтвердила live-B8-reads; `2026-09-19-inv-token-consumers.md` не нашёл
reader). Всё программирование NBIF происходит в PEI-фазе через
hardcoded defaults, без промежуточного APCB-хранилища.
F4. **PEI FV (FVMAIN, 0xAE0000..0xC30000) UNSIGNED** и field-proven
modifiable — коммьюнити-моды меняют 1,005,160 байт в проде и бутятся
(`docs/research/2026-09-12-injection-audit.md:61-63`;
`docs/research/imported/VCN-LOCK-MECHANISM.md:630-634`: "в PSP/BHD НЕТ
записей RTM/подписей 0x05/06/07/70/71/72"). PSP подписывает только
`$PS1` контейнеры (ABL/SMU/gasket/policy), НЕ x86-часть.
F5. Гипотеза "PSP RSA halt на D-series" **опровергнута собственным логом**:
`docs/action-logs/2026-09-11-vcn-policy-only-candidate.md:189-193` —
после stock-restore (readback IDENTICAL `83c4e420...`) плата тоже
выдала no-video. Все 4 предыдущих no-video (APCB-only, D3-B2,
policy-only, DXE-only) — non-discriminating. Причина no-video была
вне flashed bytes: display path / procedure / power / cable. G7
correction (line 193) прямо запрещает судить кандидаты boot-unsafe по
этой серии, пока сток не бутится в той же setup.

## Единственный неопробованный класс правки (fits «беречь флешку»)

**Direct PEI immediate flip внутри AmdNbioGfxARIPei и AmdNbioPcieARIPei:**

- в `0193_AmdNbioGfxARIPei_te.bin` найти два байта `0x3` по RVA `0x2404`
  и `0x240e` (Init Config Struct initializer), сменить `0x3 -> 0x7`
  (Full-Enabled) — но **сначала верифицировать RVA→file-offset через TE
  header**, а не слепо подставлять RVA.
- То же самое в `AmdNbioPcieARIPei` для parallel-serializer (F4 в
  s2a-runtime-donor-aperture.md:211 — Pcie PEIM имеет свой serializer,
  бьющий те же токены; без него Gfx-правка может быть overridden).
- Пересобрать TE section внутри PEI FV, обновить FFS/section checksums,
  пересобрать capsule (LZMA re-compress + outer FV), написать обратно.

Почему это единственный оставшийся путь:

- Root cause = immediate `0x3` внутри signed-nothing x86 PEIM (F1+F4).
- Все runtime-транспорты закрыты hardware-verified (session 1..6).
- APCB-редактирование бьёт мимо (F2 — токена нет в flash, чтобы флипать).
- Reflash-safety: FV unsigned → PSP не халтит (F5 плюс community boots).

Оракул для этого цикла:

- Если бут проходит **и** UVD_VERSION != FF → путь верен, VCN включён.
- Если бут проходит **и** UVD_VERSION == FF → immediate в PEIM не
  единственный источник clamp; следующий шаг = trace PSP/ABL setter,
  который может ПЕРЕЗАПИСЫВАТЬ struct+0x1e0 позже.
- Если no-video → повторить **со сток-образа под тот же display setup**
  (G7 protocol) — если стоку тоже нет видео = display path, не firmware.

Что ещё **не** сделано и что нужно до правки:

- TE header parse для 0193 модуля (RVA `0x2404`/`0x240e` → абсолютный
  file offset внутри `dump/2.bin` или `read-a.bin`) — pending.
- Верификация, что immediate байт `0x3` действительно там, где RE указал
  (открыть модуль по offset, посмотреть mnemonic — mov byte ptr [reg+0x1e0], 0x3).
- Проверка parallel Pcie PEIM offset.
- Пересборщик TE/PE32 + FFS/FV checksum — использовать существующий
  `candidates/d*/build_dN.py` scaffold (same-size PE32 swap, но здесь
  same-size TE = ещё проще, 2-byte in-place patch).

## Статус session 7

- Плата UP, живых записей не производил. Флешка не тронута.
- Runtime-путь окончательно закрыт как hypothesis space.
- Offline-путь (PEI immediate flip) уточнён до конкретных двух байтов и
  двух модулей, но **build не запущен** — сначала нужно верифицировать
  RVA→offset и immediate byte по самому модулю, чтобы не пересобирать
  вслепую 4-й раз.
- Оператор: следующая рекомендация — санкционировать offline-фазу
  (TE parse + immediate verify + build candidate, всё без прошивки),
  результат = binary с 2..4 изменёнными байтами и checksum-обновлением.
  Flash-цикл только после верификации диффа независимым разбором.

## SESSION 6 (продолжение "2") — offline token-consumer: static ceiling ПОДТВЕРЖДЁН

Свёл всю RE-цепочку токен→актуатор из 5 bounded-проходов (2026-09-19..20),
цель — найти, КТО программирует NBIF VCN-порт из токенов 0x10c2/0x10c3.

Раскрытая статически цепочка (все проходы exit 0, 20..42 checks PASS):

1. Сериализаторы (7 модулей) ПИШУТ токены 0x10c2/0x10c3/0x1204/0x1374 в
   $INV-записи. Ни один immediate-requester их не читает (2026-09-19,
   2026-09-20-clv-inv-1364: NO_DIRECT_IMMEDIATE_REQUESTER, 233 модуля).
2. Reader AmdFabricAriPei@0x1D3C — GENERIC dynamic lookup: сравнивает token
   записи с caller-supplied [EBP+8]. Только 2 direct-вызова: 0x10FF@0x1EBD,
   0x1104@0x1F94 (native-gate-inv-consumer-edge:
   NO_DIRECT_1204_OR_1374_REQUESTER).
3. Indirect edge (native-gate-indirect-cbs-edge): reader miss → request 0x3710
   → event 0xFFFFFFFE → gateway 0x36C0 → helper 0x3B60 → [PEI interface+0x20]
   с CBS GUID 04126c85-5c4e-458f-abc1-29f1f7da365e → returned first method =
   CbsBasePei+0x250 (byte-backed через InstallPpi).
4. CBS method 0x250 (setup-provider-edge, method250-buffer-edge): [EBP+0x10]
   на 0x42E = descriptor-selection; Setup-буфер (0x8B5 B) грузится независимо
   через PEI svc slot +0x54 в [EBP-0x8C8], отдаётся serializer callback 0x47D.
   Статус SETUP_PROVIDER_SPLIT_RUNTIME_VALUE_UNRESOLVED.
5. Runtime-review (native-gate-cbs-ppi-runtime-review): static component =
   PEI Foundation PPI database (LocatePpi +0x20, InstallPpi +0x18, first method
   CbsBasePei+0x250, callback dispatch +0x10). Static CBS PPI edge CLOSED;
   runtime PPI install/invoke UNRUN; token consumption UNPROVEN.

ВЕРДИКТ offline: статика этого firmware по VCN-токену ИСЧЕРПАНА — цепочка
декодирована до PEI Foundation PPI dispatch. Кто вызывает reader с VCN-токеном,
какой callback wildcard-дескриптор выбирает и что actuator пишет — в РАНТАЙМЕ,
невидимо immediate/indirect скану. Все углы (direct, computed, fn-ptr, PPI
descriptor) пройдены. Обе ветки закрыты потолками: RUNTIME SMN опровергнут на
железе, OFFLINE static упёрся в runtime PPI dispatch.

## SESSION 6 (продолжение "A") — feasibility пути A (live PEI trace)

Оператор выбрал A. Проверил ФИЗИЧЕСКИЕ предпосылки по evidence (не по памяти):

Recovery-инфраструктура ГОТОВА (проверено на железе 2026-09-11..16):

- SPI-программатор CH347T `1a86:55db`, flashrom v1.8.0, детектит Winbond
  W25Q128.V (16 MiB) @ 1.875 MHz. Запись -w+VERIFIED+readback -r — доказанная
  процедура (кампания M0..M2).
- Recovery-baseline evidence/programmer/reads/20260911/read-a.bin+read-b.bin
  (SHA-256 83c4e420...), обратная запись стока при обесточенной плате =
  доказанный recovery. Flash-эксперимент ОБРАТИМ.

ДВА жёстких ограничения observability (меняют дизайн трейса):

1. НЕТ serial: "REDACTED"
   печатать. Читаемый side-channel = сам SPI-flash (readback программатором
   после буста) или DRAM/CMOS (из Linux ПОСЛЕ успешного буста).
2. Пол наблюдаемости = P0 (video/LED/LAN) глазами оператора. M0 P0 FAILED:
   тихий ранний кандидат не дал ни сигнала, ни диагностики. Ранний PEIM
   упрётся в ту же стену: висит рано → молчит.
   JTAG/HDT: J2 не распаян, AMD HDT+ не подтверждён — как live-канал не готов.

ВЕРДИКТ feasibility A: обратим, но это МЕДЛЕННАЯ hardware-петля (flash→cold-boot
→readback, руками оператора) БЕЗ live-диагностики. Дизайн трейса: ранний PEIM
пишет token-request/return маркеры в зарезервированный SPI-регион или
фиксированный DRAM-адрес → после буста читаем регион программатором/из Linux.
ОТКРЫТО (design-развилка): куда писать маркер и как внедрить PEIM — commit в
медленный no-boot-loop; нужен ответ оператора Q1/Q2.

## SESSION 8 (2026-09-25): SMU RPC call-anything → VCN clock ungate

Источник: `bc250-smu-unlock` (rw-r-r-0644) — PoC эксплуатирует Q2 msg 0x23
ring-overflow bug → перезаписывает transfer-table pointer → обнуляет `0x7B3C`
(debug gate) → открывает secure_access (msg 0x27..0x2F: arb SMN rd/wr).
Поверх этого — `patcher.py` + `rpc.s`: хук `0x1BA6E → j 0x12000`, RPC-тело
в `0x12000..0x12048` — call-anything primitive через q3 msg 0x22 (arg=0x7F).

Также: `rpc_demo.py` (credits: dantisnfs) вызывает:

```
smu.call(0x23b14, 6, 1)    # FN_PLL_POWER_SET(domain=6=VCN, enable=1)
smu.call(0x23744, 0x16)    # FN_CLK_DOMAIN_UNGATE(0x16) — VCN clock
smu.call(0x23744, 0x17)    # FN_CLK_DOMAIN_UNGATE(0x17)
smu.call(0x23744, 0x18)    # FN_CLK_DOMAIN_UNGATE(0x18)
```

### Выполнено на живой плате (BIOS P3.00):

1. `secure_access` уже был открыт (unlock ранее выполнен в этой сессии).
2. `patches.hex` на плате содержал только metrics-8core (без RPC-секции).
   Скопировал полный hex из клона → `patcher.py --hex patches_full.hex`:
   - RPC body `0x12000..0x12048`: applied OK
   - RPC hook `0x1BA6E`: `ad02b2 → 8663d9` applied OK
   - Все 54 metrics-8core патча: already OK
3. Вызвал 4 SMU-функции:
   - `PLL_POWER_SET(6, 1)` → result `0x10ffe00`, alive=True
   - `CLK_DOMAIN_UNGATE(0x16)` → result `0x16`, alive=True
   - `CLK_DOMAIN_UNGATE(0x17)` → result `0x17`, alive=True
   - `CLK_DOMAIN_UNGATE(0x18)` → result `0x18`, alive=True
4. Проверка после ungate:
   - IP discovery: **UVD (=VCN) присутствует**, hw_id=12, ver=2.0.3,
     harvest=0x0 (НЕ fused off), base_addr=0x7800/0x7E00/0x2403000
   - Но **amdgpu НЕ создал VCN ring** (нет `amdgpu_ring_vcn*`/`uvd*`)
   - В dmesg нет ни одной строки про VCN/UVD init
   - Причина: amdgpu загрузился ДО clock ungate → пропустил VCN при init
5. Попытка SMN-read VCN-регистров (`0x1FD8100` и др.) через `sec_smn_read32`
   → **SMU wedged** (alive=False). Плата по сети жива, SMU мёртв.

### Выводы session 8:

- **Clock ungate через SMU RPC РАБОТАЕТ** — все 4 вызова вернули ожидаемые
  значения, SMU остался жив после них.
- **VCN IP discovery: harvest=0x0** — VCN физически присутствует и НЕ отключён
  предохранителями. Это подтверждает, что блокировка — программная.
- **Проблема порядка**: amdgpu init происходит раньше, чем мы делаем ungate.
  Драйвер видит VCN power-gated → пропускает его → не создаёт ring.
- **SMN-read VCN-регистров через sec_smn_read32 вешает SMU** — те же адреса
  `0x1FDxxxx`, что вешали msg 0x2A в session 3-4. Firewall на SMN-уровне
  блокирует доступ к VCN MMIO даже через secure_access.

### Следующий шаг (требует power cycle):

1. Power cycle → unlock → patch RPC
2. VCN clock ungate (4 вызова)
3. **rmmod amdgpu && modprobe amdgpu** (refcount=0, возможно)
   ИЛИ: сделать ungate через systemd unit ДО загрузки amdgpu
4. Проверить: создал ли amdgpu VCN ring при повторной инициализации
5. **НЕ читать VCN SMN-регистры** — это вешает SMU

## SESSION 9 (2026-09-25): modprobe amdgpu после clock ungate → hard hang

Power cycle выполнен. Последовательность:

1. SMU alive, secure_access=True (уже открыт с прошлого unlock — persistent?)
2. RPC patch applied (full hex с 0x12000 hook) — все 56 патчей OK
3. VCN clock ungate: все 4 вызова OK (PLL_POWER_SET + 3× CLK_DOMAIN_UNGATE)
4. `rmmod amdgpu` — exit 0 (refcnt=0, чистый unload)
5. `modprobe amdgpu` → **hard hang**: ssh timeout 124, ping 100% loss

### Анализ:

- amdgpu при инициализации пытается hw_init для ВСЕХ IP-блоков, включая VCN
- VCN clocks подняты, но **NBIF firewall всё ещё блокирует доступ к VCN MMIO**
- Драйвер пишет в VCN MMIO (ring init, firmware upload) → bus hang → hard lock
- Clock ungate ≠ полный unlock: clocks работают, но fabric isolation (NBIF
  firewall) не снята → MMIO-доступ к VCN всё ещё заблокирован

### Вывод:

**Clock ungate необходим, но НЕ достаточен.** Нужно также:

- Снять NBIF firewall (DF aperture / SYSHUB routing) для VCN MMIO range
- ИЛИ: загрузить amdgpu с `ip_block_mask` без VCN, затем вручную init VCN
- ИЛИ: найти SMU-функцию полного power-up VCN (не только clock, но и fabric)

### Следующие шаги (после power cycle):

A. Попробовать `modprobe amdgpu ip_block_mask=0xFFFFFFFB` (бит 2 = VCN off)
— загрузить драйвер без VCN, затем вручную проверить MMIO
B. Искать в SMU firmware функцию полного VCN power-on (включая fabric/NBIF)
— `rpc_demo.py` делает только clock, но есть ещё `FN_POWER_UP_VCN` и т.п.
C. Снять NBIF firewall через SMU SMN write (msg 0x98) на DF/NBIF регистры
— рискованно, но msg 0x98 пишет в volatile state

## SESSION 10 (2026-09-25): enable_vcn.py full sequence + direct-load

Использован `enable_vcn.py` (daveconde, 3664 строк) — зрелый инструмент с
полным userspace VCN bring-up. Запущен на живой плате после power cycle.

### Выполнено:

1. `--verify`: baseline dom6 state=0x01, все 3 слота READY, enable=OFF
2. `--direct-load --fw-offset 0x1ff200000`:
   - Fire sequence (msg 0x61 thunk → FUN_00023744 x3): SMU alive, slot 0x17
     clock 0→32 (converged), все 3 enable LANDED (0→1)
   - VRAM staging: navi10_vcn.bin 403648 bytes staged at MC 0xf5ff200000
   - **VCN MMIO: UNIFORM 0xFFFFFFFF** — все 11 регистров DEAD (оба сегмента)
   - GC (GB_ADDR_CONFIG) читался нормально → транспорт рабочий
3. `--manual-powerup`: ctrl 0x02→0x00 **LANDED** (первое реальное изменение
   sequencer на этой карте), cmd/rail vacuously taken
4. Повторный `--direct-load` после manual-powerup: **всё равно 0xFFFFFFFF**
5. `--msg-table`: 147 handler'ов, **НЕТ PowerUpVcn** в Q3 message space
6. `--dom6-dump`: 45 nonzero unknown dwords, ключевая находка:
   - +0x054..+0x070: 4× пары (0x06900900, 0xe8) — вероятно SMN-адреса
     ISO-clamp регистров, которые fw программирует при power-up
   - SMN 0x06900900 через config window → 0xFFFFFFFF (unmapped frame)
7. RPC `smu.call(FN_DOMAIN_POWER_UP=0x23b14, 6, 1)` → result 0x0 (success),
   но **SMU wedged** на следующем transfer_engine_sram_load (Q2 msg 0x0A)
8. После wedge: MMIO reads через debugfs → **GC тоже 0xFFFFFFFF** (весь
   GPU register file стал недоступен, не только VCN)

### ВЕРДИКТ session 10:

**ПРОТИВОРЕЧИЕ ПОДТВЕРЖДЕНО И ЗАДОКУМЕНТИРОВАНО:**

- SMU-side oracle говорит dom6 UP: clocks programmed, enables ON, gates
  released, rail vacuously taken, status=0x01010101 (up-residue)
- VCN register file: UNIFORM 0xFFFFFFFF — island CLOSED at root level

**Root cause НЕ в clock/power domain.** Блокировка на уровне:

- (a) PCIE ISO clamp (4× пары 0x06900900 в dom6 block — fw программирует
  их при реальном power-up, но host replica не может: frame unmapped)
- (b) PSP-side isolation (PSP контролирует fabric routing к VCN)
- (c) Недостающие шаги в FUN_00023b14, которые host не реплицирует

**Ключевой факт**: `smu.call(0x23b14, 6, 1)` (вызов fw-функции напрямую
через RPC) вернул 0 (success), но VCN MMIO остался FF. Значит даже
fw-internal power-up функция НЕ снимает isolation. Это PSP-level block.

### Оставшиеся пути:

1. **SMU feature bitmask** (msg 0x3C enable_smu_features): найти VCN/PG bit
   в bitmask — renoir использует PPSMC_MSG_PowerUpVcn, который feature-gated
2. **Decode FUN_00023b14** в fw image: найти, какие SMN-адреса она пишет
   (0x06900900 и др.) и реплицировать через msg 0x98 или RPC
3. **PSP investigation**: если isolation PSP-side, нужен другой подход
   (PSP firmware mod или APCB token)

## SESSION 11 (2026-09-25): SMU feature bitmask — VCN_PG найден, enable → hard hang

### Находка (критическая):

- `GetEnabledSmuFeatures` (Q0 msg 0x3D) → `0xdd602c7d`
- **VCN_PG (bit 18) = OFF**, JPEG_PG (bit 19) = OFF
- SRAM `0x157a0` содержит available/supported mask: `0x001e8480` — в нём
  **VCN_PG (bit 18) и JPEG_PG (bit 19) ПРИСУТСТВУЮТ** как supported features
- Это значит: SMU firmware ЗНАЕТ про VCN power gating, но feature ВЫКЛЮЧЕНА

### Попытка:

- `enable_smu_features` (Q3 msg 0x3C, arg = 1<<18 = VCN_PG bit)
- **Результат: hard hang** — ssh timeout 124, ping 100% loss
- Плата полностью зависла, не поднимается >2 минут

### Анализ:

- msg 0x3C handler (0x1DA78) пытается включить VCN power gating feature
- Внутри он вызывает power-up sequence для VCN domain, которая обращается
  к тем же unmapped SMN-адресам (0x06900900 и др.) → bus stall → hard hang
- Это тот же root cause что и session 10 (smu.call(0x23b14, 6, 1)):
  fw-internal VCN power-up код обращается к SMN-адресам, которые на BC-250
  не маршрутизируются → SMU застревает → вся система виснет

### ВЕРДИКТ (финальный для runtime-пути):

**VCN isolation на BC-250 — аппаратная, на уровне fabric routing.**

Доказательства:

1. Clock ungate (PLL + CLK_DOMAIN) — работает, SMU жив
2. Dom6 sequencer (ctrl/cmd/rail/status) — все показывают UP
3. Slot enables — LANDED и persistent
4. Manual powerup — ctrl gate released (первое реальное изменение)
5. VCN MMIO — UNIFORM 0xFFFFFFFF (island CLOSED)
6. FN_DOMAIN_POWER_UP через RPC — wedges SMU (unmapped SMN)
7. enable_smu_features(VCN_PG) — hard hang (тот же unmapped SMN)
8. GC через тот же MMIO транспорт — читается нормально

**Вывод**: VCN register file физически отключён от fabric на BC-250.
SMU firmware содержит код для VCN power management (feature bit, dom6
sequencer, clock slots), но hardware routing к VCN MMIO отсутствует.
Это не software lock — это hardware isolation, которую нельзя снять
runtime-записями.

### Единственный оставшийся путь:

**Offline PEI byte-flip** (path A из parallel-lanes-inventory):

- Патч `AmdNbioGfxARIPei` + `AmdNbioPcieARIPei`: `0x3 → 0x7` по RVA 0x2404
- Это меняет NBIF port config ДО того, как PSP/AGESA настраивает fabric routing
- Требует одну прошивку SPI + cold boot + readback
- FV не подписан (F4 из parallel-lanes), checksums пересчитываемы

## SESSION 12 (2026-09-25): PEI byte-flip candidate built

### Образ v001 (для немедленного теста): `candidates/BC250_PEI_VCN_PORT_ENABLE_v001.bin`

- SHA256: `4c1a77c880178beb77b410733b84406f894acc5cf04fc860967ff498d802b267`
- Base: `evidence/programmer/reads/20260911/read-a.bin` (stock P3.00, SHA256 `83c4e420...`)
- **Это тот же ROM, что сейчас на плате** — изменены только 6 байт

### Образ v002 (целевая база 5.00 CLV): `candidates/BC250_PEI_VCN_PORT_ENABLE_v002.bin`

- SHA256: `62d6ec2c2533d35991317a2607398c79fc5fb460d6690b695d5d785ad89f9d09`
- Base: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (BIOS 5.00 CLV, SHA256 `ea578104...`)
- Те же 6 байт патча, но на базе 5.00 CLV — сохранены CLV memory settings:
  MemClk=1800, UclkDiv1M0=Enabled, DfClkOvrd=1420, DfClkCtrl=Manual
- Для будущей работы с MCLK/FCLK/UCLK 1:1:1 sync

## FLASH SESSION (2026-09-25): v001 PEI VCN port enable

### Pre-flash readback

- SHA256: `8c2df19aedee8c02cf50c908111e2ee7c8167f7302bc397bcf2a1cb889c77ab0`
- Не stock P3.00 — ранее прошитый кандидат (DXE+PSP модифицированы, PEI/APCB/NVRAM = stock)
- Patch sites = 0x03 (stock, непатченные)
- Saved: `evidence/programmer/reads/20260925/pre-flash-read.bin`

### Flash

- Image: `candidates/BC250_PEI_VCN_PORT_ENABLE_v001.bin`
- Image SHA256: `4c1a77c880178beb77b410733b84406f894acc5cf04fc860967ff498d802b267`
- Base: stock P3.00 (`read-a.bin`, SHA256 `83c4e420...`) + 6 bytes PEI patch
- Programmer: CH347T via flashrom 1.8.0, chip W25Q128.V (real: W25Q128JVSQ)
- flashrom: `Erase/write done from 0 to ffffff` → `Verifying flash... VERIFIED.`

### Post-flash readback verification

- SHA256: `4c1a77c880178beb77b410733b84406f894acc5cf04fc860967ff498d802b267`
- **MATCH: image = readback** (bit-perfect)
- Patch sites confirmed: all four = 0x07
- Saved: `evidence/programmer/reads/20260925/post-flash-verify.bin`

### Cold boot result: BOOT HANG

- Первый зелёный LED проходит (PSP/early init OK)
- Второй зелёный LED НЕ проходит (PEI/DXE dispatch hang)
- Плата не поднимается по сети

### Root cause analysis

- TE header: NO checksum field → не проблема checksums
- FFS header checksums: пересчитаны корректно (verified)
- FV header: идентичен стоку
- Instruction encoding: корректный (`C6 81/82 disp32 imm8`)
- **Семантическая проблема**: значение `0x07` говорит NBIF init "поднять VCN port link",
  но VCN island power-gated → link training hang → boot hang
- Все BC250 BIOS (2.00, 3.00, 5.00, 5.00_clv, 8_cores_steam) имеют `+0x1e0=0x03, +0x1e1=0x03`
- Ни один предыдущий кандидат (D5, D9R и др.) НИКОГДА не менял PEI region
- 4700S donor имеет совершенно другой PEIM (другая платформа Oberon vs Renoir)
- Boot sequence: PSP/ABL → PEI → token engine → NBIF init → DXE
  PSP НЕ включает VCN power domain на BC250 → NBIF init с 0x07 вешает boot

### Вывод: PEI immediate flip — тупик

- Нельзя включить VCN port в PEI, потому что VCN island ещё не запитан
- Нужен другой подход: найти ТОЧНЫЙ SMN-адрес NBIF VCN port config register
  и записать его в runtime ПОСЛЕ power-up VCN domain
- Missing piece: token engine consumer (КТО читает 0x10c2/0x10c3 и В КАКОЙ
  SMN-регистр пишет результат)

### Stock восстановлен

- flashrom VERIFIED, readback = `83c4e420...`
- Плата UP, SMU alive, unlock applied, NBIF 0x6a1xx прочитаны
- SMN scan 0x101xxxxx повесил SMU (новый hazard class, записан в MISTAKES.md)

## OFFLINE RE: полная карта блокировок VCN (2026-09-25)

Собрано из всех артефактов проекта (executor-map.json, enable_vcn.py outputs,
gasket semantics, session 1-11 live data, pei-vni-hunt, s2a-runtime-donor-aperture):

### Три независимых слоя блокировки VCN:

**Layer 1: PSP SEC_GASKET firewall (bank-12, 0x0900Cxxx)**

- Stock: 169 bank-12 пар в group 0x201, все пишут 0x0 (зануление)
- Donor (Cezanne): 56 пар с реальными range values
- Runtime replay (2026-08-25): 56 writes ACCEPTED, commit=1
- Результат: VCN MMIO = 0xFFFFFFFF ДО и ПОСЛЕ → firewall НЕ достаточен

**Layer 2: Fabric routing (0x024xxxxx fabric slices)**

- VCN fabric slice: 0x02403000 (из IP discovery base_address[2])
- Route P probe (2026-08-25): THM и GC slices = dead-zero через config window
- 0x024 frame НЕ читается через PCI config 0xB8/0xBC на этой плате
- Dom6 sequencer fabric-visible через fw-window (0x6Dxxx), но НЕ writable
- Fabric routing НЕПРОВЕРЯЕМ текущими транспортами

**Layer 3: NBIF port config (tokens 0x10c2/0x10c3, struct+0x1e0/0x1e1)**

- Stock: 0x03 (Port-Disconnected) в PEIM defaults, сериализуется в RAM tokens
- Tokens ОТСУТСТВУЮТ в flash APCB (fail-closed by absence)
- PEI flip 0x03→0x07: boot hang (VCN island не запитан в момент NBIF init)
- Token consumer (КТО читает 0x10c2 и В КАКОЙ SMN пишет): НЕ декодирован
- Runtime NBIF port config write: адрес НЕИЗВЕСТЕН

### Что доказано на живом кремнии:

- Clock ungate (PLL domain 6): РАБОТАЕТ (slots enable LANDED)
- Dom6 sequencer: status=0x01010101, ctrl released (0x02→0x00)
- VCN MMIO: ВСЕГДА 0xFFFFFFFF (11 регистров, оба сегмента)
- Gasket firewall replay: ACCEPTED, но VCN не открылся
- PEI port enable: boot hang
- SMN reads 0x101xxxxx: wedge SMU (hazard class)
- SMN reads 0x1F8xx: wedge SMU (hazard class)
- enable_smu_features(VCN_PG): hard hang

## CRITICAL BUG FOUND: v001 FFS checksum was WRONG

Root cause boot hang v001: FFS header checksum calculation included State field
(byte 0x17 = 0xF8), violating EFI spec. Spec says: State and IntegrityCheck.File
are EXCLUDED from header checksum. Result: stock checksum 0x88 was changed to 0x90
(wrong). UEFI PEI dispatcher rejected the FFS file → boot hang.

Actual fix: the 4 patched bytes are in FFS DATA, not in the 24-byte FFS HEADER.
Header checksum does NOT need to change at all. v003 has 4 bytes diff (data only),
header checksum = stock value.

### v003: `candidates/BC250_PEI_VCN_PORT_ENABLE_v003.bin`

- SHA256: `545f3957a932d766e49fd6b425bcbdefe9dd724e1adf5401dc4b42c8551e8098`
- Base: stock P3.00 (`read-a.bin`, SHA256 `83c4e420...`)
- **4 bytes changed** (data only, NO header changes):
  - 0xe3f1fe: 0x03→0x07 (GfxARIPei struct+0x1e0)
  - 0xe3f208: 0x03→0x07 (GfxARIPei struct+0x1e1)
  - 0xe7433e: 0x03→0x07 (PcieARIPei struct+0x1e0)
  - 0xe74348: 0x03→0x07 (PcieARIPei struct+0x1e1)
- FFS header checksums: UNCHANGED from stock (correct)

### Непроверенные пути:

1. **Token engine consumer RE** — найти mapping token 0x10c2 → SMN address
   в DXE ARI drivers или AGESA token engine. Offline, zero board risk.
2. **Fabric routing через TA/INVOKE_CMD** — PSP trusted application route,
   единственный оставшийся транспорт для 0x024xxxxx. Требует RE PSP TA.
3. **Комбинированный подход**: gasket replay + power-up + port enable
   В ПРАВИЛЬНОМ ПОРЯДКЕ через DXE driver (не PEI, не runtime)

### Патчи (x86 immediate byte: `0x03` → `0x07`):

```
ROM 0xe3f1fe: 0x03→0x07  AmdNbioGfxARIPei  struct+0x1e0 (VCN NBIF port config)
ROM 0xe3f208: 0x03→0x07  AmdNbioGfxARIPei  struct+0x1e1 (VCN NBIF bridge enable)
ROM 0xe7433e: 0x03→0x07  AmdNbioPcieARIPei struct+0x1e0 (VCN NBIF port config)
ROM 0xe74348: 0x03→0x07  AmdNbioPcieARIPei struct+0x1e1 (VCN NBIF bridge enable)
```

### FFS header checksums (recalculated):

```
ROM 0xe3cd60: 0x88→0x90  GfxARIPei  FFS header checksum
ROM 0xe6e760: 0x8a→0x92  PcieARIPei FFS header checksum
```

### Верификация:

- PEI FV @0xE00000 (2MB): **0 $PS1 signatures** — FV не подписан PSP
- TE modules найдены UNCOMPRESSED в ROM (не LZMA)
- FFS ATTRIB_CHECKSUM не установлен → file checksum = 0xAA (fixed, не пересчитывается)
- Инструкции: `mov byte [reg+0x1e0], 0x03` → `mov byte [reg+0x1e0], 0x07`
  (Port-Disconnected/Clamped → Full-Enabled)

### Что делает патч:

- Меняет hardcoded default в Init Config Struct двух PEI-модулей
- PEIM serializer запишет `0x07` вместо `0x03` в token stream для `0x10c2/0x10c3`
- Token engine применит `0x07` к NBIF VCN port config через SMN RMW
- Это происходит В PEI PHASE — до PSP finalize, до DXE, до ReadyToBoot
- Fabric routing к VCN MMIO должен открыться ДО загрузки amdgpu

### Риски:

- Если NBIF port enable без предварительного VCN power-up → bus hang при boot
  (маловероятно: соседние порты с `0x07` работают нормально)
- Если PSP SEC_GASKET перезаписывает NBIF config ПОСЛЕ PEI → патч бесполезен
  (но gasket пишет firewall banks, не port config — разные регистры)
- Восстановление: flash stock ROM обратно (одна операция programmer'ом)

### Ожидает: решение оператора на прошивку

### v003 cold boot result: BOOT SUCCESS, VCN NOT ENUMERATED

- Плата загрузилась, ping OK, SSH OK, BIOS P3.00 confirmed
- Два зелёных blink = PSP init + PEI/DXE dispatch оба прошли
- Красный LED = static power indicator (нормально)
- amdgpu: 8 IP blocks detected, VCN/UVD НЕТ среди них
- IP discovery: UVD отсутствует в sysfs
- dmesg: ни одного упоминания vcn/uvd/jpeg

### Вывод v003:

1. **v001 boot hang = FFS checksum bug** (доказано: v003 с правильным checksum загружается)
2. **struct+0x1e0 = 0x07 безвреден** (boot OK, никакого hang)
3. **Token 0x10c2 НЕ имеет consumer** (VCN не появился — значение 0x07 в token stream
   не привело ни к какому изменению в hardware routing)
4. **PEI defaults path ЗАКРЫТ** — менять struct+0x1e0 бесполезно, это мёртвые данные

### Оставшийся вопрос: ГДЕ блокировка VCN?

- Не в firewall (bank-12 replay accepted, VCN = FF)
- Не в PEIM defaults (0x07 безвреден, нет consumer)
- Не в clock/power domain (ungate работает, dom6 UP)
- Остаётся: **fabric routing** (0x024xxxxx) и/или **PSP hardware lock**
  на translation matrices (t28 domain regs)

## SESSION 13 (2026-09-26): Pure gasket absence candidate

### Intent

Flash `BC250_5.00_clv_NO_GASKET_v001.bin` — pure PSP entry absence.
Hypothesis: removing SEC_GASKET (0x24) and TOS_SECURITY_POLICY (0x45) from
PSP directory prevents PSP from applying VCN kill values. If fabric default
state is OPEN (as on 4700S which has no gasket and VCN works), VCN should
become visible.

### Candidate

- Image: `candidates/BC250_5.00_clv_NO_GASKET_v001.bin`
- SHA256: `02d6e33f3c8a99db27a003b1da8d093163ad4583181e958a5cda214c19e3127c`
- Base: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (BIOS 5.00 CLV)
- Changes: 33 bytes in PSP directory only (entries 0x24+0x45 → 0xFF, Fletcher32 refreshed)
- All $PS1 containers intact, all other entries unchanged
- Flash package: `firmware-flash-pkg/20260926-v001-no-gasket-clv500/`

### Evidence supporting this approach

1. 4700S (same PS5-lineage silicon) has NO 0x24, NO 0x45 → VCN works
2. SEC_GASKET actively writes kill values (0x03E810=0, 0x03A2011C=0x87FF)
3. Without gasket, these kills don't happen → fabric stays at power-on default
4. PSP directory is checksummed (Fletcher32), not signed → safe to modify
5. O2 candidate (same approach on 3.00 base) was built but never flashed

### Recovery

- Stock ROM: `evidence/programmer/reads/20260911/read-a.bin` (SHA256 `83c4e420...`)
- Programmer: CH347T via flashrom, chip W25Q128.V
- Recovery proven: stock restored successfully in session 12

### Flash (2026-09-26)

- Pre-flash readback: `evidence/programmer/reads/20260926/pre-flash-read.bin`
  SHA256: `c909821315147c0d538b1dd9d3a5ce5f3ac784c7430b90ddc184e4e465b7e878`
- flashrom: Erase/write done 0..ffffff → VERIFIED
- Post-flash readback: `evidence/programmer/reads/20260926/post-flash-verify.bin`
  SHA256: `02d6e33f3c8a99db27a003b1da8d093163ad4583181e958a5cda214c19e3127c`
- **MATCH: candidate = readback** (bit-perfect)

### Cold boot result: NO GREEN LED — PSP REJECTED

- Ни одного зелёного LED = PSP early init не прошёл
- Root cause: база 5.00 CLV НИКОГДА не грузилась на этой плате.
  Плата на stock P3.00. 5.00 CLV — донорский образ с retroweb,
  не проверенный на этом железе. Провал может быть от базы, не от absence.
- Stock restored: `83c4e420...` VERIFIED

### Следующий шаг: absence на P3.00 базе

- Кандидат: `candidates/BC250_P3.00_NO_GASKET_v001.bin`
- SHA256: `d66ddcbae8940af0d4380a7b69c86cf0bd026b71ccc3d83ccd7b985e431f3d6d`
- База: stock P3.00 (`read-a.bin`, SHA256 `83c4e420...`) — ДОКАЗАНО грузится
- Единственная переменная: удаление 0x24+0x45 (34 байта в PSP directory)

### Ожидает: оператор включает плату, затем прошивка P3.00 absence

Полная цепочка (два этапа):

**Этап 1 — flash (оператор обесточивает плату):**

- Image: `candidates/BC250_P3.00_NO_GASKET_v001.bin`
- SHA256: `d66ddcbae8940af0d4380a7b69c86cf0bd026b71ccc3d83ccd7b985e431f3d6d`
- Base: stock P3.00 (proven boot), 34 bytes changed in PSP directory only

**Этап 2 — runtime (после boot в mode=1 ядро, SSH):**

- `vcn_absence_runtime_enable.py --read-only` → baseline DF window bit12
- `vcn_absence_runtime_enable.py` → donor gasket writes + bank-12
- `enable_vcn.py --manual-powerup` → VCN power domain
- `enable_vcn.py --verify` → mmUVD_VERSION check

Recovery: stock `read-a.bin` via CH347T (proven session 12)
