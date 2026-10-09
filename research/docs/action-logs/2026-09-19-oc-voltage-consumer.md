# OC voltage consumer continuation

## Intent — 2026-09-19T17:42:04+05:00

Root owns bounded offline control tracing and deliverable gates; no delegation in this pass. User requests a final integrated synchronous 1:1:1 OC BIOS and authorizes SoC up to 1.15 V. Interpret 1.15 V as a user-imposed ceiling, not a measured safe rating or permission to maximize unrelated rails, current or thermal limits. Exact flash approval and recovery requirements remain separate.
Reuse the hash-pinned clv modules and disassembly in evidence/firmware-audit/20260919-clock-trace; trace voltage offsets and record consumers without hardware operations. Known root input ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8, 16777216 bytes. Record further evidence under evidence/firmware-audit/20260919-voltage-trace and docs/research/2026-09-19-voltage-consumer.md. Append findings to memory/oc-recheck.md, correct R2 status to partial if needed.
Expected effect: establish consumer/encoding or an evidence-backed blocking boundary. Do not generate a flashable voltage candidate from unknown encoding or call requested settings applied. Rollback: remove only new analysis outputs if requested; preserve all firmware input hashes and historical findings. No chip or source image writes.

## Result

Four exact instruction windows verified against retained module bytes; +0x6E5/u8 maps to record 0x1363, +0x6E6/u32 to 0x1364 in both PEI modules. CbsBasePei 0x36F0 serializer writes $INV version 1, header 0x20 and terminal 0xFFFF; direct caller at 0x36DE. No voltage conversion in the observed copy path. Report: docs/research/2026-09-19-voltage-consumer.md; evidence/firmware-audit/20260919-voltage-trace/serialization.json.
Advisor second opinion concurs that user ceiling/engineering-board status cannot establish rail encoding or safe maxima; this was a tool-less reasoning consultation, not independent artifact review. R2/R3 remain partial. Final integrated BIOS blocked by unknown control application/units and unresolved integrated baseline; hardware verification UNRUN. No candidate created and no flash approval inferred.

## Goal-loop iteration 2 — intent and boundary

Continue read-only callback provenance on the same hash-pinned CbsBasePei module, append exact evidence and correct task statuses. Reviewer FAIL accurately identifies a missing deliverable; it does not supply voltage encoding, independent clock measurements or hardware safety evidence. No artificial ROM will be generated merely to satisfy an existence check. Rollback: append a correction; original firmware remains unchanged.

Observed: fresh SHA-256 of CbsBasePei matches 6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77. TE image base is 0x09EBA08C. Raw pointer 0x09EBD74C (base + wrapper RVA 0x36C0) occurs once at file offset 0x13C40, followed by 0xFFFFFFFE. This is a callback-table lead, not a proven runtime caller. Direct wrapper call at 0x36DE still leads to serializer 0x36F0. Searches for named IDS_NV voltage/clock constants in retained headers found none; this does not prove absence of a binary/table-based consumer.
Status: final BIOS NOT BUILT; R2 and R3 BLOCKED for final application/encoding proof, not done. Board measurements remain UNRUN. The requested safe/optimal release cannot be certified by offline artifact existence. Further work requires resolving the callback-table/IDS consumer and a physical validation stage before a release claim.

## Goal-loop iteration 3 — callback-chain verification

Intent: persist the read-only callback-table reconciliation on the unchanged module; no ROM build or hardware write. Root owns this bounded check, no worker. Rollback: append correction if contradicted.
Observed-bytes/static-analysis: TE .data RVA 0x13D80 maps to file 0x13BF0. Dispatcher at RVA 0x39A references VA 0x09ECDEAC, file 0x13C90. Its five u32 words are [0xFFFFFFFF,0,0,0,0x09ECDE4C]. The nested table at VA 0x09ECDE4C/file 0x13C30 contains [0xFFFFFFFF,0,0,0,0x09EBD74C,0xFFFFFFFE]. The callback equals ImageBase 0x09EBA08C + wrapper RVA 0x36C0. Dispatcher compares entry+0x14 against its third argument and calls entry+0x10 at RVA 0x495. Thus event 0xFFFFFFFE selects the serialization wrapper through wildcard CPU entries. This is static callback selection, not proof of boot-time execution or a voltage writer.
Verification: Python struct unpacking used section-derived VA-to-file mapping; assertions passed for module SHA-256, wrapper pointer and event selector. Original module unchanged. This narrows the next trace to the caller requesting event 0xFFFFFFFE and the destination of its $INV output, not arbitrary voltage values.
Goal verdict remains FAIL/blocked: final BIOS does not exist, 1.15 V request encoding remains unresolved, actual 1:1:1 and safe maxima require hardware evidence. Preserve the user's 'up to 1.15 V' ceiling; do not silently replace it with reviewer's 'exactly 1.15 V' requirement.

## Operator clarification — 2026-09-19T17:57:47+05:00

Intent: update baseline decision and tasks after operator explicitly selected BIOS 5.00 clv and stated flashing is available now. SoC ceiling remains 1.15 V. Root owns this update; no delegation. Fresh sha256sum confirms selected file evidence/donor/retroweb-20260916/BC250_5.00_clv.bin equals ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8. Plain clv is now the approved development base; W9/core/logo integration is no longer a prerequisite for this OC track. Actual chip identity and exact-image flash approval remain separate. Append decision to memory and revise R1; resume R2/R3 offline. Rollback: preserve historical decisions and append superseding clarification. No firmware bytes or board state changed.

## Expanded method: inspect compressed ABL payloads

Intent: persist bounded read-only ABL lineage/decompression findings rather than repeat x86 literal scans. Root owns this check; no delegation. Source unchanged clv SHA ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8; imported robin5_psp_bodies/ABL0..4 were matched byte-for-byte inside respective PSP types 0x30..0x34 at carrier+0x100 before interpretation. Use Python zlib.decompress in memory; do not write or modify signed payloads. Rollback: append correction only.
Observed: all five imported bodies start 78DA and decompress successfully. Decompressed sizes: 7952, 94624, 30336, 85200, 92096. SHA-256 respectively: 3405551617c13dc7b1db464edd74e0f7a4240a80b37ed068c7650ccfe2d19e29; af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a; 6fcae35368554127c48863169e660c27e19d9fb705871d918dbbbf933c3fbd32; 3f5890b3a830725a11e169861fcfa208fa3f5fab37a38fc7f994a221a1f213be; 1d60a34f1641204423024857249781d9184b2c9c5342f4dd8dbc070df6c5150b.
No literal $INV, little-endian u16 0x1364 or 0x1374 found in decompressed bytes. This does NOT exclude generated constants, transformed record IDs or an indirect consumer. 0x1204 has isolated hits, not interpreted as control writes. Zero compressed-body matches cannot be used to establish absence in code; unpacking is required. Final semantic trace still INCONCLUSIVE.
External exact-term search returned generic desktop-voltage material, not BC250 consumer evidence; none adopted. No voltage units, safe ceiling or rail mapping inferred from that search. Existing DF1400 candidate unchanged; no hardware test performed.
