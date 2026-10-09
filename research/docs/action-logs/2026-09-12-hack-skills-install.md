# HackSkills installation action log

## Intent (2026-09-12, Asia/Almaty; before repository write)

- Actor: root agent.
- Operator request: install and run skills from
  `https://github.com/yaklang/hack-skills`.
- Evaluated revision: `c9a4b9ee8645eb60763eb4eef172f1ecb0a5b3e8`, MIT.
- Target directory: project-local `.agents/skills/`.
- Selected packages: `rsa-attack-techniques`,
  `code-obfuscation-deobfuscation`, `symbolic-execution-tools`, and
  `vm-and-bytecode-reverse`.
- Reason for subset: these four apply to the PSP verifier/key and firmware
  disassembly track. The other packages are predominantly web, credential,
  lateral-movement, evasion, and exploitation material outside this project's
  current need and are intentionally not activated.
- Procedure: use the standard Codex skill installer with the pinned revision
  and explicit destination; verify installed file list and hashes; do not run
  repository Yak scripts or install their tool dependencies.
- Expected effect: make the selected Markdown workflows available to agents on
  the next turn. Skills themselves are not executables.
- Rollback: remove only the four newly created project-local directories after
  confirming their exact paths. No automatic rollback is planned.
- Remaining step: on the next turn, explicitly invoke the RSA skill for a
  bounded weak-key applicability audit against existing public-key evidence.

## Result (2026-09-12, Asia/Almaty)

- PASS: the standard Codex installer installed all four selected packages into
  `.agents/skills/` from pinned revision
  `c9a4b9ee8645eb60763eb4eef172f1ecb0a5b3e8`.
- PASS: recursive directory comparison against the inspected checkout found no
  differences.
- PASS: six installed Markdown files were inventoried and hashed. Manifest:
  `docs/research/2026-09-12-hack-skills-installed.sha256`.
- PASS: no Yak build script, skill example command, binary, daemon, MCP server,
  network listener, or dependency installer was executed.
- Installed-state classification: project-local and available for routing on
  the next agent turn. Runtime state: documentation skill only; there is no
  standalone process to launch.
- UNRUN: the RSA weak-key applicability audit. Per the Codex installer
  lifecycle, newly installed skills become active on the next turn.
