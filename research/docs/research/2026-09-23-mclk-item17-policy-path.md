# MCLK item 0x17: conditional dispatch follow-up

Pinned ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.

Service wrapper 0xC60 branches to dispatchers 0xE50/0xFD8. Both reference literal table address 0x6E224. Under the previously proposed, NOT proven load base 0x57100, this maps to payload 0x17124. Entry at 0x17134 is (0x606FD, 0x17), yielding Thumb target 0x95FC under the same assumption.

Fresh aligned disassembly of 0x95FC shows a fill call with length 0x20, NOT a descriptor key. At 0x9672 it loads a u16 from current-channel pointer +0x20; 0x9674 stores it at outer + channel*4 + 0x278. Byte anchors and table words were independently checked in the pinned raw payload.

This advances the conditional dispatch map, not the proven runtime path. Load base, source-to-APCB join and final clock actuator remain unresolved. No 1:1:1 recipe follows. Earlier draft incorrectly called 0x20 a descriptor and omitted the conditional base; those statements are withdrawn.

Evidence: evidence/firmware-audit/20260923-mclk-item17/result.json and aligned LLVM stdout/stderr/exit captures.
