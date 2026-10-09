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

## 1. VCN and the hardware experiments

Read [STATUS](STATUS.md), then [the VCN roadmap](research/docs/research/2026-09-19-vcn-path-roadmap.md), [the dated failure diagnosis](research/docs/research/why-vcn-fails.md) and [the later status audit](research/docs/research/2026-09-27-vcn-smu-status-audit.md). The diagnosis records an interpretation. It does not rule out every possible route or physical defect.

## 2. Signed policy and donor firmware

The [signature-scheme research](research/docs/research/2026-09-19-psp-signature-scheme-solved.md) and [GASKET script decode](research/docs/research/2026-09-19-gasket-script-decode.md) describe the policy paths. The [firmware-audit chronology](research/memory/firmware-audit.md) and [PSP research-lane history](research/.procoder/plans/psp-breach.md) show how the work developed. Old next-step proposals and confidence claims in that history are not current permissions or settled results.

## 3. SMU, firmware windows and DXE

Find candidate sources and transports in the [code index](code/INDEX.md), then follow the dated logs in the [research index](research/INDEX.md). The second-gate and Path C corrections linked in STATUS explain why some clock/domain labels cannot be read as codec-power control. Insertion controls and FULL/STUB outcomes provide negative evidence, not a working codec.

## 4. TOCTOU and the electrical questions

Start with the [pAMDora article notes](research/docs/research/2026-09-23-habr-pamdora-toctou.md) and [39C3 talk notes](research/docs/research/2026-09-23-v12-pamdora-ccc-mining.md). Follow them with the [legacy inconsistencies](research/docs/research/2026-09-27-toctou-document-audit.md), [software implementation specification](research/specs/2026-10-07-psp-toctou-implementation.md) and October 7/8 results linked in STATUS. An anchor payload or transaction order assumed for one BIOS base cannot be carried over to another without evidence.

## 5. Finding the inputs and sources

[CATALOG.json](CATALOG.json) maps original paths to public copies. [SOURCE-LINKS](references/SOURCE-LINKS.md) records the external sources collected during the work, and [Dependencies](references/DEPENDENCIES.md) explains the missing binaries, layout requirements and historical links. The full [research](research/INDEX.md), [code](code/INDEX.md) and [evidence](evidence/INDEX.md) indexes list all included paths, beyond this reading order.
