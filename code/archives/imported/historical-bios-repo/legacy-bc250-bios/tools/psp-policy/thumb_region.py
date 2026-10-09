#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thumb disassembly of a t02 region with literal-pool annotations."""
import sys, re, struct
import capstone

path = r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries\BC250_3.00_CHIPSETMENU.ROM\01_t02_0x8EAC00_14350.bin"
data = open(path, "rb").read()

start = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x12400
end = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x12700

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = True
for ins in md.disasm(data[start:end], start):
    if ins.mnemonic == ".byte":
        print("0x%08x: .byte     %s" % (ins.address, ins.op_str))
        continue
    line = "0x%08x: %-8s %s" % (ins.address, ins.mnemonic, ins.op_str)
    m = re.match(r"^(\w+),\s*\[pc,\s*#(-?0x[0-9a-f]+|-?\d+)\]$", ins.op_str, re.I)
    if m:
        off = int(m.group(2), 0)
        pc = (ins.address + 4) & ~3
        target = pc + off
        if 0 <= target <= len(data) - 4:
            val = struct.unpack_from("<I", data, target)[0]
            note = "  ; [pool@0x%x] = 0x%08x" % (target, val)
            if val == 0x31535024:
                note += "  <<< '$PS1' MAGIC"
            elif 0x03000000 <= val < 0x03300000:
                note += "  <<< PSP MMIO 0x03xx"
            elif 0x09000000 <= val < 0x0A000000:
                note += "  <<< SMN 0x09xx"
            line += note
    print(line)
