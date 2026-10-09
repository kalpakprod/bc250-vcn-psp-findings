# CLV native recipe coherence correction — intent

Timestamp: 2026-09-20T21:40:46+05:00 (Asia/Almaty)
Actor: root executor (continuation turn).

Active object: the reviewer-required correction left open by
`docs/research/2026-09-20-clv-native-operator-recipe-review.md` (status
`CORRECTION_REQUIRED`) and its action log
`docs/action-logs/2026-09-20-clv-native-operator-recipe-review.md`.

Required corrections (quoted from that review):

1. "refresh the machine result for H1330 or label the existing result explicitly as
   historical H1750; do not treat it as validation of the current H1330
   recommendation."
2. "replace the unsupported phrase 'reduce the first experiment's stress' with
   'lower historical comparison point; no safety/stress inference'."

Baseline hashes (reopened this turn, unchanged since the review):

- `docs/research/2026-09-20-clv-native-operator-recipe.md`
  sha256 `107b6a42e4945855ef610a84bd35d42d482eeb27043276bef0fcf94f7a1495f6`
- `evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result.json`
  sha256 `e4a2c4231070d83829f14c65087cd1ec3aadd20a00cd4b8ef2872de08849477d`
- `evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review_recipe.py`
  sha256 `9ec7121955739705516e9dbfbcb2c169409302d597acf2b0b6c92da4da489833`

Planned action:

- Preserve the H1750 record verbatim as an explicitly historical artifact inside the
  same evidence directory, and refresh the canonical `recipe-result.json` to the
  current H1330 recommendation identity (static menu hypothesis only; no hardware
  acceptance, no physical 1:1:1 claim).
- Point the existing review script's H1750-specific assertions at the historical
  artifact so the coherence assertion and the historical-value assertion can both be
  evaluated; the script's assertion set is otherwise unchanged.
- Apply the wording correction in the recipe report.
- Rerun the same review command and record literal stdout/stderr/exit.

Expected effect: the review command exits `0` with `failed=0`, the current machine
result names the H1330 recommendation, and the H1750 record stays available as a
labeled historical artifact.

Boundaries: no ROM, NVRAM, hardware, register, candidate, BIOS, AMIBCP, or source
input is touched. No voltage/frequency recommendation is made. No claim that H1330
was experimentally checked.

Rollback: restore the pristine bytes from the `.orig-20260920` siblings created
alongside the edited files and remove only this turn's uniquely owned outputs.

## Observed result (after writes)

- BASELINE run of the existing review verifier on the pristine tree: exit `1`,
  `status FAIL`, `checks 23`, `failed 1` (`machine_result_coherence`), stderr empty.
- Corrections applied: the H1750 machine record was preserved byte-identical as
  `evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result-H1750-historical.json`
  (sha256 `e4a2c4231070d83829f14c65087cd1ec3aadd20a00cd4b8ef2872de08849477d`, identical to the
  pristine canonical file); the canonical `recipe-result.json` now names
  `test_point = H1330-native-help` with the six H1330 fields and `hardware_run: none`;
  the recipe report wording was corrected; `review_recipe.py` input/assertion wiring follows
  the artifact split (one added assertion for the current H1330 values).
- MODIFIED run: exit `0`, `status PASS`, `checks 24`, `failed 0`, stderr empty.
- Re-verified `menu-verify.py`: exit `0`, `status PASS`, `menu-result.json` sha256 unchanged
  (`6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a`), stderr empty.
- ROLLBACK exercise: `ROLLBACK.sh` on an isolated copy and on the real tree both exited `0`
  with 6x `RESTORED_OK` (pristine hashes) and 1x `REMOVED_CREATED`; the review verifier on the
  restored tree returned to exit `1` with the same single failing assertion. GOAL was then
  reapplied from the modified snapshot (all six hashes matched) and the verifier returned to
  exit `0`, `checks 24`, `failed 0`.
- `sha256sum -c SHA256SUMS.final` in the 1to1 evidence directory: exit `0`, 3/3 `OK`.

Artifacts (all under `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-native-recipe-coherence-correction/`):
`MODIFIED_FILES.txt` `759eef45...`, `changes.patch` `e4a19886...`, `VERIFICATION.txt`
`0eedf0ce...`, `ROLLBACK.sh` `c1d4cd1f...`; captured literal stdout/stderr/exit files
`baseline.*`, `modified.*`, `rollback-copy.*`, `rollback-inplace.*`, `rollback-behavior.*`,
`reapplied.*`, `menu-verify.*`.

Final hashes: recipe report `66060b1f71639f9cc3fc5a187f9e819fecfd5a69f6ec2c91eb9c91bb40bd6e71`;
review report `d16b7267d4543cef7ee3ebb6a0592282efdc74e6c2c049cc841cc725ac89e939`; review script
`5e2d1a4fbcfd2997c99751f80eba630773ff4542fd48cff2c3da1aa9facaad87`; canonical result
`214173554e4264b5bae273c8be9115f6d0f7c200837d402e43a3d2fc99132752`; review result
`26619d57e25fb058f51b93ca6d942bf97ad5503a093feff48ca8991653a0e2c1`.

Remaining uncertainty: the H1330 profile is still a static menu hypothesis (no board run, no
persistence/POST/training observation, no independent MCLK/UCLK/FCLK measurement); the review
script belongs to the same author as this correction, so independent review of the corrected
assertion wiring is still pending. No ROM, NVRAM, register, candidate, or hardware was touched.
