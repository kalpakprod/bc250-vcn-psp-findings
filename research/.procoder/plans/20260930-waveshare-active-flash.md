# Conventional BIOS flash command core
## Scope/anchor
Owner choseA: include erase/program/verify. This implements ordinary SPI NOR requests, not PSP signature replacement, TOCTOU injection or hardware flash authorization.
## Existing groups
Shared J4004/FCH/BIOS bus; SDK master init generates outputs. Existing passive observer uses GP10-13 and must be disabled before any active pin ownership. Exact chip variant/protocol/size unknown on physical unit.
## Use cases
Read identification/status/data; build bounded single-page program or4KiB sector erase requests for a verified target. Physical backend and readback loop are separate pending steps.
## Checklist
Pure C command core: no GPIO/flash/clock calls, single-I/O3byte addresses, chip size≤16MiB, read≤128, page≤256 without crossing page, aligned4KiB erase. Destructive operations require caller's exact-target authorization and known exclusive bus. Default deny. No raw arbitrary-opcode interface/chip erase.
Native same-input regression: absent original implementation fails compile; new module passes commands/bounds/gates; rollback four roles preserves pristine source. Make test after slice.
## Questions
Blocking physical operation: bus isolation/ownership and recovery/readback exact image. Not a blocker for offline core. Preserve signed PSP regions through later host image-diff guard; not done by this command builder.
## Decisions
A recorded; include programmer capability, do not authorize physical write now. Implement minimal protocol core first, then backend/host verification. No public network write endpoint.
