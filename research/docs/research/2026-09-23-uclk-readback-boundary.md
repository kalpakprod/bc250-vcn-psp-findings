# Exact CLV UCLK getter check

Action: read-only headless Ghidra executed retained controller command on exact Robin5. Full loaded source comparison passed, command exit0.57 instruction byte records rechecked against source SHAcae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37.

- FUN23AB0 returns a cached byte at domain*28+F72C+7E.
- FUN23AC4 reads a group index from SRAM descriptor and returns a cached word atF568+group*72.
- Both complete getter bodies contain SRAM loads/arithmetic/return, not hardware-counter reads or PLL-status MMIO.
- FUN2360C and1CAD8 decode the already-known cached fixed-point/divider representation. Rechecking the math is not discovery of a new synchronization switch.

Decision: do not treat responses obtained through these getters as independent evidence of physicalUCLK or1:1:1. This closes the proposed getter-based readback route only. It does not prove that all physical readback methods are absent.

No modification, board access, telemetry, voltage, clock change or firmware candidate. Development source remains5.00CLV. Existing observedP3 board and savedP3 payloads are not used as CLV acceptance.

Current need remains a matched physical register/counter definition or a separately reviewed firmware-context observation. D17 forbids LinuxDF/SMN probes. Existing VCN EFI app was inspected and rejected for reuse as a clock reader because it performs unlock, gating and dataplane writes; none executed. No speculative EFI app or unsafe transplant created.

Evidence: evidence/firmware-audit/20260923-abl95fc-next/uclk-pll-readback-command.json and uclk-pll-readback-helpers.txt; diagnostic-preparation/readback-helper-verification.json. Same four diagnostic roles retained, supplemental record in VERIFICATION.txt.

This is a bounded negative, not a completed BIOS recipe. Further iterations must supply a new observation source, not rerun cached-getter/math or the excluded UclkDiv1 logging phases.
