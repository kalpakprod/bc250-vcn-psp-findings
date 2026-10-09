# Independent consequential-firmware review — BC-250 VCN policy-only candidate v001

## Reviewer identity, model, and effort disclosure

- Role: independent consequential-firmware reviewer (different-author review gate per `<review_policy>`).
- Effective model visible to this session: `Opus 4.8 (1M context)`, model ID `claude-opus-4-8[1m]`, Anthropic Claude Opus family. Different author from the build agent recorded as "root Codex agent"; review-gate family separation satisfied. (This session began earlier under `Opus 5 (1M context)` and was re-identified mid-session to Opus 4.8; both are Opus-family, as also disclosed in the prior D3-B2 review.)
- Effort/verbosity: Claude Code exposes no numeric effort level to the model at runtime; none is visible to disclose. Performed as a thorough, evidence-first pass with independent re-computation and independent re-runs of the builder/verifier, not acceptance of shipped JSON verdicts.
- Permissions: terminal launched with bypass-permissions; I constrained myself to read-only inspection plus this one Markdown artifact. No firmware, hardware, candidate, script, or root-owned metadata was modified.

## Scope

- Reviewed artifact: `candidates/BC250_VCN_policy_only_v001_from_read-a.bin`.
- Baselines: stock `evidence/programmer/reads/20260911/read-a.bin`; reviewed combined `candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`.
- Inspected: `scripts/build_vcn_policy_only_candidate.py`, `scripts/verify_vcn_d3b2_candidate.py`, `evidence/candidates/BC250_VCN_policy_only_v001/` (build-manifest, verification, firmware-audit, apcb-detail), `specs/2026-09-11-vcn-policy-only-candidate.md`, and both hardware-trial records: `docs/action-logs/2026-09-11-apcb-vcn-hardware-trial.md` with `evidence/programmer/reads/20260911/apcb-v001-hardware-trial-manifest.json`, and the D3-B2 trial in `docs/action-logs/2026-09-11-vcn-d3b2-fresh-candidate.md` with `evidence/programmer/reads/20260911/d3b2-v001-hardware-trial-manifest.json`.
- Evidence-class boundary: everything below is `observed-bytes` or `static-analysis` on offline images. No `emulated-or-host-tested` or `hardware-verified` evidence exists for THIS candidate. Nothing here shows it boots, that PSP accepts the modified `$PS1` carriers, or that VCN is enabled.

## Check results

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Candidate SHA-256 = `8cd9d199…193921b1`, 16 MiB | PASS | recomputed |
| 2 | Stock SHA-256 = `83c4e420…288f8ee0` | PASS | recomputed |
| 3 | D3-B2 SHA-256 = `439e2481…8914747d` | PASS | recomputed |
| 4 | Build deterministic and reproducible (stock + reviewed D3-B2 → candidate) | PASS | rebuilt in sandbox → identical SHA-256 |
| 5 | **Entire APCB block `0xAB1000..0xAB1B6F` byte-identical to stock** | PASS | independent slice compare (also whole `0xAB1000..0xAB2000` identical) |
| 6 | APCB DFG words restored to stock `0x001FFF00` at +0x130/+0x16C | PASS | value read |
| 7 | APCB checksum reconciles (stored `0xF2`, sum&0xFF==0) | PASS | independent sum |
| 8 | **PSP directory byte-identical to D3-B2** (`0x8E0000..dir-end`) | PASS | independent slice compare |
| 9 | **Relocated policy region `0x9E0000..0x9E4708` byte-identical to D3-B2** | PASS | independent slice compare |
| 10 | **policy-only vs D3-B2 diff = exactly {0xAB1010, 0xAB1132, 0xAB116E}** | PASS | independent full diff |
| 11 | Those three = exactly the D3-B2↔stock APCB delta (the removed common bytes) | PASS | independent APCB diff |
| 12 | policy-only vs stock diff confined to PSP-dir + relocated-policy regions only; zero APCB changes vs stock | PASS | 13,733 changed bytes, 0 outside {dir, policy carriers}; no byte in APCB region differs from stock |
| 13 | Changed-byte total vs stock = 13,733 in 329 ranges (matches manifest) | PASS | independent diff and range count |
| 14 | policy-only vs stock changed count is exactly 3 fewer than D3-B2 vs stock (13,736→13,733) | PASS | both diffs computed |
| 15 | PSP directory Fletcher32 valid (`0x9F717AB8`, = D3-B2, unaffected by APCB) | PASS | recomputed on candidate; also validated on stock |
| 16 | BHD directory untouched, Fletcher32 valid (`0xECE7B2E6`) | PASS | recomputed |
| 17 | Dir entry 0x24 → (idx 7, size 0x3010, loc 0xFF9E0000) | PASS | entry parse |
| 18 | Dir entry 0x45 → (idx 15, size 0x708, loc 0xFF9E4000) | PASS | entry parse |
| 19 | Gasket groups 1281/31/13/105/31; targets 0x03E810=6, 0x03A2011C=[0x107FF,0x107FF], 0x03A20124=0x10FFF; VCN bank 56 | PASS | group walk (region == D3-B2) |
| 20 | Policy groups 13/0/105/31; targets 0x03E810=6, 0x03A2011C=0x107FF; VCN tail 5 donor pairs in order | PASS | group walk (region == D3-B2) |
| 21 | Both `$PS1` headers: hash/signature material (+0x00..+0x0F, +0xD0..+0xEF) and 0x100 tail preserved from stock; only size fields (+0x14,+0x50,+0x6C) rewritten | PASS | header diff; see F1 for interpretation |
| 22 | Original carriers 0x24 @0x982000 and 0x45 @0x9CA400 unchanged from stock | PASS | slice compare |
| 23 | Inter-blob gap 0x9E3010..0x9E4000 and post-blob 0x9E4708..0xAB0000 remain all-FF | PASS | region scan |
| 24 | Builder negative test: wrong D3-B2 hash (incl. swapped args) rejected before output | PASS | reran → `D3-B2 SHA-256 mismatch`, no output |
| 25 | Builder negative test: 1-byte-corrupted D3-B2 policy region rejected before output | PASS | reran → `D3-B2 SHA-256 mismatch`, no output |
| 26 | Project verifier `--apcb-mode stock` reproduces 26/26 PASS (incl. `apcb_block_stock_identity`, header-signature-material, exact prefix delta) | PASS | reran verifier independently |
| 27 | Verifier addressed prior review gap (F4 in D3-B2 review): now asserts header signature material and exact policy prefix delta, and adds a stock APCB mode | PASS | source read |
| 28 | PSP acceptance of modified signed `$PS1` payloads | INCONCLUSIVE / UNVERIFIABLE OFFLINE | signature not verifiable here; inherited from D3-B2, unchanged; see F1 |
| 29 | Donor/unsigned VCN body applicability to this board's HWID | INCONCLUSIVE | inherited from D3-B2; see F2 |
| 30 | One-variable discriminator validity | PASS (relative to D3-B2) with caveat | see "Discriminator assessment" and F3 |
| 31 | Boot / video / VCN power / ring completion | UNRUN | no emulation or hardware run |
| 32 | Current board state before any new write | INCONCLUSIVE / OUTSTANDING PRECONDITION | see F4 |

## Discriminator assessment

Both prior hardware trials are confirmed from their manifests and logs:
- APCB-only (delta = the 3 bytes {0xAB1010,0xAB1132,0xAB116E}) — write VERIFIED, readback byte-identical, first cold boot: indicators lit, **no display**.
- D3-B2 combined (delta = full 13,736 bytes) — write VERIFIED, readback byte-identical to `439e2481…`, first cold boot: **same indicator pattern, no display**.

The one firmware delta common to both failed images is exactly the APCB DFG change. This candidate removes that common delta and nothing else relative to D3-B2 (proven: diff vs D3-B2 = the three APCB bytes only). It is therefore a **clean single-variable move relative to the D3-B2 arm**: it tests "is the APCB DFG change necessary for / contributing to the no-display result, with the policy carriers held fixed?"

Caveat (important, hence F3): this is a one-variable step *between two failing images*, not against a known-good boot. It does not isolate a single variable against stock. Its diagnostic power is asymmetric and bounded:
- If it produces video: the APCB change is implicated as a contributor, and the policy carriers are at least not fatal on their own — a genuinely informative positive.
- If it repeats no-display (the more likely outcome given F1): it does **not** prove the policy branch is the cause. It only shows the APCB change is not *solely* responsible. The `$PS1` signature question (F1) and donor-mapping question (F2) remain open, and a no-display result is also consistent with PSP rejecting the modified carriers regardless of APCB. The spec's own use-case 3 acknowledges a signed-relocation control is the needed next step in that branch.

Per instruction, no boot-stage inference is drawn from LED state: the illuminated indicators establish power-rail/status activity only and do not prove x86/UEFI/PSP execution reached any particular stage. Both prior "no-display" results are `hardware-verified` only for the observation "no video on that display setup", not for execution stage.

## Findings (severity-ranked)

### F1 — CRITICAL (inherited, by design, disclosed): stale signature over mutated/grown signed bodies
The two relocated `$PS1` carriers are byte-identical to the reviewed D3-B2 image, so the exact risk from that review is carried forward unchanged: signed payload bytes and declared body sizes changed (gasket body 0x2C50→0x2E10, policy body 0x4E0→0x508) while the record hash/signature material (+0x00, +0xD0) and 0x100 tail are copied verbatim from stock. If PSP verifies these records, it will reject them. This is the dominant risk and is unaffected by restoring stock APCB. It is a live explanation for a repeated no-display outcome and is exactly what the broader investigation still needs a signed-relocation control to separate.

### F2 — HIGH (inherited): donor VCN body not tied to this board's HWID
The gasket VCN register set originates from the historical unsigned donor body ("DO NOT FLASH" in its filename). No in-repo evidence ties that donor mapping to `BC250-01` silicon/HWID. If accepted but wrong, it could program incorrect apertures. Unchanged from D3-B2.

### F3 — MEDIUM (interpretation risk): asymmetric discriminator between two failing arms
As above: a no-display repeat is only weakly informative and must not be read as "policy branch confirmed as cause". Recommend that the experiment plan pre-commit to the next control (signed-relocation, or a stock-recovery boot to confirm the display path itself is healthy) before running, so a null result is not over-interpreted. This is an analysis-discipline finding, not a build defect.

### F4 — HIGH (operational precondition): board currently holds the failed D3-B2 image
The D3-B2 trial manifest records `rollback.not_triggered = true`; no log shows a stock restore after the D3-B2 no-display boot. Any write of this candidate must be preceded by a fresh full pre-write dump byte-compared against a known reference (as both prior trials did), so the departure state is captured before erase. Do not write over an unconfirmed state.

### F5 — LOW: builder trusts D3-B2 as an intermediate source
The candidate is derived from the D3-B2 artifact rather than rebuilt from stock + primitives. The builder pins the exact D3-B2 SHA-256 and re-derives the APCB from stock, and I confirmed the output equals stock-with-D3-B2-policy, so provenance is sound. Noted only because a compromised D3-B2 input would propagate; the hash pin and my independent stock/D3-B2 comparisons mitigate this.

### F6 — LOW: no full independent proof that policy carriers are internally sufficient
The candidate carries the policy hypothesis but there is no offline way to prove the register/aperture set is functionally complete for VCN. Runtime-only question; correctly marked UNRUN.

## Failure path and rollback

- Most probable adverse outcome on trial: PSP rejects the modified `$PS1` carriers (F1) → at best stock-equivalent behavior or clean fallback, at worst boot halt / repeated no-display. No path can be called brick-proof.
- Recovery credible: triple-verified stock image `83c4e420…` preserved; flashrom 1.8.0 / CH347 / W25Q128.V path demonstrated with independent readback across two prior trials. Contingent on re-running the pre-write dump/compare gate and keeping the programmer attached until a post-write readback matches.
- Offline artifact rollback trivial (delete candidate/reports).

## Recommendation

**APPROVE_FOR_HARDWARE_TRIAL**

Justification and strict boundary: the artifact is internally coherent, deterministically reproducible, and its central claims are independently proven at the byte level — the entire APCB block is byte-identical to stock, the PSP directory and relocated policy region are byte-identical to the reviewed D3-B2, checksums and group structure are valid, diff confinement holds, and the delta versus D3-B2 is exactly the three common APCB bytes and nothing else. It is a valid one-variable step relative to the D3-B2 arm and is a reasonable next controlled experiment. This approval means **only** that the image is coherent enough for a controlled, recovery-backed programmer experiment. It is **NOT** a statement that the image is safe, bootable, signed, or VCN-enabled; F1 keeps PSP rejection a live possibility, and F3 bounds how much a null result can conclude.

Contingent, none waived, before any write:
1. Fresh full pre-write dump byte-compared to a known reference; **resolve F4** — capture the current (D3-B2) board state first, then proceed only from a confirmed baseline.
2. Explicit new operator approval naming this exact file and SHA-256 `8cd9d199…193921b1` and board `BC250-01`.
3. Programmer kept attached; independent post-write readback byte-identical to the candidate before power-up.
4. Recovery stock write pre-authorized and rehearsed; single variable only.
5. Pre-commit the interpretation and the next control (signed-relocation / stock display-path check) so a repeated no-display is not over-read (F3). Draw no boot-stage conclusion from LED state.

Report author: Claude Opus 4.8 (1M context), independent reviewer. All PASS results were independently recomputed on the byte images and by re-running the builder and verifier; all INCONCLUSIVE/UNRUN items are marked as such and were not inferred from a higher evidence class.
