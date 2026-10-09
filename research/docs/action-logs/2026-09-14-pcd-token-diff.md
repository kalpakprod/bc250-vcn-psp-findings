# PCD-token diff in NBIO Gfx PEIM — 2026-09-14

## Database extraction intent and result

Root located the PCD signature in full raw images and checked the actual
PcdPeim getter before interpreting the layout. No chip write. Current header
source differs from image build-version6; use decoded field offsets.

BC250 database signature at SPI0xEDD774: version6, initialized length0x4F0,
uninitialized size0xC0, local-token table offset0x94. Token0x68 descriptor
at table+4*(token-1) =0x0100057A (UINT8 DATA, offset0x57A).
C0A database at SPI0xE6A404: version6, length0x4E8, uninitialized size0xD7,
local-token offset0x8C. Token0x55 descriptor=0x01000593 (offset0x593).
Both value offsets are outside initialized length but inside allocated
initialized+uninitialized extent. Values must be interpreted from zero-filled
uninitialized storage, NOT bytes following the database in SPI.
Initial Get8 value is consequently0 for both, conditional on this database
being selected and before SKU/runtime setter changes. Verify constructor
zero-fill and setter reachability before claiming values at the call site.

Getter0xF89 uses descriptor mask0xEFFFFF, distinguishes DATA/HII/VPD/STRING,
and handles DATA as database-relative storage. Thus no raw default delta
has been found for token55/68. The candidate difference currently looks like
namespace renumbering, not an enabled4700S versus disabledBC250 switch.

## G7 interface-type correction and next scope

Root identified the GUID against the retained MdePkg/Include/Ppi/Pcd.h.
It is PCD_PPI, not an unknown vendor interface. On IA32 offset+4 is Get8,
not GetBool (GetBool is+0x18). TEST AL is a nonzero test of an eight-bit
value. The following SUB CL,AL / AND7 uses that value numerically; describing
it as a Boolean is incorrect. Offset+0x48 is Set64, explaining the earlier
UMA token setter. Token55/68 are default-namespace dynamic PCD tokens.

0xE370 is passed to the separately decoded SMN write helper (8EC/8ED),
not written through PCD. Retract the prior 'PCD write to E370' description.
The real path is Get8(token) -> construct low register bits -> SMN write.

PcdPeim exists in both extractions (5304 bytes); GUID is present at file0x12C8.
Its method table will be traced to the embedded/external PCD database next.
No runtime values or VCN semantics inferred from token numbers alone.

## Getter implementation verification

In BC250 PcdPeim TE, method-table entry at file0x130C resolves to RVA0x346.
It pushes access size1, calls getter worker0xF89, dereferences a byte into AL
and returns. This independently corroborates Get8 identification from EDK2.
The PCD database implementation and signature definition are available in
retained MdeModulePkg/Universal/PCD/Pei/Service.c and
MdeModulePkg/Include/Guid/PcdDataBaseSignatureGuid.h, so no new external
parser dependency is needed for the next mapping step.

## Intent

Root compares the exact BC250 and 4700S Gfx PEI path around the only material
immediate difference after the shared NBIO copy sequence. No image or board
write. Preserve both module hashes and corrected TE deltas. A token number is
not changed without resolving the PCD database namespace.

## Observed code

- C0A entry uses PCD protocol GUID `{06E81C58-4AD7-44BC-8390-F10265F72480}`
  and calls its method at +4 with token `0x55`.
- BC250 uses the same GUID and method with token `0x68`.
- Both paths branch on the returned Boolean. If true they RMW the same
  platform configuration token/address `0xE370`, preserve high bits and OR
  `0x10`, then store it through the PCD interface.
- The surrounding read/write helper semantics are otherwise byte- and
  control-flow-equivalent after TE relocation: read helper -> RMW helper ->
  PCD write. The two token immediates are the only direct platform selector
  difference in this block.

## Interpretation

This is a concrete BIOS policy lead: one PCD Boolean gates programming of
`0xE370`. It may select an NBIO/UMA routing mode that affects the VCN bridge,
but token `0x55` in C0A and `0x68` in BC250 are version-specific namespaces;
numeric substitution is not yet justified. PCD database records, token names,
and the final `0xE370` consumer must be resolved from each image before a
candidate can be built. No VCN unlock or hardware behavior is claimed.

## Next

Locate the PCD database GUID/method table and token-value storage in both PEIM
FVs; map token 0x55/0x68 to names and defaults. Then trace `0xE370` through
BC250 NBIO/PEI consumers and check whether it controls the VCN-relevant
bridge/isolation setup. Only a same-namespace, one-variable patch should
proceed to artifact verification.
