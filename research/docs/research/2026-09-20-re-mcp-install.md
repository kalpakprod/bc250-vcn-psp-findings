# Ghidra and Cutter MCP integration — 2026-09-20

Outcome: reused existing applications/plugins, added two Codex integrations, runtime-verified both against /bin/true. No firmware modifications. Root performed all work locally.

| Component        | Version / location                                                                              | Observed status                                                                                            |
| ---------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Ghidra           | 12.1.3 /home/OWNER/tools/ghidra_12.1.3_PUBLIC                                                | headless runtime passed with existing JDK21                                                                |
| GhidraMCP        | bethington6.0.0, plugin SHA256 b652a23b433786ac2e51e650fb6020cfdbb8743db6f58f16531fcac010d13522 | health, stdio MCP handshake222 tools, metadata/list/decompile passed                                       |
| Cutter           | 2.5.0, tools/cutter/run-cutter-bc250                                                            | GUI plugin loaded, fixture analysis available                                                              |
| CutterMCP native | 0.1.6, SHA256 b4073e5b72ef8694f07a0b2589d026825e2efa95fb2a1cf14fe009501a358e83                  | SDK Streamable HTTP handshake19 tools, health tool, ELF bytes, functions, disassembly/decompilation passed |
| Codex entries    | ghidra and cutter in ~/.codex/config.toml                                                       | read-back passed;20/16 read-only tools respectively                                                        |

Ghidra server127.0.0.1:8089 (ss displays IPv4-mapped loopback); Cutter127.0.0.1:8000. No system service or reboot autostart. Existing plugins reused; no need to reinstall applications. Ghidra6 plugin originally targets12.1.2; only exercised12.1.3 paths verified. Ghidra disassembly response empty without explicit auto-analysis: inconclusive. Full API compatibility, mutation tool safety, broad Procoder gate and GUI Ghidra plugin unrun. Cutter /health is404; cutter_health MCP tool passes. Existing Plus embedded integration remains unresolved; native runtime is separately verified.

LaurieWired1.4 source inspected, rejected for deployment here because its listener defaults wildcard and a newer pre-existing project integration was discovered. No downloaded LaurieWired code executed. Existing bethington6 tag pins commit8cd2078e10b9ba28b188cb84ce5b9051a904b995, Apache2.0. Historical7 build under/tmp is absent; using persistent6 pair is explicit, not claiming7.

Codex CLI registration passed. Whole unrelated-config equality assertion failed after CLI use; no claim of exact preservation. Pre-existing node_repl/1password/telegram names remain. Subsequent allowlist-only update was checked for exact parsed equivalence except its intended field. Do not publish full configuration. Current running assistant has not hot-loaded these tools; reconnect the client. Official configuration reference: https://developers.openai.com/codex/mcp (fetched2026-09-20).

Evidence: evidence/tooling/20260920-mcp/*.json and literal stdout/stderr. Start/stop/rollback instructions: tools/ghidra-mcp/README.md. BASELINE: pre-existing apps/plugins, no ghidra/cutter client entries. MODIFIED: both named entries present and read-only selected. ROLLBACK client removal commands documented, not executed; original firmware unchanged throughout.

## Post-client-restart result

Initial live check: both ports connection-refused, no native ghidra/cutter tools in current assistant inventory. Existing configurations remained present. Restarted existing launchers as transient user units bc250-ghidra-mcp-check and bc250-cutter-mcp-check (no boot enablement). Both listeners verified loopback-only. Fresh SDK tests exit0: Ghidra initialize/list222 tools/metadata/functions; Cutter initialize/list19 tools/ELF-byte read7f454c46. JSON/stdout/stderr/exit saved as _-restart_. Root assertions passed. This verifies external SDK access, NOT current assistant tool attachment. Client reconnection may be needed; cannot promise that it resolves runtime tool discovery. Baseline processes were stopped; modified runtime is active; rollback stop commands documented but not executed. No firmware changes.
