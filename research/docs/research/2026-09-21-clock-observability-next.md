# Physical-clock observability follow-up: no exact-CLV readback route established

Date: 2026-09-21 (Asia/Almaty, UTC+05:00)  
Owner: `/root/clock_observability`  
Scope: offline source/firmware analysis only; preserve the CLV `1800MHz` memory request.

## Conclusion

**No semantically defensible, exact-CLV read-only route to prove physical `MCLK:UCLK:FCLK = 1:1:1` was found.** The retained Linux SMU v11 source contains a candidate PLL-frequency API (`GET_SMU_CLOCK_INFO`), but its clock-table implementation and physical/live-read semantics are not recovered, the exact CLV image has no standard `55AA`/`ATOM` VBIOS header for this path, and the retained source is not identified as the installed BC-250 driver build. It is not an acceptance procedure and is not sufficient evidence of physical clocks or synchronous crossing.

The exact CLV donor's request is left unchanged: `AmdSetup+0x316` is byte `0x24` at ROM offset `0x7E5`, whose exact CLV IFR option label is `1800MHz`. This is a stored request, not a measured MCLK.

## Bound target and provenance

- Target: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes; SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Local manifest: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/manifest.json`, which records the 2026-09-16 RetroWeb redistribution for BC-250 board page ID 20611; uploader unknown; research-only, not reviewed or flash-approved.
- Request byte: body base `0x4CF` + `0x316` = absolute `0x7E5`; direct test re-read `0x24`. The option-label mapping is retained in `docs/research/2026-09-20-clv-menu-map-amibcp-uefitool.md` and related exact-CLV IFR evidence.
- Candidate driver source: `/home/OWNER/orca/projects/bc250/archives/imported/recon-evidence/legacy-tmp-bc250-recon/smu_v11_0.c`, 56,083 bytes, SHA-256 `3d4a62199f4b2dfea021b9c36f473fb161f10bd3aed89bcdc99f0d5eb2a5ccb1`. This imported source file is content-pinned by hash here; no upstream commit/revision or equivalence to the installed 7.2 BC-250 kernel binary was established.

## Candidate route tested, and its limit

The direct source slice is `smu_v11_0_atom_get_smu_clockinfo` (`smu_v11_0.c:364-388`), called by `smu_v11_0_get_vbios_bootup_values` (`:390-489`):

1. It supplies `clk_id`, `syspll_id`, and `GET_SMU_CLOCK_INFO_V3_1_GET_CLOCK_FREQ` to the `getsmuclockinfo` ATOM command index.
2. It delegates execution to `amdgpu_atom_execute_table(...)` and converts the returned `atom_smu_outputclkfreq.smu_clock_freq_hz` to 10-kHz units (`/ 10000`). The helper body itself has no direct `RREG32`, `WREG32`, or SMN read/write.
3. For FCLK, the call is revision-gated (`format_revision == 3`, `content_revision >= 2`) and stores to `smu->smu_table.boot_values.fclk` using the `SMU11_SYSPLL1_0_FCLK_ID` / `SMU11_SYSPLL1_2_ID` pair.
4. The same initializer seeds its UCLK field from the ATOM firmware-info table's `bootup_mclk_in10khz`; both the 3.1 and 3.3 structures flow into `smu_table.boot_values.uclk`.

Thus the direct bytes/source prove an **ATOM-command-reported boot/PLL frequency candidate** and a VBIOS firmware-info boot-MCLK source. They do **not** prove that the command table samples a live PLL/counter rather than returning or deriving a model/boot value; the table instructions are not traced. They also do not supply independent physical MCLK and UCLK readings or a synchronous-crossing/divider status. The exact-CLV direct header check found zero standard `55AA` + pointer-at-`+0x48` + `ATOM` VBIOS headers, so this generic ATOM route is not bound to the selected donor image by available evidence. The scan does not claim that no undocumented or computed path exists.

## Reuse check and non-repetition

- Existing counter-route artifacts were read, not rerun: `docs/research/20260920-clv-independent-clock-counter-route.md` and `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/`. The retained RLC register map is a `GFXCLK:REFCLK` hardware-counter prototype only; it is not relabelled FCLK, and existing exact-CLV applicability evidence does not map it to MCLK/UCLK/FCLK. It cannot prove the requested 1:1:1 state.
- Existing driver-metric and SMU Query 0x11/0x13 alias/state checks were already established and were not repeated in this task.
- The existing board/workstation clock script was **not invoked at all** (not even `--help`): the project incident `memory/incidents/2026-09-21-readonly-probe-help-side-effect.md` records that its entry point performs reads unconditionally, and the task explicitly forbade it. The imported `f1_atom_scan.py` was also not invoked; it has historical hard-coded image/output paths and is not scoped to this exact CLV input.
- Existing exact source route remains the imported SMU v11 source plus the prior external RLC header prototype. They are insufficient because neither gives an exact-CLV binding to independent MCLK/UCLK/FCLK hardware counters/PLL/divider readback and a crossing selector.

## Exact missing link / stop condition

Do not create or run a physical-clock probe until one local, exact-target source/disassembly chain establishes all of the following:

1. The BC-250-installed driver or exact firmware source/revision and the actual call/read path for the intended observation.
2. Board-applicable, separately attributable MCLK/UMC, UCLK, and FCLK/DF physical counter or live PLL-divider/status registers, including address provenance and any indirection.
3. Whether the read returns sampled hardware state versus a requested, committed-software, boot-table, or DPM model value; the counter/reference calibration and units (including GDDR6 rate conversion).
4. The exact UCLK ratio and synchronous-crossing/status selector. Equal exported numbers or equal configured divider targets are not this selector.
5. A documented read-only transport, known-good baseline, timeout and cleanup. No register write is authorized by this analysis.

Until that chain exists, no executable future hardware-acceptance procedure is supplied: the missing path semantics make one indefensible. The CLV `0x24` / `1800MHz` request remains a fixed, unmodified context for any later work.

## Reproduction and result

Command actually executed:

```text
python3 -B evidence/firmware-audit/20260921-clock-observability-next/clock_observability_source_test.py
```

Observed stdout (literal):

```text
{"atom_vbios_headers": [], "candidate_path": "API-reported boot/PLL frequency candidate; not proven physical counter, current live frequency, or exact-CLV path", "checks": {"failed": 0, "passed": 12, "total": 12}, "output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-clock-observability-next/clock-observability-source-result.json", "request": {"AmdSetup_relative_offset": "+0x316", "absolute_offset": "0x7E5", "ifr_label": "1800MHz", "meaning": "stored request only; not a measured frequency", "value": "0x24"}, "status": "PASS"}
```

- Exit status: `0` (`source-test.exit_status`); stderr: empty (`0` bytes).
- Result: 12/12 static source/byte assertions PASS. This PASS validates the offline discrimination, not a hardware measurement or clock capability.
- Machine result SHA-256: `504e67618d0bf6ece9ca0c5fc543e12c38f1a0f5cfae1d9f652431be40322fff`.
- Verifier SHA-256: `8cfc5918b7228f26b8ef3d7ae6a3c01176e75457794e499120e0a0904a161436`.
- Stdout SHA-256: `791b0fde21856de7ffad1e7f4ea6f84e314bbe15b7749e26a7dbe9a21a01b65d`; stderr SHA-256 (empty): `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Hardware, network, sysfs, ROM/NVRAM mutation, register writes, and `probe_bc250_clocks_readonly.py` execution: **not performed**.

## Artifact paths

- This report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-clock-observability-next.md`
- Matching action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-clock-observability-next.md`
- Unique evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-clock-observability-next/`
  - `clock_observability_source_test.py`
  - `source-test.stdout`
  - `source-test.stderr`
  - `source-test.exit_status`
  - `clock-observability-source-result.json`
  - `SHA256SUMS.final`

Evidence class: `observed-bytes` + `static-analysis`. Hardware verification: **unrun**. The conclusion remains bounded to available local source and exact donor image; calculated/computed alternate register paths are not excluded.
