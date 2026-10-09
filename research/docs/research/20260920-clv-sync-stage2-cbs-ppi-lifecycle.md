# CLV phase-2 CBS PPI registration and callback dispatch lifecycle

## Exact owner path

`CbsBasePei` entrypoint statically owns and registers the CBS interface:

```text
0x614: push 0x9ECDF60       ; EFI_PEI_PPI_DESCRIPTOR
0x622: [PEI services +0x18] ; InstallPpi
0x62D: push 0x9ECDF6C       ; notify descriptor
0x63B: [PEI services +0x24] ; NotifyPpi
```

Descriptor `RVA 0x13ED4` decodes as flags `0x80000010`, GUID `04126c85-5c4e-458f-abc1-29f1f7da365e`, and PPI interface `RVA 0x13EC0`. The interface's first method pointer is `CbsBasePei+0x250`.

Notify descriptor `RVA 0x13EE0` decodes as flags `0x80000040`, Notify GUID `60db76a0-5d55-47bb-970f-34d8d0be369e`, and callback `CbsBasePei+0x4D0`.

The exact callback dispatch window in method `0x250` is byte-checked:

```text
RVA 0x47D..0x499:
8d9538f7ffff528b450c508b4d08518b9518f7ffff8b4210ffd083c40c
```

It loads the descriptor callback field at `+0x10` and calls it indirectly. This establishes the static service implementation and dispatch mechanism; runtime PPI installation/invocation is not claimed.

## Counterpart registration records

`AmdNbioGfxARIPei` and `AmdNbioSmuV10Pei` each contain the exact sequence:

```text
CBS GUID 04126c85-5c4e-458f-abc1-29f1f7da365e
Notify GUID 60db76a0-5d55-47bb-970f-34d8d0be369e
CPU wildcard 0xFFFFFFFF
callback descriptor event 0xFFFFFFFE
```

Decoded counterpart descriptors:

| Module  | CBS GUID body offset | callback RVA | descriptor bytes                           |
| ------- | -------------------: | -----------: | ------------------------------------------ |
| Gfx PEI |            `0x14EC8` |     `0x4DF0` | `FF..FF / 0 / imagebase+0x4DF0 / FFFFFFFE` |
| SMU PEI |            `0x158C0` |     `0x5740` | `FF..FF / 0 / imagebase+0x5740 / FFFFFFFE` |

Thus the static ownership/registration chain is:

```text
CbsBasePei InstallPpi(CBS GUID)
  -> Cbs PPI method 0x250 + NotifyPpi(AmdSetup GUID)
  -> wildcard/event descriptor callback field +0x10
  -> Gfx/SMU wrapper 0x4DF0/0x5740
  -> record builder / $INV token stream
```

This is the first concrete lifecycle handoff beyond serializer and literal-reader scans. It still does not prove runtime callback invocation or a token `0x1332` requester/clock actuator.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs_ppi_lifecycle_verify.py
```

Exit status: `0`; `26/26` checks passed.

Machine result: `evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs-ppi-lifecycle-result.json`.
Runner: `evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs_ppi_lifecycle_verify.py`.

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Boundary

Static registration and callback dispatch ownership are now established. Remaining unknowns are runtime invocation order, actual token requester through this callback path, and any downstream clock/training consumer.
