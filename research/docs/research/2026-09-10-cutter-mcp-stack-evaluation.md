# Cutter and MCP stack evaluation

> Historical evaluation and install record. Initial TRIAL/unrun statements are dated 2026-09-10, not current runtime status. See the later 2026-09-16-ghidra-stack-evaluation.md and memory/tools.md before choosing a current tool; do not repeat installation or change global configuration from this document.

Date: 2026-09-10 UTC
Scope: GitHub repository metadata, default-branch commits, releases, READMEs, and selected implementation files. No third-party code was installed or executed. No client-global MCP configuration was changed.

## Decision

The BC250 primary reverse-engineering stack is fixed as:

1. **Cutter + bundled Rizin** as the desktop reverse-engineering platform. Use the stable Cutter `v2.5.0` release by default.
2. **`reverse-skill` as an adapted methodology and routing source**, not as an unconditional installer or as a license to load unrelated penetration-testing modules.
3. **`CutterMCP-plus` as the current MCP integration baseline** requested by the user. Treat runtime adoption as a bounded trial until local Cutter 2.5.0 compatibility and security checks pass.
4. **`CutterMCP_native` as the newer MCP candidate**. It has the freshest relevant implementation release found in the search and should be compared in a local trial before replacing the baseline.
5. **The original `CutterMCP` as a historical compatibility reference**, not the default deployment.

Accepted design is not the same as installed or runtime-verified state. The current status is `installed / partially runtime-verified`: Cutter starts and reports `2.5.0-HEAD-a6f6ad7`, the native plugin loads in the isolated profile, and the Plus wrapper imports in its isolated Python environment. The MCP server handshake and tool calls are still unrun because the server is started from the Cutter MCP dock action.

## Item assessments

### 1. Cutter

State: `ADOPT` as the platform.

- Repository: [rizinorg/cutter](https://github.com/rizinorg/cutter)
- License: GPL-3.0
- Stable release: [v2.5.0](https://github.com/rizinorg/cutter/releases/tag/v2.5.0), published 2026-06-30.
- Development branch latest inspected commit: `f2c67790a875b027628fc5203e233522210b6c19`, 2026-08-22, `Add rz-frida plugin to the cutter releases (#3656)`.
- README says Cutter is an open-source reverse-engineering platform powered by Rizin and provides Linux, macOS, and Windows releases.

Reason: this is the requested engineering platform and the MCP implementations target Cutter's live analysis state. Pinning the stable release avoids silently following the moving `dev` branch.

Unknowns: the exact Rizin revision bundled in the selected platform package and local plugin ABI compatibility still need to be checked on the target machine.

### 2. `reverse-skill`

State: `ADAPT`.

- Repository: [zhaoxuya520/reverse-skill](https://github.com/zhaoxuya520/reverse-skill)
- License: MIT
- Default branch latest inspected commit: `7e2097fd90d25c2f976f6eba26d6c00aa88051df`, 2026-09-03, `docs: record issue and PR security integration`.
- Release: [v1.0.1](https://github.com/zhaoxuya520/reverse-skill/releases/tag/v1.0.1), published 2026-08-08.
- Inspected: `README.md`, `README_AI.md`, `RULES.md`, `skills/MASTER-ROUTING.md`, `skills/radare2/SKILL.md`, and `skills/firmware-pentest/SKILL.md`.

Useful parts: task routing, evidence chains, field-journal discipline, scope gates, tool indexes, and the static-to-dynamic reverse-engineering workflow.

Not adopted unchanged: the repository is a broad security router with penetration-testing, CTF, auto-bootstrap, and client-global integration paths. It has no Cutter-specific route in the inspected tree. The BC250 project uses only the adapted methodology and the local `cutter-reverse-engineering` skill. No automatic tool installation or unrelated security route is enabled by this decision.

### 3. `CutterMCP-plus`

State: `ADOPT` as the current MCP baseline; runtime status remains `TRIAL`.

- Repository: [restkhz/CutterMCP-plus](https://github.com/restkhz/CutterMCP-plus)
- License: GPL-3.0
- Default branch latest inspected commit: `69613e4525b08d11caf5ec6137ac3185626a79ba`, 2026-03-17, `Refactor HTTP server and document streamable MCP setup`.
- No GitHub release was published.
- Inspected: `README.md`, `mcp_plugin.py`, `mcp_server.py`, and `requirements.txt`.
- Declared dependencies: `mcp==1.12.2`, `requests==2.32.4`, and `uvicorn==0.35.0`.

Strengths:

- The plugin exposes structured JSON endpoints for functions, decompilation, disassembly, strings, segments, bytes, variables, xrefs, types, comments, renaming, and prototypes.
- The standalone wrapper supports stdio by default and optional Streamable HTTP.
- The plugin defaults to `127.0.0.1:8000` and the wrapper defaults to `127.0.0.1:9000`.
- The code bounds request bodies and integer parameters and uses a command lock around Cutter calls.

Risks and required controls:

- There is no authentication. Keep both plugin and wrapper on loopback. Do not expose them on LAN, WAN, a tunnel, or a public reverse proxy.
- Mutating tools exist. Require explicit per-call approval for rename, comment, type, and prototype changes.
- The plugin builds several `cutter.cmd` strings from request values. Input quoting and command-injection behavior must be tested and fixed or bounded before any non-loopback use. The project policy is loopback-only even after a local test.
- The README's CTF and malware examples are not evidence of BC250 compatibility.

### 4. `CutterMCP_native`

State: `TRIAL` as the newer candidate.

- Repository: [Gog400/CutterMCP_native](https://github.com/Gog400/CutterMCP_native)
- License: GPL-3.0
- Default branch latest inspected commit: `f38a404c88f8abc25734a88e553d66ef4def10b3`, 2026-08-07, `Delete .idea directory`.
- Latest release: [v0.1.6](https://github.com/Gog400/CutterMCP_native/releases/tag/v0.1.6), published 2026-08-07.
- Release assets include Linux, macOS, and Windows plugin binaries with paired SHA-256 files and `relink_plugin.py`.
- README targets Cutter `2.5.0`, uses a native C++20 plugin, and reports CI builds for all three platforms. The README explicitly says Linux and Windows were CI-built but not manually verified on the developer's machines.
- Inspected: `README.md`, `CMakeLists.txt`, `CutterMCP.cpp`, `core/McpHttpServer.cpp`, `core/McpHttpServer.hpp`, `core/Tool.hpp`, `core/ToolRegistry.cpp`, `tools/McpRenameFunctionTool.cpp`, `tools/McpAddCommentTool.cpp`, and `tools/McpSetPrototypeTool.cpp`.

Strengths:

- Direct MCP JSON-RPC endpoint at `/mcp` inside the native Cutter plugin.
- No Python MCP bridge is required for the native plugin.
- The plugin registry publishes tool schemas and provides REST plus MCP access.
- The release provides platform binaries and checksums.
- The UI defaults to `127.0.0.1` and allows an explicit host and port.

Risks and required controls:

- There is no authentication. Keep the host set to `127.0.0.1` and verify the actual listening address before use.
- The native plugin is coupled to the Cutter SDK and Qt/Rizin ABI. Pair it with Cutter 2.5.0 and test the exact platform package.
- Mutating tools are present. Review input quoting in comment and prototype paths before use. Do not expose the endpoint beyond loopback.
- The release is new and has no stars or forks in the inspected metadata. This is not a quality verdict, but it makes local compatibility testing mandatory.

### 5. Original `CutterMCP`

State: `KEEP` as a historical fallback and comparison source.

- Repository: [ap425q/CutterMCP](https://github.com/ap425q/CutterMCP)
- Canonical repository name returned by GitHub: `ap425q/CutterMCP`
- License: Apache-2.0
- Default branch latest inspected commit: `cb9432802a98498769ff7bfab28391e8e637bc04`, 2025-08-02.
- Latest release: [v2.0](https://github.com/ap425q/CutterMCP/releases/tag/v2.0), published 2025-06-01.
- Inspected: `README.md`, `bridge_mcp_cutter.py`, `src/CutterMCPPlugin.py`, and `requirements.txt`.

The implementation is useful as the original Python bridge and API baseline. It starts its plugin HTTP server on `('', 8000)`, which binds all interfaces, and several mutating handlers interpolate request values into Cutter commands. It is therefore not the default stack and must not be run as-is on a networked host.

## Fresher implementation search

GitHub repository search for `CutterMCP` returned four relevant implementation repositories:

- `Gog400/CutterMCP_native`, latest push 2026-08-07, release `v0.1.6`.
- `restkhz/CutterMCP-plus`, latest push 2026-03-17, no release.
- `ap425q/CutterMCP`, latest push 2025-08-02, release `v2.0`.
- `tjarrett9037/GhidraMCP-and-CutterMCP-Speed-and-Reliablility-Testing`, latest push 2026-04-24, a test/log repository rather than a Cutter MCP implementation.

`CutterMCP_native` is the freshest relevant implementation found. No newer mature Cutter MCP server was found in the GitHub repository search. General web search was not available because the Serper key is not configured; this is recorded as a research limitation, not silently treated as complete internet coverage.

## Installation record

- Cutter AppImage: `tools/cutter/Cutter-v2.5.0-Linux-x86_64.AppImage`, release digest `b8ad215d7a9e2af9e1f463511229f16e1f4745a0fb541413e5f4787f949ac0cf`, 144423416 bytes.
- Isolated Cutter profile: `tools/cutter/profile/`. The native plugin is installed at `tools/cutter/profile/data/rizin/cutter/plugins/native/libCutterMCP_native.so` and has the verified release digest `b4073e5b72ef8694f07a0b2589d026825e2efa95fb2a1cf14fe009501a358e83`.
- Plus source: `tools/cutter/vendor/CutterMCP-plus/`, commit `69613e4525b08d11caf5ec6137ac3185626a79ba`, archive digest `20e4b9c2b7833e3d12942f0ef154c3db839e27fa34f9fcb3fa56f30a196c5793`.
- Plus wrapper environment: `tools/cutter/.venv/`, Python 3.13.15, requirements lock at `tools/cutter/requirements.lock.txt`.
- Cutter direct version and help checks with `QT_QPA_PLATFORM=xcb`: passed. The native plugin load check reported one user native plugin loaded.
- Plus embedded Python plugin check: inconclusive for Plus itself because the official Cutter sample plugin fails the same Shiboken C++ conversion check in this AppImage. The Plus standalone wrapper import check passed.
- MCP server endpoint: not started and not yet handshaken. It remains loopback-only by policy.
- User-local Omarchy launcher: `~/.local/share/applications/bc250-cutter.desktop`, launching `tools/cutter/run-cutter-bc250`; desktop database refresh and `omarchy menu refresh` passed.

## Required first local trial

1. Install or obtain Cutter `v2.5.0` without changing global client configuration.
2. Pin the selected MCP source revision and record its license and source hash.
3. Start the plugin on `127.0.0.1` only.
4. Verify `/health`, MCP `initialize`, `tools/list`, one read-only function query, one decompilation/disassembly query, and one bounded byte read.
5. Verify that the listener is loopback-only and that no unauthenticated LAN address responds.
6. Keep mutation tools disabled or manually approved. Test input quoting with harmless fixture strings before enabling them.
7. Compare `CutterMCP-plus` and `CutterMCP_native` on the same small binary and record tool coverage, latency, failures, and cleanup.
8. Choose the runtime implementation only after the local checks pass. Do not call the stack installed or verified from metadata alone.
