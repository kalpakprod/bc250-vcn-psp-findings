# Memory Clock enum-to-policy unit trace — intent

Timestamp: 2026-09-21T13:44:57+05:00 (Asia/Almaty)
Actor: project executor; bounded memory-clock-frequency unit/conversion track only.

## Bound target and scope

- TARGET: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, pinned 16 MiB CLV BIOS, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- GOAL: trace enum `AmdSetup+0x316 = 0x24` (IFR option `1800MHz`) through existing exact-CLV extracts to its numeric memory-speed policy value and the first downstream consumer boundary. Do not reopen the already-proven CbsBasePei serialization `0x11ED`; do not follow UCLK divider actuation or DF override consumption.
- Exact ABL1 extract already tied to this image: PSP type `0x31` at SPI `0x99FD00`; decompressed 94,624-byte payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing route: reuse `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1_producer_input_verify.py` plus its full exact-payload Thumb listing. It already checks the enum table and per-channel `+0x20` writer; it is insufficient for the requested downstream boundary because it stops before caller `0x7E34` dispatches ABL item `0x17` through the external/runtime provider table at `0xC60`.
- Minimal added test: check exact bytes/control flow from `0x7E30` through `0xC60` to the indirect provider-table call, including its pointer target and relation to payload length; do not infer physical MCLK, GDDR6 edge/data-rate, PLL acceptance, or hardware behavior.
- No board, network, firmware execution, ROM/NVRAM/register write, image patch, install, or source-tree change.

## Planned owned output

- Evidence: `evidence/firmware-audit/20260921-memory-clock-units-next/`
- Report: `docs/research/2026-09-21-memory-clock-units-next.md`
- This append-only action log: `docs/action-logs/2026-09-21-memory-clock-units-next.md`
- Expected outputs: copied verifier source, read-only symlink to the pinned existing Thumb listing, exact-boundary verifier, stdout/stderr/exit records, JSON result, selected string/byte evidence, final per-file hash manifest.
- Rollback: remove only these three owned paths; leave all existing files, the original BIOS, all other agent outputs, and shared worktree state untouched.

## Verifier correction after observed assertion error

The first verifier run exited `1` before writing a result because the expected raw slice for the literal at payload `0xC70` was off by one byte. The disassembly shows `0xC70: 9B01` (`ldr r3,[sp,#0x4]`), while the payload bytes at `0xC70` begin `01 9B 01 2B` because the function byte stream has the preceding halfword boundary at `0xC6E`. This is a verifier-offset error, not a firmware finding. Change only the expected slice to `b[0xC71:0xC75] == 9b01012b` (or use the semantic listing at `0xC70`), then rerun the same immutable input and retain the failed status/output.

## Second verifier correction after observed assertion error

The first correction still reversed a 16-bit Thumb display word. At payload `0xC70`, raw little-endian bytes are `01 9B 01 2B`, while LLVM displays `ldr r3,[sp,#0x4]` / `cmp r3,#1`. The corrected expectation is `b[0xC70:0xC74] == 019b012b`; no payload bytes or finding changed. Rerun the same verifier after this byte-order correction.

## G6 method change after three manual-anchor failures

Three consecutive new-verifier runs failed before producing a result, all due to manually transcribed offsets/byte order (provider item-count slice at `0xC70`, then its halfword-aligned raw slice, then the first byte of a mixed code/string region at `0x25D7`). All exits were `1`; the exact failure messages are retained in the conversation and summarized here. No input changed. Change method class now: stop asserting the manually written raw/string offsets. Reuse the already passing exact `abl1_producer_input_verify.py` as the byte-backed conversion/field test; for the added item-`0x17` boundary, assert decoded instruction semantics from the retained full-body Thumb listing and derive `0x24`'s TBB target from the exact input byte plus decoded TBB base. Locate the MHz-nomenclature strings by exact byte search rather than a handwritten offset. Do not follow the provider table further; stop at `0x0C60` so this deliverable does not overlap the separately owned APOB/ABL handoff track.

## Verifier source correction

The method-class verifier rewrite had one extra indentation level on its final `print` statement and exited `1` at Python parse time. This is a local verifier syntax error; the immutable payload and reuse route were not reached or changed. Remove that indentation only, then rerun.

## Scope and error-ledger clarification

The parallel APOB/ABL handoff analysis owns the provider implementation. This memory-clock deliverable stops at the exact ABL call-site `0x7E34`/`0x7E3A` (`0xC60`, operation `0x17`) and does not decode the provider table or its callback. `evidence/firmware-audit/20260921-memory-clock-units-next/verifier-failures.txt` preserves the observed test failures and the method change; the originally misaddressed string at `0x25D7` is superseded by content search and is not used as an instruction claim.

## Final verifier method intent (before rerun)

- The standalone checker is being rewritten cleanly after the indentation failures. It will call the existing 65-check producer verifier from a copied script and local evidence inputs, then add only these discriminating assertions: exact baseline byte `0x7E5=0x24`, IFR option value 36=`1800MHz`, TBB enum `0x24 -> payload 0x2318 -> literal 0x708`, the same outer context flowing through the per-channel `+0x20` policy writer/reducer, and the subsequent `0x7E3A -> 0x0C60` item-`0x17` service call. It will locate MHz strings by content, not fixed offsets.
- Stop at `0x0C60`; do not inspect the provider table or callback implementation (owned by the parallel APOB/ABL handoff track). This identifies the first missing consumer boundary for this frequency-input track without duplicate cross-track work.

## Evidence-schema correction after observed assertion error

The rewritten verifier reached the copied producer check and exited `1` on `KeyError: 'enum'`: the existing result's `enum_map` rows are keyed by `site`/`value`, not an `enum` input field. This is verifier-side schema misuse, not an analysis result. Remove the redundant enum-row lookup; the new check already derives enum `0x24` through the TBB index and selected instruction bytes/semantics. Rerun against the same pinned inputs.

## Tool invocation correction after observed pre-execution rejection

The attempt to remove the verifier's convenience symlink and re-run returned a tool-level `CreateProcess ... Rejected` error because `rm -f` commands are not permitted. The shell process did not start, so there is no shell exit status and no file was deleted. Keep the harmless symlink to the local listing copy, re-run the same verifier without a cleanup command, and record its actual process status.

## Observed result after write

- Exact verifier command: `python3 -B evidence/firmware-audit/20260921-memory-clock-units-next/memory_clock_units_next_verify.py`.
- Observed process exit: `0`; stdout is the JSON summary `{"status":"PASS","checks":38,"enum_0x24_policy_integer":1800,"first_missing_consumer":"0x7E3A -> 0x0C60 item 0x17"}`; stderr is empty.
- The checker reran the existing producer verifier from a private copy: exit `0`, status `PASS`, 65 checks. New checks add exact CLV IFR/hash identity, NVAR byte `ROM[0x7E5]=0x24`, TBB-derived enum path, exact MHz-tagged policy strings, context writer/reducer semantics, and the first opaque service call boundary. No serializer proof was repeated.
- Manifest command: `(cd evidence/firmware-audit/20260921-memory-clock-units-next && sha256sum -c SHA256SUMS.final)`; observed exit `0`; every listed entry `OK`.
- Final evidence hashes: `memory-clock-units-next-result.json` `7201a262fa4a97c9e5803e88682c4065fa7ecba647290f4628e586daf15d2a48`; `memory_clock_units_next_verify.py` `faa494e27030abf4949d35b12190d6f430226b2eb11d0bdc24c394c05ae28961`; `verifier.stdout` `ab730831930b284c1c00c67c49708885237e572f1c707fdeeb65edd05bd349da`; `verifier.stderr` `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; `SHA256SUMS.final` `6b863b4748374b393af99531c0021c1f73ad4c76298ffee0cef380a942f1102d`.
- Report readback before this append: `docs/research/2026-09-21-memory-clock-units-next.md` SHA-256 `4e318813e16035216aa48303d292422ca43d113ee91807fc97b8a61ee0ced33b`; evidence source hash matches pinned `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a` and ROM hash matches pinned `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.

## Final boundary and uncertainty

Observed static result: enum `0x24` -> policy integer `1800` with exact payload strings tagging memory-clock values as MHz; the selected value reaches channel `+0x20` writes/reduction and then `0x7E3A -> 0x0C60` item `0x17`. The first missing consumer for this track is the ABL runtime/provider operation behind `0x0C60`; the separate token-7-to-Setup/INV producer join is also missing. Physical MCLK/GDDR6 conversion, PLL/training behavior, hardware acceptance and synchronization remain unrun.

## Final artifact readback

- Report reopened: `docs/research/2026-09-21-memory-clock-units-next.md`, SHA-256 `4e318813e16035216aa48303d292422ca43d113ee91807fc97b8a61ee0ced33b`.
- Action log current SHA-256 after this append is recorded by the final shell readback.
- Evidence manifest re-created after the final verifier source/result update and checked: `(cd evidence/firmware-audit/20260921-memory-clock-units-next && sha256sum -c SHA256SUMS.final)` exit `0`, every listed file `OK`; manifest SHA-256 `6b863b4748374b393af99531c0021c1f73ad4c76298ffee0cef380a942f1102d`.
- Evidence result SHA-256 `7201a262fa4a97c9e5803e88682c4065fa7ecba647290f4628e586daf15d2a48`, status `PASS`, checks `38`.
- Pinned source readback remains exact: ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; ABL1 payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
