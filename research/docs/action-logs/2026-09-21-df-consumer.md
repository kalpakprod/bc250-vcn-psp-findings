# DF override tokens 0x1373/0x1374 consumer and boundary — action log

## Intent

- Timestamp: 2026-09-21T13:40:00+05:00 (Asia/Almaty)
- Actor: project executor, slot 4 bounded trace
- Target: `evidence/firmware-audit/20260921-df-consumer/`; `docs/research/2026-09-21-luna-df-consumer-boundary.md`
- Scope: investigate downstream consumer / reader edges for DF override tokens `0x1373` (`DfPstateOverride`) and `0x1374` (`DfClockOvrd`) in CLV 5.00 donor (`BC250_5.00_clv.bin`).
- Procedure:
  1. Inspect `AmdFabricAriPei` (`c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78`) at serialization sites `0x11ace` (`0x1373` from `AmdSetup+0x703`) and `0x11b00` (`0x1374` from `AmdSetup+0x704`).
  2. Inspect CBS counterpart registration descriptor at `0x16a78` (CBS GUID `04126c85-...`, Notify GUID `60db76a0-...`, callback `0x6a88`).
  3. Audit direct reader invocations in both known `$INV` reader modules (`AmdFabricAriPei` and `AmdCcxVhAriDxe`).
  4. Perform a corpus-wide scan across all 233 extracted CLV modules for any direct queries of tokens `0x1373` and `0x1374`.
  5. Run an automated verification script to produce machine-readable JSON evidence and SHA256 manifest.
- Rationale: resolve whether DF clock overrides have direct UEFI PEI/DXE consumers or terminate at the `$INV` / ABL1 / APOB / SMU boundary.
- Expected effect: establish exact byte-backed evidence of DF override serialization and bounded negative on direct UEFI readers.
- Rollback: remove `evidence/firmware-audit/20260921-df-consumer/`, `docs/research/2026-09-21-luna-df-consumer-boundary.md`, and this action log.

## Observed result

Timestamp: 2026-09-21T13:48:00+05:00 (Asia/Almaty)
Command:

```bash
python3 -B evidence/firmware-audit/20260921-df-consumer/verify_df_consumer.py
```

Exit code: `0`
Literal stdout:

```text
=== Starting DF Override Tokens 0x1373/0x1374 Consumer Audit ===
[PASS] ROM Hash: Got ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8
[PASS] AmdFabricAriPei Hash: Got c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78
[PASS] AmdCcxVhAriDxe Hash: Got d9bc6337e3d039922016e95ed8be1fda5d7fb3e0250e43a6058d9c0d305997f0
[PASS] Fabric 0x1373 Serialization: Offset 0x11ace, reads AmdSetup+0x703
[PASS] Fabric 0x1374 Serialization: Offset 0x11b00, reads AmdSetup+0x704 (u16)
[PASS] Fabric CBS Counterpart Descriptor: CBS GUID match=True, Notify GUID match=True, Callback VA=0x09E227A0, Event=0xFFFFFFFE
[PASS] Fabric Ari Pei Direct Queries: Queries 0x10FF at 0x1D18, 0x1104 at 0x1DF3; Zero queries for 0x1373/0x1374
[PASS] CCX Ari Dxe Direct Queries: Queries 0x1000 at 0x5CA0, 0x1001 at 0x5CEC; Zero queries for 0x1373/0x1374
[PASS] Corpus Direct Query Scan: Immediate reader queries: 0x1373 hits=0, 0x1374 hits=0
```

Literal stderr:

```
(empty)
```

Input hashes:

- `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `evidence/firmware-audit/20260919-inv-buffer-lifetime/AmdFabricAriPei.bin`: `c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78`
- `evidence/firmware-audit/20260920-clv-sync-stage1/extract/donor/modules/0017_AmdCcxVhAriDxe_pe32.bin`: `d9bc6337e3d039922016e95ed8be1fda5d7fb3e0250e43a6058d9c0d305997f0`

Output hashes:

- `evidence/firmware-audit/20260921-df-consumer/verify_df_consumer.py`: `64f06779ccdc10bf488eb66d5abb0792422e199812a31eb85349c9a4cf7e2ee3`
- `evidence/firmware-audit/20260921-df-consumer/df-consumer-result.json`: `7da3381cc8c203024f7bc7817053a47c6c9af39012455bba2c7ae1f0aa2c7f24`
- `evidence/firmware-audit/20260921-df-consumer/verifier.stdout`: `4590c7f49890ff2f62e7f273a6acce4090056629ca96ce30fdafabfb02a4fbca`
- `evidence/firmware-audit/20260921-df-consumer/verifier.stderr`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `evidence/firmware-audit/20260921-df-consumer/verifier.exit`: `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`

Findings:

1. `AmdFabricAriPei` serializes `0x1373` (`DfPstateOverride`) from `AmdSetup+0x703` (1 byte) and `0x1374` (`DfClockOvrd`) from `AmdSetup+0x704` (2 bytes, u16 LE).
2. Callback dispatch for this builder is registered via descriptor at `0x16a78` with CBS GUID `04126c85-5c4e-458f-abc1-29f1f7da365e` and Notify GUID `60db76a0-5d55-47bb-970f-34d8d0be369e`.
3. Bounded negative: zero direct reader queries exist for `0x1373` or `0x1374` across the entire 233-module UEFI firmware volume.
4. Downstream consumption of DF clock override tokens is proven to exit UEFI and reside in closed early boot firmware (ABL1 / APOB / SMU).
