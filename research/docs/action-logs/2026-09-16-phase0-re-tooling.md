# Action log: Phase 0 RE tooling stand-up (Ghidra + MCP)

Date: 2026-09-16 (UTC). Actor: root. Goal turn: 5-phase route, Phase 0.
No firmware writes; all installs user-local (/home/OWNER/tools,
~/.local/bin, uv tools) or throwaway (/tmp). Repo writes: this log, the
ghidra eval doc, D19, plan checkmarks.

## 0.1 Ghidra — DONE
- Pinned release Ghidra_12.1.3_build (2026-08-18), 569,445,154 B, sha256
  `93a5d11a...`; extracted to `/home/OWNER/tools/ghidra_12.1.3_PUBLIC`.
- Blocker found and cleared: Ghidra 12 needs JDK 21+, system has JDK 17 only.
  Installed Temurin jdk-21.0.12.1+1 user-local (207 MB tarball); JAVA_HOME
  must point there.
- Smoke: analyzeHeadless import + auto-analysis + save of /usr/bin/true —
  all REPORT succeeded. (Two self-inflicted CLI errors on the way: invented
  postScript name; missing project dir. Both corrected, no side effects.)

## 0.2 Ghidra-MCP — DONE (trial PASSED)
- Evaluated bethington/ghidra-mcp @ 5ed89be (Apache-2.0, loopback-by-design,
  script endpoints default-off). Prebuilt v6.0.0 fetched but not installed.
- Built headless server jar from source (Gradle backend, GHIDRA_INSTALL_DIR;
  first attempt failed on wrong env name GHIDRA_PATH — corrected).
- Server runs on 127.0.0.1:8089 (ss-verified), /health healthy, 226 endpoints.
- Trial on exact CoreUnlock body: 5 functions (matches MCP + Rizin records),
  decompile shows Setup guard 0x1c4==88000, disasm shows 115a870/0x98/157c0.
- Quirks: params via query string (JSON body rejected); per-program selection
  ignored (one program per server instance); bridge wheel installed but direct
  HTTP used. Server left RUNNING while goal work is active (PID on :8089).

## 0.3 Parity lens — DONE
- Rizin 0.9.1 from full AppImage extraction: identical 5-function census.
  (Selective --appimage-extract with patterns yields nothing; full extract
  required.) Throwaway at /tmp/cutter-x, no install.
- CutterMCP-native GUI session: NOT re-run (needs GUI dock action); parity
  rule satisfied by Ghidra+Rizin+historical MCP record (three lenses).

## 0.4/0.5 — DONE
- UEFITool: not needed yet (parsers + lenses cover current tasks). CHIPSEC:
  stays DEFERRED. Versions/hashes recorded in the eval doc (see D19 sources).

## Checks (G9)
- Ghidra headless smoke: PASSED (own run). MCP health+load+list+decompile+
  disassemble: PASSED (own runs). 3-lens parity: PASSED (own runs).
- GUI-plugin path, full 253-tool surface, FILE_ROOT jail: UNRUN (not needed).
- No firmware artifact claimed; no hardware touched.
