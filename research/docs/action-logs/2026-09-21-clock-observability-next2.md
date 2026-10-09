# 2026-09-21 Clock observability next2 — action log

Date/time: 2026-09-21 (Asia/Almaty, +05:00)  
Actor: `/root/clock_observability` (bounded offline source-analysis worker)  
Status: intent recorded before evidence/report creation; result pending.

## Intent

- **Target:** exact CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`); retained local driver sources `import/from-windows/Users/kukuruza/tmp_bc250/recon/linux-kiq-diff/gfx_v10_0-final.c`, `.../vcn-source-context/drivers/gpu/drm/amd/amdgpu/amdgpu.h`, and `.../vcn-source-context/drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c`.
- **Procedure:** run one bounded source test for the existing `amdgpu_asic_get_gpu_clock_counter` path and `gfx_v10_0_get_gpu_clock_counter` implementation. Assert the exact IP-10.3.6 branch, SMUIO TSC register addresses, hi/lo/hi tear-safe read, 100-MHz source comment, function-pointer registration, and absence of MCLK/UCLK/FCLK/DF/UMC counter or divider semantics in this path. No live probe, sysfs read, network, hardware, firmware, register, NVRAM, or ROM write.
- **Rationale:** the previous ATOM check classified `GET_SMU_CLOCK_INFO` as boot/model state. This continuation tests the independent counter path already present in local pinned driver source rather than repeating metrics aliases or SMU query 0x11/0x13.
- **Expected effect:** prove exactly what the independent counter measures and identify the missing physical-clock inputs needed for MCLK:UCLK:FCLK acceptance.
- **Rollback:** no inputs or source files are changed. Remove only this log, the matching report, and unique evidence directory if invalidated.
- **Acceptance event:** bounded verifier starts, exits, and emits machine-readable result, stdout, stderr, and exit status.

## Observed result (2026-09-21T14:05+05:00)

- **Command:** `python3 -B evidence/firmware-audit/20260921-clock-observability-next2/physical_counter_semantics_test.py`
- **Observed stdout:** `{"checks": {"failed": 0, "passed": 16, "total": 16}, "future_procedure": null, "ip10.3.6_lower": "0x002E", "ip10.3.6_upper": "0x002D", "output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-clock-observability-next2/physical-counter-semantics-result.json", "physical_mclk_uclk_fclk": false, "status": "PASS", "timebase": "100MHz SMUIO TSC"}`
- **Exit/status:** `0`; stderr empty (`0` bytes); 16/16 static checks passed.
- **Input readback:** CLV `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, request byte `0x24` at `0x7E5`; `gfx_v10_0-final.c` SHA-256 `d08eceff9418bd1fc99ab9024b7e2e7827629a093e0754a0ecb7e92c84a09ae0`; `amdgpu.h` SHA-256 `2a3c6653038867f7d66764d78fa0058278d0f151fe17750c7f0daa2522e3fe90`.
- **Observed semantics:** callback path and exact IP-10.3.6 addresses are proven statically. The counter is the SMUIO 100 MHz Golden TSC timebase; it is not an MCLK/UCLK/FCLK/DF/UMC counter or divider/crossing readback. No future hardware acceptance procedure was supplied.
- **Evidence:** `evidence/firmware-audit/20260921-clock-observability-next2/`; result JSON SHA-256 `cba24d0cbda9e9e76e1bd11ac2536c94d081878c1ac4ebcf6bd9e82354845b91`; verifier SHA-256 `972a9568ed4847c3f0f32e74f25b3baddae67b59443fbb9bc706cb0029d82325`; `SHA256SUMS.final` verifies `5/5 OK`. Report: `docs/research/2026-09-21-clock-observability-next2.md`.
- **No hardware/network/probe:** no board, sysfs, network, ROM/NVRAM/register/firmware action; `scripts/probe_bc250_clocks_readonly.py` was not invoked.

## G7 corrections during bounded test

1. The first verifier start exited `1` with a Python `SyntaxError` at line 48 (`unterminated string literal`) and stderr length `602` bytes. The source literal was corrected; no input changed.
2. The next run exited `1` with `15/16` checks because the expected `gfx_v10_0-final.c` hash was mistyped (`...762a...`); direct readback observed `d08eceff9418bd1fc99ab9024b7e2e7827629a093e0754a0ecb7e92c84a09ae0`. The expected hash was corrected and the verifier rerun to the PASS result above.
3. The final result and manifest were reopened and verified; no original source or ROM changed.

## Completion status

The exact local independent counter is established as a 100 MHz SMUIO reference timebase only. The requested independent physical MCLK/UCLK/FCLK observability remains blocked by the missing UMC/MCLK, UCLK divider, DF/FCLK counter/PLL, crossing-status, common-calibration, installed-driver identity, and read-only transport links named in the report.
