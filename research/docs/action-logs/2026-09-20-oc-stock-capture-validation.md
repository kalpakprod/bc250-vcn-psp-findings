# Stock capture route validation

## Intent — 2026-09-20T01:35:05+05:00

Actor: root; no delegation because collector inspection and fixture verification are coupled. Root confirmed /home/OWNER/orca/projects/bc250. Python 3.14.7. Read memory/INDEX.md, oc-recheck.md, tools.md, applicable instincts and probe/verification skills; inspected both existing collectors and DF1400 runbook.
Reuse scripts/probe_bc250_clocks_readonly.py: exact default 1002:13fe filter, stdout JSON, no raw hardware access. Do not run collect_stock_runtime_readonly.py: broader AMD-only selection, journal and command-line collection are unnecessary for this task. No new collector or firmware changes.
Local identity-only inspection of DRM vendor/device found card1 1002:1900, NOT the target 1002:13fe. No local OC capture can be called a BC250 baseline. No remote connection, credentials or raw command-line read authorized by this step.
Procedure: add tests/test_bc250_clock_probe.py using synthetic sysfs and patched host metadata, execute unittest discovery and the probe on an empty synthetic tree. Write docs/runbooks/2026-09-20-oc-stock-capture.md with target gates, timeouts, exact capture fields and interpretation. Retain verification output and SHA-256 manifest in evidence/firmware-audit/20260920-stock-capture-check/. Append observed result and bounded memory finding.
Expected: host-tested filtering/serialization, not live frequency verification. Rollback: remove only these newly created test/runbook/evidence files; preserve audit correction. Existing files and original firmware remain unchanged. Hardware capture, independent clocks, SoC voltage and BIOS application remain unrun.

## Result

PASS: five new fixture checks and all 11 existing tests (16 total). `project test` had no detected command; used `python3 -m unittest discover -s tests -v`, recorded output and Python/source hashes in evidence/firmware-audit/20260920-stock-capture-check/verification.json and tests.txt. PASS: runbook shell/Python syntax and extracted Python invocation on empty synthetic DRM with host reads mocked; source-suppressed fields checked. Evidence: runbook-check.json. No production probe modification, firmware write, hardware probe or network action. Authorized board access/operator-run capture remains required; independent physical clocks remain a separate research gap. Existing worktree changes preserved.
