# BC-250 GPU overclock/undervolt guidance: pinned Cyan Skillfish governor review

- Review date: 2026-09-21 (Asia/Almaty)
- Reviewer: `/root/bc250_gpu_guidance`
- Scope: GPU/GFX clock and GPU/GFX voltage guidance for AMD BC-250/Cyan Skillfish. CPU/SoC overclocking, firmware writes, package installation, and hardware commands are out of scope.
- Evidence status: external source plus source inspection; no hardware action or governor execution.

## Conclusion

The pinned original `filippor/cyan-skillfish-governor` source provides a configurable GPU/GFX frequency-to-voltage curve and SMU/kernel backends. It does **not** publish a board-independent electrical-safe GPU range. Its numeric checks are configuration validation, not a hardware rating. The source's active examples and the community BC-250 guide's reported values must be kept separate from per-board validated limits.

The source distinguishes GPU/GFX operations from CPU operations at the API-name level (`force_gfx_*`, `get_current_gpu_voltage`, `set_gfx_vid_offset`, and separate CPU methods), but it does not establish a SoC rail mapping. In particular, these GPU values must not be relabeled as `VDDCR_SOC`, and the local BC-250 OC review still leaves `VDDCR_VDD`/SoC units and consumer unresolved. No SoC voltage limit follows from this review.

## Provenance and source hashes

### Pinned original governor repository

- Repository: <https://github.com/filippor/cyan-skillfish-governor>
- Branch: `smu`
- Pinned branch commit: `aaed42535622aee1a93df8b22860c409539f67f8`
- Branch API retrieval: <https://api.github.com/repos/filippor/cyan-skillfish-governor/branches/smu>
- Commit date in API response: `2026-09-19T15:53:37Z` (committer); message `cleanup`; unsigned according to the API response.
- Retrieval method: `agent-reach` web route (`curl https://r.jina.ai/...`) and direct `raw.githubusercontent.com` reads. No clone, build, install, or execution.
- License: MIT. Retrieved `LICENSE` SHA-256 `7fd1dea6495612cf349621799fff8359a6497bd97378c6fe9d87a9f73bd446d0`.

| Pinned file                       | URL                                                                                                                                           |  Retrieved bytes | SHA-256                                                            |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------: | ------------------------------------------------------------------ |
| `README.md`                       | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/README.md>                       |           13,560 | `25489be765111c091b75ebea4fd8cc8e15aaa5647e41af9b98a51d600b07c797` |
| `default-config.toml`             | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/default-config.toml>             |            1,605 | `236ad29e9b221532d14a87fb84ba66729a607cadbdf08b3654a6baf26b6222eb` |
| `config.toml`                     | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/config.toml>                     |            1,305 | `2a9149f88952c5a80d83182a34742d558ac6670099eaa8a84c7ce6263ef29fc2` |
| `src/config.rs`                   | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/src/config.rs>                   | read-only source | `b2c53e2d9f2de477921ad6e4cf9ae0cd91ad26939de9121eb609ffddd566e6a7` |
| `src/gpu.rs`                      | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/src/gpu.rs>                      | read-only source | `e6f42a8cec233014ab76af54a031540476cdb23f1355356c63a94d3ef5a7a389` |
| `src/gpu/kernel_freq_strategy.rs` | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/src/gpu/kernel_freq_strategy.rs> | read-only source | `4d7d741dad61bdd1b63424e57fb224ec78002ba720179a03e666fb65c21397b`  |
| `src/smu/api/queue0.rs`           | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/src/smu/api/queue0.rs>           | read-only source | `0c7c5f8ffa8a7b6d5010450bcf32115790ddf450396439467c304f5ac034e71a` |
| `src/smu/api/queue3.rs`           | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/src/smu/api/queue3.rs>           | read-only source | `3d890b6346d58cb8954bd08254d174e17a88a9cb031d8af30da30aa9cf7e52b3` |
| `src/smu/codec.rs`                | <https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/src/smu/codec.rs>                | read-only source | `a42e58e7aa1c19c5483ab61519bf4d450a0ae8d50f6b1f8f14a3ccb4bd2890ff` |

### BC-250 community guide

- Public page: <https://elektricm.github.io/amd-bc250-docs/system/governor/>
- Pinned source repository revision: `0524002c3be78e9926a3fc6fb9b40415b7b43b1f`
- Repository archive SHA-256: `dfc2f2883b64615a11c22781fe31660eb51000c6f37032af1048c7dbff707394`
- Local pinned source: `docs/reference/amd-bc250-docs/source/docs/system/governor.md`
- Local source SHA-256: `1acb99714373dd3adf495186d8a8dcd312e307e571db8dfca14ea2bd2a89d3bc`
- Local manifest entry verifies `size=26387` and the same SHA-256.
- Jina retrieval on 2026-09-21: `/tmp/amd-bc250-governor-jina-20260921.md`, SHA-256 `bc56414bbed8b92ea60451baa4b6486a8c30ab529d1928f14c9ce8ce4e720b57`.
- Trust class: community/external-primary reference, not board hardware proof.

## Exact source-supported facts

### 1. Governor README contract

The pinned README says the governor is an adaptive GPU governor for Cyan Skillfish, can set frequency/voltage through either the SMU API or kernel sysfs, and uses `safe-points` entries with `frequency` in MHz and `voltage` in mV. It requires voltage to be non-decreasing as frequency increases. These are software configuration semantics, not an electrical guarantee.

The README says that when `safe-points` is absent, the built-in conservative defaults are **350 MHz @ 700 mV** and **2000 MHz @ 1000 mV**. The source `src/config.rs` reproduces this exact fallback in `parse_safe_points()` (lines 376-383 at this pinned revision).

The README's optional `frequency-range` is an initial min/max request. `src/config.rs` clamps that request to the allowed range derived from the first/last configured safe points; it does not create a new hardware capability range.

### 2. Pinned repository `default-config.toml` (active, not comments)

Active safe points in the pinned file are:

| GPU frequency (MHz) | voltage (mV) |
| ------------------: | -----------: |
|                 500 |          700 |
|                1000 |          800 |
|                1175 |          850 |
|                1500 |          900 |
|                1600 |          910 |
|                1700 |          920 |
|                1850 |          930 |
|                2000 |          960 |

The same file sets an initial `frequency-range` of `1000..=1850` MHz. This is a governor startup request, not the source's full allowed range: `src/config.rs` derives its allowed range from the first/last safe points, here 500..=2000 MHz.

The file contains commented exploratory points, not active settings: 2050@980, 2100@1000, 2125@1020, 2150@1035, 2200@1050, 2230@1085, 2300@1110, 2350@1130, 2400@1150. Because they are commented, they are not the active default profile and are not proof of stability or safety.

### 3. Pinned repository `config.toml` (active example, separate from default)

The active checked-in `config.toml` uses `set-method = "kernel"` and the following curve:

`500@700`, `1175@700`, `1400@750`, `1600@800`, `1700@850`, `1850@900`, `2000@950`, `2050@975`, `2100@1000`, `2125@1015`, `2150@1030`, `2200@1050`, `2230@1085`, `2300@1110`, `2350@1130` (MHz@mV).

Its `2400@1150` point is commented out. This is an example configuration, not a validated BC-250 universal curve.

### 4. Pinned source implementation boundaries

- `src/config.rs` accepts each safe-point number as an unsigned 32-bit integer and enforces monotonic non-decreasing voltage with increasing frequency. For its numeric upper bound, it rejects a table when the highest frequency or voltage exceeds **10,000**; it also checks presence, type, duplicates, and monotonicity. This is an input-validation envelope, not a supported electrical range.
- If a requested frequency lies between configured points, `src/gpu.rs::voltage_for_freq()` linearly interpolates the voltage. Below the minimum or above the maximum configured point, the function returns an error. It does not query a board datasheet or validate silicon stability.
- `GPU::new()` derives `min_freq` and `max_freq` from the first and last configured safe points. The governor therefore cannot request outside its configured curve through this path, but this is software clamping only.
- The source checks PCI vendor `0x1002`, device `0x13fe`, at bus `0:01:00.0`. This confirms the intended target identity in code; it does not prove the live target was reached in this review.
- Queue 0 wrappers name `force_gfx_freq` (SMU message `0x39`), `unforce_gfx_freq` (`0x3A`), `force_gfx_vid` (`0x3B`), and `unforce_gfx_vid` (`0x3C`). `codec.rs` uses `VID = (1.55 - (mV / 1000)) / 0.00625` and the inverse for its software conversion. These are source-level encoding claims only; no hardware readback was performed.
- Queue 3 exposes separate CPU and GPU/GFX-named calls: `get_current_cpu_voltage` vs `get_current_gpu_voltage`, `set_cpu_vid_offset` vs `set_gfx_vid_offset`, and `set_cpu_vid_offset_large` vs `set_gpu_vid_offset_large`. The small offset methods accept **-5..+5** in source validation. The source does not document their rail mapping, unit behavior on the target, or a SoC selector. The large GPU offset method accepts a float without a source-side range check; this must not be interpreted as a safe voltage range.
- The kernel backend (`src/gpu/kernel_freq_strategy.rs`) reads live `pp_od_clk_voltage` text. When `SCLK:` and `VDDC:` ranges parse successfully, it clamps configured points to those ranges; if either line is missing it logs a warning and skips that clamp. Pinned file SHA-256: `4d7d741dad61bdd1b63424e57fb224ec78002ba720179a03e666fb65c21397b`. This makes kernel-backend limits dependent on the current driver/sysfs state, not the README.
- The SMU backend (`src/gpu.rs`) does not override `clamp_safe_points`; it sends `force_gfx_vid(vol)` then `force_gfx_freq(freq)`. Its constructor calls `set_gpu_max_temperature(80)` before unforcing the GFX controls. That is observed source behavior only, not a hardware-verified thermal limit.

## Community documentation values (reported examples, not supported limits)

The pinned BC-250 community page reports the following numbers. They are retained as quotes/claims from that page and are **not** promoted to hardware-supported limits:

- Overview: governor scaling from **1000 MHz idle** to **2000-2230 MHz load**, dynamic **700-1000 mV**; without a governor it reports **1500 MHz** locked. The page does not provide a board identifier, raw readback, sample count, or independent electrical measurement for these overview numbers.
- The page says a minimum GPU voltage below **700 mV** locks the GPU to 1500 MHz. This is a community guide warning, not a validated minimum rail rating.
- Its SMU example curve uses 1000@800, 1500@900, 2000@1000, 2150@1000, and 2200@1000. It says one live board held 2150-2200 MHz at 1000 mV, while other boards may need about 1025 mV at 2150 and 1050 mV at 2200. No board identity or raw evidence is supplied on the page.
- Its guide says not to exceed **1075 mV at 2200 MHz** in that community procedure, and its “known GPU limits” list labels **2230@1060 mV** air-cooled, **2300@1075 mV** with good air cooling, and **2400@1125 mV** liquid-cooled. These are cooling-dependent community examples; they are not an AMD specification or a project-approved operating envelope.
- The page's “2000 MHz @ 1000 mV safe starting point for all boards” is a community recommendation. It is not independently reproduced here and conflicts with the project rule that no safe voltage setpoint may be inferred from community text alone.

## GPU/GFX versus SoC

| Item                            | What this review can say                                                                                                                                                     | What it cannot say                                                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| GPU/GFX frequency               | The governor's `frequency` points and GFX SMU calls are intended for GPU/GFX frequency.                                                                                      | It cannot prove an applied clock on the BC-250 without live readback.                                                     |
| GPU/GFX VID/voltage             | The governor labels curve voltage in mV and has GFX VID wrappers/conversion.                                                                                                 | It cannot prove the physical rail, PMFW acceptance, or safe electrical ceiling.                                           |
| SoC / `VDDCR_SOC` / `VDDCR_VDD` | No SoC setpoint or limit is established by the governor review. Local project OC review records the donor field's rail, sign, units, consumer, and conversion as unresolved. | Do not convert 1000/1050/1075/1125/1150 mV examples into a SoC value, and do not map GPU VID selector names to SoC rails. |
| CPU values                      | Not reviewed here; another worker owns CPU AMD documentation.                                                                                                                | Do not use this report for CPU frequency or voltage decisions.                                                            |

Local corroborating boundary: `docs/research/2026-09-20-amibcp-oc-values-review.md` (SHA-256 `a805a5a00afa2b3174ffa7f6dc86d995a6299da467d5aff166ee661c25847acc`) says the donor `VDDCR_VDD` field is an unresolved offset/command field and that the `1.15 V` value is an operator ceiling, not a validated board rating. This report follows that correction.

## Performance and limit interpretation

- **Software-configurable envelope:** at this pinned revision, `safe-points` must be monotonic; each value is a u32; the highest frequency and voltage must be <=10,000; and requests outside the configured first/last points error. This is the only “supported” range directly established by code, and it is a parser/control-flow range, not a physical limit.
- **Pinned default profile:** active points end at **2000 MHz @ 960 mV**. Its higher points are comments and are not active.
- **Pinned checked-in example:** active points end at **2350 MHz @ 1130 mV**; **2400@1150** is commented. This remains an example with no hardware evidence in this review.
- **Community reported examples:** 2150-2200@1000, 2230@1060, 2300@1075, 2400@1125 are single-page/community claims or examples. They do not establish universal stability, performance gain, thermal margin, or safe operation.
- **No performance result:** this review observed no FPS, benchmark, latency, power, temperature, clock readback, error rate, or stability result. Any claimed performance limit remains unverified.

## Unknowns and next discriminating check

1. Which exact BC-250 board, cooling solution, PMFW/BIOS, and current governor/backend would be tested?
2. Does the target firmware accept the exact GFX VID/frequency messages on this board, and what physical rail do they alter?
3. What independent voltage and clock measurement would corroborate a software readback?
4. What sustained, repeatable workload and rollback procedure would establish per-board stability?
5. Is a requested SoC/`VDDCR_VDD` field consumed at all, and what are its unit/sign/rail semantics? The current project evidence leaves this open.

The next safe discriminating step is a read-only identity/telemetry capture followed by an explicitly approved, reversible one-variable A/B test. This review itself performed neither and authorizes no hardware command.

## Checks

- PASS: contract, `memory/INDEX.md`, task-relevant OC/evidence memory, research-provenance skill, and agent-reach skill were read before external research.
- PASS: `agent-reach doctor --json` completed; web backend reported available; GitHub CLI was not used for authenticated access.
- PASS: pinned branch commit and raw file hashes recorded.
- PASS: pinned kernel-backend source was fetched and hashed; its live `SCLK`/`VDDC` clamp behavior was inspected.
- PASS: local governor source snapshot and manifest hashes checked against the recorded values.
- PASS: no code execution, package installation, hardware command, firmware write, NVRAM write, or board probe.
- UNRUN: build, unit tests, runtime governor start, SMU mailbox invocation, physical clock/voltage readback, thermal/stability/performance benchmark.
- INCONCLUSIVE: any applied GPU clock/voltage, board-wide limit, SoC mapping, safe undervolt, or performance gain.

## Reproducibility commands (read-only)

```sh
# Pinned branch metadata
curl -fsSL https://r.jina.ai/https://api.github.com/repos/filippor/cyan-skillfish-governor/branches/smu

# Pinned source files
curl -fsSL https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/README.md
curl -fsSL https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/default-config.toml
curl -fsSL https://raw.githubusercontent.com/filippor/cyan-skillfish-governor/aaed42535622aee1a93df8b22860c409539f67f8/config.toml
```

All commands above are read-only network fetches. No fetched code was executed.
