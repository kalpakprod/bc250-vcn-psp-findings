# CLV P-state precedence follow-up — exact ABL1 memory-policy override branch

## Conclusion

A fresh exact-CLV ABL1 disassembly adds one branch/precedence observation beyond the prior Setup/`$INV` serialization work:

- At ABL1 payload `0x9644/0x9646`, the value in local stack slot `[SP+0x164]` is compared with `1`; its producer/meaning is unknown. Values `<=1` bypass the multi-channel synchronization path to `0x9744 -> 0x984E`.
- For values `>1`, the stack value `[SP+0x174]` is tested at `0x964E/0x9650`; its producer/meaning is unknown. Zero branches to `0x9746 -> 0x9794`; nonzero enters the per-channel collection path beginning at `0x9652`.
- In the multi-channel path, channel memory-speed words are read from runtime structures at `[channel+0x20]` (`0x9672`), staged at context table `+0x278` (`0x9674`), and zero table entries are replaced by `0x7D1` (`0x96E4..0x96E8`). A candidate lower than the current minimum replaces it at `0x971E..0x9722`.
- The selected minimum is committed to context `+0x2BC` at `0x973E` and written back to every channel `[channel+0x20]` at `0x9758`.
- The alternate branch invokes helper `0x118C` (`0x97E4`) and helper `0x10C0` (`0x9800`), then commits a helper-produced value to context `+0x2BC` (`0x981E`) and writes it to each channel `[channel+0x20]` (`0x983C`). Their selection semantics remain opaque.
- The `<=1` path reads one table entry (`0x986E`) and stores it to context `+0x2BC` (`0x989A`); the bounded `0x984E..0x98A9` window has no `[channel+0x20]` write. This is a concrete condition under which the all-channel writeback override is not executed.

This establishes an ABL1 runtime-policy override/precedence shape, not a direct consumer link from native `AmdSetup` fields. The exact CLV baseline still stores `MemoryClockSpeed=0x24` (IFR label `1800`), `UclkDiv1M0=0x01`, `MemoryPstate=0xFF` (`Auto`), `FclkDpm=0x0F` (`Auto`), `DfClockOverrideControl=0x01`, and `DfClockOvrd=1420`; these are persisted bytes only. No physical 1800 rate, UCLK/FCLK ratio, 1:1:1 operation, training result, or hardware behavior follows.

## Exact inputs and provenance

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - size `16,777,216` bytes
  - SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact ABL1 payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin`
  - PSP type `0x31`, SPI container offset `0x99FD00`, container size `0xC020` (`49,184` bytes)
  - decompressed payload size `94,624` bytes
  - SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- PSP/ABL provenance inventory: `evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json`
- Fresh object: `evidence/firmware-audit/20260921-pstate-precedence-next/ABL1-exact.o`
  - SHA-256 `c4420d815773d9ee38a00923f5c8ab0b33095bdd714b4df41cb879193c581b6e`
- Fresh disassembly: `evidence/firmware-audit/20260921-pstate-precedence-next/abl1-policy-95fc-989e.txt`
  - SHA-256 `af1c864b86e4fdd07801f55197e4a2c0157b3033a4913bb88739a8c4c752be81`

The ABL1 payload is the exact CLV decompression artifact already used for the prior structural `0x95FC` memory-policy match. This follow-up does not repeat the prior serializer/token trace; it checks new control-flow and writeback windows in that payload.

## Reproduction

From project root:

```text
llvm-objcopy -I binary -O elf32-littlearm -B arm \
  evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin \
  evidence/firmware-audit/20260921-pstate-precedence-next/ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x95fc --stop-address=0x989e \
  evidence/firmware-audit/20260921-pstate-precedence-next/ABL1-exact.o \
  > evidence/firmware-audit/20260921-pstate-precedence-next/abl1-policy-95fc-989e.txt \
  2> evidence/firmware-audit/20260921-pstate-precedence-next/objdump.stderr
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  evidence/firmware-audit/20260921-pstate-precedence-next/pstate_precedence_verify.py \
  > evidence/firmware-audit/20260921-pstate-precedence-next/verifier.stdout \
  2> evidence/firmware-audit/20260921-pstate-precedence-next/verifier.stderr
```

Tool: `/usr/bin/llvm-objcopy` and `/usr/bin/llvm-objdump`, LLVM `22.1.8`. Observed final statuses:

```text
objcopy exit: 0
objdump exit: 0
verifier exit: 0
verifier stderr: 0 bytes
verifier stdout: {"checks": {"failed": 0, "passed": 47, "total": 47}, ... "status": "PASS"}
```

Machine result: `evidence/firmware-audit/20260921-pstate-precedence-next/pstate-precedence-result.json`. The verifier reopens the pinned input hashes, PSP/ABL identity, all selected instruction addresses, exact baseline Setup bytes, and the bounded negative on the single-state window.

## Static precedence map

| Condition / address                                   | Observed branch                                                    | Observed effect                                                                   | Status                     |
| ----------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------- | -------------------------- |
| `[SP+0x164] <= 1` @ `0x9644/0x9646`                   | `BLS 0x9744`, then `B 0x9794`/`0x984E` route                       | bypasses multi-channel gather/min/writeback                                       | **PASS, static**           |
| `[SP+0x164] > 1`, `[SP+0x174] == 0` @ `0x964E/0x9650` | `BEQ 0x9746`, then `B 0x9794`                                      | alternate helper/table path; helper output can become aggregate and channel value | **PASS, static**           |
| `[SP+0x164] > 1`, `[SP+0x174] != 0`                   | falls through `0x9652`                                             | collects all channel `+0x20` values                                               | **PASS, static**           |
| zero staged table entry @ `0x96E4..0x96E8`            | `CBNZ` skips substitute; zero loads `R9=0x7D1`                     | substitutes `0x7D1` before reduction                                              | **PASS, static**           |
| candidate `R2 >= R6` @ `0x971E/0x9720`                | `BHS 0x9724`                                                       | retains current minimum                                                           | **PASS, static**           |
| candidate `R2 < R6` @ `0x971E/0x9722`                 | `UXTH R6,R2`                                                       | lowers selected minimum                                                           | **PASS, static**           |
| selected multi-channel minimum                        | `STR.W R6,[R4,#0x2BC]` @ `0x973E`; `STRH R6,[R0,#0x20]` @ `0x9758` | aggregate + every channel receive selected value                                  | **PASS, static**           |
| single-state window `0x984E..0x98A9`                  | table read `0x986E`; aggregate write `0x989A`                      | no bounded channel `+0x20` write                                                  | **PASS, bounded negative** |

## Known versus unresolved precedence

### Known from exact bytes (observed/static)

1. The ABL1 memory-policy routine compares the value at stack slot `[SP+0x164]` with `1` before its multi-channel path; the slot is not semantically identified (`0x9644/0x9646`).
2. A zero/nonzero test of stack slot `[SP+0x174]` selects either the channel-gather route or an alternate helper/table route; this slot is not semantically identified (`0x964E/0x9650`).
3. The multi-channel route itself can override per-channel requests: zero entries become `0x7D1`, the minimum wins, and the minimum is written to all channel speed slots (`0x973E`, `0x9758`).
4. The alternate route has helper calls at `0x97E4` and `0x9800`; a helper-produced output is committed to the aggregate and all channel speed slots (`0x981E`, `0x983C`).
5. The single-state route commits a table value to the aggregate but does not write channel speed slots in the bounded window (`0x984E..0x98A9`).
6. The baseline native request bytes remain unchanged; the verifier read them directly from the pinned ROM.

### Unresolved (not promoted)

1. The meaning/producer of `[SP+0x164]` and `[SP+0x174]`, including whether either derives from APOB, `$INV`, APCB, AmdSetup, or runtime policy.
2. A direct byte-backed join from `AmdSetup+0x36D` (`MemoryPstate`) or `AmdSetup+0x6A3` (`FclkDpm`) to the ABL1 context or these stack fields.
3. Whether `FclkDpm`, UCLK divisor selection, DF override, and Memory P-state are read in ABL1, in PEI/AGESA before ABL1, or in another closed component.
4. Helper semantics at `0x118C`, `0x10C0`, `0x0DD4`, and the runtime object/data source behind the per-channel `[channel+0x20]` fields.
5. Whether the alternate route has priority over the minimum route at runtime for any concrete board configuration; only the branch conditions are known.
6. Whether `0x7D1` is a sentinel, a rate, or another internal unit; no MHz interpretation is assigned.
7. Any reset/default/migration behavior for an existing `AmdSetup` variable. Existing static evidence says the exact FCLK callback/default path is not runtime-executed, and live browser/reset/NVRAM readback remains unrun; this follow-up does not change that status.
8. Physical memory training, DF/UCLK/FCLK application, 1800 operation, 1:1:1 synchronization, voltage, performance, and hardware acceptance.

## Next discriminating test

The smallest next offline test is to trace the caller of ABL1 function `0x95FC` and the construction of its input object through the exact ABL1 payload, targeting the loads that populate `[SP+0x164]`, `[SP+0x174]`, and `context+0x3C4/+0x74`. Acceptance would be a byte-backed source classification for one gate (APOB/INV/APCB/AmdSetup/runtime object) and its ordering relative to the native `$INV` producer; a negative result should preserve the first unresolved caller boundary rather than repeat token scans.

The smallest hardware discriminant remains a controlled boot with baseline `MemoryClockSpeed=0x24` (1800-labelled request) and read-only capture of the runtime ABL/AGESA context or independent memory/DF/UCLK/FCLK counters before/after any native reset/default action. This is not run here: no board, NVRAM, register, ROM, or firmware write was performed.

## Evidence boundary

Evidence class: `observed-bytes` + `static-analysis`, host-tested verifier only. No firmware execution, QEMU/ARM emulation, hardware/register/NVRAM/ROM write, candidate build, network, installation, or physical clock measurement occurred. The requested 1800-labelled baseline is preserved as an input byte (`AmdSetup+0x316=0x24`), not claimed as an applied rate.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-pstate-precedence-next.md`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-pstate-precedence-next.md`
- Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-pstate-precedence-next/`
- Verifier: `pstate_precedence_verify.py`
- Machine result: `pstate-precedence-result.json`
- Literal stdout/stderr/exit: `verifier.stdout`, `verifier.stderr`, `verifier.exit`
- Fresh disassembly/object: `abl1-policy-95fc-989e.txt`, `ABL1-exact.o`
- Failure audit: `attempt1/` (formatting assertion failure, exit `1`, preserved before correction)
- Manifest: `SHA256SUMS.final`

Rollback is removal of only this report, matching action log, and uniquely named evidence directory; pinned donor and earlier evidence are unchanged.
