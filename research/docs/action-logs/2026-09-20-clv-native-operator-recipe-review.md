# CLV native operator recipe consistency review — intent

Timestamp: 2026-09-20 (Asia/Almaty)
Actor: bounded clock-semantics reviewer.

Target: `docs/research/2026-09-20-clv-native-operator-recipe.md` and its machine result `evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result.json`.

Scope: compare the recipe's exact QIDs, `AmdSetup` offsets, menu paths, selected values, persistence/rollback wording, and physical-acceptance limits against the pinned exact-CLV native-menu guide and the latest ABL1 pointer/clock evidence. This is a read-only consistency review. No ROM, NVRAM, hardware, candidate, or recipe file will be modified.

Acceptance: (1) report whether literal menu mappings are consistent; (2) identify any correction needed to avoid confusing the bundled six-field hypothesis with the canonical one-variable diagnostic route; (3) identify any missing board-identity/visibility/measurement guard; (4) preserve the exact unresolved pointer/clock boundary.

Inputs to reopen:

- `docs/research/2026-09-20-clv-native-operator-recipe.md`
- `evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result.json`
- `docs/research/2026-09-20-clv-native-menu-1to1-guide.md`
- `docs/research/2026-09-20-clv-uclk-discrimination-guide.md`
- `docs/research/20260920-clv-abl1-r6-3c4-producer-trace.md`

Expected effect: one supplemental review report and this append-only action log. Rollback: remove only those two review artifacts. No firmware or hardware rollback is applicable.

## Scope correction after recipe changed during review

Timestamp: 2026-09-20 (Asia/Almaty). Reopened the recipe after its owner added a deterministic 1330 MHz profile. The recipe now recommends 1330 (`+0x316=0x1A`, `+0x704=0x0532` LE), while the pre-existing machine result still records H1750 (`+0x316=0x23`, `+0x704=0x06D6` LE). The review must treat this as an artifact-coherence discrepancy, not silently equate the stale H1750 result with the current recommended profile. The field/QID/offset literals themselves remain subject to the same bounded check.

The recipe phrase “reduce the first experiment's stress” is not supported by the current evidence: lower numeric request is not a validated lower-risk or training-safe relationship. The correction recommendation is to call 1330 only a lower historical comparison point and explicitly not infer lower stress/safety. No source, recipe, ROM, NVRAM, or hardware file is being edited by this review.

## Observed review result

Timestamp: 2026-09-20 (Asia/Almaty). The corrected read-only review reopened the current recipe after the H1330 addition, the prior machine result, the canonical native menu guide, the UCLK discrimination guide, and the latest ABL1 pointer trace. The final command checked 23 assertions and exited `1` with empty stderr because one deliberate coherence assertion failed: the recipe recommends H1330, while the machine result remains `test_point=H1750-native-help` with `0x23`/1750 and `0x06D6` LE. All field/QID/offset/value checks passed, including H1330 `+0x316=0x1A` and `+0x704=0x0532` LE.

Correction: refresh the machine result for H1330 or label the existing result explicitly as historical H1750; do not treat it as validation of the current H1330 recommendation. Also replace the unsupported phrase “reduce the first experiment's stress” with “lower historical comparison point; no safety/stress inference.” The native-help conflict and unresolved UclkDiv1M0 ratio remain correctly stated.

Review report: `docs/research/2026-09-20-clv-native-operator-recipe-review.md`, SHA-256 `f92d72ed89e591b2703cbc8f36f58261dff18c531ac5f0b7e71b508736fde68d`. Machine review result: `evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review-result.json`, SHA-256 `f6a9de5692b97d243cde13d4e825cccb2120ff287d6ee818bfe0627f0e5a787d`. No ROM, NVRAM, hardware, candidate, or source input changed.
