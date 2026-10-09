## Final corrected result (2026-09-20T17:39:45+05:00 Asia/Almaty)

Corrected exact-target verifier exited 0 with stdout '{"status":"PASS","checks":64,"provider_disassembly_exit":0,"provider_type_pointer_arg":"SP+0x9C preserved/unreferenced directly","provider_explicit_byte_store":"through second stack arg SP+0xA0","fclk_type_byte_write":"not established by this provider path"}', stderr empty, and 64/64 PASS. Correct frame accounting is 13 pushed registers = 0x34 bytes at 0x49CC plus 0x6C locals; arg1 is SP+0xA0 and arg2 SP+0xA4. The provider 0x4BF0/0x4BFA byte write uses arg1, which is the FCLK type pointer forwarded by helper 0x4800. This supersedes the earlier uninitialized-local interpretation; provider runtime success/returned type remains unobserved.

Physical MCLK:UCLK:FCLK=1:1:1 remains unverified. It requires live independently measured domain clocks and a booted target/control baseline; no offline static result can substitute.
