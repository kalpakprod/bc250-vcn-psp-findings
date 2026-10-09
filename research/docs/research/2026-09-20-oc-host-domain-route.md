# Offline host clock-domain route

## Result

The default selector map for Queue 3 message 0x1D does not contain descriptors 0x0E..0x12 used by the separate DF P-state applier. Calling this command with a descriptor number is not equivalent to selecting that descriptor. This narrows this specific integration route, not all possible BIOS control paths. No candidate was produced.

## Reproduction and provenance

`python3 evidence/firmware-audit/20260920-host-domain-route/verify.py`
Inputs: exact 16 MiB clv SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8; Robin-5 262400 bytes SHA-256 cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37, equal to ROM slice at 0x8FEF00. Little-endian 32-bit mapping entries; address/file identity follows retained flat SMU evidence. Reused ghidra-decompiles.txt and ghidra-helpers-decompiles.txt under 20260919-oc-clock-provenance, checked decisive instruction bytes against pinned input. No new decompiler execution or complete control-flow proof claimed.

## Selector and actuator findings

- Handler pointer at 0x7554 is 0x2EA08. Entry bytes restore correct instruction alignment: `entry` at 0x2EA08, argument getter call at 0x2EA0D and `movi.n a12,0x14` at 0x2EA10. Historical decompile beginning at 0x2EA0C is misaligned at its start and cannot establish the prologue.
- High 16 bits select API index 1..20. Index zero and values above 20 are rejected. Descriptor is loaded from 0x13EEC + 4 + index*4. Low 16 bits become a float target, not a descriptor identifier.
- Static map: [13,0,1,2,3,4,5,6,7,10,24,19,20,21,22,23,11,8,9,12]. Descriptor 19 or 20 returns without writing the target. In particular API index 14 selects descriptor21, NOT descriptor14. No static entry selects descriptors14..18.
- Target store is at 0x1402C + index*12. Handler calls 0x2E788. That routine FIRST compares state words at 0x13EEC and 0x13EF0 and skips the entire loop when equal. A changed target or successful mailbox response alone is therefore insufficient evidence of an applied frequency. The visible setter does not update these words; scheduler/concurrency effects remain untraced.
- Within the active loop, target -1/zero/other take separate paths; it does NOT simply compare target against committed frequency as prior verifier prose suggested. Nonzero target is converted to a divider and compared with helper-reported divider state. Committed floats are then updated. Byte window 0x2392E confirms downstream call to register helper0x235C8 in the retained helper trace.

## Build consequence and next code path

Do not insert a BIOS request using a guessed DF descriptor as an API index, and do not rename a stored-only request to synchronized BIOS. Existing DF1400 artifact remains a stored-request experiment, not the requested finished profile. Signed SMU and stock ROM remain unchanged.
The next offline discriminating route is the separate DF applier0x1E448 and its row-pointer setup0x1E038: resolve all arguments to Queue5 init0x1C3B0 and whether a host-transferred structure reaches those pointers or lower-level divider helpers. Runtime rewrites of the selector map also remain unexhausted. This work does not require live telemetry; later hardware acceptance does.

Checks: selected byte/map audit PASS; existing 16 unit tests PASS. Independent review incomplete (requested worker refused and returned no technical evidence); hardware/voltage/boot UNRUN.
