# Action log: glitch-signed flash package staged

## Intent (before)

Operator strategy 2026-09-23: the deliverable is a patched BIOS paired with the glitch
(spoofed key + re-signed image + rebuilt VCN lock carriers); runtime-only lanes are
closed by field experience. Stage the already-verified glitch-signed candidate as a
flash package so the physical session needs zero offline work.

Target: `firmware-flash-pkg/20260923-glitchsigned-vcn/` (new directory; copy of the
candidate, source file untouched). Companion runbook:
`docs/runbooks/2026-09-23-glitch-session-runbook-DRAFT.md`. External findings that
shape the session: `docs/research/2026-09-23-external-poc-hunt.md`.

## Result (after)

- Created `firmware-flash-pkg/20260923-glitchsigned-vcn/` with
  `BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin` + `SHA256SUMS`.
- Hash verified: `91de01eb7cb8e97014294adc8692eb8be66c3f95ce8481c234805544c0ddd517`
  (matches `evidence/firmware-audit/20260919-glitch-path/build-report.json`).
- Source candidate in `candidates/` untouched. Nothing flashed.
- No signing key material in the repo (private key lived in /tmp, path recorded in the
  build report only).
