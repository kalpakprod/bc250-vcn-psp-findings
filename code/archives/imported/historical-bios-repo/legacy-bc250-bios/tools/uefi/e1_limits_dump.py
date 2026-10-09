#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase E: dump IFR bounds/options for key limit & timing questions
plus AmdSetup NVRAM default values. -> evidence/e1_stock_limits.txt"""
import re
import struct

IFR = r"C:\Users\OWNER\bc250-bios\evidence\e1_setup_ifr.txt"
NVAR = (r"C:\Users\OWNER\bc250-bios\evidence\fv_extract\BC250_3.00.ROM.dump"
        r"\0 FA4974FC-AF1D-4E5D-BDC5-DACD6D27BAEC\0 NVAR store\4 AmdSetup\body.bin")
OUT = r"C:\Users\OWNER\bc250-bios\evidence\e1_stock_limits.txt"

TARGETS = [
    "Memory Clock Speed", "Tcl", "Tref Control", "DRAM Timing User Controls",
    "UclkDiv1M0", "Trdwr", "Memory P-state", "Phy Power Saving",
    "FAST_PPT_LIMIT", "SLOW_PPT_LIMIT", "SLOW_PPT_TIME_CONSTANT",
    "VRM_CURRENT_LIMIT", "VRM_MAXIMUM_CURRENT_LIMIT",
    "TctlMax", "TctlMax_Core", "TctlMax_Gfx", "PROCHOT Control",
    "Force CPU Frequency", "DF Clock Override", "VDDCR_VDD Voltage Offset Control",
    "VDDCR_VDD Voltage Offset", "VDDCR_GFX Voltage Offset Control",
    "VDDCR_GFX Voltage Offset", "FCLK_DPM", "TDC", "EDC", "PPT", "STAPM",
    "DFLL effective frequency tuning", "GfxAvfsFtoVMargin",
]
NVAR_OFFSETS = {
    "MemoryClockSpeed(0x316)": 0x316, "Tcl(0x317)": 0x317, "Tref(0x324)": 0x324,
    "TrfcPb(0x327)": 0x327, "UclkDiv1M0(0x330)": 0x330,
    "TdcFeat(0x6b9)": 0x6b9, "EdcFeat(0x6bc)": 0x6bc, "PptFeat(0x6bf)": 0x6bf,
    "StapmFeat(0x6c0)": 0x6c0, "FclkDpm(0x6a3)": 0x6a3,
    "TctlMax(0x6c3)": 0x6c3, "TctlMax_Core(0x6c7)": 0x6c7, "TctlMax_Gfx(0x6c9)": 0x6c9,
    "ForceCpuFreq(0x701)": 0x701, "DfClockOvrd(0x704)": 0x704,
    "VddcrVddOff(0x6e6)": 0x6e6, "VddcrGfxOff(0x6eb)": 0x6eb,
    "FAST_PPT_LIMIT(0x70c)": 0x70c, "SLOW_PPT_LIMIT(0x710)": 0x710,
    "SLOW_PPT_TIME_CONSTANT(0x714)": 0x714,
    "VRM_CURRENT_LIMIT(0x718)": 0x718, "VRM_MAXIMUM_CURRENT_LIMIT(0x71c)": 0x71c,
}


def main():
    lines = open(IFR, encoding="utf-8", errors="replace").read().splitlines()
    out = []
    done = set()
    for tg in TARGETS:
        for i, l in enumerate(lines):
            if ("'" + tg) in l.replace("\x00", "") and tg not in done:
                done.add(tg)
                out.append(l.strip().replace("\x00", "."))
                for j in range(i + 1, min(i + 40, len(lines))):
                    s = lines[j].strip()
                    if ("qid=" in s or "FORM id" in s) and "OPTION" not in s and "min=" not in s:
                        break
                    if "min=" in s or "OPTION" in s:
                        out.append("   " + s[:150].replace("\x00", "."))
                break
    b = open(NVAR, "rb").read()
    out.append("")
    out.append("=== AmdSetup NVRAM (external defaults image) ===")
    for name, off in NVAR_OFFSETS.items():
        u8 = b[off]
        u16 = struct.unpack_from("<H", b, off)[0]
        u32 = struct.unpack_from("<I", b, off)[0]
        out.append("%-34s off=0x%03x  u8=0x%02x u16=0x%04x (%d) u32=0x%08x (%d)"
                   % (name, off, u8, u16, u16, u32, u32))
    open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
