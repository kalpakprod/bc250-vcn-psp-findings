# SVC7C input-surface audit — 2026-09-15

## Authoritative SVC63 correction

Use common switch base0x45E4: entry0x462C=0x3CC -> target0x49B0,
NOT0x49F8 (entry-relative arithmetic is wrong). The branch calls0x537C,
which clears translation entries and invalidates TLB (MCR c8,c3,0)+DSB.
Thus map removal, not signature verification, is supported. Supersedes
the later incorrect0x49F8/0x19A0 paragraph. Authentication in the t28 loader
must be assessed through0x9C9C/0x10730 and dependencies, not svc63.

## Intent

Root audits all corrected `7C DF` Thumb sites in BC250 t28 after the previous
encoding correction. Goal: identify an address/value pair source that is both
runtime-controlled and capable of reaching VCN. No hardware or firmware writes.
Use the exact readback-derived t28 body and preserve only sanitized metadata.

## Findings

- `0xA660` is the only confirmed generic pair-loop consumer: address dword
  shifted left two, value dword, SVC7C width4. Its only direct caller found
  (`0xDBCA`) is selected for type `0x16` and passes fixed pointer `0xE35840`.
- The caller's source object enters `0x16D88`; that routine allocates scratch,
  performs object parsing and verification work, and calls SVC0x63. The nearby
  `0x13544` is a stub return0. No unsigned x86/NVRAM/APCB source reaches
  `0xE35840` in the current static proof.
- Other SVC7C sites are table-driven indexed register setup (e.g. `0xF81A`,
  `0xF8D2`, `0xFCF8`, `0x10004`) but their base tables and callers remain
  signed-PSP/runtime structures. No site was proven to hold the exact VCN
  frame base `0x02403000` or bank-12 values.
- The SVC7C mapper rejects address holes but `0x5A88` ignores the NULL return,
  creating a confirmed zero-address write. The exploit requires a reachable
  attacker-controlled denied address; no such input has been found.

## Decision

### Service boundary caution

The dispatch table must be resolved with the correct PC-relative base. Earlier
scratch arithmetic added each entry's own address to its value, which is not
the semantics of this `ADD PC,r3` switch. The correct base is the instruction's
PC (`0x45E4`), yielding SVC7C target `0x4D28`. No new claim about SVC0x63
verification or deallocation is made until its handler is decoded from the
same dispatch base. Empty full-file linear Thumb passes are invalid coverage
because the blob begins in ARM vector mode. They do not prove caller absence.

No BIOS-resident VCN unlock candidate is justified by the current SVC surfaces.
The next high-value static check is the `0x16D88` object provenance and
verification boundary. A candidate must show a mutable source and a controlled
VCN target before any image construction or flash approval.

## G7 correction: SVC0x63 semantics

The t02 SVC table maps `svc #0x63` to a mid-function path at 0x49F8, which checks a per-type table byte and calls 0x19A0 for resource/type teardown. This is not established as cryptographic verification. The earlier statement that t28 `0x16D88` final `svc0x63` proves signature checking is retracted. Signature decisions remain tied to ABL `svc#6` wrappers and the closed supervisor until directly decoded.
