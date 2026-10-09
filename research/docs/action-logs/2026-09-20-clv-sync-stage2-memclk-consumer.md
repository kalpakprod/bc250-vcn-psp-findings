# Stage 2 — Native MemoryClockSpeed consumer bounded audit

## Intent (before own evidence writes)

- Timestamp: 2026-09-20T10:42:00+05:00 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`, xhigh; effective runtime identity not independently exposed by this shell)
- Target: exact clv token `AmdSetup+0x316 -> INV record 0x11ED`; memory-init modules from the retained exact 233-module census: `AmdMemAm4Pei`, `PlatformMemoryConfigurationPei`, `AmdMemoryHobInfoPeim`.
- Scope: bounded actual-consumer check: test whether these native memory-init modules contain a direct token/Setup reader or whether the retained evidence ends at serializer/handoff. No broad corpus sweep, no guessed MHz/voltage, no writes.
- Expected effect: own evidence/result/report/action-log only; no ROM, firmware, candidate, hardware, settings, shared plan/memory, installation, commit, MCP, or child-agent changes.
- Rollback: delete only this evidence/report/action-log set.

## Observed result

Executed the bounded MemoryClockSpeed verifier. Exit `0`; stderr empty; `12/12` checks passed. The exact CBS serializer is confirmed; selected native memory-init module bodies have no direct `0x11ED` or `Setup+0x316` reader. The concrete next missing component is the AGESA/PSP/APOB/HOB consumer after INV handoff, not another token/label search. Own manifest check exited `0` with all files `OK`.

## Continuation intent — control-flow pivot

- Timestamp: 2026-09-20T11:05:00+05:00 (+05:00).
- Scope: stop repeating token no-hit scans; inspect complete entry/control flow of the 17-instruction `PlatformMemoryConfigurationPei` and the bounded `AmdMemAm4Pei` entry/helper chain to identify service arguments and PSP/APOB/BHD handoff structures.
- Expected result: concrete producer/consumer role or a precise closed-component boundary; no firmware/hardware/shared-state writes.

## Control-flow pivot observed result

Executed the full-entry control-flow verifier. Exit `0`; stderr empty; `27/27` checks passed.

- `PlatformMemoryConfigurationPei`: exact zero-return stub, no calls.
- `AmdMemAm4Pei`: entry `0x240 -> 0x876 -> 0x2F6`; helper path calls opaque service helpers and validates APOB/`$PSP`/`$BHD` magic/checksum structures; main path consumes protocol methods `+0x4C`/`+0x18`.
- No direct `AmdSetup+0x316`/MHz enum/training write appears in this bounded control path.

The missing component is now concrete: the opaque AGESA/PSP/APOB memory-init service behind the `AmdMemAm4Pei` protocol, not another direct token-literal scan. Own manifest check exited `0`; all listed files `OK`.

## Final control-flow pivot result

The follow-up control-flow verifier executed with exit `0`; `27/27` checks passed. It establishes:

- `PlatformMemoryConfigurationPei` is a zero-return/no-call stub (`xor eax,eax; ret`).
- `AmdMemAm4Pei` entry `0x240 -> 0x876 -> 0x2F6` invokes opaque protocol/service slots (`+0x4C`, `+0x18`) and validates APOB/`$PSP`/`$BHD` structures with checksum helpers.
- No direct MemoryClockSpeed enum or DRAM training write is exposed in this bounded path.

This replaces the earlier no-hit-only interpretation with a concrete service/structure boundary. Own manifest was regenerated and checked with all files `OK`.
