# Fallback descriptor `0x006F47C0`: no proven SMN/clock map or native `+0x703/+0x704` reach

Supplemental exact-byte review of the already joined fallback chain. This report does not repeat the descriptor-table join; it tests only (1) known map relation and (2) native-field reach.

Current: exact CLV ABL1 fallback descriptor / known map comparison / no clock-target promotion / next = keep native `+0x703/+0x704` separate until a byte-backed bridge to the ABL1 descriptor path exists.

## Result

The fallback chain is byte-backed:

```text
table[0x61E] = 0x006CA7C0
nested index = 0x6CA
table[0x6CA] = 0x006F47C0
raw low12 = 0x7C0
raw bits0..5 = 0
raw bits6..11 = 31
raw kind bits27..29 = 0
raw bit30 = 0
```

No physical SMN/clock relation follows. The existing exact map report contains static aperture bases `0x5027C` and `0x5227C`; both have low six bits `0x3C`, while the fallback descriptor has low six bits `0`. For the exact kind-1 construction, the fallback yields:

```text
context+0x49 = 0 -> R4 = 0x507C0
context+0x49 = 1 -> R4 = 0x527C0
```

Neither equals `0x5027C` or `0x5227C`; the low-six mismatch is invariant for all byte values in that kind-1 formula. Other kind/high-field merges remain unresolved and are not promoted to a map. Thus there is **no known exact native SMN/clock map relation** for raw descriptor `0x006F47C0` in the current evidence.

The native candidate fields do not have a proven route into this fallback descriptor path:

- Native `AmdSetup+0x703/+0x704` serialize as `$INV 0x1373/0x1374`.
- ABL1 contains a local `MOVW R0,#0x703` at `0xA57E`, followed by local helper `0x4830`; this is not byte-backed as native `$INV 0x1373` and the bounded helper has no direct `BL 0x10958` edge.
- ABL1 has no decoded `MOVW #0x704`, `#0x1373`, or `#0x1374` immediate. The apparent listing `#704` at `0x83F4` is a decimal displacement `0x2C0`, not native `AmdSetup+0x704`.
- The descriptor callback path enters with token/index `0x61E` at `0x107E8` and then dynamically loads the `+0x44` table. No direct edge from the `+0x703` ABL1 helper site to that dispatcher is observed.

**Decision:** do not treat `0x006F47C0` as a clock register descriptor and do not claim that changing native `+0x703/+0x704` reaches this ABL1 fallback path. The fields remain separate unresolved routes.

## Direct verification

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-fallback-map/verify_fallback_map_and_native_reach.py
```

Observed: exit `0`; `57/57` assertions passed; stderr empty. Machine result status: `BLOCKED_NO_MAP_OR_NATIVE_REACH`.

Exact inputs:

- ABL1 payload: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Thumb listing: `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Final descriptor join result: SHA-256 `31e2c2952d6d4074ddaf52fea5bed68f7656ec6a0867e225e06aab7b432f6a5c`.
- Existing conditional map result: SHA-256 `f9fccfdcef1258fa5e8eb1758f02d9bb6eb8a0e04822a4751e1d8a7b9a3ad5eb`.
- Exact map report: `docs/research/2026-09-20-oc-df-init-route.md`, SHA-256 `3122a0dce28bc61942a22d567acdc29e318a714097b48877eb0391094a7d0e43`.

Evidence class: `observed-bytes` + `static-analysis`. No ROM/candidate, firmware, settings, hardware, shared plan, MCP/global configuration, installation, or commit changed.

## Boundary

The fallback descriptor's dynamic `context+0x40` high-bit merge, active HEAP-versus-fallback selection, SVC#4 translation, and physical target remain unresolved. A future map claim requires either a byte-backed bridge from native `$INV 0x1373/0x1374` to the ABL1 token `0x61E` path or an authorized runtime/PSP handler trace. No 1:1:1 or clock-enable conclusion follows.
