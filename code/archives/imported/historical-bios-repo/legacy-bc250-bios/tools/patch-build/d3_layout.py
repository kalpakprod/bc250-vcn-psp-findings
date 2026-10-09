# D3 layout recon:
# 1) diff my_4.0_MODED vs both W25Q128BV hw dumps (which regions differ)
# 2) orig gasket $PS1 header full dump (0x100) - fields
# 3) all '$PSP' dirs in ROM
# 4) dir checksum algorithm test (neg-sum u32)
# 5) free FF runs >= 0x3020 (aligned 0x100) for blob relocation
import struct, hashlib

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
b = open(FILES + r"\my_4.0_MODED.bin", "rb").read()
h1 = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
h2 = open(FILES + r"\W25Q128BV@WSON8_20250122_140516 (1).BIN", "rb").read()
print("md5 hw1:", hashlib.md5(h1).hexdigest())
print("md5 hw2:", hashlib.md5(h2).hexdigest())


def diff_regions(a, bb, label):
    print("\n%s: len %d vs %d" % (label, len(a), len(bb)))
    if len(a) != len(bb):
        return
    runs = []
    start = None
    for i in range(len(a)):
        if a[i] != bb[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                runs.append((start, i))
                start = None
    if start is not None:
        runs.append((start, len(a)))
    print("  differing runs: %d" % len(runs))
    for s, e in runs[:40]:
        print("    %#09x - %#09x  (%#x bytes)" % (s, e, e - s))


diff_regions(b, h1, "my_4.0_MODED vs hw1")
diff_regions(h1, h2, "hw1 vs hw2")

# gasket header
print("\norig gasket $PS1 header @0x982000 (0x100):")
g = b[0x982000:0x982100]
for o in range(0, 0x100, 16):
    print("  %03x: %s  %s" % (o, g[o:o + 16].hex(" "), "".join(chr(c) if 32 <= c < 127 else "." for c in g[o:o + 16])))
psz = struct.unpack_from("<Q", g, 0x14)[0]
print("  size@0x14 = %#x, total@0x6C = %#x, version@0x60 = %#x" % (psz, struct.unpack_from("<I", g, 0x6C)[0], struct.unpack_from("<I", g, 0x60)[0]))

# dirs
print("\n'$PSP' occurrences:")
i = -1
while True:
    i = b.find(b"$PSP", i + 1)
    if i < 0:
        break
    print("  @%#x  checksum=%#010x count=%d totalsize=%#x" % (i, struct.unpack_from("<I", b, i + 4)[0], struct.unpack_from("<I", b, i + 8)[0], struct.unpack_from("<I", b, i + 12)[0]))

# dir checksum algorithm: negative dword sum over dir region skipping +4
DIR_OFF = 0x8E0000
DIR_SIZE = 0x5D0  # from totalsize field
d = b[DIR_OFF:DIR_OFF + DIR_SIZE]
s = 0
for j in range(0, DIR_SIZE, 4):
    if j == 4:
        continue
    s += struct.unpack_from("<I", d, j)[0]
neg = (-s) & 0xFFFFFFFF
stored = struct.unpack_from("<I", d, 4)[0]
print("\ndir neg-dword-sum: computed=%#010x stored=%#010x -> %s" % (neg, stored, "OK" if neg == stored else "FAIL"))

# free FF runs >= 0x3100
print("\nfree FF runs >= 0x3100:")
runs = []
i = 0
n = len(b)
FF = b"\xff"
cur = None
while i < n:
    if b[i] == 0xFF:
        if cur is None:
            cur = i
    else:
        if cur is not None:
            if i - cur >= 0x3100:
                runs.append((cur, i))
            cur = None
        # fast skip using find of non-FF? keep simple
    i += 1
if cur is not None and n - cur >= 0x3100:
    runs.append((cur, n))
for s, e in runs:
    print("  %#09x - %#09x  (%#x bytes)  align100:%s" % (s, e, e - s, (s % 0x100) == 0))
