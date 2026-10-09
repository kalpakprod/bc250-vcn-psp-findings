# CLV ABL1 reader fallback/sentinel semantics — intent

Timestamp: 2026-09-20T08:45:00+05:00 (+05:00)
Actor: luna-xhigh independent bounded executor
Target: exact ABL1 generic reader payload `0x1FB4..0x209C`, using pinned raw bytes and the already reviewed reader/output-context artifacts.

Bounded question: distinguish ordered-list fallback driven by helper status from value/sentinel handling. Verify whether the reader advances to another descriptor when the helper returns success with an Auto/sentinel value, or whether it stops/fails at the first successful provider result. Do not trace new providers, frequency units, PLL/divider semantics, runtime invocation, hardware, firmware, settings, candidates, MCP/Cutter, or source-wide paths.

Pinned inputs:

- Exact ABL1 `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing reader result `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json`, SHA-256 `537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128`.
- Existing output/context result `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1-reader-output-context-result.json`, SHA-256 `d5c43692d0b3b8d6d31b95c22ec02a8d1764a44ef4c89d7a9c6a3c5f99b4e48`.

Expected effect: one new verifier, machine-readable result, stdout/stderr, report, manifest, and this action log. Append-only integration to `memory/oc-recheck.md` and `specs/2026-09-20-clv-sync-development-plan.md` is authorized after the independent check. No pinned input changes.

Next executable action: run a minimal exact-byte verifier for the helper-status branches, first-stage value==1 gate, final typed sentinel guards, and absence of fallback branch from those sentinel guards.

Rollback: remove only the uniquely named evidence directory, report, this action log, and the two append-only integration paragraphs; preserve all pinned inputs and prior reports.

## Input-hash correction before verifier

The intent ledger initially transcribed the existing output/context result hash incorrectly as `d5c43692d0b3b8d6d31b95c22ec02a8d1764a44ef4c89d7a9c6a3c5f99b4e48`. Direct `sha256sum` before verifier execution measured `6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21`; the reader result remained `537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128`. Only the expected metadata value will be corrected in the new verifier; no input changed.

## Execution and correction ledger

Commands were run against the same pinned exact ABL1 bytes:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1_reader_fallback_status_verify.py
```

Observed verifier corrections, all limited to the new checker (inputs unchanged):

1. Exit `1`: existing output/context result stores the Fclk path under nested `result.fclk_output_path`, not a top-level `context_store`; changed only the metadata lookup.
2. Exit `1`: first-stage diagnostic slice expected one extra zero byte after `str.w r8,[sp]`; corrected exact raw slice to observed bytes.
3. Exit `1`: final helper status slice was eight bytes while the expected literal covered six; added the exact `28 d0` conditional bytes.

Final observed exit `0`, status `PASS`, `37/37` checks, stderr empty. Literal stdout/stderr are retained in the owned evidence directory.

## Finding

The reader has two distinct mechanisms:

- **Advance/fallback flag:** helper return `R0`. A zero status goes through `0x2002`, then the index increment at `0x200E`, and can try the next list element. A nonzero status enters value handling.
- **Value validation:** first-stage non-final elements must return byte value `1`; any other value, including a sentinel-like `0xFF` under `r7=0`, returns reader failure at `0x209A` rather than trying another descriptor. The final typed element has width-specific sentinel guards. For type 2, returned `0xFFFF` with `r7=0` is rejected before `STRH`; no fallback increment branch occurs in that slice. Type 1 rejects `0xFF`, type 4 rejects zero, and type 8 rejects a zero doubleword under the same terminal failure pattern.

Therefore the ordered descriptor chain is **not** combined-key fallback on arbitrary values: earlier entries act as boolean gate/status stages, and the last entry is the typed value stage. A provider success carrying Auto/sentinel does not fall through to another token.

## Final execution/readback

Final verifier command: `python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1_reader_fallback_status_verify.py`.
Observed exit `0`, `64/64 PASS`, stderr empty. The independent output/context cross-review pins the worker result `6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21` and raw-checks its core path. The Fclk accessor's type pointer is `SP+0x0C`; exact listing shows no explicit store to that local between `0x463C` and `0x466A`. Therefore the later halfword load/store path is observed, but execution of the generic reader's type-2 branch for this caller is not established. The `0x4B0` local default is committed to `context+0x78` even when the accessor skips its success store; later `0x3E8/0x4B0` comparisons are thresholds, not a token-ID decode.

Verifier correction log, all checker-only and same pinned inputs:

1. Exit `1`: output-context result did not have a top-level `context_store`; nested path was located at `result.fclk_output_path`.
2. Exit `1`: diagnostic sequence slice expected one extra zero; actual bytes begin `cd f8 00 80 2c a2...`.
3. Exit `1`: final helper status slice was 8 bytes, not the initially selected 6 bytes; appended the actual `28 d0` branch.
4. Exit `1`: Fclk default-seed slice included the next `movs r1,#0xf`; narrowed slice to end before it.
5. Exit `1`: non-equality test encoded as an equality assertion; changed the expected boolean to false.
6. Exit `1`: `ldrd r7,r9` expected bytes reversed; exact raw bytes are `dd e9 0c 79`.
7. Exit `1`: `strd r8,r0` expected bytes reversed; exact raw bytes are `cd e9 00 80`.

Shared integration appended without changing existing phase gates:

- `memory/oc-recheck.md` adds the precedence/sentinel qualification.
- `specs/2026-09-20-clv-sync-development-plan.md` adds an append-only clarification and explicitly retains phase 2 as **PARTIAL**.
- This report qualifies the earlier generic fallback wording; earlier artifacts remain unedited as history.

Manifest is `evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/SHA256SUMS.final`; it covers owned evidence, report/log, and both append-only integration records. No image, firmware, hardware, setting, candidate, source, or installed component changed.

## Final verifier expansion correction

After the initial 37-check result, the bounded verifier was expanded only with independent caller-side checks: `R7` stack-mask provenance, Uclk/Fclk zero first stack argument, Fclk `SP+0x0C` type-pointer ownership, Fclk local `0x4B0` fallback store, context `+0x78` commit, downstream `0x3E8/0x4B0` comparisons, and token/threshold non-equivalence. The final verifier was rerun on the same exact ABL1/listing inputs: exit `0`, `64/64 PASS`, stderr empty. The report now labels 64/64 final; the earlier 37-check result remains historical execution evidence.
