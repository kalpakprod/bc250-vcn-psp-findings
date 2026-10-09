# Resumed synchronization goal: blocked audit

Goal retained: all R1-R8 in `.procoder/specs/clv500-actuator-first.md`, cleanCLV500 BIOS candidate plus exact instruction, SoC first with actual<=1.15V, seek verifiedMCLK:UCLK:FCLK1:1:1 and lower latency. No scope reduction.

## Three-turn resumed audit

1. User continuation `жедай` interpreted as `делай`: completed native UclkDiv1 phase checks. Found read/log-only behavior in three ABL bodies under explicit models. End-to-end divider application, SoC setter and actual domain measurement remained absent.
2. Following automatic goal continuation: recomputed knownSMU addresses and opened primaryAMD register headers. No compatible identity established. Same blocker: missing applied-domain semantics and actualSoC control.
3. Current automatic continuation: tested register-pair alternative, searched coreboot/public code, opened AMDsmu8 headers. No matching implementation or definition recovered. Corrected overinterpretation of address mismatch. Same blocker persists. No new justified firmware edit or accepted BIOS recipe.

This is not an exhaustive proof of impossibility. The bounded avenues just executed no longer yield a discriminating experiment with an authoritative observable beyond the same model boundary. Another synthetic test or table recount will not establish the missing physical mapping.

## Acceptance status

- R1 base identity preserved, no ROM change.
- R2 actualSoC BIOS setter/units/readback NOT established.
- R3 final physical clock/divider semantics and latency result NOT established.
- R4 existing menu-only remains experimental, no justified main OC candidate.
- R5 main OC candidate STATIC-PASS absent. Native tests are not full-image acceptance.
- R6 HARDWARE-PASS NOT TESTED.
- R7 exact working BIOS recipe absent.
- R8 evidence distinctions retained, current offset inference corrected.

## What can unblock

A genuinely matching earlyPSP/clock-register implementation or independent runtime observation on the user's board. A baseline diagnostic stage is NOT permission to flash, raise clocks, change voltage or issue arbitrarySMU messages. Driver-level access needs separate approval under AGENTS.md. Even the retained `read_smu_reg` changes PCI selectorB8 and can race kernel users; do not call it write-free or risk-free. No hardware reader launched.

No fresh SPI dump or photograph is demanded as a condition for all future offline work. If a new source arrives, resume the full goal from these preserved results. Do not recreate candidates or repeat completed read/log/provider checks.
