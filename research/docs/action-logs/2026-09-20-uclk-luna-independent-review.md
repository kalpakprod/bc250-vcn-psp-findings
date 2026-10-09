# Independent review — native UclkDiv1M0 consumer trace

Timestamp: 2026-09-20T04:20:00+05:00 (initial review intent)
Actor: verify_uclk_luna executor
Target: read-only review of `evidence/firmware-audit/20260920-native-uclk-luna/uclk_consumer_trace.py`, its JSON result, the exact-clv census, and the pinned ROM/module bytes.
Procedure planned: inspect the verifier and bounded-census implementation; independently hash and re-extract the exact clv image to a disposable `/tmp` tree; rerun the verifier from a disposable copy; compare byte windows and the retained matrix; record whether absence supports exclusion or only an unresolved boundary.
Rationale: independent execution verification requested by the operator; no firmware, ROM, shared memory, source, or installation changes.
Expected effect: one concise review record containing observed tests, limitations, and any wording correction.
Rollback: delete only this uniquely named review log; disposable `/tmp/bc250-uclk-*` trees are not project artifacts.

## Observed verification

Timestamp: 2026-09-20T04:22:00+05:00 (+05:00).

1. Disposable verifier rerun (project source/result untouched):

```text
cd /tmp/bc250-uclk-review-20260920/evidence/firmware-audit/20260920-native-uclk-luna
python3 uclk_consumer_trace.py
```

Exit status: 0.
Observed stdout:
`{"status": "PASS", "checks": 21, "fresh_result": "For setup bytes 00/01/7f at +0x330, the immediate callback output record remains ID 0x1204 with value 00/01/7f respectively. The first static callback is an INV adapter (0x36c0->0x36f0), not a clock/register consumer."}`

Disposable JSON SHA-256: `66cf4d95dcce1ea29f776592626c2884ad8c7800f429a2ea3c59068581f3c11c`.

2. Fresh read-only extraction from the pinned clv ROM, written only under `/tmp/bc250-uclk-parser-20260920`:

```text
python3 scripts/firmware_audit.py evidence/donor/retroweb-20260916/BC250_5.00_clv.bin --output /tmp/bc250-uclk-parser-20260920/firmware-audit.json --extract-image evidence/donor/retroweb-20260916/BC250_5.00_clv.bin --extract-dir /tmp/bc250-uclk-parser-20260920/modules
```

Exit status: 0. Parser output: 233 modules, 233 unique executable bodies. `CbsBasePei` was independently re-extracted at FFS offset `15442408` (`0xEBA1E8`), section offset `24`, size `81520`, body SHA-256 `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`. `cmp` against the retained census body exited 0.

3. Independent raw-byte checks against the retained `CbsBasePei` body passed:

- `+0x9cc4`: `ba04120000` (record ID load `0x1204`);
- `+0x9ce4`: `8a8230030000` (load `Setup+0x330`);
- `+0x9cea`: `884103` (the actual store to record byte `+0x3`, checked independently because the verifier does not include these three store bytes in its exact assertion);
- `+0x36de`: `e80d000000` (call to `0x36f0`);
- `+0x3728`: `c70224494e56` (`$INV` header write);
- dispatcher window `RVA 0x240..0x5ff`: no `04 12` literal.

4. Bounded-census checks passed: exactly 233 records; exactly one `CbsBasePei` target candidate with operands `edx,0x1204`, category `immediate-candidate`, RVA `0x9cc4`; retained confirmed-reader list is `AmdCcxVhAriDxe` and `AmdFabricAriPei`; the caller matrix contains no `CbsBasePei` row; `verification.json` reports `517` passed and `0` failed checks with explicit unresolved-indirect/runtime limits.

5. Synthetic value discrimination is host-only serialization modeling. It does not execute firmware, apply a setup value to hardware, prove UCLK/DF mapping, prove defaults precedence, or prove firmware acceptance. The result JSON makes no hardware claim.

## Corrections and interpretation boundary

- **C1 — absence is not exclusion.** The missing final consumer is **unresolved at the bounded static-analysis boundary**, not proven to be outside the 233-module census. The census explicitly leaves arbitrary computed indirect destinations, runtime code, GUID-driven dispatch, DMA, and other dynamic paths unresolved. Do not rewrite this as "no consumer" or "outside the census".
- **C2 — matrix omission is not a negative reader classification.** `CbsBasePei` is absent from `caller-matrix.md` because `analyze.py` only emits rows for modules carrying the selected heap GUID or `NVTB` marker; its `INV` serializer marker alone does not create a row. The verifier's check therefore supports only "not listed as a confirmed INV reader," not "proved not to read INV."
- **C3 — exact-byte assertion gap.** The verifier labels the `+0x9ce1` window as a load/store and the `+0x9ce4` check as a serialized write, but the asserted windows stop before `+0x9cea` and do not check `88 41 03`. Independent raw inspection above observes that store. This is a verifier coverage limitation, not a failure of the byte-backed finding.

## Integrity and completion

Pinned ROM SHA-256 remains `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; retained module SHA-256 remains `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`; verifier SHA-256 remains `467bcd5afdfa4f72eedc7f7ff8e97717cdf100733e728ac39ff5c73ce44b0611`; retained result SHA-256 remains `b4c610093aad9a61602e2f995351166fa60215d15e9a96067151bc0bb69ef410`.

No project ROM, source, shared memory, installation, hardware, or original evidence file was changed by this review. The only project write was this review/action log. Review status: **PASS for the bounded byte-backed path; final consumer/actuator remains unresolved; hardware application unrun.**

## Timestamp correction

Recorded at `2026-09-20T04:15:45+05:00`. The `04:20`/`04:22` labels above were prefilled review-section labels rather than observed shell timestamps; this correction is the authoritative record time for the review write and readback. No finding depends on those labels.
