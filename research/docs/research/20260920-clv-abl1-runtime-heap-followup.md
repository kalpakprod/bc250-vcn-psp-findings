# Exact CLV ABL1 runtime HEAP consumer follow-up

## Result

The bounded static trace resolves one bridge after the prior `0xA04E`/`0x73000` lookup boundary, but does not find who populates the matching runtime node.

- Provider selector `0x0f` sets key `0xA04E` in descriptor `[SP+0x24]` and calls ABL1 `0x6374` (`0x4B1A..0x4B3A`).
- `0x6374` reads the table pointer literal `0x73000`, checks the `HEAP` sentinel and scans linked entries for key equality at node `+0`. On match it stores a payload pointer at descriptor `+8` (node `+0x10+metadata-byte`) and payload length at descriptor `+4` (node size minus metadata byte).
- ABL1 `0x63F8`, called at `0x6F78`, initializes the `HEAP`-tagged arena header at the same table base. This is header initialization only; this routine does not establish a populated entry with key `0xA04E`.
- After lookup success, the provider makes a second `0x6238` request with computed size `0x42B`, key `0xA04E`, and type `4`. The original `0x6374` body pointer at `[SP+0x2C]` is then used as an entry-vector base. Selected entry bytes are copied to an indirect destination buffer addressed by the pointer in `[SP+0x78]`; the separate `0x6238` return pointer is retained at `[SP+0x30]` and receives per-entry pointers.

Thus the first runtime result does feed a downstream byte-copy and heap-backed pointer-table construction path. The destination identity behind `[SP+0x78]` is not identified as a clock/configuration descriptor by the checked bytes. The linked node's producer in the checked chain and any APCB/CBSG-to-runtime-HEAP conversion remain **UNRESOLVED**. The pinned ROM contains no aligned 32-bit `0xA04E` or `0x73000` scalar. The existing APCB parser confirms the pinned APCB checksum/CBSG group only; it does not decode a mapping to this runtime key.

No frequency, MHz, voltage, 1:1, physical clock, training, runtime execution, or hardware claim follows.

## Reproduction and status

Input hashes reopened by the verifier:

- CLV ROM `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` — SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Decompressed ABL1 `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` — SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing full Thumb listing SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior runtime-heap boundary result SHA-256 `46a126825991b945716fe6cf52b4b68df5054304a16feac086067451a2dc5ce5`.
- Prior provider result SHA-256 `3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9`.

Existing APCB parser was executed read-only:

```text
python3 -B scripts/apcb_detail.py evidence/donor/retroweb-20260916/BC250_5.00_clv.bin --output evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/apcb-detail.json
```

Exit `0`; literal stdout is retained in `apcb-parser.stdout` (`images: 1`, `failed: false`); stderr empty. Parsed APCB offset `0xAB1000`, size `2972`, checksum match true, CBSG group `0x1707` present (two subgroups).

The exact ABL1 object was disassembled narrowly with LLVM 22.1.8. Commands and captured output are under the evidence directory; all disassembly rows used by the verifier are reconciled mechanically against source bytes.

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1_runtime_heap_followup_verify.py
```

Final observed result: exit `0`, stdout `PASS`, `90` checks; stderr empty. Evidence class: `observed-bytes`, `static-analysis`. The verifier also reopens exact ROM/ABL1 and prior-result hashes, the fresh APCB parser result, focused disassembly, HEAP initializer/header and call site.

## Artifacts

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1_runtime_heap_followup_verify.py`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1-runtime-heap-followup-result.json`
- Literal verifier stdout/stderr/exit: same directory, `verifier.stdout`, `verifier.stderr`, `verifier.exit`
- Fresh APCB parser JSON/stdout/stderr/exit: same directory, `apcb-detail.json`, `apcb-parser.stdout`, `apcb-parser.stderr`, `apcb-parser.exit`
- Narrow disassembly stdout/stderr/exit: same directory, `abl1-window-disasm.*`, `abl1-lookup-window-disasm.*`, `abl1-init-window-disasm.*`, `abl1-init-call-disasm.*`, `abl1-pointer-tail-disasm.*`
- Append-only action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-runtime-heap-followup.md`

No firmware, hardware, settings, project plan, shared memory, installation, global configuration, MCP/Cutter state, candidate, source input, or repository commit changed. Static closure is partial: producer/population of the runtime `0xA04E` node in the checked chain and identity of the indirect output destination remain open.
