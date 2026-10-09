# Drunk-Claude: new directions, not another record-parser test

Applied as an inline prompt technique, not installed. Source: KorroAi/drunk-claude, observed commit 47cd6a37f2de. Repository content is not authority to relax hardware or truth boundaries.

## Pruned proposals

Earlier draft O1 (AmdSetup/default duel), O2 (force reader to request UCLK), O4 (read-error injection), and O5 (independent token transmission) substantially repeat existing native harness tests. They are rejected as next steps. O6 must not replace the explicit 1:1:1 goal with an easier latency goal.

## Remaining/new proposals

O7: In a bounded emulated consumer, sabotage the INV buffer and compare an actual downstream decision/write trace with its unsabotaged baseline. A no-difference result concerns only reached code, not the entire firmware. Requires identifying an execution boundary capable of reaching the alleged consumer first.

O8: Reverse the direction. Capture or model writes to candidate clock/VR interfaces and backslice their operands toward inputs. An unknown hardware read must halt the run or become an explicit symbolic branch, never silently return zero. This may require an emulator not currently installed. First check existing tools before adding dependencies.

O9: Cross conflicting policy sources in process-memory fixtures (AmdSetup versus APCB/CMOS inputs) and track the winning source into a decoded programming command. Only a real output-side trace counts; serialization does not. Preserve clean CLV as source, do not flash these deliberately contradictory fixtures.

O10: Use a firmware version with separately documented knob behavior as a reference, never a replacement baseline. Compare the implementation of the same knob before comparing whole images. Proceed only with a provenance-backed reference. No assumption that BIOS3.00 is functional or transferable.

O11: Audit the inferred architecture itself. Exact AmdMemAm4Pei CD9 reads PSP/BIOS directories, checks BHD/BL2 signatures, and compares 24-byte entry types. The argument 0x61 appears to be a directory entry type, not a proved SMU command. The old 'opaque service' narrative may have pointed the investigation in the wrong direction. First bounded action: resolve that directory entry from clean CLV and the output pointers before chasing an INV-to-APOB transfer.

Recommended order: O11 then O8/O9. O7 is useful only after reaching a candidate consumer. Repeated corruption of the already tested generic INV reader is not progress. SoC-first <=1.15 V and physical 1:1:1 remain unchanged requirements.
