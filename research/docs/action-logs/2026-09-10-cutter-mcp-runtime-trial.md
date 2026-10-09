# CutterMCP_native runtime trial

## Intent and scope

- Date: 2026-09-10T17:45:36.663084+00:00
- Project: `/home/OWNER/orca/projects/bc250`.
- Plugin: `CutterMCP_native v0.1.6`, pinned SHA-256 `b4073e5b72ef8694f07a0b2589d026825e2efa95fb2a1cf14fe009501a358e83`.
- Scope: bounded loopback-only protocol and health validation. The server was started by the operator from the isolated Cutter MCP dock.
- Safety: no rename, comment, prototype, filesystem, firmware, programmer, or hardware mutation was requested or called. The loaded Cutter view was still empty (`current_address=0x0`).

## Bind and endpoints

- `ss -ltnp` observed `127.0.0.1:8000` owned by Cutter's `AppRun` process (PID was observed locally and is not treated as a stable identifier).
- Browser/API documentation URL: `http://127.0.0.1:8000/docs` (HTTP 200 in the operator screenshot/status).
- REST health route: `GET /api/v1/health`.
- MCP route: `POST /mcp`.

## Results

- `GET /api/v1/health`: HTTP 200, JSON `{"current_address":"0x0","status":"ok"}`.
- MCP `initialize` with protocol `2024-11-05`: HTTP 200; server reported `CutterMCP`, version `0.1.6`; tools capability present.
- MCP `tools/list`: HTTP 200; 19 tools returned.
- Read-only tools: 16 (`health`, listing, decompile/disassembly, strings/segments/bytes, current address/function, xrefs, globals, entrypoints, and types).
- Mutation-capable tools exposed by the plugin: `cutter_rename_function`, `cutter_add_comment`, and `cutter_set_prototype`. None were called.
- No LAN/WAN bind was observed.

## Pending

- Load only the harmless fixture `/usr/bin/true` through Cutter's **File → Open file in memory** action, if the operator wants the next bounded analysis test.
- Then call read-only `cutter_list_segments`, `cutter_list_functions`, `cutter_list_strings` with small limits and compare the native plugin with the Plus standalone wrapper.
- Keep server stopped when the trial is complete.

## Operator UI observation (2026-09-10T17:51:53.129814+00:00)

- The operator attempted to open `/usr/bin/true` through Cutter's File → **Open file in memory** action. Cutter displayed `Не удалось отобразить новый файл в память` (could not display the new file in memory). No file was modified and the MCP server remained loopback-only/running. The next attempt should use a normal file-open path or launch the same isolated wrapper with `/usr/bin/true` as its command-line filename, rather than changing any firmware input.

## Diagnosis of the UI error (2026-09-10T17:57:34.935858+00:00)

- Cutter 2.5.0's `Ctrl+M` action is `Map File`, not normal binary opening. It is intended to map an additional file into an already loaded project, so invoking it from an empty Dashboard can produce the observed `Не удалось отобразить новый файл в память`. The safe normal path is `File → New Window` (`Ctrl+N`) and then the new-file dialog's **Open File → Select**, or launching `tools/cutter/run-cutter-bc250 /usr/bin/true`.

## Safe fixture trial (2026-09-10T18:33:30.946473+00:00)

- The operator loaded `/usr/bin/true` in a new Cutter window. Cutter recognized ELF64 x86-64 and completed analysis.
- Native MCP read-only calls all returned HTTP 200 with `isError=false`: `cutter_list_segments(limit=10)` reported 28 total segments; `cutter_list_functions(limit=10)` reported 36 total functions; `cutter_list_strings(min_length=4, limit=10)` reported 137 total strings; current address was `0x2560`.
- Additional native calls for `entry0` at `0x2560` succeeded: function detail, JSON disassembly, 16-byte read, current function, and entrypoints. No mutation tool was called.

## CutterMCP-plus comparison

- The pinned Plus standalone wrapper imported and returned matching semantic data for functions, segments, strings, current address/function, function detail, entrypoints, and 16-byte read. Import emitted a non-fatal `pydantic_settings` `IncompleteFieldDefinitionWarning`.
- Plus `disasm_by_func_text`, `disasm_text`, `disasm_json`, and `decompile` returned usable results for `entry0`.
- Plus `disasm_by_func_json` returned `json: null` because its implementation passes the already JSON-decoded response to `json.loads`; this is a wrapper bug, not a native server failure.
- Plus `list_strings(min_length=20, limit=10)` returned only 2 items because filtering is applied after fetching the first page. Native server-side filtering returned 10 matching items.
- Adoption result: use `CutterMCP_native` for the trial and treat Plus as a baseline/reference until its wrapper response handling and pagination/filtering are adapted.

## Second fixture session intent (2026-09-11T03:59:10.272374+00:00)

- Operator started the isolated Cutter MCP server for the harmless `/usr/bin/true` fixture. This session will run only bounded read-only HTTP/MCP calls to confirm current listener state and capture tool results before switching to copied BC250 executable modules.
- Expected effect: no file, firmware, register, programmer, board, or Cutter analysis mutation.
- Stop condition: any non-loopback listener, mutation request, unexpected tool error, or need for a missing operator fact.

## Second fixture session result (2026-09-11T04:00:22.636419+00:00)

- `ss -ltnp` observed only `127.0.0.1:8000`, owned by Cutter `AppRun`; no non-loopback listener was present.
- `GET /api/v1/health` returned HTTP 200 with `current_address=0x2560` and `status=ok`.
- MCP `initialize` (id 100) and `tools/list` (id 101) returned HTTP 200; server `CutterMCP` v0.1.6.
- Bounded read-only calls (ids 102–108) for segments, functions, strings, 16 bytes at `0x2560`, JSON disassembly, function detail, and decompilation all returned HTTP 200 with `isError=false`.
- Raw response files and hashes are in `evidence/firmware-audit/mcp/fixture-true-20260910/manifest.json`; manifest SHA-256 is `ae20d7ba4bd91b9395d5a119590003ea5506fba8c942bc466e4835238f46ab3c`.
- No mutation-capable tool was called. The server remains loopback-only.

## Additional module GUI/MCP session intent (2026-09-11T07:45:43.974346+00:00)

- Target: copied executable `evidence/firmware-audit/dump-2-extract/modules/0025_AmdNbioGfxARIDxe_pe32.bin`, SHA-256 `a1b5855a339875f09cfaec8a1c17abf54251bab2c43ff577bc3cdf8711e2f61c`.
- Route: launch a separate Cutter v2.5.0 read-only window with this file; if the native MCP dock can be started on an unused loopback port, run bounded read-only tools only and save a transcript under `evidence/firmware-audit/mcp/other-modules-20260911/`.
- No input/candidate/hardware writes; no mutation tools. The existing CoreUnlock server at `127.0.0.1:8000` must remain loopback-only and undisturbed.
- Stop if the GUI/session cannot be controlled or if a non-loopback bind/port conflict appears; existing Rizin evidence remains authoritative for static module coverage.

## Additional module GUI/MCP session result (2026-09-11T07:54:23.157942+00:00)

- A separate Cutter v2.5.0 process opened the copied `AmdNbioGfxARIDxe` module and recognized it as a Cutter window, but the managed computer-use provider could not enumerate or control the XWayland Cutter window (`app_not_found` for the PID).
- No MCP server was started in the extra window, no tool call was made, and the process was terminated without changing input or analysis files. The existing CoreUnlock native MCP transcript remains the only module-specific MCP evidence.
- Existing bundled Rizin reports cover the pending module set; this is recorded as an MCP coverage limitation, not a successful MCP analysis.

## Additional module GUI/MCP retry result (2026-09-11T08:52:08.966551+00:00)

- A second read-only attempt launched Cutter v2.5.0 with `AmdNbioGfxARIDxe`, but the managed Wayland/XWayland focus/screenshot path could not keep the Cutter window controllable; no Start Server action or MCP tool call was made.
- The extra process was terminated. Existing native MCP server/session was not changed; no mutation tool, firmware command, or hardware operation occurred.

## Native MCP server cleanup intent (2026-09-11T08:53:26.506093+00:00)

- The module-specific MCP work is complete for the current controlled session; additional GUI MCP attempts were inconclusive. Stop Cutter process PID `15275` hosting the loopback server at `127.0.0.1:8000` so the unauthenticated endpoint is not left running while idle.
- Expected effect: close only the CoreUnlock Cutter window and stop the listener; all saved transcripts and input files remain on disk. No analysis mutation was performed.
- Rollback: relaunch the pinned Cutter profile and reload the copied module for a future read-only session.

## Native MCP server cleanup result (2026-09-11T08:57:23.786239+00:00)

- `kill -TERM 15275` returned exit `0`; `ss` shows no listener on `127.0.0.1:8000`.
- Saved MCP transcript remains `evidence/firmware-audit/mcp/Bc250CoreUnlockDxe-20260911/manifest.json` SHA-256 `3df026be426c0fda0ebdf6a80ae041f4846f788ee5def841268969cc0d6f3e0a`.
- No input, candidate, firmware, register, programmer, or hardware mutation occurred.

## Controlled module MCP retry intent (2026-09-11T09:50:41.527155+00:00)

- Target: copied `AmdNbioGfxARIDxe` PE32 body, SHA-256 `a1b5855a339875f09cfaec8a1c17abf54251bab2c43ff577bc3cdf8711e2f61c`.
- Method change after prior GUI-control failure: launch a separate Cutter v2.5.0 process, focus its exact Hyprland window by address, move it from the special workspace to workspace 2, then use only the native MCP dock's Start/health controls.
- Server must bind only `127.0.0.1:8000`; no mutation tools or arbitrary commands. Save read-only transcript under `evidence/firmware-audit/mcp/AmdNbioGfxARIDxe-20260911/` if the session succeeds.
- Stop on focus/control failure, non-loopback listener, port conflict, or any mutation prompt.

## GUI focus safety incident and cleanup (2026-09-11T09:54:43.669804+00:00)

- During a controlled Cutter MCP retry, focus/screenshot did not remain on Cutter and displayed an unrelated user application containing credential UI. No credential values were read, copied, logged, or persisted.
- Temporary desktop screenshots created for visual debugging were deleted immediately; no project evidence was derived from them.
- The Cutter retry is treated as inconclusive and stopped. No MCP server was started, no mutation tool was called, and no hardware/programmer operation occurred.

## Controlled module MCP retry cleanup result (2026-09-11T09:56:49.056468+00:00)

- The extra Cutter process for `AmdNbioGfxARIDxe` was terminated after the focus safety incident; current original MCP server remains stopped.
- No target module was modified and no MCP tool call was made.

## GUI screenshot cleanup confirmation (2026-09-11T09:59:12.521510+00:00)

- Confirmed all temporary Cutter-retry screenshots were deleted from `/tmp`; no unrelated application content or credential value was retained.
