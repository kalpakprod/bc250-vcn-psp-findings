# OC stock telemetry capture — no clock changes

## Status and reuse

Host-tested only. Existing `scripts/probe_bc250_clocks_readonly.py` is reused; five synthetic-fixture tests pass. No live BC250 capture was performed. Local DRM identity on 2026-09-20 was 1002:1900, not the expected 1002:13fe. Do not interpret this workstation as the board.
`collect_stock_runtime_readonly.py` is not selected: it accepts any AMD GPU and collects broader command/journal data. FirstMarker is not a telemetry collector.

## Preconditions

Operator supplies the authorized board session or executes locally on the board. Confirm programmer/clip disconnected, normal power/cooling, baseline image provenance and current PCI identity 1002:13fe. A BIOS version string alone cannot prove exact ROM identity. No flash, reboot, clock setter, voltage setter, raw PCI/SMN access or mailbox operation is part of this capture.
Keep a private fresh output directory outside the repository. Do not collect /proc/cmdline, hostname or full journals: existing probe redaction is not a general secret filter. The invocation below suppresses those fields at source without reading them. Do not override BC250_PCI_ID.

## Capture procedure

From the project root on the authorized board, use a new private output directory and run this command. It records one snapshot only; repeat in separately named files after 10 seconds of idle for baseline repeatability. Do not start a load generator in this step.

```sh
umask 077
capture_dir=$(mktemp -d /tmp/bc250-stock-XXXXXX) || exit 1
env -u BC250_PCI_ID timeout --signal=TERM --kill-after=2s 15s python3 - <<'PY' > "$capture_dir/idle-1.json"
import sys
from pathlib import Path
sys.path.insert(0, 'scripts')
import probe_bc250_clocks_readonly as probe
original_read = probe.read_text
excluded = {Path('/proc/cmdline')}
probe.read_text = lambda p: None if p in excluded or p.name == 'uevent' else original_read(p)
probe.platform.node = lambda: '<omitted>'
raise SystemExit(probe.main())
PY
status=$?
printf 'capture_exit=%s\n' "$status"
[ "$status" -eq 0 ] && sha256sum "$capture_dir/idle-1.json"
```

Stop on timeout/nonzero exit, zero target cards, missing expected metrics, abnormal temperature, instability or uncertain board identity. Preserve failed output privately; do not label a partial JSON capture valid. No process survives the timeout; no hardware-state rollback is required because this procedure issues no hardware writes. Remove only the private capture directory when intentionally discarding it.

## Fields and verdicts

- Record UTC capture time and collector SHA-256 alongside each capture. Record operator-confirmed baseline identity separately; do not include credentials or access-bearing URLs.
- Identity: kernel, BIOS version/date, target PCI ID. These describe reported state, not a full-chip identity proof.
- `pp_dpm_mclk`, `pp_dpm_fclk`, `pp_dpm_socclk`, other present allowlisted files and raw `gpu_metrics` hash: kernel-reported observations only. Missing sources remain missing; never synthesize clock values.
- PASS capture: valid JSON, expected target selected, required files readable, metrics byte length/hash verified. A successful exit with empty cards is INCONCLUSIVE for board capture.
- INCONCLUSIVE synchronization: equal MCLK/FCLK or metrics values do not prove 1:1:1; known historical driver aliases these fields. No independent clock source is validated here.
- UNRUN: physical SoC rail measurement, memory training/stability, independent UCLK/FCLK/MCLK verification and DF1400 application.
- DF1400 A/B testing remains separately gated by docs/runbooks/2026-09-19-df1400-request-test.md. Do not raise voltage or frequency to compensate for missing telemetry.
