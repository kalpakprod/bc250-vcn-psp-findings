# A2c: parse t28 DRIVER_ENTRIES container: load table + nested $PS1 blobs.
import struct, hashlib

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
T28 = ROM[0x984F00:0x984F00 + 0x1A770]
print("t28 blob len=%#x head=%s" % (len(T28), T28[:24].hex()))
if T28[0x10:0x14] == b"$PS1":
    size = struct.unpack_from("<I", T28, 0x14)[0]
    ver = struct.unpack_from("<I", T28, 0x60)[0]
    typ = struct.unpack_from("<I", T28, 0x58)[0]
    print("envelope: size=%#x type@58=%#x ver@60=%#x total@6C=%#x" % (
        size, typ, ver, struct.unpack_from("<I", T28, 0x6C)[0]))
    BODY = T28[0x100:0x100 + size]
    print("body len=%#x" % len(BODY))
else:
    BODY = T28
    print("(no $PS1 @+0x10)")

print("\n== body head u32 rows (first 0x120) ==")
for i in range(0, 0x120, 16):
    w = struct.unpack_from("<IIII", BODY, i)
    print("  +%#05x: %08x %08x %08x %08x" % (i, *w))

print("\n== nested $PS1 envelopes inside body ==")
nested = []
i = -1
while True:
    i = BODY.find(b"$PS1", i + 1)
    if i < 0:
        break
    if i + 0x70 <= len(BODY):
        sz = struct.unpack_from("<I", BODY, i + 4)[0]
        ty = struct.unpack_from("<I", BODY, i + 0x48)[0]
        vr = struct.unpack_from("<I", BODY, i + 0x50)[0]
        if 0 < sz < len(BODY):
            nested.append((i - 0x10, sz, ty, vr))  # envelope starts 0x10 before magic
for off, sz, ty, vr in nested:
    print("  env @body+%#06x size=%#-8x type@+58=%#010x ver@+60=%#010x" % (off, sz, ty, vr))

# compare nested bodies with known blobs
KNOWN = {
    "SEC_GASKET 0x24": ROM[0x982000:0x982000 + 0x2E50],
    "TOS_POLICY 0x45": ROM[0x9CA400:0x9CA400 + 0x6E0],
    "SMU 0x08": ROM[0x8FF000:0x8FF000 + 0x40200],
    "HW_IP_CONFIG 0x20": ROM[0x981900:0x981900 + 0x650],
    "FW_XHCI 0x44": ROM[0x9C3D00:0x9C3D00 + 0x6610],
}
print("\n== nested vs known standalone blobs (envelope-level md5) ==")
for off, sz, ty, vr in nested:
    env = BODY[off:off + 0x100 + sz + 0x100] if off + 0x100 + sz + 0x100 <= len(BODY) else BODY[off:]
    h = hashlib.md5(env).hexdigest()
    match = [k for k, v in KNOWN.items() if hashlib.md5(v).hexdigest() == h]
    print("  @+%#06x size=%#x md5=%s %s" % (off, sz, h[:12], ("== " + match[0]) if match else ""))

print("\n== scan whole ROM for OTHER copies of gasket/0x45 envelopes (md5 of 0x100+body) ==")
gsig = hashlib.md5(KNOWN["SEC_GASKET 0x24"]).hexdigest()
psig = hashlib.md5(KNOWN["TOS_POLICY 0x45"]).hexdigest()
step = 0x100
for off in range(0, len(ROM) - 0x3010, step):
    h = hashlib.md5(ROM[off:off + 0x2E50]).hexdigest()
    if h == gsig:
        print("  gasket envelope copy @ROM %#x" % off)
for off in range(0, len(ROM) - 0x6E0, step):
    h = hashlib.md5(ROM[off:off + 0x6E0]).hexdigest()
    if h == psig:
        print("  0x45 envelope copy @ROM %#x" % off)
print("(done)")
