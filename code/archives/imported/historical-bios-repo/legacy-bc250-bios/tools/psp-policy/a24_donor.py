# A24: identify the donor dump; group lists of 0x24/0x45 blobs in every candidate ROM;
# decisive check: does any blob contain groups {0x205, 0x20a, 0x20b} (fn@0x20d8 target)?
# Also: donor grp 0x210 content vs stock (E810 + 12 E814 commands).
import struct
import os

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
CANDS = [
    "W25Q128BV@WSON8_20250122_140516.BIN",
    "W25Q128BV@WSON8_20250122_140516 (1).BIN",
    "dump_5.00.bin",
    "my_4.0_MODED.bin",
    "BC250_3.00.ROM",
    "bc250-Steam.rom",
    "bc250 modded bios.ROM",
    "8_cores_Steam.rom",
    "MX25L4006E_BC-250.bin",
]


def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def groups_of(buf, addr):
    if addr + 0x104 > len(buf) or buf[addr + 0x10:addr + 0x14] != b"$PS1":
        return None
    b = addr + 0x100
    cnt = u32(buf, b)
    if cnt > 0x40:
        return None
    out = []
    o = b + 0x40
    for i in range(cnt):
        t, c = u32(buf, o), u32(buf, o + 4)
        if c > 0x20000:
            return None
        out.append((t, c, o + 8))
        o += 8 + 8 * c
    return out


for fn in CANDS:
    p = os.path.join(FILES, fn)
    if not os.path.exists(p):
        print("!! missing %s" % fn)
        continue
    buf = open(p, "rb").read()
    print("=== %s (%d bytes) ===" % (fn, len(buf)))
    dirs = []
    for off in range(0, len(buf) - 0x110, 4):
        if buf[off:off + 4] in (b"$PSP", b"$BIO", b"$PL2", b"$B2L"):
            n = u32(buf, off + 8)
            if 0 < n <= 0x60:
                dirs.append((off, buf[off:off + 4], n))
    if not dirs:
        print("  no dirs")
        continue
    for doff, magic, n in dirs:
        g24 = []
        g45 = []
        for i in range(n):
            e = doff + 0x10 + 0x10 * i
            typ = buf[e]
            size = u32(buf, e + 4)
            addr = u32(buf, e + 8) & 0xFFFFFF
            if typ not in (0x24, 0x45):
                continue
            gl = groups_of(buf, addr) if size > 0x200 else None
            if gl is None:
                print("  dir@%#x %r ent[%d] type=%#04x size=%#x @%#x (not group-blob)" % (
                    doff, magic, i, typ, size, addr))
                continue
            desc = " ".join("%x:%d" % (t, c) for t, c, _ in gl)
            print("  dir@%#x %r ent[%d] type=%#04x size=%#x @%#x groups: %s" % (
                doff, magic, i, typ, size, addr, desc))
            for t, c, po in gl:
                if t == 0x210:
                    pairs = [(u32(buf, po + 8 * j), u32(buf, po + 4 + 8 * j)) for j in range(c)]
                    print("      grp210: " + "; ".join("%x->%x" % pv for pv in pairs[:4]) +
                          (" ... +%d more" % (len(pairs) - 4) if len(pairs) > 4 else ""))
                if t in (0x205, 0x20a, 0x20b):
                    print("      *** HAS grp %#x (%d pairs) ***" % (t, c))
