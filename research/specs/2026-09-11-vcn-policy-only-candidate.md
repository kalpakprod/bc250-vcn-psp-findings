# BC-250 VCN policy-only candidate

## Title and scope

Build a fresh-baseline VCN candidate that retains the combined D3-B2 SEC_GASKET and TOS_SECURITY_POLICY changes while restoring the entire APCB block to the verified stock bytes. This is the next one-variable discriminator after two no-display boots shared the same APCB DFG change.

## Planning anchor

- Stock: `evidence/programmer/reads/20260911/read-a.bin`, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Combined source: `candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`, SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Hardware observation: APCB-only and D3-B2 both wrote/read back exactly but produced the same indicators and no display.

## Connected groups and observed logic

- Both failed images contain the identical APCB block with DFG words `0x007FFF00` and checksum `0x32`.
- D3-B2 additionally contains the two relocated/modified VCN policy carriers at `0x9E0000` and `0x9E4000`.
- Restoring APCB to stock leaves the policy hypothesis active while removing the only common firmware delta between the two failed candidates.

## Use cases

1. Potentially boot with the VCN policy carriers active but without the suspected APCB change.
2. If video returns, implicate the APCB change and proceed to Linux VCN checks.
3. If no display repeats, prioritize policy relocation/signature handling and use a signed-relocation control next.

## Implementation checklist

- [x] Create a strict path-parameterized builder.
- [x] Restore the complete APCB region from stock, not only the three differing bytes.
- [x] Verify policy bytes are identical to reviewed D3-B2.
- [x] Confirm candidate APCB is byte-identical to stock and checksum-valid.
- [x] Run firmware and policy structural checks with stock-APCB expectation.
- [x] Produce exact hashes and diff report.
- [ ] Obtain independent review before hardware write.
- [ ] Require exact per-image approval and full post-write readback.

## Open questions

- Blocking: PSP acceptance of the modified `$PS1` carriers remains unknown.
- Blocking: whether the common APCB change caused the two no-display results remains unproven.
- Runtime: whether policy-only is sufficient for VCN power, MMIO, and ring completion.

## Decision log

- 2026-09-11: select policy-only before the signed-relocation control because it both isolates APCB and retains a direct possibility of VCN unlock.
- 2026-09-11: do not infer BIOS execution stage from LED state.
