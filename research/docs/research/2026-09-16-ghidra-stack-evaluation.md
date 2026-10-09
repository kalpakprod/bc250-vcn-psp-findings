# Ghidra + Ghidra-MCP stack evaluation (Phase 0 record)

Date: 2026-09-16. Need: scriptable RE lens for 4700S/BC250 firmware RE with
decompiler + disassembly over HTTP for agent use. Existing capability: Cutter
2.5.0 AppImage + isolated profile, CutterMCP-native read-only trial passed on
fixture, Rizin 0.9.1 via bundle (see 2026-09-10-cutter-mcp-stack-evaluation).

## Item 1: Ghidra — ADOPT (installed, headless-verified)
- Source: NationalSecurityAgency/ghidra, release Ghidra_12.1.3_build
  (2026-08-18), asset `ghidra_12.1.3_PUBLIC_20260817.zip` 569,445,154 B,
  sha256 `93a5d11a9ad510622acaaf908c556a7b9b764d338e78a7567f3689bf5081fd54`.
- License: Apache-2.0 (standard Ghidra; LICENSE in install).
- Installed: `/home/OWNER/tools/ghidra_12.1.3_PUBLIC` (user-local, out of
  git). Requires JDK 21+: system has only JDK 17, so Temurin
  `jdk-21.0.12.1+1` installed user-local at `/home/OWNER/tools/`
  (`JAVA_HOME` must point there; Java 17 is rejected by the launcher).
- Evidence: `analyzeHeadless` import + auto-analysis + save of /usr/bin/true
  all REPORT succeeded (own run).
- Unknowns: none blocking. GUI certification: skipped (headless route used).

## Item 2: bethington/ghidra-mcp — ADOPT (headless server trial PASSED)
- Source: `bethington/ghidra-mcp`, cloned HEAD `5ed89be7c38f571d6a60ad76ed6a8012b0f58fce`
  (2026-09-16); prebuilt release v6.0.0 also fetched (ext zip sha256
  `867731de...`, bridge wheel `71939a89...`; release NOT installed — HEAD was
  built instead, version 7.0.0).
- License: Apache-2.0 (LICENSE head read). Inspected: README (headless +
  security sections), .env.template, build.gradle (Ghidra path property),
  HeadlessEndpointHandler/ManagementService/FunctionService route sources.
- Security: localhost-only by design (defaults 127.0.0.1:8089, refuses
  non-loopback bind without token); script-execution endpoints off by default;
  optional FILE_ROOT jail available. No auth on loopback — same posture as the
  Cutter MCPs; loopback-only is mandatory.
- Installed: extension unzipped to Ghidra install
  `Ghidra/Extensions/GhidraMCP/` (GUI path, unused); headless server jar built
  from source (`build/libs/GhidraMCP-7.0.0.jar`, BUILD SUCCESSFUL, Gradle
  backend, GHIDRA_INSTALL_DIR); bridge wheel installed via
  `uv tool install --python 3.12` (console `bridge-mcp-ghidra`; direct HTTP
  used in trials, bridge kept for MCP clients).
- Evidence (own runs, all loopback-verified via ss + server log):
  - server starts: 226 REST endpoints on 127.0.0.1:8089, /health healthy.
  - /load_program auto-detected PE32 + ELF (x86:LE:64).
  - CoreUnlock body (`7d22d802...`): 5 functions at file offsets
    1000/1037/1272/12b1/12d3 — matches the 09-11 MCP record (5 functions)
    and fresh Rizin 0.9.1 `afl` exactly.
  - /decompile_function(entry): Setup guard `*(int*)(...+0x1c4)==88000`
    (0x157C0) + L"Setup" — matches Rizin record.
  - /disassemble_function x5 (189 insns): immediates `115a870` x3, `0x98`,
    `157c0` — matches the SMN/Q3/skip record.
  - Params go in QUERY string, not JSON body (found by source read).
- Quirks recorded (do not re-debug): (1) JSON body params rejected with
  "Address or function name is required" — use query string; (2) per-program
  selection param (`program`) is IGNORED by the headless provider — run one
  program per server instance (restart to switch); (3) build needs
  GHIDRA_INSTALL_DIR env (GHIDRA_PATH is not read by Gradle).
- Unknowns: GUI-plugin path untested (not needed); 253-tool surface only
  spot-tested (load/list/decompile/disassemble/health); script endpoints stay
  OFF; FILE_ROOT jail not yet enabled (enable before untrusted inputs).
- Risks: unauthenticated loopback HTTP (same as Cutter MCPs); keep server
  stopped when not in use; never bind beyond 127.0.0.1.

## Item 3: Rizin-via-AppImage — ADOPT (parity lens, no install)
- Full-extracted Cutter 2.5.0 AppImage to /tmp (selective --appimage-extract
  with patterns yields nothing — use full extract), ran bundled Rizin 0.9.1
  with LD_LIBRARY_PATH on the same body: identical 5-function census.
- No repo/user install made; extraction is throwaway (/tmp/cutter-x).

## Effect on the project
- Ghidra 12.1.3 + headless GhidraMCP joins the stack as the primary scriptable
  MCP-RE lens next to Cutter (operator-named, plan PD3). Cutter remains
  mandatory for GUI work. Parity rule: trust a finding only when two of
  {Ghidra, Rizin, Cutter-MCP} agree.
- Recorded decision: `memory/decisions.md` D19. Server runtime: keep on
  127.0.0.1:8089 only while goal work is active; stop otherwise.
- Next: Phase 1 module census (C0A-stock 245 vs BC250 sets) driven through
  this server + existing parsers.
