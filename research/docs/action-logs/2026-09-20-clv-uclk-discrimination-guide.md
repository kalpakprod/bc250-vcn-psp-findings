# UclkDiv1M0 discrimination guide — intent

Timestamp: 2026-09-20T17:20:00+05:00 (Asia/Almaty)
Actor: luna bounded executor

Target: exact CLV native guide and existing read-only clock/metric evidence; pinned donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`.

Bounded action: identify the first operator test that can discriminate `UclkDiv1M0` semantics, independently rerun the existing host-only source/handler alias verifier from a disposable copy, and produce a concise measurement/rollback plan. No BIOS/NVRAM/ROM/hardware/guest/AMIBCP change, no live board probe, no voltage/frequency recommendation, and no new analyzer.

Existing route reused: `evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency_unit_verify.py`, `docs/research/2026-09-20-clv-sync-frequency-unit-discrimination.md`, `docs/research/2026-09-20-clv-sync-stage2-uclk-semantics.md`, and `docs/runbooks/2026-09-20-oc-stock-capture.md`.

Expected effect: one short research report, one machine-readable evidence result, and this append-only action log. The report must separate aliased driver metrics and software-state mailbox values from an independent physical clock measurement and must state the earliest valid one-variable operator test.

Rollback: delete only the unique report, evidence directory, and action log; existing source, donor, scripts, and board state remain unchanged.

## Continuation intent — direct capture-channel readback and exact remaining gate

Timestamp: 2026-09-20T17:35:00+05:00 (Asia/Almaty)

Target: existing guide/report evidence plus `scripts/probe_bc250_clocks_readonly.py` and `cyan_skillfish_ppt.c`. Bounded action: confirm the exact current channel mapping, run the existing host read-only probe against the current local workstation without reading command line/hostname/uevent, and update this report/result with (a) the observed non-target-card result, (b) the exact board-side operator input still missing, and (c) whether offline static progress remains possible. No remote board access, ROM/NVRAM/BIOS/hardware write, installation, guest change, or AMIBCP activity.

Expected effect: update only this report/result/evidence manifest and append this action log. Rollback: restore the prior report/result/manifest and remove this log section; board and firmware remain untouched.

## Observed result and independent readback

Timestamp: 2026-09-20T17:45:00+05:00 (Asia/Almaty).

The exact existing source/handler check was run read-only. A first attempt to run a copy from `/tmp/bc250-uclk-discrim-dyQVYY/frequency_unit_verify.py` exited `1` with `IndexError: parents[3]` because that script derives project root from its repository-relative location. The copy failure changed no project artifact. Corrected procedure ran the existing script from its intended project path:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency_unit_verify.py
```

Observed exit `0`; stdout `status=PASS`, `11/11`; stderr empty; machine result pre/post SHA-256 was unchanged at `6027fd54d8803fbd2a8b22f09c098ec5e9174ddbb143fd2b41f68a5575f7fb0c`. The verifier's final `SystemExit(0 if failed else 0)` always exits zero, so its JSON was independently asserted with `python3 -B` to have `status=PASS`, `passed=11`, `failed=0`, `SOURCE_ALIAS_ONLY`, and `SOFTWARE_STATE_ONLY`; the assertion command exited `0` and printed:

```text
{'status': 'PASS', 'checks': {'failed': 0, 'passed': 11, 'total': 11}, 'driver': 'SOURCE_ALIAS_ONLY', 'mailbox': 'SOFTWARE_STATE_ONLY'}
```

The existing read-only BC250 collector was run locally with `/proc/cmdline`, hostname, and uevent suppressed per runbook. Observed exit `0`, JSON parse exit `0`, `cards=[]`, `skipped_cards=[card1, device 0x1900, reason not the BC-250 APU (0x13fe)]`, `hardware_mutation=false`; capture hash `18ab5ffa58d04766c3e42605591d5306a9a7b4e3033a7e5cda3f74cfae504a5b`, collector hash `46712248ef3f690d82eb42d17592b7c5b4f0fdab20542eda8dcffef8ef70ed82`. This is a host-negative target filter result, **not** a BC250 capture.

Current report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-uclk-discrimination-guide.md`, SHA-256 `6c5dc2ef21a755a16a5a47c8106cd70cd3e6c4fa37783deda717250bf1f0c925`.
Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uclk-discrimination-guide/uclk-guide-result.json`, SHA-256 `169d7f88c710b033a8a68c006d0e56432c8bf532347a86eb483edf3bbc5b6346`.
Manifest: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-uclk-discrimination-guide/SHA256SUMS.final`, SHA-256 `4b4be963791e19a708cff40c991f1b350149ff8beecb62d09e8a6939a6204199`.

Final check: `python3 -m json.tool .../uclk-guide-result.json` exited `0`; `(cd evidence/firmware-audit/20260920-clv-uclk-discrimination-guide && sha256sum -c SHA256SUMS.final)` exited `0`; both entries `OK`. The exact native menu guide and native gate/counter reports were reopened; no ROM, BIOS, NVRAM, guest, AMIBCP, or hardware change occurred.

Exact remaining operator input: an operator-run read-only capture from authorized target PCI `1002:13fe` and the **current live** `AmdSetup+0x330` plus coupled-field values. Offline progress remains possible without that input by tracing `$INV 0x1204` beyond generic-reader/HOB boundaries and resolving a CLV UMC/DF/UCLK counter or divider/crossing status selector. Until both an independent physical UCLK source and selector exist, no live metric channel can confirm UclkDiv1M0 ratio semantics or `1:1:1`.
