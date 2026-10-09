# Independent consequential-firmware review — BC250 VCN D3-B2 combined v001

## Reviewer identity, model, and effort disclosure

- Role: independent consequential-firmware reviewer (different-author gate per `<review_policy>`).
- Effective model reported to this session: began as `Opus 5 (1M context)` (model ID `claude-opus-5[1m]`); a mid-session environment update re-identified the running model as `Opus 4.8 (1M context)` (model ID `claude-opus-4-8[1m]`). Both are the Anthropic Claude Opus family. The review author is therefore Claude Opus (5 / 4.8), a **different author** from the build agent recorded as "root Codex agent". Family separation for the review gate is satisfied.
- Effort/verbosity: Claude Code does not expose a numeric effort level to the model at runtime; none is visible to me to disclose. This review was performed as a thorough, evidence-first pass with independent re-computation rather than acceptance of the builder/verifier outputs.
- Permissions observed: the terminal was launched with bypass-permissions. I nonetheless constrained myself to read-only inspection plus this single Markdown artifact, as the task brief requires. No firmware, hardware, candidate, script, or root-owned metadata was modified.

## Scope of this review

Reviewed artifact: `candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`.
Stock baseline: `evidence/programmer/reads/20260911/read-a.bin`.

Inspected: `scripts/build_vcn_d3b2_candidate.py`, `scripts/verify_vcn_d3b2_candidate.py`,
`evidence/candidates/BC250_VCN_D3B2_combined_v001/` (build-manifest, verification, verification-v2, firmware-audit, apcb-detail),
`specs/2026-09-11-vcn-d3b2-fresh-baseline.md`,
`docs/action-logs/2026-09-11-vcn-d3b2-fresh-candidate.md`, `docs/action-logs/2026-09-11-apcb-vcn-hardware-trial.md`,
and historical D3-B2 references `import/from-windows/Users/kukuruza/bc250-bios/tools/patch-build/d3b2_build.py` and `d3b2_verify.py`, plus the unsigned gasket body `import/from-windows/Users/kukuruza/tmp_bc250/recon/bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin`.

All checks below were recomputed by this reviewer with independent Python parsers (not by rerunning the project verifier for its verdict). Where I reran project scripts, it was only to test builder reproducibility and negative-test behavior.

Evidence-class boundary for this review: everything below is `observed-bytes` or `static-analysis` on offline images. **No** `emulated-or-host-tested` or `hardware-verified` evidence exists for this candidate. Nothing here establishes that the image boots, that PSP accepts the modified `$PS1` records, or that VCN is enabled.

## Check results

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Candidate SHA-256 = `439e2481…8914747d` | PASS | recomputed byte-for-byte |
| 2 | Stock SHA-256 = `83c4e420…288f8ee0`, 16,777,216 B | PASS | recomputed |
| 3 | Both images exactly 16 MiB | PASS | `stat` |
| 4 | Build is deterministic and reproducible from stock + unsigned ref | PASS | rebuilt in sandbox → identical SHA-256 |
| 5 | Diff confinement (no bytes changed outside declared set) | PASS | 13,736 changed bytes, 0 outside allowed set |
| 6 | Changed-byte total matches manifest (13,736) | PASS | independent diff |
| 7 | PSP directory Fletcher32 reconciles (stock and candidate) | PASS | stock `0x63FFFCC8` and cand `0x9F717AB8` both recomputed and matched → algorithm validated on stock |
| 8 | BHD directory untouched and Fletcher32 still valid | PASS | BHD region byte-identical stock↔cand; checksum `0xECE7B2E6` reconciles |
| 9 | Dir entry 0x24 → size `0x3010`, loc `0xFF9E0000` (index 7); only size/loc bytes changed, type intact | PASS | entry-7 rel offsets changed = {+0x4,+0x5,+0x9,+0xA} |
| 10 | Dir entry 0x45 → size `0x708`, loc `0xFF9E4000` (index 15); only size/loc bytes changed, type intact | PASS | entry-15 rel offsets changed = {+0x4,+0x5,+0x9,+0xA} |
| 11 | New blobs do not overlap any other declared PSP entry | PASS | span-overlap scan clean |
| 12 | Original carrier 0x24 @0x982000 (0x2E50) unchanged | PASS | byte-identical to stock |
| 13 | Original carrier 0x45 @0x9CA400 (0x6E0) unchanged | PASS | byte-identical to stock |
| 14 | Gasket blob = stock header (sizes rewritten) + patched-unsigned body + stock 0x100 tail | PASS | reconstructed and matched candidate exactly |
| 15 | Gasket relocated sizes: hdr +0x14/+0x50 = `0x2E10`, +0x6C = `0x3010` | PASS | independent header parse |
| 16 | Gasket groups 0x201/0x203/0x210/0x280/0x281 = 1281/31/13/105/31, walk ends at 0x2E10 | PASS | independent group walk |
| 17 | Gasket targets: 0x03E810=6, 0x03A2011C=[0x107FF,0x107FF], 0x03A20124=0x10FFF | PASS | value scan |
| 18 | Gasket VCN bank 0x0900C000–0x0900CFFF pair count = 56 | PASS | range scan |
| 19 | Policy relocated sizes: hdr +0x14/+0x50 = `0x508`, +0x6C = `0x708` | PASS | header parse |
| 20 | Policy groups 0x210/0x211/0x280/0x281 = 13/0/105/31, walk ends at 0x508 | PASS | group walk |
| 21 | Policy targets: 0x03E810=6, 0x03A2011C=0x107FF | PASS | value scan |
| 22 | Policy VCN tail = exact 5 donor pairs, in order | PASS | `(C234,0)(C914,0)(C930,0)(CB80,0)(C234,1)` |
| 23 | Policy body prefix diff vs stock = exactly {0x4C,0xBC,0x245,0x246}; group 0x281 shifted +40 and byte-identical | PASS | matches historical d3b2_verify expectation |
| 24 | Both `$PS1` headers differ from stock ONLY in size fields (+0x14,+0x50,+0x6C) | PASS | header diff = {0x14,0x15,0x50,0x51,0x6C,0x6D} for both |
| 25 | Signature/hash material preserved verbatim: header +0x00..+0x0F and +0xD0..+0xEF; 0x100-byte record tail | PASS (see Finding F1 for interpretation) | byte-identical stock↔cand |
| 26 | Erased destination in STOCK was all-FF before write (0x9E0000..0x9E4708) | PASS | stock region all-0xFF |
| 27 | Inter-blob gap 0x9E3010..0x9E4000 remains all-FF | PASS | candidate region all-0xFF |
| 28 | Post-blob region 0x9E4708..0xAB0000 remains all-FF | PASS | candidate region all-0xFF |
| 29 | APCB signature/size valid; changed bytes = exactly {0xAB1010,0xAB1132,0xAB116E}; checksum reconciles (sum&0xFF==0) | PASS | independent APCB sum; DFG words 0x001FFF00→0x007FFF00 |
| 30 | No changes anywhere after APCB (0xAB1200..EOF) | PASS | 0 differing bytes |
| 31 | Builder negative test: corrupted source hash rejected before output | PASS | reran builder → `source SHA-256 mismatch`, no output |
| 32 | Builder negative test: corrupted unsigned-body hash rejected before output | PASS | reran builder → `unsigned gasket body SHA-256 mismatch`, no output |
| 33 | Gasket last-writer-wins: policy applied after gasket does not silently re-lock any target | PASS | 86 addresses shared; 0 have a policy final value that differs from the gasket final value |
| 34 | PSP acceptance of modified signed `$PS1` payloads | UNRUN / UNVERIFIABLE OFFLINE | signature not verifiable here; see F1 |
| 35 | Historical unsigned-body applicability to THIS board's HWID / supervisor parser | INCONCLUSIVE | see F2 |
| 36 | Boot / video / VCN power / ring completion | UNRUN | no emulation or hardware run performed |
| 37 | Current board rollback-to-stock state before any new write | INCONCLUSIVE / OUTSTANDING | see F3 |
| 38 | Historical full base image present for delta cross-check | UNRUN | file not in `import/`; only recorded hash `4005b68a…` — see F5 |

Verifier self-report cross-check: the project verifier reports 21/21 PASS. My independent recomputation agrees with every structural claim it makes and extends coverage (items 24–25, 33, and the negative tests are not fully asserted by the shipped verifier).

## Findings (severity-ranked)

### F1 — CRITICAL (by design, disclosed): stale signature over a mutated, grown signed body
Both relocated records are `$PS1`-wrapped signed structures. The candidate:
- changes signed payload bytes (0x03E810→6, aperture 0x87FF→0x107FF, 0x03A20124→0x10FFF, appends 51 pairs to gasket group 0x201, 5 to gasket group 0x280, and 5 VCN-tail pairs to the policy), and
- grows the declared body size (gasket body 0x2C50→0x2E10; policy body 0x4E0→0x508),

while copying the record's leading 16-byte field (+0x00) and the +0xD0 32-byte field and the trailing 0x100-byte tail **verbatim from stock**. Those preserved fields are the record's hash/signature material. A signature computed over the stock body cannot be valid over a different, longer body.
- Failure path: if PSP verifies type 0x24 / type 0x45 signatures, it will reject both records. Depending on PSP policy this manifests as: fall back to stock behavior, halt, or continue to a degraded state that never brings up display — which is **consistent with, but not proof of, the APCB-only LEDs-no-display symptom already observed**.
- This is not a defect in the build; it is the explicit research hypothesis (the spec labels it "unsigned-policy research candidate"). It is CRITICAL for any *safety/boot* claim and is the single dominant risk. It does **not** block a controlled programmer-backed trial whose purpose is to observe whether PSP accepts or rejects these carriers, provided full recovery is in place.

### F2 — HIGH: donor/unsigned body provenance not tied to this board
The gasket body is imported wholesale from `bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin` (filename self-declares "DO NOT FLASH"). Its group 0x201/0x280 VCN entries (HWID-12 donor tail) are assumed applicable to `BC250-01`. There is no evidence in-repo that this donor register set matches the reviewed board's silicon/HWID. If the donor mapping is wrong, even an *accepted* record could program incorrect apertures. Severity HIGH for behavioral correctness; does not by itself block a recovery-backed trial.

### F3 — HIGH (operational precondition): board currently holds the failed APCB-only candidate
`docs/action-logs/2026-09-11-apcb-vcn-hardware-trial.md` records the first cold boot of the APCB-only image producing LEDs and no display, a triggered stop, and a *recommended* stock restore that requires new explicit operator approval. The D3-B2 build log (line 29) confirms "the current board still contains the APCB-only candidate." I found **no action-log entry confirming a stock restore + readback was performed.** Any hardware trial of *this* candidate must be preceded by a fresh full pre-write dump that is byte-compared to stock, exactly as the prior trial did — do not write on top of an unknown/failed state without capturing it first.

### F4 — MEDIUM: shipped verifier under-asserts the signature-region preservation
`scripts/verify_vcn_d3b2_candidate.py` checks the 0x100-byte tail (`*_signature_boundary`) and that payload changed, but does not assert that the header's leading hash field (+0x00) and +0xD0 block are preserved, nor the exact policy prefix diff set {0x4C,0xBC,0x245,0x246}. The historical `d3b2_verify.py` did assert `nonce/version preserved` and the exact prefix diff. I verified these hold for the current artifact, so this is a coverage gap, not a defect in the image. Recommend porting those two assertions before the verifier is reused as the gate for future variants.

### F5 — LOW: historical full base image absent for delta cross-check
The "cannot reuse the historical image" decision rests on a recorded hash (`4005b68a…`) rather than a present file; the historical full D3-B2 image is not under `import/`. The delta logic is nonetheless independently validated against the current stock and the present unsigned reference, so this is documentation/provenance only.

### F6 — LOW: cause of the APCB-only no-display remains unattributed
Per instruction I do not assume its cause. The combined candidate does not remove the APCB DFG change; it carries it forward. If the APCB DFG change itself is implicated in the no-display result, the combined candidate inherits that risk in addition to F1. This is an open question, not a build defect.

## Failure-path and rollback assessment

- Structural rejection is impossible to rule out offline (F1). The most probable adverse outcomes on a trial are: PSP rejects the modified `$PS1` records (best case: identical to stock behavior or a clean fallback; worse case: boot halt / no display). No path here can be called "brick-proof"; the project's own instincts forbid such a claim.
- Recovery: a complete, triple-verified stock image exists (`read-a.bin` == `read-b.bin` == `read-c-prewrite.bin`, all `83c4e420…`), and the programmer path (flashrom 1.8.0, CH347, W25Q128.V) is demonstrated working with independent readback. Recovery is credible **provided** the operator re-runs the same pre-write dump/compare gate and keeps the programmer attached until a post-write readback matches.
- Rollback of the offline artifact is trivial (delete the candidate/reports).

## Recommendation

**APPROVE_FOR_HARDWARE_TRIAL**

Justification and strict boundary: the artifact is internally coherent, deterministically reproducible, exactly confined to its declared regions, structurally valid at PSP/BHD/APCB/`$PS1` layers, and its one dominant risk (F1, stale signature over a grown signed body) is fully disclosed and is precisely the question a controlled programmer-backed experiment is designed to answer (does PSP accept or reject these carriers). This approval means **only** that the image is coherent enough for a controlled, recovery-backed programmer experiment. It is **NOT** a statement that the image is safe, bootable, signed, or VCN-enabled — none of those are established, and F1 makes PSP rejection a live possibility.

This approval is contingent on all of the following before any write (none waived):
1. Fresh full pre-write dump byte-compared to stock `83c4e420…`, exactly as the APCB trial did; **resolve F3** — if the board still holds the failed APCB-only image, capture that state first, then proceed only from a confirmed baseline.
2. Explicit new operator approval naming this exact file and SHA-256 `439e2481…8914747d` and board `BC250-01`.
3. Programmer kept attached; independent post-write readback must be byte-identical to the candidate before power-up.
4. Recovery stock write pre-authorized and rehearsed; single-variable trial (do not combine with other changes).
5. Treat any boot result as `hardware-verified` evidence only for what is directly observed; LEDs alone do not prove PSP acceptance or x86/UEFI execution.

Report author: Claude Opus (5 / 4.8), independent reviewer. All PASS results above were independently recomputed on the byte images; all UNRUN/INCONCLUSIVE items are marked as such and were not inferred from a higher evidence class.
