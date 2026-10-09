# BC-250 memory-1800 versus validated-sync latency protocol

Date: 2026-09-21
Owner: bounded performance-protocol reviewer (`/root/bc250_latency_protocol`)
Status: operator protocol only; no board run, stress run, BIOS/NVRAM change, or benchmark result

## 1. Conclusion and evidence boundary

Use a paired, repeated A/B capture with the unchanged **B1800** profile as the control and a separately identified **SYNCCAND** image/profile only after its firmware and hardware acceptance gates are complete. Preserve the same workload, harness and helper source, compiler identity, CPU affinity, kernel/driver, cooling, and run parameters. Report raw trials plus median and spread; do not report a nanosecond or percentage outcome until the corresponding board trials exist.

This protocol can establish a measured workload difference. It cannot establish `MCLK=UCLK=FCLK` from equal kernel metrics. Current project evidence says the retained driver maps FCLK and MCLK through the same `MemclkFrequency` field; SMU queue `0x11` returns committed software state and queue `0x13` returns a state index/count. Independent physical clock/divider/crossing evidence remains absent. A performance improvement, a persisted BIOS request, and synchronization are three different verdicts.

Evidence classes for a future run:

- `hardware-verified`: board identity, boot/training, readback, temperatures/errors, and the exercised workload on the identified BC-250.
- `observed-bytes`: candidate/control hashes, NVRAM/Setup readback, raw probe JSON, and raw benchmark JSON.
- `emulated-or-host-tested`: this report's local tool inspection and any non-BC-250 harness self-test. It is not board performance evidence.

## 2. Planning anchor and existing route

The exact project root is `/home/OWNER/orca/projects/bc250`. The protocol reuses:

1. `scripts/measure_bc250_perf.py` (workspace-local harness candidate): compiled-C dependent-load latency proxy, memcpy bandwidth, and ALU control workload; JSON summaries and a baseline/modified compare rule; refusal unless PCI ID `1002:13fe` is present. This file and its test are untracked in the inspected worktree, so root must integrate and verify them before an operator relies on this route.
2. `scripts/probe_bc250_clocks_readonly.py` through `docs/runbooks/2026-09-20-oc-stock-capture.md`: read-only kernel-file capture of allow-listed DPM fields, `gpu_metrics`, PCI identity, and BIOS metadata. It is not an independent physical clock meter.
3. `docs/runbooks/2026-09-20-clv-native-1330-capture-sheet.md`: records exact Setup values, POST/training, boot, three independent-clock fields, and rollback classification.
4. `docs/runbooks/2026-09-19-df1400-request-test.md`: keeps stored-request retention separate from physical clock application and requires recovery/readback before any approved candidate trial.

The existing OC correction and UCLK guide are controlling qualifications: labels such as `1800`, `1330`, or `1750` are request/menu values until read back and independently measured; `UclkDiv1M0=Enabled` is not a decoded `/1` ratio; historical `131.4 ns` and `140–150 ns` reports are participant/photo-class evidence, not a current baseline.

### Read-only inspection actually performed

The following files were read for this protocol (hashes are recorded so the source boundary is reproducible):

| Input                                                       | SHA-256                                                            |
| ----------------------------------------------------------- | ------------------------------------------------------------------ |
| `memory/INDEX.md`                                           | `8cfdc0ad0c40a9dcab18ce647b9c6364c8dd605915135f3083e0ee00fc3b0e21` |
| `memory/oc-recheck.md`                                      | `531eb87a9c2462743ce38ea4383832d368c2641600571da09dcda1cc02c62912` |
| `memory/tools.md`                                           | `a3d864d214229f5e4658e622bc56c9e5cc1337db3d2550165750f1331ecaa241` |
| `docs/runbooks/2026-09-20-oc-stock-capture.md`              | `3ce85411083b7e8a7228062847a46592c94d2ba7975a6418d422b64fd1e45171` |
| `docs/runbooks/2026-09-20-clv-native-1330-capture-sheet.md` | `11b44cbcf2d5c914d9195b67648d2583c3e5dea2b86a6a0602869c02d5dc5b60` |
| `docs/runbooks/2026-09-19-df1400-request-test.md`           | `9b56cb6222d254333efdd2d27a6c821c7a159f4e84903dbaf6851d6a849973db` |
| `scripts/measure_bc250_perf.py`                             | `e577401b962d597f07bb6b970f6f1dccb5824bfa734a9761427e2fb431830dfe` |
| `tests/test_measure_bc250_perf.py`                          | `d57079aa5875f6796db27acc15c3ab719f0cc0d4c473f3fa5e8e28efc402d4ea` |

The project host is Linux `7.2.5-3-omarchy`, x86_64, Python `/usr/bin/python3` 3.14.7. Local availability checks found `/usr/bin/cc`, `/usr/bin/gcc`, `/usr/bin/clang`, `/usr/bin/top`, and `/usr/bin/sensors`; these local tools do not establish target-board availability. No `lat_mem_rd`, `tinymembench`, `mbw`, `sysbench`, `mlc`, `perf`, `clpeak`, `glmark2`, `vkmark`, `mangohud`, `amdgpu_top`, `radeontop`, `ras-mc-ctl`, `edac-util`, or `stress-ng` was found locally. `/usr/bin/stream` is a symlink to ImageMagick `magick`, not the STREAM benchmark, so it is deliberately not selected. No board was contacted and no benchmark or stress process was run.

The existing harness compiles a temporary helper for each CLI `run` and deletes it afterward; its `helper_sha256` is the C **source** hash, not a hash of the executable. The harness `compare` also checks only that helper-source hash, not compiler version or binary identity. This protocol therefore makes a same-source/same-compiler claim, not an exact same-binary claim. Record compiler path/version and script/helper source hashes in every run. If an exact same-binary guarantee is required, the current CLI is insufficient; mark `same_binary=UNPROVEN` and stop for a separately approved harness change rather than claiming byte-identical executable identity.

## 3. Conditions and preconditions

### B1800 control (unchanged baseline)

Call this condition `B1800`, not “1800 MHz measured.” Before changing anything, record:

- current full-chip/recovery image path and SHA-256, board identity, and target PCI ID `1002:13fe`;
- BIOS version/date, kernel, amdgpu version/firmware identifiers, power profile, CPU governor, cooling/ambient conditions;
- exact native menu/NVRAM values and byte readback for Memory Clock Speed (`AmdSetup+0x316`), UclkDiv1M0 (`+0x330`), Memory P-state (`+0x36D`), FCLK_DPM (`+0x6A3`), DF Clock Override Control (`+0x703`), DF Clock Override (`+0x704`), and all voltage controls;
- proof that the existing memory-clock request is the menu's `1800` option. Do not infer the enum byte from the label or from a donor image;
- the stock-capture idle snapshots `idle-1` and `idle-2` at least 10 seconds apart.

“Unchanged” means no BIOS/NVRAM/voltage/timing/driver/kernel change for the control run. If the current board is not already the requested memory-1800 state, stop: this protocol does not authorize changing it merely to create a baseline.

### SYNCCAND candidate

Use `SYNCCAND` only after the exact image/profile has a separate structural review, recovery image, explicit operator approval, independent readback, cold-boot acceptance, and a documented rollback. Record its exact image hash and all six Setup values. Do not call it synchronized because its menu fields match or because `gpu_metrics` prints equal values. Voltage remains unchanged/Auto unless a separate approved voltage experiment exists; do not combine variables in this comparison.

If candidate acceptance is incomplete, the only valid result is `CANDIDATE_NOT_READY`; no performance run is allowed. If the candidate does not boot, loses the expected values, or requires recovery, record a failure and stop rather than compensating with another clock or voltage edit.

### Common environment

Use a private directory outside the repository, with `umask 077`. The following creates only the local evidence directory; it does not change board state:

```sh
umask 077
RUN_DIR=$(mktemp -d /tmp/bc250-latency-XXXXXX) || exit 1
printf 'private_output=%s\n' "$RUN_DIR"
```

Keep raw JSON, helper source, helper hash, script hash, compiler path/version, probe snapshots, temperature/error samples, and a manifest there. Do not collect `/proc/cmdline`, hostname, full journals, serials, credentials, or access-bearing URLs. The programmer/clip must be disconnected during normal board operation.

Pin one available CPU with `--cpu N`; use the same `N` for both states. Do not change governors or affinity between states. Preserve one kernel/driver/PMFW and the same display/cooling/power conditions. If any common parameter differs, the pair is invalid or must be analysed as a separate block.

## 4. Repeated measurement procedure

Run **three cold boots per condition and five identical trials per boot** (15 trials per condition), followed by a rollback capture. A cold boot is a complete power-off interval long enough for the operator's established recovery procedure; record the interval. A practical order is B1800 boots 1–3, SYNCCAND boots 1–3, restore B1800, then one final B1800 rollback block. Record the order as a thermal/time confound; do not cherry-pick a boot. If separately approved and safe, interleave conditions to reduce drift, but do not change the profile without the operator's approval.

At each boot:

1. Confirm target PCI ID, expected BIOS/image identity, all Setup values, POST/display, training result, OS login, and no fallback. Capture two idle probe snapshots 10 seconds apart.
2. Wait for the same idle interval. Record temperature start and ambient if available. If a target-board sensor route is unavailable, do not run the performance candidate: first identify a safe, read-only target sensor source. Never substitute the workstation's sensor.
3. Run the same fixed order for every boot: `W1` dependent-load latency, `W2` host-memory memcpy bandwidth, `W3` CPU ALU control, then `W4` the same already-installed deterministic GPU workload if present. Use the same warm-up, input, scene/configuration, resolution, frame cap, duration, and process affinity. A GPU/CPU bottleneck verdict requires W4 and its telemetry; if no deterministic workload and telemetry are already installed, mark W4 and the bottleneck verdict `UNRUN` rather than installing a tool.
4. Save all raw trial outputs and an end probe/temperature/error sample. Preserve nonzero exits and partial output; do not call them valid measurements.
5. Leave voltage and unrelated clocks untouched. Stop immediately on machine check, GPU reset, corrected/uncorrected error increase, thermal alarm, training loop, loss of display/SSH, missing target card, or abnormal harness exit.

### W1–W3 command route

On the authorized board, from a copy of the exact pinned script, the normal full route is:

```sh
umask 077
python3 scripts/measure_bc250_perf.py run \
  --label B1800-b1 --method c --cpu N --repeats 5 \
  --out "$RUN_DIR/B1800-b1.json" \
  --notes 'B1800; boot 1; unchanged control'
```

Replace `N` with the same online logical CPU id on all runs. Repeat with unique labels for each boot and condition. Do not use `--quick` for acceptance. The compiled helper reports:

- `latency_ns@size`: dependent-load latency proxy. Use the largest working set above the harness's 4 MiB cache-domain ceiling as the primary DRAM-proxy metric; retain all sizes and raw values.
- `bandwidth_gbs@size`: host-memory `memcpy` throughput, not GPU VRAM bandwidth.
- `alu_ns_per_op`: CPU control workload used to detect CPU-frequency/scheduling drift.

Record script SHA-256, helper source SHA-256, compiler path/version and flags, and all harness parameters. The current CLI removes its helper, so it cannot provide a retained binary hash; state `same_binary=UNPROVEN` rather than asserting `same_binary=PROVEN`. A Python fallback is a labelled interpreter proxy and is never a board DRAM latency result. If the board cannot compile the helper, stop or record W1–W3 `UNRUN`; do not compare a C run against a Python proxy.

After each pair of snapshots, invoke the existing compare command in the same argument order (`B1800` first, `SYNCCAND` second), once for every boot pair:

```sh
python3 scripts/measure_bc250_perf.py compare \
  "$RUN_DIR/B1800-b1.json" "$RUN_DIR/SYNCCAND-b1.json" \
  --out "$RUN_DIR/compare-b1.json"
```

### W4 CPU/GPU bottleneck separation

W4 must use an existing, deterministic workload; no benchmark installation is part of this protocol. Record the executable/configuration hash and exact launch command privately. During the same fixed-duration run, collect only allow-listed read-only GPU files through the existing probe route (or an operator-approved equivalent): `gpu_busy_percent`, present DPM fields, and raw `gpu_metrics` hash. Frame time/FPS must come from the workload's own existing output, not an invented conversion. Record bounded CPU utilization/process time if an existing read-only tool is available; otherwise state `CPU_TELEMETRY=UNRUN` and do not make a CPU/GPU bottleneck claim.

For a minimal read-only GPU-busy time series on the board, this shell fragment accepts only the target PCI identity and writes samples to the private output directory. Run it alongside the same fixed W4 executable in both conditions; choose a monitor CPU other than the pinned W1–W3 CPU if task affinity is available. It does not read command line, hostname, serials, or PCI configuration:

```sh
workload_command ... & workload_pid=$!
python3 - "$workload_pid" <<'PY' > "$RUN_DIR/gpu-busy.csv" &
import glob, os, sys, time
pid = int(sys.argv[1])
while os.path.exists(f"/proc/{pid}"):
    now = time.time_ns()
    for dev in sorted(glob.glob('/sys/class/drm/card[0-9]/device')):
        try:
            if open(dev + '/vendor').read().strip() != '0x1002':
                continue
            if open(dev + '/device').read().strip() != '0x13fe':
                continue
            try:
                busy = open(dev + '/gpu_busy_percent').read().strip()
            except OSError:
                busy = 'UNAVAILABLE'
            print(f"{now},{dev},{busy}", flush=True)
        except OSError:
            continue
    time.sleep(1)
PY
monitor_pid=$!
wait "$workload_pid"; workload_status=$?
wait "$monitor_pid" || true
printf 'workload_exit=%s\n' "$workload_status"
```

The sysfs utilization series is a driver report, not physical clock evidence. If the workload exits too quickly for repeated samples, or if target identity/`gpu_busy_percent` is absent, mark telemetry and bottleneck `UNRUN/INCONCLUSIVE`. The operator must stop/inspect the workload before rerunning; this fragment does not start or tune the GPU workload itself.

If `top` is already installed on the target, capture only the selected workload's threads at the same 1-second interval; replace `WORKLOAD_PID` with the actual application process, not a shell launcher. Do not install `top` if absent:

```sh
top -b -H -d 1 -p "$WORKLOAD_PID" > "$RUN_DIR/cpu-threads.txt"
```

Classify bottleneck only from measured observations, not from the requested clock fields:

- `GPU_BOUND`: repeated GPU busy/frame-time evidence shows the GPU is the limiting path while per-core/process CPU evidence shows headroom; CPU ALU control must also remain within the predeclared pair-drift rule.
- `CPU_BOUND`: CPU per-core/process evidence shows saturation while GPU busy has headroom.
- `MIXED` or `INCONCLUSIVE`: missing telemetry, conflicting indicators, or changed workload/environment.

The labels are workload classifications, not proof that memory synchronization is present. Host-memory W1/W2 and a GPU workload measure different paths; never merge their units or call host memcpy “VRAM bandwidth.”

## 5. Temperature, errors, and validity

For each boot record start/peak/end temperature with sensor name, command/version, interval, and whether the sensor is on the target board. A bounded read-only inventory of standard hwmon temperature inputs and EDAC counters is:

```sh
for f in /sys/class/hwmon/hwmon*/name /sys/class/hwmon/hwmon*/temp*_label \
         /sys/class/hwmon/hwmon*/temp*_input \
         /sys/devices/system/edac/mc/mc*/ce_count \
         /sys/devices/system/edac/mc/mc*/ue_count; do
  [ -r "$f" ] || continue
  printf '%s=' "$f"; cat "$f"
done
```

Run this before and after each five-trial block and sample temperatures during the block from a second CPU at a fixed interval only if the target's sensor source is known. This is file output only; do not write sensor controls. Record board error state before and after: available EDAC CE/UE counters, GPU reset/error indicators, and only bounded kernel error output permitted by the operator's data policy. Missing counters are `UNAVAILABLE`, not zero. A nonzero/incremented error, thermal alarm, or reset invalidates that boot and triggers the stop rule.

The run pair is valid only when all of these match or are explicitly accounted for: target PCI identity, image/control identity, kernel/driver/PMFW, CPU affinity, harness script/source/compiler, workload sizes and iteration counts, trial count, voltage/timing settings, and acceptable temperature/error state. Existing harness checks same kernel, affinity, method, helper source hash, sizes, iteration counts, at least three trials, and ALU drift within its 3% policy. Preserve those checks, but add compiler version, BIOS/image hash, cold-boot number, temperature, and error checks externally. Exact executable-binary equality is not provided by the existing CLI.

## 6. Analysis and decision rules

Keep every raw value. For each condition/workload/boot compute median, Q1, Q3 (IQR), minimum, maximum, and the 15-trial aggregate. Also report the three per-boot medians so boot-to-boot drift is visible. For a measured metric, use:

```text
delta_percent = 100 * (median_SYNCCAND - median_B1800) / median_B1800
```

This is calculated only after data exist; it is not a predicted result. Lower is better for latency/ALU time; higher is better for bandwidth/throughput.

Use the existing compare policy as a predeclared decision rule, not as a claim about expected hardware behavior. The existing compare CLI compares two five-trial snapshots at a time; run one comparison for each matched boot pair and summarize all 15 raw trials per condition separately. For the total median/spread, this dependency-free Python fragment emits the overall and per-boot summary from the six saved JSON snapshots (read-only inputs; output can be redirected into the private run directory):

```sh
python3 - "$RUN_DIR" <<'PY'
import json, pathlib, statistics, sys
root = pathlib.Path(sys.argv[1])
for condition, labels in {
    'B1800': [f'B1800-b{i}' for i in range(1, 4)],
    'SYNCCAND': [f'SYNCCAND-b{i}' for i in range(1, 4)],
}.items():
    docs = [json.loads((root / f'{label}.json').read_text()) for label in labels]
    keys = sorted(set().union(*(t['metrics'].keys() for d in docs for t in d['trials'])))
    for key in keys:
        by_boot = [[t['metrics'][key] for t in d['trials'] if key in t['metrics']] for d in docs]
        values = [v for group in by_boot for v in group]
        if len(values) != 15:
            print(condition, key, 'count-mismatch', len(values)); continue
        q1, _, q3 = statistics.quantiles(values, n=4)
        print(condition, key, 'n=15', 'median=', statistics.median(values),
              'q1=', q1, 'q3=', q3, 'min=', min(values), 'max=', max(values),
              'boot_medians=', [statistics.median(group) for group in by_boot])
PY
```

Do not include the final rollback block in the pre-rollback B1800/SYNCCAND aggregate; report it as a separate restoration check.

- `INVALID_RUN_PAIR`: any equivalence check fails, binary identity is unproven where required, trial count is insufficient, or ALU drift exceeds the existing 3% control limit.
- `MEASURABLE_IMPROVEMENT`: primary large-working-set latency median is at least 5% lower, the sample separation rule is met (IQR disjoint or at least 80% of SYNCCAND samples below the B1800 median), and there is no cache-domain latency or bandwidth regression, no error/thermal fault, and no workload/environment confound.
- `MEASURABLE_REGRESSION`: the converse measured regression under the same validity requirements.
- `NO_MEASURABLE_EFFECT`: absolute measured median change is below the existing 2% no-effect band with valid comparable samples.
- `INCONCLUSIVE`: any result between policy bands, unstable spread, missing independent telemetry, or insufficient paired blocks.
- `INCOHERENT_RESULT`: primary gain accompanied by a cache-domain or bandwidth regression; do not call this an overall gain.

These policy percentages are decision thresholds only. No latency, bandwidth, or improvement percentage may be filled in before measurements.

### Synchronization verdict is separate

`PHYSICAL_1TO1TO1_PASS` requires repeated independent MCLK, UCLK, and FCLK measurements on the exact board, a documented common reference and unit/conversion map, and a read-only divider/crossing status or equivalent physical counter evidence. Equal `pp_dpm_mclk`, `pp_dpm_fclk`, `gpu_metrics` fields, SMU software-state values, or BIOS menu labels produce only `INCONCLUSIVE` synchronization. A valid performance improvement must be reported as a workload result, never as a synchronization proof.

## 7. Rollback and completion

After SYNCCAND measurements, restore the exact B1800 values and image using the prevalidated recovery procedure. If the SPI image changed, verify full-chip readback/hash; if only BIOS/NVRAM settings changed, verify the image identity stayed unchanged and verify Setup/NVRAM byte readback. In either case, cold boot and verify POST/display, OS, and error/temperature state. Run the same idle capture and at least one complete W1–W3 control block after rollback; if rollback is not bootable, stop and use the recorded recovery path. Do not “fix” rollback with voltage or another profile.

Completion requires a manifest linking every raw file to condition/boot/trial, exact hashes for images/scripts/helper/workload, literal exit statuses, error/temp records, the compare result, and the rollback result. Report separately: `stored-request`, `boot/training`, `performance`, `bottleneck`, `physical-clock/sync`, and `rollback`. Any unrun field remains `UNRUN`.

## 8. Open questions and decisions

### Blocking questions

- **Q1:** What exact board image and current NVRAM state constitute the operator's unchanged B1800 control? The `1800` menu label must be read back on the target; donor bytes are not sufficient.
- **Q2:** Which exact SYNCCAND image/hash has passed structural review, recovery/readback, boot, and independent acceptance? Until answered, SYNCCAND is not runnable.
- **Q3:** Which deterministic GPU workload and read-only frame-time/CPU telemetry are already installed on the board? If none, W4 remains unrun.
- **Q4:** What exact target-board temperature and error-counter sources are available? Unknown sensors must not be substituted with local-host readings.
- **Q5:** Is an exact retained helper binary required by the operator? The existing CLI records source identity but deletes its temporary binary; strict same-binary comparison requires the additional retention/hash step above.

### Decisions

- **D1:** Reuse the existing C harness and read-only clock probe; do not install `lat_mem_rd`, STREAM, GPU benchmarks, or stress tools as part of this protocol.
- **D2:** Use 3 cold boots × 5 trials per condition, preserve raw samples, and use medians/IQR/per-boot spread.
- **D3:** Separate host-memory latency/bandwidth, CPU control, and GPU workload results; no cross-domain unit conversion.
- **D4:** Treat physical synchronization as unproven until independent clock/counter/divider evidence exists, regardless of matching software values.
- **D5:** Rollback to exact B1800 is mandatory before claiming the experiment complete; no firmware or voltage action is authorized by this document.

## 9. Reported status of this review

Passed: source inventory, memory/OC qualification read, existing route selection, installed-tool availability inspection, protocol design, stop/rollback rules, and explicit evidence boundaries.

Unrun: all target-board capture, benchmark/stress execution, GPU workload, temperature/error observation, independent clock measurement, synchronized-candidate validation, and rollback execution. No performance value, nanosecond value, percentage outcome, or synchronization claim is asserted.
