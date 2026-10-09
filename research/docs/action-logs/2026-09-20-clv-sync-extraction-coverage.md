# Exact-clv extraction/coverage audit — intent

## Intent (before evidence writes)

- Timestamp: 2026-09-20T15:00:00+05:00 (Asia/Almaty)
- Actor: delegated independent reviewer (`gpt-5.6-luna`, xhigh); root remains orchestration-only.
- Target: exact-clv extraction census `evidence/firmware-audit/20260919-inv-token-consumers/census.json`, coverage metadata, stage-1 extraction provenance, and the pinned clv ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Bounded task: determine whether the retained 233 executable census covers compressed/nested/raw PEI modules and name relevant pre-memory candidates; distinguish complete x86 PE32/TE coverage from raw/non-x86/indirect coverage gaps. Reuse the existing extractor/census; no new broad parser or consumer trace.
- Expected effect: one machine-readable coverage report, one human report, and this append-only action log. No firmware/hardware/settings/voltage writes, installs, commits, children, or shared MCP changes.
- Rollback: remove only this own evidence/report/log set and any later reviewed integration section.

## Observed result

Timestamp: 2026-09-20T15:20:00+05:00 (Asia/Almaty).

Final command:

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-extraction-coverage/extraction_coverage_verify.py
```

Observed exit status `0`; `8/8` checks passed. Final hashes:

```text
78d6fcff9aa01e5505f7ba6702d54ad7c59002760e19075f5270fc67b8a2cc95  evidence/firmware-audit/20260920-clv-sync-extraction-coverage/extraction_coverage_verify.py
9deee03eea28de0b5775b5079c28792d8f528956769773fa3311f8750e54ab90  evidence/firmware-audit/20260920-clv-sync-extraction-coverage/extraction-coverage-result.json
82cf97f5b199d6bb30ad302278f6996b6826152866923c93ef49aba5919da39e  docs/research/2026-09-20-clv-sync-extraction-coverage.md
```

Concrete result: the existing census covers all 233 retained x86 PE32/TE executable sections, including nested/guided provenance, and names the relevant pre-memory PEI candidates. It does not cover raw PSP/ABL/SMU/non-x86 payload semantics or arbitrary runtime/computed targets. No new parser, firmware, hardware, settings, voltage, installation, commit, or child-agent action occurred.
