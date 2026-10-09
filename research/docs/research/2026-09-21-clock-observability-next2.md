# Physical-clock observability next2: SMUIO timebase counter found, MCLK/UCLK/FCLK path still missing

Date: 2026-09-21 (Asia/Almaty, UTC+05:00)  
Owner: `/root/clock_observability`  
Scope: offline source analysis only; no board, sysfs, network, register, firmware, NVRAM, ROM, or probe action.

## Conclusion

A real independent hardware-counter path exists in the retained local AMDGPU source, but it is **not** an MCLK/UCLK/FCLK measurement path. `amdgpu_asic_get_gpu_clock_counter()` dispatches to `gfx_v10_0_get_gpu_clock_counter()`. For the `IP_VERSION(10, 3, 6)` branch, the function reads the SMUIO `GC_10_3_6` Golden TSC counter at DWORD register indices `0x002D` (upper) and `0x002E` (lower), with `BASE_IDX=1`, using a tear-safe upper/lower/upper sequence. The source explicitly documents this SMUIO TSC as a **100 MHz timebase**.

This establishes an independent reference/timebase counter, not a physical memory-clock or fabric-clock counter. The local code still contains no exact MCLK/UMC counter or PLL readback, no UCLK divider/ratio status, no FCLK/DF physical counter or PLL readback, and no synchronous-crossing selector. Therefore no physical `MCLK:UCLK:FCLK = 1:1:1` acceptance procedure is defensible yet.

The exact CLV donor request remains unchanged: `AmdSetup+0x316` is `0x24` at ROM offset `0x7E5`, the exact CLV IFR-labelled `1800MHz` request; it remains a stored request, not a measurement.

## Exact provenance and addresses

- CLV target: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Driver source: `/home/OWNER/orca/projects/bc250/archives/imported/recon-evidence/legacy-tmp-bc250-recon/linux-kiq-diff/gfx_v10_0-final.c`, SHA-256 `d08eceff9418bd1fc99ab9024b7e2e7827629a093e0754a0ecb7e92c84a09ae0`.
- Callback declaration/dispatch header: `/home/OWNER/orca/projects/bc250/archives/imported/recon-evidence/legacy-tmp-bc250-recon/vcn-source-context/drivers/gpu/drm/amd/amdgpu/amdgpu.h`, SHA-256 `2a3c6653038867f7d66764d78fa0058278d0f151fe17750c7f0daa2522e3fe90`.
- IP-family source: `/home/OWNER/orca/projects/bc250/archives/imported/recon-evidence/legacy-tmp-bc250-recon/vcn-source-context/drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c`, SHA-256 `18920f314d4e273d32400ef1295179264999b4aa400f402fefa149212380a940`.

The path is byte-backed in the retained source:

```text
amdgpu_asic_get_gpu_clock_counter(adev)
  -> adev->asic_funcs->get_gpu_clock_counter
  -> gfx_v10_0_get_gpu_clock_counter
  -> IP_VERSION(10, 3, 6)
  -> SMUIO mmGOLDEN_TSC_COUNT_UPPER_GC_10_3_6 = 0x002D (BASE_IDX 1)
  -> SMUIO mmGOLDEN_TSC_COUNT_LOWER_GC_10_3_6 = 0x002E (BASE_IDX 1)
```

`gfx_v10_0_gfx_funcs` registers `.get_gpu_clock_counter = &gfx_v10_0_get_gpu_clock_counter`. The read performs upper, lower, upper; if the upper value changes it rereads the lower half and uses the new upper value; it returns `clock_lo | (clock_hi << 32ULL)`. The same function comment states: `The SMUIO TSC clock frequency is 100MHz`.

## What the counter proves, and what it does not

| Question                                            | Result                                                                                       | Evidence class              |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------- |
| Is there an independent hardware counter read path? | Yes: SMUIO Golden TSC, accessed by `RREG32_SOC15_NO_KIQ`                                     | `static-analysis`           |
| What does it count?                                 | A 100 MHz SMUIO TSC timebase, according to the source comment and register names             | `static-analysis`           |
| Is it MCLK/UMC?                                     | No such identity appears in the function; no UMC/MCLK term or register is read               | `static-analysis`           |
| Is it UCLK or a divider readback?                   | No UCLK/divider/status field appears in the function                                         | `static-analysis`           |
| Is it FCLK/DF or a PLL readback?                    | No FCLK/DF/PLL term or register appears in the function                                      | `static-analysis`           |
| Does it prove `1:1:1`?                              | No; one reference counter cannot establish three domain rates or synchronous crossing        | inference bounded by source |
| Is exact installed-kernel equivalence proven?       | No; the source snapshot is hash-pinned but not tied to the currently installed module binary | `observed-bytes`            |

The prior RLC `GFXCLK:REFCLK` header route remains a separate source prototype (`0x4C30..0x4C35`) and is not promoted here: existing exact-CLV applicability evidence found no direct PMFW binding and no UMC/DF/UCLK mapping. The new SMUIO TSC route is stronger as an actual local callback implementation, but it is a reference timebase, not the requested domain counter pair.

## Exact missing hardware inputs

Before any physical-clock acceptance test, the project needs all of the following from a pinned, exact installed-driver/firmware path:

1. An exact UMC/MCLK counter or live PLL-divider register, including its address provenance and whether the count is memory clock cycles, half-rate clock, or GDDR6 edge/data rate.
2. An exact UCLK divider/ratio and synchronous-crossing/status selector; `UclkDiv1M0=0x01` or equal configured values are not enough.
3. An exact DF/FCLK counter or PLL-divider/status register independently attributable to the same board IP.
4. A common reference/calibration relationship, such as the SMUIO 100 MHz timebase paired with each domain counter, with units and sampling window established.
5. Exact installed kernel/module identity and a safe read-only transport with baseline, timeout, validity/status bits, and cleanup. No transport or hardware operation is proposed by this report.
6. A hardware readback on BC250-01 showing independent samples, valid status, divider/crossing state, and repeatability under the unchanged CLV request.

Until these links exist, do not convert the SMUIO TSC value into MCLK/UCLK/FCLK or call a future capture synchronized. No executable hardware acceptance procedure is supplied because the missing domain semantics make one indefensible.

## Bounded source test

Command:

```text
python3 -B evidence/firmware-audit/20260921-clock-observability-next2/physical_counter_semantics_test.py
```

Observed literal stdout:

```text
{"checks": {"failed": 0, "passed": 16, "total": 16}, "future_procedure": null, "ip10.3.6_lower": "0x002E", "ip10.3.6_upper": "0x002D", "output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-clock-observability-next2/physical-counter-semantics-result.json", "physical_mclk_uclk_fclk": false, "status": "PASS", "timebase": "100MHz SMUIO TSC"}
```

- Exit status: `0`.
- Stderr: empty (`0` bytes).
- Result JSON: 16/16 checks PASS.
- Evidence class: `observed-bytes` + `static-analysis`; no hardware claim.
- CLV request readback: `0x24` at `0x7E5`; unchanged.
- The verifier itself is `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-clock-observability-next2/physical_counter_semantics_test.py`.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-clock-observability-next2.md`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-clock-observability-next2.md`
- Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-clock-observability-next2/`
  - `physical_counter_semantics_test.py`
  - `physical-counter-semantics-result.json`
  - `source-test.stdout`
  - `source-test.stderr`
  - `source-test.exit_status`
  - `SHA256SUMS.final`

No original ROM or source was modified. No hardware, network, sysfs, register, NVRAM, firmware, or `scripts/probe_bc250_clocks_readonly.py` action occurred.
