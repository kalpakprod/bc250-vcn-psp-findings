# DF Override Tokens 0x1373/0x1374 Consumer and Boundary Verification

Date: 2026-09-21
Author: Luna / subagent static verification
Evidence artifact: `evidence/firmware-audit/20260921-df-consumer/df-consumer-result.json`

## Summary

This investigation resolved the consumer and dispatch boundary for Data Fabric (DF) clock override tokens `0x1373` (`DfPstateOverride`) and `0x1374` (`DfClockOvrd`) in the pinned CLV 5.00 donor image (`BC250_5.00_clv.bin`, SHA-256 `ea578104...`).

Key findings:

1. **Producer / Serialization Edge**:
   - `AmdFabricAriPei` serializes `0x1373` at file offset `0x11ace` (RVA `0x11C66`) as a 1-byte field sourced from `AmdSetup+0x703`.
   - `AmdFabricAriPei` serializes `0x1374` at file offset `0x11b00` (RVA `0x11C98`) as a 2-byte (u16 LE) field sourced from `AmdSetup+0x704`.
2. **Registration and Dispatch**:
   - Serialization is triggered via the CBS counterpart registration descriptor at offset `0x16a78` in `AmdFabricAriPei`.
   - Descriptor fields match standard EDK II CBS registration: CBS GUID `04126c85-5c4e-458f-abc1-29f1f7da365e`, Notify GUID `60db76a0-5d55-47bb-970f-34d8d0be369e`, CPU wildcard `0xFFFFFFFF`, Event `0xFFFFFFFE`, and Callback VA `0x09E227A0` (file offset `0x6a88`).
3. **Absence of Direct UEFI Readers (Bounded Negative)**:
   - Inlined reader in `AmdFabricAriPei` (`0x1D00..0x1DF8`) requests only tokens `0x10FF` (at `0x1D18`) and `0x1104` (at `0x1DF3`).
   - Inlined reader in `AmdCcxVhAriDxe` (`0x5AC4`) requests only tokens `0x1000` (at `0x5CA0`) and `0x1001` (at `0x5CEC`).
   - A census scan of all 233 extracted CLV UEFI PEI/DXE modules shows **zero** direct query instructions for tokens `0x1373` or `0x1374`.
4. **Conclusion**:
   Neither token `0x1373` nor `0x1374` is consumed or acted upon directly within the UEFI firmware volume. Both tokens exist purely as CBS `$INV` serialized structures destined for the ABL1 / APOB / SMU firmware boundary.

## Disassembly Verification

### 1. Token 0x1373 (`DfPstateOverride`) Serialization in `AmdFabricAriPei`

```assembly
0x11ace: ba 73 13 00 00       mov    $0x1373,%edx      ; Token ID 0x1373
0x11ad3: 8b 45 f8             mov    -0x8(%ebp),%eax   ; Current buffer cursor
0x11ad6: 66 89 10             mov    %dx,(%eax)        ; Store token ID
0x11ad9: 8b 4d f8             mov    -0x8(%ebp),%ecx
0x11adc: 8a 51 02             mov    0x2(%ecx),%dl
0x11adf: 80 e2 fc             and    $0xfc,%dl         ; Clear type bits (type 0 = u8)
0x11ae2: 8b 45 f8             mov    -0x8(%ebp),%eax
0x11ae5: 88 50 02             mov    %dl,0x2(%eax)
0x11ae8: 8b 4d f8             mov    -0x8(%ebp),%ecx
0x11aeb: 8b 55 fc             mov    -0x4(%ebp),%edx   ; AmdSetup pointer
0x11aee: 8a 82 03 07 00 00    mov    0x703(%edx),%al   ; Load Setup+0x703
0x11af4: 88 41 03             mov    %al,0x3(%ecx)     ; Store value at cursor+3
0x11af7: 8b 4d f8             mov    -0x8(%ebp),%ecx
0x11afa: 83 c1 04             add    $0x4,%ecx         ; Cursor += 4 bytes
0x11afd: 89 4d f8             mov    %ecx,-0x8(%ebp)
```

### 2. Token 0x1374 (`DfClockOvrd`) Serialization in `AmdFabricAriPei`

```assembly
0x11b00: ba 74 13 00 00       mov    $0x1374,%edx      ; Token ID 0x1374
0x11b05: 8b 45 f8             mov    -0x8(%ebp),%eax   ; Current buffer cursor
0x11b08: 66 89 10             mov    %dx,(%eax)        ; Store token ID
0x11b0b: 8b 4d f8             mov    -0x8(%ebp),%ecx
0x11b0e: 8a 51 02             mov    0x2(%ecx),%dl
0x11b11: 80 e2 fc             and    $0xfc,%dl
0x11b14: 80 ca 01             or     $0x1,%dl          ; Set type bits to 1 (type 1 = u16)
0x11b17: 8b 45 f8             mov    -0x8(%ebp),%eax
0x11b1a: 88 50 02             mov    %dl,0x2(%eax)
0x11b1d: 8b 4d f8             mov    -0x8(%ebp),%ecx
0x11b20: 8b 55 fc             mov    -0x4(%ebp),%edx   ; AmdSetup pointer
0x11b23: 66 8b 82 04 07 00 00 mov    0x704(%edx),%ax   ; Load Setup+0x704 (u16)
0x11b2a: 66 89 41 03          mov    %ax,0x3(%ecx)     ; Store value at cursor+3
0x11b2e: 8b 4d f8             mov    -0x8(%ebp),%ecx
0x11b31: 83 c1 05             add    $0x5,%ecx         ; Cursor += 5 bytes
0x11b34: 89 4d f8             mov    %ecx,-0x8(%ebp)
```

## Reproduction & Verification Evidence

Run:

```bash
python3 -B evidence/firmware-audit/20260921-df-consumer/verify_df_consumer.py
```

Output:

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
