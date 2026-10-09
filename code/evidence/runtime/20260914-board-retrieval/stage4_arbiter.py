#!/usr/bin/env python3
"""S2-A stage 4 arbiter (single-register reads), 2026-09-12.

Replicates read_vcn_direct.py exactly: SINGLE-REGISTER seek+read(4) of the UVD
frame through /sys/kernel/debug/dri/1/amdgpu_regs.

G7 correction baked in (2026-09-12): FULL-DUMP reads of amdgpu_regs (cat) hung
the kernel twice even with the VCN domain powered+clocked, while single-register
reads of the same file were the campaign's proven transport (VcnDirect.rd =
read_reg = seek+read(4); 26.08 ladder returned clean all-ones). Read individual
registers ONLY; never dump the whole file.

Verdicts per the chain report:
  mmUVD_VERSION real value  -> bridge passage; VCN visible from x86
  all-ones everywhere       -> island isolated (bridge closed), clean result
"""
import os
import struct
import sys
import time

REGS = os.environ.get("BC250_REGS", "/sys/kernel/debug/dri/1/amdgpu_regs")
OUT = "/home/OWNER/vcn_unlock/stage4_arbiter_%s.txt" % time.strftime("%Y%m%d_%H%M%S")

PROBES = [
    ("mmUVD_POWER_STATUS", 0x7800 + 0x00BC),
    ("mmUVD_STATUS",       0x7800 + 0x00BD),
    ("mmUVD_SEMA_ADDR_LOW", 0x7800 + 0x0001),
    ("mmUVD_SCRATCH9",     0x7800 + 0x00C9),
    ("mmUVD_VERSION",      0x7800 + 0x00CA),
]


def read32(f, byte_off):
    f.seek(byte_off)
    data = f.read(4)
    if len(data) != 4:
        raise IOError("short read at 0x%06x" % byte_off)
    return struct.unpack("<I", data)[0]


def main():
    lines = []
    with open(REGS, "rb", buffering=0) as f:
        for name, dword_off in PROBES:
            byte_off = dword_off * 4
            val = read32(f, byte_off)
            mark = "" if val == 0xFFFFFFFF else "  <<< REAL VALUE"
            line = "%-20s (dword 0x%04x, byte 0x%06x) = 0x%08x%s" % (name, dword_off, byte_off, val, mark)
            print(line, flush=True)
            lines.append(line)

    real = [l for l in lines if "REAL VALUE" in l]
    verdict = "BRIDGE-PASS: %d of %d probes real" % (len(real), len(PROBES)) if real \
        else "ALL-ONES: island isolated (bridge closed); gasket latched but NBIF not passing"
    print("VERDICT: %s" % verdict, flush=True)
    lines.append("VERDICT: %s" % verdict)
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("log: %s" % OUT, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
