# Anthropic Cybersecurity Skills — whole-repository BC-250 review

Current: pinned public catalogue / complete static inventory / no additional skill approved for local install.

## Conclusion

Do **not** install the repository wholesale or add its skills to the BC-250 project stack. The pinned repository contains 818 skills and 1,096 Python helper scripts, while the BC-250 project already has focused firmware-forensics, UEFI/DXE, reverse-engineering, artifact-verification, Cutter, and research-provenance skills. The external catalogue is predominantly cloud, network, web, SOC, malware, identity, and offensive security content outside this project's scope.

The exact installed `analyzing-uefi-bootkit-persistence` tree is byte-identical to the pinned source, but it is **DEFER/ADAPT**, not an instruction to deploy persistence or run its hardware commands. Its useful portion is read-only boot-chain/firmware-integrity reasoning; its direct workflow assumes CHIPSEC, Windows Secure Boot/MOK/ESP artifacts, and generic x86/Intel tooling. It does not map AMD BC-250 PSP/APCB/SMU/VCN or native OC fields.

Recommended local install set: **empty**. Eight narrowly related skills are retained as `DEFER` reference candidates only. The other 810 are `REJECT` for this project scope. No downloaded script was executed.

## Pinned source and repository metadata

- Repository: `https://github.com/mukul975/Anthropic-Cybersecurity-Skills`
- `main` commit: `54a798831d2266a3ca61ce68a7acb80b81160d57`
- Commit message: `chore: update contributor wall`
- Commit timestamp: `2026-08-31T04:32:42Z`
- GitHub API description: 818 skills, 34 domains, 6 framework mappings; Apache-2.0
- Recursive tree SHA: `82fac49869491010960184cbdbbe91cf668148d5`
- Tree: `7,286` entries, `truncated=false`
- Full source archive SHA-256: `41ca4c6ff945f25e5bb96574b34bd0ccc25ce92efce588579fbc0c29dc98addb`
- README SHA-256: `1593e862b0997724c33225af83e45bf5138f01130ac7d1c3e2338e5aa12ab4e6`
- LICENSE SHA-256: `a941b58ef0ba43a31e24ae7ece1b743a585efed9e37792b9ca063e0798be1cbe`
- SCOPE SHA-256: `4181ffcd67c2fe0ab4575979b98ab84ceace1d46b228c9a44ff7d88d8b1f8fef`

The repository's README says 818 skills; `SCOPE.md` contains older “817” wording. The pinned tree and 818 `skills/*/SKILL.md` files are the authoritative count for this review.

## Complete inventory method and evidence

Every skill directory under the pinned archive was enumerated and its `SKILL.md`, files, hashes, subdomain, description, and recommendation were recorded. Every Python file below `skills/*/scripts/` was parsed with Python AST only; no script was imported or executed.

- Skill files: `818/818` inventoried.
- Python helper scripts: `1,096` inventoried; AST parse failures: `0`.
- Scripts with subprocess/OS call sites: `332`.
- Scripts containing network/installer literals: `509`.
- Scripts containing file/process write-call patterns: `334`.
- Static parser emitted non-fatal invalid-escape warnings in a few scripts; these are recorded as source-quality observations, not runtime tests.

Evidence directory:

`/home/OWNER/orca/projects/bc250/evidence/skill-review/20260920-anthropic-cybersecurity-skills/`

- `repository-metadata.json` — source pin and hashes.
- `skills-inventory.json` — complete 818-skill inventory and classification.
- `skills-inventory.tsv` — reviewable tabular inventory of all 818 skills.
- `script-static-findings.json` / `.tsv` — static findings for all 1,096 scripts.
- `inventory-summary.json` — counts by subdomain/recommendation.
- `worker-role-validation.json` — pinned installed-tree and rollback-role validation.

## Recommendation set

### `INSTALL_LOCAL` — none

No external skill is approved for direct local installation. Existing project skills already provide the relevant BC-250 routes, and this repository's broad catalogue would increase prompt/tool scope without adding a verified BC-250 capability.

### `DEFER` — eight reference candidates, not direct execution

| Skill                                         | Reason for defer                                                                                                                                                                       |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `analyzing-uefi-bootkit-persistence`          | Read-only boot-chain concepts are relevant, but CHIPSEC/ESP/Windows/MOK assumptions and subprocess hardware commands require BC-250 adaptation.                                        |
| `auditing-uefi-firmware-with-chipsec`         | CHIPSEC loads a kernel driver and can read/write low-level hardware/SPI/UEFI state; Intel-oriented assumptions and destructive modules require a separate AMD read-only trial.         |
| `performing-firmware-extraction-with-binwalk` | Generic extraction reference only; overlaps existing BC-250 firmware-forensics and introduces install/recursive extraction/mount assumptions.                                          |
| `performing-firmware-malware-analysis`        | Useful only for a separately scoped firmware-threat incident; it introduces binwalk/Ghidra/QEMU/network-emulation and malware triage outside OC mapping.                               |
| `detecting-secure-boot-bypass`                | Defensive boot-chain investigation candidate; not relevant to the current 1:1:1/OC field route and includes package installs plus Secure Boot/CHIPSEC operations.                      |
| `hunting-bootkits-in-efi-system-partition`    | ESP threat-hunt candidate; mounting devices and scanning boot entries require a separate authorized incident scope.                                                                    |
| `analyzing-bootkit-and-rootkit-samples`       | Malware-sample workflow, not AMD firmware/OC mapping; defer until a specific authorized sample exists.                                                                                 |
| `auditing-mcp-servers-for-tool-poisoning`     | Relevant only to a separate MCP security audit; it invokes `mcp-scan@latest`, network/SSRF probes, and install commands. Existing external-stack-evaluation remains the project route. |

### `REJECT` — 810 skills

All other skills are rejected for the current BC-250 scope. The complete names and reasons are in `skills-inventory.tsv/json`. Main rejected domains include cloud security, threat intelligence/hunting, network/web security, identity/IAM, SOC/incident response, malware unrelated to firmware, containers/Kubernetes, phishing, ransomware, offensive penetration testing, social engineering, mobile/blockchain/OT security, and deployment/configuration procedures that would add unrelated dependencies or mutation paths.

## Exact installed UEFI skill and worker-role validation

Installed target:

`/home/OWNER/orca/projects/bc250/.agents/skills/analyzing-uefi-bootkit-persistence`

Pinned source files, installed files, and preserved worker snapshot matched `4/4` hashes:

- `LICENSE`: `a941b58e...`
- `SKILL.md`: `35a1a4f9...`
- `references/api-reference.md`: `27fb34c5...`
- `scripts/agent.py`: `3d4dfaa0...`

The installer evidence roles were independently reopened with the following interpretation:

- `MODIFIED_FILE`: `modified-snapshot/` directory, present.
- `DIFF_FILE`: `DIFF_FILE.patch`, present; direct `patch` application exited `0`, and file-by-file `cmp` against `modified-snapshot` passed.
- `VERIFICATION.txt`: present and records source/destination hashes plus separate-copy checks.
- `ROLLBACK.sh`: present; `sh -n` passed, isolated absent-baseline rollback passed, isolated sibling-baseline rollback passed. The installed destination remained unchanged.

The installer action log itself still says `In progress` and has no appended observed-completion section. The role artifacts and independent readback close the artifact checks, but that worker-log status must not be rewritten by this review.

## Security and applicability findings

1. **Read-only boot-chain analysis is separable from persistence deployment.** The UEFI skill describes SPI/ESP/UEFI-variable integrity checks, but it also recommends `flashrom`, CHIPSEC modules, mounting ESPs, reading Secure Boot keys, and remediation/reflash. None of those commands was run here; no implant or persistence was installed.
2. **Architecture mismatch:** the skill's threat examples and checks target Windows/Intel-style CHIPSEC/Secure Boot/MOK/ESP workflows. BC-250 analysis needs AMD SPI/PSP/APCB/SMU/VCN boundaries, exact image provenance, and the existing local parsers. The skill does not establish OC field consumers, clocks, training, or physical `1:1:1`.
3. **Unreviewed execution risk:** across the repository, 332 scripts contain subprocess/OS calls, 509 contain network/installer literals, and 334 contain write-call patterns. The catalogue must therefore remain reference-only until a specific skill is separately reviewed.
4. **Credential/data risk:** several generic skills explicitly search for passwords, tokens, keys, or cloud credentials. They are rejected under the BC-250 secret-handling boundary and were not applied to project data.
5. **Network/destructive risk:** MCP/SSRF, phishing, C2, exploit, cloud, and persistence workflows are outside this authorized firmware mapping task. No network probe, package install, driver load, mount, flash, or hardware operation was performed.

## Applicability to native `1:1:1` OC mapping

**No direct applicability.** The repository provides generic UEFI/bootkit threat-hunt procedures, not byte-backed mapping of `AmdSetup+0x316/+0x330/+0x36D/+0x6A3/+0x703/+0x704` to AMD clock/training actuators. It cannot establish units, UclkDiv1M0 ratio, FCLK-DPM precedence, memory-training behavior, physical clocks, latency, or a safe voltage. Continue using the existing BC-250 skills and exact native menu/native-gate evidence.

## Status

- **PASS:** repository pin, full tree/archive retrieval, 818-skill inventory, all-script AST/static scan, relevant UEFI/MCP source inspection, installed-tree hash equality, patch reconstruction, and isolated rollback checks.
- **DEFER:** eight narrowly related skills listed above, pending separate adaptation/approval.
- **REJECT:** 810 unrelated or unsafe direct-install skills.
- **UNRUN:** every external skill script, CHIPSEC, binwalk, mcp-scan, network probe, package install, driver load, firmware write, BIOS write, and hardware action.
- **Decision:** keep `INSTALL_LOCAL` empty; treat the installed UEFI skill as an unexecuted, deferred reference until root decides whether to adapt its read-only portions.
