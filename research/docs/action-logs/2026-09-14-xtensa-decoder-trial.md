# Xtensa decoder trial

## Intent

Root will compile the preserved `amd_smu_reverse_engineering/ghidra` Xtensa
SLEIGH definitions in a separate evidence directory using pypcode's bundled
SLEIGH compiler. This repairs the decoder gap at 0x23CB4. Inputs are preserved;
no global installation or hardware action is planned. Reuse current pypcode
cust/flix includes. Rollback: remove only the new trial directory if needed.

## Result

Local SLEIGH compilation succeeded after adding the missing LE token field
flix_i20=(4,23) in the copied architecture definition. Stock pypcode 4.0.0
stops at 0x23CCB; the trial decoder covers 0x23CB4..0x23D4F, including
const.sf at 0x23CCD (1.0f) and 0x23CE7 (0.0f).
Native pypcode Context is initialized with an explicit sleigh XML path;
the Python convenience Context accepts a language ID, not a .sla filename.

0x23CB4 is a writer of the slot record+8 value used by metrics. With
base=literal(0x178B4)+28*slot=0xF718+28*slot, it stores a computed float
at base+0x80 (slot_base+8) and a second value at base+0x84 (slot_base+12).
If byte base+0x90 is zero AND byte base+0x7A is zero, both values become
zero without a hardware measurement. Other paths use helper 0x3A9B8 and
source clock parameters. Thus VCLK=0 in export need not mean rail power-off;
the software slot record and its computation gates must be considered.

This trial confirms disassembly coverage, not complete p-code accuracy or
safe hardware behavior. Imported approximate floating-point implementations
must be reviewed before using the trial definitions for emulation.
