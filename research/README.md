# AMD BC-250 reverse engineering

This repository is the evidence and development workspace for studying the AMD BC-250 board, firmware, boot chain, PSP/APCB/SMU/VCN behavior, UEFI/DXE components, and host-side driver paths.

## Start here

Start with [current context](docs/CURRENT-CONTEXT.md) and the
[repository map](docs/repository-layout.md). Dated inventories are historical.
For a topic-by-topic route through the workspace, use [the documentation index](docs/INDEX.md).

1. Read `AGENTS.md`.
2. Read `memory/INDEX.md` and only the topic needed for the task.
3. Read `docs/knowledge-sources.md` before using imported reports or donor material.
4. Read the focused skill under `.agents/skills/` before entering its domain.
5. Keep the original artifact immutable. Record hashes and action logs.

## Workspace

All 218,616 original import files and 1,305 later files were routed by topic with source/destination SHA-256 journals; the complete live rehash passed. Semantic review of opaque and private material remains open. See [the import catalog](docs/import-catalog.md). Recovery ZIPs are under `archives/snapshots/`, not in the root. New plans belong in `.procoder/plans/`; `specs/` is historical.

## Primary stack

- Cutter `v2.5.0` with bundled Rizin is the analysis platform.
- `reverse-skill` is adapted for routing and evidence discipline.
- `CutterMCP-plus` is the current MCP integration baseline.
- `CutterMCP_native` is the newer C++ MCP candidate to test against the baseline.
- `CutterMCP` is retained as a historical fallback.

The adoption decision and the inspected revisions are in `docs/research/2026-09-10-cutter-mcp-stack-evaluation.md`.

## Scope

Research is limited to hardware, firmware, software, and data that the user owns or is authorized to inspect. Reverse engineering, disassembly, decompilation, emulation, parser development, and controlled testing are expected. Legal scope, data protection, recovery, and explicit approval remain primary constraints.

No firmware has been flashed by repository bootstrap. A build or parser result is not hardware verification.
