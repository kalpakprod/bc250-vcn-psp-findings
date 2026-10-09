# CLV Fabric reader and PEI `InstallPeiMemory` final bounded review

## Result

Independent raw-instruction review confirms two distinct boundaries:

1. `AmdFabricAriPei` direct readers return `$INV` values through caller-provided stack slots. Handlers for tokens `0x10FF` and `0x1104` use those returned values in AGESA/IDS control paths, with no direct `WRMSR`, `in`, or `out` in the complete checked parent slices. This does not exclude transitive helper/MMIO effects and does not identify consumers `0x1331`, `0x1204`, or `0x123C`.
2. `AmdMemoryHobInfoPeim` uses an IA32 `EFI_PEI_SERVICES**` argument: `ESI=EAX`, `[ESI]` loads the service table, and `call [EAX+0x44]` is `InstallPeiMemory`. This is distinct from `AllocatePool` slot `+0x4C`; no slot confusion remains.

## Exact Fabric return-value evidence

- Pinned CLV SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact `AmdFabricAriPei` module SHA-256: `c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78`.
- Reader output store at `0x1E38`: `mov eax,[esi+0x3]; mov [edi],eax; mov eax,[esi+0x7]; mov [edi+4],eax`.
- Parent `0x1E8F`: pushes token `0x10FF` at `0x1EB0`, calls reader at `0x1EBD`, then reads `[esp+0x10]` and `[esp+0x14]` at `0x1EC7/0x1ECB`.
- Parent `0x1F6D`: pushes token `0x1104` at `0x1F8B`, calls reader at `0x1F94`, then reads `[esp+0x8]` and `[esp+0xC]` at `0x1F9E/0x1FA2`.
- IDS bytes map events `0x20000003 -> 0x1E8F` and `0x20000004 -> 0x1F6D`.
- Direct hardware-op count in checked slices (`WRMSR`, `in`, `out`): `0`.

The result is an AGESA/IDS configuration boundary, not a clock-register or hardware-synchronization proof. The worker's `19/19 PASS` result was rerun; independent reviewer checks are `32/32 PASS`.

## Exact PEI slot provenance

- Exact `AmdMemoryHobInfoPeim` module SHA-256: `aad3f828ccef4cf8878cad8c9ee1e47743748f652a1ef54af04de759983b4619`.
- At RVA `0x269`, `8B F0` assigns the PEIM entry argument to `ESI`.
- At RVA `0x26B`, `8B 06` loads `EAX=[ESI]`, proving `ESI` is a pointer-to-pointer and `EAX` is the PEI services table.
- At RVA `0x299`, `FF 50 44` calls service-table slot `+0x44`.
- Existing EDK II layout evidence lists `EFI_PEI_INSTALL_PEI_MEMORY` before `EFI_PEI_ALLOCATE_POOL`; source artifact: `evidence/firmware-audit/20260920-clv-sync-stage2-memclk-consumer/edk2-PiPeiCis-service-slots.txt`, SHA-256 `174ca8378bef20d86a51164b9fba55a68e0d187f429f59e5734c9be637196fbe`.

This independently reopens the prior APCB/ABL/APOB report's `InstallPeiMemory` edge and corrects any possible `+0x4C` confusion.

## Boundary and unrun items

- No firmware execution, PPI invocation, training, clock measurement, or hardware acceptance.
- No absence claim outside the two complete direct parent slices.
- Transitive AGESA/IDS helper MMIO effects remain unknown.
- FCLK `0x1331`, UCLK `0x1204`, MemoryPstate `0x123C`, and training actuator remain unresolved.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-fabric-reader-consumer/fabric_reader_consumer_verify.py
python3 evidence/firmware-audit/20260920-clv-fabric-reader-review/fabric_hob_review_verify.py
```

Owned evidence:

- `evidence/firmware-audit/20260920-clv-fabric-reader-review/fabric-hob-review-result.json` — SHA-256 `afa0188902717bb14aaa7278e4ad083174e2c69300dd9cb12f714b3525587aa0`
- `evidence/firmware-audit/20260920-clv-fabric-reader-review/fabric_hob_review_verify.py` — SHA-256 `bf5999a57ef1e110ad5f8097ad137995ef988e8b0c94565447ee86834d9f918d`
