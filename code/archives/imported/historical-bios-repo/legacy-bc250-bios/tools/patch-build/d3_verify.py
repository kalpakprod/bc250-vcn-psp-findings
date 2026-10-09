# Post-build verification of D3 images: reparse dir/gasket/APCB from the final images.
import struct, hashlib, json

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
OUT = r"C:\Users\OWNER\tmp_bc250\recon\d3"
BASE = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()


def fletcher32(data):
    s1 = s2 = 0
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        s1 = (s1 + w) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def check_dir(b, base, esz, tag):
    ck = struct.unpack_from("<I", b, base + 4)[0]
    cnt = struct.unpack_from("<I", b, base + 8)[0]
    calc = fletcher32(b[base + 8: base + 0x10 + cnt * esz])
    ok = calc == ck
    print("  %s dir: count=%d fletcher32 %s (stored %#x calc %#x)" % (tag, cnt, "OK" if ok else "FAIL", ck, calc))
    return ok


def ranges(diff):
    # merge changed byte indices into ranges
    rs = []
    for i, d in enumerate(diff):
        if d:
            if rs and rs[-1][1] == i - 1:
                rs[-1][1] = i
            else:
                rs.append([i, i])
    return rs


def show_diff(a, b, tag):
    diff = [x != y for x, y in zip(a, b)]
    n = sum(diff)
    print("  %s: %d bytes in %d ranges:" % (tag, n, len(ranges(diff))))
    for r in ranges(diff):
        print("    %#x - %#x (%d bytes)" % (r[0], r[1], r[1] - r[0] + 1))


for tag, fn in [
    ("D3-B", OUT + r"\D3-B_APCB-DFG-i_gasket-A-B-unsigned_DO_NOT_FLASH_WITHOUT_PROGRAMMER_BACKUP.bin"),
    ("D3-A", OUT + r"\D3-A_APCB-DFG-i-only_CONTROL_expected-false-negative.bin"),
]:
    b = open(fn, "rb").read()
    print("\n== %s (%d bytes, md5 %s)" % (tag, len(b), hashlib.md5(b).hexdigest()))
    # 1. PSP dir
    assert check_dir(b, 0x8E0000, 16, "PSP")
    assert check_dir(b, 0xAB0000, 24, "BHD")
    e24 = None
    cnt = struct.unpack_from("<I", b, 0x8E0008)[0]
    for i in range(cnt):
        eo = 0x8E0010 + 16 * i
        t, sz, loc = struct.unpack_from("<IIQ", b, eo)
        if t == 0x24:
            e24 = (sz, loc)
    print("  dir entry 0x24: size=%#x loc=%#x" % e24)
    if tag == "D3-B":
        assert e24 == (0x3010, 0xFF9E0000)
        # 2. new gasket blob
        g = 0x9E0000
        s14, = struct.unpack_from("<Q", b, g + 0x14)
        s50, = struct.unpack_from("<Q", b, g + 0x50)
        tot, = struct.unpack_from("<I", b, g + 0x6C)
        ver, = struct.unpack_from("<I", b, g + 0x60)
        print("  gasket@0x9E0000: size@14=%#x size@50=%#x total@6C=%#x ver@60=%#x" % (s14, s50, tot, ver))
        assert (s14, s50, tot) == (0x2E10, 0x2E10, 0x3010)
        assert ver == 0x0B510016
        body = b[g + 0x100: g + 0x100 + 0x2E10]
        off = 0x40
        groups = []
        while off + 8 <= len(body):
            t, c = struct.unpack_from("<II", body, off)
            if t == 0 or t > 0xFFFF or c > 0x100000:
                break
            groups.append((hex(off), hex(t), c))
            off += 8 + c * 8
        print("  gasket body groups:", groups, " end=%#x" % off)
        assert off == len(body)
        assert [x[1] for x in groups] == ["0x201", "0x203", "0x210", "0x280", "0x281"]
        assert [x[2] for x in groups] == [1281, 31, 13, 105, 31]
        # step-A values
        def val_at(addr):
            pat = struct.pack("<I", addr)
            res = []
            i = -1
            while True:
                i = body.find(pat, i + 1)
                if i < 0:
                    return res
                if i % 4 == 0:
                    res.append((i, struct.unpack_from("<I", body, i + 4)[0]))
        for a, expect in [(0x03E810, [0x6]), (0x03A2011C, [0x107FF, 0x107FF]), (0x03A20124, [0x10FFF])]:
            got = val_at(a)
            print("    %#010x -> %s" % (a, ["%#x" % v for _, v in got]))
            assert [v for _, v in got] == expect, (a, got)
        nvcn = sum(1 for i in range(0, len(body) - 8, 4)
                   if 0x0900C000 <= struct.unpack_from("<I", body, i)[0] <= 0x0900CFFF)
        print("    VCN bank pairs: %d" % nvcn)
        assert nvcn == 56
        # 3. old blob untouched
        assert b[0x982000:0x982000 + 0x2E50] == BASE[0x982000:0x982000 + 0x2E50]
        print("  old gasket @0x982000: untouched")
        # 4. region around new blob still FF
        assert all(x == 0xFF for x in b[g + 0x3010: 0xAB0000 - 0x10])
        print("  region 0x9E3010-0xAB0000: still FF")
    # 5. APCB
    a = 0xAB1000
    size = struct.unpack_from("<I", b, a + 8)[0]
    cks = b[a + 0x10]
    calc = (0x100 - sum(b[a + i] for i in range(size) if i != 0x10)) & 0xFF
    print("  APCB: size=%#x cks=%#x calc=%#x %s" % (size, cks, calc, "OK" if cks == calc else "FAIL"))
    assert cks == calc
    for w in (0x130, 0x16C):
        row = b[a + w: a + w + 4]
        print("    wildcard row +%#x: %s" % (w, row.hex()))
        assert row == bytes.fromhex("00ff7f00")
    show_diff(BASE, b, tag + " vs base")

print("\nALL VERIFICATION PASSED")
