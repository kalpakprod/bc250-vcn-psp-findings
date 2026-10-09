# План: пройти второй gate VCN (goal-сессия 2026-09-25)

Goal (оператор): продвинуться дальше сообщества, изучить второй gate, пройти его;
финал — BIOS + скрипт, включающий блок кодирования, с полным пониманием.
Правило: перепроверять КАЖДОЕ утверждение (ошибка стоит лет).

## Что перепроверено первичными источниками (verified this session)

1. **VCN не выжжен (живое железо).** `ip_discovery/die/0/12/0/`: hw_id 12,
   ver 2.0.3, base 0x7800/0x7E00/0x02403000, **harvest=0x0**. SSH root на плате
   `root@127.0.0.1` (Debian `7.1.5-bc250r2`). Драйвер amdgpu VCN не
   регистрирует (UVD/VCE/VCN fw = 0x0). => замок программный.
   Источник: `docs/research/2026-09-25-live-vcn-harvest-ssh.md`.

2. **КОРРЕКЦИЯ (совпадает с подсказкой оператора «клоки — не то»):**
   `FUN_00023b14` по первичному декомпилу
   (`evidence/firmware-audit/20260919-zd/window_decomp.txt:~360`) —
   **applier статуса/уровня доменов**: читает status word (base+param5+0x200),
   пишет 3-бит (&7)->struct+0x98, 2-бит(bits17:16)->+0x99, затем цикл 27 записей
   (шаг 0x1c), для домена param_2 пишет 7-бит уровень (bits20:14)->+0x7e.
   НЕТ PGFSM-запроса питания. => Общинное «0x23b14(6,1) включает VCN power
   domain 6» описывает уровень/клок домена, НЕ питание видеоблока.
   Unlock-тул зовёт её `FN_PLL_POWER_SET`; старая заметка звала «domain power-up»
   — оба ярлыка телом НЕ подтверждаются. `0x23744`=`FN_CLK_DOMAIN_UNGATE`(слоты
   0x16-0x18) — клок-ungate, тоже не питание.

3. **Модель второго gate (из vcn2-bringup diff, 2026-09-23, перепроверяемо):**
   рабочая карта Navi10 делает pre-driver PSP-шаги, которых нет в OS-драйвере:
   cold-reset release `0x0900c004=1`, power-таблица, затем
   **U1 (MMHUB VM contexts ×2)** и **U2 (read `0x7fec`, clear bit0)**.
   Сообщество (rxl) сделало cold-reset + power-таблицу (`0x0902F9xx`), но НЕ U1/U2.
   Navi10 PowerUpVcn `0x233f0`: PGFSM tile 0xc request @ SMN (assumed 0x0900C784)
   + `[0x111f600+0x210] low2=2`. **BC-250 SMU этого не содержит** — значит эти шаги
   надо выполнить вручную через SMN-запись.

## НЕпроверенные допущения (ОБЯЗАТЕЛЬНО закрыть до любой записи)

- A1. SMN-маппинг `окно 0x1000000 -> SMN 0x09000000`, т.е. PGFSM req = `0x0900C784`.
  (`vcn-pg-probe.py` docstring: "Assumption (not verified)".)
- A2. `[0x111f600+0x210]` адрес/семантика на BC-250.
- A3. `0x7fec` идентичность (vcn2 diff §2: нерешено; байт-декод даёт UVD_UVBASE
  (неправдоподобно), функц-декод — UVD_POWER_STATUS (адрес не сходится)).
- A4. База VCN0 SMN и 5-таблицы (t28 `0x1F8xx` vs rxl `0x0902F9xx` — не сведены).
- A5. 20-бит лимит PMFW-записи (может не достать MMHUB/VCN-regfile).

## Инструменты на живой плате (T67, 24 сент)

- `/root/vcn-t67/bc250_smu/` — SMU-пакет (mailbox/transport/api_q0-q4/primitives/
  patches.hex). `/root/vcn-t67/vcn-pg-probe.py` — проба PGFSM (--read/--powerup).
  ВНИМАНИЕ: `--powerup` пишет в НЕпроверенный `0x0900C784` (класс возможного wedge).
- Проверенно-безопасный read-класс: Q3 0x2A `sec_smn_read32` для семейств
  0x0115F/0x0116D/0x01159/0x0005A/0x0000C (probe4l3/4l5).
- ЗАПРЕТ (measured SMU-killers): `0x01D80218`/`0x01D8` power island; `0x06900900`.

## Гейты и риски

- ЛЮБАЯ SMN-запись/непроверенное чтение может повесить плату (cold-cycle recovery).
  Плата удалённая — оператор физически рядом, готов к холодному циклу.
- Требуется явная per-action авторизация оператора (boundaries > goal).
- Порядок наименьшего риска: (1) закрыть A1 диагностическим READ PGFSM-регистра
  проверенным транспортом; (2) только затем взвешивать write-эксперимент.

## Definition of done (goal)

- BIOS-образ + скрипт, воспроизводимо включающие блок кодирования, с readback и
  cold-boot проверкой, и полным объяснением цепочки. НЕ заявлять «включил» без
  hardware-доказательства (VCN ring/декод/vainfo).

## Статус

Grounding + 1 первичная перепроверка сделаны. Следующий шаг — авторизованный
диагностический READ (закрыть A1), затем решение по write-эксперименту. Флеш и
любые записи — под гейтом.

## HARDWARE RESULTS (2026-09-25, operator authorized, at power button)

Transport: on-board /root/vcn-t67 bc250_smu, secure gate already OPEN, alive OK.
Read primitive: smn_read32 = Q3 0x2A sec read.

- **R1 «clocks are not clocks» — CONFIRMED on live silicon.** Descriptor idx22/23
  windows read 0x00000000: dclk_6d100=0, dclk_ack_6d114=0, vclk_6d128=0,
  vclk_ack_6d13c=0, sel_6d150=0. The prior hypothesis (probe4l6) that 0x0116D100
  holds a live DCLK ~1111 MHz value is FALSE — these are not frequency registers.
  domain_bitmap_ccb8=0 (VCN domain bit6 not set). VCN clock-controller block
  0x0115F800=0x0000000e, +0x808=0x02, +0x964(ready)=0.
  sanity 0x0005A870=0x000000ff.
- **R2 «0x0900Cxxx (RSMU) read wedges the SMU» — NEW.** smn_read32(0x0900C004)
  via Q3 0x2A -> SmuTimeout 'SMU wedged, cold cycle', alive_after=false. Linux
  still pings (only the SMU mailbox died). => A1 (0x0900C784) CANNOT be verified
  by a 0x2A read; rxl WROTE 0x0900C004 via a different primitive (fw-window/0x98),
  not a 0x2A read. Read-path != write-path for this aperture.
- CONSEQUENCE for the plan: verifying A1/A2 by reading them is a dead transport.
  A1 must be validated another way (static SMN-base proof, or a different read
  primitive), before any write. Do NOT read 0x0900Cxxx via 0x2A again.
- STATE: SMU mailbox WEDGED, needs cold power cycle to recover. Board OS up.

## HARDWARE EXECUTION — route-B host replay v1 (2026-09-25, operator at button)

FIRST host-side execution of the route-B replay (scripts/vcn_route_b_replay.py).
Board SURVIVED (ping OK, SMU alive; abort guards worked). ABORTED cleanly at step10.

- steps 2-6 (gate-mode 0x0115A3xx): already at target (A334=0x3F, A330=1, A32C=0x17).
- step 8: 0x0115F808 0x02->0x03 (enable bit) verified.
- step 9: write 0x0115F818=1 -> READBACK 0x00000000 (did NOT latch).
- step 10: poll 0x0115F964 bit0x100 (PLL ready) -> TIMEOUT -> abort.

VERDICT: route-B v1 WITH the v1-skips does NOT bring the PLL ready. 0x0115F818
trigger does not hold; ready never sets. => the skipped steps are NOT optional.
At least one of {step1 0x0220FE00 &= ~4 (gate release), step7 0x01D80814 |= 2
(0x01D8 region)} is a REQUIRED precondition for the trigger to latch. emu ran the
FULL sequence (incl. these) and the writes stuck; hardware without them fails here.

NEXT (gated, one variable): v2 = add back the least-risky skipped step first.
step1 (0x0220FE00) read-safety unproven; step7 (0x01D80814) is 0x01D8 region
(read-BAN / SMU-killer class for READS, but the bring-up WRITES it). Both are a
risk escalation beyond v1 -> needs a separate operator write-decision.
Gate STILL NOT passed. Board healthy.

## HARDWARE EXECUTION — route-B v2 (0x01D8 authorized) + step1 probe (2026-09-25)

- **v2 (with step7 0x01D80814=2, operator "да пиши")**: board SURVIVED the 0x01D8
  write. SAME abort as v1: step9 0x0115F818=1 -> readback 0; step10 PLL-ready
  (0x0115F964 bit0x100) TIMEOUT. => 0x01D8 enable was NOT the missing precondition.
- **Post-v2 0x0115F block diag (safe reads)**: f808=0x03 (enable HELD), f810 moved
  0x013C000D->0x013f0012 (block is live/reacting), f818=0 (trigger won't hold),
  f8fc/f920/f924/f948/f958/f95c/f964/f974=0 (steps 11+ never ran - abort at 10).
- **step1 (0x0220FE00 &= ~4) BLOCKED**: read of 0x0220FE00 via Q3 0x2A WEDGES the
  SMU (SmuTimeout, alive=false), same class as 0x0900Cxxx. Blind-write forbidden
  (artifact). => step1 unreachable by this transport. SMU wedged, cold cycle needed.

VERDICT: route-B v1/v2 (all SMN-reachable steps) do NOT wake the VCN PLL on
hardware. The two steps that MIGHT complete it - step1 (0x0220FE00 gate release)
and step24 (pump) - are blocked/too-risky: step1's read wedges, step24 is ~60
blind writes to unidentified blocks (0x01130600/0x01109A00/0x01C1CE00). This
REPRODUCES the wall the 2026-09-25 vcn-pg-probe session pivoted away from.
OPEN DOUBT (deep "clocks are not clocks"): is 0x0115F600 actually the VCN PLL
controller, or misattributed? PLL-ready never sets despite enable+0x01D8.
NEXT (needs decision, not blind writes): (a) re-verify 0x0115F600->VCN
attribution statically; (b) OR the pump as a bounded risk; (c) OR the
2026-09-25 manual-PGFSM branch. Gate NOT passed. Board OS healthy, SMU wedged.

## ROOT-CAUSE FOUND (2026-09-25): 0x0115F600 is GFX deep-sleep DFLL, NOT VCN

PRIMARY SOURCE (robin_5 known_messages / SMU-HANDLERS.md / SMU-FINDINGS.md):
- msg 0x19 = PPSMC_MSG_SetMinDeepSleepGfxclkFreq (handler 0x2b2b4)
- msg 0x1A = PPSMC_MSG_SetMaxDeepSleepDfllGfxDiv (handler 0x2b2f4) — deep-sleep DFLL divider
- There is NO "SetVcnClock" message anywhere in the firmware (grep of evidence/import
  returns it ONLY inside the 2026-09-24 plan-consumers notes = an invented label).
- emu-phase2: DAT_17204 = 0x0115F600; plan-consumers tied "power steps idx25/26" to
  FUN_00023AE0 "args 0x19/0x1A" and called 0x0115F600 the "VCN clock controller".

=> The block 0x0115F600 that route-B (v1/v2/v003b) writes is the GFX DEEP-SLEEP
DFLL clock controller (driven by msg 0x19/0x1A), MISATTRIBUTED as "VCN". Route-B
targets the WRONG block. This EXPLAINS every hardware failure this session
(PLL-ready 0x0115F964 never sets for VCN; f818 trigger of a GFX block does nothing
for VCN) and the v003b flash failure. This is the operator's "clocks are not
[VCN] clocks" warning, root-caused.

CONSEQUENCE: route-B / v003b is a DEAD END for VCN. Abandon it. Do NOT flash v003b.
The prior "SMU-side PowerUpVcn handler exists (FUN_0001fc50 @0x15220)" claim must be
RE-VERIFIED with the same skepticism (may also be mis-labelled). The real VCN control
is either the actual VCN IP block (ip_discovery base 0x7800/0x7E00/0x02403000) or a
genuinely VCN-named SMU path, neither confirmed. Gate NOT passed; but the multi-year
error is removed.

## ROOT-CAUSE part 2: "FUN_0001fc50 = PowerUpVcn" is ALSO a misattribution

Primary (evidence/firmware-audit/20260924-plan-consumers/dectail-out.txt):
- FUN_0001fc50 body: sets state-struct PTR_DAT_000171dc[1] |= 3; calls FUN_0002a184
  (= the tail that writes 0x0115F600, GFX deep-sleep DFLL); calls FUN_0001fea0(...,7)
  (component walk). NOTHING VCN-specific.
- FUN_0001fcec is a GENERIC power-state-transition dispatcher: walks pointer tables
  (PTR_PTR_0001752c/17530/17534/17538, 8 entries each), handshakes at +0x214/+0x208.
  Selected by state flags param_1/param_2, NOT a VCN message id.
- FUN_0002a184 is called from OC/scaling/DF-init contexts (actuator-pass11,
  scaling-consumers, sender-smu, df-init-route) - clock/DF machinery, not VCN.

=> "SMU-side PowerUpVcn handler exists @0x15220" is UNSUPPORTED - same misattribution
class as SetVcnClock. It is a GFX deep-sleep / clock power-state bring-up step.

## HONEST VERDICT (goal-session 2026-09-25)

- The ENTIRE SMU-side VCN approach (thelamer "domain 6 power-on", the "SetVcnClock"
  controller 0x0115F600, the "PowerUpVcn handler" FUN_0001fc50, route-B, v003b) is
  built on mislabeling GFX deep-sleep / DFLL clock machinery as VCN. Verified on
  hardware (route-B v1/v2 do not wake VCN) and in primary decompile/message-table.
- Consistent with the older project/community consensus the prior session had
  overturned: SMU 11.8 message set has NO VCN message. There is NO demonstrated
  SMU-side VCN power-up on BC-250.
- VCN is present (harvest=0), not fused. But no proven SOFTWARE path powers/
  un-isolates the island: SMU has no VCN message (this session), PSP rejects VCN fw
  (prior), direct VCN MMIO/SMN wedges (prior + this session's 0x0900C/0x0220 wedges).
- GATE NOT PASSED. Deliverable "enabled VCN + BIOS + script" NOT achieved and NOT
  achievable via the repo's approach. v003b must NOT be flashed (dead end).
- VALUE: removed a years-class false path (the SMU/route-B mirage), root-caused the
  operator's "clocks are not [VCN] clocks" hint with primary evidence.
- OPEN (genuinely unsolved): whether ANY software VCN path exists. Untested: the real
  VCN IP block via a non-wedging transport; a non-SMU/non-PSP mechanism. Not found here.

## VARIANT A closed (2026-09-25, operator "поднял", at button)
- 0x02403000 (VCN aperture base) via 0x2A = 0x00000000 (readable, not isolated-FF,
  but zero = not powered).
- 0x0007E010 (VCN register-file byte-addr) via 0x2A -> WEDGES SMU (unreachable,
  same class as 0x0900C/0x0220). Board OS alive.
=> The real VCN block is not reachable/powered via any safe transport. No surprise;
verdict holds. SMU wedged (cold cycle to use the board again).

## FINAL (goal-session 2026-09-25)
Gate NOT passed; VCN NOT enabled. Truthfully cannot claim otherwise.
DELIVERED (the operator's real ask - verify every claim, do not lose years):
- Root-caused the repo's central error: 0x0115F600="VCN clock controller" and
  FUN_0001fc50="PowerUpVcn handler" are MISATTRIBUTED GFX deep-sleep/DFLL machinery
  (msg 0x19/0x1A = SetMin/MaxDeepSleepGfx; no SetVcnClock / no VCN message exists).
  Primary-source + hardware confirmed. thelamer "domain 6 power-on / power not the
  blocker" rests on the same misattribution.
- route-B / v003b = DEAD END (do not flash v003b). Recorded in MISTAKES.md.
- VCN present (harvest=0), not fused; but NO demonstrated software power path:
  SMU has no VCN message; PSP rejects VCN fw; VCN reg-file wedges every transport.
OPEN (true unsolved problem, correctly framed): whether ANY software VCN path
exists on BC-250. Not found; the leading candidates are closed with evidence.
