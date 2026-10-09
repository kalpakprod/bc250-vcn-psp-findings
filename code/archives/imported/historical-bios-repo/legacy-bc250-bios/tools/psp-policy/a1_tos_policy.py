# A1: decode TOS_SECURITY_POLICY ($PSP type 0x45) envelope+body for Robin (BC-250) and Cezanne donors.
import struct, math, os

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()


def entropy(b):
    if not b:
        return 0
    cnt = [0] * 256
    for x in b:
        cnt[x] += 1
    n = len(b)
    return -sum((c / n) * math.log2(c / n) for c in cnt if c)


def parse_env(tag, blob):
    # envelope: 16B nonce, $PS1 @+0x10, u32 size @+0x14 (body), ... body @+0x100, tail 0x100
    assert blob[0x10:0x14] == b"$PS1", blob[0x10:0x14]
    size = struct.unpack_from("<I", blob, 0x14)[0]
    total = struct.unpack_from("<I", blob, 0x6C)[0]
    ver = struct.unpack_from("<I", blob, 0x60)[0]
    typ = struct.unpack_from("<I", blob, 0x58)[0]
    body = blob[0x100:0x100 + size]
    tail = blob[0x100 + size:]
    print("%s: len=%#x $PS1 size=%#x total@6C=%#x type@58=%#x ver@60=%#x tail=%#x" % (tag, len(blob), size, total, typ, ver, len(tail)))
    print("  body: len=%#x entropy=%.2f" % (len(body), entropy(body)))
    print("  body[0:32] =", body[:32].hex())
    return body


print("== Robin (BC-250 hw dump) type 0x45 @0x9ca400, dir size 0x6e0 ==")
robin_env = ROM[0x9CA400:0x9CA400 + 0x6E0]
robin_body = parse_env("robin", robin_env)

# structure walk attempts on robin body: gasket-style groups {type,count,pairs}? u32 words
print("\n  u32 view of body head (0x80):")
for i in range(0, min(0x80, len(robin_body)), 16):
    ws = struct.unpack_from("<IIII", robin_body, i)
    print("    +%#04x: %08x %08x %08x %08x" % (i, *ws))

print("\n== Cezanne donor 0x45 blobs (keys_raw/cezanne_d*) ==")
donors = []
for root in ["cezanne_d0", "cezanne_d1", "cezanne_d2", "cezanne_d3"]:
    d = r"C:\Users\OWNER\tmp_bc250\recon\keys_raw" + "\\" + root
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if "TOS_SECURITY_POLICY" in f:
            donors.append(os.path.join(d, f))
bodies = {}
for p in donors[:6]:
    blob = open(p, "rb").read()
    if blob[0x10:0x14] != b"$PS1":
        print(os.path.basename(p), ": no $PS1 @+0x10, head:", blob[:24].hex())
        continue
    tag = os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p)
    bodies[tag] = parse_env(tag, blob)

# robin5 sec gasket copy for comparison
print("\n== robin5 (BIOS 5.00) 0x45 for cross-version check ==")
p5 = r"C:\Users\OWNER\tmp_bc250\recon\robin5_psp_bodies\TOS_SECURITY_POLICY~0x45_B.51.1.16.body"
if os.path.exists(p5):
    b5 = open(p5, "rb").read()
    print("robin5 body len=%#x entropy=%.2f head=%s" % (len(b5), entropy(b5), b5[:32].hex()))
    if robin_body[:len(b5)] == b5 or b5[:len(robin_body)] == robin_body:
        print("  robin(hw)==robin5 body: MATCH (prefix)")

# pairwise donor-vs-robin body comparison
print("\n== donor vs robin body diffs ==")
def diffranges(a, b):
    if len(a) != len(b):
        return None
    rs = []
    for i in range(len(a)):
        if a[i] != b[i]:
            if rs and rs[-1][1] == i - 1:
                rs[-1][1] = i
            else:
                rs.append([i, i])
    return rs

for tag, b in bodies.items():
    r = diffranges(robin_body, b)
    if r is None:
        # compare common prefix
        n = min(len(robin_body), len(b))
        rr = diffranges(robin_body[:n], b[:n])
        print("%s: len differs (robin %#x vs %#x); common-prefix diff ranges: %d, first: %s" % (
            tag, len(robin_body), len(b), 0 if rr is None else len(rr), rr[:4] if rr else "-"))
    else:
        print("%s: same len; %d diff ranges; first: %s" % (tag, len(r), r[:6]))
