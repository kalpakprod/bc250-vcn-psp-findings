# Exact CLV ABL1 typed-reader output and downstream context trace

## Current

Exact CLV ABL1 payload and reviewed LLVM Thumb listing were reopened and hashed before a fresh, bounded verifier. The request was narrowed to one output destination/consumer edge: follow the Fclk typed result beyond reader `0x1FB4`; retain the UclkDiv1 output boundary only as a contrast. Known cross-channel minimum `0x95FC`, aggregate classifier `0x751C`, and conditional base `0x57100` loader proof were not used.

## Conclusion

The exact static dataflow reaches one concrete context field but does not establish frequency semantics:

- Reader `0x1FB4` preserves caller output pointer `R2` in `R6`. Its type-2 path executes `STRH R0,[R6]` at payload `0x2070`.
- UclkDiv1 M0..M3 caller slices use descriptor pairs `[0x20,0x21]` through `[0x20,0x24]`, pass output slot `SP+0x0C`, load the returned byte at `0x2D12/0x2D3A/0x2D62/0x2D8E`, and send it to the logger. No persistent context store is established in those four slices.
- Fclk constructs `[0x015F,0x0160]` at `0x464E..0x465E`, passes output slot `SP+0x08` into reader `0x1FB4` at `0x466A`, reloads the returned halfword at `0x467E`, and stores through the handler's caller pointer at `0x4682`.
- A direct caller at `0x7E74` invokes handler `0x5E68` with `R0=R4`. Inside that handler, output local `SP+0x04` is initialized to `0x4B0` at `0x5FA4`, passed to the Fclk handler at `0x5FAE`, reloaded at `0x5FB2`, and committed as a halfword to `[R5+0x78]` at `0x5FBA`. `R5` is the saved context argument from `R0` (`0x5E70`), so the destination is `context+0x78`.
- The same outer routine later passes the same `R4` context base at `0x8428` to `0x10200`. That routine copies `R0` to `R4` at `0x10208`; its reachable branch `0x104B2 -> 0x10592 -> 0x107DA` reaches the first identified downstream load `LDRH R0,[R4,#0x78]` at `0x107E4`, followed by comparisons against observed immediates `0x3E8` and `0x4B0` at `0x107EC` and `0x107F2`.

This is `observed-bytes` plus `static-analysis` only. The comparisons/branch constants are measured, but their units and meaning are unknown. There is no proof here of loader/runtime invocation, conditional base `0x57100`, MCLK/UCLK/FCLK equality, divider or PLL programming, memory training, synchronous crossing, physical clock state, or hardware behavior.

## Reproduction

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1_reader_output_context_verify.py
```

Observed stdout:

```json
{
  "status": "PASS",
  "checks": 59,
  "context_store": "0x5FBA [R5+0x78]",
  "first_downstream_load": "0x107E4 LDRH R0,[R4,#0x78]",
  "claim_boundary": "Static ABL1 dataflow only. The comparisons and selected branch constants are observed, but units, value meaning, loader/runtime invocation, MCLK-UCLK-FCLK equality, divider/PLL application, memory training, and physical clocks are not established. The conditional 0x57100 mapping is not used as loader proof."
}
```

Observed stderr: empty. Exit status: `0`. Fresh verifier checks: `59/59 PASS`.

## Exact inputs and hashes

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` — SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` — SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` — SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior reader boundary result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json` — SHA-256 `537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128`.
- Prior branch result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json` — SHA-256 `d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa`.

## Owned artifacts and hashes

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1_reader_output_context_verify.py` — SHA-256 `d20f722afed37fd5421beb7f0ee392626177cdc0a31c27dc85dce91ba3d1d061`.
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1-reader-output-context-result.json` — SHA-256 `6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21`.
- Literal stdout: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/verifier.stdout` — SHA-256 `65f66c16b03889df07fb329a1f1c694c1a87c278327e2cea71b54c26a0d77449`.
- Literal stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/verifier.stderr` — SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty).
- Prior failed verifier captures retained: `verifier-attempt-1.stdout`, `verifier-attempt-1.stderr`, `verifier-attempt-2.stdout`, `verifier-attempt-2.stderr` in the same directory.
- Path-scoped Procoder check log: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/procoder-check.log` — SHA-256 `564a7c90bcb8259f838547304d4c2d173cc121a6aaee14dfe8cca20ea8068afc`.
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-reader-output-context-xhigh.md`.

## Checks and limits

- PASS: exact ROM, ABL1, disassembly, and prior-result hashes.
- PASS: 59 raw-byte/listing/dataflow assertions.
- PASS: Python compile check and path-scoped Procoder formatting (`0 unformatted`, `0 unchecked`, `0 out of scope`; broad repository notices remain non-blocking).
- UNRUN: firmware execution, loader/base relocation proof, runtime invocation, hardware boot, physical clock readback, memory training, or any MCLK/UCLK/FCLK equality test.

No firmware, hardware, settings, shared plan, memory, install, MCP/Cutter, candidate, or source input changed. Rollback is removal of only this uniquely named evidence directory, this report, and its action log.
