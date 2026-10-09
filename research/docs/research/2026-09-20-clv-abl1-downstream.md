# CLV ABL1 `0x95FC` downstream boundary and concrete `+0x20` producer path

## Conclusion

The exact clv ABL1 Thumb-2 function at payload offset `0x95FC` has **no direct in-payload `BL`/`BLX` caller** in the fresh full-body Thumb disassembly. A bounded raw scan found no validated 32-bit pointer reference to `0x95FC`/`0x95FD`; the only candidate-base collision is `0x000606FD` at payload `0x17134`, retained as an unrelated ambiguity. The immediate invocation boundary therefore remains **indirect/runtime or outside this extracted ABL1 payload**, not a proven direct caller.

A concrete preceding producer path for the same per-channel structure field `+0x20` is nevertheless established in the exact payload. The callback slot is conditionally resolved below:

```text
0x7544 entry:  r5 = [r0+0x04]
0x757C:       [r5+0x60] = 0x0320          (halfword seed)
0x7586:       BL 0x75CC                  (original r0 preserved)
0x75E2:       r4 = [r6+0x04]             (same object as 0x7548 r5)
0x7E00:       BL 0xAD58(r4)
0xAE12..22:   callback [r4+0x52C](../../../references/DEPENDENCIES.md#unavailable-local-inputs); r0=[r4+0x0C]; [r0+0x20]=r6
0x109BC..A04: callback selects index and writes [r4+0x0C]
0x7E30:       BL 0x10CC0(r4)
0x10D40..E50: callback 0x109BC selects channel; read [channel+0x20]; [channel+0x20]=r7
```

Thus the field has an observed exact-payload writer chain before/around the memory-policy function: `0xAD58` writes a selected `r6`, and `0x10CC0` performs a channel reduction and writes `r7`. This does not prove that either path invokes `0x95FC`, nor does it prove units, MHz conversion, UCLK/FCLK semantics, training acceptance, runtime execution, or hardware behavior.

## Exact input and evidence

- Input: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
- Input SHA-256: `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Fresh ELF wrapper: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb.elf.o`
- Fresh Thumb listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-data-thumb-llvm.txt`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-producer-trace-result.json`
- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1_producer_trace_verify.py`

Verifier status: `PASS`, `32` checks. Result SHA-256: `a5dd7595ec4d07993120dbcd466be6619d3fcd60aff5a85e010bbd8de8c519a9`.

## Direct-caller boundary

Fresh disassembly command:

```text
llvm-objcopy -I binary -O elf32-littlearm -B arm \
  evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin \
  evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb.elf.o
llvm-objdump -D --section=.data --triple=thumbv7 \
  evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb.elf.o \
  > evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-data-thumb-llvm.txt
```

- `llvm-objcopy` exit: `0`.
- `llvm-objdump` exit: `0`; stderr empty.
- Direct `BL`/`BLX` target `0x95FC`: `0`.
- Searched raw little-endian pointer variants for the zero, `0x57100`, `0x60000`, `0x08000000`, and `0x006A0000` candidates. No validated `0x95FC`/`0x95FD` reference was found. The `0x57100` scan has one unrelated collision, candidate value `0x000606FD` at payload `0x17134`, which is retained as an ambiguity rather than a call edge.
- The static callback initializer at payload `0xB1F8` stores literal `0x00067ABD` from `0xB218`. Four independent literals map under candidate base `0x57100` to local Thumb code: `0xB218->0x109BC`, `0xB21C->0x10994`, `0xB220->0xAD18`, and `0xB224->0x10958`. Mapping confidence is high at the static-anchor level; the loader/base relation is not independently observed.
- Resolved callback `0x109BC`: it checks the index against `[context+0x4B]`, then computes and stores the selected channel pointer to `[context+0x0C]` at `0x10A04`. Therefore the exact `+0x20` input selector is concrete: `callback(context,index) -> context+0x0C -> channel+0x20`.

The initial direct raw-input invocation of `llvm-objdump` was invalid for this tool version and observed exit `1` (`The file was not recognized as a valid object file`). The changed, successful method wrapped the immutable raw payload as an ELF object; this tool error is retained in `docs/action-logs/2026-09-20-clv-abl1-downstream.md`.

## Concrete producer path

The exact Thumb instructions were independently checked at these payload offsets:

| Payload offset | Observed role                                                                       |
| -------------: | ----------------------------------------------------------------------------------- |
|       `0x7548` | `r5 = [r0+0x04]`                                                                    |
|       `0x757C` | `strh.w r0,[r5,#0x60]`; raw bytes `a5f86000`; value seeded at this path is `0x0320` |
|       `0x7586` | `BL 0x75CC` with the original entry object                                          |
|       `0x75E2` | `r4 = [r6+0x04]`, where `r6` is the original `0x75CC` argument                      |
|       `0x7E00` | `BL 0xAD58`                                                                         |
|       `0xAE12` | load callback `[r4+0x52C]`, conditionally mapped to `0x109BC`                       |
|       `0xAE1C` | `r0 = [r4+0x0C]`                                                                    |
|      `0x109BC` | callback entry; index validation                                                    |
|      `0x10A04` | callback stores selected channel pointer `[r4+0x0C]`                                |
|       `0xAE22` | `strh r6,[r0,#0x20]`                                                                |
|       `0x7E30` | `BL 0x10CC0`                                                                        |
|      `0x10D40` | `ldrh r0,[r0,#0x20]` during the reduction                                           |
|      `0x10E50` | `strh r7,[r0,#0x20]`                                                                |
|       `0xB1F8` | `str.w r1,[r0,#0x52C]` callback-slot initialization                                 |

Function `0xAD58` selects `r6` from exact local control/data paths (default `0x0320`, a `+0x2C` value in one mode, and bounded values from the surrounding state in other modes), then writes it to each selected channel's `+0x20` and mirrors it at `[r4+0x04]+0x2C`. Function `0x10CC0` reads the channel `+0x20` values, reduces them, and writes the selected result back to each channel `+0x20`. These are static dataflow findings only.

## G7 correction: callback-base mapping

The earlier wording that treated `0x00067ABD` as external because of a `0x60000` subtraction is withdrawn. Four independent pointer literals corroborate candidate base `0x57100` and resolve `+0x52C` to local callback `0x109BC`, whose exact dataflow writes the selected channel pointer at `context+0x0C`. The base is still conditional static evidence until the ABL loader relation is recovered.

## Remaining boundary and next discriminating check

- `0x95FC` immediate caller: unresolved at the exact ABL1 static layer because no direct call or local pointer target was found; the callback/provider address is absolute/runtime-bound.
- `+0x20` writer: concrete exact-payload path established above.
- `AmdSetup+0x316`/`$INV 0x11ED` to these ABL context fields: not established.
- Units, training actuator, clock-domain relation, execution, and hardware behavior: unrun/unresolved.

The next static check is to validate the loader/runtime base relation `0x57100` and identify the dispatch/entrypoint that invokes `0x95FC`; the callback implementation itself is now locally mapped with four independent anchors.

## Fresh producer-input trace: original speed selection before `0xAD58`

The exact ABL1 payload now provides a concrete upstream policy/source path, separate from the still-unresolved invocation of `0x95FC`.

### Direct override path (`0x2220` case 2)

- Context is `r4`; action parameter is preserved as `r7=r1`.
- Override enable: `[r4+0x331] != 0`.
- Override value: halfword `[r4+0x516]`, with `0xFFFF` as the disabled/sentinel value.
- If enabled, exact bytes write:
  - `[r4+0x04]+0x2C <- [r4+0x516]` at `0x2248`;
  - `[r4+0x04]+0x28 <- 2` at `0x224E`.
- The field is then consumed by `0xAD58`, whose mode-2 branch loads `[r4+0x04]+0x2C` into the selected value `r6`.

The override field is populated earlier by `0x77E2 -> 0x113FC(r0=0x72,r1=0x96) -> 0x77F4`, which stores the returned halfword to `[r4+0x516]`. `0x113FC` assembles two parameter bytes through `0x1145A -> 0x6AC0/0x6B14`. The bounded trace does not bind this transport to `AmdSetup+0x316` or `$INV 0x11ED`.

### APCB/CBS parameter path

When the explicit override is disabled, `0x2220` calls `0x1F2C` with `r0=7`, `r1=2`, and output pointers. `0x1F2C` calls `0x47D0`; `0x47D0` sets `r0=0xD` and calls `0x49CC` with token `7`, timepoint `2`, and the output pointer. Exact payload strings at `0x491D`, `0x4955`, and `0x4989` identify this local boundary as APCB/CBS/config-parameter retrieval:

- `APCB Config parameter %04x mapped to CBS token %04x`
- `Get config parameter: token %04x, timepoint %04x`
- `Get config parameter from default: token %04x, timepoint %04x`

The returned low-byte enum is mapped by exact current bytes to these numeric policy values:

```text
2->0x07D (125)   4->0x0E1 (225)   5->0x0FA (250)
8->0x190 (400)   9->0x1C2 (450)   A->0x1F4 (500)
F->0x2EE (750)   11->0x352 (850)  14->0x3E8 (1000)
19->0x4E2 (1250) 1A->0x532 (1330) 1B->0x55F (1375)
1E->0x5DC (1500) 20->0x640 (1600) 21->0x672 (1650)
22->0x6A4 (1700) 23->0x6D6 (1750) 24->0x708 (1800)
25->0x73A (1850) 28->0x7D0 (2000)
```

These are observed stored constants. The surrounding strings use MHz nomenclature, but no unit conversion or physical-clock identity is proven by this trace.

### Consumers and remaining boundary

- `0xAD58`: mode-2 `[r4+0x04]+0x2C`; otherwise default `0x0320`, special `[r4+0x04]+0x790 == 6 -> 0x01C2`, or mode-0 bound `min(0x0320, [[r4]+0x28]+0x770)`; writes selected `r6` to each `[r4+0x0C]+0x20`.
- `0x10CC0`: loads mode/speed pair `ldrd r9,r7,[[r4+0x04]+0x28]`, reduces selected channel `[r4+0x0C]+0x20` values, clamps `[r4+0x60]` downward when needed, and writes `[r4+0x0C]+0x20 <- [r4+0x60]`.

This establishes a concrete APCB/CBS-to-policy boundary and numeric input map, but not an `AmdSetup`/`INV` edge, units, training actuator, runtime execution, 1:1:1 synchronization, or hardware acceptance.

Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-producer-input-result.json`, verifier `65/65 PASS`.

## Getter namespace and IFR cross-bind

The exact current call arguments are now byte-backed:

```text
0x2220: r4 = context, r7 = action parameter r1
0x2264: r0 = 7
0x2266: BL 0x1F2C
0x1F2C -> 0x47D0
0x47D0: r0 = 0xD; r1 = 7; r2 = 2; r3 = output pointer
0x47EA: BL 0x49CC
```

Exact payload strings around `0x49CC` identify the local namespace as APCB/CBS/config-parameter retrieval, not `$INV` by name alone:

- `APCB Config parameter %04x mapped to CBS token %04x`
- `Get config parameter: token %04x, timepoint %04x`
- `Get config parameter from default: token %04x, timepoint %04x`

The exact clv APCB parser output has two raw CBSG (`gid 0x1707`) rows whose second byte is `7`:

| subgroup instance | APCB absolute row | raw tuple fields | u16 value |
| ----------------: | ----------------: | ---------------- | --------: |
|              `13` |        `0xAB1464` | `u8_0=1,u8_1=7`  |       `0` |
|              `15` |        `0xAB1710` | `u8_0=1,u8_1=7`  |      `97` |

This is raw parser-schema evidence; the row fields are not silently renamed to a stronger token schema. The bounded `0x49CC` trace does not establish which CBSG subgroup/timepoint branch supplies the returned enum.

The exact IFR `Memory Clock Speed` question is `QID 0x20F`, `AmdSetup+0x316`, with `22` non-Auto options. The ABL TBB table maps `20` enum codes to the same displayed values; codes `0x26` (`1900MHz`) and `0x27` (`1950MHz`) fall through the invalid/default branch and are not mapped by this ABL function.

Existing-default precedence remains separate and proven from the exact clv defaults result: stored `AmdSetup+0x316 = 36` (the IFR `1800MHz` option) wins on the successful existing-variable path; missing-variable fallback is `0xFF` (`Auto`). No direct APCB/CBS-token-7 → `AmdSetup+0x316`/`$INV 0x11ED` edge is established.

Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-getter-namespace-result.json`, verifier `27/27 PASS`.
