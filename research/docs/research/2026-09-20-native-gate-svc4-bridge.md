# SVC#4 follow-up: the single pre-build semantic gate is field-to-mapped-actuator identity

> Audit 2026-09-27: the later 2026-09-20-native-gate-fallback-map.md recovers a conditional fallback descriptor. This narrows the old no-descriptor statement but does not prove active context identity, native-field reach or close G-ACT. Read the continuation before repeating the old next step.

Supplement to `docs/research/2026-09-20-native-gate-candidate-readiness.md`: this follow-up uses the direct mapped-SMN finding to narrow the readiness decision to one conjunctive pre-build semantic gate, `G-ACT`; it does not change prior result artifacts or build a candidate.

Current: exact CLV / candidate held / G-ACT is the remaining minimum offline gate before any ROM candidate / next = trace the field record through the active ABL1 context-table producer to its encoded SMN target.

## Implementation decision

**Do not build a ROM candidate until one gate, `G-ACT`, closes: a byte-backed join from the selected native `AmdSetup` field through its `$INV` record and actual active consumer/callback to the runtime descriptor that supplies the encoded SMN address and target field effect.** This is the first necessary semantic gate; it is not a matrix/status restatement. The new SVC#4 evidence changes the risk interpretation: the ABL1 callback path can perform mapped SMN/MMIO access, so an unbound descriptor is an unknown register-write target, not merely a bookkeeping field.

The gate is **partly statically closable offline** if all table/descriptor producers and inputs can be reconstructed from the exact firmware bytes. It is **not closed by the currently available CLV BIOS image**: the callback dereferences a runtime table from `[context+0x44]`, the active `+0x660` callback object is not joined to its initializer object, and no exact target descriptor value was recovered. The on-die SVC#4 handler/translation table is absent from the BIOS image, so the physical mapped window cannot be resolved from this corpus alone. Do not interpret “offline-possible in principle” as a present pass.

### Gate acceptance

For one chosen native field (start with `AmdSetup+0x330`, record `0x1204`), the byte-backed chain must demonstrate:

1. field byte loads into the correct record/token;
2. actual reader/registration/requester consumes that token/value;
3. the active ABL1 callback is the callback reached for that consumer;
4. the active context's `+0x44` descriptor entry and any nested descriptor are recovered or deterministically derived;
5. the descriptor encodes the specific SMN address/field, and the operation/effect is known well enough to predict the candidate's changed behavior.

This is one end-to-end semantic gate, `field -> active consumer -> runtime descriptor -> encoded SMN target`, rather than separate readiness labels for each link. After it closes, frequency units, ratio/crossing, training, migration, and hardware acceptance are still required for any claim beyond an explicitly bounded stored-request or actuator experiment.

## Direct exact-byte discriminator

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-svc4-bridge/verify_field_to_smn_bridge.py`.

Observed: exit `0`, `42/42` checks passed, stderr empty; machine result status `BLOCKED` with decision `HOLD_ROM_CANDIDATE_UNTIL_FIELD_TO_MAPPED_ACTUATOR_JOIN`. This is a successful direct check of the _blocker_, not a candidate acceptance.

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1 payload: 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact ABL1 Thumb listing: SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- `CbsBasePei` serializer bytes: `Setup+0x330` load at RVA `0x9CE4`; record header `0x1204` at `0x9CC4`; value byte store at `0x9CEA`.
- `AmdFabricAriPei` direct generic-reader requesters in the exact instruction census are exactly two: token `0x10FF` at RVA `0x1EB0` followed by call `0x1EBD`, and token `0x1104` at `0x1F8B` followed by call `0x1F94`. Neither direct call requests `0x1204`. This does not exclude computed/indirect/HOB/DMA/later consumers.
- ABL1 caller at `0x107E8` loads callback token/index `0x61E`, then calls dispatcher at `0x10820`; dispatcher `0x1095A` loads callback pointer from its current object `+0x660` and branches indirectly at `0x10968`.
- Candidate callback body `0x9AD8` extracts `token & 0xFFF` (`0x9AE8`), loads a pointer from runtime context `+0x44` (`0x9B18`), indexes its descriptor table (`0x9B1C`), extracts a nested index from that descriptor (`0x9B2C`), and loads the nested descriptor dynamically (`0x9B54`). The target descriptor value is not an immediate at these access sites.
- The callback literal at `0xB168` is `0x00060BD9`, conditionally mapping under base `0x57100` to entry `0x9AD8`; installer writes it to the initializer object's `+0x660` at `0xB0C4`. The consumer dispatcher later loads `[current R0+0x660]`; identity between this current object and the initializer object remains unproved.
- Mapped helper calls are present (`0x9C2A -> 0x6DA4` read; high-index path `0x9D96 -> 0x6E70` write). Existing exact SVC#4 verification confirms these are mapped-base accesses. That proves capability at the caller-contract level, not the address value or physical window.

### What this proves and does not prove

**Observed bytes/static analysis:** the native field is serialized into `0x1204`; the ABL1 callback uses a dynamic token-indexed runtime descriptor table and mapped SVC#4 helpers; exact direct Fabric reader callers request `0x10FF`/`0x1104`; the callback's caller token is `0x61E`; a potential callback function pointer is installed into an initializer object's `+0x660` slot.

**Not proven:** any path from `$INV 0x1204` to ABL1 token `0x61E`; whether this candidate callback is actively installed in the current dispatch object; the runtime table pointer or descriptor values; the encoded SMN target; a physical register, clock divider/PLL, units, clock effect, or board behavior.

## Can the gate be closed offline?

- **Potentially, for the encoded target:** yes, if static byte analysis can trace the active callback registration and exact producer/populator of the `+0x44` table, and the descriptor inputs are constants or deterministically derived from data present in the image. The required ABL1 and PEI bodies are local, so the next method should be targeted producer/dataflow recovery, not a new generic scan.
- **Not by the present evidence:** the callback slot ownership and table contents are dynamic and unresolved, while existing native consumer evidence reaches a generic reader whose direct requests are only `0x10FF/0x1104`.
- **No, for the physical map/window from the current BIOS corpus alone:** the on-die SVC#4 service handler/translation table is missing. A future exact descriptor can reveal the logical encoded SMN address without decoding the mapping service, but physical window identity or runtime hardware effect needs additional authorized PSP-ROM evidence or a bounded execution/readback trace.

Thus offline work can close the necessary _semantic target_ portion only if producer dataflow resolves the descriptor. If it cannot, stop before ROM candidate generation; do not substitute a guessed clock value or the `0x83C` Disabled option.

## Evidence and rollback

- Machine result: `evidence/firmware-audit/20260920-native-gate-svc4-bridge/field-to-smn-bridge-result.json`
- Verifier/stdout/stderr/exit and manifest: `evidence/firmware-audit/20260920-native-gate-svc4-bridge/`
- Action log: `docs/action-logs/2026-09-20-native-gate-svc4-bridge.md`
- No ROM, candidate, settings, firmware, hardware, installation, global configuration, MCP, or commit changed. Rollback is deletion of only this owned report/log/evidence directory.
- Evidence class: `observed-bytes` + `static-analysis`; no runtime or hardware claims.
