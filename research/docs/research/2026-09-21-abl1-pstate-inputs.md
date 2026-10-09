# Exact CLV ABL1 P-state input/dataflow trace

## Conclusion

A fresh local producer trace tightens the previous conditional `0x95FC` branch map:

1. `0x95FC` allocates a local block at `SP+0x160` and calls `0x6C20` (`0x962A/0x962C`). `0x6C20` stores the return of `0x6D10` at block `+0x4` (`0x6C2A/0x6C2E`). `0x6D10` returns constant `1` (`0x6D1E/0x6D20`). Therefore, if this direct call returns normally, `[SP+0x164] == 1` and the `BLS 0x9744` at `0x9646` is taken. The multi-channel gather/minimum path is not entered on this local direct-call path.
2. The same `0x6C20` block prepares block `+0x14`, which is later observed as `[SP+0x174]`: helper `0x6CA0` returns `0` (`0x6CAE`), helper `0x6CD8` returns `0` (`0x6CE6`), and the `CBZ` at `0x6C46` reaches `0x6C54`, storing `1` at `0x6C4A`. This second gate is locally prepared as `1`, but the first constant gate prevents its consumer at `0x964E/0x9650` from being reached in this path.
3. The origin of the `channel+0x20` pointer is byte-backed. Callback `0x109BC` reads an index, optionally normalizes it through `[context+0x3B0]`, stores the normalized index at `context+0x49`, and computes:

   ```text
   context+0x0C = *(context+0x8 + 0x70) + 0x170 * normalized_index
   ```

   The `0x95FC` function then reads/writes `[context+0x0C]+0x20` at `0x9672`, `0x9758`, and `0x983C`.

This is a new ABL1-local caller/dataflow edge. It does **not** join `[SP+0x164]`, `[SP+0x174]`, or the channel table to native `MemoryPstate +0x36D`, `FclkDpm +0x6A3`, UCLK, DF, APOB, APCB, or `$INV`. Do not label these local fields as `MemoryPstate` or `FclkDpm`.

## Exact inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - size `16,777,216`
  - SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- ABL1 payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin`
  - size `94,624`
  - SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Existing exact object reused read-only: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`
  - SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`
  - derived from the exact payload; no object mutation
- Fresh windows: `evidence/firmware-audit/20260921-abl1-pstate-inputs/`
  - `caller-962a-9652.stdout`
  - `initializer-6c20-6d24.stdout`
  - `getter-6ca0-6cb2.stdout`
  - `getter-6cd8-6cea.stdout`
  - `returner-6d10-6d22.stdout`
  - `channel-pointer-109bc-10a2c.stdout`

The selected windows do not overlap the parallel APOB/APCB handoff analysis; they cover only ABL1-local helper and callback code.

## Reproduction

From project root, using `/usr/bin/llvm-objdump` LLVM `22.1.8`:

```text
llvm-objdump -D --triple=thumbv7 --start-address=0x962a --stop-address=0x9652 \
  evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o \
  > evidence/firmware-audit/20260921-abl1-pstate-inputs/caller-962a-9652.stdout
llvm-objdump -D --triple=thumbv7 --start-address=0x6c20 --stop-address=0x6d24 \
  evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o \
  > evidence/firmware-audit/20260921-abl1-pstate-inputs/initializer-6c20-6d24.stdout
llvm-objdump -D --triple=thumbv7 --start-address=0x6ca0 --stop-address=0x6cb2 \
  evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o \
  > evidence/firmware-audit/20260921-abl1-pstate-inputs/getter-6ca0-6cb2.stdout
llvm-objdump -D --triple=thumbv7 --start-address=0x6cd8 --stop-address=0x6cea \
  evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o \
  > evidence/firmware-audit/20260921-abl1-pstate-inputs/getter-6cd8-6cea.stdout
llvm-objdump -D --triple=thumbv7 --start-address=0x6d10 --stop-address=0x6d22 \
  evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o \
  > evidence/firmware-audit/20260921-abl1-pstate-inputs/returner-6d10-6d22.stdout
llvm-objdump -D --triple=thumbv7 --start-address=0x109bc --stop-address=0x10a2c \
  evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o \
  > evidence/firmware-audit/20260921-abl1-pstate-inputs/channel-pointer-109bc-10a2c.stdout
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  evidence/firmware-audit/20260921-abl1-pstate-inputs/abl1_pstate_inputs_verify.py \
  > evidence/firmware-audit/20260921-abl1-pstate-inputs/verifier.stdout \
  2> evidence/firmware-audit/20260921-abl1-pstate-inputs/verifier.stderr
```

Observed final execution:

```text
objdump windows: exit 0 (all six), stderr empty
verifier: exit 0
verifier stdout: status PASS, 54/54 checks
verifier stderr: empty
```

Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl1-pstate-inputs/abl1-pstate-inputs-result.json`.

## Exact dataflow edges

|                      Address | Observed bytes/control flow                                                  | Meaning at this boundary                                                            |
| ---------------------------: | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
|              `0x962A/0x962C` | `R0=SP+0x160`; `BL 0x6C20`                                                   | producer call for the local status block                                            |
|              `0x6C2A/0x6C2E` | `BL 0x6D10`; `STR R0,[R4,#4]`                                                | block `+0x4` receives helper return                                                 |
|              `0x6D1E/0x6D20` | `MOVS R0,#1`; `POP {R4,PC}`                                                  | helper `0x6D10` returns constant `1`                                                |
|              `0x963E/0x9646` | load `[SP+0x164]`; `CMP #1`; `BLS 0x9744`                                    | direct local call yields the bypass condition                                       |
|    `0x6C36/0x6C3A`, `0x6CE6` | block `+0xC` receives `0x6CD8` result; helper returns `0`                    | one input to `+0x14` flag construction                                              |
|    `0x6C3C/0x6C40`, `0x6CAE` | block `+0x10` receives `0x6CA0` result; helper returns `0`                   | second input to `+0x14` flag construction                                           |
|       `0x6C46/0x6C54/0x6C4A` | `CBZ [R4+0xC],0x6C54`; `MOVS R1,#1`; `STR [R4,#0x14]`                        | block `+0x14` becomes `1` on this local path                                        |
|              `0x9648/0x9650` | load `[SP+0x174]`; compare zero; `BEQ 0x9746`                                | second gate exists but is unreachable after first constant gate on this direct path |
|           `0x109C0..0x109E0` | count/index check; optional `BLX [context+0x3B0]`                            | normalized-index producer boundary                                                  |
|           `0x109F0..0x10A04` | load `[context+0x8]+0x70`; multiply index by `0x170`; store `[context+0x0C]` | exact origin of pointer later used as channel base                                  |
| `0x9672`, `0x9758`, `0x983C` | accesses `[context+0x0C]+0x20`                                               | consumer of the derived channel pointer                                             |

## Known and unresolved

### Known (observed bytes/static analysis)

- The first `0x95FC` gate is fed by a direct local initializer whose relevant helper returns constant `1`; no `MemoryPstate`/`FclkDpm` label is assigned.
- The second local block flag is prepared as `1`, but execution reaches it only after the first gate fails, which the direct helper path does not permit.
- `channel+0x20` is not an unexplained external pointer: `0x109BC` derives the channel pointer from a context-owned `+0x70` table using stride `0x170` per normalized index.
- The unchanged CLV baseline still reads `AmdSetup+0x316=0x24` (1800-labelled request), `+0x36D=0xFF`, and `+0x6A3=0x0F`.

### Unresolved (not promoted)

- The producer/meaning of `0x6D4C` and `0x6C5C`, and the caller/object that supplies the outer context to `0x95FC`.
- The source of the context `+0x8/+0x70` table and the optional callback at `+0x3B0`.
- Loader/base/runtime invocation of these payload-relative functions; the exact payload still has no direct in-body call to `0x95FC`.
- Any direct or indirect relationship to `MemoryPstate`, `FclkDpm`, `UclkDiv1M0`, DF override, `$INV`, APOB, APCB, or AmdSetup.
- Units, memory training, physical clocks, 1800 application, 1:1:1 synchronization, voltage, and hardware acceptance.

## Next discriminating test

Trace the caller/object construction that supplies the outer context to `0x95FC` and the context `+0x8/+0x70` table. The acceptance edge is a byte-backed source for that table or a concrete opaque boundary; only then can it be compared against the `$INV`/APOB paths without naming it as a native P-state field. No hardware action is needed for this next offline step.

## Evidence boundary

Evidence class: `observed-bytes` + `static-analysis`, host-tested verifier only. No ROM, NVRAM, register, hardware, firmware, candidate, network, installation, or shared-memory write occurred. Native 1800-labelled request was preserved.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-abl1-pstate-inputs.md`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-abl1-pstate-inputs.md`
- Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl1-pstate-inputs/`
- Verifier/result: `abl1_pstate_inputs_verify.py`, `abl1-pstate-inputs-result.json`
- Fresh windows: six `*.stdout` files listed above
- Failed-attempt audit: `attempt1/` through `attempt4/`
- Manifest: `SHA256SUMS.final`
