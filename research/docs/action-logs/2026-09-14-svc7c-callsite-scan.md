# SVC7C call-site scan — 2026-09-14

## Intent and result

Root performs corrected Thumb call-site trace on the exact fresh BC250 t28
slice SPI0x984F00/size0x1A770. No hardware operation. Preserve a focused
listing; do not interpret an empty linear disassembly from the wrapper as
absence of callers. The generated t28-callers.txt was empty for that reason
and is not valid coverage evidence.

Function0xA660 takes a pointer in r0 and byte count in r1. For each8-byte
entry it loads an address word, shifts it left2, loads a value, and calls
svc7C with width4. It increments its cursor by8 and returns0 independently
of the service result. Size alignment/bounds are not checked locally.
This is a consumer contract, not proof of an untrusted caller vulnerability.

A direct BL at0xDBCA reaches0xA660 from the loader routine beginning0xD9DC.
That path is selected only when r4==0x16, after calls0x16D88 and0x13544
both return0. Pointer comes from literal0xDC78=0x00E35840; count comes
from stack+0x34. Thus the pointer is fixed in this caller, not freely supplied
by host input. Loader input origin and validation in those helpers remain open.
Next: determine what object type0x16 denotes and whether validation authenticates
its payload before the register-pair consumer. Signedness cannot be inferred
from helper names or successful return alone.

## Extended caller audit

The t28 dispatcher contains a second direct caller at `0xDBCA`, in loader
function `0xD9DC`. The path is selected when entry type `0x16` is observed
after validators `0x16D88` and `0x13544` return success. It passes fixed
pointer literal `0x00E35840` and a count from stack state into `0xA660`.
The pair consumer itself shifts each table address by two bits before calling
SVC7C; it does not bounds-check the pair count. This is a real data-driven
write surface, but the pointer and selection are still firmware-controlled.
No input derived from an unsigned BC250 BIOS region has been demonstrated.

## Follow-up: no direct unlocked pair source

The fixed pointer literal `0x00E35840` is outside the t28 body slice and is
therefore a runtime/global-memory address, not a static table embedded in the
extracted component. The loader's preceding `0x16D88` path receives an object
pointer from caller state, but its output table is built in scratch/global
memory after verification calls. No direct relation from unsigned x86 FV,
APCB or NVRAM bytes to this pointer was found in the bounded decode. The
unchecked pair count remains an implementation defect without a demonstrated
attacker-controlled source. This closes the current static route for an
immediate BIOS patch; it does not prove the closed verifier has no other bug.

## Validation-chain refinement

Fresh t28 decode shows `0x16D88` is not a simple bounds check: it allocates a
large scratch buffer, validates a loaded object through `0xA0E8/0xB534`,
dispatches a verification path and finally calls SVC `0x63` on the result.
The neighboring `0x13544` used in the type-0x16 selection is a literal stub
returning zero in this image, so it contributes no independent validation.
This corrects the earlier wording that both `0x16D88` and `0x13544` were
confirmed validators. The object-type and signature decision path still goes
through `0x16D88` and remains unresolved at the closed service boundary.

The pair pointer used by `0xA660` remains a fixed literal in t28. Consequently
the unchecked count is a robustness flaw but is not, by itself, a route to
inject VCN pairs from the mutable BIOS NVRAM/APCB region.
