# Exact CLV ABL1 descriptor-array/provider review

## Conclusion

The raw ABL1 bytes encode **ordered token-candidate arrays terminated by zero**, not a two-field `(prefix, key)` descriptor. The shared reader at payload `0x1FB4` calls `0x4800` with the current halfword token, advances only after a failed lookup, and stops at the zero terminator. Thus each UclkDiv1 request first tries token `0x20` and then the case-specific alternative `0x21`, `0x22`, `0x23`, or `0x24`; the Fclk-labeled branch tries `0x015F`, then `0x0160`, then zero.

The exact provider edge is `0x1FB4 -> 0x4800 -> 0x49CC`. Helper `0x4800` validates token IDs `1..0x161`, sets literal internal selector `0x0F`, and branches to `0x49CC`. Selector case `0x0F` prepares constant `0x1707` and reaches `0x6374` and `0x6238`; the common reader's first demonstrated consumer remains its caller-typed output store.

`0x0F` is established only as a dispatch selector reused as a provider field in this route. The exact inspected path does not name it `group`, `priority`, or `source index`; those labels remain unsupported. An Fclk-named caller and numeric tokens do not establish units, physical frequency, a divider/PLL write, or a memory-clock relationship.

## Exact observations

- Uclk caller: payload `0x2CB6` loads literal `0x20` into `r0`; `0x2CF0` stores it at descriptor element 0. The code at `0x2CF4`, `0x2D20`, `0x2D48`, and `0x2D70` stores the respective element-1 token (`0x21..0x24`) at `sp+0x46`; `0x2CFC` stores the zero terminator at `sp+0x48`. These paths pass the same list pointer (`sp+0x44`) to `0x1FB4`.
- Fclk caller: the literal branch test is `r1 == 0x0F` at `0x4648`. It builds halfwords `0x015F` (`0x464E`), `0x0160` (`0x4656..0x465E`), and zero (`0x4658`), then calls `0x1FB4` with the list at `sp+0x10`.
- Reader: `0x1FD8..0x1FE0` loads the current halfword and calls `0x4800`. On helper success it reaches caller-type dispatch. On failure, `0x200E..0x201A` increments the index, reads the following halfword, and repeats only if it is nonzero.
- Helper: raw code `0x4806..0x4810` checks `(token - 1) <= 0x160`, equivalent to IDs `1..0x161`. At `0x4810` it sets `r0=0x0F`; the moves at `0x4812..0x481A` forward the other arguments; the BL at `0x481C` targets `0x49CC`.
- Provider dispatch: exact `0x49CC` has a TBB selector dispatch; its case at `0x4B0E` sets `r2=0x0F` and carries `0x1707` into the case's downstream setup. The exact case contains BLs to `0x6374` (`0x4B3A`) and `0x6238` (`0x4B5C`). Their internal/runtime backing data is not decoded here.
- Pointer uncertainty: `0x49DC` loads a literal at `0x4DD0` whose bytes encode `0x0006A2D4`. Existing independent static review records four coherent anchors for candidate base `0x57100`, but not loader/runtime-base proof. Under that hypothesis only, `0x6A2D4 - 0x57100 = 0x131D4`; the exact bytes there form an 18-halfword table and its entry at index `0x0F` is `4`. The entry's semantic meaning remains unknown.

## Verification

The independent verifier passed `71/71` exact checks. Its owned disassemblies were regenerated with `llvm-objcopy` / `llvm-objdump` from the pinned decompressed ABL1 bytes and disassembled starting at exact Thumb boundaries `0x4800` and `0x49CC`. Literal stdout is retained; verifier stderr is empty. Reproduction:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/abl1_descriptor_provider_verify.py
```

Observed exit status: `0`.

Evidence class: `observed-bytes` and `static-analysis` only. Runtime execution, ABL loader base, APCB backing-table contents, physical frequency, divider/PLL behavior, and hardware result are not established.

## Pinned input hashes

- ROM `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` — 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Decompressed ABL1 `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` — 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Reviewed full Thumb listing `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` — SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Conditional-base review result `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-producer-base-review/abl1-producer-base-review-result.json` — SHA-256 `ecb7953571d3b008e76798718d216362bf819a4b0ffcb3dc52da58e23e2c483b`.

## Owned artifacts

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/abl1_descriptor_provider_verify.py`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/abl1-descriptor-provider-result.json`
- Literal verifier stdout/stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/verifier.stdout` and `.../verifier.stderr`
- Regenerated helper/provider Thumb listings: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/helper-4800-thumb-llvm.stdout` and `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/provider-49cc-thumb-llvm.stdout` (matching `.stderr` captures retained).
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-descriptor-provider-xhigh.md`.

No ROM, firmware, candidate, hardware, settings, installation, shared plan, memory, or MCP/Cutter state changed. Rollback is deletion of only this uniquely named evidence directory, this report, and its action log.
