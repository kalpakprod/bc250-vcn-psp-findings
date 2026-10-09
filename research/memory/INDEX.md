# BC250 project memory

Start at [current context](../docs/CURRENT-CONTEXT.md) for the active task,
operator constraints and primary local evidence. Dated hardware observations
are not a statement of current board state.

Created 2026-09-10 from the imported BC250 corpus and the repository-contract patterns observed in `vpn-ops` and `homelab`. Read only the topic needed for the current task and read that file to its end.

| Topic                                                                                     | When to read                                                                                             |
| ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| [Project state](project-state.md)                                                         | mission, current phase, and dated status                                                                 |
| [Corpus](corpus.md)                                                                       | source paths, provenance, import boundary, and exclusions                                                |
| [Decisions](decisions.md)                                                                 | durable choices and conditions for review                                                                |
| [Evidence model](evidence-model.md)                                                       | evidence classes and claim discipline                                                                    |
| [Open questions](open-questions.md)                                                       | unresolved PSP, APCB, VCN, SMU, UEFI, and hardware links                                                 |
| [OC review corrections](oc-recheck.md)                                                    | withdrawn sync/voltage claims, OC candidate no-go, measurement limits, PPTable producer/consumer mapping |
| [Tools](tools.md)                                                                         | existing analyzers, build paths, and reuse map                                                           |
| [Firmware and VCN audit](firmware-audit.md)                                               | current dump, extraction, module comparison, and VCN evidence state                                      |
| [Cutter stack evaluation](../docs/research/2026-09-10-cutter-mcp-stack-evaluation.md)     | pinned Cutter, reverse-skill, and MCP adoption status                                                    |
| [Instincts](../INDEX.md)                                                                   | atomic rules for tasks in this domain                                                                    |
| [Thumb halfword byte-order correction](incidents/2026-09-21-thumb-halfword-byte-order.md) | LLVM Thumb disassembly versus little-endian raw bytes                                                    |
| [Incidents](../INDEX.md)                                                                   | failures, corrections, and recovery records                                                              |

Memory stores paths, findings, and decisions only. It never stores credentials, tokens, private keys, raw security material, or unredacted personal exports.
