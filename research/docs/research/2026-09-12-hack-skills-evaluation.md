# yaklang/hack-skills evaluation for BC-250

## Item and scope

- Source: `https://github.com/yaklang/hack-skills`
- Inspected revision: `c9a4b9ee8645eb60763eb4eef172f1ecb0a5b3e8`
- Commit date: 2026-06-17T00:11:43+08:00
- Retrieval date: 2026-09-12
- License: MIT
- Requested use: add skills that materially help the authorized BC-250 BIOS,
  PSP, SMU, TOS, and key-verifier reverse-engineering work.

## Existing project capability and need

The project already has BC-250-specific firmware, Cutter, APCB, VCN/SMU,
artifact-verification, and provenance skills. The useful gap is generic
methodology for obfuscation, custom VM/bytecode, symbolic execution, and RSA
weak-key triage. General web exploitation, lateral movement, credential,
evasion, privilege-escalation, and reverse-shell playbooks do not address the
current owned-firmware task and conflict with the project's narrow-routing
rule for broad security libraries.

## Inspection

- Repository layout: 101 Markdown skills under `skills/`; two Yak build/index
  scripts; static website assets and GitHub workflows.
- Relevant files inspected completely: `README.md`, `LICENSE`, and the
  `SKILL.md` files for `rsa-attack-techniques`,
  `code-obfuscation-deobfuscation`, `symbolic-execution-tools`,
  `vm-and-bytecode-reverse`, `anti-debugging-techniques`, and
  `binary-protection-bypass`.
- The selected four packages are documentation-only Markdown resources. They
  do not provide an executable entry point, daemon, MCP server, network bind,
  or credential store.
- Referenced commands and snippets are untrusted examples and require the
  normal BC-250 gates before use. Installation does not authorize dependency
  installation, target mutation, signature bypass claims, or hardware writes.

## Decision

- `ADAPT`: install only these project-relevant packages into
  `.agents/skills/`, pinned to the inspected revision:
  `rsa-attack-techniques`, `code-obfuscation-deobfuscation`,
  `symbolic-execution-tools`, and `vm-and-bytecode-reverse`.
- `DEFER`: `anti-debugging-techniques`; no anti-debug mechanism has been
  observed in the current PSP/SMU artifacts.
- `REJECT` for current scope: bulk installation of the remaining HackSkills,
  including web exploitation, privilege escalation, credential access,
  lateral movement, evasion, reverse shell, and pivoting topics. They add no
  evidence for the BC-250 question and would broaden routing unnecessarily.

## Risks and controls

- Some generic playbooks are CTF/offensive-security oriented and may suggest
  attacks unsupported by the exact firmware. Treat every suggestion as a
  hypothesis and require direct artifact evidence.
- RSA-2048 factorization is not made feasible by installing an RSA playbook.
  First run only a bounded weak-key applicability audit against already
  extracted public parameters; never copy private/security material.
- No repository script will be executed. Only selected Markdown skill
  directories will be installed.

## Next check

After installation, load `rsa-attack-techniques` on the next agent turn and
route its attack-selection matrix against the already extracted `$KDB` public
keys. Change the decision only if a concrete weak-key prerequisite is observed.
