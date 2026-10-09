# Native CbsBasePei configuration acquisition

Unchanged CbsBasePei+0x250 and its default helper were executed in an IA32 Linux user process. The test provides PEI FillMem/LocatePpi services. The successful variable path forwards to unchanged NvramPei+0xBF8. A static table audit confirms the supplied event 0x13579BDF matches no callback, so this experiment stops short of downstream board callbacks. It is not whole-firmware or board execution.

Input: old profile03 with MCLK enum0x23, Tcl16, UCLK enum1, DF request1750.

| Supplied variable-read condition    | Native acquired MCLK | Tcl  | UCLK enum | DF request | Variable calls |
| ----------------------------------- | -------------------- | ---- | --------- | ---------- | -------------- |
| Native live read succeeds           | 0x23                 | 16   | 1         | 1750       | 2              |
| First read reports NOT_FOUND        | 0xFF                 | 0xFF | 0xFF      | 1000       | 1              |
| Size probe reports 0x8B4, not 0x8B5 | 0xFF                 | 0xFF | 0xFF      | 1000       | 1              |
| Probe succeeds, second read fails   | 0xFF                 | 0xFF | 0xFF      | 1000       | 2              |

All four runs exit0, stderr empty. Both firmware sections of each linked executable were extracted and compared to the original module bodies: eight exact comparisons. No ROM source, candidate, CMOS, SMU or hardware change.

The actual native acquisition code preserves manual values on successful lookup and resets them through compiled defaults on these three supplied failures. This confirms a mechanism capable of producing Auto before clock-policy consumers. It does not prove that any of the three failures happened on the participant's machine. A successful acquisition also does not prove that later code applies the requested frequencies.

Source/commands/output: `evidence/firmware-audit/20260923-native-cbs-acquire/test.s` and `execution.json`. Modified test stubs are explicit inputs, not altered firmware branches. Scope does not include SoC-setting semantics or latency.
