# CLV ABL1 callback-table provider and target trace

Date: 2026-09-21  
Scope: offline static trace of the data-dependent `BLX R0` reached by the conditional local path in `2026-09-21-clock-independent-review-v2.md`. This trace covers only the callback-list initializer/provider, its populated record, and the direct `BLX R0` target. It does not revisit item-17 gate/alias mapping and does not follow the separate `memory_clock_units` `0x7FC2 -> 0x8428` / `0x10958` track.

## Conclusion

The indirect edge is locally populated by ABL1 code. In the selected static path, caller `0x1354` passes list base literal `0x6E27C` to provider `0x54FC`, then to enumerator `0x1332`. Provider `0x54FC` invokes record initializer `0x50C0`, writes descriptor pointer `0x6E284` to list element 0 and a null sentinel to list element 1. Initializer `0x50C0` populates the descriptor's first function-pointer field with `0x587B1`; enumerator `0x1332` loads this field and calls it with `BLX R0` at `0x133E`. The direct populated target is therefore the Thumb pointer `0x587B1`.

Under the prior **conditional**, not loader-verified, ABL1 base `0x57100`, the list, descriptor, and target map to payload RVAs `0x1717C`, `0x17184`, and `0x16B0` respectively. The code at conditional RVA `0x16B0` loads one byte through literal `0x6E131` and returns. This identifies the local static target path only; it does not identify the byte's semantic meaning or prove runtime execution.

## Bound input and format assumptions

- Source ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` (provenance inherited from the v2 verification metadata; the ROM was not re-parsed for this focused trace).
- ABL1 raw payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- ABL1 ELF wrapper: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o`, ELF32 little-endian ARM relocatable, SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`. Its `.data` bytes were confirmed byte-identical to the raw payload.
- Tool: local `llvm-objdump` 22.1.8. Focused windows used `--triple=thumbv7m-none-eabi` and explicit start/stop addresses. Raw data words were read little-endian at exact offsets; no whole-image search was performed for this trace.
- The prior review's `0x57100` base is carried only as a conditional mapping assumption. Runtime loader base and relocation state are unproven.

## Trace

1. **Caller supplies the list base.** In the existing checked caller window, `0x136C` loads `R5` from the literal at `0x141C`; raw bytes there decode little-endian to `0x0006E27C`. The caller passes `R5` to provider `0x54FC` at `0x1370`, then to enumerator `0x1332` at `0x1376`.
2. **List provider populates the list.** `0x54FC` preserves its incoming list pointer in `R4`, calls `0x50C0`, loads literal `0x0006E284` at `0x5510`, stores it at `[R4]`, stores zero at `[R4+4]`, and returns. Thus the list has one non-null descriptor pointer followed by a terminator.
3. **Record initializer populates function fields.** `0x50C0` loads descriptor address `0x0006E284` and stores four literal function-pointer values at offsets 0, 4, 8, and 12: `0x587B1`, `0x58659`, `0x5865D`, `0x58661`. These words are also present in the raw ABL1 payload at RVAs `0x17184..0x17193`; the list words at `0x1717C` and `0x17180` are `0x6E284` and `0`.
4. **Enumerator consumes exactly one list item for `BLX R0`.** At `0x1332`, `R6` receives the list pointer and `R4` starts at zero. `0x1346` reads `[R6 + R4*4]`; a zero ends the loop. For the first nonzero entry, `0x133C` loads `[R1]` into `R0` and `0x133E` executes `BLX R0`. Given the populated descriptor, that first callback is `0x587B1`. The next list word is zero, so no second list item is reached by this loop.
5. **Direct target body.** The Thumb pointer has bit 0 set. If (and only if) base `0x57100` applies, clearing the Thumb bit and subtracting the base maps it to payload RVA `0x16B0`. The bounded listing there is `LDR R0,[PC,#4]` at `0x16B0`, `LDRB R0,[R0]` at `0x16B2`, and `BX LR` at `0x16B4`. The literal at `0x16B8` is `0x6E131`. The target's byte read is observed; its object/meaning is not identified.

The descriptor also contains sibling pointer words `0x58659`, `0x5865D`, and `0x58661`. They are not the `[record]` target used by the specified `BLX R0` edge and were not followed; later distinct indirect sites are outside this bounded request.

## Verification

- Focused LLVM windows `0x1320..0x141F`, `0x54FC..0x557B`, `0x50C0..0x511F`, and `0x16B0..0x16B5` each exited `0` with empty stderr. Exact commands and literal outputs are retained in the evidence directory.
- Direct bounded little-endian extraction recorded list/literal words; `check_callback_targets.py` checked pinned input hashes, ELF/raw identity, table and descriptor values, conditional address arithmetic, decoded window mnemonics, and target bytes. Result: `PASS`, 33/33 checks, stderr empty, exit `0`.
- Evidence manifest: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-callback-targets/evidence-manifest.sha256`, 50 entries; final `sha256sum -c` exited `0`. Manifest SHA-256: `266a8593fc23053f36c79834e89aaed7fe6161e62a24e26e1eb66923583d8cc5`.
- Prior `verify_item17_gate_listing.py` covered the preceding selected branch and confirmed the `0x133E` indirect edge but expressly stopped with table pointer/targets unresolved; it was not repurposed as a callback verifier. The smallest follow-on was focused disassembly plus a local 33-check byte/window verifier.

## Limits and remaining uncertainty

- Evidence class: `observed-bytes` + `static-analysis` only. The selected path is the previously checked conditional path; this trace does not establish that the provider or callback executes at runtime.
- The loader base remains unproven; table and target RVA associations under `0x57100` are conditional coherence, not a relocation proof.
- No clock register, PLL, training, SVC handler, physical clock, or hardware behavior was established. The direct callback's byte read at `0x6E131` has no identified semantics.
- No hardware, ROM, NVRAM, register, network, or installation operation occurred. No changes were made to the pinned firmware inputs.
- An early wrong-input disassembly, an ARM-mode attempt, and a range-insensitive `llvm-objdump -s` full-section dump occurred during tool correction. They were not used for the conclusion and are retained with corrections in the action log/evidence directory; the broad section output is not evidence for this result.

Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-callback-table-targets.md`  
Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-callback-targets/`  
Evidence index: `VERIFICATION.txt`
