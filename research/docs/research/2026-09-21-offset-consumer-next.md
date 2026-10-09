# CLV voltage-offset downstream parser/sign boundary

## Current

TARGET is the fixed plain CLV donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; the bounded downstream object is the exact extracted `AmdFabricAriPei` x86 code section and retained disassembly. RESULT is a static parser boundary. NEXT remains an indirect/computed/HOB/PSP/ABL/SMU consumer trace; no voltage candidate or hardware action is justified.

## Conclusion

The next local `$INV` reader implementation, `AmdFabricAriPei` RVA `0x1D3C`, does **not** sign-convert the producer's `0x1364` payload:

- The serializer at RVA `0x11956` emits record ID `0x1364`, sets low type bits to `2`, loads the unchanged dword from `AmdSetup+0x6E6`, and stores it at record `+0x3`.
- The parser's type-2 branch at RVA `0x1E47` loads that dword with `mov eax,[record+3]`, writes it to the low output dword, then clears the high output dword with `and dword ptr [out+4],0`. A high-bit input therefore remains `0x80000000`, not `-2147483648`.
- The parser's type-0/type-1 branches use `movzx` before `cdq`, so they also do not sign-extend their byte/word payloads.
- A module-local direct-call check finds two calls to this parser, requesting `0x10FF` (caller RVA `0x1EB0`, call `0x1EBD`) and `0x1104` (caller RVA `0x1F8B`, call `0x1F94`). Neither requests `0x1363` or `0x1364`.

This is a **reader/sign-conversion boundary**, not proof that this routine consumes `0x1364` at runtime. It proves that, if a caller supplied `0x1364`, this generic parser would expose an unsigned/zero-extended 32-bit value in its two-dword output pair. The actual caller/consumer and any later signed conversion remain unresolved.

## VDD, SoC, and GFX separation

The exact field pair in this trace is:

- `AmdSetup+0x6E5` / `$INV 0x1363`: `VDDCR_VDD Voltage Offset Control` / one-byte control.
- `AmdSetup+0x6E6` / `$INV 0x1364`: `VDDCR_VDD Voltage Offset` / four-byte value.
- `AmdSetup+0x6EA` / `+0x6EB`: separate `VDDCR_GFX` control/value pair; it is not the producer field traced here.

`VDDCR_VDD` is a firmware/HII label only. This trace does not map it to the SoC rail, does not establish a signed-millivolt encoding at the actuator, and does not connect it to `VDDCR_SOC` telemetry calibration fields. It provides no basis for interpreting `+150` as `1.15 V`, selecting a safe voltage, or claiming applied voltage.

The prior exact-clv HII inventory records the value help string as “signed integer [mV]”, while IFR declares a four-byte unsigned numeric field bounded `0..0xFFFFFFFF`; the generic parser then zero-extends that payload. If the UI intends a signed quantity, the required reinterpretation must occur after this parser in a later consumer, which this bounded trace did not identify.

## Bounded static test

The final test reopened the pinned inputs, ran a VMA-adjusted disassembly of only the parser window, and ran the focused verifier:

```text
objdump -D -b binary -m i386 -M intel --adjust-vma=0x240 \
  --start-address=0x1d3c --stop-address=0x1e8f \
  evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442-0.code
```

Observed GNU `objdump` 2.47 exit status: `0`; stderr: empty.

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  evidence/firmware-audit/20260921-offset-consumer-next/verify_offset_consumer_next.py
```

Observed verifier exit status: `0`; stderr: empty; all `31` focused checks passed; result:

```text
{"checks": 31, "status": "STATIC_PARSER_BOUNDARY_ONLY"}
```

The verifier checks the pinned donor hash, exact code/assembly/instruction-row hashes, the `0x1363/0x1364` producer bytes, parser switch bytes, two local caller windows, and a host-only high-bit model of the decoded operations. It does not execute firmware.

## Evidence and hashes

- Plain CLV donor: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact `AmdFabricAriPei` code section: `evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442-0.code`, SHA-256 `2a32fef056825e8f201db78402e0303f9541aa90013df2e56c78550c5a3f2db9`.
- Retained assembly: `.../AmdFabricAriPei-c5b99650a442-0.asm`, SHA-256 `9c4744e1129052c965828694995bc60b250ce4bdb66d858584d090ea092b9f95`.
- Retained instruction rows: `.../AmdFabricAriPei-c5b99650a442.instructions.json`, SHA-256 `77b1d4be4393fbbf920847398ae5667c42b3841066d40c2aaace1b49036c81e1`.
- Verifier: `evidence/firmware-audit/20260921-offset-consumer-next/verify_offset_consumer_next.py`, SHA-256 `0905924adc59b3804a1592975f8bf167586d56816fac744ab7cdf4bdaec0efeb`.
- Machine result: `evidence/firmware-audit/20260921-offset-consumer-next/offset-consumer-next-result.json`, SHA-256 `9915782ca762b6930f43f7c0a66650e91d2ee04c40454d78a16966d4909dbb01`.
- Literal disassembly stdout: `evidence/firmware-audit/20260921-offset-consumer-next/reader.objdump.stdout`, SHA-256 `eb0156d93cda1f00404e3878f320f61b36a0f211e8dd9ab9846fe7a90cf127db`; stderr is empty, exit file records `0`.
- Literal verifier stdout: `evidence/firmware-audit/20260921-offset-consumer-next/verifier.stdout`, SHA-256 `0cc5b0ec1b75d97800156d263ac008f9f8d0bd517b2c25d750f43613ac4fdfd7`; stderr is empty, exit file records `0`.
- Action log: `docs/action-logs/2026-09-21-offset-consumer-next.md`.

## Evidence class and limits

Evidence class is `observed-bytes` plus `static-analysis`, with a host-tested model of the decoded instructions. The parser is not shown to be invoked with `0x1364`; no final consumer, rail selector, unit/sign conversion after this parser, PMFW/SMU application, physical voltage, thermal/electrical limit, or hardware behavior is observed. The prior exact-corpus immediate scan is not repeated here.

No ROM, NVRAM, register, firmware, hardware, candidate, network, or installation action occurred. The original donor and all predecessor artifacts remain unchanged.
