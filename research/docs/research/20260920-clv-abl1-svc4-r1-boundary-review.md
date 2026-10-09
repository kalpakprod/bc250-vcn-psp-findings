# CLV ABL1 SVC#4 R1 report integrity and binding review

## Conclusion

The latest SVC#4 R1 report has a real **conditional callback path**, not a proven active FCLK-to-SVC#4 path. Exact raw bytes establish that the FCLK branch supplies `0x61E` to dispatcher `0x10958` as a callback selector/token; this is **not** the numeric SVC#4 target. Dispatcher `0x10958` loads a callback pointer from its current context `+0x660` and branches indirectly. A literal at `0xB168` conditionally maps to callback-body entry `0x9AD8` under the unproven base `0x57100`, and the candidate initializer stores it into its `parent+0x660`; however, the initializer's parent object is not byte-joined to the current `R4` passed by the FCLK branch. The static result for `0x9AD8`'s `R1=R4` helper input therefore applies **if that candidate is the active callback**, which remains unproven.

The callback `+0x44` table pointer is not a fixed table-base literal, but it is not merely an unexplained context field either: exact ABL1 code contains initializer function `0xB228`, which stores a helper-supplied pointer into `[R4+0x44]` along either a lookup-result path (`0xB266`) or fallback/helper path (`0xB274`). That proves an in-module **runtime pointer initialization mechanism**, not that this initializer ran for the active FCLK context. The table bytes and active lookup-versus-fallback selection remain runtime/context-dependent. This review does not recover or validate table entries and does not reuse the concurrent table worker's result as evidence.

## Pinned input and independent check

- Exact ABL1 decompressed payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
- Size: `94,624` bytes (`0x171A0`)
- SHA-256: `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Address convention: Thumb-2 payload-relative offsets; `$PS1` header `load_address=0`; no physical base is inferred.
- Independent reproduction: exact source bytes were wrapped with installed `llvm-objcopy` as a temporary ARM ELF in `/tmp`, disassembled at bounded addresses with fresh `llvm-objdump`, then exact byte slices were checked separately with a standard-library Python script. No prior verifier was run and no existing evidence outputs were rewritten.

Fresh exact disassembly and literal raw slices are preserved under:
`/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-boundary-review/`.
Machine check result: `.../boundary-review-result.json`; independent verifier: `.../verify_svc4_r1_boundary.py`.

## R1 is two different boundaries

### FCLK-to-dispatcher selector

Fresh disassembly and raw bytes at `0x107E8` are `40 f2 1e 61`, the Thumb encoding of `MOVW R1,#0x61E`. At `0x1081E`, bytes `20 46` pass current `R4` as dispatcher `R0`; the following call at `0x10820` targets `0x10958`. Dispatcher bytes show:

- `0x1095A`: load callback pointer `[R0+0x660]`;
- `0x1095E`: move caller `R2` (selected value) to callback `R3`;
- `0x10960`: move caller `R1` (`0x61E`) to callback `R2`;
- `0x10966`: set callback `R1=1`;
- `0x10968`: indirect branch through the loaded callback pointer.

Thus `0x61E` is an **indirect-dispatch token/index**, not the eventual SVC#4 address. Because the target is loaded and branched through dynamically, this callsite alone does not identify the callee.

### Candidate callback's helper argument

If the conditional callback body at `0x9AD8` is active, it sets `R5=R0`, preserves callback input `R3` in `R11`, extracts the low 12 bits of callback `R2`, loads a table base from `[R5+0x44]`, then indexes both an outer and nested descriptor. The candidate body selects descriptor kind bits `27..29` and combines descriptor/context values to form `R4`. At the normal read call, raw bytes at `0x9C28` are `21 46` (`MOV R1,R4`) and `0x9C2A` calls `0x6DA4`; at the write call, `0x9D94` is also `MOV R1,R4` and `0x9D96` calls `0x6E70`.

This establishes an exact **register-level R1 construction boundary inside the candidate function**. The conditional kind-1 arithmetic with `context+0x49=0` yields `R4=0x5027C`; the existing PMFW map report independently names `0x5027C`/`0x5227C` as row+0x20 aperture bases used by function `0x1EF18`. That is a conditional static address concordance only, not proof that the FCLK callback uses this descriptor or that the address is a physical clock register. It does not yield a numeric active FCLK target: the table slot, descriptor, `context+0x49` provider result and optional `context+0x2B0` value are dynamic; the callback binding itself is unproven. The helper's SVC#4 mapping semantics/physical destination remain separately unresolved.

## Callback binding is conditional, not established

The exact caller/initializer spans show different object roles:

- Function `0x7378` receives parent object in `R5` (`0x737C`), loads a child pointer candidate from `[R6+0x3C4]` into `R4` (`0x73AE`), and stores that child at `[R5+0x08]` (`0x73B2`).
- It later passes parent `R5` in `R0` to initializer `0xAF90` (`0x74DE..0x74E0`).
- `0xAF90` sets its base `R4=R0` and stores a static pointer literal `0x00060BD9` to `[R4+0x660]` at `0xB0C2..0xB0C4`. Under conditional base `0x57100`, that pointer maps to Thumb address `0x9AD9`, code entry `0x9AD8`. This is a conditional local-code pointer mapping, not a loader-base proof.
- The constructor later has an unresolved `BLX R1` at `0x74EA`; explicit `R4` add/subtract `0x2C0` operations also occur in the span.
- The FCLK branch at `0x1081E` passes its then-current `R4` to the dispatcher; identity with initializer parent `R5`, or with the separate `R4` child pointer, is not proven.

Therefore the active dispatcher lookup `[current context+0x660]` is byte-backed; the assertion that it equals `0x9AD8` is not. The latest R1 report should not narrate `callback 0x9AD8` as an unconditional established call target; use “candidate callback `0x9AD8`, if the current object's `+0x660` resolves to the conditional initializer slot.”

## `context+0x44` pointer-source boundary

Fresh independent disassembly of exact ABL1 at `0xB228..0xB280` shows a function that receives an object in `R0` (`0xB22E: MOV R4,R0`) and assigns its `+0x44` field from helper-result stack slots on two branches:

1. One helper path calls `0x6374` at `0xB23A`; branch `0xB23E` reaches `0xB264`, which loads `[SP+0x18]` and stores it to `[R4+0x44]` (`0xB266`).
2. The other path prepares/calls helper `0x6238` at `0xB252`; its zero-return branch reaches `0xB26A`, loads `[SP+0x0C]`, and stores that pointer to `[R4+0x44]` (`0xB274`). That branch zeroes `0x652` entries after assigning the pointer.

These exact instructions prove that the module contains code that initializes a context `+0x44` table pointer from dynamic helper outputs. They do **not** prove a statically embedded table-base pointer: neither `STR` writes an immediate literal, and the loaded bases come from stack outputs. Nor do they prove that `0xB228` initialized the same object consumed by the active FCLK dispatcher. The relation of this function's `R4` argument to the active dispatcher `R4`/initializer parent is outside the checked join. No table entry is decoded in this review; the minimal independent arithmetic check nevertheless confirms that `0x61E*4=0x1878`, raw literal `0x006D17C0` yields nested index `(value>>12)&0xFFF=0x6D1`, `0x6D1*4=0x1B44`, and raw nested descriptor `0x0800027C` has kind `1`, bit30 clear, low12 `0x27C`, field start `0x3C`, field end `9`.

A separate worker owns full descriptor-table discovery; this review deliberately did not decode table entries. Its result was first observed at SHA-256 `ef4f7cb0c56d0b4b7d6d2e80ef9a8bc9c3856c4b18adfa498981bb8e1fc6d93b` with status `FAIL`/`71 of 75`, then changed by its owner. Current readback at `2026-09-20 13:18:10+05:00` is result SHA-256 `14f71a9b17faa3b669681c574036ccb8edb3d75b7fde966a73aa0beb9dd9f7c0`, JSON status `PASS`/`75 of 75`. This review did not rerun, edit, or independently validate that worker's table-slot/descriptor result. Its result must remain attributed to its owner until root reopens the final artifact; this review only independently confirms the bounded `[R4+0x44]` pointer-store instructions at `0xB266/0xB274`.

## Corrected evidence boundary

- **Observed bytes/static analysis:** FCLK selects token `0x61E`; dispatcher loads a dynamic `[context+0x660]` callback pointer; a conditional initializer installs a pointer that maps to candidate `0x9AD8` under base `0x57100`; candidate function passes dynamic `R4` as helper `R1`; exact module contains a `+0x44` pointer initializer using helper-returned pointers; raw fallback arithmetic conditionally yields `0x5027C`, concordant with the separately analyzed SMU `row+0x20` aperture base.
- **Unresolved:** active callback identity; whether the live FCLK object is the object receiving either initializer; selection between existing lookup and allocation/fallback paths; runtime table contents; numeric active helper `R1`.
- **Unrun/unknown:** the active encoded descriptor and numeric helper `R1`, SVC#4 translation/mapped base, physical mapped window, PLL/clock effect, runtime execution and hardware behavior. This review does not infer that an encoded SMN target is impossible to recover without the handler; it simply does not establish the active descriptor or translation.

No firmware, ROM, settings, board, shared plan/memory, installations, or existing worker evidence artifacts were changed.
