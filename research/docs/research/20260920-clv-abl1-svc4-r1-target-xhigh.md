# Exact CLV ABL1 FCLK callback SVC#4 R1 target construction

## Current

The bounded exact-byte trace recovers one concrete descriptor-field target feeding the mapped SVC#4 access path:

```text
FCLK context field +0x78
  -> caller sets R1 = 0x61E at payload 0x107E8
  -> dispatcher 0x10958 loads callback [context+0x660]
     and presents callback R1=1, R2=0x61E, R3=selected value
  -> callback 0x9AD8:
       index = R2 & 0xFFF = 0x61E
       first_slot = ((uint32_t *)context[+0x44])[0x61E]
       nested_index = (first_slot >> 12) & 0xFFF
       descriptor = ((uint32_t *)context[+0x44])[nested_index]
       descriptor fields: bits 0..5, 6..11, 12..23, and bit 30
       R4 = descriptor/context-derived SMN selector (kind bits 27..29)
     -> read call:  R1=R4 at 0x9C28; BL 0x6DA4 at 0x9C2A
     -> write call: R1=R4 at 0x9D94; BL 0x6E70 at 0x9D96
```

This recovers the exact descriptor-field target and the construction boundary for the helper's `R1`; it does **not** recover a numeric physical SMN/MMIO address. The exact runtime table slot values, opaque on-die SVC#4 translation, loader/runtime base, and hardware effect remain unavailable.

## Exact inputs and base assumptions

- Exact ABL1 decompressed payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Historical structural source lead only: `/home/OWNER/orca/projects/bc250/archives/imported/recon-evidence/legacy-tmp-bc250-recon/lorek123_psp/ABL1_decompiled.c`, SHA-256 `9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b`.
- ISA: little-endian ARM Thumb-2. `$PS1` header `load_address=0`; all offsets above are payload-relative. No nonzero physical/runtime base is assumed, and the conditional `0x57100` mapping is not promoted to a loader proof.

## Address/value dataflow observed in exact bytes

### FCLK dispatcher argument construction

At `0x107E8`, exact Thumb bytes encode `MOVW R1,#0x61E`. The convergent FCLK path at `0x1081E` calls `0x10958` with `R0=context`; selected values are placed in `R2` immediately before the call.

Dispatcher `0x10958` is byte-backed:

- `0x1095A`: `LDR R4,[R0,#0x660]`;
- `0x1095E`: `MOV R3,R2` (selected value);
- `0x10960`: `MOV R2,R1` (`0x61E` token);
- `0x10966`: `MOVS R1,#1`;
- `0x10968`: `BX R12`.

Thus the callback receives `R1=1`, `R2=0x61E`, and `R3=branch-selected value`.

### Callback table and descriptor selection

At `0x9AE8`, the callback extracts `R2 & 0xFFF`; for this FCLK call the exact value is `0x61E`. At `0x9B18`, it loads the table pointer from `[R5+0x44]`; at `0x9B1C`, it loads `R6=table[index]`. The exact first target is therefore:

```text
first_slot = ((uint32_t *)(context + 0x44))[0x61E]
```

If that slot is nonzero and the ordinary `<0x652` path is taken, `0x9B2C` extracts `(first_slot >> 12) & 0xFFF`; `0x9B54` then loads:

```text
descriptor = ((uint32_t *)(context + 0x44))[((first_slot >> 12) & 0xFFF)]
```

The descriptor is decoded by exact instructions at `0x9B2C`, `0x9B32`, `0x9B36`, and `0x9B40` as fields bits `12..23`, `6..11`, `0..5`, and bit `30`. The callback also merges context `[R5+0x40]` fields into descriptor bits `15..19`, `20..27`, and `28..31` before forming `R4`.

### Constructed helper `R1`

For descriptor kind bits `27..29`, exact branches construct `R4` from descriptor low bits plus context byte `[R5+0x49]`; kind 1/2 additionally use `[R5+0x2B0]` in their optional paths, kind 3 adds `0x53000` and a shifted context byte, and kind 4 adds `0x1C000`. The normal mapped read passes that `R4` as `R1`:

- `0x9C22..0x9C2A`: word read setup, `MOV R1,R4`, `BL 0x6DA4`;
- `0x9D8A..0x9D96`: word write setup, `MOV R1,R4`, `BL 0x6E70`.

This is the requested exact `R1` address/value construction boundary. A numeric value cannot be substituted for `R4` without the runtime table slot and context bytes.

## SVC#4 mapping boundary

The existing exact wrapper evidence is independently re-opened by the new verifier:

- `0x6DCC`: `R0 = R6 >> 12`; `0x6DCE`: `R4 = R6 & 0xFFF`; `0x6DD2`: page-align `R0`; `0x6DD4`: `SVC #4`; `0x6DD8`: retain returned base in `R6`; `0x6E1A`: access `[R6+R4]`; `0x6DFC`: `SVC #5`.
- `0x6EA6..0x6EAE`: same high/low split and `SVC #4` for the write helper; `0x6EB2` retains returned base in `R5`; `0x6EE8` stores to `[R5+R6]`; `0x6ED6`: `SVC #5`.

This proves the caller-visible page-map/access shape, not the destination physical map.

## Verification

Command:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verify_svc4_r1_target.py \
  > /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verifier.stdout \
  2> /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verifier.stderr
```

Observed exit status `0`; stdout JSON status `PASS`, `58/58` checks; stderr empty.

Owned artifacts:

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verify_svc4_r1_target.py`, SHA-256 `0f535997b96061aec92e719633b6d3bfb8cbad91d27e0d6d0bd282c430da315e`.
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/svc4-r1-target-result.json`, SHA-256 `05fa26427c0d969a11d3779714089943d01421780beebbe8b62b910661eeecca`.
- Literal stdout: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verifier.stdout`, SHA-256 `4aed48b1cb889f0d367ca74790fdb204edfa446cef180b0f72a1e5fd6c8ea325`.
- Literal stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/verifier.stderr`, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-svc4-r1-target-xhigh.md`.

Evidence class: `observed-bytes` + `static-analysis` only.

## Limits and next decisive evidence

- Numeric `R1/R4` value for the active FCLK runtime invocation: unresolved because exact `[context+0x44][0x61E]` and nested table contents are runtime data, not fixed in the bounded callback slice.
- SVC#4 handler/translation destination: unavailable in extracted BIOS ABL1/TOS images.
- Physical SMN/MMIO register, bridge, PLL/clock domain, units, synchronization, runtime execution, and hardware acceptance: unrun/unproven.
- Decisive static/runtime evidence would be a PSP-ROM-level SVC#4 handler recovery or an authorized trace capturing `first_slot`, nested descriptor, constructed `R4`, and returned mapped base. No firmware or hardware write is proposed here.
