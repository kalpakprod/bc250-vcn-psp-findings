# PMFW Queue3 domain/request independent review — action log

## Intent (before verification)

- Timestamp: 2026-09-21T16:17:38+05:00 (Asia/Almaty).
- Actor: bounded offline reviewer `/root/clock_claims_adjudication`.
- Active object: `evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/trace_clock_sources.py` and retained result `evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/source-consumer-result.json`.
- Last confirmed result: retained machine result status `PASS`, checks `25`, SHA-256 `08a30b4bc9f7153ff81f532ebf5203d355f27840c3aca59e58a51797b50f7b63`.
- Next executable action: rerun the existing command metadata (`python3 -B trace_clock_sources.py`) in a disposable copy of its evidence directory, then compare the generated result to the retained one.
- Input paths: `evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/trace_clock_sources.py`, `evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/VERIFICATION.txt`, `evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/source-consumer-result.json`, and the byte-backed inputs named by the runner.
- Scope: Queue 3 `0x1D` source/request path, P-state bulk-loader input, Queue ID 4 `0x07` DF table input; independently assess whether `ufloat.s` and selectors establish physical clock identities. No HOB/heap tests.
- Safeguards: offline only; no hardware, MMIO, mailbox, NVRAM, ROM, candidate, network, or source changes.
- Rollback: delete only this report, this log, and the disposable `/tmp` run directory.

## Prior dispatcher error (retained)

- The earlier dispatcher printed `DISPATCH_ERROR: matching Q3 action metadata had no local verifier/trace runner path` after searching for a script name in a different log. The actual checkpoint names `trace_clock_sources.py`; the verifier was not started by that dispatcher. Its wrapper exit status was not retained in the visible output, so none is claimed here. Corrected method: use the exact runner named by `2026-09-21-smu-clock-entrypoints-continuation.md` and `VERIFICATION.txt`.

## Observed verification result

- Timestamp: 2026-09-21T16:17:38+05:00 (Asia/Almaty).
- Command: `python3 -B evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/trace_clock_sources.py` run from disposable directory `/tmp/bc250-smu-domain-review-aj32__3z`; only the copied evidence output directory was writable in the mirror.
- Exit: 0; stdout/stderr are retained only under the disposable run directory (`stdout.txt`, `stderr.txt`, `exit.status`).
- Result SHA-256: retained `08a30b4bc9f7153ff81f532ebf5203d355f27840c3aca59e58a51797b50f7b63`; rerun `08a30b4bc9f7153ff81f532ebf5203d355f27840c3aca59e58a51797b50f7b63`; identical `True`.

## Independent semantics review result

- Timestamp: 2026-09-21T16:34:54+05:00 (Asia/Almaty).
- Exact input/tool provenance: pinned CLV ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; Robin-5 PMFW SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`; retained disassembly `ghidra-decompiles.txt` SHA-256 `5f1f963f7139754e005b0bfb66a296a4a362b9b80f0e3d12591a471e54650112`; local Xtensa SLEIGH file SHA-256 `93b33680e0a1eeb844f632401d7374479a008ed5e2240e5b10b7d60cb1acf1c6`, repository commit `3f47768eace8ad8ad86c480a55637d14467cffcd`.
- Source qualification: the imported `xtensaInstructions.sinc` is marked modified in its worktree, but `git diff --ignore-space-at-eol` is empty and its `UFLOAT.S` block hashes identically to committed HEAD (`f1953913725dce53e3b40f43de37697829e711a8d61b57698d639c61d8829ebd`). This review did not edit it.
- Static evidence: existing listing shows `0x2EA2F extui` extracting low16, `0x2EA35 ufloat.s f0,a14,0`, then `0x2EA3B ssi` storing it. The local SLEIGH definition is `float(zext(A)) / 2^immediate`; immediate 0 yields identity numeric conversion. Queue3 high16 is an index followed by separate domain-ID lookup; Queue4 `0x07` splits mode `0x01` and low-byte P-state index.
- Host semantic command: the exact `python3 -B` heredoc is preserved under “Bounded host semantics test” in `docs/research/2026-09-21-smu-domain-independent-review.md`.
- Literal output from the observed run:

```text
LOCAL_SLEIGH_SEMANTICS: ufloat.s -> int2float(zext(A)) / int2float(1<<imm)
OPERAND_IMMEDIATE: 0; FRACTIONAL_SCALE: 1; MODELLED_OUTPUT: unsigned low16 unchanged as binary32
HOST_MODEL u16=0x0000 -> f32=0.0
HOST_MODEL u16=0x0001 -> f32=1.0
HOST_MODEL u16=0x006D -> f32=109.0
HOST_MODEL u16=0x036B -> f32=875.0
HOST_MODEL u16=0x04B0 -> f32=1200.0
HOST_MODEL u16=0x06D6 -> f32=1750.0
HOST_MODEL u16=0x0708 -> f32=1800.0
HOST_MODEL u16=0xFFFF -> f32=65535.0
Q3_WORD 0x00010708 -> domain_index=1, raw_request=1800
Q4_WORD 0x0103 -> mode=0x01, pstate_index=3
INFERENCE: units and physical MCLK/UCLK/FCLK identities are not encoded by these conversions/selectors
LIMIT: host semantic model, not Xtensa instruction execution or hardware measurement
SUMMARY: 8/8 conversion cases + 2 selector cases PASS; exit=0
```

- The rerun process returned exit `0`; stderr was empty. The wrapper explicitly displayed `exit_code=0` on the second observed host-model run.
- Disposable prior-verifier outputs: `/tmp/bc250-smu-domain-review-aj32__3z/stdout.txt` SHA-256 `beb6f5a6356f6bd0f845fc3cf2adef0ba8f3f3506622c824c758bab65c38c66b`; `stderr.txt` is empty (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`); `exit.status` SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` contains `0`.
- Bounded emulator availability check found no `qemu-system-xtensa`, `qemu-system-xtensaeb`, `qemu-xtensa`, Unicorn, pypcode, angr, Capstone, Rizin, `rz-bin`, or `analyzeHeadless`. The active Ghidra MCP program was `/bin/true` (`x86:LE:64`); available read-only P-code/disassembly calls are not an Xtensa execution run. Therefore no firmware/emulator execution is claimed.
- Accepted inference: immediate-0 `ufloat.s` preserves the low-16 request's numeric magnitude at the target-float store boundary.
- Rejected inference: that numeric value or a mode/P-state index proves physical MHz, MCLK/UCLK/FCLK identity, or 1:1:1 synchronization. Downstream actuator interpretation and physical-domain mapping remain unresolved.
- Report: `docs/research/2026-09-21-smu-domain-independent-review.md`.
- Final report SHA-256 and this action-log SHA-256 are recorded by the final readback command; this log is self-referential and does not embed its own final hash.
- No ROM, source, imported code, firmware, hardware, register, NVRAM, network, shared report, or shared memory was modified. No HOB/heap test was run.

### Literal prior-verifier output readback

The disposable child output reopened at `/tmp/bc250-smu-domain-review-aj32__3z/stdout.txt` was:

```json
{
  "checks": 25,
  "preserved_clv_request": {
    "AmdSetup_offset": "0x316",
    "byte": "0x24",
    "label": "1800MHz",
    "rom_offset": "0x7E5"
  },
  "pstate3": {
    "row": "0xCF84",
    "stored_plus_0x04": 1200.0,
    "stored_plus_0x10": 875.0,
    "stored_plus_0x14": 109.375,
    "stored_plus_0x18": 1750.0
  },
  "source_edges": {
    "q3_0x1d": {
      "bulk_source": "0x2E9DC reads 0x7B5C+pstate*100+0x48 -> 0x14038",
      "consumer": "0x2E788 -> 0x23890 -> 0x235C8",
      "handler": "0x2EA08",
      "mailbox": "Queue ID 3 msg 0x1D",
      "setup_join": "not observed",
      "target_source": "low16 mailbox arg -> ufloat.s -> 0x1402C+index*12",
      "unit": "raw unsigned integer; no MHz/divider scale encoded"
    },
    "q4_0x07": {
      "consumer": "0x23B7C/0x23BA8/0x23BF4 -> 0x23F18",
      "dispatch": "0x79E8/0x79EC",
      "handler": "0x1E720 -> 0x1E448",
      "mailbox": "raw Queue ID 4 msg 0x07",
      "selector": "high byte mode 0x01, low byte pstate index",
      "setup_join": "not observed",
      "table": "0xCF0C, 5 rows x 0x28",
      "unit": "fixed-point/DID arithmetic reproduces numeric stored floats; physical MHz identity unresolved"
    }
  },
  "status": "PASS",
  "unresolved": "provider/caller join from native AmdSetup/ABL1/APOB to mailbox args; physical MCLK/UCLK/FCLK assignment and crossing selector"
}
```

`stderr.txt` reopened at the same disposable path was `0` bytes; `exit.status` contains literal `0`. The follow-up exact host-model command recorded in the report returned process exit code `0` and empty stderr.

### Closeout correction and host-execution limits

- Command-line clarification (G7): the prior relative command line is the command from the disposable project CWD; the actual command event was `python3 -B /tmp/bc250-smu-domain-review-aj32__3z/project/evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/trace_clock_sources.py`, executed with CWD `/tmp/bc250-smu-domain-review-aj32__3z/project`. `VERIFICATION.txt` includes `PYTHONDONTWRITEBYTECODE=1`; the copied run retained `-B`, which provides bytecode suppression. The source/result identity comparison passed.
- Exact emulator inventory command exited 0 and reported: `qemu-system-xtensa`, `qemu-system-xtensaeb`, `qemu-xtensa`, `rizin`, `rz-bin`, `analyzeHeadless`, `unicorn`, `pypcode`, `angr`, `capstone` all `NOT_FOUND`.
- Ghidra MCP `get_metadata` returned `/bin/true`, `Architecture: x86`, `Language: x86:LE:64:default`; current session is not the Xtensa PMFW and its read-only P-code/disassembly tools are not an execution endpoint.
- Exact report-host-model command is reproduced in the report. The final observed execution returned exit code `0`, stderr empty, and literal summary `SUMMARY: 8/8 conversion cases + 2 selector cases PASS; exit=0`.
- Accepted inference: `ufloat.s` at immediate zero numerically preserves the unsigned low-16 request through the target-float store boundary. Rejected inference: that value is MHz or that either selector names a physical MCLK/UCLK/FCLK path or a 1:1:1 state.
- Report path reopened: `docs/research/2026-09-21-smu-domain-independent-review.md`; its final hash is recorded after final readback below.
- Final research report SHA-256: `bc8d7e9e125f8f200b39d90bb5421256b502430733ed797101ae78f313445fd8`.

## Final readback

- Timestamp: 2026-09-21T16:34:54+05:00 (Asia/Almaty).
- Final independent readback command: `python3 -B` heredoc reopened and hash-checked the report, this action log, original queue-trace report/log/script/result, pinned CLV ROM, Robin-5 PMFW, SLEIGH semantics source, and existing Ghidra listing; it checked the disposable rerun exit/stderr/result equality and report/action-log presence.
- Observed result: process exit `0`, `FINAL_READBACK: 17/17 PASS`.
- Final research report SHA-256: `bc8d7e9e125f8f200b39d90bb5421256b502430733ed797101ae78f313445fd8`.
- The report/action-log paths were reopened; the project input hashes match those recorded above. The original trace result remains unchanged and its disposable rerun is byte-identical. The exact CLV request `AmdSetup+0x316=0x24` was preserved.
- No ROM, source, firmware, board, register, NVRAM, shared trace, or memory file was modified; all verifier outputs remained in `/tmp`.
