# CLV voltage-offset downstream parser/sign boundary — intent

Timestamp: 2026-09-21 (Asia/Almaty). Actor: offset_consumer_route.

Scope: one read-only local disassembly trace after the already-completed
`AmdSetup+0x6E5/+0x6E6 -> $INV 0x1363/0x1364` serializer and exact-corpus
requester scans. The fixed plain CLV donor remains the only firmware target.

Target inputs:

- `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  (16 MiB, expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`)
- `evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442-0.code`
  (exact extracted x86 code section) and its retained assembly/instruction rows.

Question: does the next in-image `$INV` reader decode the producer's `0x1364`
type-2 four-byte payload as signed or unsigned, and which direct callers pass
that record ID? This is a parser/sign boundary check, not a second corpus-wide
literal census and not a voltage-actuation test.

Method/procedure (read-only):

1. Hash/reopen the pinned donor and exact AmdFabric code/assembly inputs.
2. Verify the serializer window at RVA `0x11956` (`0x1364`, type flag `2`,
   copy from `AmdSetup+0x6E6`) and the generic `$INV` parser at RVA `0x1D3C`.
3. Decode the parser's type switch `0x1E16..0x1E66` and the two local direct
   callers `0x1EB0..0x1EE5` and `0x1F76..0x1FBD`, recording the requested IDs.
4. Run a small host-side model of only those byte-backed parser operations,
   including the high-bit value `0x80000000`, to distinguish zero-extension
   from sign extension. No firmware execution is claimed.

Expected effect: a machine-readable static boundary result and a report that
identifies whether this generic reader performs signed conversion. It must not
assign a rail, mV unit, SoC/GFX identity, safe voltage, or applied effect.

Rollback: remove only this action log, the unique report, and the unique
`evidence/firmware-audit/20260921-offset-consumer-next/` directory. Inputs and
all predecessor artifacts remain untouched.

No hardware, network, install, ROM, NVRAM, register, or candidate operation is
permitted in this action.

## Method correction before final test

Exploratory `xxd` commands failed because `xxd` is not installed (shell exit
127). A subsequent `od` read initially used RVA as a raw `.code` file offset.
Reopening the retained listing header showed `.code` starts at image RVA
`0x240`; therefore the verified raw section offset for an RVA is
`RVA - 0x240`. The exploratory raw windows were misaligned and are discarded;
no finding is based on them. The final direct disassembly will set
`--adjust-vma=0x240` and the focused verifier will compare bytes at translated
offsets against the exact input.

## Correction after first verifier attempt

The first focused verifier attempt exited `1` with `FileNotFoundError` because
its repository-root calculation used `parents[2]`, resolving to `evidence/`
and producing `evidence/evidence/...`. No result was emitted and no input was
changed. The script was corrected to use `parents[3]`; the same bounded test
is rerun below.

The rerun then stopped at one verifier assertion: the producer payload-load
instruction begins at RVA `0x11979` (the preceding `0x11976` is
`mov edx,[ebp-0x4]`), and the control-field load begins at `0x11944` (the
preceding `0x11941` is the same register setup). These are verifier address
labels only; the retained assembly had already shown the correct instruction
sequence. The assertions were corrected before the final rerun.

## Observed result

Timestamp: 2026-09-21 (Asia/Almaty). The corrected bounded test completed with
verifier exit `0`, empty stderr, and `31` focused checks passed. GNU Binutils
`objdump` 2.47 completed the VMA-adjusted disassembly with exit `0` and empty
stderr. No ROM, NVRAM, register,
hardware, network, install, or candidate operation occurred.

Observed static boundary:

- `AmdFabricAriPei` parser entry RVA `0x1D3C` locates `$NVTB`, checks the `$INV`
  marker, walks typed records, and compares the requested ID against each record.
- The producer bytes at `0x11956..0x11982` encode `$INV 0x1364`, type low bits
  `2`, and unchanged dword load from `AmdSetup+0x6E6`; the paired control bytes
  at `0x11924..0x1194A` encode `$INV 0x1363` from `+0x6E5`.
- Type `2` at `0x1E47..0x1E50` copies a 32-bit payload and clears the output high
  dword. Type `0`/`1` use `movzx` followed by `cdq`, so no sign bit reaches the
  high dword there either.
- The module-local direct calls at `0x1EBD` and `0x1F94` request only `0x10FF`
  and `0x1104`; no local direct `0x1363`/`0x1364` call was found.
- Host-only high-bit controls returned `(0x80000000, 0)` and `(0xFFFFFFFF, 0)`
  for type `2`, confirming the decoded zero-extension model without executing
  firmware.

Final evidence paths and hashes:

- Report: `docs/research/2026-09-21-offset-consumer-next.md` (written after
  this result; final report hash recorded on readback).
- Verifier:
  `evidence/firmware-audit/20260921-offset-consumer-next/verify_offset_consumer_next.py`
  SHA-256 `0905924adc59b3804a1592975f8bf167586d56816fac744ab7cdf4bdaec0efeb`.
- Machine result:
  `evidence/firmware-audit/20260921-offset-consumer-next/offset-consumer-next-result.json`
  SHA-256 `9915782ca762b6930f43f7c0a66650e91d2ee04c40454d78a16966d4909dbb01`.
- Literal verifier stdout SHA-256
  `0cc5b0ec1b75d97800156d263ac008f9f8d0bd517b2c25d750f43613ac4fdfd7`;
  stderr is empty (`e3b0c442...`), exit file is `0`.
- Literal disassembly stdout SHA-256
  `eb0156d93cda1f00404e3878f320f61b36a0f211e8dd9ab9846fe7a90cf127db`;
  stderr is empty, exit file is `0`.

Remaining uncertainty: this parser is not shown to be invoked with `$INV 0x1364`.
Its zero-extension is therefore a signedness boundary, not an applied-voltage
result. The final consumer and any later sign/units conversion remain unknown.
The next method must follow a computed/indirect/HOB/PSP/ABL/SMU edge rather than
repeat the exhausted immediate-token scan.

Final report readback hash: `7c01e0cb4c1cb18bc7420076cdfc4b147fa42f66781e689388383637dc158f98`.

## Error-source ledger

- Exploratory `xxd -l ...` command: shell reported
  `/usr/bin/bash: line 1: xxd: command not found`; exit `127`. Replaced with
  `od` for raw-byte observation, then corrected the RVA-to-section-offset
  calculation as recorded above.
- First verifier command exited `1` with `FileNotFoundError: [Errno 2] No such
file or directory` for a constructed `/evidence/evidence/donor/...` path.
  Corrected root calculation from `parents[2]` to `parents[3]`.
- Second verifier attempt exited `1` with `AssertionError:
producer_0x1364_payload_load: '8b55fc8b82e6' != '8b82e6060000'`. Rechecked
  instruction starts, corrected payload load RVA from `0x11976` to `0x11979`
  and control byte load from `0x11941` to `0x11944`, then reran successfully.
