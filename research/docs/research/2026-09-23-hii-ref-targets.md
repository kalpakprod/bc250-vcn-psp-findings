# Experimental menu: binary HII reference audit

The verifier extracts forms and references from the actual candidate ROM, not just the VFR source. SHA-256: `476076f280ca6385024db1bf643e042629153afff8bab2f9a52cc61c221e411e`.

Five REF3 targets resolve to forms in their referenced formsets:

- CBS `0x7007`: UMC Common Options.
- CBS `0x7008`: UMC Debug Options.
- CBS `0x7009`: SMU Debug Options.
- CBS `0x7005`: NBIO Common Options.
- Setup `0x28EA`: Voltage Configuration.

The Setup reference to bridge form 1 also exists in the binary. Earlier report labels for 7009 and 7005 were wrong and are replaced by these decoded titles. The earlier VFR-only check did not prove binary resolution and is superseded.

Both changed expressions are in Voltage Configuration form 0x28EA. Replacement bytes `47 02 47 02 16 02` encode FALSE, FALSE, OR. One is in GRAY_OUT_IF scope (0x19), the other in SUPPRESS_IF scope (0x0A). A false condition does not itself gray or suppress its scope. Nested conditions and native enable fields still matter. The original noncanonical records' AMI interpretation is not proven, so behavioral equivalence cannot be claimed.

Command: `python3 evidence/firmware-audit/20260923-hii-refs/verify.py`.

Observed: `PASS_BINARY_TARGET_RESOLUTION`, exit 0, stderr empty. Evidence: `evidence/firmware-audit/20260923-hii-refs/result.json`.

This is static link resolution and expression decoding only. It does not prove AMI runtime navigation, voltage-setting semantics, physical clocks, or overall goal completion. No ROM change occurred during this audit.
