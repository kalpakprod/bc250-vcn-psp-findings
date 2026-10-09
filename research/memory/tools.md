# Tool and script map

## Focused source areas

- `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/apcb/`: APCB analysis.
- `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/psp-policy/`: PSP policy, gasket, and mailbox analysis.
- `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/`: FV/FFS and UEFI analysis.
- `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/patch-build/`: candidate image builders.
- `archives/imported/recon-evidence/legacy-tmp-bc250-recon/`: reverse-engineering scripts, evidence, extracts, and probe helpers.
- `archives/imported/uefi-source/legacy-tmp-bc250-dxe/`: historical BC250 VCN UEFI probe and DXE source; do not run the archived binaries as a read-only check.
- `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/`: donor and upstream source repositories.

## Reuse rule

Inspect the existing script's inputs, outputs, assumptions, and current behavior before invoking it. Record versions and hashes for consequential output. A historical script may be incomplete or unsafe for a current target.

## Required external stack

- Cutter stable `v2.5.0` with bundled Rizin: `https://github.com/rizinorg/cutter`
- Adapted methodology: `https://github.com/zhaoxuya520/reverse-skill`
- Current MCP baseline: `https://github.com/restkhz/CutterMCP-plus`
- Newer MCP candidate: `https://github.com/Gog400/CutterMCP_native`
- Historical MCP baseline: `https://github.com/ap425q/CutterMCP`

Use `docs/research/2026-09-10-cutter-mcp-stack-evaluation.md` for pinned revisions and required checks.

## External BC250 documentation

- Local snapshot: `docs/reference/amd-bc250-docs/`
- Site mirror: `docs/reference/amd-bc250-docs/mirror/amd-bc250-docs/`
- Markdown source: `docs/reference/amd-bc250-docs/source/docs/`
- Per-file provenance: `docs/reference/amd-bc250-docs/MANIFEST.json`

## 2026-09-20 MCP runtime integration

Ghidra12.1.3 and persistent bethington GhidraMCP6.0.0 pair reused; historical7 headless build under/tmp absent. Cutter2.5/native0.1.6 and Ghidra6 MCP handshake/read-only smoke tests passed on /bin/true. Codex ghidra/cutter entries registered,20/16 read-only tools allowlisted; new client session required. Loopback8089/8000 only, no boot autostart. Ghidra launcher tools/ghidra-mcp/run-server; runtime/rollback README same directory. Report docs/research/2026-09-20-re-mcp-install.md records incomplete Ghidra disassembly check, config-preservation assertion failure and rejected unused LaurieWired download. Do not install another duplicate stack from stale memory.

Post-restart correction: session-owned Ghidra/Cutter processes stopped when client restarted. Both relaunched as transient user systemd units bc250-ghidra-mcp-check/bc250-cutter-mcp-check; fresh SDK tests passed. Current assistant inventory still lacks native MCP tools: distinguish SDK reachability from client attachment. No further reinstall needed.

## 2026-09-20 correction: UEFITool source is buildable and native extraction rerun

The earlier `2026-09-20-clv-menu-map-amibcp-uefitool` inventory said UEFITool had no runnable local binary and treated the preserved source as inventory-only. That statement is superseded for this host: the preserved official `LongSoft/UEFITool` source at commit `dac91b26733ca21cb204e41614c1b8c81cc50860` (`NE alpha 76`, BSD license) built successfully with existing CMake/g++/Qt6 dependencies in project-local evidence output. A real UEFITool GUI opened the exact CLV image, and its UEFIExtract sibling report/full dump exited `0`. Native `CbsSetupDxe` PE32 extraction is byte-identical to the existing census module (`7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`).

Evidence: `docs/research/2026-09-20-clv-uefitool-native-run.md`, `evidence/firmware-audit/20260920-clv-uefitool-native-run/native-run-result.json`, and action log `docs/action-logs/2026-09-20-clv-uefitool-native-run.md`. GUI tree interaction through Orca was unavailable because the provider returned `No top-level AT-SPI window is available for uefitool`; no guessed controls or mutating GUI action was used. AMIBCP availability remains a separate, unverified track.

## 2026-09-20 correction: pytest is available via a uv-tool shim

`/home/OWNER/.local/bin/pytest` (shebang `/home/OWNER/.local/share/uv/tools/pytest/bin/python`)
runs the repository suite: `/home/OWNER/.local/bin/pytest -q tests/` -> `16 passed` (2026-09-20).
The system interpreter `/usr/bin/python3` (3.14.7) has no `pytest` module, so the earlier
`Unrun: repo pytest suite (no pytest module on host)` note in
`docs/action-logs/2026-09-20-fd-v22-to-clv-port.md` was a path/resolution error, not a missing tool.
`python3 -m unittest` also works for the three test modules when `PYTHONPATH=.` is set
(`tests/conftest.py` supplies that path only for pytest).
