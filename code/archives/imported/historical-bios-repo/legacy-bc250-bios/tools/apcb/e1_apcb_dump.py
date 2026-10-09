#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase E: full APCB group/token dump + diff across stock and modded images.

APCB blob @0xAB1000 (BC-250): header 0x20 bytes:
  magic 'APCB', u32 size(+8), u16 cks(+0xC), ..., u8 cks byte(+0x10).
Group (repeats from +0x20): {sig u32, gid u16, flags u16, inst u32, size u32};
group header is 0x10 bytes and size INCLUDES it; next group = start + size.
Subgroup inside body (where body starts with same gid): {gid u16, instance u16,
size u32}; size includes the 8-byte subgroup header.
Bodies are hexdumped raw; token rows decoded bytewise {u8 a, u8 b, u16 c}.
Output: evidence/e1_apcb_groups.txt (inventory) and evidence/e1_apcb_diff.txt
(stock vs each modded image).
"""
import struct, sys

FILES_DIR = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
IMAGES = {
    "stock_3.00":   FILES_DIR + r"\BC250_3.00.ROM",
    "chipsetmenu":  FILES_DIR + r"\BC250_3.00_CHIPSETMENU.ROM",
    "dump_5.00":    FILES_DIR + r"\dump_5.00.bin",
    "my_4.0_moded": FILES_DIR + r"\my_4.0_MODED.bin",
    "steam_8core":  FILES_DIR + r"\8_cores_Steam.rom",
    "bc250_steam":  FILES_DIR + r"\bc250-Steam.rom",
    "modded_bios":  FILES_DIR + r"\bc250 modded bios.ROM",
    "robin5.00":    FILES_DIR + r"\Robin5.00",
}
ROM_CHIP_DUMP = FILES_DIR + r"\W25Q128BV@WSON8_20250122_140516.BIN"
BASE = 0xAB1000
OUT_GROUPS = r"C:\Users\OWNER\bc250-bios\evidence\e1_apcb_groups.txt"
OUT_DIFF = r"C:\Users\OWNER\bc250-bios\evidence\e1_apcb_diff.txt"


def parse_apcb(blob, base):
    """-> list of groups: (offset, sig, gid, flags, inst, size, subgroups)
    subgroup: (offset, gid, instance, size, body bytes)"""
    size = struct.unpack_from("<I", blob, base + 8)[0]
    end = base + size
    groups = []
    off = base + 0x20  # first group at +0x20
    while off + 0x10 <= end:
        sig = blob[off:off + 4]
        gid, flags, inst, gsize = struct.unpack_from("<HHII", blob, off + 4)
        if gsize < 0x10 or off + gsize > end:
            groups.append((off, sig.decode("latin1"), gid, flags, inst, gsize, [],
                           bytes(blob[off:min(off + 0x40, end)])))
            break
        subs = []
        body_start = off + 0x10
        p = body_start
        # subgroup walk heuristic: only while body starts with same gid
        while p + 8 <= off + gsize:
            sgid, sinst, ssize = struct.unpack_from("<HHI", blob, p)
            if sgid != gid or ssize < 8 or p + ssize > off + gsize:
                break
            subs.append((p, sgid, sinst, ssize, bytes(blob[p + 8:p + ssize])))
            p += ssize
        rawbody = bytes(blob[body_start:off + gsize])
        groups.append((off, sig.decode("latin1"), gid, flags, inst, gsize, subs, rawbody))
        if gsize == 0:
            break
        off += gsize
    return size, groups


def fmt_group(off, sig, gid, flags, inst, gsize, subs, rawbody, indent=""):
    lines = []
    lines.append("%sgroup @+%#x (ROM %#x) sig=%r gid=%#06x flags=%#06x inst=%d size=%#x"
                 % (indent, off - BASE, off, sig, gid, flags, inst, gsize))
    lines.append("%s  body %d bytes @ROM %#x (APCB + %#x)" % (indent, len(rawbody), off + 0x10, off + 0x10 - BASE))
    for i in range(0, len(rawbody), 16):
        row = rawbody[i:i + 16]
        asc = "".join(chr(c) if 32 <= c < 127 else "." for c in row)
        lines.append("%s    +%#06x: %s  %s" % (indent, off + 0x10 - BASE + i, row.hex(" "), asc))
    for (p, sgid, sinst, ssize, body) in (subs or []):
        lines.append("%s  sub @+%#x gid=%#06x inst=%d size=%#x" % (indent, p - BASE, sgid, sinst, ssize))
        # bytewise token rows: {u8 a, u8 b, u16 c}
        rows = []
        for j in range(0, len(body) - 3, 4):
            a, b = body[j], body[j + 1]
            c = struct.unpack_from("<H", body, j + 2)[0]
            rows.append("(%02X,%02X,%04X)" % (a, b, c))
        lines.append("%s    token rows: %s" % (indent, " ".join(rows)))
    return lines


def main():
    out = []
    apcbs = {}
    for name, path in list(IMAGES.items()) + [("chip_dump", ROM_CHIP_DUMP)]:
        try:
            blob = open(path, "rb").read()
        except OSError as e:
            out.append("!! %s: %s" % (name, e))
            continue
        if len(blob) < BASE + 0x100 or blob[BASE:BASE + 4] != b"APCB":
            out.append("!! %s: no APCB @0x%X" % (name, BASE))
            continue
        size, groups = parse_apcb(blob, BASE)
        apcbs[name] = (size, groups)
        out.append("=" * 78)
        out.append("### %s  (APCB size=%#x, %d groups)" % (name, size, len(groups)))
        for g in groups:
            out.extend(fmt_group(*g[:8]))
        # DFG wildcard words check
        w130 = struct.unpack_from("<I", blob, BASE + 0x130)[0]
        w16c = struct.unpack_from("<I", blob, BASE + 0x16C)[0]
        out.append("  DFG wildcard words: +0x130=%#010x +0x16C=%#010x  (%s)" % (
            w130, w16c,
            "UNLOCKED 0x7F" if w130 & 0xFF == 0x7F and w16c & 0xFF == 0x7F
            else ("stock 0x1F" if (w130 & 0xFFFF00) == 0x1FFF00 else "other")))
    open(OUT_GROUPS, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("groups written:", OUT_GROUPS)

    # ---- diff stock vs mods, group by group ----
    if "stock_3.00" not in apcbs:
        print("no stock APCB; diff skipped")
        return
    ref_size, ref = apcbs["stock_3.00"]
    dlines = []
    for name, (size, groups) in apcbs.items():
        if name == "stock_3.00":
            continue
        dlines.append("=" * 78)
        dlines.append("### diff stock_3.00 -> %s (size %#x vs %#x)" % (name, ref_size, size))
        refb = open(IMAGES["stock_3.00"], "rb").read()
        modb = open(IMAGES.get(name) or ROM_CHIP_DUMP, "rb").read()
        # byte diff over APCB span
        n = min(ref_size, size)
        diff_ranges = []
        i = 0
        while i < n:
            if refb[BASE + i] != modb[BASE + i]:
                j = i
                while j < n and refb[BASE + j] != modb[BASE + j]:
                    j += 1
                diff_ranges.append((i, j))
                i = j
            else:
                i += 1
        for (a, b) in diff_ranges:
            # map to group
            gname = "?"
            for (goff, sig, gid, flags, inst, gsize, subs, rawbody) in ref:
                if goff - BASE <= a < goff - BASE + gsize:
                    gname = "group %s %#x @+%#x" % (sig, gid, goff - BASE)
                    for (p, sgid, sinst, ssize, body) in (subs or []):
                        if p - BASE + 8 <= a < p - BASE + ssize:
                            gname += " sub inst=%d @+%#x body+%#x" % (sinst, p - BASE, a - (p - BASE + 8))
            dlines.append("  diff bytes [+%#x .. +%#x) len=%d in %s" % (a, b, b - a, gname))
            for o in range(max(0, a - 8), min(n, b + 8), 16):
                dlines.append("    +%#06x  stock: %s" % (o, refb[BASE + o:BASE + o + 16].hex(" ")))
                dlines.append("    +%#06x  mod  : %s" % (o, modb[BASE + o:BASE + o + 16].hex(" ")))
    open(OUT_DIFF, "w", encoding="utf-8").write("\n".join(dlines) + "\n")
    print("diff written:", OUT_DIFF)


if __name__ == "__main__":
    main()
