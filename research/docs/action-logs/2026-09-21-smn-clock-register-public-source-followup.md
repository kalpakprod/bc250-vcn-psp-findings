# 2026-09-21 SMN clock register public-source follow-up — action log

Date/time: 2026-09-21T18:05:57+05:00 (Asia/Almaty, UTC+05:00)  
Actor: `/root/clock_observability`  
Status: intent corrected before evidence/report creation; result pending.

## Intent

- **Bound objective:** determine whether an independent public AMD/Linux/coreboot primary source assigns clock-generator/SMN semantics to the exact PMFW-derived program/poll addresses `0x0116D150` and `0x0116D174` (raw `0x6D150/0x6D174`) for Group 6/domain ID `0x18`; no broad Ryzen DDR4 guidance.
- **Bound prior evidence:** completed selector result `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smu-domain-selector/selector-result.json` and previous local-header corroboration report `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-smn-clock-register-corroboration.md`. The previous selector author's disassembly is not rerun or duplicated.
- **Tool routing:** Agent Reach `doctor --json` ran first. Exa is not configured; Jina Reader is active for web reads; GitHub CLI is detected but doctor left active backend unset because no live status check was performed. No auth/status command or credential was used. Search/read only via Jina Reader; no installs.
- **Procedure:** bounded exact-address public search and one pinned coreboot Cezanne Data Fabric header retrieval; compare address terms only against that source's fields. Maximum three relevant primary sources; stop on missing semantic map rather than broadening into unrelated clock advice.
- **Expected effect:** exact public semantic mapping if found; otherwise a bounded source gap naming the exact missing AMD/Cezanne register map and the current backend/search limits.
- **Preservation:** no hardware, network writes, account changes, ROM/NVRAM/register/firmware changes, or raw personal-export access. The CLV `AmdSetup+0x316=0x24` request stays unmodified.
- **Rollback:** no input/source files are modified. Remove only this new report, this matching log, and the unique evidence directory if invalidated.
- **Acceptance event:** direct Agent Reach retrieval/search output and one bounded static source test with exit/stdout/stderr plus artifact readback.

## G7 correction — unquoted heredoc expanded action-log Markdown

The first intent-file write used an unquoted heredoc containing Markdown backticks. Bash expanded them as command substitutions, emitting `Permission denied`, `command not found`, and `No such file or directory` messages and leaving blank fields; the command proceeded to its final hash output. The malformed log body was reopened above, rewritten with a Python literal, and read back. No source, ROM, register, network, account, or target evidence was changed. This repeats the procedure error documented in `memory/incidents/2026-09-20-bash-markdown-heredoc-expansion.md`; a separate G7 memory record will be added before further research.

## Continuation scope adjustment (2026-09-21T18:17+05:00)

The root supplied the newer completed `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-smu-domain18-identity.md` and its result `evidence/firmware-audit/20260921-smu-domain18-identity/domain18-identity-result.json`. Current result SHA-256 is `f4a005400dba428ff8ba8f782d67bfa608c9e5fc714c5771075c48d6467e5cbe`; it confirms the same `0x0116D150` / `0x0116D174` addresses but still classifies physical identity unresolved. The next local verification will bind to this newest completed result instead of the superseded selector JSON identity. No disassembly, source search, or address derivation will be repeated.

## Observed public-source and latest-result verification (2026-09-21T18:59:52+05:00)

- **Agent Reach:** `doctor --json` identified Jina Reader as the active general-web read backend. Exa was off/unconfigured. GitHub CLI was not live-verified; no `gh` command, authentication status call, login, or credential was used.
- **Bounded search output:** grep.app exact `116D150` returned HTTP 429; DuckDuckGo exact `0x116D150` and variant `6D150` queries returned no results; GitHub code search page required sign-in. No sign-in or backend setup was attempted.
- **External sources retrieved through Jina Reader:**
  1. coreboot/coreboot Cezanne `data_fabric.h` at commit `b7931d1afacdc6666b4812305a14ed3deb431201`; Jina response SHA-256 `fdf8b9a6a6b45e75fd4dd8b2031708ad8baffdec96005f9885c923d830afc460`; normalized content equals the local pinned copy. It declares generic DF configuration offsets, no target pair or clock-tree name.
  2. torvalds/linux v6.8 `gc_10_1_0_offset.h`; Jina response SHA-256 `0834a1a258b52935e37d56fea479fa62ce2c845c7a76a93c8efad5c3b886e8d2`; exact target-address match count `0`. The local imported header hash differs from the fetched v6.8 body; they are not conflated.
  3. torvalds/linux v6.8 `gfx_v10_0.c`; Jina response SHA-256 `4bd9bb4a4738817158d0a907d304bd9ac955a6631b54746a0b93d3ec904c42fb`; exact target-address match count `0`; no additional clock/telemetry semantics from this file are adopted.
- **Latest selector input:** after the earlier selector JSON changed, the new test binds the later report result `evidence/firmware-audit/20260921-smu-domain18-identity/domain18-identity-result.json`, SHA-256 `f4a005400dba428ff8ba8f782d67bfa608c9e5fc714c5771075c48d6467e5cbe`. It confirms dynamic domain `0x18`, Group 6, program `0x0116D150`, poll `0x0116D174`, physical clock identity unresolved. No selector disassembly was rerun.
- **Verification command:** `python3 -B evidence/firmware-audit/20260921-smn-clock-register-public-source-followup/verify_public_source_gap.py`
- **Observed stdout:** `{"checks": {"failed": 0, "passed": 16, "total": 16}, "latest_result": "domain18-identity-result.json", "output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smn-clock-register-public-source-followup/public-source-gap-result.json", "physical_clock_identity": "unresolved", "poll": "0x0116D174", "program": "0x0116D150", "source_families": 2, "source_files": 3, "source_literal_hits": 0, "status": "PASS", "verdict": "bounded-public-source-gap"}`
- **Exit/status:** `0`; stderr empty (`0` bytes); result checks `16/16` PASS.
- **Evidence:** latest result JSON SHA-256 `a0cd9c890d033081a97a4d81d3bf979e4fda7bc802928450ff6000c3bf093f06`; retrieval ledger and three source files are hash-pinned in `evidence/firmware-audit/20260921-smn-clock-register-public-source-followup/`; `sha256sum -c SHA256SUMS.final` verifies all entries `OK`. Report: `docs/research/2026-09-21-smn-clock-register-public-source-followup.md`.
- **Bounded verdict:** two independent public source families were checked; no direct address or physical-clock semantic mapping was found. Exact AMD/AGESA/SMN domain/register dictionary remains missing.
- **No hardware/install/auth:** no board, sysfs, network write, credentials, install, ROM/NVRAM/register/firmware write, or account change occurred.

## G7 correction: verifier input moved to the newer completed result

The first verifier version pinned the prior selector result hash `81755d70…` and exited `1` (`15/16`) when the selector result had changed to `97be0a4254c76123235dd23ea7dbf196b77e183c392083c91aaee42c832a0a38`; this was a stale-verifier-input mismatch, not a source-address contradiction. After the root supplied the completed domain18 identity report, the verifier was updated to pin its current result hash `f4a00540…` and rerun with exit `0`, `16/16`. The original failure is preserved as `verify_public_source_gap-v1.py`, `public-source-gap-result-v1.json`, and `source-verification-v1.*`.

A separate attempt to invoke `chmod` used an unset shell variable and returned `chmod: cannot access '/verify_public_source_gap.py'`; the bounded verifier was then run with an absolute path, without permissions changes, and produced the recorded PASS. A first console-summary field was mislabelled `literal_matches` while printing the ROM hash; the corrected readback output is `PASS result_checks={'failed': 0, 'passed': 16, 'total': 16} sources=3 address_hits=0 source_identity=f4a005400dba428ff8ba8f782d67bfa608c9e5fc714c5771075c48d6467e5cbe`. The machine result is authoritative. No source/ROM/input was modified.

## Completion status

The bounded public-source branch is complete. No AMD/Linux/coreboot source in the three-file limit maps the PMFW-derived SMN address pair to a physical clock; the exact missing register/domain source is named in the report. No further broad search is authorized in this slice.
