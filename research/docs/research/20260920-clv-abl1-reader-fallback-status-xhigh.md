# Exact CLV ABL1 reader fallback versus sentinel semantics

## Conclusion

The exact reader's fallback/advance decision is **helper status-driven**, not value-driven. At the first token stage, helper return `R0=0` enters the fallback path (`0x2002` then index increment `0x200E`); helper `R0!=0` requires the returned byte to equal `1` before advancing. A non-`1` value is terminal reader failure at `0x209A`.

At the final typed stage, helper `R0=0` returns failure at `0x2094`; helper success enters width-specific sentinel guards. An Auto/sentinel value does **not** cause another descriptor attempt. For type 2, `0xFFFF` with `r7=0` fails the `MVNS/UXTH/ORRS` guard before `STRH`, then returns `R0=0` at `0x209A`; no index increment is present in that slice. Type 1 rejects `0xFF`, type 4 rejects zero, and type 8 rejects a zero doubleword under equivalent terminal paths.

Thus the descriptor list is not a generic combined-key fallback. Earlier list entries are boolean gate/status stages and the final list entry is the typed value stage. This is the concrete precedence behavior relevant to why an Auto/sentinel result would not be rescued by a later token.

## Exact evidence

Pinned exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.

- `0x1FE0..0x1FE6`: helper call and `CBZ R0` status gate.
- `0x1FE6..0x1FEE`: first-stage byte load, `CMP #1`, and advance only on value `1`.
- `0x1FEE..0x2002`: non-`1` diagnostic/failure path; it does not branch to `0x200E`.
- `0x200E..0x201C`: descriptor index increment and next-element zero check.
- `0x203A..0x2042`: final helper status gate; status zero returns failure before typed dispatch.
- `0x2058..0x2064`: type-1 sentinel guard and byte store.
- `0x2066..0x2072`: type-2 sentinel guard (`0xFFFF` when `r7=0`) and halfword store.
- `0x2074..0x207E`: type-4 zero guard and word store.
- `0x2080..0x2092`: type-8 zero-doubleword guard and doubleword store.
- `0x2092..0x209E`: success `R0=1` after store; failure `R0=0` terminal path.

Existing reviewed outputs were reopened and hash-pinned:

- Prior reader result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json`, SHA-256 `537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128`.
- Output/context result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1-reader-output-context-result.json`, SHA-256 `6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21`.

## Verification

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1_reader_fallback_status_verify.py
```

Observed exit status `0`; result `PASS`; `64/64` checks; stderr empty. Evidence class: `observed-bytes`, `static-analysis`. No runtime, loader-base, frequency-unit, divider/PLL, training, or hardware claim follows.

Owned artifacts:

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1_reader_fallback_status_verify.py`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1-reader-fallback-status-result.json`
- Literal stdout/stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/verifier.stdout` and `verifier.stderr`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-reader-fallback-status-xhigh.md`
- Manifest: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/SHA256SUMS.final`

No firmware, candidate, hardware, settings, source input, or installation state changed. Rollback is deletion of this uniquely named evidence directory, report, action log, and the two append-only integration paragraphs.

## Ordered descriptor semantics correction and caller qualification

This result supersedes the earlier generic wording in `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-descriptor-provider-xhigh.md` that described every descriptor element as a normal fallback candidate. The array shape remains an ordered `u16` list, but this reader gives the first and final elements different control roles:

- If an earlier helper returns status `R0=0`, the reader advances to the next item.
- If an earlier helper returns status `R0!=0`, the returned **byte must equal `1`** to advance; another value is terminal failure. For the Uclk and Fclk callsites, the reader's `R7` sentinel mask is zero, as shown by their caller stack arguments.
- The final element is consumed as the typed value. Its all-ones/zero sentinel checks return `R0=0` terminally; they do not trigger another descriptor attempt.

This means `[0x20,0x21..0x24]` and `[0x015F,0x0160]` are not interchangeable combined-key fallbacks. They are gate/status-then-value layouts, with a separate not-found path that can skip a missing gate and attempt the second token. No semantic field name is assigned to the tokens themselves.

## Independent output/context worker review

The latest output/context report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-reader-output-context-xhigh.md` and machine result `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1-reader-output-context-result.json` were reopened; the result is `59/59 PASS` with exact pinned payload/listing hashes. Independent raw checks added here verify the concrete Fclk stack-default/context path: local default `0x4B0` at `0x5FA4`, call to the Fclk handler with `SP+4` at `0x5FAE`, reload at `0x5FB2`, and halfword store to `[context+0x78]` at `0x5FBA`; a later branch path loads that field at `0x107E4` and compares against `0x3E8` and `0x4B0`.

Important limit: the Fclk handler passes `SP+0x0C` as the reader's type-byte pointer at `0x465C`, but no explicit write to that local appears in the bounded Fclk body before the reader call at `0x466A`. Therefore the common reader's type-2 `STRH R0,[R6]` at `0x2070` is a concrete static branch, but actual type-2 branch execution for this Fclk call is **not established** merely by the handler's later `LDRH`. The caller's initialized `0x4B0` local is retained if the Fclk handler does not commit a successful reader result; the outer caller then stores that local to context+0x78. Runtime stack provenance for the type byte remains unresolved.

The downstream constants `0x3E8` and `0x4B0` are observed comparison thresholds (`1000` and `1200` in decimal). Candidate token IDs `0x015F` and `0x0160` are `351` and `352` numerically, but they are identifiers; no transformation/unit path is proved. Do not equate tokens, returned values, thresholds, or physical frequency.

Phase 2 remains **PARTIAL**. This appendix adds no candidate or hardware acceptance claim.

## Independent Fclk output/context qualification

The same 64-check verifier independently reopens the output/context result (`59/59 PASS`) and exact Thumb listing. It confirms the Fclk handler passes `SP+0x08` as result slot and `SP+0x0C` as the reader type-byte pointer; no explicit write to that type local occurs in the bounded Fclk body before the reader call. Therefore the common reader's type-2 `STRH` branch is structurally verified but actual type-2 execution for this caller is not established.

The outer Fclk caller seeds local `0x4B0` at `0x5FA4`, calls the accessor through `SP+0x04`, reloads the local at `0x5FB2`, and stores the resulting halfword at `[context+0x78]` (`0x5FBA`). A later context path loads `[R4+0x78]` at `0x107E4` and compares against `0x3E8` and `0x4B0`. Token IDs `0x015F/0x0160` are numerically distinct identifiers; no unit conversion or semantic equality to those thresholds is proved.

The final verifier result is `PASS`, `64/64` checks, exit `0`, stderr empty. This supersedes the earlier 37-check result in the same owned directory; earlier stdout/result history is retained only through the action log and is not treated as final.

## Open question

Q1: Do the downstream `0x3E8`/`0x4B0` comparisons operate on the same value space as the configuration values returned after querying tokens `0x015F`/`0x0160`, or is there a conversion/override boundary between them? The present bytes show the IDs, the later halfword load, and the threshold constants, but no value/unit join. Keep this unresolved; do not equate token IDs with thresholds or label them MHz.
