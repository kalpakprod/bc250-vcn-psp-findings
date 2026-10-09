# BC250 project contour bootstrap

## Before

- Target: `/home/OWNER/orca/projects/bc250`.
- Evidence: migrated raw corpus under `import/from-windows/`; source layout references from the local `vpn-ops` and `homelab` repositories.
- Intent: create the project contract and operational contour without modifying imported historical artifacts or writing firmware/hardware.
- Rollback: remove only the newly created root contour files and directories listed in the after section; do not remove `import/`.

## After

This entry is completed after the contract, compatibility copies, memory indexes, reference documentation, local skills, and validation checks are written. No hardware or firmware write is part of this bootstrap.

Observed result:

- Wrote `AGENT_CONTRACT.md`, byte-identical `AGENTS.md`, `CLAUDE.md`, and `EMPRYO.md`.
- Wrote the canonical `docs/`, `memory/`, `specs/`, `.agents/skills/`, `scripts/`, and `tools/` contour.
- Added eight focused project skills and six initial instincts.
- No firmware, hardware, imported raw artifact, or remote system was modified.

Validation pending: frontmatter, byte identity, link targets, XML tag balance, and repository status.

Validation result:

- `scripts/validate-contour.py` passed: four contract copies are byte-identical, eight skill frontmatters are valid, six instinct YAML files parse, local contract/index links resolve, and no secret-like file exists in the canonical contour outside `import/`.
- `git diff --check` passed.
- `AGENTS.md` and compatibility copies are uncommitted project changes only; no firmware or hardware write occurred.

Contract completion:

- Added the reusable orchestration, model-role, and execution-routing sections adapted from the reference contours without fleet-specific production rules.
- Re-ran `scripts/validate-contour.py` and `git diff --check`; both passed.

Russian contract copy:

- Created `AGENT_CONTRACT_RU.md` as a human-readable Russian translation of the project contract. It is not a compatibility instruction file and is not loaded in place of `AGENTS.md`.
- Russian contract XML-like sections are balanced and preserve the same scope, gates, evidence classes, legal boundaries, firmware safety, and workflow.
