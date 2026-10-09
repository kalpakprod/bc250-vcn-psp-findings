# CLV native operator recipe consistency review

Current disposition: the follow-up correction at the end of this document resolved the stale H1750 machine-result identity and reran the review with `24/24 PASS`. The `CORRECTION_REQUIRED` verdict below is the preserved initial result, not an open issue.

## Current

Static field/value mappings are consistent with the exact-CLV native menu evidence. One artifact-coherence correction is required: the recipe now recommends the deterministic 1330 MHz profile, while its existing machine result still describes the earlier H1750 profile.

## Result

**CORRECTION_REQUIRED — stale machine-result identity; no ROM or hardware action.**

### Field/value checks — PASS

The current recipe's six requested fields match the canonical exact-CLV map:

- Memory Clock Speed: QID `0x20F`, `+0x316`, `1330` enum `0x1A` or `1750` enum `0x23`.
- UclkDiv1M0: QID `0x229`, `+0x330`, Enabled `0x01`.
- Memory P-state: QID `0x25E`, `+0x36D`, Disabled `0x00`.
- FCLK_DPM: QID `0x7045`, `+0x6A3`, Disabled `0x00`.
- DF Clock Override Control: QID `0x37D`, `+0x703`, Manual `0x01`.
- DF Clock Override: QID `0x37E`, `+0x704`, numeric `u16` little-endian.

The newly recommended H1330 profile is internally byte-consistent: Memory Clock `+0x316=0x1A`; DF value `+0x704=1330 decimal = 0x0532` little-endian. The native DF help conflict (`FCLK > UCLK`) and the unresolved meaning of UclkDiv1M0 Enabled are correctly retained as warnings. The recipe does not claim physical acceptance.

### Required correction — machine-result coherence

The report now contains a `Recommended first test point` of 1330 MHz and lists the H1330 six-field profile. However, `evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result.json` still has:

```text
test_point = H1750-native-help
Memory Clock = 0x23 / 1750MHz label
DF Clock Override = 1750 / bytes D6 06 LE
```

This is not a field-map error, but the result is stale or ambiguously attached to the current report. Refresh the machine result to H1330, or label it explicitly as a historical H1750 result and give the H1330 profile a separate result identity. Do not use the current result as evidence that the recommended H1330 profile was checked.

### Safety/semantics wording correction

The phrase “selected only to reduce the first experiment's stress” is not supported by current evidence. A lower numeric request is not a validated lower-risk, training-safe, or physically lower-stress setting. Use “lower historical comparison point” and preserve “not a validated safe frequency.”

### Pointer/clock consistency

The recipe remains consistent with the latest ABL1 trace: runtime object identity at `[R6+0x3C4]` versus the active callback/initializer object is unresolved. No recipe field is promoted to a clock actuator, ratio, physical clock, or `MCLK=UCLK=FCLK` result. The latest UCLK guide likewise leaves divider semantics and independent physical measurement unresolved.

## Fresh bounded review

The read-only review script checked 23 assertions over the recipe, machine result, canonical native guide, UCLK guide, and pointer trace. Field/value and evidence-boundary assertions passed. One assertion failed exactly for the stale H1750 machine-result identity versus current H1330 recommendation. The review command exited `1` by design for this required correction; stderr was empty.

Evidence class: `observed-bytes` + `static-analysis` of local text/JSON artifacts. No ROM, BIOS/NVRAM, hardware, candidate, or source input changed.

## Artifacts

- Review report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-native-operator-recipe-review.md`
- Machine review result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review-result.json`
- Literal stdout: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review-final.stdout`
- Literal stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review-final.stderr`
- Exit status: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review-final.exit`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-native-operator-recipe-review.md`

## Correction applied (2026-09-20, follow-up run)

Status update: `CORRECTION_REQUIRED` -> `RESOLVED`. The verdict above is retained as the
historical review result; this section supersedes its open-item status only.

- The H1750 machine record is preserved byte-identical at
  `evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result-H1750-historical.json`
  (sha256 `e4a2c4231070d83829f14c65087cd1ec3aadd20a00cd4b8ef2872de08849477d`), labeled
  historical by filename and by the `historical_reference` block in the current result.
- The canonical `evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result.json`
  now carries `test_point = H1330-native-help` with the six H1330 fields
  (`+0x316 = 0x1A`, `+0x704 = 1330 decimal = 0x0532 LE`) and `hardware_run: none - static
menu hypothesis only`. The H1750 record is not used as validation of H1330.
- The unsupported phrase was replaced in the recipe report: "lower historical comparison
  point; no safety/stress inference. It is not a validated safe frequency."
- `review_recipe.py` now reads the historical artifact for the H1750 assertions and the
  canonical artifact for the coherence assertion; one added assertion checks the current
  H1330 values. The assertion set is otherwise unchanged.
- Rerun `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review_recipe.py`:
  exit `0`, `status PASS`, `checks 24`, `failed 0`, stderr empty. Baseline run before the
  correction: exit `1`, `checks 23`, `failed 1` on `machine_result_coherence`.
- No ROM, NVRAM, register, hardware, or candidate was touched. The H1330 profile remains a
  static menu hypothesis; no physical acceptance, ratio, or `MCLK=UCLK=FCLK` claim is added.
