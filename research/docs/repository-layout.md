# BC250 repository layout

Updated 2026-09-27. Start at `docs/CURRENT-CONTEXT.md`.
Dated inventories remain historical evidence, not current instructions.

| Location                                                  | Role and placement rule                                                             |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `AGENTS.md`                                               | Single current project contract                                                     |
| `README.md`                                               | Human entry point                                                                   |
| `memory/`                                                 | Summaries, decisions and evidence pointers, start at `INDEX.md`                     |
| `.procoder/plans/`, `.procoder/specs/`, `.procoder/todo/` | Current planning and local task details; Plane remains task authority               |
| `specs/`                                                  | Historical plans, no new plans here                                                 |
| `docs/research/`                                          | Research synthesis and independent reviews                                          |
| `docs/action-logs/`                                       | Append-only intent and result ledger                                                |
| `docs/runbooks/`, `docs/guides/`                          | Procedures, not hardware authorization                                              |
| `docs/reference/`                                         | External references, separate mirrors from conclusions                              |
| `scripts/`, `tests/`                                      | Repeatable tooling and checks                                                       |
| `candidates/`                                             | Sources and products with provenance; preserve identities                           |
| `firmware-flash-pkg/`                                     | Staged flash packages with hashes and recovery context                              |
| `evidence/hardware/`                                      | Hardware originals, including local boardview                                       |
| `evidence/`, `dump/`                                      | Captures and originals, no automatic deduplication                                  |
| `import/`                                                 | Original SHA-256 manifests and migration notes; raw source files routed, not zipped |
| `tools/`                                                  | Installed tools and wrappers, keep existing paths                                   |
| `reports/`                                                | Generated audits, check outputs and search logs                                     |
| `scratch/`, `Build/`                                      | Scratch and builds, no automatic deletion                                           |
| `old/session-exports/`                                    | Private local conversation history, not opened or published here                    |
| `.git/`, `.empryo/`, other host state                     | VCS and agent state, never rearrange                                                |
| `archives/snapshots/snapshot-*.zip`                       | Local recovery snapshots, byte-verified after the 2026-09-27 move                   |

## Стандарт входа

- `README.md` отвечает на вопрос «с чего начать»; `AGENTS.md` задаёт правила работы; `docs/CURRENT-CONTEXT.md` указывает действующую задачу и не заменяет план.
- `.procoder/plans/` и `.procoder/todo/` содержат действующие планы и статусы. `docs/research/` хранит проверяемые выводы; `docs/action-logs/` сохраняет порядок действий и не редактируется задним числом.
- `CHANGELOG.md` фиксирует значимые изменения, `MISTAKES.md` — ошибки и предотвращающие правила, `SNAPSHOTS.md` — адреса и условия восстановления.
- Для новой или переписываемой спецификации применять `Clausative` (`AndyVictors/clausative`, commit `6c644bd3c9ee6da17b3880a66855cc985fd41a40`, `Style.md`) вместе с procoder. Термины должны быть постоянны, утверждения однозначны, разделы короткие. Русский текст остаётся русским.
- Сырой импорт и непроверенные внешние данные не становятся действующими правилами. У каждого перенесённого файла должна быть исходная запись, назначение, хеш и статус проверки.

## Relocations on 2026-09-27

Independent unlock review:
`docs/research/2026-09-15-independent-unlock-review.md`.
Five VCN check/search logs: `reports/vcn-plan-checks/`.
The audit manifest records original/destination paths and hashes.
Historical action logs retain old paths with a relocation note.

## Promotion rule

Promote imported material only after checking provenance, duplication, generated
status, sensitive content and validation needs. A clean Git clone does not
contain all local evidence. Filesystem inventory is not the Git index.

Audit: `reports/repository-audit-20260927/`.
An automated content scan is not a semantic review of every source file.
