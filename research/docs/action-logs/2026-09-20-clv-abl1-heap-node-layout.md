# CLV ABL1 HEAP node layout bridge — intent

Timestamp: 2026-09-20T10:10:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor
Target: exact ABL1 runtime table lookup function `0x6374`, called after UCLK descriptor `0x20 -> 0x4800 -> 0x49CC`.

Bounded action: recover one exact runtime HEAP node layout and value flow: input key `0xA04E` at provider descriptor, global table pointer/sentinel, linked-node key comparison, returned body pointer/length fields, and the external storage boundary. Do not rerun prior 32/36/42/53/59 check suites, do not search globally for APCB consumers, and do not assign CBSG schema without bytes.

Pinned inputs:

- ROM SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.
- Exact ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.
- Prior runtime-heap result SHA-256 46a126825991b945716fe6cf52b4b68df5054304a16feac086067451a2dc5ce5.
- Prior provider result SHA-256 3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9.

Next executable action: run unique verifier evidence/firmware-audit/20260920-clv-abl1-heap-node-layout/abl1_heap_node_layout_verify.py.

Expected effect: new evidence/report/action-log artifacts only. No firmware, hardware, settings, shared plan/memory, global config, MCP/Cutter, candidates, source, commits, or subagents.

Rollback: remove only this unique evidence directory, report, and action log.
