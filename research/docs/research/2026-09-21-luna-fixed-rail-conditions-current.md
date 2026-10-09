# CLV ISL69247 / ISL95712 — PEI runtime-applicability gates

Status update: the later [PcdPeim DEPEX review](../../../references/DEPENDENCIES.md#unavailable-local-inputs) identifies the second GUID as standard `gEfiPeiPcdPpiGuid` and confirms that `PcdPeim` also requires it before dispatch. The **identity** is resolved; the earlier/bootstrap provider and live PPI database remain unresolved. Historical “identity unknown” wording below is superseded.

Current: the pinned CLV PEIMs are present with identical two-PPI depex; their decoded entry paths contain no board/SKU or VR-ID branch, but static evidence does not show the required second PPI present at runtime / no voltage recommendation.

## Conclusion

The new bounded applicability condition is the exact PEI dependency expression: both `ISL69247` and `ISL95712` require **both** PPI GUIDs `F894643D-C449-42D1-8EA8-85BDD8C65BDE` and `01F34D25-4DE2-23AD-3FF3-36353FF323F1` (`PUSH`, `PUSH`, `AND`, `END`). The first is the standard PEI MemoryDiscovered PPI; the identity and producer of the second GUID were not resolved in the local evidence. Consequently, the modules are dispatch-eligible only after both PPIs are installed, but their actual dispatch on a live board is not established.

Inside each decoded module entry path there is no board/SKU-selection or VR-manufacturer/device-ID branch before its controller mailbox writes. The only entry-path conditions are the PPI-locate result and Setup enable/loadline fields (listed below). Both sides of each fixed-voltage enable branch still stage controller writes: an enabled path stages the configured field; a disabled path stages the module's default/control value. Thus the enable flag is not a “no-write” guard. This is static applicability evidence, not proof that PEI executed or that any command reached a physical VR.

## Pinned input and direct checks

- CLV donor: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Fresh direct check and byte-identical replay: `evidence/firmware-audit/20260921-luna-fixed-rail-conditions/applicability-check.stdout` and `applicability-check-replay.stdout` both exit `0`, have empty stderr, and share SHA-256 `7a4b42a127f0badeae0994aed103b52d188b0c10281f7821bc0707fe5e0019e9`. Reproducible script `applicability_check.py` has SHA-256 `7380ffb4980ed2b3070e9f7f568fb9146f2c03f169d5f63aa7e183a937b62623`; exact replay command and all capture hashes are in `evidence/firmware-audit/20260921-luna-fixed-rail-conditions/VERIFICATION.txt`.
- The direct FFS read checked the exact file GUID/type/state/size, first dependency section, the `AND/END` expression, and TE bytes against the pre-existing extracted images. Both ROM-derived depex bodies match the preserved UEFITool extraction and parsed expression; both TE sections match the exact prior extracted TE copies.

| Module                                            | FFS file / TE data      | FFS type / state | Direct depex body SHA-256                                          | TE SHA-256                                                         |
| ------------------------------------------------- | ----------------------- | ---------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `ISL69247` `6E6D2018-28D0-4AD3-BEB3-B48E4981707D` | `0xED2C30` / `0xED2C74` | `0x06` / `0xF8`  | `c6395f7b9e6fb2e28298ee78381450f996a4f558309cd786b6ad30e171725788` | `3e1f753a627922d16e5a638a527e39f4dd26242144edae25b0ac849db6421e34` |
| `ISL95712` `02544BE0-2CB9-4B75-8111-CD8CDC07B837` | `0xED3D48` / `0xED3D8C` | `0x06` / `0xF8`  | `c6395f7b9e6fb2e28298ee78381450f996a4f558309cd786b6ad30e171725788` | `c0cc17d2d54f9cde65f471d2971596837b024d4764a28b33286032cfa95d43a9` |

## Entry-path conditions (existing objdump 2.47 CLV decode)

`ISL69247` (`entry` RVA `0x240`; body through `ret` at `0x43B`):

- `0x2BF: jl 0x2E0` follows the PPI-lookup-shaped call through `[ecx+0x20]` at `0x2B7` with the Read-Only Variable2 PPI GUID (the exact PEI-services slot identity remains inferred). A negative call result skips the Setup `GetVariable` call at `0x2DB`, but rejoins at `0x2E0`, where mailbox initialization and subsequent writes proceed.
- The other conditional branches in this entry body are `0x312` (VCORE Setup enable), `0x386` (VCORE loadline enum equals 2), `0x3B0` (GFX Setup enable), and `0x421` (GFX loadline enum equals 2). They select data/flags; they do not gate entry or all writes off.

`ISL95712` (`entry` RVA `0x240`; body through `ret` at `0x312`):

- `0x27C: jl 0x29D` follows the PPI-lookup-shaped call through `[ecx+0x20]` at `0x274` with the same Read-Only Variable2 PPI GUID (slot identity inferred). A negative call result skips `GetVariable` at `0x298`, but rejoins at `0x29D` before mailbox initialization and later writes.
- The only other conditional branch in this entry body is `0x2BA: je 0x2DF`, the MEMIO Setup enable test; both paths write the default or configured value to `0xDF` and later stage `0xDE`.

Defaults are assigned before the Setup-variable call (ISL69247: VCORE/GFX enable `0`, mV `900`, loadline `2`; ISL95712: MEMIO enable `0`, enum `0x1E`). The call result from `GetVariable` is not checked by an intervening conditional branch in these entry windows. No platform ID, board ID, controller manufacturer ID, or controller device ID check is visible in either decoded entry path. The helper's mailbox/status polling is not a VR identity check.

## Decision boundary

- **Static-analysis, confirmed:** both FFS files are present and have the same AND depex; in the decoded entry paths, the only gates are the depex PPI availability, Setup-read availability, and per-field enable/loadline branches; no board/SKU or VR-ID conditional is present in those paths; enable-disabled still stages writes.
- **Unresolved exact input:** whether and when `01F34D25-4DE2-23AD-3FF3-36353FF323F1` is installed in the selected live platform's PEI and therefore allows either module's depex to dispatch. Local source/report inventory did not map this GUID to a producer. Until that link or a runtime PEI dispatch trace exists, actual execution is **unproven**.
- **Not established:** live dispatch, which EC/mailbox is physically reached, VR identity, physical rail mapping, PMBus-style semantics, any applied voltage, or safety. No ROM/NVRAM/register/hardware action occurred; no voltage is recommended.

The cheapest decisive static continuation is to identify the producer/install call for the second depex PPI in the exact PEI core/FV. The decisive runtime evidence remains a PEI dispatch trace on the target image/board. This report did not inspect Linux rail maps or public physical-rail sources.

## Evidence paths

- Machine record, reproducible checker, literal stdout/stderr/exit, verification record and manifest: `evidence/firmware-audit/20260921-luna-fixed-rail-conditions/`.
- Existing disassembly: `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/ISL69247.disasm.txt` (SHA-256 `cb15e09a6b7c35bb6dff13c40f61b3b076c999f3ce60c62b99476bbb1db34aab`) and `ISL95712.disasm.txt` (SHA-256 `10d0e7628bb36f5e2570e6414ad928f027b2d48f5f6c37b94fc9565908c3626e`).
- Existing UEFITool report: `evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.report.txt` (SHA-256 `41e44c9dcc977bc7bb027b698b91f00c4592f95c026a2cfdfa0e153b61dc3c89`).
- Action log: `docs/action-logs/2026-09-21-luna-fixed-rail-conditions.md`.
