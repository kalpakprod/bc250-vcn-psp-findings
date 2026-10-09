# Research map

```text
BC250 VCN discovery and driver behavior
  ├─ Recorded metadata (presence/harvest) ≠ physical health
  ├─ Driver inclusion / firmware load / real codec acceptance
  └─ Power, reset and isolation
       ├─ DF / NBIF / GASKET access policy
       │    └─ APCB, PSP carriers and ABL policy consumers
       ├─ SMU mailbox / firmware windows / clock domains
       │    └─ Reachable transport ≠ VCN power mechanism
       └─ PSP boot policy and authenticated firmware
            ├─ Signature / KDB / donor compatibility analysis
            ├─ Rejected software-only changes and negative results
            └─ SPI TOCTOU research
                 ├─ External pAMDora / Somnacin provenance
                 ├─ Host model / exact image pair / read-window plan
                 └─ Hardware acceptance still unresolved
                      MISO ownership + responder timing + actual read order
```

## 1. VCN and negative hardware results

Start with [STATUS](STATUS.md), then [the VCN roadmap](research/docs/research/2026-09-19-vcn-path-roadmap.md), [the dated failure diagnosis](research/docs/research/why-vcn-fails.md) and [the later status audit](research/docs/research/2026-09-27-vcn-smu-status-audit.md). The diagnosis is a preserved interpretation, not proof that all possible routes or physical defects are excluded.

## 2. Signed policy, donors and boot chain

[Signature-scheme research](research/docs/research/2026-09-19-psp-signature-scheme-solved.md), [GASKET script decode](research/docs/research/2026-09-19-gasket-script-decode.md), [Firmware-audit chronology](research/memory/firmware-audit.md) and [PSP research-lane history](research/.procoder/plans/psp-breach.md). The lane history contains old next-step proposals and confidence claims; it is not a current permission or settled result.

## 3. SMU, firmware windows and DXE

Use the [code index](code/INDEX.md) for candidate sources and transports, then the dated logs in the [research index](research/INDEX.md). Read the second-gate and Path C corrections linked in STATUS before treating clock/domain labels as codec-power semantics. Insertion controls and FULL/STUB outcomes are valuable negative evidence, not an unlocked codec.

## 4. TOCTOU and the current electrical gap

[pAMDora article notes](research/docs/research/2026-09-23-habr-pamdora-toctou.md), [39C3 talk notes](research/docs/research/2026-09-23-v12-pamdora-ccc-mining.md), [legacy inconsistencies](research/docs/research/2026-09-27-toctou-document-audit.md), [software implementation specification](research/specs/2026-10-07-psp-toctou-implementation.md) and the October 7/8 results linked in STATUS. Different BIOS bases must not share an assumed anchor payload or assumed transaction order.

## 5. Sources, reproduction and missing inputs

The [catalog](CATALOG.json) joins original paths to released copies. [SOURCE-LINKS](references/SOURCE-LINKS.md) records the collected external basis. [Dependencies](references/DEPENDENCIES.md) explains missing binaries/layout and historical links. The full [research](research/INDEX.md), [code](code/INDEX.md) and [evidence](evidence/INDEX.md) indexes expose all included paths rather than only the selected reading list above.
