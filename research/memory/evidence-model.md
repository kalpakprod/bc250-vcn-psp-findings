# Evidence model

Use these labels in notes and reports:

- `observed-bytes`: direct bytes, sizes, hashes, parser output, or register output.
- `static-analysis`: reproducible disassembly, source trace, call graph, or structure derivation.
- `emulated-or-host-tested`: QEMU, emulator, test kernel, or host-side reproduction.
- `hardware-verified`: direct result from the identified board with baseline and readback.
- `external-primary`: vendor or upstream documentation applicable to the exact question.
- `historical-report`: imported report, chat, forum, or session summary not yet reproduced.

A conclusion may not use a stronger label than its evidence. Record contradictions and the cheapest test that can resolve them.
