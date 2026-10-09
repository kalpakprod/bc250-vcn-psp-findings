# GhidrAssistMCP evaluation

State: ADAPT, user explicitly requested installation. Need: alternate Ghidra decompiler/disassembly/pcode MCP for offline BC250 investigation. Existing GhidraMCP remains alongside it.
Source: https://github.com/symgraph/GhidrAssistMCP tag2.11.0 commit0d412d1fe3203e98a32f7dc70df21dc8f6f57131, MIT, inspected2026-09-23. Release asset pinned by SHA256 in tools/ghidrassist-mcp/README.md. README, build.gradle, extension.properties, backend/server/headless/start-script code inspected, release class signatures inspected with javap.

Risks: stock backend enables many mutation tools, only scripts/import/export disabled by default. Loopback alone is not authentication or a boundary against other local users. Added project-owned GhidraScript wrapper exposes explicit read-only subset before server.start, plus matching client allowlist. Program fixture /bin/true, not original firmware. No outward binary upload configured. Remote GitHub used only for package/source retrieval.

Compatibility: release class major65 with installed JDK21 and Ghidra12.1.3. Source build requires25, no rebuild claimed. Read-only wrapper compilation and live start verified. Existing GhidraMCP8089 preserved. New8090 bound127.0.0.1, not network-wide. No system packages/services/autostart added. Named extension symlink installation is within explicit user request. Codex config project-local.

Verification evidence: tools/ghidrassist-mcp/smoke-result.json, runtime-first.log, transaction/VERIFICATION.txt. First extended get_code smoke failed because response was async, not because decompiler failed; retained stderr and fixed client to retrieve actual task result, assertions not removed. Config baseline0 -> modified21 -> rollback0 tools, restored hash equals empty baseline, patch reconstructs exact modified config. Baseline reflects prior absence of project-local entry, not absence of all other MCPs.

Limits: stock GUI defaults are not restricted by this wrapper. Current client tool catalog needs reconnect. Single-function smoke is not full-tool validation and not firmware/hardware proof. Full uninstall not executed. Runtime persistence after reboot not configured. Original signed firmware untouched.
