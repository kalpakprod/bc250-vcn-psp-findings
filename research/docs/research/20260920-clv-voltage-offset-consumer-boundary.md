# CLV VDDCR_VDD offset: signed interpretation and consumer boundary

Historical scope: the later [token-ownership census](20260920-clv-inv-token-ownership.md) found seven inline serializer copies, not just the two checked here. The [container trace](20260920-clv-voltage-consumer-trace.md) located generic readers but no literal `0x1364` requester; computed and indirect consumers remain open. The field-to-token bytes below are unchanged.

## Current

One bounded exact-byte trace was completed from native HII/NVAR field to typed `$INV` serialization and the direct `AmdFabricAriPei` reader inventory. It stops before an applied voltage consumer or rail selector.

## Result

**PARTIAL / BLOCKED AT CONSUMER.**

### Field interpretation boundary

Exact CLV `CbsSetupDxe` IFR contains:

- Control QID `0x36B`, `AmdSetup+0x6E5`, `ONE_OF`, `Manual=1`, `Auto=0`.
- Value QID `0x36C`, `AmdSetup+0x6E6`, `NUMERIC`, raw width 4 bytes, numeric flags `0x12`, display bits `0x10`, bounds `0..0xFFFFFFFF`, step `0`.

The existing IFR text labels the value `HIDDEN` under a `SUPPRESS_IF` construct. The fresh bounded raw parser preserves the raw question record but does not decode that extended suppression construct as a stronger visibility proof. No signed interpretation, mV unit, VID code, IEEE-float meaning, or rail identity follows from the IFR type.

### Serializer trace

Both exact PEI serializers perform the same representation:

```text
AmdSetup+0x6E5 -> $INV record 0x1363, u8, flags low bits 0
AmdSetup+0x6E6 -> $INV record 0x1364, u32, flags low bits 2 (4-byte payload)
```

The value is copied unchanged; no arithmetic, sign conversion, mV scaling, VID conversion, or SoC/GFX selection is present in these bounded windows.

### Direct reader boundary

The exact `AmdFabricAriPei` generic reader path is `0x1D3C` / `0x1DFC`. Its two direct immediate call sites request only:

```text
0x10FF
0x1104
```

No direct immediate requester for `0x1364` occurs in this exact body. This is not a global absence claim: computed, indirect, HOB/DMA, and later runtime consumers remain unresolved.

## Verdict

The strongest current statement is: `AmdSetup+0x6E6` is a hidden/native-Setup u32 request serialized as `$INV 0x1364`, paired with control `$INV 0x1363`. The applied consumer, numerical conversion, physical rail identity, and hardware effect are unknown.

Therefore:

- Do **not** interpret `+150` as `1.15V`.
- Do **not** identify the field as SoC rather than GFX from driver labels.
- Do **not** call a BIOS setting an applied voltage or rail target.
- No voltage candidate or hardware action is justified by this trace.

## Fresh bounded execution

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/verify_voltage_offset_boundary.py
```

Observed stdout status: `PARTIAL_BLOCKED_AT_CONSUMER`; exit status `0`; stderr empty. The verifier reopened the pinned ROM, exact module bodies/assemblies, existing IFR parser, and EDK II header hashes. Earlier failed attempts were limited to verifier metadata/record-parser corrections and are retained in the action log; no source input changed.

Evidence class: `observed-bytes` + `static-analysis`. No ROM, NVRAM, register, hardware, candidate, or firmware mutation occurred.

## Inputs and hashes

- CLV ROM: 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- `CbsSetupDxe`: 264,160 bytes, SHA-256 `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`.
- `CbsBasePei` binary: 81,520 bytes, SHA-256 `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`.
- `CbsBasePei` assembly: SHA-256 `667dcb547b12ac6d545757270ddada1d282c8f070be57d4897a9f4b4060d72ff`.
- `AmdNbioSmuV10Pei` assembly: SHA-256 `1c74e94c6637ef7dfabcc9f03e85fffc698d730da512d61cbfe2cbaafb4186da`.
- `AmdFabricAriPei` assembly: SHA-256 `9c4744e1129052c965828694995bc60b250ce4bdb66d858584d090ea092b9f95`.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-voltage-offset-consumer-boundary.md`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/voltage-offset-boundary-result.json`
- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/verify_voltage_offset_boundary.py`
- Literal stdout: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/verifier-final6.stdout`
- Literal stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/verifier-final6.stderr`
- Exit status: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/verifier-final6.exit`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-voltage-offset-consumer-boundary.md`
