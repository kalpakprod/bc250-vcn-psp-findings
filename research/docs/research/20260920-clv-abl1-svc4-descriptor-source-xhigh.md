# CLV ABL1 SVC#4 descriptor-table source and conditional R1 target

## Current

The exact FCLK path identifies the table index and target-construction rule, but does **not** prove a physical SMN register. Callback `R1=0x61E` becomes table index `0x61E`; callback reads `table[0x61E]`, extracts a nested index from bits `12..23`, then loads a descriptor. Kind-1 address construction combines the descriptor low 12 bits, base immediate `0x50000`, and the byte at `context+0x49`:

```text
for descriptor kind 1, descriptor bit30 == 0:
R4 = (descriptor & 0xFFF) | 0x50000
     | ((context_byte49 >> 1) << 20)
     | ((context_byte49 & 1) << 13)
```

`R1=R4` reaches the already verified SVC#4 wrappers at read callsite `0x9C28/0x9C2A` and write callsite `0x9D94/0x9D96`. The `context+0x49` byte is not a static constant at those sites: exact code `0x109D8..0x109E6` invokes `[context+0x3B0]` with an output slot, then stores the callback-returned byte to `[context+0x49]`.

## Exact table source boundary

The exact ABL1 function at `0xB228` supplies two paths for the table pointer later installed at `context+0x44`:

1. **Existing HEAP object:** it queries runtime HEAP key `0x01240000` through helper `0x6374`. On the existing-node path, the returned payload pointer at `[SP+0x18]` is stored to `[context+0x44]` at `0xB264/0xB266`.
2. **Fallback allocation:** on lookup miss it requests size `0x26C0`, same key `0x01240000`, item type `4` through `0x6238`; the returned pointer is stored to `[context+0x44]` at `0xB26A/0xB274`. The code then zeroes `0x652` dwords (`0..0x651`) at `0xB276..0xB280` before further fallback initialization.

The missing source is exact: **the producer/populator of a pre-existing runtime HEAP entry keyed by `0x01240000`, its returned table-body bytes, and active callback `context+0x49` output are not exposed by the bounded ABL1 bytes**. Helper `0x6374` is a consumer/lookup: it checks the `HEAP` signature at table pointer `0x73000`, walks linked nodes, compares node key against the input key, and returns body pointer/length in the request descriptor. That proves a heap indirection boundary, not where this key's node is populated.

### Raw fallback literals — retained as candidates, not promoted to table entries

The exact linear Thumb listing has code-like stores:

- `0xC7DE..0xC7E8`: `R0=R1+0x1878`; load literal at `0xC9F0` (`0x006D17C0`); store `[R0]`.
- `0xC79A..0xC7A0`: set `R2=0x1B44`; load literal at `0xC9D8` (`0x0800027C`); store `[R1+R2]`.

These are byte-backed pointer-relative stores in the initializer body. However, this bounded pass did not prove that their live `R1` at those distant initializer sites is the exact table base installed at context+`0x44`; `R1` is adjusted within the large initializer and the flat disassembly intermixes literal data. Therefore they remain **candidate initializer constants only**. If (and only if) table-base identity and the callback's active HEAP/fallback object are independently established, their offsets would correspond to candidate slots `0x61E` and `0x6D1`; the present report does not assert that binding.

Likewise, if the candidate descriptor `0x0800027C` were the active nested descriptor, kind bits `27..29` are `1`, bit `30` is `0`, low12 is `0x27C`, and the formula above would yield `R4=0x0005027C` when `context+0x49=0`. This is a **conditional calculation**, not an active-path register read or a physical-register identification.

## Exact inputs and base assumptions

- Exact ABL1 payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior FCLK R1 construction result reused by hash (not rerun): `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/svc4-r1-target-result.json`, SHA-256 `05fa26427c0d969a11d3779714089943d01421780beebbe8b62b910661eeecca` (`58/58 PASS`).
- ISA: little-endian Thumb-2. `$PS1` header `load_address=0`; offsets are payload-relative. No physical runtime base is assumed.

## Existing address-map correlation

The only applicable exact contract already proven is the ABL1 wrapper split: input `R1` becomes `(R1 >> 12) << 12` at `SVC #4`, while `R1 & 0xFFF` remains the access offset. For the conditional numeric example `R1=0x5027C`, the wrapper would request high page `0x50000` and use offset `0x27C`. The on-die SVC#4 handler/translation table is not in the extracted ABL1/TOS images. A bounded exact-string query over current `docs/research/`, `docs/action-logs/`, and `memory/` for `0x5027C` had no hit (`evidence/.../map-match-query.txt`, empty). No exact local SMN map establishes that this conditional value names a physical register; do not label it as such.

## Verification

New bounded verifier:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verify_descriptor_source.py \
  > /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verifier.stdout \
  2> /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verifier.stderr
```

Observed final status: exit `0`, `75/75 PASS`, stderr empty. The prior 58-check SVC4 R1 result was reused by hash only.

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verify_descriptor_source.py`.
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/descriptor-source-result.json`.
- Literal stdout/stderr: same directory, `verifier.stdout`, `verifier.stderr`.
- Map query: same directory, `map-match-query.txt` (empty; exact local report-text query only).
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-svc4-descriptor-source-xhigh.md`.
- Manifest: same evidence directory, `SHA256SUMS.final`.

Evidence class: observed bytes + static analysis only. No firmware, hardware, settings, source input, plan, memory, MCP/Cutter, global configuration, installation, candidate, or commit changed.

## Gate before any stronger claim

A future **read-only** runtime data capture requires explicit operator approval for the exact authorized capture path. It must capture whether `context+0x44` came from HEAP key `0x01240000` or fallback, the active table entries at index `0x61E` and its nested index, the `context+0x49` callback result (provider pointer `[context+0x3B0]`), and optional `context+0x2B0`. Do not write firmware or hardware as part of this capture. Correlating a physical register additionally requires the SVC#4 returned base or recovery of the PSP ROM handler/translation map.

## Supplemental exact SMN map correlation — conditional static match

Fresh bounded correlation corrects the earlier “no map hit” wording: the exact map report `docs/research/2026-09-20-oc-df-init-route.md` (SHA-256 `3122a0dce28bc61942a22d567acdc29e318a714097b48877eb0391094a7d0e43`) states that PMFW function `0x1EF18` sends `row+0x20` to address bases `0x5027C` and `0x5227C`, each plus `slot*0x100 + mask_bit*0x100000`, via helper `0x2A74(0,address,value,2)`. It qualifies these as static firmware-visible aperture addresses; physical clock/domain identity remains unverified.

The descriptor-source result retains the raw fallback constants as **candidate values**, not proven table slots: literal `0x006D17C0` is loaded by code at `0xC7E4` after forming `R1+0x1878`, and `0x0800027C` by code at `0xC79E` before a store through `R1+0x1B44`. This bounded pass does not bind those distant `R1` bases to the table body at `context+0x44`, and the active call may instead use an existing heap node from key `0x01240000`.

Conditional only: if `0x0800027C` is the active nested descriptor, it selects kind 1, low12 `0x27C`, bit30 clear. The exact kind-1 construction yields `R4=0x5027C` only for `context+0x49 == 0`; that base matches the exact SMU `row+0x20` map anchor. But `context+0x49` is dynamically stored from the callback at `[context+0x3B0]` (`0x109D8..0x109E6`), and active table-base identity is unresolved. Therefore this is a **conditional static address concordance**, not proof that the FCLK callback actually uses `0x5027C`, not a physical-register read, and not hardware evidence. The existing map's `mask_bit*0x100000` variation is not equated to the callback byte's full encoding.

Supplemental verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verify_map_candidate.py`; observed exit `0`, `18/18 PASS`, stderr empty. Literal output and machine result: `map-candidate.stdout`, `map-candidate.stderr`, and `map-candidate-result.json`. Query record: `map-match-query.txt` now contains the exact report hit, not an empty result. The existing 75-check descriptor-source verifier was not rerun in this supplemental comparison.
