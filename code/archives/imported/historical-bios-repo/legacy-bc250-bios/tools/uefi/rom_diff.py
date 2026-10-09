#!/usr/bin/env python3
"""Byte-diff of community-modded BC250 ROMs vs stock 3.00.
Produces clustered diff ranges + classifies against known flash regions."""
import sys, hashlib

BASE = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00_CHIPSETMENU.ROM"
MODS = [
    r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\bc250-Steam.rom",
    r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\8_cores_Steam.rom",
    r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\bc250 modded bios.ROM",
    r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00.ROM",
    r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\Robin5.00",
    r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\W25Q128BV@WSON8_20250122_140516.BIN",
]
# Known regions (from rom_scan.py / PSP dir)
REGIONS = [
    (0x000000, 0x100000, "PSP region head? (pad)"),
    (0x8E0000, 0x9E0000, "PSP blobs (L1 dir @0x8E0000, gasket @0x982000, discovery @0x981A00)"),
]

def ranges(diff_idx, size, gap=64, minrun=8):
    """cluster diff byte indices into ranges, merging gaps<=gap bytes"""
    out = []
    for i in diff_idx:
        if out and i - out[-1][1] <= gap:
            out[-1][1] = i
        else:
            out.append([i, i])
    return [(a, b) for a, b in out if b - a >= minrun - 1]

def fmt(a, b):
    return "0x%06X..0x%06X (%5d B)" % (a, b + 1, b - a + 1)

def region_of(a, b):
    for lo, hi, name in REGIONS:
        if a < hi and b >= lo:
            return name
    return ""

base = open(BASE, "rb").read()
print("base:", len(base), hashlib.md5(base).hexdigest())
for path in MODS:
    try:
        mod = open(path, "rb").read()
    except OSError as e:
        print("!!", path, e); continue
    print("\n===", path.split("\\")[-1], len(mod), "md5", hashlib.md5(mod).hexdigest())
    if len(mod) != len(base):
        print("   size mismatch vs base, comparing common prefix")
    n = min(len(mod), len(base))
    diffs = [i for i in range(n) if mod[i] != base[i]]
    if not diffs:
        print("   IDENTICAL to base")
        continue
    print("   diff bytes: %d (%.3f%% of %d)" % (len(diffs), 100.0 * len(diffs) / n, n))
    for a, b in ranges(diffs, n):
        r = region_of(a, b)
        print("   %s  %s" % (fmt(a, b), ("<<< " + r) if r else ""))
