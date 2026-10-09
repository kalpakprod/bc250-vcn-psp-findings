# CLV phase-2 PEI lifecycle ownership: AmdNbioSmuV10Pei

## Method pivot and result

After repeated local pointer/operand absence checks, this run changed method class to exact module-entry/lifecycle reconstruction. The selected module is `AmdNbioSmuV10Pei` (TE, entry RVA `0x240`). Its entry path contains two concrete PEI `InstallPpi`-slot calls through service slot `+0x18`, with static descriptor pointers and GUIDs recovered from exact bytes.

### Concrete InstallPpi path

```text
entry RVA 0x240
  ...
  0x265: push 0x9E9EBFC
  0x26A: push ESI
  0x26B: call DWORD PTR [EAX+0x18]
  ...
  0x289: push 0x9E9EC14
  0x28E: push ESI
  0x28F: call DWORD PTR [EAX+0x18]
```

The two installed descriptor pointers map to:

| Call    | Descriptor RVA |        Flags | GUID                                   | Interface pointer   |
| ------- | -------------: | -----------: | -------------------------------------- | ------------------- |
| `0x26B` |      `0x15C20` | `0x80000010` | `ea335e48-7275-4d2b-8276-55ba5531d7d7` | `imagebase+0x15BD8` |
| `0x28F` |      `0x15C38` | `0x80000010` | `8c61c925-224e-42d7-8978-812ae5612d23` | `imagebase+0x15C18` |

This is a real static PEI lifecycle edge, not a pointer-presence hypothesis.

### Comparison with CbsBasePei

`AmdNbioSmuV10Pei` also contains a static PPI descriptor at body offset `0x159F4` / RVA `0x15B84`, whose GUID pointer resolves to:

`04126c85-5c4e-458f-abc1-29f1f7da365e`

The GUID bytes are byte-identical to `CbsBasePei` body offset `0x13C10`. Existing `CbsBasePei` entry path independently uses the PEI `InstallPpi` service slot (`RVA 0x622: 8B 42 18 FF D0`) and its own static descriptor. Thus the shared CBS PPI identity is confirmed, but the bounded `AmdNbioSmuV10Pei` entrypoint's two direct InstallPpi calls install the two GUIDs above, not this shared CBS GUID. The CBS descriptor's owner/consumption path remains outside this bounded entrypoint join.

The callback descriptor previously mapped for this module (`RVA 0x15A70`, wrapper `0x5740`, event `0xFFFFFFFE`) is static data and is not directly pushed by either entrypoint InstallPpi call.

### LocatePpi inventory

Six module-local `LocatePpi`-slot-shaped calls (`+0x20`) were retained at RVAs `0x372`, `0x410`, `0x51C`, `0xB26`, `0xC22`, and `0x1583`. They are not promoted as consumers of the callback descriptor without a GUID/argument join.

## Reproduction and evidence

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-pei-lifecycle/pei_lifecycle_verify.py
```

Exit status: `0`; `20/20` checks passed.

Machine result: `evidence/firmware-audit/20260920-clv-sync-stage2-pei-lifecycle/pei-lifecycle-result.json`.
Runner: `evidence/firmware-audit/20260920-clv-sync-stage2-pei-lifecycle/pei_lifecycle_verify.py`.

Pinned ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
Module SHA-256: `905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80`.

Evidence class: observed bytes + static analysis. No firmware execution, runtime PPI database, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Remaining boundary

The exact PEI entrypoint now proves two PPI registrations and their GUID ownership. It does not prove that the callback descriptor is installed or invoked, nor that `$INV` token `0x1204` reaches a clock/divider actuator. The next narrow edge would be one of the six LocatePpi callers with a GUID/argument reconstruction; no broader token or pointer search is warranted.
