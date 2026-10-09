# CLV memory-clock enum to ABL1 policy-unit trace

## Conclusion

The exact BIOS 5.00 CLV ABL1 payload contains a static enum-to-policy-value mapping for a memory-clock configuration path. Enum `0x24` selects literal `0x708` (decimal 1800); the exact CLV IFR assigns enum `0x24` the label `1800MHz`, and the ABL payload's clock-policy strings explicitly label `MemClkFreq` and user memory-clock values in MHz. The resulting integer is stored in an ABL context, copied into per-channel memory-speed fields, reduced across channels, then passed to an unresolved ABL service item `0x17`.

This establishes the firmware **request/policy representation as an MHz-tagged integer**. It does **not** establish that this is a physical MCLK measurement, a GDDR6 data-rate/edge-rate, a PLL divider encoding, or the final training/clock programming value. Critically, the ABL getter is APCB/CBS token `7` at timepoint `2`; no direct byte-backed edge connects that getter to exact `AmdSetup+0x316` or `$INV 0x11ED`. The matching enum and menu label are cross-domain value agreement, not proof of that missing producer join.

## Pinned inputs

- ROM TARGET: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes; SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact decompressed ABL1: PSP type `0x31`, SPI container offset `0x99FD00`; 94,624 bytes; SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`. This is the same payload hash already recovered from the pinned ROM in the preceding ABL audit.
- Exact IFR evidence: `evidence/firmware-audit/20260920-df-init-route/menu-result.json`, SHA-256 `6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a`; QID `0x20F`, field `AmdSetup+0x316`, value `36` label `1800MHz`.
- Existing serializer result was reused, not re-proved here: `docs/research/2026-09-20-clv-sync-stage2-memclk-consumer.md` records `AmdSetup+0x316 -> $INV 0x11ED`. This report does not repeat that serialization proof.

## Enum-to-value conversion

The exact ABL selector at payload `0x2220` receives its configuration branch from caller `0x7DAE` (`r0=r4`, selector `r1=2`). Its non-override path calls `0x1F2C` at `0x2266`; the existing exact disassembly traces this through `0x47D0` to `0x49CC` with getter token `7`, timepoint `2`. The selector reads the returned byte, subtracts `2`, and dispatches a Thumb branch table at `0x2286`.

For enum `0x24`:

```text
TBB base       = payload 0x228A
index          = 0x24 - 2 = 34
entry byte     = payload[0x228A + 34] = 0x47
branch target  = 0x228A + 2*0x47 = 0x2318
instruction    = payload 0x2318: movw r0, #0x708
integer        = 0x708 = 1800 decimal
```

The common continuation at `0x22BA` stores `r0` to the configuration context's `+0x2C`. This selector sets mode `2` (`r6=2` at `0x2238`, stored at `0x2332`). Its caller continues with the same outer context pointer: `0x7E00` calls `0xAD58`; in its mode-2 branch, `0xADF8` loads context `+0x2C` into `r6`, and `0xAE22` writes the selected halfword to channel `+0x20`. `0x7E30` then calls `0x10CC0`, which reduces/clamps channel `+0x20` and writes the result back at `0x10E50`.

The ABL payload contains strings such as `MemClkFreq = %d MHz`, `User MemClk Setting: %dMHz`, and `Highest Common MemClkFreq for all channels: %d`. These name the firmware-side policy fields/limits in MHz; they are not a physical-counter readout. No multiplier or GDDR6 transfer-rate conversion is shown by this enum table. The table maps enum codes directly to integer policy constants (e.g., `0x24 -> 1800`), rather than calculating a clock from a divider.

## First missing consumer boundary

After per-channel reduction, the same ABL caller at `0x7E34..0x7E3A` loads `r0=[r4]`, passes item `0x17` in `r1`, passes context `r4` in `r2`, and calls `0x0C60`. That call is the first unresolved consumer boundary for this frequency-input path. This report intentionally stops there; the provider/consumer is owned by the parallel APOB/ABL handoff track. No local PLL/divider/training-register writer is established here.

The direct source-to-target gap occurs earlier as well: the exact ABL selector reads APCB/CBS token `7`; there is no proven edge from that token namespace to stored `AmdSetup+0x316`/INV `0x11ED`. Thus the observed ABL unit mapping is a valid static policy-path result, but it cannot yet be asserted to be the downstream conversion of this particular NVAR/INV byte.

## Checks and reproduction

Reproduction command:

```text
python3 -B evidence/firmware-audit/20260921-memory-clock-units-next/memory_clock_units_next_verify.py
```

Observed result: exit `0`, stderr empty, `38/38` checks passed. The checker reruns the existing exact-ABL1 producer verifier (`65/65`, exit `0`) and adds the TBB-derived `0x24 -> 0x2318 -> 0x708` discrimination, MHz-string presence, per-channel writer/reducer path, and the `0x7E3A -> 0x0C60` service boundary. Machine result: `evidence/firmware-audit/20260921-memory-clock-units-next/memory-clock-units-next-result.json`.

Check classification:

- **PASS — observed-bytes/static-analysis:** exact ROM/payload/listing/IFR hashes; current stored byte `ROM[0x7E5]=0x24`; exact menu option `36 -> 1800MHz`; ABL TBB path outputs `0x708`; per-channel policy writes/reducer; subsequent item `0x17` call.
- **INCONCLUSIVE:** whether the ABL token-7 value is sourced from `AmdSetup+0x316`/INV `0x11ED`; the actual operation behind service item `0x17`.
- **UNRUN/UNKNOWN:** memory-controller PLL encoding, physical MCLK, GDDR6 edge/data-rate conversion, WCK, training acceptance, hardware clock readback, synchronization, stability, and performance.

No ROM, NVRAM, firmware, candidate, register, board, or hardware state was changed. No safe frequency or voltage recommendation follows.
