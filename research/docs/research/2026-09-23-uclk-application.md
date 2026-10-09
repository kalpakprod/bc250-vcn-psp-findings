# UclkDiv1: проверка применения на чистом CLV500

## Ответ на рабочий вопрос

Найденные обработчики `Override UclkDiv1 M0..M3` в ABL1, ABL3 и ABL4 не являются найденным включателем делителя. Исполненные ветви phase2 читают значение и выводят его в журнал. Изменение0/1 не вызвало записи в контекст настройки или аппаратного обращения на этих путях.

Это конкретный отрицательный результат по обработчикам, не доказательство невозможности1:1:1 и не доказательство полного отсутствия других потребителей. Связь AmdSetup+330 / INV1204 с APCB token21 всё ещё не установлена. Нельзя приписывать отрицательный результат всему BIOS-пункту только по одинаковому названию.

## Входы

- ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`: SHA256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.
- ABL1 SHA256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.
- ABL3 SHA256 3f5890b3a830725a11e169861fcfa208fa3f5fab37a38fc7f994a221a1f213be.
- ABL4 SHA256 1d60a34f1641204423024857249781d9184b2c9c5342f4dd8dbc070df6c5150b.
- ABL3/4 freshly extracted from exact ROM using retained PSP inventory container hashes, $PS1 header and zlib. No signed region modified. ABL2 extracted only to check corresponding string presence, not globally excluded as consumer.

## ABL1: реальные APCB-байты, нативный provider

Command: `tools/abl-emulator-venv/bin/python evidence/firmware-audit/20260923-uclk-application/verify_cases.py`

Original function2CA4 with phase2, native1FB4/4800/49CC and cache construction, actual APCB at modeled7B000. Gate20 reads APCB+86E; M0 token21 reads+86F (ROMAB186F). M1/M2/M3 at+870/+871/+872. Modification only in emulator memory, checksum+10 corrected. Context/data placement and logging hooks explicit model assumptions.

```text
BASELINE: M0_log=[1] context_writes=0 actuator_callbacks=0 services=0 returned=True
MODIFIED_M0: M0_log=[0] context_writes=0 actuator_callbacks=0 services=0 returned=True
RESTORED_M0: M0_log=[1] context_writes=0 actuator_callbacks=0 services=0 returned=True
AUTO_FF: M0_log=[] context_writes=0 actuator_callbacks=0 services=0 returned=True
GATE_OFF: M0_log=[] context_writes=0 actuator_callbacks=0 services=0 returned=True
PASS 5 native UclkDiv1 phase cases; no divider actuation on this path
```

Exit0, stderr empty. Hooks fail on actuator10958, assertion64C8 or any SVC. Native provider cache writes are permitted, context writes recorded. No whole-boot claim.

Initial AUTO_FF expectation was wrong: reader rejects all-ones, no log255. Failed assertion and exit1 preserved as attempt1.*. Corrected to exact empty-log assertion based on native rejection behavior, not a skipped test.

## ABL3/4: независимые копии ветки

Command: `tools/abl-emulator-venv/bin/python evidence/firmware-audit/20260923-uclk-application/later_phases.py`

ABL3 entry32B4, provider2634, logger1BE4, return4B30. ABL4 entry5CE4, provider2894, logger20F0, return7560. Here provider is deliberately modeled, unlike ABL1. Original caller code executes entry-to-return. All native writes must stay on modeled stack, all services fail closed. Returned0/1/1 produces corresponding four log values, no other writes, six cases pass. This confirms branch behavior, not loader/dispatch or actual hardware.

## Decision

Do not recommend `UclkDiv1M0=Enabled` as a proven1:1:1 recipe. Do not patch these log branches: no actuation follows. Do not patch early UCLK argument-halving at5F30 without physical-domain/service semantics.

Required next evidence is a real final UCLK divider/PLL consumer or independent register definition, not another read/log test. The earlier exactSMU PLL handler path and state-transition boundary remain open. SoC-first<=1.15V and BIOS-only goal unchanged. No OC candidate, STATIC-PASS or HARDWARE-PASS produced.

Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260923-uclk-application/`.
